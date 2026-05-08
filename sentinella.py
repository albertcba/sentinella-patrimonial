import requests
import traceback
from datetime import datetime
import os
import json
import math

DADES_ACTIUS = []

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive"
}


# ---------------------------------------------------------
#   FONAMENTALS — SINGLE STOCK SENTINELLA
# ---------------------------------------------------------

with open("fundamentals.json") as f:
    FUNDAMENTALS_SINGLE_STOCK = json.load(f)

# ---------------------------------------------------------
#   MACRO ENGINE — FRED API
# ---------------------------------------------------------

def obtenir_fred_robust(series_id, dies=7):
    """Retorna una llista de valors numèrics recents d'una sèrie FRED."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": os.getenv("FRED_API_KEY"),
        "file_type": "json",
        "sort_order": "desc",
        "limit": 10   # agafem més punts per seguretat
    }

    r = requests.get(url, params=params, timeout=20)
    data = r.json()["observations"]

    valors = []
    for obs in data:
        v = obs["value"]
        try:
            valors.append(float(v))
        except:
            continue  # ignora valors "." o no numèrics

    if len(valors) < 2:
        raise ValueError(f"No hi ha prou dades vàlides per {series_id}")

    return valors[:dies]  # retornem els més recents

def tendencia_robusta(valors):
    """Calcula tendència robusta amb mitjanes mòbils."""
    if len(valors) < 6:
        return 0  # no hi ha prou dades

    recent = sum(valors[:3]) / 3
    passat = sum(valors[3:6]) / 3

    canvi = (recent - passat) / passat * 100

    if canvi > 2:
        return -1   # vermell (tendeix a pujar)
    if canvi < -2:
        return +1   # verd (tendeix a baixar)
    return 0        # groc

def obtenir_macro():
    try:
        tga_vals = obtenir_fred_robust("WTREGEN")
        fed_vals = obtenir_fred_robust("WALCL")
        tr_vals  = obtenir_fred_robust("DFII10")

        return {
            "tga": tendencia_robusta(tga_vals),
            "fed_balance": tendencia_robusta(fed_vals),
            "tipus_reals": tendencia_robusta(tr_vals)
        }

    except Exception as e:
        print("⚠️ Error robust Macro Engine:", e)
        return {"tga": 0, "fed_balance": 0, "tipus_reals": 0}



# --- MACRO REAL (ja no és placeholder)
MACRO = obtenir_macro()
# print("DEBUG MACRO:", MACRO)


# ---------------------------------------------------------
#   SENSIBILITAT MACRO PER ACTIU
# ---------------------------------------------------------

with open("sensibilitat_macro.json") as f:
    SENSIBILITAT_MACRO = json.load(f)

# ---------------------------------------------------------
#   FUNCIONS EXISTENTS
# ---------------------------------------------------------

def es_cripto(actiu):
    return actiu["ticker"] in ["BTC-EUR", "ETH-EUR"]

def mercat_obert():
    hora = datetime.utcnow().hour
    return 7 <= hora <= 20

def calcular_dte(expiry):
    avui = datetime.utcnow().date()
    venc = datetime.strptime(expiry, "%Y-%m-%d").date()
    return (venc - avui).days

def distancia_assignacio(preu, strike):
    return strike - preu

def marge_cash_secured(strike):
    return strike * 100

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

# 🔥 AQUI VA EL JSON, A NIVELL SUPERIOR
with open("actius.json") as f:
    ACTIUS = json.load(f)


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

def semafor_put(preu_subjacent, prima, dte, dist):
    # Preu subjacient
    if preu_subjacent > 40:
        s_preu = "🟢"
    elif 37.8 <= preu_subjacent <= 40:
        s_preu = "🟡"
    else:
        s_preu = "🔴"

    # Prima
    if prima < 2.20:
        s_prima = "🟢"
    elif 2.20 <= prima <= 2.50:
        s_prima = "🟡"
    else:
        s_prima = "🔴"

    # DTE
    if dte >= 3:
        s_dte = "🟢"
    elif 1 <= dte < 3:
        s_dte = "🟡"
    else:
        s_dte = "🔴"

    # Distància assignació
    if dist > 3:
        s_dist = "🟢"
    elif 1 <= dist <= 3:
        s_dist = "🟡"
    else:
        s_dist = "🔴"

    return {
        "preu": s_preu,
        "prima": s_prima,
        "dte": s_dte,
        "dist": s_dist
    }


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

def obtenir_dades_chart_yahoo(ticker, dies_hist=90):
    """
    Retorna llista de preus de tancament per al ticker, usant l'API /v8/finance/chart.
    Controla casos on Yahoo retorna result=None o error.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "range": f"{dies_hist}d",
        "interval": "1d"
    }

    r = requests.get(url, headers=YAHOO_HEADERS, params=params, timeout=15)
    data = r.json()

    # 1) Comprovar si hi ha error explícit
    if data.get("chart", {}).get("error"):
        err = data["chart"]["error"]
        raise ValueError(f"Yahoo Chart error per {ticker}: {err.get('description')}")

    # 2) Comprovar si hi ha resultats
    result = data.get("chart", {}).get("result")
    if not result:
        raise ValueError(f"No s'han pogut obtenir dades de chart per {ticker}")

    chart = result[0]

    # 3) Comprovar que indicators existeix
    indicators = chart.get("indicators", {})
    if "quote" not in indicators or not indicators["quote"]:
        raise ValueError(f"Yahoo no retorna quotes per {ticker}")

    closes = indicators["quote"][0].get("close")
    if not closes:
        raise ValueError(f"Yahoo no retorna preus de tancament per {ticker}")

    # 4) Filtrar possibles None
    closes = [c for c in closes if c is not None]
    if len(closes) < 10:
        raise ValueError(f"No hi ha prou dades històriques per {ticker}")

    return closes

def calcular_volatilitat_hist(closes):
    """
    Volatilitat històrica anualitzada a partir de preus de tancament diaris.
    """
    if len(closes) < 2:
        raise ValueError("No hi ha prou dades per calcular volatilitat")

    returns = []
    for i in range(1, len(closes)):
        if closes[i-1] > 0 and closes[i] > 0:
            r = math.log(closes[i] / closes[i-1])
            returns.append(r)

    if len(returns) == 0:
        raise ValueError("No s'han pogut calcular retorns")

    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    sigma_daily = math.sqrt(var)
    sigma_annual = sigma_daily * math.sqrt(252)

    return sigma_annual


def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def calcular_put_black_scholes(S, K, T, r, sigma):
    """
    Preu teòric d'un PUT europeu via Black–Scholes.
    S: preu subjacient
    K: strike
    T: temps en anys
    r: tipus d'interès (p.ex. 0.04)
    sigma: volatilitat anualitzada
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return None

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    put_price = K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)
    return put_price


def obtenir_put_synthetic(subjacent, strike, expiry_str, dies_hist=90, tipus_interes=0.04):
    """
    Calcula una prima de PUT sintètica a partir de dades de /chart/.
    subjacent: ticker del subjacient (p.ex. 'WTRG')
    strike: strike del PUT (p.ex. 40)
    expiry_str: data de venciment en format 'YYYY-MM-DD'
    """
    # 1) Dades històriques
    closes = obtenir_dades_chart_yahoo(subjacent, dies_hist=dies_hist)
    preu_actual = closes[-1]

    # 2) Volatilitat històrica
    sigma = calcular_volatilitat_hist(closes)

    # 3) Temps fins venciment (en anys)
    avui = datetime.utcnow().date()
    expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
    dies_fins_venciment = (expiry - avui).days
    if dies_fins_venciment <= 0:
        raise ValueError(f"El venciment {expiry_str} ja ha passat o és avui")

    T = dies_fins_venciment / 365.0

    # 4) Preu PUT sintètic
    put_price = calcular_put_black_scholes(
        S=preu_actual,
        K=strike,
        T=T,
        r=tipus_interes,
        sigma=sigma
    )

    if put_price is None:
        raise ValueError("No s'ha pogut calcular el preu sintètic del PUT")

    # Retorn estil “put” perquè el Sentinella el pugui consumir
    return {
        "synthetic": True,
        "underlying": subjacent,
        "strike": strike,
        "expiry": expiry_str,
        "lastPrice": put_price,
        "underlyingPrice": preu_actual,
        "histVol": sigma,
        "daysToExpiry": dies_fins_venciment
    }



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
    if actiu["capa"] == "Core equity premium":
        return -2.5        
    return -4.0


def processar_actiu(actiu):
    global ULTIMA_ALERTA

    # 1) Saltar actius de Macro Hard Assets si el mercat està tancat
    if actiu["capa"] == "Macro Hard Assets" and not mercat_obert():
        print(f"Saltant {actiu['ticker']} (mercat tancat)")
        return

    # Determinar subjacent real
    if actiu["capa"] == "Options":
        ticker = actiu["underlying"]
    else:
        ticker = actiu["ticker"]
    print(f"Processant {ticker}...")

    # 2) Obtenir preu i variació
    try:
        preu, variacio = obtenir_variacio_yahoo(ticker)
    except Exception as e:
        txt = f"⚠️ Error obtenint dades per {actiu['nom']} ({ticker}):\n{e}"
        print(txt)
        enviar_missatge(txt)
        return

    print(f"{ticker}: {variacio:.2f}%  preu={preu}")
    
    if actiu["capa"] == "Options":
        subjacent = actiu["underlying"]   # <-- CORRECCIÓ
        strike = actiu["strike"]
        expiry = actiu["expiry"]

        # Normalitzar guions tipogràfics
        expiry_str = (
            expiry_str.replace("‑", "-")   # non-breaking hyphen
                       .replace("–", "-")  # en-dash
                       .replace("—", "-")  # em-dash
        )
        
        expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()

        
        # 1) Llegir PUT sintètic
        try:
            put = obtenir_put_synthetic(subjacent, strike, expiry)
        except Exception as e:
            txt = f"⚠️ Error obtenint PUT {strike} per {subjacent}:\n{e}"
            print(txt)
            enviar_missatge(txt)
            return
    
        # --- CAMPOS SINTÈTICS CORRECTES ---
        prima = put["lastPrice"]
        preu_subjacent = put["underlyingPrice"]
        vol_hist = put["histVol"]
        dte = put["daysToExpiry"]
    
        # --- CÀLCULS ADDICIONALS ---
        dist = distancia_assignacio(preu_subjacent, strike)
        marge = marge_cash_secured(strike)
        semafor = semafor_put(preu_subjacent, prima, dte, dist)
    
        # --- JSON FINAL ---
        DADES_ACTIUS.append({
            "ticker": ticker,
            "nom": actiu["nom"],
            "capa": actiu["capa"],
            "preu_subjacent": preu_subjacent,
            "prima": prima,
            "dte": dte,
            "distancia": dist,
            "marge": marge,
            "vol_hist": vol_hist,     # <-- substitueix iv
            "oi": None,               # <-- synthetic no té OI
            "vol": None,              # <-- synthetic no té volum d’opcions
            "semafor": semafor,
            "hora": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        })
    
        # ALERTES
        if prima > 2.50 or preu_subjacent < strike:
            enviar_missatge(
                f"⚠️ ALERTA PUT {subjacent} {strike}\n"
                f"Prima: {prima:.2f}\n"
                f"Preu subjacent: {preu_subjacent:.2f}\n"
                f"DTE: {dte}\n"
                f"Distància assignació: {dist}\n"
                f"Semàfor: {semafor}"
            )
    
        return
 
    # 3) Fonamentals (si existeixen)
    fundamentals = FUNDAMENTALS_SINGLE_STOCK.get(ticker)

    # 4) Rolling window de 7 preus (AUTOMÀTIC I ANTIFRÀGIL)
    preus_7d = actiu.get("preus_7d", [])   # recuperar si existeix
    preus_7d.append(preu)                 # afegir preu actual
    preus_7d = preus_7d[-7:]              # mantenir només els últims 7

    # 5) Afegir l'actiu processat al JSON final
    DADES_ACTIUS.append({
        "ticker": ticker,
        "nom": actiu["nom"],
        "capa": actiu["capa"],
        "preu": preu,
        "variacio": round(variacio, 2),
        "hora": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "semafor_macro": semafor_macro_actiu(actiu, MACRO),
        "fundamentals": fundamentals,
        "preus_7d": preus_7d
    })

    # 6) Alertes
    llindar = llindar_variacio(actiu)

    if variacio <= llindar:
        missatge = format_missatge(actiu, preu, variacio)
        enviar_missatge(missatge)

        ULTIMA_ALERTA = {
            "actiu": actiu["nom"],
            "ticker": ticker,
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
    # print("DEBUG MACRO:", MACRO)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        error_text = "⚠️ Error inesperat al sentinella global:\n" + traceback.format_exc()
        print(error_text)
        enviar_missatge(error_text)
