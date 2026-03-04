import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm]   = useState({ username: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) { setError('Passwords do not match'); return }
    if (form.password.length < 6) { setError('Password must be at least 6 characters'); return }
    setLoading(true)
    try {
      await register(form.username, form.email, form.password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const field = (name, label, type = 'text', placeholder = '') => (
    <div>
      <label className="block text-sm text-gray-400 mb-1.5">{label}</label>
      <input
        type={type}
        className="input"
        placeholder={placeholder}
        value={form[name]}
        onChange={e => setForm({ ...form, [name]: e.target.value })}
        required
      />
    </div>
  )

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <div className="w-14 h-14 bg-gradient-to-br from-violet-500 to-pink-500 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mx-auto mb-3">T</div>
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="text-gray-400 text-sm mt-1">Start cataloging your music</p>
        </div>

        <form onSubmit={handleSubmit} className="card p-6 space-y-4">
          {error && (
            <div className="bg-red-900/40 border border-red-700 text-red-400 text-sm px-4 py-2.5 rounded-lg">
              {error}
            </div>
          )}
          {field('username', 'Username', 'text', 'music_fan_42')}
          {field('email', 'Email', 'email', 'you@example.com')}
          {field('password', 'Password', 'password', '••••••••')}
          {field('confirm', 'Confirm Password', 'password', '••••••••')}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center disabled:opacity-60"
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500">
          Already have an account?{' '}
          <Link to="/login" className="link-purple font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
