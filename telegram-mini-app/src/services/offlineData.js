/**
 * Static fallback data for offline/first-launch scenarios.
 * Shown when API is unreachable and no cached data exists.
 * Format matches exact backend response shapes.
 */

export const FALLBACK_DASHBOARD = {
  portfolio: { balance_inr: 0, pnl_inr: 0, total_value: 0 },
  signals: [
    { signal: 'BUY', type: 'AI_SIGNAL', symbol: 'BTC', confidence: 82, entry: 67500, target: 72000, stop_loss: 65000, reason: 'Bullish divergence on 4H RSI' },
    { signal: 'HOLD', type: 'AI_SIGNAL', symbol: 'ETH', confidence: 65, entry: 3450, target: 3800, stop_loss: 3200, reason: 'Consolidation near support' },
    { signal: 'BUY', type: 'AI_SIGNAL', symbol: 'SOL', confidence: 78, entry: 145, target: 165, stop_loss: 135, reason: 'Volume spike + MACD crossover' },
  ],
  top_movers: {
    gainers: [
      { symbol: 'SOL', change_24h: 8.5, price_usd: 148 },
      { symbol: 'AVAX', change_24h: 6.2, price_usd: 35 },
      { symbol: 'MATIC', change_24h: 4.8, price_usd: 0.72 },
    ],
    losers: [
      { symbol: 'DOGE', change_24h: -3.2, price_usd: 0.12 },
      { symbol: 'SHIB', change_24h: -2.8, price_usd: 0.000018 },
    ]
  },
  regime: { regime: 'NEUTRAL', rec: 'Wait for confirmation', vix: 15.2, fear_greed: 50 },
  market_ticker: [
    { symbol: 'BTC', price_usd: 67500, change_24h: 2.1, market_cap: 1320000000000 },
    { symbol: 'ETH', price_usd: 3450, change_24h: 1.5, market_cap: 415000000000 },
    { symbol: 'SOL', price_usd: 148, change_24h: 8.5, market_cap: 65000000000 },
    { symbol: 'BNB', price_usd: 580, change_24h: 0.8, market_cap: 89000000000 },
    { symbol: 'XRP', price_usd: 0.52, change_24h: -0.3, market_cap: 28000000000 },
    { symbol: 'DOGE', price_usd: 0.12, change_24h: -3.2, market_cap: 17000000000 },
    { symbol: 'ADA', price_usd: 0.45, change_24h: 1.2, market_cap: 16000000000 },
    { symbol: 'AVAX', price_usd: 35, change_24h: 6.2, market_cap: 13000000000 },
  ],
  fear_greed: { score: 50, value: 'Neutral' },
  sentiment: { score: 55, data: { score: 55 } },
  dex_trending: [],
  pumpfun: [],
  vix: { value: 15.2 },
  indices: [
    { name: 'NIFTY 50', value: 22500, change: 0.4 },
    { name: 'SENSEX', value: 74200, change: 0.35 },
    { name: 'BANK NIFTY', value: 48500, change: 0.6 },
  ],
  news: []
}

export const FALLBACK_NEWS = [
  { title: 'Bitcoin crosses $67,000 as institutional demand surges', source: 'CoinDesk', time: '2h ago', url: '#', sentiment: 'bullish' },
  { title: 'Ethereum Layer-2 TVL hits new all-time high', source: 'CoinTelegraph', time: '4h ago', url: '#', sentiment: 'bullish' },
  { title: 'India crypto regulations: What traders need to know', source: 'Economic Times', time: '6h ago', url: '#', sentiment: 'neutral' },
  { title: 'Solana DeFi ecosystem grows 40% in Q1', source: 'Decrypt', time: '8h ago', url: '#', sentiment: 'bullish' },
  { title: 'RBI considers CBDC expansion to retail payments', source: 'LiveMint', time: '10h ago', url: '#', sentiment: 'neutral' },
]

export const FALLBACK_SIGNALS = [
  { signal: 'BUY', type: 'AI_SIGNAL', symbol: 'BTC', confidence: 82, entry: 67500, target: 72000, stop_loss: 65000, reason: 'Bullish divergence + volume confirmation', timeframe: '4H' },
  { signal: 'BUY', type: 'BREAKOUT', symbol: 'SOL', confidence: 78, entry: 145, target: 165, stop_loss: 135, reason: 'Resistance breakout with volume', timeframe: '1H' },
  { signal: 'HOLD', type: 'TREND', symbol: 'ETH', confidence: 65, entry: 3450, target: 3800, stop_loss: 3200, reason: 'Consolidation phase', timeframe: '4H' },
  { signal: 'BUY', type: 'REVERSAL', symbol: 'AVAX', confidence: 71, entry: 34, target: 40, stop_loss: 31, reason: 'Double bottom pattern', timeframe: '1D' },
  { signal: 'SELL', type: 'OVERBOUGHT', symbol: 'DOGE', confidence: 68, entry: 0.12, target: 0.10, stop_loss: 0.13, reason: 'RSI >80, bearish divergence', timeframe: '4H' },
]

export const FALLBACK_MARKETS = [
  { symbol: 'BTC', name: 'Bitcoin', price_usd: 67500, change_24h: 2.1, volume_24h: 28000000000, market_cap: 1320000000000 },
  { symbol: 'ETH', name: 'Ethereum', price_usd: 3450, change_24h: 1.5, volume_24h: 15000000000, market_cap: 415000000000 },
  { symbol: 'SOL', name: 'Solana', price_usd: 148, change_24h: 8.5, volume_24h: 3500000000, market_cap: 65000000000 },
  { symbol: 'BNB', name: 'BNB', price_usd: 580, change_24h: 0.8, volume_24h: 1200000000, market_cap: 89000000000 },
  { symbol: 'XRP', name: 'Ripple', price_usd: 0.52, change_24h: -0.3, volume_24h: 1800000000, market_cap: 28000000000 },
  { symbol: 'ADA', name: 'Cardano', price_usd: 0.45, change_24h: 1.2, volume_24h: 450000000, market_cap: 16000000000 },
  { symbol: 'AVAX', name: 'Avalanche', price_usd: 35, change_24h: 6.2, volume_24h: 650000000, market_cap: 13000000000 },
  { symbol: 'DOGE', name: 'Dogecoin', price_usd: 0.12, change_24h: -3.2, volume_24h: 900000000, market_cap: 17000000000 },
  { symbol: 'MATIC', name: 'Polygon', price_usd: 0.72, change_24h: 4.8, volume_24h: 380000000, market_cap: 7000000000 },
  { symbol: 'LINK', name: 'Chainlink', price_usd: 14.5, change_24h: 3.1, volume_24h: 520000000, market_cap: 8500000000 },
]

export const FALLBACK_PREDICTIONS = [
  { symbol: 'BTC', prediction: 'BULLISH', confidence: 78, target: 72000, timeframe: '7D', reasoning: 'Strong institutional inflows + halving momentum' },
  { symbol: 'ETH', prediction: 'NEUTRAL', confidence: 62, target: 3600, timeframe: '7D', reasoning: 'Awaiting ETF decision catalyst' },
  { symbol: 'SOL', prediction: 'BULLISH', confidence: 75, target: 170, timeframe: '7D', reasoning: 'DeFi TVL growth + meme coin activity' },
  { symbol: 'NIFTY', prediction: 'BULLISH', confidence: 65, target: 23000, timeframe: '7D', reasoning: 'FII buying + positive earnings season' },
]

export const FALLBACK_SENTIMENT = {
  score: 55,
  label: 'Slightly Bullish',
  data: { score: 55 },
  sources: {
    twitter: { score: 58, label: 'Bullish' },
    reddit: { score: 52, label: 'Neutral' },
    news: { score: 55, label: 'Slightly Bullish' }
  }
}

// Check if we're in offline mode
export const isOffline = () => !navigator.onLine

// Label for offline data
export const OFFLINE_BANNER = {
  message: '📡 ऑफलाइन मोड — डेमो डेटा दिखा रहे हैं',
  messageEn: '📡 Offline Mode — Showing demo data'
}
