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
    
    # 🛡️ Anti-cache Telegram: ID univoco visibile + timestamp ms
    run_id = f"{datetime.now().strftime('%H%M%S')}{random.randint(100,999)}"
    footer = f"\n\n<i>🆔 {run_id} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET</i>"
    
    payload = {
        "chat_id": chat_id,
        "text": text + footer,
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
        "per_page": 30,
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
    msg += f"<i>📡 Dati fetchati: {data_fetched}</i>\n\n"

    # 🔔 ALERT BTC
    btc = next((c for c in data if c["symbol"] == "btc"), None)
    if btc:
        btc_1h = safe_float(btc.get("price_change_percentage_1h_in_currency"))
        if abs(btc_1h) >= THRESHOLD:
            dir_emoji = "🚀" if btc_1h > 0 else "📉"
            dir_text = "SALE" if btc_1h > 0 else "SCENDE"
            send_telegram(f"🚨 <b>ALERT BTC!</b> {dir_emoji} {dir_text} del <b>{abs(btc_1h):.2f}%</b> in 1h!", is_alert=True)

    # 📊 TOP 20
    msg += f"<b>💰 Top 20</b> ({VS_CURRENCY.upper()} | 1h | 24h | Trend)\n"
    for c in data[:20]:
        name = c["name"][:12]
        price_str = f"{c['current_price']:,.2f}"
        ch1h = safe_float(c.get("price_change_percentage_1h_in_currency"))
        ch24h = safe_float(c.get("price_change_percentage_24h_in_currency"))
        spark = generate_sparkline(c.get("sparkline_in_7d", {}).get("price", []), width=8)
        msg += f"<code><b>{name}</b> {VS_CURRENCY.upper()}{price_str:>10} | {ch1h:+4.1f}% | {ch24h:+4.1f}%</code> {spark}\n"

    # 🔥 Top Performers 1h
    with_1h_data = [c for c in data if c.get("price_change_percentage_1h_in_currency") is not None]
    sorted_by_1h = sorted(with_1h_data, key=lambda x: safe_float(x.get("price_change_percentage_1h_in_currency")), reverse=True)
    
    msg += f"\n🔥 <b>Top 5 Performers (1h)</b>\n"
    for i, c in enumerate(sorted_by_1h[:5], 1):
        ch1h = safe_float(c.get("price_change_percentage_1h_in_currency"))
        msg += f"{i}. <b>{c['name']}</b> ({c['symbol'].upper()}): <b>{ch1h:+.2f}%</b>\n"
        
    msg += f"\n📉 <b>Worst 5 (1h)</b>\n"
    for i, c in enumerate(sorted_by_1h[-5:], 1):
        ch1h = safe_float(c.get("price_change_percentage_1h_in_currency"))
        msg += f"{i}. <b>{c['name']}</b> ({c['symbol'].upper()}): <b>{ch1h:+.2f}%</b>\n"

    # 📈 Gainers / Losers 24h
    valid_24h = [c for c in data[:20] if c.get("price_change_percentage_24h_in_currency") is not None]
    sorted_24h = sorted(valid_24h, key=lambda x: safe_float(x.get("price_change_percentage_24h_in_currency")), reverse=True)

    msg += f"\n🏆 <b>Top 3 Gainers (24h)</b>\n"
    for g in sorted_24h[:3]:
        ch24 = safe_float(g.get("price_change_percentage_24h_in_currency"))
        msg += f"🟢 <b>{g['name']}</b>: <b>{ch24:+.2f}%</b>\n"
        
    msg += f"\n📉 <b>Top 3 Losers (24h)</b>\n"
    for l in sorted_24h[-3:]:
        ch24 = safe_float(l.get("price_change_percentage_24h_in_currency"))
        msg += f"🔴 <b>{l['name']}</b>: <b>{ch24:+.2f}%</b>\n"

    send_telegram(msg)
    print("✅ Report inviato")

if __name__ == "__main__":
    main()
