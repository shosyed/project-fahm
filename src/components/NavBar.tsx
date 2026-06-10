import type { SurahMeta } from '../db/index.ts'
import { SURAH_META } from '../db/index.ts'
import styles from './NavBar.module.css'

interface Props {
  surah: number
  ayah: number
  surahMeta: SurahMeta
  onNavigate: (surah: number, ayah: number) => void
}

export function NavBar({ surah, ayah, surahMeta, onNavigate }: Props) {
  function prevSurah() { onNavigate(surah - 1, 1) }
  function nextSurah() { onNavigate(surah + 1, 1) }

  function prevAyah() {
    if (ayah > 1) {
      onNavigate(surah, ayah - 1)
    } else if (surah > 1) {
      const prevMeta = SURAH_META[surah - 2]
      onNavigate(surah - 1, prevMeta.ayahCount)
    }
  }

  function nextAyah() {
    if (ayah < surahMeta.ayahCount) {
      onNavigate(surah, ayah + 1)
    } else if (surah < 114) {
      onNavigate(surah + 1, 1)
    }
  }

  const isFirst = surah === 1 && ayah === 1
  const isLast = surah === 114 && ayah === surahMeta.ayahCount

  return (
    <nav className={styles.nav}>
      <div className={styles.surahRow}>
        <button onClick={prevSurah} disabled={surah === 1} className={styles.btn} title="Previous surah">‹ Surah</button>
        <select
          className={styles.surahSelect}
          value={surah}
          onChange={e => onNavigate(parseInt(e.target.value, 10), 1)}
        >
          {SURAH_META.map(s => (
            <option key={s.number} value={s.number}>
              {s.number}. {s.englishName} ({s.name})
            </option>
          ))}
        </select>
        <button onClick={nextSurah} disabled={surah === 114} className={styles.btn} title="Next surah">Surah ›</button>
      </div>
      <div className={styles.ayahRow}>
        <button onClick={prevAyah} disabled={isFirst} className={styles.btn} title="Previous ayah">‹ Ayah</button>
        <input
          className={styles.ayahInput}
          type="number"
          min={1}
          max={surahMeta.ayahCount}
          value={ayah}
          onChange={e => {
            const v = parseInt(e.target.value, 10)
            if (!isNaN(v) && v >= 1 && v <= surahMeta.ayahCount) {
              onNavigate(surah, v)
            }
          }}
        />
        <span className={styles.ayahOf}>/ {surahMeta.ayahCount}</span>
        <button onClick={nextAyah} disabled={isLast} className={styles.btn} title="Next ayah">Ayah ›</button>
      </div>
    </nav>
  )
}
