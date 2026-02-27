// 10색 팔레트. 모두 동일한 명도 패턴(-100/-700 라이트, -950/-300 다크)으로 분위기 통일.
// 앞 5개는 색상환 균등 배분 (일반적인 5인 이하 케이스 대응).
// Tailwind v4 정적 스캔을 위해 전체 클래스 문자열로 정의.
export const SPEAKER_COLORS = [
  'bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300',
  'bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300',
  'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
  'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
  'bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300',
  'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
  'bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300',
  'bg-pink-100 text-pink-700 dark:bg-pink-950 dark:text-pink-300',
  'bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300',
] as const;

export function getSpeakerColor(speakerId: string | null | undefined): string {
  if (!speakerId) return 'bg-muted text-muted-foreground';
  const hash = speakerId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  return SPEAKER_COLORS[hash % SPEAKER_COLORS.length];
}
