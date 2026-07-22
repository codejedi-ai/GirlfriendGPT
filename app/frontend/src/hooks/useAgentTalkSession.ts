import { useCallback, useEffect, useRef, useState } from 'react'
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
} from '@/lib/transcript'
import { fetchTalkToken } from '@/lib/talkToken'

const TOPIC_TRANSCRIPTION = 'lk.transcription'
const TOPIC_CHAT = 'lk.chat'
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

async function publishMicrophone(
  room: Room,
  existing?: LocalAudioTrack,
): Promise<LocalAudioTrack> {
  const track =
    existing ??
    (await createLocalAudioTrack({
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    }))
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

type RemoteAudioLike = {
  kind: Track.Kind
  attach: () => HTMLMediaElement
  attachedElements?: HTMLMediaElement[]
}

async function playMedia(el: HTMLMediaElement): Promise<boolean> {
  el.autoplay = true
  el.playsInline = true
  el.setAttribute('playsinline', 'true')
  el.muted = false
  el.volume = 1
  try {
    await el.play()
    return true
  } catch {
    return false
  }
}

/** Attach once per track; re-play existing elements on later utterances. */
async function attachRemoteAudio(track: RemoteAudioLike): Promise<boolean> {
  if (track.kind !== Track.Kind.Audio) return true
  const attached = (track.attachedElements ?? []).filter((el) => el.isConnected)
  if (attached.length > 0) {
    const results = await Promise.all(attached.map(playMedia))
    return results.every(Boolean)
  }
  const el = track.attach()
  remoteAudioHost().appendChild(el)
  return playMedia(el)
}

/** Unlock autoplay + re-attach/replay every remote audio track. */
async function ensureRemotePlayback(room: Room): Promise<boolean> {
  try {
    await room.startAudio()
  } catch {
    /* browser may still block until a fresh gesture */
  }
  let ok = room.canPlaybackAudio
  for (const p of room.remoteParticipants.values()) {
    for (const pub of p.audioTrackPublications.values()) {
      if (pub.track) {
        const played = await attachRemoteAudio(pub.track)
        ok = ok && played
      }
    }
  }
  for (const el of remoteAudioHost().querySelectorAll('audio')) {
    const played = await playMedia(el)
    ok = ok && played
  }
  return ok
}

/** Local mic level meter — starts as soon as the track exists (on Start Talking). */
function attachLocalMicMeter(
  track: LocalAudioTrack,
  onLevel: (level: number) => void,
): () => void {
  const media = track.mediaStreamTrack
  if (!media) {
    onLevel(0)
    return () => {}
  }

  // Own clone so LiveKit publish / mute does not starve the analyser.
  const probe = media.clone()
  probe.enabled = true
  const stream = new MediaStream([probe])
  const ctx = new AudioContext()
  const source = ctx.createMediaStreamSource(stream)
  const analyser = ctx.createAnalyser()
  analyser.fftSize = 2048
  analyser.smoothingTimeConstant = 0.25
  source.connect(analyser)

  const data = new Float32Array(analyser.fftSize)
  let raf = 0
  let display = 0
  let stopped = false

  const tick = () => {
    if (stopped) return
    if (track.isMuted || !probe.enabled) {
      display *= 0.75
      onLevel(display < 0.02 ? 0 : display)
      raf = requestAnimationFrame(tick)
      return
    }
    analyser.getFloatTimeDomainData(data)
    let sum = 0
    for (let i = 0; i < data.length; i++) sum += data[i] * data[i]
    const rms = Math.sqrt(sum / data.length)
    // Map quiet speech into a visible 0–1 range.
    const target = Math.min(1, Math.pow(rms * 8, 0.6))
    display =
      target > display ? display * 0.2 + target * 0.8 : display * 0.7 + target * 0.3
    onLevel(display < 0.02 ? 0 : display)
    raf = requestAnimationFrame(tick)
  }

  void ctx.resume().then(() => {
    if (!stopped) raf = requestAnimationFrame(tick)
  })

  return () => {
    stopped = true
    cancelAnimationFrame(raf)
    try {
      source.disconnect()
    } catch {
      /* ignore */
    }
    probe.stop()
    void ctx.close()
  }
}

export type UseAgentTalkSessionOpts = {
  companionName?: string
  agentId?: string
}

/**
 * GirlfriendGPT voice session: token → LiveKit → agent + live transcripts.
 */
export function useAgentTalkSession(opts: UseAgentTalkSessionOpts = {}) {
  const companionName = opts.companionName?.trim() || 'Lena'
  const agentId = opts.agentId?.trim() || undefined
  const [status, setStatus] = useState('Ready')
  const [live, setLive] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lines, setLines] = useState<TranscriptLine[]>([])
  const [micLevel, setMicLevel] = useState(0)
  const [agentLevel, setAgentLevel] = useState(0)
  const [micLive, setMicLive] = useState(false)
  const [audioBlocked, setAudioBlocked] = useState(false)
  const roomRef = useRef<Room | null>(null)
  const micTrackRef = useRef<LocalAudioTrack | null>(null)
  const micCleanupRef = useRef<(() => void) | null>(null)
  const agentMeterCleanupRef = useRef<(() => void) | null>(null)
  const kickAudioRef = useRef<() => void>(() => {})
  const kickAudioAtRef = useRef(0)
  const [micMuted, setMicMuted] = useState(false)
  const [sendingText, setSendingText] = useState(false)

  useEffect(() => {
    return () => {
      micCleanupRef.current?.()
      micCleanupRef.current = null
      agentMeterCleanupRef.current?.()
      agentMeterCleanupRef.current = null
      const room = roomRef.current
      roomRef.current = null
      if (room) void room.disconnect()
      document.getElementById('lk-remote-audio')?.replaceChildren()
    }
  }, [])

  const start = useCallback(async () => {
    if (busy || live) return
    setBusy(true)
    setError(null)
    setLines([])
    setMicLevel(0)
    setAgentLevel(0)
    setAudioBlocked(false)
    setMicMuted(false)

    // Show talk UI + green status immediately on click.
    setLive(true)
    setStatus(`Mic live — speak with ${companionName}`)

    let micTrack: LocalAudioTrack | null = null
    try {
      // Open mic + start bars in the same click gesture (before network).
      micTrack = await createLocalAudioTrack({
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      })
      micTrackRef.current = micTrack
      setMicLive(true)
      micCleanupRef.current?.()
      micCleanupRef.current = attachLocalMicMeter(micTrack, setMicLevel)

      const data = await fetchTalkToken({
        greeting_context: 'web_session',
        agent_id: agentId,
      })
      if (data.reused) {
        setStatus(`Rejoining ${companionName}…`)
      }

      const room = new Room({ adaptiveStream: false, dynacast: false })
      roomRef.current = room

      const kickAudio = (force = false) => {
        const now = Date.now()
        if (!force && now - kickAudioAtRef.current < 400) return
        kickAudioAtRef.current = now
        void ensureRemotePlayback(room).then((ok) => {
          if (roomRef.current !== room) return
          setAudioBlocked(!ok || !room.canPlaybackAudio)
        })
      }
      kickAudioRef.current = () => kickAudio(true)

      const pushLine = (line: TranscriptLine) => {
        if (!line.text.trim() && !line.final) return
        setLines((prev) => upsertTranscriptLine(prev, line))
        if (line.who === 'agent') kickAudio()
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

      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind !== Track.Kind.Audio) return
        void attachRemoteAudio(track).then((played) => {
          if (!played) setAudioBlocked(true)
          kickAudio()
        })
      })
      room.on(RoomEvent.TrackUnsubscribed, (track) => {
        track.detach().forEach((el) => el.remove())
      })
      room.on(RoomEvent.TrackUnmuted, (pub) => {
        if (pub.kind === Track.Kind.Audio) kickAudio()
      })
      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        if (speakers.some((p) => p !== room.localParticipant)) kickAudio()
      })
      room.on(RoomEvent.AudioPlaybackStatusChanged, () => {
        setAudioBlocked(!room.canPlaybackAudio)
        if (room.canPlaybackAudio) kickAudio()
      })
      room.on(RoomEvent.Disconnected, () => {
        micCleanupRef.current?.()
        micCleanupRef.current = null
        agentMeterCleanupRef.current?.()
        agentMeterCleanupRef.current = null
        micTrackRef.current = null
        kickAudioRef.current = () => {}
        setMicLive(false)
        setMicMuted(false)
        setMicLevel(0)
        setAgentLevel(0)
        setAudioBlocked(false)
        setSendingText(false)
        setLive(false)
        setBusy(false)
        setStatus('Disconnected')
        roomRef.current = null
        document.getElementById('lk-remote-audio')?.replaceChildren()
      })

      await room.connect(data.url, data.token)
      await publishMicrophone(room, micTrack)
      kickAudio(true)

      if (!room.canPlaybackAudio) {
        setStatus(`Mic live — tap Enable sound if you cannot hear ${companionName}`)
        setAudioBlocked(true)
      }

      const agentJoined = await waitForAgent(room, 20_000)
      if (!agentJoined) {
        throw new Error(
          `${companionName} did not join (voice worker offline). Keep the agent running, then retry.`,
        )
      }

      kickAudio(true)
      setStatus(
        room.canPlaybackAudio
          ? `Mic live — speak with ${companionName}`
          : `Mic live — tap Enable sound if you cannot hear ${companionName}`,
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      const nice = /Permission|NotAllowed|NotFound|NotReadable/i.test(msg)
        ? 'Microphone blocked or unavailable — allow mic access for this site and retry.'
        : msg
      setError(nice)
      setStatus('Failed')
      micCleanupRef.current?.()
      micCleanupRef.current = null
      if (micTrack) {
        micTrack.stop()
        micTrackRef.current = null
      }
      const room = roomRef.current
      roomRef.current = null
      if (room) void room.disconnect()
      setLive(false)
      setMicLive(false)
      setMicLevel(0)
    } finally {
      setBusy(false)
    }
  }, [busy, live, companionName, agentId])

  const stop = useCallback(async () => {
    micCleanupRef.current?.()
    micCleanupRef.current = null
    agentMeterCleanupRef.current?.()
    agentMeterCleanupRef.current = null
    micTrackRef.current = null
    kickAudioRef.current = () => {}
    setMicLive(false)
    setMicMuted(false)
    setMicLevel(0)
    setAgentLevel(0)
    setAudioBlocked(false)
    setSendingText(false)
    const room = roomRef.current
    roomRef.current = null
    if (room) await room.disconnect()
    document.getElementById('lk-remote-audio')?.replaceChildren()
    setLive(false)
    setStatus('Ended')
  }, [])

  const setMicrophoneMuted = useCallback(async (muted: boolean) => {
    const track = micTrackRef.current
    if (!track) return
    if (muted) await track.mute()
    else await track.unmute()
    setMicMuted(muted)
    setMicLive(!muted)
    if (muted) setMicLevel(0)
  }, [])

  const sendChat = useCallback(async (raw: string) => {
    const text = raw.trim()
    const room = roomRef.current
    if (!text || !room || !live) return
    setSendingText(true)
    try {
      const id = crypto.randomUUID()
      setLines((prev) =>
        upsertTranscriptLine(prev, { id, who: 'user', text, final: true }),
      )
      await room.localParticipant.sendText(text, { topic: TOPIC_CHAT })
      kickAudioRef.current()
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(`Text send failed: ${msg}`)
    } finally {
      setSendingText(false)
    }
  }, [live])

  const enableSound = useCallback(async () => {
    const room = roomRef.current
    if (!room) return
    const ok = await ensureRemotePlayback(room)
    setAudioBlocked(!ok || !room.canPlaybackAudio)
    if (ok && room.canPlaybackAudio) {
      setStatus(`Mic live — speak with ${companionName}`)
    }
  }, [companionName])

  return {
    status,
    live,
    busy,
    error,
    lines,
    micLevel,
    agentLevel,
    micLive,
    micMuted,
    audioBlocked,
    sendingText,
    companionName,
    start,
    stop,
    enableSound,
    sendChat,
    setMicrophoneMuted,
  }
}
