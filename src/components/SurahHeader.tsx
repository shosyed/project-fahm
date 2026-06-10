import type { SurahMeta } from '../db/index.ts'
import styles from './SurahHeader.module.css'

interface Props {
  meta: SurahMeta
  ayah: number
}

export function SurahHeader({ meta, ayah }: Props) {
  return (
    <header className={styles.header}>
      <h1 className={styles.arabicName} dir="rtl" lang="ar">{meta.name}</h1>
      <h2 className={styles.englishName}>{meta.englishName}</h2>
      <div className={styles.meta}>
        <span className={styles.badge}>{meta.revelationType}</span>
        <span className={styles.ayahNum}>Ayah {ayah} of {meta.ayahCount}</span>
      </div>
    </header>
  )
}
