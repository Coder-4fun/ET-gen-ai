import React, { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Zap, MessageSquareText } from 'lucide-react'
import axios from 'axios'
import useStore from '../store/useStore'

const SESSION_ID = `session_${Date.now()}`

export default function ChatbotPanel({ onClose }) {
  const { chatMessages, addChatMessage, chatLoading, setChatLoading, portfolio, signals } = useStore()
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, chatLoading])

  // Portfolio-aware smart prompts
  const getSmartPrompts = () => {
    const holdings = portfolio?.holdings || []
    const topLoser = holdings.reduce((a, b) => (a?.pnl_percent || 0) < (b?.pnl_percent || 0) ? a : b, holdings[0])
    
    const regimeState = useStore.getState().regime;
    const regimeNames = {
      strong_bull: 'Strong Bull', weak_bull: 'Weak Bull', sideways: 'Sideways',
      weak_bear: 'Weak Bear', strong_bear: 'Strong Bear'
    }
    const regimeName = regimeNames[regimeState?.regime] || 'Sideways'

    return [
      topLoser?.stock ? `Why is my ${topLoser.stock} position down?` : "Why is my portfolio down?",
      "Which of my holdings has bullish signals right now?",
      `What does the current ${regimeName} mean for my portfolio?`,
      "What is the strongest opportunity in the market today?",
    ]
  }

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg) return
    setInput('')
    addChatMessage({ role: 'user', content: msg, timestamp: new Date().toISOString() })
    setChatLoading(true)

    try {
      let full = ''
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: SESSION_ID }),
      })

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      const tempId = Date.now()
      addChatMessage({ role: 'assistant', content: '', _id: tempId, timestamp: new Date().toISOString() })

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(l => l.startsWith('data:'))
        for (const line of lines) {
          try {
            const parsed = JSON.parse(line.slice(5))
            if (parsed.chunk) {
              full += parsed.chunk
              const msgs = useStore.getState().chatMessages
              const updated = msgs.map(m => m._id === tempId ? { ...m, content: full } : m)
              useStore.setState({ chatMessages: updated })
            }
          } catch { /* ignore */ }
        }
      }
    } catch (e) {
      addChatMessage({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', timestamp: new Date().toISOString() })
    } finally {
      setChatLoading(false)
    }
  }

  const smartPrompts = getSmartPrompts()

  return (
    <motion.div
      initial={{ x: '100%', opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: '100%', opacity: 0 }}
      transition={{ type: 'spring', damping: 28, stiffness: 280 }}
      className="fixed right-0 top-0 h-full z-50 flex flex-col"
      style={{ width: 420, borderLeft: '1px solid var(--border)', background: 'var(--bg-surface)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4"
        style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--accent)' }}>
            <Zap size={14} fill="#000" className="text-black" />
          </div>
          <div>
            <div className="font-bold text-sm">ET Markets AI</div>
            <div className="flex items-center gap-1.5">
              <div className="live-dot" style={{ width: 6, height: 6 }} />
              <span className="text-[10px]" style={{ color: 'var(--green)' }}>Online</span>
            </div>
          </div>
        </div>
        <button onClick={onClose} className="btn-ghost p-1.5 rounded-lg"><X size={16} /></button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3">
        {chatMessages.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{ background: 'var(--accent-dim)', border: '1px solid rgba(232,255,71,0.2)' }}>
              <MessageSquareText size={28} style={{ color: 'var(--accent)' }} />
            </div>
            <div>
              <div className="font-semibold mb-1">Ask ET Markets AI</div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                I know your portfolio, active signals, and market conditions. Ask me anything.
              </div>
            </div>
          </motion.div>
        )}

        <AnimatePresence>
          {chatMessages.map((msg, i) => (
            <motion.div key={i}
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-6 h-6 rounded-lg flex-shrink-0 mr-2 mt-1 flex items-center justify-center"
                  style={{ background: 'var(--accent)' }}>
                  <Zap size={10} fill="#000" className="text-black" />
                </div>
              )}
              <div className={msg.role === 'user' ? 'chat-user' : 'chat-ai'}>
                {msg.content || (msg.role === 'assistant' && chatLoading && i === chatMessages.length - 1 ? (
                  <div className="flex items-center gap-1.5 py-1">
                    <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
                  </div>
                ) : '')}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {chatLoading && chatMessages[chatMessages.length - 1]?.role === 'user' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
            <div className="w-6 h-6 rounded-lg flex-shrink-0 mr-2 flex items-center justify-center"
              style={{ background: 'var(--accent)' }}>
              <Zap size={10} fill="#000" className="text-black" />
            </div>
            <div className="chat-ai">
              <div className="flex items-center gap-1.5 py-1">
                <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Smart prompts */}
      {chatMessages.length === 0 && (
        <div className="px-4 pb-2 flex flex-col gap-1.5">
          {smartPrompts.map(c => (
            <motion.button key={c} whileTap={{ scale: 0.98 }}
              onClick={() => sendMessage(c)}
              className="text-left px-3 py-2 rounded-lg text-xs transition-colors"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
            >
              → {c}
            </motion.button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="px-4 pb-4 pt-2" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex gap-2 items-end">
          <div className="flex-1 rounded-xl px-3 py-2.5 text-sm"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              placeholder="Ask about signals, portfolio, sectors…"
              rows={1}
              className="w-full bg-transparent resize-none outline-none text-sm"
              style={{ color: 'var(--text-primary)', fontFamily: 'inherit', maxHeight: 80 }}
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={() => sendMessage()}
            disabled={!input.trim() || chatLoading}
            className="btn-primary p-2.5 rounded-xl flex-shrink-0"
            style={{ opacity: (!input.trim() || chatLoading) ? 0.5 : 1 }}
          >
            <Send size={15} />
          </motion.button>
        </div>
        <div className="text-[10px] mt-1.5 text-center" style={{ color: 'var(--text-dim)' }}>
          Not SEBI-registered advice · For informational purposes only
        </div>
      </div>
    </motion.div>
  )
}
