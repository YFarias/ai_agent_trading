#BinanceAPI
import os
import pandas as pd
from binance.client import Client
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Lê chaves da API
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# Cria o cliente Binance
binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
binance_client.FUTURES_URL = 'https://fapi.binance.com'


# ========================
# Funções auxiliares
# ========================

def get_market_asset_data(symbol: str, interval: str = '1d', limit: int = 500) -> pd.DataFrame:
    """
    Obtém dados de mercado (candles) de um ativo futuro da Binance.
    
    :param symbol: Par de trading, ex: 'BTCUSDT'
    :param interval: Intervalo de tempo (ex: '4h', '1d', '1w')
    :param limit: Quantidade de candles a retornar (máx: 1500)
    :return: DataFrame com colunas: time, open, high, low, close, volume
    """
    klines = binance_client.futures_klines(symbol=symbol, interval=interval, limit=limit)

    df = pd.DataFrame(klines, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_base_volume", "taker_quote_volume", "ignore"
    ])

    # Convertendo tipos
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df.set_index("time", inplace=True)
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

    return df[["open", "high", "low", "close", "volume"]]