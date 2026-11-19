
import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router"

import { useAuth } from "./contexts/AuthContext"

import HomePage from "./pages/HomePage"
import RequestDetailsPage from "./pages/RequestDetailsPage"
import LoginPage from "./pages/LoginPage"
import SignupPage from "./pages/SignupPage"

function ProtectedRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return <p className="auth-loading">Checking your session...</p>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public authentication pages */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Protected application pages */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/requests/:id"
            element={<RequestDetailsPage />}
          />
        </Route>

        {/* Unknown URLs return to the dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
