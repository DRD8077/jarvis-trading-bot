import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not WEBHOOK_URL:
    print("Please set TELEGRAM_BOT_TOKEN and WEBHOOK_URL environment variables.")
    exit(1)

resp = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook", json={"url": WEBHOOK_URL})
print(resp.status_code, resp.text)
