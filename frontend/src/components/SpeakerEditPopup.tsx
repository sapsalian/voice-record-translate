import { useState } from 'react';

interface Props {
  currentName: string;
  speakerId: string;
  allSpeakers: Record<string, string>;
  onRenameAll: (newName: string) => void;
  onReassign: (name: string, dropdownId: string | null) => void;
  onCancel: () => void;
}

export function SpeakerEditContent({ currentName, speakerId, allSpeakers, onRenameAll, onReassign, onCancel }: Props) {
  const [inputValue, setInputValue] = useState(currentName);
  const [selectedId, setSelectedId] = useState('');

  const otherSpeakers = Object.entries(allSpeakers).filter(([id]) => id !== speakerId);

  return (
    <div className="flex flex-col gap-2 min-w-48">
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground whitespace-nowrap">{currentName} →</span>
        <input
          type="text"
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          onClick={e => e.stopPropagation()}
          className="flex-1 text-xs border rounded px-2 py-1 bg-background"
          autoFocus
        />
      </div>
      {otherSpeakers.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground whitespace-nowrap">이 부분만:</span>
          <select
            value={selectedId}
            onChange={e => setSelectedId(e.target.value)}
            onClick={e => e.stopPropagation()}
            className="flex-1 text-xs border rounded px-1 py-1 bg-background"
          >
            <option value="">직접 입력</option>
            {otherSpeakers.map(([id, name]) => (
              <option key={id} value={id}>{name}</option>
            ))}
          </select>
        </div>
      )}
      <div className="flex gap-1 mt-1">
        <button
          onClick={e => { e.stopPropagation(); onRenameAll(inputValue); }}
          className="flex-1 text-xs px-2 py-1 bg-primary text-primary-foreground rounded"
        >
          모두 변경
        </button>
        <button
          onClick={e => { e.stopPropagation(); selectedId ? onReassign('', selectedId) : onReassign(inputValue, null); }}
          className="flex-1 text-xs px-2 py-1 border rounded"
        >
          이 부분만
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
