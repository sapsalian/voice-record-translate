import { useState } from 'react';
import { MainPage } from './pages/MainPage';
import { SettingsPage } from './pages/SettingsPage';
import type { Session } from './types/session';

type Page = 'main' | 'settings';

interface Props {
  sessions: Session[];
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>;
}

function App({ sessions, setSessions }: Props) {
  const [page, setPage] = useState<Page>('main');

  if (page === 'settings') {
    return <SettingsPage onBack={() => setPage('main')} />;
  }

  return (
    <MainPage
      sessions={sessions}
      setSessions={setSessions}
      onSettingsOpen={() => setPage('settings')}
    />
  );
}

export default App;
