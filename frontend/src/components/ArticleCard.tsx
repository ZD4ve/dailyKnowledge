import type { Article } from '../types'

interface Props {
  article: Article
}

// Returns styling for the relevance score badge
function scoreBadge(score: number): { label: string; cls: string } {
  if (score === -1) {
    return { label: '?', cls: 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-400' }
  }
  if (score >= 8) {
    return { label: String(score), cls: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300' }
  }
  if (score >= 5) {
    return { label: String(score), cls: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300' }
  }
  return { label: String(score), cls: 'bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400' }
}

function getDomain(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return ''
  }
}

function formatTime(iso: string): string | null {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return null
  }
  if (date.getHours() === 0 && date.getMinutes() === 0) {
    return null
  }
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
}

export default function ArticleCard({ article }: Props) {
  const { label, cls } = scoreBadge(article.score)
  const domain = getDomain(article.url)
  const timeLabel = formatTime(article.publish_date)
  const faviconUrl = domain
    ? `https://www.google.com/s2/favicons?domain=${domain}&sz=32`
    : null

  // Use LLM summary if available, otherwise fall back to a text snippet
  const description = article.summary ?? article.text?.slice(0, 220)

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group relative flex flex-col bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 hover:shadow-md hover:border-blue-200 dark:hover:border-blue-600 transition-all duration-200 min-h-[120px]"
    >
      {/* Score badge — top-right corner */}
      <span
        className={`absolute top-3 right-3 text-xs font-bold px-1.5 py-0.5 rounded-md leading-none ${cls}`}
        title="Relevance score"
      >
        {label}
      </span>

      {/* Source row: favicon + site name + time */}
      <div className="flex items-center gap-1.5 mb-2 pr-9">
        {faviconUrl && (
          <img src={faviconUrl} alt="" width={14} height={14} className="rounded-sm flex-shrink-0" />
        )}
        <span className="text-xs text-gray-400 dark:text-gray-500 font-medium truncate">
          {article.site_name}
        </span>
        {timeLabel && (
          <>
            <span className="text-xs text-gray-300 dark:text-gray-600">·</span>
            <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">
              {timeLabel}
            </span>
          </>
        )}
      </div>

      {/* Title */}
      <h2 className="text-sm font-semibold leading-snug text-gray-900 dark:text-gray-100 line-clamp-3 mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
        {article.title}
      </h2>

      {/* Description — full content, card grows to fit */}
      {description && (
        <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed mt-2 min-h-[3.75rem]">
          {description}
        </p>
      )}
    </a>
  )
}
