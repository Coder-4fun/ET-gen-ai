import React, { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { createChart, CrosshairMode } from 'lightweight-charts'
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react'
import useStore, { inferBias } from '../store/useStore'

const STOCKS = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN']

// Mock detected patterns per stock
const DETECTED_PATTERNS = {
  RELIANCE: [
    { name: 'Bullish Engulfing', timeframe: 'Daily', confidence: 82, winRate: 68, bias: 'bullish', explanation: 'A bullish engulfing pattern formed at the 20-day SMA support zone. Volume is 1.8x average, confirming buyer interest. Watch for follow-through above ₹2,920 resistance.' },
    { name: 'VWAP Support Hold', timeframe: '1H', confidence: 74, winRate: 61, bias: 'bullish', explanation: 'Price bounced sharply off VWAP at ₹2,865 with above-average volume. Intraday buyers are defending this level. Positive for swing traders.' },
  ],
  ZOMATO: [
    { name: 'Death Cross (50/200 SMA)', timeframe: 'Daily', confidence: 88, winRate: 64, bias: 'bearish', explanation: 'The 50-day SMA crossed below the 200-day SMA — a classic bearish signal. Historical data shows 64% chance of further 5-8% downside within 30 days.' },
    { name: 'Below VWAP', timeframe: '1H', confidence: 79, winRate: 57, bias: 'bearish', explanation: 'Trading consistently below intraday VWAP with declining volume. Sellers remain in control. Support at ₹175, resistance at ₹188.' },
  ],
  HDFCBANK: [
    { name: 'Double Bottom', timeframe: 'Weekly', confidence: 85, winRate: 72, bias: 'bullish', explanation: 'A double bottom at ₹1,540 support is forming with RSI divergence. High probability reversal pattern. Target: ₹1,680 if neckline at ₹1,610 breaks.' },
  ],
  TATAMOTORS: [
    { name: 'Rising Wedge', timeframe: 'Daily', confidence: 76, winRate: 58, bias: 'bearish', explanation: 'Price is forming a rising wedge with declining volume — a bearish continuation pattern. Watch for break below ₹960 support for confirmation.' },
    { name: 'RSI Overbought', timeframe: '4H', confidence: 71, winRate: 55, bias: 'bearish', explanation: 'RSI at 74 on the 4H chart, approaching overbought. Historical mean reversion happens 55% of the time within 3-5 sessions.' },
  ],
  PAYTM: [
    { name: 'Falling Channel', timeframe: 'Daily', confidence: 73, winRate: 52, bias: 'bearish', explanation: 'Trading within a well-defined falling channel since Feb. Lower highs and lower lows persist. Potential breakout above ₹460 could trigger reversal.' },
  ],
  INFY: [
    { name: 'Cup & Handle', timeframe: 'Weekly', confidence: 91, winRate: 74, bias: 'bullish', explanation: 'A textbook cup and handle pattern with the handle forming near ₹1,720. Breakout above ₹1,740 targets ₹1,850. 74% historical win rate on this timeframe.' },
    { name: 'Golden Cross (50/200)', timeframe: 'Daily', confidence: 84, winRate: 67, bias: 'bullish', explanation: '50-day SMA is about to cross above 200-day SMA. This golden cross has preceded rallies of 8-12% in IT stocks historically.' },
  ],
}

export default function CandlestickChart() {
  const { signals } = useStore()
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const candleSeriesRef = useRef(null)
  const volSeriesRef = useRef(null)
  const [selectedStock, setSelectedStock] = useState('RELIANCE')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!chartRef.current) return
    const chart = createChart(chartRef.current, {
      layout: { background: { color: 'transparent' }, textColor: '#8892b0' },
      grid: { vertLines: { color: 'rgba(255,255,255,0.04)' }, horzLines: { color: 'rgba(255,255,255,0.04)' } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.08)' },
      timeScale: { borderColor: 'rgba(255,255,255,0.08)', timeVisible: true },
      width: chartRef.current.clientWidth,
      height: 340,
    })

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22C55E', downColor: '#EF4444',
      borderUpColor: '#22C55E', borderDownColor: '#EF4444',
      wickUpColor: '#22C55E80', wickDownColor: '#EF444480',
    })

    const volSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'vol',
      scaleMargins: { top: 0.8, bottom: 0 },
    })

    chartInstance.current = chart
    candleSeriesRef.current = candleSeries
    volSeriesRef.current = volSeries

    const ro = new ResizeObserver(() => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth })
    })
    ro.observe(chartRef.current)
    return () => { ro.disconnect(); chart.remove() }
  }, [])

  useEffect(() => {
    if (!candleSeriesRef.current) return
    setLoading(true)

    const base = { RELIANCE: 2800, ZOMATO: 185, HDFCBANK: 1570, TATAMOTORS: 945, PAYTM: 445, INFY: 1710 }[selectedStock] || 1000
    const now = Math.floor(Date.now() / 1000)
    const DAY = 86400
    const candles = [], vols = []
    let price = base * 0.95

    for (let i = 90; i >= 0; i--) {
      const time = now - i * DAY
      const open  = price
      const close = parseFloat((open * (1 + (Math.random() - 0.49) * 0.022)).toFixed(2))
      const high  = parseFloat((Math.max(open, close) * (1 + Math.random() * 0.012)).toFixed(2))
      const low   = parseFloat((Math.min(open, close) * (1 - Math.random() * 0.012)).toFixed(2))
      const vol   = Math.round(1e6 + Math.random() * 4e6)
      candles.push({ time, open, high, low, close })
      vols.push({ time, value: vol, color: close >= open ? 'rgba(34,197,94,0.4)' : 'rgba(239,68,68,0.4)' })
      price = close
    }

    candleSeriesRef.current.setData(candles)
    volSeriesRef.current.setData(vols)

    const sma = [], upper = [], lower = []
    const w = 20
    for (let i = w; i < candles.length; i++) {
      const slice = candles.slice(i - w, i).map(c => c.close)
      const mean = slice.reduce((a, b) => a + b, 0) / w
      const std  = Math.sqrt(slice.reduce((a, b) => a + (b - mean) ** 2, 0) / w)
      sma.push({ time: candles[i].time, value: parseFloat(mean.toFixed(2)) })
      upper.push({ time: candles[i].time, value: parseFloat((mean + 2 * std).toFixed(2)) })
      lower.push({ time: candles[i].time, value: parseFloat((mean - 2 * std).toFixed(2)) })
    }

    const smaSeries = chartInstance.current.addLineSeries({ color: 'rgba(232,255,71,0.4)', lineWidth: 1, title: 'SMA20' })
    const upperSeries = chartInstance.current.addLineSeries({ color: 'rgba(255,255,255,0.15)', lineWidth: 1, lineStyle: 2, title: 'BB+' })
    const lowerSeries = chartInstance.current.addLineSeries({ color: 'rgba(255,255,255,0.15)', lineWidth: 1, lineStyle: 2, title: 'BB-' })

    smaSeries.setData(sma)
    upperSeries.setData(upper)
    lowerSeries.setData(lower)
    chartInstance.current.timeScale().fitContent()
    setLoading(false)
  }, [selectedStock])

  const patterns = signals
    .filter(s => s.stock === selectedStock && s.pattern)
    .map(s => ({
      name: s.pattern,
      timeframe: 'Daily',
      confidence: Math.round((s.confidence_score || s.confidence || 0) * (s.confidence <= 1 ? 100 : 1)),
      winRate: Math.round((s.backtest_win_rate || 0.6) * 100),
      bias: inferBias(s),
      explanation: s.explanation || `${s.pattern} detected for ${s.stock}.`
    }))

  return (
    <div className="p-5 flex flex-col gap-4">
      {/* Stock selector */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-wrap gap-2">
        {STOCKS.map(s => (
          <motion.button
            key={s} whileTap={{ scale: 0.95 }}
            onClick={() => setSelectedStock(s)}
            className={`chip ${selectedStock === s ? 'active' : ''} font-mono text-xs`}
          >
            {s}
          </motion.button>
        ))}
      </motion.div>

      {/* Chart panel */}
      <motion.div
        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
        className="rounded-xl p-4"
        style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-between mb-3">
          <div>
            <span className="font-bold text-lg">{selectedStock}</span>
            <span className="ml-2 text-xs badge badge-brand">Daily</span>
          </div>
          <div className="flex gap-2 text-xs">
            <span className="px-2 py-1 rounded" style={{ background: 'rgba(232,255,71,0.08)', color: 'var(--accent)' }}>SMA20</span>
            <span className="px-2 py-1 rounded" style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-dim)' }}>BB</span>
          </div>
        </div>
        {loading && <div className="skeleton h-80 rounded-xl" />}
        <div ref={chartRef} style={{ display: loading ? 'none' : 'block' }} />
      </motion.div>

      {/* Detected Patterns Panel */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-xl p-5"
        style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="title-md font-semibold">Detected Patterns</h3>
          <span className="meta-xs">{patterns.length} pattern{patterns.length !== 1 ? 's' : ''} found</span>
        </div>

        {patterns.length === 0 ? (
          <div className="text-sm py-4 text-center" style={{ color: 'var(--text-dim)' }}>
            No patterns detected on {selectedStock} currently
          </div>
        ) : (
          <div className="space-y-3">
            {patterns.map((p, i) => {
              const barColor = p.bias === 'bullish' ? 'var(--green)' : 'var(--red)'
              return (
                <motion.div
                  key={p.name}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="signal-card-terminal"
                >
                  <div className="signal-card-bar" style={{ background: barColor }} />
                  <div className="signal-card-body">
                    {/* Row 1 */}
                    <div className="flex items-center gap-2 mb-1">
                      {p.bias === 'bullish' ? <TrendingUp size={12} style={{ color: barColor }} /> : <TrendingDown size={12} style={{ color: barColor }} />}
                      <span className="text-sm font-semibold">{p.name}</span>
                      <span className="meta-xs ml-auto">{p.timeframe}</span>
                    </div>
                    {/* Row 2: Score + Win Rate */}
                    <div className="flex items-center gap-3 mb-1.5">
                      <div className="flex items-center gap-1.5">
                        <span className="meta-xs">Confidence:</span>
                        <div className="w-16 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                          <div className="h-full rounded-full" style={{ background: barColor, width: `${p.confidence}%` }} />
                        </div>
                        <span className="num-ticker text-[11px] font-semibold" style={{ color: barColor }}>{p.confidence}</span>
                      </div>
                      <span className="text-[10px]" style={{ color: 'var(--text-dim)' }}>🎯 {p.winRate}% win rate</span>
                    </div>
                    {/* Row 3: Explanation */}
                    <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{p.explanation}</p>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </motion.div>
    </div>
  )
}
