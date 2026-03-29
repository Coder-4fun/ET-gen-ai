import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  Activity, TrendingUp, TrendingDown, Zap, Shield,
  BarChart3, Eye, AlertTriangle, ChevronRight
} from 'lucide-react'
import useStore, { inferBias } from '../../store/useStore'
import SignalCard from '../SignalCard'

const API = '/api'

function RegimeIndicator({ regime }) {
  const config = {
    strong_bull:  { label: 'Strong Bull',  color: '#22C55E', icon: TrendingUp },
    weak_bull:    { label: 'Weak Bull',    color: '#22C55E', icon: TrendingUp },
    sideways:     { label: 'Sideways',     color: '#F59E0B', icon: Activity },
    weak_bear:    { label: 'Weak Bear',    color: '#EF4444', icon: TrendingDown },
    strong_bear:  { label: 'Strong Bear',  color: '#EF4444', icon: TrendingDown },
  }
  const c = config[regime?.regime] || config.sideways
  const Icon = c.icon

  return (
    <div className="h-full rounded-xl p-5"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div className="flex items-center gap-2 mb-4">
        <Icon size={14} style={{ color: c.color }} />
        <span className="label-sm uppercase tracking-widest" style={{ letterSpacing: '0.15em', fontSize: 9 }}>Market Regime</span>
      </div>
      <div className="font-semibold text-lg mb-4" style={{ color: c.color }}>{c.label}</div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="meta-xs mb-1">Confidence</div>
          <div className="num-ticker font-bold text-xl">{((regime?.confidence || 0.54) * 100).toFixed(0)}</div>
        </div>
        <div>
          <div className="meta-xs mb-1">Multiplier</div>
          <div className="num-ticker font-bold text-xl">{(regime?.signal_multiplier || 0.85).toFixed(2)}×</div>
        </div>
      </div>
      {(regime?.regime === 'weak_bear' || regime?.regime === 'strong_bear') && (
        <div className="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.1)' }}>
          <AlertTriangle size={11} style={{ color: '#EF4444' }} />
          <span className="text-[10px]" style={{ color: '#EF4444' }}>Bear regime — bullish signals discounted</span>
        </div>
      )}
    </div>
  )
}

export default function DashboardSection() {
  const { signals, portfolio, setRegime } = useStore()
  const [regime, setLocalRegime] = useState(null)
  const [accuracy, setAccuracy] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [regRes, accRes] = await Promise.allSettled([
          axios.get(`${API}/regime`),
          axios.get(`${API}/accuracy`),
        ])
        if (regRes.status === 'fulfilled') {
          setLocalRegime(regRes.value.data)
          setRegime(regRes.value.data) // store globally for signal cards
        }
        if (accRes.status === 'fulfilled') setAccuracy(accRes.value.data)
      } catch (e) { /* silent */ }
    }
    load()
  }, [])

  const highConf = signals.filter(s => {
    const conf = s.confidence_score ?? (s.confidence ? (s.confidence <= 1 ? s.confidence * 100 : s.confidence) : 0)
    return conf >= 75
  })

  const bullish = signals.filter(s => s.directional_bias === 'bullish').length
  const bearish = signals.filter(s => s.directional_bias === 'bearish').length

  const totalPnl = portfolio?.summary?.total_pnl_pct ?? portfolio?.summary?.total_pnl_percent ?? 0

  return (
    <div className="p-6 max-w-[1440px] mx-auto">
      {/* Page title */}
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-5"
      >
        <h2 className="text-2xl font-bold tracking-tight">Command Center</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--text-muted)' }}>
          {signals.length} signals active · {highConf.length} high confidence · Updated {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })}
        </p>
      </motion.div>

      {/* Asymmetric Bento Grid */}
      <div className="grid gap-3 mb-4" style={{
        gridTemplateColumns: '1fr 2fr 1fr',
        gridTemplateRows: 'auto auto',
        gridTemplateAreas: `
          "signals regime portfolio"
          "accuracy regime portfolio"
        `
      }}>
        {/* Active Signals — tall left */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0 }}
          className="rounded-xl p-5"
          style={{ gridArea: 'signals', background: 'var(--bg-card)', border: '1px solid var(--border)' }}
        >
          <div className="label-sm uppercase tracking-widest mb-3" style={{ letterSpacing: '0.15em', fontSize: 9 }}>Active Signals</div>
          <div className="hero-num num-ticker" style={{ color: 'var(--accent)' }}>{signals.length}</div>
          <div className="flex items-center gap-4 mt-3">
            <div>
              <div className="meta-xs">Bullish</div>
              <div className="num-ticker font-semibold text-base" style={{ color: 'var(--green)' }}>{bullish}</div>
            </div>
            <div className="h-6 w-px" style={{ background: 'var(--border)' }} />
            <div>
              <div className="meta-xs">Bearish</div>
              <div className="num-ticker font-semibold text-base" style={{ color: 'var(--red)' }}>{bearish}</div>
            </div>
          </div>
        </motion.div>

        {/* Market Regime — wide center */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          style={{ gridArea: 'regime' }}
        >
          <RegimeIndicator regime={regime} />
        </motion.div>

        {/* Portfolio Snapshot — tall right */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-xl p-5"
          style={{ gridArea: 'portfolio', background: 'var(--bg-card)', border: '1px solid var(--border)' }}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="label-sm uppercase tracking-widest" style={{ letterSpacing: '0.15em', fontSize: 9 }}>Portfolio</span>
            <Eye size={12} style={{ color: 'var(--text-dim)' }} />
          </div>
          <div className={`hero-num num-ticker ${totalPnl >= 0 ? 'pnl-pos' : 'pnl-neg'}`} style={{ fontSize: 24 }}>
            {totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(1)}%
          </div>
          <div className="mt-3 space-y-2">
            {portfolio?.holdings?.slice(0, 4)?.map((h, i) => (
              <div key={h.stock} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-1 h-1 rounded-full" style={{ background: ['var(--accent)', 'var(--green)', '#A3A3A3', '#6B6B6B'][i] }} />
                  <span className="text-xs font-medium">{h.stock}</span>
                </div>
                <span className={`text-xs num-ticker ${h.pnl_percent >= 0 ? 'pnl-pos' : 'pnl-neg'}`}>
                  {h.pnl_percent >= 0 ? '+' : ''}{h.pnl_percent?.toFixed(1)}%
                </span>
              </div>
            )) ?? (
              <div className="text-xs" style={{ color: 'var(--text-dim)' }}>
                Add holdings manually or connect Zerodha / Angel One
              </div>
            )}
          </div>
        </motion.div>

        {/* Accuracy — bottom left */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-xl p-5"
          style={{ gridArea: 'accuracy', background: 'var(--bg-card)', border: '1px solid var(--border)' }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="label-sm uppercase tracking-widest" style={{ letterSpacing: '0.15em', fontSize: 9 }}>Signal Accuracy</span>
            {(!accuracy?.overall?.total_resolved || accuracy.overall.total_resolved === 0) && (
              <span className="text-[9px]" style={{ color: 'var(--text-dim)' }}>SIMULATED</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <motion.div
                className="h-full rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${accuracy?.overall?.total_resolved > 0 ? (accuracy.overall.accuracy_pct || 0) : 78}%` }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
                style={{ background: 'var(--green)' }}
              />
            </div>
            <span className="num-ticker font-bold text-lg" style={{ color: 'var(--green)' }}>
              {accuracy?.overall?.total_resolved > 0 ? (accuracy.overall.accuracy_pct || 0).toFixed(0) : 78}%
            </span>
          </div>
          <div className="meta-xs mt-2">
            {accuracy?.overall?.total_resolved > 0 ? accuracy.overall.total_resolved : 124} signals resolved
          </div>
        </motion.div>
      </div>

      {/* Top Signals */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="title-md font-semibold">Top Signals</h3>
          <span className="meta-xs num-ticker">Highest confidence first</span>
        </div>
        <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))' }}>
          <AnimatePresence>
            {(highConf.length > 0 ? highConf : signals).slice(0, 6).map((signal, i) => (
              <SignalCard key={signal.id ?? i} signal={signal} index={i} />
            ))}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Watermark */}
      <div className="watermark">SIMULATED DATA</div>
    </div>
  )
}
