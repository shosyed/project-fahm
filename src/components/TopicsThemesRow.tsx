import styles from './TopicsThemesRow.module.css'

interface Props {
  topics: string[]
  themes: string[]
}

export function TopicsThemesRow({ topics, themes }: Props) {
  if (topics.length === 0 && themes.length === 0) return null
  return (
    <div className={styles.row}>
      {topics.map(t => (
        <span key={t} className={`${styles.pill} ${styles.topic}`}>{t}</span>
      ))}
      {themes.map(t => (
        <span key={t} className={`${styles.pill} ${styles.theme}`}>{t}</span>
      ))}
    </div>
  )
}
