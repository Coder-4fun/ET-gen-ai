import { useEffect, useRef, useCallback } from 'react'
import useStore from '../store/useStore'

const WS_URL = 'ws://localhost:8000/ws/signals'

/**
 * v2: Exponential backoff with jitter to prevent thundering herd.
 * Replaces the fixed 3s reconnect from v1.
 */
const MAX_RECONNECT_ATTEMPTS = 10
const BASE_DELAY = 1000   // 1 second
const MAX_DELAY = 30000   // 30 seconds

function getReconnectDelay(attempt) {
  // Exponential: 1s, 2s, 4s, 8s, 16s, 30s, 30s...
  const exponential = Math.min(BASE_DELAY * Math.pow(2, attempt), MAX_DELAY)
  // Jitter: ±20% to prevent thundering herd
  const jitter = exponential * (0.8 + Math.random() * 0.4)
  return Math.floor(jitter)
}

export function useWebSocket() {
  const ws = useRef(null)
  const reconnectTimer = useRef(null)
  const reconnectAttempts = useRef(0)
  const { setWsConnected, addLiveSignal, pushLiveAlert } = useStore()

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(WS_URL)

      ws.current.onopen = () => {
        setWsConnected(true)
        reconnectAttempts.current = 0  // Reset on successful connection
        console.log('🔗 WebSocket connected')
        // Send heartbeat every 25s
        ws.current._pingInterval = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send('ping')
          }
        }, 25000)
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'NEW_SIGNAL' && data.payload) {
            const signal = data.payload
            addLiveSignal(signal)
            // Push to live alert banner if high confidence
            if (signal.confidence >= 0.75) {
              pushLiveAlert({ ...signal, _alertId: Date.now() })
            }
          } else if (data.type === 'PRICE_ALERT' && data.payload) {
            // v2: Handle price alert notifications
            pushLiveAlert({
              ...data.payload,
              signal: 'PriceTargetHit',
              confidence: 1.0,
              risk: 'Medium',
              _alertId: Date.now(),
            })
          }
        } catch (e) {
          // Ignore malformed messages
        }
      }

      ws.current.onclose = (event) => {
        setWsConnected(false)
        clearInterval(ws.current?._pingInterval)

        // Normal closure (code 1000) — don't reconnect
        if (event.code === 1000) {
          console.log('🔌 WebSocket closed normally')
          return
        }

        if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = getReconnectDelay(reconnectAttempts.current)
          console.log(
            `🔌 WebSocket disconnected — reconnecting in ${(delay / 1000).toFixed(1)}s ` +
            `(attempt ${reconnectAttempts.current + 1}/${MAX_RECONNECT_ATTEMPTS})`
          )
          reconnectTimer.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        } else {
          console.warn('🔌 WebSocket: max reconnect attempts reached — giving up')
        }
      }

      ws.current.onerror = () => {
        ws.current?.close()
      }
    } catch (e) {
      setWsConnected(false)
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = getReconnectDelay(reconnectAttempts.current)
        reconnectTimer.current = setTimeout(() => {
          reconnectAttempts.current++
          connect()
        }, delay)
      }
    }
  }, [setWsConnected, addLiveSignal, pushLiveAlert])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      clearInterval(ws.current?._pingInterval)
      ws.current?.close(1000)  // Normal closure
    }
  }, [connect])
}
