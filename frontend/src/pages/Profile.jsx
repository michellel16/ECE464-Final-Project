import { useState, useEffect, useRef, useMemo } from 'react'
import { useParams, Link, useSearchParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { Avatar } from '../components/Navbar'
import StarRating from '../components/StarRating'
import { supabase } from '../lib/supabase'
import { staticUrl } from '../utils'

export default function Profile() {
  const { username } = useParams()
  const { user: me, refreshUser } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [profile, setProfile]     = useState(null)
  const [reviews, setReviews]     = useState([])
  const [lists, setLists]         = useState([])
  const [isFollowing, setFollowing] = useState(false)
  const [isRequested, setRequested] = useState(false)
  const [tab, setTab]             = useState('reviews')
  const [loading, setLoading]     = useState(true)
  const [followLoading, setFL]    = useState(false)
  const [spotifyStatus, setSpotifyStatus] = useState(null)
  const [spotifyToast, setSpotifyToast]   = useState(null)
  const [showImport, setShowImport] = useState(false)
  const [showSpotifyMenu, setShowSpotifyMenu] = useState(false)
  const [showEditProfile, setShowEditProfile] = useState(false)
  const [showAccountSettings, setShowAccountSettings] = useState(false)
  const [followModal, setFollowModal] = useState(null)  // 'followers' | 'following' | null

  const isMe = me?.username === username

  // Honour ?tab=requests from notification deep-links
  useEffect(() => {
    const t = searchParams.get('tab')
    if (t) { setTab(t); setSearchParams({}, { replace: true }) }
  }, [])

  useEffect(() => {
    Promise.allSettled([
      axios.get(`/api/users/${username}`),
      axios.get(`/api/users/${username}/reviews?limit=100`),
      axios.get(`/api/lists/user/${username}`),
      me && !isMe ? axios.get(`/api/users/${username}/follow-status`) : Promise.resolve(null),
    ]).then(([pRes, rRes, lRes, fsRes]) => {
      if (pRes.status === 'fulfilled') setProfile(pRes.value.data)
      if (rRes.status === 'fulfilled') setReviews(rRes.value.data)
      if (lRes.status === 'fulfilled') setLists(lRes.value.data)
      if (fsRes.status === 'fulfilled' && fsRes.value?.data) {
        setFollowing(fsRes.value.data.following)
        setRequested(fsRes.value.data.requested ?? false)
      }
    }).finally(() => setLoading(false))
  }, [username, me])

  // Fetch Spotify connection status for own profile
  useEffect(() => {
    if (isMe && me) {
      axios.get('/api/spotify/status').then(r => {
        setSpotifyStatus(r.data)
      }).catch(() => {})
    }
  }, [isMe, me])

  // Handle redirect back from Spotify OAuth
  useEffect(() => {
    const spotify = searchParams.get('spotify')
    if (!spotify) return
    if (spotify === 'connected') {
      setSpotifyToast({ type: 'success', msg: 'Spotify connected successfully!' })
      axios.get('/api/spotify/status').then(r => setSpotifyStatus(r.data)).catch(() => {})
    } else if (spotify === 'error') {
      const reason = searchParams.get('reason') || 'unknown error'
      setSpotifyToast({ type: 'error', msg: `Spotify connection failed: ${reason}` })
    }
    // Remove query params from URL
    setSearchParams({}, { replace: true })
    const timer = setTimeout(() => setSpotifyToast(null), 4000)
    return () => clearTimeout(timer)
  }, [])

  async function connectSpotify() {
    try {
      const { data } = await axios.get('/api/spotify/auth-url')
      window.location.href = data.url
    } catch {
      setSpotifyToast({ type: 'error', msg: 'Could not start Spotify connection.' })
    }
  }

  async function disconnectSpotify() {
    await axios.delete('/api/spotify/disconnect')
    setSpotifyStatus({ connected: false })
  }

  async function toggleFollow() {
    if (!me || isMe) return
    setFL(true)
    try {
      if (isFollowing || isRequested) {
        await axios.delete(`/api/users/${username}/follow`)
        setFollowing(false)
        setRequested(false)
        if (isFollowing) setProfile(p => ({ ...p, follower_count: (p.follower_count ?? 1) - 1 }))
      } else {
        const { data } = await axios.post(`/api/users/${username}/follow`)
        if (data.requested) {
          setRequested(true)
        } else {
          setFollowing(true)
          setProfile(p => ({ ...p, follower_count: (p.follower_count ?? 0) + 1 }))
        }
      }
    } finally {
      setFL(false)
    }
  }

  if (loading) return <Loader />
  if (!profile) return <div className="text-center py-20 text-gray-500">User not found.</div>

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Toast */}
      {spotifyToast && (
        <div className={`fixed top-20 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all ${
          spotifyToast.type === 'success' ? 'bg-green-700 text-white' : 'bg-red-700 text-white'
        }`}>
          {spotifyToast.msg}
        </div>
      )}

      {/* Profile header */}
      <div className="card mb-6 overflow-hidden">
        {/* Banner */}
        <div className="relative h-36 sm:h-44 bg-gradient-to-br from-pink-950 via-violet-950 to-gray-900 shrink-0">
          {profile.banner_url && (
            <img src={staticUrl(profile.banner_url)} alt="" className="w-full h-full object-cover" />
          )}
        </div>

        {/* Avatar + actions row */}
        <div className="relative z-10 px-5 sm:px-6">
          <div className="flex items-end justify-between -mt-10 sm:-mt-12 mb-2">
            <div className="relative z-10 ring-4 ring-[#05050d] rounded-full shrink-0">
              <Avatar username={profile.username} avatarUrl={profile.avatar_url} size={20} />
            </div>
            {me && !isMe && (
              <div className="translate-y-6">
                <button
                  onClick={toggleFollow}
                  disabled={followLoading}
                  className={`px-4 py-1.5 rounded text-sm font-medium transition-colors disabled:opacity-60 ${
                    isFollowing
                      ? 'bg-gray-700 text-white hover:bg-red-900/60 hover:text-red-300'
                      : isRequested
                      ? 'bg-gray-700 text-gray-300 hover:bg-red-900/60 hover:text-red-300'
                      : 'btn-primary'
                  }`}
                >
                  {followLoading ? '…' : isFollowing ? 'Following' : isRequested ? 'Requested' : 'Follow'}
                </button>
              </div>
            )}
            {isMe && (
              <div className="flex gap-2 items-center translate-y-3">
                <button onClick={() => setShowEditProfile(true)} className="btn-secondary text-xs px-3 py-1.5">Edit Profile</button>
                <button onClick={() => setShowAccountSettings(true)} className="btn-secondary text-xs px-3 py-1.5">Account</button>
                {spotifyStatus !== null && (
                  <div className="relative">
                    {spotifyStatus.connected ? (
                      <>
                        <button
                          onClick={() => setShowSpotifyMenu(m => !m)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-green-700/30 border border-green-700/50 text-green-300 text-xs font-medium transition-colors hover:bg-green-700/50"
                        >
                          <SpotifyIcon className="w-3 h-3" />
                          Spotify
                          <span className="text-[10px]">{showSpotifyMenu ? '▲' : '▼'}</span>
                        </button>
                        {showSpotifyMenu && (
                          <div className="absolute right-0 top-full mt-1.5 z-30 bg-[#111127] border border-[#252540] rounded overflow-hidden shadow-xl min-w-[148px]">
                            <button
                              onClick={() => { setShowImport(true); setShowSpotifyMenu(false) }}
                              className="w-full text-left px-4 py-2.5 text-xs text-green-400 hover:bg-[#1a1a2e] transition-colors"
                            >
                              Import Music
                            </button>
                            <div className="border-t border-[#252540]" />
                            <button
                              onClick={disconnectSpotify}
                              className="w-full text-left px-4 py-2.5 text-xs text-gray-300 hover:bg-[#1a1a2e] hover:text-red-400 transition-colors"
                            >
                              Disconnect
                            </button>
                          </div>
                        )}
                      </>
                    ) : (
                      <button
                        onClick={connectSpotify}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-green-600 hover:bg-green-500 text-white text-xs font-medium transition-colors"
                      >
                        <SpotifyIcon className="w-3 h-3" />
                        Connect Spotify
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Name + bio + stats */}
          <div className="pb-6 space-y-4">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              {profile.username}
              {profile.is_private && (
                <span title="Private account" className="text-gray-500 text-base">🔒</span>
              )}
            </h1>
            {profile.bio && <p className="text-gray-300 text-sm">{profile.bio}</p>}
            {/* Music preference tags */}
            {(profile.music_preferences?.genres?.length > 0 || profile.music_preferences?.moods?.length > 0) && (
              <div className="flex flex-wrap gap-2">
                {profile.music_preferences.genres?.map(g => (
                  <span key={g} className="text-xs bg-violet-900/40 text-violet-200 border border-violet-700/50 rounded px-2.5 py-1">
                    {g}
                  </span>
                ))}
                {profile.music_preferences.moods?.map(m => (
                  <span key={m} className="text-xs bg-pink-900/30 text-pink-200 border border-pink-700/40 rounded px-2.5 py-1">
                    {m}
                  </span>
                ))}
              </div>
            )}
            {profile.music_preferences?.free_text && (
              <p className="text-gray-400 text-xs italic">"{profile.music_preferences.free_text}"</p>
            )}
            <div className="flex gap-5 text-sm text-gray-200">
              <button onClick={() => setFollowModal('followers')} className="hover:text-white transition-colors">
                <strong className="text-white">{profile.follower_count ?? 0}</strong> followers
              </button>
              <button onClick={() => setFollowModal('following')} className="hover:text-white transition-colors">
                <strong className="text-white">{profile.following_count ?? 0}</strong> following
              </button>
              {isMe ? (
                <Link to="/stats" className="hover:text-white transition-colors">
                  <strong className="text-white">{reviews.length}</strong> reviews
                </Link>
              ) : (
                <button onClick={() => setTab('reviews')} className="hover:text-white transition-colors">
                  <strong className="text-white">{reviews.length}</strong> reviews
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Private account gate: hide all content from non-followers */}
      {profile.is_private && !isMe && !isFollowing ? (
        <div className="card p-12 text-center space-y-3">
          <div className="text-5xl">🔒</div>
          <p className="text-white font-semibold text-lg">This account is private</p>
          <p className="text-gray-400 text-sm">
            {isRequested
              ? 'Your follow request is pending. Once approved you\'ll be able to see their content.'
              : 'Follow this account to see their reviews, lists, and activity.'}
          </p>
        </div>
      ) : (
        <>
          {/* Tabs */}
          <div className="flex flex-wrap items-center gap-1 bg-gray-900 rounded-xl p-1 w-fit mb-6">
            {[
              'reviews',
              'lists',
              'activity',
              ...(isMe ? ['recs'] : []),
              ...(isMe ? ['requests'] : []),
              ...(isMe && spotifyStatus?.connected ? ['spotify playlists'] : []),
            ].map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors capitalize ${
                  tab === t ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                {t === 'spotify playlists' ? (
                  <span className="flex items-center gap-1.5">
                    <SpotifyIcon className="w-3.5 h-3.5 text-green-400" />
                    Playlists
                  </span>
                ) : t === 'recs' ? (
                  <RecsTabLabel />
                ) : t === 'requests' ? (
                  <FollowRequestsTabLabel />
                ) : t}
              </button>
            ))}
          </div>

          {tab === 'reviews' && (
            <ReviewsTab reviews={reviews} />
          )}

          {tab === 'lists' && (
            <ListsTab lists={lists} isMe={isMe} />
          )}

          {tab === 'activity' && (
            <ActivityTab username={profile.username} />
          )}

          {tab === 'requests' && isMe && (
            <FollowRequestsTab />
          )}

          {tab === 'recs' && isMe && (
            <RecsTab />
          )}

          {tab === 'spotify playlists' && isMe && spotifyStatus?.connected && (
            <SpotifyPlaylistsTab />
          )}
        </>
      )}

      {/* Import modal */}
      {showImport && (
        <ImportModal onClose={() => setShowImport(false)} />
      )}

      {/* Edit profile modal */}
      {showEditProfile && (
        <EditProfileModal
          profile={profile}
          onClose={() => setShowEditProfile(false)}
          onSaved={async (updated) => {
            setProfile(p => ({ ...p, ...updated }))
            await refreshUser()
            if (updated.username && updated.username !== username) {
              navigate(`/users/${updated.username}`, { replace: true })
            }
            setShowEditProfile(false)
          }}
        />
      )}

      {/* Account settings modal */}
      {showAccountSettings && (
        <AccountSettingsModal
          email={profile.email}
          onClose={() => setShowAccountSettings(false)}
        />
      )}

      {/* Followers / Following modal */}
      {followModal && (
        <FollowListModal
          username={profile.username}
          type={followModal}
          onClose={() => setFollowModal(null)}
        />
      )}
    </div>
  )
}

// ── Activity Tab ─────────────────────────────────────────────────────────────

const ACTION_LABELS = {
  reviewed_album:              'reviewed',
  reviewed_song:               'reviewed',
  marked_album_listened:       'listened to',
  marked_album_want_to_listen: 'wants to listen to',
  marked_album_favorites:      'added to favorites',
  followed:                    'followed',
}

function ActivityTab({ username }) {
  const [activities, setActivities] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 15

  useEffect(() => {
    setLoading(true)
    setPage(1)
    axios.get(`/api/users/${username}/activity?limit=100`)
      .then(r => setActivities(r.data))
      .finally(() => setLoading(false))
  }, [username])

  if (loading) return (
    <div className="flex justify-center py-10">
      <div className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!activities || activities.length === 0) {
    return (
      <div className="card p-8 text-center text-gray-500">No recent activity.</div>
    )
  }

  const totalPages = Math.ceil(activities.length / PAGE_SIZE)
  const paged = activities.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <div className="space-y-2">
      {paged.map(a => <ActivityItem key={a.id} activity={a} />)}
      <Pagination page={page} totalPages={totalPages} onPage={setPage} />
    </div>
  )
}

function ActivityItem({ activity: a }) {
  const label = ACTION_LABELS[a.action_type] ?? a.action_type.replace(/_/g, ' ')
  const hasTarget = a.target_name && a.target_url
  const isReview = a.action_type.startsWith('reviewed_')
  const meta = a.meta ? (typeof a.meta === 'string' ? JSON.parse(a.meta) : a.meta) : null

  return (
    <div className="card p-4 flex items-center gap-4">
      {a.target_cover ? (
        hasTarget ? (
          <Link to={a.target_url} className="shrink-0">
            <img src={a.target_cover} alt="" className="w-12 h-12 rounded object-cover" loading="lazy" />
          </Link>
        ) : (
          <img src={a.target_cover} alt="" className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
        )
      ) : (
        <div className="w-12 h-12 rounded bg-gray-800 flex items-center justify-center text-gray-500 shrink-0 text-xl">
          {a.target_type === 'user' ? '👤' : '🎵'}
        </div>
      )}

      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-400">
          <span className="text-gray-300">{label} </span>
          {hasTarget ? (
            <Link to={a.target_url} className="text-white font-medium hover:text-violet-400 transition-colors">
              {a.target_name}
            </Link>
          ) : (
            <span className="text-white font-medium">{a.target_name}</span>
          )}
          {a.target_artist && (
            <span className="text-gray-500"> · {a.target_artist}</span>
          )}
        </p>
        {isReview && meta?.rating && (
          <p className="text-yellow-500 text-xs mt-0.5">{'★'.repeat(Math.round(meta.rating))} {meta.rating}</p>
        )}
        <p className="text-gray-600 text-xs mt-0.5">{new Date(a.created_at).toLocaleDateString()}</p>
      </div>
    </div>
  )
}

// ── Follow Requests Tab ───────────────────────────────────────────────────────

function FollowRequestsTabLabel() {
  const [count, setCount] = useState(0)
  useEffect(() => {
    axios.get('/api/users/me/follow-requests')
      .then(r => setCount(r.data.length))
      .catch(() => {})
  }, [])
  return (
    <span className="flex items-center gap-1.5">
      Requests
      {count > 0 && (
        <span className="bg-violet-500 text-white text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center leading-none">
          {count > 9 ? '9+' : count}
        </span>
      )}
    </span>
  )
}

function FollowRequestsTab() {
  const [requests, setRequests] = useState(null)
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    axios.get('/api/users/me/follow-requests')
      .then(r => setRequests(r.data))
      .finally(() => setLoading(false))
  }, [])

  async function accept(id) {
    await axios.post(`/api/users/me/follow-requests/${id}/accept`)
    setRequests(prev => prev.filter(r => r.id !== id))
  }

  async function reject(id) {
    await axios.post(`/api/users/me/follow-requests/${id}/reject`)
    setRequests(prev => prev.filter(r => r.id !== id))
  }

  if (loading) return (
    <div className="flex justify-center py-10">
      <div className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!requests || requests.length === 0) {
    return (
      <div className="card p-8 text-center text-gray-500">No pending follow requests.</div>
    )
  }

  return (
    <div className="space-y-2">
      {requests.map(req => (
        <div key={req.id} className="card p-4 flex items-center gap-4">
          <Avatar username={req.requester_username} avatarUrl={req.requester_avatar_url} size={10} />
          <div className="flex-1 min-w-0">
            <Link to={`/users/${req.requester_username}`} className="text-white font-medium hover:text-violet-400 transition-colors">
              {req.requester_username}
            </Link>
            <p className="text-gray-500 text-xs mt-0.5">{new Date(req.created_at).toLocaleDateString()}</p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={() => accept(req.id)}
              className="px-4 py-1.5 rounded-full text-sm font-medium bg-violet-600 hover:bg-violet-500 text-white transition-colors"
            >
              Accept
            </button>
            <button
              onClick={() => reject(req.id)}
              className="px-4 py-1.5 rounded-full text-sm font-medium border border-gray-700 text-gray-400 hover:border-red-700 hover:text-red-400 transition-colors"
            >
              Decline
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Recs Tab ─────────────────────────────────────────────────────────────────

function RecsTabLabel() {
  const [unread, setUnread] = useState(0)
  useEffect(() => {
    axios.get('/api/social/recommendations/unread-count')
      .then(r => setUnread(r.data.count))
      .catch(() => {})
  }, [])
  return (
    <span className="flex items-center gap-1.5">
      Recs
      {unread > 0 && (
        <span className="bg-pink-500 text-white text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center leading-none">
          {unread > 9 ? '9+' : unread}
        </span>
      )}
    </span>
  )
}

function RecsTab() {
  const [recs, setRecs]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const REC_PAGE_SIZE = 10

  useEffect(() => {
    axios.get('/api/social/recommendations')
      .then(r => setRecs(r.data))
      .finally(() => setLoading(false))
  }, [])

  async function markAllRead() {
    await axios.post('/api/social/recommendations/read-all')
    setRecs(prev => prev?.map(r => ({ ...r, is_read: true })))
  }

  async function markRead(id) {
    await axios.post(`/api/social/recommendations/${id}/read`)
    setRecs(prev => prev?.map(r => r.id === id ? { ...r, is_read: true } : r))
  }

  if (loading) return (
    <div className="flex justify-center py-10">
      <div className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!recs || recs.length === 0) {
    return (
      <div className="card p-8 text-center text-gray-500">
        <p className="text-lg mb-1">No recommendations yet</p>
        <p className="text-sm">When someone recommends a song or album to you, it'll appear here.</p>
      </div>
    )
  }

  const hasUnread = recs.some(r => !r.is_read)
  const totalPages = Math.ceil(recs.length / REC_PAGE_SIZE)
  const pagedRecs = recs.slice((page - 1) * REC_PAGE_SIZE, page * REC_PAGE_SIZE)

  return (
    <div className="space-y-3">
      {hasUnread && (
        <div className="flex justify-end">
          <button onClick={markAllRead} className="text-xs text-gray-500 hover:text-violet-400 transition-colors">
            Mark all as read
          </button>
        </div>
      )}
      {pagedRecs.map(rec => (
        <RecCard key={rec.id} rec={rec} onRead={markRead} />
      ))}
      <Pagination page={page} totalPages={totalPages} onPage={setPage} />
    </div>
  )
}

function RecCard({ rec, onRead }) {
  const item = rec.song ?? rec.album
  const itemType = rec.song ? 'song' : 'album'
  const href = item ? `/${itemType}s/${item.id}` : null

  return (
    <div className={`card p-4 flex items-start gap-4 transition-colors ${!rec.is_read ? 'border-violet-700/50 bg-violet-950/10' : ''}`}>
      {/* Cover */}
      {item?.cover_url ? (
        <Link to={href} className="shrink-0">
          <img src={item.cover_url} alt="" className="w-12 h-12 rounded object-cover" loading="lazy" />
        </Link>
      ) : (
        <div className="w-12 h-12 rounded bg-gray-800 flex items-center justify-center text-gray-500 shrink-0 text-xl">
          {rec.song ? '♪' : '💿'}
        </div>
      )}

      <div className="flex-1 min-w-0">
        {/* Sender */}
        <p className="text-sm text-gray-400">
          <Link to={`/users/${rec.sender_username}`} className="font-medium text-white hover:text-violet-400 transition-colors">
            {rec.sender_username}
          </Link>
          {' '}recommended a {itemType}
        </p>

        {/* Item */}
        {item && href && (
          <Link to={href} className="block mt-0.5 hover:text-violet-400 transition-colors">
            <p className="text-white font-medium text-sm">{item.title}</p>
            {item.artist && <p className="text-gray-500 text-xs">{item.artist}</p>}
          </Link>
        )}

        {/* Note */}
        {rec.note && (
          <p className="text-gray-300 text-sm mt-1.5 italic">"{rec.note}"</p>
        )}

        <p className="text-gray-600 text-xs mt-1">{new Date(rec.created_at).toLocaleDateString()}</p>
      </div>

      {/* Unread indicator + dismiss */}
      <div className="flex flex-col items-end gap-2 shrink-0">
        {!rec.is_read && <span className="w-2 h-2 rounded-full bg-violet-500" />}
        {!rec.is_read && (
          <button
            onClick={() => onRead(rec.id)}
            className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
            title="Mark as read"
          >
            ✓
          </button>
        )}
      </div>
    </div>
  )
}

// ── Import playlist as Tunelog list button ────────────────────────────────────

function ImportAsListButton({ playlistId }) {
  const [status, setStatus] = useState(null) // null | 'loading' | {list_id, tracks_added, tracks_total} | 'error'

  async function handleClick(e) {
    e.stopPropagation()
    if (status === 'loading') return
    setStatus('loading')
    try {
      const { data } = await axios.post('/api/spotify/import-playlist-as-list', { playlist_id: playlistId })
      setStatus(data)
    } catch {
      setStatus('error')
      setTimeout(() => setStatus(null), 3000)
    }
  }

  if (status && status !== 'loading' && status !== 'error') {
    return (
      <Link
        to={`/lists/${status.list_id}`}
        onClick={e => e.stopPropagation()}
        className="text-xs px-2.5 py-1 rounded-full bg-violet-700/30 text-violet-400 border border-violet-700/50 hover:bg-violet-700/50 transition-colors shrink-0"
      >
        View list ({status.tracks_added}/{status.tracks_total})
      </Link>
    )
  }

  return (
    <button
      onClick={handleClick}
      disabled={status === 'loading'}
      className="text-xs px-2.5 py-1 rounded-full bg-green-700/20 text-green-400 border border-green-700/40 hover:bg-green-700/40 transition-colors disabled:opacity-50 shrink-0"
    >
      {status === 'loading' ? '…' : status === 'error' ? 'Failed' : 'Save as list'}
    </button>
  )
}

// ── Spotify Playlists Tab ─────────────────────────────────────────────────────

const PLAYLIST_PAGE_SIZE = 20

const PLAYLIST_SORTS = [
  { value: 'default', label: 'Newest'  },
  { value: 'oldest',  label: 'Oldest'  },
  { value: 'az',      label: 'A–Z'     },
  { value: 'za',      label: 'Z–A'     },
]

function SpotifyPlaylistsTab() {
  const [playlists, setPlaylists]     = useState([])
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState(null)
  const [search, setSearch]           = useState('')
  const [sort, setSort]               = useState('default')
  const [page, setPage]               = useState(1)
  const [expanded, setExpanded]       = useState(null)
  const [loadingId, setLoadingId]     = useState(null)
  const [trackErrors, setTrackErrors] = useState({})   // { [playlistId]: errorMsg }
  const [tracks, setTracks]           = useState({})   // { [playlistId]: track[] }
  const [importingId, setImportingId] = useState(null)
  const [importErrors, setImportErrors] = useState({}) // { [spotify_id]: errorMsg }

  useEffect(() => {
    axios.get('/api/spotify/playlists')
      .then(r => { setPlaylists(r.data); setError(null) })
      .catch(e => setError(e.response?.data?.detail || e.message || 'Unknown error'))
      .finally(() => setLoading(false))
  }, [])

  async function togglePlaylist(playlist) {
    if (expanded === playlist.id) { setExpanded(null); return }
    setExpanded(playlist.id)
    if (playlist.id in tracks) return
    setLoadingId(playlist.id)
    try {
      const { data } = await axios.get(`/api/spotify/playlists/${playlist.id}/tracks`)
      setTracks(t => ({ ...t, [playlist.id]: data }))
      setTrackErrors(e => { const n = { ...e }; delete n[playlist.id]; return n })
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Failed to load tracks'
      setTrackErrors(prev => ({ ...prev, [playlist.id]: msg }))
    } finally {
      setLoadingId(null)
    }
  }

  async function retryTracks(playlist) {
    setTrackErrors(e => { const n = { ...e }; delete n[playlist.id]; return n })
    // Remove cached (failed) entry so it re-fetches
    setTracks(t => { const n = { ...t }; delete n[playlist.id]; return n })
    setLoadingId(playlist.id)
    try {
      const { data } = await axios.get(`/api/spotify/playlists/${playlist.id}/tracks`)
      setTracks(t => ({ ...t, [playlist.id]: data }))
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Failed to load tracks'
      setTrackErrors(prev => ({ ...prev, [playlist.id]: msg }))
    } finally {
      setLoadingId(null)
    }
  }

  async function importTrack(track, playlistId) {
    setImportingId(track.spotify_id)
    setImportErrors(e => { const n = { ...e }; delete n[track.spotify_id]; return n })
    try {
      const { data } = await axios.post('/api/spotify/import-track', { spotify_track_id: track.spotify_id })
      setTracks(prev => ({
        ...prev,
        [playlistId]: prev[playlistId].map(t =>
          t.spotify_id === track.spotify_id ? { ...t, tunelog_song_id: data.song_id } : t
        ),
      }))
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Import failed'
      setImportErrors(prev => ({ ...prev, [track.spotify_id]: msg }))
    } finally {
      setImportingId(null)
    }
  }

  function fmtDuration(ms) {
    if (!ms) return ''
    const s = Math.round(ms / 1000)
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
  }

  if (loading) return (
    <div className="flex items-center justify-center py-16">
      <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (error) return (
    <div className="card p-8 text-center">
      <p className="text-red-400 font-medium mb-1">Failed to load playlists</p>
      <p className="text-gray-500 text-sm">{error}</p>
    </div>
  )

  if (playlists.length === 0) return (
    <div className="card p-8 text-center text-gray-500">No playlists found.</div>
  )

  const visible = (() => {
    let list = search.trim()
      ? playlists.filter(p => p.name.toLowerCase().includes(search.toLowerCase()))
      : [...playlists]
    if (sort === 'oldest') list.reverse()
    else if (sort === 'az') list.sort((a, b) => a.name.localeCompare(b.name))
    else if (sort === 'za') list.sort((a, b) => b.name.localeCompare(a.name))
    return list
  })()
  const totalPlaylistPages = Math.ceil(visible.length / PLAYLIST_PAGE_SIZE)
  const pagedPlaylists = visible.slice((page - 1) * PLAYLIST_PAGE_SIZE, page * PLAYLIST_PAGE_SIZE)

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        <div className="relative flex-1 min-w-0">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search playlists…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); setExpanded(null) }}
            className="input w-full pl-9 py-2 text-sm"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors">
              ✕
            </button>
          )}
        </div>
        <div className="flex gap-1 bg-gray-900 rounded-xl p-1 shrink-0">
          {PLAYLIST_SORTS.map(s => (
            <button
              key={s.value}
              onClick={() => { setSort(s.value); setPage(1); setExpanded(null) }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${sort === s.value ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white'}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {visible.length === 0 ? (
        <div className="card p-6 text-center text-gray-500 text-sm">No playlists match "{search}"</div>
      ) : (
      <div className="space-y-2">
      {pagedPlaylists.map(playlist => (
        <div key={playlist.id} className="card overflow-hidden">
          {/* Playlist header — whole row toggles, import button stops propagation */}
          <div
            onClick={() => togglePlaylist(playlist)}
            className="flex items-center gap-4 p-4 hover:bg-gray-800/50 transition-colors cursor-pointer select-none"
          >
            {playlist.image_url ? (
              <img src={playlist.image_url} alt="" className="w-12 h-12 rounded shrink-0 object-cover" />
            ) : (
              <div className="w-12 h-12 rounded bg-gray-700 flex items-center justify-center shrink-0 text-gray-400 text-xl">♪</div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-white font-medium truncate">{playlist.name}</p>
            </div>
            <div onClick={e => e.stopPropagation()}>
              <ImportAsListButton playlistId={playlist.id} />
            </div>
            <span className="text-gray-500 text-sm shrink-0 ml-1">
              {expanded === playlist.id ? '▲' : '▼'}
            </span>
          </div>

          {/* Track list */}
          {expanded === playlist.id && (
            <div className="border-t border-gray-800">
              {loadingId === playlist.id ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : trackErrors[playlist.id] ? (
                <div className="p-4 text-center">
                  <p className="text-red-400 text-sm mb-2">{trackErrors[playlist.id]}</p>
                  <button
                    onClick={e => { e.stopPropagation(); retryTracks(playlist) }}
                    className="text-xs text-violet-400 hover:text-violet-300 underline"
                  >
                    Retry
                  </button>
                </div>
              ) : !(playlist.id in tracks) ? (
                <div className="p-4 text-center text-gray-500 text-sm">Loading…</div>
              ) : tracks[playlist.id].length === 0 ? (
                <p className="text-gray-500 text-sm p-4">No tracks in this playlist.</p>
              ) : (
                <div className="divide-y divide-gray-800/50">
                  {tracks[playlist.id].map((track, idx) => (
                    <div key={track.spotify_id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-800/30 transition-colors">
                      <span className="text-gray-600 text-xs w-5 text-right shrink-0">{idx + 1}</span>
                      {track.cover_url ? (
                        <img src={track.cover_url} alt="" className="w-9 h-9 rounded shrink-0 object-cover" />
                      ) : (
                        <div className="w-9 h-9 rounded bg-gray-800 flex items-center justify-center text-gray-600 shrink-0 text-xs">♪</div>
                      )}
                      <div className="flex-1 min-w-0">
                        {track.tunelog_song_id ? (
                          <Link
                            to={`/songs/${track.tunelog_song_id}`}
                            className="text-white text-sm font-medium hover:text-violet-400 transition-colors truncate block"
                          >
                            {track.name}
                          </Link>
                        ) : (
                          <p className="text-white text-sm truncate">{track.name}</p>
                        )}
                        <p className="text-gray-500 text-xs truncate">
                          {track.artist_name}{track.album_name ? ` · ${track.album_name}` : ''}
                        </p>
                        {importErrors[track.spotify_id] && (
                          <p className="text-red-400 text-xs mt-0.5">{importErrors[track.spotify_id]}</p>
                        )}
                      </div>
                      {track.duration_ms && (
                        <span className="text-gray-600 text-xs shrink-0 hidden sm:block">{fmtDuration(track.duration_ms)}</span>
                      )}
                      <div className="shrink-0 ml-1">
                        {track.tunelog_song_id ? (
                          <Link
                            to={`/songs/${track.tunelog_song_id}`}
                            className="text-xs px-3 py-1 rounded-full bg-violet-700/30 text-violet-400 border border-violet-700/50 hover:bg-violet-700/50 transition-colors"
                          >
                            View
                          </Link>
                        ) : (
                          <button
                            onClick={e => { e.stopPropagation(); importTrack(track, playlist.id) }}
                            disabled={importingId === track.spotify_id}
                            className="text-xs px-3 py-1 rounded-full bg-green-700/20 text-green-400 border border-green-700/40 hover:bg-green-700/40 transition-colors disabled:opacity-50"
                          >
                            {importingId === track.spotify_id ? '…' : 'Add'}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
      <Pagination page={page} totalPages={totalPlaylistPages} onPage={setPage} />
      </div>
      )}
    </div>
  )
}

// ── Import Modal ──────────────────────────────────────────────────────────────

function ImportModal({ onClose }) {
  const [playlists, setPlaylists]   = useState([])
  const [selected, setSelected]     = useState(null)
  const [tracks, setTracks]         = useState([])
  const [checked, setChecked]       = useState({})
  const [loading, setLoading]       = useState(true)
  const [loadingTracks, setLT]      = useState(false)
  const [importing, setImporting]   = useState(false)
  const [imported, setImported]     = useState(0)

  useEffect(() => {
    axios.get('/api/spotify/playlists')
      .then(r => setPlaylists(r.data))
      .finally(() => setLoading(false))
  }, [])

  async function selectPlaylist(playlist) {
    setSelected(playlist)
    setTracks([])
    setChecked({})
    setLT(true)
    try {
      const { data } = await axios.get(`/api/spotify/playlists/${playlist.id}/tracks`)
      setTracks(data)
      // Pre-check tracks not yet in Tunelog
      const init = {}
      data.forEach(t => { if (!t.tunelog_song_id) init[t.spotify_id] = true })
      setChecked(init)
    } finally {
      setLT(false)
    }
  }

  function toggleTrack(spotify_id) {
    setChecked(c => ({ ...c, [spotify_id]: !c[spotify_id] }))
  }

  function toggleAll() {
    const unchecked = tracks.filter(t => !t.tunelog_song_id && !checked[t.spotify_id])
    if (unchecked.length > 0) {
      const next = { ...checked }
      unchecked.forEach(t => { next[t.spotify_id] = true })
      setChecked(next)
    } else {
      const next = { ...checked }
      tracks.filter(t => !t.tunelog_song_id).forEach(t => { next[t.spotify_id] = false })
      setChecked(next)
    }
  }

  async function doImport() {
    const toImport = tracks.filter(t => checked[t.spotify_id] && !t.tunelog_song_id)
    if (toImport.length === 0) return
    setImporting(true)
    let count = 0
    for (const t of toImport) {
      try {
        await axios.post('/api/spotify/import-track', { spotify_track_id: t.spotify_id })
        count++
        setImported(count)
      } catch {
        // skip failures
      }
    }
    // Refresh track list to update tunelog_song_id
    const { data } = await axios.get(`/api/spotify/playlists/${selected.id}/tracks`)
    setTracks(data)
    setChecked({})
    setImporting(false)
  }

  const toImportCount = tracks.filter(t => checked[t.spotify_id] && !t.tunelog_song_id).length

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <h2 className="font-bold text-white text-lg flex items-center gap-2">
            <SpotifyIcon className="text-green-500 w-5 h-5" />
            Import from Spotify
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-xl leading-none">&times;</button>
        </div>

        <div className="flex flex-1 min-h-0">
          {/* Playlist list */}
          <div className="w-56 border-r border-gray-800 overflow-y-auto flex-shrink-0">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : playlists.length === 0 ? (
              <p className="text-gray-500 text-sm p-4">No playlists found.</p>
            ) : (
              playlists.map(p => (
                <button
                  key={p.id}
                  onClick={() => selectPlaylist(p)}
                  className={`w-full text-left p-3 flex items-center gap-3 transition-colors hover:bg-gray-800 ${selected?.id === p.id ? 'bg-gray-800' : ''}`}
                >
                  {p.image_url ? (
                    <img src={p.image_url} alt="" className="w-10 h-10 rounded shrink-0 object-cover" />
                  ) : (
                    <div className="w-10 h-10 rounded bg-gray-700 flex items-center justify-center shrink-0 text-gray-500">♪</div>
                  )}
                  <div className="min-w-0">
                    <p className="text-white text-xs font-medium truncate">{p.name}</p>
                    <p className="text-gray-500 text-xs">{p.track_count} tracks</p>
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Track list */}
          <div className="flex-1 overflow-y-auto">
            {!selected ? (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                Select a playlist
              </div>
            ) : loadingTracks ? (
              <div className="flex items-center justify-center h-32">
                <div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <>
                <div className="sticky top-0 bg-gray-900 border-b border-gray-800 px-4 py-2 flex items-center justify-between">
                  <button onClick={toggleAll} className="text-xs text-violet-400 hover:text-violet-300 transition-colors">
                    Toggle all new
                  </button>
                  <span className="text-xs text-gray-500">{toImportCount} to import</span>
                </div>
                {tracks.map(t => (
                  <label
                    key={t.spotify_id}
                    className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-800/50 transition-colors ${t.tunelog_song_id ? 'opacity-50' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={!!checked[t.spotify_id]}
                      onChange={() => !t.tunelog_song_id && toggleTrack(t.spotify_id)}
                      disabled={!!t.tunelog_song_id}
                      className="w-4 h-4 accent-green-500 shrink-0"
                    />
                    {t.cover_url ? (
                      <img src={t.cover_url} alt="" className="w-9 h-9 rounded shrink-0 object-cover" />
                    ) : (
                      <div className="w-9 h-9 rounded bg-gray-800 flex items-center justify-center text-gray-600 shrink-0 text-xs">♪</div>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="text-white text-sm truncate">{t.name}</p>
                      <p className="text-gray-500 text-xs truncate">{t.artist_name} · {t.album_name}</p>
                    </div>
                    {t.tunelog_song_id && (
                      <span className="text-green-600 text-xs shrink-0">In Tunelog</span>
                    )}
                  </label>
                ))}
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 flex items-center justify-between">
          {importing ? (
            <span className="text-green-400 text-sm">Importing {imported}…</span>
          ) : imported > 0 && toImportCount === 0 ? (
            <span className="text-green-400 text-sm">{imported} track{imported !== 1 ? 's' : ''} imported!</span>
          ) : (
            <span className="text-gray-500 text-sm">{toImportCount} track{toImportCount !== 1 ? 's' : ''} selected</span>
          )}
          <div className="flex gap-2">
            <button onClick={onClose} className="btn-secondary text-sm">Close</button>
            <button
              onClick={doImport}
              disabled={toImportCount === 0 || importing}
              className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
            >
              {importing ? 'Importing…' : 'Import Selected'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

// ── Edit Profile Modal ────────────────────────────────────────────────────────

const MAX_GENRES = 5
const MAX_MOODS  = 5

const POPULAR_GENRES = [
  'Pop', 'Rock', 'Hip-Hop', 'R&B', 'Electronic', 'Indie', 'Alternative',
  'Jazz', 'Classical', 'Country', 'Folk', 'Metal', 'Soul', 'Latin',
]

const MOOD_OPTIONS = [
  'Chill', 'Energetic', 'Melancholic', 'Upbeat', 'Relaxed', 'Intense',
  'Romantic', 'Party', 'Late Night', 'Focus', 'Feel-Good', 'Dark', 'Nostalgic', 'Dreamy',
]

function EditProfileModal({ profile, onClose, onSaved }) {
  const [username, setUsername]     = useState(profile.username)
  const [bio, setBio]               = useState(profile.bio ?? '')
  const [isPrivate, setIsPrivate]   = useState(profile.is_private ?? false)
  const [saving, setSaving]         = useState(false)
  const [error, setError]           = useState(null)
  const [avatarPreview, setAvatarPreview] = useState(profile.avatar_url ?? null)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [avatarError, setAvatarError] = useState(null)
  const [bannerPreview, setBannerPreview]   = useState(profile.banner_url ?? null)
  const [bannerUploading, setBannerUploading] = useState(false)
  const [bannerError, setBannerError]     = useState(null)
  const fileInputRef   = useRef(null)
  const bannerInputRef = useRef(null)

  // Music preferences state
  const [availableGenres, setAvailableGenres] = useState([])
  const [selectedGenres, setSelectedGenres]   = useState(profile.music_preferences?.genres ?? [])
  const [selectedMoods, setSelectedMoods]     = useState(profile.music_preferences?.moods ?? [])
  const [prefFreeText, setPrefFreeText]       = useState(profile.music_preferences?.free_text ?? '')
  const [genreSearch, setGenreSearch]         = useState('')

  useEffect(() => {
    axios.get('/api/charts/genres').then(r => setAvailableGenres(r.data)).catch(() => {})
  }, [])

  function toggleGenre(name) {
    setSelectedGenres(prev => {
      if (prev.includes(name)) return prev.filter(g => g !== name)
      if (prev.length >= MAX_GENRES) return prev
      return [...prev, name]
    })
  }

  function toggleMood(name) {
    setSelectedMoods(prev => {
      if (prev.includes(name)) return prev.filter(m => m !== name)
      if (prev.length >= MAX_MOODS) return prev
      return [...prev, name]
    })
  }

  async function handleAvatarChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setAvatarPreview(URL.createObjectURL(file))
    setAvatarError(null)
    setAvatarUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await axios.post('/api/users/me/avatar', form)
      setAvatarPreview(data.avatar_url)
    } catch (e) {
      setAvatarError(e.response?.data?.detail || 'Upload failed')
      setAvatarPreview(profile.avatar_url ?? null)
    } finally {
      setAvatarUploading(false)
    }
  }

  async function handleBannerChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setBannerPreview(URL.createObjectURL(file))
    setBannerError(null)
    setBannerUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await axios.post('/api/users/me/banner', form)
      setBannerPreview(data.banner_url)
    } catch (e) {
      setBannerError(e.response?.data?.detail || 'Upload failed')
      setBannerPreview(profile.banner_url ?? null)
    } finally {
      setBannerUploading(false)
    }
  }

  async function removeBanner() {
    try {
      await axios.delete('/api/users/me/banner')
      setBannerPreview(null)
    } catch {}
  }

  async function save() {
    const trimmed = username.trim()
    if (!trimmed) { setError('Username cannot be empty'); return }
    setSaving(true)
    setError(null)
    try {
      const [profileRes] = await Promise.all([
        axios.put('/api/users/me/profile', {
          username: trimmed,
          bio: bio.trim() || null,
          is_private: isPrivate,
        }),
        axios.put('/api/users/me/preferences', {
          genres: selectedGenres,
          moods: selectedMoods,
          free_text: prefFreeText.trim(),
        }),
      ])
      const data = profileRes.data
      const newPrefs = { genres: selectedGenres, moods: selectedMoods, free_text: prefFreeText.trim() }
      onSaved({
        username: data.username,
        bio: data.bio,
        avatar_url: avatarPreview ?? data.avatar_url,
        banner_url: bannerPreview,
        is_private: data.is_private,
        music_preferences: newPrefs,
      })
    } catch (e) {
      setError(e.response?.data?.detail || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-md shadow-2xl flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between p-5 border-b border-gray-800 shrink-0">
          <h2 className="font-bold text-white text-lg">Edit Profile</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl leading-none">&times;</button>
        </div>
        <div className="p-5 space-y-4 overflow-y-auto flex-1">
          {/* Banner picker */}
          <div>
            <p className="text-xs text-gray-400 mb-1.5">Banner image</p>
            <button
              type="button"
              onClick={() => bannerInputRef.current?.click()}
              className="relative group w-full h-24 rounded-xl overflow-hidden bg-gradient-to-br from-violet-950/60 to-gray-800 border border-gray-700 hover:border-violet-600 transition-colors"
              title="Change banner"
            >
              {bannerPreview && (
                <img src={staticUrl(bannerPreview)} alt="banner" className="w-full h-full object-cover" />
              )}
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                {bannerUploading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <span className="text-white text-xs font-medium">
                    {bannerPreview ? 'Change banner' : '+ Add banner'}
                  </span>
                )}
              </div>
            </button>
            {bannerPreview && (
              <button
                type="button"
                onClick={removeBanner}
                className="text-xs text-gray-500 hover:text-red-400 transition-colors mt-1"
              >
                Remove banner
              </button>
            )}
            {bannerError && <p className="text-red-400 text-xs mt-1">{bannerError}</p>}
            <input
              ref={bannerInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="hidden"
              onChange={handleBannerChange}
            />
          </div>

          {/* Avatar picker */}
          <div className="flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="relative group"
              title="Change profile picture"
            >
              {avatarPreview ? (
                <img src={staticUrl(avatarPreview)} alt="avatar" className="w-20 h-20 rounded-full object-cover ring-2 ring-violet-700/50" />
              ) : (
                <Avatar username={username} size={20} />
              )}
              <div className="absolute inset-0 rounded-full bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                {avatarUploading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                )}
              </div>
            </button>
            <p className="text-xs text-gray-500">Click to change photo</p>
            {avatarError && <p className="text-red-400 text-xs">{avatarError}</p>}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="hidden"
              onChange={handleAvatarChange}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Username</label>
            <input
              className={`input w-full ${error ? 'border-red-500 focus:border-red-500' : ''}`}
              value={username}
              onChange={e => { setUsername(e.target.value); setError(null) }}
              maxLength={50}
            />
            {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
            <p className="text-xs text-gray-600 mt-1">This is also your login name.</p>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Bio</label>
            <textarea
              className="input w-full resize-none"
              rows={3}
              value={bio}
              onChange={e => setBio(e.target.value)}
              placeholder="Tell people a bit about yourself…"
              maxLength={300}
            />
          </div>

          {/* Music Taste Preferences */}
          <div className="border-t border-gray-800 pt-4 space-y-4">
            <p className="text-sm font-medium text-white">Music Taste</p>

            <div>
              <label className="block text-xs text-gray-400 mb-2">
                Favorite Genres <span className="text-gray-600">({selectedGenres.length}/{MAX_GENRES})</span>
              </label>

              {/* Popular genres as quick-pick chips */}
              <div className="flex flex-wrap gap-1.5 mb-2">
                {POPULAR_GENRES.map(name => {
                  const selected  = selectedGenres.includes(name)
                  const atLimit   = !selected && selectedGenres.length >= MAX_GENRES
                  return (
                    <button
                      key={name}
                      type="button"
                      onClick={() => toggleGenre(name)}
                      disabled={atLimit}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                        selected   ? 'bg-violet-600 text-white' :
                        atLimit    ? 'bg-gray-800 text-gray-600 cursor-not-allowed' :
                                     'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                      }`}
                    >
                      {name}
                    </button>
                  )
                })}
              </div>

              {/* Selected non-popular genres */}
              {selectedGenres.filter(g => !POPULAR_GENRES.includes(g)).length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {selectedGenres.filter(g => !POPULAR_GENRES.includes(g)).map(name => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => toggleGenre(name)}
                      className="px-2.5 py-1 rounded-full text-xs font-medium bg-violet-600 text-white flex items-center gap-1 hover:bg-violet-700 transition-colors"
                    >
                      {name} <span className="text-violet-200 leading-none">×</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Search for more genres */}
              <div className="relative">
                <input
                  type="text"
                  className="input w-full text-sm"
                  placeholder="Search more genres…"
                  value={genreSearch}
                  onChange={e => setGenreSearch(e.target.value)}
                />
                {genreSearch.trim() && (
                  <div className="absolute top-full z-10 left-0 right-0 bg-[#111127] border border-[#252540] rounded mt-1 max-h-40 overflow-y-auto shadow-xl">
                    {availableGenres
                      .filter(g =>
                        !POPULAR_GENRES.includes(g.name) &&
                        g.name.toLowerCase().includes(genreSearch.toLowerCase().trim())
                      )
                      .slice(0, 20)
                      .map(g => (
                        <button
                          key={g.id}
                          type="button"
                          onClick={() => { toggleGenre(g.name); setGenreSearch('') }}
                          className={`w-full text-left px-3 py-2 text-xs hover:bg-[#1a1a2e] transition-colors flex items-center justify-between ${
                            selectedGenres.includes(g.name) ? 'text-violet-300' : 'text-gray-300'
                          }`}
                        >
                          {g.name}
                          {selectedGenres.includes(g.name) && <span className="text-violet-400 text-[10px]">✓</span>}
                        </button>
                      ))
                    }
                    {availableGenres.filter(g =>
                      !POPULAR_GENRES.includes(g.name) &&
                      g.name.toLowerCase().includes(genreSearch.toLowerCase().trim())
                    ).length === 0 && (
                      <p className="px-3 py-2 text-xs text-gray-500">No genres found</p>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-2">
                Vibes <span className="text-gray-600">({selectedMoods.length}/{MAX_MOODS})</span>
              </label>
              <div className="flex flex-wrap gap-1.5">
                {MOOD_OPTIONS.map(m => {
                  const selected = selectedMoods.includes(m)
                  const atLimit  = !selected && selectedMoods.length >= MAX_MOODS
                  return (
                    <button
                      key={m}
                      type="button"
                      onClick={() => toggleMood(m)}
                      disabled={atLimit}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                        selected  ? 'bg-pink-700/80 text-pink-100' :
                        atLimit   ? 'bg-gray-800 text-gray-600 cursor-not-allowed' :
                                    'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                      }`}
                    >
                      {m}
                    </button>
                  )
                })}
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Describe your taste <span className="text-gray-600">(optional)</span></label>
              <textarea
                className="input w-full resize-none text-sm"
                rows={2}
                value={prefFreeText}
                onChange={e => setPrefFreeText(e.target.value)}
                placeholder="e.g. I love lo-fi indie, sad girl vibes, 70s classics…"
                maxLength={300}
              />
              <p className="text-xs text-gray-600 mt-0.5">{prefFreeText.length}/300 · Used to improve recommendations</p>
            </div>
          </div>

          <div className="flex items-center justify-between py-1">
            <div>
              <p className="text-sm text-white font-medium">Private Account</p>
              <p className="text-xs text-gray-500 mt-0.5">New followers must be approved by you</p>
            </div>
            <button
              type="button"
              onClick={() => setIsPrivate(v => !v)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${isPrivate ? 'bg-violet-600' : 'bg-gray-700'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isPrivate ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>
        </div>
        <div className="flex justify-end gap-2 p-5 border-t border-gray-800 shrink-0">
          <button onClick={onClose} className="btn-secondary text-sm">Cancel</button>
          <button onClick={save} disabled={saving || avatarUploading} className="btn-primary text-sm disabled:opacity-50">
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Account Settings Modal ────────────────────────────────────────────────────

function AccountSettingsModal({ email, onClose }) {
  const [section, setSection] = useState('password') // 'password' | 'email'

  // Password state
  const [currentPw, setCurrentPw]   = useState('')
  const [newPw, setNewPw]           = useState('')
  const [confirmPw, setConfirmPw]   = useState('')
  const [pwSaving, setPwSaving]     = useState(false)
  const [pwError, setPwError]       = useState(null)
  const [pwSuccess, setPwSuccess]   = useState(false)

  // Email state
  const [newEmail, setNewEmail]     = useState('')
  const [emailSaving, setEmailSaving] = useState(false)
  const [emailError, setEmailError] = useState(null)
  const [emailSent, setEmailSent]   = useState(false)

  async function changePassword() {
    if (!currentPw) { setPwError('Enter your current password'); return }
    if (newPw.length < 6) { setPwError('New password must be at least 6 characters'); return }
    if (newPw !== confirmPw) { setPwError('Passwords do not match'); return }
    setPwSaving(true)
    setPwError(null)
    try {
      // Re-authenticate to verify current password
      const { error: signInErr } = await supabase.auth.signInWithPassword({ email, password: currentPw })
      if (signInErr) { setPwError('Current password is incorrect'); return }
      // Update password
      const { error: updateErr } = await supabase.auth.updateUser({ password: newPw })
      if (updateErr) throw new Error(updateErr.message)
      setPwSuccess(true)
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
    } catch (e) {
      setPwError(e.message || 'Failed to change password')
    } finally {
      setPwSaving(false)
    }
  }

  async function changeEmail() {
    const trimmed = newEmail.trim()
    if (!trimmed) { setEmailError('Enter a new email address'); return }
    if (trimmed === email) { setEmailError('That is your current email'); return }
    setEmailSaving(true)
    setEmailError(null)
    try {
      const { error } = await supabase.auth.updateUser({ email: trimmed })
      if (error) throw new Error(error.message)
      setEmailSent(true)
    } catch (e) {
      setEmailError(e.message || 'Failed to send verification email')
    } finally {
      setEmailSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <h2 className="font-bold text-white text-lg">Account Settings</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl leading-none">&times;</button>
        </div>

        {/* Section tabs */}
        <div className="flex border-b border-gray-800">
          {['password', 'email'].map(s => (
            <button
              key={s}
              onClick={() => setSection(s)}
              className={`flex-1 py-3 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
                section === s ? 'border-violet-500 text-violet-400' : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              Change {s}
            </button>
          ))}
        </div>

        <div className="p-5 space-y-4">
          {section === 'password' && (
            <>
              {pwSuccess ? (
                <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-4 text-center">
                  <p className="text-green-400 font-medium">Password updated successfully.</p>
                </div>
              ) : (
                <>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Current password</label>
                    <input type="password" className="input w-full" value={currentPw} onChange={e => setCurrentPw(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">New password</label>
                    <input type="password" className="input w-full" value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="At least 6 characters" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Confirm new password</label>
                    <input type="password" className="input w-full" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} />
                  </div>
                  {pwError && <p className="text-red-400 text-sm">{pwError}</p>}
                  <button onClick={changePassword} disabled={pwSaving} className="btn-primary text-sm w-full disabled:opacity-50">
                    {pwSaving ? 'Updating…' : 'Update password'}
                  </button>
                </>
              )}
            </>
          )}

          {section === 'email' && (
            <>
              {emailSent ? (
                <div className="bg-violet-900/30 border border-violet-700/50 rounded-lg p-4 text-center space-y-1">
                  <p className="text-violet-300 font-medium">Verification email sent!</p>
                  <p className="text-gray-400 text-sm">Check <strong>{newEmail.trim()}</strong> and click the link to confirm your new email address.</p>
                </div>
              ) : (
                <>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Current email</label>
                    <p className="text-gray-300 text-sm bg-gray-800 rounded-lg px-3 py-2">{email}</p>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">New email</label>
                    <input type="email" className="input w-full" value={newEmail} onChange={e => setNewEmail(e.target.value)} placeholder="you@example.com" />
                    <p className="text-xs text-gray-600 mt-1">A confirmation link will be sent to this address.</p>
                  </div>
                  {emailError && <p className="text-red-400 text-sm">{emailError}</p>}
                  <button onClick={changeEmail} disabled={emailSaving} className="btn-primary text-sm w-full disabled:opacity-50">
                    {emailSaving ? 'Sending…' : 'Send verification email'}
                  </button>
                </>
              )}
            </>
          )}
        </div>

        <div className="flex justify-end p-5 pt-0">
          <button onClick={onClose} className="btn-secondary text-sm">Close</button>
        </div>
      </div>
    </div>
  )
}

// ── Follow List Modal ─────────────────────────────────────────────────────────

function FollowListModal({ username, type, onClose }) {
  const [users, setUsers]   = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`/api/users/${username}/${type}`)
      .then(r => setUsers(r.data))
      .finally(() => setLoading(false))
  }, [username, type])

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-sm shadow-2xl flex flex-col max-h-[70vh]">
        <div className="flex items-center justify-between p-5 border-b border-gray-800 shrink-0">
          <h2 className="font-bold text-white text-lg capitalize">{type}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl leading-none">&times;</button>
        </div>
        <div className="overflow-y-auto flex-1">
          {loading ? (
            <div className="flex items-center justify-center py-10">
              <div className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : users.length === 0 ? (
            <p className="text-center text-gray-500 text-sm py-10">No {type} yet.</p>
          ) : (
            users.map(u => (
              <Link
                key={u.id}
                to={`/users/${u.username}`}
                onClick={onClose}
                className="flex items-center gap-3 px-5 py-3 hover:bg-gray-800 transition-colors"
              >
                <Avatar username={u.username} avatarUrl={u.avatar_url} size={9} />
                <div className="min-w-0">
                  <p className="text-white text-sm font-medium">{u.username}</p>
                  {u.bio && <p className="text-gray-500 text-xs truncate">{u.bio}</p>}
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function SpotifyIcon({ className = '' }) {
  return (
    <svg viewBox="0 0 24 24" className={`fill-current ${className}`} xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
    </svg>
  )
}

function ReviewsTab({ reviews }) {
  const [page, setPage]           = useState(1)
  const [query, setQuery]         = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const PAGE_SIZE = 10

  const filtered = useMemo(() => {
    let list = reviews
    if (typeFilter !== 'all') list = list.filter(r => r.target_type === typeFilter)
    if (query.trim()) {
      const q = query.trim().toLowerCase()
      list = list.filter(r =>
        r.target_title?.toLowerCase().includes(q) ||
        r.target_artist?.toLowerCase().includes(q)
      )
    }
    return list
  }, [reviews, typeFilter, query])

  useEffect(() => setPage(1), [typeFilter, query])

  if (reviews.length === 0) {
    return <div className="card p-8 text-center text-gray-500">No reviews yet.</div>
  }

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <div className="space-y-3">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <div className="relative">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search by title or artist…"
            className="bg-[#0d0d1f] border border-[#2a2a45] text-white text-sm rounded pl-8 pr-7 py-2 focus:outline-none focus:border-violet-500 w-60 transition-colors placeholder-gray-500"
          />
          {query && (
            <button onClick={() => setQuery('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors text-sm">✕</button>
          )}
        </div>

        <div className="flex items-center gap-1 bg-gray-900 rounded-xl p-1">
          {[
            { value: 'all',   label: 'All'    },
            { value: 'album', label: 'Albums' },
            { value: 'song',  label: 'Songs'  },
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setTypeFilter(value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                typeFilter === value ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {(query || typeFilter !== 'all') && (
          <button
            onClick={() => { setQuery(''); setTypeFilter('all') }}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Clear
          </button>
        )}

        <span className="text-gray-500 text-xs ml-auto">
          {filtered.length} review{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {filtered.length === 0 ? (
        <div className="card p-6 text-center text-gray-500 text-sm">No reviews match these filters.</div>
      ) : (
        <>
          {paged.map(r => <ReviewItem key={r.id} review={r} />)}
          <Pagination page={page} totalPages={totalPages} onPage={setPage} />
        </>
      )}
    </div>
  )
}

function Pagination({ page, totalPages, onPage }) {
  if (totalPages <= 1) return null
  return (
    <div className="flex items-center justify-center gap-3 mt-4 pt-2">
      <button
        onClick={() => onPage(page - 1)}
        disabled={page === 1}
        className="px-3 py-1.5 rounded-lg text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        ← Prev
      </button>
      <span className="text-sm text-gray-500">{page} / {totalPages}</span>
      <button
        onClick={() => onPage(page + 1)}
        disabled={page === totalPages}
        className="px-3 py-1.5 rounded-lg text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Next →
      </button>
    </div>
  )
}

function ReviewItem({ review }) {
  return (
    <div className="card p-4 flex gap-4 items-start">
      {review.target_cover && (
        <Link to={`/${review.target_type}s/${review.target_type === 'album' ? review.album_id : review.song_id}`}>
          <img src={review.target_cover} alt="" className="w-12 h-12 rounded object-cover shrink-0" loading="lazy" />
        </Link>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="min-w-0">
            <Link
              to={`/${review.target_type}s/${review.target_type === 'album' ? review.album_id : review.song_id}#review-${review.id}`}
              className="text-white font-medium truncate hover:text-violet-400 transition-colors block"
            >
              {review.target_title ?? '?'}
            </Link>
            {review.target_artist && (
              <p className="text-gray-500 text-xs">{review.target_artist}</p>
            )}
          </div>
          <StarRating value={review.rating} readonly size="sm" />
        </div>
        {review.text && <p className="text-gray-400 text-sm">{review.text}</p>}
        <p className="text-gray-600 text-xs mt-1">{new Date(review.created_at).toLocaleDateString()}</p>
      </div>
    </div>
  )
}

const LIST_PAGE_SIZE = 12

function ListsTab({ lists, isMe }) {
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [likeState, setLikeState] = useState(() => {
    const map = {}
    lists.forEach(l => { map[l.id] = { liked: l.is_liked ?? false, count: l.like_count ?? 0 } })
    return map
  })

  async function toggleLike(listId, e) {
    e.preventDefault()
    e.stopPropagation()
    if (!user) return
    try {
      const { data } = await axios.post(`/api/lists/${listId}/like`)
      setLikeState(prev => ({ ...prev, [listId]: { liked: data.liked, count: data.like_count } }))
    } catch {}
  }

  return (
    <div>
      {isMe && (
        <div className="mb-4">
          <Link to="/lists" className="btn-primary text-sm">Manage My Lists</Link>
        </div>
      )}
      {lists.length === 0 ? (
        <div className="card p-8 text-center text-gray-500">
          {isMe
            ? <><p className="mb-3">You haven't created any lists yet.</p><Link to="/lists" className="btn-primary text-sm">Create your first list</Link></>
            : 'No public lists.'}
        </div>
      ) : (
        <>
          <div className="grid sm:grid-cols-2 gap-4">
            {lists.slice((page - 1) * LIST_PAGE_SIZE, page * LIST_PAGE_SIZE).map(l => (
              <Link
                key={l.id}
                to={`/lists/${l.id}`}
                className="card p-4 hover:border-violet-700 transition-colors group text-left block"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium text-white group-hover:text-violet-400 transition-colors">{l.name}</p>
                  {!l.is_public && <span className="text-gray-600 text-xs shrink-0 mt-0.5">🔒 Private</span>}
                </div>
                {l.description && <p className="text-gray-500 text-sm mt-0.5 line-clamp-2">{l.description}</p>}
                <div className="flex items-center justify-between mt-2">
                  <p className="text-gray-600 text-xs">{l.item_count} item{l.item_count !== 1 ? 's' : ''} · {l.list_type}</p>
                  <div className="flex items-center gap-1.5">
                    {(likeState[l.id]?.count ?? 0) > 0 && (
                      <span className="text-gray-500 text-xs">{likeState[l.id]?.count}</span>
                    )}
                    {user && !isMe && (
                      <button
                        onClick={e => toggleLike(l.id, e)}
                        className={`text-sm transition-colors ${likeState[l.id]?.liked ? 'text-pink-400' : 'text-gray-600 hover:text-pink-400'}`}
                        title={likeState[l.id]?.liked ? 'Unlike' : 'Like this list'}
                      >
                        ♥
                      </button>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
          <Pagination page={page} totalPages={Math.ceil(lists.length / LIST_PAGE_SIZE)} onPage={setPage} />
        </>
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
