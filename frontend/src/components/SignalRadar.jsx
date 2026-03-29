import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Filter, Zap, TrendingUp, TrendingDown, Activity } from 'lucide-react'
import useStore from '../store/useStore'
import SignalCard from './SignalCard'

const FILTERS = [
  { id: 'all',    label: 'All Signals' },
  { id: 'High',   label: 'High Risk' },
  { id: 'Medium', label: 'Medium Risk' },
  { id: 'Low',    label: 'Low Risk' },
]

const SOURCES = ['All', 'NLP', 'Candlestick', 'Anomaly', 'Options', 'SocialSentiment']

export default function SignalRadar() {
  const { signals } = useStore()
  const [riskFilter, setRiskFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('All')

  const filtered = signals
    .filter(s => riskFilter === 'all' || s.risk === riskFilter)
    .filter(s => sourceFilter === 'All' || (s.contributing_signals ?? []).includes(sourceFilter))
    .sort((a, b) => b.confidence - a.confidence)

  const stats = {
    high:   signals.filter(s => s.risk === 'High').length,
    medium: signals.filter(s => s.risk === 'Medium').length,
    low:    signals.filter(s => s.risk === 'Low').length,
  }

  return (
    <div className="p-5 max-w-full">
      {/* Header stats bento row */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="grid grid-cols-4 gap-3 mb-5"
      >
        {[
          { label: 'Total Signals', value: signals.length, icon: Activity, color: 'var(--accent-indigo)' },
          { label: 'High Risk',     value: stats.high,     icon: TrendingDown, color: 'var(--accent-rose)' },
          { label: 'Medium Risk',   value: stats.medium,   icon: Activity,     color: 'var(--accent-amber)' },
          { label: 'Low Risk',      value: stats.low,      icon: TrendingUp,   color: 'var(--accent-emerald)' },
        ].map(({ label, value, icon: Icon, color }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.07, duration: 0.35 }}
            className="glass rounded-xl px-4 py-3 flex items-center gap-3"
          >
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: `${color}18` }}>
              <Icon size={16} style={{ color }} />
            </div>
            <div>
              <motion.div
                key={value}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="font-bold text-xl num-ticker" style={{ color }}
              >
                {value}
              </motion.div>
              <div className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{label}</div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        <div className="flex items-center gap-1.5 mr-2">
          <Filter size={13} style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Risk:</span>
        </div>
        {FILTERS.map(f => (
          <motion.button
            key={f.id}
            whileTap={{ scale: 0.95 }}
            onClick={() => setRiskFilter(f.id)}
            className={`chip ${riskFilter === f.id ? 'active' : ''}`}
          >
            {f.label}
          </motion.button>
        ))}
        <div className="w-px mx-1" style={{ background: 'rgba(255,255,255,0.08)' }} />
        <div className="flex items-center gap-1.5 mr-1">
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Source:</span>
        </div>
        {SOURCES.map(s => (
          <motion.button
            key={s}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSourceFilter(s)}
            className={`chip ${sourceFilter === s ? 'active' : ''}`}
          >
            {s}
          </motion.button>
        ))}
      </div>

      {/* Signal Grid */}
      {filtered.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-24 gap-4"
        >
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
            style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)' }}>
            <Zap size={28} style={{ color: 'var(--accent-indigo)' }} />
          </div>
          <div className="text-center">
            <div className="font-semibold mb-1">No signals found</div>
            <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Try adjusting your filters</div>
          </div>
        </motion.div>
      ) : (
        <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
          <AnimatePresence>
            {filtered.map((signal, i) => (
              <SignalCard key={signal.id ?? i} signal={signal} index={i} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
