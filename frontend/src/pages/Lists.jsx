import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'

const LIST_TYPES = ['custom', 'listened', 'want_to_listen', 'favorites']
const TYPE_LABELS = {
  custom:          'Custom',
  listened:        'Listened',
  want_to_listen:  'Want to Listen',
  favorites:       'Favorites',
}

export default function Lists() {
  const { user } = useAuth()
  const [lists, setLists]         = useState([])
  const [selected, setSelected]   = useState(null)
  const [showCreate, setCreate]   = useState(false)
  const [newList, setNewList]     = useState({ name: '', description: '', list_type: 'custom', is_public: true })
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    axios.get('/api/lists/me')
      .then(r => setLists(r.data))
      .finally(() => setLoading(false))
  }, [])

  async function createList(e) {
    e.preventDefault()
    const res = await axios.post('/api/lists/', newList)
    setLists(prev => [...prev, res.data])
    setNewList({ name: '', description: '', list_type: 'custom', is_public: true })
    setCreate(false)
  }

  async function deleteList(id) {
    await axios.delete(`/api/lists/${id}`)
    setLists(prev => prev.filter(l => l.id !== id))
    if (selected?.id === id) setSelected(null)
  }

  async function loadList(id) {
    const res = await axios.get(`/api/lists/${id}`)
    setSelected(res.data)
  }

  async function togglePublic(list) {
    const updated = { ...list, is_public: !list.is_public }
    await axios.put(`/api/lists/${list.id}`, {
      name: list.name,
      description: list.description ?? '',
      list_type: list.list_type,
      is_public: updated.is_public,
    })
    setLists(prev => prev.map(l => l.id === list.id ? { ...l, is_public: updated.is_public } : l))
    if (selected?.id === list.id) setSelected(prev => ({ ...prev, is_public: updated.is_public }))
  }

  async function removeItem(listId, itemId) {
    await axios.delete(`/api/lists/${listId}/items/${itemId}`)
    setSelected(prev => ({
      ...prev,
      items: prev.items.filter(i => i.id !== itemId),
    }))
    setLists(prev => prev.map(l => l.id === listId ? { ...l, item_count: l.item_count - 1 } : l))
  }

  if (loading) return <Loader />

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">My Lists</h1>
          <p className="text-gray-400 text-sm mt-1">Organize your music collection</p>
        </div>
        <button onClick={() => setCreate(true)} className="btn-primary">+ New List</button>
      </div>

      {/* Create list modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur flex items-center justify-center z-50 px-4">
          <div className="card w-full max-w-md p-6 space-y-4">
            <h2 className="font-bold text-white text-lg">Create New List</h2>
            <form onSubmit={createList} className="space-y-3">
              <input
                className="input"
                placeholder="List name"
                value={newList.name}
                onChange={e => setNewList({ ...newList, name: e.target.value })}
                required
              />
              <textarea
                className="input resize-none"
                rows={3}
                placeholder="Description (optional)"
                value={newList.description}
                onChange={e => setNewList({ ...newList, description: e.target.value })}
              />
              <select
                className="input"
                value={newList.list_type}
                onChange={e => setNewList({ ...newList, list_type: e.target.value })}
              >
                {LIST_TYPES.map(t => (
                  <option key={t} value={t}>{TYPE_LABELS[t]}</option>
                ))}
              </select>
              <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newList.is_public}
                  onChange={e => setNewList({ ...newList, is_public: e.target.checked })}
                  className="rounded accent-violet-500"
                />
                Public list
              </label>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary">Create</button>
                <button type="button" onClick={() => setCreate(false)} className="btn-secondary">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* List sidebar */}
        <div className="space-y-2">
          {lists.length === 0 ? (
            <div className="card p-6 text-center text-gray-500">
              <p>No lists yet.</p>
              <button onClick={() => setCreate(true)} className="link-purple mt-1 text-sm">Create your first list</button>
            </div>
          ) : (
            lists.map(l => (
              <button
                key={l.id}
                onClick={() => loadList(l.id)}
                className={`w-full text-left card p-4 transition-colors hover:border-violet-700 ${
                  selected?.id === l.id ? 'border-violet-600 bg-violet-900/10' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <p className="font-medium text-white text-sm">{l.name}</p>
                  <TypeBadge type={l.list_type} />
                </div>
                {l.description && <p className="text-gray-500 text-xs mt-1 line-clamp-1">{l.description}</p>}
                <p className="text-gray-600 text-xs mt-1">
                  {l.item_count} item{l.item_count !== 1 ? 's' : ''}
                  {!l.is_public && ' · Private'}
                </p>
              </button>
            ))
          )}
        </div>

        {/* List detail */}
        <div className="lg:col-span-2">
          {!selected ? (
            <div className="card p-12 text-center text-gray-500">
              Select a list to view its contents
            </div>
          ) : (
            <div className="card p-5 space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-white">{selected.name}</h2>
                  {selected.description && <p className="text-gray-400 text-sm mt-1">{selected.description}</p>}
                  <div className="flex gap-3 mt-2 text-xs text-gray-500">
                    <TypeBadge type={selected.list_type} />
                    <span>{selected.is_public ? 'Public' : 'Private'}</span>
                    <span>{selected.items?.length ?? 0} items</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <button
                    onClick={() => togglePublic(selected)}
                    className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                      selected.is_public
                        ? 'border-gray-600 text-gray-400 hover:border-red-700 hover:text-red-400'
                        : 'border-green-700/50 text-green-400 hover:bg-green-700/20'
                    }`}
                  >
                    {selected.is_public ? 'Make Private' : 'Make Public'}
                  </button>
                  <button
                    onClick={() => deleteList(selected.id)}
                    className="text-red-400 hover:text-red-300 text-sm transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {!selected.items?.length ? (
                <div className="text-gray-500 text-sm py-8 text-center">
                  This list is empty. Add albums or songs from their pages.
                </div>
              ) : (
                <div className="space-y-2">
                  {selected.items.map(item => (
                    <div key={item.id} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                      {item.cover_url ? (
                        <img src={item.cover_url} alt="" className="w-10 h-10 rounded object-cover shrink-0" loading="lazy" />
                      ) : (
                        <div className="w-10 h-10 rounded bg-gray-700 flex items-center justify-center shrink-0">♪</div>
                      )}
                      <div className="flex-1 min-w-0">
                        <Link
                          to={item.url ?? '#'}
                          className="text-white text-sm font-medium hover:text-violet-400 transition-colors truncate block"
                        >
                          {item.title}
                        </Link>
                        <p className="text-gray-500 text-xs">{item.type} · {item.artist}</p>
                        {item.notes && <p className="text-gray-500 text-xs italic mt-0.5">"{item.notes}"</p>}
                      </div>
                      <button
                        onClick={() => removeItem(selected.id, item.id)}
                        className="text-gray-600 hover:text-red-400 transition-colors text-sm"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function TypeBadge({ type }) {
  const colors = {
    custom:         'bg-gray-800 text-gray-400',
    listened:       'bg-green-900/40 text-green-400',
    want_to_listen: 'bg-blue-900/40 text-blue-400',
    favorites:      'bg-yellow-900/40 text-yellow-400',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${colors[type] ?? colors.custom}`}>
      {TYPE_LABELS[type] ?? type}
    </span>
  )
}

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
