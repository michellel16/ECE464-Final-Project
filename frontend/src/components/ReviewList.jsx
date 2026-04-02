import { useState, useMemo } from 'react'
import ReviewCard from './ReviewCard'

const SORT_OPTIONS = [
  { value: 'newest',  label: 'Newest' },
  { value: 'oldest',  label: 'Oldest' },
  { value: 'highest', label: 'Highest rated' },
  { value: 'lowest',  label: 'Lowest rated' },
]

const RATING_OPTIONS = [
  { value: 0,   label: 'All ratings' },
  { value: 4.5, label: '★ 4.5+' },
  { value: 4,   label: '★ 4+' },
  { value: 3,   label: '★ 3+' },
  { value: 2,   label: '★ 2+' },
  { value: 1,   label: '★ 1+' },
]

export default function ReviewList({ reviews }) {
  const [sort, setSort]       = useState('newest')
  const [minRating, setMin]   = useState(0)
  const [onlyText, setOnlyText] = useState(false)

  const filtered = useMemo(() => {
    let list = reviews.filter(r => r.rating >= minRating)
    if (onlyText) list = list.filter(r => r.text?.trim())
    switch (sort) {
      case 'oldest':  list = [...list].sort((a, b) => new Date(a.created_at) - new Date(b.created_at)); break
      case 'highest': list = [...list].sort((a, b) => b.rating - a.rating); break
      case 'lowest':  list = [...list].sort((a, b) => a.rating - b.rating); break
      default:        list = [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    }
    return list
  }, [reviews, sort, minRating, onlyText])

  if (reviews.length === 0) return (
    <div className="card p-8 text-center text-gray-500">No reviews yet. Be the first!</div>
  )

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={sort}
          onChange={e => setSort(e.target.value)}
          className="bg-gray-900 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-violet-500"
        >
          {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <select
          value={minRating}
          onChange={e => setMin(Number(e.target.value))}
          className="bg-gray-900 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-violet-500"
        >
          {RATING_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <button
          onClick={() => setOnlyText(v => !v)}
          className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
            onlyText
              ? 'border-violet-500 text-violet-400 bg-violet-900/20'
              : 'border-gray-700 text-gray-500 hover:border-gray-500 hover:text-gray-300'
          }`}
        >
          Written only
        </button>

        {(sort !== 'newest' || minRating > 0 || onlyText) && (
          <button
            onClick={() => { setSort('newest'); setMin(0); setOnlyText(false) }}
            className="text-xs text-gray-600 hover:text-gray-400 transition-colors ml-1"
          >
            Clear filters
          </button>
        )}

        <span className="text-gray-600 text-xs ml-auto">
          {filtered.length} of {reviews.length}
        </span>
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="card p-6 text-center text-gray-500 text-sm">
          No reviews match these filters.
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(r => <ReviewCard key={r.id} review={r} />)}
        </div>
      )}
    </div>
  )
}
