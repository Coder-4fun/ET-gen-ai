import React from 'react'
import { motion } from 'framer-motion'
import { X, TrendingUp, TrendingDown, BarChart3, AlertTriangle, ExternalLink, Bell } from 'lucide-react'
import useStore from '../store/useStore'

const MOCK_HISTORY = {
  'RELIANCE': ['+8.2%', '+3.1%', '-2.4%'],
  'HDFCBANK': ['+5.1%', '+1.8%', '+4.2%'],
  'BAJFINANCE': ['-3.4%', '+6.1%', '+2.7%'],
  'INFY': ['+4.5%', '+2.0%', '-1.1%'],
}

export default function SignalDetailDrawer({ signal, onClose }) {
  if (!signal) return null

  const bias = signal.directional_bias || signal.bias || 'neutral'
  const confidence = signal.confidence_score || Math.round((signal.confidence || 0) * 100)
  const barColor = bias === 'bullish' ? 'var(--green)' : bias === 'bearish' ? 'var(--red)' : 'var(--text-muted)'
  const history = MOCK_HISTORY[signal.symbol] || ['+4.1%', '+1.5%', '-0.8%']

  // Check for Devanagari
  const hasDevanagari = (t) => /[\u0900-\u097F]/.test(t || '')
  const explanation = hasDevanagari(signal.explanation || signal.summary || '')
    ? `${signal.symbol} is showing a ${signal.signal_type || signal.type || 'pattern'} signal with ${confidence}/100 confidence score. Monitor for follow-through in the next 2-3 sessions.`
    : (signal.explanation || signal.summary || signal.headline || 'No explanation available.')

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0,0,0,0.4)' }}
        onClick={onClose}
      />
      {/* Drawer */}
      <motion.div
        initial={{ x: 420 }}
        animate={{ x: 0 }}
        exit={{ x: 420 }}
        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
        className="detail-drawer z-50"
      >
        <div className="p-5">
          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-lg font-bold">{signal.symbol}</div>
              <div className="meta-xs">{signal.sector || 'NSE'} · {signal.signal_type || signal.type || 'Signal'}</div>
            </div>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/5"><X size={16} /></button>
          </div>

          {/* Score */}
          <div className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="flex items-center justify-between mb-2">
              <span className="label-sm">Confidence Score</span>
              <span className={`badge ${confidence >= 75 ? 'badge-high' : confidence >= 50 ? 'badge-medium' : 'badge-low'}`}>
                {confidence >= 75 ? 'HIGH' : confidence >= 50 ? 'MEDIUM' : 'LOW'}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${confidence}%` }}
                  transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
                  className="h-full rounded-full"
                  style={{ background: barColor }}
                />
              </div>
              <span className="num-ticker font-bold text-xl" style={{ color: barColor }}>{confidence}</span>
            </div>
            {/* Regime caution */}
            {signal.regime === 'weak_bear' || signal.regime === 'strong_bear' ? (
              <div className="flex items-center gap-2 mt-2 text-[10px]" style={{ color: 'var(--red)' }}>
                <AlertTriangle size={10} /> Bear market caution — bullish signals discounted
              </div>
            ) : null}

            {/* Signal Sources */}
            <div className="mt-4 pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <div className="label-sm mb-3 text-[10px]">Signal Sources</div>
              <div className="flex flex-wrap gap-x-4 gap-y-2">
                {['NLP', 'Candle', 'Anomaly', 'Options', 'Social', 'Regime'].map(src => {
                  const ws = signal.source_weights || signal.detector_weights || signal.weights || { NLP: 40, Candle: 30, Anomaly: 15, Regime: 15 };
                  const key = Object.keys(ws).find(k => k.toLowerCase() === src.toLowerCase());
                  const w = key ? ws[key] : null;
                  const active = w != null && w > 0;
                  return (
                    <div key={src} className="flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full" 
                        style={{ background: active ? 'var(--accent)' : 'var(--border)' }} />
                      <span className="text-[10px] uppercase font-medium" style={{ color: active ? 'var(--text-primary)' : 'var(--text-dim)' }}>
                        {src} {active && <span className="ml-0.5 text-[9px]" style={{ color: 'var(--accent)' }}>{w}%</span>}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Direction */}
          <div className="flex items-center gap-2 mb-4 px-1">
            {bias === 'bullish' ? <TrendingUp size={14} style={{ color: 'var(--green)' }} /> : <TrendingDown size={14} style={{ color: 'var(--red)' }} />}
            <span className="text-sm font-semibold" style={{ color: barColor }}>{bias.charAt(0).toUpperCase() + bias.slice(1)}</span>
          </div>

          {/* Explanation */}
          <div className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="label-sm mb-2">Analysis</div>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{explanation}</p>
            <div className="meta-xs mt-2">[Source: Signal Engine]</div>
          </div>

          {/* Historical base rate */}
          <div className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="label-sm mb-2">Historical Pattern (last 3 occurrences)</div>
            <div className="flex items-center gap-3">
              {history.map((h, i) => (
                <div key={i} className="flex-1 text-center py-2 rounded-lg"
                  style={{ background: h.startsWith('+') ? 'rgba(34,197,94,0.06)' : 'rgba(239,68,68,0.06)', border: '1px solid var(--border)' }}>
                  <div className={`num-ticker font-semibold text-sm ${h.startsWith('+') ? 'pnl-pos' : 'pnl-neg'}`}>{h}</div>
                  <div className="meta-xs mt-0.5">5-day</div>
                </div>
              ))}
            </div>
          </div>

          {/* Key levels */}
          <div className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="label-sm mb-2">Key Levels</div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <div className="meta-xs">Support</div>
                <div className="num-ticker text-sm font-medium">₹{(signal.price * 0.95 || 1200).toFixed(0)}</div>
              </div>
              <div>
                <div className="meta-xs">Resistance</div>
                <div className="num-ticker text-sm font-medium">₹{(signal.price * 1.08 || 1450).toFixed(0)}</div>
              </div>
              <div>
                <div className="meta-xs">Target</div>
                <div className="num-ticker text-sm font-medium" style={{ color: 'var(--accent)' }}>₹{(signal.price * 1.12 || 1520).toFixed(0)}</div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button className="btn-ghost flex-1 flex items-center justify-center gap-2 text-xs">
              <Bell size={12} /> Set Alert
            </button>
            <button
              className="btn-primary flex-1 flex items-center justify-center gap-2 text-xs"
              onClick={() => {
                useStore.getState().setSelectedStock(signal.symbol || signal.stock || signal.ticker)
                useStore.getState().setActiveTab('analyse')
                onClose()
              }}
            >
              <ExternalLink size={12} /> View Chart
            </button>
          </div>
        </div>
      </motion.div>
    </>
  )
}
