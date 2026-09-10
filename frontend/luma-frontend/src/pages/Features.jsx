// Placeholder page for upcoming features. Each card is intentionally
// empty for now — fill in title/description/image once the team decides
// which features ship first.
const PLACEHOLDER_FEATURES = [
  { id: 1 },
  { id: 2 },
  { id: 3 },
  { id: 4 },
]

export default function Features() {
  return (
    <div>
      <div className="page-header">
        <h1>Features</h1>
        <p>More tools are on the way — check back soon.</p>
      </div>

      <div className="history-grid">
        {PLACEHOLDER_FEATURES.map((f) => (
          <div key={f.id} className="card feature-card-placeholder">
            <div className="feature-placeholder-icon">✨</div>
            <div className="feature-placeholder-label">Coming soon</div>
          </div>
        ))}
      </div>
    </div>
  )
}