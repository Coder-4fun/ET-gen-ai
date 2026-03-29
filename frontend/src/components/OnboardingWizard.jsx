import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  TrendingUp, BarChart3, PieChart, Layers,
  ArrowRight, ArrowLeft, X, Check, Search, Plus
} from 'lucide-react'

const GOALS = [
  { id: 'find',     label: 'Find stocks to buy',          icon: TrendingUp,  desc: 'AI-powered signal detection' },
  { id: 'track',    label: 'Track my portfolio',          icon: PieChart,    desc: 'Real-time P&L monitoring' },
  { id: 'patterns', label: 'Understand chart patterns',   icon: BarChart3,   desc: 'Technical analysis insights' },
  { id: 'options',  label: 'Learn options trading',       icon: Layers,      desc: 'Options chain & strategies' },
]

const BROKERS = [
  { id: 'zerodha',  name: 'Zerodha Kite',  color: '#387ed1', available: true },
  { id: 'angelone', name: 'Angel One',      color: '#ff6b35', available: true },
  { id: 'groww',    name: 'Groww',          color: '#00d09c', available: false },
  { id: 'icici',    name: 'ICICI Direct',   color: '#f57c00', available: false },
]

const QUICK_LISTS = [
  { id: 'nifty50',   label: 'Nifty 50',   stocks: ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK'] },
  { id: 'niftyit',   label: 'Nifty IT',   stocks: ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM'] },
  { id: 'niftybank', label: 'Nifty Bank', stocks: ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK'] },
]

const POPULAR_STOCKS = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT', 'AXISBANK', 'WIPRO']

const slideVariants = {
  enter: (dir) => ({ x: dir > 0 ? 60 : -60, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir) => ({ x: dir > 0 ? -60 : 60, opacity: 0 }),
}

export default function OnboardingWizard({ onComplete }) {
  const [step, setStep] = useState(0)
  const [direction, setDirection] = useState(1)
  const [goals, setGoals] = useState([])
  const [broker, setBroker] = useState(null)
  const [watchlist, setWatchlist] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [alertLevel, setAlertLevel] = useState('high')
  const [channels, setChannels] = useState({ inApp: true, email: false, whatsapp: false })
  const [quietHours, setQuietHours] = useState(true)

  const TOTAL_STEPS = 4

  const next = () => { setDirection(1); setStep(s => Math.min(s + 1, TOTAL_STEPS - 1)) }
  const prev = () => { setDirection(-1); setStep(s => Math.max(s - 1, 0)) }

  const toggleGoal = (id) => setGoals(g => g.includes(id) ? g.filter(x => x !== id) : [...g, id])
  const addStock = (s) => { if (!watchlist.includes(s)) setWatchlist([...watchlist, s]) }
  const removeStock = (s) => setWatchlist(watchlist.filter(x => x !== s))
  const addQuickList = (stocks) => setWatchlist([...new Set([...watchlist, ...stocks])])

  const filteredStocks = POPULAR_STOCKS.filter(s =>
    s.toLowerCase().includes(searchQuery.toLowerCase()) && !watchlist.includes(s)
  )

  const finish = () => {
    localStorage.setItem('et_onboarded', '1')
    localStorage.setItem('et_prefs', JSON.stringify({ goals, broker, watchlist, alertLevel, channels, quietHours }))
    onComplete?.()
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(12px)' }}
    >
      <motion.div
        initial={{ scale: 0.92, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
        className="relative w-full max-w-lg rounded-3xl overflow-hidden"
        style={{ background: 'var(--bg-surface)', border: '1px solid rgba(255,255,255,0.06)' }}
      >
        {/* Close */}
        <button onClick={finish} className="absolute top-4 right-4 z-10 p-1.5 rounded-lg transition-colors hover:bg-white/5">
          <X size={16} style={{ color: 'var(--text-muted)' }} />
        </button>

        {/* Progress */}
        <div className="px-8 pt-6 pb-2">
          <div className="flex gap-1.5">
            {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
              <motion.div
                key={i}
                className="h-1 rounded-full flex-1"
                style={{ background: i <= step ? '#6366f1' : 'rgba(255,255,255,0.06)' }}
                animate={{ background: i <= step ? '#6366f1' : 'rgba(255,255,255,0.06)' }}
                transition={{ duration: 0.3 }}
              />
            ))}
          </div>
          <div className="flex items-center justify-between mt-3">
            <span className="text-[10px] uppercase tracking-[0.15em] font-medium" style={{ color: 'var(--text-muted)' }}>
              Step {step + 1} of {TOTAL_STEPS}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="px-8 pb-8" style={{ minHeight: 340 }}>
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={step}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: [0.23, 1, 0.32, 1] }}
            >
              {/* Step 0: Goals */}
              {step === 0 && (
                <div>
                  <h3 className="text-xl font-bold mb-1 tracking-tight">What brings you here?</h3>
                  <p className="text-sm mb-5" style={{ color: 'var(--text-muted)' }}>Select all that apply — we'll personalize your experience.</p>
                  <div className="grid grid-cols-2 gap-3">
                    {GOALS.map(g => {
                      const Icon = g.icon
                      const selected = goals.includes(g.id)
                      return (
                        <motion.button
                          key={g.id}
                          whileTap={{ scale: 0.97 }}
                          onClick={() => toggleGoal(g.id)}
                          className="text-left p-4 rounded-2xl transition-all"
                          style={{
                            background: selected ? 'rgba(99,102,241,0.1)' : 'rgba(255,255,255,0.02)',
                            border: `1px solid ${selected ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.04)'}`,
                          }}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <Icon size={15} style={{ color: selected ? '#818cf8' : 'var(--text-muted)' }} />
                            {selected && <Check size={12} style={{ color: '#818cf8' }} />}
                          </div>
                          <div className="font-medium text-sm mb-0.5">{g.label}</div>
                          <div className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{g.desc}</div>
                        </motion.button>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Step 1: Broker */}
              {step === 1 && (
                <div>
                  <h3 className="text-xl font-bold mb-1 tracking-tight">Connect your broker</h3>
                  <p className="text-sm mb-5" style={{ color: 'var(--text-muted)' }}>Optional — enables personalized portfolio signals.</p>
                  <div className="space-y-3">
                    {BROKERS.map(b => (
                      <motion.button
                        key={b.id}
                        whileTap={b.available ? { scale: 0.98 } : {}}
                        onClick={() => b.available && setBroker(b.id)}
                        className="w-full flex items-center gap-4 p-4 rounded-2xl text-left transition-all"
                        style={{
                          background: broker === b.id ? 'rgba(99,102,241,0.1)' : 'rgba(255,255,255,0.02)',
                          border: `1px solid ${broker === b.id ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.04)'}`,
                          opacity: b.available ? 1 : 0.4,
                        }}
                      >
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold"
                          style={{ background: `${b.color}18`, color: b.color }}>
                          {b.name[0]}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-sm">{b.name}</div>
                          <div className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                            {b.available ? 'Ready to connect' : 'Coming soon'}
                          </div>
                        </div>
                        {broker === b.id && <Check size={16} style={{ color: '#818cf8' }} />}
                      </motion.button>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 2: Watchlist */}
              {step === 2 && (
                <div>
                  <h3 className="text-xl font-bold mb-1 tracking-tight">Build your watchlist</h3>
                  <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>Track stocks you care about.</p>

                  {/* Quick add */}
                  <div className="flex gap-2 mb-3">
                    {QUICK_LISTS.map(q => (
                      <button key={q.id} onClick={() => addQuickList(q.stocks)}
                        className="chip text-[11px]">
                        <Plus size={10} /> {q.label}
                      </button>
                    ))}
                  </div>

                  {/* Search */}
                  <div className="relative mb-3">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
                    <input
                      type="text"
                      placeholder="Search stocks..."
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-4 py-2.5 rounded-xl text-sm outline-none"
                      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', color: 'var(--text-primary)' }}
                    />
                  </div>

                  {/* Search results */}
                  {searchQuery && (
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {filteredStocks.slice(0, 6).map(s => (
                        <button key={s} onClick={() => addStock(s)}
                          className="text-[11px] px-2.5 py-1 rounded-lg font-medium transition-colors"
                          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', color: 'var(--text-secondary)' }}>
                          + {s}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Selected */}
                  <div className="flex flex-wrap gap-1.5" style={{ maxHeight: 120, overflowY: 'auto' }}>
                    {watchlist.map(s => (
                      <motion.span
                        key={s}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-lg font-medium cursor-pointer"
                        style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)', color: '#a5b4fc' }}
                        onClick={() => removeStock(s)}
                      >
                        {s} <X size={10} />
                      </motion.span>
                    ))}
                    {watchlist.length === 0 && (
                      <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>No stocks added yet</span>
                    )}
                  </div>
                </div>
              )}

              {/* Step 3: Alerts */}
              {step === 3 && (
                <div>
                  <h3 className="text-xl font-bold mb-1 tracking-tight">Alert preferences</h3>
                  <p className="text-sm mb-5" style={{ color: 'var(--text-muted)' }}>Choose how you want to be notified.</p>

                  {/* Signal confidence threshold */}
                  <div className="mb-5">
                    <div className="text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Alert me for:</div>
                    <div className="space-y-2">
                      {[
                        { id: 'high', label: 'High confidence only (75+)', desc: 'Fewer, more reliable' },
                        { id: 'medium', label: 'Medium and above (50+)', desc: 'Balanced' },
                        { id: 'all', label: 'All signals', desc: 'Everything' },
                      ].map(opt => (
                        <button key={opt.id} onClick={() => setAlertLevel(opt.id)}
                          className="w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all"
                          style={{
                            background: alertLevel === opt.id ? 'rgba(99,102,241,0.08)' : 'rgba(255,255,255,0.02)',
                            border: `1px solid ${alertLevel === opt.id ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.04)'}`,
                          }}>
                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${alertLevel === opt.id ? '' : ''}`}
                            style={{ borderColor: alertLevel === opt.id ? '#6366f1' : 'rgba(255,255,255,0.15)' }}>
                            {alertLevel === opt.id && <div className="w-2 h-2 rounded-full" style={{ background: '#6366f1' }} />}
                          </div>
                          <div>
                            <div className="text-sm font-medium">{opt.label}</div>
                            <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{opt.desc}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Channels */}
                  <div className="mb-4">
                    <div className="text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Channels:</div>
                    <div className="space-y-2">
                      {[
                        { key: 'inApp', label: 'In-app notifications' },
                        { key: 'email', label: 'Email' },
                        { key: 'whatsapp', label: 'WhatsApp' },
                      ].map(ch => (
                        <div key={ch.key} className="flex items-center justify-between p-3 rounded-xl"
                          style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                          <span className="text-sm">{ch.label}</span>
                          <div className={`toggle-track ${channels[ch.key] ? 'on' : ''}`}
                            onClick={() => setChannels({ ...channels, [ch.key]: !channels[ch.key] })}>
                            <div className="toggle-thumb" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Quiet hours */}
                  <div className="flex items-center justify-between p-3 rounded-xl"
                    style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                    <div>
                      <div className="text-sm font-medium">Quiet hours</div>
                      <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>10:00 PM — 8:00 AM</div>
                    </div>
                    <div className={`toggle-track ${quietHours ? 'on' : ''}`}
                      onClick={() => setQuietHours(!quietHours)}>
                      <div className="toggle-thumb" />
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="px-8 pb-6 flex items-center justify-between">
          {step > 0 ? (
            <button onClick={prev} className="flex items-center gap-1.5 text-sm font-medium transition-colors"
              style={{ color: 'var(--text-muted)' }}>
              <ArrowLeft size={14} /> Back
            </button>
          ) : <div />}

          {step < TOTAL_STEPS - 1 ? (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={next}
              className="btn-primary flex items-center gap-2"
            >
              Continue <ArrowRight size={14} />
            </motion.button>
          ) : (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={finish}
              className="btn-primary flex items-center gap-2"
              style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}
            >
              Launch Dashboard <ArrowRight size={14} />
            </motion.button>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}
