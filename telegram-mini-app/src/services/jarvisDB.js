/**
 * 💾 JARVIS Embedded SQLite Database
 * ═══════════════════════════════════
 * 
 * Full SQL database INSIDE the app using sql.js (WASM).
 * No server needed. Unlimited storage. Survives app restarts.
 * Stores: trades, candles, portfolio, alerts, chat history, settings.
 * 
 * Auto-persists to IndexedDB for durability.
 */

let SQL = null
let db = null
let initialized = false
const DB_NAME = 'jarvis_main_db'
const DB_STORE = 'jarvis_sql_store'

async function loadSqlJs() {
  if (SQL) return SQL
  try {
    const initSqlJs = (await import('sql.js')).default
    SQL = await initSqlJs({
      locateFile: file => `https://sql.js.org/dist/${file}`
    })
    return SQL
  } catch (e) {
    // Fallback CDN
    const initSqlJs = (await import('sql.js')).default
    SQL = await initSqlJs()
    return SQL
  }
}

// ═══════════════════════════════════
// IndexedDB persistence layer
// ═══════════════════════════════════

function openIDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => {
      const idb = req.result
      if (!idb.objectStoreNames.contains(DB_STORE)) {
        idb.createObjectStore(DB_STORE)
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function saveToIDB(data) {
  const idb = await openIDB()
  return new Promise((resolve, reject) => {
    const tx = idb.transaction(DB_STORE, 'readwrite')
    tx.objectStore(DB_STORE).put(data, 'db')
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

async function loadFromIDB() {
  const idb = await openIDB()
  return new Promise((resolve, reject) => {
    const tx = idb.transaction(DB_STORE, 'readonly')
    const req = tx.objectStore(DB_STORE).get('db')
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

// ═══════════════════════════════════
// Database Schema
// ═══════════════════════════════════

const SCHEMA = `
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
`

// ═══════════════════════════════════
// JarvisDB Class
// ═══════════════════════════════════

class JarvisDB {
  constructor() {
    this.db = null
    this.ready = false
    this.autoSaveTimer = null
    this.changesSinceLastSave = 0
  }

  async init() {
    if (this.ready) return true
    try {
      await loadSqlJs()

      // Try to load existing DB from IndexedDB
      const savedData = await loadFromIDB().catch(() => null)
      if (savedData) {
        this.db = new SQL.Database(new Uint8Array(savedData))
        console.log('[JarvisDB] Loaded existing database from IndexedDB')
      } else {
        this.db = new SQL.Database()
        console.log('[JarvisDB] Created new database')
      }

      // Run schema migrations
      this.db.run(SCHEMA)

      // Start auto-save (every 30 seconds if changes)
      this.autoSaveTimer = setInterval(() => this._autoSave(), 30000)

      this.ready = true
      db = this.db
      initialized = true
      console.log('[JarvisDB] Database ready — 12 tables, indexed')
      return true
    } catch (e) {
      console.error('[JarvisDB] Init failed:', e)
      return false
    }
  }

  async _autoSave() {
    if (this.changesSinceLastSave === 0 || !this.db) return
    try {
      const data = this.db.export()
      await saveToIDB(data.buffer)
      this.changesSinceLastSave = 0
    } catch (e) {
      console.warn('[JarvisDB] Auto-save failed:', e.message)
    }
  }

  async save() {
    if (!this.db) return
    const data = this.db.export()
    await saveToIDB(data.buffer)
    this.changesSinceLastSave = 0
  }

  // ═══════════════════════════════════
  // Generic Query Methods
  // ═══════════════════════════════════

  run(sql, params = []) {
    if (!this.db) return null
    try {
      this.db.run(sql, params)
      this.changesSinceLastSave++
      return true
    } catch (e) {
      console.error('[JarvisDB] Query error:', e.message, sql)
      return false
    }
  }

  query(sql, params = []) {
    if (!this.db) return []
    try {
      const result = this.db.exec(sql, params)
      if (!result.length) return []
      const cols = result[0].columns
      return result[0].values.map(row => {
        const obj = {}
        cols.forEach((c, i) => { obj[c] = row[i] })
        return obj
      })
    } catch (e) {
      console.error('[JarvisDB] Query error:', e.message)
      return []
    }
  }

  getOne(sql, params = []) {
    const rows = this.query(sql, params)
    return rows[0] || null
  }

  // ═══════════════════════════════════
  // Trade Operations
  // ═══════════════════════════════════

  addTrade(trade) {
    return this.run(
      `INSERT INTO trades (symbol, side, price, quantity, total, fee, exchange, strategy, pnl, notes, tags, is_paper)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [trade.symbol, trade.side, trade.price, trade.quantity, trade.price * trade.quantity,
       trade.fee || 0, trade.exchange || 'manual', trade.strategy || '', trade.pnl || 0,
       trade.notes || '', trade.tags || '', trade.isPaper ? 1 : 0]
    )
  }

  getTrades(opts = {}) {
    let sql = 'SELECT * FROM trades WHERE 1=1'
    if (opts.symbol) sql += ` AND symbol = '${opts.symbol}'`
    if (opts.side) sql += ` AND side = '${opts.side}'`
    if (opts.isPaper !== undefined) sql += ` AND is_paper = ${opts.isPaper ? 1 : 0}`
    sql += ' ORDER BY created_at DESC'
    if (opts.limit) sql += ` LIMIT ${opts.limit}`
    return this.query(sql)
  }

  getTradeStats() {
    return this.getOne(`
      SELECT 
        COUNT(*) as total_trades,
        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
        SUM(pnl) as total_pnl,
        AVG(pnl) as avg_pnl,
        MAX(pnl) as best_trade,
        MIN(pnl) as worst_trade
      FROM trades WHERE is_paper = 0
    `)
  }

  // ═══════════════════════════════════
  // Candle Operations
  // ═══════════════════════════════════

  insertCandles(symbol, timeframe, candles) {
    const stmt = this.db.prepare(
      `INSERT OR REPLACE INTO candles (symbol, timeframe, open, high, low, close, volume, timestamp)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    )
    candles.forEach(c => {
      stmt.run([symbol, timeframe, c.open, c.high, c.low, c.close, c.volume || 0, c.timestamp])
    })
    stmt.free()
    this.changesSinceLastSave += candles.length
  }

  getCandles(symbol, timeframe, limit = 300) {
    return this.query(
      `SELECT * FROM candles WHERE symbol = '${symbol}' AND timeframe = '${timeframe}'
       ORDER BY timestamp DESC LIMIT ${limit}`
    ).reverse()
  }

  getCandleCount(symbol, timeframe) {
    const r = this.getOne(`SELECT COUNT(*) as cnt FROM candles WHERE symbol = '${symbol}' AND timeframe = '${timeframe}'`)
    return r ? r.cnt : 0
  }

  // ═══════════════════════════════════
  // Portfolio Operations
  // ═══════════════════════════════════

  updateHolding(symbol, quantity, avgPrice, exchange = 'manual', type = 'crypto') {
    return this.run(
      `INSERT INTO portfolio (symbol, quantity, avg_buy_price, exchange, asset_type, updated_at)
       VALUES (?, ?, ?, ?, ?, datetime('now'))
       ON CONFLICT(symbol) DO UPDATE SET quantity = ?, avg_buy_price = ?, updated_at = datetime('now')`,
      [symbol, quantity, avgPrice, exchange, type, quantity, avgPrice]
    )
  }

  getPortfolio() {
    return this.query('SELECT * FROM portfolio WHERE quantity > 0 ORDER BY symbol')
  }

  updatePrice(symbol, price) {
    return this.run(
      `UPDATE portfolio SET current_price = ?, updated_at = datetime('now') WHERE symbol = ?`,
      [price, symbol]
    )
  }

  getPortfolioValue() {
    return this.getOne(`
      SELECT 
        SUM(quantity * current_price) as total_value,
        SUM(quantity * avg_buy_price) as total_invested,
        SUM(quantity * (current_price - avg_buy_price)) as total_pnl,
        COUNT(*) as holdings_count
      FROM portfolio WHERE quantity > 0
    `)
  }

  // ═══════════════════════════════════
  // Chat History
  // ═══════════════════════════════════

  addChatMessage(role, content, context = null, model = null, tokens = 0, responseTime = 0) {
    return this.run(
      `INSERT INTO chat_history (role, content, context, model, tokens_used, response_time_ms)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [role, content, context, model, tokens, responseTime]
    )
  }

  getChatHistory(limit = 50) {
    return this.query(`SELECT * FROM chat_history ORDER BY created_at DESC LIMIT ${limit}`).reverse()
  }

  // ═══════════════════════════════════
  // JARVIS Memory
  // ═══════════════════════════════════

  remember(key, value, category = 'general') {
    return this.run(
      `INSERT INTO jarvis_memory (key, value, category, updated_at)
       VALUES (?, ?, ?, datetime('now'))
       ON CONFLICT(key) DO UPDATE SET value = ?, access_count = access_count + 1, updated_at = datetime('now')`,
      [key, value, category, value]
    )
  }

  recall(key) {
    const r = this.getOne(`SELECT value FROM jarvis_memory WHERE key = '${key}'`)
    if (r) this.run(`UPDATE jarvis_memory SET access_count = access_count + 1 WHERE key = '${key}'`)
    return r ? r.value : null
  }

  recallAll(category = null) {
    let sql = 'SELECT * FROM jarvis_memory'
    if (category) sql += ` WHERE category = '${category}'`
    sql += ' ORDER BY access_count DESC'
    return this.query(sql)
  }

  // ═══════════════════════════════════
  // Signals
  // ═══════════════════════════════════

  addSignal(signal) {
    return this.run(
      `INSERT INTO signals (symbol, signal_type, direction, confidence, entry_price, target_price, stop_loss, indicators)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [signal.symbol, signal.type, signal.direction, signal.confidence,
       signal.entry, signal.target, signal.stopLoss, JSON.stringify(signal.indicators || [])]
    )
  }

  getActiveSignals() {
    return this.query("SELECT * FROM signals WHERE status = 'active' ORDER BY created_at DESC")
  }

  // ═══════════════════════════════════
  // Settings
  // ═══════════════════════════════════

  setSetting(key, value) {
    return this.run(
      `INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
       ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now')`,
      [key, typeof value === 'object' ? JSON.stringify(value) : String(value), typeof value === 'object' ? JSON.stringify(value) : String(value)]
    )
  }

  getSetting(key, defaultValue = null) {
    const r = this.getOne(`SELECT value FROM settings WHERE key = '${key}'`)
    return r ? r.value : defaultValue
  }

  // ═══════════════════════════════════
  // Sync Queue (offline operations)
  // ═══════════════════════════════════

  queueSync(action, payload) {
    return this.run(
      `INSERT INTO sync_queue (action, payload) VALUES (?, ?)`,
      [action, JSON.stringify(payload)]
    )
  }

  getPendingSyncs() {
    return this.query("SELECT * FROM sync_queue WHERE status = 'pending' ORDER BY created_at")
  }

  markSynced(id) {
    return this.run(`UPDATE sync_queue SET status = 'synced', synced_at = datetime('now') WHERE id = ?`, [id])
  }

  // ═══════════════════════════════════
  // System Logs
  // ═══════════════════════════════════

  log(level, module, message, data = null) {
    return this.run(
      `INSERT INTO system_logs (level, module, message, data) VALUES (?, ?, ?, ?)`,
      [level, module, message, data ? JSON.stringify(data) : null]
    )
  }

  getLogs(level = null, limit = 100) {
    let sql = 'SELECT * FROM system_logs'
    if (level) sql += ` WHERE level = '${level}'`
    sql += ` ORDER BY created_at DESC LIMIT ${limit}`
    return this.query(sql)
  }

  // ═══════════════════════════════════
  // Database Stats
  // ═══════════════════════════════════

  getStats() {
    const tables = ['trades', 'candles', 'portfolio', 'alerts', 'chat_history',
                    'jarvis_memory', 'signals', 'watchlists', 'sync_queue', 'pnl_journal',
                    'tax_records', 'system_logs']
    const stats = {}
    tables.forEach(t => {
      const r = this.getOne(`SELECT COUNT(*) as cnt FROM ${t}`)
      stats[t] = r ? r.cnt : 0
    })

    // DB file size
    const data = this.db ? this.db.export() : new Uint8Array(0)
    stats.dbSizeBytes = data.length
    stats.dbSizeKB = (data.length / 1024).toFixed(1)
    stats.dbSizeMB = (data.length / 1048576).toFixed(2)

    return stats
  }

  // ═══════════════════════════════════
  // Export / Import
  // ═══════════════════════════════════

  exportJSON() {
    const tables = ['trades', 'portfolio', 'alerts', 'chat_history', 'jarvis_memory',
                    'signals', 'watchlists', 'settings', 'pnl_journal', 'tax_records']
    const data = {}
    tables.forEach(t => {
      data[t] = this.query(`SELECT * FROM ${t}`)
    })
    data.exported_at = new Date().toISOString()
    data.version = '6.0'
    return data
  }

  exportCSV(table) {
    const rows = this.query(`SELECT * FROM ${table}`)
    if (!rows.length) return ''
    const headers = Object.keys(rows[0])
    const csv = [headers.join(',')]
    rows.forEach(r => {
      csv.push(headers.map(h => `"${String(r[h] || '').replace(/"/g, '""')}"`).join(','))
    })
    return csv.join('\n')
  }

  async importJSON(jsonData) {
    const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData
    let imported = 0
    for (const [table, rows] of Object.entries(data)) {
      if (!Array.isArray(rows) || !rows.length) continue
      const cols = Object.keys(rows[0])
      const placeholders = cols.map(() => '?').join(',')
      rows.forEach(row => {
        this.run(
          `INSERT OR IGNORE INTO ${table} (${cols.join(',')}) VALUES (${placeholders})`,
          cols.map(c => row[c])
        )
        imported++
      })
    }
    await this.save()
    return imported
  }

  destroy() {
    if (this.autoSaveTimer) clearInterval(this.autoSaveTimer)
    if (this.db) {
      this._autoSave()
      this.db.close()
    }
    this.ready = false
  }
}

const jarvisDB = new JarvisDB()
export default jarvisDB
export { JarvisDB }
