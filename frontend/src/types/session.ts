export interface Segment {
  start: number;
  end: number;
  speaker: string | null;
  original: string;
  translated: string;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  audio_filename: string;
  target_lang: string;
  status: 'processing' | 'completed' | 'failed';
  duration: number | null;
  error_message: string | null;
  progress: number;
  progress_message: string;
  speaker_names: Record<string, string>;
  segments: Segment[];
}
