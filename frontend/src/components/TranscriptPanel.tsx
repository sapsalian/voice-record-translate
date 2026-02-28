import { useEffect, useRef, useState } from 'react';
import { Pencil } from 'lucide-react';
import { getSpeakerColor } from '@/constants/speakerColors';
import type { Segment } from '@/types/session';
import { SpeakerEditContent } from './SpeakerEditPopup';
import { useT } from '@/LocaleContext';

const isTouchDevice = window.matchMedia('(hover: none)').matches;

interface Props {
  segments: Segment[];
  speakerNames: Record<string, string>;
  currentTime?: number;
  isFollowing?: boolean;
  onSegmentClick?: (time: number) => void;
  onUserScroll?: () => void;
  isEditing?: boolean;
  showOriginal?: boolean;
  onSpeakerRenameAll?: (speakerId: string, newName: string) => void;
  onSpeakerMergeAll?: (speakerId: string, targetId: string) => void;
  onSpeakerReassign?: (segIdx: number, targetName: string, fromDropdown: string | null) => void;
  onSegmentEdit?: (segIdx: number, newTranslated: string) => void;
}

function formatTime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function TranscriptPanel({
  segments, speakerNames, currentTime, isFollowing, onSegmentClick, onUserScroll,
  isEditing, showOriginal, onSpeakerRenameAll, onSpeakerMergeAll, onSpeakerReassign, onSegmentEdit,
}: Props) {
  const t = useT();
  const containerRef = useRef<HTMLDivElement>(null);
  const segmentRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [editingSpeakerIdx, setEditingSpeakerIdx] = useState<number | null>(null);
  const [editingSegIdx, setEditingSegIdx] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');

  let currentIdx = -1;
  if (currentTime !== undefined) {
    for (let i = segments.length - 1; i >= 0; i--) {
      if (segments[i].start <= currentTime) { currentIdx = i; break; }
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

  useEffect(() => {
    if (!isEditing) {
      setEditingSpeakerIdx(null);
      setEditingSegIdx(null);
    }
  }, [isEditing]);

  if (segments.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
        {t('no_transcript')}
      </div>
    );
  }

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto">
      {segments.map((seg, i) => {
        const speakerName = seg.speaker
          ? (speakerNames[seg.speaker] ?? t('speaker', seg.speaker))
          : null;
        const colorClass = getSpeakerColor(seg.speaker);
        const isActive = i === currentIdx;
        const isEditingThisSpeaker = editingSpeakerIdx === i;
        const isEditingThisSeg = editingSegIdx === i;

        return (
          <div
            key={i}
            ref={el => { segmentRefs.current[i] = el; }}
            onClick={isEditingThisSeg ? undefined : () => onSegmentClick?.(seg.start)}
            className={`px-6 py-3 border-b last:border-b-0 ${isEditingThisSeg ? '' : 'cursor-pointer hover:bg-accent/20'} ${isActive ? 'bg-accent/40' : ''}`}
          >
            {/* Speaker badge + timestamp row */}
            <div className="flex items-center gap-2 mb-1">
              {speakerName && (
                <div className="relative group/speaker inline-flex items-center gap-1">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colorClass}`}>
                    {speakerName}
                  </span>
                  {isEditing && (
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        setEditingSpeakerIdx(isEditingThisSpeaker ? null : i);
                      }}
                      className={isTouchDevice
                        ? 'opacity-100'
                        : 'opacity-0 group-hover/speaker:opacity-100 transition-opacity'
                      }
                    >
                      <Pencil className="w-3 h-3 text-muted-foreground" />
                    </button>
                  )}
                  {/* Desktop popup */}
                  {isEditingThisSpeaker && !isTouchDevice && (
                    <div className="absolute left-0 top-full mt-1 z-20 p-3 border rounded bg-popover shadow-md min-w-56">
                      <SpeakerEditContent
                        currentName={speakerName}
                        speakerId={seg.speaker!}
                        allSpeakers={speakerNames}
                        onRenameAll={newName => { onSpeakerRenameAll?.(seg.speaker!, newName); setEditingSpeakerIdx(null); }}
                        onMergeAll={targetId => { onSpeakerMergeAll?.(seg.speaker!, targetId); setEditingSpeakerIdx(null); }}
                        onReassign={(name, dropdownId) => { onSpeakerReassign?.(i, name, dropdownId); setEditingSpeakerIdx(null); }}
                        onCancel={() => setEditingSpeakerIdx(null)}
                      />
                    </div>
                  )}
                </div>
              )}
              <span className="text-xs text-muted-foreground tabular-nums">
                {formatTime(seg.start)}
              </span>
            </div>

            {/* Touch inline speaker edit */}
            {isEditingThisSpeaker && isTouchDevice && (
              <div className="mt-2 p-3 border rounded bg-background shadow-sm">
                <SpeakerEditContent
                  currentName={speakerName!}
                  speakerId={seg.speaker!}
                  allSpeakers={speakerNames}
                  onRenameAll={newName => { onSpeakerRenameAll?.(seg.speaker!, newName); setEditingSpeakerIdx(null); }}
                  onMergeAll={targetId => { onSpeakerMergeAll?.(seg.speaker!, targetId); setEditingSpeakerIdx(null); }}
                  onReassign={(name, dropdownId) => { onSpeakerReassign?.(i, name, dropdownId); setEditingSpeakerIdx(null); }}
                  onCancel={() => setEditingSpeakerIdx(null)}
                />
              </div>
            )}

            {/* Segment text */}
            {isEditingThisSeg ? (
              <div onClick={e => e.stopPropagation()}>
                <textarea
                  className="w-full text-sm border rounded p-1 resize-none bg-background"
                  value={editValue}
                  onChange={e => setEditValue(e.target.value)}
                  rows={3}
                  autoFocus
                />
                <div className="flex gap-2 mt-1">
                  <button
                    onClick={() => { onSegmentEdit?.(i, editValue); setEditingSegIdx(null); }}
                    className="text-xs px-2 py-1 bg-primary text-primary-foreground rounded"
                  >
                    {t('save')}
                  </button>
                  <button
                    onClick={() => setEditingSegIdx(null)}
                    className="text-xs px-2 py-1 text-muted-foreground"
                  >
                    {t('cancel')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="relative group/seg">
                <p className="text-sm leading-relaxed">{seg.translated}</p>
                {showOriginal && seg.original && (
                  <p className="text-xs text-muted-foreground italic mt-1">{seg.original}</p>
                )}
                {isEditing && (
                  <button
                    onClick={e => { e.stopPropagation(); setEditingSegIdx(i); setEditValue(seg.translated); }}
                    className="absolute top-0 right-0 opacity-0 group-hover/seg:opacity-100 transition-opacity"
                  >
                    <Pencil className="w-3 h-3 text-muted-foreground" />
                  </button>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
