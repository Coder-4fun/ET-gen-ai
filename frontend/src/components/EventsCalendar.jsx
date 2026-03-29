import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  Calendar, BarChart3, Coins, Scissors, Gift, RefreshCw,
  ChevronRight, Filter, Clock, AlertCircle, TrendingUp
} from 'lucide-react'

const API = '/api'

const EVENT_CONFIG = {
  Earnings:      { icon: BarChart3, color: '#6366f1', bg: 'rgba(99,102,241,0.12)',  label: 'Earnings' },
  Dividend:      { icon: Coins,     color: '#10b981', bg: 'rgba(16,185,129,0.12)',  label: 'Dividend' },
  'Stock Split': { icon: Scissors,  color: '#06b6d4', bg: 'rgba(6,182,212,0.12)',   label: 'Split' },
  Bonus:         { icon: Gift,      color: '#f59e0b', bg: 'rgba(245,158,11,0.12)',  label: 'Bonus' },
  'Rights Issue':{ icon: TrendingUp,color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)',  label: 'Rights' },
  Buyback:       { icon: RefreshCw, color: '#ec4899', bg: 'rgba(236,72,153,0.12)',  label: 'Buyback' },
}

const IMPACT_BADGE = {
  High:   { color: '#f43f5e', bg: 'rgba(244,63,94,0.12)' },
  Medium: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  Low:    { color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
}

function EventCard({ event, index }) {
  const cfg = EVENT_CONFIG[event.type] ?? EVENT_CONFIG.Earnings
  const impact = IMPACT_BADGE[event.impact] ?? IMPACT_BADGE.Medium
  const Icon = cfg.icon

  // Days remaining
  const today = new Date()
  const eventDate = new Date(event.date)
  const daysLeft = Math.ceil((eventDate - today) / (1000 * 60 * 60 * 24))
  const isToday = daysLeft === 0
  const isSoon = daysLeft <= 3 && daysLeft > 0

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="card p-4"
      style={{
        borderLeft: `3px solid ${cfg.color}`,
        ...(isToday && { boxShadow: `0 0 20px ${cfg.color}20` }),
      }}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: cfg.bg }}>
          <Icon size={18} style={{ color: cfg.color }} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="font-bold text-sm truncate">{event.stock}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold"
              style={{ background: cfg.bg, color: cfg.color }}>
              {cfg.label}
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded"
              style={{ background: impact.bg, color: impact.color }}>
              {event.impact}
            </span>
          </div>

          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{event.detail}</div>

          <div className="flex items-center gap-3 mt-2">
            <span className="text-[10px] flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
              <Calendar size={10} />
              {new Date(event.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
            </span>
            <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
              {event.ticker}
            </span>
          </div>
        </div>

        {/* Days countdown */}
        <div className="text-right shrink-0">
          <div className={`font-bold text-lg num-ticker ${isToday ? 'text-gradient-emerald' : isSoon ? 'text-gradient-gold' : ''}`}
            style={!isToday && !isSoon ? { color: 'var(--text-secondary)' } : {}}>
            {isToday ? 'TODAY' : daysLeft < 0 ? 'Passed' : `${daysLeft}d`}
          </div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            {isToday ? '🔴 Live' : isSoon ? '⚡ Soon' : daysLeft < 0 ? '' : 'remaining'}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default function EventsCalendar() {
  const [events, setEvents] = useState([])
  const [types, setTypes] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [watchlistOnly, setWatchlistOnly] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filter !== 'all') params.event_type = filter
      if (watchlistOnly) params.watchlist_only = true
      const res = await axios.get(`${API}/alerts/events`, { params })
      setEvents(res.data.events ?? [])
      setTypes(res.data.types ?? [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filter, watchlistOnly])

  // Group by month
  const grouped = events.reduce((acc, evt) => {
    const month = new Date(evt.date).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })
    if (!acc[month]) acc[month] = []
    acc[month].push(evt)
    return acc
  }, {})

  const eventTypes = ['all', ...(types || [])]

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gradient flex items-center gap-2">
            <Calendar size={18} /> Events Calendar
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Upcoming earnings, dividends, splits & corporate actions
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setWatchlistOnly(v => !v)}
            className={`chip text-xs ${watchlistOnly ? 'active' : ''}`}>
            <Filter size={10} /> {watchlistOnly ? 'Watchlist' : 'All Stocks'}
          </button>
          <button onClick={load} disabled={loading}
            className="btn-ghost p-2 rounded-lg">
            <motion.div animate={{ rotate: loading ? 360 : 0 }}
              transition={{ duration: 1, repeat: loading ? Infinity : 0, ease: 'linear' }}>
              <RefreshCw size={14} />
            </motion.div>
          </button>
        </div>
      </div>

      {/* Event Type Filters */}
      <div className="flex flex-wrap gap-2 mb-5">
        {eventTypes.map(type => {
          const cfg = EVENT_CONFIG[type]
          return (
            <button key={type}
              onClick={() => setFilter(type)}
              className={`chip text-[11px] flex items-center gap-1.5 ${filter === type ? 'active' : ''}`}
              style={filter === type && cfg ? {
                background: cfg.bg, borderColor: `${cfg.color}40`, color: cfg.color
              } : {}}>
              {cfg && React.createElement(cfg.icon, { size: 10 })}
              {type === 'all' ? 'All Events' : cfg?.label ?? type}
              {type !== 'all' && (
                <span className="num-ticker">{events.filter(e => e.type === type).length}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Summary Cards */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        className="grid grid-cols-3 md:grid-cols-6 gap-2 mb-5">
        {Object.entries(EVENT_CONFIG).map(([type, cfg]) => {
          const count = events.filter(e => e.type === type).length
          const Icon = cfg.icon
          return (
            <div key={type} className="glass rounded-xl px-3 py-2 text-center cursor-pointer"
              onClick={() => setFilter(type === filter ? 'all' : type)}
              style={{ border: filter === type ? `1px solid ${cfg.color}40` : undefined }}>
              <Icon size={16} className="mx-auto mb-1" style={{ color: cfg.color }} />
              <div className="text-lg font-bold num-ticker" style={{ color: cfg.color }}>{count}</div>
              <div className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{cfg.label}</div>
            </div>
          )
        })}
      </motion.div>

      {/* Events Grouped by Month */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
        </div>
      ) : (
        Object.entries(grouped).map(([month, monthEvents]) => (
          <div key={month} className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <div className="text-xs font-semibold uppercase tracking-wider"
                style={{ color: 'var(--accent-indigo)' }}>
                {month}
              </div>
              <div className="flex-1 h-px" style={{ background: 'rgba(99,102,241,0.15)' }} />
              <span className="text-[10px] num-ticker" style={{ color: 'var(--text-muted)' }}>
                {monthEvents.length} events
              </span>
            </div>
            <div className="flex flex-col gap-3">
              {monthEvents.map((evt, i) => (
                <EventCard key={`${evt.stock}-${evt.type}`} event={evt} index={i} />
              ))}
            </div>
          </div>
        ))
      )}

      {events.length === 0 && !loading && (
        <div className="text-center py-16">
          <Calendar size={48} className="mx-auto mb-3 opacity-15" />
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>No upcoming events</div>
          <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
            {watchlistOnly ? 'Try showing all stocks' : 'Check back later'}
          </div>
        </div>
      )}
    </div>
  )
}
