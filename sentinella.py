import requests
import traceback
from datetime import datetime
import os
import json

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("⚠️ Falten variables d'entorn TELEGRAM_TOKEN o TELEGRAM_CHAT_ID")
    # No fem raise per no fer fallar el workflow


def enviar_missatge(text):
    if not TOKEN or not CHAT_ID:
        print("Missatge NO enviat (faltan credencials Telegram):")
        print(text)
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("Error enviant missatge:", e)


ACTIUS = [
    # Macro Hard Assets
    {"ticker": "REMX",   "nom": "VanEck Rare Earths (REMX)",        "capa": "Macro Hard Assets"},
    {"ticker": "IH2O.L", "nom": "iShares Global Water (IH2O)",      "capa": "Macro Hard Assets"},
    {"ticker": "XDWM.L", "nom": "X MSCI World Materials (XDWM)",    "capa": "Macro Hard Assets"},
    {"ticker": "IUES.L", "nom": "iShares S&P 500 Energy (IUES)",    "capa": "Macro Hard Assets"},
    {"ticker": "IUUS.L", "nom": "iShares S&P 500 Utilities (IUUS)", "capa": "Macro Hard Assets"},
    {"ticker": "AGAP.L", "nom": "WT Agriculture (AGAP)",            "capa": "Macro Hard Assets"},
    {"ticker": "INFR.L", "nom": "iShares Global Infrastructure",    "capa": "Macro Hard Assets"},
    {"ticker": "URNM.L", "nom": "Sprott Uranium Miners (URNM)",     "capa": "Macro Hard Assets"},
    {"ticker": "SSLV.L", "nom": "Invesco Physical Silver (SSLV)",   "capa": "Macro Hard Assets"},
    {"ticker": "SILJ",   "nom": "Amplify Junior Silver Miners",     "capa": "Macro Hard Assets"},
    {"ticker": "WCOA.L", "nom": "WisdomTree Enhanced Commodity",    "capa": "Macro Hard Assets"},
    {"ticker": "GLDM",   "nom": "SPDR Gold MiniShares (GLDM)",      "capa": "Macro Hard Assets"},
    {"ticker": "ZGLD.SW","nom": "21Shares Physical Gold (ZGLD)",    "capa": "Macro Hard Assets"},
    {"ticker": "IBIT",   "nom": "iShares Bitcoin Trust (IBIT)",     "capa": "Macro Hard Assets"},
    {"ticker": "ABTC.SW", "nom": "21Shares Bitcoin ETP (ABTC.SW)",  "capa": "Macro Hard Assets"},

    # BTC / ETH directes (macro/creixement)
    {"ticker": "BTC-USD","nom": "Bitcoin Spot",                     "capa": "Macro / Creixement"},
    {"ticker": "ETH-USD","nom": "Ethereum Spot",                    "capa": "Macro / Creixement"},
]

# --- NOVETAT: variable global per guardar l’última alerta ---
ULTIMA_ALERTA = None


def obtenir_variacio_yahoo(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=15)
    data = r.json()

    result = data["chart"]["result"][0]
    meta = result["meta"]

    preu_actual = meta["regularMarketPrice"]
    preu_obertura = meta["chartPreviousClose"]
    variacio = ((preu_actual - preu_obertura) / preu_obertura) * 100

    return preu_actual, variacio


def format_missatge(actiu, preu, variacio):
    direccio = "📉" if variacio < 0 else "📈"
    return (
        f"{direccio} ALERTA {actiu['nom']}\n"
        f"Capa: {actiu['capa']}\n"
        f"Ticker: {actiu['ticker']}\n"
        f"Variació diària: {variacio:.2f}%\n"
        f"Preu actual: {preu}\n"
        f"Hora: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Playbook: revisar possibles entrades / acumulació."
    )


def llindar_variacio(actiu):
    if actiu["capa"] == "Macro Hard Assets":
        return -3.0
    if "Bitcoin" in actiu["nom"] or "Ethereum" in actiu["nom"]:
        return -4.0
    return -4.0


def processar_actiu(actiu):
    global ULTIMA_ALERTA

    ticker = actiu["ticker"]
    print(f"Processant {ticker}...")

    try:
        preu, variacio = obtenir_variacio_yahoo(ticker)
    except Exception as e:
        txt = f"⚠️ Error obtenint dades per {actiu['nom']} ({ticker}):\n{e}"
        print(txt)
        enviar_missatge(txt)
        return

    print(f"{ticker}: {variacio:.2f}%  preu={preu}")

    llindar = llindar_variacio(actiu)

    if variacio <= llindar:
        missatge = format_missatge(actiu, preu, variacio)
        enviar_missatge(missatge)

        # --- NOVETAT: guardar alerta per al JSON final ---
        ULTIMA_ALERTA = {
            "actiu": actiu["nom"],
            "ticker": actiu["ticker"],
            "capa": actiu["capa"],
            "variacio": round(variacio, 2),
            "preu": preu,
            "hora": datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            "playbook": "revisar possibles entrades / acumulació"
        }
    else:
        print(f"{ticker}: variació {variacio:.2f}% (no arriba al llindar {llindar}%)")


def main():
    print("Inici sentinella patrimonial...")
    for actiu in ACTIUS:
        processar_actiu(actiu)
    print("Fi sentinella.")

    # --- NOVETAT: imprimir JSON final per al workflow ---
    if ULTIMA_ALERTA:
        print(json.dumps({"alerta": ULTIMA_ALERTA}))
    else:
        heartbeat = {
            "estat": "OK",
            "hora": datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            "missatge": "Sense alertes"
        }
        print(json.dumps({"heartbeat": heartbeat}))
    # ----------------------------------------------------


if __name__ == "__main__":
    try:
        main()
    except Exception:
        error_text = "⚠️ Error inesperat al sentinella global:\n" + traceback.format_exc()
        print(error_text)
        enviar_missatge(error_text)
