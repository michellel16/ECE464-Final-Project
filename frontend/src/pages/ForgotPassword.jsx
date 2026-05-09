import { useState } from 'react'
import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'

export default function ForgotPassword() {
  const [email, setEmail]     = useState('')
  const [sent, setSent]       = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    const redirectTo = `${window.location.origin}/reset-password`
    const { error: err } = await supabase.auth.resetPasswordForEmail(email, { redirectTo })
    setLoading(false)
    if (err) {
      setError(err.message)
    } else {
      setSent(true)
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <div className="w-14 h-14 bg-gradient-to-br from-violet-500 to-pink-500 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mx-auto mb-3">T</div>
          <h1 className="text-2xl font-bold text-white">Reset password</h1>
          <p className="text-gray-400 text-sm mt-1">We'll email you a reset link</p>
        </div>

        {sent ? (
          <div className="card p-8 text-center space-y-3">
            <div className="text-5xl">✉️</div>
            <p className="text-white font-semibold">Check your inbox</p>
            <p className="text-gray-400 text-sm">
              A reset link was sent to <span className="text-white">{email}</span>.
              Check your spam folder if you don't see it within a minute.
            </p>
            <Link to="/login" className="link-purple text-sm block pt-2">Back to sign in</Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="card p-6 space-y-4">
            {error && (
              <div className="bg-red-900/40 border border-red-700 text-red-400 text-sm px-4 py-2.5 rounded-lg">
                {error}
              </div>
            )}
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Email address</label>
              <input
                type="email"
                className="input"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center disabled:opacity-60"
            >
              {loading ? 'Sending…' : 'Send reset link'}
            </button>
            <div className="text-center">
              <Link to="/login" className="link-purple text-sm">Back to sign in</Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
