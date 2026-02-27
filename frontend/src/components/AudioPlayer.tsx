import { useEffect, useRef, useState } from 'react';
import { Play, Pause, SkipBack, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

interface Props {
  src: string;
  onTimeUpdate?: (t: number) => void;
}

function formatTime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

const SPEEDS = [0.75, 1, 1.25, 1.5, 2] as const;

export function AudioPlayer({ src, onTimeUpdate }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [isSeeking, setIsSeeking] = useState(false);
  const seekValueRef = useRef(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onEnded = () => setPlaying(false);
    const onLoaded = () => setDuration(audio.duration || 0);
    const onTime = () => {
      if (!isSeeking) {
        setCurrentTime(audio.currentTime);
        onTimeUpdate?.(audio.currentTime);
      }
    };

    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('ended', onEnded);
    audio.addEventListener('loadedmetadata', onLoaded);
    audio.addEventListener('timeupdate', onTime);
    return () => {
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('ended', onEnded);
      audio.removeEventListener('loadedmetadata', onLoaded);
      audio.removeEventListener('timeupdate', onTime);
    };
  }, [isSeeking, onTimeUpdate]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.playbackRate = speed;
  }, [speed]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      if (e.key === ' ') {
        e.preventDefault();
        togglePlay();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        seek(-5);
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        seek(5);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [playing]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) audio.pause();
    else audio.play();
  };

  const seek = (delta: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Math.max(0, Math.min(duration, audio.currentTime + delta));
  };

  const handleSeekMouseDown = () => {
    setIsSeeking(true);
  };

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    seekValueRef.current = val;
    setCurrentTime(val);
  };

  const handleSeekMouseUp = () => {
    const audio = audioRef.current;
    if (audio) audio.currentTime = seekValueRef.current;
    setIsSeeking(false);
  };

  return (
    <div className="px-4 py-3 border-b bg-background">
      <audio ref={audioRef} src={src} preload="metadata" />

      {/* Controls row */}
      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button size="sm" variant="ghost" className="w-8 h-8 p-0 shrink-0" onClick={() => seek(-5)}>
              <SkipBack className="w-4 h-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>5초 뒤로 (←)</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button size="sm" variant="ghost" className="w-9 h-9 p-0 shrink-0" onClick={togglePlay}>
              {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
          </TooltipTrigger>
          <TooltipContent>{playing ? '일시정지 (Space)' : '재생 (Space)'}</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button size="sm" variant="ghost" className="w-8 h-8 p-0 shrink-0" onClick={() => seek(5)}>
              <SkipForward className="w-4 h-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>5초 앞으로 (→)</TooltipContent>
        </Tooltip>

        <span className="text-xs text-muted-foreground tabular-nums shrink-0">
          {formatTime(currentTime)}
        </span>

        <input
          type="range"
          className="flex-1 h-1 accent-primary cursor-pointer"
          min={0}
          max={duration || 1}
          step={0.1}
          value={currentTime}
          onMouseDown={handleSeekMouseDown}
          onChange={handleSeekChange}
          onMouseUp={handleSeekMouseUp}
        />

        <span className="text-xs text-muted-foreground tabular-nums shrink-0">
          {formatTime(duration)}
        </span>
      </div>

      {/* Speed buttons */}
      <div className="flex gap-1 mt-1.5 justify-end">
        {SPEEDS.map((s) => (
          <button
            key={s}
            className={`text-xs px-2 py-0.5 rounded transition-colors ${
              speed === s
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            onClick={() => setSpeed(s)}
          >
            {s === 1 ? '1×' : `${s}×`}
          </button>
        ))}
      </div>
    </div>
  );
}
