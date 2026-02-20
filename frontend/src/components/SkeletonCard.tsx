// Shimmer placeholder that mirrors the ArticleCard layout
export default function SkeletonCard() {
  return (
    <div className="relative flex flex-col bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 min-h-[120px] overflow-hidden">
      {/* Shimmer sweep */}
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/60 dark:via-white/5 to-transparent" />

      {/* Score badge placeholder */}
      <div className="absolute top-3 right-3 w-5 h-4 rounded-md bg-gray-200 dark:bg-gray-700" />

      {/* Source row */}
      <div className="flex items-center gap-2 mb-3 pr-9">
        <div className="w-3.5 h-3.5 rounded-sm bg-gray-200 dark:bg-gray-700 flex-shrink-0" />
        <div className="h-2.5 w-16 rounded-full bg-gray-200 dark:bg-gray-700" />
        <div className="h-2.5 w-8 rounded-full bg-gray-200 dark:bg-gray-700" />
      </div>

      {/* Title */}
      <div className="space-y-2 mb-3">
        <div className="h-3 w-full rounded-full bg-gray-200 dark:bg-gray-700" />
        <div className="h-3 w-4/5 rounded-full bg-gray-200 dark:bg-gray-700" />
      </div>

      {/* Description */}
      <div className="space-y-1.5 mt-auto">
        <div className="h-2.5 w-full rounded-full bg-gray-100 dark:bg-gray-700/70" />
        <div className="h-2.5 w-full rounded-full bg-gray-100 dark:bg-gray-700/70" />
        <div className="h-2.5 w-3/5 rounded-full bg-gray-100 dark:bg-gray-700/70" />
      </div>
    </div>
  )
}

/** Full-page skeleton grid matching the CategorySection layout */
export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}
