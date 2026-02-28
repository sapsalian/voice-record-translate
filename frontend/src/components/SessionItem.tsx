import { useCallback, useEffect, useRef, useState } from 'react';

const isTouchDevice = window.matchMedia('(hover: none)').matches;
import { Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cancelSession, fetchSession, retrySession, updateSessionTitle } from '@/api/client';
import type { Session } from '@/types/session';
import { useT } from '@/LocaleContext';

interface Props {
  session: Session;
  onUpdate: (session: Session) => void;
  onDelete: (id: string) => void;
  onView?: () => void;
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function formatDate(isoString: string, locale: string): string {
  const d = new Date(isoString);
  return d.toLocaleString(locale, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function SessionItem({ session, onUpdate, onDelete, onView }: Props) {
  const t = useT();
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editTitle, setEditTitle] = useState(session.title);
  const [menuOpen, setMenuOpen] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

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

  // Close dropdown on outside click
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  // Sync title when session prop changes
  useEffect(() => {
    setEditTitle(session.title);
  }, [session.title]);

  const handleSaveTitle = async () => {
    const trimmed = editTitle.trim();
    setIsEditingTitle(false);
    if (!trimmed || trimmed === session.title) {
      setEditTitle(session.title);
      return;
    }
    try {
      const updated = await updateSessionTitle(session.id, trimmed);
      onUpdate(updated);
    } catch {
      setEditTitle(session.title);
    }
  };

  const handleCancelEdit = () => {
    setEditTitle(session.title);
    setIsEditingTitle(false);
  };

  const handleDelete = async () => {
    if (window.confirm(t('delete_confirm'))) {
      onDelete(session.id);
    }
  };

  const handleCancel = async () => {
    setIsCancelling(true);
    await cancelSession(session.id).catch(() => {});
  };

  const handleRetry = async () => {
    await retrySession(session.id).catch(() => {});
    onUpdate({
      ...session,
      status: 'processing',
      error_message: null,
      progress: 0,
      progress_message: t('retrying'),
    });
  };

  return (
    <div
      className={`group relative flex items-center gap-3 rounded-lg border px-4 py-3 ${onView ? 'cursor-pointer hover:bg-accent/50 transition-colors' : ''}`}
      onClick={onView}
    >
      <div className="flex-1 min-w-0">
        {/* Title row */}
        <div className="flex items-center gap-2 mb-1">
          {isEditingTitle ? (
            <input
              autoFocus
              className="font-medium bg-transparent border-b border-primary outline-none flex-1 min-w-0"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onClick={(e) => e.stopPropagation()}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveTitle();
                if (e.key === 'Escape') handleCancelEdit();
              }}
              onBlur={handleSaveTitle}
            />
          ) : (
            <span className="font-medium truncate">{session.title}</span>
          )}
          <Badge variant="outline" className="shrink-0 text-xs">
            {session.target_lang.toUpperCase()}
          </Badge>
          {session.status === 'completed' && (
            <Badge variant="secondary" className="shrink-0 text-xs">{t('status_completed')}</Badge>
          )}
          {session.status === 'failed' && (
            <Badge variant="destructive" className="shrink-0 text-xs">{t('status_failed')}</Badge>
          )}
        </div>

        {/* Date and duration */}
        <div className="text-xs text-muted-foreground">
          {formatDate(session.created_at, t('date_locale'))}
          {session.duration != null && (
            <span className="ml-2">{formatDuration(session.duration)}</span>
          )}
        </div>

        {/* Progress bar */}
        {session.status === 'processing' && (
          <div className="mt-2 space-y-1">
            <div className="flex items-center gap-2">
              <Progress value={session.progress} className="h-1.5 flex-1" />
              <span className="text-xs text-muted-foreground w-8 text-right">
                {session.progress}%
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Loader2 size={11} className="animate-spin text-muted-foreground shrink-0" />
              <p className="text-xs text-muted-foreground">{session.progress_message}</p>
            </div>
          </div>
        )}

        {/* Error message */}
        {session.status === 'failed' && session.error_message && (
          <p className="mt-1 text-xs text-destructive truncate" title={session.error_message}>
            {session.error_message}
          </p>
        )}
      </div>

      {/* Action area */}
      <div className="shrink-0 flex gap-1">
        {session.status === 'processing' && (
          <Button
            size="sm"
            variant="ghost"
            className="text-muted-foreground"
            onClick={handleCancel}
            disabled={isCancelling}
          >
            {isCancelling ? (
              <span className="animate-pulse">{t('canceling')}</span>
            ) : t('cancel')}
          </Button>
        )}

        {session.status === 'failed' && (
          <>
            <Button size="sm" variant="outline" onClick={handleRetry}>
              {t('retry')}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="text-muted-foreground"
              onClick={handleDelete}
            >
              {t('delete')}
            </Button>
          </>
        )}

        {session.status === 'completed' && (
          <div ref={menuRef} className="relative">
            <Button
              size="sm"
              variant="ghost"
              className={`text-muted-foreground transition-opacity ${isTouchDevice ? '' : 'opacity-0 group-hover:opacity-100'}`}
              onClick={(e) => { e.stopPropagation(); setMenuOpen((v) => !v); }}
            >
              ⋯
            </Button>
            {menuOpen && (
              <div className="absolute right-0 top-full mt-1 z-50 bg-popover border rounded-md shadow-md py-1 min-w-[120px]">
                <button
                  className="w-full text-left text-sm px-3 py-1.5 hover:bg-accent hover:text-accent-foreground"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpen(false);
                    setIsEditingTitle(true);
                  }}
                >
                  {t('rename')}
                </button>
                <button
                  className="w-full text-left text-sm px-3 py-1.5 hover:bg-accent hover:text-accent-foreground text-destructive"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpen(false);
                    handleDelete();
                  }}
                >
                  {t('delete')}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
