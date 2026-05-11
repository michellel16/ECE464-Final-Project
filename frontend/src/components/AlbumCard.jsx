import { Link } from 'react-router-dom'

export default function AlbumCard({ album, showRating = true }) {
  return (
    <Link to={`/albums/${album.id}`} className="group block">
      <div className="relative aspect-square bg-[#1a1a2e] rounded overflow-hidden mb-2 ring-1 ring-white/25">
        {album.cover_url ? (
          <img
            src={album.cover_url}
            alt={album.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-violet-900/60 to-[#1a1a2e]">
            🎵
          </div>
        )}
        {showRating && album.average_rating && (
          <div className="absolute bottom-1.5 right-1.5 bg-black/80 backdrop-blur text-yellow-300 text-[10px] font-bold px-1.5 py-0.5 rounded">
            ★ {album.average_rating}
          </div>
        )}
      </div>
      <p className="text-gray-100 text-xs font-medium truncate group-hover:text-violet-400 transition-colors">
        {album.title}
      </p>
      <p className="text-gray-300 text-[10px] truncate">
        {album.artist?.name ?? 'Unknown Artist'}
      </p>
    </Link>
  )
}
