import { useState, useEffect } from 'react'
import axios from 'axios'
import AlbumCard from '../components/AlbumCard'
import { Link } from 'react-router-dom'

export default function Discover() {
  const [albums, setAlbums]   = useState([])
  const [artists, setArtists] = useState([])
  const [tab, setTab]         = useState('albums')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      axios.get('/api/music/albums?limit=50'),
      axios.get('/api/music/artists?limit=50'),
    ]).then(([a, b]) => {
      setAlbums(a.data)
      setArtists(b.data)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader />

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-1">Discover</h1>
        <p className="text-gray-400">Browse all music on Tunelog</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-xl p-1 w-fit">
        {['albums', 'artists'].map(t => (
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
    </div>
  )
}

function ArtistCard({ artist }) {
  return (
    <Link to={`/artists/${artist.id}`} className="group block text-center">
      <div className="aspect-square bg-gray-800 rounded-full overflow-hidden mb-3 mx-auto w-28 sm:w-36">
        {artist.image_url ? (
          <img
            src={artist.image_url}
            alt={artist.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-violet-900/60 to-gray-800">
            🎤
          </div>
        )}
      </div>
      <p className="text-white font-medium text-sm group-hover:text-violet-400 transition-colors">
        {artist.name}
      </p>
      <p className="text-gray-500 text-xs mt-0.5">
        {artist.genres?.slice(0, 2).join(', ')}
      </p>
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
