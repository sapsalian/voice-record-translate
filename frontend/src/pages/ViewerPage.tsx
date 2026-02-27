import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AudioPlayer } from '@/components/AudioPlayer';
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
        <AudioPlayer src={audioSrc} onTimeUpdate={setCurrentTime} />
      </div>

      {/* Transcript */}
      <TranscriptPanel
        segments={session.segments}
        speakerNames={session.speaker_names}
        currentTime={currentTime}
      />
    </div>
  );
}
