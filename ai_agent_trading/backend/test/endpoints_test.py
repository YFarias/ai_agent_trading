## backend/test/endpoints_test.py
import asyncio
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, List

from fastapi import FastAPI, Query, Body
from pydantic import BaseModel, Field

from backend.data_source.binance_websocket import BinanceWebSocket


app = FastAPI(title="WS Smoke Test (choose asset by endpoint)")

# ---- buffers/estados em memória ----
BUFFERS: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=200))
LAST_BOOK: Dict[str, dict] = {}   # chave: SYMBOL (ex: 'PEPEUSDT')
LAST_KLINE: Dict[str, dict] = {}  # chave: stream (ex: 'pepeusdt@kline_1m')

WS_CLIENT: Optional[BinanceWebSocket] = None
WS_TASK: Optional[asyncio.Task] = None


# ---------- Handlers ----------
async def on_any(stream: str, data: dict):
    """Armazena tudo no buffer + indexa book/kline para consultas rápidas."""
    BUFFERS[stream].append(data)

    # bookTicker (não tem 'e')
    if {"s", "b", "B", "a", "A"}.issubset(data.keys()):
        sym = data["s"]
        LAST_BOOK[sym] = {
            "symbol": sym,
            "bid": float(data["b"]),
            "bid_qty": float(data["B"]),
            "ask": float(data["a"]),
            "ask_qty": float(data["A"]),
        }

    # kline (tem 'e' == 'kline')
    if data.get("e") == "kline":
        k = data.get("k", {})
        if k.get("x"):  # apenas quando a vela fecha
            LAST_KLINE[stream] = {
                "symbol": k.get("s"),
                "interval": k.get("i"),
                "open_time": k.get("t"),
                "close_time": k.get("T"),
                "open": float(k.get("o")),
                "high": float(k.get("h")),
                "low": float(k.get("l")),
                "close": float(k.get("c")),
                "volume": float(k.get("v")),
            }


# ---------- Lifespan ----------
@app.on_event("startup")
async def startup():
    global WS_CLIENT, WS_TASK
    # começa SEM streams; você escolhe via /subscribe
    WS_CLIENT = BinanceWebSocket(
        market="futures",      # troque para "spot" se quiser
        streams=[],
        rate_limit_per_sec=10, # Spot=5
    )
    WS_CLIENT.set_handler("any", on_any)
    WS_TASK = asyncio.create_task(WS_CLIENT.run())


@app.on_event("shutdown")
async def shutdown():
    global WS_CLIENT, WS_TASK
    if WS_CLIENT:
        await WS_CLIENT.close()
    if WS_TASK:
        WS_TASK.cancel()


# ---------- Models ----------
class SubscribeByParts(BaseModel):
    symbol: str = Field(..., description="ex: 'pepeusdt'")
    type: str = Field(..., description="ex: 'kline_1m', 'bookTicker', 'aggTrade', 'ticker', 'depth5'")

class SubscribeRaw(BaseModel):
    stream: str = Field(..., description="ex: 'pepeusdt@kline_1m'")

class StreamsBatch(BaseModel):
    streams: List[str]


# ---------- Helpers ----------
def build_stream(symbol: str, typ: str) -> str:
    """Monta 'symbol@type' padronizado em minúsculas."""
    return f"{symbol.lower()}@{typ}"


# ---------- Endpoints mínimos de validação ----------
@app.get("/status")
async def status():
    return {
        "connected_streams": sorted(list(WS_CLIENT.streams)) if WS_CLIENT else [],
        "buffers": {k: len(v) for k, v in BUFFERS.items()},
        "last_book_symbols": sorted(LAST_BOOK.keys()),
        "last_kline_streams": sorted(LAST_KLINE.keys()),
    }

@app.get("/streams")
async def streams():
    return {"streams": sorted(list(WS_CLIENT.streams)) if WS_CLIENT else []}

# ---- subscribe: aceita duas formas de body (raw stream OU symbol+type) ----
@app.post("/subscribe")
async def subscribe(
    raw: Optional[SubscribeRaw] = Body(None),
    parts: Optional[SubscribeByParts] = Body(None),
):
    if not WS_CLIENT:
        return {"error": "WS client not running"}

    if raw and raw.stream:
        stream = raw.stream.lower()
    elif parts and parts.symbol and parts.type:
        stream = build_stream(parts.symbol, parts.type)
    else:
        return {"error": "provide either {stream} or {symbol, type}"}

    await WS_CLIENT.subscribe(stream)
    return {"subscribed": stream}

@app.post("/unsubscribe")
async def unsubscribe(
    raw: Optional[SubscribeRaw] = Body(None),
    parts: Optional[SubscribeByParts] = Body(None),
):
    if not WS_CLIENT:
        return {"error": "WS client not running"}

    if raw and raw.stream:
        stream = raw.stream.lower()
    elif parts and parts.symbol and parts.type:
        stream = build_stream(parts.symbol, parts.type)
    else:
        return {"error": "provide either {stream} or {symbol, type}"}

    await WS_CLIENT.unsubscribe(stream)
    return {"unsubscribed": stream}

@app.get("/recent")
async def recent(stream: str = Query(..., description="ex: pepeusdt@kline_1m"), n: int = Query(5, ge=1, le=50)):
    q = BUFFERS.get(stream.lower(), deque())
    return {"stream": stream.lower(), "count": len(q), "messages": list(q)[-n:]}

@app.get("/last/bookticker")
async def last_book(symbol: str = Query(..., description="ex: PEPEUSDT")):
    data = LAST_BOOK.get(symbol.upper())
    return {"symbol": symbol.upper(), "data": data}

@app.get("/last/kline")
async def last_kline(symbol: str = Query(..., description="ex: PEPEUSDT"),
                     interval: str = Query("1m", description="ex: 1m, 5m, 1h")):
    stream = f"{symbol.lower()}@kline_{interval}"
    return {"stream": stream, "data": LAST_KLINE.get(stream)}
