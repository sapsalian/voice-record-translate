import { useEffect, useRef } from 'react';
import { getSpeakerColor } from '@/constants/speakerColors';
import type { Segment } from '@/types/session';

interface Props {
  segments: Segment[];
  speakerNames: Record<string, string>;
  currentTime?: number;
  isFollowing?: boolean;
  onSegmentClick?: (time: number) => void;
  onUserScroll?: () => void;
}

function formatTime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function TranscriptPanel({ segments, speakerNames, currentTime, isFollowing, onSegmentClick, onUserScroll }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const segmentRefs = useRef<(HTMLDivElement | null)[]>([]);

  let currentIdx = -1;
  if (currentTime !== undefined) {
    for (let i = segments.length - 1; i >= 0; i--) {
      if (segments[i].start <= currentTime) {
        currentIdx = i;
        break;
      }
    }
  }

  useEffect(() => {
    if (!isFollowing || currentIdx < 0) return;
    segmentRefs.current[currentIdx]?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [currentIdx, isFollowing]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !onUserScroll) return;
    el.addEventListener('wheel', onUserScroll, { passive: true });
    el.addEventListener('touchstart', onUserScroll, { passive: true });
    return () => {
      el.removeEventListener('wheel', onUserScroll);
      el.removeEventListener('touchstart', onUserScroll);
    };
  }, [onUserScroll]);

  if (segments.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
        대본이 없습니다.
      </div>
    );
  }

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto">
      {segments.map((seg, i) => {
        const speakerName = seg.speaker
          ? (speakerNames[seg.speaker] ?? `화자 ${seg.speaker}`)
          : null;
        const colorClass = getSpeakerColor(seg.speaker);
        const isActive = i === currentIdx;

        return (
          <div
            key={i}
            ref={el => { segmentRefs.current[i] = el; }}
            onClick={() => onSegmentClick?.(seg.start)}
            className={`px-6 py-3 border-b last:border-b-0 cursor-pointer hover:bg-accent/20 ${isActive ? 'bg-accent/40' : ''}`}
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
