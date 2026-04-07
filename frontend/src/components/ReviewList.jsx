import { useState, useMemo } from 'react'
import ReviewCard from './ReviewCard'

const SORT_OPTIONS = [
  { value: 'all',       label: 'All' },
  { value: 'highest',   label: 'Highest' },
  { value: 'lowest',    label: 'Lowest' },
  { value: 'relevance', label: 'Relevance' },
]

export default function ReviewList({ reviews }) {
  const [sort, setSort]         = useState('all')
  const [onlyText, setOnlyText] = useState(false)
  const [query, setQuery]       = useState('')

  const filtered = useMemo(() => {
    let list = onlyText ? reviews.filter(r => r.text?.trim()) : [...reviews]
    if (query.trim()) {
      const q = query.trim().toLowerCase()
      list = list.filter(r => r.text?.toLowerCase().includes(q))
    }
    switch (sort) {
      case 'highest':
        list = list.sort((a, b) => b.rating - a.rating)
        break
      case 'lowest':
        list = list.sort((a, b) => a.rating - b.rating)
        break
      case 'relevance':
        // Written reviews first, then by newest
        list = list.sort((a, b) => {
          const aHasText = !!(a.text?.trim())
          const bHasText = !!(b.text?.trim())
          if (aHasText !== bHasText) return bHasText - aHasText
          return new Date(b.created_at) - new Date(a.created_at)
        })
        break
      default:
        list = list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    }
    return list
  }, [reviews, sort, onlyText, query])

  if (reviews.length === 0) return (
    <div className="card p-8 text-center text-gray-500">No reviews yet. Be the first!</div>
  )

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Keyword search */}
        <div className="relative">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search reviews…"
            className="bg-gray-900 border border-gray-700 text-gray-300 text-sm rounded-lg pl-8 pr-7 py-1.5 focus:outline-none focus:border-violet-500 w-44 transition-colors"
          />
          {query && (
            <button onClick={() => setQuery('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors">
              ✕
            </button>
          )}
        </div>

        <div className="flex gap-1 bg-gray-900 rounded-lg p-1">
          {SORT_OPTIONS.map(o => (
            <button
              key={o.value}
              onClick={() => setSort(o.value)}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                sort === o.value
                  ? 'bg-violet-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>

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

        {(sort !== 'all' || onlyText || query) && (
          <button
            onClick={() => { setSort('all'); setOnlyText(false); setQuery('') }}
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
