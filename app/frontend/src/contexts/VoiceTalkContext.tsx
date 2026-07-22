import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

type VoiceTalkContextValue = {
  open: boolean
  companionName: string
  agentId?: string
  openTalk: (companionName?: string, agentId?: string) => void
  closeTalk: () => void
}

const VoiceTalkContext = createContext<VoiceTalkContextValue | null>(null)

export function VoiceTalkProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [companionName, setCompanionName] = useState('Lena Van Der Meer')
  const [agentId, setAgentId] = useState<string | undefined>(undefined)

  const openTalk = useCallback((name?: string, id?: string) => {
    setCompanionName((name || 'Lena Van Der Meer').trim() || 'Lena Van Der Meer')
    setAgentId(id?.trim() || undefined)
    setOpen(true)
  }, [])

  const closeTalk = useCallback(() => setOpen(false), [])

  const value = useMemo(
    () => ({ open, companionName, agentId, openTalk, closeTalk }),
    [open, companionName, agentId, openTalk, closeTalk],
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
