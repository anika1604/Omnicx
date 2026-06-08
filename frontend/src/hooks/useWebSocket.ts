import { useEffect, useRef, useCallback, useState } from 'react'

export function useWebSocket(sessionId: string | null) {
  const ws = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)

  useEffect(() => {
    if (!sessionId) return
    const socket = new WebSocket(`ws://localhost:8000/ws/${sessionId}`)
    ws.current = socket
    socket.onopen  = () => setConnected(true)
    socket.onclose = () => setConnected(false)
    socket.onmessage = e => setLastMessage(JSON.parse(e.data))
    return () => socket.close()
  }, [sessionId])

  const send = useCallback((data: object) => {
    ws.current?.send(JSON.stringify(data))
  }, [])

  return { connected, lastMessage, send }
}
