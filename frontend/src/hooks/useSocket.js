import { useEffect, useRef, useState } from 'react'

// Connects to wss://host/ws, PING every 15s (Fortinet keep-alive), auto-reconnect.
export default function useSocket(onMessage) {
  const [connected, setConnected] = useState(false)
  const cb = useRef(onMessage); cb.current = onMessage
  useEffect(() => {
    let ws, ping, stop = false
    const open = () => {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${proto}://${location.host}/ws?token=${localStorage.getItem('token')}`)
      ws.onopen = () => { setConnected(true); ping = setInterval(() => ws.send(JSON.stringify({ type: 'PING' })), 15000) }
      ws.onmessage = (e) => cb.current(JSON.parse(e.data))
      ws.onclose = () => { setConnected(false); clearInterval(ping); if (!stop) setTimeout(open, 2000) }
    }
    open()
    return () => { stop = true; clearInterval(ping); ws && ws.close() }
  }, [])
  return connected
}
