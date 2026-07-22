import { TalkPage } from './TalkPage'
import { HarnessPage } from './HarnessPage'

/**
 * GirlfriendGPT frontend (app/frontend).
 *
 * Default: Talk to Lena Van Der Meer.
 *   Frontend → app/backend POST /api/token → Frontend → LiveKit
 *
 * Optional: ?page=harness for the scraper harness UI.
 */
export function App() {
  const page = new URLSearchParams(window.location.search).get('page')
  if (page === 'harness') {
    return <HarnessPage />
  }
  const apiBase = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') ?? ''
  return <TalkPage apiBase={apiBase} />
}
