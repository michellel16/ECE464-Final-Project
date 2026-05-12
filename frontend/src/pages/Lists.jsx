import { useState, useEffect, useMemo, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
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

const GROUP_COLORS = [
  { border: 'border-violet-600/60', dot: 'bg-violet-500', label: 'text-violet-300', header: 'bg-violet-900/50 hover:bg-violet-900/70', icon: 'text-violet-400' },
  { border: 'border-pink-600/60',   dot: 'bg-pink-500',   label: 'text-pink-300',   header: 'bg-pink-900/50 hover:bg-pink-900/70',   icon: 'text-pink-400' },
  { border: 'border-blue-600/60',   dot: 'bg-blue-500',   label: 'text-blue-300',   header: 'bg-blue-900/50 hover:bg-blue-900/70',   icon: 'text-blue-400' },
  { border: 'border-emerald-600/60',dot: 'bg-emerald-500',label: 'text-emerald-300',header: 'bg-emerald-900/50 hover:bg-emerald-900/70', icon: 'text-emerald-400' },
  { border: 'border-amber-600/60',  dot: 'bg-amber-500',  label: 'text-amber-300',  header: 'bg-amber-900/50 hover:bg-amber-900/70', icon: 'text-amber-400' },
  { border: 'border-cyan-600/60',   dot: 'bg-cyan-500',   label: 'text-cyan-300',   header: 'bg-cyan-900/50 hover:bg-cyan-900/70',   icon: 'text-cyan-400' },
]

const BLANK_FORM = { name: '', description: '', list_type: 'custom', is_public: true, cover_url: '', group_name: '' }

export default function Lists() {
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const [tab, setTab]               = useState(() => {
    const t = searchParams.get('tab')
    return t === 'collab' || t === 'saved' ? t : 'mine'
  })
  const [lists, setLists]           = useState([])
  const [saved, setSaved]           = useState([])
  const [collab, setCollab]         = useState([])
  const [invites, setInvites]       = useState([])
  const [selected, setSelected]     = useState(null)
  const [showCreate, setCreate]     = useState(false)
  const [newList, setNewList]       = useState(BLANK_FORM)
  const [showEdit, setShowEdit]     = useState(false)
  const [editForm, setEditForm]     = useState(BLANK_FORM)
  const [loading, setLoading]       = useState(true)
  const [savedLoading, setSavedLoading]   = useState(false)
  const [collabLoading, setCollabLoading] = useState(false)
  const [collapsedGroups, setCollapsedGroups] = useState(new Set())
  const [draggingId, setDraggingId]       = useState(null)
  const [dropTarget, setDropTarget]       = useState(null)
  const [showShare, setShowShare]         = useState(false)
  const [pendingGroups, setPendingGroups] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tunelog_pending_groups') || '[]') }
    catch { return [] }
  })
  const [showCreateMenu, setCreateMenu]   = useState(false)
  const [showFolderCreate, setFolderCreate] = useState(false)
  const [sidebarSearch, setSidebarSearch] = useState('')
  const [dropBeforeId, setDropBeforeId]   = useState(null)
  const [listOrder, setListOrder] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tunelog_lists_order') || '[]') }
    catch { return [] }
  })
  const [folderOrder, setFolderOrder] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tunelog_folder_order') || '[]') }
    catch { return [] }
  })
  const [draggingFolder, setDraggingFolder] = useState(null)
  const [dropBeforeFolder, setDropBeforeFolder] = useState(null)
  const [editingFolder, setEditingFolder]   = useState(null)
  const [editFolderName, setEditFolderName] = useState('')
  const createMenuRef = useRef(null)

  // Persist custom order and empty folders
  useEffect(() => {
    localStorage.setItem('tunelog_lists_order', JSON.stringify(listOrder))
  }, [listOrder])

  useEffect(() => {
    localStorage.setItem('tunelog_pending_groups', JSON.stringify(pendingGroups))
  }, [pendingGroups])

  useEffect(() => {
    localStorage.setItem('tunelog_folder_order', JSON.stringify(folderOrder))
  }, [folderOrder])

  useEffect(() => {
    axios.get('/api/lists/me')
      .then(r => {
        setLists(r.data)
        setListOrder(prev => {
          const ids = r.data.map(l => l.id)
          return [...prev.filter(id => ids.includes(id)), ...ids.filter(id => !prev.includes(id))]
        })
      })
      .finally(() => setLoading(false))
  }, [])

  // Fetch invite count for badge even before visiting Collab tab
  useEffect(() => {
    axios.get('/api/lists/invites').then(r => setInvites(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (tab !== 'saved') return
    setSavedLoading(true)
    axios.get('/api/lists/saved')
      .then(r => setSaved(r.data))
      .finally(() => setSavedLoading(false))
  }, [tab])

  useEffect(() => {
    if (tab !== 'collab') return
    setCollabLoading(true)
    Promise.all([
      axios.get('/api/lists/collab'),
      axios.get('/api/lists/invites'),
    ]).then(([cr, ir]) => {
      setCollab(cr.data)
      setInvites(ir.data)
    }).finally(() => setCollabLoading(false))
  }, [tab])

  // Close create menu on outside click
  useEffect(() => {
    function handler(e) {
      if (createMenuRef.current && !createMenuRef.current.contains(e.target)) setCreateMenu(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // --- group sidebar lists by group_name (include pending empty folders) ---
  const { ungrouped, grouped } = useMemo(() => {
    const q = sidebarSearch.toLowerCase()
    const ug = [], g = {}
    lists.forEach(l => {
      if (l.group_name) {
        if (!g[l.group_name]) g[l.group_name] = []
        g[l.group_name].push(l)
      } else {
        ug.push(l)
      }
    })
    pendingGroups.forEach(name => { if (!g[name]) g[name] = [] })
    const byOrder = arr =>
      [...(q ? arr.filter(l => l.name.toLowerCase().includes(q)) : arr)]
        .sort((a, b) => {
          const ai = listOrder.indexOf(a.id), bi = listOrder.indexOf(b.id)
          return (ai < 0 ? Infinity : ai) - (bi < 0 ? Infinity : bi)
        })
    return {
      ungrouped: byOrder(ug),
      grouped: Object.fromEntries(
        Object.entries(g)
          .map(([k, v]) => [k, byOrder(v)])
          .filter(([, v]) => v.length > 0 || !q)
      ),
    }
  }, [lists, pendingGroups, listOrder, sidebarSearch])

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
    setListOrder(prev => [...prev, res.data.id])
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
    setListOrder(prev => prev.filter(oid => oid !== id))
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

  function handleDragStart(e, listId) {
    e.dataTransfer.setData('list_id', String(listId))
    e.dataTransfer.effectAllowed = 'move'
    setDraggingId(listId)
  }

  function handleDragEnd() {
    setDraggingId(null)
    setDropTarget(null)
    setDropBeforeId(null)
  }

  function handleDragOverItem(id) {
    setDropBeforeId(id)
    setDropTarget(null)
  }

  async function handleDropOnItem(e, beforeId) {
    e.preventDefault()
    e.stopPropagation()
    const draggedId = parseInt(e.dataTransfer.getData('list_id'), 10)
    if (!draggedId || draggedId === beforeId) { handleDragEnd(); return }
    const dragged = lists.find(l => l.id === draggedId)
    const before  = lists.find(l => l.id === beforeId)
    if (!dragged || !before) { handleDragEnd(); return }

    // Reorder in custom order
    setListOrder(prev => {
      const order = [...prev]
      const from = order.indexOf(draggedId)
      if (from !== -1) order.splice(from, 1)
      const to = order.indexOf(beforeId)
      order.splice(to < 0 ? order.length : to, 0, draggedId)
      return order
    })

    // Also change group if dropping into a different group's items
    if (dragged.group_name !== before.group_name) {
      const newGroup = before.group_name
      const oldGroup = dragged.group_name
      // If the source group will become empty, keep it alive in pendingGroups
      if (oldGroup) {
        const remainingInOld = lists.filter(l => l.id !== draggedId && l.group_name === oldGroup)
        if (remainingInOld.length === 0) {
          setPendingGroups(prev => prev.includes(oldGroup) ? prev : [...prev, oldGroup])
        }
      }
      setLists(all => all.map(l => l.id === draggedId ? { ...l, group_name: newGroup } : l))
      try {
        await axios.put(`/api/lists/${draggedId}`, {
          name: dragged.name, description: dragged.description ?? '',
          list_type: dragged.list_type, is_public: dragged.is_public,
          cover_url: dragged.cover_url ?? null, group_name: newGroup,
        })
      } catch {
        setLists(all => all.map(l => l.id === draggedId ? { ...l, group_name: dragged.group_name } : l))
      }
    }

    handleDragEnd()
  }

  async function handleDrop(e, targetGroup) {
    e.preventDefault()
    setDropTarget(null)
    setDraggingId(null)
    setDropBeforeId(null)
    const listId = parseInt(e.dataTransfer.getData('list_id'), 10)
    const lst = lists.find(l => l.id === listId)
    if (!lst) return
    const newGroup = targetGroup === '__ungrouped__' ? null : targetGroup
    if (lst.group_name === newGroup) return
    const oldGroup = lst.group_name
    // If the source group will become empty, keep it alive in pendingGroups
    if (oldGroup) {
      const remainingInOld = lists.filter(l => l.id !== listId && l.group_name === oldGroup)
      if (remainingInOld.length === 0) {
        setPendingGroups(prev => prev.includes(oldGroup) ? prev : [...prev, oldGroup])
      }
    }
    setLists(all => all.map(l => l.id === listId ? { ...l, group_name: newGroup } : l))
    try {
      await axios.put(`/api/lists/${listId}`, {
        name: lst.name, description: lst.description ?? '',
        list_type: lst.list_type, is_public: lst.is_public,
        cover_url: lst.cover_url ?? null, group_name: newGroup,
      })
    } catch {
      setLists(all => all.map(l => l.id === listId ? { ...l, group_name: oldGroup } : l))
    }
  }

  function handleFolderDragStart(e, groupName) {
    e.dataTransfer.setData('folder_name', groupName)
    e.dataTransfer.effectAllowed = 'move'
    setDraggingFolder(groupName)
  }

  function handleFolderDragEnd() {
    setDraggingFolder(null)
    setDropBeforeFolder(null)
  }

  function handleFolderDrop(e, beforeName, currentOrder) {
    e.preventDefault()
    e.stopPropagation()
    const draggedName = e.dataTransfer.getData('folder_name')
    if (!draggedName) return
    setFolderOrder(() => {
      const order = currentOrder.filter(n => n !== draggedName)
      const idx = beforeName === '__end__' ? order.length : order.indexOf(beforeName)
      order.splice(idx < 0 ? order.length : idx, 0, draggedName)
      return order
    })
    setDraggingFolder(null)
    setDropBeforeFolder(null)
  }

  async function submitRenameFolder(oldName, newName) {
    const trimmed = newName.trim()
    setEditingFolder(null)
    if (!trimmed || trimmed === oldName) return
    const allGroups = [...new Set([...lists.map(l => l.group_name).filter(Boolean), ...pendingGroups])]
    if (allGroups.some(g => g !== oldName && g.toLowerCase() === trimmed.toLowerCase())) return
    const toUpdate = lists.filter(l => l.group_name === oldName)
    setLists(all => all.map(l => l.group_name === oldName ? { ...l, group_name: trimmed } : l))
    setPendingGroups(prev => prev.map(g => g === oldName ? trimmed : g))
    setFolderOrder(prev => prev.map(g => g === oldName ? trimmed : g))
    await Promise.all(toUpdate.map(l =>
      axios.put(`/api/lists/${l.id}`, {
        name: l.name, description: l.description ?? '',
        list_type: l.list_type, is_public: l.is_public,
        cover_url: l.cover_url ?? null, group_name: trimmed,
      })
    ))
  }

  function createFolder(name) {
    setPendingGroups(prev => prev.includes(name) ? prev : [...prev, name])
    setFolderCreate(false)
    setCreateMenu(false)
  }

  async function deleteFolder(groupName, groupLists) {
    const msg = groupLists.length === 0
      ? `Delete folder "${groupName}"?`
      : `Delete folder "${groupName}"? Its ${groupLists.length} list${groupLists.length !== 1 ? 's' : ''} will be moved to ungrouped.`
    if (!window.confirm(msg)) return
    setPendingGroups(prev => prev.filter(g => g !== groupName))
    if (groupLists.length === 0) return
    // Optimistically ungroup all lists inside
    setLists(all => all.map(l => l.group_name === groupName ? { ...l, group_name: null } : l))
    try {
      await Promise.all(groupLists.map(lst =>
        axios.put(`/api/lists/${lst.id}`, {
          name: lst.name, description: lst.description ?? '',
          list_type: lst.list_type, is_public: lst.is_public,
          cover_url: lst.cover_url ?? null, group_name: null,
        })
      ))
    } catch {
      setLists(all => all.map(l =>
        groupLists.some(gl => gl.id === l.id) ? { ...l, group_name: groupName } : l
      ))
    }
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
          <h1 className="text-3xl font-bold text-white font-display">Lists</h1>
          <p className="text-gray-400 text-sm mt-1">Organize and discover music collections</p>
        </div>
        {tab === 'mine' && (
          <div className="relative" ref={createMenuRef}>
            <button
              onClick={() => setCreateMenu(v => !v)}
              className="btn-primary flex items-center gap-1.5"
            >
              Create <span className="text-xs opacity-70">▾</span>
            </button>
            {showCreateMenu && (
              <div className="absolute right-0 top-full mt-1 w-40 bg-gray-900 border border-gray-800 rounded-xl shadow-xl z-20 overflow-hidden">
                <button
                  onClick={() => { setCreate(true); setCreateMenu(false) }}
                  className="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
                >
                  New List
                </button>
                <button
                  onClick={() => { setFolderCreate(true); setCreateMenu(false) }}
                  className="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
                >
                  New Folder
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-xl p-1 w-fit mb-6">
        {[['mine', 'My Lists'], ['collab', 'Collab'], ['saved', 'Saved']].map(([key, label]) => (
          <button
            key={key}
            onClick={() => { setTab(key); setSelected(null) }}
            className={`relative px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === key ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            {label}
            {key === 'collab' && invites.length > 0 && tab !== 'collab' && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-500 text-black text-[10px] font-bold rounded-full flex items-center justify-center">
                {invites.length}
              </span>
            )}
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

      {/* ── Share modal ── */}
      {showShare && selected && (
        <ShareModal listId={selected.id} listName={selected.name} onClose={() => setShowShare(false)} />
      )}

      {/* ── New Folder modal ── */}
      {showFolderCreate && (
        <FolderCreateModal
          existingGroups={existingGroups}
          onConfirm={createFolder}
          onClose={() => setFolderCreate(false)}
        />
      )}

      {/* ── My Lists tab ── */}
      {tab === 'mine' && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Sidebar — entire column is the ungroup drop zone */}
          <div
            className={`space-y-3 rounded-xl transition-all ${draggingId !== null && dropTarget === '__ungrouped__' ? 'ring-1 ring-dashed ring-violet-500/50 bg-violet-900/5' : ''}`}
            onDragOver={e => { e.preventDefault(); setDropTarget('__ungrouped__') }}
            onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget)) setDropTarget(null) }}
            onDrop={e => handleDrop(e, '__ungrouped__')}
          >
            {/* Search */}
            <input
              className="input text-sm w-full"
              placeholder="Search lists…"
              value={sidebarSearch}
              onChange={e => setSidebarSearch(e.target.value)}
            />
            {lists.length === 0 ? (
              <div className="card p-6 text-center text-gray-500">
                <p>No lists yet.</p>
                <button onClick={() => setCreate(true)} className="link-purple mt-1 text-sm">Create your first list</button>
              </div>
            ) : (
              <>
                {/* Ungrouped items */}
                <div className="space-y-1">
                  {ungrouped.map(l => (
                    <SidebarItem key={l.id} list={l} selected={selected} onSelect={loadList}
                      draggingId={draggingId} onDragStart={handleDragStart} onDragEnd={handleDragEnd}
                      dropBeforeId={dropBeforeId} onDragOverItem={handleDragOverItem} onDropOnItem={handleDropOnItem} />
                  ))}
                </div>

                {(() => {
                  const sortedGroups = Object.entries(grouped).sort(([a], [b]) => {
                    const ai = folderOrder.indexOf(a), bi = folderOrder.indexOf(b)
                    return (ai < 0 ? Infinity : ai) - (bi < 0 ? Infinity : bi)
                  })
                  const sortedNames = sortedGroups.map(([name]) => name)
                  return (
                    <>
                      {sortedGroups.map(([groupName, groupLists], idx) => {
                        const collapsed = collapsedGroups.has(groupName)
                        const color = GROUP_COLORS[idx % GROUP_COLORS.length]
                        const isListTarget = dropTarget === groupName
                        const isFolderTarget = dropBeforeFolder === groupName && draggingFolder && draggingFolder !== groupName
                        return (
                          <div key={groupName}>
                            {/* Folder reorder drop indicator */}
                            {isFolderTarget && (
                              <div className="h-0.5 bg-violet-500 rounded-full mx-1 mb-1" />
                            )}
                            <div
                              draggable
                              onDragStart={e => handleFolderDragStart(e, groupName)}
                              onDragEnd={handleFolderDragEnd}
                              className={`rounded-xl overflow-hidden transition-all ${draggingFolder === groupName ? 'opacity-30' : ''} ${isListTarget ? `ring-2 ring-dashed ${color.border}` : ''}`}
                              onDragOver={e => {
                                e.preventDefault()
                                e.stopPropagation()
                                if (e.dataTransfer.types.includes('folder_name')) {
                                  setDropBeforeFolder(groupName)
                                } else {
                                  setDropTarget(groupName)
                                }
                              }}
                              onDragLeave={e => {
                                if (!e.currentTarget.contains(e.relatedTarget)) {
                                  setDropTarget(null)
                                  setDropBeforeFolder(null)
                                }
                              }}
                              onDrop={e => {
                                e.stopPropagation()
                                if (e.dataTransfer.types.includes('folder_name')) {
                                  handleFolderDrop(e, groupName, sortedNames)
                                } else {
                                  handleDrop(e, groupName)
                                }
                              }}
                            >
                              {/* Folder header */}
                              <div
                                onClick={() => editingFolder !== groupName && toggleGroup(groupName)}
                                className={`flex items-center gap-2 px-3 py-2.5 cursor-grab active:cursor-grabbing transition-colors group ${color.header}`}
                              >
                                <svg className={`w-4 h-4 shrink-0 ${color.icon}`} fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                                </svg>
                                {editingFolder === groupName ? (
                                  <input
                                    autoFocus
                                    className={`flex-1 bg-transparent text-sm font-semibold outline-none border-b ${color.label} border-current min-w-0`}
                                    value={editFolderName}
                                    onChange={e => setEditFolderName(e.target.value)}
                                    onBlur={() => submitRenameFolder(groupName, editFolderName)}
                                    onKeyDown={e => {
                                      if (e.key === 'Enter') { e.preventDefault(); submitRenameFolder(groupName, editFolderName) }
                                      if (e.key === 'Escape') setEditingFolder(null)
                                    }}
                                    onClick={e => e.stopPropagation()}
                                  />
                                ) : (
                                  <span className={`flex-1 text-sm font-semibold truncate ${color.label}`}>{groupName}</span>
                                )}
                                <span className="text-xs text-white/40 shrink-0">{groupLists.length}</span>
                                <span className={`text-[10px] shrink-0 ${color.icon} opacity-60`}>{collapsed ? '▶' : '▼'}</span>
                                <button
                                  onClick={e => { e.stopPropagation(); setEditingFolder(groupName); setEditFolderName(groupName) }}
                                  className="text-white/20 hover:text-violet-400 transition-colors text-xs shrink-0 opacity-0 group-hover:opacity-100"
                                  title="Rename folder"
                                >
                                  ✎
                                </button>
                                <button
                                  onClick={e => { e.stopPropagation(); deleteFolder(groupName, groupLists) }}
                                  className="text-white/20 hover:text-red-400 transition-colors text-xs shrink-0 opacity-0 group-hover:opacity-100"
                                  title="Delete folder"
                                >
                                  ✕
                                </button>
                              </div>

                              {/* Items */}
                              {!collapsed && (
                                <div className={`space-y-1 p-1.5 border-l-2 ${color.border} bg-gray-950/40`}>
                                  {groupLists.length === 0 ? (
                                    <div className="text-center text-white/20 text-xs py-4">Drag lists here</div>
                                  ) : groupLists.map(l => (
                                    <SidebarItem key={l.id} list={l} selected={selected} onSelect={loadList}
                                      draggingId={draggingId} onDragStart={handleDragStart} onDragEnd={handleDragEnd}
                                      dropBeforeId={dropBeforeId} onDragOverItem={handleDragOverItem} onDropOnItem={handleDropOnItem} />
                                  ))}
                                </div>
                              )}
                              {collapsed && isListTarget && (
                                <div className={`text-center text-xs py-2 ${color.label} opacity-60 ${color.header}`}>
                                  Drop here
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}

                      {/* End-of-list folder drop zone */}
                      {draggingFolder && (
                        <div
                          onDragOver={e => { e.preventDefault(); e.stopPropagation(); setDropBeforeFolder('__end__') }}
                          onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget)) setDropBeforeFolder(null) }}
                          onDrop={e => { e.stopPropagation(); handleFolderDrop(e, '__end__', sortedNames) }}
                          className="h-8"
                        >
                          {dropBeforeFolder === '__end__' && (
                            <div className="h-0.5 bg-violet-500 rounded-full mx-1 mt-1" />
                          )}
                        </div>
                      )}
                    </>
                  )
                })()}

                {/* Bottom ungroup drop zone — visible only when dragging a grouped list */}
                {draggingId !== null && lists.find(l => l.id === draggingId)?.group_name && (
                  <div
                    onDragOver={e => { e.preventDefault(); e.stopPropagation(); setDropTarget('__ungrouped__') }}
                    onDrop={e => { e.stopPropagation(); handleDrop(e, '__ungrouped__') }}
                    className={`h-14 rounded-lg border-2 border-dashed transition-all flex items-center justify-center text-xs ${
                      dropTarget === '__ungrouped__'
                        ? 'border-violet-500/60 bg-violet-900/15 text-violet-400'
                        : 'border-gray-700/50 text-gray-700'
                    }`}
                  >
                    Drop here to ungroup
                  </div>
                )}
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
                      <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-gray-500">
                        <span className="px-2 py-0.5 rounded-full bg-gray-800 text-gray-400">{selected.is_public ? 'Public' : 'Private'}</span>
                        <span className="px-2 py-0.5 rounded-full bg-gray-800 text-gray-400">{selected.items?.length ?? 0} items</span>
                        {selected.like_count > 0 && <span className="px-2 py-0.5 rounded-full bg-gray-800 text-gray-400">♥ {selected.like_count}</span>}
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
                        onClick={() => setShowShare(true)}
                        className="text-xs px-3 py-1.5 rounded-full border border-gray-700 text-gray-400 hover:border-violet-600 hover:text-violet-400 transition-colors"
                      >
                        Share
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

      {/* ── Collab tab ── */}
      {tab === 'collab' && (
        collabLoading ? <Loader /> : (
          <div className="space-y-6">
            {/* Pending invites */}
            {invites.length > 0 && (
              <div className="space-y-3">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                  Pending Invites ({invites.length})
                </h2>
                {invites.map(inv => (
                  <InviteCard
                    key={inv.list_id}
                    invite={inv}
                    onAccept={() => {
                      axios.post(`/api/lists/invites/${inv.list_id}/accept`)
                        .then(() => {
                          setInvites(prev => prev.filter(i => i.list_id !== inv.list_id))
                          // Refresh collab list to include newly accepted list
                          axios.get('/api/lists/collab').then(r => setCollab(r.data))
                        })
                        .catch(() => {})
                    }}
                    onDecline={() => {
                      axios.post(`/api/lists/invites/${inv.list_id}/decline`)
                        .then(() => setInvites(prev => prev.filter(i => i.list_id !== inv.list_id)))
                        .catch(() => {})
                    }}
                  />
                ))}
              </div>
            )}

            {/* Accepted shared lists */}
            {collab.length === 0 && invites.length === 0 ? (
              <div className="card p-12 text-center text-gray-500">
                <p className="text-lg mb-1">No shared lists yet</p>
                <p className="text-sm">When someone invites you to a list, it will appear here.</p>
              </div>
            ) : collab.length > 0 && (
              <>
                {invites.length > 0 && (
                  <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Shared with You</h2>
                )}
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {collab.map(l => (
                    <Link
                      key={l.id}
                      to={`/lists/${l.id}`}
                      className="card overflow-hidden hover:border-violet-700 transition-colors group block"
                    >
                      {(l.cover_url || l.cover_previews?.length > 0) && (
                        <div className="h-28 overflow-hidden bg-gray-800">
                          <CoverMosaic coverUrl={l.cover_url} previews={l.cover_previews} />
                        </div>
                      )}
                      <div className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Avatar username={l.owner_username} avatarUrl={l.owner_avatar_url} size={4} />
                          <span className="text-violet-400 text-xs">{l.owner_username}</span>
                          <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-medium ${
                            l.viewer_role === 'editor'
                              ? 'bg-green-900/40 text-green-400'
                              : 'bg-gray-800 text-gray-400'
                          }`}>
                            {l.viewer_role === 'editor' ? 'Editor' : 'Viewer'}
                          </span>
                        </div>
                        <p className="font-medium text-white text-sm group-hover:text-violet-400 transition-colors">{l.name}</p>
                        {l.description && <p className="text-gray-500 text-xs mt-1 line-clamp-2">{l.description}</p>}
                        <div className="flex items-center justify-between mt-2">
                          <p className="text-gray-600 text-xs">{l.item_count} item{l.item_count !== 1 ? 's' : ''}</p>
                          {!l.is_public && <span className="text-gray-600 text-xs">Private</span>}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </>
            )}
          </div>
        )
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
function SidebarItem({ list: l, selected, onSelect, draggingId, onDragStart, onDragEnd, dropBeforeId, onDragOverItem, onDropOnItem }) {
  return (
    <div
      draggable
      onDragStart={e => onDragStart(e, l.id)}
      onDragEnd={onDragEnd}
      onDragOver={e => { e.preventDefault(); e.stopPropagation(); onDragOverItem(l.id) }}
      onDrop={e => onDropOnItem(e, l.id)}
      className={`cursor-grab active:cursor-grabbing transition-opacity ${draggingId === l.id ? 'opacity-30' : ''}`}
    >
      {/* Reorder drop indicator */}
      {dropBeforeId === l.id && draggingId !== l.id && (
        <div className="h-0.5 bg-violet-500 rounded-full mx-1 mb-1" />
      )}
      <button
        onClick={() => onSelect(l.id)}
        className={`w-full text-left card overflow-hidden transition-colors hover:border-violet-700 ${
          selected?.id === l.id ? 'border-violet-600 bg-violet-900/10' : ''
        }`}
      >
        {/* Compact cover strip */}
        {(l.cover_url || l.cover_previews?.length > 0) && (
          <div className="h-14 overflow-hidden bg-gray-800">
            <CoverMosaic coverUrl={l.cover_url} previews={l.cover_previews} />
          </div>
        )}
        <div className="p-3">
          <div className="flex items-center gap-1.5 min-w-0">
            <span className="text-gray-600 text-xs shrink-0 select-none" title="Drag to reorder or move">⠿</span>
            <p className="font-medium text-white text-sm truncate">{l.name}</p>
          </div>
          <div className="flex items-center justify-between mt-1">
            <p className="text-gray-600 text-xs">
              {l.item_count} item{l.item_count !== 1 ? 's' : ''}
              {!l.is_public && ' · Private'}
            </p>
            {l.like_count > 0 && <span className="text-gray-600 text-xs">♥ {l.like_count}</span>}
          </div>
        </div>
      </button>
    </div>
  )
}

// ── Share / collaborate modal ─────────────────────────────────────────────────
function ShareModal({ listId, listName, onClose }) {
  const { user }                          = useAuth()
  const [members, setMembers]             = useState([])
  const [following, setFollowing]         = useState([])
  const [query, setQuery]                 = useState('')
  const [selectedUser, setSelectedUser]   = useState(null)
  const [showDropdown, setShowDropdown]   = useState(false)
  const [role, setRole]                   = useState('viewer')
  const [adding, setAdding]               = useState(false)
  const [error, setError]                 = useState(null)
  const [loading, setLoading]             = useState(true)
  const dropdownRef                       = useRef(null)

  useEffect(() => {
    Promise.all([
      axios.get(`/api/lists/${listId}/members`),
      axios.get('/api/users/me/following'),
    ]).then(([mr, fr]) => {
      setMembers(mr.data)
      setFollowing(fr.data)
    }).finally(() => setLoading(false))
  }, [listId])

  useEffect(() => {
    function handler(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setShowDropdown(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const memberSet = new Set(members.map(m => m.username))
  const filtered  = following.filter(u =>
    !memberSet.has(u.username) &&
    u.username.toLowerCase().includes(query.toLowerCase())
  )

  async function sendInvite(e) {
    e.preventDefault()
    if (!selectedUser) return
    setAdding(true)
    setError(null)
    try {
      await axios.post(`/api/lists/${listId}/members`, { username: selectedUser.username, role })
      const r = await axios.get(`/api/lists/${listId}/members`)
      setMembers(r.data)
      setSelectedUser(null)
      setQuery('')
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Could not send invite.')
    } finally {
      setAdding(false)
    }
  }

  async function removeMember(u) {
    try {
      await axios.delete(`/api/lists/${listId}/members/${u}`)
      setMembers(prev => prev.filter(m => m.username !== u))
    } catch {}
  }

  async function updateMemberRole(username, newRole) {
    try {
      await axios.post(`/api/lists/${listId}/members`, { username, role: newRole })
      setMembers(prev => prev.map(m => m.username === username ? { ...m, role: newRole } : m))
    } catch {}
  }

  const noFollowing = !loading && following.length === 0

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur z-50 flex items-center justify-center px-4"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="card w-full max-w-md p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-bold text-white text-lg">Share List</h2>
            <p className="text-gray-500 text-sm mt-0.5 truncate max-w-[280px]">{listName}</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-2xl leading-none ml-4">&times;</button>
        </div>

        {/* Invite form */}
        <form onSubmit={sendInvite} className="space-y-3">
          <p className="text-gray-300 text-sm font-medium">Invite a collaborator</p>
          <p className="text-gray-600 text-xs -mt-1">They'll receive an invite and can choose to accept or decline.</p>

          <div className="relative" ref={dropdownRef}>
            {selectedUser ? (
              <div className="input flex items-center gap-2 cursor-default">
                <Avatar username={selectedUser.username} avatarUrl={selectedUser.avatar_url} size={5} />
                <span className="flex-1 text-white text-sm">{selectedUser.username}</span>
                <button
                  type="button"
                  onClick={() => { setSelectedUser(null); setQuery('') }}
                  className="text-gray-500 hover:text-white"
                >✕</button>
              </div>
            ) : (
              <input
                className="input w-full"
                placeholder={loading ? 'Loading…' : noFollowing ? 'Follow someone to invite them' : 'Search people you follow…'}
                value={query}
                disabled={loading || noFollowing}
                onChange={e => { setQuery(e.target.value); setShowDropdown(true); setError(null) }}
                onFocus={() => setShowDropdown(true)}
                autoFocus={!noFollowing}
              />
            )}

            {showDropdown && !selectedUser && filtered.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-10 max-h-52 overflow-y-auto">
                {filtered.map(u => (
                  <button
                    key={u.username}
                    type="button"
                    onClick={() => { setSelectedUser(u); setShowDropdown(false); setQuery('') }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-800 transition-colors text-left"
                  >
                    <Avatar username={u.username} avatarUrl={u.avatar_url} size={6} />
                    <span className="text-white text-sm">{u.username}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <select className="input flex-1" value={role} onChange={e => setRole(e.target.value)}>
              <option value="viewer">Viewer — can see this list</option>
              <option value="editor">Editor — can add / remove items</option>
            </select>
            <button
              type="submit"
              disabled={adding || !selectedUser}
              className="btn-primary shrink-0 disabled:opacity-50"
            >
              {adding ? '…' : 'Invite'}
            </button>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </form>

        {/* Current members */}
        <div className="border-t border-gray-800 pt-4 space-y-2">
          <p className="text-gray-400 text-sm font-medium">Access</p>

          {/* Owner — always shown first */}
          {user && (
            <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
              <Avatar username={user.username} avatarUrl={user.avatar_url} size={6} />
              <span className="flex-1 text-sm text-white font-medium">{user.username}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-violet-900/40 text-violet-400">Owner</span>
            </div>
          )}

          {loading ? (
            <p className="text-gray-600 text-sm px-1">Loading…</p>
          ) : members.length === 0 ? (
            <p className="text-gray-600 text-sm px-1">No collaborators yet.</p>
          ) : members.map(m => (
            <div key={m.username} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
              <Avatar username={m.username} avatarUrl={m.avatar_url} size={6} />
              <span className="flex-1 text-sm text-white font-medium">{m.username}</span>
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
                title="Remove / cancel invite"
              >✕</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── New folder modal ──────────────────────────────────────────────────────────
function FolderCreateModal({ existingGroups, onConfirm, onClose }) {
  const [name, setName] = useState('')
  const [error, setError] = useState(null)

  function submit(e) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    if (existingGroups.map(g => g.toLowerCase()).includes(trimmed.toLowerCase())) {
      setError('A folder with this name already exists')
      return
    }
    onConfirm(trimmed)
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur z-50 flex items-center justify-center px-4"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="card w-full max-w-xs p-6 space-y-4">
        <h2 className="font-bold text-white text-lg">New Folder</h2>
        <p className="text-gray-500 text-sm -mt-2">Drag lists into the folder from the sidebar.</p>
        <form onSubmit={submit} className="space-y-3">
          <input
            className="input"
            placeholder="Folder name…"
            value={name}
            onChange={e => { setName(e.target.value); setError(null) }}
            autoFocus
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={!name.trim()} className="btn-primary disabled:opacity-50">Create</button>
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Invite card ───────────────────────────────────────────────────────────────
function InviteCard({ invite, onAccept, onDecline }) {
  const [busy, setBusy] = useState(false)

  async function handle(fn) {
    setBusy(true)
    try { await fn() } finally { setBusy(false) }
  }

  return (
    <div className="card p-4 flex items-center gap-4 border-yellow-800/40 bg-yellow-900/5">
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm font-medium truncate">{invite.list_name}</p>
        <div className="flex items-center gap-2 mt-1">
          <Avatar username={invite.owner_username} avatarUrl={invite.owner_avatar_url} size={4} />
          <span className="text-gray-400 text-xs">
            {invite.owner_username} invited you as{' '}
            <span className={invite.role === 'editor' ? 'text-green-400' : 'text-gray-300'}>
              {invite.role}
            </span>
          </span>
        </div>
      </div>
      <div className="flex gap-2 shrink-0">
        <button
          onClick={() => handle(onAccept)}
          disabled={busy}
          className="px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold transition-colors disabled:opacity-50"
        >
          Accept
        </button>
        <button
          onClick={() => handle(onDecline)}
          disabled={busy}
          className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold transition-colors disabled:opacity-50"
        >
          Decline
        </button>
      </div>
    </div>
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
