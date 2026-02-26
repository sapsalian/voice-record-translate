import { useState } from 'react';
import { MainPage } from './pages/MainPage';
import { SettingsPage } from './pages/SettingsPage';

type Page = 'main' | 'settings';

function App() {
  const [page, setPage] = useState<Page>('main');

  if (page === 'settings') {
    return <SettingsPage onBack={() => setPage('main')} />;
  }

  return <MainPage onSettingsOpen={() => setPage('settings')} />;
}

export default App;
