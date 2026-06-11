import { describe, it, expect } from 'vitest'
import { SYSTEM_PROMPT } from '../../ai/useSummarize.ts'

describe('SYSTEM_PROMPT anti-hallucination rules', () => {
  it('restricts analysis to provided text only', () => {
    expect(SYSTEM_PROMPT).toContain('Work only from the provided texts')
  })

  it('forbids using the model\'s own knowledge', () => {
    expect(SYSTEM_PROMPT).toContain('Do not use your own knowledge')
  })

  it('instructs not to generate the citation line', () => {
    expect(SYSTEM_PROMPT).toContain('Do not generate the citation line')
  })

  it('supports comparing Arabic originals with English translations of tafsir', () => {
    // Tafsir text in both Arabic and English is intentionally passed for comparison analysis.
    // Only the Quranic verse itself and its verse-translations never reach the model.
    expect(SYSTEM_PROMPT.toLowerCase()).toContain('arabic')
    expect(SYSTEM_PROMPT.toLowerCase()).toContain('english translation')
  })

  it('requires same-source comparison to prevent phantom discrepancies', () => {
    expect(SYSTEM_PROMPT).toContain('same source')
  })

  it('forbids issuing rulings or picking between conflicting sources', () => {
    expect(SYSTEM_PROMPT).toContain('Never pick a "correct" one')
  })

  it('includes conditional sections for key terms, context, and source differences', () => {
    expect(SYSTEM_PROMPT).toContain('KEY TERMS')
    expect(SYSTEM_PROMPT).toContain('CONTEXT')
    expect(SYSTEM_PROMPT).toContain('POINTS OF DIFFERENCE')
  })

  it('scopes input to tafsir commentary', () => {
    expect(SYSTEM_PROMPT.toLowerCase()).toContain('tafsir')
  })
})
