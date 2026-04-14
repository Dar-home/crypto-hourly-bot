import os
import requests
from datetime import datetime

def generate_sparkline(prices, width=10):
    if not prices or len(prices) < 2:
        return "▁" * width
    recent = prices[-24:]  # ~ultime 24 ore
    min_p, max_p = min(recent), max(recent)
    if max_p == min_p:
        return "▁" * width
    bars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    spark = [bars[min(int((p - min_p) / (max_p - min_p) * 7), 7)] for p in recent]
    step = max(1, len(spark) // width)
    return "".join(spark[::step][:width])

def send_telegram(text, is_alert=False):
    token = os.environ.get("8760975369:AAE_GPD0Q1rl9AZd2VSYpJ6BQLHgcw03sdg")
    chat_id = os.environ.get("256759604")
    if not token or not chat_id:
        raise ValueError("Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
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
        "per_page": 20,
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

    now = datetime.now().strftime("%H:%M CET")
    msg = f"🕒 <b>Report Crypto</b> | {now}\n\n"

    # 🔔 ALERT BTC
    btc = next((c for c in data if c["symbol"] == "btc"), None)
    if btc:
        btc_1h = btc.get("price_change_percentage_1h_in_currency") or 0
        if abs(btc_1h) >= THRESHOLD:
            dir_emoji = "🚀" if btc_1h > 0 else "📉"
            dir_text = "SALE" if btc_1h > 0 else "SCENDE"
            send_telegram(f"🚨 <b>ALERT BTC!</b> {dir_emoji} {dir_text} del <b>{abs(btc_1h):.2f}%</b> in 1h!", is_alert=True)

    # 📊 TOP 20
    msg += f"<b>💰 Top 20</b> ({VS_CURRENCY.upper()} | 1h | 24h | Trend)\n"
    for c in data:
        name = c["name"][:10].ljust(10)
        price = f"{c['current_price']:,.2f}"
        if len(price) > 10: price = price[:10]
        ch1h = c.get("price_change_percentage_1h_in_currency") or 0
        ch24h = c.get("price_change_percentage_24h_in_currency") or 0
        spark = generate_sparkline(c.get("sparkline_in_7d", {}).get("price", []), width=8)
        msg += f"<code>{name} {VS_CURRENCY.upper()}{price:>10} | {ch1h:+4.1f}% | {ch24h:+4.1f}%</code> {spark}\n"

    # 📈 GAINERS / LOSERS
    valid = [c for c in data if c.get("price_change_percentage_24h_in_currency") is not None]
    sorted_24 = sorted(valid, key=lambda x: x["price_change_percentage_24h_in_currency"], reverse=True)

    msg += "\n🏆 <b>Top 3 Gainers (24h)</b>\n"
    for g in sorted_24[:3]:
        msg += f"🟢 {g['name']} ({g['symbol'].upper()}): <b>{g['price_change_percentage_24h_in_currency']:+.2f}%</b>\n"
    msg += "\n📉 <b>Top 3 Losers (24h)</b>\n"
    for l in sorted_24[-3:]:
        msg += f"🔴 {l['name']} ({l['symbol'].upper()}): <b>{l['price_change_percentage_24h_in_currency']:+.2f}%</b>\n"

    send_telegram(msg)
    print("✅ Report inviato")

if __name__ == "__main__":
    main()
