import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import axios from 'axios'
import AlbumCard from '../components/AlbumCard'
import { Avatar } from '../components/Navbar'
import { useAuth } from '../contexts/AuthContext'

const LIST_TYPE_LABELS = {
  custom: 'Custom', listened: 'Listened',
  want_to_listen: 'Want to Listen', favorites: 'Favorites',
}

export default function Discover() {
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const [albums, setAlbums]   = useState([])
  const [artists, setArtists] = useState([])
  const [songs, setSongs]     = useState([])
  const [lists, setLists]     = useState([])
  const [likeState, setLikeState]   = useState({})
  const [listSort, setListSort]     = useState('trending')
  const [listsLoading, setListsLoading] = useState(false)
  const [forking, setForking]       = useState(null)
  const [copied, setCopied]         = useState(null)
  const [tab, setTab]   = useState(searchParams.get('tab') ?? 'albums')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      axios.get('/api/music/albums?limit=50'),
      axios.get('/api/music/artists?limit=50'),
      axios.get('/api/music/songs?limit=50'),
    ]).then(([albumsRes, artistsRes, songsRes]) => {
      setAlbums(albumsRes.data)
      setArtists(artistsRes.data)
      setSongs(songsRes.data)
    }).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (tab !== 'lists') return
    setListsLoading(true)
    setLists([])
    axios.get(`/api/lists/top?limit=24&sort=${listSort}`)
      .then(r => {
        setLists(r.data)
        const state = {}
        r.data.forEach(l => { state[l.id] = { liked: l.is_liked, count: l.like_count } })
        setLikeState(s => ({ ...s, ...state }))
      })
      .finally(() => setListsLoading(false))
  }, [tab, listSort])

  async function toggleLike(listId) {
    if (!user) return
    const prev = likeState[listId] ?? { liked: false, count: 0 }
    setLikeState(s => ({
      ...s,
      [listId]: { liked: !prev.liked, count: prev.count + (prev.liked ? -1 : 1) },
    }))
    try {
      await axios.post(`/api/lists/${listId}/like`)
    } catch {
      setLikeState(s => ({ ...s, [listId]: prev }))
    }
  }

  async function forkList(listId) {
    if (!user || forking) return
    setForking(listId)
    try {
      await axios.post(`/api/lists/${listId}/fork`)
      setCopied(listId)
      setTimeout(() => setCopied(null), 3000)
    } catch {
      // silent — list might already be owned by user
    } finally {
      setForking(null)
    }
  }

  if (loading) return <Loader />

  const TABS = ['albums', 'artists', 'songs', 'lists']

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-1">Discover</h1>
        <p className="text-gray-400">Browse all music on Tunelog</p>
      </div>

      <div className="flex gap-1 bg-gray-900 rounded-xl p-1 w-fit">
        {TABS.map(t => (
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

      {tab === 'albums' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {albums.map(a => <AlbumCard key={a.id} album={a} />)}
        </div>
      )}

      {tab === 'artists' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {artists.map(a => <ArtistCard key={a.id} artist={a} />)}
        </div>
      )}

      {tab === 'songs' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {songs.map(s => <SongRow key={s.id} song={s} />)}
        </div>
      )}

      {tab === 'lists' && (
        <div className="space-y-5">
          {/* Sort toggle + description */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex gap-1 bg-gray-900 rounded-xl p-1">
              {[
                ['trending', '🔥 Trending'],
                ['top',      '⭐ All Time Best'],
              ].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setListSort(key)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    listSort === key
                      ? 'bg-violet-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <p className="text-gray-500 text-sm">
              {listSort === 'trending'
                ? 'Most saves in the last 30 days'
                : 'Most saved lists of all time'}
            </p>
          </div>

          {copied && (
            <div className="bg-violet-900/30 border border-violet-700/50 text-violet-300 text-sm px-4 py-2.5 rounded-lg">
              List copied to your account — find it in <Link to="/lists" className="underline">My Lists</Link> to edit it.
            </div>
          )}

          {listsLoading ? (
            <Loader />
          ) : lists.length === 0 ? (
            <div className="card p-12 text-center text-gray-500">
              <p className="text-lg mb-1">No public lists yet</p>
              <p className="text-sm">Be the first to create and share a list!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {lists.map(l => (
                <ListCard
                  key={l.id}
                  list={l}
                  likeState={likeState[l.id]}
                  onLike={toggleLike}
                  onFork={forkList}
                  forking={forking}
                  copied={copied === l.id}
                  currentUser={user}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
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
      {/* Cover collage — clickable, links to detail page */}
      <Link to={`/lists/${list.id}`} className="block h-28 bg-gray-800 shrink-0 overflow-hidden group">
        {covers.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-3xl text-gray-700">♪</div>
        ) : covers.length === 1 ? (
          <img src={covers[0]} alt="" className="w-full h-full object-cover group-hover:opacity-90 transition-opacity" loading="lazy" />
        ) : covers.length < 4 ? (
          <div className="grid grid-cols-2 h-full">
            {covers.slice(0, 2).map((url, i) => (
              <img key={i} src={url} alt="" className="w-full h-full object-cover group-hover:opacity-90 transition-opacity" loading="lazy" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 grid-rows-2 h-full">
            {covers.slice(0, 4).map((url, i) => (
              <img key={i} src={url} alt="" className="w-full h-full object-cover group-hover:opacity-90 transition-opacity" loading="lazy" />
            ))}
          </div>
        )}
      </Link>

      {/* Content — completely separate from cover */}
      <div className="p-3 space-y-2">
        {/* Title (clickable) + type badge on same row */}
        <div className="flex items-start gap-2">
          <Link to={`/lists/${list.id}`} className="text-white hover:text-violet-400 transition-colors font-medium text-sm leading-snug line-clamp-1 flex-1">
            {list.name}
          </Link>
          <span className="text-[10px] text-gray-500 border border-gray-700 px-1.5 py-0.5 rounded-full shrink-0 leading-none mt-0.5">
            {LIST_TYPE_LABELS[list.list_type] ?? list.list_type}
          </span>
        </div>

        {/* Owner row */}
        <div className="flex items-center gap-2">
          <Link
            to={`/users/${list.owner_username}`}
            className="flex items-center gap-1.5 min-w-0 flex-1"
            onClick={e => e.stopPropagation()}
          >
            <Avatar username={list.owner_username} avatarUrl={list.owner_avatar_url} size={4} />
            <span className="text-violet-400 text-xs hover:text-violet-300 transition-colors truncate">
              {list.owner_username}
            </span>
          </Link>
          <span className="text-gray-600 text-xs shrink-0">
            {list.item_count} item{list.item_count !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Actions */}
        {canAct ? (
          <div className="flex gap-1.5 pt-0.5">
            <button
              onClick={() => onLike(list.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-semibold transition-all ${
                liked
                  ? 'bg-pink-600/20 border border-pink-500/40 text-pink-400 hover:bg-pink-600/30'
                  : 'bg-gray-800/80 border border-gray-700 text-gray-300 hover:border-pink-500/40 hover:text-pink-400'
              }`}
            >
              <span className="leading-none">{liked ? '♥' : '♡'}</span>
              {liked ? 'Saved' : 'Save'}
              {count > 0 && <span className="text-[11px] opacity-60">· {count}</span>}
            </button>

            <button
              onClick={() => onFork(list.id)}
              disabled={isBusy || !!copied}
              className={`flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-medium border transition-all disabled:opacity-50 ${
                copied
                  ? 'border-violet-500/40 text-violet-400 bg-violet-900/20'
                  : 'border-gray-700 text-gray-400 bg-gray-800/80 hover:border-violet-500/40 hover:text-violet-400'
              }`}
              title="Save an editable copy to your lists"
            >
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

function ArtistCard({ artist }) {
  return (
    <Link to={`/artists/${artist.id}`} className="group block text-center">
      <div className="aspect-square bg-gray-800 rounded-full overflow-hidden mb-3 mx-auto w-28 sm:w-36">
        {artist.image_url ? (
          <img src={artist.image_url} alt={artist.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-violet-900/60 to-gray-800">🎤</div>
        )}
      </div>
      <p className="text-white font-medium text-sm group-hover:text-violet-400 transition-colors">{artist.name}</p>
    </Link>
  )
}

function SongRow({ song }) {
  return (
    <Link to={`/songs/${song.id}`} className="card p-3 flex items-center gap-3 hover:border-violet-700 transition-colors group">
      {song.album?.cover_url ? (
        <img src={song.album.cover_url} alt="" className="w-10 h-10 rounded object-cover shrink-0" loading="lazy" />
      ) : (
        <div className="w-10 h-10 rounded bg-gray-800 flex items-center justify-center text-gray-500 shrink-0">♪</div>
      )}
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

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
