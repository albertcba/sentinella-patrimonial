import requests
import os
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_missatge(text):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Falta TOKEN o CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
    requests.get(url, params=params, timeout=10)

ACTIUS = [
    {"ticker": "REMX",   "nom": "VanEck Rare Earths (REMX)",        "capa": "Macro Hard Assets"},
    {"ticker": "IH2O.L", "nom": "iShares Global Water (IH2O)",      "capa": "Macro Hard Assets"},
    {"ticker": "XDWM.L", "nom": "X MSCI World Materials (XDWM)",    "capa": "Macro Hard Assets"},
    {"ticker": "IUES.L", "nom": "iShares S&P 500 Energy (IUES)",    "capa": "Macro Hard Assets"},
    {"ticker": "IUUS.L", "nom": "iShares S&P 500 Utilities (IUUS)", "capa": "Macro Hard Assets"},
    {"ticker": "AGAP.L", "nom": "WT Agriculture (AGAP)",            "capa": "Macro Hard Assets"},
    {"ticker": "INFR.L", "nom": "iShares Global Infrastructure",    "capa": "Macro Hard Assets"},
    {"ticker": "NUUR.L", "nom": "iShares Nuclear Energy (NUUR)",    "capa": "Macro Hard Assets"},
    {"ticker": "URNM.L", "nom": "Sprott Uranium Miners (URNM)",     "capa": "Macro Hard Assets"},
    {"ticker": "SSLV.L", "nom": "Invesco Physical Silver (SSLV)",   "capa": "Macro Hard Assets"},
    {"ticker": "SILJ",   "nom": "Amplify Junior Silver Miners",     "capa": "Macro Hard Assets"},
    {"ticker": "WCOA.L", "nom": "WisdomTree Enhanced Commodity",    "capa": "Macro Hard Assets"},
    {"ticker": "GLDM",   "nom": "SPDR Gold MiniShares (GLDM)",      "capa": "Macro Hard Assets"},
    {"ticker": "ZGLD.SW","nom": "21Shares Physical Gold (ZGLD)",    "capa": "Macro Hard Assets"},
    {"ticker": "IBIT",   "nom": "iShares Bitcoin Trust (IBIT)",     "capa": "Macro Hard Assets"},
    {"ticker": "ABTCEUR","nom": "21Shares Bitcoin ETP (ABTCEUR)",   "capa": "Macro Hard Assets"},
    {"ticker": "BTC-USD","nom": "Bitcoin Spot",                     "capa": "Macro / Creixement"},
    {"ticker": "ETH-USD","nom": "Ethereum Spot",                    "capa": "Macro / Creixement"},
]

def obtenir_variacio(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    data = r.json()
    meta = data["chart"]["result"][0]["meta"]
    preu = meta["regularMarketPrice"]
    obertura = meta["chartPreviousClose"]
    variacio = ((preu - obertura) / obertura) * 100
    return preu, variacio

def main():
    resultats = []

    for
