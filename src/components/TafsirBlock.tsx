import { useState } from 'react'
import styles from './TafsirBlock.module.css'

const LABELS: Record<string, string> = {
  jalalayn: 'Tafsir al-Jalalayn',
  ibnkathir: 'Tafsir Ibn Kathir',
}

interface Props {
  tafsirKey: string
  arabicText: string    // Arabic original — always present
  englishText?: string  // English translation — shown as primary when available
  isActive?: boolean
}

export function TafsirBlock({ tafsirKey, arabicText, englishText, isActive = false }: Props) {
  const [expanded, setExpanded] = useState(false)
  const showFull = expanded || isActive
  const hasEnglish = Boolean(englishText)

  return (
    <details className={styles.details} open>
      <summary className={styles.summary}>
        {LABELS[tafsirKey] ?? tafsirKey}
      </summary>
      <div className={styles.body}>
        {hasEnglish ? (
          <>
            <p
              className={[
                styles.englishText,
                isActive ? styles.verbatimHighlight : '',
                !showFull ? styles.textCollapsed : '',
              ].filter(Boolean).join(' ')}
            >
              {englishText}
            </p>
            <button
              className={styles.readMoreBtn}
              onClick={() => setExpanded(e => !e)}
            >
              {showFull ? 'Show less' : 'Read more'}
            </button>
            <details className={styles.arabicToggle}>
              <summary className={styles.arabicToggleSummary}>View Arabic original</summary>
              <p className={styles.arabicText} dir="rtl" lang="ar">{arabicText}</p>
            </details>
          </>
        ) : (
          <>
            <p
              className={[
                styles.arabicText,
                isActive ? styles.verbatimHighlight : '',
                !showFull ? styles.textCollapsed : '',
              ].filter(Boolean).join(' ')}
              dir="rtl"
              lang="ar"
            >
              {arabicText}
            </p>
            <button
              className={styles.readMoreBtn}
              onClick={() => setExpanded(e => !e)}
            >
              {showFull ? 'Show less' : 'Read more'}
            </button>
          </>
        )}
      </div>
    </details>
  )
}
