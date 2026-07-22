import { useEffect, useRef, useState } from 'react'

// Self-improving scraper bot UI. Talks only to the harness API on the same
// origin (/api/v1/harness/*) — no auth, no other backend endpoints — so it
// works standalone wherever the harness app is served.

type Reply = {
  text: string
  kind?: string
  harness_hit?: string | null
  promoted?: string[]
  generated?: string[]
}

type State = {
  mode?: Record<string, string>
  workflows?: { id: string; status: string; steps: number; hits: number }[]
  generated_tools?: string[]
  traces?: number
  worker?: { handled: number; tickets_opened: number }
}

type Msg =
  | { who: 'you'; text: string }
  | { who: 'bot'; reply: Reply }

const EXAMPLES = [
  'scrape https://sfbay.craigslist.org/search/apa',
  'can you scrape the listings at https://newyork.craigslist.org/search/apa',
  'what is the capital of france',
]

function kindColor(kind?: string): string {
  if (kind === 'warm') return '#13301f'
  if (kind === 'cold') return '#3a2a12'
  if (kind === 'error') return '#3a1518'
  return '#2a2030'
}
function kindFg(kind?: string): string {
  if (kind === 'warm') return '#5fd38d'
  if (kind === 'cold') return '#f0a94c'
  if (kind === 'error') return '#f06c75'
  return '#c08be0'
}

export function HarnessPage() {
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [state, setState] = useState<State>({})
  const logRef = useRef<HTMLDivElement>(null)

  const refreshState = async () => {
    try {
      const r = await fetch('/api/v1/harness/state')
      setState(await r.json())
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    refreshState()
  }, [])

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight })
  }, [msgs])

  const send = async (text: string) => {
    if (!text.trim() || busy) return
    setInput('')
    setMsgs((m) => [...m, { who: 'you', text }])
    setBusy(true)
    try {
      const r = await fetch('/api/v1/harness/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const reply: Reply = await r.json()
      setMsgs((m) => [...m, { who: 'bot', reply }])
    } catch {
      setMsgs((m) => [...m, { who: 'bot', reply: { text: 'network error', kind: 'error' } }])
    } finally {
      setBusy(false)
      refreshState()
    }
  }

  const reset = async () => {
    await fetch('/api/v1/harness/reset', { method: 'POST' })
    setMsgs([])
    refreshState()
  }

  const mono = 'ui-monospace, SFMono-Regular, Menlo, monospace'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0f1115', color: '#e6e6e6', fontFamily: mono, fontSize: 14 }}>
      <header style={{ padding: '14px 18px', borderBottom: '1px solid #232733', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
        <strong style={{ fontSize: 15 }}>🧠 self-improving scraper</strong>
        <span style={{ color: '#8b93a7', fontSize: 12 }}>
          {state.mode
            ? `bus:${state.mode.bus} · store:${state.mode.store} · reg:${state.mode.registry} · llm:${state.mode.llm} · scraper:${state.mode.scraper}`
            : 'loading…'}
        </span>
        <span style={{ flex: 1 }} />
        <button onClick={reset} style={btn}>reset learned state</button>
      </header>

      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div ref={logRef} style={{ flex: 1, overflowY: 'auto', padding: 18 }}>
            {msgs.length === 0 && (
              <div style={{ color: '#8b93a7', fontSize: 12 }}>
                Send a scrape command 3× to train, then it replays from the learned tool.
                Craigslist works live; big aggregators (Zillow/Redfin) block bots.
                {EXAMPLES.map((e) => (
                  <code key={e} onClick={() => setInput(e)} style={exampleCode}>{e}</code>
                ))}
              </div>
            )}
            {msgs.map((m, i) =>
              m.who === 'you' ? (
                <div key={i} style={{ marginBottom: 14 }}>
                  <span style={{ color: '#7aa2f7' }}>▸ {m.text}</span>
                </div>
              ) : (
                <div key={i} style={{ marginBottom: 14 }}>
                  <span style={{ ...badge, background: kindColor(m.reply.kind), color: kindFg(m.reply.kind) }}>
                    {(m.reply.kind || 'bot').toUpperCase()}
                  </span>
                  <div style={botBubble}>{m.reply.text || '(empty)'}</div>
                  <div style={{ color: '#6b7280', fontSize: 11, marginTop: 6 }}>
                    {m.reply.harness_hit ? `· ${m.reply.harness_hit}` : ''}
                  </div>
                  {m.reply.promoted && m.reply.promoted.length > 0 && (
                    <div style={{ color: '#5fd38d', fontSize: 12, marginTop: 8 }}>
                      ✦ promoted: {m.reply.promoted.join(', ')}
                      {m.reply.generated && m.reply.generated.length > 0 ? ` → code-genned: ${m.reply.generated.join(', ')}` : ''}
                    </div>
                  )}
                </div>
              ),
            )}
            {busy && <div style={{ color: '#8b93a7' }}>… working (real fetch + LLM)</div>}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              send(input)
            }}
            style={{ display: 'flex', gap: 8, padding: '14px 18px', borderTop: '1px solid #232733' }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="scrape https://sfbay.craigslist.org/search/apa"
              autoFocus
              style={inputStyle}
            />
            <button type="submit" disabled={busy} style={btn}>send</button>
          </form>
        </div>

        <div style={{ width: 300, borderLeft: '1px solid #232733', padding: 16, overflowY: 'auto', background: '#0c0e12' }}>
          <h3 style={h3}>learned state</h3>
          <div style={{ color: '#9aa3b5', fontSize: 12 }}>
            traces: {state.traces ?? 0}
            <br />
            tickets opened: {state.worker?.tickets_opened ?? 0}
            <h3 style={h3}>workflows</h3>
            {!state.workflows || state.workflows.length === 0 ? (
              <span>none yet — send 3 scrapes</span>
            ) : (
              state.workflows.map((w) => (
                <div key={w.id} style={wfBox}>
                  {w.id}
                  <br />
                  status: {w.status} · steps: {w.steps} · hits: {w.hits}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

const btn: React.CSSProperties = { background: '#2a3142', color: '#e6e6e6', border: '1px solid #3a4254', padding: '10px 14px', borderRadius: 8, cursor: 'pointer', font: 'inherit' }
const inputStyle: React.CSSProperties = { flex: 1, background: '#161922', border: '1px solid #2a2f3c', color: '#e6e6e6', padding: '10px 12px', borderRadius: 8, font: 'inherit' }
const badge: React.CSSProperties = { display: 'inline-block', fontSize: 11, padding: '1px 8px', borderRadius: 999, marginRight: 6, fontWeight: 600 }
const botBubble: React.CSSProperties = { whiteSpace: 'pre-wrap', background: '#161922', border: '1px solid #232733', borderRadius: 8, padding: '10px 12px', marginTop: 4 }
const h3: React.CSSProperties = { fontSize: 12, textTransform: 'uppercase', letterSpacing: '.06em', color: '#6b7280', margin: '18px 0 8px' }
const wfBox: React.CSSProperties = { background: '#13301f', border: '1px solid #1e4a30', borderRadius: 6, padding: '8px 10px', marginBottom: 6, fontSize: 12 }
const exampleCode: React.CSSProperties = { color: '#7aa2f7', cursor: 'pointer', display: 'block', margin: '3px 0' }
