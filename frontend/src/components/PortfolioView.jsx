import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Activity, AlertCircle, ShieldAlert, PieChart } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'
import useStore from '../store/useStore'
import PortfolioAnalytics from './PortfolioAnalytics'

function Sparkline({ data, positive }) {
  const pts = (data ?? []).map((v, i) => ({ v }))
  return (
    <ResponsiveContainer width={80} height={32}>
      <LineChart data={pts}>
        <Line type="monotone" dataKey="v" stroke={positive ? '#10b981' : '#f43f5e'}
          strokeWidth={1.5} dot={false} />
        <Tooltip contentStyle={{ display: 'none' }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

function RiskSummary({ holdings }) {
  const total = holdings.reduce((sum, h) => sum + (h.current_value || 0), 0)
  if (total === 0) return null

  const top = holdings.reduce((a, b) => ((a.current_value || 0) > (b.current_value || 0) ? a : b), holdings[0])
  const pct = ((top.current_value || 0) / total) * 100
  const isDanger = pct > 35
  const color = isDanger ? 'var(--red)' : 'var(--accent)'
  
  return (
    <div className="glass rounded-xl p-4 mb-2">
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-sm">Risk Summary</span>
        {isDanger && (
          <span className="text-[10px] font-semibold" style={{ color: 'var(--red)' }}>
            Concentration risk: {top.stock} is {pct.toFixed(1)}% of your portfolio
          </span>
        )}
      </div>
      <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <motion.div
          className="h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8 }}
          style={{ background: color }}
        />
      </div>
    </div>
  )
}

export default function PortfolioView() {
  const { portfolio } = useStore()

  if (!portfolio) {
    return (
      <div className="p-5 flex flex-col gap-3">
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
      </div>
    )
  }

  const { holdings = [], summary = {} } = portfolio
  const pnlPos = summary.total_pnl >= 0

  return (
    <div className="p-5 flex flex-col gap-4">
      {/* Summary bento */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Invested',     value: `₹${(summary.total_invested ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, color: 'var(--accent-indigo)' },
          { label: 'Current Value', value: `₹${(summary.total_current_value ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, color: '#a5b4fc' },
          { label: 'Total P&L',    value: `${pnlPos ? '+' : ''}₹${Math.abs(summary.total_pnl ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, color: pnlPos ? '#10b981' : '#f43f5e', badge: `${summary.total_pnl_percent >= 0 ? '+' : ''}${(summary.total_pnl_percent ?? 0).toFixed(2)}%` },
          { label: 'Active Signals', value: summary.active_signals_count ?? 0, color: 'var(--accent-amber)' },
        ].map(({ label, value, color, badge }) => (
          <div key={label} className="glass rounded-xl px-4 py-3">
            <div className="text-[11px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{label}</div>
            <div className="font-bold text-lg num-ticker mt-1" style={{ color }}>{value}</div>
            {badge && <div className="text-xs num-ticker mt-0.5" style={{ color }}>{badge}</div>}
          </div>
        ))}
      </motion.div>

      {/* Holdings table */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}
        className="glass rounded-2xl overflow-hidden">
        <div className="px-5 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <span className="font-semibold text-sm">Holdings</span>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead>
              <tr>
                <th>Stock</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Avg Price</th>
                <th className="text-right">LTP</th>
                <th className="text-right">P&amp;L</th>
                <th className="text-right">Return</th>
                <th className="text-right">Day Chg</th>
                <th>Trend</th>
                <th className="text-center">Signals</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h, i) => {
                const pos = h.unrealized_pnl >= 0
                return (
                  <motion.tr key={h.stock}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className="table-row-hover"
                  >
                    <td>
                      <div className="font-bold text-sm">{h.stock}</div>
                      <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{h.sector}</div>
                    </td>
                    <td className="text-right num-ticker text-sm">{h.qty}</td>
                    <td className="text-right num-ticker text-sm">₹{h.avg_buy_price?.toLocaleString('en-IN')}</td>
                    <td className="text-right num-ticker font-semibold">₹{h.current_price?.toLocaleString('en-IN')}</td>
                    <td className={`text-right num-ticker font-semibold ${pos ? 'pnl-pos' : 'pnl-neg'}`}>
                      {pos ? '+' : ''}₹{Math.abs(h.unrealized_pnl ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </td>
                    <td className={`text-right num-ticker text-xs ${pos ? 'pnl-pos' : 'pnl-neg'}`}>
                      {pos ? '+' : ''}{(h.pnl_percent ?? 0).toFixed(2)}%
                    </td>
                    <td className={`text-right num-ticker text-xs ${h.day_change_percent >= 0 ? 'pnl-pos' : 'pnl-neg'}`}>
                      {h.day_change_percent >= 0 ? '+' : ''}{(h.day_change_percent ?? 0).toFixed(2)}%
                    </td>
                    <td><Sparkline data={h.sparkline} positive={pos} /></td>
                    <td className="text-center">
                      {h.active_signals > 0 ? (
                        <span className="badge badge-brand">{h.active_signals}</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>—</span>
                      )}
                    </td>
                  </motion.tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Risk Analytics Section */}
      {holdings.length > 0 && (
        <>
          <RiskSummary holdings={holdings} />
          <PortfolioAnalytics />
        </>
      )}
    </div>
  )
}

