import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import AlbumCard from '../components/AlbumCard'
import { Avatar } from '../components/Navbar'
import StarRating from '../components/StarRating'

export default function Home() {
  const { user } = useAuth()
  const [featured, setFeatured] = useState([])
  const [feed, setFeed]         = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    const fetches = [axios.get('/api/music/albums?limit=12')]
    if (user) fetches.push(axios.get('/api/social/feed?limit=20'))

    Promise.all(fetches).then(([albumsRes, feedRes]) => {
      setFeatured(albumsRes.data)
      if (feedRes) setFeed(feedRes.data)
    }).finally(() => setLoading(false))
  }, [user])

  if (loading) return <PageLoader />

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-14">
      {/* Hero for guests */}
      {!user && (
        <section className="relative text-center py-24 rounded-2xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-900/40 via-gray-950 to-pink-900/20 pointer-events-none" />
          <div className="relative space-y-6">
            <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight">
              <span className="bg-gradient-to-r from-violet-400 via-pink-400 to-violet-400 bg-clip-text text-transparent">
                Your Music Journal
              </span>
            </h1>
            <p className="text-gray-400 text-xl max-w-2xl mx-auto">
              Rate albums, write reviews, build catalogs, and share your taste with the world.
              Like Letterboxd — but for music.
            </p>
            <div className="flex items-center justify-center gap-4 pt-2">
              <Link to="/register" className="btn-primary text-base px-8 py-3">Get Started</Link>
              <Link to="/discover" className="btn-secondary text-base px-8 py-3">Explore Music</Link>
            </div>
          </div>
        </section>
      )}

      {/* Featured albums */}
      <section>
        <SectionHeader title="Featured Albums" href="/discover" />
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4">
          {featured.map(a => <AlbumCard key={a.id} album={a} />)}
        </div>
      </section>

      {/* Activity feed for logged-in users */}
      {user && (
        <section>
          <SectionHeader title="Activity Feed" />
          {feed.length === 0 ? (
            <div className="card p-10 text-center text-gray-500">
              <p className="mb-2">Nothing here yet.</p>
              <p>
                <Link to="/discover" className="link-purple">Find users to follow →</Link>
              </p>
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
      {href && <Link to={href} className="link-purple text-sm">View all →</Link>}
    </div>
  )
}

function ActivityItem({ item }) {
  const actionLabel = {
    reviewed_album:          'reviewed',
    reviewed_song:           'reviewed',
    marked_album_listened:   'listened to',
    marked_album_want_to_listen: 'wants to listen to',
    marked_album_favorites:  'favorited',
    followed:                'followed',
  }[item.action_type] ?? item.action_type

  const targetLink = item.target_type === 'album'
    ? `/albums/${item.target_id}`
    : item.target_type === 'song'
    ? `/songs/${item.target_id}`
    : item.target_type === 'user'
    ? `/users/${item.target_name}`
    : null

  return (
    <div className="card p-4 flex items-start gap-3">
      <Link to={`/users/${item.username}`}>
        <Avatar username={item.username} size={9} />
      </Link>
      <div className="flex-1 min-w-0">
        <p className="text-sm">
          <Link to={`/users/${item.username}`} className="font-medium text-white hover:text-violet-400">
            {item.username}
          </Link>
          {' '}
          <span className="text-gray-400">{actionLabel}</span>
          {item.target_name && (
            <>
              {' '}
              {targetLink ? (
                <Link to={targetLink} className="font-medium text-white hover:text-violet-400">
                  {item.target_name}
                </Link>
              ) : (
                <span className="font-medium text-white">{item.target_name}</span>
              )}
              {item.target_artist && (
                <span className="text-gray-500"> by {item.target_artist}</span>
              )}
            </>
          )}
        </p>
        <p className="text-gray-600 text-xs mt-0.5">
          {new Date(item.created_at).toLocaleDateString()}
        </p>
      </div>
      {item.target_cover && (
        <Link to={targetLink ?? '#'}>
          <img src={item.target_cover} alt="" className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
        </Link>
      )}
    </div>
  )
}

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
