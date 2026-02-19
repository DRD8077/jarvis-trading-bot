"""
🚀 JARVIS Mini App API v6.0 — MEGA INTEGRATED Trading Platform
═══════════════════════════════════════════════════════════════════
EVERY project engine connected. REAL data. REAL-TIME.
"""
import os,json,logging,asyncio,time,math,traceback
from datetime import datetime,timezone,timedelta
from typing import Optional,Dict,List,Any
from fastapi import APIRouter,Request,Query,WebSocket,WebSocketDisconnect
from fastapi.responses import JSONResponse,StreamingResponse

logger=logging.getLogger("miniapp-api-v6")
IST=timezone(timedelta(hours=5,minutes=30))
_cache:Dict[str,Any]={}
_cache_ts:Dict[str,float]={}
def _cached(k,ttl=15):
    if k in _cache and(time.time()-_cache_ts.get(k,0))<ttl:return _cache[k]
    return None
def _set_cache(k,d):_cache[k]=d;_cache_ts[k]=time.time()
async def _t(fn,*a):
    """Run sync function in thread to prevent blocking the event loop."""
    return await asyncio.to_thread(fn,*a)
def _sanitize(o):
    if isinstance(o,float):
        if math.isnan(o)or math.isinf(o):return 0
        return o
    if isinstance(o,dict):return{k:_sanitize(v)for k,v in o.items()}
    if isinstance(o,(list,tuple)):return[_sanitize(v)for v in o]
    return o

class SafeJSON(JSONResponse):
    def render(self,content:Any)->bytes:
        return json.dumps(_sanitize(content),ensure_ascii=False,default=str).encode("utf-8")

router=APIRouter(prefix="/api/miniapp",tags=["MiniApp-v6"],default_response_class=SafeJSON)

def _si(mod,names):
    out={}
    try:
        m=__import__(mod)
        for n in names:out[n]=getattr(m,n,None)
    except Exception as e:
        logger.warning(f"Import {mod}: {e}")
        for n in names:out[n]=None
    return out

_dex=_si("dex_engine",["dex_search","dex_trending","dex_get_token","dex_new_pairs","cg_prices","cg_trending","cg_market_data","cg_fear_greed","pumpfun_trending","pumpfun_new_coins","jupiter_price","get_nse_indices","get_india_vix","fetch_crypto_news","fetch_india_news","find_dip_gems","get_full_market_snapshot","cmc_top_listings","cmc_global_metrics","dex_boosted_tokens","dex_token_profiles"])
_brain=_si("jarvis_brain",["jarvis_chat","analyze_token","generate_briefing","clear_memory","get_conversation_history","stream_chat","get_available_models","get_memory_stats","get_user_facts","get_active_positions","get_prediction_accuracy","search_memory"])
_sniper=_si("auto_sniper",["get_manager","get_all_strategies","scan_for_gems"])
_sec=_si("security_middleware",["validate_telegram_init_data","is_admin","sanitize_input"])
_crypto=_si("crypto_engine",["scan_pump_trending","scan_pump_newest","scan_trending_gems","scan_pump_top_mcap","get_top_boosted_tokens","get_latest_token_profiles","calculate_gem_score","get_sol_inr_price","usd_to_inr"])
_india_stock=_si("indian_stock_super_engine",["indian_stock_super_analysis","recommend_best_options"])
_nse=_si("nse_live_engine",["fetch_live_option_chain","get_live_spot","get_atm_otm_analysis"])
_options=_si("options_engine",["generate_option_chain","recommend_strategy","build_straddle","build_strangle","calculate_iv_rank_percentile"])
_phantom=_si("phantom_wallet",["connect_wallet","disconnect_wallet","get_wallet","is_wallet_connected","generate_phantom_connect_link","fetch_wallet_tokens","resolve_token_prices"])
_trader=_si("auto_trader",["start_auto_trader","stop_auto_trader","get_trader_status","get_available_gems","get_performance_report","get_all_strategies"])
_bse=_si("buy_sell_engine",["generate_buy_sell_signal","get_stock_signal","get_crypto_signal","scan_nifty_signals"])
_portfolio=_si("portfolio_tracker",["get_portfolio","calculate_portfolio_pnl","get_trade_history","add_holding","sell_holding","get_active_price_alerts","add_price_alert"])
_risk=_si("risk_manager",["calculate_position_size","calculate_risk_reward","kelly_from_real_trades","calculate_investment_plan"])
_ml=_si("ml_predictor",["predict_index_direction","predict_with_regime"])
_ai_sig=_si("ai_signals",["full_technical_analysis","batch_signals","quick_signal"])
_candle=_si("candle_analyzer",["analyze_index","multi_timeframe_pattern_scan"])
_coindcx=_si("coindcx_engine",["get_all_web3_prices","get_web3_gainers_losers","scan_all_web3_signals","search_web3_token","get_tokens_by_category"])
_global=_si("global_candle_engine",["analyze_all_global_markets","analyze_us_markets","analyze_asian_markets","get_india_prediction_from_global"])
_airdrop=_si("airdrop_hunter",["scan_all_airdrops","get_new_airdrop_alerts","scan_solana_airdrops"])
_rug=_si("rug_detector",["analyze_rug_risk","check_token_rug_risk","check_goplus_security"])
_pred=_si("prediction_tracker",["get_accuracy_report"])
_nifty=_si("nifty_super_brain",["get_fii_dii_data","get_india_vix","get_pcr_data","calculate_pivot_levels","get_gift_nifty","get_sector_heatmap","get_oi_buildup","get_complete_dashboard","get_ai_market_verdict","get_super_brain_analysis"])
_oi=_si("oi_trap_brain",["fetch_option_chain","detect_traps","find_budget_plays","get_options_super_signal"])
_power=_si("india_power_predictor",["power_predict"])
_regime=_si("market_regime",["detect_market_regime","get_regime_quick"])
_cross=_si("cross_asset_engine",["scan_all_correlations","get_correlation_insight"])
_intel=_si("crypto_intelligence",["analyze_token_full","get_top_crypto_picks","get_user_watchlist","add_to_watchlist"])
_news_brain=_si("jarvis_news_brain",["get_latest_news","get_stock_news","get_breaking_news","get_news_sentiment_score"])
_payment=_si("payment_system",["get_user_wallet","create_deposit_request","confirm_deposit","create_withdrawal_request","process_withdrawal","get_transaction_history","get_pending_transactions","update_user_payment_info","update_wallet_balance"])
_code_engine=_si("jarvis_code_engine",["detect_code_request","extract_github_url","execute_code_autonomous","clone_and_run_github","execute_raw_code","format_execution_result","format_github_result"])

# ═══ NEWLY CONNECTED ENGINES (Phase 9 — Full Integration) ═══
_whale=_si("whale_alert",["detect_whale_activity_from_dex","scan_whale_activity_trending","format_whale_report","check_helius_transactions"])
_web3=_si("web3_rocket_scanner",["fetch_dex_trending_pairs","fetch_dex_new_pairs","search_dex_token","fetch_pump_hot_tokens","fetch_coindcx_hot_tokens","scan_top_rockets","scan_new_launches","quick_gem_check"])
_solana=_si("solana_engine",["get_sol_balance","get_all_token_balances","resolve_token_metadata","get_recent_transactions","get_transaction_detail","swap_token","get_token_price_jupiter"])
_suncrypto=_si("suncrypto_engine",["get_coindcx_tickers","get_coindcx_markets","get_all_inr_prices","get_top_inr_gainers","get_top_inr_losers","get_inr_price","search_inr_token"])
_sentiment=_si("sentiment_engine",["analyze_news_sentiment","score_headline_sentiment","fetch_news_headlines"])
_voice=_si("voice_engine",["generate_voice_response","text_to_speech_ogg","clean_text_for_speech"])
_tracker=_si("trade_tracker",["log_prediction","verify_predictions","get_accuracy_stats","get_prediction_history"])
_pnl=_si("jarvis_pnl_journal",["log_trade","close_trade","get_daily_pnl","get_weekly_pnl","get_monthly_pnl","get_all_trades","get_trade_stats","format_pnl_report"])
_screener=_si("jarvis_screener_pro",["run_full_screener","screen_rsi_oversold","screen_rsi_overbought","screen_volume_breakout","screen_gap_up","screen_52w_high","screen_bullish_crossover","screen_momentum"])
_intraday=_si("jarvis_intraday_scanner",["run_intraday_scan","scan_breakouts","scan_volume_spikes","scan_momentum"])
_chart=_si("jarvis_chart_engine",["generate_chart","generate_multi_indicator_chart","fetch_chart_data"])
_futures=_si("jarvis_futures_brain",["get_pcr","get_max_pain","get_futures_basis","get_india_vix","get_straddle_premium","get_oi_distribution","get_complete_futures_dashboard"])
_opts_pro=_si("jarvis_options_pro",["get_strike_price","get_nearby_options","get_full_chain_summary","parse_option_query"])
_mkt_brain=_si("jarvis_market_brain",["detect_market_type","extract_token_from_message","analyze_indian_stock_deep","analyze_crypto_token_deep"])
_super_brain=_si("jarvis_super_brain",["fetch_all_news","format_news_digest","get_market_intelligence","format_jarvis_briefing"])
_ultra=_si("jarvis_ultra_ai",["ultra_predict","token_health_score","calculate_price_targets","smart_money_flow","liquidity_health","assess_rug_risk"])
_hunter=_si("nifty_options_hunter",["get_user_prefs","set_user_pref"])
_otm_atm=_si("otm_atm_engine",["get_live_spot","get_atm_options","get_otm_options","calculate_greeks","get_full_atm_otm_analysis"])
_live_idx=_si("live_index_engine",["get_live_price","generate_index_option_chain","calculate_investment_options","analyze_2min_candle"])
_cdcx_mega=_si("coindcx_mega_scanner",["mega_scan_all","scan_volume_breakout","scan_bullish_patterns","scan_momentum_plays"])
_dextools=_si("dextools_engine",["get_token_info","get_token_price","get_hot_pairs","search_pairs","get_pair_info"])
_global_mkt=_si("global_market_analyzer",["analyze_global_markets","get_global_summary","predict_india_from_global"])
_angel=_si("angelone_engine",["login_angel","get_ltp","place_order","get_positions","get_holdings","get_order_book"])
_ml_pipe=_si("ml_pipeline",["predict_for_symbol","train_model","get_model_accuracy"])
_mem_pro=_si("jarvis_memory_pro",["remember","recall","get_all_memories","clear_memories","search_memories","get_memory_summary"])
_mega=_si("jarvis_mega_trader",["start_mega_trader","stop_mega_trader","get_mega_trader_status","get_live_scan_results","get_portfolio_inr","scan_all_sources","score_gem","check_rug_safety","transfer_to_phantom","get_transfer_history"])
_real_trader=_si("jarvis_real_trader",["create_trading_wallet","get_trading_wallet","buy_token","sell_token","enable_auto_trade","disable_auto_trade","get_live_portfolio","format_trading_wallet","format_live_portfolio","format_trade_history","SOLANA_SDK_AVAILABLE"])
_conqueror=_si("jarvis_conqueror_trader",["start_conqueror","stop_conqueror","get_conqueror_status","get_live_scan","get_portfolio_inr","scan_all_gems","ai_score_gem","deep_rug_check","set_phantom_address","get_phantom_address","transfer_to_phantom","auto_withdraw_profits","start_deposit_watcher","stop_deposit_watcher"])

# ═══ NEW SUPER ENGINES (Phase 10 — Voice + Intelligence + Gemini + Auth + OTA) ═══
_hindi_voice=_si("jarvis_hindi_voice",["hindi_ai_chat","generate_sweet_hindi_voice","detect_mood","detect_voice_command"])
_gemini_bridge=_si("jarvis_gemini_bridge",["gemini_chat","gemini_analyze_market","gemini_understand_intent","gemini_analyze_image","route_query","get_on_device_config"])
_smart_auth=_si("jarvis_smart_auth",["register_user","login_user","verify_session","is_owner","has_permission"])
_super_intel=_si("jarvis_super_intelligence",["super_intelligent_response","multi_ai_analyze","generate_proactive_insights","log_prediction","verify_prediction","get_accuracy_stats","learn_user_preference"])
_ota=_si("jarvis_ota_update",["create_ota_bundle","check_update","rollback_to_version"])

def _f(d,n):return d.get(n)
def _sani(s,mx=200):
    fn=_f(_sec,"sanitize_input")
    return fn(s,mx) if fn else str(s)[:mx]
def _is_admin(uid):
    fn=_f(_sec,"is_admin")
    return fn(uid) if fn else str(uid)==os.environ.get("OWNER_CHAT_ID","5647898018")

_ws_clients:List[WebSocket]=[]

@router.websocket("/ws/prices")
async def ws_prices(ws:WebSocket):
    await ws.accept();_ws_clients.append(ws)
    try:
        while True:
            try:
                d=await _get_ticker()
                if d:await ws.send_json({"type":"ticker","data":d,"ts":datetime.now(IST).isoformat()})
            except Exception:pass
            try:
                msg=await asyncio.wait_for(ws.receive_text(),timeout=20.0)
                cmd=json.loads(msg)
                if cmd.get("type")=="subscribe":
                    syms=cmd.get("symbols",[])
                    if syms:
                        td=await _get_token_prices(syms)
                        await ws.send_json({"type":"token_update","data":td,"ts":datetime.now(IST).isoformat()})
            except asyncio.TimeoutError:pass
            except WebSocketDisconnect:break
            except Exception:pass
    except Exception:pass
    finally:
        if ws in _ws_clients:_ws_clients.remove(ws)

def _parse_dex(p,sym):
    """Parse a DexScreener pair dict into a normalized ticker item."""
    if not p or not isinstance(p,dict):return None
    pu=float(p.get("price_usd",0)or p.get("priceUsd",0)or 0)
    ch=p.get("change_24h",0)or p.get("change_1h",0)or 0
    if isinstance(p.get("priceChange"),dict):ch=p["priceChange"].get("h24",ch)
    vol=p.get("volume_24h",0)or 0
    if isinstance(p.get("volume"),dict):vol=p["volume"].get("h24",vol)
    nm=p.get("name",sym)
    if isinstance(p.get("baseToken"),dict):nm=p["baseToken"].get("name",nm)
    return{"symbol":sym,"name":nm,"price_usd":pu,"price_inr":pu*90.5,"change_24h":float(ch or 0),"volume_24h":float(vol or 0),"market_cap":0}

async def _get_ticker()->List[Dict]:
    c=_cached("ws_ticker",60)
    if c:return c
    t=[]
    # Try CoinGecko first
    fn=_f(_dex,"cg_prices")
    if fn:
        try:
            prices=await fn("bitcoin,ethereum,solana,cardano,dogecoin,shiba-inu,pepe,bonk,ripple,toncoin","usd,inr")
            sm={"bitcoin":"BTC","ethereum":"ETH","solana":"SOL","cardano":"ADA","dogecoin":"DOGE","shiba-inu":"SHIB","pepe":"PEPE","bonk":"BONK","ripple":"XRP","toncoin":"TON"}
            for cid,d in(prices or{}).items():
                t.append({"symbol":sm.get(cid,cid.upper()[:5]),"name":cid.replace("-"," ").title(),"price_usd":d.get("usd",0),"price_inr":d.get("inr",0),"change_24h":d.get("usd_24h_change",0),"volume_24h":d.get("usd_24h_vol",0),"market_cap":d.get("usd_market_cap",0)})
        except Exception:pass
    # Fallback: DexScreener search — PARALLEL calls
    if not t:
        sfn=_f(_dex,"dex_search")
        if sfn:
            top=["BTC","ETH","SOL","XRP","DOGE","PEPE","BONK","TON"]
            async def _fetch_one(sym):
                try:
                    pairs=await sfn(sym,1)
                    if pairs and isinstance(pairs,list)and pairs[0]:return _parse_dex(pairs[0],sym)
                except Exception:pass
                return None
            results=await asyncio.gather(*[_fetch_one(s)for s in top],return_exceptions=True)
            t=[r for r in results if isinstance(r,dict)and r]
    t.sort(key=lambda x:x.get("market_cap",0)or x.get("volume_24h",0),reverse=True)
    if t:_set_cache("ws_ticker",t)
    return t

async def _get_token_prices(symbols):
    fn=_f(_dex,"dex_search")
    if not fn:return[]
    async def _one(s):
        try:
            pairs=await fn(s,1)
            if pairs and isinstance(pairs,list):return pairs[0]
        except Exception:pass
        return None
    results=await asyncio.gather(*[_one(s)for s in symbols[:10]],return_exceptions=True)
    return[r for r in results if isinstance(r,dict)]

@router.get("/health")
async def health():
    engines={}
    for n,d in[("dex",_dex),("brain",_brain),("sniper",_sniper),("crypto",_crypto),("india_stock",_india_stock),("nse",_nse),("options",_options),("phantom",_phantom),("trader",_trader),("buy_sell",_bse),("portfolio",_portfolio),("risk",_risk),("ml",_ml),("ai_signals",_ai_sig),("candle",_candle),("coindcx",_coindcx),("global",_global),("airdrops",_airdrop),("rug",_rug),("nifty_brain",_nifty),("oi_trap",_oi),("power",_power),("regime",_regime),("intel",_intel),("news",_news_brain)]:
        engines[n]="active" if any(v is not None for v in d.values()) else "off"
    active=sum(1 for v in engines.values() if v=="active")
    return{"status":"ok","version":"v6.0-mega","engines_loaded":active,"engines_total":len(engines),"engines":engines,"ws":len(_ws_clients),"ts":datetime.now(IST).isoformat()}

def _det_regime(fg,vx):
    fv=fg.get("value",50)if isinstance(fg,dict)else 50
    vv=vx.get("vix",15)if isinstance(vx,dict)else 15
    if fv>70 and vv<15:r,c="BULL RUN",85
    elif fv>55:r,c="BULLISH",70
    elif fv>40:r,c="NEUTRAL",60
    elif fv>25:r,c="BEARISH",65
    else:r,c="EXTREME FEAR",80
    return{"regime":r,"confidence":c,"fear_greed":fv,"vix":vv,"rec":"Buy dip"if fv<30 else"Hold"if fv<60 else"Take profits"}

@router.get("/dashboard")
async def dashboard(user_id:Optional[str]=None):
    c=_cached("dashboard",30)
    if c:return c
    tasks=[]
    fns=[("cg_market_data",10),("cg_fear_greed",None),("fetch_crypto_news",8),("get_nse_indices",None),("get_india_vix",None),("cmc_top_listings",50),("cmc_global_metrics",None),("dex_trending",None),("pumpfun_trending",None)]
    for fn_name,arg in fns:
        fn=_f(_dex,fn_name)
        if fn:tasks.append(fn(arg)if arg else fn())
        else:tasks.append(asyncio.sleep(0))
    results=await asyncio.gather(*tasks,return_exceptions=True)
    top_coins=results[0]if isinstance(results[0],list)else[]
    fear=results[1]if isinstance(results[1],dict)else{"value":50,"label":"Neutral"}
    news_list=results[2]if isinstance(results[2],list)else[]
    indices=results[3]if isinstance(results[3],list)else[]
    vix=results[4]if isinstance(results[4],dict)else{}
    cmc=results[5]if isinstance(results[5],list)else[]
    cmc_global=results[6]if isinstance(results[6],dict)else{}
    dex_trend=results[7]if isinstance(results[7],list)else[]
    pumpfun=results[8]if isinstance(results[8],list)else[]
    ticker=await _get_ticker()
    # Use CMC data as primary if CoinGecko rate limited
    if not top_coins and cmc:
        top_coins=cmc
    if not top_coins and ticker:
        top_coins=[{"symbol":t["symbol"],"name":t.get("name",""),"price_usd":t.get("price_usd",0),"current_price":t.get("price_usd",0),"change_24h":t.get("change_24h",0),"price_change_percentage_24h":t.get("change_24h",0),"market_cap":t.get("market_cap",0)}for t in ticker]
    gainers=sorted([c2 for c2 in top_coins if c2.get("change_24h",0)>0],key=lambda x:x.get("change_24h",0),reverse=True)[:8]
    losers=sorted([c2 for c2 in top_coins if c2.get("change_24h",0)<0],key=lambda x:x.get("change_24h",0))[:8]
    sigs=[]
    for c2 in top_coins[:20]:
        chg=c2.get("change_24h",0)
        if abs(chg)>2:
            st="STRONG BUY"if chg<-8 else"BUY"if chg<-3 else"SELL"if chg>8 else"HOLD"
            sigs.append({"symbol":c2.get("symbol",""),"signal":st,"confidence":min(95,int(abs(chg)*3+40)),"price":c2.get("price_usd",0),"change":chg})
    sigs.sort(key=lambda x:x.get("confidence",0),reverse=True)
    port={"balance_inr":0,"pnl_inr":0}
    if user_id:
        pfn=_f(_portfolio,"calculate_portfolio_pnl")
        if pfn:
            try:
                pnl=await _t(pfn,int(user_id))
                port={"balance_inr":pnl.get("total_current_inr",0),"pnl_inr":pnl.get("total_pnl_inr",0),"total_invested_inr":pnl.get("total_invested_inr",0)}
            except:pass
    result={"market_ticker":ticker,"fear_greed":fear,"sentiment":fear,"portfolio":port,"signals":sigs[:8],
            "top_movers":{"gainers":gainers,"losers":losers},"regime":_det_regime(fear,vix),
            "news":news_list,"indices":indices,"vix":vix,
            "cmc_global":cmc_global,"dex_trending":dex_trend[:10],"pumpfun":pumpfun[:10],
            "ts":datetime.now(IST).isoformat()}
    _set_cache("dashboard",result)
    return result

@router.get("/markets")
async def markets(category:Optional[str]=None):
    c=_cached("markets",10)
    if c:return c
    tasks=[]
    for fn_name,arg in[("cg_market_data",50),("dex_trending",None),("get_nse_indices",None),("pumpfun_trending",None),("cmc_top_listings",100),("cmc_global_metrics",None),("dex_boosted_tokens",None),("cg_trending",None)]:
        fn=_f(_dex,fn_name)
        if fn:tasks.append(fn(arg)if arg else fn())
        else:tasks.append(asyncio.sleep(0))
    results=await asyncio.gather(*tasks,return_exceptions=True)
    crypto=results[0]if isinstance(results[0],list)else[]
    trending=results[1]if isinstance(results[1],list)else[]
    indices=results[2]if isinstance(results[2],list)else[]
    pf=results[3]if isinstance(results[3],list)else[]
    cmc=results[4]if isinstance(results[4],list)else[]
    cmc_global=results[5]if isinstance(results[5],dict)else{}
    boosted=results[6]if isinstance(results[6],list)else[]
    cg_trend=results[7]if isinstance(results[7],list)else[]
    cdx=[]
    fn=_f(_coindcx,"get_web3_gainers_losers")
    if fn:
        try:cdx=await _t(fn)
        except:pass
    result={"crypto":crypto,"trending":trending[:20],"indices":indices,"pumpfun":pf[:15],
            "cmc":cmc,"cmc_global":cmc_global,"boosted":boosted[:15],"cg_trending":cg_trend[:15],
            "coindcx":cdx,"total":len(crypto)+len(cmc),"ts":datetime.now(IST).isoformat()}
    _set_cache("markets",result)
    return result

@router.get("/signals")
async def signals(market:str="all"):
    c=_cached(f"sig_{market}",15)
    if c:return c
    sigs=[]
    if market in("all","crypto"):
        fn=_f(_dex,"cg_market_data")
        if fn:
            try:
                coins=await fn(30)
                for item in(coins or[]):
                    chg=item.get("change_24h",0)or 0
                    if abs(chg)>2:
                        st="STRONG BUY"if chg<-10 else"BUY"if chg<-5 else"SELL"if chg>10 else"HOLD"
                        sigs.append({"symbol":item.get("symbol","?"),"signal":st,"confidence":min(95,int(abs(chg)*2.5+30)),"price":item.get("price_usd",0),"change_24h":chg,"source":"crypto","market":"crypto"})
            except:pass
    if market in("all","stock","india"):
        fn=_f(_bse,"scan_nifty_signals")
        if fn:
            try:
                ss=await _t(fn,15)
                for s in(ss or[]):
                    sigs.append({"symbol":getattr(s,"symbol",""),"signal":str(getattr(s,"signal_type","HOLD")),"confidence":getattr(s,"confidence",50),"price":getattr(s,"price",0),"change_24h":getattr(s,"price_change_pct",0),"source":"nifty","market":"india"})
            except:pass
    if market in("all","web3"):
        fn=_f(_coindcx,"scan_all_web3_signals")
        if fn:
            try:
                w3=await _t(fn,10)
                for s in(w3 or[]):sigs.append({"symbol":s.get("symbol",""),"signal":s.get("signal","HOLD"),"confidence":s.get("confidence",50),"price":s.get("price_inr",0),"change_24h":s.get("change_24h",0),"source":"coindcx","market":"web3"})
            except:pass
    sigs.sort(key=lambda x:x.get("confidence",0),reverse=True)
    result={"signals":sigs[:40],"count":len(sigs),"ts":datetime.now(IST).isoformat()}
    _set_cache(f"sig_{market}",result)
    return result

@router.get("/gems")
async def gems(source:str="all",min_score:int=40,filter:str="all"):
    ck=f"gems_{source}_{filter}"
    c=_cached(ck,30)
    if c:return c
    tasks=[]
    # Always fetch these for "all"
    if source in("all","dip")and _f(_dex,"find_dip_gems"):tasks.append(("dip",_f(_dex,"find_dip_gems")()))
    if source in("all","trending")and _f(_dex,"dex_trending"):tasks.append(("trending",_f(_dex,"dex_trending")()))
    if source in("all","pumpfun")and _f(_dex,"pumpfun_trending"):tasks.append(("pumpfun",_f(_dex,"pumpfun_trending")()))
    if source in("all","new")and _f(_dex,"dex_new_pairs"):tasks.append(("new",_f(_dex,"dex_new_pairs")("solana")))
    if source in("all","pumpfun_new")and _f(_dex,"pumpfun_new_coins"):tasks.append(("pumpfun_new",_f(_dex,"pumpfun_new_coins")()))
    if source in("all","cg")and _f(_dex,"cg_trending"):tasks.append(("cg_trending",_f(_dex,"cg_trending")()))
    g=await asyncio.gather(*[t[1] for t in tasks],return_exceptions=True)
    all_g,trending_g,new_g,dip_g=[],[],[],[]
    for i,d in enumerate(g):
        tag=tasks[i][0] if i<len(tasks) else "unknown"
        if isinstance(d,list):
            for item in d:
                item["_tag"]=tag
                if tag in("trending","pumpfun","cg_trending"):trending_g.append(item)
                elif tag in("new","pumpfun_new"):new_g.append(item)
                elif tag=="dip":dip_g.append(item)
                all_g.append(item)
    # Apply filter
    if filter=="trending":filtered=trending_g
    elif filter=="new":filtered=new_g
    elif filter=="dips":filtered=dip_g
    else:filtered=all_g
    filtered.sort(key=lambda x:x.get("gem_score",x.get("volume_24h",0) or 0),reverse=True)
    r={"gems":filtered[:50],"count":len(filtered),"source":source,"filter":filter,
       "stats":{"total":len(all_g),"trending":len(trending_g),"new":len(new_g),"dips":len(dip_g)},
       "ts":datetime.now(IST).isoformat()}
    _set_cache(ck,r)
    return r

@router.get("/search")
async def search_token(q:str=Query(...,min_length=1)):
    q=_sani(q,100)
    fn=_f(_dex,"dex_search")
    pairs=await fn(q,20)if fn else[]
    return{"results":pairs,"count":len(pairs),"query":q}

@router.get("/token/{address}")
async def token_detail(address:str):
    address=_sani(address,100)
    fn=_f(_dex,"dex_get_token")
    pairs=await fn(address)if fn else[]
    ai=None
    if pairs and _f(_intel,"analyze_token_full"):
        try:ai=await _t(_f(_intel,"analyze_token_full"),pairs[0])
        except:pass
    rug=None
    if pairs and _f(_rug,"analyze_rug_risk"):
        try:rug=await _t(_f(_rug,"analyze_rug_risk"),pairs[0])
        except:pass
    return{"pairs":pairs,"primary":pairs[0]if pairs else None,"ai":ai,"rug":rug}

@router.post("/chat")
async def chat(request:Request):
    body=await request.json()
    msg=_sani(body.get("message",""),4000)
    uid=str(body.get("user_id","0"))
    if not msg:return{"reply":"Please type a message."}
    # === CODE ENGINE INTEGRATION ===
    detect_fn=_f(_code_engine,"detect_code_request")
    if detect_fn:
        req_type=detect_fn(msg)
        if req_type=="github":
            url_fn=_f(_code_engine,"extract_github_url")
            gh_url=url_fn(msg) if url_fn else None
            if gh_url:
                run_fn=_f(_code_engine,"clone_and_run_github")
                fmt_fn=_f(_code_engine,"format_github_result")
                if run_fn:
                    result=await _t(run_fn,gh_url,int(uid))
                    reply=fmt_fn(result,gh_url) if fmt_fn else json.dumps(result,default=str)
                    return{"reply":reply,"provider":"jarvis-code-engine","type":"github","ts":datetime.now(IST).isoformat()}
        elif req_type=="generate":
            exec_fn=_f(_code_engine,"execute_code_autonomous")
            fmt_fn=_f(_code_engine,"format_execution_result")
            if exec_fn:
                result=await _t(exec_fn,msg,int(uid))
                reply=fmt_fn(result,msg) if fmt_fn else json.dumps(result,default=str)
                return{"reply":reply,"provider":"jarvis-code-engine","type":"code_gen","ts":datetime.now(IST).isoformat()}
        elif req_type=="raw_code":
            raw_fn=_f(_code_engine,"execute_raw_code")
            fmt_fn=_f(_code_engine,"format_execution_result")
            if raw_fn:
                result=await _t(raw_fn,msg)
                reply=fmt_fn(result,msg) if fmt_fn else json.dumps(result,default=str)
                return{"reply":reply,"provider":"jarvis-code-engine","type":"raw_code","ts":datetime.now(IST).isoformat()}
    # === NORMAL AI CHAT ===
    ctx=""
    try:
        t=await _get_ticker()
        if t:ctx="Live: "+" | ".join([f"{x['symbol']}: ${x['price_usd']:.2f} ({x['change_24h']:+.1f}%)"for x in t[:5]])
        nfn=_f(_dex,"get_nse_indices")
        if nfn:
            idx=await nfn()
            if idx:ctx+=" | India: "+" | ".join([f"{i.get('name','')}: {i.get('value',0)}"for i in idx[:3]])
    except:pass
    fn=_f(_brain,"jarvis_chat")
    reply=await fn(msg,uid,ctx)if fn else"AI loading..."
    return{"reply":reply,"provider":"jarvis-brain","ts":datetime.now(IST).isoformat()}

@router.post("/code/execute")
async def code_execute(request:Request):
    """Execute code autonomously — generate, install, run, return output."""
    body=await request.json()
    prompt=body.get("prompt","")
    uid=str(body.get("user_id","0"))
    if not prompt:return{"error":"Kya code banana hai batao / Tell me what to code"}
    exec_fn=_f(_code_engine,"execute_code_autonomous")
    fmt_fn=_f(_code_engine,"format_execution_result")
    if not exec_fn:return{"error":"Code engine not available"}
    result=await _t(exec_fn,prompt,int(uid))
    reply=fmt_fn(result,prompt) if fmt_fn else json.dumps(result,default=str)
    return{"result":result,"formatted":reply,"ts":datetime.now(IST).isoformat()}

@router.post("/code/github")
async def code_github(request:Request):
    """Clone a GitHub repo, install deps, run it, return output."""
    body=await request.json()
    url=body.get("url","")
    uid=str(body.get("user_id","0"))
    run_cmd=body.get("run_cmd","")
    if not url:return{"error":"GitHub URL do / Give a GitHub URL"}
    run_fn=_f(_code_engine,"clone_and_run_github")
    fmt_fn=_f(_code_engine,"format_github_result")
    if not run_fn:return{"error":"Code engine not available"}
    result=await _t(run_fn,url,int(uid),run_cmd)
    reply=fmt_fn(result,url) if fmt_fn else json.dumps(result,default=str)
    return{"result":result,"formatted":reply,"ts":datetime.now(IST).isoformat()}

@router.post("/code/run")
async def code_run(request:Request):
    """Run raw code directly."""
    body=await request.json()
    code=body.get("code","")
    language=body.get("language","python")
    if not code:return{"error":"Code paste karo / Paste the code"}
    raw_fn=_f(_code_engine,"execute_raw_code")
    if not raw_fn:return{"error":"Code engine not available"}
    result=await _t(raw_fn,code,language)
    return{"result":result,"ts":datetime.now(IST).isoformat()}

@router.post("/chat/clear")
async def chat_clear(request:Request):
    body=await request.json()
    fn=_f(_brain,"clear_memory")
    if fn:fn(str(body.get("user_id","0")))
    return{"success":True}

@router.get("/chat/history")
async def chat_history(user_id:str="0"):
    fn=_f(_brain,"get_conversation_history")
    h=fn(user_id)if fn else[]
    return{"messages":h,"count":len(h)}

@router.get("/chat/models")
async def chat_models():
    """Return available AI models for the model selector."""
    fn=_f(_brain,"get_available_models")
    return{"models":fn()if fn else[{"id":"jarvis-auto","name":"JARVIS Auto","desc":"Best available","available":True}]}

@router.get("/memory/stats")
async def memory_stats(user_id:str="0"):
    """Get user's memory stats — conversations, facts, positions, accuracy."""
    fn=_f(_brain,"get_memory_stats")
    return{"stats":fn(user_id) if fn else {}}

@router.get("/memory/facts")
async def memory_facts(user_id:str="0"):
    """Get stored facts about a user."""
    fn=_f(_brain,"get_user_facts")
    return{"facts":fn(user_id) if fn else {}}

@router.get("/memory/positions")
async def memory_positions(user_id:str="0"):
    """Get user's active tracked positions."""
    fn=_f(_brain,"get_active_positions")
    positions=fn(user_id) if fn else []
    return{"positions":positions,"count":len(positions)}

@router.get("/memory/accuracy")
async def memory_accuracy(user_id:str="0"):
    """Get prediction accuracy stats."""
    fn=_f(_brain,"get_prediction_accuracy")
    return{"accuracy":fn(user_id) if fn else {}}

@router.get("/memory/search")
async def memory_search(user_id:str="0",q:str=Query("",min_length=1)):
    """Search through user's conversation memory."""
    fn=_f(_brain,"search_memory")
    results=fn(user_id,q) if fn else []
    return{"results":results,"count":len(results),"query":q}

@router.post("/chat/stream")
async def chat_stream(request:Request):
    """SSE streaming chat — word-by-word like ChatGPT."""
    body=await request.json()
    msg=_sani(body.get("message",""),4000)
    uid=str(body.get("user_id","0"))
    model_id=body.get("model","jarvis-auto")
    if not msg:return JSONResponse({"error":"Empty message"},status_code=400)
    # Build market context
    ctx=""
    try:
        t=await _get_ticker()
        if t:ctx="Live: "+" | ".join([f"{x['symbol']}: ${x['price_usd']:.2f} ({x['change_24h']:+.1f}%)"for x in t[:5]])
        nfn=_f(_dex,"get_nse_indices")
        if nfn:
            idx=await nfn()
            if idx:ctx+=" | India: "+" | ".join([f"{i.get('name','')}: {i.get('value',0)}"for i in idx[:3]])
    except:pass
    fn=_f(_brain,"stream_chat")
    if not fn:return JSONResponse({"error":"Streaming not available"},status_code=503)
    async def sse_gen():
        try:
            async for chunk in fn(msg,uid,ctx,model_id):
                yield f"data: {json.dumps({'chunk':chunk})}\n\n"
            yield f"data: {json.dumps({'done':True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error':str(e)})}\n\n"
    return StreamingResponse(sse_gen(),media_type="text/event-stream",headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@router.get("/news")
async def news(category:str="all",limit:int=20):
    c=_cached(f"news_{category}",120)
    if c:return c
    tasks=[]
    if category in("all","crypto")and _f(_dex,"fetch_crypto_news"):tasks.append(_f(_dex,"fetch_crypto_news")(limit))
    if category in("all","india")and _f(_dex,"fetch_india_news"):tasks.append(_f(_dex,"fetch_india_news")(limit))
    g=await asyncio.gather(*tasks,return_exceptions=True)
    all_n=[]
    for d in g:
        if isinstance(d,list):all_n.extend(d)
    sent=None
    sfn=_f(_news_brain,"get_news_sentiment_score")
    if sfn:
        try:sent=await _t(sfn)
        except:pass
    all_n.sort(key=lambda x:x.get("published",""),reverse=True)
    r={"news":all_n[:limit],"count":len(all_n[:limit]),"category":category,"sentiment":sent}
    _set_cache(f"news_{category}",r)
    return r

@router.post("/wallet/connect-phantom")
async def connect_phantom(request:Request):
    body=await request.json()
    uid=str(body.get("user_id","0"))
    addr=_sani(body.get("wallet_address",""),100)
    if not addr or len(addr)<32:return{"error":"Invalid wallet address"}
    fn=_f(_phantom,"connect_wallet")
    if fn:
        try:return fn(int(uid),addr)
        except Exception as e:return{"success":False,"error":str(e)}
    try:
        os.makedirs("data",exist_ok=True)
        wf="data/phantom_wallets.json"
        w=json.loads(open(wf).read())if os.path.exists(wf)else{}
        w[uid]={"address":addr,"connected_at":datetime.now(IST).isoformat()}
        with open(wf,"w")as f:json.dump(w,f,indent=2)
        return{"success":True,"address":addr}
    except Exception as e:return{"error":str(e)}

@router.post("/wallet/disconnect-phantom")
async def disconnect_phantom(request:Request):
    body=await request.json()
    fn=_f(_phantom,"disconnect_wallet")
    if fn:
        try:return{"success":fn(int(body.get("user_id","0")))}
        except:pass
    return{"success":False}

@router.get("/wallet/phantom-balance")
async def phantom_balance(address:str=Query(...)):
    try:
        import httpx as hx
        async with hx.AsyncClient(timeout=10.0)as cl:
            r=await cl.post("https://api.mainnet-beta.solana.com",json={"jsonrpc":"2.0","id":1,"method":"getBalance","params":[address]})
            if r.status_code==200:
                lam=r.json().get("result",{}).get("value",0)
                sol=lam/1e9
                pfn=_f(_dex,"cg_prices")
                prices=await pfn("solana","usd,inr")if pfn else{}
                su=prices.get("solana",{}).get("usd",0)
                si=prices.get("solana",{}).get("inr",0)
                return{"address":address,"sol_balance":round(sol,6),"usd_value":round(sol*su,2),"inr_value":round(sol*si,2),"sol_price_usd":su,"sol_price_inr":si}
    except Exception as e:
        logger.warning(f"Balance: {e}")
    return{"address":address,"sol_balance":0,"error":"Could not fetch balance"}

@router.get("/wallet/tokens")
async def wallet_tokens(address:str=Query(...)):
    fn=_f(_phantom,"fetch_wallet_tokens")
    rfn=_f(_phantom,"resolve_token_prices")
    if fn:
        try:
            tokens=await _t(fn,address)
            if rfn:tokens=await _t(rfn,tokens)
            tv=sum(t.get("value_usd",0)for t in tokens)
            return{"address":address,"tokens":tokens,"count":len(tokens),"total_value_usd":round(tv,2)}
        except Exception as e:return{"address":address,"tokens":[],"error":str(e)}
    return{"address":address,"tokens":[],"error":"Wallet engine not loaded"}

@router.get("/wallet")
async def wallet(user_id:str="0"):
    uid=int(user_id)
    r={"balance_inr":0,"total_profit":0,"total_invested":0,"portfolio":{"positions":[],"total_positions":0},"transactions":[],"phantom":None,"ts":datetime.now(IST).isoformat()}
    pfn=_f(_portfolio,"calculate_portfolio_pnl")
    if pfn:
        try:
            pnl=await _t(pfn,uid)
            r["balance_inr"]=pnl.get("total_current_inr",0)
            r["total_profit"]=pnl.get("total_pnl_inr",0)
            r["total_invested"]=pnl.get("total_invested_inr",0)
        except:pass
    hfn=_f(_portfolio,"get_portfolio")
    if hfn:
        try:
            h=await _t(hfn,uid)
            r["portfolio"]["positions"]=h;r["portfolio"]["total_positions"]=len(h)
        except:pass
    tfn=_f(_portfolio,"get_trade_history")
    if tfn:
        try:r["transactions"]=await _t(tfn,uid,20)
        except:pass
    pw=_f(_phantom,"get_wallet")
    if pw:
        try:
            w=await _t(pw,uid)
            if w:r["phantom"]={"address":w.get("address",""),"connected":True}
        except:pass
    return r

@router.get("/auto-trader/strategies")
async def at_strategies():
    fn=_f(_sniper,"get_all_strategies")
    s1=fn()if fn else[]
    fn2=_f(_trader,"get_all_strategies")
    s2=fn2()if fn2 else{}
    return{"sniper_strategies":s1,"trader_strategies":s2}

@router.post("/auto-trader/start")
async def at_start(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0));amt=float(body.get("amount",0));strat=body.get("strategy","balanced")
    fn=_f(_sniper,"get_manager")
    if fn:
        try:return fn().start_sniper(uid,amt,strat)
        except Exception as e:return{"error":str(e)}
    fn2=_f(_trader,"start_auto_trader")
    if fn2:
        try:return fn2(uid,amt,strat)
        except Exception as e:return{"error":str(e)}
    return{"error":"No engine"}

@router.post("/auto-trader/stop")
async def at_stop(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    fn=_f(_sniper,"get_manager")
    if fn:
        try:return fn().stop_sniper(uid,body.get("sell_all",True))
        except:pass
    fn2=_f(_trader,"stop_auto_trader")
    if fn2:
        try:return fn2(uid)
        except:pass
    return{"error":"Not running"}

@router.get("/auto-trader/status")
async def at_status(user_id:str="0"):
    fn=_f(_sniper,"get_manager")
    if fn:
        try:return fn().get_sniper_status(int(user_id))
        except:pass
    fn2=_f(_trader,"get_trader_status")
    if fn2:
        try:return fn2(int(user_id))
        except:pass
    return{"active":False}

@router.get("/auto-trader/performance")
async def at_performance(user_id:str="0"):
    fn=_f(_sniper,"get_manager")
    if fn:
        try:return fn().get_performance(int(user_id))
        except:pass
    fn2=_f(_trader,"get_performance_report")
    if fn2:
        try:return fn2(int(user_id))
        except:pass
    return{}

@router.post("/auto-trader/compound")
async def at_compound(request:Request):
    body=await request.json()
    fn=_f(_sniper,"get_manager")
    if fn:
        try:return fn().compound_profits(int(body.get("user_id",0)))
        except:pass
    return{"error":"N/A"}

@router.get("/auto-trader/gems")
async def at_gems(strategy:str="balanced"):
    c=_cached(f"sg_{strategy}",30)
    if c:return c
    fn=_f(_sniper,"scan_for_gems")
    gl=await fn(strategy)if fn else[]
    r={"gems":gl[:20]if gl else[],"count":len(gl)if gl else 0,"strategy":strategy}
    _set_cache(f"sg_{strategy}",r)
    return r

@router.get("/india/dashboard")
async def india_dashboard():
    c=_cached("india_dash",120)
    if c:return c
    r={"nifty":{},"banknifty":{},"fii_dii":{},"vix":{},"pcr":{},"sectors":[],"pivots":{},"gift_nifty":{},"oi_buildup":{},"prediction":{},"regime":{},"indices":[],"ts":datetime.now(IST).isoformat()}
    async def _nc(k,fn_name):
        fn=_f(_nifty,fn_name)
        if fn:
            try:return k,await _t(fn)
            except:pass
        return k,None
    tasks=[_nc(k,n) for k,n in [("fii_dii","get_fii_dii_data"),("vix","get_india_vix"),("pcr","get_pcr_data"),("pivots","calculate_pivot_levels"),("gift_nifty","get_gift_nifty"),("sectors","get_sector_heatmap"),("oi_buildup","get_oi_buildup")]]
    async def _sp():
        sfn=_f(_nse,"get_live_spot")
        if sfn:
            try:return await _t(sfn,"NIFTY"),await _t(sfn,"BANKNIFTY")
            except:pass
        return None,None
    async def _pr():
        pfn=_f(_power,"power_predict")
        if pfn:
            try:return await _t(pfn,"NIFTY")
            except:pass
        return None
    async def _rg():
        rfn=_f(_regime,"get_regime_quick")
        if rfn:
            try:return await _t(rfn)
            except:pass
        return None
    async def _ix():
        ifn=_f(_dex,"get_nse_indices")
        if ifn:
            try:return await ifn()
            except:pass
        return []
    gr=await asyncio.gather(*tasks,_sp(),_pr(),_rg(),_ix(),return_exceptions=True)
    for x in gr[:7]:
        if isinstance(x,tuple) and len(x)==2 and x[1] is not None:r[x[0]]=x[1]
    if isinstance(gr[7],tuple):
        if gr[7][0]:r["nifty"]["spot"]=gr[7][0]
        if gr[7][1]:r["banknifty"]["spot"]=gr[7][1]
    if gr[8] and not isinstance(gr[8],Exception):r["prediction"]=gr[8]
    if gr[9] and not isinstance(gr[9],Exception):r["regime"]=gr[9]
    if isinstance(gr[10],list):r["indices"]=gr[10]
    _set_cache("india_dash",r)
    return r

@router.get("/india/indices")
async def india_indices():
    c=_cached("india_idx",120)
    if c:return c
    fn=_f(_dex,"get_nse_indices")
    d=await fn()if fn else[]
    _set_cache("india_idx",d)
    return{"indices":d,"count":len(d)}

@router.get("/india/vix")
async def india_vix():
    fn=_f(_dex,"get_india_vix")
    return await fn()if fn else{}

@router.get("/india/fii-dii")
async def india_fii_dii():
    c=_cached("india_fii",300)
    if c:return c
    fn=_f(_nifty,"get_fii_dii_data")
    r=(await _t(fn))if fn else{"error":"N/A"}
    if "error" not in r:_set_cache("india_fii",r)
    return r

@router.get("/india/pcr")
async def india_pcr(symbol:str="NIFTY"):
    fn=_f(_nifty,"get_pcr_data")
    return(await _t(fn,symbol))if fn else{"error":"N/A"}

@router.get("/india/sectors")
async def india_sectors():
    c=_cached("india_sec",120)
    if c:return c
    fn=_f(_nifty,"get_sector_heatmap")
    r={"sectors":(await _t(fn))if fn else[]}
    if r["sectors"]:_set_cache("india_sec",r)
    return r

@router.get("/india/gift-nifty")
async def india_gift():
    fn=_f(_nifty,"get_gift_nifty")
    return(await _t(fn))if fn else{}

@router.get("/india/super-analysis")
async def india_super(query:str="",budget:float=2000):
    fn=_f(_india_stock,"indian_stock_super_analysis")
    if fn:
        try:return await _t(fn,query,budget)
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/india/prediction")
async def india_prediction(index:str="NIFTY"):
    c=_cached(f"ipred_{index}",60)
    if c:return c
    fn=_f(_power,"power_predict")
    if fn:
        try:
            r=await _t(fn,index)
            _set_cache(f"ipred_{index}",r)
            return r
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/india/ml-prediction")
async def india_ml(index:str="NIFTY"):
    c=_cached(f"mlp_{index}",120)
    if c:return c
    fn=_f(_ml,"predict_with_regime")
    if fn:
        try:
            sm={"NIFTY":"^NSEI","BANKNIFTY":"^NSEBANK","SENSEX":"^BSESN"}
            r=await _t(fn,sm.get(index,"^NSEI"),index)
            _set_cache(f"mlp_{index}",r)
            return r
        except Exception as e:return{"error":str(e)}
    return{"error":"ML not loaded"}

@router.get("/options/chain")
async def options_chain(symbol:str="NIFTY"):
    c=_cached(f"oc_{symbol}",30)
    if c:return c
    fn=_f(_nse,"fetch_live_option_chain")
    if fn:
        try:
            ch=await _t(fn,symbol)
            if ch:
                r={"symbol":symbol,"spot":ch.spot,"expiry":ch.expiry_dates,"max_pain":ch.max_pain,"pcr":ch.pcr_oi,
                   "total_ce_oi":ch.total_ce_oi,"total_pe_oi":ch.total_pe_oi,
                   "strikes":[{"strike":s.strike,"ce_ltp":s.ce_ltp,"pe_ltp":s.pe_ltp,"ce_oi":s.ce_oi,"pe_oi":s.pe_oi,"ce_iv":s.ce_iv,"pe_iv":s.pe_iv}for s in ch.strikes[:30]]}
                _set_cache(f"oc_{symbol}",r)
                return r
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/options/analysis")
async def options_analysis(symbol:str="NIFTY",budget:float=2000):
    fn=_f(_nse,"get_atm_otm_analysis")
    if fn:
        try:return await _t(fn,symbol,budget)
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/options/signal")
async def options_signal(symbol:str="NIFTY"):
    c=_cached(f"os_{symbol}",30)
    if c:return c
    fn=_f(_oi,"get_options_super_signal")
    if fn:
        try:
            r=await _t(fn,symbol)
            _set_cache(f"os_{symbol}",r)
            return r
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/options/traps")
async def options_traps(symbol:str="NIFTY"):
    fc=_f(_oi,"fetch_option_chain");ft=_f(_oi,"detect_traps")
    if fc and ft:
        try:
            ch=await _t(fc,symbol)
            if ch:return await _t(ft,ch)
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/options/budget-plays")
async def options_budget(symbol:str="NIFTY",min_price:float=2,max_price:float=30):
    fc=_f(_oi,"fetch_option_chain");fb=_f(_oi,"find_budget_plays")
    if fc and fb:
        try:
            ch=await _t(fc,symbol)
            if ch:return{"plays":await _t(fb,ch,min_price,max_price)}
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/options/strategy")
async def options_strategy(symbol:str="NIFTY"):
    fn=_f(_options,"recommend_strategy")
    if fn:
        try:return await _t(fn,symbol)
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/analysis/technical")
async def technical_analysis(symbol:str=Query(...)):
    c=_cached(f"ta_{symbol}",60)
    if c:return c
    r={"symbol":symbol}
    fn=_f(_ai_sig,"full_technical_analysis")
    if fn:
        try:
            sfn=_f(_dex,"dex_search")
            pairs=await sfn(symbol,1)if sfn else[]
            if pairs:r["technical"]=await _t(fn,pairs[0])
        except:pass
    bfn=_f(_bse,"get_crypto_signal")or _f(_bse,"get_stock_signal")
    if bfn:
        try:
            sig=await _t(bfn,symbol)
            if sig:r["signal"]={"symbol":getattr(sig,"symbol",""),"signal":str(getattr(sig,"signal_type","")),"confidence":getattr(sig,"confidence",0)}
        except:pass
    _set_cache(f"ta_{symbol}",r)
    return r

@router.get("/analysis/candles")
async def candle_analysis(symbol:str="NIFTY"):
    c=_cached(f"ca_{symbol}",60)
    if c:return c
    fn=_f(_candle,"analyze_index")
    if fn:
        try:
            r=await _t(fn,symbol,symbol)
            _set_cache(f"ca_{symbol}",r)
            return r
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/rug-check")
async def rug_check(symbol:str=Query(...)):
    symbol=_sani(symbol,100)
    gfn=_f(_rug,"check_goplus_security")
    if gfn:
        try:
            gp=await _t(gfn,symbol)
            if gp and not gp.get("error"):return gp
        except:pass
    fn=_f(_dex,"dex_search")
    pairs=await fn(symbol,5)if fn else[]
    if not pairs:return{"error":"Not found","risk_score":100}
    rfn=_f(_rug,"analyze_rug_risk")
    if rfn:
        try:return await _t(rfn,pairs[0])
        except:pass
    tk=pairs[0];liq=tk.get("liquidity_usd",0);vol=tk.get("volume_24h",0)
    risk=50;warns=[]
    if liq<1000:risk+=30;warns.append("Very low liquidity")
    if vol<500:risk+=20;warns.append("Low volume")
    return{"symbol":tk.get("symbol",symbol),"risk_score":min(100,risk),"verdict":"HIGH RISK"if risk>70 else"MODERATE"if risk>40 else"SAFE","warnings":warns,"liquidity":liq}

@router.get("/airdrops")
async def airdrops(wallet:Optional[str]=None):
    c=_cached("airdrops",120)
    if c:return c
    fn=_f(_airdrop,"scan_all_airdrops")
    dr=(await _t(fn,wallet))if fn else[]
    r={"airdrops":dr[:30]if dr else[],"count":len(dr)if dr else 0}
    _set_cache("airdrops",r)
    return r

@router.get("/airdrops/new")
async def new_airdrops(wallet:Optional[str]=None):
    fn=_f(_airdrop,"get_new_airdrop_alerts")
    return{"alerts":(await _t(fn,wallet))if fn else[]}

@router.get("/global/markets")
async def global_mkts():
    c=_cached("glob",120)
    if c:return c
    fn=_f(_global,"analyze_all_global_markets")
    if fn:
        try:
            a=await _t(fn)
            r={"us":[],"europe":[],"asia":[],"commodities":[],"overall":""}
            if a:
                for attr,key in[("us_signals","us"),("european_signals","europe"),("asian_signals","asia"),("commodity_signals","commodities")]:
                    if hasattr(a,attr):
                        r[key]=[{"symbol":s.symbol,"name":s.name,"signal":s.signal,"confidence":s.confidence,"price":s.price,"change":s.change_pct}for s in getattr(a,attr)]
                if hasattr(a,"overall_sentiment"):r["overall"]=a.overall_sentiment
            _set_cache("glob",r)
            return r
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/risk/position-size")
async def risk_pos(capital:float=10000,risk_pct:float=2,stop_loss_pct:float=5):
    fn=_f(_risk,"calculate_position_size")
    if fn:
        try:return await _t(fn,capital,risk_pct,stop_loss_pct)
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/risk/plan")
async def risk_plan(capital:float=10000,risk_level:str="moderate"):
    fn=_f(_risk,"calculate_investment_plan")
    if fn:
        try:return await _t(fn,capital,risk_level)
        except:pass
    return{"error":"N/A"}

@router.get("/intelligence")
async def intelligence():
    c=_cached("intl",300)
    if c:return c
    fn=_f(_dex,"get_full_market_snapshot")
    snap=await fn()if fn else{}
    bfn=_f(_brain,"generate_briefing")
    b=await bfn(snap)if bfn else"Loading..."
    r={"briefing":b,"regime":_det_regime(snap.get("fear_greed",{}),snap.get("india_vix",{})),"fear_greed":snap.get("fear_greed",{}),"vix":snap.get("india_vix",{}),"ts":datetime.now(IST).isoformat()}
    _set_cache("intl",r)
    return r

@router.get("/intelligence/top-picks")
async def top_picks(budget:float=2000):
    fn=_f(_intel,"get_top_crypto_picks")
    if fn:
        try:return{"picks":await _t(fn,5,budget)}
        except:pass
    return{"picks":[]}

@router.get("/intelligence/watchlist")
async def watchlist(user_id:str="0"):
    fn=_f(_intel,"get_user_watchlist")
    return{"watchlist":fn(user_id)if fn else[]}

@router.get("/regime")
async def regime_ep(symbol:str="^NSEI"):
    c=_cached(f"reg_{symbol}",120)
    if c:return c
    fn=_f(_regime,"get_regime_quick")
    if fn:
        try:
            r=await _t(fn,symbol)
            _set_cache(f"reg_{symbol}",r)
            return r
        except:pass
    return _det_regime({"value":50},{})

@router.get("/correlation")
async def correlation():
    fn=_f(_cross,"scan_all_correlations")
    if fn:
        try:return await _t(fn)
        except:pass
    return{"error":"N/A"}

@router.get("/predictions")
async def predictions():
    fn=_f(_pred,"get_accuracy_report")
    if fn:
        try:return await _t(fn)
        except:pass
    return{"total":0,"accuracy":0}

@router.get("/dex/trending")
async def dex_trending_ep():
    c=_cached("dxt",30)
    if c:return c
    fn=_f(_dex,"dex_trending")
    d=await fn()if fn else[]
    _set_cache("dxt",d)
    return{"trending":d,"count":len(d)}

@router.get("/dex/new-pairs")
async def dex_new_ep(chain:str="solana"):
    fn=_f(_dex,"dex_new_pairs")
    return{"pairs":await fn(chain)if fn else[],"chain":chain}

@router.get("/pumpfun/trending")
async def pumpfun_trending_ep():
    c=_cached("pft",30)
    if c:return c
    fn=_f(_dex,"pumpfun_trending")
    d=await fn()if fn else[]
    _set_cache("pft",d)
    return{"tokens":d,"count":len(d)}

@router.get("/pumpfun/new")
async def pumpfun_new_ep():
    fn=_f(_dex,"pumpfun_new_coins")
    return{"tokens":await fn()if fn else[]}

@router.get("/india/news")
async def india_news_ep(limit:int=15):
    fn=_f(_dex,"fetch_india_news")
    return{"news":await fn(limit)if fn else[]}

@router.get("/analyze")
async def analyze(symbol:str=Query(...)):
    symbol=_sani(symbol,100)
    fn=_f(_dex,"dex_search")
    pairs=await fn(symbol,5)if fn else[]
    td=pairs[0]if pairs else{}
    afn=_f(_brain,"analyze_token")
    ai=await afn(symbol,td)if afn else"Loading..."
    return{"symbol":symbol,"market_data":td,"ai_analysis":ai,"ts":datetime.now(IST).isoformat()}

@router.get("/sentiment")
async def sentiment():
    c=_cached("sent",120)
    if c:return c
    fn=_f(_dex,"cg_fear_greed")
    fg=await fn()if fn else{"value":50,"label":"Neutral"}
    _set_cache("sent",fg)
    return fg

@router.get("/futures")
async def futures_ep():
    c=_cached("fut",60)
    if c:return c
    tasks=[]
    if _f(_dex,"get_india_vix"):tasks.append(_f(_dex,"get_india_vix")())
    if _f(_dex,"get_nse_indices"):tasks.append(_f(_dex,"get_nse_indices")())
    results=await asyncio.gather(*tasks,return_exceptions=True)
    r={"vix":results[0]if len(results)>0 and isinstance(results[0],dict)else{},"indices":results[1]if len(results)>1 and isinstance(results[1],list)else[]}
    _set_cache("fut",r)
    return r

@router.get("/admin/stats")
async def admin_stats(user_id:str="0"):
    if not _is_admin(user_id):return{"error":"Unauthorized"}
    fn=_f(_sniper,"get_manager")
    mgr=fn()if fn else None
    return{"total_users":len(mgr._snipers)if mgr else 0,"ws":len(_ws_clients),"cache":len(_cache),"ts":datetime.now(IST).isoformat()}

@router.get("/admin/users")
async def admin_users(user_id:str="0"):
    if not _is_admin(user_id):return{"error":"Unauthorized"}
    fn=_f(_sniper,"get_manager")
    if fn:
        mgr=fn()
        return{"users":[{"user_id":uid,"strategy":s.get("strategy",""),"active":s.get("active",False)}for uid,s in mgr._snipers.items()],"total":len(mgr._snipers)}
    return{"users":[],"total":0}

logger.info("✅ Mini App API v6.0 MEGA loaded — ALL engines connected")

# ═══════════════════════════════════════════════════════════
#  💳 PAYMENT & WALLET (Deposit / Withdraw / Balance)
# ═══════════════════════════════════════════════════════════
@router.get("/wallet/balance")
async def wallet_balance(user_id:str="0"):
    fn=_f(_payment,"get_user_wallet")
    if fn:
        try:return{"status":"ok","data":await _t(fn,user_id)}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"ok","data":{"balance_inr":0,"balance_usd":0}}

@router.post("/deposit")
async def deposit(request:Request):
    body=await request.json()
    uid=str(body.get("user_id","0"))
    amount=float(body.get("amount",0))
    method=body.get("method","upi")
    fn=_f(_payment,"create_deposit_request")
    if fn:
        try:
            r=await _t(fn,uid,amount,method)
            return{"status":"ok","data":r}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"ok","data":{"tx_id":"demo","qr_url":"","upi_id":"jarvis@upi","amount":amount,"status":"pending"}}

@router.post("/deposit/verify")
async def deposit_verify(request:Request):
    body=await request.json()
    utr=body.get("utr","")
    amount=float(body.get("amount",0))
    fn=_f(_payment,"confirm_deposit")
    if fn and utr:
        try:return{"status":"ok","data":await _t(fn,utr)}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"ok","message":"Deposit verification submitted"}

@router.post("/withdraw")
async def withdraw(request:Request):
    body=await request.json()
    uid=str(body.get("user_id","0"))
    amount=float(body.get("amount",0))
    method="phantom"  # Only Phantom wallet withdrawals allowed
    fn=_f(_payment,"create_withdrawal_request")
    if fn:
        try:
            r=await _t(fn,uid,amount,method)
            return{"status":"ok","data":r}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"ok","data":{"status":"pending","message":"Withdrawal to Phantom wallet submitted"}}

@router.get("/transactions")
async def transactions(user_id:str="0",limit:int=50):
    fn=_f(_payment,"get_transaction_history")
    if fn:
        try:return{"status":"ok","data":await _t(fn,user_id,limit)}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"ok","data":[]}

# ═══════════════════════════════════════════════════════════════
# 🔥 PHASE 9: ALL MISSING ENGINES — FULL INTEGRATION
# ═══════════════════════════════════════════════════════════════

# ── WHALE ALERTS ──
@router.get("/whale/scan")
async def whale_scan():
    fn=_f(_whale,"scan_whale_activity_trending")
    if fn:
        try:return{"whales":await _t(fn,10),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"whales":[],"ts":datetime.now(IST).isoformat()}

@router.get("/whale/token")
async def whale_token(address:str=Query(...)):
    fn=_f(_whale,"detect_whale_activity_from_dex")
    if fn:
        try:return{"data":await _t(fn,address),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"data":{},"error":"N/A"}

@router.get("/whale/onchain")
async def whale_onchain(mint:str=Query(...)):
    fn=_f(_whale,"check_helius_transactions")
    if fn:
        try:return{"txns":await _t(fn,mint,20),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"txns":[]}

# ── WEB3 ROCKET SCANNER ──
@router.get("/web3/rockets")
async def web3_rockets():
    c=_cached("w3rockets",30)
    if c:return c
    fn=_f(_web3,"scan_top_rockets")
    fn2=_f(_web3,"fetch_dex_trending_pairs")
    data=[]
    if fn:
        try:data=await _t(fn)
        except:pass
    elif fn2:
        try:data=await _t(fn2)
        except:pass
    r={"rockets":data[:30]if data else[],"count":len(data)if data else 0,"ts":datetime.now(IST).isoformat()}
    _set_cache("w3rockets",r)
    return r

@router.get("/web3/new-launches")
async def web3_launches():
    fn=_f(_web3,"scan_new_launches")
    fn2=_f(_web3,"fetch_dex_new_pairs")
    data=[]
    if fn:
        try:data=await _t(fn)
        except:pass
    elif fn2:
        try:data=await _t(fn2)
        except:pass
    return{"launches":data[:20]if data else[],"count":len(data)if data else 0}

# ── SOLANA ENGINE ──
@router.get("/solana/balance")
async def sol_balance(wallet:str=""):
    fn=_f(_solana,"get_sol_balance")
    if fn:
        try:return{"balance":await _t(fn,wallet)if wallet else await _t(fn)}
        except:pass
    return{"balance":0}

@router.get("/solana/tokens")
async def sol_tokens(wallet:str=""):
    fn=_f(_solana,"get_all_token_balances")
    if fn:
        try:
            tokens=await _t(fn,wallet)if wallet else await _t(fn)
            rfn=_f(_solana,"resolve_token_metadata")
            if rfn and tokens:tokens=await _t(rfn,tokens)
            return{"tokens":tokens,"count":len(tokens)}
        except:pass
    return{"tokens":[],"count":0}

@router.get("/solana/transactions")
async def sol_txns(wallet:str="",limit:int=10):
    fn=_f(_solana,"get_recent_transactions")
    if fn:
        try:return{"txns":await _t(fn,wallet,limit)if wallet else await _t(fn)}
        except:pass
    return{"txns":[]}

# ── SUNCRYPTO / INR PRICES ──
@router.get("/inr/prices")
async def inr_prices():
    c=_cached("inr_prices",30)
    if c:return c
    fn=_f(_suncrypto,"get_all_inr_prices")
    if fn:
        try:
            d=await fn()
            r={"prices":d[:50]if d else[],"count":len(d)if d else 0,"ts":datetime.now(IST).isoformat()}
            _set_cache("inr_prices",r)
            return r
        except:pass
    return{"prices":[],"count":0}

@router.get("/inr/gainers")
async def inr_gainers():
    fn=_f(_suncrypto,"get_top_inr_gainers")
    if fn:
        try:return{"gainers":await fn(15),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"gainers":[]}

@router.get("/inr/losers")
async def inr_losers():
    fn=_f(_suncrypto,"get_top_inr_losers")
    if fn:
        try:return{"losers":await fn(15),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"losers":[]}

# ── SENTIMENT ENGINE ──
@router.get("/sentiment/analysis")
async def sentiment_analysis():
    c=_cached("sentiment",60)
    if c:return c
    fn=_f(_sentiment,"analyze_news_sentiment")
    if fn:
        try:
            r=await _t(fn)
            _set_cache("sentiment",r)
            return r
        except:pass
    return{"overall":"neutral","score":0}

# ── TRADE TRACKER / PNL ──
@router.get("/pnl/daily")
async def pnl_daily(user_id:str="0"):
    fn=_f(_pnl,"get_daily_pnl")
    if fn:
        try:return await _t(fn,int(user_id))
        except:pass
    return{"trades":[],"total_pnl":0}

@router.get("/pnl/weekly")
async def pnl_weekly(user_id:str="0"):
    fn=_f(_pnl,"get_weekly_pnl")
    if fn:
        try:return await _t(fn,int(user_id))
        except:pass
    return{"trades":[],"total_pnl":0}

@router.get("/pnl/monthly")
async def pnl_monthly(user_id:str="0"):
    fn=_f(_pnl,"get_monthly_pnl")
    if fn:
        try:return await _t(fn,int(user_id))
        except:pass
    return{"trades":[],"total_pnl":0}

@router.post("/pnl/log")
async def pnl_log(request:Request):
    body=await request.json()
    fn=_f(_pnl,"log_trade")
    if fn:
        try:return{"status":"ok","data":await _t(fn,**body)}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"error","error":"N/A"}

@router.post("/pnl/close")
async def pnl_close(request:Request):
    body=await request.json()
    fn=_f(_pnl,"close_trade")
    if fn:
        try:return{"status":"ok","data":await _t(fn,int(body.get("user_id",0)),int(body.get("trade_id",0)),float(body.get("exit_price",0)))}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"error","error":"N/A"}

# ── SCREENER PRO ──
@router.get("/screener/full")
async def screener_full():
    c=_cached("screener_full",60)
    if c:return c
    fn=_f(_screener,"run_full_screener")
    if fn:
        try:
            r=await _t(fn)
            _set_cache("screener_full",r)
            return r
        except:pass
    return{"results":[]}

@router.get("/screener/filter")
async def screener_filter(type:str="oversold"):
    fn_map={"oversold":"screen_rsi_oversold","overbought":"screen_rsi_overbought","volume":"screen_volume_breakout","gap_up":"screen_gap_up","52w_high":"screen_52w_high","bullish":"screen_bullish_crossover","momentum":"screen_momentum"}
    fn=_f(_screener,fn_map.get(type,"screen_rsi_oversold"))
    if fn:
        try:return{"results":await _t(fn),"filter":type}
        except:pass
    return{"results":[],"filter":type}

# ── INTRADAY SCANNER ──
@router.get("/intraday/scan")
async def intraday_scan():
    c=_cached("intra_scan",30)
    if c:return c
    fn=_f(_intraday,"run_intraday_scan")
    if fn:
        try:
            r=await _t(fn)
            result={"scan":r,"ts":datetime.now(IST).isoformat()}
            _set_cache("intra_scan",result)
            return result
        except:pass
    return{"scan":"No data","ts":datetime.now(IST).isoformat()}

@router.get("/intraday/breakouts")
async def intraday_breakouts():
    fn=_f(_intraday,"scan_breakouts")
    if fn:
        try:return{"data":await _t(fn),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"data":"No data"}

@router.get("/intraday/volume")
async def intraday_volume():
    fn=_f(_intraday,"scan_volume_spikes")
    if fn:
        try:return{"data":await _t(fn),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"data":"No data"}

@router.get("/intraday/momentum")
async def intraday_momentum():
    fn=_f(_intraday,"scan_momentum")
    if fn:
        try:return{"data":await _t(fn),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"data":"No data"}

# ── CHARTS ──
@router.get("/chart")
async def chart(symbol:str=Query(...),timeframe:str="1d"):
    fn=_f(_chart,"generate_chart")
    fn2=_f(_chart,"generate_multi_indicator_chart")
    target=fn2 or fn
    if target:
        try:return{"chart":await _t(target,symbol,timeframe)}
        except:pass
    return{"error":"Charts N/A"}

# ── FUTURES BRAIN ──
@router.get("/futures/dashboard")
async def futures_dash():
    c=_cached("futures_dash",30)
    if c:return c
    r={}
    tasks=[]
    fn_map={"pcr":"get_pcr","max_pain":"get_max_pain","basis":"get_futures_basis","vix":"get_india_vix","straddle":"get_straddle_premium","oi_dist":"get_oi_distribution"}
    for k,n in fn_map.items():
        fn=_f(_futures,n)
        if fn:tasks.append((k,fn))
    results=await asyncio.gather(*[_t(f) for _,f in tasks],return_exceptions=True)
    for i,(k,_) in enumerate(tasks):
        if not isinstance(results[i],Exception):r[k]=results[i]
    _set_cache("futures_dash",r)
    return r

# ── OPTIONS PRO ──
@router.get("/options/strike")
async def options_strike(symbol:str="NIFTY",strike:int=0,type:str="CE"):
    fn=_f(_opts_pro,"get_strike_price")
    if fn:
        try:return await _t(fn,symbol,strike,type)
        except:pass
    return{"error":"N/A"}

@router.get("/options/nearby")
async def options_nearby(symbol:str="NIFTY"):
    fn=_f(_opts_pro,"get_nearby_options")
    if fn:
        try:return await _t(fn,symbol)
        except:pass
    return{"error":"N/A"}

@router.get("/options/chain-summary")
async def options_chain_summary(symbol:str="NIFTY"):
    fn=_f(_opts_pro,"get_full_chain_summary")
    if fn:
        try:return await _t(fn,symbol)
        except:pass
    return{"error":"N/A"}

# ── ULTRA AI ANALYSIS ──
@router.get("/ultra/predict")
async def ultra_predict(symbol:str=Query(...)):
    fn=_f(_ultra,"ultra_predict")
    if fn:
        try:
            # Get token data first
            sfn=_f(_dex,"dex_search")
            pairs=await sfn(symbol,3)if sfn else[]
            token=pairs[0]if pairs else{"symbol":symbol}
            return{"prediction":await _t(fn,token),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"prediction":{},"error":"N/A"}

@router.get("/ultra/health")
async def ultra_health(symbol:str=Query(...)):
    fn=_f(_ultra,"token_health_score")
    if fn:
        try:
            sfn=_f(_dex,"dex_search")
            pairs=await sfn(symbol,3)if sfn else[]
            token=pairs[0]if pairs else{"symbol":symbol}
            return{"health":await _t(fn,token),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"health":{},"error":"N/A"}

# ── MARKET BRAIN ──
@router.get("/market-brain/analyze")
async def mkt_brain_analyze(query:str=Query(...)):
    fn=_f(_mkt_brain,"analyze_indian_stock_deep")
    fn2=_f(_mkt_brain,"analyze_crypto_token_deep")
    mtype=_f(_mkt_brain,"detect_market_type")
    if mtype:
        try:
            t=await _t(mtype,query)
            if t=="indian"and fn:return{"data":await _t(fn,query),"type":"indian"}
            elif fn2:return{"data":await _t(fn2,query),"type":"crypto"}
        except:pass
    return{"data":{},"error":"N/A"}

# ── SUPER BRAIN NEWS ──
@router.get("/briefing")
async def briefing():
    c=_cached("briefing",120)
    if c:return c
    fn=_f(_super_brain,"format_jarvis_briefing")
    if fn:
        try:
            r={"briefing":await _t(fn),"ts":datetime.now(IST).isoformat()}
            _set_cache("briefing",r)
            return r
        except:pass
    return{"briefing":"No briefing available"}

@router.get("/market-intel")
async def market_intel():
    c=_cached("mkt_intel",60)
    if c:return c
    fn=_f(_super_brain,"get_market_intelligence")
    if fn:
        try:
            r=await _t(fn)
            _set_cache("mkt_intel",r)
            return r
        except:pass
    return{"error":"N/A"}

# ── ATM/OTM ENGINE ──
@router.get("/options/atm-otm")
async def atm_otm(symbol:str="NIFTY"):
    fn=_f(_otm_atm,"get_full_atm_otm_analysis")
    if fn:
        try:return await _t(fn,symbol)
        except:pass
    return{"error":"N/A"}

@router.get("/options/greeks")
async def options_greeks(symbol:str="NIFTY",strike:int=0,type:str="CE"):
    fn=_f(_otm_atm,"calculate_greeks")
    if fn:
        try:return await _t(fn,symbol,strike,type)
        except:pass
    return{"error":"N/A"}

# ── LIVE INDEX ENGINE ──
@router.get("/live/price")
async def live_price(symbol:str="NIFTY"):
    fn=_f(_live_idx,"get_live_price")
    if fn:
        try:return await _t(fn,symbol)
        except:pass
    return{"error":"N/A"}

@router.get("/live/2min-signal")
async def live_2min(symbol:str="NIFTY"):
    fn=_f(_live_idx,"analyze_2min_candle")
    if fn:
        try:return await _t(fn,symbol,symbol)
        except:pass
    return{"error":"N/A"}

@router.get("/live/investment")
async def live_invest(symbol:str="NIFTY",amount:float=2000):
    fn_chain=_f(_live_idx,"generate_index_option_chain")
    fn_invest=_f(_live_idx,"calculate_investment_options")
    if fn_chain and fn_invest:
        try:
            chain=await _t(fn_chain,symbol+"50"if"NIFTY"in symbol else symbol,symbol)
            return await _t(fn_invest,chain,amount)
        except:pass
    return{"error":"N/A"}

# ── COINDCX MEGA SCANNER ──
@router.get("/coindcx/scan")
async def cdcx_scan():
    c=_cached("cdcx_scan",60)
    if c:return c
    fn=_f(_cdcx_mega,"mega_scan_all")
    if fn:
        try:
            r=await _t(fn)
            _set_cache("cdcx_scan",r)
            return r
        except:pass
    return{"results":[]}

# ── DEXTOOLS ──
@router.get("/dextools/hot")
async def dextools_hot():
    fn=_f(_dextools,"get_hot_pairs")
    if fn:
        try:return{"pairs":await _t(fn),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"pairs":[]}

@router.get("/dextools/search")
async def dextools_search(q:str=Query(...)):
    fn=_f(_dextools,"search_pairs")
    if fn:
        try:return{"results":await _t(fn,q),"query":q}
        except:pass
    return{"results":[],"query":q}

# ── GLOBAL MARKET ANALYZER ──
@router.get("/global/analysis")
async def global_analysis():
    c=_cached("global_analysis",120)
    if c:return c
    fn=_f(_global_mkt,"analyze_global_markets")
    fn2=_f(_global_mkt,"get_global_summary")
    if fn:
        try:
            r=await _t(fn)
            _set_cache("global_analysis",r)
            return r
        except:pass
    if fn2:
        try:
            r=await _t(fn2)
            _set_cache("global_analysis",r)
            return r
        except:pass
    return{"error":"N/A"}

@router.get("/global/india-impact")
async def global_india():
    fn=_f(_global_mkt,"predict_india_from_global")
    if fn:
        try:return await _t(fn)
        except:pass
    return{"error":"N/A"}

# ── MEMORY PRO ──
@router.post("/memory/remember")
async def memory_remember(request:Request):
    body=await request.json()
    fn=_f(_mem_pro,"remember")
    if fn:
        try:return await _t(fn,int(body.get("user_id",0)),body.get("key",""),body.get("value",""))
        except:pass
    return{"status":"ok"}

@router.get("/memory/recall")
async def memory_recall(user_id:str="0",key:str=""):
    fn=_f(_mem_pro,"recall")
    if fn:
        try:return{"data":await _t(fn,int(user_id),key)}
        except:pass
    return{"data":None}

# ── ML PIPELINE ──
@router.get("/ml/predict")
async def ml_predict_ep(symbol:str="NIFTY"):
    fn=_f(_ml_pipe,"predict_for_symbol")
    if fn:
        try:return{"prediction":await _t(fn,symbol),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"prediction":{},"error":"N/A"}

# ── ANGELONE ──
@router.get("/angelone/ltp")
async def angel_ltp(symbol:str=Query(...)):
    fn=_f(_angel,"get_ltp")
    if fn:
        try:return{"ltp":await _t(fn,symbol),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"ltp":0,"error":"N/A"}

@router.get("/angelone/positions")
async def angel_positions():
    fn=_f(_angel,"get_positions")
    if fn:
        try:return{"positions":await _t(fn),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"positions":[]}

# ── AI MARKET VERDICT (dedicated endpoint) ──
@router.get("/india/ai-verdict")
async def ai_verdict():
    c=_cached("ai_verdict",60)
    if c:return c
    fn=_f(_nifty,"get_ai_market_verdict")
    if fn:
        try:
            r={"verdict":await _t(fn),"ts":datetime.now(IST).isoformat()}
            _set_cache("ai_verdict",r)
            return r
        except:pass
    return{"verdict":"AI Verdict not available","ts":datetime.now(IST).isoformat()}

# ── VOICE ENGINE ──
@router.post("/voice/generate")
async def voice_generate(request:Request):
    body=await request.json()
    fn=_f(_voice,"generate_voice")
    fn2=_f(_voice,"text_to_speech")
    target=fn or fn2
    if target:
        try:return{"audio":await _t(target,body.get("text","")),"ts":datetime.now(IST).isoformat()}
        except:pass
    return{"audio":None,"error":"Voice N/A"}

# ═══════════════════════════════════════════════════════════════
# 🔥🚀 MEGA AI TRADER — Nuclear Autonomous Crypto Conqueror
# ═══════════════════════════════════════════════════════════════

@router.get("/mega-trader/status")
async def mega_trader_status(user_id:str="0"):
    fn=_f(_mega,"get_mega_trader_status")
    if fn:
        try:return await _t(fn,int(user_id))
        except Exception as e:return{"error":str(e)}
    return{"error":"Mega trader not available"}

@router.post("/mega-trader/create-wallet")
async def mega_create_wallet(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    fn=_f(_real_trader,"create_trading_wallet")
    if fn:
        try:return await _t(fn,uid)
        except Exception as e:return{"error":str(e)}
    return{"error":"Wallet creation not available"}

@router.post("/mega-trader/enable")
async def mega_enable(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    fn=_f(_real_trader,"enable_auto_trade")
    if fn:
        try:
            result=await _t(fn,uid)
            fn2=_f(_mega,"start_mega_trader")
            if fn2:await _t(fn2)
            return result
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.post("/mega-trader/disable")
async def mega_disable(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    fn=_f(_real_trader,"disable_auto_trade")
    if fn:
        try:return await _t(fn,uid)
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.get("/mega-trader/portfolio")
async def mega_portfolio(user_id:str="0"):
    fn=_f(_mega,"get_portfolio_inr")
    if fn:
        try:return await _t(fn,int(user_id))
        except Exception as e:return{"error":str(e)}
    return{"error":"Portfolio not available"}

@router.get("/mega-trader/scan")
async def mega_scan():
    c=_cached("mega_scan",30)
    if c:return c
    fn=_f(_mega,"get_live_scan_results")
    if fn:
        try:
            r=await fn()
            _set_cache("mega_scan",r)
            return r
        except Exception as e:return{"error":str(e)}
    return{"error":"Scan not available"}

@router.post("/mega-trader/buy")
async def mega_buy(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    mint=body.get("mint","")
    sol_amount=float(body.get("sol_amount",0.01))
    fn=_f(_real_trader,"buy_token")
    if fn:
        try:return await _t(fn,uid,mint,sol_amount)
        except Exception as e:return{"error":str(e)}
    return{"error":"Buy not available"}

@router.post("/mega-trader/sell")
async def mega_sell(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    mint=body.get("mint","")
    sell_pct=float(body.get("sell_pct",100))
    fn=_f(_real_trader,"sell_token")
    if fn:
        try:return await _t(fn,uid,mint,sell_pct)
        except Exception as e:return{"error":str(e)}
    return{"error":"Sell not available"}

@router.post("/mega-trader/transfer")
async def mega_transfer(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    destination=body.get("destination","")
    sol_amount=float(body.get("sol_amount",0))
    fn=_f(_mega,"transfer_to_phantom")
    if fn:
        try:return await _t(fn,uid,destination,sol_amount)
        except Exception as e:return{"error":str(e)}
    return{"error":"Transfer not available"}

@router.get("/mega-trader/transfers")
async def mega_transfers(user_id:str="0"):
    fn=_f(_mega,"get_transfer_history")
    if fn:
        try:return{"transfers":await _t(fn,int(user_id))}
        except:pass
    return{"transfers":[]}

@router.get("/mega-trader/rug-check")
async def mega_rug_check(mint:str=Query(...),chain:str="solana"):
    fn=_f(_mega,"check_rug_safety")
    if fn:
        try:return await fn(mint,chain)
        except Exception as e:return{"error":str(e)}
    return{"error":"Rug check not available"}

# ═══════════════════════════════════════════════════════════════
# 🔥⚡💎 CONQUEROR AI TRADER — Ultimate Autonomous Crypto Brain
# ═══════════════════════════════════════════════════════════════

@router.get("/conqueror/status")
async def conqueror_status(user_id:str="0"):
    fn=_f(_conqueror,"get_conqueror_status")
    if fn:
        try:return await _t(fn,int(user_id))
        except Exception as e:return{"error":str(e)}
    return{"error":"Conqueror not available"}

@router.post("/conqueror/start")
async def conqueror_start(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    # Enable auto trade for user
    fn_enable=_f(_real_trader,"enable_auto_trade")
    if fn_enable:
        try:await _t(fn_enable,uid)
        except:pass
    # Start conqueror engine
    fn=_f(_conqueror,"start_conqueror")
    if fn:
        try:return await _t(fn)
        except Exception as e:return{"error":str(e)}
    return{"error":"Conqueror not available"}

@router.post("/conqueror/stop")
async def conqueror_stop(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    fn_disable=_f(_real_trader,"disable_auto_trade")
    if fn_disable:
        try:await _t(fn_disable,uid)
        except:pass
    fn=_f(_conqueror,"stop_conqueror")
    if fn:
        try:return await _t(fn)
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.post("/conqueror/create-wallet")
async def conqueror_create_wallet(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    fn=_f(_real_trader,"create_trading_wallet")
    if fn:
        try:return await _t(fn,uid)
        except Exception as e:return{"error":str(e)}
    return{"error":"Wallet creation not available"}

@router.get("/conqueror/portfolio")
async def conqueror_portfolio(user_id:str="0"):
    fn=_f(_conqueror,"get_portfolio_inr")
    if fn:
        try:return await _t(fn,int(user_id))
        except Exception as e:return{"error":str(e)}
    return{"error":"Portfolio not available"}

@router.get("/conqueror/scan")
async def conqueror_scan():
    c=_cached("conqueror_scan",20)
    if c:return c
    fn=_f(_conqueror,"get_live_scan")
    if fn:
        try:
            r=await fn()
            _set_cache("conqueror_scan",r)
            return r
        except Exception as e:return{"error":str(e)}
    return{"error":"Scan not available"}

@router.post("/conqueror/set-phantom")
async def conqueror_set_phantom(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    address=body.get("phantom_address","")
    fn=_f(_conqueror,"set_phantom_address")
    if fn:
        try:return await _t(fn,uid,address)
        except Exception as e:return{"error":str(e)}
    return{"error":"N/A"}

@router.post("/conqueror/transfer")
async def conqueror_transfer(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    sol=float(body.get("sol_amount",0))
    dst=body.get("destination","")
    fn=_f(_conqueror,"transfer_to_phantom")
    if fn:
        try:return await _t(fn,uid,sol,dst)
        except Exception as e:return{"error":str(e)}
    return{"error":"Transfer not available"}

@router.post("/conqueror/withdraw-profits")
async def conqueror_withdraw(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    fn=_f(_conqueror,"auto_withdraw_profits")
    if fn:
        try:return await _t(fn,uid)
        except Exception as e:return{"error":str(e)}
    return{"error":"Withdraw not available"}

@router.get("/conqueror/rug-check")
async def conqueror_rug_check(mint:str=Query(...),chain:str="solana"):
    fn=_f(_conqueror,"deep_rug_check")
    if fn:
        try:return await fn(mint,chain)
        except Exception as e:return{"error":str(e)}
    return{"error":"Rug check not available"}

@router.post("/conqueror/buy")
async def conqueror_buy(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    mint=body.get("mint","")
    sol=float(body.get("sol_amount",0.01))
    fn=_f(_real_trader,"buy_token")
    if fn:
        try:return await _t(fn,uid,mint,sol)
        except Exception as e:return{"error":str(e)}
    return{"error":"Buy not available"}

@router.post("/conqueror/sell")
async def conqueror_sell(request:Request):
    body=await request.json()
    uid=int(body.get("user_id",0))
    mint=body.get("mint","")
    pct=float(body.get("sell_pct",100))
    fn=_f(_real_trader,"sell_token")
    if fn:
        try:return await _t(fn,uid,mint,pct)
        except Exception as e:return{"error":str(e)}
    return{"error":"Sell not available"}

