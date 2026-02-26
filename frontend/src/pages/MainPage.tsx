import { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { SessionList } from '@/components/SessionList';
import { deleteSession, fetchSessions, startProcessing } from '@/api/client';
import { fetchConfig } from '@/api/client';
import type { Session } from '@/types/session';

declare global {
  interface Window {
    pywebview?: {
      api: {
        open_file_dialog(): Promise<string | null>;
      };
    };
  }
}

interface Props {
  onSettingsOpen: () => void;
}

export function MainPage({ onSettingsOpen }: Props) {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch(() => {});
  }, []);

  const handleUpdate = useCallback((updated: Session) => {
    setSessions((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
  }, []);

  const handleDelete = useCallback(
    async (id: string) => {
      await deleteSession(id).catch(() => {});
      setSessions((prev) => prev.filter((s) => s.id !== id));
    },
    [],
  );

  const handleAddFile = async () => {
    let filePath: string | null = null;

    if (window.pywebview?.api) {
      filePath = await window.pywebview.api.open_file_dialog();
    } else {
      // Dev mode: prompt for path
      filePath = window.prompt('파일 경로를 입력하세요 (개발 모드)');
    }

    if (!filePath) return;

    const config = await fetchConfig().catch(() => ({ target_lang: 'ko' }));
    const { id } = await startProcessing(filePath, config.target_lang);
    const updated = await fetchSessions();
    setSessions(updated);
    void id; // id used via fetchSessions refresh
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b px-4 h-14 flex items-center justify-between">
        <h1 className="font-semibold text-lg">VRT</h1>
        <div className="flex gap-2">
          <Button onClick={handleAddFile}>파일 추가</Button>
          <Button variant="ghost" size="icon" onClick={onSettingsOpen} aria-label="설정">
            ⚙
          </Button>
        </div>
      </header>
      <main className="px-4 py-6">
        <SessionList sessions={sessions} onUpdate={handleUpdate} onDelete={handleDelete} />
      </main>
    </div>
  );
}
