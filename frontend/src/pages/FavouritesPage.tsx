import { useEffect, useState } from 'react'
import { getFavourites, removeFavourite, ProductData } from '../api/products'
import ProductCard from '../components/ProductCard'

interface SavedProduct extends ProductData { id: number }

export default function FavouritesPage() {
  const [items, setItems] = useState<SavedProduct[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getFavourites()
      .then((data) => setItems(data as SavedProduct[]))
      .catch(() => setError('Не удалось загрузить избранное'))
      .finally(() => setLoading(false))
  }, [])

  async function handleRemove(id: number) {
    await removeFavourite(id)
    setItems(prev => prev.filter(p => p.id !== id))
  }

  if (loading) return <p className="text-center text-gray-400 py-10">Загрузка...</p>
  if (error)   return <p className="text-center text-red-500 py-10">{error}</p>
  if (!items.length) return <p className="text-center text-gray-400 py-10">Избранное пусто</p>

  return (
    <div>
      <h1 className="text-xl font-bold mb-6">Избранное ({items.length})</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {items.map((p) => (
          <ProductCard key={p.id} product={p} isSaved onRemove={() => handleRemove(p.id)} />
        ))}
      </div>
    </div>
  )
}
