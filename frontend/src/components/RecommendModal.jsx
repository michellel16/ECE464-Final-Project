import { useState, useEffect } from 'react'
import axios from 'axios'

export default function RecommendModal({ songId, albumId, title, onClose }) {
  const [following, setFollowing] = useState([])
  const [recipient, setRecipient] = useState('')
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios.get('/api/auth/me').then(({ data: me }) =>
      axios.get(`/api/users/${me.username}/following`)
        .then(r => setFollowing(r.data))
        .finally(() => setLoading(false))
    ).catch(() => setLoading(false))
  }, [])

  async function send(e) {
    e.preventDefault()
    if (!recipient) return
    setSending(true)
    setError(null)
    try {
      await axios.post('/api/social/recommend', {
        recipient_username: recipient,
        song_id: songId ?? null,
        album_id: albumId ?? null,
        note: note || null,
      })
      setSent(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send recommendation')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm space-y-4 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <h2 className="font-bold text-white text-lg">Recommend</h2>
            <p className="text-gray-500 text-sm mt-0.5 truncate max-w-[220px]">{title}</p>
          </div>
          <button onClick={onClose} className="text-gray-600 hover:text-white transition-colors text-xl leading-none">×</button>
        </div>

        {sent ? (
          <div className="text-center py-6 space-y-2">
            <div className="text-3xl">🎵</div>
            <p className="text-white font-medium">Sent to {recipient}!</p>
            <button onClick={onClose} className="btn-primary mt-2">Done</button>
          </div>
        ) : loading ? (
          <div className="flex justify-center py-6">
            <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : following.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">
            You're not following anyone yet. Follow users to send recommendations.
          </p>
        ) : (
          <form onSubmit={send} className="space-y-4">
            <div>
              <label className="text-sm text-gray-400 block mb-1.5">Send to</label>
              <select
                value={recipient}
                onChange={e => setRecipient(e.target.value)}
                className="w-full input bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"
                required
              >
                <option value="">Select a user…</option>
                {following.map(u => (
                  <option key={u.id} value={u.username}>{u.username}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm text-gray-400 block mb-1.5">Note <span className="text-gray-600">(optional)</span></label>
              <textarea
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="Why are you recommending this?"
                maxLength={280}
                rows={3}
                className="w-full input bg-gray-800 rounded-lg px-3 py-2 text-white text-sm resize-none"
              />
            </div>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <div className="flex gap-2 pt-1">
              <button type="button" onClick={onClose} className="flex-1 btn-secondary">Cancel</button>
              <button
                type="submit"
                disabled={!recipient || sending}
                className="flex-1 btn-primary disabled:opacity-50"
              >
                {sending ? 'Sending…' : 'Send'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
