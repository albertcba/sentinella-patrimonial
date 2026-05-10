import requests
import json
from datetime import datetime

def obtenir_dades_spark(ticker):
    url = f"https://query1.finance.yahoo.com/v7/finance/spark?symbols={ticker}&range=1d&interval=1d"

    try:
        r = requests.get(url, timeout=10)

        # Si la resposta no és JSON, retornem dades buides
        try:
            data = r.json()
        except:
            print(f"⚠ Yahoo no ha retornat JSON per {ticker}")
            return {
                "preu": None,
                "variacio_pct": None
            }

        # Parse normal
        q = data["spark"]["result"][0]
        close = q["response"][0]["close"]

        return {
            "preu": close[-1],
            "variacio_pct": (close[-1] / close[0] - 1) if close[0] else None
        }

    except Exception as e:
        print(f"⚠ Error obtenint dades per {ticker}: {e}")
        return {
            "preu": None,
            "variacio_pct": None
        }

def actualitzar_fonamentals(fundamentals):
    resultat = {}

    for ticker, dades in fundamentals.items():
        print(f"Actualitzant {ticker}...")

        info = obtenir_dades_spark(ticker)

        resultat[ticker] = {
            **dades,  # mantenim els fonamentals existents
            "preu_actual": info["preu"],
            "variacio_pct": info["variacio_pct"],
            "actualitzat": datetime.utcnow().strftime("%Y-%m-%d"),
            "nota": "Actualització parcial basada en Yahoo Spark (no inclou fonamentals complets)"
        }

    return resultat

if __name__ == "__main__":
    with open("fundamentals.json") as f:
        fundamentals = json.load(f)

    actualitzat = actualitzar_fonamentals(fundamentals)

    with open("fundamentals.json", "w") as f:
        json.dump(actualitzat, f, indent=2)

    print("✔ Actualització sintètica completada.")
