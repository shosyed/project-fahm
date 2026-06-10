import { useState, useRef, useEffect } from 'react'
import { getEngine, subscribeProgress } from './webllm.ts'

export type SummarizeState =
  | { status: 'idle' }
  | { status: 'downloading'; progress: number }
  | { status: 'generating'; partial: string }
  | { status: 'done'; summary: string }
  | { status: 'error'; message: string }

const SYSTEM_PROMPT = `You are a summarization assistant for Quranic tafsir (commentary). You will be given verbatim text from a classical tafsir. Your task is to write a concise English summary of that commentary.

Rules you must follow without exception:
1. Summarize ONLY the provided commentary text. Do not add facts, rulings, or interpretations not present in the provided text.
2. Do not use your own knowledge about Islam, the Quran, Arabic, or Islamic jurisprudence.
3. Write in clear, plain English. Do not transliterate Arabic terms unless they appear in the provided text.
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
