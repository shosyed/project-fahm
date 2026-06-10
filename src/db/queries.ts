import type { AyahRecord, SimilarAyah, TopicsAndThemes } from './types.ts';
import { getDb } from './loader.ts';

export async function getAyah(surah: number, ayah: number): Promise<AyahRecord> {
  const db = await getDb();

  const arabicRows = db.exec('SELECT arabic FROM ayahs WHERE surah = ? AND ayah = ?', [surah, ayah]);
  if (arabicRows.length === 0 || arabicRows[0].values.length === 0) {
    throw new Error(`Ayah not found: ${surah}:${ayah}`);
  }
  const arabic = arabicRows[0].values[0][0] as string;

  const translRows = db.exec('SELECT key, text FROM translations WHERE surah = ? AND ayah = ?', [surah, ayah]);
  const translations: Record<string, string> = {};
  for (const row of translRows[0]?.values ?? []) {
    translations[row[0] as string] = row[1] as string;
  }

  const tafsirRows = db.exec('SELECT key, text FROM tafsirs WHERE surah = ? AND ayah = ?', [surah, ayah]);
  const tafsirs: Record<string, string> = {};
  for (const row of tafsirRows[0]?.values ?? []) {
    tafsirs[row[0] as string] = row[1] as string;
  }

  return { arabic, translations, tafsirs };
}

export async function getSimilarAyahs(surah: number, ayah: number): Promise<SimilarAyah[]> {
  const db = await getDb();
  const results: SimilarAyah[] = [];

  const simRows = db.exec(
    `SELECT surah_b, ayah_b, relationship_type, score
     FROM similar_ayahs WHERE surah_a = ? AND ayah_a = ?
     UNION ALL
     SELECT surah_a, ayah_a, relationship_type, score
     FROM similar_ayahs WHERE surah_b = ? AND ayah_b = ?`,
    [surah, ayah, surah, ayah]
  );
  for (const row of simRows[0]?.values ?? []) {
    results.push({
      surah: row[0] as number,
      ayah: row[1] as number,
      type: row[2] as string,
      score: row[3] != null ? (row[3] as number) : undefined,
    });
  }

  const mutRows = db.exec(
    `SELECT surah_b, ayah_b FROM mutashabihat WHERE surah_a = ? AND ayah_a = ?
     UNION ALL
     SELECT surah_a, ayah_a FROM mutashabihat WHERE surah_b = ? AND ayah_b = ?`,
    [surah, ayah, surah, ayah]
  );
  for (const row of mutRows[0]?.values ?? []) {
    results.push({
      surah: row[0] as number,
      ayah: row[1] as number,
      type: 'mutashabihat',
    });
  }

  return results;
}

export async function getTopicsAndThemes(surah: number, ayah: number): Promise<TopicsAndThemes> {
  const db = await getDb();

  const topicRows = db.exec('SELECT topic FROM ayah_topics WHERE surah = ? AND ayah = ?', [surah, ayah]);
  const topics = (topicRows[0]?.values ?? []).map(r => r[0] as string);

  const themeRows = db.exec('SELECT theme FROM ayah_themes WHERE surah = ? AND ayah = ?', [surah, ayah]);
  const themes = (themeRows[0]?.values ?? []).map(r => r[0] as string);

  return { topics, themes };
}
