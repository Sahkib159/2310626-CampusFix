
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react"

import type {
  AuthUser,
  LoginData,
  SignupData,
} from "../services/auth"

import {
  login as loginRequest,
  signup as signupRequest,
  logout as logoutRequest,
  refreshSession,
  registerAuthCallbacks,
  setCurrentAccessToken,
} from "../services/auth"

interface AuthContextType {
  user: AuthUser | null
  accessToken: string | null
  loading: boolean
  login: (data: LoginData) => Promise<void>
  signup: (data: SignupData) => Promise<void>
  logout: () => Promise<void>
  updateUser: (updatedUser: AuthUser) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const restorationStarted = useRef(false)

  // Keep the shared authentication helper synchronized with React state.
  useEffect(() => {
    return registerAuthCallbacks({
      onTokenRefreshed: (response) => {
        setUser(response.user)
        setAccessToken(response.access_token)
      },
      onAuthExpired: () => {
        setCurrentAccessToken(null)
        setUser(null)
        setAccessToken(null)
      },
    })
  }, [])

  // Restore the session when the application starts.
  useEffect(() => {
    if (restorationStarted.current) return

    restorationStarted.current = true

    async function restoreSession() {
      try {
        const response = await refreshSession()

        setCurrentAccessToken(response.access_token)
        setUser(response.user)
        setAccessToken(response.access_token)
      } catch {
        setCurrentAccessToken(null)
        setUser(null)
        setAccessToken(null)
      } finally {
        setLoading(false)
      }
    }

    void restoreSession()
  }, [])

  async function login(data: LoginData) {
    const response = await loginRequest(data)

    setCurrentAccessToken(response.access_token)
    setUser(response.user)
    setAccessToken(response.access_token)
  }

  async function signup(data: SignupData) {
    const response = await signupRequest(data)

    setCurrentAccessToken(response.access_token)
    setUser(response.user)
    setAccessToken(response.access_token)
  }

  async function logout() {
    try {
      await logoutRequest(accessToken)
    } finally {
      setCurrentAccessToken(null)
      setUser(null)
      setAccessToken(null)
    }
  }

  function updateUser(updatedUser: AuthUser) {
    setUser(updatedUser)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        loading,
        login,
        signup,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider")
  }

  return context
}
