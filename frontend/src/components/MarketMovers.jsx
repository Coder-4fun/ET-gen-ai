import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  TrendingUp, TrendingDown, Activity, RefreshCw,
  ArrowUpRight, ArrowDownRight, BarChart3, Zap, Flame
} from 'lucide-react'

const API = '/api'

function MoverRow({ item, index, type }) {
  const pos = item.change_pct >= 0
  const color = pos ? '#10b981' : '#f43f5e'
  const bgColor = pos ? 'rgba(16,185,129,0.06)' : 'rgba(244,63,94,0.06)'
  const borderColor = pos ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'

  return (
    <motion.div
      initial={{ opacity: 0, x: type === 'gainer' ? -12 : 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.06 }}
      className="card p-3 flex items-center gap-3"
      style={{ borderLeft: `3px solid ${color}` }}
    >
      {/* Rank */}
      <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold num-ticker shrink-0"
        style={{ background: bgColor, color, border: `1px solid ${borderColor}` }}>
        {index + 1}
      </div>

      {/* Stock info */}
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-sm truncate">{item.stock}</div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{item.sector}</span>
          <span className="text-[10px] num-ticker" style={{ color: 'var(--text-muted)' }}>{item.ticker?.replace('.NS', '')}</span>
        </div>
      </div>

      {/* Price */}
      <div className="text-right shrink-0">
        <div className="font-bold text-sm num-ticker">₹{item.price?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        <div className="flex items-center justify-end gap-0.5"
          style={{ color }}>
          {pos ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
          <span className="text-xs font-semibold num-ticker">
            {pos ? '+' : ''}{item.change_pct}%
          </span>
        </div>
      </div>

      {/* Change badge */}
      <div className="shrink-0 px-2 py-1 rounded-lg text-xs font-semibold num-ticker"
        style={{ background: bgColor, color, minWidth: 70, textAlign: 'center' }}>
        {pos ? '+' : ''}₹{item.change_abs?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
      </div>
    </motion.div>
  )
}

export default function MarketMovers() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('gainers')

  const load = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API}/alerts/movers`)
      setData(res.data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const tabs = [
    { id: 'gainers',     label: 'Top Gainers',  icon: TrendingUp,  color: '#10b981', count: data?.gainers?.length },
    { id: 'losers',      label: 'Top Losers',   icon: TrendingDown, color: '#f43f5e', count: data?.losers?.length },
    { id: 'most_active', label: 'Most Active',  icon: Activity,     color: '#6366f1', count: data?.most_active?.length },
  ]

  const currentList = data?.[activeTab] ?? []

  // Calculate totals for summary
  const gainersTotal = data?.gainers?.reduce((sum, g) => sum + g.change_pct, 0) ?? 0
  const losersTotal = data?.losers?.reduce((sum, l) => sum + l.change_pct, 0) ?? 0

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gradient flex items-center gap-2">
            <Flame size={18} /> Market Movers
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Top NIFTY 50 gainers, losers & most active stocks
          </p>
        </div>
        <button onClick={load} disabled={loading} className="btn-ghost p-2 rounded-lg">
          <motion.div animate={{ rotate: loading ? 360 : 0 }}
            transition={{ duration: 1, repeat: loading ? Infinity : 0, ease: 'linear' }}>
            <RefreshCw size={14} />
          </motion.div>
        </button>
      </div>

      {/* Summary Cards */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-3 gap-3 mb-5">
        <div className="glass rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={13} style={{ color: '#10b981' }} />
            <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Top Gainer</span>
          </div>
          <div className="font-bold text-sm truncate">{data?.gainers?.[0]?.stock ?? '—'}</div>
          <div className="text-xs num-ticker font-semibold mt-0.5" style={{ color: '#10b981' }}>
            {data?.gainers?.[0] ? `+${data.gainers[0].change_pct}%` : '—'}
          </div>
        </div>
        <div className="glass rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown size={13} style={{ color: '#f43f5e' }} />
            <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Top Loser</span>
          </div>
          <div className="font-bold text-sm truncate">{data?.losers?.[0]?.stock ?? '—'}</div>
          <div className="text-xs num-ticker font-semibold mt-0.5" style={{ color: '#f43f5e' }}>
            {data?.losers?.[0] ? `${data.losers[0].change_pct}%` : '—'}
          </div>
        </div>
        <div className="glass rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1">
            <Activity size={13} style={{ color: '#6366f1' }} />
            <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Most Active</span>
          </div>
          <div className="font-bold text-sm truncate">{data?.most_active?.[0]?.stock ?? '—'}</div>
          <div className="text-xs num-ticker font-semibold mt-0.5" style={{ color: '#6366f1' }}>
            {data?.most_active?.[0]?.volume ?? '—'} vol
          </div>
        </div>
      </motion.div>

      {/* Market Sentiment Bar */}
      {data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="glass rounded-xl p-4 mb-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              Market Sentiment
            </span>
            <span className="text-[10px] num-ticker" style={{ color: 'var(--text-muted)' }}>
              {data.gainers?.length ?? 0} advancing · {data.losers?.length ?? 0} declining
            </span>
          </div>
          <div className="h-3 rounded-full overflow-hidden flex" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(data.gainers?.length / ((data.gainers?.length ?? 0) + (data.losers?.length ?? 0))) * 100}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className="h-full rounded-l-full"
              style={{ background: 'linear-gradient(90deg, #10b981, #34d399)' }}
            />
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(data.losers?.length / ((data.gainers?.length ?? 0) + (data.losers?.length ?? 0))) * 100}%` }}
              transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
              className="h-full rounded-r-full"
              style={{ background: 'linear-gradient(90deg, #f43f5e, #fb7185)' }}
            />
          </div>
        </motion.div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        {tabs.map(tab => {
          const Icon = tab.icon
          const active = activeTab === tab.id
          return (
            <button key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`chip text-xs flex items-center gap-1.5 ${active ? 'active' : ''}`}
              style={active ? { background: `${tab.color}15`, borderColor: `${tab.color}40`, color: tab.color } : {}}>
              <Icon size={12} />
              {tab.label}
              {tab.count != null && (
                <span className="num-ticker text-[10px]">{tab.count}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* List */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
        </div>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }} className="flex flex-col gap-2">
            {currentList.map((item, i) => (
              <MoverRow key={item.ticker} item={item} index={i}
                type={activeTab === 'gainers' ? 'gainer' : activeTab === 'losers' ? 'loser' : 'active'} />
            ))}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  )
}
