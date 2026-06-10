import styles from './ErrorScreen.module.css'

interface Props {
  error: Error
}

export function ErrorScreen({ error }: Props) {
  return (
    <div className={styles.container}>
      <h1 className={styles.heading}>Failed to load database</h1>
      <p className={styles.message}>
        The Quran database could not be fetched. Check your network connection and reload the page.
      </p>
      <code className={styles.detail}>{error.message}</code>
      <button className={styles.reload} onClick={() => window.location.reload()}>
        Reload
      </button>
    </div>
  )
}
