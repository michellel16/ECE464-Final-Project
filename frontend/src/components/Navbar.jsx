import { useState, useRef, useEffect, useCallback } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'

const HISTORY_KEY = 'tunelog_search_history'
const HISTORY_LIMIT = 8

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) ?? [] } catch { return [] }
}

function saveHistory(history) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
}

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [q, setQ]               = useState('')
  const [menuOpen, setMenu]     = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory]   = useState(loadHistory)
  const [unreadCount, setUnreadCount] = useState(0)
  const [bellOpen, setBellOpen]       = useState(false)
  const [bellRecs, setBellRecs]       = useState([])
  const [bellLoading, setBellLoading] = useState(false)
  const menuRef   = useRef(null)
  const searchRef = useRef(null)
  const bellRef   = useRef(null)

  // Close dropdowns on outside click
  useEffect(() => {
    function handler(e) {
      if (menuRef.current   && !menuRef.current.contains(e.target))   setMenu(false)
      if (searchRef.current && !searchRef.current.contains(e.target)) setShowHistory(false)
      if (bellRef.current   && !bellRef.current.contains(e.target))   setBellOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Fetch unread recommendation count
  useEffect(() => {
    if (!user) { setUnreadCount(0); return }
    axios.get('/api/social/recommendations/unread-count')
      .then(r => setUnreadCount(r.data.count))
      .catch(() => {})
  }, [user])

  async function openBell() {
    if (bellOpen) { setBellOpen(false); return }
    setBellOpen(true)
    setBellLoading(true)
    try {
      const { data } = await axios.get('/api/social/recommendations')
      setBellRecs(data.slice(0, 6))
      if (unreadCount > 0) {
        await axios.post('/api/social/recommendations/read-all')
        setUnreadCount(0)
      }
    } catch {}
    finally { setBellLoading(false) }
  }

  function addToHistory(term) {
    const trimmed = term.trim()
    if (!trimmed) return
    const updated = [trimmed, ...history.filter(h => h !== trimmed)].slice(0, HISTORY_LIMIT)
    setHistory(updated)
    saveHistory(updated)
  }

  function removeFromHistory(term, e) {
    e.stopPropagation()
    const updated = history.filter(h => h !== term)
    setHistory(updated)
    saveHistory(updated)
  }

  function clearHistory() {
    setHistory([])
    saveHistory([])
  }

  function handleSearch(e) {
    e.preventDefault()
    if (q.trim()) {
      addToHistory(q.trim())
      navigate(`/search?q=${encodeURIComponent(q.trim())}`)
      setQ('')
      setShowHistory(false)
    }
  }

  function selectHistory(term) {
    addToHistory(term)
    navigate(`/search?q=${encodeURIComponent(term)}`)
    setQ('')
    setShowHistory(false)
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
        <div className="flex-1 max-w-lg relative" ref={searchRef}>
          <form onSubmit={handleSearch}>
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              onFocus={() => setShowHistory(true)}
              placeholder="Search artists, albums, songs…"
              className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded-full px-4 py-2 focus:outline-none focus:border-violet-500 placeholder-gray-500 transition-colors"
            />
          </form>
          {showHistory && history.length > 0 && (
            <div className="absolute top-full mt-2 left-0 right-0 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl py-1 z-50 overflow-hidden">
              <div className="flex items-center justify-between px-3 py-1.5">
                <span className="text-xs text-gray-500 font-medium">Recent searches</span>
                <button
                  onClick={clearHistory}
                  className="text-xs text-gray-500 hover:text-red-400 transition-colors"
                >
                  Clear all
                </button>
              </div>
              {history.map(term => (
                <button
                  key={term}
                  onClick={() => selectHistory(term)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors text-left group"
                >
                  <svg className="w-3.5 h-3.5 text-gray-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="flex-1 truncate">{term}</span>
                  <span
                    role="button"
                    onClick={e => removeFromHistory(term, e)}
                    className="text-gray-600 hover:text-gray-300 transition-colors shrink-0 px-1"
                  >
                    ✕
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-5">
          {navLink('/discover', 'Discover')}
          {navLink('/charts', 'Charts')}
          {user && navLink('/lists', 'My Lists')}
          {user && navLink('/stats', 'Stats')}
        </div>

        {/* Recommendation bell */}
        {user && (
          <div className="relative shrink-0" ref={bellRef}>
            <button
              onClick={openBell}
              className="relative p-2 text-gray-400 hover:text-white transition-colors"
              title="Recommendations"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 bg-pink-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center leading-none">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {bellOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden z-50">
                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
                  <span className="text-sm font-semibold text-white">Recommendations</span>
                  <Link
                    to={`/users/${user.username}`}
                    onClick={() => setBellOpen(false)}
                    className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
                  >
                    View all
                  </Link>
                </div>
                {bellLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="w-5 h-5 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : bellRecs.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-8 px-4">No recommendations yet.</p>
                ) : (
                  <div className="divide-y divide-gray-800/60 max-h-72 overflow-y-auto">
                    {bellRecs.map(rec => {
                      const item = rec.song ?? rec.album
                      const href = item ? `/${rec.song ? 'songs' : 'albums'}/${item.id}` : null
                      return (
                        <Link
                          key={rec.id}
                          to={href ?? '#'}
                          onClick={() => setBellOpen(false)}
                          className="flex items-center gap-3 px-4 py-3 hover:bg-gray-800 transition-colors"
                        >
                          {item?.cover_url ? (
                            <img src={item.cover_url} alt="" className="w-9 h-9 rounded shrink-0 object-cover" />
                          ) : (
                            <div className="w-9 h-9 rounded bg-gray-800 flex items-center justify-center text-gray-500 shrink-0 text-sm">
                              {rec.song ? '♪' : '💿'}
                            </div>
                          )}
                          <div className="min-w-0 flex-1">
                            <p className="text-white text-xs font-medium truncate">{item?.title ?? '—'}</p>
                            <p className="text-gray-500 text-xs truncate">
                              from <span className="text-violet-400">{rec.sender_username}</span>
                            </p>
                            {rec.note && <p className="text-gray-600 text-xs truncate italic">"{rec.note}"</p>}
                          </div>
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

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
