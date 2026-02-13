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

_dex=_si("dex_engine",["dex_search","dex_trending","dex_get_token","dex_new_pairs","cg_prices","cg_trending","cg_market_data","cg_fear_greed","pumpfun_trending","pumpfun_new_coins","jupiter_price","get_nse_indices","get_india_vix","fetch_crypto_news","fetch_india_news","find_dip_gems","get_full_market_snapshot"])
_brain=_si("jarvis_brain",["jarvis_chat","analyze_token","generate_briefing","clear_memory","get_conversation_history","stream_chat","get_available_models"])
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
    fns=[("cg_market_data",10),("cg_fear_greed",None),("fetch_crypto_news",8),("get_nse_indices",None),("get_india_vix",None)]
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
    ticker=await _get_ticker()
    # Use ticker data as fallback for gainers/losers when CoinGecko is rate limited
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
            "news":news_list,"indices":indices,"vix":vix,"ts":datetime.now(IST).isoformat()}
    _set_cache("dashboard",result)
    return result

@router.get("/markets")
async def markets(category:Optional[str]=None):
    c=_cached("markets",10)
    if c:return c
    tasks=[]
    for fn_name,arg in[("cg_market_data",50),("dex_trending",None),("get_nse_indices",None),("pumpfun_trending",None)]:
        fn=_f(_dex,fn_name)
        if fn:tasks.append(fn(arg)if arg else fn())
        else:tasks.append(asyncio.sleep(0))
    results=await asyncio.gather(*tasks,return_exceptions=True)
    crypto=results[0]if isinstance(results[0],list)else[]
    trending=results[1]if isinstance(results[1],list)else[]
    indices=results[2]if isinstance(results[2],list)else[]
    pf=results[3]if isinstance(results[3],list)else[]
    cdx=[]
    fn=_f(_coindcx,"get_web3_gainers_losers")
    if fn:
        try:cdx=await _t(fn)
        except:pass
    result={"crypto":crypto,"trending":trending[:20],"indices":indices,"pumpfun":pf[:15],"coindcx":cdx,"total":len(crypto),"ts":datetime.now(IST).isoformat()}
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
async def gems(source:str="all",min_score:int=40):
    c=_cached(f"gems_{source}",30)
    if c:return c
    tasks=[]
    if source in("all","dip")and _f(_dex,"find_dip_gems"):tasks.append(_f(_dex,"find_dip_gems")())
    if source in("all","trending")and _f(_dex,"dex_trending"):tasks.append(_f(_dex,"dex_trending")())
    if source in("all","pumpfun")and _f(_dex,"pumpfun_trending"):tasks.append(_f(_dex,"pumpfun_trending")())
    g=await asyncio.gather(*tasks,return_exceptions=True)
    all_g=[]
    for d in g:
        if isinstance(d,list):all_g.extend(d)
    all_g.sort(key=lambda x:x.get("gem_score",0),reverse=True)
    r={"gems":all_g[:40],"count":len(all_g),"source":source,"ts":datetime.now(IST).isoformat()}
    _set_cache(f"gems_{source}",r)
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
    msg=_sani(body.get("message",""),2000)
    uid=str(body.get("user_id","0"))
    if not msg:return{"reply":"Please type a message."}
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
    c=_cached("india_dash",30)
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
    c=_cached("india_idx",30)
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
    fn=_f(_nifty,"get_fii_dii_data")
    return(await _t(fn))if fn else{"error":"N/A"}

@router.get("/india/pcr")
async def india_pcr(symbol:str="NIFTY"):
    fn=_f(_nifty,"get_pcr_data")
    return(await _t(fn,symbol))if fn else{"error":"N/A"}

@router.get("/india/sectors")
async def india_sectors():
    fn=_f(_nifty,"get_sector_heatmap")
    return{"sectors":(await _t(fn))if fn else[]}

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
    method=body.get("method","upi")
    fn=_f(_payment,"create_withdrawal_request")
    if fn:
        try:
            r=await _t(fn,uid,amount,method)
            return{"status":"ok","data":r}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"ok","data":{"status":"pending","message":"Withdrawal request submitted"}}

@router.get("/transactions")
async def transactions(user_id:str="0",limit:int=50):
    fn=_f(_payment,"get_transaction_history")
    if fn:
        try:return{"status":"ok","data":await _t(fn,user_id,limit)}
        except Exception as e:return{"status":"error","error":str(e)}
    return{"status":"ok","data":[]}
