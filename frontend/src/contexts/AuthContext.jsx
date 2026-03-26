import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import { supabase } from '../lib/supabase'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  async function _syncProfile(session, username = null) {
    const token = session.access_token
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    const { data } = await axios.post('/api/auth/sync', { username })
    setUser(data)
    return data
  }

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (session) {
        try {
          await _syncProfile(session)
        } catch {
          setUser(null)
          delete axios.defaults.headers.common['Authorization']
        }
      }
      setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (!session) {
        setUser(null)
        delete axios.defaults.headers.common['Authorization']
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  async function login(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw new Error(error.message)
    await _syncProfile(data.session)
  }

  async function register(username, email, password) {
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) throw new Error(error.message)
    if (!data.session) throw new Error('Check your email to confirm your account before logging in.')
    await _syncProfile(data.session, username)
  }

  async function logout() {
    await supabase.auth.signOut()
    setUser(null)
    delete axios.defaults.headers.common['Authorization']
  }

  async function refreshUser() {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return null
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
