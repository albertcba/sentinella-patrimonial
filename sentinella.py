import requests
import traceback
from datetime import datetime
import os
import json

DADES_ACTIUS = []

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ---------------------------------------------------------
#   MACRO ENGINE — FRED API
# ---------------------------------------------------------

def obtenir_fred(series_id):
    """Retorna (valor_actual, valor_anterior) d'una sèrie FRED."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": os.getenv("FRED_API_KEY"),
        "file_type": "json",
        "sort_order": "desc",
        "limit": 2
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()["observations"]

    actual = float(data[0]["value"])
    anterior = float(data[1]["value"])
    return actual, anterior


def semafor_tendencia(actual, anterior):
    """Converteix la tendència en un semàfor numèric."""
    if actual > anterior * 1.02:
        return -1   # vermell
    if actual < anterior * 0.98:
        return +1   # verd
    return 0        # groc


def obtenir_macro():
    """Construeix el MACRO dict amb semàfors automàtics."""
    try:
        tga_act, tga_ant = obtenir_fred("WTREGEN")
        fed_act, fed_ant = obtenir_fred("WALCL")
        tr_act, tr_ant = obtenir_fred("DFII10")

        return {
            "tga": semafor_tendencia(tga_act, tga_ant),
            "fed_balance": semafor_tendencia(fed_act, fed_ant),
            "tipus_reals": semafor_tendencia(tr_act, tr_ant)
        }

    except Exception as e:
        print("⚠️ Error obtenint dades macro:", e)
        return {"tga": 0, "fed_balance": 0, "tipus_reals": 0}


# --- MACRO REAL (ja no és placeholder)
MACRO = obtenir_macro()

# ---------------------------------------------------------
#   SENSIBILITAT MACRO PER ACTIU
# ---------------------------------------------------------

SENSIBILITAT_MACRO = {
    "GLDM":      {"tga": 0, "fed_balance": 1, "tipus_reals": -2},
    "ZGLD.SW":   {"tga": 0, "fed_balance": 1, "tipus_reals": -2},
    "SSLV.L":    {"tga": 0, "fed_balance": 1, "tipus_reals": -2},
    "SILJ":      {"tga": 0, "fed_balance": 1, "tipus_reals": -2},
    "IBIT":      {"tga": 1, "fed_balance": 1, "tipus_reals": -1},
    "ABTC.SW":   {"tga": 1, "fed_balance": 1, "tipus_reals": -1},
    "REMX":      {"tga": 0, "fed_balance": 1, "tipus_reals": -1},
    "XDWM.L":    {"tga": 0, "fed_balance": 1, "tipus_reals": -1},
    "IUES.L":    {"tga": 1, "fed_balance": 1, "tipus_reals": 0},
    "IUUS.L":    {"tga": 0, "fed_balance": 1, "tipus_reals": 0},
    "INFR.L":    {"tga": 0, "fed_balance": 1, "tipus_reals": 0},
    "IH2O.L":    {"tga": 0, "fed_balance": 1, "tipus_reals": 0},
    "WCOA.L":    {"tga": 1, "fed_balance": 1, "tipus_reals": 0},
    "AGAP.L":    {"tga": 1, "fed_balance": 1, "tipus_reals": 0},
    "NUUR.L":    {"tga": 0, "fed_balance": 1, "tipus_reals": 0},
    "URNM.L":    {"tga": 0, "fed_balance": 1, "tipus_reals": 0},
}

# ---------------------------------------------------------
#   FUNCIONS EXISTENTS
# ---------------------------------------------------------

def es_cripto(actiu):
    return actiu["ticker"] in ["BTC-EUR", "ETH-EUR"]

def mercat_obert():
    hora = datetime.utcnow().hour
    return 7 <= hora <= 20

if not TOKEN or not CHAT_ID:
    print("⚠️ Falten variables d'entorn TELEGRAM_TOKEN o TELEGRAM_CHAT_ID")

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
    {"ticker": "REMX", "nom": "VanEck Rare Earths (REMX)", "capa": "Macro Hard Assets"},
    {"ticker": "IH2O.L", "nom": "iShares Global Water (IH2O)", "capa": "Macro Hard Assets"},
    {"ticker": "XDWM.L", "nom": "X MSCI World Materials (XDWM)", "capa": "Macro Hard Assets"},
    {"ticker": "IUES.L", "nom": "iShares S&P 500 Energy (IUES)", "capa": "Macro Hard Assets"},
    {"ticker": "IUUS.L", "nom": "iShares S&P 500 Utilities (IUUS)", "capa": "Macro Hard Assets"},
    {"ticker": "AGAP.L", "nom": "WT Agriculture (AGAP)", "capa": "Macro Hard Assets"},
    {"ticker": "INFR.L", "nom": "iShares Global Infrastructure", "capa": "Macro Hard Assets"},
    {"ticker": "URNM.L", "nom": "Sprott Uranium Miners (URNM)", "capa": "Macro Hard Assets"},
    {"ticker": "SSLV.L", "nom": "Invesco Physical Silver (SSLV)", "capa": "Macro Hard Assets"},
    {"ticker": "SILJ", "nom": "Amplify Junior Silver Miners", "capa": "Macro Hard Assets"},
    {"ticker": "WCOA.L", "nom": "WisdomTree Enhanced Commodity", "capa": "Macro Hard Assets"},
    {"ticker": "GLDM", "nom": "SPDR Gold MiniShares (GLDM)", "capa": "Macro Hard Assets"},
    {"ticker": "ZGLD.SW", "nom": "21Shares Physical Gold (ZGLD)", "capa": "Macro Hard Assets"},
    {"ticker": "IBIT", "nom": "iShares Bitcoin Trust (IBIT)", "capa": "Macro Hard Assets"},
    {"ticker": "ABTC.SW", "nom": "21Shares Bitcoin ETP (ABTC.SW)", "capa": "Macro Hard Assets"},

    {"ticker": "BTC-EUR", "nom": "Bitcoin Spot", "capa": "Macro / Creixement"},
    {"ticker": "ETH-EUR", "nom": "Ethereum Spot", "capa": "Macro / Creixement"},

    {"ticker": "IWFQ.L", "nom": "iShares Edge MSCI World Quality (IWFQ)", "capa": "Factors"},
    {"ticker": "IWVL.L", "nom": "iShares Edge MSCI World Value (IWVL)", "capa": "Factors"},
    {"ticker": "IWMO.L", "nom": "iShares Edge MSCI World Momentum (IWMO)", "capa": "Factors"},
    {"ticker": "MVOL.L", "nom": "iShares Edge MSCI World Minimum Vol (MVOL)", "capa": "Factors"},
]

ULTIMA_ALERTA = None

# ---------------------------------------------------------
#   SEMÀFOR MACRO PER ACTIU
# ---------------------------------------------------------

def semafor_macro_actiu(actiu, macro):
    ticker = actiu["ticker"]
    if ticker not in SENSIBILITAT_MACRO:
        return None

    s = SENSIBILITAT_MACRO[ticker]
    score = (
        s["tga"] * macro["tga"] +
        s["fed_balance"] * macro["fed_balance"] +
        s["tipus_reals"] * macro["tipus_reals"]
    )

    if score >= 2:
        return "🟢"
    if score <= -2:
        return "🔴"
    return "🟡"

# ---------------------------------------------------------
#   PROCESSAMENT D'ACTIUS
# ---------------------------------------------------------

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
    if actiu["capa"] == "Factors":
        return -2.0
    if "Bitcoin" in actiu["nom"] or "Ethereum" in actiu["nom"]:
        return -4.0
    return -4.0


def processar_actiu(actiu):
    global ULTIMA_ALERTA

    if actiu["capa"] == "Macro Hard Assets" and not mercat_obert():
        print(f"Saltant {actiu['ticker']} (mercat tancat)")
        return

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

    DADES_ACTIUS.append({
        "ticker": actiu["ticker"],
        "nom": actiu["nom"],
        "capa": actiu["capa"],
        "preu": preu,
        "variacio": round(variacio, 2),
        "hora": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "semafor_macro": semafor_macro_actiu(actiu, MACRO)
    })

    llindar = llindar_variacio(actiu)

    if variacio <= llindar:
        missatge = format_missatge(actiu, preu, variacio)
        enviar_missatge(missatge)

        ULTIMA_ALERTA = {
            "actiu": actiu["nom"],
            "ticker": actiu["ticker"],
            "capa": actiu["capa"],
            "variacio": round(variacio, 2),
            "preu": preu,
            "hora": datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            "playbook": "revisar possibles entrades / acumulació"
        }


def main():
    print("Inici sentinella patrimonial...")
    for actiu in ACTIUS:
        processar_actiu(actiu)
    print("Fi sentinella.")

    resultat = {}

    if ULTIMA_ALERTA:
        resultat["alerta"] = ULTIMA_ALERTA
    else:
        resultat["heartbeat"] = {
            "hora": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "missatge": "Sistema operatiu. Sense alertes."
        }

    resultat["sistema"] = {
        "workflow": "sentinella",
        "freq": "cada 30 minuts (7h–17h, dill–div)",
        "estat": "OK",
        "errors": "0",
        "actius_monitoritzats": len(ACTIUS)
    }

    resultat["macro"] = MACRO
    resultat["actius"] = DADES_ACTIUS
    resultat["ultima_execucio"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    print(json.dumps(resultat))
    print("DEBUG MACRO:", MACRO)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        error_text = "⚠️ Error inesperat al sentinella global:\n" + traceback.format_exc()
        print(error_text)
        enviar_missatge(error_text)
