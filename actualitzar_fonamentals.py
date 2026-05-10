import requests
import json
from datetime import datetime
import re

YF_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# ---------------------------------------------------------
# 1) OBTENIR FONAMENTALS DES DE YAHOO FINANCE
# ---------------------------------------------------------

def obtenir_yahoo_key_stats(ticker):
    """
    Retorna un diccionari amb:
    - marge_operatiu (%)
    - per_actual
    - deute_net_ebitda
    - dividend_yield (%)
    """
    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=defaultKeyStatistics,financialData"
    r = requests.get(url, headers=YF_HEADERS, timeout=10)
    data = r.json()

    try:
        ks = data["quoteSummary"]["result"][0]["defaultKeyStatistics"]
        fd = data["quoteSummary"]["result"][0]["financialData"]

        marge_operatiu = fd.get("operatingMargins", {}).get("raw", None)
        per_actual = ks.get("forwardPE", {}).get("raw", None)
        deute_net_ebitda = ks.get("enterpriseToEbitda", {}).get("raw", None)
        dividend_yield = ks.get("dividendYield", {}).get("raw", None)

        if marge_operatiu is not None:
            marge_operatiu *= 100
        if dividend_yield is not None:
            dividend_yield *= 100

        return {
            "marge_operatiu": marge_operatiu,
            "per_actual": per_actual,
            "deute_net_ebitda": deute_net_ebitda,
            "dividend_yield": dividend_yield
        }

    except Exception:
        return {
            "marge_operatiu": None,
            "per_actual": None,
            "deute_net_ebitda": None,
            "dividend_yield": None
        }


# ---------------------------------------------------------
# 2) OBTENIR ROIC I FCF YIELD DES DE MACROTRENDS
# ---------------------------------------------------------

def obtenir_macrotrends_metric(url, pattern):
    r = requests.get(url, headers=YF_HEADERS, timeout=10)
    html = r.text
    match = re.search(pattern, html)
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None


def obtenir_roic_macrotrends(ticker):
    url = f"https://www.macrotrends.net/stocks/charts/{ticker}/x/roic"
    return obtenir_macrotrends_metric(url, r"ROIC</td><td.*?>(-?\d+\.\d+)")


def obtenir_fcf_yield_macrotrends(ticker):
    url = f"https://www.macrotrends.net/stocks/charts/{ticker}/x/free-cash-flow-yield"
    return obtenir_macrotrends_metric(url, r"Free Cash Flow Yield</td><td.*?>(-?\d+\.\d+)")


# ---------------------------------------------------------
# 3) FUNCIÓ PRINCIPAL D’ACTUALITZACIÓ
# ---------------------------------------------------------

def actualitzar_fonamentals(fundamentals):
    resultat = {}

    for ticker, dades in fundamentals.items():
        print(f"Actualitzant {ticker}...")

        yf = obtenir_yahoo_key_stats(ticker)
        roic = obtenir_roic_macrotrends(ticker)
        fcf_yield = obtenir_fcf_yield_macrotrends(ticker)

        resultat[ticker] = {
            "nom": dades["nom"],
            "roic": roic,
            "marge_operatiu": yf["marge_operatiu"],
            "fcf_yield": fcf_yield,
            "per_actual": yf["per_actual"],
            "per_hist_mitja": dades.get("per_hist_mitja"),
            "deute_net_ebitda": yf["deute_net_ebitda"],
            "dividend_yield": yf["dividend_yield"],
            "actualitzat": datetime.utcnow().strftime("%Y-%m-%d")
        }

    return resultat


# ---------------------------------------------------------
# 4) EXECUCIÓ DIRECTA (opcional)
# ---------------------------------------------------------

if __name__ == "__main__":
    with open("fundamentals.json") as f:
        fundamentals = json.load(f)

    actualitzat = actualitzar_fonamentals(fundamentals)

    with open("fundamentals.json", "w") as f:
        json.dump(actualitzat, f, indent=2)

    print("✔ Fonamentals actualitzats correctament.")
