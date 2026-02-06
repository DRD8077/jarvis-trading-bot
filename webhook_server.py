from fastapi import FastAPI, Request, HTTPException
import os
import asyncio

from telegram_bot import handle_update

app = FastAPI()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if not TELEGRAM_TOKEN or token != TELEGRAM_TOKEN.split(":")[0]:
        # token mismatch - simple protection (uses bot id prefix)
        raise HTTPException(status_code=403, detail="Forbidden")
    body = await request.json()
    # handle_update is synchronous; run in default loop executor
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, handle_update, body)
    return {"ok": True}
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
import asyncio

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your bot token
TELEGRAM_BOT_TOKEN = "7897330325:AAF0opOkFdu0AiZk-tGAF_oGPrY5KMzjazE"

# Flask app setup
app = Flask(__name__)

# Telegram bot setup
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Define the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_message = f"HAR HAR MAHADEV {user_name} Ji WELCOME TO DEEPAK BOSS FAMILY!"
    await update.message.reply_text(welcome_message)

# Add command handlers
application.add_handler(CommandHandler("start", start))

# Webhook route
@app.route(f"/telegram-webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
        return "OK"

if __name__ == "__main__":
    from pyngrok import ngrok

    # Expose the Flask app to the internet using ngrok
    public_url = "https://a857-20-192-21-49.ngrok-free.app"
    logger.info(f"Ngrok tunnel URL: {public_url}")

    # Set the webhook for Telegram bot
    asyncio.run(application.bot.set_webhook(url=f"{public_url}/telegram-webhook"))

    # Run the Flask app
    app.run(port=5000)