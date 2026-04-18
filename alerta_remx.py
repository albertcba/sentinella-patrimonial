import requests
import json
import traceback

TOKEN = "8762688063:AAG2OUa9yiFOh3Rf-66aKr5rM1r1IkUqIT0"
CHAT_ID = "460087168"

def enviar_missatge(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("Error enviant missatge:", e)

def obtenir_preu_remx():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/REMX"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        result = data["chart"]["result"][0]
        preu_actual = result["meta"]["regularMarketPrice"]
        preu_obertura = result["meta"]["chartPreviousClose"]
        variacio = ((preu_actual - preu_obertura) / preu_obertura) * 100

        return preu_actual, variacio

    except Exception as e:
        error_text = f"⚠️ Error obtenint dades REMX:\n{e}"
        print(error_text)
        enviar_missatge(error_text)
        return None, None


def main():
    preu, variacio = obtenir_preu_remx()

    if preu is None:
        return  # ja hem enviat alerta d’error

    # Aquí poses la condició real
    # if variacio <= -4:
    if True:
        enviar_missatge(
            f"📡 ALERTA REMX\nVariació: {variacio:.2f}%\nPreu actual: {preu}\nCapa: Macro Hard Assets\nEntrada potencial segons playbook."
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        enviar_missatge("⚠️ Error inesperat al sentinella REMX:\n" + traceback.format_exc())
        print("Error inesperat:", e)
