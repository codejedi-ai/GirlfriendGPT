import assert from 'node:assert/strict'
import { resolveWhoFromMeta, upsertTranscriptLine } from './transcript.ts'

const a = upsertTranscriptLine([], { id: '1', who: 'user', text: 'hel', final: false })
assert.equal(a.length, 1)
assert.equal(a[0].text, 'hel')

const b = upsertTranscriptLine(a, { id: '1', who: 'user', text: 'hello', final: true })
assert.equal(b.length, 1)
assert.equal(b[0].text, 'hello')
assert.equal(b[0].final, true)

const c = upsertTranscriptLine(b, { id: '2', who: 'agent', text: 'hi', final: true })
assert.equal(c.length, 2)
assert.equal(c[1].who, 'agent')

// Dual channel: same utterance, different segment ids → one bubble.
const d = upsertTranscriptLine(c, {
  id: 'stream-other',
  who: 'user',
  text: 'hello',
  final: true,
})
assert.equal(d.length, 2, 'exact duplicate who+text must not add a bubble')

const e = upsertTranscriptLine(
  [{ id: 'a', who: 'user', text: '像是是不是要打開那個網頁去做', final: false }],
  { id: 'b', who: 'user', text: '像是是不是要打開那個網頁去做打開網頁去做', final: true },
)
assert.equal(e.length, 1)
assert.equal(e[0].text, '像是是不是要打開那個網頁去做打開網頁去做')

assert.equal(
  resolveWhoFromMeta({
    localIdentity: 'user-1',
    participantIdentity: 'user-1',
    localAudioTrackSids: [],
  }),
  'user',
)
assert.equal(
  resolveWhoFromMeta({
    localIdentity: 'user-1',
    participantIdentity: 'agent-1',
    transcribedTrackId: 'TR_mic',
    localAudioTrackSids: ['TR_mic'],
  }),
  'user',
)
assert.equal(
  resolveWhoFromMeta({
    localIdentity: 'user-1',
    participantIdentity: 'agent-1',
    transcribedTrackId: 'TR_agent',
    localAudioTrackSids: ['TR_mic'],
  }),
  'agent',
)

console.log('transcript tests ok')
