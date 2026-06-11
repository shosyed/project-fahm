import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getAyah, getSurahMeta } from '../db/index.ts'
import type { AyahRecord } from '../db/index.ts'
import { NavBar } from './NavBar.tsx'
import { SurahHeader } from './SurahHeader.tsx'
import { ArabicDisplay } from './ArabicDisplay.tsx'
import { TranslationList } from './TranslationList.tsx'
import { TafsirSection } from './TafsirSection.tsx'
import { RelatedVersesPanel } from './RelatedVersesPanel.tsx'
import styles from './ReaderPage.module.css'

export function ReaderPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navRef = useRef<HTMLDivElement>(null)
  const [navHeight, setNavHeight] = useState(0)

  const rawSurah = parseInt(searchParams.get('surah') ?? '1', 10)
  const surah = isNaN(rawSurah) || rawSurah < 1 || rawSurah > 114 ? 1 : rawSurah
  const surahMeta = getSurahMeta(surah)
  const rawAyah = parseInt(searchParams.get('ayah') ?? '1', 10)
  const ayah = isNaN(rawAyah) || rawAyah < 1 ? 1 : Math.min(rawAyah, surahMeta.ayahCount)

  const [record, setRecord] = useState<AyahRecord | null>(null)

  useEffect(() => {
    setRecord(null)
    getAyah(surah, ayah).then(setRecord)
  }, [surah, ayah])

  useEffect(() => {
    if (!navRef.current) return
    const ro = new ResizeObserver(() => {
      if (navRef.current) setNavHeight(navRef.current.offsetHeight)
    })
    ro.observe(navRef.current)
    return () => ro.disconnect()
  }, [])

  function onNavigate(newSurah: number, newAyah: number) {
    setSearchParams({ surah: String(newSurah), ayah: String(newAyah) })
  }

  return (
    <div className={styles.page}>
      <div ref={navRef} className={styles.stickyNav}>
        <NavBar surah={surah} ayah={ayah} surahMeta={surahMeta} onNavigate={onNavigate} />
      </div>
      <div className={styles.body}>
        <div className={styles.mainColumn}>
          <SurahHeader meta={surahMeta} ayah={ayah} />
          {record ? (
            <>
              <ArabicDisplay arabic={record.arabic} />
              <TranslationList translations={record.translations} />
              <TafsirSection tafsirs={record.tafsirs} surah={surah} ayah={ayah} />
            </>
          ) : (
            <div className={styles.ayahLoading}>Loading verse…</div>
          )}
        </div>
        <div
          className={styles.rightPanel}
          style={{ top: navHeight, maxHeight: `calc(100vh - ${navHeight}px)` }}
        >
          <RelatedVersesPanel surah={surah} ayah={ayah} onNavigate={onNavigate} />
        </div>
      </div>
    </div>
  )
}
