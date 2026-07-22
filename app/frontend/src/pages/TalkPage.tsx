/**
 * Optional full-page talk surface (embeds / deep links).
 * Default product UI: Landing + Discover + VoiceChatModal (see `@/config/brand`).
 */
import { useEffect, useRef } from 'react'
import {
  FaMicrophone,
  FaMicrophoneSlash,
  FaPhoneSlash,
  FaPhone,
  FaVolumeUp,
} from 'react-icons/fa'
import { HiSignal } from 'react-icons/hi2'
import { Link, useSearchParams } from 'react-router-dom'
import { useAgentTalkSession } from '@/hooks/useAgentTalkSession'
import { PRODUCT_NAME } from '@/config/brand'

export default function TalkPage() {
  const [params] = useSearchParams()
  const companionName = (params.get('name') || 'Lena Van Der Meer').trim() || 'Lena Van Der Meer'
  const agentId = params.get('agent_id')?.trim() || undefined

  const {
    status,
    live,
    busy,
    error,
    lines,
    micLevel,
    micLive,
    audioBlocked,
    start,
    stop,
    enableSound,
  } = useAgentTalkSession({ companionName, agentId })

  const logRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [lines])

  useEffect(() => {
    return () => {
      void stop()
    }
  }, [stop])

  const statusColor = error
    ? 'text-red-400'
    : live
      ? 'text-[#00ff88]'
      : busy
        ? 'text-yellow-400'
        : 'text-gray-500'

  return (
    <div className="min-h-screen flex flex-col bg-[#050714] text-white">
      <header className="flex items-center justify-between px-5 py-4 border-b border-[#00ffff]/10">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#00ffff] to-[#0099cc] flex items-center justify-center shrink-0">
            <HiSignal className="text-black text-base" />
          </div>
          <div className="min-w-0">
            <h1 className="text-base font-bold tracking-wider font-display truncate">
              {companionName.toUpperCase()}
            </h1>
            <p className={`text-[11px] tracking-wider font-body truncate ${statusColor}`}>
              {error ?? status}
            </p>
          </div>
        </div>
        <Link
          to="/discover"
          className="text-[11px] tracking-wider text-[#00ffff]/80 hover:text-[#00ffff] font-display"
        >
          {PRODUCT_NAME}
        </Link>
      </header>

      <div
        ref={logRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-3 max-w-xl w-full mx-auto"
        aria-live="polite"
      >
        {lines.length === 0 ? (
          <p className="text-center text-gray-600 font-body text-sm mt-12 px-4">
            {live
              ? 'Speak — your words appear on the right.'
              : `Start talking with ${companionName}.`}
          </p>
        ) : (
          lines.map((line) => (
            <div
              key={line.id}
              className={`flex w-full ${line.who === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm font-body leading-relaxed whitespace-pre-wrap break-words ${
                  line.who === 'user'
                    ? 'bg-[#ff0080]/20 border border-[#ff0080]/35 rounded-br-sm'
                    : 'bg-[#00ffff]/10 border border-[#00ffff]/20 rounded-bl-sm'
                } ${line.final ? '' : 'opacity-70'}`}
              >
                <div
                  className={`text-[10px] tracking-wider uppercase mb-1 font-display ${
                    line.who === 'user' ? 'text-[#ff0080]/80' : 'text-[#00ffff]/80'
                  }`}
                >
                  {line.who === 'user' ? 'You' : companionName}
                </div>
                {line.text || '…'}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="border-t border-[#00ffff]/10 px-4 py-4 space-y-3 max-w-xl w-full mx-auto">
        <div className="flex items-center gap-2" aria-label="Microphone level">
          <span className="text-[10px] uppercase tracking-wider text-gray-500 font-body w-10 text-right">
            {micLive ? 'Mic' : 'Off'}
          </span>
          <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#00ffff] to-[#ff0080] transition-[width] duration-75"
              style={{
                width: `${Math.round(micLevel * 100)}%`,
                opacity: micLive ? 1 : 0.35,
              }}
            />
          </div>
        </div>

        <div className="flex gap-2 flex-wrap">
          {!live ? (
            <button
              type="button"
              onClick={() => void start()}
              disabled={busy}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-[#00ffff] to-[#0099cc] text-black font-bold text-xs tracking-wider rounded-lg font-display disabled:opacity-40"
            >
              <FaPhone className="text-[10px]" />
              {busy ? 'CONNECTING…' : 'START TALKING'}
            </button>
          ) : (
            <>
              <button
                type="button"
                disabled
                className={`flex items-center justify-center gap-2 px-4 py-3 border rounded-lg font-bold text-xs tracking-wider font-display ${
                  micLive
                    ? 'border-[#00ff88]/40 text-[#00ff88] bg-[#00ff88]/10'
                    : 'border-gray-600 text-gray-500'
                }`}
              >
                {micLive ? (
                  <FaMicrophone className="text-[10px]" />
                ) : (
                  <FaMicrophoneSlash className="text-[10px]" />
                )}
                {micLive ? 'LIVE' : 'MIC'}
              </button>
              {audioBlocked ? (
                <button
                  type="button"
                  onClick={() => void enableSound()}
                  className="flex items-center justify-center gap-2 px-4 py-3 border border-yellow-500/40 text-yellow-400 bg-yellow-500/10 rounded-lg font-bold text-xs tracking-wider font-display"
                >
                  <FaVolumeUp className="text-[10px]" />
                  ENABLE SOUND
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => void stop()}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border border-red-500/40 text-red-400 bg-red-500/10 rounded-lg font-bold text-xs tracking-wider font-display"
              >
                <FaPhoneSlash className="text-[10px]" />
                END
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
