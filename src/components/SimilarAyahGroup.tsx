import { SURAH_META } from '../db/index.ts'
import styles from './SimilarAyahGroup.module.css'
import type { SimilarAyah } from '../db/index.ts'

interface Props {
  label: string
  items: SimilarAyah[]
  onNavigate: (surah: number, ayah: number) => void
  startOpen?: boolean
  displayLimit?: number
}

export function SimilarAyahGroup({ label, items, onNavigate, startOpen = true, displayLimit }: Props) {
  const displayed = displayLimit ? items.slice(0, displayLimit) : items
  const hidden = items.length - displayed.length

  return (
    <details className={styles.details} open={startOpen || undefined}>
      <summary className={styles.summary}>
        {label} <span className={styles.count}>({items.length})</span>
      </summary>
      <ul className={styles.list}>
        {displayed.map(item => {
          const surahName = SURAH_META[item.surah - 1]?.englishName ?? ''
          return (
            <li key={`${item.surah}:${item.ayah}`} className={styles.item}>
              <button
                className={styles.refBtn}
                onClick={() => onNavigate(item.surah, item.ayah)}
              >
                <span className={styles.ref}>{item.surah}:{item.ayah}</span>
                <span className={styles.surahName}>{surahName}</span>
              </button>
            </li>
          )
        })}
        {hidden > 0 && (
          <li className={styles.more}>Showing {displayed.length} of {items.length}</li>
        )}
      </ul>
    </details>
  )
}
