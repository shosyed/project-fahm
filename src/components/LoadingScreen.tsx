import styles from './LoadingScreen.module.css'

export function LoadingScreen() {
  return (
    <div className={styles.container}>
      <div className={styles.spinner} />
      <p className={styles.text}>Loading Quran database…</p>
    </div>
  )
}
