import { useState, useRef, useEffect } from 'react'
import { getEngine, subscribeProgress } from './webllm.ts'
import { buildCitation, CITATION_NAMES } from './citation.ts'

export type SummarizeState =
  | { status: 'idle' }
  | { status: 'downloading'; progress: number }
  | { status: 'generating'; partial: string }
  | { status: 'done'; summary: string }
  | { status: 'error'; message: string }

export const SYSTEM_PROMPT = `You are a tafsir analysis assistant for Quranic study. You will receive verbatim commentary from classical tafsir sources. Where available, both the Arabic original and its English translation are provided for the same source.

Your response must follow this structure exactly:

SUMMARY
Summarize ONLY what the provided commentary texts say — write 3–5 sentences covering the key points across all sources provided.

TRANSLATION NOTES
(Include this section only when both an Arabic original and its English translation are provided for the same tafsir source)
Identify 1–3 specific instances where the Arabic original and English translation differ in meaning, emphasis, or nuance. For each, explain what the difference reveals about the verse. Reference only the provided texts. If the texts are equivalent in meaning, write: "Translations are consistent in meaning." If only one language is available for all sources, omit this section entirely.

Rules you must follow without exception:
1. Use ONLY the provided commentary text — do not add facts, rulings, or interpretations not present in the provided text.
2. Do not use your own knowledge about Islam, the Quran, or Islamic scholarship.
3. Write in clear, plain English.
4. Do not generate the citation line — it will be added automatically.
5. If the provided text is too short or unclear to analyze, respond with exactly: "The provided text is insufficient to summarize."
6. Do not begin with "This text says" or "The commentary states" — begin directly with "SUMMARY".`

export interface TafsirEntry {
  text: string
  tafsirKey: string
  language: 'ar' | 'en'
}

export interface SummarizeControls {
  state: SummarizeState
  citation: string
  summarize: (entries: TafsirEntry[], surah: number, ayah: number) => void
}

export function useSummarize(): SummarizeControls {
  const [state, setState] = useState<SummarizeState>({ status: 'idle' })
  const [citation, setCitation] = useState('')
  const abortRef = useRef(false)

  useEffect(() => {
    return () => { abortRef.current = true }
  }, [])

  function summarize(entries: TafsirEntry[], surah: number, ayah: number) {
    abortRef.current = false
    setState({ status: 'downloading', progress: 0 })

    setCitation(buildCitation(entries.map(e => e.tafsirKey), surah, ayah))

    const unsubscribe = subscribeProgress(pct => {
      if (!abortRef.current) {
        setState({ status: 'downloading', progress: pct })
      }
    })

    // Build combined text with source label and language for each entry.
    // Arabic and English versions of the same tafsir are grouped together so
    // the model can compare them for translation differences.
    const combinedText = entries
      .map(e => {
        const name = CITATION_NAMES[e.tafsirKey] ?? e.tafsirKey
        const langLabel = e.language === 'ar' ? 'Arabic original' : 'English translation'
        return `[${name} — ${langLabel}]\n${e.text}`
      })
      .join('\n\n---\n\n')

    getEngine()
      .then(async engine => {
        unsubscribe()
        if (abortRef.current) return
        setState({ status: 'generating', partial: '' })

        // AUDIT: Anti-hallucination data-path verification
        // Passed to LLM:
        //   - SYSTEM_PROMPT (static constant)
        //   - combinedText: verbatim tafsir text(s) — Arabic originals and/or English
        //     translations — labeled by source name and language
        // NOT passed to LLM:
        //   - AyahRecord.arabic    (rendered verbatim by ArabicDisplay, never touches LLM)
        //   - AyahRecord.translations (rendered verbatim by TranslationList, never touches LLM)
        //   - The citation string (generated deterministically by buildCitation())
        const stream = await engine.chat.completions.create({
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: `Analyze the following tafsir commentary:\n\n"""\n${combinedText}\n"""` },
          ],
          stream: true,
          temperature: 0,
        })

        let accumulated = ''
        for await (const chunk of stream) {
          if (abortRef.current) break
          const delta = chunk.choices[0]?.delta?.content ?? ''
          accumulated += delta
          setState({ status: 'generating', partial: accumulated })
        }
        if (!abortRef.current) {
          setState({ status: 'done', summary: accumulated })
        }
      })
      .catch(err => {
        unsubscribe()
        if (!abortRef.current) {
          setState({ status: 'error', message: err instanceof Error ? err.message : String(err) })
        }
      })
  }

  return { state, citation, summarize }
}
