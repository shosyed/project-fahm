export interface AyahRecord {
  arabic: string;
  translations: Record<string, string>;
  tafsirs: Record<string, string>;
}

export type RevelationType = 'Meccan' | 'Medinan';

export interface SurahMeta {
  number: number;
  name: string;
  englishName: string;
  ayahCount: number;
  revelationType: RevelationType;
}

export interface SimilarAyah {
  surah: number;
  ayah: number;
  type: string;
  score?: number;
}

export interface TopicsAndThemes {
  topics: string[];
  themes: string[];
}
