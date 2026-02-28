import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Download, Pencil } from 'lucide-react';
import { AudioPlayer } from '@/components/AudioPlayer';
import type { AudioPlayerHandle } from '@/components/AudioPlayer';
import { TranscriptPanel } from '@/components/TranscriptPanel';
import { fetchSession, updateSession } from '@/api/client';
import { API_BASE } from '@/api/client';
import type { Session } from '@/types/session';
import { useT } from '@/LocaleContext';

function exportTxt(session: Session, mode: 'translated' | 'original' | 'parallel') {
  function fmtTime(sec: number) {
    const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = Math.floor(sec % 60);
    return h > 0
      ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
      : `${m}:${String(s).padStart(2, '0')}`;
  }
  const blocks = session.segments.map(seg => {
    const spk = seg.speaker ? (session.speaker_names[seg.speaker] ?? seg.speaker) : null;
    const header = `[${fmtTime(seg.start)}]${spk ? ' ' + spk : ''}`;
    if (mode === 'translated') return `${header}\n${seg.translated}`;
    if (mode === 'original')   return `${header}\n${seg.original}`;
    return `${header}\n${seg.translated}\n(${seg.original})`;
  });
  const text = blocks.join('\n\n');
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `${session.title}.txt`; a.click();
  URL.revokeObjectURL(url);
}

export function ViewerPage() {
  const navigate = useNavigate();
  const t = useT();
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<Session | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isFollowing, setIsFollowing] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);
  const [showExport, setShowExport] = useState(false);

  const audioRef = useRef<AudioPlayerHandle>(null);
  const currentTimeRef = useRef(0);
  const currentIdxRef = useRef(-1);
  const exportRef = useRef<HTMLDivElement>(null);

  useEffect(() => { currentTimeRef.current = currentTime; }, [currentTime]);

  useEffect(() => {
    if (!sessionId) return;
    fetchSession(sessionId)
      .then((s) => {
        if (!s || !s.id) {
          setNotFound(true);
        } else {
          setSession(s);
        }
      })
      .catch(() => setNotFound(true));
  }, [sessionId]);

  // Update currentIdxRef whenever session or currentTime changes
  useEffect(() => {
    if (!session) return;
    const segments = session.segments;
    const t = currentTimeRef.current;
    let idx = -1;
    for (let i = segments.length - 1; i >= 0; i--) {
      if (segments[i].start <= t) { idx = i; break; }
    }
    currentIdxRef.current = idx;
  });

  // Close export dropdown on outside click
  useEffect(() => {
    if (!showExport) return;
    const handler = (e: MouseEvent) => {
      if (exportRef.current && !exportRef.current.contains(e.target as Node)) {
        setShowExport(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showExport]);

  // J/K keyboard shortcuts
  useEffect(() => {
    if (!session) return;
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      const segments = session.segments;
      const t = currentTimeRef.current;
      let targetTime: number | null = null;

      if (e.key === 'j') {
        const next = segments.find(s => s.start > t);
        if (next) targetTime = next.start;
      } else if (e.key === 'k') {
        const currentSeg = segments[currentIdxRef.current];
        if (currentSeg && t - currentSeg.start > 2) {
          targetTime = currentSeg.start;
        } else {
          const prev = [...segments].reverse().find(s => s.start < t - 0.1);
          if (prev) targetTime = prev.start;
        }
      }

      if (targetTime !== null) {
        audioRef.current?.seekTo(targetTime);
        setIsFollowing(true);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [session]);

  const handleSegmentClick = (time: number) => {
    audioRef.current?.seekTo(time);
    setIsFollowing(true);
  };

  const handleSpeakerRenameAll = async (speakerId: string, newName: string) => {
    if (!session) return;
    const newNames = { ...session.speaker_names, [speakerId]: newName };
    const updated = await updateSession(session.id, { speaker_names: newNames });
    setSession(updated);
  };

  const handleSpeakerReassign = async (segIdx: number, targetName: string, fromDropdown: string | null) => {
    if (!session) return;
    let targetId: string = fromDropdown ?? '';
    const newNames = { ...session.speaker_names };

    if (!targetId) {
      const match = Object.entries(newNames).find(([, name]) => name === targetName);
      if (match) {
        targetId = match[0];
      } else {
        const numIds = Object.keys(newNames).map(Number).filter(n => !isNaN(n));
        targetId = String(numIds.length > 0 ? Math.max(...numIds) + 1 : 1);
        newNames[targetId] = targetName;
      }
    }

    const newSegments = session.segments.map((s, i) =>
      i === segIdx ? { ...s, speaker: targetId } : s
    );
    const updated = await updateSession(session.id, { speaker_names: newNames, segments: newSegments });
    setSession(updated);
  };

  const handleSpeakerMergeAll = async (speakerId: string, targetId: string) => {
    if (!session) return;
    const newSegments = session.segments.map(s =>
      s.speaker === speakerId ? { ...s, speaker: targetId } : s
    );
    const newNames = { ...session.speaker_names };
    delete newNames[speakerId];
    const updated = await updateSession(session.id, { speaker_names: newNames, segments: newSegments });
    setSession(updated);
  };

  const handleSegmentEdit = async (segIdx: number, newTranslated: string) => {
    if (!session) return;
    const newSegments = session.segments.map((s, i) =>
      i === segIdx ? { ...s, translated: newTranslated } : s
    );
    const updated = await updateSession(session.id, { segments: newSegments });
    setSession(updated);
  };

  if (notFound) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground">
        {t('not_found')}
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground text-sm">
        {t('loading')}
      </div>
    );
  }

  const audioSrc = `${API_BASE}/api/sessions/${session.id}/audio`;

  const exportLabels = {
    translated: t('export_translated'),
    original: t('export_original'),
    parallel: t('export_parallel'),
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      {/* Header */}
      <header className="shrink-0 border-b px-4 h-14 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors shrink-0"
        >
          {t('back_to_list')}
        </button>
        <h1 className="font-semibold truncate flex-1">{session.title}</h1>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setShowOriginal(v => !v)}
            className={`text-xs px-2 py-1 rounded ${showOriginal ? 'bg-accent text-foreground' : 'text-muted-foreground'}`}
          >
            {t('original')}
          </button>
          <button
            onClick={() => setIsEditing(v => !v)}
            className={`p-1 rounded ${isEditing ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
          >
            <Pencil className="w-4 h-4" />
          </button>
          <div ref={exportRef} className="relative">
            <button
              onClick={() => setShowExport(v => !v)}
              className="p-1 text-muted-foreground hover:text-foreground"
            >
              <Download className="w-4 h-4" />
            </button>
            {showExport && (
              <div className="absolute right-0 top-full mt-1 bg-popover border rounded shadow-md z-10 text-sm">
                {(['translated', 'original', 'parallel'] as const).map(mode => (
                  <button
                    key={mode}
                    onClick={() => { exportTxt(session, mode); setShowExport(false); }}
                    className="block w-full px-4 py-2 text-left hover:bg-accent whitespace-nowrap"
                  >
                    {exportLabels[mode]}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Audio Player */}
      <div className="shrink-0">
        <AudioPlayer ref={audioRef} src={audioSrc} onTimeUpdate={setCurrentTime} />
      </div>

      {/* Transcript with follow button */}
      <div className="relative flex-1 min-h-0 flex flex-col">
        <TranscriptPanel
          segments={session.segments}
          speakerNames={session.speaker_names}
          currentTime={currentTime}
          isFollowing={isFollowing}
          onSegmentClick={handleSegmentClick}
          onUserScroll={() => setIsFollowing(false)}
          isEditing={isEditing}
          showOriginal={showOriginal}
          onSpeakerRenameAll={handleSpeakerRenameAll}
          onSpeakerMergeAll={handleSpeakerMergeAll}
          onSpeakerReassign={handleSpeakerReassign}
          onSegmentEdit={handleSegmentEdit}
        />
        {!isFollowing && (
          <button
            onClick={() => setIsFollowing(true)}
            className="absolute bottom-4 right-4 text-xs px-3 py-1.5 rounded-full bg-primary text-primary-foreground shadow-md"
          >
            {t('follow')}
          </button>
        )}
      </div>
    </div>
  );
}
