export const CITATION_NAMES: Record<string, string> = {
  jalalayn: 'Tafsir al-Jalalayn',
  ibnkathir: 'Tafsir Ibn Kathir',
}

export function buildCitation(tafsirKey: string, surah: number, ayah: number): string {
  const name = CITATION_NAMES[tafsirKey] ?? tafsirKey
  return `[Source: ${name}, Surah ${surah}:${ayah}]`
}
