
import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"

import { useAuth } from "../contexts/AuthContext"

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setSubmitting(true)

    try {
      await login({ email, password })
      navigate("/")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-showcase">
        <Link to="/login" className="auth-brand">
          <span className="brand-icon">C</span>
          <span>Campus<span>Fix</span></span>
        </Link>

        <div className="showcase-content">
          <span className="showcase-tag">CAMPUS SERVICE MANAGEMENT</span>
          <h1>Welcome back.</h1>
          <p className="showcase-description">
            A better way to manage, track and resolve campus service requests.
          </p>

          <div className="feature-list">
            <div className="feature-item">
              <span className="feature-icon">↗</span>
              <div>
                <strong>Track Requests</strong>
                <p>Stay updated on your service requests.</p>
              </div>
            </div>

            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <strong>Get Things Done</strong>
                <p>Follow requests from submission to resolution.</p>
              </div>
            </div>

            <div className="feature-item">
              <span className="feature-icon">⌂</span>
              <div>
                <strong>A Better Campus</strong>
                <p>Helping build a better campus together.</p>
              </div>
            </div>
          </div>
        </div>

        <p className="showcase-footer">
          CampusFix · Making campus services simpler.
        </p>
      </section>

      <section className="auth-main">
        <div className="auth-card">
          <div className="auth-card-brand">
            <span className="brand-icon">C</span>
            <span>Campus<span>Fix</span></span>
          </div>

          <div className="auth-heading">
            <h2>Sign in</h2>
            <p>Enter your account details to continue.</p>
          </div>

          {error && <div className="error-message">{error}</div>}

          <form className="auth-form" onSubmit={handleSubmit}>
            <label>
              Email address
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </label>

            <label>
              Password
              <div className="password-field">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((value) => !value)}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </label>

            <button
              className="auth-submit"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Signing in..." : "Sign in"}
              <span>→</span>
            </button>
          </form>

          <div className="auth-divider"><span>OR</span></div>

          <Link to="/signup" className="auth-secondary">
            Create a new account <span>→</span>
          </Link>

          <p className="auth-bottom-link">
            <Link to="/">← Back to CampusFix</Link>
          </p>
        </div>
      </section>
    </main>
  )
}
