import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'
import useStore from '../store/useStore'

export default function SectorHeatmap() {
  const { heatmapData, signals, setSelectedSector } = useStore()
  const [hovered, setHovered] = useState(null)
  const [localData, setLocalData] = useState(null)

  useEffect(() => {
    if (heatmapData) setLocalData(heatmapData)
  }, [heatmapData])

  // Animate values jitter
  useEffect(() => {
    if (!localData) return
    const t = setInterval(() => {
      setLocalData(prev => ({
        ...prev,
        nifty_change: parseFloat((prev.nifty_change + (Math.random() - 0.5) * 0.05).toFixed(2)),
        sensex_change: parseFloat((prev.sensex_change + (Math.random() - 0.5) * 0.05).toFixed(2)),
        sectors: prev.sectors.map(s => ({
          ...s,
          change_pct: parseFloat((s.change_pct + (Math.random() - 0.5) * 0.04).toFixed(2)),
        })),
      }))
    }, 5000)
    return () => clearInterval(t)
  }, [!!localData])

  if (!localData) {
    return (
      <div className="p-5 grid gap-3" style={{ gridTemplateColumns: 'repeat(4,1fr)' }}>
        {[...Array(12)].map((_, i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
      </div>
    )
  }

  const { sectors, nifty_change, sensex_change } = localData

  const bgForPct = (pct) => {
    if (pct >= 2)    return '#0d3320'
    if (pct >= 1)    return '#0a2a1a'
    if (pct >= 0.3)  return '#071e13'
    if (pct >= -0.3) return '#181b2a'
    if (pct >= -1)   return '#2a0e0e'
    if (pct >= -2)   return '#321010'
    return '#3d0e0e'
  }
  const borderForPct = (pct) => pct >= 0.3 ? 'rgba(16,185,129,0.25)' : pct <= -0.3 ? 'rgba(244,63,94,0.25)' : 'rgba(255,255,255,0.05)'
  const textForPct   = (pct) => pct >= 0 ? '#10b981' : '#f43f5e'

  return (
    <div className="p-5 flex flex-col gap-4">
      {/* Index overview */}
      <motion.div
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-3 gap-3"
      >
        {[
          { label: 'NIFTY 50',    value: (22184.50 + nifty_change * 20).toFixed(2), change: nifty_change },
          { label: 'SENSEX',      value: (73412.43 + sensex_change * 30).toFixed(2), change: sensex_change },
          { label: 'Active Signals', value: signals.length, change: null, isCount: true },
        ].map(({ label, value, change, isCount }) => (
          <div key={label} className="glass rounded-xl px-4 py-3">
            <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>{label}</div>
            <div className="font-bold text-lg num-ticker" style={{ color: change != null ? textForPct(change) : 'var(--accent-indigo)' }}>
              {isCount ? value : `₹${parseFloat(value).toLocaleString('en-IN')}`}
            </div>
            {change != null && (
              <div className="flex items-center gap-1 mt-0.5">
                {change >= 0 ? <TrendingUp size={11} style={{ color: '#10b981' }} /> : <TrendingDown size={11} style={{ color: '#f43f5e' }} />}
                <span className="text-xs num-ticker" style={{ color: textForPct(change) }}>
                  {change >= 0 ? '+' : ''}{change.toFixed(2)}%
                </span>
              </div>
            )}
          </div>
        ))}
      </motion.div>

      {/* Heatmap grid */}
      <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))' }}>
        {sectors.map((sector, i) => {
          const pct = sector.change_pct
          const isHovered = hovered === sector.sector
          const sigCount = signals.filter(s => sector.stocks?.some(st => st.stock === s.stock)).length || sector.signal_count
          return (
            <motion.div
              key={sector.sector}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.04, duration: 0.35 }}
              whileHover={{ scale: 1.04, zIndex: 10 }}
              onHoverStart={() => setHovered(sector.sector)}
              onHoverEnd={() => setHovered(null)}
              onClick={() => setSelectedSector(sector.sector)}
              className="heatmap-cell p-3 rounded-xl"
              style={{
                background: bgForPct(pct),
                border: `1px solid ${borderForPct(pct)}`,
                minHeight: 90,
                cursor: 'pointer',
              }}
            >
              <div className="font-semibold text-xs mb-1 leading-tight" style={{ color: 'rgba(255,255,255,0.9)' }}>
                {sector.sector}
              </div>
              <motion.div
                key={pct.toFixed(2)}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="font-bold text-lg num-ticker leading-tight"
                style={{ color: textForPct(pct) }}
              >
                {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
              </motion.div>
              {sigCount > 0 && (
                <div className="flex items-center gap-1 mt-1.5">
                  <Activity size={9} style={{ color: 'rgba(255,255,255,0.4)' }} />
                  <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.4)' }}>{sigCount} signal{sigCount !== 1 ? 's' : ''}</span>
                </div>
              )}
              {isHovered && sector.top_stock && (
                <motion.div
                  initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                  className="text-[10px] mt-1 truncate" style={{ color: 'rgba(255,255,255,0.5)' }}
                >
                  📈 {sector.top_stock}
                </motion.div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
