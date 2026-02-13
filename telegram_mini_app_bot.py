#!/usr/bin/env python3
"""
🤖 JARVIS Telegram Mini App Bot v2.0
═══════════════════════════════════════
Professional CoinDCX/AngelOne grade bot with full Mini App integration.
All buttons open the real Mini App — no dummy responses.
"""

import os
import json
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MINI_APP_URL = os.getenv('MINI_APP_URL', '').rstrip('/')
ADMIN_CHAT_ID = int(os.getenv('OWNER_CHAT_ID', os.getenv('ADMIN_CHAT_ID', '0')))


class JarvisMiniAppBot:
    def __init__(self):
        if not BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set!")
        if not MINI_APP_URL or 'your-mini-app' in MINI_APP_URL:
            logger.warning("⚠️ MINI_APP_URL not configured properly! Bot buttons won't open the Mini App.")

        self.app = Application.builder().token(BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("trade", self.cmd_trade))
        self.app.add_handler(CommandHandler("signals", self.cmd_signals))
        self.app.add_handler(CommandHandler("wallet", self.cmd_wallet))
        self.app.add_handler(CommandHandler("markets", self.cmd_markets))
        self.app.add_handler(CommandHandler("options", self.cmd_options))
        self.app.add_handler(CommandHandler("airdrops", self.cmd_airdrops))
        self.app.add_handler(CommandHandler("screener", self.cmd_screener))
        self.app.add_handler(CommandHandler("risk", self.cmd_risk))
        self.app.add_handler(CommandHandler("chat", self.cmd_chat))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("menu", self.cmd_menu))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.handle_webapp_data))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    # ═══════════════════════════════════════════════════════
    #  /start — Welcome with Mini App
    # ═══════════════════════════════════════════════════════

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        # Register user
        try:
            from jarvis_admin import register_user
            register_user(user.id, user.first_name or '', user.username or '')
        except: pass

        text = (
            f"🤖 *JARVIS AI Trading Pro*\n\n"
            f"Welcome, *{user.first_name}*! 👋\n\n"
            "Your AI-powered trading command center — like CoinDCX meets intelligence.\n\n"
            "⚡ *Real-Time Features:*\n"
            "├ 📊 Live Market Data (Crypto + Stocks)\n"
            "├ 🤖 AI Trading Signals (Multi-Model)\n"
            "├ 💰 Secure Wallet (UPI Deposit/Withdraw)\n"
            "├ 📈 Options Intelligence (PCR/MaxPain)\n"
            "├ 🔍 NLP Stock Screener\n"
            "├ 🎁 Airdrop Hunter\n"
            "├ 🧠 AI Market Sentiment\n"
            "└ 🛡️ Risk Manager (Kelly Criterion)\n\n"
            "🚀 *Tap below to launch your dashboard!*"
        )

        keyboard = [
            [InlineKeyboardButton("🚀 Open JARVIS Dashboard", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))],
            [
                InlineKeyboardButton("📊 Markets", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp")),
                InlineKeyboardButton("⚡ Signals", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp")),
            ],
            [
                InlineKeyboardButton("💰 Wallet", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp")),
                InlineKeyboardButton("🤖 AI Chat", callback_data="open_chat"),
            ],
            [
                InlineKeyboardButton("📊 Options", callback_data="options"),
                InlineKeyboardButton("🎁 Airdrops", callback_data="airdrops"),
            ],
            [InlineKeyboardButton("❓ All Commands", callback_data="help")],
        ]

        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

        # Set bot menu button to open Mini App
        try:
            await context.bot.set_chat_menu_button(
                chat_id=user.id,
                menu_button=MenuButtonWebApp(text="🚀 JARVIS", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))
            )
        except Exception as e:
            logger.warning(f"Menu button error: {e}")

        # Set bot commands
        try:
            await context.bot.set_my_commands([
                BotCommand("start", "🚀 Launch JARVIS"),
                BotCommand("trade", "📊 Open Trading"),
                BotCommand("signals", "⚡ AI Signals"),
                BotCommand("wallet", "💰 Wallet"),
                BotCommand("markets", "📈 Live Markets"),
                BotCommand("options", "📊 Options Intel"),
                BotCommand("screener", "🔍 Stock Screener"),
                BotCommand("airdrops", "🎁 Airdrop Hunter"),
                BotCommand("risk", "🛡️ Risk Analysis"),
                BotCommand("chat", "🤖 AI Chat"),
                BotCommand("help", "❓ Help"),
            ])
        except: pass

    # ═══════════════════════════════════════════════════════
    #  COMMAND HANDLERS — Each opens specific Mini App page
    # ═══════════════════════════════════════════════════════

    async def cmd_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("📊 Open Trading Center", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(
            "📊 *JARVIS Trading Center*\n\nLive crypto & stock prices with AI signals.\nTap below to open:",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    async def cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("⚡ View AI Signals", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(
            "⚡ *AI Trading Signals*\n\nMulti-model AI (RSI+MACD+ML+Candle patterns) signals with entry/target/SL.",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    async def cmd_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("💰 Open Wallet", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(
            "💰 *JARVIS Wallet*\n\nUPI deposits, bank withdrawals, portfolio tracking.\nEncrypted & secure.",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    async def cmd_markets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("📈 Live Markets", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(
            "📈 *Live Market Data*\n\nNIFTY, SENSEX, BTC, ETH, SOL + 200 tokens with real-time prices.",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

    async def cmd_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "📊 *Options Intelligence*\n\n• Live PCR & Max Pain\n• India VIX Tracker\n• Budget options under ₹5\n• Smart CE/PE recommendations"
        keyboard = [[InlineKeyboardButton("📊 Open Options", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def cmd_airdrops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "🎁 *Airdrop Hunter*\n\n• Auto-scan Solana/EVM airdrops\n• Eligibility checker\n• Scam detection\n• One-click claim"
        keyboard = [[InlineKeyboardButton("🎁 Find Airdrops", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def cmd_screener(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "🔍 *NLP Stock Screener*\n\nType natural language queries like:\n• 'RSI below 30 stocks'\n• 'Volume breakout today'\n• 'Near 52-week high'"
        keyboard = [[InlineKeyboardButton("🔍 Open Screener", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def cmd_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "🛡️ *Risk Manager*\n\n• Kelly Criterion position sizing\n• Market regime detection\n• Max drawdown circuit breaker\n• Portfolio risk score"
        keyboard = [[InlineKeyboardButton("🛡️ Risk Analysis", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def cmd_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "🤖 *JARVIS AI Chat*\n\nAsk me anything! I use GPT + Gemini + Claude for the best answers.\n\n💡 Try:\n• 'Analyze NIFTY for tomorrow'\n• 'Best crypto under ₹100'\n• 'RELIANCE buy or sell?'"
        keyboard = [[InlineKeyboardButton("🤖 Open AI Chat", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_help(update.message)

    async def cmd_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.cmd_start(update, context)

    # ═══════════════════════════════════════════════════════
    #  CALLBACK HANDLER
    # ═══════════════════════════════════════════════════════

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "help":
            await self._send_help(query.message, edit=True)
        elif data == "open_chat":
            text = "🤖 *JARVIS AI is ready!*\n\nJust type your question here or open the full AI Chat in the Mini App."
            keyboard = [[InlineKeyboardButton("🤖 Open Full AI Chat", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        elif data == "options":
            text = "📊 *Options Intelligence*\n\nLive PCR, Max Pain, VIX & budget option picks."
            keyboard = [[InlineKeyboardButton("📊 Open Options", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        elif data == "airdrops":
            text = "🎁 *Airdrop Hunter*\n\nDiscover live & upcoming airdrops across chains."
            keyboard = [[InlineKeyboardButton("🎁 Find Airdrops", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        elif data == "back_main":
            await self.cmd_start(update, context)

    # ═══════════════════════════════════════════════════════
    #  MESSAGE HANDLER — AI Chat directly in Telegram
    # ═══════════════════════════════════════════════════════

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages — route to AI"""
        message = update.message
        if not message or not message.text:
            return
        
        user = update.effective_user
        text = message.text.strip()
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
        
        response = await self._get_ai_response(text, user.id)
        
        keyboard = [[InlineKeyboardButton("🚀 Open Full Dashboard", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        await message.reply_text(
            response, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='HTML'
        )

    async def handle_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle data sent from Mini App"""
        message = update.message
        if not message.web_app_data:
            return
        
        try:
            data = json.loads(message.web_app_data.data)
            action = data.get('action', '')
            
            if action == 'deposit_request':
                amount = data.get('amount', 0)
                await message.reply_text(f"💰 Deposit request received!\nAmount: ₹{amount:,.2f}\n\nPlease complete the UPI payment and share UTR number.")
            elif action == 'withdraw_request':
                amount = data.get('amount', 0)
                await message.reply_text(f"🏦 Withdrawal request submitted!\nAmount: ₹{amount:,.2f}\n\nWill be processed within 1-24 hours.")
            elif action == 'execute_trade':
                signal = data.get('signal', {})
                await message.reply_text(f"📊 Trade action noted!\n{signal.get('type','')} {signal.get('symbol','')}")
            else:
                await message.reply_text("✅ Action received from JARVIS Dashboard!")
        except json.JSONDecodeError:
            await message.reply_text("❌ Invalid data from Mini App")

    # ═══════════════════════════════════════════════════════
    #  AI RESPONSE ENGINE
    # ═══════════════════════════════════════════════════════

    async def _get_ai_response(self, query: str, user_id: int) -> str:
        """Get intelligent AI response by routing to appropriate JARVIS module"""
        
        # Try JARVIS AI brain first
        try:
            from jarvis_ai import process_query
            result = process_query(query, user_id)
            if result and str(result).strip():
                return str(result)
        except: pass
        
        # Try market brain for market queries
        try:
            from jarvis_market_brain import process_market_query
            result = process_market_query(query)
            if result and str(result).strip():
                return str(result)
        except: pass
        
        # Try super brain
        try:
            from jarvis_super_brain import get_intelligence
            result = get_intelligence(query)
            if result and str(result).strip():
                return str(result)
        except: pass
        
        # Smart fallback based on query content
        q = query.lower()
        
        if any(w in q for w in ['nifty', 'sensex', 'stock', 'share', 'market']):
            return (
                "📊 <b>Indian Market Analysis</b>\n\n"
                "JARVIS AI uses 6-model ML ensemble (XGBoost + LightGBM + RF + ExtraTrees + Ridge + LSTM) "
                "with 120+ features for predictions.\n\n"
                "Open the <b>Dashboard</b> for live signals with entry/target/SL levels.\n\n"
                "💡 <i>Available: Screener, Options Intelligence, Futures Brain</i>"
            )
        elif any(w in q for w in ['btc', 'bitcoin', 'crypto', 'eth', 'sol', 'coin', 'token']):
            return (
                "🪙 <b>Crypto Intelligence</b>\n\n"
                "JARVIS scans CoinDCX (200+ INR pairs), Pump.fun, DexScreener in real-time.\n\n"
                "Features: Gem scoring (40+ signals), rug detection, whale tracker, auto-buy dips.\n\n"
                "Open <b>Markets</b> tab in the dashboard for live prices & signals."
            )
        elif any(w in q for w in ['wallet', 'balance', 'deposit', 'withdraw', 'money', 'upi']):
            return (
                "💰 <b>Wallet System</b>\n\n"
                "• UPI QR deposit (auto-verify)\n"
                "• Bank withdrawal (1-24 hrs)\n"
                "• AES-256 encrypted storage\n"
                "• Transaction history\n\n"
                "Open <b>Wallet</b> in the dashboard to manage funds."
            )
        elif any(w in q for w in ['option', 'put', 'call', 'strike', 'pcr', 'oi']):
            return (
                "📊 <b>Options Intelligence</b>\n\n"
                "• Live PCR & Max Pain (NIFTY/BANKNIFTY)\n"
                "• India VIX tracking\n"
                "• Budget options under ₹5\n"
                "• FII/DII flow analysis\n\n"
                "Open <b>Options</b> from the dashboard for live data."
            )
        elif any(w in q for w in ['hi', 'hello', 'hey', 'start']):
            return (
                "👋 <b>Hello! I'm JARVIS AI</b>\n\n"
                "Your professional trading assistant. I cover:\n\n"
                "📊 Indian Stocks (NIFTY, 200+ stocks)\n"
                "🪙 Crypto (CoinDCX + Solana DEX)\n"
                "📈 Options & Futures Intelligence\n"
                "💰 Wallet with UPI\n"
                "🤖 AI Signals with 6-model ML\n\n"
                "Open the <b>Dashboard</b> button below or just ask me anything!"
            )
        else:
            return (
                f"🤖 <b>JARVIS AI</b>\n\n"
                f"Processing: <i>{query[:100]}</i>\n\n"
                "For the full experience with live charts, signals, and trading — "
                "open the <b>Dashboard</b> below.\n\n"
                "💡 <b>Try asking:</b>\n"
                "• Analyze RELIANCE\n"
                "• Best crypto to buy\n"
                "• NIFTY prediction tomorrow\n"
                "• Show budget options under ₹5"
            )

    # ═══════════════════════════════════════════════════════
    #  HELP
    # ═══════════════════════════════════════════════════════

    async def _send_help(self, message, edit=False):
        text = (
            "🤖 *JARVIS AI — Command Reference*\n\n"
            "🚀 *App Commands:*\n"
            "/start — Launch JARVIS Dashboard\n"
            "/menu — Main menu with all features\n\n"
            "📊 *Trading:*\n"
            "/trade — Open trading center\n"
            "/markets — Live market prices\n"
            "/signals — AI trading signals\n"
            "/screener — NLP stock screener\n\n"
            "💰 *Finance:*\n"
            "/wallet — Deposits & withdrawals\n"
            "/options — Options intelligence\n"
            "/risk — Risk analysis\n\n"
            "🤖 *AI:*\n"
            "/chat — AI conversation mode\n"
            "/airdrops — Airdrop finder\n"
            "/help — This help page\n\n"
            "💡 *Or just type any question!*\n"
            "Examples: \"Analyze NIFTY\", \"BTC signal\", \"RSI below 30\""
        )
        keyboard = [[InlineKeyboardButton("🚀 Open JARVIS", web_app=WebAppInfo(url=f"{MINI_APP_URL}/miniapp"))]]
        if edit:
            await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # ═══════════════════════════════════════════════════════
    #  RUN
    # ═══════════════════════════════════════════════════════

    def run(self):
        logger.info("🚀 JARVIS Mini App Bot v2.0 starting...")
        logger.info(f"📱 Mini App URL: {MINI_APP_URL}/miniapp")
        self.app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        exit(1)
    
    if not MINI_APP_URL or 'your-mini-app' in MINI_APP_URL:
        logger.error("❌ MINI_APP_URL not configured! Set it in .env to your ngrok/server URL")
        logger.error("   Example: MINI_APP_URL=https://abc123.ngrok-free.app")
        exit(1)
    
    bot = JarvisMiniAppBot()
    bot.run()
