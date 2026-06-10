import styles from './TafsirBlock.module.css'

const LABELS: Record<string, string> = {
  jalalayn: 'Tafsir al-Jalalayn',
  ibnkathir: 'Tafsir Ibn Kathir',
}

interface Props {
  tafsirKey: string
  text: string
}

export function TafsirBlock({ tafsirKey, text }: Props) {
  return (
    <details className={styles.details}>
      <summary className={styles.summary}>
        {LABELS[tafsirKey] ?? tafsirKey}
      </summary>
      <div className={styles.body}>
        <p className={styles.arabicText} dir="rtl" lang="ar">{text}</p>
        <button
          className={styles.aiBtn}
          disabled
          title="AI summarization coming in a future update"
        >
          Summarize (AI)
        </button>
      </div>
    </details>
  )
}
