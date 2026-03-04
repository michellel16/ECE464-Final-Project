import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { Avatar } from '../components/Navbar'
import StarRating from '../components/StarRating'

export default function Profile() {
  const { username } = useParams()
  const { user: me } = useAuth()
  const [profile, setProfile]     = useState(null)
  const [reviews, setReviews]     = useState([])
  const [lists, setLists]         = useState([])
  const [isFollowing, setFollowing] = useState(false)
  const [tab, setTab]             = useState('reviews')
  const [loading, setLoading]     = useState(true)
  const [followLoading, setFL]    = useState(false)

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
    </div>
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
