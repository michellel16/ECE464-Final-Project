import { useState, useEffect, useMemo, useRef } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { Avatar } from '../components/Navbar'

const LIST_TYPES = ['custom', 'listened', 'want_to_listen', 'favorites']
const TYPE_LABELS = {
  custom:         'Custom',
  listened:       'Listened',
  want_to_listen: 'Want to Listen',
  favorites:      'Favorites',
}

const BLANK_FORM = { name: '', description: '', list_type: 'custom', is_public: true, cover_url: '', group_name: '' }

export default function Lists() {
  const { user } = useAuth()
  const [tab, setTab]               = useState('mine')
  const [lists, setLists]           = useState([])
  const [saved, setSaved]           = useState([])
  const [selected, setSelected]     = useState(null)
  const [showCreate, setCreate]     = useState(false)
  const [newList, setNewList]       = useState(BLANK_FORM)
  const [showEdit, setShowEdit]     = useState(false)
  const [editForm, setEditForm]     = useState(BLANK_FORM)
  const [loading, setLoading]       = useState(true)
  const [savedLoading, setSavedLoading] = useState(false)
  const [collapsedGroups, setCollapsedGroups] = useState(new Set())

  useEffect(() => {
    axios.get('/api/lists/me')
      .then(r => setLists(r.data))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (tab !== 'saved') return
    setSavedLoading(true)
    axios.get('/api/lists/saved')
      .then(r => setSaved(r.data))
      .finally(() => setSavedLoading(false))
  }, [tab])

  // --- group sidebar lists by group_name ---
  const { ungrouped, grouped } = useMemo(() => {
    const ug = [], g = {}
    lists.forEach(l => {
      if (l.group_name) {
        if (!g[l.group_name]) g[l.group_name] = []
        g[l.group_name].push(l)
      } else {
        ug.push(l)
      }
    })
    return { ungrouped: ug, grouped: g }
  }, [lists])

  // existing group names for datalist autocomplete
  const existingGroups = useMemo(() => [...new Set(lists.map(l => l.group_name).filter(Boolean))], [lists])

  function toggleGroup(name) {
    setCollapsedGroups(prev => {
      const next = new Set(prev)
      next.has(name) ? next.delete(name) : next.add(name)
      return next
    })
  }

  async function createList(e) {
    e.preventDefault()
    const payload = {
      ...newList,
      cover_url:  newList.cover_url  || null,
      group_name: newList.group_name || null,
    }
    const res = await axios.post('/api/lists/', payload)
    setLists(prev => [...prev, res.data])
    setNewList(BLANK_FORM)
    setCreate(false)
  }

  async function saveEdit(e) {
    e.preventDefault()
    const payload = {
      ...editForm,
      cover_url:  editForm.cover_url  || null,
      group_name: editForm.group_name || null,
    }
    const res = await axios.put(`/api/lists/${selected.id}`, payload)
    setLists(prev => prev.map(l => l.id === selected.id ? { ...l, ...res.data } : l))
    setSelected(prev => ({ ...prev, ...res.data }))
    setShowEdit(false)
  }

  function openEdit() {
    setEditForm({
      name:        selected.name,
      description: selected.description ?? '',
      list_type:   selected.list_type,
      is_public:   selected.is_public,
      cover_url:   selected.cover_url  ?? '',
      group_name:  selected.group_name ?? '',
    })
    setShowEdit(true)
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
      name: list.name, description: list.description ?? '',
      list_type: list.list_type, is_public: updated.is_public,
      cover_url: list.cover_url ?? null, group_name: list.group_name ?? null,
    })
    setLists(prev => prev.map(l => l.id === list.id ? { ...l, is_public: updated.is_public } : l))
    if (selected?.id === list.id) setSelected(prev => ({ ...prev, is_public: updated.is_public }))
  }

  async function removeItem(listId, itemId) {
    await axios.delete(`/api/lists/${listId}/items/${itemId}`)
    setSelected(prev => ({ ...prev, items: prev.items.filter(i => i.id !== itemId) }))
    setLists(prev => prev.map(l => l.id === listId ? { ...l, item_count: l.item_count - 1 } : l))
  }

  async function unlikeSaved(listId) {
    await axios.post(`/api/lists/${listId}/like`)
    setSaved(prev => prev.filter(l => l.id !== listId))
    if (selected?.id === listId) setSelected(null)
  }

  if (loading) return <Loader />

  // unique covers from selected list's items for the cover picker
  const itemCovers = selected
    ? [...new Set((selected.items ?? []).map(i => i.cover_url).filter(Boolean))]
    : []

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Lists</h1>
          <p className="text-gray-400 text-sm mt-1">Organize and discover music collections</p>
        </div>
        {tab === 'mine' && (
          <button onClick={() => setCreate(true)} className="btn-primary">+ New List</button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-xl p-1 w-fit mb-6">
        {[['mine', 'My Lists'], ['saved', 'Saved']].map(([key, label]) => (
          <button
            key={key}
            onClick={() => { setTab(key); setSelected(null) }}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === key ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── Create modal ── */}
      {showCreate && (
        <ListFormModal
          title="Create New List"
          form={newList}
          setForm={setNewList}
          onSubmit={createList}
          onClose={() => { setCreate(false); setNewList(BLANK_FORM) }}
          existingGroups={existingGroups}
          itemCovers={[]}
        />
      )}

      {/* ── Edit modal ── */}
      {showEdit && (
        <ListFormModal
          title="Edit List"
          form={editForm}
          setForm={setEditForm}
          onSubmit={saveEdit}
          onClose={() => setShowEdit(false)}
          existingGroups={existingGroups}
          itemCovers={itemCovers}
        />
      )}

      {/* ── My Lists tab ── */}
      {tab === 'mine' && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Sidebar */}
          <div className="space-y-3">
            {lists.length === 0 ? (
              <div className="card p-6 text-center text-gray-500">
                <p>No lists yet.</p>
                <button onClick={() => setCreate(true)} className="link-purple mt-1 text-sm">Create your first list</button>
              </div>
            ) : (
              <>
                {ungrouped.map(l => (
                  <SidebarItem key={l.id} list={l} selected={selected} onSelect={loadList} />
                ))}
                {Object.entries(grouped).map(([groupName, groupLists]) => {
                  const collapsed = collapsedGroups.has(groupName)
                  return (
                    <div key={groupName} className="space-y-1">
                      <button
                        onClick={() => toggleGroup(groupName)}
                        className="w-full flex items-center justify-between px-1 py-0.5 group"
                      >
                        <span className="text-[11px] uppercase tracking-widest text-gray-500 group-hover:text-gray-300 transition-colors font-medium">
                          {groupName}
                        </span>
                        <span className="flex items-center gap-1.5 text-gray-600 group-hover:text-gray-400 transition-colors">
                          <span className="text-[10px]">{groupLists.length}</span>
                          <span className="text-[9px]">{collapsed ? '▶' : '▼'}</span>
                        </span>
                      </button>
                      {!collapsed && (
                        <div className="space-y-1 pl-2 border-l border-gray-800">
                          {groupLists.map(l => (
                            <SidebarItem key={l.id} list={l} selected={selected} onSelect={loadList} />
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </>
            )}
          </div>

          {/* Detail panel */}
          <div className="lg:col-span-2">
            {!selected ? (
              <div className="card p-12 text-center text-gray-500">Select a list to view its contents</div>
            ) : (
              <div className="card overflow-hidden">
                {/* Cover banner — custom image or mosaic fallback */}
                {(selected.cover_url || selected.cover_previews?.length > 0) && (
                  <div className="h-56 overflow-hidden bg-gray-800">
                    <CoverMosaic coverUrl={selected.cover_url} previews={selected.cover_previews} />
                  </div>
                )}

                <div className="p-5 space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-bold text-white">{selected.name}</h2>
                      {selected.description && <p className="text-gray-400 text-sm mt-1">{selected.description}</p>}
                      <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-500">
                        <TypeBadge type={selected.list_type} />
                        {selected.group_name && (
                          <span className="text-gray-500 flex items-center gap-1">
                            <span className="text-gray-600">📁</span> {selected.group_name}
                          </span>
                        )}
                        <span>{selected.is_public ? 'Public' : 'Private'}</span>
                        <span>{selected.items?.length ?? 0} items</span>
                        {selected.like_count > 0 && <span>♥ {selected.like_count}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                      <button
                        onClick={openEdit}
                        className="text-xs px-3 py-1.5 rounded-full border border-gray-700 text-gray-400 hover:border-violet-600 hover:text-violet-400 transition-colors"
                      >
                        Edit
                      </button>
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
                            <Link to={item.url ?? '#'} className="text-white text-sm font-medium hover:text-violet-400 transition-colors truncate block">
                              {item.title}
                            </Link>
                            <p className="text-gray-500 text-xs">{item.type} · {item.artist}</p>
                            {item.notes && <p className="text-gray-500 text-xs italic mt-0.5">"{item.notes}"</p>}
                          </div>
                          <button onClick={() => removeItem(selected.id, item.id)} className="text-gray-600 hover:text-red-400 transition-colors text-sm">✕</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Saved tab ── */}
      {tab === 'saved' && (
        savedLoading ? <Loader /> :
        saved.length === 0 ? (
          <div className="card p-12 text-center text-gray-500">
            <p className="text-lg mb-1">No saved lists yet</p>
            <p className="text-sm">Browse the <Link to="/discover?tab=lists" className="text-violet-400 hover:text-violet-300">Discover page</Link> and save lists you like.</p>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="space-y-2">
              {saved.map(l => (
                <button
                  key={l.id}
                  onClick={() => loadList(l.id)}
                  className={`w-full text-left card transition-colors hover:border-violet-700 overflow-hidden ${
                    selected?.id === l.id ? 'border-violet-600 bg-violet-900/10' : ''
                  }`}
                >
                  {/* mini cover / mosaic */}
                  {(l.cover_url || l.cover_previews?.length > 0) && (
                    <div className="h-28 overflow-hidden bg-gray-800">
                      <CoverMosaic coverUrl={l.cover_url} previews={l.cover_previews} />
                    </div>
                  )}
                  <div className="p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <Avatar username={l.owner_username} avatarUrl={l.owner_avatar_url} size={4} />
                      <Link to={`/users/${l.owner_username}`} onClick={e => e.stopPropagation()} className="text-violet-400 text-xs hover:text-violet-300 transition-colors">
                        {l.owner_username}
                      </Link>
                    </div>
                    <p className="font-medium text-white text-sm">{l.name}</p>
                    {l.description && <p className="text-gray-500 text-xs mt-1 line-clamp-1">{l.description}</p>}
                    <div className="flex items-center justify-between mt-1">
                      <p className="text-gray-600 text-xs">{l.item_count} item{l.item_count !== 1 ? 's' : ''}</p>
                      <div className="flex items-center gap-2">
                        <span className="text-pink-400 text-xs">♥ {l.like_count}</span>
                        <button onClick={e => { e.stopPropagation(); unlikeSaved(l.id) }} className="text-xs text-gray-500 hover:text-red-400 transition-colors" title="Remove from saved">✕</button>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="lg:col-span-2">
              {!selected ? (
                <div className="card p-12 text-center text-gray-500">Select a saved list to view its contents</div>
              ) : (
                <div className="card overflow-hidden">
                  {(selected.cover_url || selected.cover_previews?.length > 0) && (
                    <div className="h-40 overflow-hidden bg-gray-800">
                      <CoverMosaic coverUrl={selected.cover_url} previews={selected.cover_previews} />
                    </div>
                  )}
                  <div className="p-5 space-y-4">
                    <div>
                      <h2 className="text-xl font-bold text-white">{selected.name}</h2>
                      {selected.description && <p className="text-gray-400 text-sm mt-1">{selected.description}</p>}
                      <div className="flex gap-3 mt-2 text-xs text-gray-500">
                        <TypeBadge type={selected.list_type} />
                        <span>{selected.items?.length ?? 0} items</span>
                        {selected.like_count > 0 && <span className="text-pink-400">♥ {selected.like_count}</span>}
                      </div>
                    </div>
                    {!selected.items?.length ? (
                      <div className="text-gray-500 text-sm py-8 text-center">This list is empty.</div>
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
                              <Link to={item.url ?? '#'} className="text-white text-sm font-medium hover:text-violet-400 transition-colors truncate block">{item.title}</Link>
                              <p className="text-gray-500 text-xs">{item.type} · {item.artist}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      )}
    </div>
  )
}

// ── Shared form modal (create + edit) ────────────────────────────────────────
function ListFormModal({ title, form, setForm, onSubmit, onClose, existingGroups, itemCovers }) {
  const set = (field, val) => setForm(f => ({ ...f, [field]: val }))
  const [coverUploading, setCoverUploading] = useState(false)
  const [coverError, setCoverError]         = useState(null)
  const fileInputRef = useRef(null)

  async function handleCoverUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setCoverError(null)
    setCoverUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data } = await axios.post('/api/lists/covers', fd)
      set('cover_url', data.url)
    } catch (err) {
      setCoverError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setCoverUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur flex items-center justify-center z-50 px-4">
      <div className="card w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <h2 className="font-bold text-white text-lg">{title}</h2>
        <form onSubmit={onSubmit} className="space-y-3">
          <input className="input" placeholder="List name" value={form.name} onChange={e => set('name', e.target.value)} required />
          <textarea className="input resize-none" rows={2} placeholder="Description (optional)" value={form.description} onChange={e => set('description', e.target.value)} />

          <div className="grid grid-cols-2 gap-3">
            <select className="input" value={form.list_type} onChange={e => set('list_type', e.target.value)}>
              {LIST_TYPES.map(t => <option key={t} value={t}>{TYPE_LABELS[t]}</option>)}
            </select>
            <div className="relative">
              <input
                className="input w-full"
                list="group-suggestions"
                placeholder="Group (optional)"
                value={form.group_name}
                onChange={e => set('group_name', e.target.value)}
              />
              <datalist id="group-suggestions">
                {existingGroups.map(g => <option key={g} value={g} />)}
              </datalist>
            </div>
          </div>

          {/* Cover image */}
          <div className="space-y-2">
            <p className="text-xs text-gray-500">Cover image</p>
            <div className="flex gap-2">
              <input
                className="input flex-1"
                placeholder="Paste a URL…"
                value={form.cover_url}
                onChange={e => { set('cover_url', e.target.value); setCoverError(null) }}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={coverUploading}
                className="shrink-0 px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:border-violet-600 hover:text-violet-400 transition-colors text-sm disabled:opacity-50 flex items-center gap-1.5"
              >
                {coverUploading ? (
                  <span className="w-3.5 h-3.5 border-2 border-violet-400 border-t-transparent rounded-full animate-spin inline-block" />
                ) : (
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                )}
                Upload
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                className="hidden"
                onChange={handleCoverUpload}
              />
            </div>
            {coverError && <p className="text-red-400 text-xs">{coverError}</p>}

            {/* Pick from item covers */}
            {itemCovers.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-1.5">Or pick from items in this list:</p>
                <div className="flex gap-2 flex-wrap">
                  {itemCovers.map(url => (
                    <button
                      key={url}
                      type="button"
                      onClick={() => set('cover_url', form.cover_url === url ? '' : url)}
                      className={`w-12 h-12 rounded-lg overflow-hidden border-2 transition-all ${
                        form.cover_url === url ? 'border-violet-500 scale-105' : 'border-transparent hover:border-gray-500'
                      }`}
                    >
                      <img src={url} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                  {form.cover_url && itemCovers.includes(form.cover_url) && (
                    <button type="button" onClick={() => set('cover_url', '')} className="text-xs text-gray-500 hover:text-red-400 self-center ml-1">✕ Clear</button>
                  )}
                </div>
              </div>
            )}

            {/* Preview */}
            {form.cover_url && (
              <div className="relative w-fit">
                <img src={form.cover_url} alt="" className="w-20 h-20 rounded-lg object-cover" onError={e => { e.target.style.display='none' }} />
                <button
                  type="button"
                  onClick={() => set('cover_url', '')}
                  className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-gray-800 border border-gray-600 text-gray-400 hover:text-red-400 text-xs flex items-center justify-center"
                >
                  ✕
                </button>
              </div>
            )}
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input type="checkbox" checked={form.is_public} onChange={e => set('is_public', e.target.checked)} className="rounded accent-violet-500" />
            Public list
          </label>

          <div className="flex gap-3 pt-2">
            <button type="submit" className="btn-primary">{title === 'Create New List' ? 'Create' : 'Save'}</button>
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Sidebar list item ─────────────────────────────────────────────────────────
function SidebarItem({ list: l, selected, onSelect }) {
  return (
    <button
      onClick={() => onSelect(l.id)}
      className={`w-full text-left card overflow-hidden transition-colors hover:border-violet-700 ${
        selected?.id === l.id ? 'border-violet-600 bg-violet-900/10' : ''
      }`}
    >
      {/* Cover image or mosaic fallback */}
      {(l.cover_url || l.cover_previews?.length > 0) && (
        <div className="h-28 overflow-hidden bg-gray-800">
          <CoverMosaic coverUrl={l.cover_url} previews={l.cover_previews} />
        </div>
      )}
      <div className="p-3">
        <div className="flex items-center justify-between gap-1">
          <p className="font-medium text-white text-sm truncate">{l.name}</p>
          <TypeBadge type={l.list_type} />
        </div>
        {l.description && <p className="text-gray-500 text-xs mt-0.5 line-clamp-1">{l.description}</p>}
        <div className="flex items-center justify-between mt-1">
          <p className="text-gray-600 text-xs">
            {l.item_count} item{l.item_count !== 1 ? 's' : ''}
            {!l.is_public && ' · Private'}
          </p>
          {l.like_count > 0 && <span className="text-gray-600 text-xs">♥ {l.like_count}</span>}
        </div>
      </div>
    </button>
  )
}

// ── Cover image mosaic ────────────────────────────────────────────────────────
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

// ── Helpers ───────────────────────────────────────────────────────────────────
function TypeBadge({ type }) {
  const colors = {
    custom:         'bg-gray-800 text-gray-400',
    listened:       'bg-green-900/40 text-green-400',
    want_to_listen: 'bg-blue-900/40 text-blue-400',
    favorites:      'bg-yellow-900/40 text-yellow-400',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${colors[type] ?? colors.custom}`}>
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
