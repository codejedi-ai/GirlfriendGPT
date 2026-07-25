/**
 * App-level bridge: backend WebSocket → companion check-up / open talk.
 * Stays mounted on Landing and Discover so agents can ring anytime.
 */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FaPhone, FaTimes } from 'react-icons/fa'
import { useVoiceTalk } from '@/contexts/VoiceTalkContext'
import { useBackendEventsSocket } from '@/hooks/useBackendEventsSocket'

export function AgentVoiceBridge() {
  const navigate = useNavigate()
  const { open, openTalk } = useVoiceTalk()
  const { incoming, dismiss, connected, sendTalkState } = useBackendEventsSocket()

  // Tell backend when talk is live so check-ups do not interrupt.
  useEffect(() => {
    sendTalkState(open)
  }, [open, sendTalkState])

  useEffect(() => {
    if (!incoming || open) return
    const auto =
      incoming.type === 'voice_call' && incoming.auto_answer !== false
    if (!auto) return
    openTalk(incoming.agent_name, incoming.agent_id, {
      autoStart: true,
      greetingContext: incoming.greeting_context || 'reminder_call',
    })
    navigate('/discover')
    dismiss()
  }, [incoming, open, openTalk, navigate, dismiss])

  const answerIncoming = () => {
    if (!incoming) return
    openTalk(incoming.agent_name || 'Companion', incoming.agent_id, {
      autoStart: true,
      greetingContext: incoming.greeting_context || 'reminder_call',
    })
    navigate('/discover')
    dismiss()
  }

  // Auto voice_call is handled above; banner is for notify / manual answer.
  if (!incoming || open) return null
  if (incoming.type === 'voice_call' && incoming.auto_answer !== false) return null

  return (
    <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[60] w-[min(420px,92vw)] rounded-xl border border-[#00ffff]/30 bg-[#0a0b1a]/95 backdrop-blur-xl shadow-lg shadow-[#00ffff]/15 px-4 py-3">
      <p className="text-xs tracking-wider text-[#00ffff] font-display mb-1">
        CHECK-UP{connected ? '' : ' (reconnecting…)'}
      </p>
      <p className="text-sm text-white font-body mb-3">
        <span className="text-[#ff0080] font-semibold">{incoming.agent_name}</span>{' '}
        {incoming.message}
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={answerIncoming}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-[#00ffff] to-[#0099cc] text-black font-bold text-[10px] tracking-wider font-display"
        >
          <FaPhone className="text-[10px]" />
          ANSWER
        </button>
        <button
          type="button"
          onClick={dismiss}
          className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-gray-600 text-gray-400 font-bold text-[10px] tracking-wider font-display"
        >
          <FaTimes className="text-[10px]" />
          LATER
        </button>
      </div>
    </div>
  )
}
