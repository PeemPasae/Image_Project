export default function SkeletonCard() {
  return (
    <div className="card skeleton-card">
      <div className="skeleton skeleton-thumb" />
      <div className="skeleton-body">
        <div className="skeleton skeleton-line w-80" />
        <div className="skeleton skeleton-line w-50" />
      </div>
    </div>
  )
}