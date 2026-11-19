
import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"

import { useAuth } from "../contexts/AuthContext"

export default function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }

    setSubmitting(true)

    try {
      await signup({ name, email, password })
      navigate("/")
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Registration failed."
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-showcase">
        <Link to="/signup" className="auth-brand">
          <span className="brand-icon">C</span>
          <span>Campus<span>Fix</span></span>
        </Link>

        <div className="showcase-content">
          <span className="showcase-tag">JOIN CAMPUSFIX</span>
          <h1>Your campus.<br />Made better.</h1>
          <p className="showcase-description">
            Create your account and take control of your campus service requests.
          </p>

          <div className="feature-list">
            <div className="feature-item">
              <span className="feature-icon">01</span>
              <div>
                <strong>Create Your Account</strong>
                <p>Register securely as a student.</p>
              </div>
            </div>

            <div className="feature-item">
              <span className="feature-icon">02</span>
              <div>
                <strong>Submit Requests</strong>
                <p>Report campus issues whenever needed.</p>
              </div>
            </div>

            <div className="feature-item">
              <span className="feature-icon">03</span>
              <div>
                <strong>Track Progress</strong>
                <p>Keep an eye on your requests.</p>
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
            <h2>Create account</h2>
            <p>Join CampusFix to manage your campus requests.</p>
          </div>

          {error && <div className="error-message">{error}</div>}

          <form className="auth-form" onSubmit={handleSubmit}>
            <label>
              Full name
              <input
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Enter your full name"
                autoComplete="name"
                minLength={2}
                maxLength={150}
                required
              />
            </label>

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
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
                  minLength={8}
                  maxLength={128}
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

            <label>
              Confirm password
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Enter your password again"
                autoComplete="new-password"
                required
              />
            </label>

            <button
              className="auth-submit"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Creating account..." : "Create account"}
              <span>→</span>
            </button>
          </form>

          <div className="auth-divider"><span>OR</span></div>

          <Link to="/login" className="auth-secondary">
            Already have an account? Sign in
          </Link>

          <p className="auth-bottom-link">
            <Link to="/">← Back to CampusFix</Link>
          </p>
        </div>
      </section>
    </main>
  )
}
