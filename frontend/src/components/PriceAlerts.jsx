import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  Target, Plus, X, TrendingUp, TrendingDown, Bell, BellOff,
  ArrowUp, ArrowDown, Trash2, CheckCircle, AlertCircle, Zap
} from 'lucide-react'

const API = '/api'

const QUICK_STOCKS = [
  { stock: 'Reliance Industries', ticker: 'RELIANCE.NS' },
  { stock: 'HDFC Bank', ticker: 'HDFCBANK.NS' },
  { stock: 'Infosys', ticker: 'INFY.NS' },
  { stock: 'Tata Motors', ticker: 'TATAMOTORS.NS' },
  { stock: 'Bajaj Finance', ticker: 'BAJFINANCE.NS' },
  { stock: 'Zomato', ticker: 'ZOMATO.NS' },
]

function PriceAlertCard({ alert, onDelete, onToggle }) {
  const triggered = alert.triggered
  const direction = alert.direction
  const icon = direction === 'above' ? ArrowUp : ArrowDown

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="card p-4"
      style={{
        borderLeft: `3px solid ${triggered ? '#10b981' : direction === 'above' ? '#06b6d4' : '#f43f5e'}`,
        opacity: alert.active ? 1 : 0.5,
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{
              background: triggered
                ? 'rgba(16,185,129,0.15)'
                : direction === 'above'
                  ? 'rgba(6,182,212,0.12)'
                  : 'rgba(244,63,94,0.12)',
            }}>
            {triggered ? (
              <CheckCircle size={18} style={{ color: '#10b981' }} />
            ) : (
              React.createElement(icon, { size: 18, style: { color: direction === 'above' ? '#06b6d4' : '#f43f5e' } })
            )}
          </div>
          <div>
            <div className="font-bold text-sm">{alert.stock}</div>
            <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
              {alert.ticker}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!triggered && (
            <button onClick={() => onToggle(alert.id)}
              className="btn-ghost p-1.5 rounded-lg" title={alert.active ? 'Pause alert' : 'Resume alert'}>
              {alert.active ? <Bell size={13} style={{ color: '#10b981' }} /> : <BellOff size={13} style={{ color: 'var(--text-muted)' }} />}
            </button>
          )}
          <button onClick={() => onDelete(alert.id)}
            className="btn-ghost p-1.5 rounded-lg" title="Delete alert">
            <Trash2 size={13} style={{ color: '#f43f5e' }} />
          </button>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-3">
        <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Target</div>
          <div className="font-bold text-sm num-ticker mt-0.5"
            style={{ color: direction === 'above' ? '#06b6d4' : '#f43f5e' }}>
            {direction === 'above' ? '↑' : '↓'} ₹{alert.target_price?.toLocaleString('en-IN')}
          </div>
        </div>
        <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Status</div>
          <div className="text-xs font-semibold mt-0.5" style={{
            color: triggered ? '#10b981' : alert.active ? '#f59e0b' : 'var(--text-muted)'
          }}>
            {triggered ? '✓ Triggered' : alert.active ? '● Active' : '○ Paused'}
          </div>
        </div>
        <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Notify</div>
          <div className="flex gap-1 mt-1">
            {alert.notify_email && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981' }}>Email</span>}
            {alert.notify_sms && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(6,182,212,0.15)', color: '#06b6d4' }}>SMS</span>}
            {alert.notify_push && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>Push</span>}
          </div>
        </div>
      </div>

      {triggered && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="mt-3 p-2 rounded-lg flex items-center gap-2 text-[11px]"
          style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', color: '#10b981' }}>
          <CheckCircle size={12} />
          Triggered at ₹{alert.triggered_price?.toLocaleString('en-IN')} on {alert.triggered_at?.split('T')[0]}
        </motion.div>
      )}
    </motion.div>
  )
}

export default function PriceAlerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    stock: '', ticker: '', target_price: '', direction: 'above',
    notify_email: true, notify_sms: false, notify_push: true,
  })
  const [creating, setCreating] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API}/alerts/price`, { params: { active_only: false }})
      setAlerts(res.data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!form.stock || !form.target_price) return
    setCreating(true)
    try {
      await axios.post(`${API}/alerts/price`, {
        ...form,
        target_price: parseFloat(form.target_price),
      })
      setShowForm(false)
      setForm({ stock: '', ticker: '', target_price: '', direction: 'above', notify_email: true, notify_sms: false, notify_push: true })
      load()
    } catch (e) { console.error(e) }
    finally { setCreating(false) }
  }

  const handleDelete = async (id) => {
    try { await axios.delete(`${API}/alerts/price/${id}`); load() }
    catch (e) { console.error(e) }
  }

  const handleToggle = async (id) => {
    try { await axios.post(`${API}/alerts/price/${id}/toggle`); load() }
    catch (e) { console.error(e) }
  }

  const activeCount = alerts.filter(a => a.active && !a.triggered).length
  const triggeredCount = alerts.filter(a => a.triggered).length

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gradient flex items-center gap-2">
            <Target size={18} /> Price Alerts
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Groww-style price target notifications
          </p>
        </div>
        <button onClick={() => setShowForm(s => !s)}
          className="btn-primary flex items-center gap-1.5 text-xs px-3 py-1.5">
          <Plus size={12} /> New Alert
        </button>
      </div>

      {/* Stats */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-3 gap-3 mb-5">
        <div className="glass rounded-xl px-4 py-3">
          <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Active</div>
          <div className="font-bold text-xl num-ticker mt-1" style={{ color: '#f59e0b' }}>{activeCount}</div>
        </div>
        <div className="glass rounded-xl px-4 py-3">
          <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Triggered</div>
          <div className="font-bold text-xl num-ticker mt-1" style={{ color: '#10b981' }}>{triggeredCount}</div>
        </div>
        <div className="glass rounded-xl px-4 py-3">
          <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Total</div>
          <div className="font-bold text-xl num-ticker mt-1" style={{ color: 'var(--accent-indigo)' }}>{alerts.length}</div>
        </div>
      </motion.div>

      {/* Create Form */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="rounded-2xl overflow-hidden mb-5"
            style={{ border: '1px solid rgba(99,102,241,0.3)' }}
          >
            <div className="p-5" style={{ background: 'rgba(99,102,241,0.06)' }}>
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-semibold" style={{ color: '#a5b4fc' }}>
                  <Zap size={13} className="inline mr-1" />Create Price Alert
                </span>
                <button onClick={() => setShowForm(false)} className="btn-ghost p-1 rounded">
                  <X size={14} />
                </button>
              </div>

              {/* Quick stock select */}
              <div className="mb-4">
                <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>
                  Quick Select
                </div>
                <div className="flex flex-wrap gap-2">
                  {QUICK_STOCKS.map(s => (
                    <button key={s.ticker}
                      onClick={() => setForm(f => ({ ...f, stock: s.stock, ticker: s.ticker }))}
                      className={`chip text-[11px] ${form.ticker === s.ticker ? 'active' : ''}`}>
                      {s.stock.split(' ')[0]}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Stock Name</label>
                  <input value={form.stock}
                    onChange={e => setForm(f => ({ ...f, stock: e.target.value }))}
                    placeholder="Reliance Industries"
                    className="w-full text-xs px-3 py-2 rounded-lg outline-none mt-1"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Ticker</label>
                  <input value={form.ticker}
                    onChange={e => setForm(f => ({ ...f, ticker: e.target.value }))}
                    placeholder="RELIANCE.NS"
                    className="w-full text-xs px-3 py-2 rounded-lg outline-none mt-1"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Target Price (₹)</label>
                  <input value={form.target_price}
                    onChange={e => setForm(f => ({ ...f, target_price: e.target.value }))}
                    type="number" placeholder="2500.00"
                    className="w-full text-xs px-3 py-2 rounded-lg outline-none mt-1"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Direction</label>
                  <div className="flex gap-2 mt-1">
                    <button
                      onClick={() => setForm(f => ({ ...f, direction: 'above' }))}
                      className={`flex-1 text-xs py-2 rounded-lg flex items-center justify-center gap-1 transition-all`}
                      style={{
                        background: form.direction === 'above' ? 'rgba(6,182,212,0.2)' : 'rgba(255,255,255,0.04)',
                        border: `1px solid ${form.direction === 'above' ? 'rgba(6,182,212,0.4)' : 'rgba(255,255,255,0.08)'}`,
                        color: form.direction === 'above' ? '#06b6d4' : 'var(--text-muted)',
                      }}>
                      <ArrowUp size={12} /> Above
                    </button>
                    <button
                      onClick={() => setForm(f => ({ ...f, direction: 'below' }))}
                      className={`flex-1 text-xs py-2 rounded-lg flex items-center justify-center gap-1 transition-all`}
                      style={{
                        background: form.direction === 'below' ? 'rgba(244,63,94,0.2)' : 'rgba(255,255,255,0.04)',
                        border: `1px solid ${form.direction === 'below' ? 'rgba(244,63,94,0.4)' : 'rgba(255,255,255,0.08)'}`,
                        color: form.direction === 'below' ? '#f43f5e' : 'var(--text-muted)',
                      }}>
                      <ArrowDown size={12} /> Below
                    </button>
                  </div>
                </div>
              </div>

              {/* Notify channels */}
              <div className="mb-4">
                <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>Notify via</div>
                <div className="flex gap-3">
                  {[
                    { key: 'notify_email', label: 'Email', color: '#10b981' },
                    { key: 'notify_sms', label: 'SMS', color: '#06b6d4' },
                    { key: 'notify_push', label: 'In-App', color: '#6366f1' },
                  ].map(ch => (
                    <button key={ch.key}
                      onClick={() => setForm(f => ({ ...f, [ch.key]: !f[ch.key] }))}
                      className="text-[11px] px-3 py-1.5 rounded-lg transition-all"
                      style={{
                        background: form[ch.key] ? `${ch.color}20` : 'rgba(255,255,255,0.04)',
                        border: `1px solid ${form[ch.key] ? `${ch.color}50` : 'rgba(255,255,255,0.08)'}`,
                        color: form[ch.key] ? ch.color : 'var(--text-muted)',
                      }}>
                      {ch.label}
                    </button>
                  ))}
                </div>
              </div>

              <button onClick={handleCreate} disabled={creating || !form.stock || !form.target_price}
                className="btn-primary w-full text-xs py-2.5">
                {creating ? 'Creating...' : 'Create Price Alert'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Alerts List */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-28 rounded-xl" />)}
        </div>
      ) : (
        <AnimatePresence>
          <div className="flex flex-col gap-3">
            {alerts.map(alert => (
              <PriceAlertCard key={alert.id} alert={alert}
                onDelete={handleDelete} onToggle={handleToggle} />
            ))}
            {alerts.length === 0 && (
              <div className="text-center py-16">
                <Target size={48} className="mx-auto mb-3 opacity-15" />
                <div className="text-sm" style={{ color: 'var(--text-muted)' }}>No price alerts yet</div>
                <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                  Set a target price and get notified via email, SMS, or push
                </div>
              </div>
            )}
          </div>
        </AnimatePresence>
      )}
    </div>
  )
}
