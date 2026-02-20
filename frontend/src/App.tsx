import { useState, useEffect, useRef } from 'react'
import { getCategories, getCategoryArticles } from './api'
import type { Article } from './types'
import CategorySection from './components/CategorySection'
import { SkeletonGrid } from './components/SkeletonCard'

type TimeRange = 'today' | '3days' | 'week'

function getSinceDate(range: TimeRange): Date {
  const d = new Date()
  if (range === 'today') d.setHours(0, 0, 0, 0)
  else if (range === '3days') { d.setDate(d.getDate() - 2); d.setHours(0, 0, 0, 0) }
  else { d.setDate(d.getDate() - 6); d.setHours(0, 0, 0, 0) }
  return d
}

const TIME_RANGE_LABELS: Record<TimeRange, string> = {
  today: 'Today',
  '3days': '3 Days',
  week: 'Week',
}

function App() {
  const [categories, setCategories] = useState<string[]>([])
  const [articlesByCategory, setArticlesByCategory] = useState<Record<string, Article[]>>({})
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<TimeRange>('today')
  const [slideDir, setSlideDir] = useState<'left' | 'right'>('left')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const touchStartX = useRef<number | null>(null)

  function handleTouchStart(e: React.TouchEvent) {
    touchStartX.current = e.touches[0].clientX
  }

  function handleTouchEnd(e: React.TouchEvent) {
    if (touchStartX.current === null || categories.length < 2) return
    const delta = e.changedTouches[0].clientX - touchStartX.current
    touchStartX.current = null
    if (Math.abs(delta) < 50) return   // ignore small movements
    const idx = categories.indexOf(activeCategory ?? '')
    if (delta < 0) {
      // swipe left → next category slides in from the right
      setSlideDir('left')
      setActiveCategory(categories[(idx + 1) % categories.length])
    } else {
      // swipe right → previous category slides in from the left
      setSlideDir('right')
      setActiveCategory(categories[(idx - 1 + categories.length) % categories.length])
    }
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    async function load() {
      try {
        const cats = await getCategories()
        setCategories(cats)
        setActiveCategory(cats[0] ?? null)

        const entries = await Promise.all(
          cats.map(async (cat) => {
            const articles = await getCategoryArticles(cat)
            return [cat, articles] as const
          })
        )
        setArticlesByCategory(Object.fromEntries(entries))
      } catch {
        setError('Could not connect to the API. Is the backend running?')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const dateStr = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="max-w-3xl mx-auto px-4 pt-4 pb-2 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">dailyKnowledge</h1>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{dateStr}</p>
          </div>

          {/* Time range filter dropdown */}
          <div className="relative mt-1" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((v) => !v)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              aria-label="Filter by time range"
            >
              {/* Filter icon */}
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
              </svg>
              {TIME_RANGE_LABELS[timeRange]}
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg overflow-hidden z-20">
                {(Object.keys(TIME_RANGE_LABELS) as TimeRange[]).map((range) => (
                  <button
                    key={range}
                    onClick={() => { setTimeRange(range); setDropdownOpen(false) }}
                    className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                      timeRange === range
                        ? 'bg-violet-50 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 font-medium'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    {TIME_RANGE_LABELS[range]}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Category tab skeletons while loading */}
        {loading && (
          <div className="max-w-3xl mx-auto px-4 pb-3 flex items-center gap-2">
            {[80, 64, 72].map((w) => (
              <div key={w} className="shrink-0 h-7 rounded-full bg-gray-200 dark:bg-gray-700 animate-pulse" style={{ width: w }} />
            ))}
          </div>
        )}

        {/* Category tabs */}
        {!loading && categories.length > 0 && (
          <div className="max-w-3xl mx-auto px-4 pb-3 flex items-center gap-2 overflow-x-auto">
            {categories.map((cat, i) => (
              <button
                key={cat}
                onClick={() => {
                  const curIdx = categories.indexOf(activeCategory ?? '')
                  setSlideDir(i > curIdx ? 'left' : 'right')
                  setActiveCategory(cat)
                }}
                className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  activeCategory === cat
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </header>

      <main
        className="max-w-3xl mx-auto px-4 py-4 min-h-[calc(100dvh-8rem)] overflow-x-hidden"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {loading && <SkeletonGrid />}

        {error && (
          <div className="mt-8 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm text-center">
            {error}
          </div>
        )}

        {!loading && !error && activeCategory && articlesByCategory[activeCategory] && (
          <div
            key={activeCategory}
            className={slideDir === 'left' ? 'animate-slide-in-right' : 'animate-slide-in-left'}
          >
            <CategorySection
              category={activeCategory}
              articles={articlesByCategory[activeCategory]}
              sinceDate={getSinceDate(timeRange)}
            />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
