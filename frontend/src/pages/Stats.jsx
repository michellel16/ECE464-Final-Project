import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { toPng } from 'html-to-image'
import { useAuth } from '../contexts/AuthContext'
import StarRating from '../components/StarRating'
import StatsPostcard from '../components/StatsPostcard'

const SPAN_OPTIONS = [
  { value: '7d',  label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' },
  { value: '1y',  label: '1 Year' },
  { value: 'all', label: 'All Time' },
]

export default function Stats() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  // Postcard state
  const [postcardSpan, setPostcardSpan] = useState('30d')
  const [postcardData, setPostcardData] = useState(null)
  const [postcardLoading, setPostcardLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const postcardRef = useRef(null)

  useEffect(() => {
    axios.get('/api/stats/me')
      .then(r => setStats(r.data))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    setPostcardLoading(true)
    axios.get(`/api/stats/me/postcard?time_span=${postcardSpan}`)
      .then(r => setPostcardData(r.data))
      .finally(() => setPostcardLoading(false))
  }, [postcardSpan])

  const handleExport = useCallback(async () => {
    if (!postcardRef.current) return
    setExporting(true)
    try {
      const dataUrl = await toPng(postcardRef.current, { pixelRatio: 2, cacheBust: true })
      const link = document.createElement('a')
      link.download = `tunelog-${user?.username ?? 'stats'}-${postcardSpan}.png`
      link.href = dataUrl
      link.click()
    } finally {
      setExporting(false)
    }
  }, [postcardSpan, user?.username])

  if (loading) return <Loader />

  const ap = stats.audio_profile

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

      {/* Audio profile (Spotify) */}
      {ap && ap.songs_with_features > 0 && (
        <div className="card p-5 space-y-5">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h2 className="font-bold text-white flex items-center gap-2">
                <SpotifyIcon className="text-green-500 w-5 h-5" />
                Sound Profile
              </h2>
              <p className="text-gray-500 text-xs mt-0.5">Based on {ap.songs_with_features} tracked song{ap.songs_with_features !== 1 ? 's' : ''} with Spotify data</p>
            </div>
            {ap.personality && (
              <span className="px-3 py-1 rounded-full bg-green-900/40 border border-green-700/50 text-green-400 text-sm font-medium">
                {ap.personality}
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-10 gap-y-4">
            <AudioBar label="Energy"           value={ap.energy}           color="from-orange-500 to-red-500" />
            <AudioBar label="Danceability"     value={ap.danceability}     color="from-pink-500 to-violet-500" />
            <AudioBar label="Positivity"       value={ap.valence}          color="from-yellow-400 to-green-500" />
            <AudioBar label="Acousticness"     value={ap.acousticness}     color="from-blue-400 to-teal-500" />
            <AudioBar label="Instrumentalness" value={ap.instrumentalness} color="from-violet-500 to-indigo-500" />
            {ap.tempo && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-400">Avg Tempo</span>
                <span className="text-white font-medium">{Math.round(ap.tempo)} BPM</span>
              </div>
            )}
          </div>
        </div>
      )}

      {ap && ap.songs_with_features === 0 && stats.songs_listened > 0 && (
        <div className="card p-5 flex items-center gap-4">
          <SpotifyIcon className="text-green-500 w-8 h-8 shrink-0" />
          <div>
            <p className="text-white font-medium">No audio data yet</p>
            <p className="text-gray-500 text-sm">
              Connect Spotify and import tracks to see your Sound Profile.{' '}
              <Link to={`/users/${user?.username}`} className="text-violet-400 hover:text-violet-300 transition-colors">Go to profile</Link>
            </p>
          </div>
        </div>
      )}

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

      {/* ── Postcard Export ─────────────────────────────────────────────── */}
      <div className="space-y-5">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="font-bold text-white text-lg">Export Postcard</h2>
            <p className="text-gray-500 text-sm mt-0.5">
              Download a shareable summary of your listening stats
            </p>
          </div>
          <button
            onClick={handleExport}
            disabled={exporting || postcardLoading || !postcardData}
            className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {exporting ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Exporting…
              </>
            ) : (
              <>
                <DownloadIcon />
                Download PNG
              </>
            )}
          </button>
        </div>

        {/* Time span selector */}
        <div className="flex gap-2 flex-wrap">
          {SPAN_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setPostcardSpan(opt.value)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                postcardSpan === opt.value
                  ? 'bg-violet-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Postcard preview */}
        <div className="flex justify-center">
          {postcardLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : postcardData ? (
            <div className="overflow-hidden rounded-2xl shadow-2xl shadow-violet-900/30">
              <StatsPostcard
                ref={postcardRef}
                data={postcardData}
                username={user?.username}
                timeSpan={postcardSpan}
              />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function AudioBar({ label, value, color }) {
  if (value == null) return null
  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5">
        <span className="text-gray-400">{label}</span>
        <span className="text-gray-300 font-medium">{Math.round(value * 100)}%</span>
      </div>
      <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all`}
          style={{ width: `${value * 100}%` }}
        />
      </div>
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

function DownloadIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}
