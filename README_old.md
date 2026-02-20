# Telegram Option-Chain Bot (Minimal)

This workspace contains a minimal Telegram bot and an NSE option-chain
fetcher. It uses NSE's public JSON APIs (no browser automation) and a
simple rule-based analyzer to produce buy/sell/hold signals.

Files:
- `stock_data_fetcher.py`: fetches and analyzes NSE option chain data.
- `telegram_bot.py`: a lightweight Telegram bot (long-polling) that uses the fetcher and can send QR codes.
- `requirements.txt`: Python dependencies.

Quick start:

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Set your Telegram bot token as an environment variable:

```bash
export TELEGRAM_BOT_TOKEN="<your-token-here>"
```

3. Run the bot:

```bash
python3 telegram_bot.py
```

Usage:
- Send `/start` to the bot to see available commands.
- Type a symbol (e.g., `RELIANCE`) to fetch signals for that symbol.
- Use `Start Auto Updates` to get signals every 2 minutes (auto stops when you send `Stop Auto Updates`).

Notes:
- This is a starting point. The analyzer is rule-based and intended
  to be replaced with a trained ML model later.
- For production use, migrate to webhooks, use a persistent datastore
  for settings, and add robust error handling.
