import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import StarRating from '../components/StarRating'
import ReviewCard from '../components/ReviewCard'

export default function SongPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const [song, setSong]         = useState(null)
  const [reviews, setReviews]   = useState([])
  const [myReview, setMyReview] = useState(null)
  const [myStatus, setMyStatus] = useState(null)
  const [draft, setDraft]       = useState({ rating: 0, text: '' })
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving]     = useState(false)
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    const fetches = [
      axios.get(`/api/music/songs/${id}`),
      axios.get(`/api/music/songs/${id}/reviews`),
    ]
    if (user) {
      fetches.push(axios.get(`/api/music/songs/${id}/my-review`))
      fetches.push(axios.get(`/api/music/songs/${id}/status`))
    }
    Promise.all(fetches).then(([sRes, rRes, myRevRes, statusRes]) => {
      setSong(sRes.data)
      setReviews(rRes.data)
      if (myRevRes?.data.review) {
        setMyReview(myRevRes.data.review)
        setDraft({ rating: myRevRes.data.review.rating, text: myRevRes.data.review.text ?? '' })
      }
      if (statusRes) setMyStatus(statusRes.data.status)
    }).finally(() => setLoading(false))
  }, [id, user])

  async function submitReview(e) {
    e.preventDefault()
    if (!draft.rating) return
    setSaving(true)
    try {
      const res = await axios.post(`/api/music/songs/${id}/reviews`, {
        rating: draft.rating, text: draft.text
      })
      setMyReview(res.data)
      setReviews(prev => [res.data, ...prev.filter(r => r.user_id !== user.id)])
      const updated = await axios.get(`/api/music/songs/${id}`)
      setSong(updated.data)
      setShowForm(false)
    } finally {
      setSaving(false)
    }
  }

  async function setStatus(status) {
    if (!user) return
    if (myStatus === status) {
      await axios.delete(`/api/music/songs/${id}/status`)
      setMyStatus(null)
    } else {
      const res = await axios.post(`/api/music/songs/${id}/status`, { status })
      setMyStatus(res.data.status)
    }
  }

  if (loading) return <Loader />
  if (!song) return <NotFound />

  const hasFeatures = song.energy != null

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex gap-5 mb-6 items-start">
        <div className="w-24 h-24 rounded-lg overflow-hidden bg-gray-800 shrink-0 shadow-lg">
          {song.album?.cover_url ? (
            <img src={song.album.cover_url} alt={song.album.title} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-3xl">🎵</div>
          )}
        </div>
        <div>
          <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">Song</p>
          <h1 className="text-3xl font-extrabold text-white">{song.title}</h1>
          <Link to={`/artists/${song.artist_id}`} className="text-violet-400 hover:text-violet-300 font-medium transition-colors">
            {song.artist?.name}
          </Link>
          {song.album && (
            <div className="text-gray-500 text-sm mt-0.5">
              from{' '}
              <Link to={`/albums/${song.album_id}`} className="text-gray-300 hover:text-white transition-colors">
                {song.album.title}
              </Link>
            </div>
          )}
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
            {song.track_number && <span>Track {song.track_number}</span>}
            {song.duration_seconds && <span>{formatDuration(song.duration_seconds)}</span>}
            {song.spotify_id && (
              <a
                href={`https://open.spotify.com/track/${song.spotify_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-green-500 hover:text-green-400 transition-colors text-xs font-medium"
              >
                <SpotifyIcon /> Spotify
              </a>
            )}
          </div>
          {song.average_rating && (
            <div className="flex items-center gap-2 mt-2">
              <StarRating value={song.average_rating} readonly />
              <span className="text-gray-400 text-sm">{song.review_count} review{song.review_count !== 1 ? 's' : ''}</span>
            </div>
          )}
        </div>
      </div>

      {/* Spotify Embed Player */}
      {song.spotify_id && (
        <div className="mb-6">
          <iframe
            src={`https://open.spotify.com/embed/track/${song.spotify_id}?utm_source=generator&theme=0`}
            width="100%"
            height="152"
            frameBorder="0"
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
            className="rounded-xl"
          />
        </div>
      )}

      {/* Audio Features */}
      {hasFeatures && (
        <div className="card p-5 mb-6">
          <h2 className="font-bold text-white mb-4 flex items-center gap-2">
            <SpotifyIcon className="text-green-500" /> Sound Profile
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
            <FeatureBar label="Energy"           value={song.energy}           color="from-orange-500 to-red-500" />
            <FeatureBar label="Danceability"     value={song.danceability}     color="from-pink-500 to-violet-500" />
            <FeatureBar label="Positivity"       value={song.valence}          color="from-yellow-400 to-green-500" />
            <FeatureBar label="Acousticness"     value={song.acousticness}     color="from-blue-400 to-teal-500" />
            <FeatureBar label="Instrumentalness" value={song.instrumentalness} color="from-violet-500 to-indigo-500" />
            {song.tempo && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-400">Tempo</span>
                <span className="text-white font-medium">{Math.round(song.tempo)} BPM</span>
              </div>
            )}
            {song.loudness != null && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-400">Loudness</span>
                <span className="text-white font-medium">{song.loudness.toFixed(1)} dB</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Status + review actions */}
      {user && (
        <div className="flex flex-wrap gap-2 mb-6">
          {[
            { key: 'listened',       label: '✓ Listened' },
            { key: 'want_to_listen', label: '♡ Want to Listen' },
            { key: 'favorites',      label: '★ Favorite' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setStatus(key)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors border ${
                myStatus === key
                  ? 'bg-violet-600 border-violet-600 text-white'
                  : 'border-gray-700 text-gray-400 hover:border-violet-600 hover:text-violet-400'
              }`}
            >
              {label}
            </button>
          ))}
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-1.5 rounded-full text-sm font-medium border border-pink-700 text-pink-400 hover:bg-pink-700/20 transition-colors"
          >
            ✏ {myReview ? 'Edit Review' : 'Write Review'}
          </button>
        </div>
      )}

      {/* Review form */}
      {showForm && (
        <form onSubmit={submitReview} className="card p-5 mb-6 space-y-4">
          <h3 className="font-semibold text-white">Your Review</h3>
          <StarRating
            value={draft.rating}
            onChange={v => setDraft(d => ({ ...d, rating: v }))}
            size="lg"
          />
          <textarea
            className="input resize-none"
            rows={4}
            placeholder="What do you think of this track?"
            value={draft.text}
            onChange={e => setDraft(d => ({ ...d, text: e.target.value }))}
          />
          <div className="flex gap-3">
            <button type="submit" disabled={!draft.rating || saving} className="btn-primary disabled:opacity-60">
              {saving ? 'Saving…' : 'Save Review'}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      {/* Reviews */}
      <h2 className="text-lg font-bold text-white mb-3">Reviews</h2>
      {reviews.length === 0 ? (
        <div className="card p-8 text-center text-gray-500">No reviews yet.</div>
      ) : (
        <div className="space-y-3">
          {reviews.map(r => <ReviewCard key={r.id} review={r} />)}
        </div>
      )}
    </div>
  )
}

function FeatureBar({ label, value, color }) {
  if (value == null) return null
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-gray-300">{Math.round(value * 100)}%</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
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
    <svg viewBox="0 0 24 24" className={`w-4 h-4 fill-current ${className}`} xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
    </svg>
  )
}

function formatDuration(sec) {
  if (!sec) return ''
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`
}

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function NotFound() {
  return (
    <div className="text-center py-20 text-gray-500">
      <p>Song not found.</p>
      <Link to="/discover" className="link-purple mt-2 inline-block">Back to Discover</Link>
    </div>
  )
}
