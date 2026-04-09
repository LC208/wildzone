import client from './client'

export interface ProductData {
  id?: number
  marketplace: string
  external_id: string
  article: string
  title: string
  brand: string
  price: number | null
  original_price: number | null
  discount_percent: number | null
  rating: number | null
  reviews_count: number
  in_stock: boolean
  delivery_days: number | null
  url: string
  image_url: string
  category: string
  attributes: Record<string, unknown>
}

export interface SearchParams {
  query: string
  marketplaces?: string[]
  max_results?: number
  sort_by?: string
  sort_order?: string
  min_price?: number
  max_price?: number
  min_rating?: number
  max_delivery?: number
  in_stock?: boolean
  page?: number
  page_size?: number
}

export interface SearchResponse {
  results: ProductData[]
  count?: number
  page?: number
  page_size?: number
  total_pages?: number
}

const HISTORY_KEY = 'wildzone_search_history'
const LIMIT = 10

export function getSearchHistory(): string[] {
  try {
    const raw = sessionStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((x) => typeof x === 'string') : []
  } catch {
    return []
  }
}

export function saveSearchHistory(query: string) {
  const q = query.trim()
  if (!q) return
  const next = [q, ...getSearchHistory().filter((item) => item.toLowerCase() !== q.toLowerCase())].slice(0, LIMIT)
  sessionStorage.setItem(HISTORY_KEY, JSON.stringify(next))
}

export function clearSearchHistory() {
  sessionStorage.removeItem(HISTORY_KEY)
}

export const searchProducts = (params: SearchParams) =>
  client.post<SearchResponse | ProductData[]>('/search/', params).then((r) => r.data)

export const getFavourites = () =>
  client.get<{ results: ProductData[] }>('/favourites/').then((r) => r.data.results)

export const addFavourite = (product: ProductData) =>
  client.post('/favourites/', product)

export const removeFavourite = (id: number) =>
  client.delete(`/favourites/${id}/`)
