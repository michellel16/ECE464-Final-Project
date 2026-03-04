import { Link } from 'react-router-dom'
import { Avatar } from './Navbar'
import StarRating from './StarRating'

export default function ReviewCard({ review }) {
  return (
    <div className="card p-4 space-y-2">
      <div className="flex items-center justify-between">
        <Link to={`/users/${review.username}`} className="flex items-center gap-2">
          <Avatar username={review.username} size={7} />
          <span className="text-sm font-medium text-white hover:text-violet-400 transition-colors">
            {review.username}
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <StarRating value={review.rating} readonly size="sm" />
          <span className="text-gray-500 text-xs">
            {new Date(review.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
      {review.text && (
        <p className="text-gray-300 text-sm leading-relaxed">{review.text}</p>
      )}
    </div>
  )
}
