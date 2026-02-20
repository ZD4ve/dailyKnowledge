// Mirrors the backend `dataArticle` model from helper.py
export interface Article {
  id: number
  site_name: string
  url: string
  title: string
  text: string
  authors: string | null
  publish_date: string   // ISO datetime string from FastAPI
  score: number          // -1 = not yet scored
  summary: string | null
  created_at: string
}
