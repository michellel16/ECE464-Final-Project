import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import StarRating from '../components/StarRating'

export default function Stats() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/stats/me')
      .then(r => setStats(r.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader />

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">My Stats</h1>
        <p className="text-gray-400 text-sm mt-1">Your music listening journey at a glance</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Albums Listened"  value={stats.albums_listened}  emoji="💿" />
        <StatCard label="Songs Listened"   value={stats.songs_listened}   emoji="🎵" />
        <StatCard label="Reviews Written"  value={stats.total_reviews}    emoji="✍" />
        <StatCard
          label="Avg Rating Given"
          value={stats.average_rating ? `${stats.average_rating} / 5` : '—'}
          emoji="⭐"
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top genres */}
        {stats.top_genres.length > 0 && (
          <div className="card p-5 space-y-4">
            <h2 className="font-bold text-white">Top Genres</h2>
            <div className="space-y-3">
              {stats.top_genres.map((g, i) => {
                const max = stats.top_genres[0].count
                return (
                  <div key={g.name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-300">{i + 1}. {g.name}</span>
                      <span className="text-gray-500">{g.count} album{g.count !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-violet-600 to-pink-500 rounded-full transition-all"
                        style={{ width: `${(g.count / max) * 100}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Rating distribution */}
        {Object.keys(stats.rating_distribution ?? {}).length > 0 && (
          <div className="card p-5 space-y-4">
            <h2 className="font-bold text-white">Rating Distribution</h2>
            <div className="space-y-2">
              {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map(r => {
                const count = stats.rating_distribution[r.toString()] ?? 0
                const maxCount = Math.max(...Object.values(stats.rating_distribution))
                return (
                  <div key={r} className="flex items-center gap-3 text-sm">
                    <span className="text-yellow-500 w-6 text-right font-mono">{r}</span>
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-yellow-500/70 rounded-full"
                        style={{ width: maxCount ? `${(count / maxCount) * 100}%` : '0%' }}
                      />
                    </div>
                    <span className="text-gray-500 w-5 text-right">{count}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Recent reviews */}
      {stats.recent_reviews.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-bold text-white text-lg">Recent Reviews</h2>
          <div className="space-y-3">
            {stats.recent_reviews.map(r => (
              <div key={r.id} className="card p-4 flex items-start gap-4">
                {r.target_cover && (
                  <Link to={`/${r.target_type}s/${r.target_id}`}>
                    <img src={r.target_cover} alt="" className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
                  </Link>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <Link
                        to={`/${r.target_type}s/${r.target_id}`}
                        className="text-white font-medium hover:text-violet-400 transition-colors"
                      >
                        {r.target_title}
                      </Link>
                      {r.target_artist && (
                        <p className="text-gray-500 text-xs">{r.target_artist}</p>
                      )}
                    </div>
                    <StarRating value={r.rating} readonly size="sm" />
                  </div>
                  {r.text && <p className="text-gray-400 text-sm mt-1">{r.text}</p>}
                  <p className="text-gray-600 text-xs mt-1">{new Date(r.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {stats.total_reviews === 0 && (
        <div className="card p-10 text-center text-gray-500">
          <p className="text-lg mb-2">No activity yet!</p>
          <p className="mb-4">Start exploring and reviewing music to see your stats.</p>
          <Link to="/discover" className="btn-primary">Explore Music</Link>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, emoji }) {
  return (
    <div className="card p-5 text-center">
      <div className="text-3xl mb-2">{emoji}</div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-gray-500 text-xs mt-1">{label}</div>
    </div>
  )
}

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
