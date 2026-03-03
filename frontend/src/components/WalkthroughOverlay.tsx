import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { useT } from '@/LocaleContext';

export interface WalkthroughStep {
  targetRef: React.RefObject<HTMLElement | null>;
  title: string;
  description: string;
  placement: 'bottom' | 'top' | 'left' | 'right';
}

interface Props {
  steps: WalkthroughStep[];
  onDone: () => void;
}

interface Rect {
  top: number;
  left: number;
  width: number;
  height: number;
}

const PADDING = 8;
const CARD_WIDTH = 280;

export function WalkthroughOverlay({ steps, onDone }: Props) {
  const t = useT();
  const [idx, setIdx] = useState(0);
  const [targetRect, setTargetRect] = useState<Rect | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  // Find first non-null step
  const effectiveSteps = steps.filter((s) => s.targetRef.current !== null);
  const step = effectiveSteps[idx] ?? null;

  useLayoutEffect(() => {
    if (!step?.targetRef.current) {
      setTargetRect(null);
      return;
    }
    const rect = step.targetRef.current.getBoundingClientRect();
    setTargetRect({ top: rect.top, left: rect.left, width: rect.width, height: rect.height });
  }, [idx, step]);

  useEffect(() => {
    if (effectiveSteps.length === 0) {
      onDone();
    }
  }, [effectiveSteps.length, onDone]);

  if (!step || effectiveSteps.length === 0) return null;

  const isLast = idx === effectiveSteps.length - 1;

  const handleNext = () => {
    if (isLast) {
      onDone();
    } else {
      setIdx((i) => i + 1);
    }
  };

  // Compute card position based on targetRect and placement
  let cardStyle: React.CSSProperties = { position: 'fixed', width: CARD_WIDTH, zIndex: 9999 };
  if (targetRect) {
    const { top, left, width, height } = targetRect;
    const { placement } = step;
    if (placement === 'bottom') {
      cardStyle = { ...cardStyle, top: top + height + PADDING, left: left + width / 2 - CARD_WIDTH / 2 };
    } else if (placement === 'top') {
      cardStyle = { ...cardStyle, top: top - PADDING - 120, left: left + width / 2 - CARD_WIDTH / 2 };
    } else if (placement === 'right') {
      cardStyle = { ...cardStyle, top: top + height / 2 - 60, left: left + width + PADDING };
    } else {
      cardStyle = { ...cardStyle, top: top + height / 2 - 60, left: left - CARD_WIDTH - PADDING };
    }
    // Clamp within viewport
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    if (typeof cardStyle.left === 'number') {
      cardStyle.left = Math.max(8, Math.min(vw - CARD_WIDTH - 8, cardStyle.left));
    }
    if (typeof cardStyle.top === 'number') {
      cardStyle.top = Math.max(8, Math.min(vh - 160, cardStyle.top));
    }
  }

  return (
    <>
      {/* Backdrop with spotlight hole */}
      {targetRect && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9998,
            pointerEvents: 'none',
            boxShadow: `0 0 0 9999px rgba(0,0,0,0.5)`,
            top: targetRect.top - PADDING,
            left: targetRect.left - PADDING,
            width: targetRect.width + PADDING * 2,
            height: targetRect.height + PADDING * 2,
            borderRadius: 6,
          }}
        />
      )}
      {/* Full click-blocker behind card */}
      <div
        style={{ position: 'fixed', inset: 0, zIndex: 9998 }}
        onClick={handleNext}
      />
      {/* Tooltip card */}
      <div
        ref={cardRef}
        style={cardStyle}
        className="bg-popover text-popover-foreground border rounded-lg shadow-lg p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-1">
          <span className="font-semibold text-sm">{step.title}</span>
          <span className="text-xs text-muted-foreground">{idx + 1}/{effectiveSteps.length}</span>
        </div>
        <p className="text-sm text-muted-foreground mb-3">{step.description}</p>
        <Button size="sm" className="w-full" onClick={handleNext}>
          {isLast ? t('wt_done') : t('wt_next')}
        </Button>
      </div>
    </>
  );
}
