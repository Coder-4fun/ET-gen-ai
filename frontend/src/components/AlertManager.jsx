import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bell, Mail, MessageSquare, Phone, Clock, CheckCircle, XCircle,
  Shield, TrendingUp, Calendar, Zap, Volume2, VolumeX, Send,
  Target, ChevronDown, Settings, BarChart3, AlertTriangle
} from 'lucide-react'
import axios from 'axios'
import useStore from '../store/useStore'

const API = '/api'

function Toggle({ on, onChange, color }) {
  return (
    <div
      className={`toggle-track ${on ? 'on' : ''}`}
      onClick={() => onChange(!on)}
      style={on ? { background: `rgba(${color || '99,102,241'},0.5)` } : {}}
    >
      <div className="toggle-thumb" />
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color, sub }) {
  return (
    <div className="glass rounded-xl px-4 py-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={13} style={{ color }} />
        <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{label}</span>
      </div>
      <div className="font-bold text-xl num-ticker" style={{ color }}>{value}</div>
      {sub && <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>{sub}</div>}
    </div>
  )
}

function ChannelCard({ icon: Icon, title, subtitle, enabled, onToggle, color, children, testChannel }) {
  const [testing, setTesting] = useState(false)

  const handleTest = async () => {
    setTesting(true)
    try { await axios.post(`${API}/alerts/test/${testChannel}`) }
    catch (e) { console.warn(e) }
    finally { setTimeout(() => setTesting(false), 2000) }
  }

  return (
    <motion.div
      layout
      className="rounded-xl p-4"
      style={{
        background: enabled ? `rgba(${color},0.06)` : 'rgba(255,255,255,0.02)',
        border: `1px solid ${enabled ? `rgba(${color},0.25)` : 'rgba(255,255,255,0.06)'}`,
        transition: 'all 0.3s ease',
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: `rgba(${color},${enabled ? '0.2' : '0.08'})` }}>
            <Icon size={15} style={{ color: `rgb(${color})` }} />
          </div>
          <div>
            <div className="text-sm font-semibold" style={{ color: enabled ? 'var(--text-primary)' : 'var(--text-muted)' }}>
              {title}
            </div>
            <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{subtitle}</div>
          </div>
        </div>
        <Toggle on={enabled} onChange={onToggle} color={color} />
      </div>
      <AnimatePresence>
        {enabled && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            {children}
            {testChannel && (
              <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <button onClick={handleTest} disabled={testing}
                  className="btn-ghost text-[11px] px-3 py-1.5 flex items-center gap-1.5">
                  <Send size={10} />
                  {testing ? '✓ Test Sent!' : `Send Test ${title.split(' ')[0]}`}
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function NotifCategory({ icon: Icon, label, desc, on, onChange, color }) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: `${color}15` }}>
          <Icon size={12} style={{ color }} />
        </div>
        <div>
          <div className="text-xs font-medium">{label}</div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{desc}</div>
        </div>
      </div>
      <Toggle on={on} onChange={onChange} />
    </div>
  )
}

export default function AlertManager() {
  const { alerts, alertConfig, setAlertConfig, setAlerts } = useStore()
  const [config, setConfig] = useState(alertConfig ?? {
    email_enabled: true, sms_enabled: false, whatsapp_enabled: false,
    email_address: '', sms_number: '', whatsapp_number: '',
    min_confidence: 0.75, watchlist: [], portfolio_alerts: true,
    notify_signals: true, notify_price_targets: true,
    notify_portfolio: true, notify_events: true, notify_market_movers: false,
    max_emails_per_day: 10, max_sms_per_day: 5, max_whatsapp_per_day: 3,
    quiet_hours_enabled: false, quiet_start: '22:00', quiet_end: '08:00',
  })
  const [saving, setSaving] = useState(false)
  const [stats, setStats] = useState(null)
  const [watchlistInput, setWatchlistInput] = useState('')
  const [activeSection, setActiveSection] = useState('channels')

  // Load stats + config on mount
  useEffect(() => {
    axios.get(`${API}/alerts/stats`).then(r => setStats(r.data)).catch(() => {})
    axios.get(`${API}/alerts/config`).then(r => {
      setConfig(c => ({ ...c, ...r.data }))
    }).catch(() => {})
    axios.get(`${API}/alerts`).then(r => {
      const { setAlerts } = useStore.getState()
      setAlerts(r.data)
    }).catch(() => {})
  }, [])

  const save = async () => {
    setSaving(true)
    try {
      await axios.post(`${API}/alerts/config`, config)
      setAlertConfig(config)
    } catch (e) { console.warn(e) }
    finally { setTimeout(() => setSaving(false), 600) }
  }

  const addWatch = () => {
    const s = watchlistInput.trim().toUpperCase()
    if (s && !config.watchlist.includes(s)) {
      setConfig(c => ({ ...c, watchlist: [...c.watchlist, s] }))
    }
    setWatchlistInput('')
  }

  const sections = [
    { id: 'channels', label: 'Channels', icon: Zap },
    { id: 'preferences', label: 'Preferences', icon: Settings },
    { id: 'history', label: 'History', icon: Clock },
  ]

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gradient flex items-center gap-2">
            <Bell size={18} /> Notification Center
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Groww-style multi-channel alerts · Email · SMS · WhatsApp
          </p>
        </div>
        <button onClick={save} className="btn-primary text-xs flex items-center gap-1.5" disabled={saving}>
          {saving ? (
            <><CheckCircle size={12} /> Saved!</>
          ) : (
            <><Shield size={12} /> Save Settings</>
          )}
        </button>
      </div>

      {/* Stats Row */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <StatCard icon={Bell} label="Total Alerts" value={stats?.total_alerts ?? 0}
          color="var(--accent-indigo)" sub="All time" />
        <StatCard icon={Mail} label="Emails Today" value={stats?.today_email ?? 0}
          color="#10b981" sub={`Max ${config.max_emails_per_day}/day`} />
        <StatCard icon={Phone} label="SMS Today" value={stats?.today_sms ?? 0}
          color="#06b6d4" sub={`Max ${config.max_sms_per_day}/day`} />
        <StatCard icon={MessageSquare} label="WhatsApp Today" value={stats?.today_whatsapp ?? 0}
          color="#25d366" sub={`Max ${config.max_whatsapp_per_day}/day`} />
      </motion.div>

      {/* Section Tabs */}
      <div className="flex gap-2 mb-5">
        {sections.map(sec => {
          const Icon = sec.icon
          const active = activeSection === sec.id
          return (
            <button key={sec.id} onClick={() => setActiveSection(sec.id)}
              className={`chip ${active ? 'active' : ''} text-xs flex items-center gap-1.5`}>
              <Icon size={12} /> {sec.label}
            </button>
          )
        })}
      </div>

      <AnimatePresence mode="wait">
        {/* ── CHANNELS SECTION ─────────────────────────────────────────── */}
        {activeSection === 'channels' && (
          <motion.div key="channels" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="flex flex-col gap-3 max-w-2xl">

            {/* Email Channel */}
            <ChannelCard
              icon={Mail} title="Email Alerts" subtitle="Rich HTML signal reports"
              enabled={config.email_enabled}
              onToggle={v => setConfig(c => ({ ...c, email_enabled: v }))}
              color="16,185,129" testChannel="email"
            >
              <input value={config.email_address}
                onChange={e => setConfig(c => ({ ...c, email_address: e.target.value }))}
                placeholder="your@email.com"
                className="w-full text-xs px-3 py-2 rounded-lg outline-none"
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
              />
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Daily limit</span>
                <select value={config.max_emails_per_day}
                  onChange={e => setConfig(c => ({ ...c, max_emails_per_day: +e.target.value }))}
                  className="text-[11px] px-2 py-1 rounded-lg outline-none"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}>
                  {[3, 5, 10, 15, 20].map(n => <option key={n} value={n}>{n} emails/day</option>)}
                </select>
              </div>
            </ChannelCard>

            {/* SMS Channel */}
            <ChannelCard
              icon={Phone} title="SMS Alerts" subtitle="Instant phone notifications"
              enabled={config.sms_enabled}
              onToggle={v => setConfig(c => ({ ...c, sms_enabled: v }))}
              color="6,182,212" testChannel="sms"
            >
              <input value={config.sms_number}
                onChange={e => setConfig(c => ({ ...c, sms_number: e.target.value }))}
                placeholder="+91 XXXXX XXXXX"
                className="w-full text-xs px-3 py-2 rounded-lg outline-none"
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
              />
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Daily limit</span>
                <select value={config.max_sms_per_day}
                  onChange={e => setConfig(c => ({ ...c, max_sms_per_day: +e.target.value }))}
                  className="text-[11px] px-2 py-1 rounded-lg outline-none"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}>
                  {[2, 3, 5, 10].map(n => <option key={n} value={n}>{n} SMS/day</option>)}
                </select>
              </div>
            </ChannelCard>

            {/* WhatsApp Channel */}
            <ChannelCard
              icon={MessageSquare} title="WhatsApp Alerts" subtitle="via Twilio Business API"
              enabled={config.whatsapp_enabled}
              onToggle={v => setConfig(c => ({ ...c, whatsapp_enabled: v }))}
              color="37,211,102" testChannel="whatsapp"
            >
              <input value={config.whatsapp_number}
                onChange={e => setConfig(c => ({ ...c, whatsapp_number: e.target.value }))}
                placeholder="+91 XXXXX XXXXX"
                className="w-full text-xs px-3 py-2 rounded-lg outline-none"
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
              />
            </ChannelCard>

            {/* Quiet Hours */}
            <div className="rounded-xl p-4"
              style={{
                background: config.quiet_hours_enabled ? 'rgba(245,158,11,0.06)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${config.quiet_hours_enabled ? 'rgba(245,158,11,0.25)' : 'rgba(255,255,255,0.06)'}`,
              }}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ background: 'rgba(245,158,11,0.15)' }}>
                    {config.quiet_hours_enabled ? <VolumeX size={15} style={{ color: '#f59e0b' }} /> : <Volume2 size={15} style={{ color: '#f59e0b' }} />}
                  </div>
                  <div>
                    <div className="text-sm font-semibold">Quiet Hours</div>
                    <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>No alerts during sleep time</div>
                  </div>
                </div>
                <Toggle on={config.quiet_hours_enabled}
                  onChange={v => setConfig(c => ({ ...c, quiet_hours_enabled: v }))} />
              </div>
              {config.quiet_hours_enabled && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="flex items-center gap-3 mt-2">
                  <div className="flex-1">
                    <label className="text-[10px]" style={{ color: 'var(--text-muted)' }}>From</label>
                    <input type="time" value={config.quiet_start}
                      onChange={e => setConfig(c => ({ ...c, quiet_start: e.target.value }))}
                      className="w-full text-xs px-3 py-1.5 rounded-lg outline-none mt-1"
                      style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-[10px]" style={{ color: 'var(--text-muted)' }}>To</label>
                    <input type="time" value={config.quiet_end}
                      onChange={e => setConfig(c => ({ ...c, quiet_end: e.target.value }))}
                      className="w-full text-xs px-3 py-1.5 rounded-lg outline-none mt-1"
                      style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
                    />
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}

        {/* ── PREFERENCES SECTION ───────────────────────────────────── */}
        {activeSection === 'preferences' && (
          <motion.div key="prefs" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="flex flex-col gap-4 max-w-2xl">

            {/* Notification Categories */}
            <div className="glass rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Settings size={15} style={{ color: 'var(--accent-indigo)' }} />
                <span className="font-semibold text-sm">Notification Categories</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                  style={{ background: 'rgba(16,185,129,0.2)', color: '#10b981' }}>GROWW STYLE</span>
              </div>

              <NotifCategory icon={Zap} label="AI Signals" desc="High confidence signal alerts"
                on={config.notify_signals} onChange={v => setConfig(c => ({ ...c, notify_signals: v }))}
                color="var(--accent-indigo)" />

              <NotifCategory icon={Target} label="Price Targets" desc="Alert when stock hits your target price"
                on={config.notify_price_targets} onChange={v => setConfig(c => ({ ...c, notify_price_targets: v }))}
                color="#06b6d4" />

              <NotifCategory icon={BarChart3} label="Portfolio Alerts" desc="P&L changes, stop loss triggers"
                on={config.notify_portfolio} onChange={v => setConfig(c => ({ ...c, notify_portfolio: v }))}
                color="#10b981" />

              <NotifCategory icon={Calendar} label="Corporate Events" desc="Earnings, dividends, splits, bonus"
                on={config.notify_events} onChange={v => setConfig(c => ({ ...c, notify_events: v }))}
                color="#f59e0b" />

              <NotifCategory icon={TrendingUp} label="Market Movers" desc="Top gainers & losers alerts"
                on={config.notify_market_movers} onChange={v => setConfig(c => ({ ...c, notify_market_movers: v }))}
                color="#f43f5e" />
            </div>

            {/* Confidence Threshold */}
            <div className="glass rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle size={14} style={{ color: 'var(--accent-amber)' }} />
                  <span className="text-sm font-semibold">Min Confidence Threshold</span>
                </div>
                <span className="num-ticker font-bold text-sm" style={{ color: 'var(--accent-indigo)' }}>
                  {Math.round(config.min_confidence * 100)}%
                </span>
              </div>
              <input type="range" min={50} max={95} step={5}
                value={config.min_confidence * 100}
                onChange={e => setConfig(c => ({ ...c, min_confidence: e.target.value / 100 }))}
                className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                style={{
                  accentColor: 'var(--accent-indigo)',
                  background: `linear-gradient(to right, #6366f1 ${config.min_confidence * 100}%, rgba(255,255,255,0.1) 0)`
                }}
              />
              <div className="flex justify-between text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>
                <span>50% (More alerts)</span><span>95% (Only critical)</span>
              </div>
            </div>

            {/* Priority Watchlist */}
            <div className="glass rounded-2xl p-5">
              <div className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Target size={14} style={{ color: '#06b6d4' }} />
                Priority Watchlist
              </div>
              <div className="flex gap-2 mb-3">
                <input value={watchlistInput}
                  onChange={e => setWatchlistInput(e.target.value.toUpperCase())}
                  onKeyDown={e => e.key === 'Enter' && addWatch()}
                  placeholder="Add stock (e.g. RELIANCE)"
                  className="flex-1 text-xs px-3 py-2 rounded-lg outline-none"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
                />
                <button onClick={addWatch} className="btn-primary text-xs px-4">Add</button>
              </div>
              <div className="flex flex-wrap gap-2">
                {config.watchlist.map(s => (
                  <div key={s} className="chip text-xs">
                    {s}
                    <button onClick={() => setConfig(c => ({ ...c, watchlist: c.watchlist.filter(x => x !== s) }))}
                      className="ml-1 opacity-60 hover:opacity-100">×</button>
                  </div>
                ))}
                {config.watchlist.length === 0 && (
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    No stocks added. Alerts will still fire for portfolio + high confidence signals.
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* ── HISTORY SECTION ───────────────────────────────────────── */}
        {activeSection === 'history' && (
          <motion.div key="history" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <div className="glass rounded-2xl overflow-hidden">
              <div className="px-5 py-3 flex items-center justify-between"
                style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <div className="flex items-center gap-2">
                  <Clock size={14} style={{ color: 'var(--text-muted)' }} />
                  <span className="font-semibold text-sm">Alert History</span>
                </div>
                <span className="text-[10px] num-ticker" style={{ color: 'var(--text-muted)' }}>
                  {alerts?.length ?? 0} alerts
                </span>
              </div>
              {!alerts?.length ? (
                <div className="py-16 text-center">
                  <Bell size={40} className="mx-auto mb-3 opacity-15" />
                  <div className="text-sm" style={{ color: 'var(--text-muted)' }}>No alerts sent yet</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                    Configure channels above and alerts will appear here
                  </div>
                </div>
              ) : (
                <table className="data-table w-full">
                  <thead><tr>
                    <th>Stock</th><th>Signal</th><th>Channel</th><th className="text-right">Confidence</th><th className="text-center">Status</th><th className="text-right">Time</th>
                  </tr></thead>
                  <tbody>
                    {alerts.map((a, i) => {
                      const channelIcon = {
                        email: <Mail size={11} style={{ color: '#10b981' }} />,
                        sms: <Phone size={11} style={{ color: '#06b6d4' }} />,
                        whatsapp: <MessageSquare size={11} style={{ color: '#25d366' }} />,
                        'in-app': <Bell size={11} style={{ color: '#6366f1' }} />,
                      }
                      return (
                        <motion.tr key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                          transition={{ delay: i * 0.03 }} className="table-row-hover">
                          <td className="font-semibold text-xs">{a.stock}</td>
                          <td className="text-xs" style={{ color: 'var(--text-muted)' }}>{a.signal_type}</td>
                          <td>
                            <span className="chip text-[10px] flex items-center gap-1 w-fit">
                              {channelIcon[a.channel] ?? null}
                              {a.channel}
                            </span>
                          </td>
                          <td className="text-right num-ticker text-xs">
                            {Math.round((a.confidence ?? 0) * 100)}%
                          </td>
                          <td className="text-center">
                            {a.delivered
                              ? <CheckCircle size={13} style={{ color: '#10b981' }} className="mx-auto" />
                              : <XCircle size={13} style={{ color: '#f43f5e' }} className="mx-auto" />}
                          </td>
                          <td className="text-right text-[10px] num-ticker" style={{ color: 'var(--text-muted)' }}>
                            {a.sent_at ? new Date(a.sent_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—'}
                          </td>
                        </motion.tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
