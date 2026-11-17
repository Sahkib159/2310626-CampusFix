
type HeaderProps = {
  onRefresh: () => void
}

export default function Header({ onRefresh }: HeaderProps) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">CAMPUS SERVICE MANAGEMENT</p>

        <h1>CampusFix</h1>

        <p className="subtitle">
          Manage and track campus service requests.
        </p>
      </div>

      <button className="refresh-button" onClick={onRefresh}>
        Refresh
      </button>
    </header>
  )
}
