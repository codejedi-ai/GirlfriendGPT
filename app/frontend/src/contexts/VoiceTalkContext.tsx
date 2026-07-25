import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

type VoiceTalkContextValue = {
  open: boolean
  companionName: string
  agentId?: string
  /** When true, VoiceChatModal should call start() as soon as it mounts. */
  autoStart: boolean
  /** Token greeting_context — reminder_call for companion check-ups. */
  greetingContext: string
  openTalk: (
    companionName?: string,
    agentId?: string,
    opts?: { autoStart?: boolean; greetingContext?: string },
  ) => void
  closeTalk: () => void
  clearAutoStart: () => void
}

const VoiceTalkContext = createContext<VoiceTalkContextValue | null>(null)

export function VoiceTalkProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [companionName, setCompanionName] = useState('Lena Van Der Meer')
  const [agentId, setAgentId] = useState<string | undefined>(undefined)
  const [autoStart, setAutoStart] = useState(false)
  const [greetingContext, setGreetingContext] = useState('web_session')

  const openTalk = useCallback(
    (
      name?: string,
      id?: string,
      opts?: { autoStart?: boolean; greetingContext?: string },
    ) => {
      setCompanionName((name || 'Lena Van Der Meer').trim() || 'Lena Van Der Meer')
      setAgentId(id?.trim() || undefined)
      setAutoStart(Boolean(opts?.autoStart))
      setGreetingContext(
        (opts?.greetingContext || (opts?.autoStart ? 'reminder_call' : 'web_session')).trim() ||
          'web_session',
      )
      setOpen(true)
    },
    [],
  )

  const closeTalk = useCallback(() => {
    setOpen(false)
    setAutoStart(false)
    setGreetingContext('web_session')
  }, [])

  const clearAutoStart = useCallback(() => setAutoStart(false), [])

  const value = useMemo(
    () => ({
      open,
      companionName,
      agentId,
      autoStart,
      greetingContext,
      openTalk,
      closeTalk,
      clearAutoStart,
    }),
    [open, companionName, agentId, autoStart, greetingContext, openTalk, closeTalk, clearAutoStart],
  )

  return <VoiceTalkContext.Provider value={value}>{children}</VoiceTalkContext.Provider>
}

export function useVoiceTalk(): VoiceTalkContextValue {
  const ctx = useContext(VoiceTalkContext)
  if (!ctx) {
    throw new Error('useVoiceTalk must be used within VoiceTalkProvider')
  }
  return ctx
}
