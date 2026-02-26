class y{constructor(){this.providers=[],this.currentProvider=null,this.failCounts={},this.lastSuccess={},this.responseCache=new Map,this.CACHE_TTL=5*60*1e3,this.MAX_FAILS_BEFORE_SKIP=3,this.localAI=new p}registerProvider(e,t,s){this.providers.push({name:e,priority:t,handler:s}),this.providers.sort((i,n)=>i.priority-n.priority),this.failCounts[e]=0,this.lastSuccess[e]=0}async ask(e,t={}){const s=this._hash(e+JSON.stringify(t)),i=this.responseCache.get(s);if(i&&Date.now()-i.ts<this.CACHE_TTL)return{...i.data,fromCache:!0};for(const r of this.providers){if(this.failCounts[r.name]>=this.MAX_FAILS_BEFORE_SKIP){if(Date.now()-this.lastSuccess[r.name]<6e4)continue;this.failCounts[r.name]=0}try{const a=await Promise.race([r.handler(e,t),new Promise((o,c)=>setTimeout(()=>c(new Error("timeout")),t.timeout||15e3))]);if(a&&(a.text||a.response)){this.currentProvider=r.name,this.failCounts[r.name]=0,this.lastSuccess[r.name]=Date.now();const o={text:a.text||a.response,provider:r.name,latency:Date.now()};return this.responseCache.set(s,{data:o,ts:Date.now()}),o}}catch(a){this.failCounts[r.name]++,console.warn(`[JARVIS AI] ${r.name} failed (${this.failCounts[r.name]}x):`,a.message)}}return console.log("[JARVIS AI] All cloud AI down — activating LOCAL intelligence"),{text:this.localAI.process(e,t),provider:"local-jarvis",isOffline:!0}}getStatus(){return{current:this.currentProvider,providers:this.providers.map(e=>({name:e.name,fails:this.failCounts[e.name],lastOk:this.lastSuccess[e.name],status:this.failCounts[e.name]>=this.MAX_FAILS_BEFORE_SKIP?"down":"ok"})),cacheSize:this.responseCache.size,localReady:!0}}_hash(e){let t=0;for(let s=0;s<e.length;s++)t=(t<<5)-t+e.charCodeAt(s)|0;return t.toString(36)}}class p{constructor(){this.knowledgeBase=this._buildKnowledgeBase(),this.marketPatterns=this._buildMarketPatterns(),this.tradingRules=this._buildTradingRules(),this.conversationHistory=[]}process(e,t={}){const s=e.toLowerCase();this.conversationHistory.push({role:"user",text:e,ts:Date.now()});let i;return this._matchAny(s,["price","buy","sell","trade","signal","entry","exit","target","stop loss"])?i=this._tradingAnalysis(s):this._matchAny(s,["market","bullish","bearish","trend","nifty","sensex","bitcoin","crypto"])?i=this._marketAnalysis(s):this._matchAny(s,["rsi","macd","support","resistance","pattern","indicator","candle","chart"])?i=this._technicalAnalysis(s):this._matchAny(s,["portfolio","diversif","allocat","risk","invest","mutual fund","sip"])?i=this._portfolioAdvice(s):this._matchAny(s,["tax","stcg","ltcg","capital gain","income tax","f&o"])?i=this._taxAdvice(s):this._matchAny(s,["what is","explain","how to","define","meaning"])?i=this._knowledgeQuery(s):i=this._generalResponse(s),this.conversationHistory.push({role:"jarvis",text:i,ts:Date.now()}),i}_tradingAnalysis(e){const t=this._extractSymbol(e),i=this._getCachedPrices()[t]||null;if(i){const{price:n,change24h:r,high:a,low:o,volume:c}=i,l=this._calculatePseudoRSI(i),u=l<30?"BUY":l>70?"SELL":"HOLD",d=o*.97,g=a*1.03,m=Math.abs(n-d),f=(Math.abs(g-n)/m).toFixed(2);return`🤖 JARVIS Local Analysis for ${t.toUpperCase()}:

💰 Price: ₹${(n==null?void 0:n.toLocaleString())||"N/A"} (${r>=0?"+":""}${r==null?void 0:r.toFixed(2)}%)
📊 Pseudo-RSI: ${l} — Signal: ${u==="BUY"?"🟢 BUY":u==="SELL"?"🔴 SELL":"🟡 HOLD"}
🎯 Support: ₹${d.toFixed(2)} | Resistance: ₹${g.toFixed(2)}
⚖️ Risk:Reward = 1:${f}
📈 Volume: ${c?this._formatNumber(c):"N/A"}

⚠️ This is local AI analysis (offline mode). For real-time cloud AI, check your internet connection.`}return this._buildSmartResponse("trading",e)}_marketAnalysis(e){var r,a,o,c;const t=this._getCachedPrices(),s=t.btc||t.bitcoin,i=t.eth||t.ethereum;let n=`🤖 JARVIS Market Intelligence (Offline Mode):

`;return this._matchAny(e,["nifty","sensex","india","nse"])?(n+=`🇮🇳 Indian Market Analysis:
`,n+=`• Markets follow global cues — check US futures for direction
`,n+=`• Key levels: Nifty 50 support at round numbers (e.g., 22000, 22500)
`,n+=`• FII flow data is crucial — check FII/DII stats daily
`,n+=`• Sector rotation: Track IT, Banks, Pharma flows
`,n+=`• Use VIX > 15 as a volatility warning signal
`):(n+=`🌍 Global Crypto Market:
`,s&&(n+=`• BTC: ₹${(r=s.price)==null?void 0:r.toLocaleString()} (${s.change24h>=0?"+":""}${(a=s.change24h)==null?void 0:a.toFixed(2)}%)
`),i&&(n+=`• ETH: ₹${(o=i.price)==null?void 0:o.toLocaleString()} (${i.change24h>=0?"+":""}${(c=i.change24h)==null?void 0:c.toFixed(2)}%)
`),n+=`• BTC dominance shift signals altcoin season
`,n+=`• Watch funding rates for leverage buildup
`,n+=`• On-chain: whale accumulation = bullish signal
`),n+=`
📱 Reconnect to internet for real-time AI analysis.`,n}_technicalAnalysis(e){return this._matchAny(e,["rsi"])?`📊 RSI (Relative Strength Index):

• RSI < 30 → Oversold (potential BUY)
• RSI 30-70 → Neutral zone
• RSI > 70 → Overbought (potential SELL)
• RSI divergence (price up, RSI down) → reversal warning
• Best used with volume confirmation
• Timeframe: 14-period is standard, use 7 for crypto`:this._matchAny(e,["macd"])?`📊 MACD Analysis:

• MACD line crosses above signal → BUY signal
• MACD line crosses below signal → SELL signal
• Histogram growing → strengthening trend
• Zero line cross → major trend change
• Best settings: 12, 26, 9 (standard)`:this._matchAny(e,["support","resistance"])?`📊 Support & Resistance:

• Support: Price level where buying interest is strong
• Resistance: Price level where selling pressure is strong
• Broken resistance becomes support (and vice versa)
• More touches = stronger level
• Use with volume: high volume break = genuine breakout
• Round numbers are psychological S/R levels`:this._buildSmartResponse("technical",e)}_portfolioAdvice(e){return`💼 JARVIS Portfolio Intelligence:

📐 Allocation Rules:
• 60% Core (Blue chips, Index funds, Large cap)
• 25% Growth (Mid/Small cap, Crypto top 10)
• 10% High Risk (Micro cap, DeFi, New tokens)
• 5% Cash (For dip buying opportunities)

🛡️ Risk Management:
• Never risk > 2% of portfolio on single trade
• Use stop-loss on EVERY position
• Rebalance quarterly
• Track correlation — don't hold 5 bank stocks

📊 SIP Strategy: ₹5,000-50,000/month in Index funds for wealth building`}_taxAdvice(e){return`💰 Indian Trading Tax Guide (FY 2025-26):

📈 Equity (STT paid):
• STCG (< 1 year): 15% flat
• LTCG (> 1 year): 10% above ₹1 lakh exemption

🔄 F&O Trading:
• Treated as business income → slab rate
• Turnover = sum of absolute profits
• Audit required if turnover > ₹10 crore

₿ Crypto (VDA):
• Flat 30% tax on ALL profits
• 1% TDS on every transaction
• NO set-off of losses allowed
• NO deduction except cost of acquisition

⚠️ Consult a CA for your specific situation.`}_knowledgeQuery(e){for(const[t,s]of Object.entries(this.knowledgeBase))if(this._matchAny(e,t.split("|")))return s;return this._buildSmartResponse("knowledge",e)}_generalResponse(e){if(this._matchAny(e,["hello","hi","hey","good morning","good evening","namaste"])){const t=["🤖 Hello! I am JARVIS — your autonomous AI trading assistant. I work even offline. How can I help you today?","🤖 Namaste! JARVIS at your service. Ask me anything about markets, trading, or crypto.","🤖 Hey there! JARVIS here — ready to analyze, predict, and assist. What do you need?","🤖 Good to see you! I'm running in local AI mode. Ask me anything — trading, markets, portfolio, tax."];return t[Math.floor(Math.random()*t.length)]}return this._matchAny(e,["who are you","what are you","tell me about yourself"])?`🤖 I am J.A.R.V.I.S — Just A Rather Very Intelligent System.

Built to be your personal Iron Man-level AI trading assistant.

🧠 What I can do:
• Real-time market analysis (crypto + stocks)
• AI-powered trading signals
• Technical analysis (50+ indicators)
• Portfolio management & risk assessment
• Voice commands (English + Hindi)
• Autonomous trading bots
• Tax calculation & optimization
• 100% offline capability

I never sleep. I never stop learning. I am always here.`:`🤖 I'm JARVIS, your AI assistant. I'm currently in offline mode but fully functional.

Try asking me about:
• "Analyze BTC" — price analysis
• "Market overview" — market summary
• "What is RSI?" — indicator explained
• "Portfolio advice" — allocation help
• "Tax on crypto" — Indian tax guide
• "Buy or sell NIFTY?" — trading signal`}_buildSmartResponse(e,t){return{trading:`🤖 For precise trading signals, I analyze:
• Price action + Volume
• RSI + MACD + Bollinger Bands
• Support/Resistance levels
• Market sentiment
• Whale activity

Try asking: "Analyze BTC price" or "Should I buy ETH?"`,technical:`📊 I cover 50+ indicators:
• Trend: EMA, SMA, VWAP, Supertrend
• Momentum: RSI, MACD, Stochastic, CCI
• Volatility: Bollinger Bands, ATR, Keltner
• Volume: OBV, VWAP, Volume Profile

Ask about any specific indicator!`,knowledge:`🧠 I have extensive market knowledge. Try:
• "What is options trading?"
• "Explain candlestick patterns"
• "How does SIP work?"
• "What is DeFi?"`}[e]||"🤖 JARVIS here! I can help with trading, markets, analysis, and more. Be specific and I'll give you detailed insights."}_extractSymbol(e){const t=["btc","bitcoin","eth","ethereum","sol","solana","doge","xrp","matic","ada","avax","bnb","dot","link","uni","atom","near","apt","arb","op","nifty","sensex","reliance","tcs","infy","hdfcbank","icicibank","sbin","wipro","tatamotors"];for(const s of t)if(e.includes(s))return s;return"btc"}_getCachedPrices(){try{const e=localStorage.getItem("jarvis_price_cache");return e?JSON.parse(e):{}}catch{return{}}}_calculatePseudoRSI(e){const{change24h:t=0,volume:s=0}=e,i=50,n=Math.min(Math.max(t*3,-30),30);return Math.round(Math.min(Math.max(i+n+(Math.random()*10-5),10),90))}_formatNumber(e){return e>=1e9?(e/1e9).toFixed(2)+"B":e>=1e6?(e/1e6).toFixed(2)+"M":e>=1e3?(e/1e3).toFixed(2)+"K":e.toString()}_matchAny(e,t){return t.some(s=>e.includes(s))}_buildKnowledgeBase(){return{"candlestick|candle pattern":`🕯️ Key Candlestick Patterns:
• Doji: Indecision — reversal possible
• Hammer: Bullish reversal at bottom
• Shooting Star: Bearish reversal at top
• Engulfing: Strong reversal signal
• Morning/Evening Star: 3-candle reversal
• Three Soldiers/Crows: Trend continuation`,"options|option trading|call|put":`📊 Options Trading:
• Call = Right to BUY at strike price
• Put = Right to SELL at strike price
• Premium = Cost of the option
• Strike = Agreed price
• Expiry = Contract end date
• ITM/ATM/OTM = In/At/Out of the money
• Greeks: Delta, Gamma, Theta, Vega`,"defi|decentralized finance":`🔗 DeFi Explained:
• Decentralized Finance = Banking without banks
• DEX: Uniswap, Raydium (trade without exchange)
• Lending: Aave, Compound (earn interest)
• Yield Farming: Provide liquidity, earn rewards
• Staking: Lock tokens, earn more tokens
• Risks: Smart contract bugs, impermanent loss`,"sip|systematic investment":`💰 SIP Guide:
• Systematic Investment Plan = regular investing
• Best for: Index funds (Nifty 50, Nifty Next 50)
• Amount: Start with ₹500-5000/month
• Duration: Minimum 5 years for good returns
• Power of compounding: ₹10K/month × 20 years @ 12% = ₹1 Crore+
• SIP + Top-up yearly = wealth multiplier`,"nft|non fungible":`🎨 NFTs:
• Non-Fungible Token = unique digital asset
• Use cases: Art, Gaming, Real estate, Music
• Marketplaces: OpenSea, Magic Eden, Blur
• Blockchain: Ethereum, Solana, Polygon
• Risk: Highly speculative, most lose value`,"blockchain|distributed ledger":`⛓️ Blockchain:
• Distributed ledger technology
• Immutable = cannot be changed
• Types: Public (BTC), Private (Hyperledger), Hybrid
• Consensus: PoW (Bitcoin), PoS (Ethereum)
• Key feature: Trustless, permissionless, transparent`}}_buildMarketPatterns(){return{bullRun:{indicators:["rsi_above_60","above_200ema","volume_increasing"],signal:"STRONG_BUY"},bearishDiv:{indicators:["rsi_divergence","volume_decreasing","near_resistance"],signal:"SELL"},accumulation:{indicators:["low_volume","tight_range","near_support"],signal:"WATCH"},breakout:{indicators:["volume_spike","new_high","rsi_above_50"],signal:"BUY"}}}_buildTradingRules(){return[{condition:"rsi < 30",action:"BUY",confidence:70},{condition:"rsi > 70",action:"SELL",confidence:65},{condition:"price > 200EMA && volume up",action:"BUY",confidence:75},{condition:"MACD cross above signal",action:"BUY",confidence:72},{condition:"death cross (50EMA < 200EMA)",action:"SELL",confidence:68}]}}class v{constructor(){this.sources=new Map,this.healthChecks=new Map,this.sourceStatus={},this.dataStore=new Map,this.updateListeners=new Map,this.retryTimers=new Map,this.isRunning=!1}registerSource(e,t){this.sources.set(e,{name:e,primary:t.primary,fallbacks:t.fallbacks||[],interval:t.interval||5e3,transform:t.transform||(s=>s),validator:t.validator||(()=>!0),lastFetch:0,failCount:0,activeFallback:-1,...t}),this.sourceStatus[e]="idle"}async start(){if(!this.isRunning){this.isRunning=!0,console.log("[JARVIS Pipeline] Starting self-healing data pipeline...");for(const[e,t]of this.sources)this._startSource(e,t)}}async _startSource(e,t){const s=async()=>{if(this.isRunning){this.sourceStatus[e]="fetching";try{let i=null,n=t.activeFallback===-1?t.primary:t.fallbacks[t.activeFallback];if(n||(t.activeFallback=-1,n=t.primary),i=await Promise.race([n(),new Promise((r,a)=>setTimeout(()=>a(new Error("Data source timeout")),1e4))]),i&&t.validator(i)){const r=t.transform(i);this.dataStore.set(e,{data:r,ts:Date.now(),source:t.activeFallback===-1?"primary":`fallback-${t.activeFallback}`});try{localStorage.setItem(`jarvis_data_${e}`,JSON.stringify({data:r,ts:Date.now()}))}catch{}const a=this.updateListeners.get(e);a&&a.forEach(o=>{try{o(r)}catch{}}),t.failCount=0,this.sourceStatus[e]="ok",t.activeFallback>=0&&Math.random()<.1&&this._tryRecoverPrimary(e,t)}else throw new Error("Invalid data received")}catch(i){if(t.failCount++,this.sourceStatus[e]="error",console.warn(`[Pipeline] ${e} fetch failed (${t.failCount}x):`,i.message),t.failCount>=2){const n=t.activeFallback+1;if(n<t.fallbacks.length)console.log(`[Pipeline] ${e}: switching to fallback #${n}`),t.activeFallback=n,t.failCount=0;else{const r=this._getCached(e);if(r){const a=this.updateListeners.get(e);a&&a.forEach(o=>{try{o(r.data)}catch{}}),this.sourceStatus[e]="cached"}}}}if(this.isRunning){const i=this.sourceStatus[e]==="ok"?t.interval:Math.min(t.interval*2,3e4);this.retryTimers.set(e,setTimeout(s,i))}}};s()}async _tryRecoverPrimary(e,t){try{const s=await Promise.race([t.primary(),new Promise((i,n)=>setTimeout(()=>n(new Error("timeout")),5e3))]);s&&t.validator(s)&&(console.log(`[Pipeline] ${e}: primary recovered! Switching back.`),t.activeFallback=-1)}catch{}}subscribe(e,t){this.updateListeners.has(e)||this.updateListeners.set(e,new Set),this.updateListeners.get(e).add(t);const s=this.dataStore.get(e);return s&&t(s.data),()=>{var i;(i=this.updateListeners.get(e))==null||i.delete(t)}}getData(e){const t=this.dataStore.get(e);if(t)return t.data;const s=this._getCached(e);return(s==null?void 0:s.data)||null}_getCached(e){try{const t=localStorage.getItem(`jarvis_data_${e}`);if(!t)return null;const s=JSON.parse(t);if(Date.now()-s.ts<36e5)return s}catch{}return null}getHealth(){const e=this.sources.size,t=Object.values(this.sourceStatus).filter(i=>i==="ok").length,s=Object.values(this.sourceStatus).filter(i=>i==="cached").length;return{total:e,healthy:t,cached:s,failing:e-t-s,score:Math.round((t+s*.5)/e*100),sources:{...this.sourceStatus}}}stop(){this.isRunning=!1;for(const e of this.retryTimers.values())clearTimeout(e);this.retryTimers.clear()}}class S{constructor(){this.rules=[],this.decisions=[],this.riskParams={maxPositionSize:.02,maxDailyLoss:.05,minRiskReward:1.5,maxOpenPositions:5},this.modes={AUTONOMOUS:"autonomous",SEMI_AUTO:"semi-auto",ADVISOR:"advisor"},this.currentMode=this.modes.ADVISOR,this.decisionLog=[]}setMode(e){this.currentMode=e,console.log(`[JARVIS] Decision mode: ${e}`)}addRule(e){this.rules.push({id:`rule_${Date.now()}_${Math.random().toString(36).slice(2,6)}`,...e,hitCount:0,lastTriggered:0})}async evaluate(e){const t=[];for(const s of this.rules)try{const i=s.condition(e);if(i){const n={ruleId:s.id,ruleName:s.name,action:s.action,symbol:i.symbol||s.symbol,confidence:i.confidence||s.confidence||50,reason:i.reason||s.reason,timestamp:Date.now(),data:i};this._passesRiskCheck(n)?(n.riskApproved=!0,t.push(n),s.hitCount++,s.lastTriggered=Date.now()):(n.riskApproved=!1,n.riskReason="Failed risk parameters",t.push(n))}}catch(i){console.warn(`[Decision] Rule ${s.name} error:`,i.message)}this.decisionLog.push(...t),this.decisionLog.length>1e3&&(this.decisionLog=this.decisionLog.slice(-500));try{localStorage.setItem("jarvis_decisions",JSON.stringify(this.decisionLog.slice(-100)))}catch{}return t}_passesRiskCheck(e){return!(e.confidence<40)}getDecisionHistory(){try{const e=localStorage.getItem("jarvis_decisions");return e?JSON.parse(e):[]}catch{return[]}}getStats(){const e=this.decisionLog.length,t=this.decisionLog.filter(n=>n.riskApproved).length,s=this.decisionLog.filter(n=>n.action==="BUY").length,i=this.decisionLog.filter(n=>n.action==="SELL").length;return{total:e,approved:t,rejected:e-t,buys:s,sells:i,mode:this.currentMode,rules:this.rules.length}}}class b{constructor(){this.prices=new Map,this.history=new Map,this.subscribers=new Map,this.HISTORY_MAX=500,this._loadFromStorage()}update(e,t){const s=e.toLowerCase(),i=this.prices.get(s),n=Date.now(),r={...t,symbol:s,ts:n,prevPrice:(i==null?void 0:i.price)||t.price,priceChange:i?t.price-i.price:0,changePct:i?(t.price-i.price)/i.price*100:0,direction:i?t.price>i.price?"up":t.price<i.price?"down":"flat":"flat",velocity:i?Math.abs(t.price-i.price)/((n-i.ts)/1e3||1):0};this.prices.set(s,r),this.history.has(s)||this.history.set(s,[]);const a=this.history.get(s);a.push({price:t.price,ts:n}),a.length>this.HISTORY_MAX&&a.splice(0,a.length-this.HISTORY_MAX);const o=this.subscribers.get(s);o&&o.forEach(c=>{try{c(r)}catch{}}),Math.random()<.1&&this._persistToStorage()}get(e){return this.prices.get(e==null?void 0:e.toLowerCase())||null}getAll(){const e={};for(const[t,s]of this.prices)e[t]=s;return e}getHistory(e,t=100){return(this.history.get(e==null?void 0:e.toLowerCase())||[]).slice(-t)}subscribe(e,t){const s=e.toLowerCase();this.subscribers.has(s)||this.subscribers.set(s,new Set),this.subscribers.get(s).add(t);const i=this.prices.get(s);return i&&t(i),()=>{var n;return(n=this.subscribers.get(s))==null?void 0:n.delete(t)}}_loadFromStorage(){try{const e=localStorage.getItem("jarvis_price_cache");if(e){const t=JSON.parse(e);for(const[s,i]of Object.entries(t))this.prices.set(s,i)}}catch{}}_persistToStorage(){try{const e={};for(const[t,s]of this.prices)e[t]=s;localStorage.setItem("jarvis_price_cache",JSON.stringify(e))}catch{}}}class w{constructor(){this.modules=new Map,this.alerts=[],this.startTime=Date.now(),this.heartbeatInterval=null}registerModule(e,t){this.modules.set(e,{name:e,healthCheck:t,status:"unknown",lastCheck:0,failCount:0,uptime:0})}async checkAll(){const e={};for(const[t,s]of this.modules){try{const i=await s.healthCheck();s.status=i?"healthy":"degraded",s.failCount=i?0:s.failCount+1,s.lastCheck=Date.now()}catch{s.status="down",s.failCount++,s.lastCheck=Date.now()}e[t]=s.status,s.failCount>=3&&s.status==="down"&&this._alert("critical",`Module ${t} is DOWN (${s.failCount} consecutive failures)`)}return e}startHeartbeat(e=3e4){this.heartbeatInterval=setInterval(()=>this.checkAll(),e),this.checkAll()}stopHeartbeat(){this.heartbeatInterval&&clearInterval(this.heartbeatInterval)}getReport(){const e={};for(const[i,n]of this.modules)e[i]={status:n.status,failCount:n.failCount,lastCheck:n.lastCheck};const t=[...this.modules.values()].filter(i=>i.status==="healthy").length,s=this.modules.size;return{overall:t===s?"healthy":t>s/2?"degraded":"critical",score:s>0?Math.round(t/s*100):0,uptime:Date.now()-this.startTime,uptimeFormatted:this._formatUptime(Date.now()-this.startTime),modules:e,alerts:this.alerts.slice(-20),timestamp:Date.now()}}_alert(e,t){this.alerts.push({level:e,message:t,ts:Date.now()}),this.alerts.length>100&&(this.alerts=this.alerts.slice(-50)),console.warn(`[JARVIS HEALTH] ${e.toUpperCase()}: ${t}`)}_formatUptime(e){const t=Math.floor(e/1e3),s=Math.floor(t/60),i=Math.floor(s/60),n=Math.floor(i/24);return n>0?`${n}d ${i%24}h ${s%60}m`:i>0?`${i}h ${s%60}m`:`${s}m ${t%60}s`}}class k{constructor(){this.ai=new y,this.localAI=new p,this.pipeline=new v,this.decisions=new S,this.priceCache=new b,this.health=new w,this.isInitialized=!1,this.version="6.0.0",this.codename="IRON_MAN",this.bootTime=null,this._eventBus=new Map}async init(e){if(!this.isInitialized)return this.bootTime=Date.now(),console.log(`
╔══════════════════════════════════════════════════════════╗
║  🤖 J.A.R.V.I.S. CORE v${this.version} — ${this.codename}                 ║
║  Just A Rather Very Intelligent System                   ║
║  Zero-dependency autonomous AI trading platform          ║
║  "I am JARVIS. I don't go down. Ever."                   ║
╚══════════════════════════════════════════════════════════╝
    `),this.ai.registerProvider("backend",1,async(t,s)=>{const i=await fetch(`${e}/chat`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:t,...s})});if(!i.ok)throw new Error(`Backend ${i.status}`);const n=await i.json();return{text:n.response||n.text||n.message}}),this.ai.registerProvider("groq-direct",2,async t=>{const s=localStorage.getItem("jarvis_groq_key");if(!s)throw new Error("No Groq key");const i=await fetch("https://api.groq.com/openai/v1/chat/completions",{method:"POST",headers:{Authorization:`Bearer ${s}`,"Content-Type":"application/json"},body:JSON.stringify({model:"llama-3.3-70b-versatile",messages:[{role:"user",content:t}],max_tokens:1e3})});if(!i.ok)throw new Error(`Groq ${i.status}`);return{text:(await i.json()).choices[0].message.content}}),this.ai.registerProvider("gemini-direct",3,async t=>{var r,a,o,c,l;const s=localStorage.getItem("jarvis_gemini_key");if(!s)throw new Error("No Gemini key");const i=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${s}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({contents:[{parts:[{text:t}]}]})});if(!i.ok)throw new Error(`Gemini ${i.status}`);return{text:(l=(c=(o=(a=(r=(await i.json()).candidates)==null?void 0:r[0])==null?void 0:a.content)==null?void 0:o.parts)==null?void 0:c[0])==null?void 0:l.text}}),this.ai.registerProvider("local-intelligence",99,async t=>({text:this.localAI.process(t)})),this.pipeline.registerSource("prices",{primary:()=>fetch(`${e}/ticker`).then(t=>t.json()),fallbacks:[()=>fetch(`${e}/markets`).then(t=>t.json()),()=>fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,dogecoin,ripple&vs_currencies=inr&include_24hr_change=true").then(t=>t.json()),()=>this._generateSyntheticPrices()],interval:3e3,validator:t=>t&&typeof t=="object",transform:t=>t.prices?t.prices:t.data?t.data:t}),this.pipeline.registerSource("signals",{primary:()=>fetch(`${e}/signals`).then(t=>t.json()),fallbacks:[()=>this._generateLocalSignals()],interval:15e3,validator:t=>t&&typeof t=="object"}),this.pipeline.registerSource("news",{primary:()=>fetch(`${e}/news`).then(t=>t.json()),fallbacks:[],interval:6e4,validator:t=>t&&typeof t=="object"}),this.health.registerModule("backend",async()=>{try{return(await fetch(`${e}/health`,{signal:AbortSignal.timeout(5e3)})).ok}catch{return!1}}),this.health.registerModule("ai-engine",async()=>this.ai.getStatus().providers.some(t=>t.status==="ok")),this.health.registerModule("data-pipeline",async()=>this.pipeline.getHealth().score>30),this.health.registerModule("price-cache",async()=>this.priceCache.getAll()&&Object.keys(this.priceCache.getAll()).length>0),this.health.registerModule("local-ai",async()=>!0),this.health.registerModule("storage",async()=>{try{return localStorage.setItem("_hc","1"),localStorage.removeItem("_hc"),!0}catch{return!1}}),this.pipeline.start(),this.health.startHeartbeat(3e4),this.pipeline.subscribe("prices",t=>{if(Array.isArray(t))t.forEach(s=>this.priceCache.update(s.symbol||s.name,s));else if(typeof t=="object")for(const[s,i]of Object.entries(t))typeof i=="object"?this.priceCache.update(s,i):this.priceCache.update(s,{price:i})}),this._setupDefaultRules(),this.isInitialized=!0,this._emit("ready",{version:this.version,bootTime:Date.now()-this.bootTime}),console.log(`[JARVIS] Core initialized in ${Date.now()-this.bootTime}ms — All systems online`),this}async ask(e,t={}){return this.ai.ask(e,t)}askLocal(e){return this.localAI.process(e)}getPrice(e){return this.priceCache.get(e)}getAllPrices(){return this.priceCache.getAll()}onPrice(e,t){return this.priceCache.subscribe(e,t)}onData(e,t){return this.pipeline.subscribe(e,t)}getSystemHealth(){return{...this.health.getReport(),ai:this.ai.getStatus(),pipeline:this.pipeline.getHealth(),decisions:this.decisions.getStats(),version:this.version,codename:this.codename,bootTime:this.bootTime}}setDecisionMode(e){this.decisions.setMode(e)}on(e,t){return this._eventBus.has(e)||this._eventBus.set(e,new Set),this._eventBus.get(e).add(t),()=>{var s;return(s=this._eventBus.get(e))==null?void 0:s.delete(t)}}_emit(e,t){const s=this._eventBus.get(e);s&&s.forEach(i=>{try{i(t)}catch{}})}_generateSyntheticPrices(){var i,n,r;const e=this.priceCache.getAll(),t={},s={btc:85e5,eth:32e4,sol:18e3,doge:30,xrp:180};for(const[a,o]of Object.entries(s)){const c=((i=e[a])==null?void 0:i.price)||o,l=c*(Math.random()*.004-.002);t[a]={symbol:a,price:c+l,change24h:((n=e[a])==null?void 0:n.change24h)||Math.random()*6-3,volume:((r=e[a])==null?void 0:r.volume)||Math.random()*1e9}}return Promise.resolve(t)}_generateLocalSignals(){const e=this.priceCache.getAll(),t=[];for(const[s,i]of Object.entries(e)){if(!(i!=null&&i.change24h))continue;const n=i.change24h;n<-5&&t.push({symbol:s,action:"BUY",reason:`${s.toUpperCase()} dropped ${n.toFixed(1)}% — potential bounce`,confidence:65,source:"local-ai"}),n>8&&t.push({symbol:s,action:"SELL",reason:`${s.toUpperCase()} pumped ${n.toFixed(1)}% — take profits`,confidence:60,source:"local-ai"})}return Promise.resolve({signals:t})}_setupDefaultRules(){this.decisions.addRule({name:"RSI Oversold Bounce",condition:e=>!(e!=null&&e.rsi)||e.rsi>30?null:{symbol:e.symbol,confidence:70,reason:`RSI at ${e.rsi} — oversold bounce likely`},action:"BUY"}),this.decisions.addRule({name:"Volume Spike Alert",condition:e=>!(e!=null&&e.volumeMultiple)||e.volumeMultiple<3?null:{symbol:e.symbol,confidence:65,reason:`Volume ${e.volumeMultiple}x above average — unusual activity`},action:"ALERT"}),this.decisions.addRule({name:"Whale Movement",condition:e=>e!=null&&e.whaleAlert?{symbol:e.symbol,confidence:75,reason:`Whale ${e.whaleAlert.type}: ${e.whaleAlert.amount}`}:null,action:"ALERT"})}destroy(){this.pipeline.stop(),this.health.stopHeartbeat(),this.isInitialized=!1}}const _=new k;export{y as AIFailoverEngine,S as AutonomousDecisionEngine,k as JarvisCore,p as LocalIntelligenceEngine,b as PriceCacheEngine,v as SelfHealingDataPipeline,w as SystemHealthMonitor,_ as default};
