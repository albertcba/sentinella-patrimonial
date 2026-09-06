import requests
import os
from datetime import datetime
import json

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

# ---------------------------------------------------------
#   FONAMENTALS — SINGLE STOCK SENTINELLA
# ---------------------------------------------------------

with open("actius.json") as f:
    ACTIUS = json.load(f)

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
