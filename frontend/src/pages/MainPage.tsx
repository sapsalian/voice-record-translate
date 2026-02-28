import { useCallback, useEffect, useRef, useState } from 'react';
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
import { useT } from '@/LocaleContext';

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
  sessions: Session[];
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>;
  onSettingsOpen: () => void;
}

type ModalData = {
  fileNames: string[];
  handle: (targetLang: string) => Promise<void>;
};

export function MainPage({ sessions, setSessions, onSettingsOpen }: Props) {
  const navigate = useNavigate();
  const t = useT();
  const [isDragOver, setIsDragOver] = useState(false);
  const [modalData, setModalData] = useState<ModalData | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 스크롤 위치 보존: 마운트 시 복원, 언마운트 시 저장
  useEffect(() => {
    const saved = sessionStorage.getItem('mainScrollY');
    if (saved) window.scrollTo(0, Number(saved));
    return () => {
      sessionStorage.setItem('mainScrollY', String(window.scrollY));
    };
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
  }, [setSessions]);

  const handleUpdate = useCallback((updated: Session) => {
    setSessions((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
  }, [setSessions]);

  const handleDelete = useCallback(async (id: string) => {
    await deleteSession(id).catch(() => {});
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }, [setSessions]);

  const handleViewSession = (id: string) => {
    navigate('/viewer/' + id);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    e.target.value = '';
    if (files.length === 0) return;
    setModalData({
      fileNames: files.map((f) => f.name),
      handle: async (lang) => {
        await Promise.all(files.map((f) => uploadAndProcess(f, lang)));
        setSessions(await fetchSessions());
      },
    });
  };

  const handleAddFile = async () => {
    if (window.pywebview?.api) {
      const paths = await window.pywebview.api.open_file_dialog();
      if (!paths || paths.length === 0) return;
      setModalData({
        fileNames: paths.map((p) => p.split('/').pop() ?? p),
        handle: async (lang) => {
          await Promise.all(paths.map((p) => startProcessing(p, lang)));
          setSessions(await fetchSessions());
        },
      });
    } else {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b px-4 h-14 flex items-center justify-between">
        <h1 className="font-semibold text-lg">VRT</h1>
        <div className="flex gap-2">
          <Button onClick={handleAddFile}>{t('add_file')}</Button>
          <Button variant="ghost" size="icon" onClick={onSettingsOpen} aria-label={t('settings')}>
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
          <p className="text-primary font-semibold text-xl">{t('drop_files')}</p>
        </div>
      )}

      {/* Hidden file input for web mode */}
      <input
        ref={fileInputRef}
        type="file"
        accept="audio/*,.mp3,.m4a,.wav,.ogg,.flac,.aac,.wma,.opus"
        multiple
        className="hidden"
        onChange={handleFileInputChange}
      />

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
