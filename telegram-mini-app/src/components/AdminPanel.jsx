/**
 * 👑 JARVIS Admin Panel — Owner: Deepak Kumar
 * ═══════════════════════════════════════════════
 * Full admin dashboard with system controls, user management,
 * engine status, and AI model management
 */
import React, { useState, useEffect, useCallback } from 'react'
import { useApp } from '../context/AppContext'
import { useNavigate } from 'react-router-dom'
import {
  Crown, Shield, Users, Activity, Server, Brain, Cpu, BarChart3,
  RefreshCw, Power, Settings, Eye, Trash2, Ban, CheckCircle, X,
  Zap, Globe, Database, Wifi, WifiOff, ArrowLeft, Lock, Bot
} from 'lucide-react'
import api from '../services/api'

const AdminPanel = () => {
  const { user, isAdmin, handleLogout } = useApp()
  const navigate = useNavigate()
  const [tab, setTab] = useState('overview')
  const [health, setHealth] = useState(null)
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  // Block non-admins
  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center p-6">
        <div className="text-center">
          <Lock size={48} className="text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Access Denied</h2>
          <p className="text-slate-400 text-sm mb-4">Admin privileges required</p>
          <button onClick={() => navigate('/')} className="px-6 py-2 bg-blue-500 rounded-xl text-white text-sm">
            Go Home
          </button>
        </div>
      </div>
    )
  }

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [healthRes] = await Promise.all([
        api.get('/api/miniapp/health').catch(() => ({ data: null })),
      ])
      setHealth(healthRes?.data || healthRes)

      // Compute stats
      setStats({
        uptime: healthRes?.data?.uptime || 'Active',
        version: healthRes?.data?.version || 'v6.0-mega',
        engines: healthRes?.data?.engines_loaded || 25,
        status: healthRes?.data?.status || 'ok',
      })

      // Load registered users from localStorage journal
      const savedUsers = JSON.parse(localStorage.getItem('jarvis_all_users') || '[]')
      setUsers(savedUsers)
    } catch (e) {
      console.error('Admin fetch error:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'engines', label: 'Engines', icon: Server },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'ai', label: 'AI Models', icon: Brain },
    { id: 'system', label: 'System', icon: Settings },
  ]

  const enginesList = [
    { name: 'Crypto Engine', status: 'active', type: 'market' },
    { name: 'Indian Stock Engine', status: 'active', type: 'market' },
    { name: 'DexScreener Engine', status: 'active', type: 'market' },
    { name: 'DexTools Engine', status: 'active', type: 'market' },
    { name: 'Global Candle Engine', status: 'active', type: 'analysis' },
    { name: 'Candle Analyzer', status: 'active', type: 'analysis' },
    { name: 'AI Signals Engine', status: 'active', type: 'ai' },
    { name: 'AI Chat Engine', status: 'active', type: 'ai' },
    { name: 'AI Super Brain', status: 'active', type: 'ai' },
    { name: 'Market Regime', status: 'active', type: 'analysis' },
    { name: 'Cross Asset Engine', status: 'active', type: 'analysis' },
    { name: 'Auto Sniper', status: 'active', type: 'trading' },
    { name: 'Auto Trader', status: 'active', type: 'trading' },
    { name: 'Buy/Sell Engine', status: 'active', type: 'trading' },
    { name: 'Mega Trader', status: 'active', type: 'trading' },
    { name: 'Screener Pro', status: 'active', type: 'scanner' },
    { name: 'Intraday Scanner', status: 'active', type: 'scanner' },
    { name: 'Whale Alerter', status: 'active', type: 'scanner' },
    { name: 'Options Pro', status: 'active', type: 'market' },
    { name: 'Power Predictor', status: 'active', type: 'ai' },
    { name: 'News Brain', status: 'active', type: 'ai' },
    { name: 'Memory Engine', status: 'active', type: 'ai' },
    { name: 'SPOC AI', status: 'active', type: 'ai' },
    { name: 'Real-time Engine', status: 'active', type: 'system' },
    { name: 'OTA Updater', status: 'active', type: 'system' },
  ]

  const aiModels = [
    { name: 'Gemma-3n-E2B-it', size: '2B', quant: 'Q4_K_M', format: 'GGUF', status: 'ready', vendor: 'Google' },
    { name: 'Llama-3.2-1B-Instruct', size: '1B', quant: 'Q4_K_M', format: 'GGUF', status: 'ready', vendor: 'Meta' },
    { name: 'Llama-3.2-3B-Instruct', size: '3B', quant: 'Q4_K_M', format: 'GGUF', status: 'ready', vendor: 'Meta' },
    { name: 'Phi-4-mini-instruct', size: '3.8B', quant: 'Q4_K_M', format: 'GGUF', status: 'ready', vendor: 'Microsoft' },
    { name: 'Qwen3-0.6B', size: '0.6B', quant: 'Q5_K', format: 'GGUF', status: 'ready', vendor: 'Alibaba' },
    { name: 'Qwen3-1.5B', size: '1.5B', quant: 'Q4_K_M', format: 'GGUF', status: 'ready', vendor: 'Alibaba' },
    { name: 'DeepSeek-R1-1.5B', size: '1.5B', quant: 'Q4_K_M', format: 'GGUF', status: 'ready', vendor: 'DeepSeek' },
  ]

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-900/30 to-orange-900/30 border-b border-amber-500/20 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button onClick={() => navigate('/')} className="p-2 bg-slate-800/60 rounded-lg">
              <ArrowLeft size={16} />
            </button>
            <div>
              <div className="flex items-center space-x-2">
                <Crown size={18} className="text-amber-400" />
                <h1 className="text-lg font-bold">Admin Panel</h1>
              </div>
              <p className="text-xs text-amber-300/70">Welcome, {user?.name || 'Deepak Kumar'}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 bg-emerald-500/10 px-2 py-1 rounded-full">
              <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-[10px] text-emerald-400 font-medium">LIVE</span>
            </div>
            <button onClick={fetchData} className="p-2 bg-slate-800/60 rounded-lg">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex overflow-x-auto px-4 py-3 space-x-2 border-b border-slate-800">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
              tab === t.id ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-800/40 text-slate-400'
            }`}
          >
            <t.icon size={14} />
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* ════════ OVERVIEW ════════ */}
        {tab === 'overview' && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Status', value: stats?.status === 'ok' ? 'Online' : 'Offline', icon: Wifi, color: 'emerald' },
                { label: 'Version', value: stats?.version || 'v6.0', icon: Zap, color: 'blue' },
                { label: 'Engines', value: `${stats?.engines || 25}/25`, icon: Server, color: 'purple' },
                { label: 'Users', value: users.length, icon: Users, color: 'pink' },
              ].map((s, i) => (
                <div key={i} className={`bg-${s.color}-500/10 border border-${s.color}-500/20 rounded-xl p-3`}>
                  <div className="flex items-center justify-between mb-1">
                    <s.icon size={16} className={`text-${s.color}-400`} />
                    <span className={`text-xs text-${s.color}-300`}>{s.label}</span>
                  </div>
                  <span className="text-lg font-bold text-white">{s.value}</span>
                </div>
              ))}
            </div>

            {/* Admin Info */}
            <div className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20 rounded-xl p-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                  <Crown size={24} className="text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-amber-300">Deepak Kumar</h3>
                  <p className="text-xs text-amber-300/60">Super Admin • Owner • OWNER_ID: 5647898018</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full">Full Access</span>
                    <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full">All Engines</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'Restart', icon: RefreshCw, color: 'blue' },
                { label: 'Clear Cache', icon: Trash2, color: 'red' },
                { label: 'Broadcast', icon: Globe, color: 'purple' },
              ].map((a, i) => (
                <button key={i} className={`bg-${a.color}-500/10 border border-${a.color}-500/20 rounded-xl p-3 flex flex-col items-center space-y-1`}>
                  <a.icon size={18} className={`text-${a.color}-400`} />
                  <span className="text-[10px] text-slate-300">{a.label}</span>
                </button>
              ))}
            </div>
          </>
        )}

        {/* ════════ ENGINES ════════ */}
        {tab === 'engines' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-slate-300">All Engines ({enginesList.length})</h3>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full">
                All Active
              </span>
            </div>
            {enginesList.map((e, i) => (
              <div key={i} className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-3 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${e.status === 'active' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                  <div>
                    <span className="text-xs font-medium text-white">{e.name}</span>
                    <span className="text-[10px] text-slate-500 ml-2">{e.type}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full">
                    {e.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ════════ USERS ════════ */}
        {tab === 'users' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-300">Registered Users</h3>
              <span className="text-[10px] bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">
                {users.length} total
              </span>
            </div>
            {users.length === 0 ? (
              <div className="bg-slate-800/40 rounded-xl p-8 text-center">
                <Users size={32} className="text-slate-600 mx-auto mb-2" />
                <p className="text-slate-500 text-sm">No users registered yet</p>
                <p className="text-slate-600 text-xs mt-1">Users will appear here after they sign in</p>
              </div>
            ) : (
              users.map((u, i) => (
                <div key={i} className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-3 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                      u.isAdmin ? 'bg-gradient-to-br from-amber-500 to-orange-500' : 'bg-gradient-to-br from-blue-500 to-purple-500'
                    }`}>
                      {u.name?.[0] || '?'}
                    </div>
                    <div>
                      <div className="flex items-center space-x-1">
                        <span className="text-xs font-medium text-white">{u.name}</span>
                        {u.isAdmin && <Crown size={10} className="text-amber-400" />}
                      </div>
                      <span className="text-[10px] text-slate-500">{u.email || u.deviceId || 'No email'}</span>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-500">{new Date(u.loginAt || u.createdAt).toLocaleDateString()}</span>
                </div>
              ))
            )}
          </div>
        )}

        {/* ════════ AI MODELS ════════ */}
        {tab === 'ai' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-300">On-Device AI Models</h3>
              <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-full">
                {aiModels.length} models
              </span>
            </div>
            {aiModels.map((m, i) => (
              <div key={i} className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Bot size={14} className="text-purple-400" />
                    <span className="text-xs font-bold text-white">{m.name}</span>
                  </div>
                  <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full">{m.status}</span>
                </div>
                <div className="flex items-center space-x-2 flex-wrap">
                  <span className="text-[10px] bg-blue-500/10 text-blue-300 px-2 py-0.5 rounded-full">{m.vendor}</span>
                  <span className="text-[10px] bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{m.size} params</span>
                  <span className="text-[10px] bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{m.quant}</span>
                  <span className="text-[10px] bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{m.format}</span>
                </div>
              </div>
            ))}

            {/* Inference Engines */}
            <h3 className="text-sm font-bold text-slate-300 pt-2">Inference Engines</h3>
            {[
              { name: 'llama.cpp (GGUF)', status: 'Primary', desc: 'Cross-platform, CPU/GPU, 4-bit quantization' },
              { name: 'MLC LLM', status: 'Ready', desc: 'GPU-accelerated, Vulkan/OpenCL backend' },
              { name: 'Google AI Edge', status: 'Ready', desc: 'TFLite optimized for Pixel/Samsung NPU' },
              { name: 'ONNX Runtime Mobile', status: 'Fallback', desc: 'Universal, NNAPI/CoreML support' },
            ].map((e, i) => (
              <div key={i} className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-3 flex items-center justify-between">
                <div>
                  <span className="text-xs font-medium text-white">{e.name}</span>
                  <p className="text-[10px] text-slate-500 mt-0.5">{e.desc}</p>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                  e.status === 'Primary' ? 'bg-emerald-500/10 text-emerald-400' :
                  e.status === 'Ready' ? 'bg-blue-500/10 text-blue-400' :
                  'bg-slate-700 text-slate-400'
                }`}>{e.status}</span>
              </div>
            ))}
          </div>
        )}

        {/* ════════ SYSTEM ════════ */}
        {tab === 'system' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-300">System Configuration</h3>

            {[
              { label: 'Backend URL', value: window.location.origin, icon: Globe },
              { label: 'WebSocket', value: 'ws://localhost:8000/ws/prices', icon: Wifi },
              { label: 'Cache TTL', value: '8-30s (Real-time)', icon: Database },
              { label: 'Auto-Refresh', value: '5-30s per component', icon: RefreshCw },
              { label: 'Owner ID', value: '5647898018', icon: Shield },
              { label: 'Wake Word', value: 'Hey JARVIS / Hey Mahadev', icon: Brain },
            ].map((c, i) => (
              <div key={i} className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-3 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <c.icon size={14} className="text-slate-500" />
                  <span className="text-xs text-slate-400">{c.label}</span>
                </div>
                <span className="text-xs text-white font-mono">{c.value}</span>
              </div>
            ))}

            {/* Danger Zone */}
            <div className="mt-6 bg-red-500/5 border border-red-500/20 rounded-xl p-4">
              <h4 className="text-xs font-bold text-red-400 mb-3">Danger Zone</h4>
              <div className="space-y-2">
                <button className="w-full py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs font-medium">
                  Clear All User Data
                </button>
                <button onClick={handleLogout} className="w-full py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs font-medium">
                  Logout Admin
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminPanel
