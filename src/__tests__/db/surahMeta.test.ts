import { describe, it, expect } from 'vitest'
import { getSurahMeta, SURAH_META } from '../../db/surahMeta.ts'

describe('getSurahMeta', () => {
  it('returns Al-Fatiha for surah 1', () => {
    const meta = getSurahMeta(1)
    expect(meta.number).toBe(1)
    expect(meta.englishName).toBe('Al-Fatiha')
    expect(meta.ayahCount).toBe(7)
    expect(meta.revelationType).toBe('Meccan')
  })

  it('returns An-Nas for surah 114', () => {
    const meta = getSurahMeta(114)
    expect(meta.number).toBe(114)
    expect(meta.englishName).toBe('An-Nas')
    expect(meta.ayahCount).toBe(6)
    expect(meta.revelationType).toBe('Meccan')
  })

  it('returns Al-Baqara as Medinan', () => {
    const meta = getSurahMeta(2)
    expect(meta.revelationType).toBe('Medinan')
    expect(meta.ayahCount).toBe(286)
  })

  it('throws for surah 0', () => {
    expect(() => getSurahMeta(0)).toThrow('Invalid surah number: 0')
  })

  it('throws for surah 115', () => {
    expect(() => getSurahMeta(115)).toThrow('Invalid surah number: 115')
  })
})

describe('SURAH_META', () => {
  it('has exactly 114 entries', () => {
    expect(SURAH_META).toHaveLength(114)
  })

  it('has consecutive numbers from 1 to 114', () => {
    SURAH_META.forEach((s, i) => {
      expect(s.number).toBe(i + 1)
    })
  })

  it('all revelationType values are Meccan or Medinan', () => {
    const valid = new Set(['Meccan', 'Medinan'])
    SURAH_META.forEach(s => {
      expect(valid.has(s.revelationType)).toBe(true)
    })
  })
})
