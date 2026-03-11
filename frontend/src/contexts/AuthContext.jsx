import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore token from storage on mount
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      axios.get('/api/auth/me')
        .then(r => setUser(r.data))
        .catch(() => _clearToken())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  function _clearToken() {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }

  async function login(username, password) {
    const form = new FormData()
    form.append('username', username)
    form.append('password', password)
    const { data } = await axios.post('/api/auth/login', form)
    localStorage.setItem('token', data.access_token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
    const me = await axios.get('/api/auth/me')
    setUser(me.data)
  }

  async function register(username, email, password) {
    await axios.post('/api/auth/register', { username, email, password })
    await login(username, password)
  }

  function logout() {
    setUser(null)
    _clearToken()
  }

  async function refreshUser() {
    const me = await axios.get('/api/auth/me')
    setUser(me.data)
    return me.data
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
