import { Outlet } from 'react-router-dom'
import { Sidebar } from '@/components/Sidebar'
import { VoiceChatModal } from '@/components/VoiceChatModal'
import { VoiceTalkProvider, useVoiceTalk } from '@/contexts/VoiceTalkContext'
import { HiSignal } from 'react-icons/hi2'
import { useState } from 'react'

function AuthenticatedShell() {
  const { open, companionName, agentId, openTalk, closeTalk } = useVoiceTalk()
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
          />
        ) : (
          <Outlet />
        )}
      </main>

      {!open ? (
        <button
          type="button"
          onClick={() => openTalk('Lena Van Der Meer', 'e11a0000-0000-4000-8000-000000000001')}
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-[#00ffff] to-[#0099cc] flex items-center justify-center shadow-lg shadow-[#00ffff]/20 hover:scale-110 transition-all duration-300 hover:shadow-xl hover:shadow-[#00ffff]/30"
          aria-label="Open voice chat with Lena"
        >
          <HiSignal className="text-black text-xl" />
        </button>
      ) : null}
    </div>
  )
}

export function AuthenticatedLayout() {
  return (
    <VoiceTalkProvider>
      <AuthenticatedShell />
    </VoiceTalkProvider>
  )
}
