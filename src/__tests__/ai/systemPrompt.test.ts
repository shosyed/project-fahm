import { describe, it, expect } from 'vitest'
import { SYSTEM_PROMPT } from '../../ai/useSummarize.ts'

describe('SYSTEM_PROMPT anti-hallucination rules', () => {
  it('restricts summarization to provided text only', () => {
    expect(SYSTEM_PROMPT).toContain('Summarize ONLY')
  })

  it('forbids using the model\'s own knowledge', () => {
    expect(SYSTEM_PROMPT).toContain('Do not use your own knowledge')
  })

  it('instructs not to generate the citation line', () => {
    expect(SYSTEM_PROMPT).toContain('Do not generate the citation line')
  })

  it('does not reference arabic text or translations as inputs', () => {
    expect(SYSTEM_PROMPT.toLowerCase()).not.toContain('arabic')
    expect(SYSTEM_PROMPT.toLowerCase()).not.toContain('translations')
  })

  it('scopes input to tafsir commentary', () => {
    expect(SYSTEM_PROMPT.toLowerCase()).toContain('tafsir')
  })
})
