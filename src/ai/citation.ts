export const CITATION_NAMES: Record<string, string> = {
  jalalayn: 'Tafsir al-Jalalayn',
  ibnkathir: 'Tafsir Ibn Kathir',
  ibnkathir_en: 'Tafsir Ibn Kathir',  // same source, deduplicated in buildCitation
}

export function buildCitation(tafsirKey: string | string[], surah: number, ayah: number): string {
  const keys = typeof tafsirKey === 'string' ? [tafsirKey] : tafsirKey
  const seen = new Set<string>()
  const names: string[] = []
  for (const k of keys) {
    const name = CITATION_NAMES[k] ?? k
    if (!seen.has(name)) {
      seen.add(name)
      names.push(name)
    }
  }
  return `[Source: ${names.join(' & ')}, Surah ${surah}:${ayah}]`
}
