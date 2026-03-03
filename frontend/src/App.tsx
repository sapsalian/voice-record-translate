import { useState } from 'react';
import { MainPage } from './pages/MainPage';
import { SettingsPage } from './pages/SettingsPage';
import { OnboardingPage } from './pages/OnboardingPage';
import type { Session } from './types/session';

type Page = 'main' | 'settings';

interface Props {
  sessions: Session[];
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>;
  onUiLangChange: (lang: string) => void;
  needsOnboarding: boolean;
  initialLang: string;
}

function App({ sessions, setSessions, onUiLangChange, needsOnboarding, initialLang }: Props) {
  const [page, setPage] = useState<Page>('main');

  if (needsOnboarding) {
    return (
      <OnboardingPage
        initialLang={initialLang}
        onComplete={(lang) => {
          onUiLangChange(lang);
        }}
      />
    );
  }

  if (page === 'settings') {
    return <SettingsPage onBack={() => setPage('main')} onUiLangChange={onUiLangChange} />;
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
