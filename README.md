# 🤖 Crypto Hourly Bot
Bot Telegram gratuito che invia ogni ora:
- 📊 Top 20 crypto con variazione 1h/24h e sparkline
- 🏆 Top 3 gainers & losers
- 🚨 Alert immediato se BTC varia > X% in 1h

## 🚀 Setup in 3 minuti
1. Crea un bot Telegram con `@BotFather` e ottieni il `TOKEN`
2. Avvia il bot e cerca il tuo `CHAT_ID` su `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Vai su GitHub → `Settings` → `Secrets and variables` → `Actions` → aggiungi:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `BTC_ALERT_THRESHOLD` (es. `3` per alert se BTC >3% in 1h)
   - `VS_CURRENCY` (opzionale, default `eur`)
4. Clicca su `Actions` → `Run workflow` per testare

⏰ Il cron scatta ogni ora UTC. Il timestamp mostra l'ora italiana (CET/CEST).
🆓 100% gratuito via GitHub Actions (2000 min/mese).
