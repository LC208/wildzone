import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { searchProducts, ProductData, SearchParams } from '../api/products'
import ProductCard from '../components/ProductCard'

const SORT_OPTIONS = [
  { value: '', label: 'По умолчанию' },
  { value: 'price_asc', label: 'Цена ↑' },
  { value: 'price_desc', label: 'Цена ↓' },
  { value: 'rating_desc', label: 'Рейтинг ↓' },
  { value: 'delivery_days_asc', label: 'Доставка ↑' },
]

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const [results, setResults] = useState<ProductData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [minRating, setMinRating] = useState('')
  const [maxDelivery, setMaxDelivery] = useState('')
  const [inStock, setInStock] = useState(false)
  const [marketplaces, setMarketplaces] = useState<string[]>([])
  const [sort, setSort] = useState('')

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) return
    setLoading(true); setError('')
    try {
      const [sort_by, sort_order] = sort
        ? (() => { const parts = sort.split('_'); const order = parts.pop()!; return [parts.join('_'), order] })()
        : ['', '']
      const params: SearchParams = {
        query: q, max_results: 30,
        ...(marketplaces.length ? { marketplaces } : {}),
        ...(minPrice ? { min_price: Number(minPrice) } : {}),
        ...(maxPrice ? { max_price: Number(maxPrice) } : {}),
        ...(minRating ? { min_rating: Number(minRating) } : {}),
        ...(maxDelivery ? { max_delivery: Number(maxDelivery) } : {}),
        ...(inStock ? { in_stock: true } : {}),
        ...(sort_by ? { sort_by, sort_order } : {}),
      }
      setResults(await searchProducts(params))
    } catch {
      setError('Ошибка при поиске. Проверьте, что backend запущен.')
    } finally { setLoading(false) }
  }, [sort, marketplaces, minPrice, maxPrice, minRating, maxDelivery, inStock])

  useEffect(() => {
    const q = searchParams.get('q') ?? ''
    setQuery(q)
    if (q) doSearch(q)
  }, [searchParams])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (query.trim()) { setSearchParams({ q: query.trim() }); doSearch(query.trim()) }
  }

  function toggleMp(mp: string) {
    setMarketplaces(prev => prev.includes(mp) ? prev.filter(x => x !== mp) : [...prev, mp])
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
        <input type="text" value={query} onChange={e => setQuery(e.target.value)} placeholder="Поиск..."
          className="flex-1 border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
        <button type="submit" className="bg-indigo-600 text-white px-5 py-2 rounded-xl text-sm hover:bg-indigo-700 transition">Найти</button>
      </form>

      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 flex flex-wrap gap-3 items-end">
        <div className="flex gap-2">
          {['wb', 'ozon'].map(mp => (
            <button key={mp} onClick={() => toggleMp(mp)}
              className={`px-3 py-1 rounded-lg text-sm border transition ${marketplaces.includes(mp) ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-600 border-gray-300 hover:border-indigo-400'}`}>
              {mp === 'wb' ? 'Wildberries' : 'Ozon'}
            </button>
          ))}
        </div>
        <div className="flex gap-2 items-center">
          <input type="number" placeholder="Цена от" value={minPrice} onChange={e => setMinPrice(e.target.value)}
            className="w-24 border border-gray-300 rounded-lg px-2 py-1 text-sm" />
          <span className="text-gray-400">—</span>
          <input type="number" placeholder="до" value={maxPrice} onChange={e => setMaxPrice(e.target.value)}
            className="w-24 border border-gray-300 rounded-lg px-2 py-1 text-sm" />
        </div>
        <input type="number" step="0.1" min="0" max="5" placeholder="Рейтинг от" value={minRating}
          onChange={e => setMinRating(e.target.value)} className="w-28 border border-gray-300 rounded-lg px-2 py-1 text-sm" />
        <input type="number" min="0" placeholder="Доставка макс (дн.)" value={maxDelivery}
          onChange={e => setMaxDelivery(e.target.value)} className="w-40 border border-gray-300 rounded-lg px-2 py-1 text-sm" />
        <label className="flex items-center gap-1 text-sm cursor-pointer select-none">
          <input type="checkbox" checked={inStock} onChange={e => setInStock(e.target.checked)} className="accent-indigo-600" />
          В наличии
        </label>
        <select value={sort} onChange={e => setSort(e.target.value)} className="border border-gray-300 rounded-lg px-2 py-1 text-sm">
          {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <button onClick={() => doSearch(query)} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-lg text-sm hover:bg-gray-200 transition">Применить</button>
      </div>

      {loading && <p className="text-center text-gray-400 py-10">Поиск...</p>}
      {error && <p className="text-center text-red-500 py-10">{error}</p>}
      {!loading && !error && results.length === 0 && searchParams.get('q') && (
        <p className="text-center text-gray-400 py-10">Ничего не найдено</p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {results.map((p) => (
          <ProductCard key={`${p.marketplace}-${p.external_id}`} product={p} />
        ))}
      </div>
    </div>
  )
}
