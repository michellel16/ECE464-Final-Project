import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [q, setQ]           = useState('')
  const [menuOpen, setMenu] = useState(false)
  const menuRef = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenu(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  function handleSearch(e) {
    e.preventDefault()
    if (q.trim()) {
      navigate(`/search?q=${encodeURIComponent(q.trim())}`)
      setQ('')
    }
  }

  const navLink = (to, label) => (
    <Link
      to={to}
      className={`text-sm transition-colors ${
        location.pathname === to
          ? 'text-white font-medium'
          : 'text-gray-400 hover:text-white'
      }`}
    >
      {label}
    </Link>
  )

  return (
    <nav className="fixed top-0 inset-x-0 z-50 bg-gray-950/95 backdrop-blur border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 shrink-0 mr-2">
          <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
            T
          </div>
          <span className="hidden sm:block font-bold text-lg bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
            Tunelog
          </span>
        </Link>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex-1 max-w-lg">
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Search artists, albums, songs…"
            className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded-full px-4 py-2 focus:outline-none focus:border-violet-500 placeholder-gray-500 transition-colors"
          />
        </form>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-5">
          {navLink('/discover', 'Discover')}
          {user && navLink('/lists', 'My Lists')}
          {user && navLink('/stats', 'Stats')}
        </div>

        {/* Auth */}
        <div className="ml-auto shrink-0">
          {user ? (
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenu(!menuOpen)}
                className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 rounded-full px-3 py-1.5 transition-colors"
              >
                <Avatar username={user.username} avatarUrl={user.avatar_url} size={6} />
                <span className="text-sm text-gray-200 hidden sm:block">{user.username}</span>
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-2 w-52 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl py-1 overflow-hidden">
                  <Link
                    to={`/users/${user.username}`}
                    className="flex items-center gap-2 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-800 hover:text-white"
                    onClick={() => setMenu(false)}
                  >
                    <Avatar username={user.username} avatarUrl={user.avatar_url} size={6} />
                    Profile
                  </Link>
                  <Link
                    to="/lists"
                    className="block px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-800 hover:text-white"
                    onClick={() => setMenu(false)}
                  >
                    My Lists
                  </Link>
                  <Link
                    to="/stats"
                    className="block px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-800 hover:text-white"
                    onClick={() => setMenu(false)}
                  >
                    Stats
                  </Link>
                  <div className="border-t border-gray-800 mt-1 pt-1">
                    <button
                      onClick={() => { logout(); setMenu(false); navigate('/') }}
                      className="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-gray-800"
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link to="/login"    className="text-sm text-gray-400 hover:text-white transition-colors">Sign in</Link>
              <Link to="/register" className="btn-primary text-sm py-1.5 px-4">Sign up</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export function Avatar({ username, avatarUrl = null, size = 8, className = '' }) {
  const colors = [
    'from-violet-500 to-pink-500',
    'from-blue-500 to-violet-500',
    'from-pink-500 to-rose-500',
    'from-emerald-500 to-teal-500',
    'from-amber-500 to-orange-500',
  ]
  const idx = username ? username.charCodeAt(0) % colors.length : 0
  const px = size * 4  // Tailwind spacing: 1 unit = 4px

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={username}
        style={{ width: px, height: px }}
        className={`rounded-full object-cover shrink-0 ${className}`}
      />
    )
  }

  return (
    <div
      style={{ width: px, height: px, fontSize: `${px * 0.42}px` }}
      className={`bg-gradient-to-br ${colors[idx]} rounded-full flex items-center justify-center text-white font-bold shrink-0 ${className}`}
    >
      {username?.[0]?.toUpperCase() ?? '?'}
    </div>
  )
}
