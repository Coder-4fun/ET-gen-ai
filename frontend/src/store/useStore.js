import { create } from 'zustand'

const useStore = create((set, get) => ({
  // ── Signals ────────────────────────────────────────────────────────────
  signals: [],
  topSignals: [],
  setSignals: (signals) => set({ signals }),
  addLiveSignal: (signal) => set((state) => {
    const existing = state.signals.filter(s => s.id !== signal.id)
    return { signals: [signal, ...existing].slice(0, 100) }
  }),

  // ── Portfolio ──────────────────────────────────────────────────────────
  portfolio: null,
  setPortfolio: (portfolio) => set({ portfolio }),

  // ── Heatmap ────────────────────────────────────────────────────────────
  heatmapData: null,
  setHeatmapData: (heatmapData) => set({ heatmapData }),

  // ── News ───────────────────────────────────────────────────────────────
  news: [],
  setNews: (news) => set({ news }),

  // ── Options ────────────────────────────────────────────────────────────
  optionsData: null,
  setOptionsData: (optionsData) => set({ optionsData }),

  // ── Backtest ───────────────────────────────────────────────────────────
  backtestResults: [],
  setBacktestResults: (backtestResults) => set({ backtestResults }),

  // ── Alerts ─────────────────────────────────────────────────────────────
  alerts: [],
  alertConfig: null,
  liveAlerts: [],
  setAlerts: (alerts) => set({ alerts }),
  setAlertConfig: (alertConfig) => set({ alertConfig }),
  pushLiveAlert: (alert) => set((state) => {
    const exists = state.liveAlerts.some(a => 
      a.id === alert.id || 
      ((a.symbol || a.stock) === (alert.symbol || alert.stock) && (a.signal_type || a.signal || a.type) === (alert.signal_type || alert.signal || alert.type))
    );
    if (exists) return state;
    return { liveAlerts: [alert, ...state.liveAlerts].slice(0, 3) }
  }),
  dismissLiveAlert: (id) => set((state) => ({
    liveAlerts: state.liveAlerts.filter(a => a.id !== id)
  })),

  // ── Chat ───────────────────────────────────────────────────────────────
  chatMessages: [],
  chatLoading: false,
  addChatMessage: (msg) => set((state) => ({
    chatMessages: [...state.chatMessages, msg]
  })),
  setChatLoading: (chatLoading) => set({ chatLoading }),

  // ── UI State ───────────────────────────────────────────────────────────
  activeTab: 'dashboard',
  setActiveTab: (activeTab) => set({ activeTab }),
  chatOpen: false,
  setChatOpen: (chatOpen) => set({ chatOpen }),
  selectedStock: null,
  setSelectedStock: (selectedStock) => set({ selectedStock }),
  selectedSector: null,
  setSelectedSector: (selectedSector) => set({ selectedSector }),

  // ── Signal Detail Drawer ───────────────────────────────────────────────
  selectedSignal: null,
  setSelectedSignal: (selectedSignal) => set({ selectedSignal }),

  // ── Command Palette (CMD+K) ────────────────────────────────────────────
  commandPaletteOpen: false,
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),

  // ── Keyboard Shortcuts Modal ───────────────────────────────────────────
  shortcutsOpen: false,
  setShortcutsOpen: (shortcutsOpen) => set({ shortcutsOpen }),

  // ── Market Regime (dashboard cache) ────────────────────────────────────
  regime: null,
  setRegime: (regime) => set({ regime }),

  // ── WebSocket ──────────────────────────────────────────────────────────
  wsConnected: false,
  setWsConnected: (wsConnected) => set({ wsConnected }),
}))

// ── Helper: Infer directional bias from signal data ──────────────────────
export function inferBias(signal) {
  const bias = signal.directional_bias || signal.direction || signal.bias
  if (bias) return bias.toLowerCase()

  const type = (signal.signal_type || signal.type || signal.signal || '').toLowerCase()
  const pattern = (signal.pattern || '').toLowerCase()
  
  const textToScan = type + ' ' + pattern
  
  if (/bullish|surge|accumulation|call|upgrade|buy|above\s?vwap|golden\s?cross|breakout|oversold|hammer|engulfing|morning\s?star|piercing/i.test(textToScan)) return 'bullish'
  if (/bearish|crash|selling|put|downgrade|below\s?vwap|risk|death\s?cross|breakdown|overbought|drop|spike|shooting\s?star|dark\s?cloud/i.test(textToScan)) return 'bearish'
  
  return 'neutral'
}

export default useStore
