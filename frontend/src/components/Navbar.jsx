import { useState, useRef, useEffect, useCallback } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { staticUrl } from '../utils'

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
  const [unreadCount, setUnreadCount]   = useState(0)
  const [bellOpen, setBellOpen]         = useState(false)
  const [notifications, setNotifications] = useState([])
  const [bellLoading, setBellLoading]   = useState(false)
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

  // Fetch unread notification count
  useEffect(() => {
    if (!user) { setUnreadCount(0); return }
    axios.get('/api/notifications/unread-count')
      .then(r => setUnreadCount(r.data.count))
      .catch(() => {})
  }, [user])

  async function openBell() {
    if (bellOpen) { setBellOpen(false); return }
    setBellOpen(true)
    setBellLoading(true)
    try {
      const { data } = await axios.get('/api/notifications/')
      setNotifications(data.slice(0, 10))
      if (unreadCount > 0) {
        await axios.post('/api/notifications/mark-all-read')
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
      className={`text-[10px] font-semibold tracking-widest uppercase transition-colors pb-0.5 border-b ${
        location.pathname === to
          ? 'text-white border-violet-500'
          : 'text-gray-300 hover:text-white border-transparent'
      }`}
    >
      {label}
    </Link>
  )

  return (
    <nav className="fixed top-0 inset-x-0 z-50 backdrop-blur-md border-b border-[#252540]" style={{ backgroundColor: 'rgba(5,5,13,0.97)' }}>
      <div className="max-w-7xl mx-auto px-6 h-15 flex items-center gap-6" style={{ height: '60px' }}>
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0 mr-2">
          <div className="w-7 h-7 bg-gradient-to-br from-pink-500 to-violet-700 flex items-center justify-center text-white font-semibold text-xs rounded-sm"
               style={{ fontFamily: '"Playfair Display", serif', fontStyle: 'italic', fontSize: '15px' }}>
            T
          </div>
          <span className="hidden sm:block font-semibold text-[15px] tracking-wide uppercase bg-gradient-to-r from-pink-300 via-violet-200 to-violet-300 bg-clip-text text-transparent"
                style={{ letterSpacing: '0.12em' }}>
            Tunelog
          </span>
        </Link>

        {/* Search */}
        <div className="flex-1 max-w-md relative" ref={searchRef}>
          <form onSubmit={handleSearch}>
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              onFocus={() => setShowHistory(true)}
              placeholder="Search artists, albums, songs…"
              className="w-full bg-[#0b0b18] border border-[#252535] text-white text-xs rounded px-4 py-2 focus:outline-none focus:border-violet-600/70 placeholder-gray-500 transition-colors"
            />
          </form>
          {showHistory && history.length > 0 && (
            <div className="absolute top-full mt-1.5 left-0 right-0 bg-[#0e0e1c] border border-[#1c1c2e] rounded shadow-2xl py-1 z-50 overflow-hidden">
              <div className="flex items-center justify-between px-3 py-1.5">
                <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-widest">Recent searches</span>
                <button
                  onClick={clearHistory}
                  className="text-[10px] text-gray-500 hover:text-red-400 transition-colors"
                >
                  Clear all
                </button>
              </div>
              {history.map(term => (
                <button
                  key={term}
                  onClick={() => selectHistory(term)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-gray-300 hover:bg-[#1a1a2e] hover:text-white transition-colors text-left group"
                >
                  <svg className="w-3 h-3 text-gray-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="flex-1 truncate">{term}</span>
                  <span
                    role="button"
                    onClick={e => removeFromHistory(term, e)}
                    className="text-gray-500 hover:text-gray-300 transition-colors shrink-0 px-1"
                  >
                    ✕
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-6">
          {navLink('/discover', 'Discover')}
          {user && navLink('/lists', 'Lists')}
          {user && navLink('/stats', 'Stats')}
        </div>

        {/* Recommendation bell */}
        {user && (
          <div className="relative shrink-0" ref={bellRef}>
            <button
              onClick={openBell}
              className="relative p-2 text-gray-300 hover:text-white transition-colors"
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
              <div className="absolute right-0 top-full mt-1 w-80 bg-[#0e0e1c] border border-[#252535] rounded shadow-2xl overflow-hidden z-50">
                <div className="px-4 py-3 border-b border-[#252535]">
                  <span className="text-[10px] font-semibold text-gray-300 tracking-widest uppercase">Notifications</span>
                </div>
                {bellLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="w-5 h-5 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : notifications.length === 0 ? (
                  <p className="text-gray-400 text-xs text-center py-8 px-4">No notifications yet.</p>
                ) : (
                  <div className="divide-y divide-[#1c1c2e] max-h-80 overflow-y-auto">
                    {notifications.map(n => <NotifRow key={n.id} n={n} onClose={() => setBellOpen(false)} />)}
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
                className="flex items-center gap-2 hover:bg-white/5 rounded px-2.5 py-1.5 transition-colors border border-transparent hover:border-[#1c1c2e]"
              >
                <Avatar username={user.username} avatarUrl={user.avatar_url} size={8} />
                <span className="text-sm text-white hidden sm:block font-medium">{user.username}</span>
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-full mt-1 w-52 bg-[#0e0e1c] border border-[#252535] rounded shadow-2xl py-1 overflow-hidden">
                  <Link
                    to={`/users/${user.username}`}
                    className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-200 hover:bg-[#1a1a2e] hover:text-white"
                    onClick={() => setMenu(false)}
                  >
                    <Avatar username={user.username} avatarUrl={user.avatar_url} size={6} />
                    Profile
                  </Link>
                  <Link
                    to="/lists"
                    className="block px-4 py-2.5 text-sm text-gray-200 hover:bg-[#1a1a2e] hover:text-white"
                    onClick={() => setMenu(false)}
                  >
                    My Lists
                  </Link>
                  <Link
                    to="/stats"
                    className="block px-4 py-2.5 text-sm text-gray-200 hover:bg-[#1a1a2e] hover:text-white"
                    onClick={() => setMenu(false)}
                  >
                    Stats
                  </Link>
                  <div className="border-t border-[#252535] mt-1 pt-1">
                    <button
                      onClick={() => { logout(); setMenu(false); navigate('/') }}
                      className="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-[#1a1a2e]"
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link to="/login"    className="text-xs text-gray-300 hover:text-white transition-colors">Sign in</Link>
              <Link to="/register" className="btn-primary text-xs py-1.5 px-4">Sign up</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

function NotifRow({ n, onClose }) {
  const { user } = useAuth()

  const ICONS = {
    new_follower:   '👤',
    follow_request: '🔔',
    review_like:    '❤️',
    recommendation: '🎵',
    list_invite:     '📋',
    list_role_update:'📋',
  }

  function label() {
    const who = n.from_user?.username ?? 'Someone'
    if (n.type === 'new_follower')   return <><span className="text-violet-400">{who}</span> started following you</>
    if (n.type === 'follow_request') return <><span className="text-violet-400">{who}</span> wants to follow you</>
    if (n.type === 'review_like')    return <><span className="text-violet-400">{who}</span> liked your review</>
    if (n.type === 'list_invite')    return <><span className="text-violet-400">{who}</span> invited you to collaborate on a list</>
    if (n.type === 'list_role_update') {
      const role = n.entity_type
      return <><span className="text-violet-400">{who}</span> updated your access to <span className={role === 'editor' ? 'text-green-400' : 'text-gray-300'}>{role}</span></>
    }
    if (n.type === 'recommendation') {
      const item = n.song ?? n.album
      return <><span className="text-violet-400">{who}</span> recommended {item ? <span className="text-white">{item.title}</span> : 'something'}</>
    }
    return who
  }

  function href() {
    if (n.type === 'new_follower' || n.type === 'follow_request') {
      return n.from_user?.username ? `/users/${n.from_user.username}` : null
    }
    if (n.type === 'review_like') {
      if (n.review_target) {
        return `/${n.review_target.type === 'album' ? 'albums' : 'songs'}/${n.review_target.id}`
      }
      return null
    }
    if (n.type === 'list_invite' || n.type === 'list_role_update') {
      return '/lists?tab=collab'
    }
    if (n.type === 'recommendation') {
      return user?.username ? `/users/${user.username}?tab=recs` : null
    }
    return null
  }

  const item    = n.song ?? n.album
  const coverUrl = item?.cover_url ?? null
  const target  = href()
  const content = (
    <div className={`flex items-center gap-3 px-4 py-2.5 transition-colors ${n.is_read ? 'opacity-60' : ''} hover:bg-[#1a1a2e]`}>
      <div className="w-8 h-8 rounded bg-[#1a1a2e] flex items-center justify-center text-xs shrink-0 overflow-hidden border border-[#252535]">
        {coverUrl
          ? <img src={coverUrl} alt="" className="w-full h-full object-cover" />
          : <span>{ICONS[n.type] ?? '🔔'}</span>}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-gray-200 text-[11px] leading-snug">{label()}</p>
        {n.note && <p className="text-gray-500 text-[10px] italic truncate mt-0.5">"{n.note}"</p>}
        {!n.is_read && <span className="inline-block w-1.5 h-1.5 rounded-full bg-violet-500 ml-1 align-middle" />}
      </div>
    </div>
  )

  return target
    ? <Link to={target} onClick={onClose} className="block">{content}</Link>
    : <div>{content}</div>
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
        src={staticUrl(avatarUrl)}
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
