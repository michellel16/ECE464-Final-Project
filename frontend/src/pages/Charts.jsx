import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import StarRating from '../components/StarRating'
import { useAuth } from '../contexts/AuthContext'

export default function Charts() {
  const { user } = useAuth()
  const [albums, setAlbums]     = useState([])
  const [genres, setGenres]     = useState([])
  const [years, setYears]       = useState([])
  const [loading, setLoading]   = useState(true)
  const [backfilling, setBackfilling] = useState(false)
  const [backfillResult, setBackfillResult] = useState(null)
  const [mbStatus, setMbStatus] = useState(null)
  const pollRef = useRef(null)

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

  function startPolling() {
    if (pollRef.current) return
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await axios.get('/api/spotify/backfill-status')
        setMbStatus(data)
        if (!data.running) {
          clearInterval(pollRef.current)
          pollRef.current = null
          // Reload filters now that new genres may have been added
          const [g, y] = await Promise.all([
            axios.get('/api/charts/genres'),
            axios.get('/api/charts/years'),
          ])
          setGenres(g.data)
          setYears(y.data)
        }
      } catch { /* ignore */ }
    }, 3000)
  }

  // Clean up interval on unmount
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  async function runBackfill() {
    setBackfilling(true)
    setBackfillResult(null)
    setMbStatus(null)
    try {
      const { data } = await axios.post('/api/spotify/backfill-metadata')
      setBackfillResult(data)
      // Reload genres + years in case Spotify pass added new ones
      const [g, y] = await Promise.all([
        axios.get('/api/charts/genres'),
        axios.get('/api/charts/years'),
      ])
      setGenres(g.data)
      setYears(y.data)
      // If MusicBrainz job was kicked off, start polling
      if (data.mb_started) {
        setMbStatus({ running: true, done: 0, total: data.mb_artist_queue, genres_added: 0 })
        startPolling()
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Unknown error'
      setBackfillResult({ error: detail })
    } finally {
      setBackfilling(false)
    }
  }

  const hasFilter = selectedYear || selectedDecade || selectedGenre

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Charts</h1>
          <p className="text-gray-400 text-sm mt-1">Top-rated albums on Tunelog</p>
        </div>
        {user && (
          <div className="flex flex-col items-end gap-1">
            <button
              onClick={runBackfill}
              disabled={backfilling}
              className="text-xs px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:border-violet-600 hover:text-violet-400 transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              {backfilling ? (
                <span className="w-3 h-3 border-2 border-violet-400 border-t-transparent rounded-full animate-spin inline-block" />
              ) : (
                <span>↻</span>
              )}
              {backfilling ? 'Syncing…' : 'Sync metadata'}
            </button>
            {backfillResult && !backfillResult.error && (
              <div className="text-right">
                <p className="text-[11px] text-gray-500">
                  {backfillResult.artists_genres_synced} artists · {backfillResult.albums_genres_propagated} albums tagged · {backfillResult.albums_release_date_fixed} dates fixed
                  {!backfillResult.spotify_available && ' (Spotify offline)'}
                </p>
                {backfillResult.still_untagged_albums > 0 && (
                  <p className="text-[11px] text-yellow-600">
                    {backfillResult.still_untagged_albums} album{backfillResult.still_untagged_albums !== 1 ? 's' : ''} still untagged — Spotify may have no genre data for their artists
                  </p>
                )}
                {backfillResult.still_untagged_albums === 0 && (
                  <p className="text-[11px] text-green-600">All albums tagged</p>
                )}
              </div>
            )}
            {backfillResult?.error && (
              <p className="text-[11px] text-red-400">{backfillResult.error}</p>
            )}
            {/* MusicBrainz background job progress */}
            {mbStatus && (
              <div className="text-right mt-1">
                {mbStatus.running ? (
                  <p className="text-[11px] text-violet-400 flex items-center gap-1 justify-end">
                    <span className="w-2.5 h-2.5 border border-violet-400 border-t-transparent rounded-full animate-spin inline-block" />
                    MusicBrainz: {mbStatus.done}/{mbStatus.total} artists…
                  </p>
                ) : (
                  <p className="text-[11px] text-green-500">
                    MusicBrainz done · {mbStatus.genres_added} artists newly tagged
                  </p>
                )}
              </div>
            )}
          </div>
        )}
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
    </Link>
  )
}
