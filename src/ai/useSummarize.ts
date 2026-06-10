import { useState, useRef, useEffect } from 'react'
import { getEngine, subscribeProgress } from './webllm.ts'

export type SummarizeState =
  | { status: 'idle' }
  | { status: 'downloading'; progress: number }
  | { status: 'generating'; partial: string }
  | { status: 'done'; summary: string }
  | { status: 'error'; message: string }

export const SYSTEM_PROMPT = `You are a summarization assistant for Quranic tafsir (commentary). You will be given verbatim text from a classical tafsir. Your task is to write a concise English summary of that commentary.

Rules you must follow without exception:
1. Summarize ONLY the provided commentary text. Do not add facts, rulings, or interpretations not present in the provided text.
2. Do not use your own knowledge about Islam, the Quran, or Islamic jurisprudence.
3. Write in clear, plain English. Do not transliterate any terms unless they appear in the provided text.
4. Do not generate the citation line — it will be added automatically.
5. If the provided text is too short or unclear to summarize meaningfully, respond with exactly: "The provided text is insufficient to summarize."
6. Do not begin your response with "This text says" or "The commentary states" — begin directly with the substance.
7. Keep the summary to 3–5 sentences.`

export interface SummarizeControls {
  state: SummarizeState
  summarize: (text: string, tafsirKey: string, surah: number, ayah: number) => void
}

export function useSummarize(): SummarizeControls {
  const [state, setState] = useState<SummarizeState>({ status: 'idle' })
  const abortRef = useRef(false)

  useEffect(() => {
    return () => { abortRef.current = true }
  }, [])

  function summarize(text: string, _tafsirKey: string, _surah: number, _ayah: number) {
    abortRef.current = false
    setState({ status: 'downloading', progress: 0 })

    const unsubscribe = subscribeProgress(pct => {
      if (!abortRef.current) {
        setState({ status: 'downloading', progress: pct })
      }
    })

    getEngine()
      .then(async engine => {
        unsubscribe()
        if (abortRef.current) return
        setState({ status: 'generating', partial: '' })

        // AUDIT: Anti-hallucination data-path verification
        // The only data passed to the LLM is:
        //   - SYSTEM_PROMPT (static constant, see top of this file)
        //   - `text`: the verbatim tafsir commentary string from AyahRecord.tafsirs[key]
        // NOT passed to the LLM:
        //   - AyahRecord.arabic    (rendered verbatim by ArabicDisplay, never touches LLM)
        //   - AyahRecord.translations (rendered verbatim by TranslationList, never touches LLM)
        //   - The citation string (generated deterministically by buildCitation() in src/ai/citation.ts)
        // The user message template is: `Summarize the following tafsir commentary:\n\n"""\n${text}\n"""`
        // systemPrompt.test.ts verifies SYSTEM_PROMPT contains anti-hallucination rules.
        // citation.test.ts verifies the citation is code-generated, not LLM-generated.
        const stream = await engine.chat.completions.create({
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: `Summarize the following tafsir commentary:\n\n"""\n${text}\n"""` },
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

  return { state, summarize }
}
