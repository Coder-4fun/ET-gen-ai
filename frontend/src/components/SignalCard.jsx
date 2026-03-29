import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle } from 'lucide-react'
import useStore, { inferBias } from '../store/useStore'

export default function SignalCard({ signal, index = 0, compact = false }) {
  const { setSelectedSignal, regime, backtestResults } = useStore()

  const conf = signal.confidence_score ?? Math.round((signal.confidence ?? 0) * (signal.confidence <= 1 ? 100 : 1))
  const bias = inferBias(signal)
  const barColor = bias === 'bullish' ? 'var(--green)' : bias === 'bearish' ? 'var(--red)' : 'var(--text-muted)'
  const signalType = signal.signal_type || signal.type || signal.signal || 'Signal'
  const symbol = signal.symbol || signal.stock || signal.ticker || '—'
  const headline = signal.headline || signal.explanation || signal.summary || ''
  const sector = signal.sector || ''
  const isMock = signal._isMock || signal.is_mock
  const isBearRegime = regime?.regime === 'weak_bear' || regime?.regime === 'strong_bear'

  // Truncate headline
  const shortHeadline = headline.length > 90 ? headline.slice(0, 87) + '…' : headline

  const date = signal.date || signal.detected_at || signal.created_at
  const dateStr = date ? new Date(date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.04, ease: [0.23, 1, 0.32, 1] }}
      onClick={() => setSelectedSignal(signal)}
      className="signal-card-terminal"
      style={{ cursor: 'pointer' }}
    >
      {/* Left color bar */}
      <div className="signal-card-bar" style={{ background: barColor }} />

      {/* Body */}
      <div className="signal-card-body">
        {/* Row 1: Symbol, Type pill, Score bar, Date */}
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-sm font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
            {symbol}
          </span>
          <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide"
            style={{ background: `${barColor}15`, color: barColor, border: `1px solid ${barColor}25` }}>
            {signalType}
          </span>
          {/* Score bar */}
          <div className="flex items-center gap-1.5 ml-auto">
            <div className="w-16 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <motion.div
                className="h-full rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${conf}%` }}
                transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
                style={{ background: barColor }}
              />
            </div>
            <span className="num-ticker text-[11px] font-semibold" style={{ color: barColor, minWidth: 18 }}>{conf}</span>
          </div>
          {dateStr && (
            <span className="meta-xs num-ticker ml-1">{dateStr}</span>
          )}
        </div>

        {/* Row 2: Headline */}
        {shortHeadline && (
          <div className="text-[12px] font-medium leading-snug mb-1" style={{ color: 'var(--text-secondary)' }}>
            {shortHeadline}
          </div>
        )}

        {/* Row 3: Price / sector / badges */}
        <div className="flex items-center gap-3 flex-wrap">
          {signal.price && (
            <span className="num-ticker text-[11px] font-semibold" style={{ color: 'var(--accent)' }}>
              ₹{Number(signal.price).toLocaleString('en-IN')}
            </span>
          )}
          {(() => {
            const bt = backtestResults?.find(b => b.signal_type === signalType || b.signal_type === signal.signal_type);
            if (bt?.win_rate != null) {
              return (
                <span className="text-[10px]" style={{ color: 'var(--text-dim)' }}>
                  🎯 {Math.round(bt.win_rate > 1 ? bt.win_rate : bt.win_rate * 100)}% win
                </span>
              );
            }
            return (
              <span className="text-[10px]" style={{ color: 'var(--text-dim)' }}>
                🎯 No backtest data
              </span>
            );
          })()}
          <div className="flex items-center gap-1.5 ml-auto">
            {isMock && <span className="badge badge-mock text-[8px]">MOCK</span>}
            {!isMock && signal.live && <span className="badge text-[8px]" style={{ background: 'rgba(255,59,48,0.12)', color: 'var(--live-red)' }}>LIVE</span>}
            {sector && <span className="meta-xs">{sector}</span>}
          </div>
        </div>

        {/* Regime caution */}
        {(regime?.regime === 'weak_bear' || regime?.regime === 'strong_bear') && bias === 'bullish' && (
          <div className="flex items-center gap-1 mt-1.5 text-[9px]" style={{ color: '#F59E0B' }}>
            <AlertTriangle size={9} /> Bear market regime — reduce position sizing
          </div>
        )}
        {(regime?.regime === 'strong_bull' || regime?.regime === 'bullish') && bias === 'bearish' && (
          <div className="flex items-center gap-1 mt-1.5 text-[9px]" style={{ color: '#F59E0B' }}>
            <AlertTriangle size={9} /> Bull market — counter-trend signal, lower conviction
          </div>
        )}
      </div>
    </motion.div>
  )
}
