import { describe, it, expect } from 'vitest'
import { buildCitation, CITATION_NAMES } from '../../ai/citation.ts'

describe('buildCitation', () => {
  it('formats jalalayn correctly', () => {
    expect(buildCitation('jalalayn', 2, 255)).toBe('[Source: Tafsir al-Jalalayn, Surah 2:255]')
  })

  it('formats ibnkathir correctly', () => {
    expect(buildCitation('ibnkathir', 1, 1)).toBe('[Source: Tafsir Ibn Kathir, Surah 1:1]')
  })

  it('falls back to raw key for unknown tafsirKey', () => {
    expect(buildCitation('unknownkey', 3, 10)).toBe('[Source: unknownkey, Surah 3:10]')
  })

  it('always starts with [Source:', () => {
    expect(buildCitation('jalalayn', 1, 1)).toMatch(/^\[Source: /)
    expect(buildCitation('ibnkathir', 114, 6)).toMatch(/^\[Source: /)
    expect(buildCitation('other', 2, 2)).toMatch(/^\[Source: /)
  })
})

describe('CITATION_NAMES', () => {
  it('contains entry for jalalayn', () => {
    expect('jalalayn' in CITATION_NAMES).toBe(true)
    expect(CITATION_NAMES['jalalayn']).toBe('Tafsir al-Jalalayn')
  })

  it('contains entry for ibnkathir', () => {
    expect('ibnkathir' in CITATION_NAMES).toBe(true)
    expect(CITATION_NAMES['ibnkathir']).toBe('Tafsir Ibn Kathir')
  })
})
