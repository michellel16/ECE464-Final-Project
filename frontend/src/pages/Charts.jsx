import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import StarRating from '../components/StarRating'

const PAGE_SIZE = 25
const TABS = ['albums', 'artists', 'songs']

export default function Charts() {
  const [activeTab, setActiveTab]   = useState('albums')
  const [page, setPage]             = useState(0)
  const [items, setItems]           = useState([])
  const [total, setTotal]           = useState(0)
  const [loading, setLoading]       = useState(true)

  const [genres, setGenres]         = useState([])
  const [years, setYears]           = useState([])
  const [selectedYear, setYear]     = useState('')
  const [selectedDecade, setDecade] = useState('')
  const [selectedGenre, setGenre]   = useState('')

  useEffect(() => {
    Promise.all([
      axios.get('/api/charts/genres'),
      axios.get('/api/charts/years'),
    ]).then(([g, y]) => {
      setGenres(g.data)
      setYears(y.data)
    }).catch(() => {})
  }, [])

  const fetchItems = useCallback(() => {
    setLoading(true)
    const skip = page * PAGE_SIZE
    const params = new URLSearchParams({ limit: PAGE_SIZE, skip })
    if (selectedGenre) params.set('genre_id', selectedGenre)
    if (activeTab === 'albums') {
      if (selectedYear)   params.set('year',   selectedYear)
      if (selectedDecade) params.set('decade', selectedDecade)
    }
    axios.get(`/api/charts/${activeTab}?${params}`)
      .then(r => {
        setItems(r.data.items ?? [])
        setTotal(r.data.total ?? 0)
      })
      .catch(() => { setItems([]); setTotal(0) })
      .finally(() => setLoading(false))
  }, [activeTab, page, selectedYear, selectedDecade, selectedGenre])

  useEffect(() => { fetchItems() }, [fetchItems])

  function switchTab(tab) {
    setActiveTab(tab)
    setPage(0)
    setItems([])
  }

  function resetFilters() {
    setYear('')
    setDecade('')
    setGenre('')
    setPage(0)
  }

  const hasFilter  = selectedYear || selectedDecade || selectedGenre
  const decades    = Array.from({ length: 7 }, (_, i) => 2020 - i * 10)
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white font-display">Charts</h1>
        <p className="text-gray-400 text-sm mt-1">Top-rated music on Tunelog</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4">
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => switchTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              activeTab === tab
                ? 'bg-violet-700 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6 flex flex-wrap gap-3 items-center">
        {activeTab === 'albums' && (
          <>
            <select
              value={selectedYear}
              onChange={e => { setYear(e.target.value); setDecade(''); setPage(0) }}
              className="input text-xs py-1.5 px-3 min-w-[110px]"
            >
              <option value="">Search year...</option>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
            <select
              value={selectedDecade}
              onChange={e => { setDecade(e.target.value); setYear(''); setPage(0) }}
              className="input text-xs py-1.5 px-3 min-w-[110px]"
            >
              <option value="">Any decade</option>
              {decades.map(d => <option key={d} value={d}>{d}s</option>)}
            </select>
          </>
        )}
        <select
          value={selectedGenre}
          onChange={e => { setGenre(e.target.value); setPage(0) }}
          className="input text-xs py-1.5 px-3 min-w-[130px]"
        >
          <option value="">Search genres...</option>
          {genres.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
        {hasFilter && (
          <button onClick={resetFilters} className="text-xs text-gray-400 hover:text-white transition-colors">
            Clear filters
          </button>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="card p-12 text-center text-gray-500">
          <p className="text-lg mb-1">No {activeTab} found</p>
          <p className="text-sm">Try changing the filters, or add some reviews!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {activeTab === 'albums'  && items.map(e => <AlbumRow  key={e.album.id}  entry={e} />)}
          {activeTab === 'artists' && items.map(e => <ArtistRow key={e.artist.id} entry={e} />)}
          {activeTab === 'songs'   && items.map(e => <SongRow   key={e.song.id}   entry={e} />)}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && !loading && (
        <div className="flex items-center justify-center gap-1 mt-6 flex-wrap">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 rounded-lg text-sm border border-gray-700 text-gray-400 hover:border-violet-600 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ←
          </button>
          {pageNumbers(page, totalPages).map((n, i) =>
            n === '…' ? (
              <span key={`ellipsis-${i}`} className="px-2 py-1.5 text-gray-600 text-sm select-none">…</span>
            ) : (
              <button
                key={n}
                onClick={() => setPage(n - 1)}
                className={`w-9 py-1.5 rounded-lg text-sm border transition-colors ${
                  n - 1 === page
                    ? 'bg-violet-700 border-violet-700 text-white font-medium'
                    : 'border-gray-700 text-gray-400 hover:border-violet-600 hover:text-white'
                }`}
              >
                {n}
              </button>
            )
          )}
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 rounded-lg text-sm border border-gray-700 text-gray-400 hover:border-violet-600 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            →
          </button>
        </div>
      )}
    </div>
  )
}

function pageNumbers(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = []
  const addRange = (a, b) => { for (let i = a; i <= b; i++) pages.push(i) }
  addRange(1, Math.min(2, total))
  if (current > 4) pages.push('…')
  const lo = Math.max(3, current)
  const hi = Math.min(total - 2, current + 2)
  if (lo <= hi) addRange(lo, hi)
  if (current < total - 3) pages.push('…')
  addRange(Math.max(total - 1, 3), total)
  return [...new Set(pages)]
}

function RatingBadge({ average_rating, review_count }) {
  return (
    <div className="shrink-0 text-right">
      {review_count > 0 ? (
        <>
          <div className="flex items-center gap-1.5 justify-end">
            <StarRating value={average_rating} readonly size="sm" />
            <span className="text-white font-bold text-sm">{average_rating.toFixed(2)}</span>
          </div>
          <p className="text-gray-600 text-xs mt-0.5">{review_count} review{review_count !== 1 ? 's' : ''}</p>
        </>
      ) : (
        <p className="text-gray-600 text-xs">No reviews yet</p>
      )}
    </div>
  )
}

function RankLabel({ rank }) {
  return (
    <div className="w-8 text-right shrink-0">
      <span className={`font-bold tabular-nums ${
        rank === 1 ? 'text-yellow-400 text-lg' :
        rank === 2 ? 'text-gray-300 text-base' :
        rank === 3 ? 'text-amber-600 text-base' :
        'text-gray-600 text-sm'
      }`}>{rank}</span>
    </div>
  )
}

function GenrePills({ genres }) {
  if (!genres?.length) return null
  return (
    <div className="flex gap-1 mt-1 flex-wrap">
      {genres.slice(0, 3).map(g => (
        <span key={g.id} className="text-[10px] text-violet-400/70 bg-violet-900/20 px-1.5 py-0.5 rounded-full">
          {g.name}
        </span>
      ))}
    </div>
  )
}

function AlbumRow({ entry }) {
  const { rank, album, average_rating, review_count } = entry
  const year = album.release_date?.slice(0, 4)
  return (
    <Link to={`/albums/${album.id}`} className="card p-4 flex items-center gap-4 hover:border-violet-700 transition-colors group">
      <RankLabel rank={rank} />
      <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-800 shrink-0">
        {album.cover_url
          ? <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover" loading="lazy" />
          : <div className="w-full h-full flex items-center justify-center text-gray-600 text-lg">💿</div>}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium truncate group-hover:text-violet-400 transition-colors">{album.title}</p>
        <p className="text-gray-400 text-sm truncate">
          {album.artist?.name}
          {year && <span className="text-gray-600"> · {year}</span>}
        </p>
        <GenrePills genres={album.genres} />
      </div>
      <RatingBadge average_rating={average_rating} review_count={review_count} />
    </Link>
  )
}

function ArtistRow({ entry }) {
  const { rank, artist, average_rating, review_count } = entry
  return (
    <Link to={`/artists/${artist.id}`} className="card p-4 flex items-center gap-4 hover:border-violet-700 transition-colors group">
      <RankLabel rank={rank} />
      <div className="w-12 h-12 rounded-full overflow-hidden bg-gray-800 shrink-0">
        {artist.image_url
          ? <img src={artist.image_url} alt={artist.name} className="w-full h-full object-cover" loading="lazy" />
          : <div className="w-full h-full flex items-center justify-center text-gray-600 text-xl">🎤</div>}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium truncate group-hover:text-violet-400 transition-colors">{artist.name}</p>
        <GenrePills genres={artist.genres} />
      </div>
      <RatingBadge average_rating={average_rating} review_count={review_count} />
    </Link>
  )
}

function SongRow({ entry }) {
  const { rank, song, average_rating, review_count } = entry
  return (
    <Link to={`/songs/${song.id}`} className="card p-4 flex items-center gap-4 hover:border-violet-700 transition-colors group">
      <RankLabel rank={rank} />
      <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-800 shrink-0">
        {song.album?.cover_url
          ? <img src={song.album.cover_url} alt={song.album.title} className="w-full h-full object-cover" loading="lazy" />
          : <div className="w-full h-full flex items-center justify-center text-gray-600 text-lg">🎵</div>}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium truncate group-hover:text-violet-400 transition-colors">{song.title}</p>
        <p className="text-gray-400 text-sm truncate">
          {song.artist?.name}
          {song.album && <span className="text-gray-600"> · {song.album.title}</span>}
        </p>
      </div>
      <RatingBadge average_rating={average_rating} review_count={review_count} />
    </Link>
  )
}
