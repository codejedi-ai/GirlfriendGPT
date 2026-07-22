export type LineWho = 'agent' | 'user'

export type TranscriptLine = {
  id: string
  who: LineWho
  text: string
  final: boolean
}

export function normalizeTranscriptText(text: string): string {
  return text.replace(/\s+/g, ' ').trim()
}

/**
 * Insert or replace a streaming transcript segment.
 * Dedupes by id, and collapses identical (who+text) bubbles from dual LiveKit
 * channels (text stream + TranscriptionReceived) that use different segment ids.
 */
export function upsertTranscriptLine(
  lines: TranscriptLine[],
  next: TranscriptLine,
): TranscriptLine[] {
  const idx = lines.findIndex((l) => l.id === next.id)
  if (idx >= 0) {
    const copy = lines.slice()
    copy[idx] = { ...copy[idx], ...next }
    return copy
  }

  const norm = normalizeTranscriptText(next.text)
  if (norm) {
    const dupIdx = lines.findIndex((l) => {
      if (l.who !== next.who) return false
      const existing = normalizeTranscriptText(l.text)
      if (!existing) return false
      if (existing === norm) return true
      // Streaming: same utterance arriving again with a different id.
      if (!l.final || !next.final) {
        return existing.startsWith(norm) || norm.startsWith(existing)
      }
      return false
    })
    if (dupIdx >= 0) {
      const copy = lines.slice()
      const prev = copy[dupIdx]
      const longer = next.text.length >= prev.text.length ? next.text : prev.text
      copy[dupIdx] = {
        ...prev,
        text: longer,
        final: prev.final || next.final,
      }
      return copy
    }
  }

  return [...lines, next]
}

/**
 * Decide bubble side from LiveKit transcription metadata.
 * Local identity / local mic track → user (right); otherwise agent (left).
 */
export function resolveWhoFromMeta(opts: {
  localIdentity: string
  participantIdentity?: string
  transcribedTrackId?: string
  localAudioTrackSids: string[]
}): LineWho {
  if (opts.participantIdentity && opts.participantIdentity === opts.localIdentity) {
    return 'user'
  }
  if (
    opts.transcribedTrackId &&
    opts.localAudioTrackSids.includes(opts.transcribedTrackId)
  ) {
    return 'user'
  }
  return 'agent'
}
