import React, { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Play, Pause, SkipBack, SkipForward, Volume2, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react'

const API = '/api'

function IndexTile({ name, value, change }) {
  const pos = change >= 0
  return (
    <div className="rounded-xl p-3" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}>
      <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>{name}</div>
      <div className="font-bold text-sm num-ticker" style={{ color: 'var(--text-primary)' }}>
        {value?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) ?? '—'}
      </div>
      <div className={`text-xs font-semibold num-ticker ${pos ? 'pnl-pos' : 'pnl-neg'}`}>
        {pos ? '▲' : '▼'} {Math.abs(change)}%
      </div>
    </div>
  )
}

function MoverBar({ items, isGainer }) {
  const color = isGainer ? '#10b981' : '#f43f5e'
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider mb-2 flex items-center gap-1.5" style={{ color: 'var(--text-muted)' }}>
        {isGainer ? <TrendingUp size={10} color={color} /> : <TrendingDown size={10} color={color} />}
        {isGainer ? 'Top Gainers' : 'Top Losers'}
      </div>
      {items.map((m, i) => (
        <div key={m.ticker} className="flex items-center gap-2 mb-2">
          <span className="text-[11px] w-28 truncate" style={{ color: 'var(--text-secondary)' }}>{m.stock}</span>
          <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <motion.div
              className="h-full rounded-full"
              style={{ background: color }}
              initial={{ width: 0 }}
              animate={{ width: `${Math.abs(m.change / 5) * 100}%` }}
              transition={{ duration: 0.8, delay: i * 0.1 + 0.3 }}
            />
          </div>
          <span className={`text-[11px] num-ticker font-semibold w-12 text-right ${isGainer ? 'pnl-pos' : 'pnl-neg'}`}>
            {m.change >= 0 ? '+' : ''}{m.change}%
          </span>
        </div>
      ))}
    </div>
  )
}

function ScriptPlayer({ lines, isPlaying, currentLine }) {
  return (
    <div className="rounded-xl p-4 min-h-[80px] relative overflow-hidden"
      style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)' }}>
      {/* Scanning line effect */}
      {isPlaying && (
        <motion.div
          className="absolute left-0 right-0 h-0.5 opacity-30"
          style={{ background: 'linear-gradient(90deg, transparent, #6366f1, transparent)' }}
          animate={{ top: ['10%', '90%'] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
        />
      )}
      <AnimatePresence mode="wait">
        <motion.p
          key={currentLine}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.3 }}
          className="text-sm leading-relaxed"
          style={{ color: 'var(--text-secondary)' }}>
          {lines[currentLine] ?? '…'}
        </motion.p>
      </AnimatePresence>
      <div className="flex gap-1 mt-2">
        {lines.map((_, i) => (
          <div key={i} className="h-0.5 flex-1 rounded-full transition-all duration-300"
            style={{ background: i === currentLine ? '#6366f1' : 'rgba(255,255,255,0.08)' }} />
        ))}
      </div>
    </div>
  )
}

export default function MarketVideo() {
  const [data, setData]           = useState(null)
  const [loading, setLoading]     = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentLine, setLine]    = useState(0)
  const [activeSection, setSection] = useState('summary')
  const intervalRef = useRef(null)
  const videoRef = useRef(null)

  const load = async () => {
    setLoading(true)
    setIsPlaying(false)
    setLine(0)
    try {
      const res = await axios.get(`${API}/video/daily`)
      setData(res.data)
    } catch (e) {
      console.error('Video load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    if (!data || !isPlaying) {
      clearInterval(intervalRef.current)
      return
    }
    const lines = data.script_lines ?? []
    intervalRef.current = setInterval(() => {
      setLine(l => {
        if (l >= lines.length - 1) {
          clearInterval(intervalRef.current)
          setIsPlaying(false)
          return l
        }
        return l + 1
      })
    }, 3500)
    return () => clearInterval(intervalRef.current)
  }, [isPlaying, data])

  useEffect(() => {
    if (videoRef.current) {
      if (isPlaying) videoRef.current.play().catch(e => console.log('Video play blocked:', e))
      else videoRef.current.pause()
    }
  }, [isPlaying])

  const lines     = data?.script_lines ?? []
  const progress  = lines.length > 0 ? ((currentLine + 1) / lines.length) * 100 : 0
  const moodColor = data?.mood === 'bullish' ? '#10b981' : '#f43f5e'

  return (
    <div className="p-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>Daily Briefing</h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            {data?.date || new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} · {data?.duration_seconds || 75} seconds
          </p>
        </div>
        <button onClick={load} disabled={loading} className="btn-ghost p-2 rounded-lg">
          <motion.div animate={{ rotate: loading ? 360 : 0 }}
            transition={{ duration: 1, repeat: loading ? Infinity : 0, ease: 'linear' }}>
            <RefreshCw size={14} />
          </motion.div>
        </button>
      </div>

      {loading ? (
        <div className="flex flex-col gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
        </div>
      ) : data && (
        <>
          {/* Video player card */}
          <div className="rounded-2xl overflow-hidden mb-5"
            style={{ border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(10,14,33,0.8)' }}>
            {/* Gradient header */}
            <div className="px-5 py-4 flex items-center justify-between"
              style={{ background: `linear-gradient(135deg, ${moodColor}18, rgba(99,102,241,0.1))` }}>
              <div>
                <div className="flex items-center gap-2 mb-0.5">
                  <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: moodColor }} />
                  <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: moodColor }}>
                    {data.mood_emoji} Daily Briefing
                  </span>
                </div>
                <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{data.date}</div>
              </div>
              <div className="text-right">
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Duration</div>
                <div className="num-ticker font-bold" style={{ color: 'var(--text-secondary)' }}>
                  {data.duration_seconds}s
                </div>
              </div>
            </div>

            {/* Placeholder Video Player */}
            <div className="w-full aspect-video bg-black relative border-y border-white/10">
              <video 
                ref={videoRef}
                src="https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4" 
                className="w-full h-full object-cover opacity-80"
                loop
                muted
                playsInline
              />
            </div>

            {/* Script player */}
            <div className="p-4">
              <ScriptPlayer lines={lines} isPlaying={isPlaying} currentLine={currentLine} />

              {/* Progress bar */}
              <div className="mt-3 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
                <motion.div className="h-full rounded-full"
                  style={{ background: 'linear-gradient(90deg, #6366f1, #06b6d4)', width: `${progress}%` }}
                  transition={{ duration: 0.2 }} />
              </div>
              <div className="flex justify-between text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>
                <span>{currentLine + 1} / {lines.length}</span>
                <span>{Math.round(progress)}%</span>
              </div>

              {/* Controls */}
              <div className="flex items-center justify-center gap-3 mt-4">
                <button onClick={() => setLine(0)} className="btn-ghost p-2 rounded-lg">
                  <SkipBack size={14} />
                </button>
                <motion.button
                  whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  onClick={() => setIsPlaying(p => !p)}
                  className="w-10 h-10 rounded-full flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, #6366f1, #06b6d4)' }}>
                  {isPlaying ? <Pause size={16} className="text-white" /> : <Play size={16} className="text-white ml-0.5" />}
                </motion.button>
                <button onClick={() => setLine(l => Math.min(l + 1, lines.length - 1))} className="btn-ghost p-2 rounded-lg">
                  <SkipForward size={14} />
                </button>
                <button
                  onClick={() => {
                    if ('speechSynthesis' in window) {
                      window.speechSynthesis.cancel()
                      const text = lines.join('. ')
                      const utterance = new SpeechSynthesisUtterance(text)
                      utterance.rate = 0.95
                      utterance.pitch = 1
                      utterance.lang = 'en-IN'
                      window.speechSynthesis.speak(utterance)
                    }
                  }}
                  className="btn-ghost p-2 rounded-lg"
                  data-tip="Read aloud"
                >
                  <Volume2 size={14} style={{ color: 'var(--text-secondary)' }} />
                </button>
              </div>
            </div>
          </div>

          {/* Section tabs */}
          <div className="flex gap-1 mb-4 p-1 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)', width: 'fit-content' }}>
            {[['summary', 'Market Summary'], ['movers', 'Top Movers'], ['sectors', 'Sectors']].map(([id, label]) => (
              <button key={id} onClick={() => setSection(id)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                style={{
                  background: activeSection === id ? 'rgba(99,102,241,0.25)' : 'transparent',
                  color: activeSection === id ? '#a5b4fc' : 'var(--text-muted)',
                }}>
                {label}
              </button>
            ))}
          </div>

          {/* Summary section */}
          {activeSection === 'summary' && (
            <div className="grid grid-cols-2 gap-3 mb-4">
              {Object.entries(data.indices).map(([key, idx]) => (
                <IndexTile key={key} name={key.replace('_', ' ').toUpperCase()} value={idx.value} change={idx.change} />
              ))}
            </div>
          )}

          {/* Movers section */}
          {activeSection === 'movers' && (
            <div className="grid grid-cols-2 gap-4">
              <div className="card">
                <MoverBar items={data.top_gainers} isGainer={true} />
              </div>
              <div className="card">
                <MoverBar items={data.top_losers}  isGainer={false} />
              </div>
            </div>
          )}

          {/* Sectors section */}
          {activeSection === 'sectors' && (
            <div className="card">
              <div className="text-xs font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>
                Sector Performance Today
              </div>
              {data.sector_rotation.map((s, i) => {
                const pos = s.change >= 0
                return (
                  <div key={s.sector} className="flex items-center gap-3 mb-3">
                    <span className="text-xs w-32 shrink-0" style={{ color: 'var(--text-secondary)' }}>{s.sector}</span>
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: pos ? '#10b981' : '#f43f5e' }}
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.abs(s.change) / 3 * 100}%` }}
                        transition={{ duration: 0.8, delay: i * 0.1 }}
                      />
                    </div>
                    <span className={`text-xs num-ticker font-semibold w-12 text-right ${pos ? 'pnl-pos' : 'pnl-neg'}`}>
                      {pos ? '+' : ''}{s.change}%
                    </span>
                    <span className="text-[10px] w-16 text-right" style={{ color: 'var(--text-muted)' }}>{s.signal}</span>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}
