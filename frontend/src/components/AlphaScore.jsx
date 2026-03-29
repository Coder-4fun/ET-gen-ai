import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { TrendingUp, TrendingDown, Minus, RefreshCw, Info } from 'lucide-react'

const API = '/api'

const SIGNAL_COLORS = {
  'Strong Buy': { bg: 'rgba(16,185,129,0.12)', border: '#10b981', text: '#10b981', ring: '#10b981' },
  'Bullish':    { bg: 'rgba(6,182,212,0.12)',  border: '#06b6d4', text: '#06b6d4', ring: '#06b6d4' },
  'Neutral-Up': { bg: 'rgba(245,158,11,0.12)', border: '#f59e0b', text: '#f59e0b', ring: '#f59e0b' },
  'Neutral':    { bg: 'rgba(148,163,184,0.1)', border: '#94a3b8', text: '#94a3b8', ring: '#94a3b8' },
  'Caution':    { bg: 'rgba(244,63,94,0.12)',  border: '#f43f5e', text: '#f43f5e', ring: '#f43f5e' },
}

function ScoreRing({ score, color, size = 60 }) {
  const r = (size - 8) / 2
  const circ = 2 * Math.PI * r
  const dash = (score / 100) * circ

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="rgba(255,255,255,0.06)" strokeWidth={5} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth={5}
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - dash }}
          transition={{ duration: 1.2, ease: 'easeOut', delay: 0.2 }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-bold text-sm num-ticker" style={{ color }}>{score}</span>
      </div>
    </div>
  )
}

function ComponentBar({ label, value, color }) {
  return (
    <div className="flex items-center gap-2 mb-1.5">
      <span className="text-[10px] w-24 shrink-0" style={{ color: 'var(--text-muted)' }}>{label}</span>
      <div className="flex-1 h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.3 }}
        />
      </div>
      <span className="text-[10px] w-7 text-right num-ticker" style={{ color: 'var(--text-muted)' }}>{value.toFixed(0)}</span>
    </div>
  )
}

function AlphaCard({ item, rank, delay }) {
  const [expanded, setExpanded] = useState(false)
  const colors = SIGNAL_COLORS[item.signal_label] || SIGNAL_COLORS['Neutral']

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      onClick={() => setExpanded(e => !e)}
      className="card cursor-pointer"
      style={{
        border: `1px solid ${expanded ? colors.border : 'rgba(255,255,255,0.07)'}`,
        background: expanded ? colors.bg : undefined,
        transition: 'all 0.25s',
      }}
      whileHover={{ scale: 1.01 }}
    >
      <div className="flex items-center gap-3">
        {/* Rank badge */}
        <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-sm font-bold num-ticker"
          style={{
            background: rank <= 3 ? `rgba(${rank === 1 ? '245,158,11' : rank === 2 ? '148,163,184' : '205,127,50'},0.2)` : 'rgba(255,255,255,0.05)',
            color: rank <= 3 ? (rank === 1 ? '#f59e0b' : rank === 2 ? '#e2e8f0' : '#cd7f32') : 'var(--text-muted)',
          }}>
          {rank}
        </div>

        {/* Ring */}
        <ScoreRing score={item.alpha_score} color={colors.ring} size={52} />

        {/* Stock info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="font-semibold text-sm truncate" style={{ color: 'var(--text-primary)' }}>
              {item.stock}
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold"
              style={{ background: colors.bg, color: colors.text, border: `1px solid ${colors.border}40` }}>
              {item.signal_label}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{item.sector}</span>
            {item.active_signals > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full"
                style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
                {item.active_signals} signals
              </span>
            )}
          </div>
        </div>

        {/* Score large */}
        <div className="text-right shrink-0">
          <div className="font-bold text-xl num-ticker" style={{ color: colors.text }}>
            {item.alpha_score}
          </div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>/ 100</div>
        </div>
      </div>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: 'hidden' }}
          >
            <div className="mt-4 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.07)' }}>
              <div className="text-[11px] font-semibold mb-2 uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                Score Breakdown
              </div>
              <ComponentBar label="Institutional" value={item.components.institutional} color={colors.ring} />
              <ComponentBar label="Technical"     value={item.components.technical}     color={colors.ring} />
              <ComponentBar label="Sentiment"     value={item.components.sentiment}     color={colors.ring} />
              <ComponentBar label="Earnings"      value={item.components.earnings}      color={colors.ring} />

              {item.signal_types?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {item.signal_types.map(t => (
                    <span key={t} className="px-2 py-0.5 rounded text-[10px]"
                      style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)' }}>
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function AlphaScore() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter]   = useState('All')

  const load = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API}/alpha`)
      setData(res.data)
    } catch (e) {
      console.error('Alpha load failed:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const FILTERS = ['All', 'Strong Buy', 'Bullish', 'Neutral-Up', 'Neutral', 'Caution']
  const scores = data?.scores?.filter(s => filter === 'All' || s.signal_label === filter) ?? []

  const topStock = data?.scores?.[0]

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gradient">Alpha Score Leaderboard</h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            AI-ranked stocks by composite signal strength · Click a card for breakdown
          </p>
        </div>
        <button onClick={load} disabled={loading}
          className="btn-ghost p-2 rounded-lg"
          style={{ opacity: loading ? 0.5 : 1 }}>
          <motion.div animate={{ rotate: loading ? 360 : 0 }}
            transition={{ duration: 1, repeat: loading ? Infinity : 0, ease: 'linear' }}>
            <RefreshCw size={14} />
          </motion.div>
        </button>
      </div>

      {/* Top stock highlight */}
      {topStock && (
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-2xl p-4 mb-5"
          style={{
            background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(6,182,212,0.1))',
            border: '1px solid rgba(99,102,241,0.3)',
          }}>
          <div className="text-[10px] uppercase tracking-widest mb-2 font-semibold" style={{ color: '#a5b4fc' }}>
            🏆 Top Alpha Pick Today
          </div>
          <div className="flex items-center gap-4">
            <ScoreRing score={topStock.alpha_score} color="#a5b4fc" size={72} />
            <div>
              <div className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{topStock.stock}</div>
              <div className="text-sm font-semibold" style={{ color: '#a5b4fc' }}>{topStock.signal_label}</div>
              <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                Institutional: {topStock.components.institutional.toFixed(0)} · Technical: {topStock.components.technical.toFixed(0)} · Sentiment: {topStock.components.sentiment.toFixed(0)}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Formula callout */}
      <div className="rounded-xl p-3 mb-5 flex items-start gap-2"
        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <Info size={13} style={{ color: '#06b6d4', marginTop: 1 }} />
        <div className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
          <span style={{ color: 'var(--text-secondary)' }} className="font-semibold">Formula: </span>
          Alpha Score = Institutional Buying (25%) + Technical Breakout (25%) + Sentiment (25%) + Earnings Growth (25%)
        </div>
      </div>

      {/* Filter chips */}
      <div className="flex gap-2 flex-wrap mb-4">
        {FILTERS.map(f => {
          const col = Object.entries(SIGNAL_COLORS).find(([k]) => k === f)?.[1]
          return (
            <button key={f} onClick={() => setFilter(f)}
              className="px-3 py-1 rounded-full text-xs font-medium transition-all"
              style={{
                background: filter === f ? (col?.bg ?? 'rgba(99,102,241,0.2)') : 'rgba(255,255,255,0.05)',
                border: `1px solid ${filter === f ? (col?.border ?? '#6366f1') : 'rgba(255,255,255,0.08)'}`,
                color: filter === f ? (col?.text ?? '#a5b4fc') : 'var(--text-muted)',
              }}>
              {f}
            </button>
          )
        })}
      </div>

      {/* Cards list */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[...Array(6)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {scores.map((item, i) => (
            <AlphaCard key={item.ticker} item={item} rank={i + 1} delay={i * 0.04} />
          ))}
          {scores.length === 0 && (
            <div className="text-center py-16" style={{ color: 'var(--text-muted)' }}>
              No stocks matching this filter
            </div>
          )}
        </div>
      )}
    </div>
  )
}
