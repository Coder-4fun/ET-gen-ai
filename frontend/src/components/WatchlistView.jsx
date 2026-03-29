import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { Bookmark, BookmarkX, RefreshCw, TrendingUp, TrendingDown, Bell, Plus, X } from 'lucide-react'

const API = '/api'

function WatchlistCard({ item, onRemove }) {
  const pos = item.change_pct >= 0
  const hasAlert = !!item.alert

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="card"
      style={{
        border: hasAlert ? '1px solid rgba(16,185,129,0.4)' : '1px solid rgba(255,255,255,0.07)',
        background: hasAlert ? 'rgba(16,185,129,0.05)' : undefined,
      }}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{item.stock}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)' }}>
              {item.sector}
            </span>
            {item.signal_count > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full font-semibold"
                style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
                {item.signal_count} signals
              </span>
            )}
          </div>

          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Added {item.added} · {item.ticker}
          </div>

          {hasAlert && (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-2 flex items-center gap-1.5 text-[11px]"
              style={{ color: '#10b981' }}>
              <Bell size={10} />
              {item.alert}
            </motion.div>
          )}

          {item.top_signal && (
            <div className="mt-1.5 text-[10px]" style={{ color: 'var(--text-muted)' }}>
              Top signal: <span style={{ color: '#a5b4fc' }}>{item.top_signal}</span>
              {item.top_confidence && (
                <span className="ml-1 num-ticker">({(item.top_confidence * 100).toFixed(0)}%)</span>
              )}
            </div>
          )}
        </div>

        <div className="text-right shrink-0">
          <div className="font-bold text-base num-ticker" style={{ color: 'var(--text-primary)' }}>
            ₹{item.current_price?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className={`text-sm font-semibold num-ticker flex items-center justify-end gap-0.5 ${pos ? 'pnl-pos' : 'pnl-neg'}`}>
            {pos ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {pos ? '+' : ''}{item.change_pct}%
          </div>
        </div>

        <button onClick={() => onRemove(item.ticker)}
          className="btn-ghost p-1.5 rounded-lg shrink-0 mt-0.5"
          title="Remove from watchlist">
          <BookmarkX size={13} style={{ color: '#f43f5e' }} />
        </button>
      </div>
    </motion.div>
  )
}

const POPULAR_STOCKS = [
  { ticker: 'MARUTI.NS',    stock: 'Maruti Suzuki',    sector: 'Auto' },
  { ticker: 'DRREDDY.NS',   stock: "Dr Reddy's",       sector: 'Pharma' },
  { ticker: 'TITAN.NS',     stock: 'Titan Company',    sector: 'Consumer' },
  { ticker: 'ONGC.NS',      stock: 'ONGC',             sector: 'Energy' },
  { ticker: 'POWERGRID.NS', stock: 'Power Grid',       sector: 'Utilities' },
  { ticker: 'ADANIPORTS.NS',stock: 'Adani Ports',      sector: 'Infrastructure' },
]

export default function WatchlistView() {
  const [items, setItems]       = useState([])
  const [loading, setLoading]   = useState(true)
  const [showAdd, setShowAdd]   = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API}/watchlist`)
      setItems(res.data.items ?? [])
    } catch (e) {
      console.error('Watchlist load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleRemove = async (ticker) => {
    try {
      await axios.delete(`${API}/watchlist/${ticker}`)
      setItems(prev => prev.filter(i => i.ticker !== ticker))
    } catch (e) { console.error('Remove error:', e) }
  }

  const handleAdd = async (stock) => {
    try {
      await axios.post(`${API}/watchlist`, stock)
      setShowAdd(false)
      load()
    } catch (e) { console.error('Add error:', e) }
  }

  const alertCount = items.filter(i => i.alert).length

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gradient flex items-center gap-2">
            <Bookmark size={18} /> Smart Watchlist
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Signal-aware watchlist with live alerts
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowAdd(s => !s)}
            className="btn-primary flex items-center gap-1.5 text-xs px-3 py-1.5">
            <Plus size={12} /> Add Stock
          </button>
          <button onClick={load} disabled={loading} className="btn-ghost p-2 rounded-lg">
            <motion.div animate={{ rotate: loading ? 360 : 0 }}
              transition={{ duration: 1, repeat: loading ? Infinity : 0, ease: 'linear' }}>
              <RefreshCw size={14} />
            </motion.div>
          </button>
        </div>
      </div>

      {/* Alert summary */}
      {alertCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl p-3 mb-4 flex items-center gap-2"
          style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }}>
          <Bell size={14} style={{ color: '#10b981' }} />
          <span className="text-sm" style={{ color: '#10b981' }}>
            <strong>{alertCount}</strong> stock{alertCount > 1 ? 's' : ''} in your watchlist {alertCount > 1 ? 'have' : 'has'} active high-confidence signals!
          </span>
        </motion.div>
      )}

      {/* Add stock panel */}
      <AnimatePresence>
        {showAdd && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="rounded-xl overflow-hidden mb-4"
            style={{ border: '1px solid rgba(99,102,241,0.3)' }}>
            <div className="p-4" style={{ background: 'rgba(99,102,241,0.08)' }}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold" style={{ color: '#a5b4fc' }}>Quick Add</span>
                <button onClick={() => setShowAdd(false)} className="btn-ghost p-1 rounded">
                  <X size={12} />
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {POPULAR_STOCKS.filter(s => !items.some(i => i.ticker === s.ticker)).map(s => (
                  <button key={s.ticker} onClick={() => handleAdd(s)}
                    className="flex items-center gap-2 p-2 rounded-lg text-left transition-all"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.15)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.04)'}>
                    <Plus size={12} style={{ color: '#6366f1' }} />
                    <div>
                      <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>{s.stock}</div>
                      <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{s.sector}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Watchlist */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
        </div>
      ) : (
        <AnimatePresence>
          <div className="flex flex-col gap-3">
            {items.map(item => (
              <WatchlistCard key={item.ticker} item={item} onRemove={handleRemove} />
            ))}
            {items.length === 0 && (
              <div className="text-center py-16" style={{ color: 'var(--text-muted)' }}>
                <Bookmark size={40} className="mx-auto mb-3 opacity-20" />
                <div>Your watchlist is empty</div>
                <div className="text-xs mt-1">Add stocks using the button above</div>
              </div>
            )}
          </div>
        </AnimatePresence>
      )}
    </div>
  )
}
