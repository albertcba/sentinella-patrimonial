import requests
import os
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_missatge(text):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Falta TOKEN o CHAT_ID")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("⚠️ Error enviant missatge:", e)


# ───────────────────────────────────────────────
#   UNIVERS D’ACTIUS (mateix que sentinella.py)
# ───────────────────────────────────────────────

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
    {"ticker": "ABTC.SW","nom": "21Shares Bitcoin ETP (ABTC.SW)",   "capa": "Macro Hard Assets"},

    {"ticker": "BTC-EUR","nom": "Bitcoin Spot",                     "capa": "Macro / Creixement"},
    {"ticker": "ETH-EUR","nom": "Ethereum Spot",                    "capa": "Macro / Creixement"},

    {"ticker": "IWFQ.L", "nom": "iShares MSCI World Quality",       "capa": "Factors"},
    {"ticker": "IWVL.L", "nom": "iShares MSCI World Value",         "capa": "Factors"},
    {"ticker": "IWMO.L", "nom": "iShares MSCI World Momentum",      "capa": "Factors"},
    {"ticker": "MVOL.L", "nom": "iShares MSCI World Min Vol",       "capa": "Factors"},
]


# ───────────────────────────────────────────────
#   OBTENIR VARIACIÓ VIA YAHOO FINANCE
# ───────────────────────────────────────────────

def obtenir_variacio(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=15)
    data = r.json()

    # Validacions robustes
    if "chart" not in data or data["chart"]["result"] is None:
        raise ValueError(f"Yahoo no retorna dades per {ticker}")

    result = data["chart"]["result"][0]
    meta = result.get("meta")

    if not meta:
        raise ValueError(f"Meta buida per {ticker}")

    preu = meta.get("regularMarketPrice")
    obertura = meta.get("chartPreviousClose")

    if preu is None or obertura is None:
        raise ValueError(f"Preu o obertura no disponibles per {ticker}")

    variacio = ((preu - obertura) / obertura) * 100
    return preu, variacio

# ───────────────────────────────────────────────
#   MAIN
# ───────────────────────────────────────────────

def main():
    resultats = []

    for actiu in ACTIUS:
        try:
            preu, var = obtenir_variacio(actiu["ticker"])
            resultats.append({
                "nom": actiu["nom"],
                "capa": actiu["capa"],
                "var": var,
                "preu": preu
            })
        except Exception as e:
            print(f"⚠️ Error amb {actiu['nom']} ({actiu['ticker']}): {e}")

    if not resultats:
        enviar_missatge("⚠️ No s'han pogut obtenir dades per cap actiu.")
        return

    pujades = sorted(resultats, key=lambda x: x["var"], reverse=True)[:5]
    caigudes = sorted(resultats, key=lambda x: x["var"])[:5]

    missatge = "📊 *Resum diari — Tancament EUA*\n"
    missatge += f"Data: {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"

    missatge += "🔺 *Top pujades*\n"
    for r in pujades:
        missatge += f"{r['nom']} ({r['capa']}): +{r['var']:.2f}% — {r['preu']}\n"

    missatge += "\n🔻 *Top caigudes*\n"
    for r in caigudes:
        missatge += f"{r['nom']} ({r['capa']}): {r['var']:.2f}% — {r['preu']}\n"

    enviar_missatge(missatge)


if __name__ == "__main__":
    main()
