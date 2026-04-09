import { useMemo, useState } from 'react'
import { ProductData, addFavourite } from '../api/products'
import { getToken } from '../api/auth'

const MP_LABELS: Record<string, { label: string; color: string }> = {
  wildberries: { label: 'Wildberries', color: 'bg-purple-600' },
  ozon: { label: 'Ozon', color: 'bg-blue-500' },
}

interface Props {
  product: ProductData
  isSaved?: boolean
  onRemove?: () => void
  onSaved?: (product: ProductData) => void
  onCompare?: (product: ProductData) => void
  isCompared?: boolean
}

export default function ProductCard({ product, isSaved = false, onRemove, onSaved, onCompare, isCompared = false }: Props) {
  const [saved, setSaved] = useState(isSaved)
  const [loading, setLoading] = useState(false)
  const mp = useMemo(() => MP_LABELS[product.marketplace] ?? { label: product.marketplace, color: 'bg-gray-500' }, [product.marketplace])

  const price = product.price != null ? product.price.toLocaleString('ru-RU') : '—'
  const oldPrice = product.original_price != null ? product.original_price.toLocaleString('ru-RU') : ''
  const rating = product.rating != null ? product.rating.toFixed(1) : '—'
  const reviews = product.reviews_count?.toLocaleString('ru-RU') ?? '0'

  async function handleSave() {
    if (!getToken()) return
    setLoading(true)
    try {
      await addFavourite(product)
      setSaved(true)
      onSaved?.(product)
    } finally {
      setLoading(false)
    }
  }

  return (
    <article className="h-full rounded-xl border border-gray-200 bg-white shadow-sm flex flex-col overflow-hidden">
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
          <span className={`text-xs ${product.in_stock ? 'text-green-600' : 'text-red-500'}`}>
            {product.in_stock ? 'В наличии' : 'Нет в наличии'}
          </span>
        </div>

        <p className="text-sm font-medium leading-tight line-clamp-2 min-h-[2.5rem]">{product.title}</p>

        <div className="mt-1 min-h-[1rem]">
          {product.brand && <p className="text-xs text-gray-400 line-clamp-1">{product.brand}</p>}
        </div>

        <div className="mt-2 flex items-end gap-2 min-h-[2rem]">
          <span className="text-lg font-bold leading-none">{price} ₽</span>
          {oldPrice && product.original_price !== product.price && (
            <span className="text-xs text-gray-400 line-through">{oldPrice} ₽</span>
          )}
          {product.discount_percent != null && (
            <span className="text-xs text-red-500 font-medium">-{product.discount_percent}%</span>
          )}
        </div>

        <div className="mt-1 min-h-[1rem] text-xs text-gray-500">
          <span>⭐ {rating} ({reviews})</span>
          {product.delivery_days != null && <span className="ml-3">🚚 {product.delivery_days} дн.</span>}
        </div>

        <div className="mt-3 flex gap-2 pt-2">
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center text-sm border border-indigo-600 text-indigo-600 rounded-lg py-2 hover:bg-indigo-50 transition"
          >
            Открыть
          </a>

          {onCompare ? (
            <button
              onClick={() => onCompare(product)}
              className={`flex-1 text-sm rounded-lg py-2 border transition ${isCompared ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'}`}
            >
              {isCompared ? 'В сравнении' : 'Сравнить'}
            </button>
          ) : null}

          {onRemove ? (
            <button
              onClick={onRemove}
              className="flex-1 text-sm bg-red-50 text-red-600 border border-red-200 rounded-lg py-2 hover:bg-red-100 transition"
            >
              Удалить
            </button>
          ) : (
            <button
              onClick={handleSave}
              disabled={saved || loading || !getToken()}
              className="flex-1 text-sm bg-indigo-600 text-white rounded-lg py-2 hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              {saved ? '✓ В избранном' : loading ? '...' : 'В избранное'}
            </button>
          )}
        </div>
      </div>
    </article>
  )
}
