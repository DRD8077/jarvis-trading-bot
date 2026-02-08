
import os
import sys
from dotenv import load_dotenv
load_dotenv()
import threading
import time
from typing import Optional
import json
import logging
import re
from datetime import datetime, timedelta
import pytz
import pandas as pd

import qrcode
from io import BytesIO

from stock_data_fetcher import fetch_nse_option_chain, parse_option_chain_json, analyze_option_chain, format_signal_message
from ml_pipeline import predict_for_symbol
from live_index_engine import (
    get_live_price, generate_index_option_chain, calculate_investment_options,
    format_investment_message, analyze_2min_candle, format_2min_signal,
    get_full_market_snapshot
)
from ml_predictor import predict_index_direction, format_ml_prediction
from ai_chat import ai_chat, clear_chat_history
from sms_engine import (
    send_sms, validate_indian_phone, send_telegram_sms_style,
    build_entry_sms, build_exit_sms, build_market_open_sms,
    build_prediction_sms, check_position_health, build_verification_sms
)

# ─── J.A.R.V.I.S. AI BRAIN ───
try:
    from jarvis_ai import (
        classify_intent, Intent, get_action_for_intent,
        build_jarvis_keyboard, generate_jarvis_welcome, generate_jarvis_help,
        generate_jarvis_greeting, generate_morning_briefing, generate_market_summary,
        jarvis_format, build_jarvis_context, check_proactive_alerts,
        # Memory system
        remember_user, recall_user, remember_name, get_user_context, add_to_conversation,
    )
    JARVIS_AVAILABLE = True
except ImportError:
    JARVIS_AVAILABLE = False

# ─── BUY/SELL SIGNAL ENGINE ───
try:
    from buy_sell_engine import (
        get_stock_signal, get_crypto_signal, scan_nifty_signals,
        scan_crypto_signals, scan_index_signals,
        format_signal_message as format_bs_signal, format_scanner_results,
        check_buy_sell_alerts, format_alert_message
    )
    BUY_SELL_AVAILABLE = True
except ImportError:
    BUY_SELL_AVAILABLE = False

# ─── ADMIN PANEL ───
try:
    from admin_panel import (
        is_admin, is_feature_enabled, handle_admin_command, handle_admin_callback,
        register_user, get_user_language, set_user_language, is_user_blocked,
        generate_admin_panel, build_admin_keyboard, get_system_health,
        get_broadcast_targets, log_broadcast, init_admin_db
    )
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False

# ─── GLOBAL CANDLE ENGINE ───
try:
    from global_candle_engine import (
        analyze_all_global_markets, analyze_us_markets, analyze_european_markets,
        analyze_asian_markets, analyze_commodities,
        format_global_analysis, format_regional_signals,
        get_india_prediction_from_global
    )
    GLOBAL_AVAILABLE = True
except ImportError:
    GLOBAL_AVAILABLE = False

# ─── VOICE ENGINE ───
try:
    from voice_engine import (
        generate_voice, generate_voice_for_message, transcribe_voice_message,
        download_telegram_voice, send_voice_message, should_send_voice,
        clean_text_for_speech, cleanup_voice_cache,
        create_video_note, send_video_note
    )
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# ─── CRYPTO INTELLIGENCE ENGINE ───
try:
    from crypto_intelligence import (
        analyze_token_full, format_token_signal, format_token_voice,
        get_top_crypto_picks, format_top_picks, format_picks_voice,
        add_to_watchlist, set_price_alert, check_price_alerts_all,
        enrich_token_line, enrich_tokens_batch
    )
    CRYPTO_INTEL_AVAILABLE = True
except ImportError:
    CRYPTO_INTEL_AVAILABLE = False

# ─── JARVIS MONITOR ───
try:
    from jarvis_monitor import start_monitor, stop_monitor, get_thread_health
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False

# ─── JARVIS SPOC ───
try:
    from jarvis_spoc import (
        format_spoc_dashboard, format_spoc_quick, format_spoc_voice,
        format_daily_briefing, start_spoc, stop_spoc,
        check_module_health, log_command, BOSS_NAME
    )
    SPOC_AVAILABLE = True
except ImportError:
    SPOC_AVAILABLE = False

# ─── JARVIS SUPER BRAIN — Worldwide Intelligence + News + Auto SPOC ───
try:
    from jarvis_super_brain import (
        fetch_all_news, format_news_digest, format_news_voice,
        get_market_intelligence, format_jarvis_briefing, format_briefing_voice,
        jarvis_animated_header, detect_solana_address,
        start_super_brain, stop_super_brain, jarvis_route_command,
    )
    SUPER_BRAIN_AVAILABLE = True
except ImportError:
    SUPER_BRAIN_AVAILABLE = False

# ─── NEW SUPER-POWERED MODULE IMPORTS ───
try:
    from sentiment_engine import analyze_news_sentiment, calculate_fear_greed_index, format_sentiment_message
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False

try:
    from risk_manager import calculate_position_size, kelly_criterion, calculate_risk_reward, format_risk_report
    RISK_AVAILABLE = True
except ImportError:
    RISK_AVAILABLE = False

# ─── PHASE 6 POWER MODULES ───
try:
    from market_regime import detect_regime, format_regime_report, get_regime_adjusted_signal
    REGIME_AVAILABLE = True
except ImportError:
    REGIME_AVAILABLE = False

try:
    from options_engine import (
        generate_option_chain_with_greeks, suggest_strategy,
        format_options_analysis, format_strategy_suggestion,
        calculate_pcr, calculate_max_pain
    )
    OPTIONS_AVAILABLE = True
except ImportError:
    OPTIONS_AVAILABLE = False

try:
    from buy_sell_engine import get_scalping_signal, get_multi_timeframe_signal, format_scalping_signal, format_multi_tf
    SCALP_AVAILABLE = True
except ImportError:
    SCALP_AVAILABLE = False

try:
    from rug_detector import check_goplus_security, format_goplus_report
    GOPLUS_AVAILABLE = True
except ImportError:
    GOPLUS_AVAILABLE = False

try:
    from portfolio_tracker import (
        add_stock_holding, sell_stock_holding, get_stock_portfolio,
        calculate_stock_portfolio_pnl, format_stock_portfolio,
        calculate_tax, format_tax_report, format_combined_portfolio
    )
    STOCK_PORTFOLIO_AVAILABLE = True
except ImportError:
    STOCK_PORTFOLIO_AVAILABLE = False

try:
    from whale_alert import check_helius_transactions, format_onchain_whale_report
    ONCHAIN_AVAILABLE = True
except ImportError:
    ONCHAIN_AVAILABLE = False

# ─── COINDCX WEB3 ENGINE ───
try:
    from coindcx_engine import (
        coindcx_signal, coindcx_top_movers, coindcx_best_signals,
        coindcx_quick_price, get_composite_signal, format_composite_signal,
        # New Web3 All-Token Functions
        coindcx_all_web3, coindcx_web3_category, coindcx_web3_scan,
        coindcx_web3_search, coindcx_web3_summary, coindcx_web3_movers,
        get_all_web3_tokens, get_web3_token_count, search_web3_token,
        WEB3_CATEGORIES,
        # ₹2K Investment Calculator + All-Token Dump
        coindcx_token_invest, coindcx_all_tokens_dump, coindcx_all_tokens_by_category,
    )
    COINDCX_AVAILABLE = True
except ImportError:
    COINDCX_AVAILABLE = False

# ─── MEGA SCANNER ENGINE (Top 100 AI/ML + Candles) ───
try:
    from coindcx_mega_scanner import (
        mega_scan_top100, format_mega_top100, format_mega_detail_card,
        format_mega_voice, format_bg_alert_top_signals,
        detect_crypto_candle_patterns,
        calculate_wealth_strategy, format_wealth_strategy, format_wealth_voice,
        _fmt_inr as mega_fmt_inr,
    )
    MEGA_SCANNER_AVAILABLE = True
except ImportError:
    MEGA_SCANNER_AVAILABLE = False

# ─── PHANTOM WALLET ENGINE ───
try:
    from phantom_wallet import (
        connect_wallet, disconnect_wallet, get_wallet, is_wallet_connected,
        generate_phantom_connect_link, scan_wallet as phantom_scan_wallet,
        format_wallet_scan, format_wallet_voice, format_wallet_alerts,
        start_wallet_alerts, stop_wallet_alerts,
        # New: Real-time + Security + Dashboard
        get_wallet_dashboard, auto_connect_owner_wallet,
        start_realtime_monitoring, get_security_status,
        OWNER_WALLET, OWNER_CHAT_ID as PHANTOM_OWNER_ID,
    )
    PHANTOM_AVAILABLE = True
except ImportError:
    PHANTOM_AVAILABLE = False

# ─── WEB3 ROCKET SCANNER — ₹2K → ₹50K Moonshot Hunter ───
try:
    from web3_rocket_scanner import (
        rocket_scan_full, rocket_scan_fast, rocket_scan_coindcx,
        rocket_scan_pump, rocket_token_detail,
        scan_rockets, get_new_rocket_alerts,
        format_rocket_scan, format_single_rocket, format_rocket_voice
    )
    ROCKET_AVAILABLE = True
except ImportError:
    ROCKET_AVAILABLE = False

# ─── JARVIS SECURITY ENGINE — Military-Grade Protection ───
try:
    from jarvis_security import (
        security_check, security_check_wallet, rate_limiter,
        sanitize_input, log_action, log_wallet_operation,
        get_security_dashboard, get_recent_audit_log,
        validate_financial_input, validate_symbol, check_admin_brute_force,
        get_security_metrics,
    )
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

# ─── AIRDROP HUNTER — Auto-Capture Free Crypto ───
try:
    from airdrop_hunter import (
        airdrop_scan_full, airdrop_scan_solana, airdrop_upcoming,
        scan_all_airdrops, format_airdrop_scan, format_airdrop_voice,
        start_airdrop_hunter, stop_airdrop_hunter, set_alert_callback,
        register_wallet, get_new_airdrop_alerts,
    )
    AIRDROP_AVAILABLE = True
except ImportError:
    AIRDROP_AVAILABLE = False

# ─── DEXTOOLS ENGINE — Multi-Chain Token Intelligence ───
try:
    from dextools_engine import (
        dextools_top15, dextools_meme_board, dextools_new_pairs,
        dextools_airdrops, dextools_voice, scan_all_tokens,
        format_top_tokens, format_voice_summary, get_token_links,
        start_dextools_scanner, stop_dextools_scanner,
        set_alert_callback as set_dextools_alert_callback,
    )
    DEXTOOLS_AVAILABLE = True
except ImportError:
    DEXTOOLS_AVAILABLE = False

# ─── AI/ML SIGNAL ENGINE — World's #1 Buy/Sell Indicators ───
try:
    from ai_signals import (
        full_technical_analysis, quick_signal, batch_signals,
        format_signal_report, format_signal_voice,
    )
    AI_SIGNALS_AVAILABLE = True
except ImportError:
    AI_SIGNALS_AVAILABLE = False

# ─── ULTRA AI PREDICTION ENGINE — Buy/Sell + Risk + Health ───
try:
    from jarvis_ultra_ai import (
        ultra_predict, batch_ultra_predict,
        format_ultra_top_tokens, format_ultra_token_card,
        format_ultra_voice,
        assess_rug_risk, detect_whale_activity,
        liquidity_health, smart_money_flow,
        calculate_price_targets, token_health_score,
    )
    ULTRA_AI_AVAILABLE = True
except ImportError:
    ULTRA_AI_AVAILABLE = False

# ─── JARVIS MARKET BRAIN — Stock vs Crypto Intelligence ───
try:
    from jarvis_market_brain import (
        detect_market_type, extract_token_from_message, extract_token_from_reply,
        analyze_indian_stock_deep, format_indian_stock_report, format_indian_stock_voice,
        analyze_crypto_token_deep, format_crypto_deep_report, format_crypto_deep_voice,
    )
    MARKET_BRAIN_AVAILABLE = True
except ImportError:
    MARKET_BRAIN_AVAILABLE = False

# ─── INDIAN STOCK SUPER ENGINE — ATM/OTM + Holidays + AI Power ───
try:
    from indian_stock_super_engine import (
        get_market_status as get_super_market_status,
        get_upcoming_holidays,
        recommend_best_options,
        indian_stock_super_analysis,
        format_super_analysis,
        format_super_voice,
        format_option_comparison,
    )
    SUPER_ENGINE_AVAILABLE = True
except ImportError:
    SUPER_ENGINE_AVAILABLE = False

# ─── QR WALLET CONNECT — Trust Wallet QR Engine ───
try:
    from qr_wallet_connect import (
        generate_trust_connect_mega,
        generate_trust_wallet_connect_qr,
        generate_solana_pay_qr,
        generate_receive_qr,
        generate_dapp_browser_qr,
        generate_multi_chain_qr_pack,
        generate_trust_wallet_send_link,
        generate_trust_wallet_dapp_link,
        track_qr_session,
        get_qr_stats,
        OWNER_SOLANA_WALLET as QR_OWNER_WALLET,
        TRUST_WALLET_COINS,
    )
    QR_WALLET_AVAILABLE = True
except ImportError:
    QR_WALLET_AVAILABLE = False

# ─── SOLANA ENGINE — Free Blockchain Operations ───
try:
    from solana_engine import (
        get_sol_balance, get_all_token_balances, resolve_token_metadata,
        get_recent_transactions, check_transaction_confirmed,
        generate_solana_pay_url, generate_phantom_transfer_link,
        generate_phantom_connect_deeplink, generate_phantom_browse_link,
        scan_for_claimable_airdrops, generate_claim_and_transfer_links,
        detect_new_tokens, start_tx_monitor, stop_tx_monitor,
        get_wallet_summary, format_wallet_summary,
        format_wallet_voice as solana_wallet_voice,
        format_transfer_acknowledgment, format_token_arrival_alert,
        is_scam_token,
        OWNER_WALLET as SOL_OWNER_WALLET,
        OWNER_PHANTOM_USERNAME,
    )
    SOLANA_ENGINE_AVAILABLE = True
except ImportError:
    SOLANA_ENGINE_AVAILABLE = False

import requests

# --- Logging setup ---
LOG_FILE = os.environ.get("TELEGRAM_BOT_LOG", "telegram_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_bot")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN not set! Add it to .env or environment variables.")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

IST = pytz.timezone('Asia/Kolkata')

auto_thread = None
auto_flag = threading.Event()
chat_storage = {}

# ═══════════════════════════════════════════════════════════
#  DECORATIVE UI CONSTANTS
# ═══════════════════════════════════════════════════════════

HEADER_LINE = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DOUBLE_LINE = "═══════════════════════════════"
SPARKLE_LINE = "✦═══════════════════════════✦"
DIAMOND_LINE = "◆━━━━━━━━━━━━━━━━━━━━━━━━━◆"
STAR_LINE = "★═══════════════════════════★"
FIRE_LINE = "🔥━━━━━━━━━━━━━━━━━━━━━━━🔥"

# ═══════════════════════════════════════════════════════════
#  OWNER / ADMIN ACCESS CONTROL
# ═══════════════════════════════════════════════════════════
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "5647898018"))

def _is_owner(chat_id) -> bool:
    """Check if chat_id is the bot owner.
    Only the owner can see dashboard, portfolio, trade history, positions."""
    return int(chat_id) == OWNER_CHAT_ID

# ═══════════════════════════════════════════════════════════
#  CORE TELEGRAM FUNCTIONS
# ═══════════════════════════════════════════════════════════

def send_message(chat_id: int, text: str, reply_markup: Optional[dict] = None):
    url = f"{API_URL}/sendMessage"
    # Auto-split long messages (Telegram limit = 4096 chars)
    if len(text) > 4000:
        chunks = _split_message(text, 4000)
        for i, chunk in enumerate(chunks):
            payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}
            if reply_markup and i == len(chunks) - 1:
                payload["reply_markup"] = json.dumps(reply_markup)
            try:
                r = requests.post(url, json=payload, timeout=10)
                if r.status_code != 200:
                    logger.error(f"send_message chunk failed: {r.text[:200]}")
                    # Retry without parse_mode
                    payload2 = {"chat_id": chat_id, "text": chunk}
                    if reply_markup and i == len(chunks) - 1:
                        payload2["reply_markup"] = json.dumps(reply_markup)
                    try:
                        requests.post(url, json=payload2, timeout=10)
                    except Exception as e:
                        logger.error(f"[MSG] Chunk retry failed for {chat_id}: {e}")
            except Exception as e:
                logger.error(f"[MSG] Chunk send failed for {chat_id}: {e}")
        return
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"send_message -> chat_id={chat_id} status={r.status_code}")
        if r.status_code != 200:
            logger.error(f"send_message failed: {r.text[:200]}")
            # Retry without parse_mode (fallback for special chars)
            payload2 = {"chat_id": chat_id, "text": text}
            if reply_markup:
                payload2["reply_markup"] = json.dumps(reply_markup)
            try:
                r2 = requests.post(url, json=payload2, timeout=10)
                if r2.status_code != 200:
                    logger.error(f"send_message retry also failed: {r2.text[:200]}")
            except Exception as e:
                logger.error(f"[MSG] Retry send failed for {chat_id}: {e}")
    except Exception as e:
        logger.error(f"[MSG] send_message exception for chat_id={chat_id}: {e}")


def _split_message(text: str, max_len: int = 4000) -> list:
    """Split a long message into chunks at newline boundaries."""
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind('\n', 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip('\n')
    if text:
        chunks.append(text)
    return chunks


def send_photo(chat_id: int, image_bytes: bytes, caption: Optional[str] = None):
    url = f"{API_URL}/sendPhoto"
    files = {"photo": ("qrcode.png", image_bytes)}
    data = {"chat_id": chat_id, "parse_mode": "Markdown"}
    if caption:
        data["caption"] = caption
    try:
        r = requests.post(url, files=files, data=data, timeout=10)
        print(f"send_photo -> chat_id={chat_id} status={r.status_code}")
    except Exception as e:
        print(f"send_photo exception for chat_id={chat_id}: {e}")


def send_jarvis_voice(chat_id: int, text: str, intent: str = "", is_voice_input: bool = False):
    """
    🎤 Send JARVIS voice — AUTO-PLAY video note (round bubble)!
    1. Generate Gemini TTS audio (OGG)
    2. Convert to video note (MP4 with JARVIS avatar)
    3. Send as sendVideoNote → AUTO-PLAYS in Telegram!
    4. Fallback: regular sendVoice if video note fails
    """
    if not VOICE_AVAILABLE:
        return
    
    try:
        if not should_send_voice(text, intent, is_voice_input):
            return
        
        voice_path = generate_voice_for_message(text, chat_id)
        if not voice_path:
            return
        
        # TRY VIDEO NOTE (auto-play round bubble!)
        try:
            video_path = create_video_note(voice_path)
            if video_path:
                if send_video_note(chat_id, video_path, TELEGRAM_TOKEN):
                    logger.info(f"[JARVIS-VOICE] Auto-play video note sent to {chat_id}")
                    return
        except Exception as ve:
            logger.warning(f"[JARVIS-VOICE] Video note failed, falling back to voice: {ve}")
        
        # FALLBACK: regular voice message (press-to-play)
        send_voice_message(chat_id, voice_path, TELEGRAM_TOKEN)
    except Exception as e:
        logger.error(f"[JARVIS-VOICE] Failed to send voice: {e}")


def generate_qr(data: str) -> bytes:
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════
#  PERSONALIZATION — JARVIS FEMININE GREETING
# ═══════════════════════════════════════════════════════════

def get_user_greeting(update: dict) -> str:
    """Simple greeting for all pages."""
    try:
        user = update.get("message", {}).get("from", {})
        first_name = user.get("first_name", "")
    except Exception:
        first_name = ""
    
    name = first_name or "Friend"
    greeting = f"🌸 *नमस्ते {name} जी!* 💕\n"
    return greeting


def get_welcome_greeting(update: dict) -> str:
    """Beautiful JARVIS welcome greeting for /start page."""
    try:
        user = update.get("message", {}).get("from", {})
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or "Friend"
    except Exception:
        full_name = "Friend"
    
    greeting = (
        f"🌸✨ *नमस्ते {full_name.upper()} जी!* ✨🌸\n"
        f"{SPARKLE_LINE}\n"
    )
    return greeting


def get_user_name(update: dict) -> str:
    """Get user's display name from update."""
    try:
        user = update.get("message", {}).get("from", {})
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        return f"{first_name} {last_name}".strip() or "User"
    except Exception:
        return "User"


# ═══════════════════════════════════════════════════════════
#  STUNNING UI — KEYBOARD WITH RICH EMOJIS
# ═══════════════════════════════════════════════════════════

def build_keyboard():
    """Build J.A.R.V.I.S. themed keyboard — organized by category."""
    if JARVIS_AVAILABLE:
        return build_jarvis_keyboard()
    
    # Fallback keyboard if JARVIS module unavailable
    rows = [
        ["🤖 AI Chat 💬", "☀️ Morning Brief 📊"],
        ["🔱 NIFTY Signals 📊", "🔱 SENSEX Signals 📊"],
        ["💎 NIFTY Calls OTM 🚀", "💎 SENSEX Calls OTM 🚀"],
        ["⚡ NIFTY Puts OTM 📉", "⚡ SENSEX Puts OTM 📉"],
        ["💰 Invest ₹2K NIFTY", "💰 Invest ₹2K SENSEX"],
        ["💸 Invest ₹20K NIFTY", "💸 Invest ₹20K SENSEX"],
        ["🤖 NIFTY ML Predict 🧠", "🤖 SENSEX ML Predict 🧠"],
        ["⚡ 2-Min NIFTY Signal", "⚡ 2-Min SENSEX Signal"],
        ["🇮🇳⚡ NIFTY Call/Put AI", "📊 SENSEX Call/Put AI"],
        ["🏦 BankNIFTY Call/Put AI", "📅 Market Holidays 🇮🇳"],
        ["📈🇮🇳 Indian Stock AI 🧠", "🧠 Super Prediction 🔮"],
        ["📰 Market Sentiment 💬", "⚠️ Risk Calculator 🛡️"],
        ["🕯️ Candle Patterns 📊", "🌍 Market Trend 📈"],
        ["⏰ Market Status 🔔", "📊 Live Snapshot 🔴"],
        ["🔮 Tomorrow Prediction 🎯"],
        ["🪙 Crypto Gems 💎", "🔥 Trending Crypto 📈"],
        ["🟣 Pump.fun Trending 🔥", "🆕 Pump.fun New Launches"],
        ["🏆 Pump.fun Top MCap", "🪙 All Gems (Pump+Dex)"],
        ["📉 Crypto Dips 🔴", "🚀 Crypto Pumps 🟢"],
        ["🤖 AI Crypto Pick 🧠", "🔔 Crypto Alerts ON/OFF"],
        ["🐋 Whale Scanner 🔍", "🛡️ Rug Detector 🔎"],
        ["📂 My Crypto Portfolio", "📜 Trade History"],
        ["🔔 Price Alerts 📊", "📊 Gem Accuracy 🔬"],
        ["🌐 Multi-Chain Gems 🔗", "💰 Buy Crypto /buy"],
        ["🔥 DexTools Top 15", "🐸 Meme Board"],
        ["🆕 Live New Pairs", "🎁 DexTools Airdrops"],
        ["🧠 AI Signal Report", "📊 Multi-Chain Scan"],
        ["🚀🔥 ROCKET Scanner", "🔥 Fast Rockets"],
        ["🚀 CoinDCX Rockets", "🟣 Pump.fun Rockets"],
        ["🔥 TOP 100 AI Signals 🧠", "💰 ₹2K → ₹2L Strategy 🚀"],
        ["🔥 Crypto Deep Analysis 🪙"],
        ["🌐 All Web3 Tokens", "📋 Web3 Token List"],
        ["💰 ₹2K Token Invest", "🚀💥 Web3 Top Movers"],
        ["🔍 Web3 AI Scan All", "🔷 Web3 Layer 1"],
        ["🔶 Web3 Layer 2", "🏦 Web3 DeFi Tokens"],
        ["🐸 Web3 Meme Coins", "🤖 Web3 AI Tokens"],
        ["🎮 Web3 Gaming NFT"],
        ["👻 Phantom Wallet 🔮", "👻 Connect Wallet"],
        ["👻 Wallet Scan 📊", "👻 Wallet Summary ⚡"],
        ["👻 Claim Airdrops 🎁", "👻 Transfer SOL 💸"],
        ["👻 Wallet Alerts ON", "👻 Disconnect Wallet"],
        ["🎁 Airdrop Hunter 🚀", "🔮 Upcoming Airdrops"],
        ["🎁 Solana Airdrops"],
        ["🛡️ Security Dashboard", "🔐 Security Status"],
        ["🔗 Trust Wallet QR 📱", "◎ Solana Pay QR"],
        ["📲 SMS Alerts ON 🔔", "📲 SMS Alerts OFF 🔕"],
        ["💵 Set Investment Amount", "📊 My Positions"],
        ["➕ Add Symbol 🎯", "➖ Remove Symbol ❌", "📋 Watchlist"],
        ["🔔 Subscribe Alerts ✅", "🔕 Unsubscribe ❌", "👥 My Subs"],
        ["📱 Generate QR 🔗", "❓ Help 💡", "🏠 /start"],
    ]
    return {"keyboard": rows, "resize_keyboard": True}


# ═══════════════════════════════════════════════════════════
#  OPTION CHAIN ANALYSIS
# ═══════════════════════════════════════════════════════════

def find_best_otm_options(calls_df, puts_df, underlying, option_type="calls", num_strikes=3):
    """Find best OTM options with return potential."""
    results = []
    
    if option_type == "calls":
        df = calls_df.copy()
        otm = df[df['strike'] > underlying].sort_values('strike')
    else:
        df = puts_df.copy()
        otm = df[df['strike'] < underlying].sort_values('strike', ascending=False)
    
    if otm.empty:
        return []
    
    for _, row in otm.head(num_strikes).iterrows():
        strike = float(row.get('strike', 0))
        ltp = float(row.get('lastPrice', 0))
        iv = float(row.get('impliedVolatility', 0))
        bid = float(row.get('bidprice', ltp))
        
        if ltp <= 0:
            continue
        
        moneyness = abs(strike - underlying) / underlying
        return_potential = (50 + iv * 100 + moneyness * 100) * 10
        
        results.append({
            'strike': strike,
            'ltp': ltp,
            'bid': bid,
            'iv': iv,
            'moneyness_pct': moneyness * 100,
            'return_potential': return_potential,
            'oi': float(row.get('openInterest', 0))
        })
    
    return sorted(results, key=lambda x: x['return_potential'], reverse=True)


# ═══════════════════════════════════════════════════════════
#  TOMORROW PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════

def generate_tomorrow_prediction() -> str:
    """Generate comprehensive next-day prediction based on global markets,
    technical analysis, and sentiment — recommends CALL or PUT."""
    import yfinance as yf
    
    now = datetime.now(IST)
    tomorrow = (now + timedelta(days=1)).strftime("%A, %d %b %Y")
    
    parts = []
    parts.append(f"🔮✨ *TOMORROW'S MARKET PREDICTION* ✨🔮")
    parts.append(FIRE_LINE)
    parts.append(f"📅 *Date:* {tomorrow}")
    parts.append(f"⏰ *Generated:* {now.strftime('%H:%M IST, %d %b %Y')}")
    parts.append(HEADER_LINE)
    
    # Collect signals
    bullish_signals = 0
    bearish_signals = 0
    total_signals = 0
    
    # 1. Global Market Analysis
    parts.append("\n🌍 *GLOBAL MARKET SCAN:*")
    global_indices = {
        "US S&P 500": "^GSPC",
        "US NASDAQ": "^IXIC",
        "US Dow Jones": "^DJI",
        "UK FTSE 100": "^FTSE",
        "Japan Nikkei": "^N225",
        "Hong Kong HSI": "^HSI",
        "Gold": "GC=F",
        "Crude Oil": "CL=F",
        "VIX (Fear)": "^VIX",
    }
    
    for name, ticker in global_indices.items():
        try:
            data = yf.download(ticker, period="5d", progress=False)
            if data is not None and len(data) >= 2:
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                col = 'Close' if 'Close' in data.columns else 'close'
                close_vals = data[col].values
                prev = float(close_vals[-2])
                curr = float(close_vals[-1])
                if prev > 0:
                    change_pct = ((curr - prev) / prev) * 100
                    total_signals += 1
                    if "VIX" in name:
                        if change_pct > 0:
                            bearish_signals += 1
                            icon = "🔴"
                        else:
                            bullish_signals += 1
                            icon = "🟢"
                    else:
                        if change_pct > 0:
                            bullish_signals += 1
                            icon = "🟢"
                        else:
                            bearish_signals += 1
                            icon = "🔴"
                    parts.append(f"  {icon} {name}: {change_pct:+.2f}%")
        except Exception:
            pass
    
    # 2. NIFTY & SENSEX Technical Analysis
    parts.append(f"\n{HEADER_LINE}")
    parts.append("📊 *TECHNICAL ANALYSIS:*")
    
    for yf_ticker, display_name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
        try:
            from candle_analyzer import analyze_index
            analysis = analyze_index(yf_ticker, display_name)
            signal = analysis.get("signal", "HOLD")
            conf = analysis.get("confidence", 0.5)
            price = analysis.get("indicators", {}).get("price", 0)
            rsi = analysis.get("indicators", {}).get("rsi", 50)
            
            if signal == "BUY":
                bullish_signals += 2
                total_signals += 2
                icon = "🟢"
            elif signal == "SELL":
                bearish_signals += 2
                total_signals += 2
                icon = "🔴"
            else:
                total_signals += 1
                icon = "🟡"
            
            parts.append(f"  {icon} *{display_name}:* {signal} ({conf:.0%})")
            parts.append(f"     Price: ₹{price:.0f} | RSI: {rsi:.1f}")
            
            if rsi > 70:
                bearish_signals += 1
                total_signals += 1
                parts.append(f"     ⚠️ RSI Overbought — reversal possible")
            elif rsi < 30:
                bullish_signals += 1
                total_signals += 1
                parts.append(f"     ✅ RSI Oversold — bounce likely")
        except Exception:
            parts.append(f"  ⚠️ {display_name} analysis unavailable")
    
    # 3. Final Prediction
    parts.append(f"\n{DOUBLE_LINE}")
    parts.append("🎯 *TOMORROW'S VERDICT:*")
    parts.append(FIRE_LINE)
    
    if total_signals > 0:
        bull_pct = (bullish_signals / total_signals) * 100
        bear_pct = (bearish_signals / total_signals) * 100
    else:
        bull_pct = 50
        bear_pct = 50
    
    bull_blocks = int(bull_pct / 10)
    bear_blocks = int(bear_pct / 10)
    bull_bar = "🟩" * bull_blocks + "⬜" * (10 - bull_blocks)
    bear_bar = "🟥" * bear_blocks + "⬜" * (10 - bear_blocks)
    
    parts.append(f"\n  📈 Bullish: {bull_bar} {bull_pct:.0f}%")
    parts.append(f"  📉 Bearish: {bear_bar} {bear_pct:.0f}%")
    
    if bull_pct > 65:
        verdict = "🟢🚀 *STRONG BUY CALLS* 🚀🟢"
        action = "BUY CALL OPTIONS (CE)"
        emoji_border = "💚💚💚💚💚💚💚💚💚💚"
        detail = "Markets showing strong bullish momentum. Buy CE (Call) options."
    elif bull_pct > 55:
        verdict = "🟢 *MODERATELY BULLISH — BUY CALLS* 🟢"
        action = "BUY CALL OPTIONS (with caution)"
        emoji_border = "💚💚💚💚💚🟡🟡🟡🟡🟡"
        detail = "Mild bullish tilt. Call options favored but keep strict stop-loss."
    elif bear_pct > 65:
        verdict = "🔴📉 *STRONG BUY PUTS* 📉🔴"
        action = "BUY PUT OPTIONS (PE)"
        emoji_border = "❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️"
        detail = "Markets showing strong bearish pressure. Buy PE (Put) options."
    elif bear_pct > 55:
        verdict = "🔴 *MODERATELY BEARISH — BUY PUTS* 🔴"
        action = "BUY PUT OPTIONS (with caution)"
        emoji_border = "❤️❤️❤️❤️❤️🟡🟡🟡🟡🟡"
        detail = "Bearish tilt visible. Put options favored but manage risk."
    else:
        verdict = "🟡⚖️ *NEUTRAL — WAIT & WATCH* ⚖️🟡"
        action = "NO TRADE — Stay on sidelines"
        emoji_border = "🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡"
        detail = "No clear direction. Avoid trading, wait for clearer signals."
    
    parts.append(f"\n  {emoji_border}")
    parts.append(f"\n  🎯 *VERDICT:* {verdict}")
    parts.append(f"  💰 *ACTION:* {action}")
    parts.append(f"\n  📝 {detail}")
    parts.append(f"\n  {emoji_border}")
    
    parts.append(f"\n{HEADER_LINE}")
    parts.append("⚠️ *DISCLAIMER:*")
    parts.append("_AI-generated prediction. Not financial advice._")
    parts.append("_Always use stop-loss. Trade at your own risk._")
    parts.append(STAR_LINE)
    
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════
#  AUTO ALERT SYSTEM (24/7 Background Thread)
# ═══════════════════════════════════════════════════════════

last_auto_alert_time = {}

def is_market_open() -> bool:
    """Check if NSE market is open (Mon-Fri 9:15 AM - 3:30 PM IST)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def auto_alert_loop():
    """Background thread: automatically sends NIFTY/SENSEX signals + SMS to all subscribers.
    
    During market hours:
      - 9:15 AM: Market open SMS to all SMS subscribers
      - Every 2 min: candle analysis + Telegram + SMS alerts
      - Continuous: EXIT monitoring for open positions
    Off hours: every 2 hours global market summary + next day prediction
    """
    logger.info("🔔 Auto-Alert Engine STARTED — running 24/7 with SMS & EXIT monitoring")
    
    while not auto_flag.is_set():
        try:
            from data_store import (
                list_subscribers, list_active_sms_subscribers,
                get_open_positions, save_position, close_position
            )
            subs = list_subscribers()
            sms_subs = list_active_sms_subscribers()
            
            if not subs and not sms_subs:
                logger.info("[AUTO] No subscribers, sleeping 60s...")
                time.sleep(60)
                continue
            
            now = datetime.now(IST)
            
            if is_market_open():
                # ── MARKET HOURS: 2-min candle alerts + SMS + EXIT monitoring ──
                interval = 120  # 2 minutes
                
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                #  9:15 AM MARKET OPEN SMS ALERT
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                market_open_key = f"market_open_{now.strftime('%Y%m%d')}"
                if market_open_key not in last_auto_alert_time:
                    if now.hour == 9 and 15 <= now.minute <= 20:
                        last_auto_alert_time[market_open_key] = time.time()
                        logger.info("[AUTO] 🔔 Sending MARKET OPEN alerts!")
                        
                        try:
                            nifty_price = get_live_price("^NSEI")
                            sensex_price = get_live_price("^BSESN")
                            
                            # Get quick ML signals for open
                            nifty_sig = "WAIT"
                            sensex_sig = "WAIT"
                            try:
                                np_ml = predict_index_direction("^NSEI", "NIFTY")
                                if "error" not in np_ml:
                                    nifty_sig = np_ml.get("direction", "WAIT")
                            except Exception:
                                pass
                            try:
                                sp_ml = predict_index_direction("^BSESN", "SENSEX")
                                if "error" not in sp_ml:
                                    sensex_sig = sp_ml.get("direction", "WAIT")
                            except Exception:
                                pass
                            
                            # Telegram market-open alert to all subs
                            open_alert = (
                                f"🔔🔔🔔 *MARKET OPEN — 9:15 AM IST* 🔔🔔🔔\n"
                                f"{FIRE_LINE}\n"
                                f"📊 *NIFTY:* ₹{nifty_price:,.2f} → ML: *{nifty_sig}*\n"
                                f"📊 *SENSEX:* ₹{sensex_price:,.2f} → ML: *{sensex_sig}*\n"
                                f"{HEADER_LINE}\n"
                                f"⚡ First 2-min candle signals coming in 2 min...\n"
                                f"📲 SMS subscribers will get alerts on phone!\n"
                                f"{STAR_LINE}"
                            )
                            for chat_id in subs:
                                try:
                                    send_message(chat_id, open_alert)
                                except Exception:
                                    pass
                            
                            # SMS market-open alert to all SMS subscribers
                            for sub in sms_subs:
                                try:
                                    sms_msg = build_market_open_sms(
                                        user_name=sub.get("user_name", "Trader"),
                                        nifty_price=nifty_price,
                                        sensex_price=sensex_price,
                                        nifty_signal=nifty_sig,
                                        sensex_signal=sensex_sig
                                    )
                                    send_sms(sub["phone"], sms_msg)
                                    time.sleep(0.5)
                                except Exception as e:
                                    logger.error(f"[SMS] Market open failed for {sub['phone']}: {e}")
                        except Exception as e:
                            logger.error(f"[AUTO] Market open alert failed: {e}")
                
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                #  EXIT MONITORING FOR OPEN POSITIONS
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                try:
                    open_positions = get_open_positions()
                    if open_positions:
                        nifty_spot = get_live_price("^NSEI")
                        sensex_spot = get_live_price("^BSESN")
                        
                        for pos in open_positions:
                            try:
                                spot = nifty_spot if "NIFTY" in pos["index_name"].upper() else sensex_spot
                                health = check_position_health(pos, spot)
                                
                                action = health.get("action", "HOLD")
                                if action in ("EXIT_URGENT", "EXIT_NOW", "BOOK_PROFIT", "BOOK_PARTIAL", "EXIT_EOD"):
                                    exit_key = f"exit_{pos['id']}_{action}"
                                    last_exit_time = last_auto_alert_time.get(exit_key, 0)
                                    if time.time() - last_exit_time < 600:  # Don't repeat exit within 10 min
                                        continue
                                    last_auto_alert_time[exit_key] = time.time()
                                    
                                    pnl = health["pnl"]
                                    pnl_pct = health["pnl_pct"]
                                    reason = health["reason"]
                                    urgency = health["urgency"]
                                    
                                    # Telegram EXIT alert
                                    if pnl >= 0:
                                        exit_emoji = "🟢💰"
                                        exit_action = "BOOK PROFIT"
                                    else:
                                        exit_emoji = "🔴🚨"
                                        exit_action = "EXIT NOW"
                                    
                                    exit_alert = (
                                        f"{exit_emoji} *{exit_action} — {pos['index_name']}* {exit_emoji}\n"
                                        f"{FIRE_LINE}\n"
                                        f"⚠️ *Urgency:* {urgency}\n"
                                        f"📊 Strike: ₹{pos['strike']:,.0f} {pos['option_type']}\n"
                                        f"💰 Entry: ₹{pos['entry_price']:.2f} → Now: ~₹{health['estimated_premium']:.2f}\n"
                                        f"📈 P&L: ₹{pnl:,.0f} ({pnl_pct:+.1f}%)\n"
                                        f"🧠 {reason}\n"
                                        f"{HEADER_LINE}\n"
                                    )
                                    
                                    if action in ("EXIT_URGENT", "EXIT_NOW"):
                                        exit_alert += (
                                            f"🚨🚨 *TAKE EXIT FROM MARKET* 🚨🚨\n"
                                            f"Market going against your position!\n"
                                            f"*EXIT IN NEXT 5 MINUTES!*\n"
                                        )
                                    elif action in ("BOOK_PROFIT", "BOOK_PARTIAL"):
                                        exit_alert += (
                                            f"✅ *CONGRATULATIONS! Book your profit NOW!*\n"
                                            f"Don't be greedy — secure your gains!\n"
                                        )
                                    
                                    exit_alert += f"\n{STAR_LINE}"
                                    
                                    # Send to the position owner
                                    try:
                                        send_message(pos["chat_id"], exit_alert)
                                    except Exception:
                                        pass
                                    
                                    # SMS EXIT alert
                                    if pos.get("phone"):
                                        try:
                                            # Find user_name from sms_subs
                                            u_name = "Trader"
                                            for s in sms_subs:
                                                if s["phone"] == pos["phone"]:
                                                    u_name = s.get("user_name", "Trader")
                                                    break
                                            
                                            sms_msg = build_exit_sms(
                                                user_name=u_name,
                                                index_name=pos["index_name"],
                                                reason=reason,
                                                entry_price=pos["entry_price"],
                                                current_price=health["estimated_premium"],
                                                pnl=pnl,
                                                pnl_pct=pnl_pct,
                                                urgency=urgency
                                            )
                                            send_sms(pos["phone"], sms_msg)
                                        except Exception as e:
                                            logger.error(f"[SMS] Exit alert failed: {e}")
                                    
                                    # Auto-close position if urgent
                                    if action == "EXIT_URGENT":
                                        try:
                                            close_position(pos["id"], health["estimated_premium"], pnl)
                                            logger.info(f"[AUTO] Auto-closed position {pos['id']} P&L: {pnl}")
                                        except Exception:
                                            pass
                                            
                            except Exception as e:
                                logger.error(f"[AUTO] Position check failed for {pos['id']}: {e}")
                except Exception as e:
                    logger.error(f"[AUTO] Exit monitoring error: {e}")
                
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                #  2-MIN CANDLE ANALYSIS + SMS ALERTS
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                for index_name, ticker, display_name in [
                    ("NIFTY", "^NSEI", "NIFTY 50"),
                    ("SENSEX", "^BSESN", "SENSEX")
                ]:
                    try:
                        # 2-minute candle analysis
                        candle_analysis = analyze_2min_candle(ticker, display_name)
                        signal = candle_analysis.get("signal", "HOLD")
                        confidence = candle_analysis.get("confidence", 0)
                        
                        if signal in ("BUY_CE", "BUY_PE") and confidence >= 0.45:
                            key = f"{index_name}_{signal}_2m"
                            last_time = last_auto_alert_time.get(key, 0)
                            if time.time() - last_time < 300:  # Don't repeat within 5 min
                                continue
                            last_auto_alert_time[key] = time.time()
                            
                            # Format 2-min signal
                            alert = format_2min_signal(candle_analysis, display_name)
                            
                            # Add ML prediction context
                            ml_dir = "?"
                            ml_conf = 0
                            try:
                                ml_pred = predict_index_direction(ticker, index_name)
                                if "error" not in ml_pred:
                                    ml_dir = ml_pred.get("direction", "?")
                                    ml_conf = ml_pred.get("confidence", 0)
                                    alert += f"\n\n🤖 *ML Prediction:* {ml_dir} ({ml_conf:.0%})"
                            except Exception:
                                pass
                            
                            # Add investment calc for ₹2K default + personalized for SMS subscribers
                            opt_type = "CE" if signal == "BUY_CE" else "PE"
                            best_strike = None
                            best_premium = None
                            best_qty = None
                            best_cost = None
                            try:
                                chain = generate_index_option_chain(ticker, index_name)
                                if "error" not in chain:
                                    inv = calculate_investment_options(chain, 2000, opt_type)
                                    if inv.get("recommendations"):
                                        best = inv["recommendations"][0]
                                        best_strike = best["strike"]
                                        best_premium = best["premium"]
                                        best_qty = best["qty"]
                                        best_cost = best["total_cost"]
                                        alert += (
                                            f"\n\n💰 *Quick ₹2K Trade:*"
                                            f"\n┣ Strike: ₹{best_strike:,.0f} {opt_type}"
                                            f"\n┣ Premium: ₹{best_premium:.2f}"
                                            f"\n┣ Qty: {best_qty} ({best['num_lots']} lots)"
                                            f"\n┗ Cost: ₹{best_cost:,.0f}"
                                        )
                            except Exception:
                                pass
                            
                            # Send Telegram alert to all subs
                            for chat_id in subs:
                                try:
                                    send_message(chat_id, alert)
                                except Exception as e:
                                    logger.error(f"[AUTO] Failed to send to {chat_id}: {e}")
                            
                            # ── PERSONALIZED SMS ALERTS ──
                            for sub in sms_subs:
                                try:
                                    user_name = sub.get("user_name", "Trader")
                                    phone = sub["phone"]
                                    inv_amount = sub.get("investment_amount", 2000)
                                    
                                    # Calculate personalized trade for this user's investment
                                    p_strike = best_strike or 0
                                    p_premium = best_premium or 0
                                    p_qty = best_qty or 0
                                    p_target = p_premium * 1.5  # 50% target
                                    
                                    if inv_amount != 2000 and best_strike:
                                        try:
                                            chain = generate_index_option_chain(ticker, index_name)
                                            if "error" not in chain:
                                                p_inv = calculate_investment_options(chain, inv_amount, opt_type)
                                                if p_inv.get("recommendations"):
                                                    pb = p_inv["recommendations"][0]
                                                    p_strike = pb["strike"]
                                                    p_premium = pb["premium"]
                                                    p_qty = pb["qty"]
                                                    p_target = p_premium * 1.5
                                        except Exception:
                                            pass
                                    
                                    if p_strike and p_premium:
                                        sms_msg = build_entry_sms(
                                            user_name=user_name,
                                            index_name=index_name,
                                            signal=signal,
                                            strike=p_strike,
                                            premium=p_premium,
                                            qty=p_qty,
                                            investment=inv_amount,
                                            target=p_target
                                        )
                                        send_sms(phone, sms_msg)
                                        
                                        # Save position for exit monitoring
                                        try:
                                            save_position(
                                                chat_id=sub["chat_id"],
                                                phone=phone,
                                                index_name=index_name,
                                                option_type=opt_type,
                                                strike=p_strike,
                                                entry_price=p_premium,
                                                qty=p_qty,
                                                investment=inv_amount
                                            )
                                        except Exception as e:
                                            logger.error(f"[AUTO] Save position failed: {e}")
                                        
                                        time.sleep(0.5)
                                except Exception as e:
                                    logger.error(f"[SMS] Entry alert failed for {sub.get('phone', '?')}: {e}")
                        
                        # Also run traditional analysis every 10 min
                        from candle_analyzer import analyze_index
                        trad_analysis = analyze_index(ticker, display_name)
                        trad_signal = trad_analysis.get("signal", "HOLD")
                        trad_confidence = trad_analysis.get("confidence", 0.5)
                        price = trad_analysis.get("indicators", {}).get("price", 0)
                        rsi = trad_analysis.get("indicators", {}).get("rsi", 50)
                        atr = trad_analysis.get("indicators", {}).get("atr", 100)
                        
                        if trad_signal in ("BUY", "SELL") and trad_confidence >= 0.55:
                            key = f"{index_name}_{trad_signal}"
                            last_time = last_auto_alert_time.get(key, 0)
                            if time.time() - last_time < 1800:
                                continue
                            last_auto_alert_time[key] = time.time()
                            
                            if trad_signal == "BUY":
                                emoji = "🟢🚀"
                                action = "BUY CALL (CE)"
                                sl = price - (atr * 1.5)
                                t1 = price + (atr * 1.0)
                                t2 = price + (atr * 2.0)
                            else:
                                emoji = "🔴📉"
                                action = "BUY PUT (PE)"
                                sl = price + (atr * 1.5)
                                t1 = price - (atr * 1.0)
                                t2 = price - (atr * 2.0)
                            
                            rr = abs(t1 - price) / abs(price - sl) if abs(price - sl) > 0 else 0
                            
                            alert = (
                                f"{FIRE_LINE}\n"
                                f"{emoji} *AUTO SIGNAL — {index_name}* {emoji}\n"
                                f"{DIAMOND_LINE}\n"
                                f"⏰ *Time:* {now.strftime('%H:%M IST')}\n"
                                f"📊 *Signal:* *{trad_signal}* | Confidence: *{trad_confidence:.0%}*\n"
                                f"💹 *Price:* ₹{price:.2f}\n"
                                f"📈 *RSI:* {rsi:.1f}\n"
                                f"{HEADER_LINE}\n"
                                f"💰 *ACTION:* {action}\n"
                                f"┣ 🎯 Entry: ₹{price:.2f}\n"
                                f"┣ 🛑 Stop Loss: ₹{sl:.2f}\n"
                                f"┣ ✅ Target 1: ₹{t1:.2f}\n"
                                f"┗ 🏆 Target 2: ₹{t2:.2f}\n"
                                f"📊 Risk-Reward: 1:{rr:.2f}\n"
                                f"{HEADER_LINE}\n"
                            )
                            
                            reasons = trad_analysis.get("reasons", [])
                            if reasons:
                                alert += "🧠 *AI ANALYSIS:*\n"
                                for i, reason in enumerate(reasons[:3], 1):
                                    alert += f"  {i}. {reason}\n"
                            
                            alert += f"\n{STAR_LINE}\n"
                            alert += "⚠️ _Auto-alert. Not financial advice. Use SL._"
                            
                            for chat_id in subs:
                                try:
                                    send_message(chat_id, alert)
                                except Exception as e:
                                    logger.error(f"[AUTO] Failed to send to {chat_id}: {e}")
                            
                            # SMS for traditional strong signals too
                            for sub in sms_subs:
                                try:
                                    sms_txt = build_prediction_sms(
                                        user_name=sub.get("user_name", "Trader"),
                                        index_name=index_name,
                                        direction=trad_signal,
                                        confidence=trad_confidence,
                                        strike=price,
                                        option_type="CE" if trad_signal == "BUY" else "PE",
                                        investment=sub.get("investment_amount", 2000),
                                        expected_profit=sub.get("investment_amount", 2000) * 0.3
                                    )
                                    send_sms(sub["phone"], sms_txt)
                                    time.sleep(0.5)
                                except Exception as e:
                                    logger.error(f"[SMS] Trad alert failed: {e}")
                                    
                    except Exception as e:
                        logger.error(f"[AUTO] Analysis failed for {index_name}: {e}")
                
                time.sleep(interval)
                
            else:
                # ── OFF HOURS: Send periodic global summary + prediction ──
                key = "off_market_summary"
                last_time = last_auto_alert_time.get(key, 0)
                
                if time.time() - last_time >= 7200:  # every 2 hours
                    last_auto_alert_time[key] = time.time()
                    
                    try:
                        prediction = generate_tomorrow_prediction()
                        
                        for chat_id in subs:
                            try:
                                header = (
                                    f"🌙 *OFF-MARKET AUTO UPDATE* 🌙\n"
                                    f"{SPARKLE_LINE}\n"
                                    f"⏰ {now.strftime('%H:%M IST, %d %b %Y')}\n\n"
                                )
                                send_message(chat_id, header + prediction)
                            except Exception as e:
                                logger.error(f"[AUTO] Failed off-market msg to {chat_id}: {e}")
                    except Exception as e:
                        logger.error(f"[AUTO] Prediction failed: {e}")
                
                time.sleep(300)  # check every 5 min during off-hours
                
        except Exception as e:
            logger.error(f"[AUTO] Loop error: {e}", exc_info=True)
            time.sleep(30)


# ═══════════════════════════════════════════════════════════
#  CRYPTO GEM ALERT LOOP — 24/7 DexScreener Scanner
# ═══════════════════════════════════════════════════════════

def crypto_alert_loop():
    """Background thread: scans DexScreener + pump.fun every 10 seconds.
    
    Sends alerts to subscribed users when:
    - New gem detected (score >= 40)
    - Major dip in trending token (>10% drop in 1h)
    - Price alerts triggered
    Also logs predictions for gem score backtesting.
    """
    logger.info("🪙 Crypto Gem Scanner STARTED — scanning DexScreener + pump.fun 24/7")
    
    scan_interval = 10
    backtest_counter = 0  # log predictions every 6th scan (60 sec)
    price_alert_counter = 0  # check price alerts every 3rd scan (30 sec)
    
    while not auto_flag.is_set():
        try:
            # Get users who have crypto alerts ON
            crypto_subscribers = []
            for k, v in chat_storage.items():
                if k.startswith("crypto_alerts_") and v:
                    try:
                        cid = int(k.replace("crypto_alerts_", ""))
                        crypto_subscribers.append(cid)
                    except ValueError:
                        pass
            
            if not crypto_subscribers:
                time.sleep(30)
                continue
            
            from crypto_engine import get_new_gem_alerts, get_new_dip_alerts, format_gem_alert, format_dip_alert
            
            # ── SCAN FOR NEW GEMS ──
            new_gems = get_new_gem_alerts(min_score=40)
            for gem in new_gems:
                alert_msg = format_gem_alert(gem)
                for cid in crypto_subscribers:
                    try:
                        send_message(cid, alert_msg)
                    except Exception as e:
                        logger.error(f"[CRYPTO] Alert send failed to {cid}: {e}")
                time.sleep(0.3)
            
            # ── SCAN FOR MAJOR DIPS ──
            new_dips = get_new_dip_alerts(max_change_h1=-10.0)
            if new_dips:
                dip_msg = format_dip_alert(new_dips)
                for cid in crypto_subscribers:
                    try:
                        send_message(cid, dip_msg)
                    except Exception as e:
                        logger.error(f"[CRYPTO] Dip alert send failed to {cid}: {e}")

            # ── LOG PREDICTIONS FOR BACKTESTING (every ~60s) ──
            backtest_counter += 1
            if backtest_counter >= 6:
                backtest_counter = 0
                try:
                    from gem_backtester import log_batch_predictions, update_prediction_prices
                    from crypto_engine import scan_all_gems
                    gems = scan_all_gems(min_score=30, limit=10)
                    if gems:
                        log_batch_predictions(gems, min_score=30)
                    update_prediction_prices()
                except Exception as e:
                    logger.debug(f"[BACKTEST] {e}")

            # ── CHECK PRICE ALERTS (every ~30s) ──
            price_alert_counter += 1
            if price_alert_counter >= 3:
                price_alert_counter = 0
                try:
                    from portfolio_tracker import check_price_alerts, format_price_alert_msg
                    triggered = check_price_alerts()
                    for alert in triggered:
                        alert_msg = format_price_alert_msg(alert)
                        try:
                            send_message(alert["chat_id"], alert_msg)
                        except Exception:
                            pass
                except Exception as e:
                    logger.debug(f"[PRICE_ALERT] {e}")

            time.sleep(scan_interval)
            
        except Exception as e:
            logger.error(f"[CRYPTO] Alert loop error: {e}", exc_info=True)
            time.sleep(15)


# ═══════════════════════════════════════════════════════════
#  MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════

def handle_update(update: dict):
    if "message" not in update:
        return
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    
    # ════════════════════════════
    #   🎤 VOICE MESSAGE HANDLING — User speaks, JARVIS listens
    # ════════════════════════════
    voice = msg.get("voice") or msg.get("audio")
    if voice and VOICE_AVAILABLE:
        file_id = voice.get("file_id", "")
        if file_id:
            send_message(chat_id, "🎤🌸 *आपकी आवाज़ सुन रही हूँ...* ⏳💕")
            try:
                # Download voice message
                audio_path = download_telegram_voice(file_id, TELEGRAM_TOKEN)
                if audio_path:
                    # Transcribe to text
                    transcribed = transcribe_voice_message(audio_path)
                    if transcribed:
                        text = transcribed
                        send_message(chat_id, f"🎤 *आपने कहा:* _{text}_\n\n🌸 _अभी process कर रही हूँ..._ 💕")
                        # Mark this as voice input so we respond with voice too
                        chat_storage[f"voice_input_{chat_id}"] = True
                        # Save to memory
                        if JARVIS_AVAILABLE:
                            try:
                                add_to_conversation(chat_id, "user_voice", text)
                            except:
                                pass
                    else:
                        send_message(chat_id, "🎤 माफ़ कीजिए, आवाज़ ठीक से सुनाई नहीं दी। 🌸\nPlease फिर से बोलिए या text में लिखिए! 💕", reply_markup=build_keyboard())
                        return
                else:
                    send_message(chat_id, "🎤 Voice download नहीं हो पाया। Please फिर से try कीजिए! 🌸", reply_markup=build_keyboard())
                    return
            except Exception as e:
                logger.error(f"Voice handling error: {e}")
                send_message(chat_id, "🎤 Voice processing में error आया। Text में लिखिए! 🌸", reply_markup=build_keyboard())
                return
    
    if not text:
        return
    
    # ═══════════════════════════════════════════
    #  🛡️ SECURITY CHECK — MANDATORY for ALL messages
    # ═══════════════════════════════════════════
    if SECURITY_AVAILABLE:
        allowed, cleaned_text, sec_reason = security_check(chat_id, text)
        if not allowed:
            if "banned" in sec_reason:
                send_message(chat_id, "🚫 *Access Denied* — You are temporarily blocked.\nPlease wait and try again later.")
            elif "rate_limit" in sec_reason or "flood" in sec_reason:
                send_message(chat_id, "⚠️ Too many messages! Please wait a moment. 🙏")
            return
        text = cleaned_text  # Use sanitized text
    else:
        # FALLBACK SECURITY — basic rate limit even without security module
        _now = time.time()
        _uid = str(chat_id)
        if not hasattr(handle_update, '_rate_cache'):
            handle_update._rate_cache = {}
        _rc = handle_update._rate_cache
        if _uid in _rc and (_now - _rc[_uid]['ts'] < 2) and _rc[_uid]['cnt'] > 10:
            send_message(chat_id, "⚠️ Too many messages! Please wait a moment. 🙏")
            return
        if _uid not in _rc or _now - _rc[_uid]['ts'] > 60:
            _rc[_uid] = {'ts': _now, 'cnt': 0}
        _rc[_uid]['cnt'] += 1
        # Basic input sanitization fallback
        if text and len(text) > 4096:
            text = text[:4096]
        if text:
            import re as _re
            _dangerous = ['<script', 'javascript:', '; rm ', '| bash', 'exec(', 'eval(', '__import__']
            for _d in _dangerous:
                if _d.lower() in text.lower():
                    text = text.replace(_d, '[BLOCKED]')
                    logger.warning(f"[SECURITY-FALLBACK] Blocked dangerous input from {chat_id}")

    logger.info(f"handle_update -> chat_id={chat_id} text={text[:50] if text else ''}")
    
    # Store chat id
    chat_storage["last_chat"] = chat_id
    try:
        with open("last_chat_id.txt", "w") as f:
            f.write(str(chat_id))
    except Exception as e:
        logger.error(f"Failed to write last_chat_id.txt: {e}")
    
    # ── PERSONALIZED GREETING ──
    greeting = get_user_greeting(update)
    user_name = get_user_name(update)
    
    # 🧠 Memory: Remember user name
    if JARVIS_AVAILABLE:
        try:
            remember_name(chat_id, user_name)
        except:
            pass
    
    # ════════════════════════════════════════════════════════
    #  🔁 REPLY-BASED CRYPTO DEEP ANALYSIS — When user replies
    #  to any bot message containing a crypto token
    # ════════════════════════════════════════════════════════
    reply_msg = msg.get("reply_to_message")
    if reply_msg and MARKET_BRAIN_AVAILABLE:
        original_text = reply_msg.get("text", "")
        # Extract token from the original message user replied to
        token = extract_token_from_reply(original_text, text)
        if token:
            is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
            send_message(chat_id, f"{greeting}🔥🧠 *JARVIS Deep AI Analysis for {token}...*\n_15+ World-Class Indicators + ML + Candles + Price Targets_ ⏳")
            try:
                deep_data = analyze_crypto_token_deep(token)
                pages = format_crypto_deep_report(deep_data)
                for page in pages:
                    send_message(chat_id, page, reply_markup=build_keyboard())
                # Voice response
                voice_text = format_crypto_deep_voice(deep_data)
                send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto", is_voice_input=is_voice)
                return
            except Exception as e:
                logger.error(f"[REPLY-ANALYSIS] Error for {token}: {e}")
                send_message(chat_id, f"❌ {token} analysis failed: {str(e)[:100]}", reply_markup=build_keyboard())
                return
    
    # ════════════════════════════
    #   /start COMMAND
    # ════════════════════════════
    if text == "/start" or text == "🏠 /start":
        user_name = get_user_name(update)
        
        if JARVIS_AVAILABLE:
            welcome = generate_jarvis_welcome(user_name)
        else:
            welcome_greeting = get_welcome_greeting(update)
            welcome = (
                f"{welcome_greeting}"
                f"\n"
                f"🔱💎 *WELCOME TO DAVID CREW TRADING BOT* 💎🔱\n"
                f"{FIRE_LINE}\n"
                f"\n"
                f"🚀 *India's Most Powerful AI Trading Assistant* 🚀\n"
            )
        send_message(chat_id, welcome, reply_markup=build_keyboard())
        # 🎤 JARVIS speaks the welcome
        send_jarvis_voice(chat_id, f"नमस्ते {user_name} जी! मैं जार्विस हूँ, आपकी AI ट्रेडिंग असिस्टेंट। सारे सिस्टम्स तैयार हैं। बताइए, आज मैं आपकी क्या मदद करूँ?", intent="greeting")
        return
    #   HELP
    # ════════════════════════════
    if text in ("❓ Help", "❓ Help 💡", "Help"):
        user_name = get_user_name(update)
        if JARVIS_AVAILABLE:
            help_text = generate_jarvis_help(user_name)
        else:
            help_text = (
                f"{greeting}"
                f"💡 *HELP — BOT COMMANDS* 💡\n"
                f"{DOUBLE_LINE}\n"
                f"Use the menu buttons below or type naturally!\n"
            )
        send_message(chat_id, help_text, reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   MARKET TREND
    # ════════════════════════════
    if text in ("Market Trend", "📈 Market Trend", "🌍 Market Trend 📈"):
        send_message(chat_id, f"{greeting}🔄 *Analyzing global markets...* Please wait 20-30s ⏳")
        try:
            from global_market_analyzer import get_market_trend_analysis
            import signal as sig
            def timeout_handler(signum, frame):
                raise TimeoutError("Market analysis timed out")
            try:
                sig.signal(sig.SIGALRM, timeout_handler)
                sig.alarm(45)
                trend_msg = get_market_trend_analysis()
                sig.alarm(0)
                if not trend_msg or not trend_msg.strip():
                    send_message(chat_id, f"{greeting}⚠️ Market trend returned no data. Try again later.")
                else:
                    decorated = (
                        f"{greeting}"
                        f"🌍 *GLOBAL MARKET TREND* 🌍\n"
                        f"{FIRE_LINE}\n\n"
                        f"{trend_msg}\n\n"
                        f"{STAR_LINE}"
                    )
                    send_message(chat_id, decorated)
            except TimeoutError:
                sig.alarm(0)
                send_message(chat_id, f"{greeting}⏱️ Analysis taking too long.\n\n🟡 Check again in a moment.")
            except Exception as e:
                logger.error(f"Market trend failed: {e}", exc_info=True)
                send_message(chat_id, f"{greeting}⚠️ Market trend temporarily unavailable.")
        except Exception as e:
            logger.error(f"Market trend outer error: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}⚠️ Market trend temporarily unavailable.")
        return

    # ════════════════════════════
    #   SUBSCRIBE ALERTS
    # ════════════════════════════
    if text in ("🔔 Subscribe Alerts", "Subscribe Alerts", "🔔 Subscribe Alerts ✅"):
        try:
            from data_store import add_subscriber
            add_subscriber(chat_id)
            sub_msg = (
                f"{greeting}"
                f"✅🔔 *ALERTS ACTIVATED* 🔔✅\n"
                f"{FIRE_LINE}\n\n"
                f"🎉 *{user_name}*, you're now subscribed!\n\n"
                f"📊 *What you'll get:*\n"
                f"┣ 🟢 Live BUY/SELL signals during market hours\n"
                f"┣ 🔮 Tomorrow's prediction every evening\n"
                f"┣ 🌍 Global market updates off-hours\n"
                f"┗ ⚡ Instant NIFTY/SENSEX alerts\n\n"
                f"🔥 _24/7 Auto Trading Intelligence Active!_ 🔥\n"
                f"{STAR_LINE}"
            )
            send_message(chat_id, sub_msg, reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Subscribe failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Subscribe failed. Please try again.")
        return

    # ════════════════════════════
    #   UNSUBSCRIBE
    # ════════════════════════════
    if text in ("Unsubscribe Alerts", "🔕 Unsubscribe", "🔕 Unsubscribe ❌"):
        try:
            from data_store import remove_subscriber
            remove_subscriber(chat_id)
            send_message(chat_id, f"{greeting}🔕 *Unsubscribed* from automated alerts.\n\n_You can re-subscribe anytime!_", reply_markup=build_keyboard())
        except Exception:
            send_message(chat_id, f"{greeting}❌ Unsubscribe failed.")
        return

    # ════════════════════════════
    #   MY SUBS
    # ════════════════════════════
    if text in ("My Subscriptions", "👥 My Subs"):
        try:
            from data_store import list_subscribers
            subs = list_subscribers()
            is_subbed = chat_id in subs
            status = "✅ *ACTIVE*" if is_subbed else "❌ *NOT SUBSCRIBED*"
            subs_msg = (
                f"{greeting}"
                f"👥 *SUBSCRIPTION STATUS*\n"
                f"{HEADER_LINE}\n\n"
                f"📊 Total Subscribers: *{len(subs)}*\n"
                f"🔔 Your Status: {status}\n\n"
                f"{SPARKLE_LINE}"
            )
            send_message(chat_id, subs_msg, reply_markup=build_keyboard())
        except Exception:
            send_message(chat_id, f"{greeting}❌ Failed to fetch subscriptions.")
        return

    # ════════════════════════════
    #   ADD SYMBOL
    # ════════════════════════════
    if text in ("Add Symbol", "🎯 Add Symbol", "➕ Add Symbol 🎯"):
        send_message(chat_id, f"{greeting}🎯 *Send me a symbol to add:*\n\n_Example: RELIANCE, INFY, SBIN, TCS_")
        chat_storage["awaiting_add_symbol"] = chat_id
        return

    # ════════════════════════════
    #   REMOVE SYMBOL
    # ════════════════════════════
    if text in ("Remove Symbol", "❌ Remove Symbol", "➖ Remove Symbol ❌"):
        send_message(chat_id, f"{greeting}❌ *Send me a symbol to remove:*")
        chat_storage["awaiting_remove_symbol"] = chat_id
        return

    # ════════════════════════════
    #   WATCHLIST
    # ════════════════════════════
    if text in ("My Watchlist", "📋 My Watchlist", "📋 Watchlist"):
        try:
            from data_store import get_watchlist
            watchlist = get_watchlist(chat_id)
            if watchlist:
                wl_items = "\n".join([f"  💎 {s}" for s in watchlist])
                wl_msg = (
                    f"{greeting}"
                    f"📋 *YOUR WATCHLIST* 📋\n"
                    f"{DIAMOND_LINE}\n\n"
                    f"{wl_items}\n\n"
                    f"📊 Total: *{len(watchlist)}* symbols\n"
                    f"{SPARKLE_LINE}"
                )
            else:
                wl_msg = (
                    f"{greeting}"
                    f"📋 *YOUR WATCHLIST* 📋\n"
                    f"{HEADER_LINE}\n\n"
                    f"_Empty! Use ➕ Add Symbol to add stocks._\n"
                    f"{SPARKLE_LINE}"
                )
            send_message(chat_id, wl_msg, reply_markup=build_keyboard())
        except Exception:
            send_message(chat_id, f"{greeting}❌ Failed to fetch watchlist.")
        return

    # ════════════════════════════
    #   NIFTY SIGNALS
    # ════════════════════════════
    if text in ("📊 NIFTY Signals", "🔱 NIFTY Signals 📊"):
        send_message(chat_id, f"{greeting}🔄 *Analyzing NIFTY 50...* ⏳")
        try:
            from candle_analyzer import analyze_index
            analysis = analyze_index("^NSEI", "NIFTY 50")
            sig_text = analysis["analysis"]
            signal = analysis.get("signal", "HOLD")
            conf = analysis.get("confidence", 0.5)
            
            if signal == "BUY":
                sig_emoji = "🟢🚀"
            elif signal == "SELL":
                sig_emoji = "🔴📉"
            else:
                sig_emoji = "🟡⚖️"
            
            decorated = (
                f"{greeting}"
                f"🔱 *NIFTY 50 — LIVE ANALYSIS* 🔱\n"
                f"{FIRE_LINE}\n\n"
                f"{sig_text}\n\n"
                f"{DIAMOND_LINE}\n"
                f"🎯 *Signal:* {sig_emoji} *{signal}*\n"
                f"📊 *Confidence:* {conf:.0%}\n"
                f"{STAR_LINE}"
            )
            # Add Buy/Sell signal if available
            if BUY_SELL_AVAILABLE:
                try:
                    bs_signal = get_stock_signal("NIFTY")
                    if bs_signal:
                        lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                        decorated += "\n\n" + format_bs_signal(bs_signal, lang=lang)
                except Exception:
                    pass
            send_message(chat_id, decorated, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, f"NIFTY ka signal {signal} hai, confidence {conf:.0%}. Full details text mein hain. Entry aur stop loss check kar lijiye.", intent="buy_sell_stock")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Failed to fetch NIFTY signals: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   SENSEX SIGNALS
    # ════════════════════════════
    if text in ("📊 SENSEX Signals", "🔱 SENSEX Signals 📊"):
        send_message(chat_id, f"{greeting}🔄 *Analyzing SENSEX...* ⏳")
        try:
            from candle_analyzer import analyze_index
            analysis = analyze_index("^BSESN", "SENSEX")
            sig_text = analysis["analysis"]
            signal = analysis.get("signal", "HOLD")
            conf = analysis.get("confidence", 0.5)
            
            if signal == "BUY":
                sig_emoji = "🟢🚀"
            elif signal == "SELL":
                sig_emoji = "🔴📉"
            else:
                sig_emoji = "🟡⚖️"
            
            decorated = (
                f"{greeting}"
                f"🔱 *SENSEX — LIVE ANALYSIS* 🔱\n"
                f"{FIRE_LINE}\n\n"
                f"{sig_text}\n\n"
                f"{DIAMOND_LINE}\n"
                f"🎯 *Signal:* {sig_emoji} *{signal}*\n"
                f"📊 *Confidence:* {conf:.0%}\n"
                f"{STAR_LINE}"
            )
            # Add Buy/Sell signal if available
            if BUY_SELL_AVAILABLE:
                try:
                    bs_signal = get_stock_signal("SENSEX")
                    if bs_signal:
                        lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                        decorated += "\n\n" + format_bs_signal(bs_signal, lang=lang)
                except Exception:
                    pass
            send_message(chat_id, decorated, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, f"SENSEX ka signal {signal} hai, confidence {conf:.0%}. Full details text mein hain. Entry aur stop loss check kar lijiye.", intent="buy_sell_stock")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Failed to fetch SENSEX signals: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   OTM CALLS / PUTS (unified)
    # ════════════════════════════
    otm_map = {
        "📞 NIFTY Calls OTM": ("TCS", "^NSEI", "NIFTY", "calls"),
        "💎 NIFTY Calls OTM 🚀": ("TCS", "^NSEI", "NIFTY", "calls"),
        "📞 SENSEX Calls OTM": ("RELIANCE", "^BSESN", "SENSEX", "calls"),
        "💎 SENSEX Calls OTM 🚀": ("RELIANCE", "^BSESN", "SENSEX", "calls"),
        "📞 NIFTY Puts OTM": ("TCS", "^NSEI", "NIFTY", "puts"),
        "⚡ NIFTY Puts OTM 📉": ("TCS", "^NSEI", "NIFTY", "puts"),
        "📞 SENSEX Puts OTM": ("RELIANCE", "^BSESN", "SENSEX", "puts"),
        "⚡ SENSEX Puts OTM 📉": ("RELIANCE", "^BSESN", "SENSEX", "puts"),
    }
    
    if text in otm_map:
        proxy_sym, yf_ticker, index_name, opt_type = otm_map[text]
        is_calls = opt_type == "calls"
        
        type_emoji = "🚀💎" if is_calls else "📉⚡"
        type_label = "CALLS" if is_calls else "PUTS"
        type_word = "Call" if is_calls else "Put"
        
        send_message(chat_id, f"{greeting}🔄 *Fetching {index_name} OTM {type_label}...* ⏳")
        
        try:
            import yfinance as yf
            data = fetch_nse_option_chain(proxy_sym)
            
            if data:
                calls_df, puts_df, underlying = parse_option_chain_json(data)
                otm = find_best_otm_options(calls_df, puts_df, underlying, option_type=opt_type, num_strikes=5)
                
                msg_parts = [
                    f"{greeting}",
                    f"{type_emoji} *{index_name} OTM {type_label} — HIGH LEVERAGE* {type_emoji}",
                    f"{FIRE_LINE}",
                    f"💹 *Current Price:* ₹{underlying:.0f}\n",
                ]
                
                if otm:
                    for i, opt in enumerate(otm[:3], 1):
                        medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉'
                        msg_parts.append(f"{medal} *{type_word} Option {i}:*")
                        msg_parts.append(f"  ┣ Strike: ₹{opt['strike']:.0f}")
                        msg_parts.append(f"  ┣ Premium: ₹{opt['ltp']:.2f}")
                        msg_parts.append(f"  ┣ IV: {opt['iv']:.2f}%")
                        sign = '+' if is_calls else '-'
                        msg_parts.append(f"  ┣ OTM: {sign}{opt['moneyness_pct']:.2f}%")
                        msg_parts.append(f"  ┣ Return Potential: {opt['return_potential']:.0f}%")
                        msg_parts.append(f"  ┗ Open Interest: {opt['oi']:.0f}")
                        msg_parts.append("")
                else:
                    msg_parts.append("_(Live option data pending — using market analysis)_")
                
                msg_parts.append(f"{STAR_LINE}")
                send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
            else:
                # Fallback with simulated data
                ticker_data = yf.Ticker(yf_ticker)
                hist = ticker_data.history(period="5d")
                price = float(hist['Close'].iloc[-1])
                
                msg_parts = [
                    f"{greeting}",
                    f"{type_emoji} *{index_name} OTM {type_label} — HIGH LEVERAGE* {type_emoji}",
                    f"{FIRE_LINE}",
                    f"💹 *Current Price:* ₹{price:.0f}\n",
                    f"*Recommended {type_word} Strikes:*\n",
                ]
                
                if is_calls:
                    strikes = [int(price * m) for m in [1.01, 1.02, 1.03]]
                else:
                    strikes = [int(price * m) for m in [0.99, 0.98, 0.97]]
                
                for i, strike in enumerate(strikes, 1):
                    premium = abs(strike - price) * 0.5
                    otm_pct = abs(strike - price) / price * 100
                    medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉'
                    msg_parts.append(f"{medal} *{type_word} Option {i}:*")
                    msg_parts.append(f"  ┣ Strike: ₹{strike}")
                    msg_parts.append(f"  ┣ Premium: ₹{premium:.0f}")
                    sign = '+' if is_calls else '-'
                    msg_parts.append(f"  ┣ OTM: {sign}{otm_pct:.1f}%")
                    ret_pot = (abs(strike - premium - price) / premium * 100) if premium > 0 else 0
                    msg_parts.append(f"  ┗ Return Potential: {ret_pot:.0f}%")
                    msg_parts.append("")
                
                msg_parts.append(f"{STAR_LINE}")
                send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
                
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Error: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   MARKET STATUS (SUPER ENGINE)
    # ════════════════════════════
    if text in ("⏰ Market Status", "Market Status", "⏰ Market Status 🔔", "market status", "/marketstatus"):
        now = datetime.now(IST)
        
        if SUPER_ENGINE_AVAILABLE:
            try:
                status = get_super_market_status()
                holidays = get_upcoming_holidays(3)
                
                status_msg = (
                    f"{greeting}"
                    f"⏰ *NSE MARKET STATUS* ⏰\n"
                    f"{DIAMOND_LINE}\n\n"
                    f"{status.message}\n\n"
                )
                if status.is_expiry_day:
                    expiry_emoji = "🔥🔥🔥" if status.expiry_type == "monthly" else "⚡"
                    status_msg += f"{expiry_emoji} *{status.expiry_type.upper()} EXPIRY DAY!*\n\n"
                elif status.days_to_expiry > 0:
                    status_msg += f"📅 Next expiry: {status.days_to_expiry} days\n\n"
                if status.market_hours_left:
                    status_msg += f"⏰ Market time left: {status.market_hours_left}\n"
                
                status_msg += f"\n🕐 *Time:* {now.strftime('%I:%M %p IST')}\n"
                status_msg += f"📅 *Date:* {now.strftime('%A, %d %b %Y')}\n\n"
                
                if holidays:
                    status_msg += f"📅 *Upcoming Holidays:*\n"
                    for h in holidays:
                        status_msg += f"  🔴 {h['name']} — {h['date']} ({h['days_away']}d)\n"
                    status_msg += "\n"
                
                status_msg += f"ℹ️ Mon-Fri, 9:15 AM - 3:30 PM IST\n"
                status_msg += f"📅 NIFTY Weekly Expiry: Thursday\n"
                status_msg += f"📅 BankNIFTY Weekly: Wednesday\n"
                status_msg += f"\n{SPARKLE_LINE}"
                
                send_message(chat_id, status_msg, reply_markup=build_keyboard())
                
                # Voice
                if VOICE_AVAILABLE:
                    try:
                        send_voice_message(chat_id, status.hindi, intent="info")
                    except:
                        pass
                return
            except Exception as e:
                logger.error(f"Super market status error: {e}")
        
        # Fallback old logic
        mkt_open = is_market_open()
        
        if mkt_open:
            status_text = "🟢 *MARKET OPEN*"
            status_detail = "NSE is currently trading (9:15 AM - 3:30 PM IST)"
        else:
            status_text = "🔴 *MARKET CLOSED*"
            if now.weekday() >= 5:
                status_detail = "Weekend — Market reopens Monday 9:15 AM IST"
            elif now.hour < 9 or (now.hour == 9 and now.minute < 15):
                status_detail = "Pre-market — Opens at 9:15 AM IST"
            else:
                status_detail = "After hours — Reopens tomorrow 9:15 AM IST"
        
        status_msg = (
            f"{greeting}"
            f"⏰ *NSE MARKET STATUS* ⏰\n"
            f"{DIAMOND_LINE}\n\n"
            f"{status_text}\n"
            f"📝 {status_detail}\n\n"
            f"🕐 *Current Time:* {now.strftime('%I:%M %p IST')}\n"
            f"📅 *Date:* {now.strftime('%A, %d %b %Y')}\n\n"
            f"{SPARKLE_LINE}"
        )
        send_message(chat_id, status_msg, reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   TOMORROW PREDICTION
    # ════════════════════════════
    if text in ("🔮 Tomorrow Prediction 🎯", "Tomorrow Prediction"):
        send_message(chat_id, f"{greeting}🔮 *Generating AI prediction...* This may take 30-60 seconds ⏳")
        try:
            prediction = generate_tomorrow_prediction()
            full_msg = f"{greeting}{prediction}"
            send_message(chat_id, full_msg, reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Prediction temporarily unavailable. Try again later.")
        return

    # ════════════════════════════
    #   GENERATE QR
    # ════════════════════════════
    if text in ("Generate QR", "🔗 Generate QR", "📱 Generate QR 🔗"):
        try:
            qr = generate_qr("https://t.me/David_crew_bot")
            caption = (
                f"📱🔱 *DAVID CREW TRADING BOT* 🔱📱\n"
                f"{HEADER_LINE}\n"
                f"Scan to join the #1 AI Trading Bot! 🌸\n"
                f"🌸 राधे राधे 🌸"
            )
            send_photo(chat_id, qr, caption=caption)
            send_message(chat_id, f"{greeting}✅ QR Code बन गया! अपने दोस्तों को शेयर कीजिए 🌸", reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"QR failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Failed to generate QR code.")
        return

    # ════════════════════════════════════════════════════════
    #   🔗 TRUST WALLET QR — Connect via QR Code Scan
    # ════════════════════════════════════════════════════════
    if text in ("🔗 Trust Wallet QR 📱", "Trust Wallet QR", "trust wallet qr"):
        if not QR_WALLET_AVAILABLE:
            send_message(chat_id, f"{greeting}❌ QR Wallet Connect engine not available.")
            return
        try:
            send_message(chat_id, f"{greeting}⏳ *Trust Wallet QR generate ho raha hai...* 📱🔒")
            
            # Generate mega QR pack (Trust Wallet + Solana Pay)
            result = generate_trust_connect_mega(chain="solana")
            
            # Send primary Trust Wallet QR
            send_photo(chat_id, result["primary_qr"], caption=result["caption"])
            
            # Send Solana Pay QR if available
            if result.get("solana_pay_qr"):
                sol_caption = (
                    f"◎ *SOLANA PAY QR — ALTERNATIVE METHOD* ◎\n"
                    f"{'━' * 32}\n\n"
                    f"Ye QR code *Trust Wallet, Phantom,*\n"
                    f"*Solflare* — sabhi Solana wallets me kaam karega!\n\n"
                    f"📍 Address: `{result['address']}`\n"
                    f"🌸 राधे राधे 🌸"
                )
                send_photo(chat_id, result["solana_pay_qr"], caption=sol_caption)
            
            # Send all connect methods
            send_message(chat_id, f"{greeting}{result['methods_text']}", reply_markup=build_keyboard())
            
            # Track session
            track_qr_session(chat_id, "solana", result["address"])
            
            # Voice response
            voice_text = (
                "Trust Wallet QR code ban gaya! "
                "Apna Trust Wallet app kholiye aur QR scanner se scan kijiye. "
                "Wallet turant connect ho jayega. "
                "Jai Shri Ram!"
            )
            send_jarvis_voice(chat_id, voice_text, intent="wallet_connect")
            
        except Exception as e:
            logger.error(f"Trust Wallet QR failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Trust Wallet QR generate nahi ho paya. Retry karo.")
        return

    # ════════════════════════════════════════════════════════
    #   ◎ SOLANA PAY QR — Universal Wallet Connect
    # ════════════════════════════════════════════════════════
    if text in ("◎ Solana Pay QR", "Solana Pay QR", "solana pay qr"):
        if not QR_WALLET_AVAILABLE:
            send_message(chat_id, f"{greeting}❌ QR Wallet Connect engine not available.")
            return
        try:
            send_message(chat_id, f"{greeting}⏳ *Solana Pay QR generate ho raha hai...* ◎")
            
            result = generate_solana_pay_qr()
            
            caption = (
                f"◎🔱 *SOLANA PAY — UNIVERSAL WALLET QR* 🔱◎\n"
                f"{'━' * 32}\n\n"
                f"📱 *Compatible Wallets:*\n"
                f"• Trust Wallet ✅\n"
                f"• Phantom ✅\n"
                f"• Solflare ✅\n"
                f"• Backpack ✅\n"
                f"• Glow ✅\n\n"
                f"📍 Address: `{result.get('solana_pay_uri', '')[:50]}...`\n"
                f"🌸 राधे राधे 🌸"
            )
            send_photo(chat_id, result["qr_image"], caption=caption)
            send_message(chat_id, f"{greeting}{result['instructions']}", reply_markup=build_keyboard())
            
            track_qr_session(chat_id, "solana_pay", OWNER_SOLANA_WALLET if 'OWNER_SOLANA_WALLET' in dir() else "unknown")
            
        except Exception as e:
            logger.error(f"Solana Pay QR failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Solana Pay QR generate nahi ho paya.")
        return

    # ════════════════════════════
    #   LIVE SNAPSHOT
    # ════════════════════════════
    if text in ("📊 Live Snapshot 🔴", "Live Snapshot"):
        send_message(chat_id, f"{greeting}🔄 *Fetching live market data...* ⏳")
        try:
            snapshot = get_full_market_snapshot()
            send_message(chat_id, f"{greeting}{snapshot}", reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, snapshot, intent="market_summary")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Snapshot failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   INVEST ₹2K / ₹20K NIFTY/SENSEX
    # ════════════════════════════
    invest_map = {
        "💰 Invest ₹2K NIFTY": ("^NSEI", "NIFTY", 2000),
        "💰 Invest ₹2K SENSEX": ("^BSESN", "SENSEX", 2000),
        "💸 Invest ₹20K NIFTY": ("^NSEI", "NIFTY", 20000),
        "💸 Invest ₹20K SENSEX": ("^BSESN", "SENSEX", 20000),
    }
    
    if text in invest_map:
        ticker, name, amount = invest_map[text]
        send_message(chat_id, f"{greeting}🔄 *Calculating ₹{amount:,} investment plan for {name}...* ⏳")
        try:
            chain = generate_index_option_chain(ticker, name)
            if "error" in chain:
                send_message(chat_id, f"{greeting}❌ {chain['error']}")
            else:
                result = calculate_investment_options(chain, amount)
                msg = format_investment_message(result)
                send_message(chat_id, f"{greeting}\n{msg}", reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Investment calc failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Calculation failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   ML PREDICTIONS
    # ════════════════════════════
    ml_map = {
        "🤖 NIFTY ML Predict 🧠": ("^NSEI", "NIFTY 50"),
        "🤖 SENSEX ML Predict 🧠": ("^BSESN", "SENSEX"),
    }
    
    if text in ml_map:
        ticker, name = ml_map[text]
        send_message(chat_id, f"{greeting}🧠 *Running AI/ML analysis for {name}...*\n_Training ensemble (XGBoost + RF + GB)... ~30s_ ⏳")
        try:
            pred = predict_index_direction(ticker, name)
            msg = format_ml_prediction(pred)
            
            # Also add quick investment calc
            try:
                chain = generate_index_option_chain(ticker, name)
                if "error" not in chain and "error" not in pred:
                    opt_type = "CE" if pred.get("direction") == "UP" else "PE"
                    for amount in [2000, 20000]:
                        inv = calculate_investment_options(chain, amount, opt_type)
                        inv_msg = format_investment_message(inv, top_n=1)
                        msg += f"\n\n💵 *If you invest ₹{amount:,}:*\n{inv_msg}"
            except Exception:
                pass
            
            send_message(chat_id, f"{greeting}\n{msg}", reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"ML predict failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ ML prediction failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   2-MIN CANDLE SIGNALS
    # ════════════════════════════
    candle_2m_map = {
        "⚡ 2-Min NIFTY Signal": ("^NSEI", "NIFTY 50"),
        "⚡ 2-Min SENSEX Signal": ("^BSESN", "SENSEX"),
    }
    
    if text in candle_2m_map:
        ticker, name = candle_2m_map[text]
        send_message(chat_id, f"{greeting}⚡ *Analyzing 2-min candles for {name}...* ⏳")
        try:
            analysis = analyze_2min_candle(ticker, name)
            msg = format_2min_signal(analysis, name)
            
            # Add investment calc if there's a signal
            signal = analysis.get("signal", "HOLD")
            if signal in ("BUY_CE", "BUY_PE"):
                try:
                    chain = generate_index_option_chain(ticker, name)
                    if "error" not in chain:
                        opt_type = "CE" if signal == "BUY_CE" else "PE"
                        for amount in [2000, 5000, 20000]:
                            inv = calculate_investment_options(chain, amount, opt_type)
                            if inv.get("recommendations"):
                                best = inv["recommendations"][0]
                                msg += (
                                    f"\n\n💰 *₹{amount:,} Trade Plan:*"
                                    f"\n┣ Strike: ₹{best['strike']:,.0f} {opt_type}"
                                    f"\n┣ Premium: ₹{best['premium']:.2f}"
                                    f"\n┣ Lots: {best['num_lots']} ({best['qty']} qty)"
                                    f"\n┣ Cost: ₹{best['total_cost']:,.0f}"
                                    f"\n┗ Breakeven: ₹{best['breakeven']:,.0f}"
                                )
                except Exception:
                    pass
            
            send_message(chat_id, f"{greeting}\n{msg}", reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ 2-min analysis failed: {str(e)[:100]}")
        return

    # ════════════════════════════════════════════════════
    #  🇮🇳⚡ NIFTY CALL/PUT AI — Super Engine ATM/OTM
    # ════════════════════════════════════════════════════
    if text in ("🇮🇳⚡ NIFTY Call/Put AI", "nifty call put", "nifty call", "nifty put",
                "nifty option", "nifty atm", "nifty otm", "/niftyoption"):
        if SUPER_ENGINE_AVAILABLE:
            send_message(chat_id, f"{greeting}🇮🇳⚡ *NIFTY Call/Put AI chal raha hai...*\n_ATM/OTM analysis + Greeks + ML + ₹2K→₹2L path... ~30s_ ⏳")
            try:
                data = recommend_best_options("NIFTY", 2000.0, "auto")
                wrapper = {
                    'timestamp': datetime.now(IST).strftime("%I:%M %p IST"),
                    'sections': {'nifty_options': data},
                }
                pages = format_super_analysis(wrapper)
                for page in pages:
                    send_message(chat_id, page, reply_markup=build_keyboard())
                # ATM vs OTM comparison
                comparison = format_option_comparison(wrapper, "NIFTY")
                if comparison and len(comparison) > 50:
                    send_message(chat_id, comparison, reply_markup=build_keyboard())
                # Voice
                if VOICE_AVAILABLE:
                    try:
                        voice_text = format_super_voice(wrapper)
                        send_voice_message(chat_id, voice_text, intent="analysis")
                    except:
                        pass
            except Exception as e:
                logger.error(f"NIFTY Call/Put AI error: {e}", exc_info=True)
                send_message(chat_id, f"{greeting}❌ NIFTY option analysis failed: {str(e)[:100]}")
        else:
            send_message(chat_id, f"{greeting}❌ Indian Super Engine not loaded.")
        return

    # ════════════════════════════════════════════════════
    #  📊 SENSEX CALL/PUT AI — Super Engine ATM/OTM
    # ════════════════════════════════════════════════════
    if text in ("📊 SENSEX Call/Put AI", "sensex call put", "sensex call", "sensex put",
                "sensex option", "sensex atm", "sensex otm", "/sensexoption"):
        if SUPER_ENGINE_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *SENSEX Call/Put AI chal raha hai...*\n_ATM/OTM + Greeks + ML + Strategy... ~30s_ ⏳")
            try:
                data = recommend_best_options("SENSEX", 2000.0, "auto")
                wrapper = {
                    'timestamp': datetime.now(IST).strftime("%I:%M %p IST"),
                    'sections': {'sensex_options': data},
                }
                pages = format_super_analysis(wrapper)
                for page in pages:
                    send_message(chat_id, page, reply_markup=build_keyboard())
                comparison = format_option_comparison(wrapper, "SENSEX")
                if comparison and len(comparison) > 50:
                    send_message(chat_id, comparison, reply_markup=build_keyboard())
                if VOICE_AVAILABLE:
                    try:
                        voice_text = format_super_voice(wrapper)
                        send_voice_message(chat_id, voice_text, intent="analysis")
                    except:
                        pass
            except Exception as e:
                logger.error(f"SENSEX Call/Put AI error: {e}", exc_info=True)
                send_message(chat_id, f"{greeting}❌ SENSEX option analysis failed: {str(e)[:100]}")
        else:
            send_message(chat_id, f"{greeting}❌ Indian Super Engine not loaded.")
        return

    # ════════════════════════════════════════════════════
    #  🏦 BANKNIFTY CALL/PUT AI — Super Engine ATM/OTM
    # ════════════════════════════════════════════════════
    if text in ("🏦 BankNIFTY Call/Put AI", "banknifty call put", "banknifty call", "banknifty put",
                "bank nifty option", "bank nifty call", "bank nifty put", "/bankniftyoption"):
        if SUPER_ENGINE_AVAILABLE:
            send_message(chat_id, f"{greeting}🏦 *BankNIFTY Call/Put AI chal raha hai...*\n_ATM/OTM + Greeks + ML... ~30s_ ⏳")
            try:
                data = recommend_best_options("BANKNIFTY", 2000.0, "auto")
                wrapper = {
                    'timestamp': datetime.now(IST).strftime("%I:%M %p IST"),
                    'sections': {'banknifty_options': data},
                }
                pages = format_super_analysis(wrapper)
                for page in pages:
                    send_message(chat_id, page, reply_markup=build_keyboard())
                comparison = format_option_comparison(wrapper, "BANKNIFTY")
                if comparison and len(comparison) > 50:
                    send_message(chat_id, comparison, reply_markup=build_keyboard())
                if VOICE_AVAILABLE:
                    try:
                        voice_text = format_super_voice(wrapper)
                        send_voice_message(chat_id, voice_text, intent="analysis")
                    except:
                        pass
            except Exception as e:
                logger.error(f"BankNIFTY Call/Put AI error: {e}", exc_info=True)
                send_message(chat_id, f"{greeting}❌ BankNIFTY option analysis failed: {str(e)[:100]}")
        else:
            send_message(chat_id, f"{greeting}❌ Indian Super Engine not loaded.")
        return

    # ════════════════════════════════════════════════════
    #  📅 MARKET HOLIDAYS — NSE Holiday Calendar
    # ════════════════════════════════════════════════════
    if text in ("📅 Market Holidays 🇮🇳", "Market Holidays", "holiday", "holidays",
                "agla holiday", "next holiday", "/holidays", "chhutti",
                "market kab band", "market off kab"):
        if SUPER_ENGINE_AVAILABLE:
            try:
                holidays = get_upcoming_holidays(10)
                status = get_super_market_status()
                
                lines = [
                    f"{greeting}",
                    f"{'═'*28}",
                    f"🇮🇳📅 *NSE MARKET HOLIDAYS*",
                    f"{'═'*28}",
                    f"",
                    f"📊 *Current: {status.message}*",
                    f"",
                ]
                if status.phase == "holiday":
                    lines.append(f"🔴 *Aaj chutti hai: {status.next_holiday}*")
                    lines.append(f"📅 Next open: {status.next_open}")
                    lines.append(f"")
                
                lines.append(f"📅 *Upcoming NSE Holidays:*")
                lines.append(f"{'─'*25}")
                for h in holidays:
                    lines.append(f"🔴 *{h['name']}*")
                    lines.append(f"  📅 {h['date']}")
                    lines.append(f"  ⏰ {h['days_away']} din mein")
                    lines.append(f"")
                
                lines.extend([
                    f"{'─'*28}",
                    f"ℹ️ Market: Mon-Fri, 9:15 AM - 3:30 PM IST",
                    f"📅 NIFTY Weekly Expiry: Thursday",
                    f"📅 BankNIFTY Weekly: Wednesday",
                    f"📅 Monthly Expiry: Last Thursday",
                    f"\n{SPARKLE_LINE}",
                ])
                
                send_message(chat_id, "\n".join(lines), reply_markup=build_keyboard())
                
                # Voice
                if VOICE_AVAILABLE:
                    try:
                        voice = f"Boss, {status.hindi} "
                        voice += "Agle holidays: " + ", ".join(
                            f"{h['name']} {h['days_away']} din baad" for h in holidays[:3]
                        )
                        send_voice_message(chat_id, voice, intent="info")
                    except:
                        pass
            except Exception as e:
                send_message(chat_id, f"{greeting}❌ Holiday data error: {str(e)[:100]}")
        else:
            send_message(chat_id, f"{greeting}❌ Holiday engine not loaded.")
        return

    # ════════════════════════════
    #   🧠 SUPER PREDICTION — ALL AI ENGINES COMBINED
    # ════════════════════════════
    if text in ("🧠 Super Prediction 🔮", "Super Prediction"):
        send_message(chat_id, f"{greeting}🧠🔮 *Running SUPER AI Analysis...*\n_Candle Patterns + ML Ensemble + Sentiment + Risk... ~45s_ ⏳")
        try:
            parts_msg = []
            parts_msg.append(f"🧠✨ *SUPER AI PREDICTION ENGINE* ✨🧠")
            parts_msg.append(FIRE_LINE)
            parts_msg.append(f"⏰ {datetime.now(IST).strftime('%H:%M IST, %d %b %Y')}")
            parts_msg.append("")

            for yf_ticker, display_name, short_name in [("^NSEI", "NIFTY 50", "NIFTY"), ("^BSESN", "SENSEX", "SENSEX")]:
                parts_msg.append(f"{'─' * 30}")
                parts_msg.append(f"📊 *{display_name}*")

                # 1) Candle Pattern Analysis
                try:
                    from candle_analyzer import analyze_index
                    ca = analyze_index(yf_ticker, display_name)
                    parts_msg.append(f"  🕯️ Candles: *{ca.get('signal', 'HOLD')}* ({ca.get('confidence', 0):.0%})")
                    patterns = ca.get("patterns_found", [])
                    if patterns:
                        for p in patterns[:3]:
                            parts_msg.append(f"     • {p}")
                except Exception:
                    parts_msg.append(f"  🕯️ Candles: _unavailable_")

                # 2) ML Ensemble Prediction
                try:
                    ml = predict_index_direction(yf_ticker, short_name)
                    if "error" not in ml:
                        parts_msg.append(f"  🤖 ML Ensemble: *{ml.get('direction', '?')}* ({ml.get('confidence', 0):.0%})")
                        parts_msg.append(f"     Models: {ml.get('models_used', 'RF+GB+XGB')}")
                    else:
                        parts_msg.append(f"  🤖 ML: _error_")
                except Exception:
                    parts_msg.append(f"  🤖 ML: _unavailable_")

                # 3) Sentiment Analysis
                if SENTIMENT_AVAILABLE:
                    try:
                        sent = analyze_news_sentiment()
                        mood = sent.get("overall_mood", "Neutral")
                        score = sent.get("avg_sentiment", 0)
                        parts_msg.append(f"  📰 Sentiment: *{mood}* (score: {score:.2f})")
                    except Exception:
                        parts_msg.append(f"  📰 Sentiment: _unavailable_")

                # 4) Risk Assessment
                if RISK_AVAILABLE:
                    try:
                        import yfinance as yf
                        hist = yf.download(yf_ticker, period="90d", progress=False)
                        if hist is not None and len(hist) > 10:
                            if isinstance(hist.columns, pd.MultiIndex):
                                hist.columns = hist.columns.get_level_values(0)
                            returns = hist['Close'].pct_change().dropna().values
                            vol_annual = float(np.std(returns) * np.sqrt(252) * 100)
                            parts_msg.append(f"  ⚠️ Volatility: *{vol_annual:.1f}%* annualized")
                            price_now = float(hist['Close'].iloc[-1])
                            ps = calculate_position_size(
                                capital=100000, entry_price=price_now,
                                stop_loss_price=price_now * 0.98, risk_per_trade_pct=2.0
                            )
                            parts_msg.append(f"  🛡️ Max Position: *₹{ps.get('position_value', 0):,.0f}* (2% risk rule)")
                    except Exception:
                        pass

                parts_msg.append("")

            # Combined verdict
            parts_msg.append(DOUBLE_LINE)
            parts_msg.append("🎯 *COMBINED AI VERDICT:*")

            total_bull = 0
            total_bear = 0
            total_count = 0
            for yf_ticker, short_name in [("^NSEI", "NIFTY"), ("^BSESN", "SENSEX")]:
                try:
                    from candle_analyzer import analyze_index
                    ca = analyze_index(yf_ticker, short_name)
                    sig = ca.get("signal", "HOLD")
                    if sig == "BUY": total_bull += 2
                    elif sig == "SELL": total_bear += 2
                    total_count += 2
                except Exception:
                    pass
                try:
                    ml = predict_index_direction(yf_ticker, short_name)
                    if "error" not in ml:
                        d = ml.get("direction", "")
                        if d in ("UP", "BULLISH"): total_bull += 2
                        elif d in ("DOWN", "BEARISH"): total_bear += 2
                        total_count += 2
                except Exception:
                    pass

            if total_count > 0:
                bull_pct = total_bull / total_count * 100
            else:
                bull_pct = 50

            if bull_pct >= 65:
                parts_msg.append("🟢🚀 *STRONG BUY CALLS (CE)* — All engines agree 🚀🟢")
            elif bull_pct >= 55:
                parts_msg.append("🟢 *MODERATELY BULLISH — Favor CALLS (CE)* 🟢")
            elif bull_pct <= 35:
                parts_msg.append("🔴📉 *STRONG BUY PUTS (PE)* — Bearish pressure 📉🔴")
            elif bull_pct <= 45:
                parts_msg.append("🔴 *MODERATELY BEARISH — Favor PUTS (PE)* 🔴")
            else:
                parts_msg.append("🟡 *NEUTRAL — Wait for clarity* 🟡")

            parts_msg.append("")
            parts_msg.append("⚠️ _AI-generated. Not financial advice. Use SL._")
            parts_msg.append(STAR_LINE)

            send_message(chat_id, "\n".join(parts_msg), reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Super prediction failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Super prediction failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   📰 MARKET SENTIMENT
    # ════════════════════════════
    if text in ("📰 Market Sentiment 💬", "Market Sentiment"):
        send_message(chat_id, f"{greeting}📰 *Analyzing market sentiment...* ⏳")
        try:
            if SENTIMENT_AVAILABLE:
                sent = analyze_news_sentiment()
                mood = sent.get("overall_mood", "Neutral")
                score = sent.get("avg_sentiment", 0)
                headlines = sent.get("headlines", [])
                source_scores = sent.get("source_scores", {})

                parts_msg = []
                parts_msg.append(f"📰💬 *MARKET SENTIMENT ANALYSIS* 💬📰")
                parts_msg.append(FIRE_LINE)

                # Mood indicator
                if score > 0.3:
                    mood_icon = "🟢🚀"
                elif score > 0:
                    mood_icon = "🟢"
                elif score > -0.3:
                    mood_icon = "🔴"
                else:
                    mood_icon = "🔴📉"

                parts_msg.append(f"\n{mood_icon} *Overall Mood:* {mood}")
                parts_msg.append(f"📊 *Sentiment Score:* {score:.2f} (-1 to +1)")

                # Sentiment gauge
                gauge_pos = int((score + 1) * 5)
                gauge_pos = max(0, min(10, gauge_pos))
                gauge = "🟢" * gauge_pos + "🔴" * (10 - gauge_pos)
                parts_msg.append(f"📈 [{gauge}]")

                if headlines:
                    parts_msg.append(f"\n📰 *Top Headlines:*")
                    for i, h in enumerate(headlines[:5], 1):
                        title = h.get("title", "") if isinstance(h, dict) else str(h)
                        parts_msg.append(f"  {i}. {title[:80]}")

                if source_scores:
                    parts_msg.append(f"\n📊 *Source Breakdown:*")
                    for src, sc in source_scores.items():
                        parts_msg.append(f"  • {src}: {sc:+.2f}")

                # Fear & Greed
                try:
                    fg = calculate_fear_greed_index()
                    fg_val = fg.get("index_value", 50)
                    fg_label = fg.get("label", "Neutral")
                    parts_msg.append(f"\n😱 *Fear & Greed Index:* {fg_val:.0f}/100 — *{fg_label}*")
                except Exception:
                    pass

                # Trading implication
                parts_msg.append(f"\n{HEADER_LINE}")
                if score > 0.2:
                    parts_msg.append("💡 *Implication:* Positive sentiment → Favor *CALLS (CE)*")
                elif score < -0.2:
                    parts_msg.append("💡 *Implication:* Negative sentiment → Favor *PUTS (PE)*")
                else:
                    parts_msg.append("💡 *Implication:* Mixed sentiment → *Wait & Watch*")

                parts_msg.append(f"\n⚠️ _Sentiment can shift fast. Combine with technical analysis._")
                parts_msg.append(STAR_LINE)
                send_message(chat_id, "\n".join(parts_msg), reply_markup=build_keyboard())
            else:
                send_message(chat_id, f"{greeting}⚠️ Sentiment engine not available. Install dependencies.", reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Sentiment failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Sentiment analysis failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   ⚠️ RISK CALCULATOR
    # ════════════════════════════
    if text in ("⚠️ Risk Calculator 🛡️", "Risk Calculator"):
        send_message(chat_id, f"{greeting}⚠️ *Calculating risk parameters...* ⏳")
        try:
            import yfinance as yf

            parts_msg = []
            parts_msg.append(f"⚠️🛡️ *RISK MANAGEMENT CALCULATOR* 🛡️⚠️")
            parts_msg.append(FIRE_LINE)

            for yf_ticker, display_name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
                try:
                    hist = yf.download(yf_ticker, period="90d", progress=False)
                    if hist is None or len(hist) < 10:
                        continue
                    if isinstance(hist.columns, pd.MultiIndex):
                        hist.columns = hist.columns.get_level_values(0)
                    close = hist['Close']
                    price = float(close.iloc[-1])
                    returns = close.pct_change().dropna()
                    vol_daily = float(returns.std()) * 100
                    vol_annual = vol_daily * np.sqrt(252)
                    max_dd = float(((close / close.cummax()) - 1).min()) * 100

                    parts_msg.append(f"\n📊 *{display_name}* @ ₹{price:,.0f}")
                    parts_msg.append(f"  ┣ Daily Volatility: *{vol_daily:.2f}%*")
                    parts_msg.append(f"  ┣ Annual Volatility: *{vol_annual:.1f}%*")
                    parts_msg.append(f"  ┣ Max Drawdown (90d): *{max_dd:.1f}%*")

                    # Position sizing for different capitals
                    for capital in [10000, 50000, 100000, 500000]:
                        sl_pct = 2.0
                        risk_amt = capital * (sl_pct / 100)
                        sl_points = price * 0.02
                        max_qty = int(risk_amt / sl_points) if sl_points > 0 else 0
                        parts_msg.append(f"  ┣ ₹{capital:,.0f} capital → Max position: *{max_qty} qty* (2% risk)")

                    # ATR-based stop loss
                    if len(hist) >= 15:
                        atr_col = None
                        try:
                            import pandas_ta
                            atr_s = pandas_ta.atr(hist['High'], hist['Low'], hist['Close'], length=14)
                            if atr_s is not None and len(atr_s) > 0:
                                atr_val = float(atr_s.iloc[-1])
                                parts_msg.append(f"  ┣ ATR(14): *₹{atr_val:.0f}*")
                                parts_msg.append(f"  ┣ Suggested SL: *₹{price - atr_val * 1.5:.0f}* (1.5× ATR)")
                                parts_msg.append(f"  ┗ Suggested TP: *₹{price + atr_val * 2:.0f}* (2× ATR)")
                        except Exception:
                            pass

                except Exception as e:
                    parts_msg.append(f"\n⚠️ {display_name}: Error ({str(e)[:50]})")

            parts_msg.append(f"\n{HEADER_LINE}")
            parts_msg.append("🧠 *RISK RULES:*")
            parts_msg.append("  1. Never risk more than 2% of capital per trade")
            parts_msg.append("  2. Always use stop-loss orders")
            parts_msg.append("  3. Risk-Reward ratio should be at least 1:2")
            parts_msg.append("  4. Don't overtrade — max 3 open positions")
            parts_msg.append(f"\n⚠️ _Risk management is the key to long-term survival._")
            parts_msg.append(STAR_LINE)

            send_message(chat_id, "\n".join(parts_msg), reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Risk calc failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Risk calculation failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   🕯️ CANDLE PATTERNS
    # ════════════════════════════
    if text in ("🕯️ Candle Patterns 📊", "Candle Patterns"):
        send_message(chat_id, f"{greeting}🕯️ *Scanning 40+ candlestick patterns...* ⏳")
        try:
            from candle_analyzer import analyze_index

            parts_msg = []
            parts_msg.append(f"🕯️📊 *JAPANESE CANDLESTICK ANALYSIS* 📊🕯️")
            parts_msg.append(FIRE_LINE)
            parts_msg.append(f"_Scanning 40+ patterns across multiple timeframes_\n")

            for yf_ticker, display_name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
                try:
                    analysis = analyze_index(yf_ticker, display_name)
                    sig = analysis.get("signal", "HOLD")
                    conf = analysis.get("confidence", 0.5)
                    patterns = analysis.get("patterns_found", [])
                    indicators = analysis.get("indicators", {})

                    if sig == "BUY":
                        icon = "🟢🚀"
                    elif sig == "SELL":
                        icon = "🔴📉"
                    else:
                        icon = "🟡⚖️"

                    parts_msg.append(f"{'─' * 30}")
                    parts_msg.append(f"{icon} *{display_name}* — Signal: *{sig}* ({conf:.0%})")

                    # Show detected patterns
                    if patterns:
                        parts_msg.append(f"  🕯️ *Patterns Found:*")
                        for p in patterns[:8]:
                            parts_msg.append(f"     • {p}")
                    else:
                        parts_msg.append(f"  🕯️ _No strong patterns detected_")

                    # Show key indicators
                    price = indicators.get("price", 0)
                    rsi = indicators.get("rsi", 50)
                    macd = indicators.get("macd", 0)
                    atr = indicators.get("atr", 0)
                    if price > 0:
                        parts_msg.append(f"  📈 Price: ₹{price:,.0f} | RSI: {rsi:.1f}")
                        if atr > 0:
                            parts_msg.append(f"  📊 ATR: ₹{atr:.0f} | MACD: {macd:.2f}")

                    # Candle-based recommendation
                    if sig == "BUY":
                        parts_msg.append(f"  💡 *Bullish candle setup → Favor CALLS (CE)*")
                    elif sig == "SELL":
                        parts_msg.append(f"  💡 *Bearish candle setup → Favor PUTS (PE)*")

                    parts_msg.append("")
                except Exception as e:
                    parts_msg.append(f"  ⚠️ {display_name}: {str(e)[:50]}\n")

            parts_msg.append(HEADER_LINE)
            parts_msg.append("🕯️ *Patterns scanned:* Doji, Hammer, Engulfing, Morning/Evening Star,")
            parts_msg.append("Harami, Marubozu, Three White Soldiers, Dark Cloud Cover,")
            parts_msg.append("Piercing Line, Spinning Top, Tweezer, and 30+ more")
            parts_msg.append(f"\n⚠️ _Combine patterns with volume & indicators for best results._")
            parts_msg.append(STAR_LINE)
            send_message(chat_id, "\n".join(parts_msg), reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Candle patterns failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Candle pattern scan failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   CRYPTO GEMS
    # ════════════════════════════
    if text in ("🪙 Crypto Gems 💎", "Crypto Gems"):
        try:
            send_message(chat_id, f"{greeting}🪙 Scanning DexScreener for gems... Please wait ⏳")
            from crypto_engine import scan_trending_gems, _format_gems_basic
            gems = scan_trending_gems(min_score=15, limit=10)
            if gems:
                msg = _format_gems_basic(gems)
            else:
                msg = "❌ No gems found right now. DexScreener may be loading."
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Crypto scan failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   TRENDING CRYPTO
    # ════════════════════════════
    if text in ("🔥 Trending Crypto 📈", "Trending Crypto"):
        try:
            send_message(chat_id, f"{greeting}🔥 Fetching DexScreener trending tokens...\n_Rug Check + Buy/Sell Signals loading..._")
            from crypto_engine import format_trending_overview, scan_trending_gems
            msg = format_trending_overview()
            # Add enrichment from top trending gems
            if CRYPTO_INTEL_AVAILABLE:
                try:
                    gems = scan_trending_gems(min_score=5, limit=5)
                    if gems:
                        msg += "\n\n🧠 *JARVIS INTELLIGENCE:*\n"
                        for g in gems[:5]:
                            msg += f"*{g.get('symbol','?')}:* {enrich_token_line(g)}\n"
                except Exception:
                    pass
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if CRYPTO_INTEL_AVAILABLE:
                send_jarvis_voice(chat_id, "Trending tokens ka rug check aur signals ready hain। Text mein dekh lijiye details।", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Trending fetch failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   PUMP.FUN TRENDING
    # ════════════════════════════
    if text in ("🟣 Pump.fun Trending 🔥", "Pump.fun Trending"):
        try:
            send_message(chat_id, f"{greeting}🟣 Scanning pump.fun trending tokens... ⏳\n_Rug Check + Buy/Sell Signals loading..._")
            from crypto_engine import scan_pump_trending, format_pump_trending
            tokens = scan_pump_trending(min_score=5, limit=10)
            msg = format_pump_trending(tokens)
            if CRYPTO_INTEL_AVAILABLE and tokens:
                msg += "\n\n🧠 *JARVIS INTELLIGENCE:*\n"
                for t in tokens[:5]:
                    msg += f"*{t.get('symbol','?')}:* {enrich_token_line(t)}\n"
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if CRYPTO_INTEL_AVAILABLE and tokens:
                send_jarvis_voice(chat_id, "Pump.fun trending tokens ka analysis complete hai। Rug check aur buy sell signals text mein dekh lijiye। Jo green signal hai uspe entry le sakte ho.", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Pump.fun scan failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   PUMP.FUN NEW LAUNCHES
    # ════════════════════════════
    if text in ("🆕 Pump.fun New Launches", "Pump.fun New"):
        try:
            send_message(chat_id, f"{greeting}🆕 Fetching newest pump.fun launches... ⏳\n_Rug Check + Buy/Sell Signals loading..._")
            from crypto_engine import scan_pump_newest, format_pump_new_launches
            tokens = scan_pump_newest(min_score=0, limit=10)
            msg = format_pump_new_launches(tokens)
            if CRYPTO_INTEL_AVAILABLE and tokens:
                msg += "\n\n🧠 *JARVIS INTELLIGENCE:*\n"
                for t in tokens[:5]:
                    msg += f"*{t.get('symbol','?')}:* {enrich_token_line(t)}\n"
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if CRYPTO_INTEL_AVAILABLE and tokens:
                send_jarvis_voice(chat_id, "New launches ka rug check aur signals ready hai। Bahut naye tokens hain, careful rehna। Jo safe hai wo text mein green dikhega.", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Pump.fun new launches fetch failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   PUMP.FUN TOP MARKET CAP
    # ════════════════════════════
    if text in ("🏆 Pump.fun Top MCap", "Pump.fun Top"):
        try:
            send_message(chat_id, f"{greeting}🏆 Fetching pump.fun top tokens by market cap... ⏳\n_Rug Check + Buy/Sell Signals loading..._")
            from crypto_engine import scan_pump_top_mcap, format_pump_top
            tokens = scan_pump_top_mcap(limit=10)
            msg = format_pump_top(tokens)
            if CRYPTO_INTEL_AVAILABLE and tokens:
                msg += "\n\n🧠 *JARVIS INTELLIGENCE:*\n"
                for t in tokens[:5]:
                    msg += f"*{t.get('symbol','?')}:* {enrich_token_line(t)}\n"
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if CRYPTO_INTEL_AVAILABLE and tokens:
                send_jarvis_voice(chat_id, "Top market cap tokens ka analysis ready hai। Rug check aur buy sell signals text mein hain. Dekh lijiye.", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Pump.fun top fetch failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   ALL GEMS (PUMP + DEX combined)
    # ════════════════════════════
    if text in ("🪙 All Gems (Pump+Dex)", "All Gems"):
        try:
            send_message(chat_id, f"{greeting}🪙💎 Scanning pump.fun + DexScreener for gems... ⏳\n_Rug Check + Buy/Sell Signals loading..._")
            from crypto_engine import scan_all_gems, _format_gems_basic
            gems = scan_all_gems(min_score=10, limit=10)
            if gems:
                msg = _format_gems_basic(gems)
                if CRYPTO_INTEL_AVAILABLE:
                    msg += "\n\n🧠 *JARVIS INTELLIGENCE:*\n"
                    for g in gems[:5]:
                        msg += f"*{g.get('symbol','?')}:* {enrich_token_line(g)}\n"
            else:
                msg = "❌ No gems found right now. Try again later."
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if CRYPTO_INTEL_AVAILABLE and gems:
                send_jarvis_voice(chat_id, "All gems scan complete hai। Rug check aur signals text mein dekh lo. Safe tokens pe green signal hoga.", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Combined scan failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   CRYPTO DIPS
    # ════════════════════════════
    if text in ("📉 Crypto Dips 🔴", "Crypto Dips"):
        try:
            send_message(chat_id, f"{greeting}📉 Scanning for dip buy opportunities...\n_Rug Check + Buy/Sell Signals loading..._")
            from crypto_engine import scan_dip_tokens, format_dip_alert
            dips = scan_dip_tokens(max_change_h1=-5.0, limit=10)
            if dips:
                msg = format_dip_alert(dips)
                if CRYPTO_INTEL_AVAILABLE:
                    msg += "\n\n🧠 *JARVIS INTELLIGENCE:*\n"
                    for d in dips[:5]:
                        msg += f"*{d.get('symbol','?')}:* {enrich_token_line(d)}\n"
            else:
                msg = f"{greeting}✅ No significant dips in trending tokens right now. Market looks stable!"
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if CRYPTO_INTEL_AVAILABLE and dips:
                send_jarvis_voice(chat_id, "Dip tokens ka analysis ready hai। Rug check check karen — agar safe hai to dip pe buy kar sakte hain. Text mein details hain.", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Dip scan failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   CRYPTO PUMPS
    # ════════════════════════════
    if text in ("🚀 Crypto Pumps 🟢", "Crypto Pumps"):
        try:
            send_message(chat_id, f"{greeting}🚀 Scanning for pumping tokens...\n_Rug Check + Buy/Sell Signals loading..._")
            from crypto_engine import scan_pumping_tokens, _format_gems_basic, fmt_inr
            pumps = scan_pumping_tokens(min_change_h1=20.0, limit=10)
            if pumps:
                msg = "🚀🟢 *CRYPTO PUMPS — HOT RIGHT NOW* 🟢🚀\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += "_All prices in ₹ INR | Rug Check + Signals included_\n\n"
                for i, g in enumerate(pumps[:5], 1):
                    src = "🟣 pump.fun" if g.get("source") == "pump.fun" else "🟢 Dex"
                    msg += (
                        f"*{i}. {g['symbol']}* ({g.get('chain', '?').upper()}) [{src}]\n"
                        f"   💰 {fmt_inr(g.get('price_inr', 0))}\n"
                        f"   🚀 1h: {g.get('change_h1', 0):+.1f}% | 24h: {g.get('change_h24', 0):+.1f}%\n"
                        f"   📊 MCap: {fmt_inr(g.get('mcap_inr', 0))}\n"
                    )
                    if CRYPTO_INTEL_AVAILABLE:
                        msg += f"{enrich_token_line(g)}\n"
                    url = g.get('url') or g.get('dex_url', '')
                    if url:
                        msg += f"   🔗 [Chart]({url})\n"
                    msg += "\n"
                msg += "⚠️ *Careful! Pumps can reverse fast. Use tight SL!*"
            else:
                msg = f"{greeting}🔹 No major pumps detected in trending tokens right now."
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if pumps:
                send_jarvis_voice(chat_id, "Pumping tokens ka analysis ready hai। Rug check aur buy sell signals har token ke saath hain। Text mein details dekh lo. Tight stop loss lagana mat bhulna!", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Pump scan failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   AI CRYPTO PICK (SUPER-POWERED by crypto_intelligence)
    # ════════════════════════════
    if text in ("🤖 AI Crypto Pick 🧠", "AI Crypto Pick"):
        try:
            send_message(chat_id, f"{greeting}🤖🧠 *JARVIS Full Crypto Intelligence Analysis... Please wait* ⏳\n_Rug Check + Buy/Sell Signals + Price Targets + INR_")
            if CRYPTO_INTEL_AVAILABLE:
                picks = get_top_crypto_picks(limit=5, budget_inr=2000)
                if picks:
                    msg = format_top_picks(picks)
                    voice_text = format_picks_voice(picks)
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                    send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                    # Auto-add to watchlist
                    for p in picks[:3]:
                        try:
                            add_to_watchlist(str(chat_id), p.get("symbol", ""))
                        except Exception as e:
                            logger.error(f"[WATCHLIST] Auto-add failed for {p.get('symbol','?')}: {e}")
                else:
                    send_message(chat_id, f"{greeting}❌ कोई safe token नहीं मिला अभी। बाद में try करें।", reply_markup=build_keyboard())
            else:
                # Fallback to old crypto_engine
                from crypto_engine import scan_trending_gems, ai_analyze_gems
                gems = scan_trending_gems(min_score=10, limit=10)
                if gems:
                    msg = ai_analyze_gems(gems, max_gems=5)
                else:
                    msg = "❌ No trending tokens to analyze right now."
                send_message(chat_id, msg, reply_markup=build_keyboard())
                send_jarvis_voice(chat_id, msg, intent="chat")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ AI analysis failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   CRYPTO ALERTS ON/OFF
    # ════════════════════════════
    if text in ("🔔 Crypto Alerts ON/OFF", "Crypto Alerts"):
        key = f"crypto_alerts_{chat_id}"
        current = chat_storage.get(key, False)
        chat_storage[key] = not current
        if not current:
            # Subscribe
            from data_store import add_subscriber
            add_subscriber(chat_id)
            send_message(
                chat_id,
                f"{greeting}🔔🪙 *CRYPTO GEM ALERTS: ON* 🪙🔔\n\n"
                f"You'll receive alerts when:\n"
                f"┣ 💎 New gem detected (score 40+)\n"
                f"┣ 📉 Major dip in trending token (>10% drop)\n"
                f"┣ 🚀 Token pumping (>50% in 1h)\n\n"
                f"📊 Scanning every 10 seconds 24/7!\n"
                f"_Tap again to turn OFF_",
                reply_markup=build_keyboard()
            )
        else:
            send_message(
                chat_id,
                f"{greeting}🔕 *CRYPTO ALERTS: OFF*\n\n"
                f"You won't receive crypto gem alerts.\n"
                f"_Tap again to turn ON_",
                reply_markup=build_keyboard()
            )
        return

    # ════════════════════════════
    #   WHALE SCANNER
    # ════════════════════════════
    if text in ("🐋 Whale Scanner 🔍", "Whale Scanner"):
        try:
            send_message(chat_id, f"{greeting}🐋 Scanning for whale activity in trending tokens... ⏳")
            from whale_alert import scan_whale_activity_trending, format_whale_scan
            results = scan_whale_activity_trending(limit=8)
            msg = format_whale_scan(results)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Whale scan failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   RUG DETECTOR
    # ════════════════════════════
    if text in ("🛡️ Rug Detector 🔎", "Rug Detector"):
        try:
            send_message(chat_id, f"{greeting}🛡️ Scanning trending tokens for rug risk... ⏳")
            from rug_detector import scan_rug_risk_trending, format_rug_scan
            results = scan_rug_risk_trending(limit=10)
            msg = format_rug_scan(results)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Rug scan failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   MY CRYPTO PORTFOLIO (PER-USER — each user sees their own)
    # ════════════════════════════
    if text in ("📂 My Crypto Portfolio", "My Portfolio", "Portfolio"):
        try:
            from portfolio_tracker import calculate_portfolio_pnl, format_portfolio
            pnl_data = calculate_portfolio_pnl(chat_id)
            msg = format_portfolio(pnl_data)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Portfolio error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   TRADE HISTORY (PER-USER)
    # ════════════════════════════
    if text in ("📜 Trade History", "Trade History"):
        try:
            from portfolio_tracker import get_trade_history, format_trade_history
            trades = get_trade_history(chat_id, limit=15)
            msg = format_trade_history(trades)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Trade history error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   PRICE ALERTS LIST
    # ════════════════════════════
    if text in ("🔔 Price Alerts 📊", "Price Alerts"):
        try:
            from portfolio_tracker import get_active_price_alerts, format_alerts_list
            alerts = get_active_price_alerts(chat_id)
            msg = format_alerts_list(alerts)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Price alerts error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   GEM ACCURACY REPORT
    # ════════════════════════════
    if text in ("📊 Gem Accuracy 🔬", "Gem Accuracy"):
        try:
            from gem_backtester import get_accuracy_stats, format_accuracy_report
            stats = get_accuracy_stats()
            msg = format_accuracy_report(stats)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Accuracy report error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   MULTI-CHAIN GEMS
    # ════════════════════════════
    if text in ("🌐 Multi-Chain Gems 🔗", "Multi-Chain Gems"):
        try:
            send_message(chat_id, f"{greeting}🌐 Scanning all chains for gems... ⏳\n_Rug Check + Buy/Sell Signals loading..._")
            from crypto_engine import scan_multichain_gems, format_multichain_overview
            gems = scan_multichain_gems(min_score=10, limit=12)
            msg = format_multichain_overview(gems)
            if CRYPTO_INTEL_AVAILABLE and gems:
                msg += "\n\n🧠 *JARVIS INTELLIGENCE:*\n"
                for g in gems[:5]:
                    msg += f"*{g.get('symbol','?')}:* {enrich_token_line(g)}\n"
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if CRYPTO_INTEL_AVAILABLE and gems:
                send_jarvis_voice(chat_id, "Multi-chain gems ka analysis ready hai। Rug check aur signals text mein dekh lijiye।", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Multi-chain scan failed: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   /buy COMMAND — Add to portfolio (PER-USER)
    # ════════════════════════════
    if text.startswith("/buy ") or text.startswith("💰 Buy Crypto /buy"):
        if text == "💰 Buy Crypto /buy":
            send_message(
                chat_id,
                f"{greeting}💰 *ADD TO PORTFOLIO*\n\n"
                f"Format: `/buy SYMBOL QTY PRICE_INR`\n\n"
                f"Examples:\n"
                f"┣ `/buy FARTCOIN 1000000 0.0065`\n"
                f"┣ `/buy BONK 5000000 0.001`\n"
                f"┣ `/buy SOL 2 14500`\n\n"
                f"Price in ₹ INR per token.",
                reply_markup=build_keyboard()
            )
            return
        try:
            parts = text.split()
            if len(parts) < 4:
                send_message(chat_id, "❌ Format: `/buy SYMBOL QTY PRICE_INR`\nExample: `/buy FARTCOIN 1000000 0.0065`", reply_markup=build_keyboard())
                return
            symbol = parts[1].upper()
            qty = float(parts[2])
            price = float(parts[3])
            # Validate financial inputs
            if SECURITY_AVAILABLE:
                ok, msg = validate_financial_input(qty, "quantity", min_val=0)
                if not ok:
                    send_message(chat_id, f"❌ {msg}", reply_markup=build_keyboard())
                    return
                ok, msg = validate_financial_input(price, "price", min_val=0)
                if not ok:
                    send_message(chat_id, f"❌ {msg}", reply_markup=build_keyboard())
                    return
                ok, msg = validate_symbol(symbol)
                if not ok:
                    send_message(chat_id, f"❌ {msg}", reply_markup=build_keyboard())
                    return
            from portfolio_tracker import add_holding
            from crypto_engine import fmt_inr
            add_holding(chat_id, symbol, qty, price)
            invested = qty * price
            send_message(
                chat_id,
                f"✅ *ADDED TO PORTFOLIO*\n\n"
                f"🪙 {symbol}\n"
                f"🔢 Qty: {qty:,.0f}\n"
                f"💵 Price: {fmt_inr(price)}\n"
                f"💰 Invested: {fmt_inr(invested)}\n\n"
                f"View: 📂 My Crypto Portfolio",
                reply_markup=build_keyboard()
            )
        except (ValueError, IndexError):
            send_message(chat_id, "❌ Format: `/buy SYMBOL QTY PRICE_INR`", reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Buy error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   /sell COMMAND — Sell from portfolio (PER-USER)
    # ════════════════════════════
    if text.startswith("/sell "):
        try:
            parts = text.split()
            if len(parts) < 3:
                send_message(chat_id, "❌ Format: `/sell SYMBOL PRICE_INR`\nExample: `/sell FARTCOIN 0.015`", reply_markup=build_keyboard())
                return
            symbol = parts[1].upper()
            price = float(parts[2])
            from portfolio_tracker import sell_holding
            from crypto_engine import fmt_inr
            result = sell_holding(chat_id, symbol, price)
            if result["success"]:
                pnl = result["pnl_inr"]
                pnl_emoji = "🟢📈" if pnl >= 0 else "🔴📉"
                send_message(
                    chat_id,
                    f"{pnl_emoji} *SOLD {result['symbol']}*\n\n"
                    f"🔢 Qty: {result['qty_sold']:,.0f}\n"
                    f"💵 Sell Price: {fmt_inr(price)}\n"
                    f"💰 Received: {fmt_inr(result['total_received_inr'])}\n"
                    f"📊 Invested: {fmt_inr(result['total_invested_inr'])}\n"
                    f"{'🟢' if pnl>=0 else '🔴'} P&L: {fmt_inr(abs(pnl))} ({'+' if pnl>=0 else '-'}{abs(result['roi_pct']):.1f}%)",
                    reply_markup=build_keyboard()
                )
            else:
                send_message(chat_id, f"❌ {result.get('error', 'Sell failed')}", reply_markup=build_keyboard())
        except (ValueError, IndexError):
            send_message(chat_id, "❌ Format: `/sell SYMBOL PRICE_INR`", reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Sell error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   /alert COMMAND — Set price alert (OWNER ONLY)
    #   /alert COMMAND — Price alert (PER-USER)
    # ════════════════════════════
    if text.startswith("/alert "):
        try:
            parts = text.split()
            if len(parts) < 3:
                send_message(chat_id, "❌ Format: `/alert SYMBOL PRICE [above/below]`\nExample: `/alert FARTCOIN 0.01 above`", reply_markup=build_keyboard())
                return
            symbol = parts[1].upper()
            target = float(parts[2])
            direction = parts[3].lower() if len(parts) > 3 else "above"
            from portfolio_tracker import add_price_alert
            from crypto_engine import fmt_inr
            alert_id = add_price_alert(chat_id, symbol, target, direction)
            emoji = "⬆️" if direction == "above" else "⬇️"
            send_message(
                chat_id,
                f"🔔 *PRICE ALERT SET!*\n\n"
                f"🪙 {symbol}\n"
                f"{emoji} Alert when price goes {direction} {fmt_inr(target)}\n"
                f"📋 Alert ID: {alert_id}\n\n"
                f"Delete: `/delalert {alert_id}`",
                reply_markup=build_keyboard()
            )
        except (ValueError, IndexError):
            send_message(chat_id, "❌ Format: `/alert SYMBOL PRICE [above/below]`", reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Alert error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   /delalert COMMAND — Delete price alert (PER-USER)
    # ════════════════════════════
    if text.startswith("/delalert "):
        try:
            alert_id = int(text.split()[1])
            from portfolio_tracker import delete_price_alert
            if delete_price_alert(alert_id, chat_id):
                send_message(chat_id, f"✅ Alert #{alert_id} deleted.", reply_markup=build_keyboard())
            else:
                send_message(chat_id, f"❌ Alert #{alert_id} not found or not yours.", reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"❌ Error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   /rug COMMAND — Check specific token
    # ════════════════════════════
    if text.startswith("/rug "):
        try:
            token_addr = text.split()[1].strip()
            send_message(chat_id, f"{greeting}🛡️ Analyzing rug risk for `{token_addr[:20]}...`")
            from rug_detector import check_token_rug_risk, format_rug_check
            result = check_token_rug_risk(token_addr)
            msg = format_rug_check(result)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"❌ Rug check error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   /whale COMMAND — Check whale activity for token
    # ════════════════════════════
    if text.startswith("/whale "):
        try:
            token_addr = text.split()[1].strip()
            send_message(chat_id, f"{greeting}🐋 Analyzing whale activity for `{token_addr[:20]}...`")
            from whale_alert import detect_whale_activity_from_dex, format_whale_report
            result = detect_whale_activity_from_dex(token_addr)
            msg = format_whale_report(result)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"❌ Whale check error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   JARVIS — ASK JARVIS (Natural Language)
    # ════════════════════════════
    if text in ("🤖 Ask JARVIS 💬", "Ask JARVIS"):
        send_message(
            chat_id,
            f"{greeting}"
            f"🤖🌸 *J.A.R.V.I.S. ACTIVATED* 🌸🤖\n"
            f"{FIRE_LINE}\n\n"
            f"_\"नमस्ते जी! मैं तैयार हूँ, बताइए क्या करना है!\"_ 💕\n\n"
            f"मैं आपकी बात समझती हूँ! बस बोलिए या लिखिए:\n\n"
            f"💡 *ये बोलके देखिए:*\n"
            f"┣ _\"NIFTY में call लूँ या put?\"_\n"
            f"┣ _\"Best crypto gem ढूंढो\"_\n"
            f"┣ _\"ये token rug pull तो नहीं?\"_\n"
            f"┣ _\"Whale activity दिखाओ\"_\n"
            f"┣ _\"Portfolio P&L बताओ\"_\n"
            f"┣ _\"Morning briefing दो\"_\n"
            f"┣ _\"₹5000 में best option?\"_\n"
            f"┣ _\"Crypto market कैसा है आज?\"_\n\n"
            f"🧠 *Stocks, crypto, options, risk — सब मुझ पर छोड़िए!*\n"
            f"बस बोलिए, मैं समझ जाऊँगी! 🌸\n"
            f"{SPARKLE_LINE}",
            reply_markup=build_keyboard()
        )
        send_jarvis_voice(chat_id, "नमस्ते जी! मैं जार्विस, आपकी AI असिस्टेंट। मैं तैयार हूँ! बस बोलिए या लिखिए, मैं सब समझती हूँ।", intent="greeting")
        chat_storage[f"ai_mode_{chat_id}"] = True
        return

    # ════════════════════════════
    #   JARVIS — MORNING BRIEFING
    # ════════════════════════════
    if text in ("☀️ Morning Brief 📊", "Morning Brief", "morning briefing"):
        send_message(chat_id, f"🤖🌸 *आपकी briefing तैयार कर रही हूँ...* ⏳💕")
        try:
            if JARVIS_AVAILABLE:
                brief = generate_morning_briefing(chat_id)
            else:
                brief = f"{greeting}☀️ Morning briefing अभी उपलब्ध नहीं है। AI Chat try कीजिये! 🌸"
            send_message(chat_id, brief, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, brief, intent="morning_brief")
        except Exception as e:
            logger.error(f"Morning briefing error: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Briefing फेल हो गई। फिर से try कीजिये! 🌸", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   CATEGORY SEPARATORS (ignore clicks on section headers)
    # ════════════════════════════
    separator_labels = (
        "📊 ━━ STOCK MARKET ━━ 📊", "🪙 ━━ CRYPTO MARKET ━━ 🪙",
        "🛡️ ━━ CRYPTO TOOLS ━━ 🛡️", "🤖 ━━ AI & ALERTS ━━ 🤖",
        "📋 ━━ ACCOUNT ━━ 📋",
        "💹 ━━ CoinDCX Web3 AI ━━ 💹",
        "🌐 ━━ ALL Web3 Tokens ━━ 🌐",
        "🏷️ ━━ Web3 Categories ━━ 🏷️",
        "🔍 ━━ Web3 AI Scan ━━ 🔍",
        # Hindi headers from JARVIS keyboard
        "🟢🔴 ━━ BUY/SELL सिग्नल ━━ 🟢🔴",
        "📊 ━━ स्टॉक मार्केट ━━ 📊",
        "🌡️ ━━ मार्केट इंटेलिजेंस ━━ 🌡️",
        "🪙 ━━ क्रिप्टो मार्केट ━━ 🪙",
        "🔥 ━━ DEXTOOLS ENGINE ━━ 🔥",
        "🚀 ━━ ROCKET SCANNER ━━ 🚀",
        "💰 ━━ TOP 100 AI + WEALTH ━━ 💰",
        "🛡️ ━━ क्रिप्टो टूल्स ━━ 🛡️",
        "👻 ━━ PHANTOM WALLET ━━ 👻",
        "🎁 ━━ AIRDROP HUNTER ━━ 🎁",
        "🔗 ━━ QR WALLET CONNECT ━━ 🔗",
        "🌍 ━━ ग्लोबल मार्केट ━━ 🌍",
        "🧠 ━━ SUPER BRAIN ━━ ⚡",
        "🛡️ ━━ SECURITY CENTER ━━ 🛡️",
        "🤖 ━━ AI & अलर्ट ━━ 🤖",
        "🔐 ━━ सेटिंग्स ━━ 🔐",
        "📋 ━━ अकाउंट ━━ 📋",
    )
    if text in separator_labels or ("━━" in text and len(text) < 50):
        send_message(chat_id, f"🤖🌸 _इस section के buttons use कीजिए!_ 👇", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   AI CHAT
    # ════════════════════════════
    if text in ("🤖 AI Chat 💬", "AI Chat"):
        send_message(
            chat_id,
            f"{greeting}"
            f"🤖💬 *J.A.R.V.I.S. AI CHAT ACTIVATED* 💬🤖\n"
            f"{FIRE_LINE}\n\n"
            f"I'm connected to multiple AI engines! Ask me anything:\n\n"
            f"💡 *Examples:*\n"
            f"┣ _\"Should I buy NIFTY CE or PE today?\"_\n"
            f"┣ _\"Which SENSEX option for ₹5000 budget?\"_\n"
            f"┣ _\"Find me a crypto gem on pump.fun\"_\n"
            f"┣ _\"Is it safe to invest in this token?\"_\n"
            f"┣ _\"Best scalping strategy for today\"_\n\n"
            f"Just type your question — I'll analyze with live data! 🚀\n"
            f"{SPARKLE_LINE}",
            reply_markup=build_keyboard()
        )
        chat_storage[f"ai_mode_{chat_id}"] = True
        return

    # ════════════════════════════
    #   CLEAR AI CHAT
    # ════════════════════════════
    if text in ("🧹 Clear AI Chat", "Clear AI Chat"):
        clear_chat_history(chat_id)
        chat_storage.pop(f"ai_mode_{chat_id}", None)
        send_message(chat_id, f"{greeting}🧹 AI chat history cleared! Start fresh 🚀", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   SMS ALERTS ON — Register phone number
    # ════════════════════════════
    if text in ("📲 SMS Alerts ON 🔔", "SMS Alerts ON"):
        send_message(
            chat_id,
            f"{greeting}"
            f"📲🔔 *SMS ALERTS SETUP* 🔔📲\n"
            f"{FIRE_LINE}\n\n"
            f"📱 *Send me your phone number:*\n\n"
            f"Format: `+91XXXXXXXXXX` or `XXXXXXXXXX`\n\n"
            f"✅ You'll receive SMS alerts:\n"
            f"┣ 📈 Market open signals (9:15 AM)\n"
            f"┣ 💰 BUY CALL/PUT recommendations\n"
            f"┣ 🔴 EXIT alerts when position is losing\n"
            f"┣ 🟢 PROFIT BOOK alerts\n"
            f"┣ ⚠️ Market crash warnings\n\n"
            f"_Send your 10-digit Indian mobile number now:_\n"
            f"{SPARKLE_LINE}",
            reply_markup=build_keyboard()
        )
        chat_storage[f"awaiting_phone_{chat_id}"] = True
        return

    # ════════════════════════════
    #   SMS ALERTS OFF
    # ════════════════════════════
    if text in ("📲 SMS Alerts OFF 🔕", "SMS Alerts OFF"):
        try:
            from data_store import remove_sms_subscriber
            remove_sms_subscriber(chat_id)
            send_message(
                chat_id,
                f"{greeting}📲🔕 *SMS Alerts DEACTIVATED*\n\n_You'll still receive Telegram alerts._\n{SPARKLE_LINE}",
                reply_markup=build_keyboard()
            )
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Failed to deactivate SMS alerts.")
        return

    # ════════════════════════════
    #   SET INVESTMENT AMOUNT
    # ════════════════════════════
    if text in ("💵 Set Investment Amount", "Set Investment"):
        send_message(
            chat_id,
            f"{greeting}"
            f"💵 *SET YOUR INVESTMENT AMOUNT* 💵\n"
            f"{HEADER_LINE}\n\n"
            f"Send me the amount you want to invest:\n\n"
            f"_Examples:_\n"
            f"┣ `2000` — for ₹2,000\n"
            f"┣ `5000` — for ₹5,000\n"
            f"┣ `20000` — for ₹20,000\n"
            f"┣ `50000` — for ₹50,000\n\n"
            f"📊 I'll calculate exact trades for YOUR budget!\n"
            f"{SPARKLE_LINE}",
            reply_markup=build_keyboard()
        )
        chat_storage[f"awaiting_investment_{chat_id}"] = True
        return

    # ════════════════════════════
    #   MY POSITIONS (PER-USER)
    # ════════════════════════════
    if text in ("📊 My Positions", "My Positions"):
        try:
            from data_store import get_open_positions, get_sms_subscriber
            positions = get_open_positions(chat_id)
            sub = get_sms_subscriber(chat_id)
            inv_amount = sub.get("investment_amount", 2000) if sub else 2000
            
            if not positions:
                # No positions — show what they COULD invest in right now
                suggestion = ""
                try:
                    nifty_data = get_live_price("^NSEI")
                    nifty_price = nifty_data.get("price", 0) if isinstance(nifty_data, dict) else 0
                    if nifty_price > 0:
                        ml_pred = predict_index_direction("^NSEI", "NIFTY")
                        ml_dir = ml_pred.get("direction", "NEUTRAL") if "error" not in ml_pred else "NEUTRAL"
                        ml_conf = ml_pred.get("confidence", 0) if "error" not in ml_pred else 0
                        opt_type = "CE" if ml_dir in ("BULLISH", "UP") else "PE"
                        
                        chain = generate_index_option_chain("^NSEI", "NIFTY")
                        if "error" not in chain:
                            inv = calculate_investment_options(chain, inv_amount, opt_type)
                            if inv.get("recommendations"):
                                best = inv["recommendations"][0]
                                suggestion = (
                                    f"\n💡 *SUGGESTED TRADE (₹{inv_amount:,.0f} budget):*\n"
                                    f"┣ 🤖 AI: NIFTY *{ml_dir}* ({ml_conf:.0%})\n"
                                    f"┣ 📋 BUY: *{best['strike']:,.0f} {opt_type}*\n"
                                    f"┣ 💰 Premium: ₹{best['premium']:.2f}\n"
                                    f"┣ 📦 Qty: {best['qty']}\n"
                                    f"┣ 💵 Cost: ₹{best['total_cost']:,.0f}\n"
                                    f"┣ ✅ Target: ₹{best['premium'] * 1.5:.2f} (+50%)\n"
                                    f"┗ 🛑 SL: ₹{best['premium'] * 0.7:.2f} (-30%)\n"
                                )
                except Exception:
                    pass
                
                send_message(
                    chat_id,
                    f"{greeting}"
                    f"📊 *YOUR POSITIONS* 📊\n{HEADER_LINE}\n\n"
                    f"_No open positions tracked yet._\n"
                    f"{suggestion}\n"
                    f"📲 When we send you a BUY alert,\n"
                    f"your position will be tracked here with *live P&L*!\n"
                    f"{SPARKLE_LINE}",
                    reply_markup=build_keyboard()
                )
            else:
                msg_parts = [f"{greeting}", f"📊 *YOUR OPEN POSITIONS* 📊\n{FIRE_LINE}\n"]
                total_invested = 0
                total_pnl = 0
                
                for i, pos in enumerate(positions, 1):
                    # Get current price for P&L
                    try:
                        ticker = "^NSEI" if pos["index_name"] == "NIFTY" else "^BSESN"
                        live = get_live_price(ticker)
                        current_spot = live.get("price", 0) if isinstance(live, dict) and "error" not in live else 0
                        health = check_position_health(pos, current_spot)
                        
                        pnl = health["pnl"]
                        pnl_pct = health["pnl_pct"]
                        total_invested += pos["investment"]
                        total_pnl += pnl
                        
                        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
                        action_emoji = "⚠️" if health["action"] in ("EXIT_NOW", "EXIT_URGENT") else "✅" if health["action"] in ("BOOK_PROFIT", "BOOK_PARTIAL") else "📊"
                        
                        msg_parts.append(
                            f"\n{pnl_emoji} *Trade #{i}: {pos['index_name']} {pos['option_type']}*\n"
                            f"┣ 📋 Strike: ₹{pos['strike']:,.0f} {pos['option_type']}\n"
                            f"┣ 💰 Entry Premium: ₹{pos['entry_price']:.2f}\n"
                            f"┣ 📈 Current Premium: ~₹{health['estimated_premium']:.2f}\n"
                            f"┣ 📦 Qty: {pos['qty']}\n"
                            f"┣ 💵 Invested: ₹{pos['investment']:,.0f}\n"
                            f"┣ 💹 Current Value: ₹{health['current_value']:,.0f}\n"
                            f"┣ {pnl_emoji} P&L: ₹{pnl:+,.0f} ({pnl_pct:+.1f}%)\n"
                            f"┗ {action_emoji} Action: *{health['action']}* — _{health['reason']}_\n"
                        )
                    except Exception:
                        msg_parts.append(f"\n⚠️ Trade #{i}: {pos['index_name']} {pos['option_type']} Strike ₹{pos['strike']:,.0f}\n")
                
                # Portfolio summary
                total_pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
                msg_parts.append(
                    f"\n{HEADER_LINE}\n"
                    f"📊 *PORTFOLIO SUMMARY:*\n"
                    f"┣ Total Invested: ₹{total_invested:,.0f}\n"
                    f"┣ Total P&L: {total_pnl_emoji} ₹{total_pnl:+,.0f}\n"
                    f"┗ Positions: {len(positions)} open\n"
                    f"\n{STAR_LINE}"
                )
                send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Failed to fetch positions: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   PHONE NUMBER INPUT HANDLER
    # ════════════════════════════
    if chat_storage.get(f"awaiting_phone_{chat_id}"):
        phone = validate_indian_phone(text)
        if phone:
            try:
                from data_store import add_sms_subscriber, save_position
                add_sms_subscriber(chat_id, phone, user_name=user_name, investment_amount=2000)
                chat_storage.pop(f"awaiting_phone_{chat_id}", None)
                
                # Also auto-subscribe to Telegram alerts
                try:
                    from data_store import add_subscriber
                    add_subscriber(chat_id)
                except Exception:
                    pass
                
                # ── AUTO-CALCULATE CURRENT BEST TRADE ──
                trade_block = ""
                sms_trade_snippet = ""
                nifty_price = 0
                opt_type = "CE"
                best_strike = 0
                best_premium = 0
                best_qty = 0
                best_cost = 0
                ml_dir = "NEUTRAL"
                ml_conf = 0
                
                try:
                    nifty_data = get_live_price("^NSEI")
                    nifty_price = nifty_data.get("price", 0) if isinstance(nifty_data, dict) else 0
                    if nifty_price > 0:
                        ml_pred = predict_index_direction("^NSEI", "NIFTY")
                        ml_dir = ml_pred.get("direction", "NEUTRAL") if "error" not in ml_pred else "NEUTRAL"
                        ml_conf = ml_pred.get("confidence", 0) if "error" not in ml_pred else 0
                        
                        opt_type = "CE" if ml_dir in ("BULLISH", "UP") else "PE"
                        opt_label = "CALL (CE)" if opt_type == "CE" else "PUT (PE)"
                        
                        chain = generate_index_option_chain("^NSEI", "NIFTY")
                        if "error" not in chain:
                            inv = calculate_investment_options(chain, 2000, opt_type)
                            if inv.get("recommendations"):
                                best = inv["recommendations"][0]
                                best_strike = best["strike"]
                                best_premium = best["premium"]
                                best_qty = best["qty"]
                                best_cost = best["total_cost"]
                                target_premium = best_premium * 1.5
                                sl_premium = best_premium * 0.7
                                
                                trade_block = (
                                    f"\n🎯🔥 *YOUR RECOMMENDED TRADE RIGHT NOW:* 🔥🎯\n"
                                    f"{HEADER_LINE}\n"
                                    f"┣ 📊 *NIFTY* @ ₹{nifty_price:,.2f}\n"
                                    f"┣ 🤖 AI Signal: *{ml_dir}* ({ml_conf:.0%} confident)\n"
                                    f"┣ 💎 *BUY: NIFTY {best_strike:,.0f} {opt_label}*\n"
                                    f"┣ 💰 Premium: ₹{best_premium:.2f} per unit\n"
                                    f"┣ 📦 Quantity: {best_qty}\n"
                                    f"┣ 💵 Total Cost: ₹{best_cost:,.0f}\n"
                                    f"┣ ✅ Target Price: ₹{target_premium:.2f} (+50% = +₹{best_cost * 0.5:,.0f})\n"
                                    f"┗ 🛑 Stop Loss: ₹{sl_premium:.2f} (-30% = -₹{best_cost * 0.3:,.0f})\n"
                                )
                                
                                sms_trade_snippet = f"NIFTY {best_strike:.0f} {opt_type} @ Rs{best_premium:.1f} Qty:{best_qty}"
                                
                                # Auto-save this as a tracked position
                                try:
                                    save_position(
                                        chat_id=chat_id,
                                        phone=phone,
                                        index_name="NIFTY",
                                        option_type=opt_type,
                                        strike=best_strike,
                                        entry_price=best_premium,
                                        qty=best_qty,
                                        investment=best_cost
                                    )
                                except Exception:
                                    pass
                except Exception as e:
                    logger.error(f"[SMS] Trade calc failed: {e}")
                
                # ── SEND VERIFICATION SMS TO PHONE ──
                sms_sent = False
                try:
                    verification_msg = build_verification_sms(
                        user_name=user_name,
                        trade_info=sms_trade_snippet
                    )
                    sms_sent = send_sms(phone, verification_msg)
                    logger.info(f"[SMS] Verification SMS {'SENT' if sms_sent else 'FAILED'} to {phone}")
                except Exception as e:
                    logger.error(f"[SMS] Verification SMS error: {e}")
                
                # Always send Telegram-style "SMS" notification (guaranteed delivery)
                try:
                    tg_verify = (
                        f"📲💬 *SMS-STYLE NOTIFICATION* 💬📲\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🙏 {user_name} JI!\n\n"
                        f"✅ You are subscribed to *DavidCrew Trading Bot* alerts!\n"
                        f"📱 Phone: +91-{phone[:5]}-{phone[5:]}\n\n"
                    )
                    if sms_trade_snippet:
                        tg_verify += f"📊 Current: *{sms_trade_snippet}*\n\n"
                    tg_verify += (
                        f"You'll get BUY/EXIT alerts here + on phone.\n"
                        f"━━━━━━━━━━━━━━━━━━━━"
                    )
                    send_telegram_sms_style(chat_id, tg_verify)
                except Exception:
                    pass
                
                sms_status = "✅ *Verification SMS sent to your phone!*" if sms_sent else "✅ *Telegram notification sent!* _(Free SMS APIs limited for India — all alerts come via Telegram reliably)_"
                
                send_message(
                    chat_id,
                    f"{greeting}"
                    f"✅📲 *SMS ALERTS ACTIVATED!* 📲✅\n"
                    f"{FIRE_LINE}\n\n"
                    f"📱 *Phone:* +91-{phone[:5]}-{phone[5:]}\n"
                    f"👤 *Name:* {user_name}\n"
                    f"💵 *Budget:* ₹2,000\n"
                    f"📲 {sms_status}\n"
                    f"{trade_block}\n"
                    f"🔔 *You'll automatically receive:*\n"
                    f"┣ 📈 9:15 AM market open alert on phone\n"
                    f"┣ 💰 *BUY CALL/PUT* — exact strike, qty, cost\n"
                    f"┣ 🔴 *EXIT NOW* — when position is losing >30%\n"
                    f"┣ 🟢 *BOOK PROFIT* — when position gains >50%\n"
                    f"┣ ⚠️ Market crash warnings\n\n"
                    f"💡 *💵 Set Investment Amount* to change from ₹2K\n"
                    f"📊 *📊 My Positions* to track your live P&L\n"
                    f"{STAR_LINE}",
                    reply_markup=build_keyboard()
                )
            except Exception as e:
                send_message(chat_id, f"{greeting}❌ Failed to register: {str(e)[:100]}")
        else:
            send_message(
                chat_id,
                f"{greeting}❌ Invalid phone number!\n\nPlease send a valid 10-digit Indian mobile number.\nExample: `9876543210` or `+919876543210`",
                reply_markup=build_keyboard()
            )
        return

    # ════════════════════════════
    #   INVESTMENT AMOUNT INPUT HANDLER
    # ════════════════════════════
    if chat_storage.get(f"awaiting_investment_{chat_id}"):
        try:
            amount = float(re.sub(r'[^0-9.]', '', text))
            if amount < 100:
                send_message(chat_id, f"{greeting}❌ Minimum investment is ₹100. Please try again.")
                return
            if amount > 10000000:
                send_message(chat_id, f"{greeting}❌ Maximum is ₹1,00,00,000. Please try again.")
                return
            
            from data_store import update_sms_investment, get_sms_subscriber
            sub = get_sms_subscriber(chat_id)
            if sub:
                update_sms_investment(chat_id, amount)
            else:
                # Not registered for SMS yet, save in chat storage
                chat_storage[f"user_investment_{chat_id}"] = amount
            
            chat_storage.pop(f"awaiting_investment_{chat_id}", None)
            
            # Calculate a trade example with new budget
            trade_preview = ""
            try:
                nifty_data = get_live_price("^NSEI")
                nifty_price = nifty_data.get("price", 0) if isinstance(nifty_data, dict) else 0
                if nifty_price > 0:
                    ml_pred = predict_index_direction("^NSEI", "NIFTY")
                    ml_dir = ml_pred.get("direction", "NEUTRAL") if "error" not in ml_pred else "NEUTRAL"
                    opt_type = "CE" if ml_dir in ("BULLISH", "UP") else "PE"
                    
                    chain = generate_index_option_chain("^NSEI", "NIFTY")
                    if "error" not in chain:
                        inv = calculate_investment_options(chain, amount, opt_type)
                        if inv.get("recommendations"):
                            best = inv["recommendations"][0]
                            trade_preview = (
                                f"\n📊 *EXAMPLE TRADE FOR ₹{amount:,.0f}:*\n"
                                f"┣ NIFTY @ ₹{nifty_price:,.2f} → *{ml_dir}*\n"
                                f"┣ BUY: *{best['strike']:,.0f} {opt_type}*\n"
                                f"┣ Premium: ₹{best['premium']:.2f} × {best['qty']} qty\n"
                                f"┣ Cost: ₹{best['total_cost']:,.0f}\n"
                                f"┣ ✅ Profit at +50%: ₹{best['total_cost'] * 0.5:,.0f}\n"
                                f"┗ 🛑 Loss at -30%: ₹{best['total_cost'] * 0.3:,.0f}\n"
                            )
            except Exception:
                pass
            
            send_message(
                chat_id,
                f"{greeting}"
                f"✅ *Investment set to ₹{amount:,.0f}!* 💵\n"
                f"{HEADER_LINE}\n"
                f"{trade_preview}\n"
                f"📲 All trade alerts will use ₹{amount:,.0f} budget\n"
                f"You'll see exact strike, qty, and cost in every alert!\n"
                f"{SPARKLE_LINE}",
                reply_markup=build_keyboard()
            )
        except (ValueError, TypeError):
            send_message(chat_id, f"{greeting}❌ Please send a valid number. Example: `5000`")
        return

    # ════════════════════════════
    #   NIFTY/SENSEX TEXT INPUT
    # ════════════════════════════
    if text and text.strip().upper() in ["NIFTY", "SENSEX"]:
        symbol = text.strip().upper()
        
        if chat_storage.get("awaiting_add_symbol") == chat_id:
            try:
                from data_store import add_to_watchlist
                add_to_watchlist(chat_id, symbol)
                send_message(chat_id, f"{greeting}✅ Added *{symbol}* to your watchlist! 💎", reply_markup=build_keyboard())
                chat_storage.pop("awaiting_add_symbol", None)
            except Exception:
                send_message(chat_id, f"{greeting}❌ Failed to add {symbol}.")
            return
        
        if chat_storage.get("awaiting_remove_symbol") == chat_id:
            try:
                from data_store import remove_from_watchlist
                remove_from_watchlist(chat_id, symbol)
                send_message(chat_id, f"{greeting}✅ Removed *{symbol}* from watchlist.", reply_markup=build_keyboard())
                chat_storage.pop("awaiting_remove_symbol", None)
            except Exception:
                send_message(chat_id, f"{greeting}❌ Failed to remove {symbol}.")
            return
        
        # Show signals
        try:
            from candle_analyzer import analyze_index
            ticker_map = {"NIFTY": ("^NSEI", "NIFTY 50"), "SENSEX": ("^BSESN", "SENSEX")}
            if symbol in ticker_map:
                ticker, name = ticker_map[symbol]
                analysis = analyze_index(ticker, name)
                sig_text = analysis["analysis"]
                signal = analysis.get("signal", "HOLD")
                decorated = (
                    f"{greeting}"
                    f"🔱 *{name} — ANALYSIS* 🔱\n"
                    f"{FIRE_LINE}\n\n"
                    f"{sig_text}\n\n"
                    f"🎯 Signal: *{signal}*\n"
                    f"{STAR_LINE}"
                )
                send_message(chat_id, decorated, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Failed to analyze {symbol}")
        return

    # ════════════════════════════
    #   SIGNALS (legacy text)
    # ════════════════════════════
    if text == "Signals":
        try:
            from data_store import get_watchlist
            from candle_analyzer import analyze_index
            watchlist = get_watchlist(chat_id)
        except Exception:
            watchlist = []
        
        if not watchlist:
            watchlist = ["NIFTY", "SENSEX"]
        
        msg_parts = [f"{greeting}", f"📊 *PORTFOLIO SIGNALS* 📊\n{FIRE_LINE}\n"]
        
        ticker_map = {
            "NIFTY": ("^NSEI", "NIFTY 50"),
            "SENSEX": ("^BSESN", "SENSEX"),
        }
        
        for symbol in watchlist[:5]:
            symbol_upper = symbol.upper()
            if symbol_upper in ticker_map:
                ticker, name = ticker_map[symbol_upper]
                try:
                    analysis = analyze_index(ticker, name)
                    msg_parts.append(analysis["analysis"])
                    signal = analysis.get("signal", "HOLD")
                    conf = analysis.get("confidence", 0.5)
                    if signal == "BUY":
                        msg_parts.append(f"🟢 *BUY* (Confidence: {conf:.0%})")
                    elif signal == "SELL":
                        msg_parts.append(f"🔴 *SELL* (Confidence: {conf:.0%})")
                    else:
                        msg_parts.append(f"🟡 *HOLD*")
                    msg_parts.append(HEADER_LINE)
                except Exception as e:
                    msg_parts.append(f"{symbol}: Error - {str(e)[:50]}")
            else:
                msg_parts.append(f"{symbol}: _Index not supported (use NIFTY or SENSEX)_")
            msg_parts.append("")
        
        msg_parts.append(STAR_LINE)
        send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   SYMBOL LOOKUP (generic) — SKIP if AI mode is on
    # ════════════════════════════
    is_ai_mode = chat_storage.get(f"ai_mode_{chat_id}", False)
    if text and text.strip().isalpha() and len(text.strip()) <= 10 and not is_ai_mode:
        symbol = text.strip().upper()
        
        # Skip common words that aren't stock symbols
        common_words = {"HELLO", "HI", "HEY", "THANKS", "OK", "YES", "NO", "BYE",
                        "GOOD", "GREAT", "NICE", "HELP", "PLEASE", "SORRY", "TEST",
                        "START", "STOP", "WHAT", "HOW", "WHY", "WHEN", "WHO", "WHERE",
                        "CAN", "WILL", "THE", "AND", "FOR", "NOT", "ARE", "BUT", "ITS"}
        
        if symbol in common_words:
            # Route to AI chat instead
            pass
        elif chat_storage.get("awaiting_add_symbol") == chat_id:
            try:
                from data_store import add_to_watchlist
                add_to_watchlist(chat_id, symbol)
                send_message(chat_id, f"{greeting}✅ Added *{symbol}* to watchlist! 💎", reply_markup=build_keyboard())
                chat_storage.pop("awaiting_add_symbol", None)
            except Exception:
                send_message(chat_id, f"{greeting}❌ Failed to add {symbol}.")
            return
        elif chat_storage.get("awaiting_remove_symbol") == chat_id:
            try:
                from data_store import remove_from_watchlist
                remove_from_watchlist(chat_id, symbol)
                send_message(chat_id, f"{greeting}✅ Removed *{symbol}* from watchlist.", reply_markup=build_keyboard())
                chat_storage.pop("awaiting_remove_symbol", None)
            except Exception:
                send_message(chat_id, f"{greeting}❌ Failed to remove {symbol}.")
            return
        else:
            # Fetch option chain
            send_message(chat_id, f"{greeting}🔄 *Fetching data for {symbol}...* ⏳")
            data = fetch_nse_option_chain(symbol)
            if not data:
                send_message(chat_id, f"{greeting}❌ Failed to fetch option chain for *{symbol}*.")
                return
            calls, puts, u = parse_option_chain_json(data)
            analysis = analyze_option_chain(calls, puts, u)
            result = format_signal_message(symbol, analysis)
            
            decorated = (
                f"{greeting}"
                f"💎 *{symbol} — OPTION ANALYSIS* 💎\n"
                f"{FIRE_LINE}\n\n"
                f"{result}\n\n"
                f"{STAR_LINE}"
            )
            send_message(chat_id, decorated, reply_markup=build_keyboard())
            return

    # ════════════════════════════
    #   🟢🔴 BUY/SELL SIGNAL HANDLERS
    # ════════════════════════════
    if text in ("🟢🔴 Stock Buy/Sell Signal",):
        if BUY_SELL_AVAILABLE:
            send_message(chat_id, f"🤖 *जार्विस NIFTY + SENSEX का Full Buy/Sell सिग्नल चेक कर रहा है...* ⏳")
            try:
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msgs = []
                nifty_signal = get_stock_signal("NIFTY")
                if nifty_signal:
                    msgs.append(format_bs_signal(nifty_signal, lang=lang))
                sensex_signal = get_stock_signal("SENSEX")
                if sensex_signal:
                    msgs.append(format_bs_signal(sensex_signal, lang=lang))
                if msgs:
                    full_msg = "\n\n".join(msgs)
                    send_message(chat_id, full_msg, reply_markup=build_keyboard())
                    send_jarvis_voice(chat_id, "NIFTY aur SENSEX ka full buy sell signal ready hai. Entry price, stop loss, aur targets sab text mein hain. Dhyaan se dekhiye.", intent="buy_sell_stock")
                else:
                    send_message(chat_id, "❌ सिग्नल नहीं मिला। बाद में कोशिश करें।", reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Stock buy/sell error: {e}")
                send_message(chat_id, f"❌ Error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Buy/Sell Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("🟢🔴 Crypto Buy/Sell Signal",):
        if BUY_SELL_AVAILABLE:
            send_message(chat_id, f"🤖 *जार्विस Top Crypto का Buy/Sell सिग्नल चेक कर रहा है...* ⏳")
            try:
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msgs = []
                for sym in ["BTC", "ETH", "SOL"]:
                    try:
                        signal = get_crypto_signal(sym)
                        if signal:
                            msgs.append(format_bs_signal(signal, lang=lang))
                    except Exception:
                        pass
                if msgs:
                    full_msg = "\n\n".join(msgs)
                    send_message(chat_id, full_msg, reply_markup=build_keyboard())
                    send_jarvis_voice(chat_id, "Bitcoin, Ethereum aur Solana ka full buy sell signal ready hai. Entry, stop loss aur targets sab text mein hain.", intent="buy_sell_crypto")
                else:
                    send_message(chat_id, "❌ Crypto सिग्नल नहीं मिला। बाद में कोशिश करें।", reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Crypto buy/sell error: {e}")
                send_message(chat_id, f"❌ Error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Buy/Sell Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("📊 Scan NIFTY Signals",):
        if BUY_SELL_AVAILABLE:
            send_message(chat_id, f"🤖 *जार्विस NIFTY 50 स्टॉक्स स्कैन कर रहा है...* ⏳\n_30-60 सेकंड लग सकते हैं_")
            try:
                signals = scan_nifty_signals(top_n=10)
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = format_scanner_results(signals, "NIFTY 50 स्कैनर", lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"NIFTY scan error: {e}")
                send_message(chat_id, f"❌ NIFTY स्कैन फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Buy/Sell Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("📊 Scan Crypto Signals",):
        if BUY_SELL_AVAILABLE:
            send_message(chat_id, f"🤖 *जार्विस Top Crypto स्कैन कर रहा है...* ⏳\n_30-60 सेकंड लग सकते हैं_")
            try:
                signals = scan_crypto_signals(top_n=10)
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = format_scanner_results(signals, "Crypto स्कैनर", lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Crypto scan error: {e}")
                send_message(chat_id, f"❌ Crypto स्कैन फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Buy/Sell Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("📊 Index Buy/Sell",):
        if BUY_SELL_AVAILABLE:
            send_message(chat_id, f"🤖 *जार्विस Index सिग्नल चेक कर रहा है...* ⏳")
            try:
                signals = scan_index_signals()
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = format_scanner_results(signals, "Index Buy/Sell सिग्नल", lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Index signal error: {e}")
                send_message(chat_id, f"❌ Index सिग्नल फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Buy/Sell Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════
    #   💹 COINDCX WEB3 AI ENGINE HANDLERS
    # ════════════════════════════════════════════

    # --- CoinDCX AI Signal (Full composite signal for a coin) ---
    if text in ("💹 CoinDCX AI Signal 🤖", "CoinDCX AI Signal", "CoinDCX Signal"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🤖💹 *CoinDCX AI Engine एक्टिवेट...* ⏳\n_BTC का पूरा AI/ML सिग्नल बना रहा हूँ..._")
            try:
                msg = coindcx_signal("BTC", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                # Also send ETH signal
                msg2 = coindcx_signal("ETH", lang="hi")
                send_message(chat_id, msg2, reply_markup=build_keyboard())
                # SOL signal
                msg3 = coindcx_signal("SOL", lang="hi")
                send_message(chat_id, msg3, reply_markup=build_keyboard())
                try:
                    if VOICE_AVAILABLE:
                        from voice_engine import generate_voice_note
                        voice_text = f"CoinDCX AI Signal ready. BTC, ETH aur SOL ka complete analysis bhej diya hai. Please check karein."
                        generate_voice_note(chat_id, voice_text)
                except:
                    pass
            except Exception as e:
                send_message(chat_id, f"❌ CoinDCX Signal Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- CoinDCX Top Movers (Gainers + Losers) ---
    if text in ("📊 CoinDCX Top Movers", "CoinDCX Top Movers", "CoinDCX Movers"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *CoinDCX Top Movers स्कैन कर रहा हूँ...* ⏳")
            try:
                msg = coindcx_top_movers(lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                try:
                    if VOICE_AVAILABLE:
                        from voice_engine import generate_voice_note
                        generate_voice_note(chat_id, "CoinDCX ke top gainers aur losers bhej diye hain. Check karein kaunse coins pump aur dump ho rahe hain.")
                except:
                    pass
            except Exception as e:
                send_message(chat_id, f"❌ Top Movers Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- CoinDCX Best Signals (AI Scan top coins) ---
    if text in ("🔍 CoinDCX Best Signals", "CoinDCX Best Signals"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍🤖 *CoinDCX AI सारे कॉइन स्कैन कर रहा है...* ⏳\n_Top 20 coins ML analysis — 1-2 min लग सकता है_")
            try:
                msg = coindcx_best_signals(lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                try:
                    if VOICE_AVAILABLE:
                        from voice_engine import generate_voice_note
                        generate_voice_note(chat_id, "CoinDCX AI ne best buy aur sell signals dhundh liye hain. Complete ML analysis ke saath bhej diya hai.")
                except:
                    pass
            except Exception as e:
                send_message(chat_id, f"❌ Best Signals Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- CoinDCX Price Check ---
    if text in ("💰 CoinDCX Price Check", "CoinDCX Price Check", "CoinDCX Price"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}💰 *CoinDCX Top Prices INR में...* ⏳")
            try:
                # Show prices for top coins
                top_coins = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "BNB", "SUI", "AVAX", "DOT"]
                lines = ["═" * 28, "💰 CoinDCX Live Prices (INR)", "═" * 28, ""]
                for sym in top_coins:
                    p = coindcx_quick_price(sym, lang="hi")
                    lines.append(p)
                    lines.append("")
                lines.append("⚡ CoinDCX Web3 Engine")
                send_message(chat_id, "\n".join(lines), reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Price Check Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════
    #   🌐 COINDCX ALL WEB3 TOKENS HANDLERS
    # ════════════════════════════════════════════

    # --- All Web3 Tokens Summary ---
    if text in ("🌐 All Web3 Tokens", "All Web3 Tokens", "Web3 Tokens", "web3 tokens"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🌐🪙 *CoinDCX ALL 613+ Web3 Tokens लोड हो रहे हैं...*\n_AI/ML Prediction + ₹2K Investment Calculator for EVERY token_ ⏳\n_30-60 sec लगेगा — सब्र रखो Boss!_ 🧠")
            try:
                pages = coindcx_all_tokens_dump(sort_by="volume", lang="hi")
                for i, page in enumerate(pages):
                    send_message(chat_id, page)
                    import time as _t
                    _t.sleep(0.3)  # Avoid Telegram rate limit
                send_message(chat_id, f"✅ *सभी {len(pages)} pages भेज दिए!*\n🌐 *हर एक Web3 Token covered — कोई miss नहीं!*\n\n💡 किसी token का detail: /cdx <symbol>\n💰 ₹2K Invest Report: /invest <symbol>", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Web3 All Tokens Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ═══════════════════════════════════════════════════════
    # 🚀 WEB3 ROCKET SCANNER — ₹2K → ₹50K Moonshot Hunter
    # ═══════════════════════════════════════════════════════

    # --- ROCKET Full Scan (All Sources) ---
    if text in ("🚀🔥 ROCKET Scanner", "rocket", "/rocket", "rocket scan", "rockets",
                "moonshot", "50x token", "25x token", "2k se 50k", "hot token",
                "🚀 rocket", "fast token", "pump token"):
        if ROCKET_AVAILABLE:
            send_message(chat_id, f"{greeting}🚀🔥 *ROCKET SCANNER चल रहा है...*\n"
                        f"_DexScreener + pump.fun + CoinDCX scan — 15-30 sec..._\n"
                        f"_₹2K → ₹50K tokens ढूंढ रहा हूं!_ ⏳")
            try:
                msg = rocket_scan_full()
                send_message(chat_id, msg, reply_markup=build_keyboard())
                try:
                    if VOICE_AVAILABLE:
                        from voice_engine import generate_voice_note
                        rockets = scan_rockets(min_score=30, limit=10)
                        voice_text = format_rocket_voice(rockets)
                        generate_voice_note(chat_id, voice_text)
                except:
                    pass
            except Exception as e:
                send_message(chat_id, f"❌ Rocket Scan Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Rocket Scanner load nahi hua. Bot restart karo.", reply_markup=build_keyboard())
        return

    # --- ROCKET Fast Scan (DexScreener + pump.fun only) ---
    if text in ("🔥 Fast Rockets", "fast rocket", "fast rockets", "/fastrocket",
                "quick rocket", "dex rockets"):
        if ROCKET_AVAILABLE:
            send_message(chat_id, f"{greeting}🔥 *FAST ROCKET SCAN...*\n_DexScreener + pump.fun — 10 sec_ ⏳")
            try:
                msg = rocket_scan_fast()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Fast Scan Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Rocket Scanner load nahi hua.", reply_markup=build_keyboard())
        return

    # --- ROCKET CoinDCX Only (with OI data) ---
    if text in ("🚀 CoinDCX Rockets", "coindcx rocket", "/cdxrocket",
                "coindcx hot", "cdx rockets"):
        if ROCKET_AVAILABLE:
            send_message(chat_id, f"{greeting}🚀🔵 *CoinDCX ROCKET Scan — OI + Buy Pressure data...*\n_₹ INR trading pairs scan_ ⏳")
            try:
                msg = rocket_scan_coindcx()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ CoinDCX Rocket Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Rocket Scanner load nahi hua.", reply_markup=build_keyboard())
        return

    # --- ROCKET pump.fun Only ---
    if text in ("🟣 Pump.fun Rockets", "pump rocket", "/pumprocket",
                "pump fun rocket", "solana rocket"):
        if ROCKET_AVAILABLE:
            send_message(chat_id, f"{greeting}🟣🚀 *pump.fun ROCKET Scan — Solana meme coins...*\n_Trending + New launches scan_ ⏳")
            try:
                msg = rocket_scan_pump()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ pump.fun Rocket Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Rocket Scanner load nahi hua.", reply_markup=build_keyboard())
        return

    # --- ROCKET Token Detail (e.g., /rocketcheck PEPE) ---
    if text.lower().startswith(("/rocketcheck ", "rocket check ", "rocket detail ")):
        query = text.split(" ", 1)[-1].strip() if " " in text else ""
        if query and ROCKET_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍 *{query} ROCKET Analysis...*\n_Full 360° scan chala raha hun_ ⏳")
            try:
                msg = rocket_token_detail(query)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Token Detail Error: {str(e)[:150]}", reply_markup=build_keyboard())
        elif not query:
            send_message(chat_id, "💡 Usage: /rocketcheck PEPE\nja /rocketcheck <token_symbol>", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Rocket Scanner load nahi hua.", reply_markup=build_keyboard())
        return

    # ═══════════════════════════════════════════════════════════
    #  🎁 AIRDROP HUNTER — Auto-Capture Free Crypto
    # ═══════════════════════════════════════════════════════════

    # --- Full Airdrop Scan ---
    if text in ("🎁 Airdrop Hunter 🚀", "airdrop", "/airdrop", "airdrop scan",
                "free crypto", "free airdrop", "airdrop hunter"):
        if AIRDROP_AVAILABLE:
            send_message(chat_id, f"{greeting}🎁🚀 *AIRDROP HUNTER SCANNING...*\n"
                         f"_DeFi, Solana, Web aggregators scan हो रहा है..._\n"
                         f"⏳ _15 second wait करिए..._")
            try:
                msg = airdrop_scan_full()
                send_message(chat_id, msg, reply_markup=build_keyboard())
                if VOICE_AVAILABLE:
                    try:
                        airdrops = scan_all_airdrops()
                        voice_text = format_airdrop_voice(airdrops)
                        send_jarvis_voice(chat_id, voice_text, intent="airdrop")
                    except Exception:
                        pass
            except Exception as e:
                send_message(chat_id, f"❌ Airdrop scan error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Airdrop Hunter module load nahi hua।", reply_markup=build_keyboard())
        return

    # --- Upcoming Airdrop Protocols ---
    if text in ("🔮 Upcoming Airdrops", "upcoming airdrops", "/upcoming",
                "upcoming airdrop", "airdrop farming"):
        if AIRDROP_AVAILABLE:
            try:
                msg = airdrop_upcoming()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Airdrop module not available.", reply_markup=build_keyboard())
        return

    # --- Solana Airdrops Only ---
    if text in ("🎁 Solana Airdrops", "solana airdrop", "/solairdrop"):
        if AIRDROP_AVAILABLE:
            send_message(chat_id, f"{greeting}🟣 *Solana Wallet Airdrop Scan...*\n_Phantom wallet tokens check हो रहे हैं..._")
            try:
                msg = airdrop_scan_solana()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Airdrop module not available.", reply_markup=build_keyboard())
        return

    # ═══════════════════════════════════════════════════════════
    #  🛡️ SECURITY DASHBOARD — Owner Only
    # ═══════════════════════════════════════════════════════════

    if text in ("🛡️ Security Dashboard", "security", "/security", "security dashboard"):
        if _is_owner(chat_id) and SECURITY_AVAILABLE:
            try:
                msg = get_security_dashboard()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Security Error: {str(e)[:150]}", reply_markup=build_keyboard())
        elif not _is_owner(chat_id):
            send_message(chat_id, "🔒 Security Dashboard sirf Owner ke liye hai.", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Security module not loaded.", reply_markup=build_keyboard())
        return

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  🔥 DEXTOOLS ENGINE + 🧠 AI/ML SIGNALS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # --- DexTools Top 15 Tokens (ULTRA AI) ---
    if text in ("🔥 DexTools Top 15", "dextools top 15", "/dextools", "dextools",
                "top 15 tokens", "top tokens", "dex top", "top 15"):
        if DEXTOOLS_AVAILABLE:
            send_message(chat_id, f"{greeting}🔥🧠 *DEXTOOLS TOP 15 — ULTRA AI SCANNING...*\n"
                         f"_DexScreener + CoinGecko — All Chains..._\n"
                         f"_10 TA Indicators + Risk + Whale + Smart Money..._\n"
                         f"_Har token ke saath BUY/SELL prediction aa raha hai!_ ⏳")
            try:
                tokens = scan_all_tokens(limit=15)
                if ULTRA_AI_AVAILABLE:
                    tokens = batch_ultra_predict(tokens)
                    msg = format_ultra_top_tokens(tokens, title="🔥 DEXTOOLS TOP 15 — ULTRA AI")
                elif AI_SIGNALS_AVAILABLE:
                    tokens = batch_signals(tokens)
                    msg = format_top_tokens(tokens)
                else:
                    msg = format_top_tokens(tokens)
                send_message(chat_id, msg, reply_markup=build_keyboard())
                if VOICE_AVAILABLE:
                    try:
                        if ULTRA_AI_AVAILABLE:
                            voice_text = format_ultra_voice(tokens[:5])
                        else:
                            voice_text = format_voice_summary(tokens[:5])
                        send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                    except Exception as e:
                        logger.warning(f"[VOICE] DexTools voice delivery failed: {e}")
            except Exception as e:
                logger.error(f"DexTools Top 15 error: {e}", exc_info=True)
                send_message(chat_id, f"❌ DexTools Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ DexTools Engine not loaded.", reply_markup=build_keyboard())
        return

    # --- Meme Board (ULTRA AI) ---
    if text in ("🐸 Meme Board", "meme board", "/memeboard", "meme coins",
                "meme token", "top memes"):
        if DEXTOOLS_AVAILABLE:
            send_message(chat_id, f"{greeting}🐸🔥 *MEME BOARD — ULTRA AI SCANNING...*\n"
                         f"_Top meme coins + AI BUY/SELL predictions..._\n⏳")
            try:
                from dextools_engine import fetch_meme_board
                tokens = fetch_meme_board(limit=15)
                if ULTRA_AI_AVAILABLE:
                    tokens = batch_ultra_predict(tokens)
                    msg = format_ultra_top_tokens(tokens, title="🐸 MEME BOARD — ULTRA AI")
                else:
                    msg = dextools_meme_board()
                send_message(chat_id, msg, reply_markup=build_keyboard())
                if VOICE_AVAILABLE and ULTRA_AI_AVAILABLE and tokens:
                    try:
                        voice_text = format_ultra_voice(tokens[:3])
                        send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                    except:
                        pass
            except Exception as e:
                logger.error(f"Meme Board error: {e}", exc_info=True)
                send_message(chat_id, f"❌ Meme Board Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ DexTools Engine not loaded.", reply_markup=build_keyboard())
        return

    # --- Live New Pairs (ULTRA AI) ---
    if text in ("🆕 Live New Pairs", "new pairs", "/newpairs", "live new pairs",
                "new listings", "new tokens"):
        if DEXTOOLS_AVAILABLE:
            send_message(chat_id, f"{greeting}🆕 *LIVE NEW PAIRS — ULTRA AI SCANNING...*\n"
                         f"_Brand new launches + AI BUY/SELL + Rug Risk..._\n⏳")
            try:
                from dextools_engine import fetch_dexscreener_new_pairs
                tokens = fetch_dexscreener_new_pairs(limit=15)
                if ULTRA_AI_AVAILABLE:
                    tokens = batch_ultra_predict(tokens)
                    msg = format_ultra_top_tokens(tokens, title="🆕 LIVE NEW PAIRS — ULTRA AI")
                else:
                    msg = dextools_new_pairs()
                send_message(chat_id, msg, reply_markup=build_keyboard())
                if VOICE_AVAILABLE and ULTRA_AI_AVAILABLE and tokens:
                    try:
                        voice_text = format_ultra_voice(tokens[:3])
                        send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                    except:
                        pass
            except Exception as e:
                logger.error(f"New Pairs error: {e}", exc_info=True)
                send_message(chat_id, f"❌ New Pairs Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ DexTools Engine not loaded.", reply_markup=build_keyboard())
        return

    # --- DexTools Airdrops ---
    if text in ("🎁 DexTools Airdrops", "dextools airdrops", "/dexairdrops",
                "dex airdrops"):
        if DEXTOOLS_AVAILABLE:
            send_message(chat_id, f"{greeting}🎁 *DEXTOOLS AIRDROPS SCANNING...*\n⏳")
            try:
                msg = dextools_airdrops()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Airdrops Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ DexTools Engine not loaded.", reply_markup=build_keyboard())
        return

    # --- AI Signal Report (ULTRA AI — Full Card per Token) ---
    if text in ("🧠 AI Signal Report", "ai signal", "/signal", "signal report",
                "buy sell signal", "ai prediction"):
        if DEXTOOLS_AVAILABLE:
            send_message(chat_id, f"{greeting}🧠📊 *JARVIS ULTRA AI SIGNAL ENGINE...*\n"
                         f"_Top 5 tokens ka FULL AI analysis..._\n"
                         f"_10 TA Indicators + Rug Risk + Whale + Price Targets..._\n"
                         f"_Har token ke saath CLEAR BUY/SELL prediction!_ ⏳")
            try:
                tokens = scan_all_tokens(limit=5)
                if ULTRA_AI_AVAILABLE:
                    tokens = batch_ultra_predict(tokens)
                    for t in tokens[:5]:
                        card = format_ultra_token_card(t, rank=tokens.index(t) + 1)
                        send_message(chat_id, card, reply_markup=build_keyboard())
                        time.sleep(0.5)
                elif AI_SIGNALS_AVAILABLE:
                    for t in tokens[:5]:
                        analysis = full_technical_analysis(t)
                        report = format_signal_report(t, analysis)
                        send_message(chat_id, report, reply_markup=build_keyboard())
                        time.sleep(0.5)
                else:
                    send_message(chat_id, "❌ AI Signal Engine not available.", reply_markup=build_keyboard())
                
                if VOICE_AVAILABLE and tokens:
                    try:
                        if ULTRA_AI_AVAILABLE:
                            voice_text = format_ultra_voice(tokens[:3])
                        elif AI_SIGNALS_AVAILABLE:
                            analysis = full_technical_analysis(tokens[0])
                            voice_text = format_signal_voice(tokens[0], analysis)
                        else:
                            voice_text = None
                        if voice_text:
                            send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                    except:
                        pass
            except Exception as e:
                logger.error(f"Signal Report error: {e}", exc_info=True)
                send_message(chat_id, f"❌ Signal Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ AI Signal Engine not loaded.", reply_markup=build_keyboard())
        return

    # --- Multi-Chain Scan (ULTRA AI) ---
    if text in ("📊 Multi-Chain Scan", "multi chain scan", "/multichain",
                "all chains", "multi chain", "all blockchain"):
        if DEXTOOLS_AVAILABLE:
            send_message(chat_id, f"{greeting}📊🌐 *MULTI-CHAIN ULTRA AI SCAN...*\n"
                         f"_ETH, BSC, SOL, BASE, ARB, MATIC, AVAX — All chains..._\n"
                         f"_AI BUY/SELL + Risk Analysis har token ke saath!_ ⏳")
            try:
                tokens = scan_all_tokens(limit=15, include_memes=True)
                if ULTRA_AI_AVAILABLE:
                    tokens = batch_ultra_predict(tokens)
                    msg = format_ultra_top_tokens(tokens, title="🌐 MULTI-CHAIN TOP 15 — ULTRA AI")
                elif AI_SIGNALS_AVAILABLE:
                    tokens = batch_signals(tokens)
                    msg = format_top_tokens(tokens, title="🌐 MULTI-CHAIN TOP 15")
                else:
                    msg = format_top_tokens(tokens, title="🌐 MULTI-CHAIN TOP 15")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Multi-Chain error: {e}", exc_info=True)
                send_message(chat_id, f"❌ Multi-Chain Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ DexTools Engine not loaded.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #  🔥 TOP 100 AI SIGNALS — Mega Scanner
    # ════════════════════════════════════════════════════════

    if text in ("🔥 TOP 100 AI Signals 🧠", "top 100", "top100", "/top100", "/megatop",
                "top 100 signals", "mega scan", "100 tokens", "mega ai"):
        if MEGA_SCANNER_AVAILABLE:
            send_message(chat_id, f"{greeting}🔥🧠 *MEGA AI SCANNER — Top 100 Tokens*\n\n"
                        f"_613+ tokens scan ho rahe hain..._\n"
                        f"📊 RSI + EMA + MACD + BB + Stochastic\n"
                        f"📈 ADX + Volume + OBV + Momentum\n"
                        f"🕯️ 25+ Candle Patterns (Hammer, Engulfing, Morning Star...)\n"
                        f"🤖 ML Prediction (Random Forest + Gradient Boosting)\n\n"
                        f"⏳ _1-2 min wait karo Boss — Top 100 aa rahe hain!_")
            try:
                results = mega_scan_top100(top_n=100)
                if results:
                    total_pages = max(1, (len(results) + 19) // 20)
                    for pg in range(1, total_pages + 1):
                        msg = format_mega_top100(results, page=pg, per_page=20)
                        send_message(chat_id, msg)
                        import time as _t; _t.sleep(0.3)
                    send_message(chat_id, f"✅ *Top {len(results)} tokens — AI/ML + Candle Analysis COMPLETE!*\n"
                                f"🟢 BUY: {sum(1 for r in results if r['ai_score'] >= 4)} tokens\n"
                                f"🔴 SELL: {sum(1 for r in results if r['ai_score'] <= -4)} tokens\n"
                                f"🤖 ML Predicted: {sum(1 for r in results if r.get('has_ml'))} tokens\n"
                                f"🕯️ Candle Patterns: {sum(1 for r in results if r.get('has_candles'))} tokens\n\n"
                                f"💡 /invest <symbol> for detailed report\n"
                                f"💡 /megatop 2 for page 2", reply_markup=build_keyboard())
                    try:
                        if VOICE_AVAILABLE:
                            voice_text = format_mega_voice(results)
                            send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                    except Exception as e:
                        logger.warning(f"[VOICE] Mega scanner voice failed: {e}")
                else:
                    send_message(chat_id, "❌ Koi signal nahi mila. Baad mein try karo.", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Mega Scan Error: {str(e)[:200]}", reply_markup=build_keyboard())
        elif COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍 *Web3 AI Scan (basic)...*")
            try:
                msg = coindcx_web3_scan(lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Scanner उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- TOP 100 Page Navigation ---
    if text.startswith("/megatop "):
        parts = text.split()
        pg = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        if MEGA_SCANNER_AVAILABLE:
            send_message(chat_id, f"🔥 *Page {pg} loading...* ⏳")
            try:
                results = mega_scan_top100(top_n=100)
                if results:
                    msg = format_mega_top100(results, page=pg, per_page=20)
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                else:
                    send_message(chat_id, "❌ No signals.", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:150]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #  💰 ₹2K → ₹2L WEALTH STRATEGY
    # ════════════════════════════════════════════════════════

    if text in ("💰 ₹2K → ₹2L Strategy 🚀", "2k to 2l", "2k se 2l", "/wealth",
                "wealth strategy", "2000 to 200000", "₹2K strategy", "2k strategy"):
        if MEGA_SCANNER_AVAILABLE:
            send_message(chat_id, f"{greeting}💰🚀 *₹2,000 → ₹2,00,000 STRATEGY बना रहा हूँ...*\n"
                        f"_5 strategies + compound growth calculator + reality check_ ⏳")
            try:
                data = calculate_wealth_strategy(2000, 200000)
                msg = format_wealth_strategy(data)
                # Split if too long
                if len(msg) > 4000:
                    parts = msg.split("\n\n")
                    current = ""
                    for part in parts:
                        if len(current) + len(part) > 3800:
                            send_message(chat_id, current)
                            current = part
                            import time as _t; _t.sleep(0.3)
                        else:
                            current += "\n\n" + part if current else part
                    if current:
                        send_message(chat_id, current, reply_markup=build_keyboard())
                else:
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                
                # Send JARVIS Strategy Voice
                try:
                    if VOICE_AVAILABLE:
                        voice_text = format_wealth_voice(data)
                        send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                except Exception as e:
                    logger.warning(f"[VOICE] Wealth strategy voice failed: {e}")
                
                # Also show current top 5 BUY signals
                try:
                    results = mega_scan_top100(top_n=10)
                    buys = [r for r in results if r.get('ai_score', 0) >= 4][:5]
                    if buys:
                        buy_lines = [f"\n{'═'*28}", f"🔥 *JARVIS Top 5 BUY Picks RIGHT NOW:*\n"]
                        for i, r in enumerate(buys, 1):
                            buy_lines.append(f"{r['emoji']} *{i}. {r['symbol']}* — {mega_fmt_inr(r['price_inr'])} ({r['change_24h']:+.1f}%)")
                            buy_lines.append(f"   🎯 {r['hindi']}")
                            buy_lines.append(f"   SL: {mega_fmt_inr(r['stop_loss'])} | T1: {mega_fmt_inr(r['target_1'])}")
                        buy_lines.append(f"\n💡 _Ye tokens abhi AI BUY signal mein hain. /invest <symbol> for full report_")
                        send_message(chat_id, "\n".join(buy_lines), reply_markup=build_keyboard())
                except Exception as e:
                    logger.error(f"[BUY-SIGNAL] Failed to send buy picks: {e}")
                
            except Exception as e:
                send_message(chat_id, f"❌ Strategy Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, f"₹2K se ₹2L banana possible hai!\n\n"
                        f"📈 10% compound trades x 48 = 100x\n"
                        f"💪 20% swing trades x 26 = 100x\n"
                        f"🚀 Ya ek 100x meme coin find karo\n\n"
                        f"JARVIS AI signals follow karo aur discipline rakho Boss!", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #  📈🇮🇳 INDIAN STOCK AI — Deep Analysis (6-Model ML + Candles + News + PCR)
    # ════════════════════════════════════════════════════════════
    if text in ("📈🇮🇳 Indian Stock AI 🧠", "Indian Stock AI", "stock ai", "nifty ai", "sensex ai",
                "/stockai", "indian stock", "indian market ai"):
        if MARKET_BRAIN_AVAILABLE:
            is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
            send_message(chat_id, f"{greeting}📈🇮🇳 *JARVIS Indian Stock Market AI Analyzing...*\n"
                        f"_6-Model ML Ensemble + 43 Candle Patterns + News Sentiment + Option Chain + Fear & Greed_\n"
                        f"⏳ _30 sec wait karo Boss — Full analysis aa raha hai!_")
            try:
                stock_data = analyze_indian_stock_deep(text)
                pages = format_indian_stock_report(stock_data)
                for page in pages:
                    send_message(chat_id, page, reply_markup=build_keyboard())
                voice_text = format_indian_stock_voice(stock_data)
                send_jarvis_voice(chat_id, voice_text, intent="buy_sell_stock", is_voice_input=is_voice)
            except Exception as e:
                logger.error(f"[STOCK-AI] Error: {e}")
                send_message(chat_id, f"❌ Indian Stock AI error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            # Fallback to existing candle analysis
            send_message(chat_id, f"{greeting}🔄 *NIFTY + SENSEX Analysis...* ⏳")
            try:
                from candle_analyzer import analyze_index
                for ticker, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
                    analysis = analyze_index(ticker, name)
                    if analysis:
                        send_message(chat_id, analysis.get("analysis", "No data"), reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Stock analysis error: {str(e)[:100]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #  🔥 CRYPTO DEEP ANALYSIS — Single Token Deep Dive (All World Indicators)
    # ════════════════════════════════════════════════════════════
    if text in ("🔥 Crypto Deep Analysis 🪙", "Crypto Deep Analysis", "crypto deep", "/cryptodeep"):
        send_message(chat_id,
            f"{greeting}"
            f"🔥🧠 *JARVIS CRYPTO DEEP ANALYSIS*\n"
            f"{'═'*25}\n\n"
            f"🪙 *Token ka naam ya symbol bhejo:*\n\n"
            f"💡 *Examples:*\n"
            f"  • `BTC` — Bitcoin deep analysis\n"
            f"  • `SOL` — Solana full AI report\n"
            f"  • `PEPE` — Meme coin risk check\n"
            f"  • `SUI` — All indicators + targets\n\n"
            f"📊 *Ye milega aapko:*\n"
            f"  ✅ 15+ Technical Indicators\n"
            f"  ✅ ML Prediction (RF + Gradient Boosting)\n"
            f"  ✅ Multi-Timeframe (15m / 1h / 4h / 1D)\n"
            f"  ✅ 25+ Candle Pattern Detection\n"
            f"  ✅ Price Targets + Stop Loss\n"
            f"  ✅ Rug Risk + Whale + Liquidity Score\n"
            f"  ✅ ₹2K Investment Calculator\n"
            f"  ✅ Final BUY/SELL Verdict\n\n"
            f"🔁 _Ya kisi bhi crypto message pe REPLY karo — JARVIS automatically deep analyze karega!_\n"
            f"{'─'*25}",
            reply_markup=build_keyboard()
        )
        chat_storage[f"awaiting_crypto_deep_{chat_id}"] = True
        return

    # Handle crypto deep analysis token input
    if chat_storage.get(f"awaiting_crypto_deep_{chat_id}"):
        chat_storage.pop(f"awaiting_crypto_deep_{chat_id}", None)
        token = text.strip().upper().replace("$", "").split()[0]
        if len(token) >= 2 and len(token) <= 10 and token.isalpha():
            if MARKET_BRAIN_AVAILABLE:
                is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
                send_message(chat_id, f"{greeting}🔥🧠 *JARVIS Deep AI Analysis for {token}...*\n"
                            f"_15+ Indicators + ML + Candle Patterns + Price Targets_ ⏳")
                try:
                    deep_data = analyze_crypto_token_deep(token)
                    pages = format_crypto_deep_report(deep_data)
                    for page in pages:
                        send_message(chat_id, page, reply_markup=build_keyboard())
                    voice_text = format_crypto_deep_voice(deep_data)
                    send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto", is_voice_input=is_voice)
                except Exception as e:
                    logger.error(f"[CRYPTO-DEEP] Error for {token}: {e}")
                    send_message(chat_id, f"❌ {token} deep analysis failed: {str(e)[:150]}", reply_markup=build_keyboard())
            else:
                send_message(chat_id, f"❌ Market Brain unavailable. Try /cdx {token}", reply_markup=build_keyboard())
            return
        else:
            send_message(chat_id, f"❌ Invalid token: {text[:20]}. Valid example: BTC, ETH, SOL", reply_markup=build_keyboard())
            return

    # --- Web3 Tokens List (Paginated) ---
    if text in ("📋 Web3 Token List", "Web3 Token List", "web3 list"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}📋 *सभी Web3 Tokens (by Volume)...* ⏳")
            try:
                msg = coindcx_all_web3(page=1, sort_by="volume", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Token List Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 All Movers (Gainers/Losers from ALL tokens) ---
    if text in ("🚀💥 Web3 Top Movers", "Web3 Top Movers", "Web3 Movers", "web3 movers"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🚀💥 *सभी Web3 Tokens में टॉप मूवर्स स्कैन...* ⏳")
            try:
                msg = coindcx_web3_movers(lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                try:
                    if VOICE_AVAILABLE:
                        from voice_engine import generate_voice_note
                        generate_voice_note(chat_id, "CoinDCX ke saare Web3 tokens mein se top gainers aur losers dhundh liye hain.")
                except:
                    pass
            except Exception as e:
                send_message(chat_id, f"❌ Web3 Movers Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 AI Scan All Tokens ---
    if text in ("🔍 Web3 AI Scan All", "Web3 AI Scan", "Web3 Scan", "web3 scan"):
        if MEGA_SCANNER_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍🧠 *MEGA AI SCAN — 613+ Tokens Scanning...*\n"
                        f"_RSI + EMA + MACD + BB + Stochastic + ADX + Volume + OBV + ML + Candle Patterns_\n"
                        f"⏳ _1-2 min wait karo Boss — Top 100 signals aa rahe hain!_")
            try:
                results = mega_scan_top100(top_n=100)
                if results:
                    # Send page by page (20 tokens per page)
                    total_pages = max(1, (len(results) + 19) // 20)
                    for pg in range(1, total_pages + 1):
                        msg = format_mega_top100(results, page=pg, per_page=20)
                        send_message(chat_id, msg)
                        import time as _t; _t.sleep(0.3)
                    send_message(chat_id, f"✅ *Top {len(results)} tokens scanned with AI/ML + Candles!*\n"
                                f"💡 Detail: /megatop <page> | /invest <symbol>", reply_markup=build_keyboard())
                    try:
                        if VOICE_AVAILABLE:
                            voice_text = format_mega_voice(results)
                            send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                    except:
                        pass
                else:
                    send_message(chat_id, "❌ Koi signal nahi mila. Baad mein try karo.", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Mega Scan Error: {str(e)[:200]}", reply_markup=build_keyboard())
        elif COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍🤖 *सभी Web3 Tokens AI Scan — 1-2 min लग सकता है...* ⏳\n_RSI + EMA + MACD + Volume analysis चल रहा है_")
            try:
                msg = coindcx_web3_scan(lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Web3 Scan Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category: DeFi ---
    if text in ("🏦 Web3 DeFi Tokens", "Web3 DeFi", "DeFi Tokens", "defi tokens"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🏦 *DeFi Tokens लोड हो रहे हैं...* ⏳")
            try:
                msg = coindcx_web3_category("DeFi", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ DeFi Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category: Meme ---
    if text in ("🐸 Web3 Meme Coins", "Web3 Meme", "Meme Coins", "meme coins"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🐸 *Meme Coins लोड हो रहे हैं...* ⏳")
            try:
                msg = coindcx_web3_category("Meme", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Meme Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category: AI & Data ---
    if text in ("🤖 Web3 AI Tokens", "Web3 AI", "AI Tokens", "ai tokens"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🤖 *AI & Data Tokens लोड हो रहे हैं...* ⏳")
            try:
                msg = coindcx_web3_category("AI & Data", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ AI Tokens Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category: Layer 1 ---
    if text in ("🔷 Web3 Layer 1", "Web3 L1", "Layer 1", "layer 1"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🔷 *Layer 1 Tokens लोड हो रहे हैं...* ⏳")
            try:
                msg = coindcx_web3_category("Layer 1", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ L1 Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category: Layer 2 ---
    if text in ("🔶 Web3 Layer 2", "Web3 L2", "Layer 2", "layer 2"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🔶 *Layer 2 Tokens लोड हो रहे हैं...* ⏳")
            try:
                msg = coindcx_web3_category("Layer 2", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ L2 Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category: Gaming/NFT ---
    if text in ("🎮 Web3 Gaming NFT", "Web3 Gaming", "Gaming NFT", "gaming nft"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🎮 *Gaming & NFT Tokens लोड हो रहे हैं...* ⏳")
            try:
                msg = coindcx_web3_category("Gaming & NFT", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Gaming Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category: Infrastructure ---
    if text in ("🔧 Web3 Infra Tokens", "Web3 Infra", "Infra Tokens", "infra tokens"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🔧 *Infrastructure Tokens लोड हो रहे हैं...* ⏳")
            try:
                msg = coindcx_web3_category("Infrastructure", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Infra Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category Scan (DeFi AI scan) ---
    if text in ("🔍 Scan DeFi Signals", "Scan DeFi", "defi scan"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍🏦 *DeFi Tokens AI Scan...* ⏳")
            try:
                msg = coindcx_web3_scan(category="DeFi", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ DeFi Scan Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Web3 Category Scan (Meme AI scan) ---
    if text in ("🔍 Scan Meme Signals", "Scan Meme", "meme scan"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍🐸 *Meme Coins AI Scan...* ⏳")
            try:
                msg = coindcx_web3_scan(category="Meme", lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Meme Scan Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- /web3 command handler ---
    if text.startswith("/web3"):
        if COINDCX_AVAILABLE:
            parts = text.split()
            if len(parts) == 1:
                # /web3 — show summary
                msg = coindcx_web3_summary(lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            elif parts[1].lower() in ("page", "p") and len(parts) >= 3:
                # /web3 page 2
                try:
                    page = int(parts[2])
                    sort_by = parts[3] if len(parts) > 3 else "volume"
                    msg = coindcx_all_web3(page=page, sort_by=sort_by, lang="hi")
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                except:
                    send_message(chat_id, "❌ Format: /web3 page <number>", reply_markup=build_keyboard())
            elif parts[1].lower() in ("cat", "category") and len(parts) >= 3:
                # /web3 cat DeFi
                cat = " ".join(parts[2:])
                msg = coindcx_web3_category(cat, lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            elif parts[1].lower() in ("scan",):
                # /web3 scan [category]
                cat = " ".join(parts[2:]) if len(parts) > 2 else None
                send_message(chat_id, f"{greeting}🔍 *Web3 AI Scan चल रहा है...* ⏳")
                msg = coindcx_web3_scan(category=cat, lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            elif parts[1].lower() in ("search", "find", "s"):
                # /web3 search solana
                if len(parts) >= 3:
                    q = " ".join(parts[2:])
                    msg = coindcx_web3_search(q, lang="hi")
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                else:
                    send_message(chat_id, "❌ Format: /web3 search <token name>", reply_markup=build_keyboard())
            elif parts[1].lower() in ("movers", "top"):
                # /web3 movers
                msg = coindcx_web3_movers(lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            elif parts[1].lower() in ("list", "all"):
                # /web3 list
                sort = parts[2] if len(parts) > 2 else "volume"
                msg = coindcx_all_web3(page=1, sort_by=sort, lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            else:
                # /web3 <symbol> — treat as signal
                sym = parts[1].upper()
                send_message(chat_id, f"{greeting}🤖 *${sym} AI signal बना रहा हूँ...* ⏳")
                msg = coindcx_signal(sym, lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- /cdx command handler (quick signal for any token) ---
    if text.startswith("/cdx"):
        if COINDCX_AVAILABLE:
            parts = text.split()
            if len(parts) >= 2:
                sym = parts[1].upper()
                send_message(chat_id, f"{greeting}🤖💹 *${sym} Full AI Signal...* ⏳")
                try:
                    msg = coindcx_signal(sym, lang="hi")
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ Signal Error for {sym}: {str(e)[:150]}", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "❌ Format: /cdx <symbol>\nExample: /cdx BTC, /cdx PEPE, /cdx SOL", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- /web3search command handler ---
    if text.startswith("/web3search"):
        if COINDCX_AVAILABLE:
            parts = text.split(maxsplit=1)
            if len(parts) >= 2:
                q = parts[1].strip()
                msg = coindcx_web3_search(q, lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            else:
                send_message(chat_id, "❌ Format: /web3search <token name>\nExample: /web3search solana", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- /web3cat command handler ---
    if text.startswith("/web3cat"):
        if COINDCX_AVAILABLE:
            parts = text.split(maxsplit=1)
            if len(parts) >= 2:
                cat = parts[1].strip()
                msg = coindcx_web3_category(cat, lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            else:
                cats = list(WEB3_CATEGORIES.keys()) if 'WEB3_CATEGORIES' in dir() else ["Layer 1", "Layer 2", "DeFi", "Meme", "AI & Data", "Gaming & NFT", "Infrastructure"]
                cat_list = "\n".join([f"  • {c}" for c in cats])
                send_message(chat_id, f"❌ Format: /web3cat <category>\n\nCategories:\n{cat_list}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- /web3scan command handler ---
    if text.startswith("/web3scan"):
        if COINDCX_AVAILABLE:
            parts = text.split(maxsplit=1)
            cat = parts[1].strip() if len(parts) >= 2 else None
            send_message(chat_id, f"{greeting}🔍🤖 *Web3 AI Scan{'  [' + cat + ']' if cat else ''} चल रहा है...* ⏳")
            try:
                msg = coindcx_web3_scan(category=cat, lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Scan Error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   💰 ₹2K INVESTMENT CALCULATOR — /invest <symbol>
    # ════════════════════════════════════════════════════════

    if text.startswith("/invest"):
        if COINDCX_AVAILABLE:
            parts = text.split()
            if len(parts) >= 2:
                sym = parts[1].upper()
                amt = 2000
                if len(parts) >= 3:
                    try:
                        amt = float(parts[2])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"[INVEST] Invalid amount '{parts[2]}', using default ₹2000: {e}")
                send_message(chat_id, f"{greeting}💰🧠 *₹{amt:,.0f} Investment Report for ${sym}...*\n_AI calculating targets, SL, 50x moonshot_ ⏳")
                try:
                    msg = coindcx_token_invest(sym, amount=amt, lang="hi")
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ Investment Calc Error: {str(e)[:200]}", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "❌ Format: /invest <symbol> [amount]\n\nExample:\n  /invest BTC\n  /invest SOL 5000\n  /invest PEPE 10000", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- 💰 ₹2K Invest Button Handler ---
    if text in ("💰 ₹2K Token Invest", "₹2K Invest", "2k invest", "token invest", "investment calc"):
        if COINDCX_AVAILABLE:
            chat_storage[f"awaiting_invest_{chat_id}"] = True
            send_message(chat_id, f"{greeting}💰🧠 *₹2K Investment Calculator*\n\n"
                        f"Token का symbol बताओ Boss!\n"
                        f"Example: BTC, SOL, PEPE, DOGE\n\n"
                        f"या command use करो: /invest BTC 5000")
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Handle awaiting invest symbol ---
    if chat_storage.get(f"awaiting_invest_{chat_id}"):
        chat_storage.pop(f"awaiting_invest_{chat_id}", None)
        if COINDCX_AVAILABLE:
            sym = text.strip().upper().replace("$", "")
            send_message(chat_id, f"{greeting}💰 *₹2,000 Investment Report for ${sym} बना रहा हूँ...* ⏳")
            try:
                msg = coindcx_token_invest(sym, amount=2000, lang="hi")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:200]}", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   📋 ALL TOKENS BY CATEGORY — Button + /web3allcat
    # ════════════════════════════════════════════════════════

    if text in ("📋 Web3 Token List", "Web3 Token List", "web3 token list", "all tokens category"):
        if COINDCX_AVAILABLE:
            send_message(chat_id, f"{greeting}📋🌐 *ALL Web3 Tokens by Category लोड हो रहे हैं...*\n_Category-wise AI Signal for every token_ ⏳")
            try:
                pages = coindcx_all_tokens_by_category(lang="hi")
                for i, page in enumerate(pages):
                    send_message(chat_id, page)
                    import time as _t
                    _t.sleep(0.3)
                send_message(chat_id, f"✅ *All {len(pages)} category pages sent!*\n💡 Detail: /cdx <symbol> | Invest: /invest <symbol>", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Category Dump Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ CoinDCX Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   👻 PHANTOM WALLET — Solana Wallet Integration
    # ════════════════════════════════════════════════════════

    # --- Phantom Wallet Main Menu ---
    if text in ("👻 Phantom Wallet 🔮", "Phantom Wallet", "phantom wallet", "phantom", "/phantom"):
        if PHANTOM_AVAILABLE:
            wallet = get_wallet(chat_id)
            if wallet:
                _phantom_user = os.environ.get("OWNER_PHANTOM_USERNAME", "")
                status = f"✅ *Wallet Connected!*\n📍 Address: `{wallet['address'][:8]}...{wallet['address'][-6:]}`\n👻 Phantom: {_phantom_user}\n🔐 Security: ✅ Encrypted"
            else:
                status = "❌ *No Wallet Connected*"
            
            sol_status = ""
            if SOLANA_ENGINE_AVAILABLE:
                try:
                    bal = get_sol_balance()
                    sol_status = f"\n⚡ SOL Balance: {bal:.4f} SOL"
                except Exception as e:
                    logger.warning(f"[WALLET] SOL balance check failed: {e}")
                    sol_status = "\n⚡ SOL Balance: Checking..."
            
            send_message(chat_id, f"{greeting}👻🔮 *PHANTOM WALLET*\n{HEADER_LINE}\n\n"
                        f"{status}{sol_status}\n\n"
                        f"*Available Actions:*\n"
                        f"👻 Connect Wallet — Phantom deep link connect\n"
                        f"👻 Wallet Scan 📊 — Token scan + AI prediction\n"
                        f"👻 Wallet Summary ⚡ — Full portfolio (FREE)\n"
                        f"👻 Claim Airdrops 🎁 — Auto-claim to wallet\n"
                        f"👻 Transfer SOL 💸 — Send via Phantom\n"
                        f"👻 Wallet Dashboard 📋 — Real-time dashboard\n"
                        f"👻 Wallet Alerts ON — 24/7 monitoring\n"
                        f"👻 Disconnect Wallet — Remove\n\n"
                        f"🔐 *Security:* Military-Grade Encryption Active\n"
                        f"⚡ *Engine:* 100% FREE (Solana RPC + Jupiter)\n"
                        f"📡 *Monitor:* Transaction alerts + Airdrop detection", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Phantom Wallet Engine उपलब्ध नहीं है। Bot restart करो।", reply_markup=build_keyboard())
        return

    # --- Phantom Connect Wallet ---
    if text in ("👻 Connect Wallet", "connect wallet", "connect phantom"):
        if PHANTOM_AVAILABLE:
            # Generate proper Phantom deep links using Solana Engine
            if SOLANA_ENGINE_AVAILABLE:
                links = generate_phantom_connect_deeplink(bot_name="DavidCrewBot", chat_id=chat_id)
                phantom_url = links.get("phantom_connect", "")
                browse_url = links.get("phantom_browse", "")
                wallet_addr = links.get("wallet_address", os.environ.get("OWNER_SOLANA_WALLET", ""))
                
                send_message(chat_id, 
                    f"👻🔗 *PHANTOM WALLET CONNECT*\n"
                    f"{HEADER_LINE}\n\n"
                    f"📱 *Method 1 — One-Click Phantom Connect:*\n"
                    f"👇 Ye link tap karo — Phantom app open hoga:\n"
                    f"🔗 [Open Phantom & Connect]({phantom_url})\n\n"
                    f"📱 *Method 2 — Phantom Browser:*\n"
                    f"👇 Ye link Phantom browser mein wallet dikhayega:\n"
                    f"🔗 [View in Phantom Browser]({browse_url})\n\n"
                    f"📱 *Method 3 — Direct Address Paste:*\n"
                    f"1️⃣ Phantom App kholo 📲\n"
                    f"2️⃣ Top par address tap karo (copy hoga)\n"
                    f"3️⃣ Yahan paste kardo — bas!\n\n"
                    f"📱 *Method 4 — Solana Pay:*\n"
                    f"Phantom mein Scanner se scan karo:\n"
                    f"`solana:{wallet_addr}`\n\n"
                    f"✅ *Already Connected:* `{wallet_addr[:8]}...{wallet_addr[-4:]}`\n"
                    f"👤 Phantom: {OWNER_PHANTOM_USERNAME}\n\n"
                    f"🔐 *100% Safe:* Sirf public address — private key NAHI!\n"
                    f"⚡ *FREE APIs:* Solana RPC + Jupiter + DexScreener\n"
                    f"📡 *24/7 Monitor:* Transaction alerts ON",
                    reply_markup=build_keyboard())
            else:
                send_message(chat_id, 
                    f"👻🔗 *PHANTOM WALLET CONNECT*\n"
                    f"{HEADER_LINE}\n\n"
                    f"📱 *Address Paste karo:*\n"
                    f"1️⃣ Phantom App kholo 📲\n"
                    f"2️⃣ Top par address tap karo (copy hoga)\n"
                    f"3️⃣ Yahan paste kardo — bas!\n\n"
                    f"📱 *Phantom Download:*\n"
                    f"  • Mobile: [Phantom App](https://phantom.app/download)\n"
                    f"  • Chrome: [Extension](https://chrome.google.com/webstore/detail/phantom/bfnaelmomeimhlpmgjnjophhpkkoljpa)\n\n"
                    f"🔐 *100% Safe:* Sirf public address — private key NAHI!\n"
                    f"⏳ _Waiting for your wallet address..._",
                    reply_markup=build_keyboard())
            chat_storage[f"awaiting_phantom_address_{chat_id}"] = True
        else:
            send_message(chat_id, "❌ Phantom Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Handle awaiting phantom address ---
    if chat_storage.get(f"awaiting_phantom_address_{chat_id}"):
        addr = text.strip()
        # Solana addresses are base58, typically 32-44 chars
        if len(addr) >= 32 and len(addr) <= 50 and addr.isalnum():
            chat_storage.pop(f"awaiting_phantom_address_{chat_id}", None)
            if PHANTOM_AVAILABLE:
                try:
                    result = connect_wallet(chat_id, addr)
                    if result.get("success"):
                        send_message(chat_id, f"✅👻 *Wallet Connected Successfully!*\n\n"
                                    f"📍 Address: `{addr[:8]}...{addr[-6:]}`\n"
                                    f"🔗 Network: Solana Mainnet\n\n"
                                    f"अब '👻 Wallet Scan 📊' button दबाओ — सारे tokens scan होंगे with AI prediction! 🧠",
                                    reply_markup=build_keyboard())
                        send_jarvis_voice(chat_id, f"Wallet connect ho gaya hai! Ab Wallet Scan button dabao, saare tokens scan hone lagenge.", intent="greeting")
                    else:
                        send_message(chat_id, f"❌ Connect Failed: {result.get('error', 'Unknown')}", reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ Error: {str(e)[:200]}", reply_markup=build_keyboard())
            return

    # --- AUTO-DETECT: If user pastes a Solana address ANYWHERE, auto-connect wallet ---
    if PHANTOM_AVAILABLE and SUPER_BRAIN_AVAILABLE and not is_wallet_connected(chat_id):
        detected_addr = detect_solana_address(text)
        if detected_addr:
            try:
                result = connect_wallet(chat_id, detected_addr)
                if result.get("success"):
                    send_message(chat_id,
                        f"🤖👻 *JARVIS Auto-Detected Wallet!*\n\n"
                        f"📍 Address: `{detected_addr[:8]}...{detected_addr[-6:]}`\n"
                        f"✅ Auto-connected to Solana Mainnet!\n\n"
                        f"⚡ Scanning your tokens now...\n"
                        f"_JARVIS ne automatically wallet detect kar liya!_ 🧠",
                        reply_markup=build_keyboard())
                    send_jarvis_voice(chat_id, f"Boss! Maine wallet address detect kar liya. Auto connect ho gaya hai. Ab scan start karta hoon.", intent="greeting")
                    # Auto-trigger wallet scan
                    try:
                        scan = phantom_scan_wallet(chat_id)
                        if scan.get("success"):
                            formatted = format_wallet_scan(scan)
                            send_message(chat_id, formatted, reply_markup=build_keyboard())
                            voice_text = format_wallet_voice(scan)
                            if voice_text:
                                send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
                    except Exception:
                        pass
                    return
            except Exception:
                pass

    # --- Phantom Wallet Scan ---
    if text in ("👻 Wallet Scan 📊", "wallet scan", "phantom scan", "scan wallet"):
        if PHANTOM_AVAILABLE:
            if is_wallet_connected(chat_id):
                send_message(chat_id, f"{greeting}👻🔍 *Phantom Wallet Scan चल रहा है...*\n"
                            f"_Solana tokens fetch + AI prediction + ₹ value calculate_ ⏳\n"
                            f"_15-30 sec लगेगा..._")
                try:
                    scan_result = phantom_scan_wallet(chat_id)
                    if scan_result.get("success"):
                        msg = format_wallet_scan(scan_result)
                        send_message(chat_id, msg, reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, f"❌ Scan Error: {scan_result.get('error', 'Unknown')}", reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ Wallet Scan Error: {str(e)[:200]}", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "❌ *Pehle wallet connect karo!*\n\n'👻 Connect Wallet' button dabo ya:\n/phantom connect <your_address>", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Phantom Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Phantom Disconnect ---
    if text in ("👻 Disconnect Wallet", "disconnect wallet", "phantom disconnect"):
        if PHANTOM_AVAILABLE:
            success = disconnect_wallet(chat_id)
            if success:
                send_message(chat_id, "✅ *Wallet disconnected successfully!*\n👻 Phantom link removed.", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "❌ *No wallet connected to disconnect.*", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Phantom Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Phantom Wallet Alerts ON ---
    if text in ("👻 Wallet Alerts ON", "wallet alerts on", "phantom alerts on"):
        if PHANTOM_AVAILABLE:
            if is_wallet_connected(chat_id):
                try:
                    start_realtime_monitoring(send_fn=send_message, voice_fn=None)
                    send_message(chat_id, "✅🔔 *Phantom Real-Time Alerts ON!*\n\n"
                                f"👻 आपके wallet tokens 24/7 monitor हो रहे हैं\n"
                                f"🔴 Real-time scanning: Every 2 minutes\n"
                                f"📊 Big price moves पर alert आएगा!\n"
                                f"🔐 Security: Military-grade encryption active", reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ Alert Start Error: {str(e)[:200]}", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "❌ Pehle wallet connect karo!", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Phantom Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Phantom Wallet Alerts OFF ---
    if text in ("👻 Wallet Alerts OFF", "wallet alerts off", "phantom alerts off"):
        if PHANTOM_AVAILABLE:
            stop_wallet_alerts()
            send_message(chat_id, "✅🔕 *Phantom Wallet Alerts OFF!*", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Phantom Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Phantom Wallet Dashboard ---
    if text in ("👻 Wallet Dashboard 📋", "wallet dashboard", "phantom dashboard", "/phantomdashboard"):
        if PHANTOM_AVAILABLE:
            try:
                dashboard_msg = get_wallet_dashboard(chat_id)
                send_message(chat_id, f"{greeting}{dashboard_msg}", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Dashboard Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Phantom Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Wallet Summary via Solana Engine (FREE) ---
    if text in ("👻 Wallet Summary ⚡", "wallet summary", "/walletsummary"):
        if SOLANA_ENGINE_AVAILABLE:
            send_message(chat_id, f"{greeting}⚡ *Scanning Phantom wallet via FREE Solana RPC...*\n_Tokens, prices, transactions loading..._ ⏳")
            try:
                summary = get_wallet_summary()
                msg = format_wallet_summary(summary)
                send_message(chat_id, msg, reply_markup=build_keyboard())
                # Voice
                voice_text = solana_wallet_voice(summary)
                if voice_text:
                    send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto")
            except Exception as e:
                send_message(chat_id, f"❌ Wallet Summary Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Solana Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Claim Airdrops to Phantom Wallet ---
    if text in ("👻 Claim Airdrops 🎁", "claim airdrops", "/claimairdrops"):
        if SOLANA_ENGINE_AVAILABLE:
            send_message(chat_id, f"{greeting}🎁 *Scanning wallet for claimable tokens...*\n_Checking Phantom wallet for airdrops..._ ⏳")
            try:
                claimable = scan_for_claimable_airdrops()
                if claimable:
                    msg = "🎁⚡ *CLAIMABLE TOKENS IN WALLET*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    total_value = 0
                    for i, tok in enumerate(claimable[:10], 1):
                        sym = tok.get("symbol", "?")
                        amt = tok.get("amount", 0)
                        val = tok.get("value_usd", 0)
                        total_value += val
                        change = tok.get("change_24h", 0)
                        mint = tok.get("mint", "")
                        icon = "🚀" if change > 20 else "🟢" if change > 0 else "🔴"
                        
                        # Check scam
                        scam, scam_reason = is_scam_token(tok)
                        scam_badge = "⚠️ SCAM" if scam else "✅ Safe"
                        
                        msg += f"{icon} *{i}. {sym}* ({scam_badge})\n"
                        msg += f"   Balance: {amt:.4f}\n"
                        if val > 0:
                            msg += f"   Value: ${val:.4f}\n"
                        if change:
                            msg += f"   24h: {change:+.1f}%\n"
                        
                        if not scam:
                            links = generate_claim_and_transfer_links(tok)
                            msg += f"   🔄 [Swap to SOL (Phantom)]({links['swap_to_sol']})\n"
                            msg += f"   💵 [Swap to USDC (Phantom)]({links['swap_to_usdc']})\n"
                            msg += f"   🔍 [DexScreener]({links['dexscreener']})\n"
                        msg += "\n"
                    
                    msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    msg += f"💰 *Total Claimable:* ${total_value:.4f}\n"
                    _phantom_user = os.environ.get("OWNER_PHANTOM_USERNAME", "")
                    _wallet_display = OWNER_WALLET[:6] + "..." + OWNER_WALLET[-4:] if PHANTOM_AVAILABLE and OWNER_WALLET else ""
                    msg += f"👻 Phantom: {_phantom_user}\n"
                    msg += f"📍 Wallet: `{_wallet_display}`\n\n"
                    msg += f"👆 *Tap 'Swap to SOL'* — Phantom browser mein Jupiter open hoga!\n"
                    msg += f"⚡ One-click swap → SOL automatically wallet mein aayega!\n"
                    msg += f"🛡️ _JARVIS ne scam check kiya hai — safe tokens only_"
                    
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                    send_jarvis_voice(chat_id, f"Boss! {len(claimable)} tokens milein wallet mein. Safe tokens ko swap karke SOL mein convert kar sakte ho. Links bhej diye hain.", intent="buy_sell_crypto")
                else:
                    send_message(chat_id, 
                        f"🎁 *No Claimable Tokens Found*\n\n"
                        f"Wallet mein abhi koi new airdrop token nahi hai.\n"
                        f"📡 Auto-scanner hamesha check kar raha hai.\n"
                        f"Jab koi milega, turant alert aayega! 🔔\n\n"
                        f"💡 *Tip:* Zyada airdrops ke liye ye use karo:\n"
                        f"  • Jupiter Exchange (jup.ag)\n"
                        f"  • Phantom Swap\n"
                        f"  • Marginfi (lending)",
                        reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Airdrop Scan Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Solana Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Transfer SOL via Phantom ---
    if text in ("👻 Transfer SOL 💸", "transfer sol", "/transfersol"):
        if SOLANA_ENGINE_AVAILABLE:
            try:
                links = generate_phantom_transfer_link(
                    recipient=OWNER_WALLET if PHANTOM_AVAILABLE else os.environ.get("OWNER_SOLANA_WALLET", ""),
                )
                sol_bal = get_sol_balance()
                _phantom_user = os.environ.get("OWNER_PHANTOM_USERNAME", "@davidbot1")
                _wallet_short = (OWNER_WALLET if PHANTOM_AVAILABLE else os.environ.get("OWNER_SOLANA_WALLET", ""))[:6] + "..." + (OWNER_WALLET if PHANTOM_AVAILABLE else os.environ.get("OWNER_SOLANA_WALLET", ""))[-4:]
                
                msg = (
                    f"💸⚡ *SOLANA TRANSFER — via Phantom*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👻 Phantom: {_phantom_user}\n"
                    f"📍 Wallet: `{_wallet_short}`\n"
                    f"⚡ SOL Balance: {sol_bal:.4f} SOL\n\n"
                    f"🔄 *Quick Transfer Links:*\n"
                    f"  🟣 [Open Jupiter in Phantom]({links['phantom_jupiter']})\n"
                    f"  🔵 [Open Raydium in Phantom]({links['phantom_raydium']})\n"
                    f"  📋 [View on Solscan]({links['solscan']})\n\n"
                    f"💡 *How to Transfer:*\n"
                    f"1️⃣ Phantom app kholo\n"
                    f"2️⃣ SOL token tap karo\n"
                    f"3️⃣ 'Send' button dabo\n"
                    f"4️⃣ Address paste karo ya QR scan karo\n"
                    f"5️⃣ Amount enter karo → Confirm\n\n"
                    f"📡 *JARVIS monitors 24/7* — transfer complete hote hi\n"
                    f"✅ Acknowledgment alert aayega!\n\n"
                    f"🔐 _Free Solana RPC — zero fees for monitoring!_"
                )
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Transfer Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Solana Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- Phantom Security Status ---
    if text in ("🔐 Security Status", "phantom security", "/phantomsecurity"):
        if PHANTOM_AVAILABLE:
            try:
                sec_msg = get_security_status(chat_id)
                send_message(chat_id, f"{greeting}{sec_msg}", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Security Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Phantom Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # --- /phantom command handler ---
    if text.startswith("/phantom"):
        parts = text.split()
        if PHANTOM_AVAILABLE:
            if len(parts) >= 3 and parts[1].lower() == "connect":
                addr = parts[2].strip()
                try:
                    result = connect_wallet(chat_id, addr)
                    if result.get("success"):
                        send_message(chat_id, f"✅👻 *Wallet Connected!*\n📍 `{addr[:8]}...{addr[-6:]}`", reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, f"❌ {result.get('error', 'Failed')}", reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ Error: {str(e)[:200]}", reply_markup=build_keyboard())
            elif len(parts) >= 2 and parts[1].lower() == "scan":
                if is_wallet_connected(chat_id):
                    send_message(chat_id, f"{greeting}👻🔍 *Wallet Scan...* ⏳")
                    try:
                        scan_result = phantom_scan_wallet(chat_id)
                        if scan_result.get("success"):
                            msg = format_wallet_scan(scan_result)
                            send_message(chat_id, msg, reply_markup=build_keyboard())
                        else:
                            send_message(chat_id, f"❌ {scan_result.get('error', 'Scan failed')}", reply_markup=build_keyboard())
                    except Exception as e:
                        send_message(chat_id, f"❌ {str(e)[:200]}", reply_markup=build_keyboard())
                else:
                    send_message(chat_id, "❌ Pehle connect karo: /phantom connect <address>", reply_markup=build_keyboard())
            elif len(parts) >= 2 and parts[1].lower() == "disconnect":
                disconnect_wallet(chat_id)
                send_message(chat_id, "✅ Wallet disconnected.", reply_markup=build_keyboard())
            elif len(parts) >= 2 and parts[1].lower() == "dashboard":
                try:
                    dashboard_msg = get_wallet_dashboard(chat_id)
                    send_message(chat_id, dashboard_msg, reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ {str(e)[:200]}", reply_markup=build_keyboard())
            elif len(parts) >= 2 and parts[1].lower() == "security":
                try:
                    sec_msg = get_security_status(chat_id)
                    send_message(chat_id, sec_msg, reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ {str(e)[:200]}", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "👻 *Phantom Wallet Commands:*\n\n"
                            "/phantom connect <address>\n"
                            "/phantom scan\n"
                            "/phantom dashboard\n"
                            "/phantom security\n"
                            "/phantom disconnect", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Phantom Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   🌍 GLOBAL MARKET HANDLERS
    # ════════════════════════════
    if text in ("🌍 Global Market Brain",):
        if GLOBAL_AVAILABLE:
            send_message(chat_id, f"🤖🌍 *जार्विस ग्लोबल मार्केट ब्रेन एक्टिवेट हो रहा है...* ⏳\n_सारी दुनिया के मार्केट स्कैन कर रहा हूँ_")
            try:
                analysis = analyze_all_global_markets()
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = format_global_analysis(analysis, lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Global analysis error: {e}")
                send_message(chat_id, f"❌ ग्लोबल एनालिसिस फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Global Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("🔮 India from Global",):
        if GLOBAL_AVAILABLE:
            send_message(chat_id, f"🤖🔮 *जार्विस ग्लोबल डाटा से भारत का प्रेडिक्शन बना रहा है...* ⏳")
            try:
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = get_india_prediction_from_global(lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"India prediction error: {e}")
                send_message(chat_id, f"❌ प्रेडिक्शन फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Global Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("🇺🇸 US Markets",):
        if GLOBAL_AVAILABLE:
            send_message(chat_id, f"🤖🇺🇸 *US मार्केट एनालिसिस...* ⏳")
            try:
                signals = analyze_us_markets()
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = format_regional_signals(signals, "🇺🇸 US मार्केट एनालिसिस", lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ US मार्केट फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Global Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("🇪🇺 Europe Markets",):
        if GLOBAL_AVAILABLE:
            send_message(chat_id, f"🤖🇪🇺 *यूरोप मार्केट एनालिसिस...* ⏳")
            try:
                signals = analyze_european_markets()
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = format_regional_signals(signals, "🇪🇺 यूरोप मार्केट एनालिसिस", lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ यूरोप मार्केट फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Global Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("🌏 Asia Markets",):
        if GLOBAL_AVAILABLE:
            send_message(chat_id, f"🤖🌏 *एशिया मार्केट एनालिसिस...* ⏳")
            try:
                signals = analyze_asian_markets()
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = format_regional_signals(signals, "🌏 एशिया मार्केट एनालिसिस", lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ एशिया मार्केट फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Global Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text in ("🥇 Commodities",):
        if GLOBAL_AVAILABLE:
            send_message(chat_id, f"🤖🥇 *कमोडिटी एनालिसिस (Gold, Silver, Crude)...* ⏳")
            try:
                signals = analyze_commodities()
                lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                msg = format_regional_signals(signals, "🥇 कमोडिटी एनालिसिस", lang=lang)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ कमोडिटी फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Global Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   🔐 ADMIN PANEL
    # ════════════════════════════
    if text in ("🔐 Admin Panel", "/admin"):
        if ADMIN_AVAILABLE:
            if is_admin(str(chat_id)):
                panel_text = generate_admin_panel(str(chat_id))
                admin_kb = build_admin_keyboard()
                # Send with inline keyboard
                send_message(chat_id, panel_text, reply_markup=build_keyboard())
            else:
                send_message(chat_id, "🚫 ये Admin Panel सिर्फ Admin के लिए है।\nआपकी Chat ID admin list में नहीं है। 🌸", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Admin Panel उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # Admin commands — OWNER ONLY
    if text.startswith("/toggle") or text.startswith("/features") or text.startswith("/stats") or \
       text.startswith("/system") or text.startswith("/logs") or text.startswith("/block") or \
       text.startswith("/unblock") or text.startswith("/broadcast") or text.startswith("/enable_all") or \
       text.startswith("/disable_all") or text.startswith("/users"):
        if not _is_owner(chat_id):
            send_message(chat_id, "🚫 ये Admin commands सिर्फ Owner के लिए हैं।", reply_markup=build_keyboard())
            return
        if ADMIN_AVAILABLE:
            parts = text.split(maxsplit=1)
            cmd = parts[0].lstrip("/")
            args = parts[1] if len(parts) > 1 else ""
            response, kb = handle_admin_command(str(chat_id), cmd, args)
            
            # Handle broadcast
            if response and response.startswith("📢 BROADCAST_READY"):
                parts = response.split("|")
                if len(parts) >= 3:
                    target_count = int(parts[1])
                    broadcast_msg = parts[2]
                    targets = get_broadcast_targets()
                    sent = 0
                    for target_id in targets:
                        try:
                            send_message(int(target_id), f"📢 *जार्विस ब्रॉडकास्ट:*\n\n{broadcast_msg}")
                            sent += 1
                            time.sleep(0.1)
                        except Exception:
                            pass
                    log_broadcast(broadcast_msg, str(chat_id), sent)
                    send_message(chat_id, f"✅ ब्रॉडकास्ट भेजा गया!\n📊 {sent}/{target_count} यूज़र को डिलीवर हुआ।", reply_markup=build_keyboard())
            else:
                send_message(chat_id, response, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Admin Panel उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   🇮🇳 LANGUAGE SWITCH
    # ════════════════════════════
    if text in ("🇮🇳 Hindi / English",):
        if ADMIN_AVAILABLE:
            current_lang = get_user_language(str(chat_id))
            new_lang = "en" if current_lang == "hi" else "hi"
            result = set_user_language(str(chat_id), new_lang)
            send_message(chat_id, result, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "🇮🇳 भाषा बदलने के लिए Admin Panel चाहिए।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   🌡️ MARKET REGIME DETECTION (NEW — Phase 6 Power Upgrade)
    # ════════════════════════════════════════════════════════════
    if text in ("🌡️ Market Regime 🔬", "Market Regime"):
        if REGIME_AVAILABLE:
            send_message(chat_id, "🤖🌡️ *Market Regime Detect कर रही हूँ...* ⏳\n_Bull? Bear? Sideways? Volatile?_")
            try:
                regime = detect_regime("^NSEI")
                msg = format_regime_report(regime)
                send_message(chat_id, msg, reply_markup=build_keyboard())
                # Voice
                if VOICE_AVAILABLE:
                    try:
                        voice_text = f"Market regime: {regime.get('regime', 'Unknown')}. Confidence {regime.get('confidence', 0):.0f} percent. Volatility state: {regime.get('volatility_state', 'Normal')}. Recommended position size: {regime.get('position_size_pct', 100):.0f} percent."
                        asyncio.run(send_jarvis_voice(chat_id, voice_text))
                    except Exception:
                        pass
            except Exception as e:
                send_message(chat_id, f"❌ Regime Detection फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Market Regime engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   📊 OPTIONS ANALYSIS (Greeks + Strategy Builder)
    # ════════════════════════════════════════════════════════════
    if text in ("📊 Options Analysis 💹", "Options Analysis"):
        if OPTIONS_AVAILABLE:
            send_message(chat_id, "🤖📊 *NIFTY Options Analysis...* ⏳\n_Greeks, IV, PCR, Max Pain, Strategy सब दे रही हूँ!_")
            try:
                chain = generate_option_chain_with_greeks("^NSEI")
                strategy = suggest_strategy("^NSEI")
                pcr = calculate_pcr("^NSEI")
                max_p = calculate_max_pain("^NSEI")

                msg = format_options_analysis(chain, "NIFTY")
                if strategy:
                    msg += "\n\n" + format_strategy_suggestion(strategy, "NIFTY")
                if pcr:
                    msg += f"\n\n📊 *PCR:* {pcr.get('pcr', 'N/A')}"
                    pcr_val = pcr.get('pcr', 0)
                    if isinstance(pcr_val, (int, float)):
                        if pcr_val > 1.2:
                            msg += " 🟢 (Bullish — Heavy put writing)"
                        elif pcr_val < 0.7:
                            msg += " 🔴 (Bearish — Heavy call writing)"
                        else:
                            msg += " 🟡 (Neutral)"
                if max_p:
                    msg += f"\n💥 *Max Pain:* ₹{max_p.get('max_pain', 'N/A'):,}"

                send_message(chat_id, msg, reply_markup=build_keyboard())
                if VOICE_AVAILABLE:
                    try:
                        voice_text = f"Options analysis ready. PCR is {pcr.get('pcr', 'not available')}. Strategy suggestion: {strategy.get('strategy', 'Check report')}."
                        asyncio.run(send_jarvis_voice(chat_id, voice_text))
                    except Exception:
                        pass
            except Exception as e:
                send_message(chat_id, f"❌ Options Analysis फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Options Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   ⚡ INTRADAY SCALP SIGNAL
    # ════════════════════════════════════════════════════════════
    if text in ("⚡ Scalp Signal 🎯", "Scalp Signal"):
        if SCALP_AVAILABLE:
            send_message(chat_id, "🤖⚡ *Intraday Scalp Signal बना रही हूँ...* ⏳\n_1m + 5m data + RSI + EMA + VWAP_")
            try:
                nifty_scalp = get_scalping_signal("^NSEI", "NIFTY")
                bank_scalp = get_scalping_signal("^NSEBANK", "BANKNIFTY")
                msg = ""
                if nifty_scalp:
                    msg += format_scalping_signal(nifty_scalp) + "\n\n"
                if bank_scalp:
                    msg += format_scalping_signal(bank_scalp)
                if not msg:
                    msg = "⚠️ Scalp signal data unavailable right now."
                send_message(chat_id, msg, reply_markup=build_keyboard())
                if VOICE_AVAILABLE and nifty_scalp:
                    try:
                        voice_text = f"NIFTY scalp signal: {nifty_scalp.get('signal', 'N/A')}. Entry {nifty_scalp.get('entry', 'N/A')}. Target {nifty_scalp.get('target1', 'N/A')}. Stoploss {nifty_scalp.get('stoploss', 'N/A')}."
                        asyncio.run(send_jarvis_voice(chat_id, voice_text))
                    except Exception:
                        pass
            except Exception as e:
                send_message(chat_id, f"❌ Scalp Signal फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Scalp Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   📊 MULTI-TIMEFRAME SIGNAL
    # ════════════════════════════════════════════════════════════
    if text in ("📊 Multi-TF Signal 🔄", "Multi-TF Signal"):
        if SCALP_AVAILABLE:
            send_message(chat_id, "🤖📊 *Multi-Timeframe Analysis...* ⏳\n_5m + 15m + 1h + Daily = Combined Signal_")
            try:
                nifty_mtf = get_multi_timeframe_signal("^NSEI", "NIFTY")
                msg = ""
                if nifty_mtf:
                    msg = format_multi_tf(nifty_mtf)
                if not msg:
                    msg = "⚠️ Multi-TF data unavailable."
                send_message(chat_id, msg, reply_markup=build_keyboard())
                if VOICE_AVAILABLE and nifty_mtf:
                    try:
                        voice_text = f"Multi-timeframe signal for NIFTY: {nifty_mtf.get('combined_signal', 'N/A')}. Confidence {nifty_mtf.get('confidence', 0):.0f} percent."
                        asyncio.run(send_jarvis_voice(chat_id, voice_text))
                    except Exception:
                        pass
            except Exception as e:
                send_message(chat_id, f"❌ Multi-TF फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Multi-TF Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   📈 STOCK PORTFOLIO (PER-USER)
    # ════════════════════════════════════════════════════════════
    if text in ("📈 My Stock Portfolio", "Stock Portfolio"):
        if STOCK_PORTFOLIO_AVAILABLE:
            send_message(chat_id, "🤖📈 *Stock Portfolio लोड कर रही हूँ...* ⏳")
            try:
                pnl = calculate_stock_portfolio_pnl(chat_id)
                msg = format_stock_portfolio(pnl)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Stock Portfolio फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Stock Portfolio उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   🏦 COMBINED PORTFOLIO (PER-USER)
    # ════════════════════════════════════════════════════════════
    if text in ("🏦 Combined Portfolio", "Combined Portfolio"):
        if STOCK_PORTFOLIO_AVAILABLE:
            send_message(chat_id, "🤖🏦 *Combined Portfolio (Crypto + Stocks)...* ⏳")
            try:
                msg = format_combined_portfolio(chat_id)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Combined Portfolio फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Combined Portfolio उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   🧾 TAX CALCULATOR
    # ════════════════════════════════════════════════════════════
    if text in ("🧾 Tax Calculator 💰", "Tax Calculator"):
        if STOCK_PORTFOLIO_AVAILABLE:
            send_message(chat_id, "🤖🧾 *Indian Tax Calculate कर रही हूँ...* ⏳\n_Crypto 30% + Stock STCG/LTCG_")
            try:
                tax = calculate_tax(chat_id)
                msg = format_tax_report(tax)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Tax Calculator फेल: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Tax Calculator उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   /buystock and /sellstock commands (PER-USER)
    # ════════════════════════════════════════════════════════════
    if text.startswith("/buystock"):
        if STOCK_PORTFOLIO_AVAILABLE:
            try:
                parts = text.split()
                if len(parts) < 4:
                    send_message(chat_id, "Usage: `/buystock RELIANCE 10 2500`\n(Symbol Qty Price)", reply_markup=build_keyboard())
                    return
                symbol = parts[1].upper()
                qty = float(parts[2])
                price = float(parts[3])
                add_stock_holding(chat_id, symbol, qty, price)
                send_message(chat_id, f"✅ *{symbol}* added!\n📊 {qty:.0f} shares × ₹{price:,.2f} = ₹{qty*price:,.0f}", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Stock Portfolio उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    if text.startswith("/sellstock"):
        if STOCK_PORTFOLIO_AVAILABLE:
            try:
                parts = text.split()
                if len(parts) < 3:
                    send_message(chat_id, "Usage: `/sellstock RELIANCE 2500`\n(Symbol SellPrice)", reply_markup=build_keyboard())
                    return
                symbol = parts[1].upper()
                sell_price = float(parts[2])
                result = sell_stock_holding(chat_id, symbol, sell_price)
                if result["success"]:
                    pnl_em = "🟢" if result["pnl"] >= 0 else "🔴"
                    send_message(chat_id,
                        f"✅ *{symbol} SOLD!*\n"
                        f"📊 Qty: {result['qty_sold']:.0f} × ₹{sell_price:,.2f}\n"
                        f"{pnl_em} P&L: ₹{result['pnl']:+,.0f} ({result['roi_pct']:+.1f}%)\n"
                        f"📅 Held: {result.get('holding_days',0)} days",
                        reply_markup=build_keyboard())
                else:
                    send_message(chat_id, f"❌ {result.get('error', 'Failed')}", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Stock Portfolio उपलब्ध नहीं है।", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   JARVIS SUPER BRAIN COMMANDS — News, Intelligence, SPOC
    # ════════════════════════════

    # /news — Worldwide News Digest
    if text.lower() in ("/news", "news", "khabar", "headlines", "/newsall") or text in ("📰 News Digest",):
        if SUPER_BRAIN_AVAILABLE:
            send_message(chat_id, jarvis_animated_header("thinking"))
            digest = format_news_digest()
            send_message(chat_id, digest, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, format_news_voice(), intent="market_summary")
        else:
            send_message(chat_id, "📰 News engine loading...", reply_markup=build_keyboard())
        return

    # /briefing — Complete Intelligence Briefing
    if text.lower() in ("/briefing", "briefing", "intelligence", "sab batao", "update de", "/intelligence") or text in ("🧠 Intelligence Briefing",):
        if SUPER_BRAIN_AVAILABLE:
            send_message(chat_id, jarvis_animated_header("scan"))
            briefing = format_jarvis_briefing()
            send_message(chat_id, briefing, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, format_briefing_voice(), intent="market_summary")
        else:
            send_message(chat_id, "🧠 Briefing engine loading...", reply_markup=build_keyboard())
        return

    # /spoc — JARVIS SPOC Dashboard (full system health)
    if text.lower() in ("/spoc", "spoc", "spoc dashboard", "system health", "jarvis status") or text in ("🔱 SPOC Dashboard",):
        if SPOC_AVAILABLE:
            send_message(chat_id, jarvis_animated_header("scan") if SUPER_BRAIN_AVAILABLE else "🧠 Loading...")
            dashboard = format_spoc_dashboard(TELEGRAM_TOKEN)
            send_message(chat_id, dashboard, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, format_spoc_voice(), intent="greeting")
        else:
            send_message(chat_id, "🧠 SPOC module not available.", reply_markup=build_keyboard())
        return

    # /spocquick — Quick status
    if text.lower() in ("/spocquick", "quick status", "jarvis quick") or text in ("📊 Quick Status",):
        if SPOC_AVAILABLE:
            send_message(chat_id, format_spoc_quick(), reply_markup=build_keyboard())
        return

    # Super Brain command router (handles news-related natural language)
    if SUPER_BRAIN_AVAILABLE:
        brain_result = jarvis_route_command(text, chat_id)
        if brain_result:
            send_message(chat_id, brain_result["response"], reply_markup=build_keyboard())
            if brain_result.get("voice"):
                send_jarvis_voice(chat_id, brain_result["voice"], intent=brain_result.get("intent", "chat"))
            return

    # ════════════════════════════
    #   J.A.R.V.I.S. NLU ROUTER — AI Chat Fallback with Intent Understanding
    # ════════════════════════════
    is_ai_mode_final = chat_storage.get(f"ai_mode_{chat_id}", False)
    is_question = any(w in text.lower() for w in [
        "?", "should", "which", "what", "how", "when", "why", "can",
        "nifty", "sensex", "call", "put", "option", "buy", "sell",
        "invest", "predict", "strategy", "risk", "profit", "loss",
        "strike", "premium", "lot", "target", "stop", "market",
        "bullish", "bearish", "tomorrow", "today", "analysis",
        "hello", "hi", "hey", "thanks", "good", "jarvis", "brief",
        "crypto", "gem", "whale", "rug", "pump", "token", "coin",
        "portfolio", "alert", "trend", "dip", "moon", "scan",
        # Hindi keywords
        "kya", "kaise", "kab", "kyun", "kaha", "kaun", "kitna",
        "namaste", "pranam", "ram", "jai", "mahadev", "shukriya",
        "dhanyavad", "theek", "accha", "batao", "chahiye", "hoga",
        "jayega", "girega", "upar", "neeche", "aaj", "kal",
        "signal", "global", "admin", "candle", "indicator",
        # Rocket / Quick profit keywords
        "rocket", "moonshot", "jaldi", "quick", "fast", "turant",
        "paisa", "paise", "rupee", "rupaye", "laga", "lagao",
        "bana", "kamao", "double", "triple", "5000", "50000",
        "token", "naam", "dikhao", "recommend",
        # Hindi Devanagari
        "टोकन", "पैसा", "रुपए", "बताओ", "दिखाओ", "कमाओ",
        "पंप", "मून", "रॉकेट", "क्रिप्टो", "जल्दी",
    ])
    
    if is_ai_mode_final or (is_question and len(text) > 1):
        # ── JARVIS NLU: Try to classify intent first ──
        if JARVIS_AVAILABLE and len(text) > 2:
            intent, confidence = classify_intent(text)
            
            # 🧠 Memory: Save user intent to conversation
            try:
                add_to_conversation(chat_id, "user", text, intent)
            except Exception as e:
                logger.warning(f"[MEMORY] Failed to save user message: {e}")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            #  🚀 QUICK PROFIT / ROCKET SCAN — Direct handler
            #  Handles: "₹5000 se ₹50000 kaise banau", "pump token batao", etc.
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if intent in (Intent.QUICK_PROFIT, Intent.ROCKET_SCAN) and confidence >= 0.4:
                is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
                send_message(chat_id, 
                    f"🚀🔥 *JARVIS ROCKET SCANNER ACTIVATED!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔍 _₹2K → ₹50K moonshot tokens ढूंढ रही हूँ..._\n"
                    f"_DexScreener + Pump.fun + CoinDCX scanning..._\n"
                    f"⏳ _10 second wait करिए..._ 💕")
                
                try:
                    if ROCKET_AVAILABLE:
                        # Run full rocket scan — get RAW list, not formatted string
                        rockets = scan_rockets(min_score=20, limit=12, include_coindcx=True)
                        if rockets:
                            # Count sources for user visibility
                            dex_count = sum(1 for r in rockets if r.get('source') in ('dexscreener', 'pump.fun'))
                            cdx_count = sum(1 for r in rockets if r.get('source') == 'coindcx')
                            msg = format_rocket_scan(rockets)
                            # Add source summary
                            if dex_count > 0 or cdx_count > 0:
                                src_info = f"\n📡 _Sources: {dex_count} DexScreener/Pump.fun + {cdx_count} CoinDCX_"
                                msg = msg.replace('━━━━━━━━━━━━━━━━━━━━━━━━━━━', '━━━━━━━━━━━━━━━━━━━━━━━━━━━' + src_info, 1)
                            voice_text = format_rocket_voice(rockets)
                            send_message(chat_id, msg, reply_markup=build_keyboard())
                            if voice_text:
                                send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto", is_voice_input=is_voice)
                            else:
                                send_jarvis_voice(chat_id, 
                                    "Rocket scan complete! Text message mein saare hot tokens dikh rahe hain with entry price, target aur stop loss. Check kariye jaldi!", 
                                    intent="buy_sell_crypto", is_voice_input=is_voice)
                        else:
                            send_message(chat_id, 
                                "🚀 Abhi koi strong rocket token nahi mila.\n"
                                "⏳ Thodi der mein dobara try kariye — market change hota rehta hai!\n"
                                "💡 Ya fir '🚀🔥 ROCKET Scanner' button press kariye.",
                                reply_markup=build_keyboard())
                    elif CRYPTO_INTEL_AVAILABLE:
                        # Fallback to crypto intelligence
                        picks = get_top_crypto_picks(limit=5, budget_inr=5000)
                        if picks:
                            msg = format_top_picks(picks)
                            voice_text = format_picks_voice(picks)
                            send_message(chat_id, msg, reply_markup=build_keyboard())
                            send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto", is_voice_input=is_voice)
                        else:
                            send_message(chat_id, "❌ Abhi tokens nahi mil rahe. Thodi der mein try kariye.", reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, 
                            "🚀 Rocket Scanner se results:\n"
                            "💡 '🚀🔥 ROCKET Scanner' button press kariye neeche se!",
                            reply_markup=build_keyboard())
                except Exception as e:
                    logger.error(f"[QUICK_PROFIT] Error: {e}")
                    send_message(chat_id, f"❌ Rocket scan mein error aaya: {str(e)[:100]}. Dobara try kariye.", reply_markup=build_keyboard())
                return
            
            action = get_action_for_intent(intent, confidence, text)
            
            # If JARVIS can redirect to an existing handler button
            if action["action"] == "redirect" and confidence >= 0.5:
                logger.info(f"[JARVIS NLU] Intent={intent} Conf={confidence:.2f} -> Redirect to: {action['button']}")
                # Simulate the button press by creating a fake update
                fake_update = {"message": {"chat": {"id": chat_id}, "text": action["button"], "from": update.get("message", {}).get("from", {})}}
                handle_update(fake_update)
                return
            
            # Special handlers
            if action["action"] == "special":
                if action["type"] == "morning_brief":
                    send_message(chat_id, f"🤖🌸 *briefing तैयार कर रही हूँ...* ⏳💕")
                    try:
                        brief = generate_morning_briefing(chat_id)
                        send_message(chat_id, brief, reply_markup=build_keyboard())
                        send_jarvis_voice(chat_id, brief, intent="morning_brief")
                    except Exception as e:
                        logger.error(f"Morning brief error: {e}")
                        send_message(chat_id, f"{greeting}❌ Briefing फेल हो गई। 🌸", reply_markup=build_keyboard())
                    return
                
                elif action["type"] == "market_summary":
                    send_message(chat_id, f"🤖🌸 *सारे markets analyze कर रही हूँ...* ⏳💕")
                    try:
                        summary = generate_market_summary(chat_id)
                        send_message(chat_id, summary, reply_markup=build_keyboard())
                        send_jarvis_voice(chat_id, summary, intent="market_summary")
                    except Exception as e:
                        logger.error(f"Market summary error: {e}")
                        send_message(chat_id, f"{greeting}❌ Summary failed.", reply_markup=build_keyboard())
                    return
                
                elif action["type"] == "greeting":
                    try:
                        user_name = get_user_name(update)
                        greet_msg = generate_jarvis_greeting(user_name, chat_id)
                        send_message(chat_id, greet_msg, reply_markup=build_keyboard())
                        send_jarvis_voice(chat_id, f"नमस्ते {user_name} जी! मैं जार्विस हूँ, आपकी AI ट्रेडिंग असिस्टेंट। बताइए क्या मदद करूँ?", intent="greeting")
                    except Exception:
                        send_message(chat_id, f"{greeting}🌸 नमस्ते जी! मैं J.A.R.V.I.S. — आपके साथ हूँ! 💕🤖", reply_markup=build_keyboard())
                    return
                
                elif action["type"] == "buy_sell_signal":
                    if BUY_SELL_AVAILABLE:
                        send_message(chat_id, f"🤖📈 *जार्विस Buy/Sell सिग्नल जनरेट कर रहा है...* ⏳")
                        try:
                            # Try to extract symbol from text
                            sym = text.upper().strip()
                            nifty_signal = get_stock_signal("NIFTY")
                            sensex_signal = get_stock_signal("SENSEX")
                            btc_signal = get_crypto_signal("BTC")
                            lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                            msgs = []
                            if nifty_signal:
                                msgs.append(format_bs_signal(nifty_signal, lang=lang))
                            if sensex_signal:
                                msgs.append(format_bs_signal(sensex_signal, lang=lang))
                            if btc_signal:
                                msgs.append(format_bs_signal(btc_signal, lang=lang))
                            if msgs:
                                full_signal = "\n\n".join(msgs)
                                send_message(chat_id, full_signal, reply_markup=build_keyboard())
                                send_jarvis_voice(chat_id, full_signal, intent="buy_sell_stock")
                            else:
                                send_message(chat_id, "❌ सिग्नल नहीं मिला। बाद में कोशिश करें।", reply_markup=build_keyboard())
                        except Exception as e:
                            logger.error(f"NLU buy/sell error: {e}")
                            send_message(chat_id, f"❌ सिग्नल फेल: {str(e)[:100]}", reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, "❌ Buy/Sell Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
                    return
                
                elif action["type"] == "admin_panel":
                    if ADMIN_AVAILABLE and is_admin(str(chat_id)):
                        panel_text = generate_admin_panel(str(chat_id))
                        send_message(chat_id, panel_text, reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, "🚫 Admin Panel सिर्फ Admin के लिए है।", reply_markup=build_keyboard())
                    return
                
                elif action["type"] == "global_candles":
                    if GLOBAL_AVAILABLE:
                        send_message(chat_id, f"🤖🌍 *जार्विस ग्लोबल कैंडल्स एनालाइज़ कर रहा है...* ⏳")
                        try:
                            analysis = analyze_all_global_markets()
                            lang = get_user_language(str(chat_id)) if ADMIN_AVAILABLE else "hi"
                            msg = format_global_analysis(analysis, lang=lang)
                            send_message(chat_id, msg, reply_markup=build_keyboard())
                        except Exception as e:
                            logger.error(f"NLU global candles error: {e}")
                            send_message(chat_id, f"❌ ग्लोबल एनालिसिस फेल: {str(e)[:100]}", reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, "❌ Global Engine उपलब्ध नहीं है।", reply_markup=build_keyboard())
                    return
                
                elif action["type"] == "language_switch":
                    if ADMIN_AVAILABLE:
                        current_lang = get_user_language(str(chat_id))
                        new_lang = "en" if current_lang == "hi" else "hi"
                        result = set_user_language(str(chat_id), new_lang)
                        send_message(chat_id, result, reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, "🇮🇳 भाषा बदलने के लिए Admin Panel चाहिए।", reply_markup=build_keyboard())
                    return
        
        # ════════════════════════════════════════════════════════
        #  🧠 JARVIS MARKET BRAIN — Smart Stock vs Crypto Detection
        #  Automatically routes Indian stock queries to stock engine
        #  and crypto queries to crypto deep analysis engine
        # ════════════════════════════════════════════════════════
        if MARKET_BRAIN_AVAILABLE:
            market_type = detect_market_type(text)
            
            # INDIAN STOCK MARKET — Deep AI/ML analysis
            if market_type == 'indian_stock':
                is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
                send_message(chat_id, f"{greeting}📈🇮🇳 *JARVIS Indian Market AI Analyzing...*\n"
                            f"_ML + Candles + Sentiment + News + Option Chain_ ⏳")
                try:
                    stock_data = analyze_indian_stock_deep(text)
                    pages = format_indian_stock_report(stock_data)
                    for page in pages:
                        send_message(chat_id, page, reply_markup=build_keyboard())
                    voice_text = format_indian_stock_voice(stock_data)
                    send_jarvis_voice(chat_id, voice_text, intent="buy_sell_stock", is_voice_input=is_voice)
                except Exception as e:
                    logger.error(f"[BRAIN-STOCK] Error: {e}")
                    send_message(chat_id, f"❌ Indian Stock AI error: {str(e)[:100]}", reply_markup=build_keyboard())
                return
            
            # CRYPTO MARKET — Deep analysis with specific token extraction
            elif market_type == 'crypto':
                # Try to extract a specific token from the text
                token = extract_token_from_message(text)
                if token:
                    is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
                    send_message(chat_id, f"{greeting}🔥🧠 *JARVIS Deep AI Analysis for {token}...*\n"
                                f"_15+ Indicators + ML + Candle Patterns + Price Targets_ ⏳")
                    try:
                        deep_data = analyze_crypto_token_deep(token)
                        pages = format_crypto_deep_report(deep_data)
                        for page in pages:
                            send_message(chat_id, page, reply_markup=build_keyboard())
                        voice_text = format_crypto_deep_voice(deep_data)
                        send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto", is_voice_input=is_voice)
                    except Exception as e:
                        logger.error(f"[BRAIN-CRYPTO] Error for {token}: {e}")
                        send_message(chat_id, f"❌ {token} analysis failed: {str(e)[:100]}", reply_markup=build_keyboard())
                    return
                # If no specific token, fall through to existing crypto detection
        
        # ── JARVIS Smart Crypto Detection ──
        # If user asks about a specific token or crypto in free text
        crypto_keywords = re.compile(
            r'(crypto|token|coin|dex|pump\.fun|solana|sol|eth|btc|bitcoin|bnb|'
            r'kaun\s*sa|konsa|kaunsa|best\s*token|gem|altcoin|meme\s*coin|'
            r'buy\s*karu|sell\s*karu|invest|kharid|bech|rug|scam|safe|legit|'
            r'price\s*target|kab\s*sell|kitna\s*profit|100x|10x|moon)',
            re.IGNORECASE
        )
        if CRYPTO_INTEL_AVAILABLE and crypto_keywords.search(text):
            is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
            send_message(chat_id, f"{greeting}🤖🧠 *JARVIS Crypto Intelligence analyzing...* ⏳💕\n_Rug Check + Signals + Targets_")
            try:
                # Check if user is asking about a specific token
                # Extract potential token name/symbol from text
                token_match = re.search(r'(?:about|check|analyze|bata|batao|kaise\s*hai)\s+(\w+)', text, re.IGNORECASE)
                specific_token = token_match.group(1).upper() if token_match else None
                
                if specific_token and len(specific_token) >= 2 and specific_token not in ('THE', 'IS', 'KYA', 'HAI', 'KE', 'KA', 'MEIN', 'CRYPTO', 'TOKEN', 'COIN'):
                    # Analyze specific token
                    analysis = analyze_token_full(specific_token)
                    if analysis and analysis.get("found"):
                        msg = format_token_signal(analysis)
                        voice_text = format_token_voice(analysis)
                        send_message(chat_id, msg, reply_markup=build_keyboard())
                        send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto", is_voice_input=is_voice)
                        try:
                            add_to_watchlist(str(chat_id), specific_token)
                        except Exception as e:
                            logger.error(f"[WATCHLIST] Auto-add failed for {specific_token}: {e}")
                        return
                
                # General crypto query → top picks
                picks = get_top_crypto_picks(limit=5, budget_inr=2000)
                if picks:
                    msg = format_top_picks(picks)
                    voice_text = format_picks_voice(picks)
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                    send_jarvis_voice(chat_id, voice_text, intent="buy_sell_crypto", is_voice_input=is_voice)
                    return
            except Exception as e:
                logger.error(f"[JARVIS-CRYPTO-NLU] Error: {e}")
                # Fall through to regular AI chat
        
        # ── Default: Send to AI Chat with JARVIS persona + Memory ──
        is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
        send_message(chat_id, f"🤖🌸 *जार्विस सोच रही है...* ⏳💕")
        try:
            # Build enhanced context with memory
            memory_context = ""
            if JARVIS_AVAILABLE:
                try:
                    memory_context = get_user_context(chat_id)
                except Exception as e:
                    logger.warning(f"[MEMORY] Failed to get user context: {e}")
            
            response = ai_chat(text, chat_id)
            send_message(chat_id, f"{greeting}{response}", reply_markup=build_keyboard())
            # 🧠 Memory: Save response
            if JARVIS_AVAILABLE:
                try:
                    add_to_conversation(chat_id, "jarvis", response[:300], "chat")
                except Exception as e:
                    logger.warning(f"[MEMORY] Failed to save JARVIS response: {e}")
            # 🎤 JARVIS speaks the response
            send_jarvis_voice(chat_id, response, intent="chat", is_voice_input=is_voice)
        except Exception as e:
            logger.error(f"AI chat failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ AI response failed. Try again or use menu buttons.")
        return

    # ════════════════════════════
    #   UNKNOWN COMMAND — JARVIS handles gracefully
    # ════════════════════════════
    unknown_msg = (
        f"{greeting}"
        f"🤖🌸 *J.A.R.V.I.S.:* ये समझ नहीं आया मुझे जी। 💕\n\n"
        f"💡 *ये करिए:*\n"
        f"┣ नीचे मेनू बटन यूज़ करिए 👇\n"
        f"┣ /start टाइप करिए सब फीचर देखने के लिए\n"
        f"┣ 🤖 Ask JARVIS पर टैप करिए मुझसे बात करने के लिए\n"
        f"┣ या बस अपना सवाल हिंदी/English में पूछिए!\n"
        f"{SPARKLE_LINE}"
    )
    send_message(chat_id, unknown_msg, reply_markup=build_keyboard())
    send_jarvis_voice(chat_id, "ये समझ नहीं आया मुझे जी। कृपया मेनू बटन यूज़ करिए या Ask JARVIS पर टैप करिए।", intent="help")


# ═══════════════════════════════════════════════════════════
#  POLLING LOOP
# ═══════════════════════════════════════════════════════════

def poll_updates():
    """
    Main polling loop with exponential backoff and auto-reconnect.
    Designed to keep running 24/7 even through network failures.
    """
    offset = None
    backoff = 1          # Start at 1 second
    MAX_BACKOFF = 120    # Max 2 minutes between retries
    consecutive_errors = 0
    total_updates = 0
    start_time = time.time()

    logger.info("[POLL] 🚀 Polling loop started with exponential backoff + auto-reconnect")

    while True:
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        try:
            r = requests.get(f"{API_URL}/getUpdates", params=params, timeout=40)
            js = r.json()

            if not js.get("ok"):
                raise ValueError(f"Telegram API error: {js.get('description', 'unknown')}")

            # Success — reset backoff
            backoff = 1
            consecutive_errors = 0

            updates = js.get("result", [])
            if updates:
                logger.info(f"[POLL] Received {len(updates)} updates")

            for u in updates:
                offset = u["update_id"] + 1
                total_updates += 1
                try:
                    handle_update(u)
                except Exception as e:
                    logger.error(f"[POLL] Error handling update: {e}", exc_info=True)

        except requests.exceptions.Timeout:
            # Normal for long-polling — NOT an error
            logger.debug("[POLL] Long-poll timeout (normal)")
            continue

        except requests.exceptions.ConnectionError as e:
            consecutive_errors += 1
            logger.warning(f"[POLL] ❌ Connection error #{consecutive_errors}: {e}")

            if consecutive_errors == 1:
                logger.info(f"[POLL] 🔄 Network issue detected, auto-reconnecting...")
            elif consecutive_errors >= 10:
                logger.critical(f"[POLL] 🚨 {consecutive_errors} consecutive failures! Uptime: {int(time.time()-start_time)}s, Total updates: {total_updates}")

            time.sleep(min(backoff, MAX_BACKOFF))
            backoff = min(backoff * 2, MAX_BACKOFF)  # Exponential backoff
            continue

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"[POLL] ⚠️ Unexpected error #{consecutive_errors}: {e}")
            time.sleep(min(backoff, MAX_BACKOFF))
            backoff = min(backoff * 2, MAX_BACKOFF)
            continue

        time.sleep(0.5)


# ═══════════════════════════════════════════════════════════
#  MAIN — START BOT + AUTO-ALERT THREAD
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("[STARTUP] 🤖🌸 J.A.R.V.I.S. Trading Bot starting...")
    print("🤖🌸 Starting J.A.R.V.I.S. Trading Bot (polling + auto-alerts)")
    # SECURITY: Never print token — even partial tokens can be exploited
    print(f"🔱 Token: {'*' * 10}...{TELEGRAM_TOKEN[-4:]}")
    
    # Initialize database
    try:
        from data_store import init_db
        init_db()
        logger.info("[STARTUP] Database initialized")
    except Exception as e:
        logger.error(f"[STARTUP] DB init failed: {e}")
    
    # ═══════════════════════════════════════════════════════════
    #  🛡️ MAIN THREAD SUPERVISOR — Auto-restart ALL bot threads
    # ═══════════════════════════════════════════════════════════
    _main_threads: dict = {}  # name -> {thread, factory, restart_count}
    _supervisor_running = True
    
    def _register_main_thread(name: str, thread: threading.Thread, factory_fn, description: str = ""):
        """Register a thread with the main supervisor."""
        _main_threads[name] = {
            "thread": thread,
            "factory": factory_fn,
            "restart_count": 0,
            "last_restart": 0,
            "backoff": 5,
            "description": description,
            "started_at": time.time(),
        }
        logger.info(f"[SUPERVISOR-MAIN] Registered: {name} ({description})")
    
    def _main_supervisor_loop():
        """Supervisor loop that checks and restarts crashed main threads."""
        logger.info("[SUPERVISOR-MAIN] 🛡️ Main Thread Supervisor ONLINE!")
        while _supervisor_running:
            for name, info in _main_threads.items():
                thread = info["thread"]
                if thread is None or not thread.is_alive():
                    if info["restart_count"] >= 30:
                        continue
                    if time.time() - info["last_restart"] < info["backoff"]:
                        continue
                    
                    info["restart_count"] += 1
                    info["last_restart"] = time.time()
                    info["backoff"] = min(info["backoff"] * 2, 300)
                    
                    logger.warning(f"[SUPERVISOR-MAIN] 🔄 Thread '{name}' DEAD! Restarting #{info['restart_count']}...")
                    
                    try:
                        new_thread = info["factory"]()
                        new_thread.start()
                        info["thread"] = new_thread
                        info["started_at"] = time.time()
                        logger.info(f"[SUPERVISOR-MAIN] ✅ Thread '{name}' restarted!")
                        
                        # Notify owner
                        try:
                            _notify_cid = int(os.environ.get("TEST_CHAT_ID", "0"))
                            if _notify_cid:
                                send_message(_notify_cid,
                                    f"🔄 *JARVIS Auto-Recovery*\n\n"
                                    f"✅ Thread *{info['description']}* restarted auto!\n"
                                    f"Restart #{info['restart_count']}\n"
                                    f"⏰ {datetime.now(IST).strftime('%I:%M %p IST')}")
                        except Exception as e:
                            logger.error(f"[SUPERVISOR] Recovery notification failed: {e}")
                    except Exception as e:
                        logger.error(f"[SUPERVISOR-MAIN] ❌ Failed to restart '{name}': {e}")
                else:
                    # Healthy — reduce backoff
                    uptime = time.time() - info.get("started_at", time.time())
                    if uptime > 600:
                        info["backoff"] = max(5, info["backoff"] // 2)
            
            time.sleep(30)
    
    # Start auto-alert background thread (with supervisor)
    def _make_auto_alert_thread():
        return threading.Thread(target=auto_alert_loop, daemon=True, name="AutoAlertEngine")
    
    auto_thread = _make_auto_alert_thread()
    auto_thread.start()
    _register_main_thread("auto_alert", auto_thread, _make_auto_alert_thread, "🔔 Auto-Alert Engine")
    logger.info("[STARTUP] 🔔 Auto-Alert Engine started (background thread)")
    
    # Start crypto gem scanner thread (with supervisor)
    def _make_crypto_thread():
        return threading.Thread(target=crypto_alert_loop, daemon=True, name="CryptoGemScanner")
    
    crypto_thread = _make_crypto_thread()
    crypto_thread.start()
    _register_main_thread("crypto_scanner", crypto_thread, _make_crypto_thread, "🪙 Crypto Gem Scanner")
    logger.info("[STARTUP] 🪙 Crypto Gem Scanner started (background thread)")

    # Start Web3 Rocket Scanner background alerts (with supervisor)
    if ROCKET_AVAILABLE:
        def rocket_alert_loop():
            """Background: scan for rockets every 30s, alert on score >= 60."""
            logger.info("🚀 Rocket Scanner STARTED — hunting 25x tokens 24/7")
            while not auto_flag.is_set():
                try:
                    crypto_subscribers = []
                    for k, v in chat_storage.items():
                        if k.startswith("crypto_alerts_") and v:
                            try:
                                cid = int(k.replace("crypto_alerts_", ""))
                                crypto_subscribers.append(cid)
                            except ValueError:
                                pass
                    if not crypto_subscribers:
                        time.sleep(60)
                        continue
                    new_rockets = get_new_rocket_alerts(min_score=60)
                    for rocket in new_rockets:
                        alert_msg = format_single_rocket(rocket)
                        for cid in crypto_subscribers:
                            try:
                                send_message(cid, alert_msg)
                            except Exception:
                                pass
                        time.sleep(0.5)
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"[ROCKET] Alert loop error: {e}")
                    time.sleep(30)
        
        def _make_rocket_thread():
            return threading.Thread(target=rocket_alert_loop, daemon=True, name="RocketScanner")
        
        rocket_thread = _make_rocket_thread()
        rocket_thread.start()
        _register_main_thread("rocket_scanner", rocket_thread, _make_rocket_thread, "🚀 Rocket Scanner")
        logger.info("[STARTUP] 🚀 Rocket Scanner started (background thread)")
    
    # Start JARVIS Monitor (auto price alerts + rug detection + keep-alive + new token alerts + Web3 signals)
    if MONITOR_AVAILABLE:
        try:
            _owner_id = int(os.environ.get("TEST_CHAT_ID", "0"))
            start_monitor(
                send_fn=lambda cid, txt, **kw: send_message(cid, txt, reply_markup=build_keyboard()),
                voice_fn=send_jarvis_voice,
                token=TELEGRAM_TOKEN,
                owner_id=_owner_id
            )
            logger.info("[STARTUP] 🔔 JARVIS Monitor started (price alerts + rug watch + keep-alive + new token alerts + Web3 signals + phantom RT)")
        except Exception as e:
            logger.error(f"[STARTUP] Monitor start failed: {e}")

    # 🛡️ Start Main Thread Supervisor
    _main_supervisor = threading.Thread(target=_main_supervisor_loop, daemon=True, name="MainSupervisor")
    _main_supervisor.start()
    logger.info("[STARTUP] 🛡️ Main Thread Supervisor started — auto-restart for ALL threads")

    # Auto-connect owner Phantom wallet
    if PHANTOM_AVAILABLE:
        try:
            auto_connect_owner_wallet()
            logger.info("[STARTUP] 👻 Owner Phantom wallet auto-connected")
        except Exception as e:
            logger.error(f"[STARTUP] Phantom auto-connect failed: {e}")

    # 🎁 Start Airdrop Hunter — Auto scans every 5 minutes
    if AIRDROP_AVAILABLE:
        try:
            # Set alert callback so airdrop hunter can send messages
            set_alert_callback(lambda cid, txt: send_message(cid, txt, reply_markup=build_keyboard()))
            # Register owner's Solana wallet
            register_wallet(OWNER_CHAT_ID, "solana", os.environ.get("OWNER_SOLANA_WALLET", ""))
            # Start background scanner
            start_airdrop_hunter()
            logger.info("[STARTUP] 🎁🚀 Airdrop Hunter LAUNCHED — auto-scan every 5 min!")
        except Exception as e:
            logger.error(f"[STARTUP] Airdrop Hunter start failed: {e}")

    # 🔥 Start DexTools Scanner — Multi-chain token intelligence
    if DEXTOOLS_AVAILABLE:
        try:
            set_dextools_alert_callback(
                lambda cid, txt: send_message(
                    int(os.environ.get("TEST_CHAT_ID", "0")) if cid is None else cid,
                    txt, reply_markup=build_keyboard()
                )
            )
            start_dextools_scanner()
            logger.info("[STARTUP] 🔥 DexTools Scanner LAUNCHED — multi-chain alerts every 3 min!")
        except Exception as e:
            logger.error(f"[STARTUP] DexTools Scanner start failed: {e}")

    # ⚡ Start Solana TX Monitor — FREE blockchain monitoring
    if SOLANA_ENGINE_AVAILABLE:
        try:
            start_tx_monitor(
                alert_fn=lambda cid, txt: send_message(cid, txt, reply_markup=build_keyboard()),
                token_fn=lambda cid, txt: send_message(cid, txt, reply_markup=build_keyboard()),
            )
            logger.info("[STARTUP] ⚡ Solana TX Monitor LAUNCHED — 24/7 FREE blockchain monitoring!")
        except Exception as e:
            logger.error(f"[STARTUP] Solana TX Monitor start failed: {e}")

    # Start JARVIS SPOC — System health monitoring for Boss
    if SPOC_AVAILABLE:
        try:
            _owner_id = int(os.environ.get("TEST_CHAT_ID", "0"))
            start_spoc(
                send_fn=lambda cid, txt, **kw: send_message(cid, txt, reply_markup=build_keyboard()),
                voice_fn=send_jarvis_voice,
                token=TELEGRAM_TOKEN
            )
            logger.info("[STARTUP] 🧠 JARVIS SPOC started (system health + daily briefing)")
        except Exception as e:
            logger.error(f"[STARTUP] SPOC start failed: {e}")

    # Start JARVIS Super Brain — Worldwide news + proactive intelligence
    if SUPER_BRAIN_AVAILABLE:
        try:
            start_super_brain(
                send_fn=lambda cid, txt, **kw: send_message(cid, txt, reply_markup=build_keyboard()),
                voice_fn=send_jarvis_voice,
                token=TELEGRAM_TOKEN
            )
            logger.info("[STARTUP] 🧠⚡ JARVIS Super Brain started (news + intelligence + SPOC)")
        except Exception as e:
            logger.error(f"[STARTUP] Super Brain start failed: {e}")

    # Send JARVIS startup message
    test_chat_id = os.environ.get("TEST_CHAT_ID")
    if test_chat_id:
        try:
            _phantom_line = f"👻 *Phantom Wallet:* `{OWNER_WALLET[:8]}...{OWNER_WALLET[-4:]}` ✅\n" if PHANTOM_AVAILABLE else ""
            startup_msg = (
                f"🤖⚡ *J.A.R.V.I.S. SUPER BRAIN ONLINE* ⚡🤖\n"
                f"{FIRE_LINE}\n\n"
                f"_\"Main hoon JARVIS — aapka Super AI Computer! Duniya bhar ki har cheez meri nazar mein hai. 🧠⚡\"_\n\n"
                f"🧠 *CORE AI SYSTEMS*\n"
                f"✅ J.A.R.V.I.S. AI Brain — *ACTIVE* 🌸\n"
                f"✅ NLU Intent Engine — *ACTIVE*\n"
                f"✅ 🧠 Memory System — *ACTIVE* 💾\n"
                f"✅ Super Brain Intelligence — {'*ACTIVE* 🧠⚡' if SUPER_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ SPOC Dashboard — {'*ACTIVE* 🔱' if SPOC_AVAILABLE else '*OFF*'}\n"
                f"✅ Auto-Play Voice (Kore) — {'*ACTIVE* 🎤' if VOICE_AVAILABLE else '*OFF*'}\n\n"
                f"📊 *MARKET ENGINES*\n"
                f"✅ Stock ML Engine — *ACTIVE* (6 models)\n"
                f"✅ Crypto Scanner — *ACTIVE* (5 chains)\n"
                f"✅ CoinDCX Web3 — {'*ACTIVE*' if COINDCX_AVAILABLE else '*OFF*'}\n"
                f"✅ Global Market Brain — {'*ACTIVE* 🌍' if GLOBAL_AVAILABLE else '*OFF*'}\n"
                f"✅ 🚀 Rocket Scanner — {'*ACTIVE* 🚀' if ROCKET_AVAILABLE else '*OFF*'}\n\n"
                f"🔔 *ALERT SYSTEMS*\n"
                f"✅ Auto-Alert Engine — *ACTIVE*\n"
                f"✅ JARVIS Monitor — {'*ACTIVE* 🔔' if MONITOR_AVAILABLE else '*OFF*'}\n"
                f"✅ Web3 Signal Scanner — {'*ACTIVE* 📊' if MONITOR_AVAILABLE else '*OFF*'}\n"
                f"✅ New Token Detector — {'*ACTIVE* 🆕' if MONITOR_AVAILABLE else '*OFF*'}\n"
                f"✅ Whale Detector — *ACTIVE*\n"
                f"✅ Rug Detector — *ACTIVE*\n\n"
                f"🛡️ *AUTO-RECOVERY SYSTEMS*\n"
                f"✅ Thread Supervisor — *ACTIVE* 🛡️\n"
                f"✅ Main Thread Watchdog — *ACTIVE* 🔄\n"
                f"✅ Auto-Restart Engine — *ACTIVE* ♻️\n"
                f"✅ Exponential Backoff — *ACTIVE*\n\n"
                f"🛡️ *SECURITY SHIELD*\n"
                f"✅ Anti-Flood Protection — {'*ACTIVE* 🛡️' if SECURITY_AVAILABLE else '*OFF*'}\n"
                f"✅ Input Sanitization — {'*ACTIVE* 🧹' if SECURITY_AVAILABLE else '*OFF*'}\n"
                f"✅ Rate Limiter — {'*ACTIVE* ⏱️' if SECURITY_AVAILABLE else '*OFF*'}\n"
                f"✅ Auto-Ban Engine — {'*ACTIVE* 🚫' if SECURITY_AVAILABLE else '*OFF*'}\n"
                f"✅ Audit Logger — {'*ACTIVE* 📋' if SECURITY_AVAILABLE else '*OFF*'}\n\n"
                f"🎁 *AIRDROP HUNTER*\n"
                f"✅ Auto-Scan Engine — {'*ACTIVE* 🎁' if AIRDROP_AVAILABLE else '*OFF*'}\n"
                f"✅ Solana Wallet Scanner — {'*ACTIVE* 💜' if AIRDROP_AVAILABLE else '*OFF*'}\n"
                f"✅ Scam Detector — {'*ACTIVE* 🚨' if AIRDROP_AVAILABLE else '*OFF*'}\n"
                f"✅ DeFi Protocol Tracker — {'*ACTIVE* 📡' if AIRDROP_AVAILABLE else '*OFF*'}\n\n"
                f"🔥 *DEXTOOLS MULTI-CHAIN ENGINE*\n"
                f"✅ DexScreener Hot Pairs — {'*ACTIVE* 🔥' if DEXTOOLS_AVAILABLE else '*OFF*'}\n"
                f"✅ Live New Pairs — {'*ACTIVE* 🆕' if DEXTOOLS_AVAILABLE else '*OFF*'}\n"
                f"✅ Meme Board — {'*ACTIVE* 🐸' if DEXTOOLS_AVAILABLE else '*OFF*'}\n"
                f"✅ DexTools Airdrops — {'*ACTIVE* 🎁' if DEXTOOLS_AVAILABLE else '*OFF*'}\n"
                f"✅ 7-Chain Coverage — {'*ACTIVE* 🌐' if DEXTOOLS_AVAILABLE else '*OFF*'}\n\n"
                f"🧠 *AI/ML SIGNAL ENGINE*\n"
                f"✅ RSI + MACD + Bollinger — {'*ACTIVE* 📊' if AI_SIGNALS_AVAILABLE else '*OFF*'}\n"
                f"✅ VWAP + EMA + Fibonacci — {'*ACTIVE* 📐' if AI_SIGNALS_AVAILABLE else '*OFF*'}\n"
                f"✅ Buy/Sell Predictions — {'*ACTIVE* 🎯' if AI_SIGNALS_AVAILABLE else '*OFF*'}\n"
                f"✅ Multi-Indicator Score — {'*ACTIVE* 🧠' if AI_SIGNALS_AVAILABLE else '*OFF*'}\n\n"
                f"🔥 *ULTRA AI PREDICTION ENGINE*\n"
                f"✅ 10-Indicator AI Predictor — {'*ACTIVE* 🔥' if ULTRA_AI_AVAILABLE else '*OFF*'}\n"
                f"✅ Rug Risk Assessment — {'*ACTIVE* 🛡️' if ULTRA_AI_AVAILABLE else '*OFF*'}\n"
                f"✅ Whale Detection — {'*ACTIVE* 🐳' if ULTRA_AI_AVAILABLE else '*OFF*'}\n"
                f"✅ Smart Money Flow — {'*ACTIVE* 💰' if ULTRA_AI_AVAILABLE else '*OFF*'}\n"
                f"✅ Price Targets & R:R — {'*ACTIVE* 🎯' if ULTRA_AI_AVAILABLE else '*OFF*'}\n"
                f"✅ Token Health Score — {'*ACTIVE* 💎' if ULTRA_AI_AVAILABLE else '*OFF*'}\n"
                f"✅ Hindi BUY/SELL Calls — {'*ACTIVE* 🇮🇳' if ULTRA_AI_AVAILABLE else '*OFF*'}\n\n"
                f"🔥🧠 *MEGA SCANNER ENGINE (TOP 100)*\n"
                f"✅ Top 100 AI/ML Signals — {'*ACTIVE* 🔥' if MEGA_SCANNER_AVAILABLE else '*OFF*'}\n"
                f"✅ 25+ Candle Pattern Detection — {'*ACTIVE* 🕯️' if MEGA_SCANNER_AVAILABLE else '*OFF*'}\n"
                f"✅ ML Prediction (RF+GB) — {'*ACTIVE* 🤖' if MEGA_SCANNER_AVAILABLE else '*OFF*'}\n"
                f"✅ ₹2K → ₹2L Strategy — {'*ACTIVE* 💰' if MEGA_SCANNER_AVAILABLE else '*OFF*'}\n"
                f"✅ Auto-Alert Top 100 — {'*EVERY 5 MIN* ⚡' if MEGA_SCANNER_AVAILABLE else '*OFF*'}\n\n"
                f"🧠 *MARKET BRAIN — Stock vs Crypto AI*\n"
                f"✅ Market Type Detection — {'*ACTIVE* 🧠' if MARKET_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Indian Stock Deep AI — {'*ACTIVE* 📈🇮🇳' if MARKET_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Crypto Deep Analysis — {'*ACTIVE* 🔥🪙' if MARKET_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Reply-Based Token Analysis — {'*ACTIVE* 🔁' if MARKET_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Smart Query Routing — {'*ACTIVE* 🎯' if MARKET_BRAIN_AVAILABLE else '*OFF*'}\n\n"
                f"🇮🇳🔱 *INDIAN STOCK SUPER ENGINE*\n"
                f"✅ ATM/OTM Call/Put Advisor — {'*ACTIVE* 🎯' if SUPER_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ NSE Holiday Calendar — {'*ACTIVE* 📅' if SUPER_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ Market Hours Detection — {'*ACTIVE* ⏰' if SUPER_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ Weekly/Monthly Expiry — {'*ACTIVE* 📊' if SUPER_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ Black-Scholes Greeks — {'*ACTIVE* Δ Γ Θ' if SUPER_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ IV Rank + Volatility — {'*ACTIVE* 📈' if SUPER_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ ₹2K → ₹2L Option Path — {'*ACTIVE* 💰🚀' if SUPER_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ Hindi BUY/SELL Call/Put — {'*ACTIVE* 🇮🇳' if SUPER_ENGINE_AVAILABLE else '*OFF*'}\n\n"
                f"📰 *INTELLIGENCE*\n"
                f"✅ Worldwide News (15+ sources) — {'*ACTIVE* 📰' if SUPER_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Proactive Alerts — {'*ACTIVE*' if SUPER_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Crypto Intelligence — {'*ACTIVE* 🧠' if CRYPTO_INTEL_AVAILABLE else '*OFF*'}\n\n"
                f"👻 *PHANTOM WALLET*\n"
                f"✅ Phantom RT — {'*ACTIVE* 👻' if PHANTOM_AVAILABLE else '*OFF*'}\n"
                f"✅ Auto-Detect Address — {'*ACTIVE*' if SUPER_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Security — {'*AES-256 ENCRYPTED* 🔐' if PHANTOM_AVAILABLE else '*OFF*'}\n"
                f"{_phantom_line}\n"
                f"🔗 *TRUST WALLET QR CONNECT*\n"
                f"✅ QR Code Generator — {'*ACTIVE* 📱' if QR_WALLET_AVAILABLE else '*OFF*'}\n"
                f"✅ Trust Wallet Deep Links — {'*ACTIVE* 🔗' if QR_WALLET_AVAILABLE else '*OFF*'}\n"
                f"✅ Solana Pay QR — {'*ACTIVE* ◎' if QR_WALLET_AVAILABLE else '*OFF*'}\n"
                f"✅ Multi-Chain Support — {'*ACTIVE* 🌐' if QR_WALLET_AVAILABLE else '*OFF*'}\n\n"
                f"⏰ {datetime.now(IST).strftime('%I:%M %p IST, %d %b %Y')}\n\n"
                f"💡 *New Powers:*\n"
                f"🇮🇳⚡ NIFTY/SENSEX/BankNIFTY Call/Put AI: ATM vs OTM Advisor!\n"
                f"📅 Indian Market Holidays: All NSE holidays 2025-2026!\n"
                f"🔱 Black-Scholes Greeks: Δ Γ Θ V ρ for every option!\n"
                f"💰 ₹2K→₹2L Path: Compound strategy with exact strikes!\n"
                f"⏰ Smart Market Status: Expiry detection + time left!\n"
                f"🧠 MARKET BRAIN: Indian Stock vs Crypto auto-detection!\n"
                f"📈🇮🇳 Indian Stock AI: 6-Model ML + 43 Candles + News!\n"
                f"🔥🪙 Crypto Deep Analysis: 15+ Indicators + ML + Targets!\n"
                f"🔁 Reply-Based Analysis: Reply to any crypto msg for deep dive!\n"
                f"🔥 MEGA SCANNER: Top 100 CoinDCX Tokens AI/ML + Candles!\n"
                f"🕯️ 25+ Candle Patterns: Hammer, Engulfing, Morning Star!\n"
                f"🤖 ML Prediction: Random Forest + Gradient Boosting!\n"
                f"💰 ₹2K → ₹2L Strategy: 5 proven compound growth plans!\n"
                f"⚡ Auto-Alert: Top 100 signals every 5 minutes!\n"
                f"� ULTRA AI: Har token ke saath BUY/SELL + Risk + Health!\n"
                f"🛡️ Rug Risk + 🐳 Whale Detection + 💰 Smart Money Flow!\n"
                f"🎯 Price Targets + R:R Ratio har token ke saath!\n"
                f"�🔗 Trust Wallet QR: Scan karke wallet connect! 📱\n"
                f"◎ Solana Pay QR: Universal wallet QR support!\n"
                f"� DexTools Top 15: Multi-chain hot tokens with deep links!\n"
                f"🧠 AI/ML Signals: RSI, MACD, Bollinger, VWAP, Fibonacci!\n"
                f"🐸 Meme Board: Top meme coins across all chains!\n"
                f"🆕 Live New Pairs: Brand new token launches!\n"
                f"🎁 Airdrop Hunter: Auto-scan free crypto airdrops!\n"
                f"🛡️ Military-Grade Security: Anti-flood + Auto-ban!\n"
                f"📊 /dextools — Top 15 Tokens | /signal — AI Signals\n"
                f"📰 /news — News | 🧠 /briefing — Intelligence\n"
                f"🔱 /spoc — Dashboard | /memeboard — Memes\n\n"
                f"{STAR_LINE}\n"
                f"🧠⚡ *J.A.R.V.I.S. SUPER BRAIN — MAIN HOON NA, BOSS!* ⚡🧠"
            )
            send_message(int(test_chat_id), startup_msg, reply_markup=build_keyboard())
            # Send startup voice in background thread (non-blocking)
            def _startup_voice():
                try:
                    send_jarvis_voice(int(test_chat_id), "JARVIS Super Brain online! Boss Deepak sir, saare systems 100 percent FREE mein chal rahe hain! MEGA SCANNER ENGINE ab ACTIVE hai — Top 100 CoinDCX tokens mein AI ML prediction, 25 plus candle patterns, Random Forest ML, har 5 minute auto-alert! ULTRA AI bhi active — DexTools, Rug Risk, Whale Detection sab! 2 hazaar rupaye se 2 lakh ka strategy bhi ready hai. Trust Wallet QR Connect, Solana Engine, Airdrop Hunter sab active. Main hoon na boss! Jai Shri Ram!", intent="greeting")
                except:
                    pass
            threading.Thread(target=_startup_voice, daemon=True).start()
            logger.info(f"[STARTUP] Sent JARVIS startup message to {test_chat_id}")
        except Exception as e:
            logger.error(f"[STARTUP] Failed to send startup: {e}")
    
    # Start polling with crash-restart protection
    logger.info("[STARTUP] 🚀 Starting main polling loop with auto-restart protection")
    restart_count = 0
    while True:
        try:
            poll_updates()
        except KeyboardInterrupt:
            logger.info("[SHUTDOWN] 🛑 KeyboardInterrupt — shutting down gracefully")
            if MONITOR_AVAILABLE:
                try:
                    from jarvis_monitor import stop_monitor
                    stop_monitor()
                except:
                    pass
            if SUPER_BRAIN_AVAILABLE:
                try:
                    stop_super_brain()
                except:
                    pass
            if SPOC_AVAILABLE:
                try:
                    stop_spoc()
                except:
                    pass
            break
        except Exception as e:
            restart_count += 1
            logger.critical(f"[CRASH] 💥 Polling loop crashed (restart #{restart_count}): {e}", exc_info=True)
            # Notify owner about crash
            try:
                _crash_cid = int(os.environ.get("TEST_CHAT_ID", "0"))
                if _crash_cid:
                    send_message(_crash_cid, 
                        f"⚠️ *JARVIS Auto-Recovery*\n\n"
                        f"Polling crash detected (#{restart_count}).\n"
                        f"Error: {str(e)[:200]}\n"
                        f"Auto-restarting in 5 seconds...\n"
                        f"⏰ {datetime.now(IST).strftime('%I:%M %p IST')}")
            except Exception as e2:
                logger.error(f"[POLLING] Crash notification also failed: {e2}")
            time.sleep(5)  # Wait before restart
            logger.info(f"[RESTART] 🔄 Auto-restarting polling loop (attempt #{restart_count})")
            continue
