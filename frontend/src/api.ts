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

/**
 * Returns all articles for a category, sorted by publish_date descending.
 * The frontend further filters and re-sorts by score.
 *
 * Backend endpoint needed:
 *   GET /categories/{category}/articles
 *   → list[dataArticle]  sorted by publish_date desc
 *
 * This endpoint already exists in the current backend.
 */
export async function getCategoryArticles(category: string): Promise<Article[]> {
  const res = await api.get<Article[]>(`/api/categories/${encodeURIComponent(category)}/articles`)
  return res.data
}
