import { useSummarize } from '../ai/index.ts'
import type { AyahRecord } from '../db/index.ts'
import { TafsirBlock } from './TafsirBlock.tsx'
import styles from './TafsirSection.module.css'

interface Props {
  tafsirs: AyahRecord['tafsirs']
  surah: number
  ayah: number
}

const TAFSIR_ORDER = ['jalalayn', 'ibnkathir'] as const

function stripHtml(raw: string): string {
  const doc = new DOMParser().parseFromString(raw, 'text/html')
  return doc.body.textContent ?? raw
}

export function TafsirSection({ tafsirs, surah, ayah }: Props) {
  const { state, citation, summarize } = useSummarize()
  const isActive = state.status !== 'idle'

  const entries = TAFSIR_ORDER
    .filter(key => tafsirs[key])
    .map(key => ({ text: stripHtml(tafsirs[key]!), tafsirKey: key }))

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
            {state.status === 'idle' && '✦ Summarize both (AI)'}
            {state.status === 'downloading' && `Downloading model… ${state.progress}%`}
            {state.status === 'generating' && 'Generating…'}
            {state.status === 'done' && '✦ Re-summarize'}
            {state.status === 'error' && 'Retry'}
          </button>
          {state.status === 'idle' && (
            <span className={styles.aiHint}>Runs locally · first use ~2 GB download</span>
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
            <p className={styles.summaryText}>
              {state.status === 'generating' ? state.partial : state.summary}
            </p>
          )}
          {state.status === 'error' && (
            <p className={styles.errorText}>{state.message}</p>
          )}
          <p className={styles.citationText}>{citation}</p>
        </div>
      )}

      {entries.map(e => (
        <TafsirBlock
          key={e.tafsirKey}
          tafsirKey={e.tafsirKey}
          text={e.text}
          isActive={isActive}
        />
      ))}
    </section>
  )
}
