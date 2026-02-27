/**
 * 🎤 JARVIS SMART VOICE COMMANDS — Natural Language Navigation & Actions
 * ═══════════════════════════════════════════════════════════════════════
 * 
 * Like in Iron Man: "JARVIS, run a diagnostic" / "Deploy Mark VII"
 * Users can say things naturally and JARVIS understands:
 * 
 * Navigation:
 * - "JARVIS dashboard dikhao" → navigates to /
 * - "gems scan karo" → navigates to /gems
 * - "moonshot hunter kholo" → navigates to /moonshot
 * - "portfolio dikhao" → navigates to /portfolio
 * 
 * Actions:
 * - "market scan karo" → triggers background scan
 * - "Bitcoin ka price batao" → speaks BTC price
 * - "auto trader start karo" → navigates to auto-sniper
 * - "kya haal hai market ka" → speaks market summary
 * 
 * Works with Hindi, English, and Hinglish — exact match not needed
 */

// Command patterns: [regex patterns, action type, action data, JARVIS response]
const VOICE_COMMANDS = [
  // ═══ NAVIGATION ═══
  { patterns: [/dashboard|home|ghar|main page|shuru/i], action: 'navigate', path: '/', response: 'Dashboard khol rahi hoon Sir.' },
  { patterns: [/chat|baat|talk|sunao|bolo/i], action: 'navigate', path: '/chat', response: 'Chat mode active Sir. Bataiye kya poochna hai.' },
  { patterns: [/moonshot|moon shot|100x|1000x|gem hunt/i], action: 'navigate', path: '/moonshot', response: 'MoonShot Hunter khol rahi hoon Sir. 100x gems dhundhte hain!' },
  { patterns: [/sniper|auto snipe|auto trade start/i], action: 'navigate', path: '/auto-sniper', response: 'AI Auto Sniper ready Sir. Automatic trading shuru karein?' },
  { patterns: [/trad(e|ing)|khareed|bech|buy|sell/i], action: 'navigate', path: '/trading', response: 'Trading page khol rahi hoon Sir.' },
  { patterns: [/wallet|balance|paisa|pais(e|a) (dikhao|batao)/i], action: 'navigate', path: '/wallet', response: 'Wallet open kar rahi hoon Sir.' },
  { patterns: [/gem|hidden gem|gem scan/i], action: 'navigate', path: '/gems', response: 'Gem Scanner active Sir. Hidden gems dhundh rahi hoon.' },
  { patterns: [/portfolio|invest|holding/i], action: 'navigate', path: '/portfolio', response: 'Portfolio Analytics khol rahi hoon Sir. Aapke investments ka analysis.' },
  { patterns: [/indian stock|nifty|sensex|bharat|india market/i], action: 'navigate', path: '/indian-stocks', response: 'Indian Stocks dashboard Sir. NIFTY ka haal dekhte hain.' },
  { patterns: [/option(s)?|nifty option|put|call/i], action: 'navigate', path: '/nifty-options', response: 'Options Live data Sir. Chain analysis ready.' },
  { patterns: [/whale|bada trader|big player/i], action: 'navigate', path: '/whales', response: 'Whale Alerts khol rahi hoon Sir. Bade players ka movement dekhte hain.' },
  { patterns: [/web3|defi|dex scan/i], action: 'navigate', path: '/web3-scanner', response: 'Web3 Scanner active Sir. DeFi tokens scan ho rahe hain.' },
  { patterns: [/crypto top|top (100|1000)|ranking/i], action: 'navigate', path: '/crypto-top1000', response: 'Top Crypto rankings load kar rahi hoon Sir.' },
  { patterns: [/candle|chart pattern|pattern analysis/i], action: 'navigate', path: '/candle-brain', response: 'AI Candle Brain Sir. Chart patterns ka analysis chalu.' },
  { patterns: [/backtest|past test|strategy test/i], action: 'navigate', path: '/backtest', response: 'Backtesting module Sir. Strategy test karte hain.' },
  { patterns: [/setting|setup|config/i], action: 'navigate', path: '/settings', response: 'Settings page Sir.' },
  { patterns: [/watchlist|watch list|track/i], action: 'navigate', path: '/watchlist', response: 'Aapki Watchlist Sir.' },
  { patterns: [/alert|notification|notify/i], action: 'navigate', path: '/smart-alerts', response: 'Smart Alerts Sir. Custom alerts set karte hain.' },
  { patterns: [/paper trad|practice|safe mode/i], action: 'navigate', path: '/paper-trading', response: 'Paper Trading Sir. Safe practice mode.' },
  { patterns: [/copy trad|follow trader/i], action: 'navigate', path: '/copy-trading', response: 'Copy Trading Sir. Top traders follow karte hain.' },
  { patterns: [/voice|awaaz|sun/i], action: 'navigate', path: '/voice', response: 'Voice mode active Sir. Main sun rahi hoon.' },
  { patterns: [/mega trad|power trad/i], action: 'navigate', path: '/mega-trader', response: 'MEGA Trader Sir! Maximum power trading mode.' },
  { patterns: [/pnl|profit loss|journal/i], action: 'navigate', path: '/pnl-journal', response: 'P&L Journal Sir. Trading history dekhte hain.' },
  { patterns: [/tax|income tax|crypto tax/i], action: 'navigate', path: '/tax-calculator', response: 'Tax Calculator Sir. Tax calculate karte hain.' },
  { patterns: [/vault|password|secure/i], action: 'navigate', path: '/vault', response: 'Secure Vault Sir. Data safe hai.' },

  // ═══ ACTIONS ═══
  { patterns: [/scan (karo|now|shuru)|market scan|check karo/i], action: 'scan', response: 'Emergency scan shuru kar rahi hoon Sir!' },
  { patterns: [/bitcoin (ka )?(price|rate|value)|btc (price|kitna)/i], action: 'btc-price', response: null }, // Dynamic response
  { patterns: [/market (ka )?(haal|status|kya hai|kaisa)/i], action: 'market-status', response: null },
  { patterns: [/good night|soja|neend|sleep/i], action: 'sleep', response: 'Good night Sir! Main watch karti rahungi.' },
  { patterns: [/wake up|utho|jaago/i], action: 'wakeup', response: 'Main jaag gayi Sir! Bataiye kya karna hai.' },
  { patterns: [/help|madad|kya kar sakti|features/i], action: 'help', response: 'Sir, main bahut kuch kar sakti hoon! Gems scan, auto trade, market analysis, whale tracking, portfolio management, aur bahut kuch. Bas bolo kya chahiye!' },
  { patterns: [/kaun ho|who are you|apna parichay|introduce/i], action: 'intro', response: 'Sir, main JARVIS hoon. Just A Rather Very Intelligent System. Tony Stark ne banaya tha, lekin ab main aapki hoon. Aapke trading mein, aapka AI guardian.' },
  { patterns: [/thank|shukriya|dhanyavaad/i], action: 'thanks', response: 'Sir, ye toh mera kaam hai. Iron Man ka JARVIS kabhi thank you nahi leta. Aur kuch karna hai?' },
]

/**
 * Process a voice transcript and execute the matching command
 * @param {string} transcript - Raw voice text
 * @returns {{ matched: boolean, action: string, response: string }}
 */
async function processVoiceCommand(transcript) {
  if (!transcript) return { matched: false }

  const text = transcript.toLowerCase().trim()
  console.log('[JARVIS Commands] Processing:', text)

  // Find matching command
  for (const cmd of VOICE_COMMANDS) {
    for (const pattern of cmd.patterns) {
      if (pattern.test(text)) {
        console.log('[JARVIS Commands] Matched:', cmd.action, cmd.path || '')

        // Execute action
        switch (cmd.action) {
          case 'navigate':
            window.dispatchEvent(new CustomEvent('jarvis-navigate', { detail: { path: cmd.path } }))
            if (cmd.response) {
              window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: cmd.response, priority: 'high' } }))
            }
            return { matched: true, action: 'navigate', path: cmd.path, response: cmd.response }

          case 'scan':
            try {
              const brain = await import('./jarvisProactiveBrain.js')
              const b = brain.default || brain
              if (b?.scanNow) b.scanNow()
            } catch {
              window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: cmd.response, priority: 'high' } }))
            }
            return { matched: true, action: 'scan', response: cmd.response }

          case 'btc-price':
            try {
              const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,inr&include_24hr_change=true')
              const data = await res.json()
              const usd = data?.bitcoin?.usd || 0
              const inr = data?.bitcoin?.inr || 0
              const change = data?.bitcoin?.usd_24h_change || 0
              const response = `Sir, Bitcoin ka price abhi ${usd.toLocaleString()} dollars hai, yaani ${inr.toLocaleString()} rupaye. 24 ghante mein ${change >= 0 ? change.toFixed(1) + ' percent upar' : Math.abs(change).toFixed(1) + ' percent neeche'} hai.`
              window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: response, priority: 'high' } }))
              return { matched: true, action: 'btc-price', response }
            } catch {
              window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: 'Sir, Bitcoin price fetch nahi ho pa raha. Network check kariye.', priority: 'high' } }))
              return { matched: true, action: 'btc-price' }
            }

          case 'market-status':
            try {
              const res = await fetch('https://api.coingecko.com/api/v3/global')
              const data = await res.json()
              const mcap = data?.data?.total_market_cap?.usd || 0
              const change = data?.data?.market_cap_change_percentage_24h_usd || 0
              const btcDom = data?.data?.market_cap_percentage?.btc || 0
              const response = `Sir, global crypto market cap ${(mcap / 1e12).toFixed(2)} trillion dollars hai. 24 ghante mein ${change >= 0 ? change.toFixed(1) + ' percent upar' : Math.abs(change).toFixed(1) + ' percent neeche'}. Bitcoin dominance ${btcDom.toFixed(1)} percent hai.`
              window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: response, priority: 'high' } }))
              return { matched: true, action: 'market-status', response }
            } catch {
              window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: 'Sir, market data abhi available nahi hai. Thodi der mein try karte hain.', priority: 'high' } }))
              return { matched: true, action: 'market-status' }
            }

          case 'sleep':
          case 'wakeup':
          case 'help':
          case 'intro':
          case 'thanks':
            window.dispatchEvent(new CustomEvent('jarvis-speak', { detail: { text: cmd.response, priority: 'high' } }))
            return { matched: true, action: cmd.action, response: cmd.response }

          default:
            return { matched: true, action: cmd.action }
        }
      }
    }
  }

  return { matched: false }
}

/**
 * Get list of available commands for help display
 */
function getCommandList() {
  return VOICE_COMMANDS.map(cmd => ({
    action: cmd.action,
    path: cmd.path,
    examples: cmd.patterns.map(p => p.source.replace(/\\/g, '').replace(/\(/g, '').replace(/\)/g, '').replace(/\|/g, ' / ')),
  }))
}

const jarvisSmartCommands = {
  processVoiceCommand,
  getCommandList,
  VOICE_COMMANDS,
}

export default jarvisSmartCommands
export { processVoiceCommand, getCommandList }
