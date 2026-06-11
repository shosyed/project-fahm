import { useEffect } from 'react'
import { useSummarize } from '../ai/index.ts'
import type { TafsirEntry } from '../ai/index.ts'
import type { AyahRecord } from '../db/index.ts'
import { TafsirBlock } from './TafsirBlock.tsx'
import styles from './TafsirSection.module.css'

interface Props {
  tafsirs: AyahRecord['tafsirs']
  surah: number
  ayah: number
}

const TAFSIR_PAIRS = [
  { arKey: 'jalalayn',  enKey: 'jalalayn_en',  label: 'Tafsir al-Jalalayn' },
  { arKey: 'ibnkathir', enKey: 'ibnkathir_en', label: 'Tafsir Ibn Kathir'  },
] as const

function stripHtml(raw: string): string {
  const doc = new DOMParser().parseFromString(raw, 'text/html')
  return doc.body.textContent ?? raw
}

export function TafsirSection({ tafsirs, surah, ayah }: Props) {
  const { state, citation, summarize, restore } = useSummarize()
  const isActive = state.status !== 'idle'

  // Build entries for the LLM — Arabic original first, then English translation for each pair
  const entries: TafsirEntry[] = []
  for (const { arKey, enKey } of TAFSIR_PAIRS) {
    if (tafsirs[arKey]) entries.push({ text: stripHtml(tafsirs[arKey]!), tafsirKey: arKey, language: 'ar' })
    if (tafsirs[enKey]) entries.push({ text: stripHtml(tafsirs[enKey]!), tafsirKey: enKey, language: 'en' })
  }

  // On every ayah open: restore from session cache if available, otherwise run fresh.
  // tafsirs/summarize/restore change in lock-step with surah/ayah — safe to omit from deps.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (restore(surah, ayah)) return
    const autoEntries: TafsirEntry[] = []
    for (const { arKey, enKey } of TAFSIR_PAIRS) {
      if (tafsirs[arKey]) autoEntries.push({ text: stripHtml(tafsirs[arKey]!), tafsirKey: arKey, language: 'ar' })
      if (tafsirs[enKey]) autoEntries.push({ text: stripHtml(tafsirs[enKey]!), tafsirKey: enKey, language: 'en' })
    }
    if (autoEntries.length > 0) {
      summarize(autoEntries, surah, ayah)
    }
  }, [surah, ayah])

  function handleSummarize() {
    summarize(entries, surah, ayah)
  }

  return (
    <section className={styles.section}>
      <div className={styles.headerRow}>
        <h3 className={styles.heading}>Commentary</h3>
        <div className={styles.aiRow}>
          <button
            className={styles.aiBtn}
            onClick={handleSummarize}
            disabled={state.status === 'downloading' || state.status === 'generating'}
          >
            {state.status === 'idle'        && '✦ Analyze & compare (AI)'}
            {state.status === 'downloading' && `Downloading model… ${state.progress}%`}
            {state.status === 'generating'  && 'Analyzing…'}
            {state.status === 'done'        && '✦ Re-analyze'}
            {state.status === 'error'       && 'Retry'}
          </button>
          {state.status === 'downloading' && (
            <span className={styles.aiHint}>
              First use downloads ~2 GB model · runs locally in your browser · cached after
            </span>
          )}
        </div>
      </div>

      {state.status === 'downloading' && (
        <div className={styles.progressBar}>
          <div className={styles.progressFill} style={{ width: `${state.progress}%` }} />
        </div>
      )}

      {state.status !== 'idle' && (
        <div className={styles.summaryBox}>
          {(state.status === 'generating' || state.status === 'done') && (
            <div className={styles.summaryText}>
              {(state.status === 'generating' ? state.partial : state.summary)
                .split('\n')
                .map((line, i) => {
                  if (['SUMMARY', 'KEY TERMS', 'CONTEXT', 'TRANSLATION NOTES', 'POINTS OF DIFFERENCE'].includes(line)) {
                    return <p key={i} className={styles.summarySection}>{line}</p>
                  }
                  return line ? <p key={i}>{line}</p> : <br key={i} />
                })
              }
            </div>
          )}
          {state.status === 'error' && (
            <p className={styles.errorText}>{state.message}</p>
          )}
          <p className={styles.citationText}>{citation}</p>
        </div>
      )}

      {TAFSIR_PAIRS.map(({ arKey, enKey }) => {
        const arRaw = tafsirs[arKey]
        const enRaw = tafsirs[enKey]
        if (!arRaw && !enRaw) return null
        return (
          <TafsirBlock
            key={arKey}
            tafsirKey={arKey}
            arabicText={arRaw ? stripHtml(arRaw) : ''}
            englishText={enRaw ? stripHtml(enRaw) : undefined}
            isActive={isActive}
          />
        )
      })}
    </section>
  )
}
