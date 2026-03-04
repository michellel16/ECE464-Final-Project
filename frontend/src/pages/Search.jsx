import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import axios from 'axios'
import { Avatar } from '../components/Navbar'

export default function Search() {
  const [params] = useSearchParams()
  const q = params.get('q') ?? ''
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!q) return
    setLoading(true)
    axios.get(`/api/search/?q=${encodeURIComponent(q)}`)
      .then(r => setResults(r.data))
      .finally(() => setLoading(false))
  }, [q])

  if (!q) return (
    <div className="max-w-3xl mx-auto px-4 py-16 text-center text-gray-500">
      Use the search bar above to find artists, albums, songs, or users.
    </div>
  )

  if (loading) return <Loader />

  if (!results) return null

  const total = results.artists.length + results.albums.length + results.songs.length + results.users.length

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-2xl font-bold text-white">
        Results for <span className="text-violet-400">"{q}"</span>
        <span className="ml-3 text-gray-500 text-base font-normal">{total} found</span>
      </h1>

      {results.artists.length > 0 && (
        <Section title="Artists">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {results.artists.map(a => (
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

      {results.albums.length > 0 && (
        <Section title="Albums">
          <div className="space-y-2">
            {results.albums.map(a => (
              <Link key={a.id} to={`/albums/${a.id}`} className="card p-3 flex items-center gap-4 hover:border-violet-700 transition-colors group">
                {a.cover_url ? (
                  <img src={a.cover_url} alt={a.title} className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
                ) : (
                  <div className="w-12 h-12 rounded bg-gray-800 flex items-center justify-center text-xl shrink-0">🎵</div>
                )}
                <div className="min-w-0">
                  <p className="text-white font-medium group-hover:text-violet-400 transition-colors truncate">{a.title}</p>
                  <p className="text-gray-500 text-sm">{a.artist?.name} · {a.release_date?.slice(0, 4)}</p>
                  <div className="flex gap-1 mt-1">
                    {a.genres?.map(g => (
                      <span key={g} className="text-xs text-violet-400 bg-violet-900/30 px-2 py-0.5 rounded-full">{g}</span>
                    ))}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </Section>
      )}

      {results.songs.length > 0 && (
        <Section title="Songs">
          <div className="space-y-2">
            {results.songs.map(s => (
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

      {results.users.length > 0 && (
        <Section title="Users">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {results.users.map(u => (
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

      {total === 0 && (
        <div className="text-center text-gray-500 py-12">No results found for "{q}"</div>
      )}
    </div>
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
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
