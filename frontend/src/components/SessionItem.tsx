import { useCallback, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { fetchSession } from '@/api/client';
import type { Session } from '@/types/session';

interface Props {
  session: Session;
  onUpdate: (session: Session) => void;
  onDelete: (id: string) => void;
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function formatDate(isoString: string): string {
  const d = new Date(isoString);
  return d.toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function SessionItem({ session, onUpdate, onDelete }: Props) {
  const poll = useCallback(async () => {
    try {
      const updated = await fetchSession(session.id);
      onUpdate(updated);
    } catch {
      // ignore transient errors
    }
  }, [session.id, onUpdate]);

  useEffect(() => {
    if (session.status !== 'processing') return;
    const timer = setInterval(poll, 1000);
    return () => clearInterval(timer);
  }, [session.status, poll]);

  return (
    <div className="flex items-center gap-3 rounded-lg border px-4 py-3">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium truncate">{session.title}</span>
          <Badge variant="outline" className="shrink-0 text-xs">
            {session.target_lang.toUpperCase()}
          </Badge>
          {session.status === 'completed' && (
            <Badge variant="secondary" className="shrink-0 text-xs">완료</Badge>
          )}
          {session.status === 'failed' && (
            <Badge variant="destructive" className="shrink-0 text-xs">실패</Badge>
          )}
        </div>

        <div className="text-xs text-muted-foreground">
          {formatDate(session.created_at)}
          {session.duration != null && (
            <span className="ml-2">{formatDuration(session.duration)}</span>
          )}
        </div>

        {session.status === 'processing' && (
          <div className="mt-2 space-y-1">
            <div className="flex items-center gap-2">
              <Progress value={session.progress} className="h-1.5 flex-1" />
              <span className="text-xs text-muted-foreground w-8 text-right">
                {session.progress}%
              </span>
            </div>
            <p className="text-xs text-muted-foreground">{session.progress_message}</p>
          </div>
        )}

        {session.status === 'failed' && session.error_message && (
          <p className="mt-1 text-xs text-destructive truncate">{session.error_message}</p>
        )}
      </div>

      <div className="shrink-0 flex gap-1">
        {session.status === 'completed' && (
          <Button size="sm" variant="outline" disabled>
            열기
          </Button>
        )}
        {session.status === 'processing' && (
          <Button
            size="sm"
            variant="ghost"
            className="text-muted-foreground"
            onClick={() => onDelete(session.id)}
          >
            취소
          </Button>
        )}
        {session.status === 'failed' && (
          <Button
            size="sm"
            variant="ghost"
            className="text-muted-foreground"
            onClick={() => onDelete(session.id)}
          >
            삭제
          </Button>
        )}
      </div>
    </div>
  );
}
