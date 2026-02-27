import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { SessionList } from '@/components/SessionList';
import { AddFilesModal } from '@/components/AddFilesModal';
import {
  deleteSession,
  fetchSessions,
  startProcessing,
  uploadAndProcess,
} from '@/api/client';
import type { Session } from '@/types/session';

declare global {
  interface Window {
    pywebview?: {
      api: {
        open_file_dialog(): Promise<string[] | null>;
      };
    };
  }
}

interface Props {
  onSettingsOpen: () => void;
}

type ModalData = {
  fileNames: string[];
  handle: (targetLang: string) => Promise<void>;
};

export function MainPage({ onSettingsOpen }: Props) {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [modalData, setModalData] = useState<ModalData | null>(null);

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch(() => {});
  }, []);

  // Drag-and-drop: use counter to handle enter/leave on child elements
  useEffect(() => {
    let counter = 0;

    const onDragEnter = (e: DragEvent) => {
      e.preventDefault();
      counter++;
      setIsDragOver(true);
    };
    const onDragLeave = () => {
      counter--;
      if (counter <= 0) {
        counter = 0;
        setIsDragOver(false);
      }
    };
    const onDragOver = (e: DragEvent) => e.preventDefault();
    const onDrop = (e: DragEvent) => {
      e.preventDefault();
      counter = 0;
      setIsDragOver(false);
      const files = Array.from(e.dataTransfer?.files ?? []);
      if (files.length === 0) return;
      setModalData({
        fileNames: files.map((f) => f.name),
        handle: async (lang) => {
          await Promise.all(files.map((f) => uploadAndProcess(f, lang)));
          setSessions(await fetchSessions());
        },
      });
    };

    document.addEventListener('dragenter', onDragEnter);
    document.addEventListener('dragleave', onDragLeave);
    document.addEventListener('dragover', onDragOver);
    document.addEventListener('drop', onDrop);
    return () => {
      document.removeEventListener('dragenter', onDragEnter);
      document.removeEventListener('dragleave', onDragLeave);
      document.removeEventListener('dragover', onDragOver);
      document.removeEventListener('drop', onDrop);
    };
  }, []);

  const handleUpdate = useCallback((updated: Session) => {
    setSessions((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    await deleteSession(id).catch(() => {});
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const handleViewSession = (id: string) => {
    navigate('/viewer/' + id);
  };

  const handleAddFile = async () => {
    let paths: string[] | null = null;

    if (window.pywebview?.api) {
      paths = await window.pywebview.api.open_file_dialog();
    } else {
      // Dev mode: prompt for path(s)
      const input = window.prompt('파일 경로 입력 (쉼표 구분, 개발 모드)');
      if (input) {
        paths = input.split(',').map((s) => s.trim()).filter(Boolean);
      }
    }

    if (!paths || paths.length === 0) return;

    const captured = paths;
    setModalData({
      fileNames: captured.map((p) => p.split('/').pop() ?? p),
      handle: async (lang) => {
        await Promise.all(captured.map((p) => startProcessing(p, lang)));
        setSessions(await fetchSessions());
      },
    });
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
        <SessionList sessions={sessions} onUpdate={handleUpdate} onDelete={handleDelete} onView={handleViewSession} />
      </main>

      {/* Drag-and-drop overlay */}
      {isDragOver && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-primary/10 border-4 border-dashed border-primary pointer-events-none">
          <p className="text-primary font-semibold text-xl">파일을 여기에 놓으세요</p>
        </div>
      )}

      {/* File confirmation modal */}
      {modalData && (
        <AddFilesModal
          fileNames={modalData.fileNames}
          onClose={() => setModalData(null)}
          onConfirm={modalData.handle}
        />
      )}
    </div>
  );
}
