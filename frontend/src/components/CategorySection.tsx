import type { Article } from '../types'
import ArticleCard from './ArticleCard'

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
      return sb - sa
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
