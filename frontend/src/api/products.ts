import client from './client'

export interface ProductData {
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
}

export const searchProducts = (params: SearchParams) =>
  client.post<ProductData[]>('/search/', params).then((r) => r.data)

export const getFavourites = () =>
  client.get<ProductData[]>('/favourites/').then((r) => r.data)

export const addFavourite = (product: ProductData) =>
  client.post('/favourites/', product)

export const removeFavourite = (id: number) =>
  client.delete(`/favourites/${id}/`)
