import os
import pandas as pd
from finnhub import Client
from dotenv import load_dotenv 
import time
from typing import Optional


load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Setup client
finnhub_client = Client(api_key=FINNHUB_API_KEY)


_RES_MAP = {
    "1m":"1","5m":"5","15m":"15","30m":"30","60m":"60","1h":"60",
    "1d":"D","d":"D","D":"D","1w":"W","w":"W","1M":"M","m":"M"
}
# intervals that require resample from 60m
_NEEDS_RESAMPLE = {"4h":"4H","8h":"8H","12h":"12H"}

def _compute_start_end(interval: str, limit: int,
                       start: Optional[int], end: Optional[int]) -> tuple[int,int]:
    """Retorna (start,end) em epoch seconds."""
    if end is None:
        end = int(time.time())
    if start is not None:
        return start, end

    # seconds per bar (approximation) for minutes; for D/W/M takes wide windows
    sec_per = {
        "1m":60,"5m":300,"15m":900,"30m":1800,"60m":3600,"1h":3600,
        "4h":14400,"8h":28800,"12h":43200,
        "1d":86400,"d":86400,"D":86400,
        "1w":7*86400,"w":7*86400,"W":7*86400,
        "1M":30*86400,"m":30*86400,"M":30*86400,
    }[interval]
    start = end - limit*sec_per
    return start, end

def _to_df(candles: dict) -> pd.DataFrame:
    """Converte resposta {'t','o','h','l','c','v','s'} -> DataFrame OHLCV UTC."""
    if not candles or candles.get("s") != "ok":
        return pd.DataFrame(columns=["ts","open","high","low","close","volume"])
    df = pd.DataFrame({
        "ts": pd.to_datetime(candles["t"], unit="s", utc=True),
        "open": candles["o"],
        "high": candles["h"],
        "low": candles["l"],
        "close": candles["c"],
        "volume": candles["v"],
    })
    return df.astype({"open":"float64","high":"float64","low":"float64","close":"float64","volume":"float64"})

def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample OHLCV preservando OHLC correto."""
    if df.empty: 
        return df
    df = df.set_index("ts").sort_index()
    agg = {
        "open":"first", "high":"max", "low":"min", "close":"last", "volume":"sum"
    }
    out = df.resample(rule).agg(agg).dropna().reset_index()
    return out

def get_market_data(
    symbol: str,
    interval: str = "1d",
    market: str = "crypto",              # "stock" | "crypto" | "forex"
    limit: int = 500,
    start: Optional[int] = None,
    end: Optional[int] = None,
    exchange: str = "BINANCE"            # used for crypto (ex.: "BINANCE")
) -> pd.DataFrame:
    """
    Returns candles in DataFrame with columns: ts, open, high, low, close, volume.
    - interval: "1m","5m","15m","30m","1h","4h","8h","12h","1d","1w","1M"
    - market: "stock" (AAPL), "crypto" (BTCUSDT), "forex" (OANDA:EUR_USD)
    - limit: approximate number of bars (for D/W/M is approximate window)
    - start/end: epoch seconds; if omitted, calculates by 'limit'.
    """
    interval = interval.strip()
    start, end = _compute_start_end(interval, limit, start, end)

    # decide endpoint and symbol
    if market == "stock":
        res_key = _RES_MAP.get(interval, interval)
        raw = finnhub_client.stock_candles(symbol, res_key, start, end)

    elif market == "crypto":
        res_key = _RES_MAP.get(interval, interval if interval in ("D","W","M") else "60")
        full_symbol = f"{exchange}:{symbol}"
        raw = finnhub_client.crypto_candles(full_symbol, res_key, start, end)

    elif market == "forex":
        res_key = _RES_MAP.get(interval, interval)
        # for forex, Finnhub uses format "OANDA:EUR_USD" in the symbol
        raw = finnhub_client.forex_candles(symbol, res_key, start, end)
    else:
        raise ValueError("market must be 'stock', 'crypto' or 'forex'.")

    df = _to_df(raw)

    # resample se for 4h/8h/12h
    if interval in _NEEDS_RESAMPLE:
        df = _resample_ohlcv(df, _NEEDS_RESAMPLE[interval])

    return df

    