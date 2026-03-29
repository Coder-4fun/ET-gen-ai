import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search } from 'lucide-react'
import useStore from '../store/useStore'

const NSE_STOCKS = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', sector: 'Energy', change: +1.2 },
  { symbol: 'TCS', name: 'Tata Consultancy', sector: 'IT', change: +2.4 },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', sector: 'Banking', change: -1.3 },
  { symbol: 'INFY', name: 'Infosys', sector: 'IT', change: +0.8 },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', sector: 'Banking', change: +0.5 },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Banking', change: -2.1 },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel', sector: 'Telecom', change: +1.1 },
  { symbol: 'ITC', name: 'ITC Limited', sector: 'FMCG', change: +0.3 },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Banking', change: -0.4 },
  { symbol: 'LT', name: 'Larsen & Toubro', sector: 'Infra', change: +0.5 },
  { symbol: 'TATAMOTORS', name: 'Tata Motors', sector: 'Auto', change: +3.1 },
  { symbol: 'BAJFINANCE', name: 'Bajaj Finance', sector: 'Finance', change: -0.9 },
  { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical', sector: 'Pharma', change: -2.0 },
  { symbol: 'WIPRO', name: 'Wipro Limited', sector: 'IT', change: +1.9 },
  { symbol: 'TATASTEEL', name: 'Tata Steel', sector: 'Metals', change: -3.1 },
  { symbol: 'AXISBANK', name: 'Axis Bank', sector: 'Banking', change: +0.2 },
  { symbol: 'TITAN', name: 'Titan Company', sector: 'Consumer', change: +2.3 },
  { symbol: 'ASIANPAINT', name: 'Asian Paints', sector: 'Consumer', change: -0.5 },
  { symbol: 'DLF', name: 'DLF Limited', sector: 'Realty', change: +4.7 },
  { symbol: 'ZOMATO', name: 'Zomato', sector: 'Tech', change: -1.8 },
  { symbol: 'HCLTECH', name: 'HCL Technologies', sector: 'IT', change: +1.4 },
  { symbol: 'TECHM', name: 'Tech Mahindra', sector: 'IT', change: +0.6 },
  { symbol: 'MARUTI', name: 'Maruti Suzuki', sector: 'Auto', change: +1.7 },
  { symbol: 'PAYTM', name: 'One97 Communications', sector: 'Tech', change: -2.5 },
]

export default function CommandPalette({ isOpen, onClose }) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef(null)
  const { signals, setActiveTab, setSelectedStock } = useStore()
  
  // Recent searches from localStorage
  const [recent, setRecent] = useState(() => {
    try { return JSON.parse(localStorage.getItem('et_recent_search') || '[]') } catch { return [] }
  })

  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  const filtered = query.length > 0
    ? NSE_STOCKS.filter(s =>
        s.symbol.toLowerCase().includes(query.toLowerCase()) ||
        s.name.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 8)
    : recent.length > 0
      ? NSE_STOCKS.filter(s => recent.includes(s.symbol)).slice(0, 5)
      : NSE_STOCKS.slice(0, 6)

  const hasSignal = (symbol) => {
    const sig = signals.find(s => s.symbol === symbol)
    return sig ? (sig.directional_bias || sig.bias || 'neutral') : null
  }

  const select = useCallback((stock) => {
    // Save to recent
    const updated = [stock.symbol, ...recent.filter(r => r !== stock.symbol)].slice(0, 5)
    setRecent(updated)
    localStorage.setItem('et_recent_search', JSON.stringify(updated))
    setSelectedStock(stock.symbol)
    setActiveTab('analyse')
    onClose()
  }, [recent, setActiveTab, setSelectedStock, onClose])

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIndex(i => Math.min(i + 1, filtered.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIndex(i => Math.max(i - 1, 0)) }
    else if (e.key === 'Enter' && filtered[selectedIndex]) { select(filtered[selectedIndex]) }
    else if (e.key === 'Escape') { onClose() }
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="cmd-palette-overlay"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, y: -10, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.98 }}
          transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
          className="cmd-palette"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex items-center gap-3 px-4" style={{ borderBottom: '1px solid var(--border)' }}>
            <Search size={15} style={{ color: 'var(--text-dim)' }} />
            <input
              ref={inputRef}
              type="text"
              placeholder="Search NSE stocks..."
              value={query}
              onChange={e => { setQuery(e.target.value); setSelectedIndex(0) }}
              onKeyDown={handleKeyDown}
              style={{ border: 'none' }}
            />
            <span className="kbd">ESC</span>
          </div>

          <div className="cmd-palette-results">
            {query.length === 0 && recent.length > 0 && (
              <div className="px-4 py-2">
                <span className="meta-xs uppercase tracking-wider" style={{ letterSpacing: '0.15em' }}>Recent</span>
              </div>
            )}
            {filtered.map((stock, i) => {
              const sigBias = hasSignal(stock.symbol)
              return (
                <div
                  key={stock.symbol}
                  className={`cmd-palette-item ${i === selectedIndex ? 'selected' : ''}`}
                  onClick={() => select(stock)}
                  onMouseEnter={() => setSelectedIndex(i)}
                >
                  {/* Signal dot */}
                  <div className="w-2 h-2 rounded-full" style={{
                    background: sigBias === 'bullish' ? 'var(--green)' : sigBias === 'bearish' ? 'var(--red)' : 'var(--border)'
                  }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{stock.symbol}</span>
                      <span className="meta-xs truncate">{stock.name}</span>
                    </div>
                  </div>
                  <span className="meta-xs">{stock.sector}</span>
                  <span className={`num-ticker text-xs font-medium ${stock.change >= 0 ? 'pnl-pos' : 'pnl-neg'}`}>
                    {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(1)}%
                  </span>
                </div>
              )
            })}
            {filtered.length === 0 && (
              <div className="p-6 text-center">
                <span className="text-sm" style={{ color: 'var(--text-dim)' }}>No stocks found</span>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
