import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { ViewerPage } from './pages/ViewerPage.tsx'
import { fetchSessions } from './api/client'
import type { Session } from './types/session'
import { TooltipProvider } from '@/components/ui/tooltip'

function Root() {
  const [sessions, setSessions] = useState<Session[]>([])
  const location = useLocation()

  useEffect(() => {
    fetchSessions().then(setSessions).catch(() => {})
  }, [])

  return (
    <TooltipProvider delayDuration={600}>
    <div key={location.pathname} style={{ animation: 'page-fade-in 150ms ease' }}>
      <Routes>
        <Route path="/" element={<App sessions={sessions} setSessions={setSessions} />} />
        <Route path="/viewer/:sessionId" element={<ViewerPage />} />
      </Routes>
    </div>
    </TooltipProvider>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Root />
    </BrowserRouter>
  </StrictMode>,
)
