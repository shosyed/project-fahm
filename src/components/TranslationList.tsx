import type { AyahRecord } from '../db/index.ts'
import { TranslationBlock } from './TranslationBlock.tsx'

interface Props {
  translations: AyahRecord['translations']
}

const TRANSLATION_ORDER = ['yusufali', 'pickthall'] as const

export function TranslationList({ translations }: Props) {
  return (
    <div>
      {TRANSLATION_ORDER.map(key => (
        <TranslationBlock key={key} translatorKey={key} text={translations[key] ?? ''} />
      ))}
    </div>
  )
}
