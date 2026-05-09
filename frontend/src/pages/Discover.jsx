import { useState, useEffect, useRef } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import axios from 'axios'
import AlbumCard from '../components/AlbumCard'
import { Avatar } from '../components/Navbar'
import StarRating from '../components/StarRating'
import { useAuth } from '../contexts/AuthContext'

const LIST_TYPE_LABELS = {
  custom: 'Custom', listened: 'Listened',
  want_to_listen: 'Want to Listen', favorites: 'Favorites',
}

const ALBUM_SORTS  = [
  { key: 'top_rated',         label: 'Top Rated'        },
  { key: 'trending',          label: 'Trending'         },
  { key: 'recently_reviewed', label: 'Recently Reviewed'},
  { key: 'new_releases',      label: 'Newest'           },
  { key: 'alpha',             label: 'A–Z'              },
]
const ARTIST_SORTS = [
  { key: 'top_rated', label: 'Top Rated' },
  { key: 'trending',  label: 'Trending'  },
  { key: 'alpha',     label: 'A–Z'       },
]
const SONG_SORTS   = [
  { key: 'top_rated', label: 'Top Rated' },
  { key: 'trending',  label: 'Trending'  },
  { key: 'alpha',     label: 'A–Z'       },
]
const LIST_SORTS   = [
  { key: 'top',      label: 'Top Rated' },
  { key: 'trending', label: 'Trending'  },
]

const DECADES = Array.from({ length: 7 }, (_, i) => 2020 - i * 10)

const PAGE_SIZES = { albums: 12, artists: 10, songs: 20, lists: 12 }

function pageNumbers(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = []
  const addRange = (a, b) => { for (let i = a; i <= b; i++) pages.push(i) }
  addRange(1, Math.min(2, total))
  if (current > 4) pages.push('…')
  const lo = Math.max(3, current - 1)
  const hi = Math.min(total - 2, current + 1)
  if (lo <= hi) addRange(lo, hi)
  if (current < total - 3) pages.push('…')
  addRange(Math.max(total - 1, 3), total)
  return [...new Set(pages)]
}

export default function Discover() {
  const [searchParams] = useSearchParams()
  const { user } = useAuth()

  const initialTab  = searchParams.get('tab')  ?? 'albums'
  const initialSort = searchParams.get('sort') ?? null

  const [tab, setTab]               = useState(initialTab)
  const [albumSort, setAlbumSort]   = useState(
    initialTab === 'albums' && initialSort ? initialSort : 'top_rated'
  )
  const [artistSort, setArtistSort] = useState('trending')
  const [songSort, setSongSort]     = useState(
    initialTab === 'songs' && initialSort ? initialSort : 'top_rated'
  )
  const [listSort, setListSort]     = useState('top')

  const [genreId, setGenreId]         = useState('')
  const [year, setYear]               = useState('')
  const [decade, setDecade]           = useState('')
  const [albumSearch, setAlbumSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const searchTimer = useRef(null)

  const [genres, setGenres] = useState([])
  const [years, setYears]   = useState([])

  const [albums, setAlbums]     = useState([])
  const [albumTotal, setAlbumTotal] = useState(0)
  const [albumPage, setAlbumPage]   = useState(1)

  const [artists, setArtists]     = useState([])
  const [artistTotal, setArtistTotal] = useState(0)
  const [artistPage, setArtistPage]   = useState(1)

  const [songs, setSongs]       = useState([])
  const [songTotal, setSongTotal]   = useState(0)
  const [songPage, setSongPage]     = useState(1)

  const [lists, setLists]       = useState([])
  const [listPage, setListPage]     = useState(1)

  const [likeState, setLikeState] = useState({})
  const [forking, setForking]     = useState(null)
  const [copied, setCopied]       = useState(null)
  const [loading, setLoading]     = useState(false)

  // Debounce album search input
  useEffect(() => {
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => {
      setDebouncedSearch(albumSearch)
      setAlbumPage(1)
    }, 350)
    return () => clearTimeout(searchTimer.current)
  }, [albumSearch])

  // Load filter option data once
  useEffect(() => {
    Promise.all([axios.get('/api/charts/genres'), axios.get('/api/charts/years')])
      .then(([g, y]) => { setGenres(g.data); setYears(y.data) })
      .catch(() => {})
  }, [])

  // Fetch music content when tab/sort/filters/page change
  useEffect(() => {
    if (tab === 'lists') return
    setLoading(true)

    if (tab === 'albums') {
      const ps   = PAGE_SIZES.albums
      const skip = (albumPage - 1) * ps
      const params = new URLSearchParams({ limit: ps, skip, include_total: true, sort: albumSort })
      if (genreId) params.set('genre_id', genreId)
      if (year) params.set('year', year)
      else if (decade) params.set('decade', decade)
      if (debouncedSearch) params.set('search', debouncedSearch)
      axios.get(`/api/music/albums?${params}`)
        .then(r => { setAlbums(r.data.items); setAlbumTotal(r.data.total) })
        .finally(() => setLoading(false))
    } else if (tab === 'artists') {
      const ps   = PAGE_SIZES.artists
      const skip = (artistPage - 1) * ps
      const params = new URLSearchParams({ limit: ps, skip, include_total: true, sort: artistSort })
      if (genreId) params.set('genre_id', genreId)
      axios.get(`/api/music/artists?${params}`)
        .then(r => { setArtists(r.data.items); setArtistTotal(r.data.total) })
        .finally(() => setLoading(false))
    } else if (tab === 'songs') {
      const ps   = PAGE_SIZES.songs
      const skip = (songPage - 1) * ps
      const params = new URLSearchParams({ limit: ps, skip, include_total: true, sort: songSort })
      if (genreId) params.set('genre_id', genreId)
      axios.get(`/api/music/songs?${params}`)
        .then(r => { setSongs(r.data.items); setSongTotal(r.data.total) })
        .finally(() => setLoading(false))
    }
  }, [tab, albumSort, artistSort, songSort, genreId, year, decade, albumPage, artistPage, songPage, debouncedSearch])

  // Fetch lists separately
  useEffect(() => {
    if (tab !== 'lists') return
    setLoading(true)
    const ps   = PAGE_SIZES.lists
    const skip = (listPage - 1) * ps
    axios.get(`/api/lists/top?limit=${ps}&skip=${skip}&sort=${listSort}`)
      .then(r => {
        setLists(r.data)
        const state = {}
        r.data.forEach(l => { state[l.id] = { liked: l.is_liked, count: l.like_count } })
        setLikeState(s => ({ ...s, ...state }))
      })
      .finally(() => setLoading(false))
  }, [tab, listSort, listPage])

  function switchTab(t) {
    setTab(t)
    setYear('')
    setDecade('')
    setAlbumSearch('')
    setAlbumPage(1); setArtistPage(1); setSongPage(1); setListPage(1)
  }

  function setSort(v) {
    if (tab === 'albums')  { setAlbumSort(v);  setAlbumPage(1) }
    else if (tab === 'artists') { setArtistSort(v); setArtistPage(1) }
    else if (tab === 'songs')   { setSongSort(v);   setSongPage(1) }
    else                        { setListSort(v);   setListPage(1) }
  }

  function clearFilters() {
    setGenreId(''); setYear(''); setDecade(''); setAlbumSearch('')
    setAlbumPage(1); setArtistPage(1); setSongPage(1)
  }

  async function toggleLike(listId) {
    if (!user) return
    const prev = likeState[listId] ?? { liked: false, count: 0 }
    setLikeState(s => ({ ...s, [listId]: { liked: !prev.liked, count: prev.count + (prev.liked ? -1 : 1) } }))
    try { await axios.post(`/api/lists/${listId}/like`) }
    catch { setLikeState(s => ({ ...s, [listId]: prev })) }
  }

  async function forkList(listId) {
    if (!user || forking) return
    setForking(listId)
    try {
      await axios.post(`/api/lists/${listId}/fork`)
      setCopied(listId)
      setTimeout(() => setCopied(null), 3000)
    } catch {} finally { setForking(null) }
  }

  const sortOptions  = tab === 'albums' ? ALBUM_SORTS : tab === 'artists' ? ARTIST_SORTS : tab === 'songs' ? SONG_SORTS : LIST_SORTS
  const currentSort  = tab === 'albums' ? albumSort : tab === 'artists' ? artistSort : tab === 'songs' ? songSort : listSort
  const hasFilter    = genreId || year || decade || albumSearch
  const showYearDecade = tab === 'albums'

  const currentPage  = tab === 'albums' ? albumPage : tab === 'artists' ? artistPage : tab === 'songs' ? songPage : listPage
  const setPage      = tab === 'albums' ? setAlbumPage : tab === 'artists' ? setArtistPage : tab === 'songs' ? setSongPage : setListPage
  const pageSize     = PAGE_SIZES[tab] ?? 12
  const total        = tab === 'albums' ? albumTotal : tab === 'artists' ? artistTotal : tab === 'songs' ? songTotal : null
  const totalPages   = total !== null ? Math.max(1, Math.ceil(total / pageSize)) : null

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-1">Discover</h1>
        <p className="text-gray-400">Browse and filter music on Tunelog</p>
      </div>

      {/* Tabs (left) + Sort pills (right) — same row */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-1 bg-gray-900 rounded-xl p-1">
          {['albums', 'artists', 'songs', 'lists'].map(t => (
            <button key={t} onClick={() => switchTab(t)}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${tab === t ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white'}`}>
              {t}
            </button>
          ))}
        </div>

        <div className="flex gap-1 bg-gray-900 rounded-xl p-1">
          {sortOptions.map(({ key, label }) => (
            <button key={key} onClick={() => setSort(key)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${currentSort === key ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Filters row */}
      {tab !== 'lists' && (
        <div className="flex flex-wrap items-center gap-3">
          {tab === 'albums' && (
            <div className="relative">
              <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
              </svg>
              <input
                type="text"
                value={albumSearch}
                onChange={e => setAlbumSearch(e.target.value)}
                placeholder="Search albums…"
                className="input text-sm py-1.5 pl-8 pr-7 w-44"
              />
              {albumSearch && (
                <button onClick={() => setAlbumSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors text-xs">✕</button>
              )}
            </div>
          )}
          <select value={genreId} onChange={e => { setGenreId(e.target.value); setAlbumPage(1); setArtistPage(1); setSongPage(1) }}
            className="input text-sm py-1.5 px-3 min-w-[130px]">
            <option value="">All genres</option>
            {genres.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>

          {showYearDecade && (
            <>
              <select value={year} onChange={e => { setYear(e.target.value); setDecade(''); setAlbumPage(1) }}
                className="input text-sm py-1.5 px-3 min-w-[110px]">
                <option value="">Any year</option>
                {years.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
              <select value={decade} onChange={e => { setDecade(e.target.value); setYear(''); setAlbumPage(1) }}
                className="input text-sm py-1.5 px-3 min-w-[110px]">
                <option value="">Any decade</option>
                {DECADES.map(d => <option key={d} value={d}>{d}s</option>)}
              </select>
            </>
          )}

          {hasFilter && (
            <button onClick={clearFilters} className="text-sm text-gray-400 hover:text-white transition-colors">
              Clear filters
            </button>
          )}
        </div>
      )}

      {/* Content */}
      {loading ? <Loader /> : (
        <>
          {tab === 'albums' && (
            albums.length === 0
              ? <EmptyState />
              : albumSort === 'top_rated'
                ? <div className="space-y-2">{albums.map((al, i) => <ChartAlbumRow key={al.id} album={al} rank={(albumPage - 1) * PAGE_SIZES.albums + i + 1} />)}</div>
                : <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">{albums.map(a => <AlbumCard key={a.id} album={a} />)}</div>
          )}

          {tab === 'artists' && (
            artists.length === 0
              ? <EmptyState />
              : <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">{artists.map(a => <ArtistCard key={a.id} artist={a} />)}</div>
          )}

          {tab === 'songs' && (
            songs.length === 0
              ? <EmptyState />
              : <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{songs.map(s => <SongRow key={s.id} song={s} />)}</div>
          )}

          {tab === 'lists' && (
            <div className="space-y-5">
              {copied && (
                <div className="bg-violet-900/30 border border-violet-700/50 text-violet-300 text-sm px-4 py-2.5 rounded-lg">
                  List copied — find it in <Link to="/lists" className="underline">My Lists</Link> to edit it.
                </div>
              )}

              {lists.length === 0
                ? <EmptyState />
                : <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {lists.map(l => (
                      <ListCard key={l.id} list={l} likeState={likeState[l.id]}
                        onLike={toggleLike} onFork={forkList}
                        forking={forking} copied={copied === l.id} currentUser={user} />
                    ))}
                  </div>
              }
            </div>
          )}

          {/* Pagination */}
          {tab !== 'lists' && totalPages > 1 && (
            <Pagination current={currentPage} total={totalPages} onPage={setPage} />
          )}
          {tab === 'lists' && (lists.length === PAGE_SIZES.lists || listPage > 1) && (
            <div className="flex justify-center gap-2 pt-2">
              <button
                onClick={() => setListPage(p => Math.max(1, p - 1))}
                disabled={listPage === 1}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                ← Prev
              </button>
              <span className="px-4 py-2 text-sm text-gray-400">Page {listPage}</span>
              <button
                onClick={() => setListPage(p => p + 1)}
                disabled={lists.length < PAGE_SIZES.lists}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
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

function Pagination({ current, total, onPage }) {
  const pages = pageNumbers(current, total)
  return (
    <div className="flex justify-center items-center gap-1 pt-2 flex-wrap">
      <button
        onClick={() => onPage(p => Math.max(1, p - 1))}
        disabled={current === 1}
        className="px-3 py-2 rounded-lg text-sm font-medium bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        ←
      </button>
      {pages.map((p, i) =>
        p === '…'
          ? <span key={`ellipsis-${i}`} className="px-2 py-2 text-gray-600 text-sm">…</span>
          : <button
              key={p}
              onClick={() => onPage(p)}
              className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                p === current
                  ? 'bg-violet-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {p}
            </button>
      )}
      <button
        onClick={() => onPage(p => Math.min(total, p + 1))}
        disabled={current === total}
        className="px-3 py-2 rounded-lg text-sm font-medium bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        →
      </button>
    </div>
  )
}

function ChartAlbumRow({ album, rank }) {
  const year = album.release_date?.slice(0, 4)
  return (
    <Link to={`/albums/${album.id}`}
      className="card p-4 flex items-center gap-4 hover:border-violet-700 transition-colors group">
      <div className="w-8 text-right shrink-0">
        <span className={`font-bold tabular-nums ${
          rank === 1 ? 'text-yellow-400 text-lg' :
          rank === 2 ? 'text-gray-300 text-base' :
          rank === 3 ? 'text-amber-600 text-base' : 'text-gray-600 text-sm'
        }`}>{rank}</span>
      </div>
      <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-800 shrink-0">
        {album.cover_url
          ? <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover" loading="lazy" />
          : <div className="w-full h-full flex items-center justify-center text-gray-600 text-lg">💿</div>}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium truncate group-hover:text-violet-400 transition-colors">{album.title}</p>
        <p className="text-gray-400 text-sm truncate">
          {album.artist?.name}{year && <span className="text-gray-600"> · {year}</span>}
        </p>
        {album.genres?.length > 0 && (
          <div className="flex gap-1 mt-1 flex-wrap">
            {album.genres.slice(0, 3).map(g => (
              <span key={g.id} className="text-[10px] text-violet-400/70 bg-violet-900/20 px-1.5 py-0.5 rounded-full">{g.name}</span>
            ))}
          </div>
        )}
      </div>
      <div className="shrink-0 text-right">
        {album.review_count > 0 ? (
          <>
            <div className="flex items-center gap-1.5 justify-end">
              <StarRating value={album.average_rating} readonly size="sm" />
              <span className="text-white font-bold text-sm">{album.average_rating?.toFixed(2)}</span>
            </div>
            <p className="text-gray-600 text-xs mt-0.5">{album.review_count} review{album.review_count !== 1 ? 's' : ''}</p>
          </>
        ) : (
          <p className="text-gray-600 text-xs">No reviews yet</p>
        )}
      </div>
    </Link>
  )
}

function ArtistCard({ artist }) {
  return (
    <Link to={`/artists/${artist.id}`} className="group block text-center">
      <div className="aspect-square bg-gray-800 rounded-full overflow-hidden mb-3 mx-auto w-28 sm:w-36">
        {artist.image_url
          ? <img src={artist.image_url} alt={artist.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" />
          : <div className="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-violet-900/60 to-gray-800">🎤</div>}
      </div>
      <p className="text-white font-medium text-sm group-hover:text-violet-400 transition-colors">{artist.name}</p>
      {artist.genres?.length > 0 && (
        <p className="text-gray-500 text-xs mt-0.5 truncate px-2">{artist.genres.slice(0, 2).map(g => g.name).join(' · ')}</p>
      )}
    </Link>
  )
}

function SongRow({ song }) {
  return (
    <Link to={`/songs/${song.id}`} className="card p-3 flex items-center gap-3 hover:border-violet-700 transition-colors group">
      {song.album?.cover_url
        ? <img src={song.album.cover_url} alt="" className="w-10 h-10 rounded object-cover shrink-0" loading="lazy" />
        : <div className="w-10 h-10 rounded bg-gray-800 flex items-center justify-center text-gray-500 shrink-0">♪</div>}
      <div className="min-w-0 flex-1">
        <p className="text-white text-sm font-medium truncate group-hover:text-violet-400 transition-colors">{song.title}</p>
        <p className="text-gray-500 text-xs truncate">{song.artist?.name}{song.album ? ` · ${song.album.title}` : ''}</p>
      </div>
      {song.average_rating && (
        <span className="text-yellow-400 text-xs shrink-0">★ {song.average_rating.toFixed(1)}</span>
      )}
    </Link>
  )
}

function ListCard({ list, likeState, onLike, onFork, forking, copied, currentUser }) {
  const { liked, count } = likeState ?? { liked: list.is_liked, count: list.like_count }
  const covers  = list.cover_previews ?? []
  const isOwner = currentUser?.username === list.owner_username
  const canAct  = currentUser && !isOwner
  const isBusy  = forking === list.id

  return (
    <div className="card overflow-hidden">
      <Link to={`/lists/${list.id}`} className="block h-28 bg-gray-800 shrink-0 overflow-hidden group">
        {covers.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-3xl text-gray-700">♪</div>
        ) : covers.length === 1 ? (
          <img src={covers[0]} alt="" className="w-full h-full object-cover group-hover:opacity-90 transition-opacity" loading="lazy" />
        ) : covers.length < 4 ? (
          <div className="grid grid-cols-2 h-full">
            {covers.slice(0, 2).map((url, i) => <img key={i} src={url} alt="" className="w-full h-full object-cover group-hover:opacity-90 transition-opacity" loading="lazy" />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 grid-rows-2 h-full">
            {covers.slice(0, 4).map((url, i) => <img key={i} src={url} alt="" className="w-full h-full object-cover group-hover:opacity-90 transition-opacity" loading="lazy" />)}
          </div>
        )}
      </Link>
      <div className="p-3 space-y-2">
        <div className="flex items-start gap-2">
          <Link to={`/lists/${list.id}`} className="text-white hover:text-violet-400 transition-colors font-medium text-sm leading-snug line-clamp-1 flex-1">
            {list.name}
          </Link>
          <span className="text-[10px] text-gray-500 border border-gray-700 px-1.5 py-0.5 rounded-full shrink-0 leading-none mt-0.5">
            {LIST_TYPE_LABELS[list.list_type] ?? list.list_type}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Link to={`/users/${list.owner_username}`} className="flex items-center gap-1.5 min-w-0 flex-1" onClick={e => e.stopPropagation()}>
            <Avatar username={list.owner_username} avatarUrl={list.owner_avatar_url} size={4} />
            <span className="text-violet-400 text-xs hover:text-violet-300 transition-colors truncate">{list.owner_username}</span>
          </Link>
          <span className="text-gray-600 text-xs shrink-0">{list.item_count} item{list.item_count !== 1 ? 's' : ''}</span>
        </div>
        {canAct ? (
          <div className="flex gap-1.5 pt-0.5">
            <button onClick={() => onLike(list.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-semibold transition-all ${
                liked ? 'bg-pink-600/20 border border-pink-500/40 text-pink-400 hover:bg-pink-600/30'
                      : 'bg-gray-800/80 border border-gray-700 text-gray-300 hover:border-pink-500/40 hover:text-pink-400'
              }`}>
              <span className="leading-none">{liked ? '♥' : '♡'}</span>
              {liked ? 'Saved' : 'Save'}
              {count > 0 && <span className="text-[11px] opacity-60">· {count}</span>}
            </button>
            <button onClick={() => onFork(list.id)} disabled={isBusy || !!copied}
              className={`flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-medium border transition-all disabled:opacity-50 ${
                copied ? 'border-violet-500/40 text-violet-400 bg-violet-900/20'
                       : 'border-gray-700 text-gray-400 bg-gray-800/80 hover:border-violet-500/40 hover:text-violet-400'
              }`}
              title="Save an editable copy to your lists">
              {copied ? '✓' : isBusy ? '…' : '⎘ Copy'}
            </button>
          </div>
        ) : count > 0 && (
          <p className="text-xs text-gray-600">♥ {count} {count === 1 ? 'save' : 'saves'}</p>
        )}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="card p-12 text-center text-gray-500">
      <p className="text-lg mb-1">Nothing here yet</p>
      <p className="text-sm">Try adjusting the filters or add some content!</p>
    </div>
  )
}

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
