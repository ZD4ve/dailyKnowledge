import type { Article } from '../types'
import ArticleCard from './ArticleCard'

// Deterministic hash of an integer — used as a stable tiebreaker within same-score articles.
// Same ID always produces the same value, so order never changes on reload.
function hashId(id: number): number {
  let h = id ^ (id >>> 16)
  h = Math.imul(h, 0x45d9f3b)
  return h ^ (h >>> 16)
}

interface Props {
  category: string
  articles: Article[]
  sinceDate: Date
  untilDate?: Date
}

export default function CategorySection({ articles, sinceDate, untilDate }: Props) {
  const filtered = articles
    .filter((a) => {
      const d = new Date(a.publish_date)
      return d >= sinceDate && (untilDate === undefined || d < untilDate)
    })
    .sort((a, b) => {
      // Treat unscored (-1) as lowest priority
      const sa = a.score === -1 ? -Infinity : a.score
      const sb = b.score === -1 ? -Infinity : b.score
      if (sb !== sa) return sb - sa
      // Same score: stable pseudo-random order based on article ID
      return hashId(a.id) - hashId(b.id)
    })

  if (filtered.length === 0) {
    return (
      <p className="text-center text-gray-400 dark:text-gray-500 py-20 text-sm">
        No articles in this time range yet.
      </p>
    )
  }

  return (
    // Single column on mobile, 2-column grid on md+ screens
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {filtered.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  )
}
