import asyncio
import json
import random
from typing import Awaitable, Callable, Dict, Iterable, List, Optional, Set, Tuple

import websockets

SPOT_URL = "wss://stream.binance.com:9443/stream"
FUTURES_URL = "wss://fstream.binance.com/stream"

# Tipagem dos handlers: async def handler(stream: str, data: dict) -> None
Handler = Callable[[str, dict], Awaitable[None]]


def _default_noop(_: str, __: dict) -> Awaitable[None]:
    async def _noop(*args, **kwargs):
        return None
    return _noop("", {})


class BinanceWebSocket:
    """
    Exemplo de uso:

    ws = BinanceWebSocket(
        market="futures",
        streams=["btcusdt@kline_1m", "pepeusdt@bookTicker"],
        rate_limit_per_sec=10,  # Futures=10, Spot=5
    )

    # Handlers
    async def on_kline(stream, data): ...
    async def on_book_ticker(stream, data): ...
    async def on_any(stream, data): ...

    ws.set_handler("kline", on_kline)
    ws.set_handler("bookTicker", on_book_ticker)
    ws.set_handler("any", on_any)  # opcional, recebe tudo

    await ws.run()  # bloqueia até exception/close; use em task para rodar com sua app
    """

    def __init__(
        self,
        market: str = "futures",                  # "spot" ou "futures"
        streams: Optional[Iterable[str]] = None,  # lista de streams iniciais
        rate_limit_per_sec: int = 10,             # Spot=5, Futures=10
        max_queue: int = 2048,                    # fila interna do websockets
        ping_interval: int = 150,                 # segundos
    ):
        assert market in ("spot", "futures")
        self.base_url = FUTURES_URL if market == "futures" else SPOT_URL
        self.rate_limit_per_sec = rate_limit_per_sec
        self.max_queue = max_queue
        self.ping_interval = ping_interval

        self.streams: Set[str] = set(s.lower() for s in (streams or []))
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._stop = False
        self._id = 0

        # fila de mensagens de controle (SUBSCRIBE/UNSUBSCRIBE)
        self._ctrl_q: "asyncio.Queue[dict]" = asyncio.Queue()

        # roteamento
        self._handlers: Dict[str, Handler] = {
            "kline": _default_noop,         # payload["e"] == "kline"
            "aggTrade": _default_noop,      # payload["e"] == "aggTrade"
            "bookTicker": _default_noop,    # identificamos pelo formato
            "24hrMiniTicker": _default_noop,# payload["e"] == "24hrMiniTicker"
            "depthUpdate": _default_noop,   # payload["e"] == "depthUpdate"
            "ticker": _default_noop,        # payload["e"] == "24hrTicker" (spot)
            "any": _default_noop,           # fallback para qualquer coisa
        }

    # ---------------------- API pública ----------------------

    def set_handler(self, kind: str, handler: Handler) -> None:
        """
        kind pode ser: "kline", "aggTrade", "bookTicker", "24hrMiniTicker",
                       "depthUpdate", "ticker", "any".
        """
        self._handlers[kind] = handler

    async def subscribe(self, *streams: str) -> None:
        """Enfileira SUBSCRIBE (respeita rate-limit no worker)."""
        new_streams = [s.lower() for s in streams if s and s.lower() not in self.streams]
        if not new_streams:
            return
        self.streams.update(new_streams)
        await self._ctrl_q.put({"method": "SUBSCRIBE", "params": new_streams})

    async def unsubscribe(self, *streams: str) -> None:
        """Enfileira UNSUBSCRIBE (respeita rate-limit no worker)."""
        rem_streams = [s.lower() for s in streams if s and s.lower() in self.streams]
        if not rem_streams:
            return
        for s in rem_streams:
            self.streams.discard(s)
        await self._ctrl_q.put({"method": "UNSUBSCRIBE", "params": rem_streams})

    async def close(self) -> None:
        self._stop = True
        try:
            if self.ws:
                await self.ws.close()
        finally:
            self._connected = False

    async def run(self) -> None:
        """Loop de conexão com reconexão/backoff."""
        backoff = 1
        while not self._stop:
            try:
                await self._connect_and_serve()
                backoff = 1  # saiu ok
            except asyncio.CancelledError:
                raise
            except Exception:
                # reconecta com backoff exponencial + jitter
                await asyncio.sleep(backoff + random.random())
                backoff = min(backoff * 2, 30)

    # ---------------------- internos ----------------------

    async def _send(self, msg: dict) -> None:
        self._id += 1
        msg["id"] = self._id
        assert self.ws is not None
        await self.ws.send(json.dumps(msg))

    async def _ctrl_worker(self) -> None:
        """Envia SUBSCRIBE/UNSUBSCRIBE respeitando rate-limit."""
        interval = 1 / max(1, self.rate_limit_per_sec)
        while self._connected and not self._stop:
            try:
                msg = await asyncio.wait_for(self._ctrl_q.get(), timeout=5)
            except asyncio.TimeoutError:
                continue
            try:
                await self._send(msg)
            except Exception:
                # se falhar envio, devolve à fila para tentar novo envio após reconexão
                await self._ctrl_q.put(msg)
                return
            await asyncio.sleep(interval)

    async def _ping_worker(self) -> None:
        """Mantém a conexão viva."""
        while self._connected and not self._stop:
            try:
                assert self.ws is not None
                await self.ws.ping()
            except Exception:
                return
            await asyncio.sleep(self.ping_interval)

    async def _receiver(self) -> None:
        """Recebe mensagens e roteia para handlers."""
        assert self.ws is not None
        async for raw in self.ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue

            # formato combinado: {"stream": "<name>", "data": {...}}
            stream = msg.get("stream")
            data = msg.get("data")

            if stream is None and data is None:
                # alguns streams globais podem vir com array direto (ex.: !miniTicker@arr)
                # padroniza como "any"
                await self._dispatch("any", "", msg)
                continue

            if data is None:
                # fallback
                await self._dispatch("any", stream or "", msg)
                continue

            # tenta derivar "kind" a partir do conteúdo
            event_type = data.get("e")  # muitos payloads têm 'e'
            kind = None

            if event_type in ("kline", "aggTrade", "depthUpdate", "24hrMiniTicker", "24hrTicker"):
                kind = "ticker" if event_type == "24hrTicker" else event_type
            else:
                # bookTicker não tem 'e'; inferimos por campos
                if {"b", "B", "a", "A"}.issubset(data.keys()):
                    kind = "bookTicker"

            if kind is None:
                # não reconhecido? manda para "any"
                await self._dispatch("any", stream, data)
            else:
                await self._dispatch(kind, stream, data)
                # também manda para "any" se quiser observar tudo:
                if self._handlers.get("any"):
                    await self._dispatch("any", stream, data)

    async def _dispatch(self, kind: str, stream: str, data: dict) -> None:
        handler = self._handlers.get(kind)
        if handler is None:
            return
        try:
            await handler(stream, data)
        except Exception:
            # Protege o loop de exceções em handlers
            pass

    async def _connect_and_serve(self) -> None:
        """Abre a conexão (com ?streams=...) e roda workers + receiver."""
        # monta URL com streams iniciais, se houver
        url = self.base_url
        if self.streams:
            joined = "/".join(sorted(self.streams))
            url = f"{self.base_url}?streams={joined}"

        async with websockets.connect(url, max_queue=self.max_queue) as ws:
            self.ws = ws
            self._connected = True

            ctrl_task = asyncio.create_task(self._ctrl_worker())
            ping_task = asyncio.create_task(self._ping_worker())
            recv_task = asyncio.create_task(self._receiver())

            done, pending = await asyncio.wait(
                {ctrl_task, ping_task, recv_task},
                return_when=asyncio.FIRST_EXCEPTION
            )
            # cancela o que restou
            for t in pending:
                t.cancel()

            self._connected = False

