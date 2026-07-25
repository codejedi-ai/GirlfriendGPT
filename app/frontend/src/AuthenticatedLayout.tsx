import { Outlet } from 'react-router-dom'
import { Sidebar } from '@/components/Sidebar'
import { VoiceChatModal } from '@/components/VoiceChatModal'
import { useVoiceTalk } from '@/contexts/VoiceTalkContext'
import { useState } from 'react'

/**
 * Discover / profile shell. Talk pane opens when VoiceTalkContext.open
 * (e.g. agent voice_call via AgentVoiceBridge WebSocket).
 */
export function AuthenticatedLayout() {
  const {
    open,
    companionName,
    agentId,
    autoStart,
    greetingContext,
    closeTalk,
    clearAutoStart,
  } = useVoiceTalk()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div
      className={`flex bg-[#050714] ${
        open ? 'h-[100dvh] max-h-[100dvh] overflow-hidden' : 'min-h-screen'
      }`}
    >
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((prev) => !prev)}
        mobileOpen={mobileOpen}
        onMobileToggle={() => setMobileOpen((prev) => !prev)}
      />
      <main
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          open ? 'h-full max-h-[100dvh] overflow-hidden' : 'min-h-screen'
        } ${sidebarCollapsed ? 'sm:ml-[72px]' : 'sm:ml-[240px]'}`}
      >
        {open ? (
          <VoiceChatModal
            open={open}
            onClose={closeTalk}
            companionName={companionName}
            agentId={agentId}
            autoStart={autoStart}
            greetingContext={greetingContext}
            onAutoStartConsumed={clearAutoStart}
          />
        ) : (
          <Outlet />
        )}
      </main>
    </div>
  )
}
