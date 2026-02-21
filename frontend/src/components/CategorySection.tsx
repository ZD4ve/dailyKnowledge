import { useRef, useEffect } from 'react'
import type { Article } from '../types'
import ArticleCard from './ArticleCard'
import { SkeletonGrid } from './SkeletonCard'

interface Props {
  category: string
  articles: Article[]
  hasMore: boolean
  loadingMore: boolean
  onLoadMore: () => void
}

export default function CategorySection({ articles, hasMore, loadingMore, onLoadMore }: Props) {
  const sentinelRef = useRef<HTMLDivElement>(null)

  // Infinite scroll: fire onLoadMore when sentinel enters viewport
  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          onLoadMore()
        }
      },
      { rootMargin: '400px' },
    )

    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [onLoadMore])

  return (
    <div>
      {/* Single column on mobile, 2-column grid on md+ screens */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {articles.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </div>

      {/* Loading indicator for next page */}
      {loadingMore && hasMore && (
        <div className="mt-3">
          <SkeletonGrid count={2} />
        </div>
      )}

      {/* Invisible sentinel to trigger loading next page */}
      {hasMore && <div ref={sentinelRef} className="h-1" />}
    </div>
  )
}
