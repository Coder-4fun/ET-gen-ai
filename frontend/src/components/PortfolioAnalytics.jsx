import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line
} from 'recharts'
import { TrendingUp, PieChart as PieChartIcon, Award, Target, BarChart3, Activity } from 'lucide-react'
import useStore from '../store/useStore'

const SECTOR_COLORS = {
  Banking:        '#6366f1',
  IT:             '#06b6d4',
  Energy:         '#f59e0b',
  Auto:           '#10b981',
  NBFC:           '#ec4899',
  Pharma:         '#8b5cf6',
  Consumer:       '#f43f5e',
  FMCG:           '#14b8a6',
  Telecom:        '#f97316',
  Infrastructure: '#0ea5e9',
  Utilities:      '#84cc16',
  Power:          '#eab308',
  Unknown:        '#64748b',
}

function DonutChart({ data }) {
  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <div className="relative" style={{ width: 200, height: 200, margin: '0 auto' }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%" cy="50%"
            innerRadius={55} outerRadius={85}
            paddingAngle={3}
            dataKey="value"
            strokeWidth={0}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} style={{ filter: `drop-shadow(0 0 6px ${entry.color}40)` }} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: '#1a1d27', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8, fontSize: 12, color: '#e2e8f0',
            }}
            formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Value']}
          />
        </PieChart>
      </ResponsiveContainer>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Total</div>
        <div className="font-bold text-base num-ticker" style={{ color: 'var(--text-primary)' }}>
          ₹{(total / 1000).toFixed(0)}K
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, sub, color }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass rounded-xl px-4 py-3"
    >
      <div className="flex items-center gap-2 mb-1.5">
        <div className="w-6 h-6 rounded-lg flex items-center justify-center"
          style={{ background: `${color}15` }}>
          <Icon size={12} style={{ color }} />
        </div>
        <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{label}</span>
      </div>
      <div className="font-bold text-lg num-ticker" style={{ color }}>{value}</div>
      {sub && <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>{sub}</div>}
    </motion.div>
  )
}

export default function PortfolioAnalytics() {
  const { portfolio } = useStore()

  const analytics = useMemo(() => {
    if (!portfolio?.holdings?.length) return null

    const holdings = portfolio.holdings
    const summary = portfolio.summary || {}

    // Sector allocation
    const sectorMap = {}
    holdings.forEach(h => {
      const sector = h.sector || 'Unknown'
      if (!sectorMap[sector]) sectorMap[sector] = { value: 0, count: 0, pnl: 0 }
      sectorMap[sector].value += h.current_value || (h.qty * (h.current_price || h.avg_buy_price))
      sectorMap[sector].count += 1
      sectorMap[sector].pnl += h.unrealized_pnl || 0
    })

    const sectorData = Object.entries(sectorMap)
      .map(([sector, data]) => ({
        name: sector,
        value: Math.round(data.value),
        count: data.count,
        pnl: Math.round(data.pnl),
        color: SECTOR_COLORS[sector] || '#64748b',
      }))
      .sort((a, b) => b.value - a.value)

    const totalValue = sectorData.reduce((s, d) => s + d.value, 0)

    // Performance by stock (for bar chart)
    const stockPerf = holdings
      .map(h => ({
        stock: h.stock?.split(' ')[0] ?? h.stock,
        pnl_pct: h.pnl_percent || 0,
        color: (h.pnl_percent || 0) >= 0 ? '#10b981' : '#f43f5e',
      }))
      .sort((a, b) => b.pnl_pct - a.pnl_pct)

    // XIRR approximation (simplified for mock)
    const xirrApprox = (summary.total_pnl_percent || 0) * 1.15 // Annualized rough

    // Diversification score (0-100)
    const sectorCount = Object.keys(sectorMap).length
    const maxAllocation = Math.max(...sectorData.map(s => s.value / totalValue))
    const diversificationScore = Math.round(
      ((sectorCount / 10) * 50) + ((1 - maxAllocation) * 50)
    )

    // Best & worst performers
    const sorted = [...holdings].sort((a, b) => (b.pnl_percent || 0) - (a.pnl_percent || 0))
    const bestPerformer = sorted[0]
    const worstPerformer = sorted[sorted.length - 1]

    return {
      sectorData,
      totalValue,
      stockPerf,
      xirrApprox,
      diversificationScore,
      bestPerformer,
      worstPerformer,
      summary,
      holdingsCount: holdings.length,
      sectorCount,
    }
  }, [portfolio])

  if (!analytics) {
    return (
      <div className="p-5 flex flex-col gap-3">
        {[...Array(6)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
      </div>
    )
  }

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-5">
        <h2 className="text-lg font-bold text-gradient flex items-center gap-2">
          <PieChartIcon size={18} /> Portfolio Analytics
        </h2>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
          360° portfolio analysis · Sector allocation · Performance benchmarking
        </p>
      </div>

      {/* Key Metrics */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <MetricCard icon={TrendingUp} label="XIRR (Est.)" color="#10b981"
          value={`${analytics.xirrApprox >= 0 ? '+' : ''}${analytics.xirrApprox.toFixed(1)}%`}
          sub="Annualized return" />
        <MetricCard icon={Target} label="Diversification" color="#6366f1"
          value={`${analytics.diversificationScore}/100`}
          sub={`${analytics.sectorCount} sectors`} />
        <MetricCard icon={Award} label="Best Performer" color="#10b981"
          value={analytics.bestPerformer?.stock?.split(' ')[0] ?? '—'}
          sub={`${(analytics.bestPerformer?.pnl_percent || 0) >= 0 ? '+' : ''}${(analytics.bestPerformer?.pnl_percent || 0).toFixed(1)}%`} />
        <MetricCard icon={Activity} label="Holdings" color="#06b6d4"
          value={analytics.holdingsCount}
          sub={`₹${(analytics.totalValue / 100000).toFixed(1)}L total`} />
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        {/* Sector Allocation Donut */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <PieChartIcon size={14} style={{ color: 'var(--accent-indigo)' }} />
            <span className="font-semibold text-sm">Sector Allocation</span>
          </div>
          <DonutChart data={analytics.sectorData} />

          {/* Legend */}
          <div className="mt-4 grid grid-cols-2 gap-2">
            {analytics.sectorData.map(sector => (
              <div key={sector.name} className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: sector.color }} />
                <span className="text-[11px] truncate flex-1" style={{ color: 'var(--text-secondary)' }}>
                  {sector.name}
                </span>
                <span className="text-[10px] num-ticker font-medium" style={{ color: 'var(--text-muted)' }}>
                  {((sector.value / analytics.totalValue) * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Stock P&L Performance */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}
          className="glass rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={14} style={{ color: 'var(--accent-cyan)' }} />
            <span className="font-semibold text-sm">Stock Performance</span>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={analytics.stockPerf} layout="vertical"
              margin={{ left: 0, right: 10, top: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis type="number" tick={{ fill: '#4a5578', fontSize: 10 }}
                axisLine={false} tickLine={false}
                tickFormatter={v => `${v.toFixed(0)}%`} />
              <YAxis type="category" dataKey="stock" width={65}
                tick={{ fill: '#8892b0', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: '#1a1d27', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8, fontSize: 12, color: '#e2e8f0',
                }}
                formatter={(value) => [`${value >= 0 ? '+' : ''}${value.toFixed(2)}%`, 'P&L']}
              />
              <Bar dataKey="pnl_pct" radius={[0, 4, 4, 0]}>
                {analytics.stockPerf.map((entry, i) => (
                  <Cell key={i} fill={entry.color} fillOpacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Sector Detail Table */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
        className="glass rounded-2xl overflow-hidden">
        <div className="px-5 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <span className="font-semibold text-sm">Sector Breakdown</span>
        </div>
        <table className="data-table w-full">
          <thead><tr>
            <th>Sector</th><th className="text-right">Stocks</th>
            <th className="text-right">Value</th><th className="text-right">Allocation</th>
            <th className="text-right">P&L</th>
          </tr></thead>
          <tbody>
            {analytics.sectorData.map((sector, i) => {
              const pnlPos = sector.pnl >= 0
              return (
                <motion.tr key={sector.name}
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.04 }} className="table-row-hover">
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background: sector.color }} />
                      <span className="font-semibold text-xs">{sector.name}</span>
                    </div>
                  </td>
                  <td className="text-right num-ticker text-xs">{sector.count}</td>
                  <td className="text-right num-ticker text-xs">
                    ₹{sector.value.toLocaleString('en-IN')}
                  </td>
                  <td className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                        <div className="h-full rounded-full"
                          style={{
                            width: `${(sector.value / analytics.totalValue) * 100}%`,
                            background: sector.color,
                          }} />
                      </div>
                      <span className="num-ticker text-xs" style={{ color: sector.color }}>
                        {((sector.value / analytics.totalValue) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className={`text-right num-ticker text-xs font-semibold ${pnlPos ? 'pnl-pos' : 'pnl-neg'}`}>
                    {pnlPos ? '+' : ''}₹{Math.abs(sector.pnl).toLocaleString('en-IN')}
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </motion.div>
    </div>
  )
}
