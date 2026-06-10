import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Database, QueryExecResult } from 'sql.js'

// Mock getDb to return a fake Database
const mockExec = vi.fn<(...args: unknown[]) => QueryExecResult[]>()
const mockDb = { exec: mockExec } as unknown as Database

vi.mock('../../db/loader.ts', () => ({
  getDb: vi.fn().mockResolvedValue(mockDb),
}))

// Import AFTER mock is set up
const { getAyah, getTopicsAndThemes } = await import('../../db/queries.ts')

describe('getAyah', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns correct AyahRecord shape', async () => {
    mockExec
      .mockReturnValueOnce([{ columns: ['arabic'], values: [['بِسْمِ اللَّهِ']] }])
      .mockReturnValueOnce([{ columns: ['key', 'text'], values: [['yusufali', 'In the name of Allah'], ['pickthall', 'In the name of Allah']] }])
      .mockReturnValueOnce([{ columns: ['key', 'text'], values: [['jalalayn', 'Commentary text'], ['ibnkathir', 'More commentary']] }])

    const result = await getAyah(1, 1)
    expect(result.arabic).toBe('بِسْمِ اللَّهِ')
    expect(result.translations['yusufali']).toBe('In the name of Allah')
    expect(result.translations['pickthall']).toBe('In the name of Allah')
    expect(result.tafsirs['jalalayn']).toBe('Commentary text')
    expect(result.tafsirs['ibnkathir']).toBe('More commentary')
  })

  it('throws when ayah is not found', async () => {
    mockExec.mockReturnValueOnce([])
    await expect(getAyah(999, 999)).rejects.toThrow('Ayah not found: 999:999')
  })

  it('returns empty translations when no rows exist', async () => {
    mockExec
      .mockReturnValueOnce([{ columns: ['arabic'], values: [['test arabic']] }])
      .mockReturnValueOnce([])
      .mockReturnValueOnce([])
    const result = await getAyah(1, 1)
    expect(result.translations).toEqual({})
    expect(result.tafsirs).toEqual({})
  })
})

describe('getTopicsAndThemes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns empty arrays when no rows exist', async () => {
    mockExec.mockReturnValueOnce([]).mockReturnValueOnce([])
    const result = await getTopicsAndThemes(1, 1)
    expect(result.topics).toEqual([])
    expect(result.themes).toEqual([])
  })

  it('returns populated arrays from rows', async () => {
    mockExec
      .mockReturnValueOnce([{ columns: ['topic'], values: [['Creation'], ['Guidance']] }])
      .mockReturnValueOnce([{ columns: ['theme'], values: [['Worship']] }])
    const result = await getTopicsAndThemes(1, 1)
    expect(result.topics).toEqual(['Creation', 'Guidance'])
    expect(result.themes).toEqual(['Worship'])
  })
})
