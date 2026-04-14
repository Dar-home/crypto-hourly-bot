import os
import random
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
    return float(value) if value is not None else default

def send_telegram(text, is_alert=False):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise ValueError("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 🆔 ID univoco VISIBILE all'inizio (mai troncato)
    run_id = f"{datetime.now().strftime('%H%M%S')}{random.randint(100,999)}"
    header = f"🆔 <code>{run_id}</code> | {datetime.now().strftime('%H:%M:%S')} CET\n\n"
    
    payload = {
        "chat_id": chat_id,
        "text": header + text,  # ✅ ID all'inizio = sempre visibile
        "parse_mode": "HTML"
    }
    if is_alert:
        payload["disable_notification"] = False
        
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code != 200:
        print(f"❌ Errore Telegram: {res.text}")
    res.raise_for_status()

def main():
    THRESHOLD = float(os.environ.get("BTC_ALERT_THRESHOLD", "3.0"))
    VS_CURRENCY = os.environ.get("VS_CURRENCY", "eur")
    
    URL = "https://api.coingecko.com/api/v3/coins/markets"
    PARAMS = {
        "vs_currency": VS_CURRENCY,
        "order": "market_cap_desc",
        "per_page": 30,
        "page": 1,
        "sparkline": True
    }

    try:
        res = requests.get(URL, params=PARAMS, timeout=15)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        send_telegram(f"❌ Errore API: {str(e)}")
        print(f"❌ Errore: {e}")
        return

    now = datetime.now().strftime("%H:%M:%S CET")
    data_fetched = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Costruiamo il messaggio in modo compatto per evitare truncation
    msg = f"🕒 Report Crypto | {now}\n"
    msg += f"📡 Dati: {data_fetched}\n\n"

    # 🔔 ALERT BTC
    btc = next((c for c in data if c["symbol"] == "btc"), None)
    if btc:
        btc_1h = safe_float(btc.get("price_change_percentage_1h_in_currency"))
        if abs(btc_1h) >= THRESHOLD:
            dir_emoji = "🚀" if btc_1h > 0 else "📉"
            dir_text = "SALE" if btc_1h > 0 else "SCENDE"
            send_telegram(f"🚨 ALERT BTC! {dir_emoji} {dir_text} del {abs(btc_1h):.2f}% in 1h!", is_alert=True)

    # 📊 TOP 20 (formato compatto)
    msg += "💰 Top 20\n"
    for c in data[:20]:
        name = c["name"][:10]
        price = f"{c['current_price']:,.0f}" if c['current_price'] >= 1 else f"{c['current_price']:.4f}"
        ch1h = safe_float(c.get("price_change_percentage_1h_in_currency"))
        ch24h = safe_float(c.get("price_change_percentage_24h_in_currency"))
        spark = generate_sparkline(c.get("sparkline_in_7d", {}).get("price", []), width=6)
        msg += f"<b>{name}</b> {price} {ch1h:+.1f}% {spark}\n"

    # 🔥 Top Performers 1h
    with_1h = [c for c in data if c.get("price_change_percentage_1h_in_currency") is not None]
    sorted_1h = sorted(with_1h, key=lambda x: safe_float(x.get("price_change_percentage_1h_in_currency")), reverse=True)
    
    msg += "\n🔥 Top 3 (1h)\n"
    for c in sorted_1h[:3]:
        ch = safe_float(c.get("price_change_percentage_1h_in_currency"))
        msg += f"🟢 <b>{c['name']}</b> {ch:+.2f}%\n"
        
    msg += "\n📉 Worst 3 (1h)\n"
    for c in sorted_1h[-3:]:
        ch = safe_float(c.get("price_change_percentage_1h_in_currency"))
        msg += f"🔴 <b>{c['name']}</b> {ch:+.2f}%\n"

    send_telegram(msg)
    print(f"✅ Report inviato | ID: {datetime.now().strftime('%H%M%S')}XXX")

if __name__ == "__main__":
    main()
