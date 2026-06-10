import type { AyahRecord } from '../db/index.ts'
import { TafsirBlock } from './TafsirBlock.tsx'

interface Props {
  tafsirs: AyahRecord['tafsirs']
}

const TAFSIR_ORDER = ['jalalayn', 'ibnkathir'] as const

export function TafsirSection({ tafsirs }: Props) {
  return (
    <div>
      {TAFSIR_ORDER.map(key => (
        <TafsirBlock key={key} tafsirKey={key} text={tafsirs[key] ?? ''} />
      ))}
    </div>
  )
}
