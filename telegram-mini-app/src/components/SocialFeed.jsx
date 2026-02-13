import React, { useState, useEffect } from 'react'
import {
  MessageCircle, Heart, TrendingUp, TrendingDown, Users, Send,
  ThumbsUp, BarChart3, RefreshCw, Filter, Clock
} from 'lucide-react'
import { fetchSocialFeed } from '../services/api'
import { useApp } from '../context/AppContext'

const SocialFeed = () => {
  const { user, addNotification, hapticFeedback } = useApp()
  const userId = String(user?.id || '')
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [liked, setLiked] = useState({})

  const load = async () => {
    setLoading(true)
    try {
      const res = await fetchSocialFeed(userId)
      setPosts(res?.data?.data || res?.data?.feed || [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleLike = (i) => {
    hapticFeedback('impact')
    setLiked(p => ({ ...p, [i]: !p[i] }))
  }

  const filteredPosts = filter === 'all' ? posts :
    posts.filter(p => (p.type || '').toLowerCase().includes(filter))

  const filters = [
    { key: 'all', label: '🔥 All' },
    { key: 'trade', label: '📈 Trades' },
    { key: 'signal', label: '⚡ Signals' },
    { key: 'news', label: '📰 News' },
  ]

  if (loading) return (
    <div className="p-4 bg-slate-900 min-h-screen space-y-4">
      {[1,2,3,4].map(i => <div key={i} className="skeleton h-32 rounded-2xl" />)}
    </div>
  )

  return (
    <div className="p-4 pb-24 bg-slate-900 min-h-screen text-white">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center space-x-2">
            <div className="w-7 h-7 bg-gradient-to-br from-pink-500 to-rose-500 rounded-lg flex items-center justify-center">
              <Users size={16} />
            </div>
            <span>Social Feed</span>
          </h1>
          <p className="text-slate-400 text-sm">Community trades & signals</p>
        </div>
        <button onClick={load} className="p-2 bg-slate-800 rounded-full">
          <RefreshCw size={18} className="text-pink-400" />
        </button>
      </div>

      {/* Filters */}
      <div className="flex space-x-2 mb-4 overflow-x-auto pb-1">
        {filters.map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)}
            className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              filter === f.key ? 'bg-pink-600 text-white' : 'bg-slate-800 text-slate-400'
            }`}>{f.label}</button>
        ))}
      </div>

      {/* Posts */}
      <div className="space-y-3">
        {filteredPosts.length === 0 ? (
          <div className="text-center py-12">
            <MessageCircle size={40} className="mx-auto text-slate-600 mb-2" />
            <p className="text-slate-500">No posts yet</p>
            <p className="text-xs text-slate-600">Community activity will appear here</p>
          </div>
        ) : filteredPosts.map((post, i) => {
          const isBullish = (post.sentiment || post.side || '').toLowerCase().includes('bull') || 
                           (post.sentiment || post.side || '').toLowerCase().includes('buy')
          return (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
              {/* Header */}
              <div className="p-3 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-pink-500 to-purple-500 rounded-full flex items-center justify-center text-xs font-bold">
                    {(post.user || post.trader || 'U')[0].toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{post.user || post.trader || 'Anonymous'}</p>
                    <div className="flex items-center space-x-1 text-[10px] text-slate-500">
                      <Clock size={8} />
                      <span>{post.time || post.timestamp || 'Just now'}</span>
                    </div>
                  </div>
                </div>
                {post.type && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                    post.type === 'trade' ? 'bg-blue-500/20 text-blue-400' :
                    post.type === 'signal' ? 'bg-purple-500/20 text-purple-400' :
                    'bg-slate-700 text-slate-400'
                  }`}>{post.type}</span>
                )}
              </div>

              {/* Content */}
              <div className="px-3 pb-2">
                <p className="text-sm leading-relaxed">{post.content || post.message || post.text || ''}</p>
              </div>

              {/* Trade Card (if applicable) */}
              {(post.symbol || post.pair) && (
                <div className={`mx-3 mb-2 p-2.5 rounded-lg border ${
                  isBullish ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'
                }`}>
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      {isBullish ? <TrendingUp size={14} className="text-emerald-400" /> : <TrendingDown size={14} className="text-red-400" />}
                      <span className="font-bold">{post.symbol || post.pair}</span>
                      <span className={`font-medium ${isBullish ? 'text-emerald-400' : 'text-red-400'}`}>
                        {post.side || (isBullish ? 'LONG' : 'SHORT')}
                      </span>
                    </div>
                    {post.pnl && (
                      <span className={`font-bold ${parseFloat(post.pnl) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {parseFloat(post.pnl) >= 0 ? '+' : ''}{post.pnl}%
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between px-3 py-2 border-t border-slate-700/50">
                <button onClick={() => handleLike(i)} className="flex items-center space-x-1 text-xs">
                  <Heart size={14} className={liked[i] ? 'text-pink-500 fill-pink-500' : 'text-slate-500'} />
                  <span className={liked[i] ? 'text-pink-500' : 'text-slate-500'}>
                    {(post.likes || 0) + (liked[i] ? 1 : 0)}
                  </span>
                </button>
                <div className="flex items-center space-x-1 text-xs text-slate-500">
                  <MessageCircle size={14} />
                  <span>{post.comments || 0}</span>
                </div>
                <div className="flex items-center space-x-1 text-xs text-slate-500">
                  <BarChart3 size={14} />
                  <span>{post.views || 0}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default SocialFeed
