import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Home, TrendingUp, Wallet, Bot, Zap, MoreHorizontal, X,
  Globe, Copy, Users, Activity, PieChart, Waves, FlaskConical,
  BarChart3, Settings, Search, Brain, Mic, Flame, Layers, LineChart, Gauge,
  Crosshair, Puzzle, ShieldCheck, ScanLine, Rocket
} from 'lucide-react'
import { useApp } from '../context/AppContext'

const Navigation = () => {
  const location = useLocation()
  const { hapticFeedback } = useApp()
  const [showMore, setShowMore] = useState(false)

  const mainNav = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/trading', icon: TrendingUp, label: 'Trade' },
    { path: '/chat', icon: Bot, label: 'AI Chat' },
    { path: '/wallet', icon: Wallet, label: 'Wallet' },
    { path: '/more', icon: MoreHorizontal, label: 'More', isMenu: true },
  ]

  const moreItems = [
    { path: '/phantom', icon: Globe, label: 'Phantom Wallet', color: 'from-purple-500 to-blue-500', desc: 'Solana wallet & auto-trade' },
    { path: '/mega-trader', icon: Rocket, label: '🤖 MEGA AI Trader', color: 'from-red-600 to-yellow-500', desc: 'NUCLEAR autonomous AI trader' },
    { path: '/auto-trader', icon: Zap, label: 'Auto Trader', color: 'from-amber-500 to-orange-500', desc: 'AI trading bot' },
    { path: '/copy-trading', icon: Copy, label: 'Copy Trading', color: 'from-blue-500 to-cyan-500', desc: 'Copy top traders' },
    { path: '/options', icon: Activity, label: 'Options Chain', color: 'from-orange-500 to-red-500', desc: 'Nifty/BankNifty options' },
    { path: '/indian-stocks', icon: Flame, label: 'Indian Stocks', color: 'from-orange-500 to-amber-500', desc: 'NSE/BSE super analysis' },
    { path: '/nifty-options', icon: Layers, label: 'Live Options', color: 'from-red-500 to-pink-500', desc: 'Real NSE option chain' },
    { path: '/candle-indicators', icon: LineChart, label: 'Candles & TA', color: 'from-cyan-500 to-blue-500', desc: '43 patterns + 50 indicators' },
    { path: '/power-predictor', icon: Gauge, label: 'AI Predictor', color: 'from-purple-600 to-pink-600', desc: '10-signal ML prediction' },
    { path: '/intraday-scanner', icon: ScanLine, label: 'Intraday Scan', color: 'from-yellow-500 to-amber-500', desc: 'Breakout + Volume + Momentum' },
    { path: '/options-pro', icon: Crosshair, label: 'Options Pro', color: 'from-red-500 to-orange-500', desc: 'Strike intel + F&O brain' },
    { path: '/strategy-builder', icon: Puzzle, label: 'Strategy Build', color: 'from-indigo-500 to-purple-500', desc: 'Straddle, Strangle, Condor' },
    { path: '/risk-manager', icon: ShieldCheck, label: 'Risk Manager', color: 'from-green-500 to-emerald-500', desc: 'Kelly + Position sizing' },
    { path: '/portfolio', icon: PieChart, label: 'Portfolio', color: 'from-violet-500 to-purple-500', desc: 'Cross-asset analytics' },
    { path: '/whales', icon: Waves, label: 'Whale Alerts', color: 'from-cyan-500 to-teal-500', desc: 'Track big money' },
    { path: '/backtest', icon: FlaskConical, label: 'Backtest', color: 'from-emerald-500 to-teal-500', desc: 'AI strategy tester' },
    { path: '/social', icon: Users, label: 'Social Feed', color: 'from-pink-500 to-rose-500', desc: 'Community trades' },
    { path: '/gems', icon: Search, label: 'Gem Scanner', color: 'from-emerald-500 to-green-500', desc: 'Find hidden gems' },
    { path: '/screener', icon: BarChart3, label: 'Screener', color: 'from-blue-500 to-indigo-500', desc: 'Market screener' },
    { path: '/intelligence', icon: Brain, label: 'Intelligence', color: 'from-purple-500 to-pink-500', desc: 'AI market intel' },
    { path: '/settings', icon: Settings, label: 'Settings', color: 'from-slate-500 to-slate-600', desc: 'Preferences' },
  ]

  const isMoreActive = moreItems.some(i => location.pathname === i.path)

  return (
    <>
      {/* More Menu Overlay */}
      {showMore && (
        <div className="fixed inset-0 z-50 flex flex-col justify-end">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowMore(false)} />
          <div className="relative bg-slate-900 border-t border-slate-700 rounded-t-3xl max-h-[70vh] overflow-y-auto animate-slide-up">
            <div className="sticky top-0 bg-slate-900 p-4 pb-2 flex items-center justify-between border-b border-slate-800 z-10">
              <h2 className="text-base font-bold text-white">All Features</h2>
              <button onClick={() => setShowMore(false)} className="p-1.5 bg-slate-800 rounded-full">
                <X size={16} className="text-slate-400" />
              </button>
            </div>
            <div className="p-3 grid grid-cols-3 gap-2 pb-safe">
              {moreItems.map(item => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link key={item.path} to={item.path}
                    onClick={() => { setShowMore(false); hapticFeedback('impact') }}
                    className={`flex flex-col items-center p-3 rounded-xl transition-all active:scale-95 ${
                      isActive ? 'bg-blue-500/10 ring-1 ring-blue-500/30' : 'bg-slate-800 hover:bg-slate-700'
                    }`}>
                    <div className={`w-10 h-10 bg-gradient-to-br ${item.color} rounded-xl flex items-center justify-center mb-1.5 shadow-lg`}>
                      <Icon size={18} className="text-white" />
                    </div>
                    <span className="text-[10px] font-medium text-white text-center leading-tight">{item.label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 glass z-40 border-t border-slate-700/50"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
        <div className="flex justify-around items-center px-2 py-1.5">
          {mainNav.map((item) => {
            const Icon = item.icon
            const isActive = item.isMenu ? isMoreActive :
              item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path)

            return (
              <button key={item.path}
                onClick={() => {
                  hapticFeedback('impact')
                  if (item.isMenu) setShowMore(!showMore)
                }}
                {...(!item.isMenu ? {} : {})}
                className={`flex flex-col items-center py-1.5 px-3 rounded-xl transition-all duration-200 ${
                  (item.isMenu && showMore) ? 'text-blue-400 bg-blue-500/10' :
                  isActive ? 'text-blue-400 bg-blue-500/10' : 'text-slate-500 hover:text-slate-300'
                }`}>
                {item.isMenu ? (
                  <>
                    <Icon size={20} strokeWidth={showMore ? 2.5 : 1.5} />
                    <span className="text-[10px] mt-0.5 font-medium">{item.label}</span>
                    {isMoreActive && !showMore && <div className="w-1 h-1 bg-blue-400 rounded-full mt-0.5" />}
                  </>
                ) : (
                  <Link to={item.path} className="flex flex-col items-center">
                    <Icon size={20} strokeWidth={isActive ? 2.5 : 1.5} />
                    <span className="text-[10px] mt-0.5 font-medium">{item.label}</span>
                    {isActive && <div className="w-1 h-1 bg-blue-400 rounded-full mt-0.5" />}
                  </Link>
                )}
              </button>
            )
          })}
        </div>
      </nav>
    </>
  )
}

export default Navigation
