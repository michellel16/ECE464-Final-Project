const API_BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || ''

export function staticUrl(path) {
  if (!path) return null
  if (path.startsWith('http')) return path
  return `${API_BASE}${path}`
}
