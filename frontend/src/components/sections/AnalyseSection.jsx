import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CandlestickChart, Layers, BarChart3 } from 'lucide-react'
import { lazy, Suspense } from 'react'

const CandlestickChartView = lazy(() => import('../CandlestickChart'))
const OptionsChain         = lazy(() => import('../OptionsChain'))
const BacktestView         = lazy(() => import('../BacktestView'))

const SUB_TABS = [
  { id: 'chart',    label: 'Charts',        icon: CandlestickChart },
  { id: 'options',  label: 'Options Chain',  icon: Layers },
  { id: 'backtest', label: 'Backtester',     icon: BarChart3 },
]

const Loader = () => (
  <div className="flex flex-col gap-4 p-6">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="skeleton h-28 rounded-2xl" style={{ animationDelay: `${i * 0.1}s` }} />
    ))}
  </div>
)

export default function AnalyseSection() {
  const [activeTab, setActiveTab] = useState('chart')

  return (
    <div className="h-full flex flex-col">
      {/* Sub-nav */}
      <div className="px-6 pt-5 pb-0">
        <div className="flex items-center gap-1 p-1 rounded-xl w-fit"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.04)' }}>
          {SUB_TABS.map(tab => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <motion.button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="relative flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-colors"
                style={{ color: active ? 'var(--text-primary)' : 'var(--text-muted)' }}
                whileTap={{ scale: 0.97 }}
              >
                {active && (
                  <motion.div
                    layoutId="analyse-tab-bg"
                    className="absolute inset-0 rounded-lg"
                    style={{ background: 'rgba(6,182,212,0.12)', border: '1px solid rgba(6,182,212,0.2)' }}
                    transition={{ type: 'spring', bounce: 0.15, duration: 0.5 }}
                  />
                )}
                <span className="relative flex items-center gap-2">
                  <Icon size={13} />
                  {tab.label}
                </span>
              </motion.button>
            )
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
          >
            <Suspense fallback={<Loader />}>
              {activeTab === 'chart'    && <CandlestickChartView />}
              {activeTab === 'options'  && <OptionsChain />}
              {activeTab === 'backtest' && <BacktestView />}
            </Suspense>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
