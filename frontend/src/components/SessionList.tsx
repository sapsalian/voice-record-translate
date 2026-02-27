import { SessionItem } from '@/components/SessionItem';
import type { Session } from '@/types/session';

interface Props {
  sessions: Session[];
  onUpdate: (session: Session) => void;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

export function SessionList({ sessions, onUpdate, onDelete, onView }: Props) {
  const processing = sessions.filter((s) => s.status === 'processing');
  const done = sessions.filter((s) => s.status !== 'processing');

  if (sessions.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-20">
        <p className="text-lg">파일을 추가해서 전사·번역을 시작하세요</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {processing.length > 0 && (
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-2">처리 중</h2>
          <div className="space-y-2">
            {processing.map((s) => (
              <SessionItem key={s.id} session={s} onUpdate={onUpdate} onDelete={onDelete} onView={undefined} />
            ))}
          </div>
        </section>
      )}

      {done.length > 0 && (
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-2">완료</h2>
          <div className="space-y-2">
            {done.map((s) => (
              <SessionItem
                key={s.id}
                session={s}
                onUpdate={onUpdate}
                onDelete={onDelete}
                onView={s.status === 'completed' ? () => onView(s.id) : undefined}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
