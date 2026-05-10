import requests
import json
from datetime import datetime

YF_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def obtenir_dades_quote(ticker):
    """
    Obté dades bàsiques de Yahoo Finance via endpoint 'quote'.
    Aquest endpoint és estable i no bloqueja GitHub Actions.
    """
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
    r = requests.get(url, headers=YF_HEADERS, timeout=10)
    data = r.json()

    try:
        q = data["quoteResponse"]["result"][0]

        return {
            "marge_operatiu": q.get("operatingMargins", None),
            "per_actual": q.get("forwardPE", None),
            "deute_net_ebitda": q.get("enterpriseToEbitda", None),
            "dividend_yield": q.get("dividendYield", None),
            "fcf_yield": q.get("freeCashflow", None),  # pot ser None
            "roic": None  # ROIC no està disponible en aquest endpoint
        }

    except Exception:
        return {
            "marge_operatiu": None,
            "per_actual": None,
            "deute_net_ebitda": None,
            "dividend_yield": None,
            "fcf_yield": None,
            "roic": None
        }


def actualitzar_fonamentals(fundamentals):
    resultat = {}

    for ticker, dades in fundamentals.items():
        print(f"Actualitzant {ticker}...")

        yf = obtenir_dades_quote(ticker)

        # Convertir marges i dividend yield a percentatge si cal
        marge = yf["marge_operatiu"] * 100 if yf["marge_operatiu"] else None
        dividend = yf["dividend_yield"] * 100 if yf["dividend_yield"] else None

        resultat[ticker] = {
            "nom": dades["nom"],
            "roic": yf["roic"],  # no disponible en aquest endpoint
            "marge_operatiu": marge,
            "fcf_yield": yf["fcf_yield"],
            "per_actual": yf["per_actual"],
            "per_hist_mitja": dades.get("per_hist_mitja"),
            "deute_net_ebitda": yf["deute_net_ebitda"],
            "dividend_yield": dividend,
            "actualitzat": datetime.utcnow().strftime("%Y-%m-%d")
        }

    return resultat


if __name__ == "__main__":
    with open("fundamentals.json") as f:
        fundamentals = json.load(f)

    actualitzat = actualitzar_fonamentals(fundamentals)

    with open("fundamentals.json", "w") as f:
        json.dump(actualitzat, f, indent=2)

    print("✔ Fonamentals actualitzats correctament.")
