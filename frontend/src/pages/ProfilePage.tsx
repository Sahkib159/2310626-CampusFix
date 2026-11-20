
import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router"

import Header from "../components/Header"
import { useAuth } from "../contexts/AuthContext"

import {
  updateProfile,
  changePassword,
} from "../services/auth"

export default function ProfilePage() {
  const { user, accessToken, updateUser, logout } = useAuth()
  const navigate = useNavigate()

  const [name, setName] = useState(user?.name ?? "")
  const [email, setEmail] = useState(user?.email ?? "")
  const [currentPassword, setCurrentPassword] = useState("")

  const [passwordCurrent, setPasswordCurrent] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)

  const [profileError, setProfileError] = useState("")
  const [profileMessage, setProfileMessage] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [passwordMessage, setPasswordMessage] = useState("")

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!accessToken || !user) {
      setProfileError("Your session has expired. Please log in again.")
      return
    }

    setProfileError("")
    setProfileMessage("")

    const updatedName = name.trim()
    const updatedEmail = email.trim().toLowerCase()

    if (updatedName.length < 2) {
      setProfileError("Name must contain at least 2 characters.")
      return
    }

    if (updatedEmail !== user.email && !currentPassword) {
      setProfileError("Current password is required to change email.")
      return
    }

    const data: {
      name?: string
      email?: string
      current_password?: string
    } = {}

    if (updatedName !== user.name) {
      data.name = updatedName
    }

    if (updatedEmail !== user.email) {
      data.email = updatedEmail
      data.current_password = currentPassword
    }

    if (Object.keys(data).length === 0) {
      setProfileError("No profile changes to save.")
      return
    }

    setSavingProfile(true)

    try {
      const updatedUser = await updateProfile(data, accessToken)

      updateUser(updatedUser)
      setName(updatedUser.name)
      setEmail(updatedUser.email)
      setCurrentPassword("")

      setProfileMessage("Profile updated successfully.")
    } catch (err) {
      setProfileError(
        err instanceof Error ? err.message : "Could not update profile."
      )
    } finally {
      setSavingProfile(false)
    }
  }

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!accessToken) {
      setPasswordError("Your session has expired. Please log in again.")
      return
    }

    setPasswordError("")
    setPasswordMessage("")

    if (newPassword.length < 8) {
      setPasswordError("New password must contain at least 8 characters.")
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation do not match.")
      return
    }

    if (passwordCurrent === newPassword) {
      setPasswordError("New password must differ from your current password.")
      return
    }

    setSavingPassword(true)

    try {
      await changePassword(
        {
          current_password: passwordCurrent,
          new_password: newPassword,
        },
        accessToken
      )

      setPasswordMessage("Password changed successfully. Logging out...")

      try {
        await logout()
      } catch {
        // The password change already revoked refresh sessions.
        // AuthContext clears local authentication state in its finally block.
      }

      navigate("/login", { replace: true })
    } catch (err) {
      setPasswordError(
        err instanceof Error ? err.message : "Could not change password."
      )
    } finally {
      setSavingPassword(false)
    }
  }

  return (
    <main className="app">
      <Header />

      <section className="profile-page">
        <div className="profile-heading">
          <div>
            <h2>My Profile</h2>
            <p>Manage your CampusFix account information and security.</p>
          </div>

          <button
            type="button"
            className="profile-back-button"
            onClick={() => navigate("/")}
          >
            Back to Dashboard
          </button>
        </div>

        <div className="profile-grid">
          <section className="panel profile-card">
            <div className="profile-card-heading">
              <h3>Account Information</h3>
              <p>View and update your personal information.</p>
            </div>

            <div className="profile-account-summary">
              <div className="profile-avatar">
                {user?.name?.charAt(0).toUpperCase() || "U"}
              </div>

              <div>
                <strong>{user?.name || "User"}</strong>
                <span>{user?.role || "STUDENT"}</span>
              </div>
            </div>

            <div className="profile-readonly-field">
              <span>Account ID</span>
              <strong>{user?.id || "Unavailable"}</strong>
            </div>

            <form onSubmit={handleProfileSubmit} className="profile-form">
              <label htmlFor="profile-name">Full Name</label>
              <input
                id="profile-name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                minLength={2}
                maxLength={150}
                required
              />

              <label htmlFor="profile-email">Email Address</label>
              <input
                id="profile-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />

              {email.trim().toLowerCase() !== user?.email && (
                <>
                  <label htmlFor="profile-current-password">
                    Current Password (required to change email)
                  </label>

                  <input
                    id="profile-current-password"
                    type="password"
                    value={currentPassword}
                    onChange={(event) =>
                      setCurrentPassword(event.target.value)
                    }
                    autoComplete="current-password"
                    required
                  />
                </>
              )}

              {profileError && (
                <p className="error-message">{profileError}</p>
              )}

              {profileMessage && (
                <p className="success-message">{profileMessage}</p>
              )}

              <button
                type="submit"
                className="primary-button"
                disabled={savingProfile}
              >
                {savingProfile ? "Saving..." : "Save Profile"}
              </button>
            </form>
          </section>

          <section className="panel profile-card">
            <div className="profile-card-heading">
              <h3>Change Password</h3>
              <p>Update your password to keep your account secure.</p>
            </div>

            <form onSubmit={handlePasswordSubmit} className="profile-form">
              <label htmlFor="password-current">Current Password</label>

              <input
                id="password-current"
                type="password"
                value={passwordCurrent}
                onChange={(event) => setPasswordCurrent(event.target.value)}
                autoComplete="current-password"
                required
              />

              <label htmlFor="password-new">New Password</label>

              <input
                id="password-new"
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                minLength={8}
                maxLength={128}
                autoComplete="new-password"
                required
              />

              <label htmlFor="password-confirm">Confirm New Password</label>

              <input
                id="password-confirm"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                minLength={8}
                maxLength={128}
                autoComplete="new-password"
                required
              />

              {passwordError && (
                <p className="error-message">{passwordError}</p>
              )}

              {passwordMessage && (
                <p className="success-message">{passwordMessage}</p>
              )}

              <button
                type="submit"
                className="primary-button"
                disabled={savingPassword}
              >
                {savingPassword ? "Changing Password..." : "Change Password"}
              </button>

              <p className="profile-security-note">
                Changing your password revokes your active refresh sessions.
                You will need to log in again.
              </p>
            </form>
          </section>
        </div>
      </section>
    </main>
  )
}
