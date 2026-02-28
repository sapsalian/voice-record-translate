import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { ViewerPage } from './pages/ViewerPage.tsx'
import { fetchConfig, fetchSessions } from './api/client'
import type { Session } from './types/session'
import { TooltipProvider } from '@/components/ui/tooltip'
import { LocaleProvider } from './LocaleContext'

function Root() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [uiLang, setUiLang] = useState('ko')
  const location = useLocation()

  useEffect(() => {
    fetchSessions().then(setSessions).catch(() => {})
    fetchConfig().then((c) => setUiLang(c.ui_lang)).catch(() => {})
  }, [])

  return (
    <LocaleProvider lang={uiLang}>
      <TooltipProvider delayDuration={600}>
        <div key={location.pathname} style={{ animation: 'page-fade-in 150ms ease' }}>
          <Routes>
            <Route
              path="/"
              element={
                <App
                  sessions={sessions}
                  setSessions={setSessions}
                  onUiLangChange={setUiLang}
                />
              }
            />
            <Route path="/viewer/:sessionId" element={<ViewerPage />} />
          </Routes>
        </div>
      </TooltipProvider>
    </LocaleProvider>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Root />
    </BrowserRouter>
  </StrictMode>,
)
