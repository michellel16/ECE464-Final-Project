import { forwardRef } from 'react'

// All styles are inline so html-to-image captures them reliably
const s = {
  card: {
    width: '420px',
    background: 'linear-gradient(160deg, #0d0d1f 0%, #160d2b 45%, #0d1f1a 100%)',
    color: '#ffffff',
    padding: '36px 32px',
    fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
    borderRadius: '20px',
    boxSizing: 'border-box',
    position: 'relative',
    overflow: 'hidden',
  },
  glow: {
    position: 'absolute',
    top: '-80px',
    right: '-80px',
    width: '260px',
    height: '260px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(124,58,237,0.18) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  glow2: {
    position: 'absolute',
    bottom: '-60px',
    left: '-60px',
    width: '200px',
    height: '200px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(34,197,94,0.1) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  brand: {
    fontSize: '11px',
    fontWeight: '800',
    letterSpacing: '0.2em',
    textTransform: 'uppercase',
    color: '#7c3aed',
    marginBottom: '2px',
  },
  username: {
    fontSize: '22px',
    fontWeight: '700',
    color: '#ffffff',
    lineHeight: 1.2,
  },
  period: {
    fontSize: '12px',
    color: '#6b7280',
    marginTop: '3px',
    letterSpacing: '0.03em',
  },
  divider: {
    height: '1px',
    background: 'rgba(255,255,255,0.07)',
    margin: '18px 0',
  },
  sectionLabel: {
    fontSize: '9px',
    fontWeight: '700',
    letterSpacing: '0.18em',
    textTransform: 'uppercase',
    color: '#6b7280',
    marginBottom: '12px',
  },
  songRow: {
    display: 'flex',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    marginBottom: '10px',
    gap: '8px',
  },
  songLeft: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '10px',
    minWidth: 0,
    flex: 1,
  },
  songNum: {
    fontSize: '11px',
    color: '#7c3aed',
    fontWeight: '700',
    fontVariantNumeric: 'tabular-nums',
    flexShrink: 0,
    width: '18px',
  },
  songInfo: { minWidth: 0, flex: 1 },
  songTitle: {
    fontSize: '13px',
    fontWeight: '600',
    color: '#f3f4f6',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  songArtist: {
    fontSize: '11px',
    color: '#9ca3af',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  songRating: {
    fontSize: '12px',
    color: '#fbbf24',
    fontWeight: '600',
    flexShrink: 0,
    fontVariantNumeric: 'tabular-nums',
  },
  genrePills: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  pill: {
    padding: '3px 10px',
    borderRadius: '999px',
    background: 'rgba(124,58,237,0.18)',
    border: '1px solid rgba(124,58,237,0.35)',
    fontSize: '11px',
    color: '#c4b5fd',
    fontWeight: '500',
  },
  summaryGrid: {
    display: 'flex',
    justifyContent: 'space-around',
    textAlign: 'center',
  },
  summaryNum: {
    fontSize: '26px',
    fontWeight: '800',
    color: '#a78bfa',
    lineHeight: 1.1,
  },
  summaryNumGold: {
    fontSize: '26px',
    fontWeight: '800',
    color: '#fbbf24',
    lineHeight: 1.1,
  },
  summaryLabel: {
    fontSize: '9px',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.12em',
    marginTop: '3px',
  },
  personality: {
    textAlign: 'center',
    padding: '8px 16px',
    background: 'rgba(34,197,94,0.08)',
    borderRadius: '10px',
    border: '1px solid rgba(34,197,94,0.22)',
  },
  personalityText: {
    color: '#4ade80',
    fontSize: '12px',
    fontWeight: '600',
    letterSpacing: '0.02em',
  },
  footer: {
    textAlign: 'center',
    color: '#374151',
    fontSize: '10px',
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
  },
  noData: {
    textAlign: 'center',
    color: '#6b7280',
    fontSize: '13px',
    padding: '20px 0',
  },
}

const SPAN_LABELS = {
  '7d':  'Last 7 Days',
  '30d': 'Last 30 Days',
  '90d': 'Last 90 Days',
  '1y':  'This Year',
  'all': 'All Time',
}

const StatsPostcard = forwardRef(function StatsPostcard({ data, username, timeSpan }, ref) {
  const label = SPAN_LABELS[timeSpan] ?? 'All Time'
  const { top_songs, top_albums, top_genres, audio_profile, summary } = data

  const hasActivity = summary.total_reviews > 0 || summary.songs_listened > 0

  return (
    <div ref={ref} style={s.card}>
      {/* Decorative glows */}
      <div style={s.glow} />
      <div style={s.glow2} />

      {/* Header */}
      <div style={{ position: 'relative' }}>
        <div style={s.brand}>Tunelog</div>
        <div style={s.username}>@{username}</div>
        <div style={s.period}>{label}</div>
      </div>

      <div style={s.divider} />

      {!hasActivity ? (
        <div style={s.noData}>No activity yet for this period.</div>
      ) : (
        <>
          {/* Top Songs */}
          {top_songs.length > 0 && (
            <div style={{ position: 'relative' }}>
              <div style={s.sectionLabel}>Top Songs</div>
              {top_songs.map((song, i) => (
                <div key={i} style={s.songRow}>
                  <div style={s.songLeft}>
                    <span style={s.songNum}>{String(i + 1).padStart(2, '0')}</span>
                    <div style={s.songInfo}>
                      <div style={s.songTitle}>{song.title}</div>
                      {song.artist && <div style={s.songArtist}>{song.artist}</div>}
                    </div>
                  </div>
                  <span style={s.songRating}>★ {song.rating}</span>
                </div>
              ))}
            </div>
          )}

          {/* Top Albums (show only if no song reviews but album reviews exist) */}
          {top_songs.length === 0 && top_albums.length > 0 && (
            <div style={{ position: 'relative' }}>
              <div style={s.sectionLabel}>Top Albums</div>
              {top_albums.map((album, i) => (
                <div key={i} style={s.songRow}>
                  <div style={s.songLeft}>
                    <span style={s.songNum}>{String(i + 1).padStart(2, '0')}</span>
                    <div style={s.songInfo}>
                      <div style={s.songTitle}>{album.title}</div>
                      {album.artist && <div style={s.songArtist}>{album.artist}</div>}
                    </div>
                  </div>
                  <span style={s.songRating}>★ {album.rating}</span>
                </div>
              ))}
            </div>
          )}

          {/* Top Genres */}
          {top_genres.length > 0 && (
            <>
              <div style={s.divider} />
              <div style={{ position: 'relative' }}>
                <div style={s.sectionLabel}>Top Genres</div>
                <div style={s.genrePills}>
                  {top_genres.map((g, i) => (
                    <span key={i} style={s.pill}>{g.name}</span>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Summary Numbers */}
          <div style={s.divider} />
          <div style={s.summaryGrid}>
            <div>
              <div style={s.summaryNum}>{summary.albums_listened}</div>
              <div style={s.summaryLabel}>Albums</div>
            </div>
            <div>
              <div style={s.summaryNum}>{summary.songs_listened}</div>
              <div style={s.summaryLabel}>Songs</div>
            </div>
            <div>
              <div style={s.summaryNum}>{summary.total_reviews}</div>
              <div style={s.summaryLabel}>Reviews</div>
            </div>
            {summary.avg_rating && (
              <div>
                <div style={s.summaryNumGold}>★{summary.avg_rating}</div>
                <div style={s.summaryLabel}>Avg Rating</div>
              </div>
            )}
          </div>

          {/* Personality Badge */}
          {audio_profile?.personality && (
            <>
              <div style={s.divider} />
              <div style={s.personality}>
                <span style={s.personalityText}>{audio_profile.personality}</span>
              </div>
            </>
          )}
        </>
      )}

      <div style={s.divider} />

      {/* Footer */}
      <div style={s.footer}>
        tunelog · {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
      </div>
    </div>
  )
})

export default StatsPostcard
