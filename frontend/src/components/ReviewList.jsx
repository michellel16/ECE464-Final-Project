import { useState, useMemo, useEffect } from 'react'
import ReviewCard from './ReviewCard'

const REVIEWS_PER_PAGE = 8

const SORT_OPTIONS = [
  { value: 'all',        label: 'All'        },
  { value: 'highest',    label: 'Highest'    },
  { value: 'lowest',     label: 'Lowest'     },
  { value: 'most_liked', label: 'Most Liked' },
  { value: 'relevance',  label: 'Relevance'  },
]

export default function ReviewList({ reviews }) {
  const [sort, setSort]         = useState('all')
  const [onlyText, setOnlyText] = useState(false)
  const [query, setQuery]       = useState('')
  const [page, setPage]         = useState(1)
  const [scrolled, setScrolled] = useState(false)

  // When reviews load in, jump to the page containing the linked review and scroll to it
  useEffect(() => {
    if (scrolled || reviews.length === 0) return
    const m = window.location.hash.match(/^#review-(\d+)$/)
    if (!m) return
    const targetId = Number(m[1])
    const sorted = [...reviews].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    const idx = sorted.findIndex(r => r.id === targetId)
    if (idx === -1) return
    setPage(Math.ceil((idx + 1) / REVIEWS_PER_PAGE))
    setScrolled(true)
    setTimeout(() => {
      document.getElementById(`review-${targetId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 120)
  }, [reviews, scrolled])

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
      case 'most_liked':
        list = list.sort((a, b) => (b.like_count ?? 0) - (a.like_count ?? 0))
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

  // Reset to page 1 whenever filters change
  useEffect(() => { setPage(1) }, [sort, onlyText, query])

  const totalPages = Math.max(1, Math.ceil(filtered.length / REVIEWS_PER_PAGE))
  const paged = filtered.slice((page - 1) * REVIEWS_PER_PAGE, page * REVIEWS_PER_PAGE)

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
            className="bg-[#0d0d1f] border border-[#2a2a45] text-gray-200 text-sm rounded pl-8 pr-7 py-2 focus:outline-none focus:border-violet-500 w-52 transition-colors placeholder-gray-500"
          />
          {query && (
            <button onClick={() => setQuery('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors">
              ✕
            </button>
          )}
        </div>

        <div className="flex gap-1 bg-[#0d0d1f] border border-[#252540] rounded p-1">
          {SORT_OPTIONS.map(o => (
            <button
              key={o.value}
              onClick={() => setSort(o.value)}
              className={`px-3 py-1.5 rounded text-xs font-medium tracking-wide transition-colors ${
                sort === o.value
                  ? 'bg-violet-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>

        <button
          onClick={() => setOnlyText(v => !v)}
          className={`px-3 py-1.5 rounded text-xs border tracking-wide transition-colors ${
            onlyText
              ? 'border-violet-500 text-violet-300 bg-violet-900/20'
              : 'border-[#252540] text-gray-400 hover:border-violet-600/50 hover:text-gray-200'
          }`}
        >
          Written only
        </button>

        {(sort !== 'all' || onlyText || query) && (
          <button
            onClick={() => { setSort('all'); setOnlyText(false); setQuery('') }}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors ml-1"
          >
            Clear filters
          </button>
        )}

      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="card p-6 text-center text-gray-500 text-sm">
          No reviews match these filters.
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {paged.map(r => <ReviewCard key={r.id} review={r} />)}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 rounded text-xs bg-[#1a1a2e] border border-[#252540] text-gray-300 hover:bg-[#252540] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                ← Prev
              </button>
              <span className="text-xs text-gray-400">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 rounded text-xs bg-[#1a1a2e] border border-[#252540] text-gray-300 hover:bg-[#252540] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
