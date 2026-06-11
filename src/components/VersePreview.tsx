import { useState, useEffect } from 'react'
import { getAyah, getSurahMeta } from '../db/index.ts'
import type { AyahRecord } from '../db/index.ts'
import { ArabicDisplay } from './ArabicDisplay.tsx'
import { TranslationList } from './TranslationList.tsx'
import { TafsirSection } from './TafsirSection.tsx'
import styles from './VersePreview.module.css'

interface Props {
  surah: number
  ayah: number
  onBack: () => void
}

export function VersePreview({ surah, ayah, onBack }: Props) {
  const [record, setRecord] = useState<AyahRecord | null>(null)
  const surahMeta = getSurahMeta(surah)

  useEffect(() => {
    setRecord(null)
    getAyah(surah, ayah).then(setRecord)
  }, [surah, ayah])

  return (
    <div className={styles.preview}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={onBack}>← Back</button>
        <span className={styles.ref}>{surah}:{ayah}</span>
        <span className={styles.surahName}>{surahMeta.englishName}</span>
      </div>
      {record ? (
        <>
          <ArabicDisplay arabic={record.arabic} />
          <TranslationList translations={record.translations} />
          <TafsirSection tafsirs={record.tafsirs} surah={surah} ayah={ayah} />
        </>
      ) : (
        <div className={styles.loading}>Loading…</div>
      )}
    </div>
  )
}
