import type { AyahRecord } from '../db/index.ts'
import { TranslationBlock } from './TranslationBlock.tsx'
import styles from './TranslationList.module.css'

interface Props {
  translations: AyahRecord['translations']
}

const TRANSLATION_ORDER = ['yusufali', 'pickthall'] as const

export function TranslationList({ translations }: Props) {
  return (
    <div className={styles.grid}>
      {TRANSLATION_ORDER.map(key => (
        <TranslationBlock key={key} translatorKey={key} text={translations[key] ?? ''} />
      ))}
    </div>
  )
}
