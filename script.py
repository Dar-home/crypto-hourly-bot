import os
import random
import requests
from datetime import datetime

def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("❌ Mancano i segreti Telegram")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    res = requests.post(url, json=payload, timeout=10)
    print(f"✅ Telegram response: {res.status_code}")

def main():
    # 🎲 Numero casuale che CAMBIA OGNI RUN
    random_id = random.randint(10000, 99999)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    msg = (
        f"🧪 <b>DEBUG BOT</b>\n"
        f"🆔 Run ID: <code>{random_id}</code>\n"
        f"⏰ Timestamp: {timestamp}\n"
        f"🔢 Random: {random_id}\n\n"
        f"✅ Se vedi questo, lo script è aggiornato e funziona!"
    )
    
    print(f"🚀 Invio messaggio | ID: {random_id}")
    send_telegram(msg)

if __name__ == "__main__":
    main()
