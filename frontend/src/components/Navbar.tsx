import { Link, useNavigate } from 'react-router-dom'
import { clearTokens, getToken } from '../api/auth'

export default function Navbar() {
  const navigate = useNavigate()
  const isAuth = !!getToken()

  function logout() {
    clearTokens()
    navigate('/login')
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-indigo-600 tracking-tight">Wildzone</Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/" className="hover:text-indigo-600 transition">Поиск</Link>
          {isAuth && <Link to="/favourites" className="hover:text-indigo-600 transition">Избранное</Link>}
          {isAuth
            ? <button onClick={logout} className="text-red-500 hover:text-red-700 transition">Выйти</button>
            : <>
                <Link to="/login" className="hover:text-indigo-600 transition">Войти</Link>
                <Link to="/register" className="bg-indigo-600 text-white px-3 py-1 rounded hover:bg-indigo-700 transition">Регистрация</Link>
              </>
          }
        </nav>
      </div>
    </header>
  )
}
