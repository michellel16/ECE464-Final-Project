import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import StarRating from '../components/StarRating'
import ReviewList from '../components/ReviewList'

const STATUS_LABELS = {
  listened:        { label: 'Listened',        emoji: '✓' },
  want_to_listen:  { label: 'Want to Listen',  emoji: '♡' },
  favorites:       { label: 'Favorites',        emoji: '★' },
}

export default function AlbumPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const [album, setAlbum]       = useState(null)
  const [reviews, setReviews]   = useState([])
  const [myReview, setMyReview] = useState(null)
  const [myStatus, setMyStatus] = useState(null)
  const [reviewDraft, setDraft] = useState({ rating: 0, text: '' })
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [addingList, setAddingList] = useState(false)
  const [myLists, setMyLists]   = useState([])
  const [playingId, setPlayingId] = useState(null)
  const audioRef = useRef(null)

  useEffect(() => {
    const fetches = [
      axios.get(`/api/music/albums/${id}`),
      axios.get(`/api/music/albums/${id}/reviews`),
    ]
    if (user) {
      fetches.push(axios.get(`/api/music/albums/${id}/my-review`))
      fetches.push(axios.get(`/api/music/albums/${id}/status`))
      fetches.push(axios.get('/api/lists/me'))
    }
    Promise.all(fetches).then(([albumRes, reviewsRes, myRevRes, statusRes, listsRes]) => {
      setAlbum(albumRes.data)
      setReviews(reviewsRes.data)
      if (myRevRes) {
        setMyReview(myRevRes.data.review)
        if (myRevRes.data.review) setDraft({ rating: myRevRes.data.review.rating, text: myRevRes.data.review.text ?? '' })
      }
      if (statusRes) setMyStatus(statusRes.data.status)
      if (listsRes) setMyLists(listsRes.data)
    }).finally(() => setLoading(false))
  }, [id, user])

  async function submitReview(e) {
    e.preventDefault()
    if (!reviewDraft.rating) return
    setSaving(true)
    try {
      const res = await axios.post(`/api/music/albums/${id}/reviews`, {
        rating: reviewDraft.rating, text: reviewDraft.text
      })
      setMyReview(res.data)
      setReviews(prev => {
        const filtered = prev.filter(r => r.user_id !== user.id)
        return [res.data, ...filtered]
      })
      // Update album average
      const updated = await axios.get(`/api/music/albums/${id}`)
      setAlbum(updated.data)
      setShowForm(false)
    } finally {
      setSaving(false)
    }
  }

  async function setStatus(status) {
    if (!user) return
    if (myStatus === status) {
      await axios.delete(`/api/music/albums/${id}/status`)
      setMyStatus(null)
    } else {
      const res = await axios.post(`/api/music/albums/${id}/status`, { status })
      setMyStatus(res.data.status)
    }
  }

  async function addToList(listId) {
    await axios.post(`/api/lists/${listId}/items`, { album_id: parseInt(id) })
    setAddingList(false)
  }

  function playPreview(songId, previewUrl) {
    if (playingId === songId) {
      audioRef.current?.pause()
      setPlayingId(null)
      return
    }
    if (audioRef.current) {
      audioRef.current.pause()
    }
    const audio = new Audio(previewUrl)
    audioRef.current = audio
    audio.play()
    setPlayingId(songId)
    audio.onended = () => setPlayingId(null)
  }

  if (loading) return <Loader />
  if (!album) return <NotFound />

  const year = album.release_date?.slice(0, 4)

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Hero */}
      <div className="flex flex-col sm:flex-row gap-6 mb-8">
        <div className="w-48 h-48 rounded-xl overflow-hidden bg-gray-800 shrink-0 shadow-2xl shadow-violet-900/30">
          {album.cover_url ? (
            <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-6xl">🎵</div>
          )}
        </div>
        <div className="flex-1 space-y-2">
          <p className="text-gray-400 text-sm uppercase tracking-wider">Album</p>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight">{album.title}</h1>
          <Link to={`/artists/${album.artist_id}`} className="text-violet-400 hover:text-violet-300 font-medium text-lg transition-colors">
            {album.artist?.name}
          </Link>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-400">
            {year && <span>{year}</span>}
            {album.genres?.map(g => (
              <span key={g.id} className="text-violet-300 bg-violet-900/30 px-2 py-0.5 rounded-full text-xs">{g.name}</span>
            ))}
          </div>

          {/* Rating summary */}
          {album.average_rating && (
            <div className="flex items-center gap-3 pt-1">
              <StarRating value={album.average_rating} readonly />
              <span className="text-gray-400 text-sm">{album.review_count} review{album.review_count !== 1 ? 's' : ''}</span>
            </div>
          )}

          {/* Action buttons */}
          {user && (
            <div className="flex flex-wrap gap-2 pt-2">
              {Object.entries(STATUS_LABELS).map(([key, { label, emoji }]) => (
                <button
                  key={key}
                  onClick={() => setStatus(key)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors border ${
                    myStatus === key
                      ? 'bg-violet-600 border-violet-600 text-white'
                      : 'border-gray-700 text-gray-400 hover:border-violet-600 hover:text-violet-400'
                  }`}
                >
                  {emoji} {label}
                </button>
              ))}
              <button
                onClick={() => setShowForm(!showForm)}
                className="px-4 py-1.5 rounded-full text-sm font-medium border border-pink-700 text-pink-400 hover:bg-pink-700/20 transition-colors"
              >
                ✏ {myReview ? 'Edit Review' : 'Write Review'}
              </button>
              <div className="relative">
                <button
                  onClick={() => setAddingList(!addingList)}
                  className="px-4 py-1.5 rounded-full text-sm font-medium border border-gray-700 text-gray-400 hover:border-violet-600 hover:text-violet-400 transition-colors"
                >
                  + Add to List
                </button>
                {addingList && myLists.length > 0 && (
                  <div className="absolute left-0 top-full mt-1 w-52 bg-gray-900 border border-gray-700 rounded-xl shadow-xl py-1 z-10">
                    {myLists.map(l => (
                      <button
                        key={l.id}
                        onClick={() => addToList(l.id)}
                        className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white"
                      >
                        {l.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Review form */}
      {showForm && user && (
        <form onSubmit={submitReview} className="card p-5 mb-6 space-y-4">
          <h3 className="font-semibold text-white">Your Review</h3>
          <div>
            <p className="text-sm text-gray-400 mb-2">Rating</p>
            <StarRating
              value={reviewDraft.rating}
              onChange={v => setDraft(d => ({ ...d, rating: v }))}
              size="lg"
            />
          </div>
          <textarea
            className="input resize-none"
            rows={4}
            placeholder="Share your thoughts about this album…"
            value={reviewDraft.text}
            onChange={e => setDraft(d => ({ ...d, text: e.target.value }))}
          />
          <div className="flex gap-3">
            <button type="submit" disabled={!reviewDraft.rating || saving} className="btn-primary disabled:opacity-60">
              {saving ? 'Saving…' : 'Save Review'}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      {/* Description */}
      {album.description && (
        <div className="text-gray-400 text-sm leading-relaxed mb-8 max-w-2xl">{album.description}</div>
      )}

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Track listing */}
        <div className="lg:col-span-1">
          <h2 className="text-lg font-bold text-white mb-3">Tracklist</h2>
          <div className="card divide-y divide-gray-800">
            {album.songs?.map(s => (
              <div key={s.id} className="flex items-center gap-3 px-4 py-3 hover:bg-gray-800/50 transition-colors group">
                {s.spotify_preview_url ? (
                  <button
                    onClick={() => playPreview(s.id, s.spotify_preview_url)}
                    className="w-6 h-6 flex items-center justify-center rounded-full bg-violet-600 hover:bg-violet-500 transition-colors shrink-0"
                    title={playingId === s.id ? 'Pause preview' : 'Play 30s preview'}
                  >
                    {playingId === s.id ? (
                      <svg viewBox="0 0 24 24" className="w-3 h-3 fill-white"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                    ) : (
                      <svg viewBox="0 0 24 24" className="w-3 h-3 fill-white"><polygon points="5,3 19,12 5,21"/></svg>
                    )}
                  </button>
                ) : (
                  <span className="text-gray-600 text-xs w-6 text-right shrink-0">{s.track_number}</span>
                )}
                <Link to={`/songs/${s.id}`} className="text-white text-sm flex-1 group-hover:text-violet-400 transition-colors">{s.title}</Link>
                <span className="text-gray-600 text-xs">{formatDuration(s.duration_seconds)}</span>
                {s.average_rating && (
                  <span className="text-yellow-500 text-xs font-bold">★{s.average_rating}</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Reviews */}
        <div className="lg:col-span-2">
          <h2 className="text-lg font-bold text-white mb-3">Reviews</h2>
          <ReviewList reviews={reviews} />
        </div>
      </div>
    </div>
  )
}

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
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
      <p>Album not found.</p>
      <Link to="/discover" className="link-purple mt-2 inline-block">Back to Discover</Link>
    </div>
  )
}
