import { useEffect, useCallback } from 'react'
import axios from 'axios'
import useStore from '../store/useStore'

const API = '/api'
const REFRESH_MS = 30_000   // 30 seconds

export function usePortfolio() {
  const { setPortfolio } = useStore()

  const fetchPortfolio = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/portfolio`)
      setPortfolio(data)
    } catch (e) {
      console.warn('Portfolio fetch failed:', e.message)
    }
  }, [setPortfolio])

  useEffect(() => {
    fetchPortfolio()
    const interval = setInterval(fetchPortfolio, REFRESH_MS)
    return () => clearInterval(interval)
  }, [fetchPortfolio])

  return { refresh: fetchPortfolio }
}
