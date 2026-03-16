import { useState } from 'react'
import { ProductData, addFavourite } from '../api/products'
import { getToken } from '../api/auth'

const MP_LABELS: Record<string, { label: string; color: string }> = {
  wb:   { label: 'WB',   color: 'bg-purple-600' },
  ozon: { label: 'Ozon', color: 'bg-blue-500'   },
}

interface Props {
  product: ProductData
  isSaved?: boolean
  onRemove?: () => void
  onSaved?: (product: ProductData) => void
}

export default function ProductCard({ product, isSaved = false, onRemove, onSaved }: Props) {
  const [saved, setSaved] = useState(isSaved)
  const [loading, setLoading] = useState(false)
  const mp = MP_LABELS[product.marketplace] ?? { label: product.marketplace, color: 'bg-gray-500' }

  if (isSaved && !saved) setSaved(true)

  async function handleSave() {
    if (!getToken()) { alert('Войдите, чтобы добавить в избранное'); return }
    setLoading(true)
    try {
      await addFavourite(product)
      setSaved(true)
      onSaved?.(product)
    } catch { alert('Ошибка при сохранении') }
    finally { setLoading(false) }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition flex flex-col overflow-hidden">
      {product.image_url && (
        <img src={product.image_url} alt={product.title}
          className="w-full h-44 object-contain bg-gray-50 p-2"
          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
      )}
      <div className="p-3 flex flex-col gap-1 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-white text-xs font-semibold px-2 py-0.5 rounded ${mp.color}`}>{mp.label}</span>
          {product.in_stock
            ? <span className="text-green-600 text-xs">В наличии</span>
            : <span className="text-red-500 text-xs">Нет в наличии</span>}
        </div>
        <p className="text-sm font-medium leading-tight line-clamp-2">{product.title}</p>
        {product.brand && <p className="text-xs text-gray-400">{product.brand}</p>}
        <div className="flex items-end gap-2 mt-1">
          {product.price != null && (
            <span className="text-lg font-bold">{product.price.toLocaleString('ru-RU')} ₽</span>
          )}
          {product.original_price != null && product.original_price !== product.price && (
            <span className="text-xs text-gray-400 line-through">{product.original_price.toLocaleString('ru-RU')} ₽</span>
          )}
          {product.discount_percent != null && (
            <span className="text-xs text-red-500 font-medium">-{product.discount_percent}%</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
          {product.rating != null && <span>⭐ {product.rating} ({product.reviews_count})</span>}
          {product.delivery_days != null && <span>🚚 {product.delivery_days} дн.</span>}
        </div>
        <div className="flex gap-2 mt-auto pt-2">
          <a href={product.url} target="_blank" rel="noopener noreferrer"
            className="flex-1 text-center text-sm border border-indigo-600 text-indigo-600 rounded-lg py-1 hover:bg-indigo-50 transition">
            Открыть
          </a>
          {onRemove
            ? <button onClick={onRemove}
                className="flex-1 text-sm bg-red-50 text-red-600 border border-red-200 rounded-lg py-1 hover:bg-red-100 transition">
                Удалить
              </button>
            : <button onClick={handleSave} disabled={saved || loading}
                className="flex-1 text-sm bg-indigo-600 text-white rounded-lg py-1 hover:bg-indigo-700 disabled:opacity-50 transition">
                {saved ? '✓ В избранном' : loading ? '...' : 'В избранное'}
              </button>
          }
        </div>
      </div>
    </div>
  )
}