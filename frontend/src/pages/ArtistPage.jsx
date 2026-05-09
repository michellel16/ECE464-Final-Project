import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import axios from 'axios'
import AlbumCard from '../components/AlbumCard'
import { useAuth } from '../contexts/AuthContext'

export default function ArtistPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [artist, setArtist] = useState(null)
  const [albums, setAlbums] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  useEffect(() => {
    Promise.all([
      axios.get(`/api/music/artists/${id}`),
      axios.get(`/api/music/artists/${id}/albums`),
    ]).then(([aRes, albRes]) => {
      setArtist(aRes.data)
      setAlbums(albRes.data)
    }).finally(() => setLoading(false))
  }, [id])

  async function handleDelete() {
    if (!confirmDelete) { setConfirmDelete(true); return }
    setDeleting(true)
    try {
      await axios.delete(`/api/music/artists/${id}`)
      navigate('/discover')
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  if (loading) return <Loader />
  if (!artist) return <NotFound />

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 mb-10">
        <div className="w-36 h-36 rounded-full overflow-hidden bg-gray-800 shrink-0 ring-4 ring-violet-700/40">
          {artist.image_url ? (
            <img src={artist.image_url} alt={artist.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-5xl">🎤</div>
          )}
        </div>
        <div className="flex-1">
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-4xl font-extrabold text-white">{artist.name}</h1>
            {user && (
              <button
                onClick={handleDelete}
                disabled={deleting}
                className={`shrink-0 text-xs px-3 py-1.5 rounded-lg border transition-colors disabled:opacity-50 ${
                  confirmDelete
                    ? 'border-red-500 text-red-400 bg-red-950/40 hover:bg-red-900/60'
                    : 'border-gray-700 text-gray-500 hover:border-red-600 hover:text-red-400'
                }`}
              >
                {deleting ? 'Deleting…' : confirmDelete ? 'Confirm delete' : 'Delete artist'}
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {artist.genres?.map(g => (
              <span key={g.id} className="text-xs text-violet-300 bg-violet-900/40 px-2.5 py-1 rounded-full">
                {g.name}
              </span>
            ))}
          </div>
          <div className="flex gap-4 mt-3 text-sm text-gray-400">
            {artist.country && <span>{artist.country}</span>}
            {artist.formed_year && <span>Est. {artist.formed_year}</span>}
            <span>{albums.length} album{albums.length !== 1 ? 's' : ''}</span>
          </div>
        </div>
      </div>

      {artist.bio && (
        <div className="card p-5 mb-8 text-gray-300 text-sm leading-relaxed max-w-3xl">
          {artist.bio}
        </div>
      )}

      <h2 className="text-xl font-bold text-white mb-4">Discography</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
        {albums.map(a => (
          <AlbumCard key={a.id} album={{ ...a, artist: { name: artist.name } }} />
        ))}
      </div>
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
