import { getSpeakerColor } from '@/constants/speakerColors';
import type { Segment } from '@/types/session';

interface Props {
  segments: Segment[];
  speakerNames: Record<string, string>;
  currentTime?: number; // Phase 5에서 자동 스크롤에 사용
}

function formatTime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function TranscriptPanel({ segments, speakerNames, currentTime }: Props) {
  // Phase 5에서 자동 스크롤 연결에 쓸 현재 세그먼트 인덱스 계산
  let currentIdx = -1;
  if (currentTime !== undefined) {
    for (let i = segments.length - 1; i >= 0; i--) {
      if (segments[i].start <= currentTime) {
        currentIdx = i;
        break;
      }
    }
  }

  if (segments.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
        대본이 없습니다.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {segments.map((seg, i) => {
        const speakerName = seg.speaker
          ? (speakerNames[seg.speaker] ?? `화자 ${seg.speaker}`)
          : null;
        const colorClass = getSpeakerColor(seg.speaker);
        const isActive = i === currentIdx;

        return (
          <div
            key={i}
            className={`px-6 py-3 border-b last:border-b-0 ${isActive ? 'bg-accent/40' : ''}`}
          >
            <div className="flex items-center gap-2 mb-1">
              {speakerName && (
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colorClass}`}>
                  {speakerName}
                </span>
              )}
              <span className="text-xs text-muted-foreground tabular-nums">
                {formatTime(seg.start)}
              </span>
            </div>
            <p className="text-sm leading-relaxed">{seg.translated}</p>
          </div>
        );
      })}
    </div>
  );
}
