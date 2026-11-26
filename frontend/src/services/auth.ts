
const API_URL = "/api/auth"

// ==========================================
// TYPES
// ==========================================

export interface AuthUser {
  id: string
  name: string
  email: string
  role: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export interface SignupData {
  name: string
  email: string
  password: string
}

export interface LoginData {
  email: string
  password: string
}

export interface ProfileUpdateData {
  name?: string
  email?: string
  current_password?: string
}

export interface PasswordChangeData {
  current_password: string
  new_password: string
}

export interface UserSession {
  id: string
  created_at: string
  expires_at: string
  revoked: boolean
}

export interface SessionRevocationResponse {
  message: string
}

type AuthCallbacks = {
  onTokenRefreshed: (response: AuthResponse) => void
  onAuthExpired: () => void
}

// ==========================================
// SHARED AUTH STATE
// ==========================================

let authCallbacks: AuthCallbacks | null = null
let refreshPromise: Promise<AuthResponse> | null = null
let currentAccessToken: string | null = null

export function registerAuthCallbacks(callbacks: AuthCallbacks) {
  authCallbacks = callbacks

  return () => {
    if (authCallbacks === callbacks) {
      authCallbacks = null
    }
  }
}

export function setCurrentAccessToken(token: string | null) {
  currentAccessToken = token
}

// ==========================================
// SHARED RESPONSE HANDLER
// ==========================================

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed (${response.status})`

    try {
      const error = await response.json()
      message = error.detail || error.message || message
    } catch {
      // Keep the default error message.
    }

    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

// ==========================================
// AUTHENTICATION APIs
// ==========================================

// Register a new student account.
export async function signup(data: SignupData): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/signup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  })

  return handleResponse<AuthResponse>(response)
}

// Log in an existing user.
export async function login(data: LoginData): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  })

  return handleResponse<AuthResponse>(response)
}

// Obtain a new access token using the HttpOnly refresh cookie.
export async function refreshSession(): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/refresh`, {
    method: "POST",
    credentials: "include",
  })

  return handleResponse<AuthResponse>(response)
}

// Log out and clear the refresh cookie.
export async function logout(
  accessToken?: string | null
): Promise<void> {
  const response = await fetch(`${API_URL}/logout`, {
    method: "POST",
    headers: accessToken
      ? { Authorization: `Bearer ${accessToken}` }
      : undefined,
    credentials: "include",
  })

  return handleResponse<void>(response)
}

// ==========================================
// AUTOMATIC ACCESS TOKEN REFRESH
// ==========================================

async function refreshAccessToken(): Promise<AuthResponse> {
  if (!refreshPromise) {
    refreshPromise = refreshSession()
      .then((response) => {
        currentAccessToken = response.access_token
        authCallbacks?.onTokenRefreshed(response)

        return response
      })
      .catch((error) => {
        currentAccessToken = null
        authCallbacks?.onAuthExpired()

        throw error
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

// Send an authenticated request and retry once after refreshing a 401.
export async function authenticatedFetch(
  url: string | URL,
  options: RequestInit = {},
  accessToken: string
): Promise<Response> {
  if (!currentAccessToken) {
    currentAccessToken = accessToken
  }

  const makeRequest = (token: string) => {
    const headers = new Headers(options.headers)
    headers.set("Authorization", `Bearer ${token}`)

    return fetch(url, {
      ...options,
      headers,
      credentials: options.credentials ?? "include",
    })
  }

  const firstResponse = await makeRequest(accessToken)

  if (firstResponse.status !== 401) {
    return firstResponse
  }

  let retryToken: string

  // Another request may already have refreshed the token.
  if (
    currentAccessToken &&
    currentAccessToken !== accessToken
  ) {
    retryToken = currentAccessToken
  } else {
    const refreshed = await refreshAccessToken()
    retryToken = refreshed.access_token
  }

  const retryResponse = await makeRequest(retryToken)

  // Do not retry indefinitely if the refreshed token is also rejected.
  if (retryResponse.status === 401) {
    currentAccessToken = null
    authCallbacks?.onAuthExpired()
  }

  return retryResponse
}

// ==========================================
// USER PROFILE APIs
// ==========================================

// Get the currently authenticated user's profile.
export async function getCurrentUser(
  accessToken: string
): Promise<AuthUser> {
  const response = await authenticatedFetch(
    `${API_URL}/me`,
    {},
    accessToken
  )

  return handleResponse<AuthUser>(response)
}

// Update the currently authenticated user's profile.
export async function updateProfile(
  data: ProfileUpdateData,
  accessToken: string
): Promise<AuthUser> {
  const response = await authenticatedFetch(
    `${API_URL}/me`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    },
    accessToken
  )

  return handleResponse<AuthUser>(response)
}

// Change the currently authenticated user's password.
export async function changePassword(
  data: PasswordChangeData,
  accessToken: string
): Promise<{ message: string }> {
  const response = await authenticatedFetch(
    `${API_URL}/change-password`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    },
    accessToken
  )

  return handleResponse<{ message: string }>(response)
}

export async function getUserSessions(
  accessToken: string
): Promise<UserSession[]> {
  const response = await authenticatedFetch(
    `${API_URL}/sessions`,
    {},
    accessToken
  )

  return handleResponse<UserSession[]>(response)
}

export async function revokeUserSession(
  sessionId: string,
  accessToken: string
): Promise<SessionRevocationResponse> {
  const response = await authenticatedFetch(
    `${API_URL}/sessions/${encodeURIComponent(sessionId)}`,
    {
      method: "DELETE",
    },
    accessToken
  )

  return handleResponse<SessionRevocationResponse>(response)
}
