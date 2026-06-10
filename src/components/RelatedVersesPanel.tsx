import { useState, useEffect } from 'react'
import { getSimilarAyahs, getTopicsAndThemes } from '../db/index.ts'
import type { SimilarAyah, TopicsAndThemes } from '../db/index.ts'
import { TopicsThemesRow } from './TopicsThemesRow.tsx'
import { SimilarAyahGroup } from './SimilarAyahGroup.tsx'
import styles from './RelatedVersesPanel.module.css'

const TYPE_LABELS: Record<string, string> = {
  morphological_match: 'Morphological Match',
  mutashabihat: 'Similar Phrasing (Mutashabihat)',
}

function typeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

interface Props {
  surah: number
  ayah: number
  onNavigate: (surah: number, ayah: number) => void
}

export function RelatedVersesPanel({ surah, ayah, onNavigate }: Props) {
  const [similar, setSimilar] = useState<SimilarAyah[] | null>(null)
  const [topics, setTopics] = useState<TopicsAndThemes | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setSimilar(null)
    setTopics(null)
    Promise.all([
      getSimilarAyahs(surah, ayah),
      getTopicsAndThemes(surah, ayah),
    ]).then(([sim, top]) => {
      setSimilar(sim)
      setTopics(top)
      setLoading(false)
    }).catch(() => {
      setSimilar([])
      setTopics({ topics: [], themes: [] })
      setLoading(false)
    })
  }, [surah, ayah])

  if (loading) {
    return <div className={styles.loading}>Loading related verses…</div>
  }

  const hasTopics = (topics?.topics.length ?? 0) > 0 || (topics?.themes.length ?? 0) > 0
  const hasSimilar = (similar?.length ?? 0) > 0

  if (!hasTopics && !hasSimilar) return null

  // Group similar ayahs: mutashabihat vs. everything else
  const mutashabihat = (similar ?? []).filter(s => s.type === 'mutashabihat')
  const others = (similar ?? []).filter(s => s.type !== 'mutashabihat')

  // Group non-mutashabihat by type
  const groupedOthers = new Map<string, SimilarAyah[]>()
  for (const item of others) {
    const arr = groupedOthers.get(item.type) ?? []
    arr.push(item)
    groupedOthers.set(item.type, arr)
  }

  return (
    <section className={styles.section}>
      <h3 className={styles.heading}>Related Verses</h3>
      {hasTopics && topics && (
        <TopicsThemesRow topics={topics.topics} themes={topics.themes} />
      )}
      {hasSimilar && (
        <div className={styles.groups}>
          {Array.from(groupedOthers.entries()).map(([type, items]) => (
            <SimilarAyahGroup
              key={type}
              label={typeLabel(type)}
              items={items}
              onNavigate={onNavigate}
              startOpen={true}
            />
          ))}
          {mutashabihat.length > 0 && (
            <SimilarAyahGroup
              key="mutashabihat"
              label={typeLabel('mutashabihat')}
              items={mutashabihat}
              onNavigate={onNavigate}
              startOpen={false}
              displayLimit={50}
            />
          )}
        </div>
      )}
    </section>
  )
}
