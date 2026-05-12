import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { Avatar } from '../components/Navbar'

const TYPE_LABELS = {
  custom: 'Custom', listened: 'Listened',
  want_to_listen: 'Want to Listen', favorites: 'Favorites',
}
const TYPE_COLORS = {
  custom:         'bg-gray-800 text-gray-400',
  listened:       'bg-green-900/40 text-green-400',
  want_to_listen: 'bg-blue-900/40 text-blue-400',
  favorites:      'bg-yellow-900/40 text-yellow-400',
}

export default function ListDetail() {
  const { id }      = useParams()
  const { user }    = useAuth()
  const navigate    = useNavigate()
  const [list, setList]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [liked, setLiked]       = useState(false)
  const [likeCount, setLikeCount] = useState(0)
  const [forking, setForking]   = useState(false)
  const [forked, setForked]     = useState(false)
  const [members, setMembers]   = useState([])
  const [memberInput, setMemberInput] = useState('')
  const [memberRole, setMemberRole]   = useState('viewer')
  const [addingMember, setAddingMember] = useState(false)
  const [memberError, setMemberError]   = useState(null)

  useEffect(() => {
    axios.get(`/api/lists/${id}`)
      .then(r => {
        setList(r.data)
        setLiked(r.data.is_liked)
        setLikeCount(r.data.like_count)
        setMembers(r.data.members ?? [])
      })
      .catch(() => navigate('/discover?tab=lists', { replace: true }))
      .finally(() => setLoading(false))
  }, [id])

  async function toggleLike() {
    if (!user) return
    const prev = liked
    setLiked(!prev)
    setLikeCount(c => c + (prev ? -1 : 1))
    try {
      await axios.post(`/api/lists/${id}/like`)
    } catch {
      setLiked(prev)
      setLikeCount(c => c + (prev ? 1 : -1))
    }
  }

  async function forkList() {
    if (!user || forking) return
    setForking(true)
    try {
      await axios.post(`/api/lists/${id}/fork`)
      setForked(true)
    } catch {
    } finally {
      setForking(false)
    }
  }

  async function addMember(e) {
    e.preventDefault()
    if (!memberInput.trim()) return
    setAddingMember(true)
    setMemberError(null)
    try {
      await axios.post(`/api/lists/${id}/members`, { username: memberInput.trim(), role: memberRole })
      const r = await axios.get(`/api/lists/${id}/members`)
      setMembers(r.data)
      setMemberInput('')
    } catch (err) {
      setMemberError(err.response?.data?.detail ?? 'Could not add member.')
    } finally {
      setAddingMember(false)
    }
  }

  async function removeMember(username) {
    try {
      await axios.delete(`/api/lists/${id}/members/${username}`)
      setMembers(prev => prev.filter(m => m.username !== username))
    } catch {}
  }

  async function updateMemberRole(username, newRole) {
    try {
      await axios.post(`/api/lists/${id}/members`, { username, role: newRole })
      setMembers(prev => prev.map(m => m.username === username ? { ...m, role: newRole } : m))
    } catch {}
  }

  async function acceptInvite() {
    try {
      await axios.post(`/api/lists/invites/${id}/accept`)
      setList(prev => ({ ...prev, viewer_role: prev.members?.find(m => m.status === 'pending')?.role ?? 'viewer' }))
      // Reload to get updated viewer_role from server
      const r = await axios.get(`/api/lists/${id}`)
      setList(r.data)
    } catch {}
  }

  async function declineInvite() {
    try {
      await axios.post(`/api/lists/invites/${id}/decline`)
      if (!list.is_public) {
        navigate(-1)
      } else {
        setList(prev => ({ ...prev, viewer_role: null }))
      }
    } catch {}
  }

  async function leaveList() {
    if (!window.confirm('Leave this list? You will lose access.')) return
    try {
      await axios.post(`/api/lists/${id}/leave`)
      if (!list.is_public) {
        navigate(-1)
      } else {
        setList(prev => ({ ...prev, viewer_role: null }))
      }
    } catch {}
  }

  if (loading) return <Loader />
  if (!list) return null

  const isOwner   = user?.username === list.owner_username
  const canAct    = user && !isOwner
  const isPending = list.viewer_role === 'pending'
  const isCollab  = list.viewer_role === 'editor' || list.viewer_role === 'viewer'

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-4">
      {/* Back link */}
      <button onClick={() => navigate(-1)} className="text-gray-500 hover:text-white text-sm transition-colors flex items-center gap-1">
        ← Back
      </button>

      {/* Header card */}
      <div className="card overflow-hidden">
        {/* Cover banner */}
        {(list.cover_url || list.cover_previews?.length > 0) && (
          <div className="h-40 overflow-hidden bg-gray-800">
            <CoverMosaic coverUrl={list.cover_url} previews={list.cover_previews} />
          </div>
        )}
        <div className="p-4">
        <div className="flex items-start gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE_COLORS[list.list_type] ?? TYPE_COLORS.custom}`}>
                {TYPE_LABELS[list.list_type] ?? list.list_type}
              </span>
              {!list.is_public && (
                <span className="text-xs text-gray-500 border border-gray-700 px-2 py-0.5 rounded-full">Private</span>
              )}
            </div>

            <h1 className="text-xl font-bold text-white mt-2 leading-tight">{list.name}</h1>
            {list.description && (
              <p className="text-gray-400 text-sm mt-2 leading-relaxed">{list.description}</p>
            )}

            <div className="flex items-center gap-3 mt-4 flex-wrap">
              <Link to={`/users/${list.owner_username}`} className="flex items-center gap-2 group">
                <Avatar username={list.owner_username} avatarUrl={list.owner_avatar_url} size={6} />
                <span className="text-violet-400 text-sm group-hover:text-violet-300 transition-colors">
                  {list.owner_username}
                </span>
              </Link>
              <span className="text-gray-700">·</span>
              <span className="text-gray-500 text-sm">{list.items?.length ?? 0} items</span>
              {likeCount > 0 && (
                <>
                  <span className="text-gray-700">·</span>
                  <span className="text-gray-500 text-sm">♥ {likeCount} {likeCount === 1 ? 'save' : 'saves'}</span>
                </>
              )}
            </div>
          </div>

          {/* Action buttons */}
          {canAct && (
            <div className="flex flex-col gap-2 shrink-0">
              <button
                onClick={toggleLike}
                className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold border transition-all min-w-[90px] ${
                  liked
                    ? 'bg-pink-600/20 border-pink-500/40 text-pink-400 hover:bg-pink-600/30'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-pink-500/40 hover:text-pink-400'
                }`}
              >
                <span>{liked ? '♥' : '♡'}</span>
                {liked ? 'Saved' : 'Save'}
              </button>
              <button
                onClick={forkList}
                disabled={forking || forked}
                className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border transition-all disabled:opacity-60 min-w-[90px] ${
                  forked
                    ? 'border-violet-500/40 text-violet-400 bg-violet-900/20'
                    : 'border-gray-700 text-gray-400 bg-gray-800 hover:border-violet-500/40 hover:text-violet-400'
                }`}
                title="Save an editable copy to your lists"
              >
                {forked ? '✓ Copied' : forking ? '…' : '⎘ Copy'}
              </button>
              {forked && (
                <Link to="/lists" className="text-[11px] text-center text-violet-400 hover:text-violet-300 underline">
                  View in My Lists →
                </Link>
              )}
            </div>
          )}
        </div>
        </div>
      </div>

      {/* Pending invite banner */}
      {isPending && (
        <div className="card p-4 border-yellow-800/50 bg-yellow-900/10">
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <p className="text-yellow-300 text-sm font-medium">
                {list.owner_username} invited you to collaborate
              </p>
              <p className="text-gray-500 text-xs mt-0.5">
                Accept to gain access to this list.
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                onClick={acceptInvite}
                className="px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold transition-colors"
              >
                Accept
              </button>
              <button
                onClick={declineInvite}
                className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold transition-colors"
              >
                Decline
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Collab banner for accepted members */}
      {isCollab && (
        <div className="card p-4 border-violet-800/50 bg-violet-900/10">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <p className="text-violet-300 text-sm font-medium">
                {list.viewer_role === 'editor' ? 'You can edit this list' : 'Shared with you'}
              </p>
              <p className="text-gray-500 text-xs">
                {list.viewer_role === 'editor'
                  ? 'You have editor access — you can add and remove items.'
                  : 'You have viewer access to this list.'}
              </p>
            </div>
            <button
              onClick={leaveList}
              className="shrink-0 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-red-900/30 border border-gray-700 hover:border-red-700/50 text-gray-400 hover:text-red-400 text-xs font-medium transition-all"
            >
              Leave
            </button>
          </div>
        </div>
      )}

      {/* Items */}
      {!list.items?.length ? (
        <div className="card p-12 text-center text-gray-500">This list is empty.</div>
      ) : (
        <div className="space-y-1.5">
          {list.items.map((item, i) => (
            <Link
              key={item.id}
              to={item.url ?? '#'}
              className="card p-3 flex items-center gap-3 hover:border-violet-700 transition-colors group"
            >
              <span className="text-gray-600 text-xs w-5 text-right shrink-0 tabular-nums">{i + 1}</span>
              {item.cover_url ? (
                <img src={item.cover_url} alt="" className="w-10 h-10 rounded object-cover shrink-0" loading="lazy" />
              ) : (
                <div className="w-10 h-10 rounded bg-gray-800 flex items-center justify-center text-gray-600 shrink-0">♪</div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium truncate group-hover:text-violet-400 transition-colors">
                  {item.title}
                </p>
                <p className="text-gray-500 text-xs truncate capitalize">
                  {item.type} · {item.artist}
                </p>
                {item.notes && (
                  <p className="text-gray-600 text-xs italic mt-0.5">"{item.notes}"</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Members panel — owner only */}
      {isOwner && (
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold text-white text-base">Shared with</h2>

          {/* Add member form */}
          <form onSubmit={addMember} className="flex gap-2 flex-wrap">
            <input
              className="input flex-1 min-w-0"
              placeholder="Username…"
              value={memberInput}
              onChange={e => { setMemberInput(e.target.value); setMemberError(null) }}
            />
            <select
              className="input w-28 shrink-0"
              value={memberRole}
              onChange={e => setMemberRole(e.target.value)}
            >
              <option value="viewer">Viewer</option>
              <option value="editor">Editor</option>
            </select>
            <button
              type="submit"
              disabled={addingMember || !memberInput.trim()}
              className="btn-primary shrink-0 disabled:opacity-50"
            >
              {addingMember ? '…' : 'Add'}
            </button>
          </form>
          {memberError && <p className="text-red-400 text-sm">{memberError}</p>}

          {/* Member list */}
          <div className="space-y-2">
            {/* Owner row — always first */}
            <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
              <Avatar username={list.owner_username} avatarUrl={list.owner_avatar_url} size={6} />
              <Link to={`/users/${list.owner_username}`} className="flex-1 text-sm font-medium text-white hover:text-violet-400 transition-colors">
                {list.owner_username}
              </Link>
              <span className="text-xs px-2 py-0.5 rounded-full bg-violet-900/40 text-violet-400">
                Owner
              </span>
            </div>

            {members.length === 0 ? (
              <p className="text-gray-600 text-sm px-1">No one else has access yet.</p>
            ) : members.map(m => (
              <div key={m.username} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                <Avatar username={m.username} avatarUrl={m.avatar_url} size={6} />
                <Link to={`/users/${m.username}`} className="flex-1 text-sm font-medium text-white hover:text-violet-400 transition-colors">
                  {m.username}
                </Link>
                {m.status === 'pending' ? (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-900/40 text-yellow-400">Pending</span>
                ) : (
                  <select
                    value={m.role}
                    onChange={e => updateMemberRole(m.username, e.target.value)}
                    className="text-xs bg-gray-700 border border-gray-600 text-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:border-violet-500 cursor-pointer"
                  >
                    <option value="viewer">Viewer</option>
                    <option value="editor">Editor</option>
                  </select>
                )}
                <button
                  onClick={() => removeMember(m.username)}
                  className="text-gray-600 hover:text-red-400 transition-colors text-sm ml-1"
                  title="Remove"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function CoverMosaic({ coverUrl, previews = [] }) {
  if (coverUrl) {
    return <img src={coverUrl} alt="" className="w-full h-full object-cover" loading="lazy" />
  }
  const p = previews.slice(0, 4)
  if (!p.length) return null
  if (p.length === 1) {
    return <img src={p[0]} alt="" className="w-full h-full object-cover" loading="lazy" />
  }
  return (
    <div className="grid grid-cols-2 h-full">
      {p.map((url, i) => (
        <img key={i} src={url} alt="" className="w-full h-full object-cover" loading="lazy" />
      ))}
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
