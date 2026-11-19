
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
} from "../services/auth"

interface AuthContextType {
  user: AuthUser | null
  accessToken: string | null
  loading: boolean
  login: (data: LoginData) => Promise<void>
  signup: (data: SignupData) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Prevent duplicate refresh requests in React StrictMode.
  const restorationStarted = useRef(false)

  useEffect(() => {
    if (restorationStarted.current) return

    restorationStarted.current = true

    async function restoreSession() {
      try {
        const response = await refreshSession()

        setUser(response.user)
        setAccessToken(response.access_token)
      } catch {
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

    setUser(response.user)
    setAccessToken(response.access_token)
  }

  async function signup(data: SignupData) {
    const response = await signupRequest(data)

    setUser(response.user)
    setAccessToken(response.access_token)
  }

  async function logout() {
    try {
      await logoutRequest()
    } finally {
      setUser(null)
      setAccessToken(null)
    }
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
