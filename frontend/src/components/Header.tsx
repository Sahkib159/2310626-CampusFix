
import { useState } from "react"
import { useNavigate, useLocation } from "react-router"
import { useAuth } from "../contexts/AuthContext"

type HeaderProps = {
  onRefresh?: () => void | Promise<void>
}

export default function Header({ onRefresh }: HeaderProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [refreshing, setRefreshing] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleRefresh() {
    if (!onRefresh || refreshing) return

    setRefreshing(true)

    try {
      await onRefresh()
    } finally {
      setRefreshing(false)
    }
  }

  async function handleLogout() {
    const confirmed = window.confirm(
      "Are you sure you want to log out of CampusFix?"
    )

    if (!confirmed) return

    setLoggingOut(true)

    try {
      await logout()
      navigate("/login", { replace: true })
    } catch {
      alert("Logout failed. Please try again.")
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <header className="dashboard-header">
      <div
        className="dashboard-brand"
        onClick={() => navigate("/")}
        style={{ cursor: "pointer" }}
      >
        <div className="dashboard-logo">C</div>

        <div>
          <h1>CampusFix</h1>
          <p>CAMPUS SERVICE MANAGEMENT</p>
        </div>
      </div>

      <div className="dashboard-header-right">
        <div className="dashboard-user">
          <div className="user-avatar">
            {user?.name?.charAt(0).toUpperCase() || "U"}
          </div>

          <div className="user-details">
            <strong>{user?.name || "User"}</strong>
            <span>{user?.role || "STUDENT"}</span>
          </div>
        </div>

        <button
          className="dashboard-refresh"
          onClick={() => navigate("/profile")}
          disabled={loggingOut}
          aria-current={location.pathname === "/profile" ? "page" : undefined}
        >
          Profile
        </button>

        {onRefresh && (
          <button
            className="dashboard-refresh"
            onClick={() => void handleRefresh()}
            disabled={refreshing || loggingOut}
          >
            <span className={refreshing ? "refresh-icon spinning" : "refresh-icon"}>
              ↻
            </span>
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        )}

        <button
          className="dashboard-logout"
          onClick={() => void handleLogout()}
          disabled={loggingOut || refreshing}
        >
          <span>↪</span>
          {loggingOut ? "Logging out..." : "Logout"}
        </button>
      </div>
    </header>
  )
}
