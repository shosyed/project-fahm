import { useState } from 'react'
import styles from './TafsirBlock.module.css'

const LABELS: Record<string, string> = {
  jalalayn: 'Tafsir al-Jalalayn',
  ibnkathir: 'Tafsir Ibn Kathir',
}

interface Props {
  tafsirKey: string
  text: string       // HTML-stripped, ready to render
  isActive?: boolean // true when a summary is being generated/shown
}

export function TafsirBlock({ tafsirKey, text, isActive = false }: Props) {
  const [expanded, setExpanded] = useState(false)
  const showFull = expanded || isActive

  return (
    <details className={styles.details} open>
      <summary className={styles.summary}>
        {LABELS[tafsirKey] ?? tafsirKey}
      </summary>
      <div className={styles.body}>
        <p
          className={[
            styles.arabicText,
            isActive ? styles.verbatimHighlight : '',
            !showFull ? styles.arabicTextCollapsed : '',
          ].filter(Boolean).join(' ')}
          dir="rtl"
          lang="ar"
        >
          {text}
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
