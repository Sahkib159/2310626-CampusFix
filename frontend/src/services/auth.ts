
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
export async function logout(): Promise<void> {
  const response = await fetch(`${API_URL}/logout`, {
    method: "POST",
    credentials: "include",
  })

  return handleResponse<void>(response)
}

// Get the currently authenticated user's profile.
export async function getCurrentUser(
  accessToken: string
): Promise<AuthUser> {
  const response = await fetch(`${API_URL}/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  return handleResponse<AuthUser>(response)
}

// Update the currently authenticated user's profile.
export async function updateProfile(
  data: ProfileUpdateData,
  accessToken: string
): Promise<AuthUser> {
  const response = await fetch(`${API_URL}/me`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  return handleResponse<AuthUser>(response)
}

// Change the currently authenticated user's password.
export async function changePassword(
  data: PasswordChangeData,
  accessToken: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/change-password`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  })

  return handleResponse<{ message: string }>(response)
}
