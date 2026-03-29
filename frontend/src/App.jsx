import React, { useEffect, useState, lazy, Suspense, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  LayoutDashboard, Radar, BarChart2, Search, MessageSquare,
  Wifi, WifiOff, Zap, Menu, X, Bell, Settings, ChevronDown, Command
} from 'lucide-react'
import useStore from './store/useStore'
import { useWebSocket } from './hooks/useWebSocket'
import { usePortfolio } from './hooks/usePortfolio'
import LiveAlertBanner from './components/LiveAlertBanner'
import ChatbotPanel from './components/ChatbotPanel'
import OnboardingWizard from './components/OnboardingWizard'
import CommandPalette from './components/CommandPalette'
import SignalDetailDrawer from './components/SignalDetailDrawer'

// Hub sections
import DashboardSection from './components/sections/DashboardSection'
import RadarSection from './components/sections/RadarSection'
import AnalyseSection from './components/sections/AnalyseSection'
import DiscoverSection from './components/sections/DiscoverSection'

// Settings overlay
import AlertManager from './components/AlertManager'
import PriceAlerts from './components/PriceAlerts'
import MarketVideo from './components/MarketVideo'
import PortfolioView from './components/PortfolioView'

const API = '/api'

const PRIMARY_NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'radar',     label: 'Radar',     icon: Radar,    badge: 'LIVE' },
  { id: 'analyse',   label: 'Analyse',   icon: BarChart2 },
  { id: 'discover',  label: 'Discover',  icon: Search },
]

const SECONDARY_NAV = [
  { id: 'alerts',       label: 'Notifications' },
  { id: 'price_alerts', label: 'Price Alerts' },
  { id: 'video',        label: 'Daily Briefing' },
  { id: 'portfolio',    label: 'Portfolio' },
]

const SHORTCUTS = [
  { key: 'D', label: 'Dashboard' },
  { key: 'R', label: 'Radar' },
  { key: 'A', label: 'Analyse' },
  { key: 'V', label: 'Discover' },
  { key: '⌘K', label: 'Search stocks' },
  { key: '⌘/', label: 'Show shortcuts' },
  { key: 'ESC', label: 'Close drawer/modal' },
  { key: '1-5', label: 'Sub-tab navigation' },
]

const pageVariants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.23, 1, 0.32, 1] } },
  exit:    { opacity: 0, y: -6, transition: { duration: 0.2 } },
}

const TabLoader = () => (
  <div className="flex flex-col gap-4 p-6">
    {[...Array(4)].map((_, i) => (
      <div key={i} className="skeleton h-24 rounded-2xl" style={{ animationDelay: `${i * 0.1}s` }} />
    ))}
  </div>
)

function ShortcutsModal({ onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={onClose}
    >
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.5)' }} />
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="relative z-10 rounded-xl p-6 w-[380px]"
        style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-hover)' }}
        onClick={e => e.stopPropagation()}
      >
        <h3 className="title-md font-semibold mb-4">Keyboard Shortcuts</h3>
        <div className="space-y-2">
          {SHORTCUTS.map(s => (
            <div key={s.key} className="flex items-center justify-between py-1">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{s.label}</span>
              <span className="kbd px-2 py-0.5">{s.key}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  )
}

export default function App() {
  const {
    activeTab, setActiveTab, chatOpen, setChatOpen, wsConnected, signals,
    selectedSignal, setSelectedSignal,
    commandPaletteOpen, setCommandPaletteOpen,
    shortcutsOpen, setShortcutsOpen,
  } = useStore()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [niftyData, setNiftyData] = useState({ value: null, change: 0, live: false })
  const [moreOpen, setMoreOpen] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())

  // Initialize live hooks
  useWebSocket()
  usePortfolio()

  // Check onboarding
  useEffect(() => {
    if (!localStorage.getItem('et_onboarded')) {
      setShowOnboarding(true)
    }
  }, [])

  // Clock
  useEffect(() => {
    const t = setInterval(() => setCurrentTime(new Date()), 30000)
    return () => clearInterval(t)
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      // Don't fire in inputs
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

      const isMod = e.metaKey || e.ctrlKey

      if (isMod && e.key === 'k') { e.preventDefault(); setCommandPaletteOpen(true); return }
      if (isMod && e.key === '/') { e.preventDefault(); setShortcutsOpen(true); return }
      if (e.key === 'Escape') {
        if (selectedSignal) { setSelectedSignal(null); return }
        if (commandPaletteOpen) { setCommandPaletteOpen(false); return }
        if (shortcutsOpen) { setShortcutsOpen(false); return }
        if (chatOpen) { setChatOpen(false); return }
        return
      }
      if (!isMod) {
        if (e.key === 'd' || e.key === 'D') { setActiveTab('dashboard'); return }
        if (e.key === 'r' || e.key === 'R') { setActiveTab('radar'); return }
        if (e.key === 'a' || e.key === 'A') { setActiveTab('analyse'); return }
        if (e.key === 'v' || e.key === 'V') { setActiveTab('discover'); return }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [selectedSignal, commandPaletteOpen, shortcutsOpen, chatOpen])

  // Fetch all data
  const fetchAllData = async () => {
    try {
      const [sigRes, heatRes, newsRes, backtestRes] = await Promise.allSettled([
        axios.get(`${API}/signals`),
        axios.get(`${API}/heatmap`),
        axios.get(`${API}/news`),
        axios.get(`${API}/backtest/all`),
      ])
      const { setSignals, setHeatmapData, setNews, setBacktestResults } = useStore.getState()
      if (sigRes.status === 'fulfilled')       setSignals(sigRes.value.data)
      if (heatRes.status === 'fulfilled')      setHeatmapData(heatRes.value.data)
      if (newsRes.status === 'fulfilled')      setNews(newsRes.value.data)
      if (backtestRes.status === 'fulfilled')  setBacktestResults(backtestRes.value.data)
    } catch (e) { console.warn('Data fetch error:', e.message) }
  }

  useEffect(() => {
    fetchAllData()
    const refreshInterval = setInterval(fetchAllData, 60000)
    return () => clearInterval(refreshInterval)
  }, [])

  // NIFTY ticker
  useEffect(() => {
    const fetchNifty = async () => {
      try {
        const res = await axios.get(`${API}/market/nifty`)
        const { nifty } = res.data
        if (nifty) {
          setNiftyData({ value: nifty.price, change: nifty.change_pct, live: res.data.live ?? true })
        }
      } catch (e) {
        setNiftyData(prev => ({ value: prev.value || 22500, change: prev.change || 0, live: false }))
      }
    }
    fetchNifty()
    const t = setInterval(fetchNifty, 30000)
    return () => clearInterval(t)
  }, [])

  const activeSignalCount = signals.filter(s => {
    const conf = s.confidence_score ?? (s.confidence ? (s.confidence <= 1 ? s.confidence * 100 : s.confidence) : 0)
    return conf >= 75
  }).length
  const isSecondary = SECONDARY_NAV.some(n => n.id === activeTab)

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
      {/* Background */}
      <div className="mesh-bg" />
      <div className="grid-dots" />

      {/* ── Sidebar ─────────────────────────────────────── */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -220, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -220, opacity: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="sidebar-rail relative z-20 flex flex-col"
            style={{ width: 220, minWidth: 220 }}
          >
            {/* Logo */}
            <div className="sidebar-logo">
              <div className="flex items-center gap-3 px-5 py-5">
                <motion.div
                  whileHover={{ rotate: 180 }}
                  transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
                  className="logo-mark"
                >
                  <Zap size={14} fill="white" className="text-white" />
                </motion.div>
                <div>
                  <div className="text-gradient font-bold text-[13px] leading-tight tracking-tight">ET Markets</div>
                  <div className="text-[9px] font-medium tracking-wide uppercase" style={{ color: 'var(--text-muted)' }}>Intelligence Layer</div>
                </div>
              </div>
            </div>

            {/* NIFTY Ticker */}
            <div className="mx-4 mt-3 nifty-ticker">
              <div className="flex items-center justify-between">
                <span className="text-[9px] uppercase tracking-[0.15em] font-semibold" style={{ color: 'var(--text-muted)' }}>NIFTY 50</span>
                {niftyData.live && <div className="live-dot" style={{ width: 5, height: 5 }} />}
              </div>
              <div className="flex items-end gap-2 mt-1">
                <span className="num-ticker font-bold text-[15px] leading-none">
                  {niftyData.value ? niftyData.value.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '—'}
                </span>
                <span className={`text-[11px] font-semibold mb-px num-ticker ${niftyData.change >= 0 ? 'pnl-pos' : 'pnl-neg'}`}>
                  {niftyData.change >= 0 ? '+' : ''}{niftyData.change.toFixed(2)}%
                </span>
              </div>
            </div>

            {/* Primary Nav */}
            <nav className="flex-1 px-3 pt-5 overflow-y-auto">
              <div className="nav-section-label">Navigation</div>
              {PRIMARY_NAV.map((item, i) => {
                const Icon = item.icon
                const isActive = activeTab === item.id
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04, duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                    onClick={() => { setActiveTab(item.id); setMoreOpen(false) }}
                    className={`nav-item ${isActive && !isSecondary ? 'active' : ''}`}
                  >
                    <Icon size={15} />
                    <span className="flex-1 text-[13px]">{item.label}</span>
                    {item.id === 'radar' && activeSignalCount > 0 && (
                      <span className="signal-badge">{activeSignalCount}</span>
                    )}
                    {item.badge && (
                      <span className="live-badge">{item.badge}</span>
                    )}
                  </motion.div>
                )
              })}

              {/* More menu */}
              <div className="mt-2 mb-1">
                <div className="nav-section-label mt-3">More</div>
                <motion.div
                  onClick={() => setMoreOpen(v => !v)}
                  className={`nav-item ${isSecondary ? 'active' : ''}`}
                  whileTap={{ scale: 0.98 }}
                >
                  <Settings size={15} />
                  <span className="flex-1 text-[13px]">
                    {isSecondary ? SECONDARY_NAV.find(n => n.id === activeTab)?.label : 'Tools & Settings'}
                  </span>
                  <motion.div animate={{ rotate: moreOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
                    <ChevronDown size={13} />
                  </motion.div>
                </motion.div>

                <AnimatePresence>
                  {moreOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
                      className="overflow-hidden"
                    >
                      <div className="pl-4 pt-1 space-y-0.5">
                        {SECONDARY_NAV.map(item => (
                          <motion.div
                            key={item.id}
                            initial={{ x: -8, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            onClick={() => setActiveTab(item.id)}
                            className={`nav-sub-item ${activeTab === item.id ? 'active' : ''}`}
                          >
                            {item.label}
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </nav>

            {/* AI Chat Button */}
            <div className="px-4 pb-5">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setChatOpen(true)}
                className="ai-chat-btn w-full"
              >
                <MessageSquare size={14} />
                <span>AI Chat</span>
                <div className="ai-chat-glow" />
              </motion.button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ── Main Content ────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 relative z-10">

        {/* Top Bar */}
        <motion.header
          initial={{ y: -40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
          className="top-bar"
        >
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(v => !v)} className="btn-ghost p-2 rounded-lg">
              <Menu size={15} />
            </button>
            <div>
              <h1 className="font-bold text-[14px] tracking-tight" style={{ color: 'var(--text-primary)' }}>
                {PRIMARY_NAV.find(n => n.id === activeTab)?.label
                  ?? SECONDARY_NAV.find(n => n.id === activeTab)?.label
                  ?? 'Dashboard'}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Search button */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-colors"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-dim)' }}
            >
              <Search size={12} />
              <span>Search stocks</span>
              <span className="kbd text-[9px]">⌘K</span>
            </button>

            {/* Connection Status */}
            <div className="status-pill">
              {wsConnected ? (
                <>
                  <div className="live-dot" style={{ width: 6, height: 6 }} />
                  <span className="text-[11px] font-medium" style={{ color: '#22C55E' }}>Connected</span>
                </>
              ) : (
                <>
                  <WifiOff size={11} style={{ color: 'var(--text-muted)' }} />
                  <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>Reconnecting…</span>
                </>
              )}
            </div>

            {/* Time */}
            <div className="text-[11px] num-ticker font-medium" style={{ color: 'var(--text-muted)' }}>
              {niftyData.live ? '◉' : '○'} {currentTime.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })} IST
            </div>
          </div>
        </motion.header>

        {/* Live Alert Banner */}
        <LiveAlertBanner />

        {/* Tab Content */}
        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="h-full"
            >
              <Suspense fallback={<TabLoader />}>
                {activeTab === 'dashboard'    && <DashboardSection />}
                {activeTab === 'radar'        && <RadarSection />}
                {activeTab === 'analyse'      && <AnalyseSection />}
                {activeTab === 'discover'     && <DiscoverSection />}
                {activeTab === 'alerts'       && <AlertManager />}
                {activeTab === 'price_alerts' && <PriceAlerts />}
                {activeTab === 'video'        && <MarketVideo />}
                {activeTab === 'portfolio'    && <PortfolioView />}
              </Suspense>
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* ── Signal Detail Drawer ───────────────────────── */}
      <AnimatePresence>
        {selectedSignal && (
          <SignalDetailDrawer signal={selectedSignal} onClose={() => setSelectedSignal(null)} />
        )}
      </AnimatePresence>

      {/* ── Command Palette (CMD+K) ────────────────────── */}
      <CommandPalette isOpen={commandPaletteOpen} onClose={() => setCommandPaletteOpen(false)} />

      {/* ── Keyboard Shortcuts Modal ──────────────────── */}
      <AnimatePresence>
        {shortcutsOpen && <ShortcutsModal onClose={() => setShortcutsOpen(false)} />}
      </AnimatePresence>

      {/* ── Chatbot Panel ───────────────────────────────── */}
      <AnimatePresence>
        {chatOpen && <ChatbotPanel onClose={() => setChatOpen(false)} />}
      </AnimatePresence>

      {/* ── Onboarding ──────────────────────────────────── */}
      <AnimatePresence>
        {showOnboarding && <OnboardingWizard onComplete={() => setShowOnboarding(false)} />}
      </AnimatePresence>
    </div>
  )
}
