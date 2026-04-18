import requests

TOKEN = "8762688063:AAG2OUa9yiFOh3Rf-66aKr5rM1r1IkUqIT0"
CHAT_ID = "460087168"

def enviar_missatge(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
    requests.get(url, params=params)

def obtenir_preu_remx():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/REMX"
    headers = {"User-Agent": "Mozilla/5.0"}
    data = requests.get(url, headers=headers).json()
    result = data["chart"]["result"][0]
    preu_actual = result["meta"]["regularMarketPrice"]
    preu_obertura = result["meta"]["chartPreviousClose"]
    variacio = ((preu_actual - preu_obertura) / preu_obertura) * 100
    return preu_actual, variacio


def main():
    preu, variacio = obtenir_preu_remx()

#    if variacio <= -4:
    if True:
        enviar_missatge(
            f"ALERTA REMX\nVariació: {variacio:.2f}%\nPreu actual: {preu}\nCapa: Macro Hard Assets\nEntrada potencial segons playbook."
        )

if __name__ == "__main__":
    main()
