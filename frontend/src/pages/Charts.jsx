import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import StarRating from '../components/StarRating'

export default function Charts() {
  const [albums, setAlbums]     = useState([])
  const [genres, setGenres]     = useState([])
  const [years, setYears]       = useState([])
  const [loading, setLoading]   = useState(true)

  const [selectedYear, setYear]   = useState('')
  const [selectedDecade, setDecade] = useState('')
  const [selectedGenre, setGenre] = useState('')

  useEffect(() => {
    Promise.all([
      axios.get('/api/charts/genres'),
      axios.get('/api/charts/years'),
    ]).then(([g, y]) => {
      setGenres(g.data)
      setYears(y.data)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ limit: 50 })
    if (selectedYear)   params.set('year',     selectedYear)
    if (selectedDecade) params.set('decade',   selectedDecade)
    if (selectedGenre)  params.set('genre_id', selectedGenre)
    axios.get(`/api/charts/albums?${params}`)
      .then(r => setAlbums(r.data))
      .finally(() => setLoading(false))
  }, [selectedYear, selectedDecade, selectedGenre])

  const decades = Array.from({ length: 7 }, (_, i) => 2020 - i * 10)

  function resetFilters() {
    setYear('')
    setDecade('')
    setGenre('')
  }

  const hasFilter = selectedYear || selectedDecade || selectedGenre

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Charts</h1>
        <p className="text-gray-400 text-sm mt-1">Top-rated albums on Tunelog</p>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6 flex flex-wrap gap-3 items-center">
        <select
          value={selectedYear}
          onChange={e => { setYear(e.target.value); setDecade('') }}
          className="input text-sm py-1.5 px-3 min-w-[110px]"
        >
          <option value="">Any year</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>

        <select
          value={selectedDecade}
          onChange={e => { setDecade(e.target.value); setYear('') }}
          className="input text-sm py-1.5 px-3 min-w-[110px]"
        >
          <option value="">Any decade</option>
          {decades.map(d => <option key={d} value={d}>{d}s</option>)}
        </select>

        <select
          value={selectedGenre}
          onChange={e => setGenre(e.target.value)}
          className="input text-sm py-1.5 px-3 min-w-[130px]"
        >
          <option value="">All genres</option>
          {genres.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>

        {hasFilter && (
          <button
            onClick={resetFilters}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : albums.length === 0 ? (
        <div className="card p-12 text-center text-gray-500">
          <p className="text-lg mb-1">No albums found</p>
          <p className="text-sm">Try changing the filters, or add some reviews!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {albums.map((entry, i) => (
            <ChartRow key={entry.album.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  )
}

function ChartRow({ entry }) {
  const { rank, album, average_rating, review_count } = entry
  const year = album.release_date?.slice(0, 4)

  return (
    <Link
      to={`/albums/${album.id}`}
      className="card p-4 flex items-center gap-4 hover:border-violet-700 transition-colors group"
    >
      {/* Rank */}
      <div className="w-8 text-right shrink-0">
        <span className={`font-bold tabular-nums ${
          rank === 1 ? 'text-yellow-400 text-lg' :
          rank === 2 ? 'text-gray-300 text-base' :
          rank === 3 ? 'text-amber-600 text-base' :
          'text-gray-600 text-sm'
        }`}>
          {rank}
        </span>
      </div>

      {/* Cover */}
      <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-800 shrink-0">
        {album.cover_url ? (
          <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-600 text-lg">💿</div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium truncate group-hover:text-violet-400 transition-colors">
          {album.title}
        </p>
        <p className="text-gray-400 text-sm truncate">
          {album.artist?.name}
          {year && <span className="text-gray-600"> · {year}</span>}
        </p>
        {album.genres?.length > 0 && (
          <div className="flex gap-1 mt-1 flex-wrap">
            {album.genres.slice(0, 3).map(g => (
              <span key={g.id} className="text-[10px] text-violet-400/70 bg-violet-900/20 px-1.5 py-0.5 rounded-full">
                {g.name}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Rating */}
      <div className="shrink-0 text-right">
        <div className="flex items-center gap-1.5 justify-end">
          <StarRating value={average_rating} readonly size="sm" />
          <span className="text-white font-bold text-sm">{average_rating.toFixed(2)}</span>
        </div>
        <p className="text-gray-600 text-xs mt-0.5">{review_count} review{review_count !== 1 ? 's' : ''}</p>
      </div>
    </Link>
  )
}
