import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Navbar    from './components/Navbar'
import Home      from './pages/Home'
import Login     from './pages/Login'
import Register  from './pages/Register'
import Discover  from './pages/Discover'
import Search    from './pages/Search'
import ArtistPage from './pages/ArtistPage'
import AlbumPage  from './pages/AlbumPage'
import SongPage   from './pages/SongPage'
import Profile    from './pages/Profile'
import Lists      from './pages/Lists'
import Stats      from './pages/Stats'

function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Spinner />
  return user ? children : <Navigate to="/login" replace />
}

function Spinner() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function AppRoutes() {
  const { loading } = useAuth()
  if (loading) return <Spinner />

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="pt-16">
        <Routes>
          <Route path="/"                element={<Home />} />
          <Route path="/login"           element={<Login />} />
          <Route path="/register"        element={<Register />} />
          <Route path="/discover"        element={<Discover />} />
          <Route path="/search"          element={<Search />} />
          <Route path="/artists/:id"     element={<ArtistPage />} />
          <Route path="/albums/:id"      element={<AlbumPage />} />
          <Route path="/songs/:id"       element={<SongPage />} />
          <Route path="/users/:username" element={<Profile />} />
          <Route path="/lists"           element={<Protected><Lists /></Protected>} />
          <Route path="/stats"           element={<Protected><Stats /></Protected>} />
          <Route path="*"                element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
