import { useState } from 'react'
import { ProductData, addFavourite } from '../api/products'
import { getToken } from '../api/auth'

const MP_LABELS: Record<string, { label: string; color: string }> = {
  wb: { label: 'Wildberries', color: 'bg-purple-600' },
  ozon: { label: 'Ozon', color: 'bg-blue-500' },
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

  async function handleSave() {
    if (!getToken()) {
      alert('Войдите, чтобы добавить в избранное')
      return
    }

    setLoading(true)
    try {
      await addFavourite(product)
      setSaved(true)
      onSaved?.(product)
    } catch {
      alert('Ошибка при сохранении')
    } finally {
      setLoading(false)
    }
  }

  return (
    <article className="h-full bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition flex flex-col overflow-hidden">
      <div className="h-44 bg-gray-50 flex items-center justify-center p-3 shrink-0">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.title}
            className="max-h-full max-w-full object-contain"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = 'none'
            }}
          />
        ) : (
          <div className="text-sm text-gray-400">Нет изображения</div>
        )}
      </div>

      <div className="p-3 flex flex-col flex-1 min-h-0">
        <div className="flex items-start gap-2 mb-2 min-h-[1.75rem]">
          <span className={`text-white text-xs font-semibold px-2 py-0.5 rounded ${mp.color}`}>{mp.label}</span>
          {product.in_stock ? (
            <span className="text-green-600 text-xs leading-5">В наличии</span>
          ) : (
            <span className="text-red-500 text-xs leading-5">Нет в наличии</span>
          )}
        </div>

        <div className="min-h-[3rem] overflow-hidden">
          <p className="text-sm font-medium leading-snug line-clamp-2 break-words">
            {product.title}
          </p>
        </div>

        <div className="mt-1 min-h-[1rem]">
          {product.brand && <p className="text-xs text-gray-400 line-clamp-1">{product.brand}</p>}
        </div>

        <div className="mt-2 flex items-end gap-2 min-h-[2rem]">
          {product.price != null && (
            <span className="text-lg font-bold leading-none">
              {product.price.toLocaleString('ru-RU')} ₽
            </span>
          )}
          {product.original_price != null && product.original_price !== product.price && (
            <span className="text-xs text-gray-400 line-through">
              {product.original_price.toLocaleString('ru-RU')} ₽
            </span>
          )}
          {product.discount_percent != null && (
            <span className="text-xs text-red-500 font-medium">-{product.discount_percent}%</span>
          )}
        </div>

        <div className="flex items-center gap-3 text-xs text-gray-500 mt-1 min-h-[1rem]">
          {product.rating != null && <span>⭐ {product.rating} ({product.reviews_count})</span>}
          {product.delivery_days != null && <span>🚚 {product.delivery_days} дн.</span>}
        </div>

        <div className="flex gap-2 mt-auto pt-2">
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center text-sm border border-indigo-600 text-indigo-600 rounded-lg py-1 hover:bg-indigo-50 transition"
          >
            Открыть
          </a>

          {onRemove ? (
            <button
              onClick={onRemove}
              className="flex-1 text-sm bg-red-50 text-red-600 border border-red-200 rounded-lg py-1 hover:bg-red-100 transition"
            >
              Удалить
            </button>
          ) : (
            <button
              onClick={handleSave}
              disabled={saved || loading}
              className="flex-1 text-sm bg-indigo-600 text-white rounded-lg py-1 hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              {saved ? '✓ В избранном' : loading ? '...' : 'В избранное'}
            </button>
          )}
        </div>
      </div>
    </article>
  )
}
