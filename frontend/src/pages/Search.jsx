import { useState, useEffect } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { Avatar } from '../components/Navbar'

const TABS = ['All', 'Artists', 'Albums', 'Songs', 'Users']

export default function Search() {
  const [params] = useSearchParams()
  const q = params.get('q') ?? ''
  const { user } = useAuth()
  const navigate = useNavigate()

  const [tab, setTab] = useState('All')

  const [localResults, setLocalResults]     = useState(null)
  const [spotifyResults, setSpotifyResults] = useState(null)
  const [localLoading, setLocalLoading]     = useState(false)
  const [spotifyLoading, setSpotifyLoading] = useState(false)
  const [spotifyError, setSpotifyError]     = useState(null)
  const [importing, setImporting]           = useState({})
  const [similarArtists, setSimilarArtists] = useState(null)   // {label, items}
  const [similarAlbums, setSimilarAlbums]   = useState(null)


  // Reset tab and similar results when query changes
  useEffect(() => { setTab('All') }, [q])

  useEffect(() => {
    if (!q) {
      setLocalResults(null)
      setSpotifyResults(null)
      setSimilarArtists(null)
      setSimilarAlbums(null)
      return
    }

    setLocalLoading(true)
    setSpotifyLoading(true)
    setLocalResults(null)
    setSpotifyResults(null)
    setSpotifyError(null)
    setSimilarArtists(null)
    setSimilarAlbums(null)

    axios.get(`/api/search/?q=${encodeURIComponent(q)}`)
      .then(r => {
        setLocalResults(r.data)
        // Fire similar-item lookups immediately with the fresh data (no OpenAI)
        const topArtist = r.data.artists?.[0]
        const topAlbum  = r.data.albums?.[0]
        if (topArtist) {
          axios.get(`/api/search/similar?item_type=artist&item_id=${topArtist.id}&limit=5`)
            .then(s => { if (s.data.items?.length) setSimilarArtists(s.data) })
            .catch(e => console.error('[similar artists]', e?.response?.data ?? e.message))
        }
        if (topAlbum) {
          axios.get(`/api/search/similar?item_type=album&item_id=${topAlbum.id}&limit=5`)
            .then(s => { if (s.data.items?.length) setSimilarAlbums(s.data) })
            .catch(e => console.error('[similar albums]', e?.response?.data ?? e.message))
        }
      })
      .finally(() => setLocalLoading(false))

    axios.get(`/api/spotify/search?q=${encodeURIComponent(q)}`)
      .then(r => setSpotifyResults(r.data))
      .catch(err => {
        setSpotifyError(err.response?.data?.detail ?? err.message ?? 'Unknown error')
        setSpotifyResults(null)
      })
      .finally(() => setSpotifyLoading(false))
  }, [q])

  async function importAlbum(spotifyAlbumId) {
    if (!user) { navigate('/login'); return }
    setImporting(i => ({ ...i, [spotifyAlbumId]: true }))
    try {
      const { data } = await axios.post('/api/spotify/import-album', { spotify_album_id: spotifyAlbumId })
      navigate(`/albums/${data.album_id}`)
    } catch {
      setImporting(i => ({ ...i, [spotifyAlbumId]: false }))
    }
  }

  async function importArtist(spotifyArtistId) {
    if (!user) { navigate('/login'); return }
    setImporting(i => ({ ...i, [spotifyArtistId]: true }))
    try {
      const { data } = await axios.post('/api/spotify/import-artist', { spotify_artist_id: spotifyArtistId })
      navigate(`/artists/${data.artist_id}`)
    } catch {
      setImporting(i => ({ ...i, [spotifyArtistId]: false }))
    }
  }

  async function importTrack(spotifyTrackId) {
    if (!user) { navigate('/login'); return }
    setImporting(i => ({ ...i, [spotifyTrackId]: true }))
    try {
      const { data } = await axios.post('/api/spotify/import-track', { spotify_track_id: spotifyTrackId })
      navigate(`/songs/${data.song_id}`)
    } catch {
      setImporting(i => ({ ...i, [spotifyTrackId]: false }))
    }
  }

  if (!q) return (
    <div className="max-w-3xl mx-auto px-4 py-16 text-center text-gray-500">
      Use the search bar above to find artists, albums, songs, or users.
    </div>
  )

  const localTotal = localResults
    ? localResults.artists.length + localResults.albums.length + localResults.songs.length + localResults.users.length
    : 0

  const hasSpotify = spotifyResults && (
    spotifyResults.tracks.length + spotifyResults.albums.length + spotifyResults.artists.length > 0
  )

  const showArtists = tab === 'All' || tab === 'Artists'
  const showAlbums  = tab === 'All' || tab === 'Albums'
  const showSongs   = tab === 'All' || tab === 'Songs'
  const showUsers   = tab === 'All' || tab === 'Users'

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <h1 className="text-2xl font-bold text-white">
        Results for <span className="text-violet-400">"{q}"</span>
      </h1>

      {/* ── Tabs ── */}
      <div className="flex gap-1 border-b border-gray-800">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === t
                ? 'border-violet-500 text-violet-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {localLoading && <Loader />}

      {!localLoading && localResults && (
        <div className="space-y-8">

          {/* Artists */}
          {showArtists && localResults.artists.length > 0 && (
            <Section title="Artists">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {localResults.artists.map(a => (
                  <Link key={a.id} to={`/artists/${a.id}`} className="group card p-4 flex flex-col items-center gap-2 hover:border-violet-700 transition-colors">
                    {a.image_url ? (
                      <img src={a.image_url} alt={a.name} className="w-20 h-20 rounded-full object-cover" loading="lazy" />
                    ) : (
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-violet-900 to-gray-800 flex items-center justify-center text-3xl">🎤</div>
                    )}
                    <p className="text-white font-medium text-sm text-center group-hover:text-violet-400 transition-colors">{a.name}</p>
                    <p className="text-gray-500 text-xs text-center">{a.genres?.join(', ')}</p>
                  </Link>
                ))}
              </div>
            </Section>
          )}

          {/* Albums */}
          {showAlbums && localResults.albums.length > 0 && (
            <Section title="Albums">
              <div className="space-y-2">
                {localResults.albums.map(a => (
                  <Link key={a.id} to={`/albums/${a.id}`} className="card p-3 flex items-center gap-4 hover:border-violet-700 transition-colors group">
                    {a.cover_url ? (
                      <img src={a.cover_url} alt={a.title} className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
                    ) : (
                      <div className="w-12 h-12 rounded bg-gray-800 flex items-center justify-center text-xl shrink-0">🎵</div>
                    )}
                    <div className="min-w-0">
                      <p className="text-white font-medium group-hover:text-violet-400 transition-colors truncate">{a.title}</p>
                      <p className="text-gray-500 text-sm">{a.artist?.name} · {a.release_date?.slice(0, 4)}</p>
                    </div>
                  </Link>
                ))}
              </div>
            </Section>
          )}

          {/* Songs */}
          {showSongs && localResults.songs.length > 0 && (
            <Section title="Songs">
              <div className="space-y-2">
                {localResults.songs.map(s => (
                  <Link key={s.id} to={`/songs/${s.id}`} className="card p-3 flex items-center gap-4 hover:border-violet-700 transition-colors group">
                    {s.album?.cover_url ? (
                      <img src={s.album.cover_url} alt="" className="w-10 h-10 rounded object-cover shrink-0" loading="lazy" />
                    ) : (
                      <div className="w-10 h-10 rounded bg-gray-800 flex items-center justify-center shrink-0">♪</div>
                    )}
                    <div className="min-w-0">
                      <p className="text-white font-medium group-hover:text-violet-400 transition-colors truncate">{s.title}</p>
                      <p className="text-gray-500 text-sm">{s.artist?.name}{s.album ? ` · ${s.album.title}` : ''}</p>
                    </div>
                  </Link>
                ))}
              </div>
            </Section>
          )}

          {/* Users */}
          {showUsers && localResults.users.length > 0 && (
            <Section title="Users">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {localResults.users.map(u => (
                  <Link key={u.username} to={`/users/${u.username}`} className="card p-4 flex items-center gap-3 hover:border-violet-700 transition-colors group">
                    <Avatar username={u.username} size={10} />
                    <div className="min-w-0">
                      <p className="text-white font-medium group-hover:text-violet-400 transition-colors">{u.username}</p>
                      {u.bio && <p className="text-gray-500 text-xs truncate">{u.bio}</p>}
                    </div>
                  </Link>
                ))}
              </div>
            </Section>
          )}

          {/* Empty state for filtered tab */}
          {localTotal > 0 && (
            (tab === 'Artists' && localResults.artists.length === 0) ||
            (tab === 'Albums'  && localResults.albums.length === 0)  ||
            (tab === 'Songs'   && localResults.songs.length === 0)   ||
            (tab === 'Users'   && localResults.users.length === 0)
          ) && (
            <p className="text-gray-500 text-sm">No {tab.toLowerCase()} found for "{q}".</p>
          )}

          {localTotal === 0 && !spotifyLoading && tab !== 'Users' && (
            <p className="text-gray-500 text-sm">No Tunelog results — see Spotify results below.</p>
          )}

          {localTotal === 0 && tab === 'Users' && (
            <p className="text-gray-500 text-sm">No users found for "{q}".</p>
          )}
        </div>
      )}

      {/* ── Recommended based on search ── */}
      {(similarArtists || similarAlbums) && (tab === 'All' || tab === 'Artists' || tab === 'Albums') && (
        <div className="space-y-6 pt-2">
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-800" />
            <span className="text-xs text-gray-400 font-medium tracking-wide uppercase">Recommended</span>
            <div className="flex-1 h-px bg-gray-800" />
          </div>

          {similarArtists && (tab === 'All' || tab === 'Artists') && (
            <div className="space-y-3">
              <p className="text-base font-semibold text-white">{similarArtists.label}</p>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                {similarArtists.items.map(a => (
                  <Link key={a.id} to={`/artists/${a.id}`} className="group card p-3 flex flex-col items-center gap-2 hover:border-violet-700 transition-colors">
                    {a.image_url ? (
                      <img src={a.image_url} alt={a.name} className="w-16 h-16 rounded-full object-cover" loading="lazy" />
                    ) : (
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-900 to-gray-800 flex items-center justify-center text-2xl">🎤</div>
                    )}
                    <p className="text-white text-xs font-medium text-center group-hover:text-violet-400 transition-colors">{a.name}</p>
                    {a.similarity != null && (
                      <span className="text-[10px] text-violet-400/70">{Math.round(a.similarity * 100)}% match</span>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {similarAlbums && (tab === 'All' || tab === 'Albums') && (
            <div className="space-y-3">
              <p className="text-base font-semibold text-white">{similarAlbums.label}</p>
              <div className="space-y-2">
                {similarAlbums.items.map(a => (
                  <Link key={a.id} to={`/albums/${a.id}`} className="card p-3 flex items-center gap-4 hover:border-violet-700 transition-colors group">
                    {a.cover_url ? (
                      <img src={a.cover_url} alt={a.title} className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
                    ) : (
                      <div className="w-12 h-12 rounded bg-gray-800 flex items-center justify-center text-xl shrink-0">🎵</div>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="text-white font-medium group-hover:text-violet-400 transition-colors truncate">{a.title}</p>
                      <p className="text-gray-500 text-sm">{a.artist?.name} · {a.release_date?.slice(0, 4)}</p>
                    </div>
                    {a.similarity != null && (
                      <span className="text-[10px] text-violet-400/70 shrink-0">{Math.round(a.similarity * 100)}% match</span>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Spotify section (All + Artists/Albums/Songs tabs, not Users) ── */}
      {tab !== 'Users' && (
        <>
          {(hasSpotify || spotifyLoading || spotifyError) && (
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-gray-800" />
              <span className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
                <SpotifyIcon className="text-green-500 w-3.5 h-3.5" /> Spotify Catalog
              </span>
              <div className="flex-1 h-px bg-gray-800" />
            </div>
          )}

          {spotifyError && (
            <div className="card p-4 border-red-900/50 text-sm">
              <p className="text-red-400 font-medium">Spotify search unavailable</p>
              <p className="text-gray-500 mt-0.5">{spotifyError}</p>
            </div>
          )}

          {spotifyLoading && (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
              Searching Spotify…
            </div>
          )}

          {!spotifyLoading && hasSpotify && (
            <div className="space-y-8">
              {(tab === 'All' || tab === 'Artists') && spotifyResults.artists.length > 0 && (
                <Section title="Artists on Spotify">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {spotifyResults.artists.map(a => (
                      <div key={a.spotify_id} className="card p-4 flex flex-col items-center gap-2">
                        {a.image_url ? (
                          <img src={a.image_url} alt={a.name} className="w-20 h-20 rounded-full object-cover" loading="lazy" />
                        ) : (
                          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-green-900/40 to-gray-800 flex items-center justify-center text-3xl">🎤</div>
                        )}
                        <p className="text-white font-medium text-sm text-center">{a.name}</p>
                        {a.genres.length > 0 && (
                          <p className="text-gray-500 text-xs text-center">{a.genres.slice(0, 2).join(', ')}</p>
                        )}
                        {a.tunelog_artist_id ? (
                          <Link to={`/artists/${a.tunelog_artist_id}`} className="text-xs text-violet-400 hover:text-violet-300 transition-colors font-medium">
                            View in Tunelog →
                          </Link>
                        ) : (
                          <button
                            onClick={() => importArtist(a.spotify_id)}
                            disabled={!!importing[a.spotify_id]}
                            className="text-xs px-3 py-1 rounded-full bg-green-700/30 text-green-400 border border-green-700/50 hover:bg-green-700/50 disabled:opacity-50 transition-colors font-medium"
                          >
                            {importing[a.spotify_id] ? 'Importing…' : '+ Import'}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {(tab === 'All' || tab === 'Albums') && spotifyResults.albums.length > 0 && (
                <Section title="Albums on Spotify">
                  <div className="space-y-2">
                    {spotifyResults.albums.map(a => (
                      <div key={a.spotify_id} className="card p-3 flex items-center gap-4">
                        {a.cover_url ? (
                          <img src={a.cover_url} alt={a.name} className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
                        ) : (
                          <div className="w-12 h-12 rounded bg-gray-800 flex items-center justify-center text-xl shrink-0">🎵</div>
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="text-white font-medium truncate">{a.name}</p>
                          <p className="text-gray-500 text-sm">{a.artist_name} · {a.release_date} · {a.track_count} tracks</p>
                        </div>
                        {a.tunelog_album_id ? (
                          <Link to={`/albums/${a.tunelog_album_id}`} className="text-xs text-violet-400 hover:text-violet-300 transition-colors font-medium shrink-0">
                            View →
                          </Link>
                        ) : (
                          <button
                            onClick={() => importAlbum(a.spotify_id)}
                            disabled={!!importing[a.spotify_id]}
                            className="text-xs px-3 py-1.5 rounded-full bg-green-700/30 text-green-400 border border-green-700/50 hover:bg-green-700/50 disabled:opacity-50 transition-colors font-medium shrink-0"
                          >
                            {importing[a.spotify_id] ? 'Importing…' : '+ Import'}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {(tab === 'All' || tab === 'Songs') && spotifyResults.tracks.length > 0 && (
                <Section title="Tracks on Spotify">
                  <div className="space-y-2">
                    {spotifyResults.tracks.map(t => (
                      <div key={t.spotify_id} className="card p-3 flex items-center gap-4">
                        {t.cover_url ? (
                          <img src={t.cover_url} alt="" className="w-10 h-10 rounded object-cover shrink-0" loading="lazy" />
                        ) : (
                          <div className="w-10 h-10 rounded bg-gray-800 flex items-center justify-center shrink-0 text-gray-600">♪</div>
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="text-white font-medium truncate">{t.name}</p>
                          <p className="text-gray-500 text-sm truncate">{t.artist_name}{t.album_name ? ` · ${t.album_name}` : ''}</p>
                        </div>
                        {t.tunelog_song_id ? (
                          <Link to={`/songs/${t.tunelog_song_id}`} className="text-xs text-violet-400 hover:text-violet-300 transition-colors font-medium shrink-0">
                            View →
                          </Link>
                        ) : (
                          <button
                            onClick={() => importTrack(t.spotify_id)}
                            disabled={!!importing[t.spotify_id]}
                            className="text-xs px-3 py-1.5 rounded-full bg-green-700/30 text-green-400 border border-green-700/50 hover:bg-green-700/50 disabled:opacity-50 transition-colors font-medium shrink-0"
                          >
                            {importing[t.spotify_id] ? 'Importing…' : '+ Import'}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </Section>
              )}
            </div>
          )}
        </>
      )}

      {!spotifyLoading && spotifyResults !== null && !hasSpotify && localTotal === 0 && tab !== 'Users' && (
        <div className="text-center text-gray-500 py-12">No results found for "{q}"</div>
      )}
    </div>
  )
}

function SpotifyIcon({ className = '' }) {
  return (
    <svg viewBox="0 0 24 24" className={`fill-current ${className}`} xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
    </svg>
  )
}

function Section({ title, children }) {
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-gray-200">{title}</h2>
      {children}
    </div>
  )
}

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-[20vh]">
      <div className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
