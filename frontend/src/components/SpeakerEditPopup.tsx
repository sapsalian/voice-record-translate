import { useState } from 'react';

interface Props {
  currentName: string;
  speakerId: string;
  allSpeakers: Record<string, string>;
  onRenameAll: (newName: string) => void;
  onMergeAll: (targetId: string) => void;
  onReassign: (name: string, targetId: string | null) => void;
  onCancel: () => void;
}

export function SpeakerEditContent({ currentName, speakerId, allSpeakers, onRenameAll, onMergeAll, onReassign, onCancel }: Props) {
  const [inputValue, setInputValue] = useState(currentName);

  const otherSpeakers = Object.entries(allSpeakers).filter(([id]) => id !== speakerId);
  const matchedEntry = otherSpeakers.find(([, name]) => name === inputValue);
  const isExisting = !!matchedEntry;
  const listId = `speaker-list-${speakerId}`;

  return (
    <div className="flex flex-col gap-2 min-w-48">
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground whitespace-nowrap">{currentName} →</span>
        <input
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          onClick={e => e.stopPropagation()}
          list={listId}
          className="flex-1 text-xs border rounded px-2 py-1 bg-background"
          autoFocus
        />
        <datalist id={listId}>
          {otherSpeakers.map(([id, name]) => <option key={id} value={name} />)}
        </datalist>
      </div>
      <div className="flex gap-1 mt-1">
        <button
          onClick={e => { e.stopPropagation(); isExisting ? onMergeAll(matchedEntry![0]) : onRenameAll(inputValue); }}
          className="flex-1 text-xs px-2 py-1 bg-primary text-primary-foreground rounded"
        >
          {isExisting ? `${inputValue}로 전체 합치기` : '이름 변경'}
        </button>
        <button
          onClick={e => { e.stopPropagation(); isExisting ? onReassign('', matchedEntry![0]) : onReassign(inputValue, null); }}
          className="flex-1 text-xs px-2 py-1 border rounded"
        >
          {isExisting ? `이 부분만 ${inputValue}로` : '이 부분만 새 화자로'}
        </button>
        <button
          onClick={e => { e.stopPropagation(); onCancel(); }}
          className="text-xs px-2 py-1 text-muted-foreground"
        >
          취소
        </button>
      </div>
    </div>
  );
}
