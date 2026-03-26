import { useState } from 'react'

/** Renders 5 stars (each worth 0.5) – total range 0.5–5.0 */
export default function StarRating({ value, onChange, readonly = false, size = 'md' }) {
  const [hovered, setHovered] = useState(null)
  const display = hovered ?? value ?? 0
  const steps = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]

  const sizeClass = size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-3xl' : 'text-2xl'

  return (
    <div
      className={`flex items-center gap-0.5 ${readonly ? '' : 'cursor-pointer select-none'}`}
      onMouseLeave={() => !readonly && setHovered(null)}
    >
      {[1, 2, 3, 4, 5].map(star => {
        const full = display >= star
        const half = !full && display >= star - 0.5
        return (
          <span
            key={star}
            className={`relative ${sizeClass} ${readonly ? '' : 'hover:scale-110 transition-transform'}`}
            onMouseMove={e => {
              if (readonly) return
              const rect = e.currentTarget.getBoundingClientRect()
              const pct  = (e.clientX - rect.left) / rect.width
              setHovered(pct < 0.5 ? star - 0.5 : star)
            }}
            onClick={e => {
              if (readonly || !onChange) return
              const rect = e.currentTarget.getBoundingClientRect()
              const pct  = (e.clientX - rect.left) / rect.width
              const val  = pct < 0.5 ? star - 0.5 : star
              onChange(val === value ? 0 : val)
            }}
          >
            {full ? (
              <span className="text-yellow-400">★</span>
            ) : half ? (
              <span className="relative">
                <span className="text-gray-600">★</span>
                <span className="absolute inset-0 overflow-hidden w-1/2 text-yellow-400">★</span>
              </span>
            ) : (
              <span className="text-gray-600">★</span>
            )}
          </span>
        )
      })}
      {value != null && (
        <span className={`ml-1 text-gray-400 ${size === 'sm' ? 'text-xs' : 'text-sm'}`}>
          {value.toFixed(1)}
        </span>
      )}
    </div>
  )
}
