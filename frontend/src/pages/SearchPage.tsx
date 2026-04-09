import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  searchProducts,
  getFavourites,
  ProductData,
  SearchParams,
  SearchResponse,
  saveSearchHistory,
  getSearchHistory,
} from '../api/products'
import { getToken } from '../api/auth'
import ProductCard from '../components/ProductCard'

const SORT_OPTIONS = [
  { value: '', label: 'По умолчанию' },
  { value: 'price_asc', label: 'Цена ↑' },
  { value: 'price_desc', label: 'Цена ↓' },
  { value: 'rating_desc', label: 'Рейтинг ↓' },
  { value: 'delivery_days_asc', label: 'Доставка ↑' },
]

const POPULAR = ['кроссовки', 'наушники', 'рюкзак', 'смартфон', 'пауэрбанк', 'куртка']
const PER_MARKETPLACE = 4

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const [results, setResults] = useState<ProductData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [savedKeys, setSavedKeys] = useState<Set<string>>(new Set())

  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [minRating, setMinRating] = useState('')
  const [maxDelivery, setMaxDelivery] = useState('')
  const [inStock, setInStock] = useState(false)
  const [sort, setSort] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)

  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const [ozonItems, setOzonItems] = useState<ProductData[]>([])
  const [wbItems, setWbItems] = useState<ProductData[]>([])
  const [ozonBackendPage, setOzonBackendPage] = useState(1)
  const [wbBackendPage, setWbBackendPage] = useState(1)
  const [ozonHasMore, setOzonHasMore] = useState(true)
  const [wbHasMore, setWbHasMore] = useState(true)

  useEffect(() => {
    if (!getToken()) return
    getFavourites()
      .then((items) => {
        setSavedKeys(new Set(items.map((p) => `${p.marketplace}:${p.external_id}`)))
      })
      .catch(() => {})
  }, [])

  const suggestions = useMemo(() => {
    const history = getSearchHistory()
    const q = query.trim().toLowerCase()
    const source = [...history, ...POPULAR]
    return source
      .filter((item, idx) => source.findIndex((x) => x.toLowerCase() === item.toLowerCase()) === idx)
      .filter((item) => !q || item.toLowerCase().includes(q))
      .slice(0, 8)
  }, [query])

  function getBaseParams(q: string): SearchParams {
    const [sort_by, sort_order] = sort
      ? (() => {
          const parts = sort.split('_')
          const order = parts.pop()!
          return [parts.join('_'), order]
        })()
      : ['', '']

    return {
      query: q,
      ...(minPrice ? { min_price: Number(minPrice) } : {}),
      ...(maxPrice ? { max_price: Number(maxPrice) } : {}),
      ...(minRating ? { min_rating: Number(minRating) } : {}),
      ...(maxDelivery ? { max_delivery: Number(maxDelivery) } : {}),
      ...(inStock ? { in_stock: true } : {}),
      ...(sort_by ? { sort_by, sort_order } : {}),
    }
  }

  function parseItems(data: SearchResponse | ProductData[]) {
    return Array.isArray(data) ? data : data.results ?? []
  }

  function uniqueMerge(prev: ProductData[], next: ProductData[]) {
    const map = new Map<string, ProductData>()
    for (const item of [...prev, ...next]) {
      map.set(`${item.marketplace}:${item.external_id}`, item)
    }
    return Array.from(map.values())
  }

  function buildPage(ozon: ProductData[], wb: ProductData[], currentPage: number) {
    const start = (currentPage - 1) * PER_MARKETPLACE
    const ozonSlice = ozon.slice(start, start + PER_MARKETPLACE)
    const wbSlice = wb.slice(start, start + PER_MARKETPLACE)
    return [...ozonSlice, ...wbSlice]
  }

  async function fetchMarketplacePage(
    q: string,
    marketplace: 'ozon' | 'wb',
    backendPage: number
  ) {
    const params: SearchParams = {
      ...getBaseParams(q),
      marketplaces: [marketplace],
      page: backendPage,
    }

    const data = await searchProducts(params)
    const items = parseItems(data).filter((p) => p.marketplace === marketplace)

    if (marketplace === 'ozon') {
      setOzonItems((prev) => uniqueMerge(prev, items))
      setOzonHasMore(items.length > 0)
      setOzonBackendPage(backendPage)
    } else {
      setWbItems((prev) => uniqueMerge(prev, items))
      setWbHasMore(items.length > 0)
      setWbBackendPage(backendPage)
    }

    return items
  }

  async function ensurePageData(q: string, nextPage: number, currentOzon: ProductData[], currentWb: ProductData[]) {
    const needed = nextPage * PER_MARKETPLACE

    let ozonPool = currentOzon
    let wbPool = currentWb

    while (ozonPool.length < needed && ozonHasMore) {
      const next = await fetchMarketplacePage(q, 'ozon', ozonBackendPage + 1)
      if (!next.length) break
      ozonPool = uniqueMerge(ozonPool, next)
    }

    while (wbPool.length < needed && wbHasMore) {
      const next = await fetchMarketplacePage(q, 'wb', wbBackendPage + 1)
      if (!next.length) break
      wbPool = uniqueMerge(wbPool, next)
    }

    return { ozonPool, wbPool }
  }

  async function fetchInitialSearch(q: string) {
    if (!q.trim()) return

    setLoading(true)
    setError('')
    try {
      const params: SearchParams = {
        ...getBaseParams(q),
        page: 1,
      }

      const data = await searchProducts(params)
      const items = parseItems(data)

      const ozon = items.filter((p) => p.marketplace === 'ozon')
      const wb = items.filter((p) => p.marketplace === 'wb')

      setOzonItems(ozon)
      setWbItems(wb)
      setOzonBackendPage(1)
      setWbBackendPage(1)
      setOzonHasMore(ozon.length > 0)
      setWbHasMore(wb.length > 0)
      setPage(1)

      const firstPage = buildPage(ozon, wb, 1)
      setResults(firstPage)
      setTotalPages(Math.max(
        Math.ceil(ozon.length / PER_MARKETPLACE),
        Math.ceil(wb.length / PER_MARKETPLACE),
        1
      ))

      saveSearchHistory(q)
    } catch {
      setError('Ошибка при поиске. Проверьте, что backend запущен.')
    } finally {
      setLoading(false)
    }
  }

  async function goToPage(nextPage: number) {
    if (!query.trim()) return
    setLoading(true)
    setError('')

    try {
      const { ozonPool, wbPool } = await ensurePageData(query.trim(), nextPage, ozonItems, wbItems)
      const pageItems = buildPage(ozonPool, wbPool, nextPage)
      setResults(pageItems)
      setPage(nextPage)

      const pages = Math.max(
        Math.ceil(ozonPool.length / PER_MARKETPLACE),
        Math.ceil(wbPool.length / PER_MARKETPLACE),
        1
      )
      setTotalPages(pages)
    } catch {
      setError('Не удалось загрузить следующую страницу')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const q = searchParams.get('q') ?? ''
    setQuery(q)
    if (q) fetchInitialSearch(q)
  }, [searchParams])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    setSearchParams({ q })
    fetchInitialSearch(q)
  }

  function applyFilters() {
    if (query.trim()) fetchInitialSearch(query.trim())
  }

  function handleSaved(product: ProductData) {
    setSavedKeys((prev) => new Set(prev).add(`${product.marketplace}:${product.external_id}`))
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 mb-4 relative">
        <div className="relative flex-1">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                placeholder="Поиск..."
                className="w-full border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute left-0 right-0 top-full mt-2 z-20 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                  {suggestions.map((item) => (
                    <button
                      key={item}
                      type="button"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        setQuery(item)
                        setSearchParams({ q: item })
                        fetchInitialSearch(item)
                      }}
                      className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              type="submit"
              className="bg-indigo-600 text-white px-5 py-2 rounded-xl text-sm hover:bg-indigo-700 transition"
            >
              Найти
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {POPULAR.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setQuery(item)
                setSearchParams({ q: item })
                fetchInitialSearch(item)
              }}
              className="px-3 py-1.5 text-sm rounded-full border border-gray-200 bg-white hover:bg-gray-50 transition"
            >
              {item}
            </button>
          ))}
        </div>
      </form>

      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 flex flex-wrap gap-3 items-end">
        <div className="flex gap-2 items-center">
          <input
            type="number"
            placeholder="Цена от"
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
            className="w-24 border border-gray-300 rounded-lg px-2 py-1 text-sm"
          />
          <span className="text-gray-400">—</span>
          <input
            type="number"
            placeholder="до"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            className="w-24 border border-gray-300 rounded-lg px-2 py-1 text-sm"
          />
        </div>

        <input
          type="number"
          step="0.1"
          min="0"
          max="5"
          placeholder="Рейтинг от"
          value={minRating}
          onChange={(e) => setMinRating(e.target.value)}
          className="w-28 border border-gray-300 rounded-lg px-2 py-1 text-sm"
        />

        <input
          type="number"
          min="0"
          placeholder="Доставка макс (дн.)"
          value={maxDelivery}
          onChange={(e) => setMaxDelivery(e.target.value)}
          className="w-40 border border-gray-300 rounded-lg px-2 py-1 text-sm"
        />

        <label className="flex items-center gap-1 text-sm cursor-pointer select-none">
          <input
            type="checkbox"
            checked={inStock}
            onChange={(e) => setInStock(e.target.checked)}
            className="accent-indigo-600"
          />
          В наличии
        </label>

        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="border border-gray-300 rounded-lg px-2 py-1 text-sm"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <button
          type="button"
          onClick={applyFilters}
          className="bg-gray-100 text-gray-700 px-3 py-1 rounded-lg text-sm hover:bg-gray-200 transition"
        >
          Применить
        </button>
      </div>

      {loading && <p className="text-center text-gray-400 py-10">Поиск...</p>}
      {error && <p className="text-center text-red-500 py-10">{error}</p>}
      {!loading && !error && results.length === 0 && searchParams.get('q') && (
        <p className="text-center text-gray-400 py-10">Ничего не найдено</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-stretch">
        {results.map((p) => (
          <ProductCard
            key={`${p.marketplace}-${p.external_id}`}
            product={p}
            isSaved={savedKeys.has(`${p.marketplace}:${p.external_id}`)}
            onSaved={handleSaved}
          />
        ))}
      </div>

      {query.trim() && results.length > 0 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            type="button"
            disabled={page <= 1 || loading}
            onClick={() => goToPage(page - 1)}
            className="px-4 py-2 rounded-lg border border-gray-300 bg-white disabled:opacity-50"
          >
            Назад
          </button>
          <span className="text-sm text-gray-500">Страница {page} из {totalPages}</span>
          <button
            type="button"
            disabled={loading || (!ozonHasMore && !wbHasMore && page >= totalPages)}
            onClick={() => goToPage(page + 1)}
            className="px-4 py-2 rounded-lg border border-gray-300 bg-white disabled:opacity-50"
          >
            Далее
          </button>
        </div>
      )}
    </div>
  )
}
