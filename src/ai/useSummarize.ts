import { useState, useRef, useEffect } from 'react'
import { getEngine, subscribeProgress } from './webllm.ts'
import { buildCitation, CITATION_NAMES } from './citation.ts'

export type SummarizeState =
  | { status: 'idle' }
  | { status: 'downloading'; progress: number }
  | { status: 'generating'; partial: string }
  | { status: 'done'; summary: string }
  | { status: 'error'; message: string }

export const SYSTEM_PROMPT = `You are a tafsir study assistant for a Muslim reader working through the Quran verse by verse. You receive verbatim commentary from classical tafsir sources. Where available, both the Arabic original and its English translation are provided for the same source.

Your job is to help the reader understand this verse using only what the commentators wrote. Work only from the provided texts.

Your response must follow this structure exactly. Include a section only if the provided texts contain material for it — never pad a section to fill it.

SUMMARY
In 1–3 sentences, state what the commentary says this verse means. If the sources agree, give the shared explanation once. If they differ, attribute each view to its source by name (e.g. "Ibn Kathir explains… al-Jalalayn instead emphasizes…").

KEY TERMS
(Include only if a source explicitly explains a specific Arabic word, name, or phrase.)
List up to 3 terms the commentary itself defines or glosses. Give the term and the meaning as stated in the text. Do not define terms the texts leave unexplained.

CONTEXT
(Include only if a source states an occasion of revelation, a preceding or following event, or who is being addressed.)
In 1–2 sentences, give the situational context the commentary provides (e.g. the reason for revelation, the audience, the surrounding narrative).

TRANSLATION NOTES
(Include only when both an Arabic original and its English translation are provided for the same source.)
Identify 1–3 places where the Arabic and its English translation differ in meaning, emphasis, or nuance, and say what each difference reveals about the verse. Compare only matching Arabic/English pairs from the same source — never compare across different sources. If they match in meaning, write: "Translations are consistent in meaning." If no source has both languages, omit this section.

POINTS OF DIFFERENCE
(Include only if two or more sources actually disagree.)
In 1–2 sentences, name the sources and state precisely where they diverge. Omit this section if the sources agree or if only one source is provided.

Rules you must follow without exception:
1. Use ONLY the provided commentary text. Do not add facts, rulings, names, dates, hadith, or interpretations that are not in the provided text.
2. Do not use your own knowledge of Islam, the Quran, Arabic, or Islamic scholarship — even if you are confident it is correct.
3. Attribute disputed claims to the source that made them. If you cannot tell which source said something, state it plainly without attribution rather than guessing.
4. If sources conflict, present both views. Never pick a "correct" one, issue a ruling, or tell the reader what to believe or do.
5. Write in clear, plain English. Keep the whole response concise enough to read at a glance.
6. Do not generate the citation line — it will be added automatically.
7. If the provided text is too short or unclear to analyze, respond with exactly: "The provided text is insufficient to summarize."
8. Begin your response directly with the first applicable section heading. Do not write a preamble such as "This text says" or "The commentary states."`

export interface TafsirEntry {
  text: string
  tafsirKey: string
  language: 'ar' | 'en'
}

// Session-level cache: persists for the lifetime of the page, cleared on refresh.
// Keyed by "surah:ayah" → { summary, citation }.
const _cache = new Map<string, { summary: string; citation: string }>()

export interface SummarizeControls {
  state: SummarizeState
  citation: string
  summarize: (entries: TafsirEntry[], surah: number, ayah: number) => void
  restore: (surah: number, ayah: number) => boolean
}

export function useSummarize(): SummarizeControls {
  const [state, setState] = useState<SummarizeState>({ status: 'idle' })
  const [citation, setCitation] = useState('')
  const abortRef = useRef(false) // true on unmount → aborts any in-flight run
  const genRef = useRef(0)       // incremented each call → superseded runs bail early

  useEffect(() => {
    return () => { abortRef.current = true }
  }, [])

  function restore(surah: number, ayah: number): boolean {
    const cached = _cache.get(`${surah}:${ayah}`)
    if (!cached) return false
    setState({ status: 'done', summary: cached.summary })
    setCitation(cached.citation)
    return true
  }

  function summarize(entries: TafsirEntry[], surah: number, ayah: number) {
    const myGen = ++genRef.current
    abortRef.current = false
    setState({ status: 'downloading', progress: 0 })

    const theCitation = buildCitation(entries.map(e => e.tafsirKey), surah, ayah)
    setCitation(theCitation)

    const cacheKey = `${surah}:${ayah}`
    const unsubscribe = subscribeProgress(pct => {
      if (genRef.current === myGen && !abortRef.current) {
        setState({ status: 'downloading', progress: pct })
      }
    })

    // Truncate each entry to fit within the model's context window.
    // Arabic tokenizes at ~2× density vs English, so Arabic entries get a tighter budget.
    // With context_window_size: 8192 and ~350 tokens for the system prompt, we have
    // roughly 7800 tokens available. These limits keep total well inside that.
    const CHAR_LIMIT: Record<TafsirEntry['language'], number> = { ar: 2500, en: 5000 }
    const truncated = entries.map(e => {
      const limit = CHAR_LIMIT[e.language]
      const text = e.text.length > limit
        ? e.text.slice(0, limit) + '\n[… text truncated to fit model context …]'
        : e.text
      return { ...e, text }
    })

    // Build combined text with source label and language for each entry.
    // Arabic and English versions of the same tafsir are grouped together so
    // the model can compare them for translation differences.
    const combinedText = truncated
      .map(e => {
        const name = CITATION_NAMES[e.tafsirKey] ?? e.tafsirKey
        const langLabel = e.language === 'ar' ? 'Arabic original' : 'English translation'
        return `[${name} — ${langLabel}]\n${e.text}`
      })
      .join('\n\n---\n\n')

    const isActive = () => genRef.current === myGen && !abortRef.current

    getEngine()
      .then(async engine => {
        unsubscribe()
        if (!isActive()) return
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
          if (!isActive()) break
          const delta = chunk.choices[0]?.delta?.content ?? ''
          accumulated += delta
          setState({ status: 'generating', partial: accumulated })
        }
        if (isActive()) {
          setState({ status: 'done', summary: accumulated })
          _cache.set(cacheKey, { summary: accumulated, citation: theCitation })
        }
      })
      .catch(err => {
        unsubscribe()
        if (isActive()) {
          setState({ status: 'error', message: err instanceof Error ? err.message : String(err) })
        }
      })
  }

  return { state, citation, summarize, restore }
}
