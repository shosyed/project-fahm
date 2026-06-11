import { useState } from 'react'
import { useSummarize, buildCitation } from '../ai/index.ts'
import styles from './TafsirBlock.module.css'

const LABELS: Record<string, string> = {
  jalalayn: 'Tafsir al-Jalalayn',
  ibnkathir: 'Tafsir Ibn Kathir',
}

// Some tafsirs (e.g. Ibn Kathir from api.quran.com) are stored with HTML markup.
// Strip tags and decode entities so plain Arabic text is displayed.
function stripHtml(raw: string): string {
  const doc = new DOMParser().parseFromString(raw, 'text/html')
  return doc.body.textContent ?? raw
}

interface Props {
  tafsirKey: string
  text: string
  surah: number
  ayah: number
}

export function TafsirBlock({ tafsirKey, text, surah, ayah }: Props) {
  const { state, summarize } = useSummarize()
  const [expanded, setExpanded] = useState(false)

  const plainText = stripHtml(text)
  const citation = buildCitation(tafsirKey, surah, ayah)
  const isActive = state.status !== 'idle'
  // Auto-expand when summary is active so user can see the source alongside the summary
  const showFull = expanded || isActive

  function handleClick() {
    summarize(plainText, tafsirKey, surah, ayah)
  }

  return (
    <details className={styles.details}>
      <summary className={styles.summary}>
        {LABELS[tafsirKey] ?? tafsirKey}
      </summary>
      <div className={styles.body}>

        {/* AI button at the top */}
        <div className={styles.aiRow}>
          <button
            className={styles.aiBtn}
            onClick={handleClick}
            disabled={state.status === 'downloading' || state.status === 'generating'}
          >
            {state.status === 'idle' && '✦ Summarize in English (AI)'}
            {state.status === 'downloading' && `Downloading AI model… ${state.progress}%`}
            {state.status === 'generating' && 'Generating summary…'}
            {state.status === 'done' && '✦ Re-summarize'}
            {state.status === 'error' && 'Retry'}
          </button>
          {state.status === 'idle' && (
            <span className={styles.aiHint}>
              Runs locally on your device · first use downloads ~2 GB model
            </span>
          )}
        </div>

        {state.status === 'downloading' && (
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${state.progress}%` }} />
          </div>
        )}

        {state.status !== 'idle' && (
          <div className={styles.summaryBox}>
            {(state.status === 'generating' || state.status === 'done') && (
              <p className={styles.summaryText}>
                {state.status === 'generating' ? state.partial : state.summary}
              </p>
            )}
            {state.status === 'error' && (
              <p className={styles.errorText}>{state.message}</p>
            )}
            <p className={styles.citation}>{citation}</p>
          </div>
        )}

        {/* Verbatim Arabic tafsir text — always shown; highlighted when summary is active */}
        <p
          className={[
            styles.arabicText,
            isActive ? styles.verbatimHighlight : '',
            !showFull ? styles.arabicTextCollapsed : '',
          ].filter(Boolean).join(' ')}
          dir="rtl"
          lang="ar"
        >
          {plainText}
        </p>
        <button
          className={styles.readMoreBtn}
          onClick={() => setExpanded(e => !e)}
        >
          {showFull ? 'Show less' : 'Read more'}
        </button>

      </div>
    </details>
  )
}
