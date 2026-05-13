import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import AlbumCard from '../components/AlbumCard'

export default function ArtistPage() {
  const { id } = useParams()
  const [artist, setArtist] = useState(null)
  const [albums, setAlbums] = useState([])
  const [loading, setLoading]       = useState(true)
  const [albumsLoading, setAlbLoad] = useState(true)
  useEffect(() => {
    setLoading(true)
    setAlbLoad(true)
    setArtist(null)
    setAlbums([])
    axios.get(`/api/music/artists/${id}`)
      .then(r => setArtist(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
    axios.get(`/api/music/artists/${id}/albums`)
      .then(r => setAlbums(r.data))
      .catch(() => {})
      .finally(() => setAlbLoad(false))
  }, [id])

  if (loading) return <Loader />
  if (!artist) return <NotFound />

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 mb-10">
        <div className="w-36 h-36 rounded-full overflow-hidden bg-[#1a1a2e] shrink-0 ring-2 ring-violet-600/50">
          {artist.image_url ? (
            <img src={artist.image_url} alt={artist.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-5xl">🎤</div>
          )}
        </div>
        <div className="flex-1">
          <h1 className="text-4xl font-extrabold text-white font-display">{artist.name}</h1>
          <div className="flex flex-wrap gap-2 mt-2">
            {artist.genres?.map(g => (
              <span key={g.id} className="text-xs text-violet-200 bg-violet-900/40 border border-violet-700/50 px-3 py-1 rounded">
                {g.name}
              </span>
            ))}
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-300">
            {artist.country && <span>{artist.country}</span>}
            {artist.formed_year && <span>Est. {artist.formed_year}</span>}
            <span>{albums.length} album{albums.length !== 1 ? 's' : ''}</span>
          </div>
        </div>
      </div>

      {artist.bio && (
        <div className="card p-5 mb-8 text-gray-200 text-sm leading-relaxed max-w-3xl">
          {artist.bio}
        </div>
      )}

      <h2 className="text-xl font-bold text-white mb-4">Discography</h2>
      {albumsLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="aspect-square bg-gray-800 rounded-lg mb-2" />
              <div className="h-3 bg-gray-800 rounded w-3/4 mb-1" />
              <div className="h-3 bg-gray-800 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
          {albums.map(a => (
            <AlbumCard key={a.id} album={{ ...a, artist: { name: artist.name } }} />
          ))}
        </div>
      )}
    </div>
  )
}

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function NotFound() {
  return (
    <div className="text-center py-20 text-gray-500">
      <p>Artist not found.</p>
      <Link to="/discover" className="link-purple mt-2 inline-block">Back to Discover</Link>
    </div>
  )
}
