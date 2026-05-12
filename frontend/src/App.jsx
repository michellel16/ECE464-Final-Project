import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Navbar from './components/Navbar'

const Home          = lazy(() => import('./pages/Home'))
const Discover      = lazy(() => import('./pages/Discover'))
const Login         = lazy(() => import('./pages/Login'))
const Register      = lazy(() => import('./pages/Register'))
const Search        = lazy(() => import('./pages/Search'))
const ArtistPage    = lazy(() => import('./pages/ArtistPage'))
const AlbumPage     = lazy(() => import('./pages/AlbumPage'))
const SongPage      = lazy(() => import('./pages/SongPage'))
const Profile       = lazy(() => import('./pages/Profile'))
const Lists         = lazy(() => import('./pages/Lists'))
const ListDetail    = lazy(() => import('./pages/ListDetail'))
const Stats         = lazy(() => import('./pages/Stats'))
const Charts        = lazy(() => import('./pages/Charts'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword  = lazy(() => import('./pages/ResetPassword'))

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
        <Suspense fallback={<Spinner />}>
          <Routes>
            <Route path="/"                element={<Home />} />
            <Route path="/login"            element={<Login />} />
            <Route path="/register"         element={<Register />} />
            <Route path="/forgot-password"  element={<ForgotPassword />} />
            <Route path="/reset-password"   element={<ResetPassword />} />
            <Route path="/discover"        element={<Discover />} />
            <Route path="/search"          element={<Search />} />
            <Route path="/artists/:id"     element={<ArtistPage />} />
            <Route path="/albums/:id"      element={<AlbumPage />} />
            <Route path="/songs/:id"       element={<SongPage />} />
            <Route path="/users/:username" element={<Profile />} />
            <Route path="/lists"           element={<Protected><Lists /></Protected>} />
            <Route path="/lists/:id"       element={<ListDetail />} />
            <Route path="/stats"           element={<Protected><Stats /></Protected>} />
            <Route path="/charts"          element={<Charts />} />
            <Route path="*"                element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
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
