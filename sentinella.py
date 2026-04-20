import requests
import traceback
from datetime import datetime
import os
import json

DADES_ACTIUS = []

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def es_cripto(actiu):
    return actiu["ticker"] in ["BTC-EUR", "ETH-EUR"]

def mercat_obert():
    # Horari ampliat que cobreix Europa i USA
    hora = datetime.utcnow().hour
    return 7 <= hora <= 20

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
    {"ticker": "REMX",   "nom": "VanEck Rare Earths (REMX)",                    "capa": "Macro Hard Assets"},
    {"ticker": "IH2O.L", "nom": "iShares Global Water (IH2O)",                  "capa": "Macro Hard Assets"},
    {"ticker": "XDWM.L", "nom": "X MSCI World Materials (XDWM)",                "capa": "Macro Hard Assets"},
    {"ticker": "IUES.L", "nom": "iShares S&P 500 Energy (IUES)",                "capa": "Macro Hard Assets"},
    {"ticker": "IUUS.L", "nom": "iShares S&P 500 Utilities (IUUS)",             "capa": "Macro Hard Assets"},
    {"ticker": "AGAP.L", "nom": "WT Agriculture (AGAP)",                        "capa": "Macro Hard Assets"},
    {"ticker": "INFR.L", "nom": "iShares Global Infrastructure",                "capa": "Macro Hard Assets"},
    {"ticker": "URNM.L", "nom": "Sprott Uranium Miners (URNM)",                 "capa": "Macro Hard Assets"},
    {"ticker": "SSLV.L", "nom": "Invesco Physical Silver (SSLV)",               "capa": "Macro Hard Assets"},
    {"ticker": "SILJ",   "nom": "Amplify Junior Silver Miners",                 "capa": "Macro Hard Assets"},
    {"ticker": "WCOA.L", "nom": "WisdomTree Enhanced Commodity",                "capa": "Macro Hard Assets"},
    {"ticker": "GLDM",   "nom": "SPDR Gold MiniShares (GLDM)",                  "capa": "Macro Hard Assets"},
    {"ticker": "ZGLD.SW","nom": "21Shares Physical Gold (ZGLD)",                "capa": "Macro Hard Assets"},
    {"ticker": "IBIT",   "nom": "iShares Bitcoin Trust (IBIT)",                 "capa": "Macro Hard Assets"},
    {"ticker": "ABTC.SW", "nom": "21Shares Bitcoin ETP (ABTC.SW)",              "capa": "Macro Hard Assets"},

    # BTC / ETH directes (macro/creixement)
    {"ticker": "BTC-EUR","nom": "Bitcoin Spot",                                 "capa": "Macro / Creixement"},
    {"ticker": "ETH-EUR","nom": "Ethereum Spot",                                "capa": "Macro / Creixement"},

    # FACTORS (Prioritat 2)
    {"ticker": "IWFQ.L", "nom": "iShares Edge MSCI World Quality (IWFQ)",       "capa": "Factors"},
    {"ticker": "IWVL.L", "nom": "iShares Edge MSCI World Value (IWVL)",         "capa": "Factors"},
    {"ticker": "IWMO.L", "nom": "iShares Edge MSCI World Momentum (IWMO)",      "capa": "Factors"},
    {"ticker": "MVOL.L", "nom": "iShares Edge MSCI World Minimum Vol (MVOL)",   "capa": "Factors"},
    
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
    if actiu["capa"] == "Factors":
        return -2.0        
    if "Bitcoin" in actiu["nom"] or "Ethereum" in actiu["nom"]:
        return -4.0
    return -4.0


def processar_actiu(actiu):
    global ULTIMA_ALERTA

    # Saltar ETFs fora d’horari de mercat
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

    # Guardar dades per al dashboard
    DADES_ACTIUS.append({
        "ticker": actiu["ticker"],
        "nom": actiu["nom"],
        "capa": actiu["capa"],
        "preu": preu,
        "variacio": round(variacio, 2),
        "hora": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    })

    
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
    #if ULTIMA_ALERTA:
    #    print(json.dumps({"alerta": ULTIMA_ALERTA}))
    #else:
    #    heartbeat = {
    #        "estat": "OK",
    #        "hora": datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
    #        "missatge": "Sense alertes"
    #    }
    #    print(json.dumps({"heartbeat": heartbeat}))
    # ----------------------------------------------------


    resultat = {}

    # ALERTA
    if ULTIMA_ALERTA:
        resultat["alerta"] = ULTIMA_ALERTA

    # HEARTBEAT
    else:
        resultat["heartbeat"] = {
            "hora": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "missatge": "Sistema operatiu. Sense alertes."
        }

    # SISTEMA
    resultat["sistema"] = {
        "workflow": "sentinella",
        "freq": "cada 30 minuts (7h–17h, dill–div)",
        "estat": "OK",
        "errors": "0",
        "actius_monitoritzats": len(ACTIUS)
    }

    # TAULA D'ACTIUS
    resultat["actius"] = DADES_ACTIUS

    # TIMESTAMP D'ÚLTIMA EXECUCIÓ
    resultat["ultima_execucio"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # SORTIDA JSON FINAL
    print(json.dumps(resultat))





if __name__ == "__main__":
    try:
        main()
    except Exception:
        error_text = "⚠️ Error inesperat al sentinella global:\n" + traceback.format_exc()
        print(error_text)
        enviar_missatge(error_text)
