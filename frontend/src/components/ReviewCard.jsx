import { useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Avatar } from './Navbar'
import StarRating from './StarRating'
import { useAuth } from '../contexts/AuthContext'

export default function ReviewCard({ review: initial }) {
  const { user } = useAuth()
  const [likeCount, setLikeCount] = useState(initial.like_count ?? 0)
  const [liked, setLiked] = useState(initial.liked_by_me ?? false)
  const [toggling, setToggling] = useState(false)

  async function toggleLike() {
    if (!user || toggling) return
    setToggling(true)
    // Optimistic update
    setLiked(l => !l)
    setLikeCount(c => liked ? c - 1 : c + 1)
    try {
      const { data } = await axios.post(`/api/music/reviews/${initial.id}/like`)
      setLiked(data.liked)
      setLikeCount(data.like_count)
    } catch {
      // Revert on error
      setLiked(l => !l)
      setLikeCount(c => liked ? c + 1 : c - 1)
    } finally {
      setToggling(false)
    }
  }

  return (
    <div className="card p-4 space-y-2">
      <div className="flex items-center justify-between">
        <Link to={`/users/${initial.username}`} className="flex items-center gap-2">
          <Avatar username={initial.username} avatarUrl={initial.avatar_url} size={7} />
          <span className="text-sm font-medium text-white hover:text-violet-400 transition-colors">
            {initial.username}
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <StarRating value={initial.rating} readonly size="sm" />
          <span className="text-gray-500 text-xs">
            {new Date(initial.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {initial.text && (
        <p className="text-gray-300 text-sm leading-relaxed">{initial.text}</p>
      )}

      {/* Like button — only shown when logged in */}
      <div className="flex items-center pt-1">
        <button
          onClick={toggleLike}
          disabled={!user || toggling}
          className={`flex items-center gap-1.5 text-xs transition-colors ${
            !user
              ? 'text-gray-700 cursor-default'
              : liked
              ? 'text-pink-400 hover:text-pink-300'
              : 'text-gray-600 hover:text-pink-400'
          }`}
          title={user ? (liked ? 'Unlike' : 'Like this review') : 'Sign in to like'}
        >
          <HeartIcon filled={liked} />
          {likeCount > 0 && <span>{likeCount}</span>}
        </button>
      </div>
    </div>
  )
}

function HeartIcon({ filled }) {
  return filled ? (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  )
}
