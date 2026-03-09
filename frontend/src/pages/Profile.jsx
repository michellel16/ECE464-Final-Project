import { useState, useEffect } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { Avatar } from '../components/Navbar'
import StarRating from '../components/StarRating'

export default function Profile() {
  const { username } = useParams()
  const { user: me } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [profile, setProfile]     = useState(null)
  const [reviews, setReviews]     = useState([])
  const [lists, setLists]         = useState([])
  const [isFollowing, setFollowing] = useState(false)
  const [tab, setTab]             = useState('reviews')
  const [loading, setLoading]     = useState(true)
  const [followLoading, setFL]    = useState(false)
  const [spotifyStatus, setSpotifyStatus] = useState(null)
  const [spotifyToast, setSpotifyToast]   = useState(null)
  const [showImport, setShowImport] = useState(false)
  const [showSpotifyMenu, setShowSpotifyMenu] = useState(false)

  const isMe = me?.username === username

  useEffect(() => {
    const fetches = [
      axios.get(`/api/users/${username}`),
      axios.get(`/api/users/${username}/reviews`),
      axios.get(`/api/lists/user/${username}`),
    ]
    if (me && !isMe) {
      fetches.push(axios.get(`/api/users/${username}/follow-status`))
    }
    Promise.all(fetches).then(([pRes, rRes, lRes, fsRes]) => {
      setProfile(pRes.data)
      setReviews(rRes.data)
      setLists(lRes.data)
      if (fsRes) setFollowing(fsRes.data.following)
    }).finally(() => setLoading(false))
  }, [username, me])

  // Fetch Spotify connection status for own profile
  useEffect(() => {
    if (isMe && me) {
      axios.get('/api/spotify/status').then(r => setSpotifyStatus(r.data)).catch(() => {})
    }
  }, [isMe, me])

  // Handle redirect back from Spotify OAuth
  useEffect(() => {
    const spotify = searchParams.get('spotify')
    if (!spotify) return
    if (spotify === 'connected') {
      setSpotifyToast({ type: 'success', msg: 'Spotify connected successfully!' })
      axios.get('/api/spotify/status').then(r => setSpotifyStatus(r.data)).catch(() => {})
    } else if (spotify === 'error') {
      const reason = searchParams.get('reason') || 'unknown error'
      setSpotifyToast({ type: 'error', msg: `Spotify connection failed: ${reason}` })
    }
    // Remove query params from URL
    setSearchParams({}, { replace: true })
    const timer = setTimeout(() => setSpotifyToast(null), 4000)
    return () => clearTimeout(timer)
  }, [])

  async function connectSpotify() {
    try {
      const { data } = await axios.get('/api/spotify/auth-url')
      window.location.href = data.url
    } catch {
      setSpotifyToast({ type: 'error', msg: 'Could not start Spotify connection.' })
    }
  }

  async function disconnectSpotify() {
    await axios.delete('/api/spotify/disconnect')
    setSpotifyStatus({ connected: false })
  }

  async function toggleFollow() {
    if (!me || isMe) return
    setFL(true)
    try {
      if (isFollowing) {
        await axios.delete(`/api/users/${username}/follow`)
        setFollowing(false)
        setProfile(p => ({ ...p, follower_count: (p.follower_count ?? 1) - 1 }))
      } else {
        await axios.post(`/api/users/${username}/follow`)
        setFollowing(true)
        setProfile(p => ({ ...p, follower_count: (p.follower_count ?? 0) + 1 }))
      }
    } finally {
      setFL(false)
    }
  }

  if (loading) return <Loader />
  if (!profile) return <div className="text-center py-20 text-gray-500">User not found.</div>

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Toast */}
      {spotifyToast && (
        <div className={`fixed top-20 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all ${
          spotifyToast.type === 'success' ? 'bg-green-700 text-white' : 'bg-red-700 text-white'
        }`}>
          {spotifyToast.msg}
        </div>
      )}

      {/* Profile header */}
      <div className="card p-6 mb-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
          <Avatar username={profile.username} size={20} className="ring-4 ring-violet-700/40" />
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-white">{profile.username}</h1>
            {profile.bio && <p className="text-gray-400 mt-1 text-sm">{profile.bio}</p>}
            <div className="flex gap-5 mt-3 text-sm text-gray-400">
              <span><strong className="text-white">{profile.follower_count ?? 0}</strong> followers</span>
              <span><strong className="text-white">{profile.following_count ?? 0}</strong> following</span>
              <span><strong className="text-white">{reviews.length}</strong> reviews</span>
            </div>
          </div>
          {me && !isMe && (
            <button
              onClick={toggleFollow}
              disabled={followLoading}
              className={`px-6 py-2 rounded-full text-sm font-medium transition-colors disabled:opacity-60 ${
                isFollowing
                  ? 'bg-gray-700 text-white hover:bg-red-900/60 hover:text-red-300'
                  : 'btn-primary'
              }`}
            >
              {followLoading ? '…' : isFollowing ? 'Following' : 'Follow'}
            </button>
          )}
          {isMe && (
            <Link to="/stats" className="btn-secondary text-sm">View Stats</Link>
          )}
        </div>

        {/* Spotify section — only on own profile */}
        {isMe && spotifyStatus !== null && (
          <div className="mt-5 pt-5 border-t border-gray-800">
            {spotifyStatus.connected ? (
              <div className="flex flex-col gap-3">
                <button
                  onClick={() => setShowSpotifyMenu(m => !m)}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-green-700/30 border border-green-700/50 text-green-400 text-sm font-semibold w-fit transition-colors hover:bg-green-700/50"
                >
                  <SpotifyIcon className="w-4 h-4" />
                  Connected
                  <span className="text-green-600 text-xs ml-1">{showSpotifyMenu ? '▲' : '▼'}</span>
                </button>
                {showSpotifyMenu && (
                  <div className="flex items-center gap-3 flex-wrap pl-1">
                    {spotifyStatus.display_name && (
                      <span className="text-gray-400 text-sm">{spotifyStatus.display_name}</span>
                    )}
                    <button
                      onClick={() => { setShowImport(true); setShowSpotifyMenu(false) }}
                      className="px-4 py-1.5 rounded-full text-sm font-medium bg-green-700/30 text-green-400 border border-green-700/50 hover:bg-green-700/50 transition-colors"
                    >
                      Import Music
                    </button>
                    <button
                      onClick={disconnectSpotify}
                      className="px-4 py-1.5 rounded-full text-sm font-medium border border-gray-700 text-gray-500 hover:border-red-700 hover:text-red-400 transition-colors"
                    >
                      Disconnect
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={connectSpotify}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-green-600 hover:bg-green-500 text-white text-sm font-semibold transition-colors"
              >
                <SpotifyIcon className="w-4 h-4" />
                Connect Spotify
              </button>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-xl p-1 w-fit mb-6">
        {['reviews', 'lists'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
              tab === t ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'reviews' && (
        <div className="space-y-3">
          {reviews.length === 0 ? (
            <div className="card p-8 text-center text-gray-500">No reviews yet.</div>
          ) : (
            reviews.map(r => <ReviewItem key={r.id} review={r} />)
          )}
        </div>
      )}

      {tab === 'lists' && (
        <div>
          {isMe && (
            <div className="mb-4">
              <Link to="/lists" className="btn-primary text-sm">Manage My Lists</Link>
            </div>
          )}
          {lists.length === 0 ? (
            <div className="card p-8 text-center text-gray-500">No public lists.</div>
          ) : (
            <div className="grid sm:grid-cols-2 gap-4">
              {lists.map(l => <ListCard key={l.id} list={l} />)}
            </div>
          )}
        </div>
      )}

      {/* Import modal */}
      {showImport && (
        <ImportModal onClose={() => setShowImport(false)} />
      )}
    </div>
  )
}

// ── Import Modal ──────────────────────────────────────────────────────────────

function ImportModal({ onClose }) {
  const [playlists, setPlaylists]   = useState([])
  const [selected, setSelected]     = useState(null)
  const [tracks, setTracks]         = useState([])
  const [checked, setChecked]       = useState({})
  const [loading, setLoading]       = useState(true)
  const [loadingTracks, setLT]      = useState(false)
  const [importing, setImporting]   = useState(false)
  const [imported, setImported]     = useState(0)

  useEffect(() => {
    axios.get('/api/spotify/playlists')
      .then(r => setPlaylists(r.data))
      .finally(() => setLoading(false))
  }, [])

  async function selectPlaylist(playlist) {
    setSelected(playlist)
    setTracks([])
    setChecked({})
    setLT(true)
    try {
      const { data } = await axios.get(`/api/spotify/playlists/${playlist.id}/tracks`)
      setTracks(data)
      // Pre-check tracks not yet in Tunelog
      const init = {}
      data.forEach(t => { if (!t.tunelog_song_id) init[t.spotify_id] = true })
      setChecked(init)
    } finally {
      setLT(false)
    }
  }

  function toggleTrack(spotify_id) {
    setChecked(c => ({ ...c, [spotify_id]: !c[spotify_id] }))
  }

  function toggleAll() {
    const unchecked = tracks.filter(t => !t.tunelog_song_id && !checked[t.spotify_id])
    if (unchecked.length > 0) {
      const next = { ...checked }
      unchecked.forEach(t => { next[t.spotify_id] = true })
      setChecked(next)
    } else {
      const next = { ...checked }
      tracks.filter(t => !t.tunelog_song_id).forEach(t => { next[t.spotify_id] = false })
      setChecked(next)
    }
  }

  async function doImport() {
    const toImport = tracks.filter(t => checked[t.spotify_id] && !t.tunelog_song_id)
    if (toImport.length === 0) return
    setImporting(true)
    let count = 0
    for (const t of toImport) {
      try {
        await axios.post('/api/spotify/import-track', { spotify_track_id: t.spotify_id })
        count++
        setImported(count)
      } catch {
        // skip failures
      }
    }
    // Refresh track list to update tunelog_song_id
    const { data } = await axios.get(`/api/spotify/playlists/${selected.id}/tracks`)
    setTracks(data)
    setChecked({})
    setImporting(false)
  }

  const toImportCount = tracks.filter(t => checked[t.spotify_id] && !t.tunelog_song_id).length

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <h2 className="font-bold text-white text-lg flex items-center gap-2">
            <SpotifyIcon className="text-green-500 w-5 h-5" />
            Import from Spotify
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-xl leading-none">&times;</button>
        </div>

        <div className="flex flex-1 min-h-0">
          {/* Playlist list */}
          <div className="w-56 border-r border-gray-800 overflow-y-auto flex-shrink-0">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : playlists.length === 0 ? (
              <p className="text-gray-500 text-sm p-4">No playlists found.</p>
            ) : (
              playlists.map(p => (
                <button
                  key={p.id}
                  onClick={() => selectPlaylist(p)}
                  className={`w-full text-left p-3 flex items-center gap-3 transition-colors hover:bg-gray-800 ${selected?.id === p.id ? 'bg-gray-800' : ''}`}
                >
                  {p.image_url ? (
                    <img src={p.image_url} alt="" className="w-10 h-10 rounded shrink-0 object-cover" />
                  ) : (
                    <div className="w-10 h-10 rounded bg-gray-700 flex items-center justify-center shrink-0 text-gray-500">♪</div>
                  )}
                  <div className="min-w-0">
                    <p className="text-white text-xs font-medium truncate">{p.name}</p>
                    <p className="text-gray-500 text-xs">{p.track_count} tracks</p>
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Track list */}
          <div className="flex-1 overflow-y-auto">
            {!selected ? (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                Select a playlist
              </div>
            ) : loadingTracks ? (
              <div className="flex items-center justify-center h-32">
                <div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <>
                <div className="sticky top-0 bg-gray-900 border-b border-gray-800 px-4 py-2 flex items-center justify-between">
                  <button onClick={toggleAll} className="text-xs text-violet-400 hover:text-violet-300 transition-colors">
                    Toggle all new
                  </button>
                  <span className="text-xs text-gray-500">{toImportCount} to import</span>
                </div>
                {tracks.map(t => (
                  <label
                    key={t.spotify_id}
                    className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-800/50 transition-colors ${t.tunelog_song_id ? 'opacity-50' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={!!checked[t.spotify_id]}
                      onChange={() => !t.tunelog_song_id && toggleTrack(t.spotify_id)}
                      disabled={!!t.tunelog_song_id}
                      className="w-4 h-4 accent-green-500 shrink-0"
                    />
                    {t.cover_url ? (
                      <img src={t.cover_url} alt="" className="w-9 h-9 rounded shrink-0 object-cover" />
                    ) : (
                      <div className="w-9 h-9 rounded bg-gray-800 flex items-center justify-center text-gray-600 shrink-0 text-xs">♪</div>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="text-white text-sm truncate">{t.name}</p>
                      <p className="text-gray-500 text-xs truncate">{t.artist_name} · {t.album_name}</p>
                    </div>
                    {t.tunelog_song_id && (
                      <span className="text-green-600 text-xs shrink-0">In Tunelog</span>
                    )}
                  </label>
                ))}
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 flex items-center justify-between">
          {importing ? (
            <span className="text-green-400 text-sm">Importing {imported}…</span>
          ) : imported > 0 && toImportCount === 0 ? (
            <span className="text-green-400 text-sm">{imported} track{imported !== 1 ? 's' : ''} imported!</span>
          ) : (
            <span className="text-gray-500 text-sm">{toImportCount} track{toImportCount !== 1 ? 's' : ''} selected</span>
          )}
          <div className="flex gap-2">
            <button onClick={onClose} className="btn-secondary text-sm">Close</button>
            <button
              onClick={doImport}
              disabled={toImportCount === 0 || importing}
              className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
            >
              {importing ? 'Importing…' : 'Import Selected'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SpotifyIcon({ className = '' }) {
  return (
    <svg viewBox="0 0 24 24" className={`fill-current ${className}`} xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
    </svg>
  )
}

function ReviewItem({ review }) {
  return (
    <div className="card p-4 flex gap-4 items-start">
      {review.target_cover && (
        <Link to={`/${review.target_type}s/${review.target_type === 'album' ? review.album_id : review.song_id}`}>
          <img src={review.target_cover} alt="" className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
        </Link>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="min-w-0">
            <p className="text-white font-medium truncate">{review.target_title ?? '?'}</p>
            {review.target_artist && (
              <p className="text-gray-500 text-xs">{review.target_artist}</p>
            )}
          </div>
          <StarRating value={review.rating} readonly size="sm" />
        </div>
        {review.text && <p className="text-gray-400 text-sm">{review.text}</p>}
        <p className="text-gray-600 text-xs mt-1">{new Date(review.created_at).toLocaleDateString()}</p>
      </div>
    </div>
  )
}

function ListCard({ list }) {
  return (
    <Link to={`/lists`} className="card p-4 hover:border-violet-700 transition-colors group">
      <p className="font-medium text-white group-hover:text-violet-400 transition-colors">{list.name}</p>
      {list.description && <p className="text-gray-500 text-sm mt-0.5 line-clamp-2">{list.description}</p>}
      <p className="text-gray-600 text-xs mt-2">{list.item_count} items · {list.list_type}</p>
    </Link>
  )
}

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
