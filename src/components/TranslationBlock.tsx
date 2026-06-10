import styles from './TranslationBlock.module.css'

const LABELS: Record<string, string> = {
  yusufali: 'Abdullah Yusuf Ali (1934)',
  pickthall: 'Marmaduke Pickthall (1930)',
}

interface Props {
  translatorKey: string
  text: string
}

export function TranslationBlock({ translatorKey, text }: Props) {
  return (
    <div className={styles.block}>
      <span className={styles.label}>{LABELS[translatorKey] ?? translatorKey}</span>
      <p className={styles.text}>{text}</p>
    </div>
  )
}
