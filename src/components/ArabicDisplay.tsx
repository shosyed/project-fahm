import styles from './ArabicDisplay.module.css'

interface Props {
  arabic: string
}

export function ArabicDisplay({ arabic }: Props) {
  return (
    <div className={styles.container}>
      <p className={styles.text} dir="rtl" lang="ar">{arabic}</p>
    </div>
  )
}
