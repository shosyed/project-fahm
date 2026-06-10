import { useSummarize, buildCitation } from '../ai/index.ts'
import styles from './TafsirBlock.module.css'

const LABELS: Record<string, string> = {
  jalalayn: 'Tafsir al-Jalalayn',
  ibnkathir: 'Tafsir Ibn Kathir',
}

interface Props {
  tafsirKey: string
  text: string
  surah: number
  ayah: number
}

export function TafsirBlock({ tafsirKey, text, surah, ayah }: Props) {
  const { state, summarize } = useSummarize()

  const citation = buildCitation(tafsirKey, surah, ayah)

  function handleClick() {
    summarize(text, tafsirKey, surah, ayah)
  }

  const isActive = state.status !== 'idle'

  return (
    <details className={styles.details}>
      <summary className={styles.summary}>
        {LABELS[tafsirKey] ?? tafsirKey}
      </summary>
      <div className={styles.body}>
        <p
          className={`${styles.arabicText}${isActive ? ` ${styles.verbatimHighlight}` : ''}`}
          dir="rtl"
          lang="ar"
        >
          {text}
        </p>

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

        {state.status === 'downloading' && (
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${state.progress}%` }} />
          </div>
        )}

        <button
          className={styles.aiBtn}
          onClick={handleClick}
          disabled={state.status === 'downloading' || state.status === 'generating'}
          title={state.status === 'idle' ? 'Summarize this tafsir using an on-device AI model' : undefined}
        >
          {state.status === 'idle' && 'Summarize (AI)'}
          {state.status === 'downloading' && `Downloading model… ${state.progress}%`}
          {state.status === 'generating' && 'Generating…'}
          {state.status === 'done' && 'Re-summarize'}
          {state.status === 'error' && 'Retry'}
        </button>
      </div>
    </details>
  )
}
