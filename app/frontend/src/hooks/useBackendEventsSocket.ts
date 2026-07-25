/**
 * Persistent WebSocket to app/backend (`/api/ws/events`).
 * Companions POST /api/agent/reach (or checkup loop) → browser gets voice_call.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { getClientSessionId } from '@/lib/talkToken'

export type VoiceInviteEvent = {
  type: 'voice_call' | 'agent_reach'
  agent_id: string
  agent_name: string
  message: string
  auto_answer?: boolean
  mode?: string
  greeting_context?: string
  purpose?: string
  client_session_id?: string | null
  ts?: number
}

function eventsWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/api/ws/events`
}

export function useBackendEventsSocket() {
  const [incoming, setIncoming] = useState<VoiceInviteEvent | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const dismiss = useCallback(() => setIncoming(null), [])

  const sendTalkState = useCallback((live: boolean) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'talk_state', live: Boolean(live) }))
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined

    const clearPing = () => {
      if (pingTimer.current) {
        clearInterval(pingTimer.current)
        pingTimer.current = null
      }
    }

    const connect = () => {
      if (cancelled) return
      const ws = new WebSocket(eventsWsUrl())
      wsRef.current = ws

      ws.onopen = () => {
        retryRef.current = 0
        setConnected(true)
        const sid = getClientSessionId()
        ws.send(JSON.stringify({ type: 'hello', client_session_id: sid }))
        clearPing()
        pingTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 20_000)
      }

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(String(ev.data)) as VoiceInviteEvent & {
            type: string
          }
          if (data?.type === 'pong' || data?.type === 'welcome') return
          if (
            (data?.type === 'voice_call' || data?.type === 'agent_reach') &&
            data.agent_id
          ) {
            setIncoming({
              type: data.type,
              agent_id: data.agent_id,
              agent_name: data.agent_name || 'Companion',
              message: data.message || 'is checking up on you',
              auto_answer: Boolean(data.auto_answer) || data.type === 'voice_call',
              mode: data.mode,
              greeting_context: data.greeting_context || 'reminder_call',
              purpose: data.purpose || 'checkup',
              client_session_id: data.client_session_id,
              ts: data.ts,
            })
          }
        } catch {
          /* ignore */
        }
      }

      ws.onclose = () => {
        clearPing()
        wsRef.current = null
        setConnected(false)
        if (cancelled) return
        const delay = Math.min(10_000, 600 * 2 ** retryRef.current++)
        reconnectTimer = setTimeout(connect, delay)
      }

      ws.onerror = () => {
        try {
          ws.close()
        } catch {
          /* ignore */
        }
      }
    }

    connect()
    return () => {
      cancelled = true
      clearPing()
      if (reconnectTimer) clearTimeout(reconnectTimer)
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [])

  return { incoming, dismiss, connected, sendTalkState }
}

/** @deprecated use useBackendEventsSocket */
export const useAgentReachEvents = useBackendEventsSocket
