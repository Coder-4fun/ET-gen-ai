import React from 'react'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, CartesianGrid, ReferenceLine
} from 'recharts'
import useStore from '../store/useStore'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass rounded-xl px-3 py-2 text-xs" style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
      <div className="font-semibold mb-1">{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</div>
      ))}
    </div>
  )
}

export default function BacktestView() {
  const { backtestResults } = useStore()

  if (!backtestResults?.length) {
    return <div className="p-5 flex flex-col gap-3">{[...Array(5)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}</div>
  }

  const sorted = [...backtestResults].sort((a, b) => b.win_rate - a.win_rate)
  const equityData = backtestResults[0]?.equity_curve ?? []

  return (
    <div className="p-5 flex flex-col gap-4">
      {/* Win rate bar chart */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-4">
        <div className="font-semibold text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>Win Rate by Signal Type</div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={sorted} layout="vertical" margin={{ left: 20 }}>
            <XAxis type="number" domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`}
              tick={{ fontSize: 10, fill: '#4a5578' }} />
            <YAxis type="category" dataKey="signal_type" tick={{ fontSize: 10, fill: '#8892b0' }} width={130} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="win_rate" radius={[0, 4, 4, 0]}>
              {sorted.map((entry) => (
                <Cell key={entry.signal_type}
                  fill={entry.win_rate >= 0.65 ? '#10b981' : entry.win_rate >= 0.55 ? '#f59e0b' : '#f43f5e'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Equity curve */}
      {equityData.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-4">
          <div className="font-semibold text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
            Equity Curve — {backtestResults[0]?.signal_type}
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={equityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#4a5578' }} />
              <YAxis tick={{ fontSize: 10, fill: '#4a5578' }} domain={['auto', 'auto']} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={100} stroke="rgba(255,255,255,0.15)" strokeDasharray="4 2" />
              <Line type="monotone" dataKey="equity" stroke="#6366f1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Stats table */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
        className="glass rounded-2xl overflow-hidden">
        <div className="px-5 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <span className="font-semibold text-sm">Signal Performance Summary</span>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr>
              <th>Signal Type</th>
              <th className="text-right">Win Rate</th>
              <th className="text-right">Avg Return</th>
              <th className="text-right">Sharpe</th>
              <th className="text-right">Max DD</th>
              <th className="text-right">Signals</th>
            </tr></thead>
            <tbody>
              {sorted.map((r, i) => {
                const wr = (r.win_rate * 100).toFixed(1)
                const wrColor = r.win_rate >= 0.65 ? '#10b981' : r.win_rate >= 0.55 ? '#f59e0b' : '#f43f5e'
                return (
                  <motion.tr key={r.signal_type}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }} className="table-row-hover">
                    <td className="font-medium text-xs">{r.signal_type}</td>
                    <td className="text-right num-ticker font-bold" style={{ color: wrColor }}>{wr}%</td>
                    <td className={`text-right num-ticker text-xs ${r.avg_return >= 0 ? 'pnl-pos' : 'pnl-neg'}`}>
                      {r.avg_return >= 0 ? '+' : ''}{r.avg_return?.toFixed(2)}%
                    </td>
                    <td className="text-right num-ticker text-xs">{r.sharpe_ratio?.toFixed(2)}</td>
                    <td className="text-right num-ticker text-xs pnl-neg">{r.max_drawdown?.toFixed(1)}%</td>
                    <td className="text-right num-ticker text-xs" style={{ color: 'var(--text-muted)' }}>{r.total_signals}</td>
                  </motion.tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  )
}
