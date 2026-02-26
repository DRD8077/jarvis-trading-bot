const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/sql-wasm-browser-Bun_uS8f.js","assets/vendor-react-DwoDrinR.js"])))=>i.map(i=>d[i]);
import{_ as c}from"./index-CgyISwKQ.js";import"./vendor-react-DwoDrinR.js";import"./vendor-ui-D35vr7Mu.js";let i=null,L=null,_=!1;const R="jarvis_main_db",T="jarvis_sql_store";async function A(){if(i)return i;try{const n=(await c(async()=>{const{default:e}=await import("./sql-wasm-browser-Bun_uS8f.js").then(t=>t.s);return{default:e}},__vite__mapDeps([0,1]))).default;return i=await n({locateFile:e=>`https://sql.js.org/dist/${e}`}),i}catch{const e=(await c(async()=>{const{default:t}=await import("./sql-wasm-browser-Bun_uS8f.js").then(s=>s.s);return{default:t}},__vite__mapDeps([0,1]))).default;return i=await e(),i}}function u(){return new Promise((n,e)=>{const t=indexedDB.open(R,1);t.onupgradeneeded=()=>{const s=t.result;s.objectStoreNames.contains(T)||s.createObjectStore(T)},t.onsuccess=()=>n(t.result),t.onerror=()=>e(t.error)})}async function d(n){const e=await u();return new Promise((t,s)=>{const a=e.transaction(T,"readwrite");a.objectStore(T).put(n,"db"),a.oncomplete=()=>t(),a.onerror=()=>s(a.error)})}async function y(){const n=await u();return new Promise((e,t)=>{const a=n.transaction(T,"readonly").objectStore(T).get("db");a.onsuccess=()=>e(a.result),a.onerror=()=>t(a.error)})}const S=`
  -- Trades history
  CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    price REAL NOT NULL,
    quantity REAL NOT NULL,
    total REAL,
    fee REAL DEFAULT 0,
    exchange TEXT DEFAULT 'manual',
    strategy TEXT,
    pnl REAL DEFAULT 0,
    notes TEXT,
    tags TEXT,
    is_paper INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    closed_at TEXT
  );

  -- Candle data (OHLCV)
  CREATE TABLE IF NOT EXISTS candles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open REAL, high REAL, low REAL, close REAL,
    volume REAL,
    timestamp INTEGER NOT NULL,
    UNIQUE(symbol, timeframe, timestamp)
  );

  -- Portfolio holdings
  CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    quantity REAL NOT NULL DEFAULT 0,
    avg_buy_price REAL DEFAULT 0,
    current_price REAL DEFAULT 0,
    exchange TEXT DEFAULT 'manual',
    asset_type TEXT DEFAULT 'crypto',
    updated_at TEXT DEFAULT (datetime('now'))
  );

  -- Price alerts
  CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    condition TEXT NOT NULL,
    target_price REAL NOT NULL,
    current_price REAL,
    triggered INTEGER DEFAULT 0,
    triggered_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    notification_sent INTEGER DEFAULT 0,
    repeat_enabled INTEGER DEFAULT 0
  );

  -- AI Chat history
  CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,
    model TEXT,
    tokens_used INTEGER DEFAULT 0,
    response_time_ms INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
  );

  -- JARVIS memory (learns user preferences)
  CREATE TABLE IF NOT EXISTS jarvis_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    confidence REAL DEFAULT 1.0,
    access_count INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now'))
  );

  -- Trading signals
  CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    direction TEXT,
    confidence REAL,
    entry_price REAL,
    target_price REAL,
    stop_loss REAL,
    indicators TEXT,
    status TEXT DEFAULT 'active',
    result TEXT,
    pnl REAL,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT
  );

  -- Watchlists
  CREATE TABLE IF NOT EXISTS watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT 'Default',
    symbols TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
  );

  -- App settings/config
  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
  );

  -- Offline sync queue
  CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    synced_at TEXT
  );

  -- P&L journal
  CREATE TABLE IF NOT EXISTS pnl_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    realized_pnl REAL DEFAULT 0,
    unrealized_pnl REAL DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0,
    notes TEXT,
    mood TEXT,
    created_at TEXT DEFAULT (datetime('now'))
  );

  -- Tax records
  CREATE TABLE IF NOT EXISTS tax_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_year TEXT NOT NULL,
    symbol TEXT NOT NULL,
    buy_date TEXT, sell_date TEXT,
    buy_price REAL, sell_price REAL,
    quantity REAL,
    pnl REAL,
    holding_period_days INTEGER,
    tax_type TEXT,
    tax_amount REAL,
    created_at TEXT DEFAULT (datetime('now'))
  );

  -- System logs
  CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT DEFAULT 'info',
    module TEXT,
    message TEXT NOT NULL,
    data TEXT,
    created_at TEXT DEFAULT (datetime('now'))
  );

  -- Create indexes for performance
  CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
  CREATE INDEX IF NOT EXISTS idx_trades_created ON trades(created_at);
  CREATE INDEX IF NOT EXISTS idx_candles_symbol_tf ON candles(symbol, timeframe);
  CREATE INDEX IF NOT EXISTS idx_candles_ts ON candles(timestamp);
  CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol);
  CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_history(created_at);
  CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
  CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
  CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_queue(status);
  CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level);
`;class I{constructor(){this.db=null,this.ready=!1,this.autoSaveTimer=null,this.changesSinceLastSave=0}async init(){if(this.ready)return!0;try{await A();const e=await y().catch(()=>null);return e?(this.db=new i.Database(new Uint8Array(e)),console.log("[JarvisDB] Loaded existing database from IndexedDB")):(this.db=new i.Database,console.log("[JarvisDB] Created new database")),this.db.run(S),this.autoSaveTimer=setInterval(()=>this._autoSave(),3e4),this.ready=!0,L=this.db,_=!0,console.log("[JarvisDB] Database ready — 12 tables, indexed"),!0}catch(e){return console.error("[JarvisDB] Init failed:",e),!1}}async _autoSave(){if(!(this.changesSinceLastSave===0||!this.db))try{const e=this.db.export();await d(e.buffer),this.changesSinceLastSave=0}catch(e){console.warn("[JarvisDB] Auto-save failed:",e.message)}}async save(){if(!this.db)return;const e=this.db.export();await d(e.buffer),this.changesSinceLastSave=0}run(e,t=[]){if(!this.db)return null;try{return this.db.run(e,t),this.changesSinceLastSave++,!0}catch(s){return console.error("[JarvisDB] Query error:",s.message,e),!1}}query(e,t=[]){if(!this.db)return[];try{const s=this.db.exec(e,t);if(!s.length)return[];const a=s[0].columns;return s[0].values.map(r=>{const E={};return a.forEach((o,l)=>{E[o]=r[l]}),E})}catch(s){return console.error("[JarvisDB] Query error:",s.message),[]}}getOne(e,t=[]){return this.query(e,t)[0]||null}addTrade(e){return this.run(`INSERT INTO trades (symbol, side, price, quantity, total, fee, exchange, strategy, pnl, notes, tags, is_paper)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,[e.symbol,e.side,e.price,e.quantity,e.price*e.quantity,e.fee||0,e.exchange||"manual",e.strategy||"",e.pnl||0,e.notes||"",e.tags||"",e.isPaper?1:0])}getTrades(e={}){let t="SELECT * FROM trades WHERE 1=1";return e.symbol&&(t+=` AND symbol = '${e.symbol}'`),e.side&&(t+=` AND side = '${e.side}'`),e.isPaper!==void 0&&(t+=` AND is_paper = ${e.isPaper?1:0}`),t+=" ORDER BY created_at DESC",e.limit&&(t+=` LIMIT ${e.limit}`),this.query(t)}getTradeStats(){return this.getOne(`
      SELECT 
        COUNT(*) as total_trades,
        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
        SUM(pnl) as total_pnl,
        AVG(pnl) as avg_pnl,
        MAX(pnl) as best_trade,
        MIN(pnl) as worst_trade
      FROM trades WHERE is_paper = 0
    `)}insertCandles(e,t,s){const a=this.db.prepare(`INSERT OR REPLACE INTO candles (symbol, timeframe, open, high, low, close, volume, timestamp)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`);s.forEach(r=>{a.run([e,t,r.open,r.high,r.low,r.close,r.volume||0,r.timestamp])}),a.free(),this.changesSinceLastSave+=s.length}getCandles(e,t,s=300){return this.query(`SELECT * FROM candles WHERE symbol = '${e}' AND timeframe = '${t}'
       ORDER BY timestamp DESC LIMIT ${s}`).reverse()}getCandleCount(e,t){const s=this.getOne(`SELECT COUNT(*) as cnt FROM candles WHERE symbol = '${e}' AND timeframe = '${t}'`);return s?s.cnt:0}updateHolding(e,t,s,a="manual",r="crypto"){return this.run(`INSERT INTO portfolio (symbol, quantity, avg_buy_price, exchange, asset_type, updated_at)
       VALUES (?, ?, ?, ?, ?, datetime('now'))
       ON CONFLICT(symbol) DO UPDATE SET quantity = ?, avg_buy_price = ?, updated_at = datetime('now')`,[e,t,s,a,r,t,s])}getPortfolio(){return this.query("SELECT * FROM portfolio WHERE quantity > 0 ORDER BY symbol")}updatePrice(e,t){return this.run("UPDATE portfolio SET current_price = ?, updated_at = datetime('now') WHERE symbol = ?",[t,e])}getPortfolioValue(){return this.getOne(`
      SELECT 
        SUM(quantity * current_price) as total_value,
        SUM(quantity * avg_buy_price) as total_invested,
        SUM(quantity * (current_price - avg_buy_price)) as total_pnl,
        COUNT(*) as holdings_count
      FROM portfolio WHERE quantity > 0
    `)}addChatMessage(e,t,s=null,a=null,r=0,E=0){return this.run(`INSERT INTO chat_history (role, content, context, model, tokens_used, response_time_ms)
       VALUES (?, ?, ?, ?, ?, ?)`,[e,t,s,a,r,E])}getChatHistory(e=50){return this.query(`SELECT * FROM chat_history ORDER BY created_at DESC LIMIT ${e}`).reverse()}remember(e,t,s="general"){return this.run(`INSERT INTO jarvis_memory (key, value, category, updated_at)
       VALUES (?, ?, ?, datetime('now'))
       ON CONFLICT(key) DO UPDATE SET value = ?, access_count = access_count + 1, updated_at = datetime('now')`,[e,t,s,t])}recall(e){const t=this.getOne(`SELECT value FROM jarvis_memory WHERE key = '${e}'`);return t&&this.run(`UPDATE jarvis_memory SET access_count = access_count + 1 WHERE key = '${e}'`),t?t.value:null}recallAll(e=null){let t="SELECT * FROM jarvis_memory";return e&&(t+=` WHERE category = '${e}'`),t+=" ORDER BY access_count DESC",this.query(t)}addSignal(e){return this.run(`INSERT INTO signals (symbol, signal_type, direction, confidence, entry_price, target_price, stop_loss, indicators)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,[e.symbol,e.type,e.direction,e.confidence,e.entry,e.target,e.stopLoss,JSON.stringify(e.indicators||[])])}getActiveSignals(){return this.query("SELECT * FROM signals WHERE status = 'active' ORDER BY created_at DESC")}setSetting(e,t){return this.run(`INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
       ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now')`,[e,typeof t=="object"?JSON.stringify(t):String(t),typeof t=="object"?JSON.stringify(t):String(t)])}getSetting(e,t=null){const s=this.getOne(`SELECT value FROM settings WHERE key = '${e}'`);return s?s.value:t}queueSync(e,t){return this.run("INSERT INTO sync_queue (action, payload) VALUES (?, ?)",[e,JSON.stringify(t)])}getPendingSyncs(){return this.query("SELECT * FROM sync_queue WHERE status = 'pending' ORDER BY created_at")}markSynced(e){return this.run("UPDATE sync_queue SET status = 'synced', synced_at = datetime('now') WHERE id = ?",[e])}log(e,t,s,a=null){return this.run("INSERT INTO system_logs (level, module, message, data) VALUES (?, ?, ?, ?)",[e,t,s,a?JSON.stringify(a):null])}getLogs(e=null,t=100){let s="SELECT * FROM system_logs";return e&&(s+=` WHERE level = '${e}'`),s+=` ORDER BY created_at DESC LIMIT ${t}`,this.query(s)}getStats(){const e=["trades","candles","portfolio","alerts","chat_history","jarvis_memory","signals","watchlists","sync_queue","pnl_journal","tax_records","system_logs"],t={};e.forEach(a=>{const r=this.getOne(`SELECT COUNT(*) as cnt FROM ${a}`);t[a]=r?r.cnt:0});const s=this.db?this.db.export():new Uint8Array(0);return t.dbSizeBytes=s.length,t.dbSizeKB=(s.length/1024).toFixed(1),t.dbSizeMB=(s.length/1048576).toFixed(2),t}exportJSON(){const e=["trades","portfolio","alerts","chat_history","jarvis_memory","signals","watchlists","settings","pnl_journal","tax_records"],t={};return e.forEach(s=>{t[s]=this.query(`SELECT * FROM ${s}`)}),t.exported_at=new Date().toISOString(),t.version="6.0",t}exportCSV(e){const t=this.query(`SELECT * FROM ${e}`);if(!t.length)return"";const s=Object.keys(t[0]),a=[s.join(",")];return t.forEach(r=>{a.push(s.map(E=>`"${String(r[E]||"").replace(/"/g,'""')}"`).join(","))}),a.join(`
`)}async importJSON(e){const t=typeof e=="string"?JSON.parse(e):e;let s=0;for(const[a,r]of Object.entries(t)){if(!Array.isArray(r)||!r.length)continue;const E=Object.keys(r[0]),o=E.map(()=>"?").join(",");r.forEach(l=>{this.run(`INSERT OR IGNORE INTO ${a} (${E.join(",")}) VALUES (${o})`,E.map(N=>l[N])),s++})}return await this.save(),s}destroy(){this.autoSaveTimer&&clearInterval(this.autoSaveTimer),this.db&&(this._autoSave(),this.db.close()),this.ready=!1}}const p=new I;export{I as JarvisDB,p as default};
