import React, { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import useStore from '../store/useStore'

// Inner component allows each alert to manage its own 8-second timeout independently
function AlertItem({ alert, dismiss }) {
  useEffect(() => {
    const timer = setTimeout(() => dismiss(alert.id), 8000)
    return () => clearTimeout(timer)
  }, [alert.id, dismiss])

  // Guard against Hindi/Devanagari text
  const hasDevanagari = (text) => /[\u0900-\u097F]/.test(text || '')
  const getSafeText = (s) => {
    const explanation = s.explanation || s.summary || s.headline || ''
    if (hasDevanagari(explanation)) {
      return `${s.symbol || s.stock || 'Asset'} signal detected — check Radar for details.`
    }
    return explanation
  }

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0, x: 40 }}
      transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
      className="flex items-center gap-3 px-5 py-2.5 overflow-hidden"
      style={{ borderBottom: '1px solid var(--border)' }}
    >
      {/* bias bar */}
      <div className="w-1 h-4 rounded-full flex-shrink-0" style={{
        background: (alert.directional_bias || alert.bias || alert.signal?.includes('Bullish') ? 'bullish' : 'bearish') === 'bullish' ? 'var(--green)' : 'var(--red)'
      }} />
      <span className="text-xs font-semibold flex-shrink-0" style={{ color: 'var(--accent)' }}>{alert.symbol || alert.stock}</span>
      <span className="text-xs truncate flex-1" style={{ color: 'var(--text-secondary)' }}>
        {getSafeText(alert)}
      </span>
      <span className="badge badge-mock text-[9px] flex-shrink-0">
        {alert._isMock || !alert.live ? 'MOCK' : 'LIVE'}
      </span>
      <button
        onClick={() => dismiss(alert.id)}
        className="p-1 rounded hover:bg-white/5 transition-colors flex-shrink-0"
      >
        <X size={12} style={{ color: 'var(--text-dim)' }} />
      </button>
    </motion.div>
  )
}

export default function LiveAlertBanner() {
  const { liveAlerts, dismissLiveAlert } = useStore()

  if (!liveAlerts || liveAlerts.length === 0) return null

  return (
    <div className="alert-banner">
      <AnimatePresence>
        {liveAlerts.map((alert) => (
          <AlertItem key={alert.id || alert._alertId} alert={alert} dismiss={dismissLiveAlert} />
        ))}
      </AnimatePresence>
    </div>
  )
}
