import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function HomePage() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`)
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-indigo-600 mb-2">Wildzone</h1>
        <p className="text-gray-500 text-lg">Сравнивай товары с Wildberries и Ozon в одном месте</p>
      </div>
      <form onSubmit={handleSearch} className="w-full max-w-xl flex gap-2">
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="Поиск товаров..." autoFocus
          className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
        <button type="submit"
          className="bg-indigo-600 text-white px-6 py-3 rounded-xl text-sm font-medium hover:bg-indigo-700 transition">
          Найти
        </button>
      </form>
    </div>
  )
}
