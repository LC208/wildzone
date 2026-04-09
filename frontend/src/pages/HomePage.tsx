import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSearchHistory } from '../api/products'

const POPULAR = ['кроссовки', 'наушники', 'рюкзак', 'смартфон', 'пауэрбанк', 'куртка']

export default function HomePage() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  const history = getSearchHistory()

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`)
  }

  function go(q: string) {
    navigate(`/search?q=${encodeURIComponent(q)}`)
  }

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="w-full max-w-3xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-indigo-600 mb-3">Wildzone</h1>
          <p className="text-gray-500 text-lg">Сравнивай товары с Wildberries и Ozon в одном месте</p>
        </div>

        <form onSubmit={handleSearch} className="w-full flex flex-col gap-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Поиск товаров..."
              autoFocus
              className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <button
              type="submit"
              className="bg-indigo-600 text-white px-6 py-3 rounded-xl text-sm font-medium hover:bg-indigo-700 transition"
            >
              Найти
            </button>
          </div>

          <div className="flex flex-wrap gap-2 justify-center">
            {POPULAR.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => go(item)}
                className="px-3 py-1.5 text-sm rounded-full border border-gray-200 bg-white hover:bg-gray-50 transition"
              >
                {item}
              </button>
            ))}
          </div>

          {history.length > 0 && (
            <div className="mt-4 bg-white border border-gray-200 rounded-xl p-4">
              <p className="text-sm font-medium mb-3 text-gray-700">История поиска</p>
              <div className="flex flex-wrap gap-2">
                {history.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => go(item)}
                    className="px-3 py-1.5 text-sm rounded-full bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
