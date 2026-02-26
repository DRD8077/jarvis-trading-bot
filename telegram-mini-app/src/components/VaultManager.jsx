import React, { useState, useEffect, useRef } from 'react'
import { Lock, Unlock, Key, Shield, Eye, EyeOff, Plus, Trash2, ArrowLeft, Copy, Check } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const VaultManager = () => {
  const navigate = useNavigate()
  const encryptedVaultRef = useRef(null)
  const [isUnlocked, setIsUnlocked] = useState(false)
  const [pin, setPin] = useState('')
  const [keys, setKeys] = useState([])
  const [showAdd, setShowAdd] = useState(false)
  const [newKey, setNewKey] = useState({ name: '', value: '', category: 'api' })
  const [error, setError] = useState('')
  const [copiedId, setCopiedId] = useState(null)
  const [showValues, setShowValues] = useState({})

  useEffect(() => {
    import('../services/encryptedVault').then(m => { encryptedVaultRef.current = m?.default || m }).catch(() => {})
  }, [])

  const handleUnlock = async () => {
    if (pin.length < 4) {
      setError('PIN minimum 4 digits')
      return
    }
    const ok = encryptedVaultRef.current ? await encryptedVaultRef.current.unlock(pin) : false
    if (ok) {
      setIsUnlocked(true)
      setError('')
      loadKeys()
    } else {
      setError('Wrong PIN — Try again')
    }
  }

  const loadKeys = async () => {
    const stored = []
    const categories = ['api', 'exchange', 'personal', 'other']
    for (const cat of categories) {
      const items = encryptedVaultRef.current ? await encryptedVaultRef.current.retrieve(`vault_list_${cat}`) : null
      if (items) {
        items.forEach(item => stored.push({ ...item, category: cat }))
      }
    }
    setKeys(stored)
  }

  const handleAdd = async () => {
    if (!newKey.name || !newKey.value) return
    const item = { name: newKey.name, id: Date.now().toString() }
    if (encryptedVaultRef.current) await encryptedVaultRef.current.store(`vault_${item.id}`, newKey.value)
    const listKey = `vault_list_${newKey.category}`
    const existing = (encryptedVaultRef.current ? await encryptedVaultRef.current.retrieve(listKey) : null) || []
    existing.push(item)
    if (encryptedVaultRef.current) await encryptedVaultRef.current.store(listKey, existing)
    setNewKey({ name: '', value: '', category: 'api' })
    setShowAdd(false)
    loadKeys()
  }

  const handleDelete = async (item) => {
    if (encryptedVaultRef.current) await encryptedVaultRef.current.remove(`vault_${item.id}`)
    const listKey = `vault_list_${item.category}`
    const existing = (encryptedVaultRef.current ? await encryptedVaultRef.current.retrieve(listKey) : null) || []
    if (encryptedVaultRef.current) await encryptedVaultRef.current.store(listKey, existing.filter(e => e.id !== item.id))
    loadKeys()
  }

  const handleCopy = async (item) => {
    const value = encryptedVaultRef.current ? await encryptedVaultRef.current.retrieve(`vault_${item.id}`) : null
    if (value) {
      await navigator.clipboard.writeText(value)
      setCopiedId(item.id)
      setTimeout(() => setCopiedId(null), 2000)
    }
  }

  const toggleShow = async (item) => {
    if (showValues[item.id]) {
      setShowValues(prev => ({ ...prev, [item.id]: null }))
    } else {
      const value = encryptedVaultRef.current ? await encryptedVaultRef.current.retrieve(`vault_${item.id}`) : null
      setShowValues(prev => ({ ...prev, [item.id]: value }))
    }
  }

  if (!isUnlocked) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] text-white flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center space-y-3">
            <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
              <Lock size={40} />
            </div>
            <h1 className="text-2xl font-bold">Secure Vault</h1>
            <p className="text-sm text-slate-400">AES-256-GCM Encrypted Storage</p>
            <p className="text-xs text-slate-500">Enter your PIN to unlock. First time? Set a new PIN.</p>
          </div>

          <div className="space-y-3">
            <input
              type="password"
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
              placeholder="Enter PIN (minimum 4 digits)"
              maxLength={8}
              className="w-full bg-slate-800 rounded-xl px-4 py-4 text-center text-2xl tracking-[0.5em] outline-none focus:ring-2 focus:ring-green-500"
              onKeyDown={e => e.key === 'Enter' && handleUnlock()}
            />
            {error && <p className="text-red-400 text-sm text-center">{error}</p>}
            <button
              onClick={handleUnlock}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-600 py-4 rounded-xl font-bold flex items-center justify-center gap-2"
            >
              <Unlock size={20} /> Unlock Vault
            </button>
            <button onClick={() => navigate(-1)} className="w-full text-slate-500 py-2 text-sm">
              ← Back
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white p-4 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="text-slate-400">
            <ArrowLeft size={20} />
          </button>
          <Shield className="text-green-400" size={24} />
          <div>
            <h1 className="font-bold text-lg">Secure Vault</h1>
            <p className="text-xs text-green-400">🔓 Unlocked • AES-256-GCM</p>
          </div>
        </div>
        <button
          onClick={() => { encryptedVaultRef.current?.lock?.(); setIsUnlocked(false); setPin('') }}
          className="px-3 py-1 bg-red-500/20 text-red-400 rounded-lg text-xs flex items-center gap-1"
        >
          <Lock size={14} /> Lock
        </button>
      </div>

      {/* Keys List */}
      <div className="space-y-3">
        {keys.length === 0 && !showAdd && (
          <div className="text-center py-12 space-y-3">
            <Key className="mx-auto text-slate-600" size={48} />
            <p className="text-slate-500">Vault is empty</p>
            <p className="text-xs text-slate-600">Add API keys, exchange credentials, passwords</p>
          </div>
        )}

        {keys.map((item) => (
          <div key={item.id} className="bg-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key size={16} className="text-green-400" />
                <span className="font-medium">{item.name}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700 text-slate-400 uppercase">
                  {item.category}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => toggleShow(item)} className="p-2 text-slate-400 hover:text-white">
                  {showValues[item.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
                <button onClick={() => handleCopy(item)} className="p-2 text-slate-400 hover:text-green-400">
                  {copiedId === item.id ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                </button>
                <button onClick={() => handleDelete(item)} className="p-2 text-slate-400 hover:text-red-400">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            {showValues[item.id] && (
              <p className="text-xs font-mono bg-slate-900 p-2 rounded break-all text-green-300">
                {showValues[item.id]}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Add New */}
      {showAdd ? (
        <div className="mt-4 bg-slate-800 rounded-xl p-4 space-y-3">
          <h3 className="font-bold flex items-center gap-2"><Plus size={16} /> Add Secret</h3>
          <input
            value={newKey.name}
            onChange={e => setNewKey(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Name (e.g. Binance API Key)"
            className="w-full bg-slate-900 rounded-lg px-3 py-2 text-sm outline-none"
          />
          <textarea
            value={newKey.value}
            onChange={e => setNewKey(prev => ({ ...prev, value: e.target.value }))}
            placeholder="Secret value"
            rows={3}
            className="w-full bg-slate-900 rounded-lg px-3 py-2 text-sm outline-none resize-none"
          />
          <select
            value={newKey.category}
            onChange={e => setNewKey(prev => ({ ...prev, category: e.target.value }))}
            className="w-full bg-slate-900 rounded-lg px-3 py-2 text-sm outline-none"
          >
            <option value="api">API Key</option>
            <option value="exchange">Exchange Credential</option>
            <option value="personal">Personal</option>
            <option value="other">Other</option>
          </select>
          <div className="flex gap-2">
            <button onClick={handleAdd} className="flex-1 bg-green-600 py-2 rounded-lg font-bold text-sm">Save</button>
            <button onClick={() => setShowAdd(false)} className="flex-1 bg-slate-700 py-2 rounded-lg text-sm">Cancel</button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowAdd(true)}
          className="w-full mt-4 py-3 rounded-xl border-2 border-dashed border-slate-700 text-slate-400 flex items-center justify-center gap-2 hover:border-green-500 hover:text-green-400"
        >
          <Plus size={18} /> Add New Secret
        </button>
      )}
    </div>
  )
}

export default VaultManager
