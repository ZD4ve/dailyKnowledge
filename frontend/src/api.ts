import axios from 'axios'
import type { Article } from './types'

// Point this at your FastAPI backend
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
})

/** Returns a list of category names */
export async function getCategories(): Promise<string[]> {
  const res = await api.get<string[]>('/api/categories')
  return res.data
}

export interface PaginatedResponse {
  articles: Article[]
  total: number
}

/**
 * Returns a page of articles for a category, sorted by score descending.
 * Supports server-side date filtering and pagination.
 *
 * Backend endpoint needed:
 *   GET /api/categories/{category}/articles?since=ISO&until=ISO&limit=N&offset=N
 *   → { articles: list[dataArticle], total: int }
 *   Articles sorted by score DESC (unscored at end), then by id hash for stable order.
 */
export async function getCategoryArticles(
  category: string,
  params?: { since?: string; until?: string; limit?: number; offset?: number },
): Promise<PaginatedResponse> {
  const res = await api.get<PaginatedResponse>(
    `/api/categories/${encodeURIComponent(category)}/articles`,
    { params },
  )
  return res.data
}
