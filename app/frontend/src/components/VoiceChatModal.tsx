import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import {
  FaMicrophone,
  FaMicrophoneSlash,
  FaPhoneSlash,
  FaPhone,
  FaTimes,
  FaVolumeUp,
  FaPaperPlane,
} from 'react-icons/fa'
import { HiSignal } from 'react-icons/hi2'
import { useAgentTalkSession } from '@/hooks/useAgentTalkSession'

interface VoiceTalkPaneProps {
  open: boolean
  onClose: () => void
  companionName?: string
  agentId?: string
}

/**
 * Full-viewport talk/chat beside the sidebar.
 * Transcript scrolls edge-to-edge; footer (mic + text) stays fixed.
 */
export function VoiceChatModal({
  open,
  onClose,
  companionName = 'Lena Van Der Meer',
  agentId,
}: VoiceTalkPaneProps) {
  const {
    status,
    live,
    busy,
    error,
    lines,
    micLevel,
    micLive,
    micMuted,
    audioBlocked,
    sendingText,
    start,
    stop,
    enableSound,
    sendChat,
    setMicrophoneMuted,
  } = useAgentTalkSession({ companionName, agentId })

  const voiceLevel = micMuted ? 0 : micLevel

  const logRef = useRef<HTMLDivElement>(null)
  const [draft, setDraft] = useState('')

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [lines])

  useEffect(() => {
    if (!open && live) {
      void stop()
    }
  }, [open, live, stop])

  const handleClose = async () => {
    if (live || busy) await stop()
    onClose()
  }

  const submitText = async (e?: FormEvent) => {
    e?.preventDefault()
    const text = draft.trim()
    if (!text || !live || sendingText) return
    setDraft('')
    await sendChat(text)
  }

  const onComposerKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void submitText()
    }
  }

  if (!open) return null

  const statusColor = error
    ? 'text-red-400'
    : live
      ? 'text-[#00ff88]'
      : busy
        ? 'text-yellow-400'
        : 'text-gray-500'
  const statusDot = error
    ? 'bg-red-400'
    : live
      ? 'bg-[#00ff88]'
      : busy
        ? 'bg-yellow-400 animate-pulse'
        : 'bg-gray-500'

  return (
    <div className="flex flex-col h-full max-h-full min-h-0 overflow-hidden bg-[#050714] text-white">
      <header className="flex items-center justify-between px-3 py-3 border-b border-[#00ffff]/10 bg-[#0a0b1a] shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#00ffff] to-[#0099cc] flex items-center justify-center shrink-0">
            <HiSignal className="text-black text-base" />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-bold text-white tracking-wider font-display truncate">
              {companionName.toUpperCase()}
            </h2>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-1.5 h-1.5 rounded-full ${statusDot}`} />
              <span className={`text-[10px] tracking-wider font-body truncate ${statusColor}`}>
                {error ?? status}
              </span>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => void handleClose()}
          className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/5 transition-all shrink-0"
          aria-label="Back"
        >
          <FaTimes className="text-sm" />
        </button>
      </header>

      {/* Full-bleed transcript — only this scrolls */}
      <div
        ref={logRef}
        className="flex-1 min-h-0 overflow-y-auto overscroll-contain w-full"
        aria-live="polite"
      >
        <div className="w-full space-y-3 py-4">
          {lines.length === 0 ? (
            <p className="text-center text-gray-600 font-body text-sm mt-16 px-3">
              {live
                ? 'Speak or type below. Mic and text both work.'
                : `Connect, then talk or type with ${companionName}.`}
            </p>
          ) : (
            lines.map((line) => (
              <div
                key={line.id}
                className={`flex w-full px-3 ${line.who === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[92%] px-3.5 py-2.5 rounded-2xl text-sm font-body leading-relaxed whitespace-pre-wrap break-words ${
                    line.who === 'user'
                      ? 'bg-[#ff0080]/20 border border-[#ff0080]/35 rounded-br-sm text-white'
                      : 'bg-[#00ffff]/10 border border-[#00ffff]/20 rounded-bl-sm text-gray-100'
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
      </div>

      {/* Fixed footer: mic + text */}
      <div className="shrink-0 border-t border-[#00ffff]/10 pb-[max(0.75rem,env(safe-area-inset-bottom))] space-y-3 bg-[#0a0b1a]">
        {!live ? (
          <div className="px-3 pt-3">
          <button
            type="button"
            onClick={() => void start()}
            disabled={busy}
            className="w-full flex items-center justify-center gap-2 px-4 py-3.5 bg-gradient-to-r from-[#00ffff] to-[#0099cc] text-black font-bold text-xs tracking-wider rounded-lg transition-all duration-300 hover:scale-[1.01] hover:shadow-lg hover:shadow-[#00ffff]/20 font-display disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <FaPhone className="text-[10px]" />
            {busy ? 'CONNECTING…' : 'START TALKING'}
          </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 px-3 pt-3">
              <button
                type="button"
                onClick={() => void setMicrophoneMuted(!micMuted)}
                className={`flex items-center justify-center gap-2 px-3 py-2 border rounded-lg font-bold text-[10px] tracking-wider font-display shrink-0 ${
                  micLive && !micMuted
                    ? 'border-[#00ff88]/40 text-[#00ff88] bg-[#00ff88]/10'
                    : 'border-gray-600 text-gray-400'
                }`}
                aria-pressed={micMuted}
                title={micMuted ? 'Unmute microphone' : 'Mute microphone (text-only)'}
              >
                {micMuted ? (
                  <FaMicrophoneSlash className="text-[10px]" />
                ) : (
                  <FaMicrophone className="text-[10px]" />
                )}
                {micMuted ? 'TEXT' : 'MIC'}
              </button>

              {/* Compact meter between MIC and END */}
              <div
                className="flex-1 min-w-0 h-7 flex items-end gap-px rounded bg-white/[0.04] overflow-hidden px-0.5"
                aria-label="Your microphone level"
              >
                {Array.from({ length: 40 }, (_, i) => {
                  const t = i / 39
                  const envelope = 0.4 + 0.6 * Math.sin(Math.PI * t)
                  const wobble = 0.7 + 0.3 * Math.sin(i * 1.9 + voiceLevel * 10)
                  const pct = Math.max(
                    8,
                    Math.round(voiceLevel * envelope * wobble * 100),
                  )
                  return (
                    <div key={i} className="flex-1 h-full flex items-end min-w-0">
                      <div
                        className="w-full rounded-t-sm bg-gradient-to-t from-[#00ffff] to-[#ff0080] origin-bottom"
                        style={{
                          height: `${pct}%`,
                          opacity: live ? 0.45 + voiceLevel * 0.55 : 0.2,
                          transition: 'height 50ms linear, opacity 80ms linear',
                        }}
                      />
                    </div>
                  )
                })}
              </div>

              {audioBlocked ? (
                <button
                  type="button"
                  onClick={() => void enableSound()}
                  className="flex items-center justify-center gap-2 px-3 py-2 border border-yellow-500/40 text-yellow-400 bg-yellow-500/10 rounded-lg font-bold text-[10px] tracking-wider font-display shrink-0"
                >
                  <FaVolumeUp className="text-[10px]" />
                  SOUND
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => void stop()}
                className="flex items-center justify-center gap-2 px-3 py-2 border border-red-500/40 text-red-400 bg-red-500/10 rounded-lg font-bold text-[10px] tracking-wider font-display shrink-0"
              >
                <FaPhoneSlash className="text-[10px]" />
                END
              </button>
            </div>

            <form onSubmit={(e) => void submitText(e)} className="flex gap-2 items-end px-3">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={onComposerKey}
                rows={1}
                placeholder={`Message ${companionName}…`}
                disabled={sendingText}
                className="flex-1 min-h-[44px] max-h-28 resize-y bg-white/5 border border-[#00ffff]/20 rounded-lg px-3 py-2.5 text-sm font-body text-white placeholder:text-gray-600 focus:outline-none focus:border-[#00ffff]/50"
              />
              <button
                type="submit"
                disabled={!draft.trim() || sendingText}
                className="h-11 w-11 shrink-0 flex items-center justify-center rounded-lg bg-gradient-to-r from-[#00ffff] to-[#0099cc] text-black disabled:opacity-40"
                aria-label="Send message"
              >
                <FaPaperPlane className="text-xs" />
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
