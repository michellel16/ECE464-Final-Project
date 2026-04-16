import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { Avatar } from '../components/Navbar'
import AlbumCard from '../components/AlbumCard'

export default function Home() {
  const { user } = useAuth()
  const [albums, setAlbums]                     = useState([])
  const [artists, setArtists]                   = useState([])
  const [songs, setSongs]                       = useState([])
  const [feed, setFeed]                         = useState([])
  const [recommended, setRecommended]           = useState([])
  const [recommendedArtists, setRecArtists]     = useState([])
  const [forYouAlbums, setForYouAlbums]         = useState([])
  const [forYouSongs, setForYouSongs]           = useState([])
  const [forYouSource, setForYouSource]         = useState(null)
  const [suggested, setSuggested]               = useState([])
  const [loading, setLoading]                   = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      axios.get('/api/music/albums?limit=12&sort=recently_reviewed'),
      axios.get('/api/music/artists?limit=12&sort=recently_reviewed'),
      axios.get('/api/music/songs?limit=6&sort=recently_reviewed'),
    ]).then(([albumsRes, artistsRes, songsRes]) => {
      setAlbums(albumsRes.data)
      setArtists(artistsRes.data)
      setSongs(songsRes.data)
    }).finally(() => setLoading(false))

    if (user) {
      axios.get(`/api/users/${user.username}/activity?limit=15`)
        .then(r => setFeed(r.data))
        .catch(() => {})
      axios.get('/api/music/recommended?song_limit=8')
        .then(r => { setRecommended(r.data.songs); setRecArtists(r.data.artists) })
        .catch(() => {})
      axios.get('/api/recommendations/me?album_limit=6&song_limit=6')
        .then(r => {
          setForYouAlbums(r.data.albums)
          setForYouSongs(r.data.songs)
          setForYouSource(r.data.source)
        })
        .catch(() => {})
      axios.get('/api/users/suggested?limit=5')
        .then(r => setSuggested(r.data))
        .catch(() => {})
    }
  }, [user])

  if (loading) return <PageLoader />

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-14">

      {/* Hero for guests */}
      {!user && (
        <section className="relative text-center py-20 rounded-2xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-900/40 via-gray-950 to-pink-900/20 pointer-events-none" />
          <div className="relative space-y-5">
            <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight">
              <span className="bg-gradient-to-r from-violet-400 via-pink-400 to-violet-400 bg-clip-text text-transparent">
                Your Music Journal
              </span>
            </h1>
            <p className="text-gray-400 text-xl max-w-2xl mx-auto">
              Rate albums, write reviews, build catalogs, and share your taste with the world.
            </p>
            <div className="flex items-center justify-center gap-4 pt-2">
              <Link to="/register" className="btn-primary text-base px-8 py-3">Get Started</Link>
              <Link to="/login" className="btn-secondary text-base px-8 py-3">Sign in</Link>
            </div>
          </div>
        </section>
      )}

      {/* Artists */}
      <section>
        <SectionHeader title="Recently Reviewed Artists" href="/discover?tab=artists" />
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4">
          {artists.map(a => <ArtistCard key={a.id} artist={a} />)}
        </div>
      </section>

      {/* Albums */}
      <section>
        <SectionHeader title="Recently Reviewed Albums" href="/discover?tab=albums" />
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
          {albums.map(a => <AlbumCard key={a.id} album={a} />)}
        </div>
      </section>

      {/* Songs */}
      <section>
        <SectionHeader title="Recently Reviewed Songs" href="/discover?tab=songs" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {songs.map(s => <SongRow key={s.id} song={s} />)}
        </div>
      </section>

      {/* Albums For You — vector-based */}
      {user && forYouAlbums.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-bold text-white">Albums For You</h2>
              <p className="text-gray-500 text-sm mt-0.5">
                {forYouSource === 'embedding'
                  ? 'Matched to your taste using semantic similarity'
                  : 'Top picks from the Tunelog community'}
              </p>
            </div>
            {forYouSource === 'embedding' && (
              <span className="text-xs text-violet-400/70 bg-violet-900/20 border border-violet-800/40 rounded-full px-3 py-1">
                AI-powered
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
            {forYouAlbums.map(a => <ForYouAlbumCard key={a.id} album={a} />)}
          </div>
        </section>
      )}

      {/* Songs For You — vector-based */}
      {user && forYouSongs.length > 0 && (
        <section>
          <div className="mb-5">
            <h2 className="text-xl font-bold text-white">Songs For You</h2>
            <p className="text-gray-500 text-sm mt-0.5">
              {forYouSource === 'embedding'
                ? 'Discovered via your taste profile'
                : 'Trending on Tunelog'}
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {forYouSongs.map(s => <ForYouSongRow key={s.id} song={s} />)}
          </div>
        </section>
      )}

      {/* Recommended Artists */}
      {user && recommendedArtists.length > 0 && (
        <section>
          <div className="mb-5">
            <h2 className="text-xl font-bold text-white">Recommended Artists</h2>
            <p className="text-gray-500 text-sm mt-0.5">Artists you might enjoy based on your taste</p>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4">
            {recommendedArtists.map(a => <RecommendedArtistCard key={a.id} artist={a} />)}
          </div>
        </section>
      )}

      {/* Recommended Songs */}
      {user && recommended.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-bold text-white">Recommended Songs</h2>
              <p className="text-gray-500 text-sm mt-0.5">Picked for you based on your taste</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {recommended.map(s => <RecommendedSongRow key={s.id} song={s} />)}
          </div>
        </section>
      )}

      {/* Suggested users */}
      {user && suggested.length > 0 && (
        <section>
          <SectionHeader title="People to Follow" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {suggested.map(u => <SuggestedUserCard key={u.id} user={u} />)}
          </div>
        </section>
      )}

      {/* Activity feed */}
      {user && (
        <section>
          <h2 className="text-xl font-bold text-white mb-5">Your Activity</h2>
          {feed.length === 0 ? (
            <div className="card p-10 text-center text-gray-500">
              <p className="mb-2">No activity yet.</p>
              <p><Link to="/discover" className="link-purple">Start exploring music →</Link></p>
            </div>
          ) : (
            <div className="space-y-3">
              {feed.map(a => <ActivityItem key={a.id} item={a} />)}
            </div>
          )}
        </section>
      )}
    </div>
  )
}

function SectionHeader({ title, href }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <h2 className="text-xl font-bold text-white">{title}</h2>
      {href && <Link to={href} className="text-sm text-violet-400 hover:text-violet-300 transition-colors">See more →</Link>}
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

function RecommendedArtistCard({ artist }) {
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
      {artist.reason && (
        <p className="text-violet-400/70 text-xs mt-0.5 truncate px-1">{artist.reason}</p>
      )}
    </Link>
  )
}

function RecommendedSongRow({ song }) {
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
        {song.reason && (
          <p className="text-violet-400/70 text-xs truncate mt-0.5">{song.reason}</p>
        )}
      </div>
      {song.average_rating && (
        <span className="text-yellow-400 text-xs shrink-0">★ {song.average_rating.toFixed(1)}</span>
      )}
    </Link>
  )
}

function SuggestedUserCard({ user: u }) {
  const [following, setFollowing] = useState(false)
  const [loading, setLoading] = useState(false)

  async function follow() {
    if (loading || following) return
    setLoading(true)
    try {
      await axios.post(`/api/users/${u.username}/follow`)
      setFollowing(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card p-4 flex items-center gap-3">
      <Link to={`/users/${u.username}`}>
        <Avatar username={u.username} avatarUrl={u.avatar_url} size={10} />
      </Link>
      <div className="flex-1 min-w-0">
        <Link to={`/users/${u.username}`} className="font-medium text-white hover:text-violet-400 transition-colors text-sm">
          {u.username}
        </Link>
        <p className="text-gray-500 text-xs">
          {u.mutual_follows
            ? `${u.mutual_follows} mutual follow${u.mutual_follows !== 1 ? 's' : ''}`
            : `${u.follower_count ?? 0} follower${u.follower_count !== 1 ? 's' : ''}`}
        </p>
      </div>
      <button
        onClick={follow}
        disabled={loading || following}
        className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
          following
            ? 'bg-gray-700 text-gray-400'
            : 'btn-primary'
        }`}
      >
        {loading ? '…' : following ? 'Following' : 'Follow'}
      </button>
    </div>
  )
}

function ActivityItem({ item }) {
  const actionLabel = {
    reviewed_album:              'Reviewed',
    reviewed_song:               'Reviewed',
    marked_album_listened:       'Listened to',
    marked_album_want_to_listen: 'Want to listen to',
    marked_album_favorites:      'Favorited',
    followed:                    'Followed',
  }[item.action_type] ?? item.action_type

  const targetLink = item.target_type === 'album' ? `/albums/${item.target_id}`
    : item.target_type === 'song'  ? `/songs/${item.target_id}`
    : item.target_type === 'user'  ? `/users/${item.target_name}`
    : null

  return (
    <div className="card p-4 flex items-center gap-4">
      {item.target_cover ? (
        <Link to={targetLink ?? '#'} className="shrink-0">
          <img src={item.target_cover} alt="" className="w-12 h-12 rounded object-cover" loading="lazy" />
        </Link>
      ) : (
        <div className="w-12 h-12 rounded bg-gray-800 flex items-center justify-center text-gray-500 shrink-0 text-xl">
          {item.target_type === 'user' ? '👤' : '🎵'}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm">
          <span className="text-gray-400">{actionLabel} </span>
          {item.target_name && (targetLink
            ? <Link to={targetLink} className="font-medium text-white hover:text-violet-400">{item.target_name}</Link>
            : <span className="font-medium text-white">{item.target_name}</span>
          )}
          {item.target_artist && <span className="text-gray-500"> · {item.target_artist}</span>}
        </p>
        <p className="text-gray-600 text-xs mt-0.5">{new Date(item.created_at).toLocaleDateString()}</p>
      </div>
    </div>
  )
}

function ForYouAlbumCard({ album }) {
  return (
    <Link to={`/albums/${album.id}`} className="group block">
      <div className="relative aspect-square bg-gray-800 rounded-lg overflow-hidden mb-2">
        {album.cover_url ? (
          <img
            src={album.cover_url}
            alt={album.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-violet-900/60 to-gray-800">
            💿
          </div>
        )}
        {album.similarity != null && (
          <span className="absolute bottom-1.5 right-1.5 text-[10px] font-semibold bg-black/70 text-violet-300 rounded-full px-1.5 py-0.5 backdrop-blur-sm">
            {Math.round(album.similarity * 100)}% match
          </span>
        )}
      </div>
      <p className="text-white text-xs font-medium truncate group-hover:text-violet-400 transition-colors">
        {album.title}
      </p>
      <p className="text-gray-500 text-[11px] truncate">{album.artist?.name}</p>
    </Link>
  )
}

function ForYouSongRow({ song }) {
  return (
    <Link
      to={`/songs/${song.id}`}
      className="card p-3 flex items-center gap-3 hover:border-violet-700 transition-colors group"
    >
      {song.album?.cover_url ? (
        <img
          src={song.album.cover_url}
          alt=""
          className="w-10 h-10 rounded object-cover shrink-0"
          loading="lazy"
        />
      ) : (
        <div className="w-10 h-10 rounded bg-gray-800 flex items-center justify-center text-gray-500 shrink-0">
          ♪
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="text-white text-sm font-medium truncate group-hover:text-violet-400 transition-colors">
          {song.title}
        </p>
        <p className="text-gray-500 text-xs truncate">
          {song.artist?.name}{song.album ? ` · ${song.album.title}` : ''}
        </p>
      </div>
      {song.similarity != null && (
        <span className="text-violet-400 text-[10px] font-semibold shrink-0 bg-violet-900/30 rounded-full px-2 py-0.5">
          {Math.round(song.similarity * 100)}%
        </span>
      )}
    </Link>
  )
}

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
