import { useEffect, useRef, useState } from 'react'
import {
  Room,
  RoomEvent,
  Track,
  createLocalAudioTrack,
  ParticipantKind,
  type LocalAudioTrack,
  type Participant,
} from 'livekit-client'
import {
  resolveWhoFromMeta,
  upsertTranscriptLine,
  type TranscriptLine,
} from './transcript'

/**
 * Voice talk UI for the AI girlfriend.
 *
 * Traffic (locked):
 *   1) Frontend → app/backend  POST /api/token  → { token, url }
 *   2) Frontend → LiveKit      Room.connect(url, token)  → WebRTC
 *
 * Live transcript: Lena (agent) on the left, you on the right.
 */

type TokenResponse = {
  token: string
  url: string
  room: string
  identity: string
  agent_id: string
  agent_name: string
}

type Props = {
  apiBase?: string
}

const TOPIC_TRANSCRIPTION = 'lk.transcription'
const ATTR_SEGMENT_ID = 'lk.segment_id'
const ATTR_FINAL = 'lk.transcription_final'
const ATTR_TRACK_ID = 'lk.transcribed_track_id'

function localAudioSids(room: Room): string[] {
  return [...room.localParticipant.audioTrackPublications.values()]
    .map((p) => p.trackSid)
    .filter(Boolean) as string[]
}

function whoFor(
  room: Room,
  participantIdentity: string | undefined,
  transcribedTrackId: string | undefined,
) {
  return resolveWhoFromMeta({
    localIdentity: room.localParticipant.identity,
    participantIdentity,
    transcribedTrackId,
    localAudioTrackSids: localAudioSids(room),
  })
}

async function publishMicrophone(room: Room): Promise<LocalAudioTrack> {
  // Explicit permission + track publish (more reliable than setMicrophoneEnabled alone).
  const probe = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  })
  probe.getTracks().forEach((t) => t.stop())

  const track = await createLocalAudioTrack({
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
  })
  await room.localParticipant.publishTrack(track, {
    source: Track.Source.Microphone,
    name: 'microphone',
  })
  return track
}

function waitForAgent(room: Room, timeoutMs: number): Promise<boolean> {
  const isAgent = (p: Participant) =>
    p.kind === ParticipantKind.AGENT || p.isAgent || (p.identity || '').startsWith('agent-')
  if ([...room.remoteParticipants.values()].some(isAgent)) return Promise.resolve(true)
  return new Promise((resolve) => {
    const timer = window.setTimeout(() => {
      room.off(RoomEvent.ParticipantConnected, onJoin)
      resolve([...room.remoteParticipants.values()].some(isAgent))
    }, timeoutMs)
    const onJoin = (p: Participant) => {
      if (!isAgent(p)) return
      window.clearTimeout(timer)
      room.off(RoomEvent.ParticipantConnected, onJoin)
      resolve(true)
    }
    room.on(RoomEvent.ParticipantConnected, onJoin)
  })
}

/** Keep remote audio elements off-screen but not display:none (browsers mute that). */
function remoteAudioHost(): HTMLElement {
  let host = document.getElementById('lk-remote-audio')
  if (!host) {
    host = document.createElement('div')
    host.id = 'lk-remote-audio'
    host.setAttribute('aria-hidden', 'true')
    host.style.cssText =
      'position:fixed;width:1px;height:1px;left:-9999px;overflow:hidden;pointer-events:none;'
    document.body.appendChild(host)
  }
  return host
}

function attachRemoteAudio(track: { kind: Track.Kind; attach: () => HTMLMediaElement }): void {
  if (track.kind !== Track.Kind.Audio) return
  const el = track.attach()
  el.autoplay = true
  el.playsInline = true
  el.setAttribute('playsinline', 'true')
  el.muted = false
  el.volume = 1
  remoteAudioHost().appendChild(el)
  void el.play().catch(() => {
    /* unlocked via room.startAudio() / Enable sound */
  })
}

function attachAllRemoteAudio(room: Room): void {
  for (const p of room.remoteParticipants.values()) {
    for (const pub of p.audioTrackPublications.values()) {
      if (pub.track) attachRemoteAudio(pub.track)
    }
  }
}

function attachMicMeter(
  track: LocalAudioTrack,
  onLevel: (level: number) => void,
): () => void {
  const media = track.mediaStreamTrack
  const stream = new MediaStream([media])
  const ctx = new AudioContext()
  const source = ctx.createMediaStreamSource(stream)
  const analyser = ctx.createAnalyser()
  analyser.fftSize = 256
  source.connect(analyser)
  const data = new Uint8Array(analyser.frequencyBinCount)
  let raf = 0
  const tick = () => {
    analyser.getByteFrequencyData(data)
    let sum = 0
    for (let i = 0; i < data.length; i++) sum += data[i]
    onLevel(Math.min(1, sum / (data.length * 128)))
    raf = requestAnimationFrame(tick)
  }
  void ctx.resume()
  raf = requestAnimationFrame(tick)
  return () => {
    cancelAnimationFrame(raf)
    void ctx.close()
  }
}

export function TalkPage({ apiBase = '' }: Props) {
  const [status, setStatus] = useState('Ready')
  const [live, setLive] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lines, setLines] = useState<TranscriptLine[]>([])
  const [micLevel, setMicLevel] = useState(0)
  const [micLive, setMicLive] = useState(false)
  const [audioBlocked, setAudioBlocked] = useState(false)
  const roomRef = useRef<Room | null>(null)
  const micCleanupRef = useRef<(() => void) | null>(null)
  const logRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [lines])

  useEffect(() => {
    return () => {
      micCleanupRef.current?.()
      micCleanupRef.current = null
    }
  }, [])

  const start = async () => {
    if (busy || live) return
    setBusy(true)
    setError(null)
    setLines([])
    setMicLive(false)
    setMicLevel(0)
    setStatus('Requesting microphone…')
    try {
      const res = await fetch(`${apiBase}/api/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ greeting_context: 'web_session' }),
      })
      if (!res.ok) {
        throw new Error((await res.text()) || res.statusText)
      }
      const data: TokenResponse = await res.json()

      // adaptiveStream/dynacast add ICE churn on local Docker LiveKit; keep simple.
      const room = new Room({ adaptiveStream: false, dynacast: false })
      roomRef.current = room

      const pushLine = (line: TranscriptLine) => {
        if (!line.text.trim() && !line.final) return
        setLines((prev) => upsertTranscriptLine(prev, line))
      }

      room.registerTextStreamHandler(TOPIC_TRANSCRIPTION, async (reader, participantInfo) => {
        const attrs = reader.info.attributes ?? {}
        const segmentId = attrs[ATTR_SEGMENT_ID] || reader.info.id || crypto.randomUUID()
        const trackId = attrs[ATTR_TRACK_ID]
        const who = whoFor(room, participantInfo?.identity, trackId)
        let text = ''
        for await (const chunk of reader) {
          text += chunk
          pushLine({ id: segmentId, who, text, final: false })
        }
        const finalAttrs = reader.info.attributes ?? {}
        const final = finalAttrs[ATTR_FINAL] !== 'false'
        pushLine({ id: segmentId, who, text, final })
      })

      // Do not also listen to TranscriptionReceived — same segments arrive on
      // lk.transcription with different ids and produced duplicate YOU/LENA bubbles.

      room.on(RoomEvent.TrackSubscribed, (track) => {
        attachRemoteAudio(track)
      })
      room.on(RoomEvent.TrackUnsubscribed, (track) => {
        track.detach().forEach((el) => el.remove())
      })
      room.on(RoomEvent.AudioPlaybackStatusChanged, () => {
        setAudioBlocked(!room.canPlaybackAudio)
        if (room.canPlaybackAudio) {
          attachAllRemoteAudio(room)
        }
      })
      room.on(RoomEvent.Disconnected, () => {
        micCleanupRef.current?.()
        micCleanupRef.current = null
        setMicLive(false)
        setMicLevel(0)
        setAudioBlocked(false)
        setLive(false)
        setBusy(false)
        setStatus('Disconnected')
        roomRef.current = null
        document.getElementById('lk-remote-audio')?.replaceChildren()
      })

      setStatus('Connecting to LiveKit…')
      await room.connect(data.url, data.token)

      // Unlock playback while still in the Start-button user-gesture chain.
      // Agent audio often arrives later; without this, Chrome intermittently mutes it.
      try {
        await room.startAudio()
        setAudioBlocked(!room.canPlaybackAudio)
      } catch {
        setAudioBlocked(true)
      }

      setStatus('Publishing microphone…')
      const micTrack = await publishMicrophone(room)
      setMicLive(true)
      micCleanupRef.current = attachMicMeter(micTrack, setMicLevel)

      setStatus('Waiting for Lena to join…')
      const agentJoined = await waitForAgent(room, 20_000)
      if (!agentJoined) {
        throw new Error(
          'Lena did not join the room (voice worker offline). Keep the agent running, then retry.',
        )
      }

      attachAllRemoteAudio(room)
      try {
        await room.startAudio()
        setAudioBlocked(!room.canPlaybackAudio)
      } catch {
        setAudioBlocked(true)
      }

      setLive(true)
      setStatus(
        room.canPlaybackAudio
          ? 'Mic live — speak with Lena'
          : 'Connected — tap Enable sound if you cannot hear Lena',
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      const nice =
        /Permission|NotAllowed|NotFound|NotReadable/i.test(msg)
          ? 'Microphone blocked or unavailable — allow mic access for this site and retry.'
          : msg
      setError(nice)
      setStatus('Failed')
      const room = roomRef.current
      roomRef.current = null
      if (room) void room.disconnect()
    } finally {
      setBusy(false)
    }
  }

  const stop = async () => {
    micCleanupRef.current?.()
    micCleanupRef.current = null
    setMicLive(false)
    setMicLevel(0)
    setAudioBlocked(false)
    const room = roomRef.current
    roomRef.current = null
    if (room) await room.disconnect()
    document.getElementById('lk-remote-audio')?.replaceChildren()
    setLive(false)
    setStatus('Ended')
  }

  const enableSound = async () => {
    const room = roomRef.current
    if (!room) return
    try {
      await room.startAudio()
      attachAllRemoteAudio(room)
      setAudioBlocked(!room.canPlaybackAudio)
      if (room.canPlaybackAudio) setStatus('Mic live — speak with Lena')
    } catch {
      setAudioBlocked(true)
    }
  }

  return (
    <div style={shell}>
      <header style={header}>
        <h1 style={title}>Lena</h1>
        <p style={lead}>Live conversation — her words on the left, yours on the right.</p>
        <div style={actions}>
          <button type="button" onClick={start} disabled={busy || live} style={btn}>
            Start talking
          </button>
          <button type="button" onClick={stop} disabled={!live} style={{ ...btn, ...btnSecondary }}>
            End
          </button>
          {live && audioBlocked ? (
            <button type="button" onClick={enableSound} style={{ ...btn, ...btnSound }}>
              Enable sound
            </button>
          ) : null}
        </div>
        <div style={micRow} aria-label="Microphone level">
          <span style={micLabel}>{micLive ? 'Mic' : 'Mic off'}</span>
          <div style={micBarTrack}>
            <div
              style={{
                ...micBarFill,
                width: `${Math.round(micLevel * 100)}%`,
                opacity: micLive ? 1 : 0.35,
              }}
            />
          </div>
        </div>
        <p style={{ ...statusStyle, ...(error ? statusErr : live ? statusLive : null) }}>
          {error ?? status}
        </p>
      </header>

      <div ref={logRef} style={transcript} aria-live="polite">
        {lines.length === 0 ? (
          <p style={emptyHint}>
            {live
              ? 'Speak — the mic bar should move. Your words appear on the right.'
              : 'Transcripts appear here once you connect.'}
          </p>
        ) : (
          lines.map((line) => (
            <div
              key={line.id}
              style={{
                ...row,
                justifyContent: line.who === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  ...bubble,
                  ...(line.who === 'user' ? bubbleUser : bubbleAgent),
                  ...(line.final ? null : bubbleInterim),
                }}
              >
                <div style={whoLabel}>{line.who === 'user' ? 'You' : 'Lena'}</div>
                {line.text || '…'}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

const shell: React.CSSProperties = {
  minHeight: '100vh',
  display: 'flex',
  flexDirection: 'column',
  background: 'linear-gradient(160deg, #1a1410, #2a2118)',
  color: '#f3e8d8',
  fontFamily: '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif',
}
const header: React.CSSProperties = {
  padding: '1.5rem 1.25rem 0.75rem',
  textAlign: 'center',
  borderBottom: '1px solid rgba(243, 232, 216, 0.1)',
}
const title: React.CSSProperties = {
  margin: '0 0 0.35rem',
  fontSize: 'clamp(2rem, 6vw, 2.8rem)',
  fontWeight: 600,
}
const lead: React.CSSProperties = { margin: '0 0 1rem', color: '#b8a894', fontSize: '0.95rem' }
const actions: React.CSSProperties = {
  display: 'flex',
  gap: '0.75rem',
  flexWrap: 'wrap',
  justifyContent: 'center',
}
const btn: React.CSSProperties = {
  appearance: 'none',
  border: '1px solid rgba(243, 232, 216, 0.12)',
  background: 'rgba(196, 120, 90, 0.18)',
  color: '#f3e8d8',
  font: 'inherit',
  fontSize: '1rem',
  padding: '0.75rem 1.25rem',
  cursor: 'pointer',
}
const btnSecondary: React.CSSProperties = { background: 'transparent' }
const btnSound: React.CSSProperties = {
  background: '#5c4030',
  borderColor: '#c4a574',
}
const micRow: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.6rem',
  justifyContent: 'center',
  marginTop: '0.85rem',
}
const micLabel: React.CSSProperties = {
  fontSize: '0.75rem',
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: '#b8a894',
  width: '3.5rem',
  textAlign: 'right',
}
const micBarTrack: React.CSSProperties = {
  width: 'min(16rem, 55vw)',
  height: '0.45rem',
  borderRadius: '999px',
  background: 'rgba(243, 232, 216, 0.12)',
  overflow: 'hidden',
}
const micBarFill: React.CSSProperties = {
  height: '100%',
  background: '#c4785a',
  transition: 'width 60ms linear',
}
const statusStyle: React.CSSProperties = {
  margin: '0.75rem 0 0',
  color: '#b8a894',
  fontSize: '0.9rem',
  minHeight: '1.25rem',
}
const statusLive: React.CSSProperties = { color: '#9ec7a0' }
const statusErr: React.CSSProperties = { color: '#e8a090' }
const transcript: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  padding: '1.25rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.75rem',
  maxWidth: '42rem',
  width: '100%',
  margin: '0 auto',
  boxSizing: 'border-box',
}
const emptyHint: React.CSSProperties = { color: '#8a7a68', textAlign: 'center', marginTop: '2rem' }
const row: React.CSSProperties = { display: 'flex', width: '100%' }
const bubble: React.CSSProperties = {
  maxWidth: '85%',
  padding: '0.7rem 0.95rem',
  borderRadius: '1rem',
  textAlign: 'left',
  lineHeight: 1.45,
  fontSize: '1.05rem',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
}
const bubbleAgent: React.CSSProperties = {
  background: 'rgba(243, 232, 216, 0.08)',
  border: '1px solid rgba(243, 232, 216, 0.14)',
  borderBottomLeftRadius: '0.25rem',
}
const bubbleUser: React.CSSProperties = {
  background: 'rgba(196, 120, 90, 0.28)',
  border: '1px solid rgba(196, 120, 90, 0.35)',
  borderBottomRightRadius: '0.25rem',
}
const bubbleInterim: React.CSSProperties = { opacity: 0.72 }
const whoLabel: React.CSSProperties = {
  fontSize: '0.7rem',
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: '#b8a894',
  marginBottom: '0.25rem',
}
