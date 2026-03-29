import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Globe, RefreshCw, Filter, Building2, TrendingUp, AlertTriangle, ShieldCheck, Users, Zap } from 'lucide-react'

const API = '/api'

const EVENT_ICONS = {
  PromoterBuy:      <TrendingUp size={14} />,
  BulkDeal:         <Zap size={14} />,
  FIIAccumulation:  <Globe size={14} />,
  EarningsSurprise: <BarChart size={14} />,
  InsiderTrade:     <Users size={14} />,
  DIIBuying:        <Building2 size={14} />,
  RegulatoryApproval: <ShieldCheck size={14} />,
  BlockDeal:        <AlertTriangle size={14} />,
}

const EVENT_TYPE_LABELS = {
  PromoterBuy:        'Promoter Buy',
  BulkDeal:           'Bulk Deal',
  FIIAccumulation:    'FII Accumulation',
  EarningsSurprise:   'Earnings Surprise',
  InsiderTrade:       'Insider Trade',
  DIIBuying:          'DII Buying',
  RegulatoryApproval: 'Regulatory',
  BlockDeal:          'Block Deal',
}

const IMPACT_COLORS = {
  'Strongly Bullish': '#10b981',
  'Bullish':          '#06b6d4',
  'Neutral':          '#94a3b8',
  'Cautionary':       '#f43f5e',
}

const CustomFIITooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg px-3 py-2 text-xs" style={{ background: 'rgba(15,20,40,0.97)', border: '1px solid rgba(255,255,255,0.12)' }}>
      <div className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} className="flex gap-2">
          <span style={{ color: p.fill }}>{p.name}:</span>
          <span className="num-ticker" style={{ color: 'var(--text-secondary)' }}>
            {p.value >= 0 ? '+' : ''}₹{Math.abs(p.value).toLocaleString()} Cr
          </span>
        </div>
      ))}
    </div>
  )
}

function RadarEventCard({ event, delay }) {
  const [expanded, setExpanded] = useState(false)
  const impactColor = IMPACT_COLORS[event.impact] ?? '#94a3b8'
  const icon = EVENT_ICONS[event.type] ?? <Zap size={14} />

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.35 }}
      className="card cursor-pointer"
      style={{
        borderLeft: `3px solid ${event.color}`,
        background: expanded ? `${event.color}0d` : undefined,
        transition: 'background 0.2s',
      }}
      onClick={() => setExpanded(e => !e)}
      whileHover={{ scale: 1.005 }}
    >
      <div className="flex items-start gap-3">
        {/* Type icon */}
        <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
          style={{ background: `${event.color}20`, color: event.color }}>
          {icon}
        </div>

        <div className="flex-1 min-w-0">
          {/* Badge row */}
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold"
              style={{ background: `${event.color}20`, color: event.color }}>
              {EVENT_TYPE_LABELS[event.type] ?? event.type}
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{ background: 'rgba(255,255,255,0.05)', color: impactColor }}>
              {event.impact}
            </span>
            <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{event.date}</span>
          </div>

          {/* Headline */}
          <div className="text-sm font-semibold mb-1 leading-snug" style={{ color: 'var(--text-primary)' }}>
            {event.headline}
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4 flex-wrap">
            <span className="text-xs font-bold num-ticker" style={{ color: event.color }}>{event.value}</span>
            <div className="flex items-center gap-1">
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Signal:</span>
              <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
                <motion.div className="h-full rounded-full" style={{ background: event.color }}
                  initial={{ width: 0 }} animate={{ width: `${event.signal_strength}%` }}
                  transition={{ duration: 0.8, delay: 0.2 }} />
              </div>
              <span className="text-[10px] num-ticker" style={{ color: event.color }}>{event.signal_strength}%</span>
            </div>
          </div>
        </div>

        {/* Stock */}
        <div className="text-right shrink-0">
          <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{event.stock}</div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{event.sector}</div>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="mt-3 pt-3 text-xs leading-relaxed"
          style={{ borderTop: '1px solid rgba(255,255,255,0.07)', color: 'var(--text-secondary)' }}>
          {event.detail}
          <div className="flex gap-4 mt-2">
            <span style={{ color: 'var(--text-muted)' }}>Historical success rate:
              <span className="num-ticker ml-1" style={{ color: event.color }}>{event.historical_success_rate}%</span>
            </span>
            <span style={{ color: 'var(--text-muted)' }}>Avg 90-day return:
              <span className={`num-ticker ml-1 ${event.avg_return_90d >= 0 ? 'pnl-pos' : 'pnl-neg'}`}>
                {event.avg_return_90d >= 0 ? '+' : ''}{event.avg_return_90d}%
              </span>
            </span>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default function OpportunityRadar() {
  const [events, setEvents]     = useState([])
  const [fiiFlow, setFiiFlow]   = useState(null)
  const [loading, setLoading]   = useState(true)
  const [filter, setFilter]     = useState('All')
  const [activeTab, setActiveTab] = useState('events')

  const load = async () => {
    setLoading(true)
    try {
      const [evtRes, fiiRes] = await Promise.allSettled([
        axios.get(`${API}/radar`),
        axios.get(`${API}/radar/fii-dii`),
      ])
      if (evtRes.status === 'fulfilled') setEvents(evtRes.value.data.events ?? [])
      if (fiiRes.status === 'fulfilled') setFiiFlow(fiiRes.value.data)
    } catch (e) {
      console.error('Radar load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const eventTypes = ['All', ...new Set(events.map(e => e.type))]
  const filtered = filter === 'All' ? events : events.filter(e => e.type === filter)

  const fiiChartData = fiiFlow?.flow?.map(d => ({
    date: d.date.slice(5),
    FII: d.fii_net,
    DII: d.dii_net,
  })) ?? []

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gradient">Opportunity Radar</h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Real-time corporate events · Institutional flows · Insider activity
          </p>
        </div>
        <button onClick={load} disabled={loading} className="btn-ghost p-2 rounded-lg">
          <motion.div animate={{ rotate: loading ? 360 : 0 }}
            transition={{ duration: 1, repeat: loading ? Infinity : 0, ease: 'linear' }}>
            <RefreshCw size={14} />
          </motion.div>
        </button>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 mb-5 p-1 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)', width: 'fit-content' }}>
        {[['events', 'Corporate Events'], ['fii', 'FII / DII Flow']].map(([id, label]) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className="px-4 py-1.5 rounded-lg text-xs font-medium transition-all"
            style={{
              background: activeTab === id ? 'rgba(99,102,241,0.25)' : 'transparent',
              color: activeTab === id ? '#a5b4fc' : 'var(--text-muted)',
            }}>
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'events' && (
        <>
          {/* Event type filter */}
          <div className="flex gap-2 flex-wrap mb-4">
            {eventTypes.map(t => (
              <button key={t} onClick={() => setFilter(t)}
                className="px-3 py-1 rounded-full text-[11px] font-medium transition-all"
                style={{
                  background: filter === t ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
                  border: `1px solid ${filter === t ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.08)'}`,
                  color: filter === t ? '#a5b4fc' : 'var(--text-muted)',
                }}>
                {EVENT_TYPE_LABELS[t] ?? t}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex flex-col gap-3">
              {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {filtered.map((event, i) => (
                <RadarEventCard key={event.id} event={event} delay={i * 0.05} />
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === 'fii' && fiiFlow && (
        <div>
          {/* Summary strip */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className="card text-center">
              <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>FII Net (10d)</div>
              <div className={`text-xl font-bold num-ticker ${fiiFlow.summary.fii_net_10d >= 0 ? 'pnl-pos' : 'pnl-neg'}`}>
                {fiiFlow.summary.fii_net_10d >= 0 ? '+' : ''}₹{fiiFlow.summary.fii_net_10d.toLocaleString()} Cr
              </div>
              <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{fiiFlow.summary.fii_trend}</div>
            </div>
            <div className="card text-center">
              <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>DII Net (10d)</div>
              <div className={`text-xl font-bold num-ticker ${fiiFlow.summary.dii_net_10d >= 0 ? 'pnl-pos' : 'pnl-neg'}`}>
                {fiiFlow.summary.dii_net_10d >= 0 ? '+' : ''}₹{fiiFlow.summary.dii_net_10d.toLocaleString()} Cr
              </div>
              <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{fiiFlow.summary.dii_trend}</div>
            </div>
          </div>

          {/* Chart */}
          <div className="card">
            <div className="text-xs font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>
              FII vs DII Net Activity (₹ Cr)
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={fiiChartData} barGap={4}>
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false}
                  tickFormatter={v => `${v >= 0 ? '+' : ''}${v}`} />
                <Tooltip content={<CustomFIITooltip />} />
                <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" />
                <Bar dataKey="FII" fill="#6366f1" radius={[3, 3, 0, 0]} />
                <Bar dataKey="DII" fill="#06b6d4" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="flex gap-4 mt-3 justify-center">
              {[['FII', '#6366f1'], ['DII', '#06b6d4']].map(([label, color]) => (
                <div key={label} className="flex items-center gap-1.5">
                  <div className="w-3 h-1.5 rounded" style={{ background: color }} />
                  <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
