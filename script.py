import os
import requests
from datetime import datetime

def generate_sparkline(prices, width=10):
    if not prices or len(prices) < 2:
        return "▁" * width
    recent = prices[-24:]
    min_p, max_p = min(recent), max(recent)
    if max_p == min_p:
        return "▁" * width
    bars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    spark = [bars[min(int((p - min_p) / (max_p - min_p) * 7), 7)] for p in recent]
    step = max(1, len(spark) // width)
    return "".join(spark[::step][:width])

def safe_float(value, default=0.0):
    """Gestisce correttamente i null/None restituiti da CoinGecko"""
    return float(value) if value is not None else default

def send_telegram(text, is_alert=False):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise ValueError("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # 🛡️ Anti-cache: aggiunge carattere invisibile + timestamp ms per forzare messaggio "nuovo"
    unique_marker = f"\u200B{int(datetime.now().timestamp() * 1000)}"
    payload = {
        "chat_id": chat_id,
        "text": text + unique_marker,
        "parse_mode": "HTML"
    }
    if is_alert:
        payload["disable_notification"] = False
        
    res = requests.post(url, json=payload, timeout=10)
    res.raise_for_status()

def main():
    THRESHOLD = float(os.environ.get("BTC_ALERT_THRESHOLD", "3.0"))
    VS_CURRENCY = os.environ.get("VS_CURRENCY", "eur")
    
    URL = "https://api.coingecko.com/api/v3/coins/markets"
    PARAMS = {
        "vs_currency": VS_CURRENCY,
        "order": "market_cap_desc",
        "per_page": 30,  # Prendiamo 30 per avere margine per le sezioni performer
        "page": 1,
        "sparkline": True
    }

    try:
        res = requests.get(URL, params=PARAMS, timeout=15)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        send_telegram(f"❌ <b>Errore API</b>\n{str(e)}")
        print(f"❌ Errore: {e}")
        return

    now = datetime.now().strftime("%H:%M:%S CET")
    data_fetched = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    msg = f"🕒 <b>Report Crypto</b> | {now}\n"
    msg += f"<i>📡 Dati fetchati alle: {data_fetched}</i>\n\n"

    # 🔔 ALERT BTC (se presente nelle top 30)
    btc = next((c for c in data if c["symbol"] == "btc"), None)
    if btc:
        btc_1h = safe_float(btc.get("price_change_percentage_1h_in_currency"))
        if abs(btc_1h) >= THRESHOLD:
            dir_emoji = "🚀" if btc_1h > 0 else "📉"
            dir_text = "SALE" if btc_1h > 0 else "SCENDE"
            send_telegram(f"🚨 <b>ALERT BTC!</b> {dir_emoji} {dir_text} del <b>{abs(btc_1h):.2f}%</b> in 
