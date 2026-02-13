
import os
import sys
from dotenv import load_dotenv
load_dotenv()
import threading
import time
from typing import Optional, Any, Dict
import json
import logging
import re
from datetime import datetime, timedelta
import pytz
import pandas as pd

# Early logger setup (needed before imports that use logger)
_log_file = os.environ.get("TELEGRAM_BOT_LOG", "telegram_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(_log_file, mode='a'),
        logging.StreamHandler()
    ]
)
# Prevent duplicate handlers on re-import
logger = logging.getLogger("telegram_bot")
logger.handlers.clear()
logger.addHandler(logging.FileHandler(_log_file, mode='a'))
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

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
        # Super Brain — Admin vs User personality
        get_jarvis_prompt_for_user, get_personality_for_user,
        INTENT_TO_BUTTON,
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
    from jarvis_tools import (
        get_weather, web_search, identify_song, generate_image,
        get_news_headlines, get_crypto_news,
        mem0_add, mem0_search, mem0_get_all,
        WEATHER_AVAILABLE, SEARCH_AVAILABLE, SONG_AVAILABLE,
        IMAGE_AVAILABLE, NEWS_ENHANCED, MEM0_AVAILABLE,
    )
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    WEATHER_AVAILABLE = SEARCH_AVAILABLE = SONG_AVAILABLE = False
    IMAGE_AVAILABLE = NEWS_ENHANCED = MEM0_AVAILABLE = False

try:
    from sentiment_engine import analyze_news_sentiment, calculate_fear_greed_index, format_sentiment_message
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False

# ─── JARVIS CODER — AI Programming Engine ───
try:
    from jarvis_coder import (
        generate_code, save_project, install_dependencies, push_to_github,
        format_code_result, start_coding_session, process_coding_input,
        get_session, end_coding_session, is_in_coding_session,
        CODER_AVAILABLE, CLAUDE_CONNECTED, GITHUB_CONNECTED,
    )
except ImportError:
    CODER_AVAILABLE = CLAUDE_CONNECTED = GITHUB_CONNECTED = False

# ─── JARVIS CODE ENGINE — Autonomous Code Execution ───
try:
    from jarvis_code_engine import (
        execute_code_autonomous, clone_and_run_github, execute_raw_code,
        detect_code_request, extract_github_url,
        format_execution_result, format_github_result,
        CODE_ENGINE_AVAILABLE,
    )
except ImportError:
    CODE_ENGINE_AVAILABLE = False

# ─── JARVIS ADMIN — Approval + Per-User Personal AI ───
try:
    from jarvis_admin import (
        register_user as ja_register_user,
        get_user as ja_get_user,
        get_user_tier, is_admin as ja_is_admin,
        has_feature, request_approval, approve_request, reject_request,
        get_pending_approvals, format_admin_dashboard,
        grant_feature, upgrade_user,
        get_user_prefs, set_user_pref, format_user_profile,
        set_alerts as ja_set_alerts, are_alerts_on,
        ADMIN_SYSTEM_AVAILABLE, ADMIN_CHAT_ID as JA_ADMIN_CHAT_ID,
    )
except ImportError:
    ADMIN_SYSTEM_AVAILABLE = False

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

# ─── NIFTY SUPER BRAIN — Ultimate Indian Market Intelligence ───
try:
    from nifty_super_brain import (
        get_fii_dii_data, format_fii_dii,
        get_india_vix, format_india_vix,
        get_pcr_data, format_pcr_dashboard,
        calculate_pivot_levels, format_pivot_levels,
        get_gift_nifty, format_gift_nifty,
        get_sector_heatmap, format_sector_heatmap,
        get_oi_buildup, format_oi_buildup,
        get_complete_dashboard,
        get_ai_market_verdict, get_super_brain_analysis,
    )
    NIFTY_BRAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Nifty Super Brain not available: {e}")
    NIFTY_BRAIN_AVAILABLE = False

# ─── NIFTY OPTIONS HUNTER — Budget Options + Position Guardian ───
try:
    from nifty_options_hunter import (
        stop_all_crypto_alerts, start_all_crypto_alerts, is_crypto_alerts_enabled,
        get_user_prefs, set_user_pref,
        find_budget_options, format_budget_options,
        generate_morning_picks,
        track_position, check_position_guardian, get_my_positions_enhanced,
        close_tracked_position,
    )
    OPTIONS_HUNTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Options Hunter not available: {e}")
    OPTIONS_HUNTER_AVAILABLE = False

try:
    from options_engine import (
        generate_option_chain, recommend_strategy,
        format_option_chain, format_strategy,
        format_recommendations, calculate_iv_rank_percentile,
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
        register_wallet, get_new_airdrop_alerts, get_user_wallet,
        get_all_user_wallets, scan_ton_wallet, usd_to_inr,
        OWNER_TON_WALLET,
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

# ─── JARVIS GENIUS ENGINE — Super-Intelligence Layer ───
try:
    from jarvis_genius import (
        genius_chat, genius_classify, get_next_suggestion,
        get_personalized_alerts, semantic_memory, conversation_state,
        extract_entities, record_feedback, detect_implicit_feedback,
        proactive_engine, verify_response_quality,
    )
    GENIUS_AVAILABLE = True
    logger.info("🧠 JARVIS GENIUS ENGINE loaded — Super-Intelligence ACTIVE")
except ImportError as e:
    GENIUS_AVAILABLE = False
    logger.warning(f"JARVIS Genius not available: {e}")

# ─── TRADE TRACKER — Self-Learning Prediction Accuracy ───
try:
    from trade_tracker import (
        log_prediction, verify_predictions, get_calibrated_confidence,
        get_real_win_rate, get_adaptive_weights, format_accuracy_report,
    )
    TRACKER_AVAILABLE = True
    logger.info("📊 TRADE TRACKER loaded — Self-Learning ACTIVE")
except ImportError as e:
    TRACKER_AVAILABLE = False
    logger.warning(f"Trade Tracker not available: {e}")

# ─── MULTI-AGENT SPECIALISTS ───
try:
    from jarvis_agents import (
        route_to_specialist, run_multi_specialist,
        auto_research, format_research_context,
    )
    AGENTS_AVAILABLE = True
    logger.info("🤖 MULTI-AGENT SPECIALISTS loaded — Expert Routing ACTIVE")
except ImportError as e:
    AGENTS_AVAILABLE = False
    logger.warning(f"Agent Specialists not available: {e}")

# ─── CROSS-ASSET CORRELATION ENGINE ───
try:
    from cross_asset_engine import (
        get_correlation_insight, format_correlation_report, scan_all_correlations,
    )
    CORRELATION_AVAILABLE = True
    logger.info("🔗 CROSS-ASSET CORRELATION loaded — Divergence Detection ACTIVE")
except ImportError as e:
    CORRELATION_AVAILABLE = False
    logger.warning(f"Cross-Asset Engine not available: {e}")

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

# ─── OTM↔ATM ENGINE — Smart Options Strike Analysis ───
try:
    from otm_atm_engine import (
        full_otm_atm_analysis, rapid_momentum_signal,
        format_otm_atm_report, format_momentum_signal,
    )
    OTM_ATM_AVAILABLE = True
    logger.info("📊 OTM↔ATM ENGINE loaded — Smart Strike Analysis ACTIVE")
except ImportError as e:
    OTM_ATM_AVAILABLE = False
    logger.warning(f"OTM↔ATM Engine not available: {e}")

# ─── INDIA POWER PREDICTOR — 10-Signal Multi-Factor Prediction ───
try:
    from india_power_predictor import (
        power_predict, format_power_prediction, format_power_voice,
    )
    POWER_PREDICT_AVAILABLE = True
    logger.info("🔮 INDIA POWER PREDICTOR loaded — 10-Signal Engine ACTIVE")
except ImportError as e:
    POWER_PREDICT_AVAILABLE = False
    logger.warning(f"India Power Predictor not available: {e}")

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

# ─── JARVIS PAYMENT SYSTEM — Encrypted UPI + Auto-Invest ───
try:
    from jarvis_payment import (
        PAYMENT_AVAILABLE,
        get_wallet as pay_get_wallet, get_wallet_balance, get_portfolio,
        generate_deposit_qr, verify_deposit,
        set_bank_details, request_withdrawal,
        auto_invest, scan_gem_tokens, sell_position, sell_all,
        get_transaction_history, set_rebalance_callback, start_auto_rebalance,
        calculate_crypto_tax, format_tax_report,
        format_wallet_dashboard, format_portfolio, format_gem_scan,
        format_invest_result, AUTO_INVEST_CONFIG,
    )
except ImportError:
    PAYMENT_AVAILABLE = False

# ─── JARVIS REAL TRADER — On-Chain Solana Trading via Jupiter DEX ───
try:
    from jarvis_real_trader import (
        SOLANA_SDK_AVAILABLE as REAL_TRADER_SDK,
        create_trading_wallet, get_trading_wallet, get_sol_balance as trader_sol_balance,
        buy_token, sell_token, execute_swap, get_swap_quote,
        get_live_portfolio, get_token_accounts as trader_token_accounts,
        enable_auto_trade, disable_auto_trade,
        start_auto_trader, stop_auto_trader, set_trade_callback,
        format_trading_wallet, format_live_portfolio, format_trade_history,
        COMPOUND_STAGES,
    )
    REAL_TRADER_AVAILABLE = True
except ImportError as _rt_err:
    REAL_TRADER_AVAILABLE = False
    REAL_TRADER_SDK = False
    logger.warning(f"[IMPORT] jarvis_real_trader not loaded: {_rt_err}")

# ─── OI + TRAP BRAIN — NIFTY/SENSEX Options Intelligence ───
try:
    from oi_trap_brain import (
        OI_TRAP_BRAIN_AVAILABLE,
        fetch_option_chain, detect_traps, find_budget_plays,
        get_options_super_signal, get_oi_change,
        format_trap_analysis, format_live_chain, format_strike_map,
        format_max_pain, format_oi_change, format_straddle_premium,
        format_super_signal,
    )
except ImportError as _oi_err:
    OI_TRAP_BRAIN_AVAILABLE = False
    logger.warning(f"[IMPORT] oi_trap_brain not loaded: {_oi_err}")

# ─── OPTIONS PRO — Real-time Strike Prices from NSE ───
try:
    from jarvis_options_pro import (
        OPTIONS_PRO_AVAILABLE,
        get_strike_price, get_nearby_options, get_full_chain_summary,
        parse_option_query,
        format_strike_result, format_strike_voice,
        format_nearby_options, format_chain_summary,
    )
except ImportError as _op_err:
    OPTIONS_PRO_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_options_pro not loaded: {_op_err}")

# ─── SUPER TRADER BRAIN — Nuclear Market Intelligence ───
try:
    from jarvis_super_trader_brain import (
        SUPER_BRAIN_AVAILABLE,
        get_nuclear_market_view, format_nuclear_view, format_nuclear_voice,
        get_quick_pulse,
    )
except ImportError as _sb_err:
    SUPER_BRAIN_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_super_trader_brain not loaded: {_sb_err}")

# ─── SUPER MEMORY — Persistent Conversations + Positions ───
try:
    from jarvis_memory_pro import (
        MEMORY_PRO_AVAILABLE,
        remember_message, get_conversation_history, get_full_context_for_ai,
        remember_fact, recall_fact, get_all_facts,
        add_position, close_position, get_active_positions, update_position_price,
        parse_position_from_text, format_positions, format_position_voice,
        get_memory_stats, format_memory_stats, set_user_name, flush_all,
        load_memory, save_memory, search_memory,
    )
except ImportError as _mem_err:
    MEMORY_PRO_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_memory_pro not loaded: {_mem_err}")

# ─── CHART ENGINE — Professional Trading Charts ───
try:
    from jarvis_chart_engine import (
        CHART_ENGINE_AVAILABLE,
        handle_chart_command, generate_chart, get_chart_analysis,
        parse_chart_request, cleanup_old_charts,
    )
except ImportError as _ce_err:
    CHART_ENGINE_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_chart_engine not loaded: {_ce_err}")

# ─── SCREENER PRO — Natural Language Stock Screener ───
try:
    from jarvis_screener_pro import (
        SCREENER_AVAILABLE,
        run_screener, screen_oversold, screen_overbought,
        screen_volume_spike, screen_gap_ups, screen_top_momentum,
        screen_52week_high, screen_strong_bullish,
    )
except ImportError as _sc_err:
    SCREENER_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_screener_pro not loaded: {_sc_err}")

# ─── NEWS BRAIN — Real-Time News + Sentiment ───
try:
    from jarvis_news_brain import (
        NEWS_BRAIN_AVAILABLE,
        handle_news_command, get_latest_news, get_stock_news,
        get_breaking_news, get_sector_news, get_news_sentiment_score,
    )
except ImportError as _nb_err:
    NEWS_BRAIN_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_news_brain not loaded: {_nb_err}")

# ─── BACKTESTER PRO — Strategy Backtesting Engine ───
try:
    from jarvis_backtester_pro import (
        BACKTESTER_AVAILABLE,
        handle_backtest_command, backtest_rsi_strategy,
        backtest_macd_strategy, backtest_bollinger_strategy,
    )
except ImportError as _bt_err:
    BACKTESTER_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_backtester_pro not loaded: {_bt_err}")

# ─── P&L JOURNAL — Trade Journal + Analytics ───
try:
    from jarvis_pnl_journal import (
        PNL_JOURNAL_AVAILABLE,
        log_trade, close_trade, format_daily_pnl, format_weekly_pnl,
        format_monthly_pnl, format_overall_stats, parse_trade_entry,
    )
except ImportError as _pj_err:
    PNL_JOURNAL_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_pnl_journal not loaded: {_pj_err}")

# ─── INTRADAY SCANNER — Real-Time Breakout Detection ───
try:
    from jarvis_intraday_scanner import (
        INTRADAY_SCANNER_AVAILABLE,
        run_intraday_scan, scan_breakouts, scan_volume_spikes, scan_momentum,
    )
except ImportError as _is_err:
    INTRADAY_SCANNER_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_intraday_scanner not loaded: {_is_err}")

# ─── FUTURES BRAIN — PCR + Max Pain + Basis ───
try:
    from jarvis_futures_brain import (
        FUTURES_BRAIN_AVAILABLE,
        handle_futures_command, get_futures_dashboard,
        format_pcr, format_max_pain, format_vix,
    )
except ImportError as _fb_err:
    FUTURES_BRAIN_AVAILABLE = False
    logger.warning(f"[IMPORT] jarvis_futures_brain not loaded: {_fb_err}")

# ─── JARVIS PERSONAL AI AGENT — Never Says No ───
try:
    from jarvis_personal_agent import (
        AGENT_AVAILABLE,
        save_note, get_notes, delete_note,
        add_reminder, get_reminders, set_reminder_callback, start_reminder_engine,
        add_task, get_tasks, complete_task,
        research_topic, format_research,
        get_weather as agent_get_weather, calculate as agent_calculate,
        detect_agent_intent, execute_agent_action,
        format_notes, format_tasks, format_reminders, format_agent_dashboard,
    )
except ImportError:
    AGENT_AVAILABLE = False

# ─── NSE LIVE ENGINE — Real-Time Option Chain + Pricing (NUCLEAR) ───
try:
    from nse_live_engine import (
        NSE_LIVE_AVAILABLE,
        fetch_live_option_chain, get_live_spot, get_strike_price as nse_get_strike,
        get_atm_otm_analysis, format_option_chain_telegram,
        format_atm_otm_analysis, LiveOptionChain, LiveOptionStrike,
    )
except ImportError as _nse_err:
    NSE_LIVE_AVAILABLE = False
    logger.warning(f"[IMPORT] nse_live_engine not loaded: {_nse_err}")

# ─── PREDICTION ACCURACY TRACKER — L3 Upgrade ───
try:
    from prediction_tracker import (
        PREDICTION_TRACKER_AVAILABLE,
        record_prediction, verify_predictions,
        get_accuracy_report, format_accuracy_report,
    )
except ImportError as _pt_err:
    PREDICTION_TRACKER_AVAILABLE = False
    logger.warning(f"[IMPORT] prediction_tracker not loaded: {_pt_err}")

import requests

# ─── AUTOMATION ENGINE ───
try:
    from automation_engine import automation_engine
    AUTOMATION_ENGINE_AVAILABLE = True
except Exception as e:
    AUTOMATION_ENGINE_AVAILABLE = False
    logger.warning(f"Automation Engine not available: {e}")

# Logger already configured early (above imports)

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
#  AUTOMATION ENGINE STARTUP — Full background automation
# ═══════════════════════════════════════════════════════════
if AUTOMATION_ENGINE_AVAILABLE:
    try:
        automation_engine.start()
        logger.info("[AUTOMATION] Engine started — background tasks active.")
    except Exception as e:
        logger.warning(f"[AUTOMATION] Engine failed to start: {e}")

# ═══════════════════════════════════════════════════════════
#  L1 UPGRADE: ATOMIC JSON WRITES — prevents corruption on crash
# ═══════════════════════════════════════════════════════════
import tempfile

_json_write_lock = threading.Lock()

def atomic_json_write(filepath: str, data: Any):
    """Write JSON atomically: write to tmp, then rename (crash-safe)."""
    with _json_write_lock:
        dir_name = os.path.dirname(filepath) or "."
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=dir_name)
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, filepath)
        except Exception as e:
            logger.error(f"[ATOMIC-WRITE] Failed for {filepath}: {e}")
            # Try direct write as fallback
            try:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass

# ═══════════════════════════════════════════════════════════
#  L1 UPGRADE: IN-MEMORY STOPPED USERS CACHE
#  No more disk I/O on every send_message!
# ═══════════════════════════════════════════════════════════
_stopped_users_cache: Dict[str, bool] = {}
_stopped_cache_loaded = False

def _load_stopped_users_cache():
    """Load stopped users from disk into memory (once at startup)."""
    global _stopped_users_cache, _stopped_cache_loaded
    try:
        if os.path.exists("jarvis_stopped_users.json"):
            with open("jarvis_stopped_users.json", "r") as f:
                _stopped_users_cache = json.load(f)
        _stopped_cache_loaded = True
        logger.info(f"[L1] Loaded {len(_stopped_users_cache)} stopped users into cache")
    except Exception as e:
        logger.warning(f"[L1] Stopped users cache load error: {e}")
        _stopped_cache_loaded = True

def set_user_stopped(chat_id: int, stopped: bool = True):
    """Set user stopped status in cache + persist atomically."""
    _stopped_users_cache[str(chat_id)] = stopped
    chat_storage[f"crypto_alerts_{chat_id}"] = not stopped
    atomic_json_write("jarvis_stopped_users.json", _stopped_users_cache)

def is_user_stopped_cached(chat_id: int) -> bool:
    """Check if user stopped — from memory, no disk I/O."""
    if not _stopped_cache_loaded:
        _load_stopped_users_cache()
    return _stopped_users_cache.get(str(chat_id), False)

# Restore stopped-users from L1 cache (replaces old disk read)
_load_stopped_users_cache()
for _cid_str, _val in _stopped_users_cache.items():
    if _val:
        chat_storage[f"crypto_alerts_{_cid_str}"] = False
logger.info(f"[STARTUP] L1 stopped user cache loaded for {sum(1 for v in _stopped_users_cache.values() if v)} users")


def is_user_alerts_stopped(chat_id: int) -> bool:
    """Check if user has stopped ALL alerts (crypto + market). L1: Memory-only."""
    # Check in-memory flag
    if chat_storage.get(f"crypto_alerts_{chat_id}") is False:
        return True
    # Check L1 cache (no disk read!)
    return is_user_stopped_cached(chat_id)


def guarded_alert_send(chat_id, text, **kwargs):
    """GLOBAL guard: Only send alert if user hasn't stopped alerts.
    ALL background modules (monitor, airdrop, dextools, web3) use this."""
    try:
        cid = int(chat_id)
    except (ValueError, TypeError):
        return
    if is_user_alerts_stopped(cid):
        logging.warning(f"[GUARD] BLOCKED alert to {cid} — user pressed STOP (guarded_alert_send)")
        return
    # Double check — nuclear level
    if chat_storage.get(f"crypto_alerts_{cid}") is False:
        logging.warning(f"[GUARD] BLOCKED alert to {cid} — in-memory flag (guarded_alert_send)")
        return
    send_message(cid, text, reply_markup=build_keyboard())


def guarded_voice_send(chat_id, text, **kwargs):
    """GLOBAL guard: Only send voice if user hasn't stopped alerts."""
    try:
        cid = int(chat_id)
    except (ValueError, TypeError):
        return
    if is_user_alerts_stopped(cid):
        logging.warning(f"[GUARD] BLOCKED voice to {cid} — user pressed STOP")
        return
    if chat_storage.get(f"crypto_alerts_{cid}") is False:
        return
    send_jarvis_voice(cid, text, **kwargs)


def market_brain_send(chat_id, text, **kwargs):
    """MARKET BRAIN send — BYPASSES crypto stop.
    Only checks its own market_brain_stopped flag.
    This allows market analysis to flow even when crypto alerts are OFF."""
    try:
        cid = int(chat_id)
    except (ValueError, TypeError):
        return
    if chat_storage.get(f"market_brain_stopped_{cid}") is True:
        logging.warning(f"[MARKET-BRAIN] BLOCKED to {cid} — market brain OFF")
        return
    send_message(cid, text, reply_markup=build_keyboard())


def market_brain_voice_send(chat_id, text, **kwargs):
    """MARKET BRAIN voice — BYPASSES crypto stop."""
    try:
        cid = int(chat_id)
    except (ValueError, TypeError):
        return
    if chat_storage.get(f"market_brain_stopped_{cid}") is True:
        return
    send_jarvis_voice(cid, text, **kwargs)

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

# NUCLEAR STOP: All background thread names that send CRYPTO alerts
# MarketBrainNotifier is EXCLUDED — market brain always sends
_BG_THREAD_NAMES = {
    "AutoAlertEngine", "CryptoGemScanner", "RocketScanner",
    "PredictionTracker", "jarvis-monitor", "keepalive-watchdog",
    "new-token-detector", "web3-signal-scanner", "phantom-realtime",
    "thread-supervisor", "AirdropHunter", "MainSupervisor",
}
# Market Brain thread is NEVER blocked by crypto stop
_MARKET_BRAIN_THREAD = "MarketBrainNotifier"

def send_message(chat_id: int, text: str, reply_markup: Optional[dict] = None):
    # ══ NUCLEAR STOP CHECK — L1 UPGRADED: Memory-only, no disk I/O ══
    _tname = threading.current_thread().name
    if _tname in _BG_THREAD_NAMES:
        try:
            _cid = int(chat_id)
            # Check in-memory flag FIRST (fastest)
            if chat_storage.get(f"crypto_alerts_{_cid}") is False:
                return
            # Check L1 cached stopped users (no disk read!)
            if is_user_stopped_cached(_cid):
                chat_storage[f"crypto_alerts_{_cid}"] = False
                return
        except Exception as _e:
            logging.error(f"[NUCLEAR-STOP] Check error: {_e}")
    # ══ END NUCLEAR STOP ══
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


def send_photo(chat_id: int, image_bytes: bytes, caption: Optional[str] = None, reply_markup: dict = None):
    # ══ NUCLEAR STOP CHECK ══
    _tname = threading.current_thread().name
    if _tname in _BG_THREAD_NAMES:
        try:
            _cid = int(chat_id)
            if chat_storage.get(f"crypto_alerts_{_cid}") is False:
                return
            _sf = "jarvis_stopped_users.json"
            if os.path.exists(_sf):
                with open(_sf, "r") as _ff:
                    _sd = json.load(_ff)
                if _sd.get(str(_cid), False):
                    chat_storage[f"crypto_alerts_{_cid}"] = False
                    return
        except Exception:
            pass
    # ══ END NUCLEAR STOP ══
    url = f"{API_URL}/sendPhoto"
    files = {"photo": ("qrcode.png", image_bytes)}
    data = {"chat_id": chat_id, "parse_mode": "Markdown"}
    if caption:
        data["caption"] = caption
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(url, files=files, data=data, timeout=30)
        print(f"send_photo -> chat_id={chat_id} status={r.status_code}")
        if r.status_code != 200:
            logger.error(f"send_photo failed: {r.text[:200]}")
    except Exception as e:
        logger.error(f"send_photo exception for chat_id={chat_id}: {e}")


def _send_jarvis_voice_sync(chat_id: int, text: str, intent: str = "", is_voice_input: bool = False):
    """
    🎤 Send JARVIS voice — AUTO-PLAY video note (round bubble)!
    1. Generate TTS audio (OGG)
    2. Convert to video note (MP4 with JARVIS avatar)
    3. Send as sendVideoNote → AUTO-PLAYS in Telegram!
    4. Fallback: regular sendVoice if video note fails
    """
    # ══ NUCLEAR STOP CHECK ══
    _tname = threading.current_thread().name
    if _tname in _BG_THREAD_NAMES:
        try:
            _cid = int(chat_id)
            if chat_storage.get(f"crypto_alerts_{_cid}") is False:
                logging.warning(f"[NUCLEAR-STOP] BLOCKED bg voice from {_tname} to {_cid}")
                return
            _sf = "jarvis_stopped_users.json"
            if os.path.exists(_sf):
                with open(_sf, "r") as _ff:
                    _sd = json.load(_ff)
                if _sd.get(str(_cid), False):
                    chat_storage[f"crypto_alerts_{_cid}"] = False
                    logging.warning(f"[NUCLEAR-STOP] BLOCKED bg voice from {_tname} to {_cid}")
                    return
        except Exception:
            pass
    # ══ END NUCLEAR STOP ══
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
        
        # FALLBACK: regular voice message (auto-play waveform in Telegram)
        send_voice_message(chat_id, voice_path, TELEGRAM_TOKEN)
    except Exception as e:
        logger.error(f"[JARVIS-VOICE] Failed to send voice: {e}")


def send_jarvis_voice(chat_id: int, text: str, intent: str = "", is_voice_input: bool = False):
    """
    🎤 ASYNC wrapper — sends voice in background thread so text response comes FIRST.
    This makes JARVIS feel INSTANT: text arrives in 2-3 sec, voice follows 3-5 sec later.
    """
    t = threading.Thread(
        target=_send_jarvis_voice_sync,
        args=(chat_id, text, intent, is_voice_input),
        daemon=True,
        name="JarvisVoiceSend",
    )
    t.start()


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
        ["🔮 NIFTY Power Predict 💪", "🔮 SENSEX Power Predict 💪"],
        ["📊 NIFTY OTM↔ATM 🎯", "📊 SENSEX OTM↔ATM 🎯"],
        ["📊 BankNIFTY OTM↔ATM 🎯", "⚡ 2-Min Momentum 🚀"],
        ["📈🇮🇳 Indian Stock AI 🧠", "🧠 Super Prediction 🔮"],
        ["📰 Market Sentiment 💬", "⚠️ Risk Calculator 🛡️"],
        ["🕯️ Candle Patterns 📊", "🌍 Market Trend 📈"],
        ["⏰ Market Status 🔔", "📊 Live Snapshot 🔴"],
        ["🔮 Tomorrow Prediction 🎯"],
        ["🇮🇳 NIFTY Super Dashboard 🧠"],
        ["🏛️ FII/DII Flow 📊", "😱 India VIX Gauge 📊"],
        ["📊 NIFTY PCR 🔢", "📊 BankNIFTY PCR 🔢"],
        ["📐 NIFTY Pivot Levels 📊", "📐 SENSEX Pivot Levels"],
        ["🌅 GIFT NIFTY Gap 📊", "📊 OI Buildup Analysis"],
        ["🏭 Sector Heatmap 📊", "⚡ Scalp Signal 🎯"],
        ["📊 Multi-TF Signal 🔄"],
        ["💰 Budget Options 🎯", "💰 BankNIFTY Budget 🎯"],
        ["⚡ Strike Price Pro 🎯", "🧠 Options Super Signal"],
        ["📊 My Tracked Positions", "🧠 Memory Status"],
        ["📊 Live Charts 📈", "🔍 Smart Screener 🔎"],
        ["📰 Market News 📰", "⚡ Intraday Scanner ⚡"],
        ["🔬 Backtester Pro 🔬", "📊 Futures Brain 📊"],
        ["📋 P&L Journal 📋", "🚀 Top Movers 🚀"],
        ["🔔 9AM Auto Picks 🌅", "🛡️ My Positions Guard"],
        ["🛑 STOP All Crypto 🛑", "🟢 START Crypto Alerts"],
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
        ["�🔐 JARVIS WALLET 💳", "💵 Deposit (UPI) 📱"],
        ["🤖 Auto-Invest 🚀", "📊 My Portfolio 💎"],
        ["💎 Gem Scanner 🔍", "🏦 Withdraw to Bank 💸"],
        ["🏛️ Income Tax 📊", "📜 Transactions 📋"],
        ["🚀 Real Trading Wallet", "🤖 Auto-Trade ON/OFF"],
        ["📊 Live Portfolio 🔥", "📜 Trade History 📋"],
        ["🤖 JARVIS Agent 🧠", "📝 My Notes 📒"],
        ["✅ My Tasks 📋", "⏰ My Reminders 🔔"],
        ["🔍 Research 🧠", "🌤️ Weather ☁️"],
        ["�👻 Phantom Wallet 🔮", "👻 Connect Wallet"],
        ["👻 Wallet Scan 📊", "👻 Wallet Summary ⚡"],
        ["👻 Claim Airdrops 🎁", "👻 Transfer SOL 💸"],
        ["👻 Wallet Alerts ON", "👻 Disconnect Wallet"],
        ["💎 Telegram Wallet 💳", "🎁 Airdrop Hunter 🚀"],
        ["📝 Set My Wallet 🔑", "👛 My Wallets 💰"],
        ["🔮 Upcoming Airdrops", "🎁 Solana Airdrops"],
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
            data = yf.download(ticker, period="5d", progress=False, timeout=15)
            if data is not None and len(data) >= 2:
                # Handle yfinance MultiIndex columns robustly
                if isinstance(data.columns, pd.MultiIndex):
                    data = data.droplevel(1, axis=1)
                    # Remove duplicate columns
                    data = data.loc[:, ~data.columns.duplicated()]
                col = 'Close' if 'Close' in data.columns else 'close'
                close_series = data[col]
                if isinstance(close_series, pd.DataFrame):
                    close_series = close_series.iloc[:, 0]
                close_vals = close_series.values
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
            
            # Filter out users who pressed STOP
            subs = [s for s in subs if not is_user_alerts_stopped(s)]
            
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
                            
                            # ━━━ 9 AM AUTO-PICKS: Budget Call/Put ━━━
                            try:
                                if OPTIONS_HUNTER_AVAILABLE:
                                    morning_picks = generate_morning_picks()
                                    for chat_id in subs:
                                        try:
                                            prefs = get_user_prefs(chat_id)
                                            if prefs.get("morning_picks", True) and prefs.get("stock_alerts", True):
                                                send_message(chat_id, morning_picks)
                                        except Exception:
                                            pass
                                    logger.info("[AUTO] 🎯 9 AM Budget Options picks sent!")
                            except Exception as e:
                                logger.error(f"[AUTO] Morning picks error: {e}")
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
                #  + POSITION GUARDIAN (Trail SL)
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                try:
                    open_positions = get_open_positions()
                    if open_positions:
                        nifty_spot = get_live_price("^NSEI")
                        sensex_spot = get_live_price("^BSESN")
                        banknifty_spot = get_live_price("^NSEBANK")
                        
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
                #  POSITION GUARDIAN — Trail SL Auto-Protect
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                try:
                    if OPTIONS_HUNTER_AVAILABLE:
                        guardian_positions = get_open_positions()
                        if guardian_positions:
                            for pos in guardian_positions:
                                try:
                                    idx_name = pos["index_name"].upper()
                                    if "BANK" in idx_name:
                                        spot = get_live_price("^NSEBANK")
                                    elif "NIFTY" in idx_name:
                                        spot = get_live_price("^NSEI")
                                    else:
                                        spot = get_live_price("^BSESN")
                                    
                                    guardian_alert = check_position_guardian(pos, spot)
                                    if guardian_alert and guardian_alert.get("msg"):
                                        guardian_key = f"guardian_{pos['id']}_{guardian_alert['type']}"
                                        if time.time() - last_auto_alert_time.get(guardian_key, 0) > 300:
                                            last_auto_alert_time[guardian_key] = time.time()
                                            try:
                                                send_message(pos["chat_id"], guardian_alert["msg"])
                                            except Exception:
                                                pass
                                except Exception as e:
                                    logger.error(f"[GUARDIAN] Check failed for {pos.get('id')}: {e}")
                except Exception as e:
                    logger.error(f"[GUARDIAN] Guardian loop error: {e}")

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
                        # Respect STOP flag
                        if is_user_alerts_stopped(cid):
                            continue
                        # Also check OPTIONS_HUNTER prefs (STOP ALL)
                        if OPTIONS_HUNTER_AVAILABLE:
                            if not is_crypto_alerts_enabled(cid):
                                continue
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
            # ── SONG RECOGNITION MODE ──
            if chat_storage.get(f"awaiting_song_{chat_id}") and SONG_AVAILABLE:
                chat_storage[f"awaiting_song_{chat_id}"] = False
                send_message(chat_id, "🎵 Listening to the song... 🎶")
                try:
                    audio_path = download_telegram_voice(file_id, TELEGRAM_TOKEN)
                    if audio_path:
                        with open(audio_path, "rb") as _af:
                            audio_bytes = _af.read()
                        result = identify_song(audio_bytes)
                        send_message(chat_id, result, reply_markup=build_keyboard())
                        send_jarvis_voice(chat_id, result[:200], intent="chat")
                    else:
                        send_message(chat_id, "⚠️ Audio download failed. Try again!", reply_markup=build_keyboard())
                except Exception as e:
                    logger.error(f"Song recognition error: {e}")
                    send_message(chat_id, f"⚠️ Song recognition error: {e}", reply_markup=build_keyboard())
                return

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
    
    # 🧠💾 SUPER MEMORY: Save every message + detect positions
    if MEMORY_PRO_AVAILABLE:
        try:
            set_user_name(chat_id, user_name)
            remember_message(chat_id, "user", text)
        except Exception as _me:
            logger.debug(f"[MEMORY-PRO] Save error: {_me}")
    
    # 🧠💾 POSITION DETECTION: "maine nifty 25950 call li"
    if MEMORY_PRO_AVAILABLE and text:
        try:
            _pos_info = parse_position_from_text(text)
            if _pos_info:
                _p_sym = _pos_info["symbol"]
                _p_strike = _pos_info["strike"]
                _p_type = _pos_info["option_type"]
                _p_action = _pos_info["action"]
                _p_price = _pos_info.get("price", 0)
                
                if _p_action == "BUY":
                    # Try to get real-time price if user didn't mention price
                    if not _p_price and OPTIONS_PRO_AVAILABLE:
                        try:
                            from jarvis_options_pro import get_strike_price as _gsp
                            _sp_data = _gsp(_p_sym, _p_strike, _p_type)
                            if _sp_data and not _sp_data.get("error"):
                                _p_price = _sp_data.get("ltp", 0)
                        except:
                            pass
                    
                    pos = add_position(chat_id, _p_sym, _p_strike, _p_type, _p_price)
                    opt_name = "CALL" if _p_type == "CE" else "PUT"
                    price_txt = f" @ ₹{_p_price:,.2f}" if _p_price else ""
                    send_message(chat_id,
                        f"✅ *Position Tracked!* 📊\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📌 *{_p_sym} {_p_strike} {opt_name}*{price_txt}\n"
                        f"🆔 Position #{pos.get('id', 0)}\n"
                        f"⏰ {datetime.now(IST).strftime('%I:%M %p')}\n\n"
                        f"🧠 _JARVIS yaad rakhega aur din bhar analyze karega!_\n"
                        f"💡 _Close karne ke liye: \"{_p_sym.lower()} {_p_strike} {opt_name.lower()} sell ki\"_",
                        reply_markup=build_keyboard()
                    )
                    # Voice confirmation
                    try:
                        from voice_engine import generate_voice
                        _vt = f"Ji haan! Maine note kar liya... {_p_sym} {_p_strike} {opt_name} position tracked hai ab! Main din bhar analyze karungi aapke liye!"
                        _vf = generate_voice(_vt)
                        if _vf:
                            send_voice(chat_id, _vf)
                    except:
                        pass
                    
                    # Now also get live analysis
                    if OPTIONS_PRO_AVAILABLE:
                        try:
                            from jarvis_options_pro import get_strike_price as _gsp2, format_strike_result as _fsr
                            _live = _gsp2(_p_sym, _p_strike, _p_type)
                            if _live and not _live.get("error"):
                                send_message(chat_id, _fsr(_live), reply_markup=build_keyboard())
                        except:
                            pass
                    return
                
                elif _p_action == "SELL":
                    closed = close_position(chat_id, symbol=_p_sym, strike=_p_strike, exit_price=_p_price)
                    if closed:
                        pnl = closed.get("pnl", 0)
                        pnl_pct = closed.get("pnl_pct", 0)
                        emoji = "🟢" if pnl >= 0 else "🔴"
                        opt_name = "CALL" if _p_type == "CE" else "PUT"
                        send_message(chat_id,
                            f"{emoji} *Position Closed!* 📊\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"📌 *{_p_sym} {_p_strike} {opt_name}*\n"
                            f"📥 Entry: ₹{closed.get('entry_price', 0):,.2f}\n"
                            f"📤 Exit: ₹{_p_price:,.2f}\n"
                            f"💰 P&L: ₹{pnl:+,.2f} ({pnl_pct:+.1f}%)\n\n"
                            f"🧠 _Position closed and saved to memory!_",
                            reply_markup=build_keyboard()
                        )
                        return
        except Exception as _pe:
            logger.debug(f"[MEMORY-PRO] Position parse error: {_pe}")
    
    # 🔐 Admin System: Register user on every interaction
    if ADMIN_SYSTEM_AVAILABLE:
        try:
            _username = msg.get("chat", {}).get("username", "")
            ja_register_user(chat_id, user_name, _username)
        except Exception:
            pass
    
    # ════════════════════════════════════════════════════════
    #  Ignore section-header buttons (decorative, non-functional)
    # ════════════════════════════════════════════════════════
    if text and "━━" in text:
        # These are category headers in the keyboard, not commands
        send_message(chat_id, f"{greeting}ℹ️ Yeh section header hai. Neeche ke buttons press karo! 🌸", reply_markup=build_keyboard())
        return

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
        send_message(chat_id, welcome)
        # 🚀 Send Mini App inline button
        _mini_url = os.environ.get("MINI_APP_URL", "").rstrip("/")
        if _mini_url:
            _inline_kb = {
                "inline_keyboard": [
                    [{"text": "🚀 Open JARVIS Trading App", "web_app": {"url": f"{_mini_url}/miniapp"}}],
                    [
                        {"text": "📊 Markets", "web_app": {"url": f"{_mini_url}/miniapp"}},
                        {"text": "🤖 AI Chat", "web_app": {"url": f"{_mini_url}/miniapp"}},
                    ],
                    [
                        {"text": "💰 Wallet", "web_app": {"url": f"{_mini_url}/miniapp"}},
                        {"text": "🎯 Auto-Sniper", "web_app": {"url": f"{_mini_url}/miniapp"}},
                    ],
                ]
            }
            send_message(chat_id, "👇 *Tap below to open the full trading dashboard:*", reply_markup=_inline_kb)
        # 🎤 JARVIS speaks the welcome
        send_jarvis_voice(chat_id, f"नमस्ते {user_name} जी! मैं राम लाल हूँ, आपकी AI ट्रेडिंग असिस्टेंट। सारे सिस्टम्स 100 percent active हैं। OI ट्रैप ब्रेन, ऑप्शन सुपर सिग्नल, वॉइस Aoede — सब ready है। बताइए, आज मैं आपकी क्या मदद करूँ?", intent="greeting")
        return
    # ════════════════════════════
    #   /menu COMMAND
    # ════════════════════════════
    if text == "/menu":
        send_message(chat_id, f"🤖🌸 _Menu!_ 👇", reply_markup=build_keyboard())
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
            trend_msg = get_market_trend_analysis()
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
        except Exception as e:
            logger.error(f"Market trend failed: {e}", exc_info=True)
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
    #   NIFTY SIGNALS — NUCLEAR UPGRADED
    # ════════════════════════════
    if text in ("📊 NIFTY Signals", "🔱 NIFTY Signals 📊"):
        send_message(chat_id, f"{greeting}🔄 *Analyzing NIFTY 50 — FULL POWER...* ⏳")
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
            
            # Get REAL spot price from NSE
            nse_spot_str = ""
            if NSE_LIVE_AVAILABLE:
                try:
                    spot_data = get_live_spot("NIFTY")
                    if spot_data.get("price", 0) > 0:
                        nse_spot_str = (
                            f"\n💹 *REAL NSE Price:* ₹{spot_data['price']:,.2f}"
                            f" ({'+' if spot_data.get('change', 0) >= 0 else ''}{spot_data.get('change', 0):,.2f},"
                            f" {'+' if spot_data.get('change_pct', 0) >= 0 else ''}{spot_data.get('change_pct', 0):.2f}%)"
                            f" _{spot_data.get('source', '')}_ ✅"
                        )
                except Exception:
                    pass
            
            decorated = (
                f"{greeting}"
                f"🔱 *NIFTY 50 — LIVE ANALYSIS* 🔱\n"
                f"{FIRE_LINE}{nse_spot_str}\n\n"
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
    #   SENSEX LIVE / BANKNIFTY LIVE — NUCLEAR: Real NSE/BSE Spot
    # ════════════════════════════
    if text in ("📊 SENSEX Live", "sensex live", "sensex price", "/sensexlive"):
        send_message(chat_id, f"{greeting}🔄 *SENSEX Live Data — REAL BSE...* ⏳")
        try:
            from candle_analyzer import analyze_index
            analysis = analyze_index("^BSESN", "SENSEX")
            sig_text = analysis["analysis"]
            signal = analysis.get("signal", "HOLD")
            conf = analysis.get("confidence", 0.5)
            sig_emoji = "🟢🚀" if signal == "BUY" else ("🔴📉" if signal == "SELL" else "🟡⚖️")
            nse_spot_str = ""
            if NSE_LIVE_AVAILABLE:
                try:
                    spot_data = get_live_spot("SENSEX")
                    if spot_data.get("price", 0) > 0:
                        nse_spot_str = f"\n💹 *REAL Price:* ₹{spot_data['price']:,.2f} _{spot_data.get('source', '')}_ ✅"
                except Exception:
                    pass
            decorated = (
                f"{greeting}"
                f"📊 *SENSEX — LIVE DATA* 📊\n"
                f"{FIRE_LINE}{nse_spot_str}\n\n"
                f"{sig_text}\n\n"
                f"{DIAMOND_LINE}\n"
                f"🎯 *Signal:* {sig_emoji} *{signal}*\n"
                f"📊 *Confidence:* {conf:.0%}\n"
                f"{STAR_LINE}"
            )
            send_message(chat_id, decorated, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, f"SENSEX live price aur signal {signal} hai, confidence {conf:.0%}.", intent="analysis")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ SENSEX live data fetch failed: {str(e)[:100]}")
        return

    if text in ("📊 BankNIFTY Live", "banknifty live", "banknifty price", "/bankniftylive"):
        send_message(chat_id, f"{greeting}🔄 *BankNIFTY Live Data fetch ho raha hai...* ⏳")
        try:
            from candle_analyzer import analyze_index
            analysis = analyze_index("^NSEBANK", "BANKNIFTY")
            sig_text = analysis["analysis"]
            signal = analysis.get("signal", "HOLD")
            conf = analysis.get("confidence", 0.5)
            sig_emoji = "🟢🚀" if signal == "BUY" else ("🔴📉" if signal == "SELL" else "🟡⚖️")
            nse_spot_str = ""
            if NSE_LIVE_AVAILABLE:
                try:
                    spot_data = get_live_spot("BANKNIFTY")
                    if spot_data.get("price", 0) > 0:
                        nse_spot_str = f"\n💹 *REAL Price:* ₹{spot_data['price']:,.2f} _{spot_data.get('source', '')}_ ✅"
                except Exception:
                    pass
            decorated = (
                f"{greeting}"
                f"🏦 *BANKNIFTY — LIVE DATA* 🏦\n"
                f"{FIRE_LINE}{nse_spot_str}\n\n"
                f"{sig_text}\n\n"
                f"{DIAMOND_LINE}\n"
                f"🎯 *Signal:* {sig_emoji} *{signal}*\n"
                f"📊 *Confidence:* {conf:.0%}\n"
                f"{STAR_LINE}"
            )
            send_message(chat_id, decorated, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, f"BankNIFTY live price aur signal {signal} hai, confidence {conf:.0%}.", intent="analysis")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ BankNIFTY live data fetch failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   OTM CALLS / PUTS (unified) — 🔥 NUCLEAR: REAL NSE DATA
    # ════════════════════════════
    otm_map = {
        "📞 NIFTY Calls OTM": ("NIFTY", "calls"),
        "💎 NIFTY Calls OTM 🚀": ("NIFTY", "calls"),
        "📞 SENSEX Calls OTM": ("SENSEX", "calls"),
        "💎 SENSEX Calls OTM 🚀": ("SENSEX", "calls"),
        "📞 NIFTY Puts OTM": ("NIFTY", "puts"),
        "⚡ NIFTY Puts OTM 📉": ("NIFTY", "puts"),
        "📞 SENSEX Puts OTM": ("SENSEX", "puts"),
        "⚡ SENSEX Puts OTM 📉": ("SENSEX", "puts"),
        "📞 BankNIFTY Calls OTM": ("BANKNIFTY", "calls"),
        "📞 BankNIFTY Puts OTM": ("BANKNIFTY", "puts"),
    }
    
    if text in otm_map:
        index_name, opt_type = otm_map[text]
        is_calls = opt_type == "calls"
        
        type_emoji = "🚀💎" if is_calls else "📉⚡"
        type_label = "CALLS" if is_calls else "PUTS"
        type_word = "CE" if is_calls else "PE"
        
        send_message(chat_id, f"{greeting}🔄 *Fetching {index_name} OTM {type_label} — REAL NSE DATA...* ⏳")
        
        try:
            if NSE_LIVE_AVAILABLE:
                # ═══ NUCLEAR: Real NSE Option Chain ═══
                analysis = get_atm_otm_analysis(index_name, budget=2000, direction="auto", num_strikes=6)
                
                if "error" not in analysis:
                    spot = analysis["spot"]
                    options = analysis["best_calls"] if is_calls else analysis["best_puts"]
                    # Filter only OTM options
                    otm_options = [o for o in options if o.get("moneyness") == "OTM"]
                    if not otm_options:
                        otm_options = options[:5]  # Show all if no pure OTM
                    
                    data_tag = "✅ REAL NSE" if analysis["is_real_data"] else "⚠️ Synthetic"
                    msg_parts = [
                        f"{greeting}",
                        f"{type_emoji} *{index_name} OTM {type_label} — HIGH LEVERAGE* {type_emoji}",
                        f"{FIRE_LINE}",
                        f"💹 *Spot:* ₹{spot:,.2f} | 📡 {data_tag}",
                        f"📊 *PCR:* {analysis['pcr']:.2f} | 🎯 *Max Pain:* ₹{analysis['max_pain']:,.0f}",
                        f"🛡️ *Support:* ₹{analysis['support']:,.0f} | 🚧 *Resistance:* ₹{analysis['resistance']:,.0f}",
                        f"📅 *Expiry:* {analysis['days_to_expiry']} days | Lot: {analysis['lot_size']}",
                        f"",
                    ]
                    
                    for i, opt in enumerate(otm_options[:5], 1):
                        medal = '🥇' if i == 1 else '🥈' if i == 2 else ('🥉' if i == 3 else f'#{i}')
                        moneyness = opt.get("moneyness", "OTM")
                        score = opt.get("score", 0)
                        
                        msg_parts.append(f"{medal} *₹{opt['strike']:,.0f} {type_word}* ({moneyness}) — Score: {score:.0f}/100")
                        msg_parts.append(f"  ┣ 💰 LTP: *₹{opt['ltp']:,.2f}* | Cost/Lot: ₹{opt['cost_per_lot']:,.0f}")
                        msg_parts.append(f"  ┣ 📊 IV: {opt['iv']:.1f}% | Delta: {opt['delta']:.3f}")
                        msg_parts.append(f"  ┣ 📈 OI: {opt['oi']:,} | Volume: {opt['volume']:,}")
                        
                        profits = opt.get("profits", {})
                        p1 = profits.get("1.0%", {})
                        p2 = profits.get("2.0%", {})
                        if p1:
                            msg_parts.append(f"  ┣ 📈 +1% move: ROI *{p1.get('roi', 0):+.0f}%* (₹{p1.get('profit', 0):+,.0f}/lot)")
                        if p2:
                            msg_parts.append(f"  ┗ 🚀 +2% move: ROI *{p2.get('roi', 0):+.0f}%* (₹{p2.get('profit', 0):+,.0f}/lot)")
                        msg_parts.append("")
                    
                    msg_parts.append(f"⚡ Straddle: ₹{analysis['straddle_premium']:,.2f}")
                    msg_parts.append(f"📐 Range: ₹{analysis['expected_range'][0]:,.0f} - ₹{analysis['expected_range'][1]:,.0f}")
                    msg_parts.append(f"{STAR_LINE}")
                    send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
                else:
                    send_message(chat_id, f"{greeting}❌ {analysis.get('error', 'Data unavailable')}", reply_markup=build_keyboard())
            else:
                # Fallback: old method
                data = fetch_nse_option_chain("TCS" if index_name == "NIFTY" else "RELIANCE")
                if data:
                    calls_df, puts_df, underlying = parse_option_chain_json(data)
                    otm = find_best_otm_options(calls_df, puts_df, underlying, option_type=opt_type, num_strikes=5)
                    msg_parts = [f"{greeting}", f"{type_emoji} *{index_name} OTM {type_label}*", f"💹 Price: ₹{underlying:.0f}"]
                    for i2, opt2 in enumerate(otm[:3], 1):
                        msg_parts.append(f"#{i2} Strike: ₹{opt2['strike']:.0f} | Premium: ₹{opt2['ltp']:.2f} | OI: {opt2['oi']:.0f}")
                    send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
                else:
                    send_message(chat_id, f"{greeting}❌ Option data unavailable. Try during market hours.", reply_markup=build_keyboard())
                
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

    # ════════════════════════════════════════════════════════
    #   🇮🇳 NIFTY SUPER BRAIN — All Indian Market Intelligence
    # ════════════════════════════════════════════════════════

    # --- NIFTY Super Dashboard (Master) ---
    if text in ("🇮🇳 NIFTY Super Dashboard 🧠", "nifty dashboard", "/niftydashboard",
                "nifty super dashboard", "market dashboard"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🇮🇳🧠 *Loading SUPER DASHBOARD...*\n_FII/DII + VIX + PCR + OI + Pivots 🔄_ ⏳")
            try:
                msg = get_complete_dashboard()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Dashboard error: {e}")
                send_message(chat_id, f"❌ Dashboard load error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Nifty Super Brain module unavailable.", reply_markup=build_keyboard())
        return

    # --- 🧠⚡ SUPER BRAIN AI ANALYSIS (FREE AI) ---
    if text.lower() in ("/superbrain", "super brain", "superbrain", "nifty brain", "ai analysis",
                         "brain analysis", "jarvis brain", "market brain"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, 
                f"{greeting}🧠⚡ *SUPER BRAIN ACTIVATING...*\n"
                f"_JARVIS AI + Multi-Factor Intelligence 🔄_ ⏳\n"
                f"_FII/DII + VIX + PCR + OI + AI Verdict..._")
            try:
                msg = get_super_brain_analysis()
                send_message(chat_id, msg, reply_markup=build_keyboard())
                send_jarvis_voice(chat_id, "Boss, Super Brain analysis complete. Screen pe dekh lo, full AI verdict di hai NIFTY aur market ki!", intent="market_summary")
            except Exception as e:
                logger.error(f"Super Brain AI error: {e}")
                # Fallback to regular dashboard
                try:
                    msg = get_complete_dashboard()
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                except Exception:
                    send_message(chat_id, f"❌ Super Brain error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Nifty Super Brain module unavailable.", reply_markup=build_keyboard())
        return

    # --- FII/DII Flow Data ---
    if text in ("🏛️ FII/DII Flow 📊", "fii dii", "/fiidii", "fii dii flow",
                "fii data", "dii data", "fii/dii"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🏛️ *Loading FII/DII data...* ⏳")
            try:
                msg = format_fii_dii()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"FII/DII error: {e}")
                send_message(chat_id, f"❌ FII/DII data error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # --- India VIX Fear Gauge ---
    if text in ("😱 India VIX Gauge 📊", "india vix", "/indiavix", "vix",
                "vix gauge", "fear gauge", "india vix gauge"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}😱 *Loading India VIX Fear Gauge...* ⏳")
            try:
                msg = format_india_vix()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"VIX error: {e}")
                send_message(chat_id, f"❌ VIX data error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # --- NIFTY PCR Dashboard ---
    if text in ("📊 NIFTY PCR 🔢", "nifty pcr", "/niftypcr", "pcr nifty", "pcr"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *Loading NIFTY PCR dashboard...* ⏳")
            try:
                msg = format_pcr_dashboard(index="NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"PCR error: {e}")
                send_message(chat_id, f"❌ PCR data error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # --- BankNIFTY PCR Dashboard ---
    if text in ("📊 BankNIFTY PCR 🔢", "banknifty pcr", "/bankniftypcr", "pcr banknifty"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *Loading BankNIFTY PCR...* ⏳")
            try:
                msg = format_pcr_dashboard(index="BANKNIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"BankNIFTY PCR error: {e}")
                send_message(chat_id, f"❌ PCR error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # --- NIFTY Pivot Levels ---
    if text in ("📐 NIFTY Pivot Levels 📊", "nifty pivots", "/niftypivots",
                "pivot levels", "pivot nifty", "nifty pivot"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}📐 *Calculating NIFTY Pivot Levels...* ⏳")
            try:
                msg = format_pivot_levels(index="NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Pivot error: {e}")
                send_message(chat_id, f"❌ Pivot error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # --- SENSEX Pivot Levels ---
    if text in ("📐 SENSEX Pivot Levels", "sensex pivots", "/sensexpivots", "pivot sensex"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}📐 *Calculating SENSEX Pivot Levels...* ⏳")
            try:
                msg = format_pivot_levels(index="SENSEX")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"SENSEX Pivot error: {e}")
                send_message(chat_id, f"❌ Pivot error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # --- GIFT NIFTY Gap Prediction ---
    if text in ("🌅 GIFT NIFTY Gap 📊", "gift nifty", "/giftnifty", "sgx nifty",
                "gift nifty gap", "gap prediction"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🌅 *Loading GIFT NIFTY / Gap Prediction...* ⏳")
            try:
                msg = format_gift_nifty()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"GIFT NIFTY error: {e}")
                send_message(chat_id, f"❌ GIFT NIFTY error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # --- OI Buildup Analysis ---
    if text in ("📊 OI Buildup Analysis", "oi buildup", "/oibuildup", "oi analysis",
                "open interest", "oi nifty"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *Analyzing OI Buildup...* ⏳")
            try:
                msg = format_oi_buildup(index="NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"OI error: {e}")
                send_message(chat_id, f"❌ OI analysis error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # --- Sector Rotation Heatmap ---
    if text in ("🏭 Sector Heatmap 📊", "sector heatmap", "/sectorheatmap",
                "sector rotation", "sectors", "nse sectors"):
        if NIFTY_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🏭 *Loading Sector Rotation Heatmap...*\n_11 sectors scanning..._ ⏳")
            try:
                msg = format_sector_heatmap()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Sector error: {e}")
                send_message(chat_id, f"❌ Sector data error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   🛑 STOP ALL CRYPTO ALERTS — Smart NLU matching
    # ════════════════════════════════════════════════════════
    _stop_exact = {
        "🛑 STOP All Crypto 🛑", "stop all crypto", "stop crypto",
        "/stopcrypto", "stop all crypto alerts", "stop alerts", "stop notification",
        "stop notifications", "stop all notifications", "stop all alerts",
        "stop all crypto notification", "stop all crypto notifications",
        "stop", "band karo", "alert band", "alerts off", "notifications off",
        "notification off", "alert off", "sab band karo", "sab band kar do",
        "band kar do", "band kardo", "alert band karo", "alert band kar do",
        "notification band karo", "notification band kar do",
        "notifications band karo", "notifications band kar do",
        "sab notifications band karo", "sab notification band kar do",
        "sab alert band karo", "sab kuch band karo", "sab kuch band kar do",
        "crypto band karo", "crypto band kar do", "airdrop band karo",
        "airdrop band kar do", "alert hatao", "notification hatao",
        "stop everything", "turn off alerts", "turn off notifications",
        "mute", "mute alerts", "mute all", "silence", "quiet",
        "no more alerts", "no alerts", "no notifications",
        "chup karo", "chup ho jao", "mat bhejo", "mat bhejna",
        "alert mat bhejo", "notification mat bhejo", "kuch mat bhejo",
    }
    # Smart regex patterns for Hindi/English/Hinglish stop intent
    _stop_patterns = [
        r'(?:sab|all|सब|सारे?|sabhi|सभी).*(?:band|बंद|stop|off|hatao|हटाओ)',
        r'(?:band|बंद|stop|off).*(?:karo|kar do|करो|कर दो|kar|करें)',
        r'(?:notification|alert|नोटिफिकेशन|अलर्ट).*(?:band|बंद|stop|off|hatao|हटाओ|mat|मत)',
        r'(?:band|बंद).*(?:notification|alert|नोटिफिकेशन|अलर्ट|crypto|airdrop|dextools)',
        r'(?:mat|मत).*(?:bhej|भेज|send)',
        r'(?:stop|रोक|बंद).*(?:crypto|airdrop|dextools|web3|notification|alert)',
        r'(?:airdrop|dextools|crypto|web3).*(?:stop|band|बंद|off|hatao|हटाओ)',
        r'(?:chup|चुप|silence|quiet|mute).*(?:karo|करो|kar|ho)',
    ]
    _text_lower = text.lower().strip()
    _is_stop = _text_lower in _stop_exact
    if not _is_stop:
        for pat in _stop_patterns:
            if re.search(pat, _text_lower, re.IGNORECASE):
                _is_stop = True
                break
    if _is_stop:
        # ══════════════════════════════════════════════════════
        #  🛑 STOP CRYPTO ALERTS ONLY
        #  Background threads keep running! Only crypto notifications OFF
        #  Market Brain notifications remain unaffected
        # ══════════════════════════════════════════════════════
        # Stop crypto-specific alerts
        if OPTIONS_HUNTER_AVAILABLE:
            try:
                stop_all_crypto_alerts(chat_id)
            except Exception:
                pass
        # Set in-memory CRYPTO flag only
        chat_storage[f"crypto_alerts_{chat_id}"] = False
        # Remove from crypto subscriber list
        try:
            from data_store import remove_subscriber
            remove_subscriber(chat_id)
        except Exception:
            pass
        # L1: Persist stop flag atomically + update cache
        set_user_stopped(chat_id, True)
        send_message(chat_id, 
            f"🛑 *Crypto Alerts बंद!*\n\n"
            f"❌ Crypto alerts: *OFF*\n"
            f"❌ Airdrop notifications: *OFF*\n"
            f"❌ DexTools alerts: *OFF*\n"
            f"❌ Web3 signals: *OFF*\n\n"
            f"✅ Background threads: *RUNNING*\n"
            f"✅ Market Brain: *RUNNING* (9:15-3:30 IST)\n"
            f"✅ JARVIS AI: *ACTIVE*\n\n"
            f"_\"🟢 START Crypto Alerts\" दबाइए वापस शुरू करने के लिए_",
            reply_markup=build_keyboard())
        logger.info(f"[STOP] 🛑 User {chat_id} STOPPED crypto alerts (bg threads still running)")
        return

    # ════════════════════════════════════════════════════════
    #   🟢 START All Crypto Alerts — Smart NLU matching
    # ════════════════════════════════════════════════════════
    _start_exact = {
        "🟢 START Crypto Alerts", "start crypto", "/startcrypto",
        "start all crypto alerts", "start alerts", "alerts on",
        "start", "shuru karo", "alert chalu", "notifications on",
        "notification on", "alert on", "start notifications",
        "start all alerts", "start all notifications",
        "chalu karo", "chalu kar do", "shuru kar do",
        "alert shuru karo", "notification shuru karo",
        "alert chalu karo", "notification chalu karo",
        "sab chalu karo", "sab shuru karo",
    }
    _start_patterns = [
        r'(?:sab|all|सब|सारे?|sabhi|सभी).*(?:chalu|shuru|start|on|चालू|शुरू)',
        r'(?:chalu|shuru|start|on|चालू|शुरू).*(?:karo|kar do|करो|कर दो)',
        r'(?:notification|alert|नोटिफिकेशन|अलर्ट).*(?:chalu|shuru|start|on|चालू|शुरू)',
    ]
    _is_start = _text_lower in _start_exact
    if not _is_start:
        for pat in _start_patterns:
            if re.search(pat, _text_lower, re.IGNORECASE):
                _is_start = True
                break
    if _is_start:
        # ══════════════════════════════════════════════════════
        #  🟢 START CRYPTO ALERTS
        # ══════════════════════════════════════════════════════
        if OPTIONS_HUNTER_AVAILABLE:
            try:
                start_all_crypto_alerts(chat_id)
            except Exception:
                pass
        chat_storage[f"crypto_alerts_{chat_id}"] = True
        # Re-add to subscriber list
        try:
            from data_store import add_subscriber
            add_subscriber(chat_id)
        except Exception:
            pass
        # L1: Remove from stopped users cache + persist atomically
        set_user_stopped(chat_id, False)
        send_message(chat_id, 
            f"🟢 *Crypto Alerts शुरू!*\n\n"
            f"✅ Crypto alerts: *ON*\n"
            f"✅ Airdrop notifications: *ON*\n"
            f"✅ DexTools alerts: *ON*\n"
            f"✅ Web3 signals: *ON*\n"
            f"✅ Market Brain: *RUNNING* (9:15-3:30 IST)\n"
            f"✅ All background threads: *RUNNING*",
            reply_markup=build_keyboard())
        logger.info(f"[START] 🟢 User {chat_id} STARTED crypto alerts")
        return

    # ════════════════════════════════════════════════════════
    #   💰 BUDGET OPTIONS HUNTER — ₹4-5 Options
    # ════════════════════════════════════════════════════════
    if text in ("💰 Budget Options 🎯", "budget options", "/budgetoptions",
                "budget calls", "₹5 options", "cheap options", "saste options"):
        if OPTIONS_HUNTER_AVAILABLE:
            send_message(chat_id, f"{greeting}💰🎯 *BUDGET OPTIONS HUNT...*\n_₹4-8 ke options dhundh raha hoon + ML/AI analysis_ ⏳")
            try:
                data = find_budget_options(index="NIFTY", direction="AUTO")
                msg = format_budget_options(data)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Budget options error: {e}")
                send_message(chat_id, f"❌ Budget options error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Options Hunter module unavailable.", reply_markup=build_keyboard())
        return

    if text in ("💰 BankNIFTY Budget 🎯", "banknifty budget", "banknifty budget options"):
        if OPTIONS_HUNTER_AVAILABLE:
            send_message(chat_id, f"{greeting}💰🏦 *BankNIFTY BUDGET HUNT...* ⏳")
            try:
                data = find_budget_options(index="BANKNIFTY", direction="AUTO")
                msg = format_budget_options(data)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   🔔 9 AM MORNING PICKS
    # ════════════════════════════════════════════════════════
    if text in ("🔔 9AM Auto Picks 🌅", "9am picks", "/morningpicks",
                "morning picks", "auto picks", "9 am picks"):
        if OPTIONS_HUNTER_AVAILABLE:
            send_message(chat_id, f"{greeting}🔔🌅 *Generating Morning Picks...*\n_NIFTY + BankNIFTY budget options_ ⏳")
            try:
                msg = generate_morning_picks()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Morning picks error: {e}")
                send_message(chat_id, f"❌ Morning picks error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   🛡️ MY POSITIONS (Enhanced with Guardian)
    # ════════════════════════════════════════════════════════
    if text in ("🛡️ My Positions Guard", "my positions guard", "position guardian",
                "/mypositions", "position status"):
        if OPTIONS_HUNTER_AVAILABLE:
            send_message(chat_id, f"{greeting}🛡️ *Loading Positions + Guardian...* ⏳")
            try:
                msg = get_my_positions_enhanced(chat_id)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   /track — Track a new position
    # ════════════════════════════════════════════════════════
    if text.startswith("/track") or text.startswith("track "):
        if OPTIONS_HUNTER_AVAILABLE:
            # Parse: /track NIFTY 23000CE 5
            parts = text.replace("/track", "").strip().split()
            if len(parts) >= 3:
                try:
                    index = parts[0].upper()
                    strike_str = parts[1].upper()
                    entry_price = float(parts[2])
                    
                    # Parse strike+type (e.g., 23000CE)
                    opt_type = "CE" if "CE" in strike_str else "PE"
                    strike = float(strike_str.replace("CE", "").replace("PE", ""))
                    
                    qty = int(parts[3]) if len(parts) > 3 else 0
                    
                    result = track_position(chat_id, index, strike, opt_type, entry_price, qty)
                    if "error" in result:
                        send_message(chat_id, f"❌ {result['error']}", reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, result["msg"], reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ Parse error: {str(e)[:100]}\n\n💡 Format: /track NIFTY 23000CE 5", reply_markup=build_keyboard())
            else:
                send_message(chat_id, (
                    "📝 *Position Track karne ka format:*\n\n"
                    "`/track NIFTY 23000CE 5`\n"
                    "`/track BANKNIFTY 50000PE 8`\n"
                    "`/track SENSEX 75000CE 4`\n\n"
                    "📊 Format: /track [INDEX] [STRIKE][CE/PE] [ENTRY_PRICE]\n"
                    "🛡️ Guardian auto-activate hoga!\n"
                ), reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   /close — Close a tracked position
    # ════════════════════════════════════════════════════════
    if text.startswith("/close"):
        if OPTIONS_HUNTER_AVAILABLE:
            parts = text.replace("/close", "").strip().split()
            if len(parts) >= 2:
                try:
                    pos_id = int(parts[0])
                    exit_price = float(parts[1])
                    msg = close_tracked_position(chat_id, pos_id, exit_price)
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ Error: {str(e)[:100]}\n\n💡 Format: /close [ID] [EXIT_PRICE]", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "💡 Format: /close [POSITION_ID] [EXIT_PRICE]\nEx: /close 1 25", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   🧠� SUPER MEMORY — Tracked Positions + Memory Status
    # ════════════════════════════════════════════════════════════

    if text in ("📊 My Tracked Positions", "my tracked positions", "tracked positions",
                "meri positions", "meri position", "position status", "/tracked"):
        if MEMORY_PRO_AVAILABLE:
            msg = format_positions(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
            
            # Update live prices for all open positions
            active = get_active_positions(chat_id)
            if active and OPTIONS_PRO_AVAILABLE:
                try:
                    from jarvis_options_pro import get_strike_price as _gsp3
                    for pos in active:
                        _live = _gsp3(pos["symbol"], pos["strike"], pos["option_type"])
                        if _live and not _live.get("error"):
                            update_position_price(chat_id, pos["id"], _live["ltp"],
                                f"{_live.get('recommendation', '')} | IV:{_live.get('iv',0):.0f}%")
                    # Resend with updated prices
                    msg2 = format_positions(chat_id)
                    if msg2 != msg:
                        send_message(chat_id, f"📊 *LIVE UPDATED:*\n{msg2}", reply_markup=build_keyboard())
                except:
                    pass
            
            # Voice
            try:
                from voice_engine import generate_voice
                _vt = format_position_voice(active if MEMORY_PRO_AVAILABLE else [])
                _vf = generate_voice(_vt)
                if _vf:
                    send_voice(chat_id, _vf)
            except:
                pass
        else:
            send_message(chat_id, "❌ Memory module unavailable.", reply_markup=build_keyboard())
        return

    if text in ("🧠 Memory Status", "memory status", "jarvis memory", "/memory"):
        if MEMORY_PRO_AVAILABLE:
            msg = format_memory_stats(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Memory module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   📊 CHART ENGINE — Professional Trading Charts
    # ════════════════════════════════════════════════════════════

    if text in ("📊 Live Charts 📈", "live charts", "charts", "/chart") or \
       re.search(r'chart\s*(dikhao|dikha|show|draw|plot|bana)', text.lower()) or \
       re.search(r'(dikhao|dikha|show)\s*chart', text.lower()) or \
       re.search(r'^(reliance|tcs|infy|nifty|sensex|banknifty|sbin|tatamotors|hdfcbank|icicibank|itc|wipro|btc|eth|sol)\s*(chart|graph)', text.lower()):
        if CHART_ENGINE_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *Chart Engine loading...*\n_Generating professional chart_ ⏳")
            try:
                chart_path, analysis = handle_chart_command(text)
                if chart_path and os.path.exists(chart_path):
                    with open(chart_path, 'rb') as f:
                        files = {'photo': f}
                        data_payload = {'chat_id': chat_id, 'caption': f"📊 {text.upper()[:50]}", 'parse_mode': 'Markdown'}
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                                    data=data_payload, files=files, timeout=30)
                    send_message(chat_id, analysis, reply_markup=build_keyboard())
                    cleanup_old_charts()
                else:
                    send_message(chat_id, analysis, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Chart error: {e}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Chart Engine unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   🔍 SCREENER PRO — Smart Stock Screener
    # ════════════════════════════════════════════════════════════

    if text in ("🔍 Smart Screener 🔎", "smart screener", "screener", "stock screener", "/screener"):
        if SCREENER_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍 *Screener Pro scanning 90+ stocks...*\n⏳ _Please wait..._")
            msg = screen_top_momentum()
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Screener unavailable.", reply_markup=build_keyboard())
        return

    if re.search(r'(screen|scan|filter|screener|dikhao).*(rsi|volume|oversold|overbought|gap|momentum|52.*week|bullish|breakout)', text.lower()) or \
       re.search(r'(rsi|volume|oversold|overbought|gap|momentum|52.*week|bullish|breakout).*(screen|scan|filter|stocks|dikhao)', text.lower()):
        if SCREENER_AVAILABLE:
            send_message(chat_id, f"{greeting}🔍 *Running custom screen...*\n⏳")
            msg = run_screener(text)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Screener unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   📰 NEWS BRAIN — Real-Time Market News
    # ════════════════════════════════════════════════════════════

    if text in ("📰 Market News 📰", "market news", "latest news", "news", "koi news",
                "breaking news", "kya news hai", "/news"):
        if NEWS_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}📰 *Fetching latest news...*\n⏳")
            msg = get_latest_news(10)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ News Brain unavailable.", reply_markup=build_keyboard())
        return

    if re.search(r'(news|khabar).*(reliance|tcs|infy|hdfc|icici|sbin|tata|adani|nifty|sensex)', text.lower()) or \
       re.search(r'(reliance|tcs|infy|hdfc|icici|sbin|tata|adani)\s*(ki|ka|news|khabar)', text.lower()):
        if NEWS_BRAIN_AVAILABLE:
            stock_match = re.search(r'(reliance|tcs|infy|hdfcbank|icicibank|sbin|tatamotors|adanient|nifty|sensex|wipro|itc)', text.lower())
            stock = stock_match.group(1).upper() if stock_match else "NIFTY"
            send_message(chat_id, f"📰 *Fetching {stock} news...*\n⏳")
            msg = get_stock_news(stock)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ News Brain unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   🔬 BACKTESTER PRO — Strategy Backtesting
    # ════════════════════════════════════════════════════════════

    if text in ("🔬 Backtester Pro 🔬", "backtester", "backtest", "/backtest"):
        if BACKTESTER_AVAILABLE:
            send_message(chat_id, f"{greeting}🔬 *Running RSI Backtest on NIFTY (1 year)...*\n⏳")
            msg = backtest_rsi_strategy("NIFTY", "1y")
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Backtester unavailable.", reply_markup=build_keyboard())
        return

    if re.search(r'backtest.*(rsi|macd|bollinger|ema|sma|strategy)', text.lower()) or \
       re.search(r'(rsi|macd|bollinger).*(backtest|test|check|karo)', text.lower()):
        if BACKTESTER_AVAILABLE:
            send_message(chat_id, f"{greeting}🔬 *Running backtest...*\n⏳ _Analyzing historical data..._")
            msg = handle_backtest_command(text)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Backtester unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   📋 P&L JOURNAL — Trade Journal
    # ════════════════════════════════════════════════════════════

    if text in ("📋 P&L Journal 📋", "pnl journal", "trade journal", "journal", "my pnl",
                "aaj ka pnl", "/journal", "/pnl"):
        if PNL_JOURNAL_AVAILABLE:
            msg = format_overall_stats(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Journal unavailable.", reply_markup=build_keyboard())
        return

    if text.lower() in ("daily pnl", "aaj ka pnl", "today pnl", "/dailypnl"):
        if PNL_JOURNAL_AVAILABLE:
            msg = format_daily_pnl(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    if text.lower() in ("weekly pnl", "hafta pnl", "week pnl", "/weeklypnl"):
        if PNL_JOURNAL_AVAILABLE:
            msg = format_weekly_pnl(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    if text.lower() in ("monthly pnl", "mahina pnl", "month pnl", "/monthlypnl"):
        if PNL_JOURNAL_AVAILABLE:
            msg = format_monthly_pnl(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   ⚡ INTRADAY SCANNER — Real-Time Breakouts
    # ════════════════════════════════════════════════════════════

    if text in ("⚡ Intraday Scanner ⚡", "intraday scanner", "breakout scanner", "scanner",
                "intraday scan", "breakouts", "/intraday"):
        if INTRADAY_SCANNER_AVAILABLE:
            send_message(chat_id, f"{greeting}⚡ *Intraday Scanner running...*\n_Scanning 50+ stocks for breakouts_ ⏳")
            msg = run_intraday_scan()
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Intraday Scanner unavailable.", reply_markup=build_keyboard())
        return

    if text.lower() in ("volume spike", "volume alert", "volume breakout", "/volumespike"):
        if INTRADAY_SCANNER_AVAILABLE:
            send_message(chat_id, f"🔥 *Scanning volume spikes...*\n⏳")
            msg = scan_volume_spikes()
            send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    if text in ("🚀 Top Movers 🚀", "top movers", "biggest movers", "top gainers losers", "/movers"):
        if INTRADAY_SCANNER_AVAILABLE:
            msg = scan_momentum()
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Scanner unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   📊 FUTURES BRAIN — PCR + Max Pain + Basis
    # ════════════════════════════════════════════════════════════

    if text in ("📊 Futures Brain 📊", "futures brain", "futures dashboard", "futures analysis",
                "pcr max pain", "/futures"):
        if FUTURES_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *Futures Brain loading...*\n_PCR + Max Pain + Basis + VIX_ ⏳")
            msg = get_futures_dashboard("NIFTY")
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Futures Brain unavailable.", reply_markup=build_keyboard())
        return

    if re.search(r'\bpcr\b', text.lower()) or text.lower() in ("put call ratio", "pcr ratio", "/pcr"):
        if FUTURES_BRAIN_AVAILABLE:
            symbol = "BANKNIFTY" if "bank" in text.lower() else "NIFTY"
            msg = format_pcr(symbol)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    if re.search(r'max\s*pain', text.lower()) or text.lower() in ("/maxpain",):
        if FUTURES_BRAIN_AVAILABLE:
            symbol = "BANKNIFTY" if "bank" in text.lower() else "NIFTY"
            msg = format_max_pain(symbol)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    if text.lower() in ("vix", "india vix", "/vix"):
        if FUTURES_BRAIN_AVAILABLE:
            msg = format_vix()
            send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   🧠�🔥 NUCLEAR TRADER BRAIN — Full Market Intelligence
    # ════════════════════════════════════════════════════════════

    if text in ("🧠🔥 Nuclear Brain 🔥", "nuclear brain", "super brain", "trader brain",
                "nuclear trader", "conquer brain", "pro brain", "/brain"):
        if SUPER_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🧠🔥 *NUCLEAR TRADER BRAIN loading...*\n_Sabhi data sources combine ho rahe hain_ ⏳")
            try:
                # NIFTY nuclear view
                nifty_data = get_nuclear_market_view("NIFTY")
                if nifty_data:
                    msg = format_nuclear_view(nifty_data)
                    send_message(chat_id, msg, reply_markup=build_keyboard())

                    # Voice response
                    try:
                        from voice_engine import generate_voice
                        voice_text = format_nuclear_voice(nifty_data)
                        voice_file = generate_voice(voice_text)
                        if voice_file:
                            send_voice(chat_id, voice_file)
                    except:
                        pass
                else:
                    send_message(chat_id, "❌ Nuclear brain data nahi mila. Market hours check karein.", reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Nuclear brain error: {e}")
                send_message(chat_id, f"❌ Nuclear brain error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Nuclear Trader Brain module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   ⚡🎯 STRIKE PRICE PRO — Real-time NSE Option Strike Prices
    # ════════════════════════════════════════════════════════════

    # Auto-detect: "nifty 25950 call", "26000 pe kya hai", etc.
    _strike_query = None
    if OPTIONS_PRO_AVAILABLE:
        _strike_query = parse_option_query(text)
    
    if text == "⚡ Strike Price Pro 🎯" or _strike_query:
        if OPTIONS_PRO_AVAILABLE:
            if _strike_query:
                sym = _strike_query["symbol"]
                strike = _strike_query["strike"]
                opt = _strike_query["option_type"]
                send_message(chat_id, f"{greeting}⚡ *{sym} {strike} {opt} — LIVE PRICE loading...* 🎯\n_Real-time NSE data fetch ho raha hai_ ⏳")
                try:
                    data = get_strike_price(sym, strike, opt)
                    if data:
                        msg = format_strike_result(data)
                        send_message(chat_id, msg, reply_markup=build_keyboard())
                        # Voice response
                        voice_text = format_strike_voice(data)
                        try:
                            from voice_engine import generate_voice
                            voice_file = generate_voice(voice_text)
                            if voice_file:
                                send_voice(chat_id, voice_file)
                        except:
                            pass
                    else:
                        send_message(chat_id, f"❌ {sym} {strike} {opt} ka data nahi mila. Market timing check karein (9:15 AM - 3:30 PM).", reply_markup=build_keyboard())
                except Exception as e:
                    logger.error(f"Strike price error: {e}")
                    send_message(chat_id, f"❌ Strike price error: {str(e)[:200]}", reply_markup=build_keyboard())
            else:
                # No specific strike — show nearby options
                send_message(chat_id, f"{greeting}📊 *NIFTY Live Option Chain loading...* ⏳")
                try:
                    nearby = get_nearby_options("NIFTY", 10)
                    if nearby and len(nearby) > 0:
                        msg = format_nearby_options(nearby)
                        send_message(chat_id, msg, reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, "❌ No nearby options available right now. Market may be closed or data unavailable.", reply_markup=build_keyboard())
                except Exception as e:
                    logger.error(f"Nearby options error: {e}")
                    send_message(chat_id, f"❌ Error loading nearby options: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Options Pro module unavailable.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════════
    #   🔥🧠 OI + TRAP BRAIN — NIFTY/SENSEX Options Intelligence
    # ════════════════════════════════════════════════════════════

    # 1. OI Trap Analysis
    if text in ("🧠 OI Trap Analysis 🔥", "oi trap analysis", "trap analysis",
                "oi trap", "/oitrap", "bull trap", "bear trap"):
        if OI_TRAP_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🧠🔥 *OI TRAP ANALYSIS loading...*\n_Bull Trap / Bear Trap / Range Trap detect ho raha hai_ ⏳")
            try:
                msg = format_trap_analysis("NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                # Also send SENSEX
                msg2 = format_trap_analysis("SENSEX")
                send_message(chat_id, msg2, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"OI Trap error: {e}")
                send_message(chat_id, f"❌ OI Trap Analysis error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ OI Trap Brain module unavailable.", reply_markup=build_keyboard())
        return

    # 2. Live Option Chain — NUCLEAR: Use NSE Live Engine first
    if text in ("📊 Live Option Chain 📈", "live option chain", "option chain",
                "/optionchain", "live chain", "nifty chain"):
        send_message(chat_id, f"{greeting}📊📈 *LIVE OPTION CHAIN loading...*\n_NSE se real-time data fetch ho raha hai_ ⏳")
        try:
            chain_sent = False
            # Try NSE Live Engine FIRST (real data)
            if NSE_LIVE_AVAILABLE:
                chain = fetch_live_option_chain("NIFTY")
                if chain and chain.strikes:
                    msg = format_option_chain_telegram(chain, num_strikes=12)
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                    chain_sent = True
            # Fallback: OI Trap Brain
            if not chain_sent and OI_TRAP_BRAIN_AVAILABLE:
                msg = format_live_chain("NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                chain_sent = True
            if not chain_sent:
                send_message(chat_id, "❌ Option Chain modules unavailable.", reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Live chain error: {e}")
            send_message(chat_id, f"❌ Option Chain error: {str(e)[:150]}", reply_markup=build_keyboard())
        return

    # 3. NIFTY Strike Map
    if text in ("🎯 NIFTY Strike Map 📊", "nifty strike map", "nifty oi map",
                "/niftymap", "nifty support resistance"):
        if OI_TRAP_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🎯📊 *NIFTY OI STRIKE MAP...*\n_Support/Resistance from live OI_ ⏳")
            try:
                msg = format_strike_map("NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"NIFTY strike map error: {e}")
                send_message(chat_id, f"❌ Strike Map error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # 4. SENSEX Strike Map
    if text in ("🎯 SENSEX Strike Map 📊", "sensex strike map", "sensex oi map",
                "/sensexmap", "sensex support resistance", "sensex chain"):
        if OI_TRAP_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🎯📊 *SENSEX OI STRIKE MAP...*\n_BSE se data fetch ho raha hai_ ⏳")
            try:
                msg = format_strike_map("SENSEX")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"SENSEX strike map error: {e}")
                send_message(chat_id, f"❌ SENSEX Map error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # 5. Max Pain Live
    if text in ("📉 Max Pain Live 🎯", "max pain", "max pain live",
                "/maxpain", "max pain nifty"):
        if OI_TRAP_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}📉🎯 *MAX PAIN ANALYSIS...*\n_Real OI se calculate ho raha hai_ ⏳")
            try:
                msg = format_max_pain("NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                msg2 = format_max_pain("SENSEX")
                send_message(chat_id, msg2, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Max pain error: {e}")
                send_message(chat_id, f"❌ Max Pain error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # 6. OI Change Tracker
    if text in ("🔄 OI Change Tracker 📊", "oi change tracker", "oi change",
                "/oichange", "oi movement", "smart money"):
        if OI_TRAP_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🔄📊 *OI CHANGE TRACKER...*\n_Smart money movement detect ho raha hai_ ⏳")
            try:
                msg = format_oi_change("NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"OI change error: {e}")
                send_message(chat_id, f"❌ OI Change error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # 7. Straddle Premium
    if text in ("⚡ Straddle Premium 📊", "straddle premium", "atm straddle",
                "/straddle", "expected range", "straddle"):
        if OI_TRAP_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}⚡📊 *ATM STRADDLE PREMIUM...*\n_Expected range calculate ho raha hai_ ⏳")
            try:
                msg = format_straddle_premium("NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                msg2 = format_straddle_premium("SENSEX")
                send_message(chat_id, msg2, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Straddle error: {e}")
                send_message(chat_id, f"❌ Straddle error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Module unavailable.", reply_markup=build_keyboard())
        return

    # 8. Options Super Signal (THE ULTIMATE)
    if text in ("🧠 Options Super Signal", "options super signal", "super signal",
                "/supersignal", "best option", "kya buy karu", "call ya put",
                "option signal", "nifty signal", "sensex signal"):
        if OI_TRAP_BRAIN_AVAILABLE:
            send_message(chat_id, f"{greeting}🧠🔥 *OPTIONS SUPER SIGNAL...*\n_NIFTY + SENSEX ka ultimate verdict aa raha hai_ ⏳")
            try:
                msg = format_super_signal("NIFTY")
                send_message(chat_id, msg, reply_markup=build_keyboard())
                msg2 = format_super_signal("SENSEX")
                send_message(chat_id, msg2, reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"Super signal error: {e}")
                send_message(chat_id, f"❌ Super Signal error: {str(e)[:150]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ OI Trap Brain module unavailable.", reply_markup=build_keyboard())
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
            send_photo(chat_id, qr, caption=caption, reply_markup=build_keyboard())
            send_message(chat_id, f"{greeting}✅ QR Code बन गया! अपने दोस्तों को शेयर कीजिए 🌸", reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"QR failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ QR Code generation failed. Please try again.", reply_markup=build_keyboard())
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
            
            track_qr_session(chat_id, "solana_pay", QR_OWNER_WALLET if QR_WALLET_AVAILABLE else "unknown")
            
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
    #   ML PREDICTIONS — L3: Tracked for accuracy
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
            
            # L3: Track prediction for accuracy measurement
            if PREDICTION_TRACKER_AVAILABLE and pred and "error" not in str(pred):
                try:
                    record_prediction(
                        symbol=name.replace(" 50", ""),
                        direction=pred.get("direction", "NEUTRAL"),
                        confidence=pred.get("confidence", 0.5),
                        current_price=pred.get("current_price", 0),
                        target_price=pred.get("target", 0),
                        stop_loss=pred.get("stop_loss", 0),
                        model_name="ml_ensemble",
                        timeframe="1d",
                        source="ml_predictor",
                        chat_id=chat_id,
                    )
                except Exception:
                    pass
            
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
            
            # Add REAL NSE prices if available
            if NSE_LIVE_AVAILABLE:
                try:
                    spot_data = get_live_spot(name.replace(" 50", ""))
                    if spot_data.get("price", 0) > 0:
                        msg += f"\n\n💹 *REAL SPOT:* ₹{spot_data['price']:,.2f} _{spot_data.get('source', '')}_ ✅"
                except Exception:
                    pass
            
            send_message(chat_id, f"{greeting}\n{msg}", reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"ML predict failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ ML prediction failed: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   🎯 PREDICTION ACCURACY REPORT — L3
    # ════════════════════════════
    if text in ("🎯 Prediction Accuracy", "prediction accuracy", "/accuracy",
                "accuracy report", "kitna sahi predict kiya", "prediction record"):
        if PREDICTION_TRACKER_AVAILABLE:
            send_message(chat_id, f"{greeting}🎯 *Generating accuracy report...* ⏳")
            try:
                # Verify latest predictions first
                verify_predictions()
                report = get_accuracy_report(days=30)
                msg = format_accuracy_report(report)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"{greeting}❌ Accuracy report failed: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, f"{greeting}❌ Prediction Tracker not loaded.", reply_markup=build_keyboard())
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
    #  🇮🇳⚡ NIFTY CALL/PUT AI — Super Engine ATM/OTM + REAL NSE
    # ════════════════════════════════════════════════════
    if text in ("🇮🇳⚡ NIFTY Call/Put AI", "nifty call put", "nifty call", "nifty put",
                "nifty option", "nifty atm", "nifty otm", "/niftyoption"):
        if SUPER_ENGINE_AVAILABLE or NSE_LIVE_AVAILABLE:
            send_message(chat_id, f"{greeting}🇮🇳⚡ *NIFTY Call/Put AI chal raha hai...*\n_ATM/OTM + REAL NSE Prices + Greeks + ML... ~30s_ ⏳")
            try:
                # Page 1: Super Engine Analysis
                if SUPER_ENGINE_AVAILABLE:
                    data = recommend_best_options("NIFTY", 2000.0, "auto")
                    wrapper = {
                        'timestamp': datetime.now(IST).strftime("%I:%M %p IST"),
                        'sections': {'nifty_options': data},
                    }
                    pages = format_super_analysis(wrapper)
                    for page in pages:
                        send_message(chat_id, page, reply_markup=build_keyboard())
                    comparison = format_option_comparison(wrapper, "NIFTY")
                    if comparison and len(comparison) > 50:
                        send_message(chat_id, comparison, reply_markup=build_keyboard())
                
                # Page 2: REAL NSE Option Prices (NUCLEAR UPGRADE)
                if NSE_LIVE_AVAILABLE:
                    nse_analysis = get_atm_otm_analysis("NIFTY", budget=2000, direction="auto", num_strikes=6)
                    if "error" not in nse_analysis:
                        ce_msg = format_atm_otm_analysis(nse_analysis, "CE")
                        pe_msg = format_atm_otm_analysis(nse_analysis, "PE")
                        send_message(chat_id, ce_msg, reply_markup=build_keyboard())
                        send_message(chat_id, pe_msg, reply_markup=build_keyboard())
                
                if VOICE_AVAILABLE:
                    try:
                        if SUPER_ENGINE_AVAILABLE:
                            voice_text = format_super_voice(wrapper)
                        else:
                            voice_text = "NIFTY option chain analysis complete. Real NSE prices bata diye hain ji!"
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
    #  📊 SENSEX CALL/PUT AI — Super Engine + REAL NSE
    # ════════════════════════════════════════════════════
    if text in ("📊 SENSEX Call/Put AI", "sensex call put", "sensex call", "sensex put",
                "sensex option", "sensex atm", "sensex otm", "/sensexoption"):
        if SUPER_ENGINE_AVAILABLE or NSE_LIVE_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *SENSEX Call/Put AI chal raha hai...*\n_ATM/OTM + REAL BSE Prices + Greeks... ~30s_ ⏳")
            try:
                if SUPER_ENGINE_AVAILABLE:
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
                
                # REAL NSE/BSE Data
                if NSE_LIVE_AVAILABLE:
                    nse_analysis = get_atm_otm_analysis("SENSEX", budget=2000, direction="auto", num_strikes=6)
                    if "error" not in nse_analysis:
                        ce_msg = format_atm_otm_analysis(nse_analysis, "CE")
                        pe_msg = format_atm_otm_analysis(nse_analysis, "PE")
                        send_message(chat_id, ce_msg, reply_markup=build_keyboard())
                        send_message(chat_id, pe_msg, reply_markup=build_keyboard())
                
                if VOICE_AVAILABLE:
                    try:
                        voice_text = format_super_voice(wrapper) if SUPER_ENGINE_AVAILABLE else "SENSEX option analysis complete!"
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
    #  🏦 BANKNIFTY CALL/PUT AI — Super Engine + REAL NSE
    # ════════════════════════════════════════════════════
    if text in ("🏦 BankNIFTY Call/Put AI", "banknifty call put", "banknifty call", "banknifty put",
                "bank nifty option", "bank nifty call", "bank nifty put", "/bankniftyoption"):
        if SUPER_ENGINE_AVAILABLE or NSE_LIVE_AVAILABLE:
            send_message(chat_id, f"{greeting}🏦 *BankNIFTY Call/Put AI chal raha hai...*\n_ATM/OTM + REAL NSE Prices + Greeks + ML... ~30s_ ⏳")
            try:
                if SUPER_ENGINE_AVAILABLE:
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
                
                # REAL NSE Data
                if NSE_LIVE_AVAILABLE:
                    nse_analysis = get_atm_otm_analysis("BANKNIFTY", budget=2000, direction="auto", num_strikes=6)
                    if "error" not in nse_analysis:
                        ce_msg = format_atm_otm_analysis(nse_analysis, "CE")
                        pe_msg = format_atm_otm_analysis(nse_analysis, "PE")
                        send_message(chat_id, ce_msg, reply_markup=build_keyboard())
                        send_message(chat_id, pe_msg, reply_markup=build_keyboard())
                
                if VOICE_AVAILABLE:
                    try:
                        voice_text = format_super_voice(wrapper) if SUPER_ENGINE_AVAILABLE else "BankNIFTY option chain analysis complete!"
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
    #  🔮 POWER PREDICT — 10-Signal Multi-Factor Prediction
    # ════════════════════════════════════════════════════
    power_predict_map = {
        "🔮 NIFTY Power Predict 💪": "NIFTY",
        "🔮 SENSEX Power Predict 💪": "SENSEX",
        "nifty power": "NIFTY",
        "sensex power": "SENSEX",
        "banknifty power": "BANKNIFTY",
        "/powerpredict": "NIFTY",
    }
    if text in power_predict_map:
        idx_name = power_predict_map[text]
        if POWER_PREDICT_AVAILABLE:
            send_message(chat_id, f"{greeting}🔮 *{idx_name} POWER PREDICTION bana rahi hoon...*\n_10 signals combine ho rahe hain — ML + TA + FII + VIX + PCR + Pivot + GIFT + News + Correlation... ~15s_ ⏳")
            try:
                result = power_predict(idx_name)
                if result.get("error"):
                    send_message(chat_id, f"{greeting}❌ {result['error']}", reply_markup=build_keyboard())
                else:
                    pages = format_power_prediction(result)
                    for page in pages:
                        send_message(chat_id, page, reply_markup=build_keyboard())
                    if VOICE_AVAILABLE:
                        try:
                            voice_text = format_power_voice(result)
                            send_voice_message(chat_id, voice_text, intent="analysis")
                        except Exception:
                            pass
            except Exception as e:
                logger.error(f"Power Predict error ({idx_name}): {e}", exc_info=True)
                send_message(chat_id, f"{greeting}❌ Power Prediction failed: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, f"{greeting}❌ Power Predictor not loaded.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════
    #  📊 OTM↔ATM ANALYSIS — NUCLEAR: Real NSE + Smart Strike Scoring
    # ════════════════════════════════════════════════════
    otm_atm_map = {
        "📊 NIFTY OTM↔ATM 🎯": "NIFTY",
        "📊 SENSEX OTM↔ATM 🎯": "SENSEX",
        "📊 BankNIFTY OTM↔ATM 🎯": "BANKNIFTY",
        "nifty otm atm": "NIFTY",
        "sensex otm atm": "SENSEX",
        "banknifty otm atm": "BANKNIFTY",
        "/otmatm": "NIFTY",
    }
    if text in otm_atm_map:
        idx_name = otm_atm_map[text]
        if NSE_LIVE_AVAILABLE or OTM_ATM_AVAILABLE:
            send_message(chat_id, f"{greeting}📊 *{idx_name} OTM↔ATM Analysis — REAL NSE DATA...*\n_Real prices + scoring + Greeks + profit scenarios... ~20s_ ⏳")
            try:
                sent = False
                # NSE Live Engine (REAL DATA first!)
                if NSE_LIVE_AVAILABLE:
                    nse_data = get_atm_otm_analysis(idx_name, budget=2000, direction="auto", num_strikes=8)
                    if "error" not in nse_data:
                        ce_msg = format_atm_otm_analysis(nse_data, "CE")
                        pe_msg = format_atm_otm_analysis(nse_data, "PE")
                        send_message(chat_id, ce_msg, reply_markup=build_keyboard())
                        send_message(chat_id, pe_msg, reply_markup=build_keyboard())
                        sent = True
                
                # Also send old engine report for additional analysis
                if OTM_ATM_AVAILABLE:
                    report = full_otm_atm_analysis(idx_name)
                    pages = format_otm_atm_report(report)
                    for page in pages:
                        send_message(chat_id, page, reply_markup=build_keyboard())
                    sent = True
                
                if not sent:
                    send_message(chat_id, f"{greeting}❌ {idx_name} OTM↔ATM data unavailable.", reply_markup=build_keyboard())
            except Exception as e:
                logger.error(f"OTM↔ATM error ({idx_name}): {e}", exc_info=True)
                send_message(chat_id, f"{greeting}❌ OTM↔ATM analysis failed: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, f"{greeting}❌ OTM↔ATM Engine not loaded.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════
    #  ⚡ 2-MIN MOMENTUM — Rapid Scalping Signal
    # ════════════════════════════════════════════════════
    if text in ("⚡ 2-Min Momentum 🚀", "2 min momentum", "/momentum"):
        if OTM_ATM_AVAILABLE:
            send_message(chat_id, f"{greeting}⚡ *2-Min Momentum Signal bana rahi hoon...*\n_NIFTY rapid scalping signal... ~10s_ ⏳")
            try:
                signal = rapid_momentum_signal("NIFTY")
                msg = format_momentum_signal(signal)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"{greeting}❌ Momentum signal failed: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, f"{greeting}❌ Momentum Engine not loaded.", reply_markup=build_keyboard())
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
            send_message(chat_id, msg)
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Crypto scan failed: {str(e)[:100]}")
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
            send_message(chat_id, msg)
            if CRYPTO_INTEL_AVAILABLE:
                send_jarvis_voice(chat_id, "Trending tokens ka rug check aur signals ready hain। Text mein dekh lijiye details।", intent="buy_sell_crypto")
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Trending fetch failed: {str(e)[:100]}")
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
    #   JARVIS PREDICTION ACCURACY (Self-Learning)
    # ════════════════════════════
    if text in ("/accuracy", "accuracy", "prediction accuracy", "jarvis accuracy",
                "kitni sahi thi", "accuracy report", "accuracy kya hai"):
        if TRACKER_AVAILABLE:
            try:
                # First verify any pending predictions
                verify_predictions(max_verify=20)
                msg = format_accuracy_report()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"{greeting}❌ Accuracy report error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, f"{greeting}📊 Trade Tracker module not loaded.", reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   CROSS-ASSET CORRELATION REPORT
    # ════════════════════════════
    if text in ("/correlation", "correlation", "correlations", "cross asset",
                "divergence", "market regime", "asset correlation"):
        if CORRELATION_AVAILABLE:
            try:
                send_message(chat_id, f"{greeting}🔗 Scanning cross-asset correlations... ⏳")
                msg = format_correlation_report()
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"{greeting}❌ Correlation scan error: {str(e)[:100]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, f"{greeting}🔗 Cross-Asset Engine not loaded.", reply_markup=build_keyboard())
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
    #  �🔐 JARVIS PAYMENT SYSTEM + WALLET + AUTO-INVEST
    # ═══════════════════════════════════════════════════════════

    # --- JARVIS Wallet Dashboard ---
    if text in ("💰🔐 JARVIS WALLET 💳", "/wallet", "jarvis wallet", "my wallet", "mera wallet"):
        if PAYMENT_AVAILABLE:
            try:
                msg = format_wallet_dashboard(chat_id)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Wallet error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Payment system loading ho raha hai...", reply_markup=build_keyboard())
        return

    # --- Deposit via UPI ---
    if text in ("💵 Deposit (UPI) 📱", "/deposit", "deposit", "paisa jama karo"):
        if PAYMENT_AVAILABLE:
            send_message(chat_id,
                f"{greeting}💵📱 *JARVIS UPI DEPOSIT*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Kitna deposit karna hai? Amount type karo:\n\n"
                f"💡 *Quick Options:*\n"
                f"  • `/deposit 500` — ₹500\n"
                f"  • `/deposit 1000` — ₹1,000\n"
                f"  • `/deposit 2000` — ₹2,000\n"
                f"  • `/deposit 5000` — ₹5,000\n"
                f"  • `/deposit 10000` — ₹10,000\n\n"
                f"📱 UPI se scan karke pay karo — PhonePe, GPay, Paytm sab chalega!\n\n"
                f"🔐 _AES-256 Encrypted | HMAC Verified_",
                reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Payment system available nahi hai.", reply_markup=build_keyboard())
        return

    # --- Deposit with specific amount ---
    if text.startswith("/deposit ") and PAYMENT_AVAILABLE:
        try:
            amount = float(text.split(" ", 1)[1].replace(",", "").replace("₹", "").strip())
            result = generate_deposit_qr(chat_id, amount)
            if "error" in result:
                send_message(chat_id, f"❌ {result['error']}", reply_markup=build_keyboard())
            elif result.get("qr_image"):
                send_photo(chat_id, result["qr_image"],
                    caption=(
                        f"💵📱 *UPI PAYMENT — ₹{amount:,.0f}*\n\n"
                        f"📱 PhonePe / GPay / Paytm se scan karo!\n"
                        f"🆔 Ref: `{result['tx_ref']}`\n\n"
                        f"✅ Payment ke baad UTR type karo: `/verify UTR_NUMBER`\n"
                        f"🔐 _Encrypted & Secured by JARVIS_"
                    ))
                # Also send UPI link for direct tap
                send_message(chat_id,
                    f"👆 *QR scan karo ya direct UPI link:*\n\n"
                    f"📱 [Pay ₹{amount:,.0f} via UPI]({result['upi_url']})\n\n"
                    f"✅ Payment ke baad UTR/Ref enter karo:\n"
                    f"`/verify YOUR_UTR_NUMBER`\n\n"
                    f"_Auto-verify hoga — no admin needed!_",
                    reply_markup=build_keyboard())
            else:
                send_message(chat_id,
                    f"💵 *UPI Payment — ₹{amount:,.0f}*\n\n"
                    f"📱 [Pay via UPI]({result['upi_url']})\n"
                    f"🆔 Ref: `{result['tx_ref']}`\n\n"
                    f"_QR generate nahi hua, link se pay karo_",
                    reply_markup=build_keyboard())
        except ValueError:
            send_message(chat_id, "❌ Valid amount enter karo: `/deposit 2000`", reply_markup=build_keyboard())
        return

    # --- Auto-Verify Deposit (UTR) — No Admin Needed ---
    if text.startswith("/verify ") and PAYMENT_AVAILABLE:
        try:
            utr = text.split(" ", 1)[1].strip()
            result = verify_deposit(chat_id, utr)
            if result.get("success"):
                send_message(chat_id,
                    f"✅💰 *DEPOSIT VERIFIED!*\n\n"
                    f"💵 Amount: ₹{result['amount']:,.2f}\n"
                    f"🆔 UTR: `{result['utr']}`\n"
                    f"🆔 Ref: `{result['tx_ref']}`\n"
                    f"💰 New Balance: ₹{result['new_balance']:,.2f}\n\n"
                    f"🤖 Ab `/autoinvest {int(result['amount'])}` se invest karo!\n"
                    f"_Auto-verified by JARVIS — no admin needed!_",
                    reply_markup=build_keyboard())
            else:
                send_message(chat_id, f"❌ {result.get('error', 'Verification failed')}", reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"❌ Format: `/verify YOUR_UTR_NUMBER`\nError: {e}", reply_markup=build_keyboard())
        return

    # --- Auto-Invest ---
    if text in ("🤖 Auto-Invest 🚀", "/autoinvest", "auto invest", "auto-invest"):
        if PAYMENT_AVAILABLE:
            balance = get_wallet_balance(chat_id)
            if balance["balance_inr"] > 0:
                send_message(chat_id,
                    f"{greeting}🤖🚀 *JARVIS AUTO-INVEST ENGINE*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💵 Available: *₹{balance['balance_inr']:,.2f}*\n\n"
                    f"Auto-invest kaise kaam karta hai:\n"
                    f"🔍 Tokens dhundta hai jo -5% ya zyada gire hain\n"
                    f"💎 Jinke paas 100x+ recovery potential hai\n"
                    f"🎯 10+ tokens mein diversify karta hai\n"
                    f"🛡️ Auto stop-loss -30% pe lagta hai\n"
                    f"📈 Auto take-profit 2x, 5x, 10x, 50x, 100x pe\n\n"
                    f"💡 *Amount type karo:*\n"
                    f"  • `/autoinvest 500` — ₹500 invest\n"
                    f"  • `/autoinvest 2000` — ₹2,000 invest\n"
                    f"  • `/autoinvest all` — Full balance invest\n\n"
                    f"_🤖 JARVIS 24/7 monitor karega aapka portfolio_",
                    reply_markup=build_keyboard())
            else:
                send_message(chat_id,
                    f"{greeting}🤖 *Auto-Invest — Balance Empty*\n\n"
                    f"Pehle deposit karo: `/deposit 2000`\n"
                    f"Phir invest karo: `/autoinvest 2000`",
                    reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Payment system available nahi hai.", reply_markup=build_keyboard())
        return

    # --- Auto-invest with amount ---
    if text.startswith("/autoinvest ") and PAYMENT_AVAILABLE:
        try:
            amount_txt = text.split(" ", 1)[1].strip()
            if amount_txt.lower() == "all":
                balance = get_wallet_balance(chat_id)
                amount = balance["balance_inr"]
            else:
                amount = float(amount_txt.replace(",", "").replace("₹", ""))

            send_message(chat_id,
                f"🤖🔍 *Scanning for gem tokens...*\n"
                f"_Finding tokens down ≥5% with 100x potential..._")

            result = auto_invest(chat_id, amount)
            msg = format_invest_result(result)
            send_message(chat_id, msg, reply_markup=build_keyboard())
            if VOICE_AVAILABLE:
                try:
                    num = result.get("num_tokens", 0)
                    send_jarvis_voice(chat_id, f"Boss, auto-invest complete! ₹{amount:.0f} ke {num} gem tokens mein invest kiya hai. JARVIS 24/7 monitor karega!", intent="investment")
                except Exception:
                    pass
        except ValueError:
            send_message(chat_id, "❌ Valid amount dein: `/autoinvest 2000`", reply_markup=build_keyboard())
        return

    # --- Portfolio ---
    if text in ("📊 My Portfolio 💎", "/portfolio", "portfolio", "mera portfolio"):
        if PAYMENT_AVAILABLE:
            try:
                msg = format_portfolio(chat_id)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Portfolio error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Payment system available nahi hai.", reply_markup=build_keyboard())
        return

    # --- Gem Scanner ---
    if text in ("💎 Gem Scanner 🔍", "/gems", "gem scan", "gem find"):
        if PAYMENT_AVAILABLE:
            send_message(chat_id, f"{greeting}💎🔍 *Scanning for gem tokens...*")
            try:
                gems = scan_gem_tokens()
                msg = format_gem_scan(gems)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Gem Scanner error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Payment system available nahi hai.", reply_markup=build_keyboard())
        return

    # --- Withdraw to Bank ---
    if text in ("🏦 Withdraw to Bank 💸", "/withdraw", "withdraw", "bank transfer", "paise nikalo"):
        if PAYMENT_AVAILABLE:
            balance = get_wallet_balance(chat_id)
            send_message(chat_id,
                f"{greeting}🏦💸 *JARVIS WITHDRAWAL*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💵 Available: *₹{balance['balance_inr']:,.2f}*\n\n"
                f"📋 *Steps:*\n"
                f"1️⃣ Bank details set karo (1 time):\n"
                f"   `/setbank BANK_NAME ACC_NO IFSC NAME`\n"
                f"   Example: `/setbank SBI 12345678 SBIN0001234 Rahul Kumar`\n\n"
                f"2️⃣ Withdraw karo:\n"
                f"   `/withdraw 5000` — ₹5,000 withdraw\n\n"
                f"⏰ *Processing:* 1-24 hours (IMPS/NEFT)\n"
                f"📍 *Min:* ₹500 | *Max:* Full balance\n\n"
                f"🔐 _Bank details encrypted (AES-256)_",
                reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Payment system available nahi hai.", reply_markup=build_keyboard())
        return

    # --- Set Bank Details ---
    if text.startswith("/setbank ") and PAYMENT_AVAILABLE:
        try:
            parts = text.split(None, 4)
            if len(parts) >= 5:
                result = set_bank_details(chat_id, parts[1], parts[2], parts[3], parts[4])
                if result.get("success"):
                    send_message(chat_id,
                        f"✅🏦 *Bank Details Saved!*\n\n"
                        f"🏦 Bank: {result['bank']}\n"
                        f"💳 Account: {result['account_masked']}\n\n"
                        f"🔐 _Encrypted & Secure_\n"
                        f"Ab `/withdraw AMOUNT` se paise nikal sakte ho!",
                        reply_markup=build_keyboard())
                else:
                    send_message(chat_id, f"❌ {result.get('error', '')}", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "Format: `/setbank BANK_NAME ACC_NO IFSC HOLDER_NAME`", reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"❌ Error: {e}", reply_markup=build_keyboard())
        return

    # --- Withdraw with amount ---
    if text.startswith("/withdraw ") and PAYMENT_AVAILABLE:
        try:
            amount = float(text.split(" ", 1)[1].replace(",", "").replace("₹", "").strip())
            result = request_withdrawal(chat_id, amount)
            if result.get("success"):
                send_message(chat_id,
                    f"✅💸 *Withdrawal Request Submitted!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💰 Amount: *₹{result['amount']:,.2f}*\n"
                    f"🏦 Bank: {result['bank']}\n"
                    f"🆔 Ref: `{result['tx_ref']}`\n"
                    f"⏰ Est: {result['estimated_time']}\n"
                    f"💵 Remaining: ₹{result['new_balance']:,.2f}\n\n"
                    f"🔐 _Processing securely..._",
                    reply_markup=build_keyboard())
                # Notify admin
                if _is_owner(chat_id) is False:
                    try:
                        send_message(OWNER_CHAT_ID,
                            f"🏦 *Withdrawal Request*\n"
                            f"User: {chat_id}\nAmount: ₹{result['amount']:,.2f}\n"
                            f"Bank: {result['bank']}\nRef: {result['tx_ref']}")
                    except Exception:
                        pass
            else:
                send_message(chat_id, f"❌ {result.get('error', '')}", reply_markup=build_keyboard())
        except ValueError:
            send_message(chat_id, "❌ Valid amount dein: `/withdraw 5000`", reply_markup=build_keyboard())
        return

    # --- Sell All Positions ---
    if text.lower() in ("/sellall", "sell all", "sab bech do"):
        if PAYMENT_AVAILABLE:
            result = sell_all(chat_id)
            if result.get("success") and result.get("count", 0) > 0:
                pnl = result["total_profit_inr"]
                emoji = "🟢" if pnl >= 0 else "🔴"
                send_message(chat_id,
                    f"{emoji} *All Positions Sold!*\n\n"
                    f"📊 Positions: {result['count']}\n"
                    f"💰 Total: ₹{result['total_sold_inr']:,.2f}\n"
                    f"📈 Profit: ₹{pnl:+,.2f}\n"
                    f"💵 Balance: ₹{result['new_balance']:,.2f}",
                    reply_markup=build_keyboard())
            else:
                send_message(chat_id, "Koi active position nahi hai.", reply_markup=build_keyboard())
        return

    # --- Income Tax Report ---
    if text in ("🏛️ Income Tax 📊", "/tax", "/incometax", "income tax", "tax report", "kitna tax lagega"):
        if PAYMENT_AVAILABLE:
            try:
                msg = format_tax_report(chat_id)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Tax calculation error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Payment system available nahi hai.", reply_markup=build_keyboard())
        return

    # --- Transaction History ---
    if text in ("📜 Transactions 📋", "/transactions", "transaction history", "mere transactions"):
        if PAYMENT_AVAILABLE:
            try:
                txns = get_transaction_history(chat_id, 15)
                if txns:
                    msg = "📜 *TRANSACTION HISTORY*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    for i, tx in enumerate(reversed(txns), 1):
                        t = tx.get("type", "unknown")
                        emoji = {"deposit": "⬆️", "deposit_verified": "✅", "auto_invest": "🤖",
                                 "withdrawal": "⬇️", "sell": "💰"}.get(t, "📋")
                        amt = tx.get("amount_inr", 0)
                        msg += f"{i}. {emoji} *{t.upper()}* — ₹{amt:,.2f}\n"
                        msg += f"   {tx.get('created', '')[:16]}\n\n"
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                else:
                    send_message(chat_id, "📜 Koi transaction nahi hai abhi.", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Payment system available nahi hai.", reply_markup=build_keyboard())
        return

    # ═══════════════════════════════════════════════════════════
    #  🚀 JARVIS REAL TRADER — On-Chain Solana Trading
    # ═══════════════════════════════════════════════════════════

    # --- Create / View Trading Wallet ---
    if text in ("🚀 Real Trading Wallet", "/create_wallet", "/trading_wallet", "trading wallet", "real wallet", "create wallet"):
        if REAL_TRADER_AVAILABLE:
            try:
                wallet = get_trading_wallet(chat_id)
                if wallet:
                    msg = format_trading_wallet(chat_id)
                    send_message(chat_id, msg, reply_markup=build_keyboard())
                else:
                    # Create new wallet
                    result = create_trading_wallet(chat_id)
                    if result.get("success"):
                        msg = (
                            f"🟢 *REAL TRADING WALLET CREATED!*\n\n"
                            f"📍 *Address:*\n`{result['pubkey']}`\n\n"
                            f"⚡ *How to start:*\n"
                            f"1️⃣ Send SOL to this address from Phantom/Solflare\n"
                            f"2️⃣ Press '🤖 Auto-Trade ON/OFF' to enable\n"
                            f"3️⃣ JARVIS will auto-buy gem tokens on dips!\n\n"
                            f"🎯 *Compound targets:*\n"
                            f"  💰 ₹2K → ₹2L (Stage 1)\n"
                            f"  💰 ₹2L → ₹2Cr (Stage 2)\n"
                            f"  💰 ₹2Cr → ₹2L Cr (Stage 3)\n\n"
                            f"🛡️ Stop-loss: -35% | Take-profit: 2x→10000x\n"
                            f"⚠️ REAL MONEY trading. DYOR!"
                        )
                        send_message(chat_id, msg, reply_markup=build_keyboard())
                    else:
                        send_message(chat_id, f"❌ {result.get('error', 'Wallet creation failed')}", reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Real Trader module not available. Solana SDK needed.", reply_markup=build_keyboard())
        return

    # --- Auto-Trade Toggle ---
    if text in ("🤖 Auto-Trade ON/OFF", "/autotrade", "auto trade", "auto-trade toggle"):
        if REAL_TRADER_AVAILABLE:
            try:
                wallet = get_trading_wallet(chat_id)
                if not wallet:
                    send_message(chat_id, "❌ Pehle wallet create karo! Press '🚀 Real Trading Wallet'", reply_markup=build_keyboard())
                    return
                if wallet.get("auto_trade_enabled"):
                    result = disable_auto_trade(chat_id)
                    send_message(chat_id,
                        "⏸️ *Auto-Trade DISABLED*\n\n"
                        "JARVIS ab auto buy/sell nahi karega.\n"
                        "Manual trading: /buy <token> <sol_amount>\n"
                        "Re-enable anytime!",
                        reply_markup=build_keyboard())
                else:
                    sol_bal = trader_sol_balance(wallet["pubkey"])
                    if sol_bal < 0.01:
                        send_message(chat_id,
                            f"❌ *Insufficient SOL!*\n\n"
                            f"Balance: {sol_bal:.4f} SOL\n"
                            f"Min needed: 0.01 SOL\n\n"
                            f"Send SOL to:\n`{wallet['pubkey']}`",
                            reply_markup=build_keyboard())
                        return
                    result = enable_auto_trade(chat_id)
                    send_message(chat_id,
                        f"🟢 *AUTO-TRADE ENABLED!* 🚀\n\n"
                        f"💰 SOL Balance: {sol_bal:.4f} SOL\n"
                        f"🤖 JARVIS will now:\n"
                        f"  1. Scan DexScreener + Pump.fun every 3 min\n"
                        f"  2. Auto-buy top gems on -5%+ dips\n"
                        f"  3. Auto-sell at 2x/5x/10x/50x/100x/1000x/10000x\n"
                        f"  4. Stop-loss at -35%\n"
                        f"  5. Auto-compound: ₹2K → ₹2L → ₹2Cr → ₹2L Cr\n\n"
                        f"⚠️ REAL SOL will be spent! Monitor your portfolio.",
                        reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Real Trader not available.", reply_markup=build_keyboard())
        return

    # --- Live Portfolio ---
    if text in ("📊 Live Portfolio 🔥", "/live_portfolio", "live portfolio", "real portfolio"):
        if REAL_TRADER_AVAILABLE:
            try:
                wallet = get_trading_wallet(chat_id)
                if not wallet:
                    send_message(chat_id, "❌ Pehle wallet create karo! Press '🚀 Real Trading Wallet'", reply_markup=build_keyboard())
                    return
                msg = format_live_portfolio(chat_id)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Real Trader not available.", reply_markup=build_keyboard())
        return

    # --- Trade History ---
    if text in ("📜 Trade History 📋", "/trade_history", "trade history", "real trades"):
        if REAL_TRADER_AVAILABLE:
            try:
                msg = format_trade_history(chat_id)
                send_message(chat_id, msg, reply_markup=build_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ Error: {str(e)[:200]}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Real Trader not available.", reply_markup=build_keyboard())
        return

    # --- Manual Buy: /buy <token_mint> <sol_amount> ---
    if text.startswith("/buy ") and REAL_TRADER_AVAILABLE:
        parts = text.split()
        if len(parts) >= 3:
            token_mint = parts[1]
            try:
                sol_amount = float(parts[2])
            except ValueError:
                send_message(chat_id, "❌ Usage: /buy <token_mint> <sol_amount>\nExample: /buy EPjFWdd5... 0.1", reply_markup=build_keyboard())
                return
            send_message(chat_id, f"⏳ *Executing REAL buy...*\n\nToken: `{token_mint[:20]}...`\nSOL: {sol_amount}")
            result = buy_token(chat_id, token_mint, sol_amount)
            if result.get("success"):
                send_message(chat_id,
                    f"🟢 *BUY EXECUTED!*\n\n"
                    f"Token: `{token_mint[:20]}...`\n"
                    f"SOL Spent: {sol_amount:.4f}\n"
                    f"TX: [Solscan]({result.get('solscan_url', '')})\n\n"
                    f"🎯 Targets set: 2x→10000x\n"
                    f"🛡️ Stop-loss: -35%",
                    reply_markup=build_keyboard())
            else:
                send_message(chat_id, f"❌ Buy failed: {result.get('error', 'Unknown error')}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Usage: /buy <token_mint> <sol_amount>\nExample: /buy EPjFWdd5... 0.1", reply_markup=build_keyboard())
        return

    # --- Manual Sell: /sell <token_mint> [pct] ---
    if text.startswith("/sell ") and REAL_TRADER_AVAILABLE:
        parts = text.split()
        if len(parts) >= 2:
            token_mint = parts[1]
            sell_pct = 100.0
            if len(parts) >= 3:
                try:
                    sell_pct = float(parts[2])
                except ValueError:
                    sell_pct = 100.0
            send_message(chat_id, f"⏳ *Executing REAL sell...*\n\nToken: `{token_mint[:20]}...`\nSelling: {sell_pct}%")
            result = sell_token(chat_id, token_mint, sell_pct)
            if result.get("success"):
                send_message(chat_id,
                    f"🔴 *SELL EXECUTED!*\n\n"
                    f"Token: `{token_mint[:20]}...`\n"
                    f"SOL Received: {result.get('sol_received', 0):.4f}\n"
                    f"TX: [Solscan]({result.get('solscan_url', '')})",
                    reply_markup=build_keyboard())
            else:
                send_message(chat_id, f"❌ Sell failed: {result.get('error', 'Unknown error')}", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Usage: /sell <token_mint> [percentage]\nExample: /sell EPjFWdd5... 50", reply_markup=build_keyboard())
        return

    # ═══════════════════════════════════════════════════════════
    #  🤖 JARVIS PERSONAL AI AGENT
    # ═══════════════════════════════════════════════════════════

    # --- Agent Dashboard ---
    if text in ("🤖 JARVIS Agent 🧠", "/agent", "jarvis agent", "personal agent"):
        if AGENT_AVAILABLE:
            msg = format_agent_dashboard(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Agent module loading...", reply_markup=build_keyboard())
        return

    # --- Notes ---
    if text in ("📝 My Notes 📒", "/notes", "my notes", "mere notes"):
        if AGENT_AVAILABLE:
            msg = format_notes(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Agent module available nahi hai.", reply_markup=build_keyboard())
        return

    if text.startswith("/note ") and AGENT_AVAILABLE:
        content = text[6:].strip()
        note = save_note(chat_id, "Quick Note", content)
        send_message(chat_id, f"📝✅ *Note Saved!*\n\n{content[:300]}\n\n_🆔 {note['id']}_", reply_markup=build_keyboard())
        return

    # --- Tasks ---
    if text in ("✅ My Tasks 📋", "/tasks", "my tasks", "mere tasks"):
        if AGENT_AVAILABLE:
            msg = format_tasks(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Agent module available nahi hai.", reply_markup=build_keyboard())
        return

    if text.startswith("/task ") and AGENT_AVAILABLE:
        task_text = text[6:].strip()
        task = add_task(chat_id, task_text)
        send_message(chat_id, f"✅ *Task Added!*\n\n📋 {task_text}\n_🆔 {task['id']}_", reply_markup=build_keyboard())
        return

    if text.startswith("/done ") and AGENT_AVAILABLE:
        task_id = text[6:].strip()
        if complete_task(chat_id, task_id):
            send_message(chat_id, f"✅ Task `{task_id}` complete! 🎉", reply_markup=build_keyboard())
        else:
            send_message(chat_id, f"❌ Task `{task_id}` nahi mila.", reply_markup=build_keyboard())
        return

    # --- Reminders ---
    if text in ("⏰ My Reminders 🔔", "/reminders", "my reminders"):
        if AGENT_AVAILABLE:
            msg = format_reminders(chat_id)
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Agent module available nahi hai.", reply_markup=build_keyboard())
        return

    if text.startswith("/remind ") and AGENT_AVAILABLE:
        reminder_text = text[8:].strip()
        # Parse "in X minutes" pattern
        m = re.search(r'(\d+)\s*(min|minute|hour|ghante|hr)', reminder_text.lower())
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            mins = val * 60 if unit in ("hour", "ghante", "hr") else val
        else:
            mins = 30
        result = add_reminder(chat_id, reminder_text, minutes=mins)
        if result.get("success"):
            send_message(chat_id,
                f"⏰✅ *Reminder Set!*\n\n"
                f"📝 {reminder_text}\n"
                f"⏰ {result['remind_at']}\n\n"
                f"_JARVIS yaad dilayega!_ 🔔",
                reply_markup=build_keyboard())
        return

    # --- Research ---
    if text in ("🔍 Research 🧠", "/research"):
        if AGENT_AVAILABLE:
            send_message(chat_id,
                f"{greeting}🔍🧠 *JARVIS RESEARCH*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Kya research karna hai? Batao:\n\n"
                f"• `/research Bitcoin price prediction`\n"
                f"• `/research NIFTY analysis`\n"
                f"• `/research AI trends 2026`\n"
                f"• `/research Solana ecosystem`\n\n"
                f"_Wikipedia, News, CoinGecko, DuckDuckGo se data_",
                reply_markup=build_keyboard())
        return

    if text.startswith("/research ") and AGENT_AVAILABLE:
        query = text[10:].strip()
        send_message(chat_id, f"🔍 *Researching:* {query[:50]}...")
        results = research_topic(query)
        msg = format_research(results)
        send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    # --- Weather ---
    if text in ("🌤️ Weather ☁️", "/weather", "weather", "mausam"):
        if AGENT_AVAILABLE:
            msg = agent_get_weather("Delhi")
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Agent module available nahi hai.", reply_markup=build_keyboard())
        return

    if text.startswith("/weather ") and AGENT_AVAILABLE:
        city = text[9:].strip()
        msg = agent_get_weather(city)
        send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    # --- Calculator ---
    if text.startswith("/calc ") and AGENT_AVAILABLE:
        expr = text[6:].strip()
        msg = agent_calculate(expr)
        send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    # ═══════════════════════════════════════════════════════════
    #  �🛡️ SECURITY DASHBOARD — Owner Only
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
                
                # Add cross-asset correlation insight
                if CORRELATION_AVAILABLE:
                    try:
                        corr_insight = get_correlation_insight("NIFTY")
                        if corr_insight:
                            pages.append(f"🔗 *Cross-Asset Correlations:*\n{corr_insight}")
                    except Exception:
                        pass
                
                for page in pages:
                    send_message(chat_id, page)
                
                # Log prediction for accuracy tracking
                if TRACKER_AVAILABLE and stock_data:
                    try:
                        verdict = stock_data.get("verdict", stock_data.get("action", ""))
                        score = stock_data.get("score", stock_data.get("confidence", 50))
                        price = stock_data.get("price", stock_data.get("current_price", 0))
                        log_prediction(text, verdict, score, price, source="stock_ai")
                    except Exception:
                        pass
                
                voice_text = format_indian_stock_voice(stock_data)
                send_jarvis_voice(chat_id, voice_text, intent="buy_sell_stock", is_voice_input=is_voice)
            except Exception as e:
                logger.error(f"[STOCK-AI] Error: {e}")
                send_message(chat_id, f"❌ Indian Stock AI error: {str(e)[:150]}")
        else:
            # Fallback to existing candle analysis
            send_message(chat_id, f"{greeting}🔄 *NIFTY + SENSEX Analysis...* ⏳")
            try:
                from candle_analyzer import analyze_index
                for ticker, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
                    analysis = analyze_index(ticker, name)
                    if analysis:
                        send_message(chat_id, analysis.get("analysis", "No data"))
            except Exception as e:
                send_message(chat_id, f"❌ Stock analysis error: {str(e)[:100]}")
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
                    
                    # Add cross-asset correlation insight
                    if CORRELATION_AVAILABLE:
                        try:
                            corr_insight = get_correlation_insight(token)
                            if corr_insight:
                                pages.append(f"🔗 *Cross-Asset Correlations:*\n{corr_insight}")
                        except Exception:
                            pass
                    
                    # Add calibrated confidence if tracker available
                    if TRACKER_AVAILABLE and deep_data:
                        try:
                            raw_score = deep_data.get("ultra_score", deep_data.get("score", 50))
                            real_conf = get_calibrated_confidence(raw_score)
                            pages.append(f"📐 *Calibrated Confidence:* {real_conf*100:.0f}% (based on past accuracy)")
                        except Exception:
                            pass
                    
                    for page in pages:
                        send_message(chat_id, page, reply_markup=build_keyboard())
                    
                    # Log prediction for accuracy tracking
                    if TRACKER_AVAILABLE and deep_data:
                        try:
                            verdict = deep_data.get("verdict", deep_data.get("action", ""))
                            score = deep_data.get("ultra_score", deep_data.get("score", 50))
                            price = deep_data.get("price", deep_data.get("current_price", 0))
                            indicators = {
                                "ai_signal": deep_data.get("ai_signal"),
                                "rug_risk": deep_data.get("rug_score"),
                                "money_flow": deep_data.get("money_flow"),
                                "whale": deep_data.get("whale_signal"),
                            }
                            log_prediction(token, verdict, score, price, 
                                         source="crypto_deep", indicators=indicators)
                        except Exception:
                            pass
                    
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

    # --- Telegram Wallet (@wallet) Integration ---
    if text in ("💎 Telegram Wallet 💳", "telegram wallet", "/telegramwallet",
                "ton wallet", "connect telegram wallet"):
        ton_addr = OWNER_TON_WALLET if AIRDROP_AVAILABLE else "N/A"
        sol_addr = OWNER_WALLET if PHANTOM_AVAILABLE else (SOL_OWNER_WALLET if SOLANA_ENGINE_AVAILABLE else os.environ.get("OWNER_SOLANA_WALLET", "N/A"))
        msg = (
            f"💎💳 *JARVIS — TELEGRAM WALLET INTEGRATION* 💳💎\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Telegram ka built-in @wallet use karke aap directly\n"
            f"bot se crypto send/receive kar sakte ho! 🚀\n\n"
            f"📲 *SETUP STEPS (1-time):*\n"
            f"1️⃣ Telegram mein @wallet open karo\n"
            f"2️⃣ 'Start' button dabo\n"
            f"3️⃣ Wallet create / import karo\n"
            f"4️⃣ TON, USDT, BTC, ETH — sab available!\n\n"
            f"💰 *SUPPORTED ACTIONS:*\n"
            f"  🔹 Send/Receive TON, USDT, BTC, ETH\n"
            f"  🔹 P2P trading inside Telegram\n"
            f"  🔹 Swap tokens instantly\n"
            f"  🔹 Buy crypto with card/bank\n"
            f"  🔹 Send crypto to any Telegram user\n\n"
            f"🔗 *QUICK LINKS:*\n"
            f"  🏦 [Open Telegram Wallet](https://t.me/wallet)\n"
            f"  💱 [CryptoBot (another option)](https://t.me/CryptoBot)\n"
            f"  🔄 [xRocket Wallet](https://t.me/xRocket)\n\n"
            f"👛 *YOUR WALLETS:*\n"
            f"  💎 *TON:* `{ton_addr}`\n"
            f"  🟣 *Solana:* `{sol_addr[:8]}...{sol_addr[-6:]}`\n"
            f"  🔗 [View TON on TonViewer](https://tonviewer.com/{ton_addr})\n"
            f"  🔗 [View SOL on Solscan](https://solscan.io/account/{sol_addr})\n\n"
            f"📝 *SET YOUR OWN WALLET:*\n"
            f"  Type: `/setwallet ton YOUR_ADDRESS`\n"
            f"  Type: `/setwallet solana YOUR_ADDRESS`\n\n"
            f"💡 *Tips:*\n"
            f"  • @wallet se USDT send karo — instant transfer!\n"
            f"  • P2P se Indian Rupees (₹) se buy karo\n"
            f"  • Airdrops auto-track ho rahe hain dono wallets par!\n\n"
            f"⚠️ _Apna seed phrase kisi ko share mat karo!_"
        )
        send_message(chat_id, msg, reply_markup=build_keyboard())
        return

    # --- Set My Wallet (any user can set their own wallet) ---
    if text in ("📝 Set My Wallet 🔑", "set my wallet", "set wallet") or text.startswith("/setwallet"):
        if AIRDROP_AVAILABLE:
            # Parse: /setwallet ton <addr> or /setwallet solana <addr>
            parts = text.split()
            if len(parts) >= 3 and parts[0].lower() in ("/setwallet", "setwallet"):
                chain = parts[1].lower()
                addr = parts[2]
                if chain in ("ton", "solana", "evm", "ethereum", "bsc", "arbitrum"):
                    register_wallet(chat_id, chain, addr)
                    msg = (
                        f"✅ *Wallet Registered Successfully!*\n\n"
                        f"⛓️ Chain: *{chain.upper()}*\n"
                        f"📍 Address: `{addr}`\n\n"
                        f"🎁 Airdrop Hunter ab is wallet ko bhi scan karega!\n"
                        f"📊 Auto-detection ON — naye tokens milenge toh alert aayega.\n\n"
                        f"💡 _Other wallets add karne ke liye:_\n"
                        f"  `/setwallet ton YOUR_TON_ADDRESS`\n"
                        f"  `/setwallet solana YOUR_SOL_ADDRESS`\n"
                        f"  `/setwallet evm YOUR_ETH_ADDRESS`"
                    )
                else:
                    msg = (
                        f"❌ Unknown chain: *{chain}*\n\n"
                        f"Supported chains: *ton, solana, evm, ethereum, bsc, arbitrum*\n\n"
                        f"Example: `/setwallet ton UQBl...zkC`"
                    )
            else:
                msg = (
                    f"📝🔑 *SET YOUR WALLET ADDRESS*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"Apna wallet address set karo — airdrops auto-track honge!\n\n"
                    f"📲 *Commands:*\n"
                    f"  `/setwallet ton YOUR_TON_ADDRESS`\n"
                    f"  `/setwallet solana YOUR_SOL_ADDRESS`\n"
                    f"  `/setwallet evm YOUR_ETH_ADDRESS`\n\n"
                    f"📝 *Example:*\n"
                    f"  `/setwallet ton UQBlUgQZt_EGCpWC1...`\n"
                    f"  `/setwallet solana 8F1PJhuJ...`\n\n"
                    f"🎁 Set karne ke baad:\n"
                    f"  ✅ Airdrop auto-scan ON\n"
                    f"  ✅ Token alerts ON\n"
                    f"  ✅ Value in ₹ INR shown\n"
                    f"  ✅ Swap links auto-generated\n\n"
                    f"⚠️ _Sirf PUBLIC wallet address dalo — private key KABHI nahi!_"
                )
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Airdrop module not available.", reply_markup=build_keyboard())
        return

    # --- My Wallets (show all registered wallets) ---
    if text in ("👛 My Wallets 💰", "my wallets", "/mywallets", "my wallet"):
        if AIRDROP_AVAILABLE:
            wallets = get_all_user_wallets(chat_id)
            if not wallets:
                msg = (
                    f"👛 *YOUR WALLETS*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"❌ Koi wallet registered nahi hai!\n\n"
                    f"📝 Set karo: `/setwallet ton YOUR_ADDRESS`\n"
                    f"📝 Ya: `/setwallet solana YOUR_ADDRESS`"
                )
            else:
                msg = f"👛💰 *YOUR REGISTERED WALLETS*\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                chain_icons = {"solana": "🟣", "ton": "💎", "evm": "🔵", "ethereum": "🔵", "bsc": "🟡", "arbitrum": "🔷"}
                for chain, addr in wallets.items():
                    icon = chain_icons.get(chain, "🔹")
                    msg += f"{icon} *{chain.upper()}:*\n"
                    msg += f"   📍 `{addr}`\n"
                    if chain == "solana":
                        msg += f"   🔗 [Solscan](https://solscan.io/account/{addr})\n"
                    elif chain == "ton":
                        msg += f"   🔗 [TonViewer](https://tonviewer.com/{addr})\n"
                    elif chain in ("evm", "ethereum"):
                        msg += f"   🔗 [Etherscan](https://etherscan.io/address/{addr})\n"
                    msg += "\n"
                msg += "🎁 _Sab wallets par airdrop auto-scan chal raha hai!_\n"
                msg += "⚡ _Scan interval: Every 30 seconds_\n\n"
                msg += "📝 _Aur wallet add karo:_ `/setwallet chain address`"
            send_message(chat_id, msg, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Airdrop module not available.", reply_markup=build_keyboard())
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
                _sol_wallet = OWNER_WALLET if PHANTOM_AVAILABLE else (SOL_OWNER_WALLET if SOLANA_ENGINE_AVAILABLE else os.environ.get("OWNER_SOLANA_WALLET", ""))
                links = generate_phantom_transfer_link(
                    recipient=_sol_wallet,
                )
                sol_bal = get_sol_balance()
                _phantom_user = os.environ.get("OWNER_PHANTOM_USERNAME", "@davidbot1")
                _wallet_short = f"{_sol_wallet[:6]}...{_sol_wallet[-4:]}" if len(_sol_wallet) > 10 else _sol_wallet
                
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
                send_message(chat_id, panel_text, reply_markup=admin_kb)
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
                chain = generate_option_chain("NIFTY")
                reco = recommend_strategy("NIFTY")
                iv_data = calculate_iv_rank_percentile("NIFTY")

                msg = format_option_chain(chain, "hi")
                if reco:
                    msg += "\n\n" + format_recommendations(reco, "hi")
                if iv_data:
                    msg += f"\n\n📊 *IV Rank:* {iv_data.get('iv_rank', 'N/A'):.1f}%"
                    msg += f"\n📊 *IV Percentile:* {iv_data.get('iv_percentile', 'N/A'):.1f}%"
                if chain:
                    mp = chain.get("max_pain", 0)
                    pcr_val = chain.get("pcr", 0)
                    if mp: msg += f"\n💥 *Max Pain:* ₹{mp:,.0f}"
                    if pcr_val:
                        msg += f"\n📊 *PCR:* {pcr_val:.2f}"
                        if pcr_val > 1.2:
                            msg += " 🟢 (Bullish — Heavy put writing)"
                        elif pcr_val < 0.7:
                            msg += " 🔴 (Bearish — Heavy call writing)"
                        else:
                            msg += " 🟡 (Neutral)"

                send_message(chat_id, msg, reply_markup=build_keyboard())
                if VOICE_AVAILABLE:
                    try:
                        voice_text = f"Options analysis ready. IV Rank {iv_data.get('iv_rank', 'N/A'):.0f} percent. Strategy: {reco.get('primary', {}).get('strategy', 'Check report')}."
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

    # /news — Worldwide News Digest (enhanced with NewsAPI)
    if text.lower() in ("/news", "news", "khabar", "headlines", "/newsall") or text in ("📰 News Digest",):
        if SUPER_BRAIN_AVAILABLE:
            send_message(chat_id, jarvis_animated_header("thinking"))
            digest = format_news_digest()
            # Append NewsAPI headlines if available
            if NEWS_ENHANCED:
                try:
                    extra = get_news_headlines("business", "in", 5)
                    if extra:
                        digest += f"\n\n{extra}"
                except Exception:
                    pass
            send_message(chat_id, digest, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, format_news_voice(), intent="market_summary")
        elif NEWS_ENHANCED:
            send_message(chat_id, "📰 Fetching news...", reply_markup=build_keyboard())
            headlines = get_news_headlines("general", "in", 10)
            send_message(chat_id, headlines or "📰 No headlines available.", reply_markup=build_keyboard())
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

    # ════════════════════════════════════════════════════════
    #   🛠️ JARVIS TOOLS — Weather, Search, Song, Image, Memory
    # ════════════════════════════════════════════════════════

    # 🌤️ Weather
    if text in ("🌤️ Weather",) or text.lower().startswith(("/weather", "weather", "mausam")):
        if WEATHER_AVAILABLE:
            # Extract city from command
            _city = "Mumbai"  # default
            _text_clean = text.replace("🌤️", "").strip()
            for _prefix in ["/weather", "weather", "mausam batao", "mausam kaisa hai", "mausam"]:
                _text_clean = _text_clean.lower().replace(_prefix, "").strip()
            if _text_clean and len(_text_clean) > 1:
                _city = _text_clean.title()
            send_message(chat_id, f"🌤️ Checking weather for {_city}...", reply_markup=build_keyboard())
            result = get_weather(_city)
            send_message(chat_id, result, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, f"Weather in {_city}: {result[:200]}", intent="chat")
        else:
            send_message(chat_id, "⚠️ Weather feature not available (API key missing).", reply_markup=build_keyboard())
        return

    # 🔍 Web Search
    if text in ("🔍 Web Search",) or text.lower().startswith(("/search", "search", "google")):
        if SEARCH_AVAILABLE:
            _query = text.lower().replace("/search", "").replace("search", "").replace("google", "").strip()
            if not _query or _query == "🔍 web":
                # Ask user what to search
                send_message(chat_id, "🔍 *Web Search*\n\nKya search karna hai? Type karo:\n_Example: search Bitcoin price today_", reply_markup=build_keyboard())
                chat_storage[f"awaiting_search_{chat_id}"] = True
            else:
                send_message(chat_id, "🔍 Searching...", reply_markup=build_keyboard())
                result = web_search(_query)
                send_message(chat_id, result, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "⚠️ Web Search not available (API key missing).", reply_markup=build_keyboard())
        return

    # Handle awaiting search query
    if chat_storage.get(f"awaiting_search_{chat_id}") and SEARCH_AVAILABLE:
        chat_storage[f"awaiting_search_{chat_id}"] = False
        send_message(chat_id, "🔍 Searching...", reply_markup=build_keyboard())
        result = web_search(text)
        send_message(chat_id, result, reply_markup=build_keyboard())
        return

    # 🎵 Song Recognition
    if text in ("🎵 Identify Song 🎶",) or text.lower() in ("/song", "song", "gaana pehchano", "identify song", "kya gaana hai", "shazam"):
        if SONG_AVAILABLE:
            send_message(chat_id, "🎵 *Song Recognition*\n\nMujhe ek voice message bhejo audio ke saath — main gaana pehchaan lungi! 🎶\n\n_Record the song playing near you and send as voice message._", reply_markup=build_keyboard())
            chat_storage[f"awaiting_song_{chat_id}"] = True
        else:
            send_message(chat_id, "⚠️ Song recognition not available (ACRCloud API key missing).", reply_markup=build_keyboard())
        return

    # 🎨 Image Generation
    if text in ("🎨 Generate Image",) or text.lower().startswith(("/imagine", "imagine", "generate image", "create image", "tasveer banao")):
        if IMAGE_AVAILABLE:
            _prompt = text.lower().replace("/imagine", "").replace("imagine", "").replace("generate image", "").replace("create image", "").replace("tasveer banao", "").strip()
            if not _prompt or _prompt in ("🎨",):
                send_message(chat_id, "🎨 *Image Generation*\n\nBatao kya image banana hai?\n_Example: /imagine a cute robot trading stocks_", reply_markup=build_keyboard())
                chat_storage[f"awaiting_image_{chat_id}"] = True
            else:
                send_message(chat_id, "🎨 Generating image... (10-30 sec)", reply_markup=build_keyboard())
                img_bytes = generate_image(_prompt)
                if img_bytes:
                    send_photo(chat_id, img_bytes, caption=f"🎨 *Generated:* _{_prompt}_", reply_markup=build_keyboard())
                else:
                    send_message(chat_id, "⚠️ Image generation failed. Try a different prompt.", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "⚠️ Image generation not available (Stability API key missing).", reply_markup=build_keyboard())
        return

    # Handle awaiting image prompt
    if chat_storage.get(f"awaiting_image_{chat_id}") and IMAGE_AVAILABLE:
        chat_storage[f"awaiting_image_{chat_id}"] = False
        send_message(chat_id, "🎨 Generating image... (10-30 sec)", reply_markup=build_keyboard())
        img_bytes = generate_image(text)
        if img_bytes:
            send_photo(chat_id, img_bytes, caption=f"🎨 *Generated:* _{text}_", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "⚠️ Image generation failed. Try a different prompt.", reply_markup=build_keyboard())
        return

    # 🧠 Memory
    if text in ("🧠 My Memory",) or text.lower() in ("/memory", "memory", "meri memory", "yaad karo", "what do you remember"):
        if MEM0_AVAILABLE:
            memories = mem0_get_all(str(chat_id))
            if memories:
                msg = "🧠 *Your JARVIS Memory:*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                for i, m in enumerate(memories[:15], 1):
                    content = m.get("memory", m.get("content", ""))[:100]
                    msg += f"{i}. {content}\n"
                msg += f"\n📊 Total: {len(memories)} memories stored"
                send_message(chat_id, msg, reply_markup=build_keyboard())
            else:
                send_message(chat_id, "🧠 No memories stored yet. I'll learn about you as we chat! 💕", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "🧠 Memory: Using local storage (Mem0 API not configured).", reply_markup=build_keyboard())
        return

    # 📰 Crypto News (enhanced with NewsAPI)
    if text in ("📰 Crypto News",) or text.lower() in ("/cryptonews", "crypto news", "crypto khabar"):
        if NEWS_ENHANCED:
            send_message(chat_id, "📰 Fetching crypto news...", reply_markup=build_keyboard())
            news = get_crypto_news()
            if news:
                send_message(chat_id, news, reply_markup=build_keyboard())
            else:
                send_message(chat_id, "📰 No crypto news available right now.", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "📰 Crypto news (enhanced) not available.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════

    # ════════════════════════════════════════════════════════
    #   ⚡ JARVIS CODE ENGINE — Autonomous Execution
    #   User says "code banao X" → JARVIS generates, runs, returns OUTPUT
    #   User sends GitHub URL → JARVIS clones, installs, runs, returns OUTPUT
    # ════════════════════════════════════════════════════════
    
    # ── ⚡ "Run Code" button — awaits code paste ──
    if text in ("⚡ Run Code 🏃", "run code", "/runcode"):
        chat_storage[f"awaiting_code_{chat_id}"] = True
        send_message(chat_id,
            f"⚡ *JARVIS CODE ENGINE — Ready!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 Apna code paste kariye — main *auto-run* kar dungi! 🏃\n\n"
            f"Supported: Python, JavaScript, Go, Rust, C/C++, Bash\n\n"
            f"Ya phir bataiye kya banana hai — main *khud generate + run* karungi! 🚀",
            reply_markup=build_keyboard())
        return

    # ── 🐙 "GitHub Run" button — awaits GitHub URL ──
    if text in ("🐙 GitHub Run 🔗", "github run", "/githubrun"):
        chat_storage[f"awaiting_github_{chat_id}"] = True
        send_message(chat_id,
            f"🐙 *JARVIS GITHUB RUNNER — Ready!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 GitHub URL paste kariye!\n"
            f"Main *auto-clone → install → run* karungi! ⚡\n\n"
            f"Example:\n`https://github.com/user/repo`\n\n"
            f"_Bas URL do, baaki sab main karungi!_ 🌸",
            reply_markup=build_keyboard())
        return

    # ── Handle awaiting code paste (raw code execution) ──
    if chat_storage.get(f"awaiting_code_{chat_id}") and CODE_ENGINE_AVAILABLE:
        chat_storage[f"awaiting_code_{chat_id}"] = False
        
        # Check if it's a code request or raw code
        _code_type = detect_code_request(text)
        
        if _code_type == 'raw_code' or (len(text.split('\n')) > 2 and any(kw in text for kw in ['import ', 'def ', 'print(', 'function ', 'console.', 'class ', '#!'])):
            # Raw code — detect language and execute
            _lang = "python"
            if any(kw in text for kw in ['console.log', 'const ', 'let ', 'var ', 'function ', '=>']):
                _lang = "javascript"
            elif text.startswith('#!') and 'bash' in text.split('\n')[0]:
                _lang = "bash"
            elif any(kw in text for kw in ['fmt.', 'func ', 'package main']):
                _lang = "go"
            elif any(kw in text for kw in ['fn main', 'println!', 'use std']):
                _lang = "rust"
            elif any(kw in text for kw in ['#include', 'int main', 'printf']):
                _lang = "c" if '#include <stdio.h>' in text else "cpp"
            
            send_message(chat_id,
                f"⚡ *Code Engine Running...*\n"
                f"🔤 Language: {_lang.title()}\n"
                f"_Executing..._ ⏳",
                reply_markup=build_keyboard())
            
            result = execute_raw_code(text, _lang)
            msg = format_execution_result(result, f"Raw {_lang} code")
            send_message(chat_id, msg, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id,
                f"Code execute ho gaya! {'Output aa gaya hai, check kariye ji!' if result.get('success') else 'Error aaya hai, main fix karti hoon!'}",
                intent="greeting")
        else:
            # Treat as code generation request
            send_message(chat_id,
                f"⚡🧠 *JARVIS Code Engine — Generating + Running...*\n"
                f"_AI code likh rahi hai + auto-run karungi..._ ⏳🚀",
                reply_markup=build_keyboard())
            
            result = execute_code_autonomous(text, chat_id)
            msg = format_execution_result(result, text[:60])
            send_message(chat_id, msg, reply_markup=build_keyboard())
            _voice = f"Code ban gaya aur run bhi ho gaya! {result.get('description', '')} " if result.get('success') else "Code mein thodi problem aayi, dubara try kariye!"
            send_jarvis_voice(chat_id, _voice, intent="greeting")
        return

    # ── Handle awaiting GitHub URL ──
    if chat_storage.get(f"awaiting_github_{chat_id}") and CODE_ENGINE_AVAILABLE:
        _gh_url = extract_github_url(text) if CODE_ENGINE_AVAILABLE else None
        if _gh_url:
            chat_storage[f"awaiting_github_{chat_id}"] = False
            send_message(chat_id,
                f"🐙⚡ *Cloning + Installing + Running...*\n"
                f"🔗 _{_gh_url[:60]}_\n"
                f"_Auto-magic in progress..._ ⏳🚀",
                reply_markup=build_keyboard())
            
            result = clone_and_run_github(_gh_url, chat_id)
            msg = format_github_result(result, _gh_url)
            send_message(chat_id, msg, reply_markup=build_keyboard())
            _voice = f"GitHub repo clone ho gaya aur run bhi ho gaya!" if result.get('success') else "Repo mein thodi problem hai, check kariye details!"
            send_jarvis_voice(chat_id, _voice, intent="greeting")
            return
        else:
            send_message(chat_id,
                f"🔗 Ye valid GitHub URL nahi hai.\n"
                f"Format: `https://github.com/user/repo`\n"
                f"_Sahi URL paste kariye_ 🌸",
                reply_markup=build_keyboard())
            return

    # ── Auto-detect GitHub URL in any message ──
    if CODE_ENGINE_AVAILABLE and 'github.com/' in text:
        _gh_url = extract_github_url(text)
        if _gh_url:
            send_message(chat_id,
                f"🐙⚡ *GitHub Repo Detected!*\n"
                f"_Auto-clone + install + run kar rahi hoon..._ ⏳🚀",
                reply_markup=build_keyboard())
            
            result = clone_and_run_github(_gh_url, chat_id)
            msg = format_github_result(result, _gh_url)
            send_message(chat_id, msg, reply_markup=build_keyboard())
            send_jarvis_voice(chat_id,
                f"GitHub repo ka output aa gaya! {'Successfully run ho gaya!' if result.get('success') else 'Kuch issue hai, details dekh lijiye!'}",
                intent="greeting")
            return

    # ── Auto-detect code generation requests ──
    if CODE_ENGINE_AVAILABLE and not chat_storage.get(f"coding_active_{chat_id}"):
        _code_req = detect_code_request(text)
        if _code_req == 'generate':
            # Extract the actual request (remove trigger words)
            import re as _re_temp
            _clean_prompt = _re_temp.sub(
                r'\b(code|program|script|app|project|bot)\s*(banao|bana\s*do|likho|likh\s*do|generate|create|make|build|write|karo)\b',
                '', text, flags=_re_temp.IGNORECASE
            ).strip()
            if not _clean_prompt:
                _clean_prompt = text
            
            send_message(chat_id,
                f"⚡🧠 *JARVIS Code Engine — Generating + Running...*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 _{_clean_prompt[:80]}{'...' if len(_clean_prompt) > 80 else ''}_\n"
                f"_AI code likh rahi hai + auto-install + auto-run..._ ⏳🚀\n"
                f"_Sirf OUTPUT milega — code ki tension nahi!_ 💕",
                reply_markup=build_keyboard())
            
            result = execute_code_autonomous(_clean_prompt, chat_id)
            msg = format_execution_result(result, _clean_prompt[:60])
            send_message(chat_id, msg, reply_markup=build_keyboard())
            
            if result.get('success'):
                _voice = f"Done Boss ji! {result.get('description', 'Code ka output aa gaya!')} Check kariye! 🌸"
            else:
                _voice = "Thodi problem aayi code mein, lekin main dubara try kar sakti hoon. Bataiye kya modify karna hai!"
            send_jarvis_voice(chat_id, _voice, intent="greeting")
            return

    # ════════════════════════════════════════════════════════
    #   💻 JARVIS CODER — Interactive Programming Session
    # ════════════════════════════════════════════════════════
    _coder_triggers = {
        "💻 JARVIS Coder 🚀", "jarvis coder", "/code", "/coder",
        "code banao", "code likho", "programming kar",
        "program banao", "code generate", "code create",
        "app banao", "script banao", "project banao",
        "programming karo", "code karo",
    }
    if text in _coder_triggers or text.lower() in _coder_triggers:
        if CODER_AVAILABLE:
            # Check permission for non-admin
            if ADMIN_SYSTEM_AVAILABLE and not ja_is_admin(chat_id) and not has_feature(chat_id, "coding"):
                result = request_approval(chat_id, "coding", "Wants to use JARVIS Coder")
                if result.get("status") == "pending":
                    send_message(chat_id, 
                        f"🔒 *Permission Required*\n\n"
                        f"💻 JARVIS Coder ke liye Admin approval chahiye.\n"
                        f"📋 Request sent to Boss Deepak Kumar sir!\n\n"
                        f"_Approval milne par access mil jayega_ 🌸",
                        reply_markup=build_keyboard())
                    # Notify admin
                    if result.get("admin_notification"):
                        try:
                            send_message(JA_ADMIN_CHAT_ID, result["admin_notification"])
                        except Exception:
                            pass
                    return
            session = start_coding_session(chat_id)
            _ai_status = "✅ Groq + Gemini (100% FREE)"
            _github_status = "✅ GitHub Connected" if GITHUB_CONNECTED else "⚠️ GitHub not connected"
            send_message(chat_id,
                f"💻🚀 *JARVIS CODER — AI Programming Engine*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧠 *AI:* {_ai_status}\n"
                f"🔗 *GitHub:* {_github_status}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Batao kya banana hai? 🤖\n\n"
                f"_Examples:_\n"
                f"• `Python web scraper for crypto prices`\n"
                f"• `React dashboard for trading`\n"
                f"• `FastAPI server with auth`\n"
                f"• `Telegram bot for reminders`\n\n"
                f"Type your project description:",
                reply_markup=build_keyboard())
            chat_storage[f"coding_active_{chat_id}"] = True
        else:
            send_message(chat_id, "❌ JARVIS Coder module not available.", reply_markup=build_keyboard())
        return

    # Handle active coding session input
    if chat_storage.get(f"coding_active_{chat_id}") and CODER_AVAILABLE:
        _code_text = text.lower().strip()
        
        # Check for coding sub-commands
        if _code_text in ("done", "exit", "cancel", "back", "wapas"):
            chat_storage[f"coding_active_{chat_id}"] = False
            send_message(chat_id, "✅ Coding session ended. Main menu par wapas!", reply_markup=build_keyboard())
            return
        
        if _code_text.startswith("install"):
            send_message(chat_id, "📦 Installing dependencies...", reply_markup=build_keyboard())
            session = get_session(chat_id)
            if session and session.get("project") and session.get("project_dir"):
                ok, result_msg = install_dependencies(session["project"], session["project_dir"])
                send_message(chat_id, result_msg, reply_markup=build_keyboard())
            else:
                send_message(chat_id, "⚠️ Pehle koi code generate karo!", reply_markup=build_keyboard())
            return
        
        if _code_text.startswith(("github", "push", "git push")):
            send_message(chat_id, "🔗 Pushing to GitHub...", reply_markup=build_keyboard())
            session = get_session(chat_id)
            if session and session.get("project") and session.get("project_dir"):
                _parts = text.split()
                _repo = _parts[1] if len(_parts) > 1 else session["project"].get("project_name", f"jarvis-project-{int(time.time())}")
                _desc = session["project"].get("description", "Generated by JARVIS AI Coder")
                ok, result_msg = push_to_github(session["project_dir"], _repo, _desc)
                if ok:
                    send_message(chat_id, f"✅ *GitHub Push Successful!*\n🔗 {result_msg}", reply_markup=build_keyboard())
                else:
                    send_message(chat_id, f"❌ GitHub push failed: {result_msg}", reply_markup=build_keyboard())
            else:
                send_message(chat_id, "⚠️ Pehle koi code generate karo!", reply_markup=build_keyboard())
            return
        
        # Generate code using process_coding_input
        send_message(chat_id, 
            f"💻🧠 *Generating Code...*\n"
            f"_AI soch raha hai..._ ⏳\n\n"
            f"Prompt: _{text[:100]}{'...' if len(text) > 100 else ''}_",
            reply_markup=build_keyboard())
        
        result = process_coding_input(chat_id, text)
        if result and result.get("message"):
            # process_coding_input returns {"message": str, "done": bool}
            send_message(chat_id, result["message"], reply_markup=build_keyboard())
            if not result.get("done"):
                send_message(chat_id, 
                    f"💡 *Commands:*\n"
                    f"• `install` — Install dependencies\n"
                    f"• `github <repo-name>` — Push to GitHub\n"
                    f"• `run` — Run the project\n"
                    f"• Type modifications — Update code\n"
                    f"• `done` — Exit coding mode",
                    reply_markup=build_keyboard())
            else:
                chat_storage[f"coding_active_{chat_id}"] = False
        else:
            send_message(chat_id, "❌ Code generation failed. Try again with a different prompt.", reply_markup=build_keyboard())
        return

    # ════════════════════════════════════════════════════════
    #   👑 JARVIS ADMIN COMMANDS — Boss Deepak Kumar
    # ════════════════════════════════════════════════════════
    if text in ("👑 Admin Dashboard",) or text.lower() in ("/dashboard", "admin dashboard"):
        if ADMIN_SYSTEM_AVAILABLE and ja_is_admin(chat_id):
            dashboard = format_admin_dashboard()
            send_message(chat_id, dashboard, reply_markup=build_keyboard())
        elif ADMIN_SYSTEM_AVAILABLE:
            send_message(chat_id, "🚫 Sirf Boss Deepak Kumar ke liye! 🌸", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Admin system not available.", reply_markup=build_keyboard())
        return

    # /approve command
    if text.lower().startswith("/approve ") and ADMIN_SYSTEM_AVAILABLE:
        if ja_is_admin(chat_id):
            req_id = text.split(maxsplit=1)[1].strip()
            result = approve_request(req_id)
            send_message(chat_id, result["message"], reply_markup=build_keyboard())
            # Notify the user
            if result.get("chat_id"):
                try:
                    send_message(result["chat_id"],
                        f"✅ *Approval Granted!*\n\n"
                        f"Boss Deepak Kumar ne aapka request approve kar diya!\n"
                        f"Feature: {result.get('feature', 'unknown')}\n\n"
                        f"Ab aap isse use kar sakte ho! 🎉",
                        reply_markup=build_keyboard())
                except Exception:
                    pass
        else:
            send_message(chat_id, "🚫 Sirf Admin ke liye!", reply_markup=build_keyboard())
        return

    # /reject command
    if text.lower().startswith("/reject ") and ADMIN_SYSTEM_AVAILABLE:
        if ja_is_admin(chat_id):
            parts = text.split(maxsplit=2)
            req_id = parts[1].strip()
            reason = parts[2] if len(parts) > 2 else ""
            result = reject_request(req_id, reason)
            send_message(chat_id, result["message"], reply_markup=build_keyboard())
            if result.get("chat_id"):
                try:
                    send_message(result["chat_id"],
                        f"❌ *Request Rejected*\n\n"
                        f"Boss ne aapka request reject kiya.\n"
                        f"{'Reason: ' + reason if reason else ''}\n\n"
                        f"_Kuch aur chahiye toh batao_ 🌸",
                        reply_markup=build_keyboard())
                except Exception:
                    pass
        else:
            send_message(chat_id, "🚫 Sirf Admin ke liye!", reply_markup=build_keyboard())
        return

    # /grant command
    if text.lower().startswith("/grant ") and ADMIN_SYSTEM_AVAILABLE:
        if ja_is_admin(chat_id):
            parts = text.split()
            if len(parts) >= 3:
                _target_cid = int(parts[1])
                _feature = parts[2]
                result = grant_feature(_target_cid, _feature)
                send_message(chat_id, result, reply_markup=build_keyboard())
            else:
                send_message(chat_id, "Usage: `/grant <chat_id> <feature>`", reply_markup=build_keyboard())
        else:
            send_message(chat_id, "🚫 Sirf Admin ke liye!", reply_markup=build_keyboard())
        return

    # /upgrade command
    if text.lower().startswith("/upgrade"):
        if ADMIN_SYSTEM_AVAILABLE:
            parts = text.split()
            if ja_is_admin(chat_id) and len(parts) >= 2:
                _target_cid = int(parts[1])
                result = upgrade_user(_target_cid)
                send_message(chat_id, result, reply_markup=build_keyboard())
            elif not ja_is_admin(chat_id):
                # User requesting upgrade for themselves
                result = request_approval(chat_id, "coding", "Requesting Premium upgrade")
                send_message(chat_id, 
                    f"⭐ *Premium Upgrade Request*\n\n"
                    f"Request Boss Deepak Kumar ko bhej diya!\n"
                    f"Jald hi approval milega! 🌸",
                    reply_markup=build_keyboard())
                if result.get("admin_notification"):
                    try:
                        send_message(JA_ADMIN_CHAT_ID, result["admin_notification"])
                    except Exception:
                        pass
        return

    # 👤 User Profile
    if text in ("👤 My Profile",) or text.lower() in ("/profile", "my profile", "meri profile", "mera account"):
        if ADMIN_SYSTEM_AVAILABLE:
            profile = format_user_profile(chat_id)
            send_message(chat_id, profile, reply_markup=build_keyboard())
        else:
            send_message(chat_id, "❌ Profile system not available.", reply_markup=build_keyboard())
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
            # 🧠 GENIUS: Use smart hybrid classification (regex + LLM)
            if GENIUS_AVAILABLE:
                try:
                    intent, confidence = genius_classify(text, chat_id)
                except Exception:
                    intent, confidence = classify_intent(text)
            else:
                intent, confidence = classify_intent(text)
            
            # 🧠 Memory: Save user intent to conversation
            try:
                add_to_conversation(chat_id, "user", text, intent)
            except Exception as e:
                logger.warning(f"[MEMORY] Failed to save user message: {e}")
            
            # 🧠 Mem0: Store in semantic cloud memory
            if MEM0_AVAILABLE:
                try:
                    mem0_add(str(chat_id), text, {"intent": str(intent), "source": "chat"})
                except Exception:
                    pass
            
            # 🧠 GENIUS: Store in semantic memory + track entities
            if GENIUS_AVAILABLE:
                try:
                    entities = extract_entities(text)
                    semantic_memory.store_interaction(chat_id, text, "", intent=intent, 
                        entities=entities.get('stocks', []) + entities.get('crypto', []))
                except Exception:
                    pass
            
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
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        #  🧠 SMART INTENT DETECTION — Catch STOP/START in free-form text
        #  This catches Hindi voice & natural language before AI chat
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        _intent_lower = text.lower()
        _stop_intent_patterns = [
            r'(?:sab|all|सब|सारे?|sabhi|सभी|jitne|जितने).*(?:band|बंद|stop|off|hatao|हटाओ|rok|रोक)',
            r'(?:band|बंद|stop|off).*(?:karo|kar\s*do|करो|कर\s*दो|kar|करें|kijiye|कीजिए)',
            r'(?:notification|alert|नोटिफिकेशन|अलर्ट).*(?:band|बंद|stop|off|hatao|हटाओ|mat|मत|nahi|नहीं)',
            r'(?:mat|मत|nahi|नहीं|na).*(?:bhej|भेज|send|dena|देना)',
            r'(?:stop|band|बंद|rok|रोक).*(?:notification|alert|नोटिफिकेशन|अलर्ट|message|crypto|airdrop)',
            r'(?:airdrop|dextools|crypto|web3).*(?:band|बंद|stop|off|rok|रोक)',
            r'(?:kuch\s*(?:bhi\s*)?(?:mat|nahi)|कुछ\s*(?:भी\s*)?(?:मत|नहीं)).*(?:bhej|भेज|send|dena|देना)',
            r'(?:chup|चुप|silence|mute|quiet)',
        ]
        _start_intent_patterns = [
            r'(?:sab|all|सब|सारे?|sabhi|सभी).*(?:chalu|shuru|start|on|चालू|शुरू)',
            r'(?:chalu|shuru|start|on|चालू|शुरू).*(?:karo|kar\s*do|करो|कर\s*दो)',
            r'(?:notification|alert|नोटिफिकेशन|अलर्ट).*(?:chalu|shuru|start|on|चालू|शुरू)',
            r'(?:phir\s*se|फिर\s*से|wapas|वापस|dobara|दोबारा).*(?:chalu|shuru|on|bhej|चालू|शुरू|भेज)',
        ]
        _detected_stop = any(re.search(p, _intent_lower) for p in _stop_intent_patterns)
        _detected_start = any(re.search(p, _intent_lower) for p in _start_intent_patterns)
        
        if _detected_stop and not _detected_start:
            logger.info(f"[NLU-INTENT] 🧠 Detected STOP intent from: '{text[:60]}'")
            # Execute STOP logic
            chat_storage[f"crypto_alerts_{chat_id}"] = False
            try:
                from data_store import remove_subscriber
                remove_subscriber(chat_id)
            except Exception:
                pass
            try:
                set_user_stopped(chat_id, True)
            except Exception:
                pass
            if OPTIONS_HUNTER_AVAILABLE:
                try:
                    stop_all_crypto_alerts(chat_id)
                except Exception:
                    pass
            send_message(chat_id, (
                f"{greeting}🛑 *बॉस, सब बंद कर दिया!* 🙏\n\n"
                f"✅ Airdrop alerts: *OFF*\n"
                f"✅ DexTools notifications: *OFF*\n"
                f"✅ Web3 signals: *OFF*\n"
                f"✅ Crypto alerts: *OFF*\n"
                f"✅ Market signals: *OFF*\n"
                f"✅ ALL notifications: *OFF*\n\n"
                f"_अब कोई भी notification नहीं आएगा_ 🔇\n"
                f"_वापस शुरू करने के लिए \"🟢 START Crypto Alerts\" दबाइए_ 🌸"
            ), reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, "बॉस, सब notifications बंद कर दिया! अब कोई भी alert नहीं आएगा। जब चाहें START बटन दबा दीजिए।", intent="stop_alerts")
            return
        
        if _detected_start and not _detected_stop:
            logger.info(f"[NLU-INTENT] 🧠 Detected START intent from: '{text[:60]}'")
            chat_storage[f"crypto_alerts_{chat_id}"] = True
            try:
                from data_store import add_subscriber
                add_subscriber(chat_id)
            except Exception:
                pass
            try:
                set_user_stopped(chat_id, False)
            except Exception:
                pass
            if OPTIONS_HUNTER_AVAILABLE:
                try:
                    start_all_crypto_alerts(chat_id)
                except Exception:
                    pass
            send_message(chat_id, (
                f"{greeting}🟢 *बॉस, सब शुरू कर दिया!* 🚀\n\n"
                f"✅ ALL notifications: *ON*\n"
                f"✅ Crypto + Airdrop + DexTools + Web3: *ON*\n\n"
                f"_अब सभी alerts आने लगेंगे!_ 🌸"
            ), reply_markup=build_keyboard())
            send_jarvis_voice(chat_id, "बॉस, सभी notifications शुरू कर दिया! अब सारे alerts आने लगेंगे।", intent="start_alerts")
            return

        # ── Default: Send to JARVIS GENIUS AI (or fallback to ai_chat) ──
        is_voice = chat_storage.pop(f"voice_input_{chat_id}", False)
        send_message(chat_id, f"🤖🧠 *जार्विस GENIUS सोच रही है...* ⏳💕")
        try:
            # 🧠 MULTI-AGENT: Route to specialist if agents available
            agent_response = None
            if AGENTS_AVAILABLE:
                try:
                    routing = route_to_specialist(text)
                    if routing and routing[0][1] > 0.5:
                        specialist = routing[0][0]
                        
                        # Auto-research: gather real data BEFORE specialist answers
                        research_ctx = ""
                        try:
                            research = auto_research(text.split()[-1] if text.split() else text, 
                                                    asset_type=specialist if specialist in ("stock", "crypto") else "auto")
                            research_ctx = format_research_context(research)
                        except Exception:
                            pass
                        
                        result = run_multi_specialist(text, data=research_ctx)
                        if result.get("response") and len(result["response"]) > 30:
                            agent_response = result["response"]
                            specialist_name = result.get("specialist", "general")
                            logger.info(f"[AGENTS] Routed to {specialist_name} (conf={routing[0][1]:.2f})")
                except Exception as e:
                    logger.debug(f"[AGENTS] Specialist routing failed: {e}")

            # 🧠 GENIUS: Use autonomous agent with tool calling & deep reasoning
            if GENIUS_AVAILABLE:
                from ai_chat import _chat_histories
                history = _chat_histories.get(chat_id, [])
                
                # If agent already answered, use it as context for genius
                genius_context = text
                if agent_response:
                    genius_context = f"{text}\n\n[SPECIALIST ANALYSIS]:\n{agent_response[:600]}"
                
                response = genius_chat(genius_context, chat_id, intent="chat", chat_history=history)
                
                # If genius gave a short/generic response but agent had good one, prefer agent
                if agent_response and len(response) < 50 and len(agent_response) > 100:
                    response = agent_response
                
                # Store in ai_chat history too for consistency
                _chat_histories.setdefault(chat_id, [])
                _chat_histories[chat_id].append({"role": "user", "content": text})
                _chat_histories[chat_id].append({"role": "assistant", "content": response})
                if len(_chat_histories[chat_id]) > 20:
                    _chat_histories[chat_id] = _chat_histories[chat_id][-12:]
                
                # Check response quality
                try:
                    is_good, quality_note = verify_response_quality(text, response)
                    if not is_good:
                        logger.warning(f"[GENIUS] Quality issue: {quality_note}")
                        # If quality is bad and agent had a response, use agent's
                        if agent_response and len(agent_response) > 50:
                            response = agent_response
                except Exception:
                    pass
            elif agent_response:
                # No genius available but agent answered
                response = agent_response
            else:
                # Fallback to regular ai_chat
                response = ai_chat(text, chat_id)
            
            send_message(chat_id, f"{greeting}{response}", reply_markup=build_keyboard())
            
            # 🧠 Memory: Save response (old + new)
            if JARVIS_AVAILABLE:
                try:
                    add_to_conversation(chat_id, "jarvis", response[:300], "chat")
                except Exception as e:
                    logger.warning(f"[MEMORY] Failed to save JARVIS response: {e}")
            if MEMORY_PRO_AVAILABLE:
                try:
                    remember_message(chat_id, "assistant", response[:500], "chat")
                except:
                    pass
            
            # 🧠 GENIUS: Suggest next action
            if GENIUS_AVAILABLE:
                try:
                    suggestion = get_next_suggestion(chat_id, intent if 'intent' in dir() else 'chat')
                    if suggestion:
                        send_message(chat_id, f"💡 _{suggestion}_")
                except Exception:
                    pass
            
            # 🎤 JARVIS speaks the response
            send_jarvis_voice(chat_id, response, intent="chat", is_voice_input=is_voice)
        except Exception as e:
            logger.error(f"AI chat failed: {e}", exc_info=True)
            # Emergency fallback
            try:
                response = ai_chat(text, chat_id)
                send_message(chat_id, f"{greeting}{response}", reply_markup=build_keyboard())
            except Exception:
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
    # ━━━ FLUSH STALE UPDATES ON STARTUP ━━━
    # Skip all pending updates from when bot was offline
    # This prevents "buttons not responding" due to processing old presses
    try:
        flush_r = requests.get(f"{API_URL}/getUpdates", params={"offset": -1, "timeout": 1}, timeout=10)
        flush_js = flush_r.json()
        stale = flush_js.get("result", [])
        if stale:
            last_id = stale[-1]["update_id"]
            # Confirm offset to skip all stale updates
            requests.get(f"{API_URL}/getUpdates", params={"offset": last_id + 1, "timeout": 1}, timeout=10)
            logger.info(f"[POLL] ✅ Flushed stale updates (last_id={last_id}) — fresh start!")
        else:
            logger.info("[POLL] No stale updates to flush")
    except Exception as e:
        logger.warning(f"[POLL] Flush failed (non-critical): {e}")

    offset = None
    backoff = 1          # Start at 1 second
    MAX_BACKOFF = 120    # Max 2 minutes between retries
    consecutive_errors = 0
    total_updates = 0
    start_time = time.time()

    # ═══ L1 UPGRADE: ThreadPoolExecutor replaces unbounded threads ═══
    from concurrent.futures import ThreadPoolExecutor
    _executor = ThreadPoolExecutor(max_workers=24, thread_name_prefix="BotWorker")

    logger.info("[POLL] 🚀 Polling loop started with ThreadPoolExecutor(24) + exponential backoff")

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
                # ═══ L1: Submit to thread pool instead of unbounded Thread() ═══
                def _process_update(update):
                    try:
                        handle_update(update)
                    except Exception as e:
                        logger.error(f"[POLL] Error handling update: {e}", exc_info=True)
                _executor.submit(_process_update, u)

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

        time.sleep(0.05)  # Ultra-fast polling — near-instant response


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
                                # Respect STOP flag — skip users who stopped alerts
                                if is_user_alerts_stopped(cid):
                                    continue
                                if OPTIONS_HUNTER_AVAILABLE:
                                    try:
                                        if not is_crypto_alerts_enabled(cid):
                                            continue
                                    except Exception:
                                        pass
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
    
    # Start Prediction Verification background thread (self-learning)
    if PREDICTION_TRACKER_AVAILABLE:
        def prediction_verify_loop():
            """Background: verify predictions every 2 minutes for rapid learning."""
            logger.info("📊 Prediction Tracker STARTED — RAPID 2-min self-learning loop")
            while not auto_flag.is_set():
                try:
                    stats = verify_predictions(max_verify=50)
                    if stats.get("verified", 0) > 0:
                        logger.info(f"[TRACKER] Verified {stats['verified']} predictions: "
                                   f"{stats.get('correct', 0)} correct, {stats.get('wrong', 0)} wrong")
                    time.sleep(120)  # 2 minutes — rapid verification
                except Exception as e:
                    logger.error(f"[TRACKER] Verify loop error: {e}")
                    time.sleep(60)
        def _make_tracker_thread():
            return threading.Thread(target=prediction_verify_loop, daemon=True, name="PredictionTracker")
        tracker_thread = _make_tracker_thread()
        tracker_thread.start()
        _register_main_thread("prediction_tracker", tracker_thread, _make_tracker_thread, "📊 Prediction Tracker")
        logger.info("[STARTUP] 📊 Prediction Tracker started (self-learning)")
        def prediction_verify_loop():
            """Background: verify predictions every 2 minutes for rapid learning."""
            logger.info("📊 Prediction Tracker STARTED — RAPID 2-min self-learning loop")
            while not auto_flag.is_set():
                try:
                    stats = verify_predictions(max_verify=50)
                    if stats.get("verified", 0) > 0:
                        logger.info(f"[TRACKER] Verified {stats['verified']} predictions: "
                                   f"{stats.get('correct', 0)} correct, {stats.get('wrong', 0)} wrong")
                    time.sleep(120)  # 2 minutes — rapid verification
                except Exception as e:
                    logger.error(f"[TRACKER] Verify loop error: {e}")
                    time.sleep(60)
        
        def _make_tracker_thread():
            return threading.Thread(target=prediction_verify_loop, daemon=True, name="PredictionTracker")
        
        tracker_thread = _make_tracker_thread()
        tracker_thread.start()
        _register_main_thread("prediction_tracker", tracker_thread, _make_tracker_thread, "📊 Prediction Tracker")
        logger.info("[STARTUP] 📊 Prediction Tracker started (self-learning)")
    
    # Start JARVIS Monitor (auto price alerts + rug detection + keep-alive + new token alerts + Web3 signals)
    if MONITOR_AVAILABLE:
        try:
            _owner_id = int(os.environ.get("TEST_CHAT_ID", "0"))
            start_monitor(
                send_fn=guarded_alert_send,
                voice_fn=guarded_voice_send,
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
            # Set alert callback so airdrop hunter can send messages (GUARDED — respects STOP)
            set_alert_callback(guarded_alert_send)
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
            def _guarded_dextools_send(cid, txt):
                actual_cid = int(os.environ.get("TEST_CHAT_ID", "0")) if cid is None else cid
                guarded_alert_send(actual_cid, txt)
            set_dextools_alert_callback(_guarded_dextools_send)
            start_dextools_scanner()
            logger.info("[STARTUP] 🔥 DexTools Scanner LAUNCHED — multi-chain alerts every 3 min!")
        except Exception as e:
            logger.error(f"[STARTUP] DexTools Scanner start failed: {e}")

    # ⚡ Start Solana TX Monitor — FREE blockchain monitoring
    if SOLANA_ENGINE_AVAILABLE:
        try:
            start_tx_monitor(
                alert_fn=guarded_alert_send,
                token_fn=guarded_alert_send,
            )
            logger.info("[STARTUP] ⚡ Solana TX Monitor LAUNCHED — 24/7 FREE blockchain monitoring!")
        except Exception as e:
            logger.error(f"[STARTUP] Solana TX Monitor start failed: {e}")

    # 💰 Start Payment System — Auto-Rebalance Engine
    if PAYMENT_AVAILABLE:
        try:
            set_rebalance_callback(guarded_alert_send)
            start_auto_rebalance()
            logger.info("[STARTUP] 💰🔐 Payment System + Auto-Rebalance LAUNCHED!")
        except Exception as e:
            logger.error(f"[STARTUP] Payment System start failed: {e}")

    # 🚀 Start Real Trader — On-Chain Auto-Trade Engine
    if REAL_TRADER_AVAILABLE:
        try:
            set_trade_callback(guarded_alert_send)
            start_auto_trader()
            logger.info("[STARTUP] 🚀💰 REAL TRADER — Jupiter DEX Auto-Trade Engine LAUNCHED!")
        except Exception as e:
            logger.error(f"[STARTUP] Real Trader start failed: {e}")

    # 🤖 Start Personal Agent — Reminders Engine
    if AGENT_AVAILABLE:
        try:
            set_reminder_callback(guarded_alert_send)
            start_reminder_engine()
            logger.info("[STARTUP] 🤖🧠 Personal AI Agent + Reminders LAUNCHED!")
        except Exception as e:
            logger.error(f"[STARTUP] Agent start failed: {e}")

    # Start JARVIS SPOC — System health monitoring for Boss
    if SPOC_AVAILABLE:
        try:
            _owner_id = int(os.environ.get("TEST_CHAT_ID", "0"))
            start_spoc(
                send_fn=guarded_alert_send,
                voice_fn=guarded_voice_send,
                token=TELEGRAM_TOKEN
            )
            logger.info("[STARTUP] 🧠 JARVIS SPOC started (system health + daily briefing)")
        except Exception as e:
            logger.error(f"[STARTUP] SPOC start failed: {e}")

    # Start JARVIS Super Brain — Worldwide news + proactive intelligence
    if SUPER_BRAIN_AVAILABLE:
        try:
            start_super_brain(
                send_fn=guarded_alert_send,
                voice_fn=guarded_voice_send,
                token=TELEGRAM_TOKEN
            )
            logger.info("[STARTUP] 🧠⚡ JARVIS Super Brain started (news + intelligence + SPOC)")
        except Exception as e:
            logger.error(f"[STARTUP] Super Brain start failed: {e}")

    # ═══════════════════════════════════════════════════════════
    #  🧠⚡ MARKET BRAIN 2-MIN NOTIFIER
    #  Sends NIFTY/SENSEX Super Brain analysis every 2 min
    #  ONLY during 9:15 AM → 3:30 PM IST, Mon-Fri
    #  BYPASSES crypto stop — uses market_brain_send()
    # ═══════════════════════════════════════════════════════════
    _market_brain_running = True
    _market_brain_owner = int(os.environ.get("TEST_CHAT_ID", os.environ.get("OWNER_CHAT_ID", "5647898018")))

    def _market_brain_loop():
        """Background thread: Super Brain notification every 2 minutes during market hours."""
        logger.info("[MARKET-BRAIN] 🧠⚡ Market Brain Notifier STARTED — 2-min cycle, 9:15-15:30 IST Mon-Fri")
        _cycle = 0
        while _market_brain_running:
            try:
                now = datetime.now(IST)
                weekday = now.weekday()  # 0=Mon, 6=Sun
                hour = now.hour
                minute = now.minute
                time_mins = hour * 60 + minute

                market_open = 9 * 60 + 15    # 9:15 AM
                market_close = 15 * 60 + 30   # 3:30 PM

                # Skip weekends (Saturday=5, Sunday=6)
                if weekday >= 5:
                    # Sleep longer on weekends
                    logger.debug("[MARKET-BRAIN] Weekend — sleeping 5 min")
                    time.sleep(300)
                    continue

                # Check if within market hours
                if time_mins < market_open or time_mins > market_close:
                    # Before market: check every 2 min if close to open
                    if time_mins >= (market_open - 15):
                        logger.debug(f"[MARKET-BRAIN] Pre-market ({now.strftime('%H:%M')}) — waiting for 9:15")
                        time.sleep(60)
                    else:
                        # Far from market hours — sleep 5 min
                        time.sleep(300)
                    continue

                # ══ MARKET HOURS — Send Super Brain analysis ══
                _cycle += 1
                logger.info(f"[MARKET-BRAIN] 📊 Cycle #{_cycle} — {now.strftime('%H:%M IST')}")

                try:
                    # Try full Super Brain with AI
                    if NIFTY_BRAIN_AVAILABLE:
                        from nifty_super_brain import get_complete_dashboard, get_ai_market_verdict
                        dashboard = get_complete_dashboard()

                        # Every 5th cycle (~10 min), add AI verdict too
                        if _cycle % 5 == 1:
                            ai_verdict = get_ai_market_verdict(dashboard)
                            full_msg = f"{dashboard}\n\n{'═' * 30}\n\n{ai_verdict}"
                        else:
                            full_msg = dashboard

                        header = (
                            f"🧠⚡ *MARKET BRAIN — Auto Update #{_cycle}*\n"
                            f"⏰ {now.strftime('%I:%M %p IST')} | "
                            f"{'Mon Tue Wed Thu Fri'.split()[weekday]}\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        )
                        market_brain_send(_market_brain_owner, header + full_msg)

                        # Voice every 10th cycle (~20 min)
                        if _cycle % 10 == 1:
                            try:
                                market_brain_voice_send(
                                    _market_brain_owner,
                                    f"Boss, market brain update number {_cycle}. "
                                    f"Time hai {now.strftime('%I:%M %p')}. "
                                    f"Full analysis screen pe dekh lo!",
                                    intent="market_summary"
                                )
                            except Exception:
                                pass
                    else:
                        # Fallback: basic live price
                        try:
                            from live_index_engine import get_live_price
                            nifty = get_live_price("NIFTY")
                            sensex = get_live_price("SENSEX")
                            n_price = nifty.get("price", 0) if nifty else 0
                            n_chg = nifty.get("change_pct", 0) if nifty else 0
                            s_price = sensex.get("price", 0) if sensex else 0
                            s_chg = sensex.get("change_pct", 0) if sensex else 0
                            n_icon = "🟢" if n_chg >= 0 else "🔴"
                            s_icon = "🟢" if s_chg >= 0 else "🔴"
                            msg = (
                                f"🧠 *Market Brain #{_cycle}* — {now.strftime('%I:%M %p IST')}\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"{n_icon} NIFTY: {n_price:,.2f} ({n_chg:+.2f}%)\n"
                                f"{s_icon} SENSEX: {s_price:,.2f} ({s_chg:+.2f}%)\n"
                            )
                            market_brain_send(_market_brain_owner, msg)
                        except Exception as e:
                            logger.error(f"[MARKET-BRAIN] Fallback price error: {e}")

                except Exception as e:
                    logger.error(f"[MARKET-BRAIN] Analysis error: {e}")
                    market_brain_send(_market_brain_owner,
                        f"⚠️ *Market Brain #{_cycle}* — {now.strftime('%I:%M %p IST')}\n"
                        f"Analysis error: {str(e)[:100]}\nRetrying in 2 min...")

                # Sleep 2 minutes
                time.sleep(120)

            except Exception as e:
                logger.error(f"[MARKET-BRAIN] Loop error: {e}", exc_info=True)
                time.sleep(60)

    def _make_market_brain_thread():
        return threading.Thread(target=_market_brain_loop, daemon=True, name="MarketBrainNotifier")

    _mb_thread = _make_market_brain_thread()
    _mb_thread.start()
    _register_main_thread("market_brain", _mb_thread, _make_market_brain_thread, "🧠⚡ Market Brain Notifier")
    logger.info("[STARTUP] 🧠⚡ Market Brain 2-min Notifier started (9:15-15:30 IST, Mon-Fri)")

    # ═══════════════════════════════════════════════════════════
    #  🌐 START WEB SERVER — Mini App + API on port 8000
    # ═══════════════════════════════════════════════════════════
    try:
        from jarvis_admin import start_web_server
        _web_port = int(os.environ.get("PORT", "8000"))
        _web_thread = start_web_server(port=_web_port)
        logger.info(f"[STARTUP] 🌐 Web Server started on port {_web_port} (Mini App + API)")
    except Exception as e:
        logger.error(f"[STARTUP] ⚠️ Web Server start failed: {e}")

    # Send JARVIS startup message
    test_chat_id = os.environ.get("TEST_CHAT_ID")
    if test_chat_id:
        try:
            _phantom_line = f"👻 *Phantom Wallet:* `{OWNER_WALLET[:8]}...{OWNER_WALLET[-4:]}` ✅\n" if PHANTOM_AVAILABLE else ""
            
            # Count active modules dynamically
            _avail_flags = [
                JARVIS_AVAILABLE, VOICE_AVAILABLE, NIFTY_BRAIN_AVAILABLE,
                OPTIONS_HUNTER_AVAILABLE, OPTIONS_AVAILABLE, SCALP_AVAILABLE,
                GOPLUS_AVAILABLE, GLOBAL_AVAILABLE, COINDCX_AVAILABLE,
                MEGA_SCANNER_AVAILABLE, MARKET_BRAIN_AVAILABLE, SUPER_ENGINE_AVAILABLE,
                AI_SIGNALS_AVAILABLE, ULTRA_AI_AVAILABLE, CRYPTO_INTEL_AVAILABLE,
                PHANTOM_AVAILABLE, AIRDROP_AVAILABLE, DEXTOOLS_AVAILABLE,
                MONITOR_AVAILABLE, SUPER_BRAIN_AVAILABLE, SPOC_AVAILABLE,
                SECURITY_AVAILABLE, ROCKET_AVAILABLE, QR_WALLET_AVAILABLE,
                REAL_TRADER_AVAILABLE, OI_TRAP_BRAIN_AVAILABLE,
            ]
            active_mod_count = sum(1 for f in _avail_flags if f)
            
            import threading as _t
            bg_count = len([t for t in _t.enumerate() if t.daemon and t.is_alive()])
            
            startup_msg = (
                f"⚡🤖 *R.A.M. L.A.L. SMART AI SYSTEM* 🤖⚡\n"
                f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
                f"┃  🧠 *BOOT / INITIALIZATION*       ┃\n"
                f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"*</> JARVIS Smart AI Setup Getting Ready...*\n\n"
                f"╔══════════════════════════════╗\n"
                f"║  📦 AI Modules    : *{active_mod_count}*  LOADED     ║\n"
                f"║  ⚙️ BG Services   : *{bg_count}*  RUNNING     ║\n"
                f"║  🎯 Commands      : *250+*  READY     ║\n"
                f"║  🧠 AI Models     : *6*  ACTIVE       ║\n"
                f"║  🔊 Voice Engine  : Andrew LIVE      ║\n"
                f"║  📡 Status        : *100% ONLINE* ✅  ║\n"
                f"╚══════════════════════════════╝\n\n"
                f"🧠 *AI CORE:*\n"
                f"✅ JARVIS Brain — *ACTIVE* 🌸\n"
                f"✅ NLU Intent (95+ intents) — *ACTIVE*\n"
                f"✅ Voice (Kore) — {'*ACTIVE* 🎤' if VOICE_AVAILABLE else '*OFF*'}\n"
                f"✅ Memory — *ACTIVE* 💾\n"
                f"✅ Super Memory — {'*ACTIVE* 🧠💾' if MEMORY_PRO_AVAILABLE else '*OFF*'}\n"
                f"✅ Super Brain — {'*ACTIVE* 🧠⚡' if SUPER_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Position Tracker — {'*ACTIVE* 📊' if MEMORY_PRO_AVAILABLE else '*OFF*'}\n\n"
                f"📊 *MARKET + OPTIONS:*\n"
                f"✅ Stock ML (6 models) — *ACTIVE*\n"
                f"✅ OI Trap Brain (NSE+BSE) — {'*ACTIVE* 🔥' if OI_TRAP_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ NIFTY Super Brain — {'*ACTIVE* 🇮🇳' if NIFTY_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Options Pro (Strike) — {'*ACTIVE* 🎯' if OPTIONS_PRO_AVAILABLE else '*OFF*'}\n"
                f"✅ Options Hunter (₹2-₹30) — {'*ACTIVE* 💰' if OPTIONS_HUNTER_AVAILABLE else '*OFF*'}\n"
                f"✅ Global Market Brain — {'*ACTIVE* 🌍' if GLOBAL_AVAILABLE else '*OFF*'}\n\n"
                f"🪙 *CRYPTO + TRADING:*\n"
                f"✅ 5-Chain Scanner — *ACTIVE*\n"
                f"✅ Rocket Scanner — {'*ACTIVE* 🚀' if ROCKET_AVAILABLE else '*OFF*'}\n"
                f"✅ Real Trader (Jupiter DEX) — {'*ACTIVE* 💰' if REAL_TRADER_AVAILABLE else '*OFF*'}\n"
                f"✅ DexTools Multi-Chain — {'*ACTIVE* 🔥' if DEXTOOLS_AVAILABLE else '*OFF*'}\n"
                f"✅ Airdrop Hunter — {'*ACTIVE* 🎁' if AIRDROP_AVAILABLE else '*OFF*'}\n\n"
                f"⚡ *CODE ENGINE + ALIEN TECH:*\n"
                f"✅ Code Engine (Auto-Run) — {'*ACTIVE* ⚡' if CODE_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ GitHub Runner (Clone+Run) — {'*ACTIVE* 🐙' if CODE_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ AI Auto-Fix (Error→Fix→Run) — {'*ACTIVE* 🔧' if CODE_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ JARVIS Coder (Interactive) — {'*ACTIVE* 💻' if CODER_AVAILABLE else '*OFF*'}\n\n"
                f"� *NUCLEAR TRADING ARSENAL:*\n"
                f"✅ Chart Engine (Pro Charts) — {'*ACTIVE* 📊' if CHART_ENGINE_AVAILABLE else '*OFF*'}\n"
                f"✅ Smart Screener (90 stocks) — {'*ACTIVE* 🔍' if SCREENER_AVAILABLE else '*OFF*'}\n"
                f"✅ News Brain (RSS+Sentiment) — {'*ACTIVE* 📰' if NEWS_BRAIN_AVAILABLE else '*OFF*'}\n"
                f"✅ Backtester Pro (RSI/MACD/BB) — {'*ACTIVE* 🔬' if BACKTESTER_AVAILABLE else '*OFF*'}\n"
                f"✅ P&L Journal (Trade Diary) — {'*ACTIVE* 📋' if PNL_JOURNAL_AVAILABLE else '*OFF*'}\n"
                f"✅ Intraday Scanner (50 stocks) — {'*ACTIVE* ⚡' if INTRADAY_SCANNER_AVAILABLE else '*OFF*'}\n"
                f"✅ Futures Brain (PCR+MaxPain) — {'*ACTIVE* 📊' if FUTURES_BRAIN_AVAILABLE else '*OFF*'}\n\n"
                f"�🛡️ *PROTECTION:*\n"
                f"✅ Security Shield — {'*ACTIVE* 🛡️' if SECURITY_AVAILABLE else '*OFF*'}\n"
                f"✅ Thread Supervisor — *ACTIVE* ♻️\n"
                f"✅ Auto-Restart — *ACTIVE*\n"
                f"{_phantom_line}\n"
                f"⏰ {datetime.now(IST).strftime('%I:%M %p IST, %d %b %Y')}\n\n"
                f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
                f"┃ ✅ *ALL SYSTEMS OPERATIONAL*      ┃\n"
                f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n"
                f"🧠⚡ *RAM LAL HOON NA, BOSS!* ⚡🧠"
            )
            send_message(int(test_chat_id), startup_msg, reply_markup=build_keyboard())
            # Send Mini App button
            _mini_url = os.environ.get("MINI_APP_URL", "").rstrip("/")
            if _mini_url:
                _inline_kb = {
                    "inline_keyboard": [
                        [{"text": "🚀 Open JARVIS Trading App", "web_app": {"url": f"{_mini_url}/miniapp"}}],
                    ]
                }
                send_message(int(test_chat_id), "👇 *Open the Real-Time Trading Dashboard:*", reply_markup=_inline_kb)
            # Send startup voice in background thread (non-blocking)
            def _startup_voice():
                try:
                    send_jarvis_voice(int(test_chat_id), "RAM LAL Smart AI System online! Boss Deepak sir, sabhi systems 100 percent active hain! Aaj se Code Engine bhi live hai — Aap bolo code banao, main khud generate karungi, install karungi aur run karke sirf output dungi! GitHub se bhi direct run kar sakti hoon! OI Trap Brain, Options Super Signal, Real Solana Trader, sab LIVE hai! Voice Andrew active hai, super awesome very cute aur respected! Main hoon na boss! Jai Shri Ram!", intent="greeting")
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
