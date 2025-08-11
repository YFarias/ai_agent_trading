#BinanceAPI


import os
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

def get_price(symbol: str) -> float:
    """Retorna o último preço de um ativo futuro (ex: BTCUSDT)."""
    ticker = binance_client.futures_symbol_ticker(symbol=symbol)
    return float(ticker["price"])


def get_balance(asset: str = "USDT") -> float:
    """Retorna o saldo disponível de um ativo específico na conta de futuros."""
    balances = binance_client.futures_account_balance()
    for item in balances:
        if item["asset"] == asset:
            return float(item["balance"])
    return 0.0


def get_position_info(symbol: str) -> dict:
    """Retorna informações da posição aberta de um símbolo (ex: tamanho, entrada, PnL)."""
    positions = binance_client.futures_position_information(symbol=symbol)
    return positions[0] if positions else {}


def get_exchange_info() -> dict:
    """Retorna informações sobre todos os ativos de Futuros disponíveis."""
    return binance_client.futures_exchange_info()















