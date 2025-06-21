export interface MusicFile {
  id: string;
  original_filename: string;
  file_format: string;
  duration: number;
  sample_rate: number;
  channels: number;
  bit_depth: number;
  file_size: number;
  uploaded_at: string;
  genre?: string;
  metadata?: Record<string, any>;
}

export interface Transcription {
  id: string;
  text: string;
  language: string;
  confidence: number;
  word_timestamps?: any[];
  created_at: string;
}

export interface Lyrics {
  id: string;
  source: string;
  lyrics_text: string;
  confidence: number;
  language: string;
  created_at: string;
}

export interface SearchResult {
  file: MusicFile;
  transcriptions: Transcription[];
  lyrics: Lyrics[];
  similarity_score?: number;
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  genre: string;
  size: number;
  duration: number;
  hash: string;
}

export interface TranscriptionRequest {
  file_id: string;
  language?: string;
  options?: {
    word_timestamps?: boolean;
    [key: string]: any;
  };
}

export interface ExportFormat {
  format: 'json' | 'csv' | 'xlsx' | 'zip' | 'tar.gz' | 'mono_tar.gz';
  label: string;
  description: string;
}

export interface StorageStats {
  total_files: number;
  total_size: number;
  by_format: Record<string, { count: number; size: number }>;
  by_genre: Record<string, { count: number; size: number }>;
}