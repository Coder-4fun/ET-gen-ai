import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Map, Flame, Calendar, Target, Award } from 'lucide-react'

// Import the existing components
import SectorHeatmap from '../SectorHeatmap'
import MarketMovers from '../MarketMovers'
import EventsCalendar from '../EventsCalendar'
import OpportunityRadar from '../OpportunityRadar'
import AlphaScore from '../AlphaScore'

export default function DiscoverSection() {
  const [activeTab, setActiveTab] = useState('heatmap')

  const tabs = [
    { id: 'heatmap', label: 'Sector Heatmap', icon: Map },
    { id: 'movers', label: 'Market Movers', icon: Flame },
    { id: 'radar', label: 'Opportunity Radar', icon: Target },
    { id: 'alpha', label: 'Alpha Score', icon: Award },
    { id: 'events', label: 'Events Calendar', icon: Calendar },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'heatmap': return <SectorHeatmap />
      case 'movers': return <MarketMovers />
      case 'radar': return <OpportunityRadar />
      case 'alpha': return <AlphaScore />
      case 'events': return <EventsCalendar />
      default: return <SectorHeatmap />
    }
  }

  return (
    <div className="p-6 max-w-[1440px] mx-auto h-full flex flex-col">
      <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="mb-5 shrink-0">
        <h2 className="text-2xl font-bold tracking-tight">Discover</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--text-muted)' }}>
          Explore market sectors, top movers, and AI-driven opportunities
        </p>
      </motion.div>

      {/* Sub-navigation */}
      <div className="flex items-center gap-2 mb-6 shrink-0 border-b border-white/5 pb-2">
        {tabs.map(tab => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm font-medium ${
                isActive 
                  ? 'bg-white/10 text-white' 
                  : 'text-[#A3A3A3] hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon size={16} className={isActive ? 'text-[var(--accent)]' : ''} />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto min-h-0 relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0"
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
