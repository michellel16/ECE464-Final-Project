import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import axios from 'axios'
import AlbumCard from '../components/AlbumCard'

export default function Discover() {
  const [searchParams] = useSearchParams()
  const [albums, setAlbums]   = useState([])
  const [artists, setArtists] = useState([])
  const [songs, setSongs]     = useState([])
  const [tab, setTab]         = useState(searchParams.get('tab') ?? 'albums')
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

  if (loading) return <Loader />

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-1">Discover</h1>
        <p className="text-gray-400">Browse all music on Tunelog</p>
      </div>

      <div className="flex gap-1 bg-gray-900 rounded-xl p-1 w-fit">
        {['albums', 'artists', 'songs'].map(t => (
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
      <p className="text-gray-500 text-xs mt-0.5">{artist.genres?.slice(0, 2).join(', ')}</p>
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
