import { useEffect, useMemo, useState } from 'react'
import { getFavourites, removeFavourite, ProductData } from '../api/products'
import ProductCard from '../components/ProductCard'

interface SavedProduct extends ProductData { id: number }

export default function FavouritesPage() {
  const [items, setItems] = useState<SavedProduct[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    getFavourites()
      .then((data) => setItems(data as SavedProduct[]))
      .catch(() => setError('Не удалось загрузить избранное'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter((p) =>
      [p.title, p.brand, p.category, p.marketplace, p.article]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q))
    )
  }, [items, query])

  async function handleRemove(id: number) {
    await removeFavourite(id)
    setItems((prev) => prev.filter((p) => p.id !== id))
  }

  if (loading) return <p className="text-center text-gray-400 py-10">Загрузка...</p>
  if (error) return <p className="text-center text-red-500 py-10">{error}</p>

  return (
    <div>
      <div className="flex flex-col gap-4 mb-6">
        <h1 className="text-xl font-bold">Избранное ({filtered.length})</h1>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Поиск по избранному..."
          className="w-full max-w-md border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      {!filtered.length ? (
        <p className="text-center text-gray-400 py-10">Избранное пусто</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filtered.map((p) => (
            <ProductCard key={p.id} product={p} isSaved onRemove={() => handleRemove(p.id)} />
          ))}
        </div>
      )}
    </div>
  )
}
