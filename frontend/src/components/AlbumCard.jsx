import { Link } from 'react-router-dom'

export default function AlbumCard({ album, showRating = true }) {
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
            🎵
          </div>
        )}
        {showRating && album.average_rating && (
          <div className="absolute bottom-1.5 right-1.5 bg-black/70 backdrop-blur text-yellow-400 text-xs font-bold px-1.5 py-0.5 rounded">
            ★ {album.average_rating}
          </div>
        )}
      </div>
      <p className="text-white text-sm font-medium truncate group-hover:text-violet-400 transition-colors">
        {album.title}
      </p>
      <p className="text-gray-500 text-xs truncate">
        {album.artist?.name ?? 'Unknown Artist'}
      </p>
    </Link>
  )
}
