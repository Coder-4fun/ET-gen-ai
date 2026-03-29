import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import axios from 'axios'
import useStore from '../store/useStore'

export default function OptionsChain() {
  const { optionsData, setOptionsData } = useStore()
  const [loading, setLoading] = useState(!optionsData)
  const [selectedStock, setSelectedStock] = useState('NIFTY')

  useEffect(() => {
    const fetch = async () => {
      setLoading(true)
      try {
        const { data } = await axios.get(`/api/options/${selectedStock}`)
        setOptionsData(data)
      } catch (e) {
        console.warn('Options fetch error', e)
      } finally { setLoading(false) }
    }
    fetch()
  }, [selectedStock])

  if (loading) return <div className="p-5 flex flex-col gap-3">{[...Array(6)].map((_, i) => <div key={i} className="skeleton h-10 rounded-xl" />)}</div>
  if (!optionsData) return <div className="p-5 text-center" style={{ color: 'var(--text-muted)' }}>No options data</div>

  const { chain = [], spot_price, pcr, max_pain, iv_skew, signal } = optionsData
  const maxOI = Math.max(...chain.flatMap(r => [r.ce_oi, r.pe_oi]), 1)
  const pcrColor = pcr > 1.2 ? '#f43f5e' : pcr < 0.7 ? '#10b981' : '#f59e0b'

  return (
    <div className="p-5 flex flex-col gap-4">
      {/* Stock selector */}
      <div className="flex gap-2">
        {['NIFTY', 'BANKNIFTY', 'RELIANCE', 'ZOMATO'].map(s => (
          <motion.button key={s} whileTap={{ scale: 0.95 }}
            onClick={() => setSelectedStock(s)}
            className={`chip text-xs font-mono ${selectedStock === s ? 'active' : ''}`}>{s}</motion.button>
        ))}
      </div>

      {/* Summary bar */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'PCR', value: pcr?.toFixed(2), color: pcrColor },
          { label: 'Max Pain', value: `₹${max_pain?.toLocaleString('en-IN')}`, color: '#a5b4fc' },
          { label: 'IV Skew', value: iv_skew, color: '#67e8f9' },
          { label: 'Signal', value: signal, color: pcrColor },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass rounded-xl px-4 py-3">
            <div className="text-[11px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{label}</div>
            <div className="font-bold text-base mt-1 num-ticker" style={{ color }}>{value}</div>
          </div>
        ))}
      </motion.div>

      {/* IV Curve */}
      {optionsData.iv_curve?.length > 0 && (
        <div className="glass rounded-2xl p-4">
          <div className="text-sm font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>IV Smile Curve</div>
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={optionsData.iv_curve}>
              <XAxis dataKey="strike" tick={{ fontSize: 10, fill: '#4a5578' }} />
              <YAxis tick={{ fontSize: 10, fill: '#4a5578' }} domain={['auto', 'auto']} />
              <Tooltip contentStyle={{ background: '#111420', border: '1px solid #2d3148', borderRadius: 8, fontSize: 12 }} />
              <ReferenceLine x={spot_price} stroke="rgba(99,102,241,0.5)" strokeDasharray="4 2" label={{ value: 'Spot', fill: '#a5b4fc', fontSize: 10 }} />
              <Line type="monotone" dataKey="iv" stroke="#06b6d4" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Strike Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="px-4 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <span className="text-sm font-semibold">Options Chain</span>
          <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>Spot: ₹{spot_price?.toLocaleString('en-IN')}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full text-xs">
            <thead>
              <tr>
                <th className="text-right" style={{ color: '#10b981' }}>CE OI</th>
                <th className="text-right" style={{ color: '#10b981' }}>CE Vol</th>
                <th className="text-right" style={{ color: '#10b981' }}>CE IV</th>
                <th className="text-center font-bold">Strike</th>
                <th className="text-left" style={{ color: '#f43f5e' }}>PE IV</th>
                <th className="text-left" style={{ color: '#f43f5e' }}>PE Vol</th>
                <th className="text-left" style={{ color: '#f43f5e' }}>PE OI</th>
              </tr>
            </thead>
            <tbody>
              {chain.map((row, i) => {
                const ceIntensity = row.ce_oi / maxOI
                const peIntensity = row.pe_oi / maxOI
                const isATM = Math.abs(row.strike - spot_price) < (spot_price * 0.005)
                return (
                  <motion.tr key={row.strike}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    style={{ background: isATM ? 'rgba(99,102,241,0.07)' : 'transparent' }}
                  >
                    <td className="text-right num-ticker"
                      style={{ background: `rgba(16,185,129,${ceIntensity * 0.25})` }}>
                      {(row.ce_oi / 1000).toFixed(0)}K
                    </td>
                    <td className="text-right num-ticker" style={{ color: 'var(--text-secondary)' }}>
                      {(row.ce_vol / 1000).toFixed(0)}K
                    </td>
                    <td className="text-right num-ticker" style={{ color: '#34d399' }}>{row.ce_iv?.toFixed(1)}%</td>
                    <td className="text-center font-bold" style={{ color: isATM ? '#a5b4fc' : 'var(--text-primary)' }}>
                      {row.strike.toLocaleString('en-IN')}
                      {isATM && <span className="ml-1 text-[9px] badge badge-brand">ATM</span>}
                    </td>
                    <td className="num-ticker" style={{ color: '#fb7185' }}>{row.pe_iv?.toFixed(1)}%</td>
                    <td className="num-ticker" style={{ color: 'var(--text-secondary)' }}>
                      {(row.pe_vol / 1000).toFixed(0)}K
                    </td>
                    <td style={{ background: `rgba(244,63,94,${peIntensity * 0.25})` }}
                      className="num-ticker">
                      {(row.pe_oi / 1000).toFixed(0)}K
                    </td>
                  </motion.tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
