export const CITATION_NAMES: Record<string, string> = {
  jalalayn: 'Tafsir al-Jalalayn',
  ibnkathir: 'Tafsir Ibn Kathir',
}

export function buildCitation(tafsirKey: string | string[], surah: number, ayah: number): string {
  const keys = typeof tafsirKey === 'string' ? [tafsirKey] : tafsirKey
  const names = keys.map(k => CITATION_NAMES[k] ?? k).join(' & ')
  return `[Source: ${names}, Surah ${surah}:${ayah}]`
}
