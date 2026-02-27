import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AudioPlayer } from '@/components/AudioPlayer';
import type { AudioPlayerHandle } from '@/components/AudioPlayer';
import { TranscriptPanel } from '@/components/TranscriptPanel';
import { fetchSession } from '@/api/client';
import { API_BASE } from '@/api/client';
import type { Session } from '@/types/session';

export function ViewerPage() {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<Session | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isFollowing, setIsFollowing] = useState(true);

  const audioRef = useRef<AudioPlayerHandle>(null);
  const currentTimeRef = useRef(0);
  const currentIdxRef = useRef(-1);

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

  if (notFound) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground">
        세션을 찾을 수 없습니다.
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground text-sm">
        불러오는 중...
      </div>
    );
  }

  const audioSrc = `${API_BASE}/api/sessions/${session.id}/audio`;

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      {/* Header */}
      <header className="shrink-0 border-b px-4 h-14 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors shrink-0"
        >
          ← 목록으로
        </button>
        <h1 className="font-semibold truncate">{session.title}</h1>
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
        />
        {!isFollowing && (
          <button
            onClick={() => setIsFollowing(true)}
            className="absolute bottom-4 right-4 text-xs px-3 py-1.5 rounded-full bg-primary text-primary-foreground shadow-md"
          >
            재생 위치로
          </button>
        )}
      </div>
    </div>
  );
}
