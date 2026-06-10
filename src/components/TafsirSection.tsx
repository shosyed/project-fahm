import type { AyahRecord } from '../db/index.ts'
import { TafsirBlock } from './TafsirBlock.tsx'

interface Props {
  tafsirs: AyahRecord['tafsirs']
  surah: number
  ayah: number
}

const TAFSIR_ORDER = ['jalalayn', 'ibnkathir'] as const

export function TafsirSection({ tafsirs, surah, ayah }: Props) {
  return (
    <div>
      {TAFSIR_ORDER.map(key => (
        <TafsirBlock key={key} tafsirKey={key} text={tafsirs[key] ?? ''} surah={surah} ayah={ayah} />
      ))}
    </div>
  )
}
