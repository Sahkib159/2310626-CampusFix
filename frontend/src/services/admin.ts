
const API_URL = "/api/admin"

export interface AdminUser {
  id: string
  name: string
  email: string
  role: string
  is_active: boolean
  is_banned: boolean
  ban_reason: string | null
  banned_at: string | null
  banned_by: string | null
  created_at: string
}

export interface AdminUserList {
  users: AdminUser[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface AdminDashboardStats {
  total_users: number
  total_students: number
  total_staff: number
  total_admins: number
  active_users: number
  inactive_users: number
  banned_users: number
}

export interface RecentUser {
  id: string
  name: string
  email: string
  role: string
  created_at: string
}

export interface AuditLog {
  id: string
  actor_id: string | null
  target_user_id: string | null
  action: string
  email: string | null
  ip_address: string
  user_agent: string | null
  details: string | null
  created_at: string
}

export interface AuditLogList {
  logs: AuditLog[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface UserListFilters {
  search?: string
  role?: string
  is_active?: string
  page?: number
  page_size?: number
}

export interface AuditLogFilters {
  action?: string
  email?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

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

function authHeaders(accessToken: string): HeadersInit {
  return {
    Authorization: `Bearer ${accessToken}`,
  }
}

function buildQuery(
  values: Record<string, string | number | undefined>
): string {
  const params = new URLSearchParams()

  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      params.set(key, String(value))
    }
  })

  const query = params.toString()
  return query ? `?${query}` : ""
}

export async function getDashboardStats(
  accessToken: string
): Promise<AdminDashboardStats> {
  const response = await fetch(`${API_URL}/dashboard/stats`, {
    headers: authHeaders(accessToken),
  })

  return handleResponse<AdminDashboardStats>(response)
}

export async function getRecentUsers(
  accessToken: string,
  limit = 5
): Promise<RecentUser[]> {
  const response = await fetch(
    `${API_URL}/dashboard/recent-users?limit=${limit}`,
    {
      headers: authHeaders(accessToken),
    }
  )

  return handleResponse<RecentUser[]>(response)
}

export async function getAdminUsers(
  accessToken: string,
  filters: UserListFilters = {}
): Promise<AdminUserList> {
  const query = buildQuery({
    search: filters.search,
    role: filters.role,
    is_active:
      filters.is_active === ""
        ? undefined
        : filters.is_active,
    page: filters.page ?? 1,
    page_size: filters.page_size ?? 10,
  })

  const response = await fetch(`${API_URL}/users${query}`, {
    headers: authHeaders(accessToken),
  })

  return handleResponse<AdminUserList>(response)
}

export async function banUser(
  accessToken: string,
  userId: string,
  reason: string
): Promise<AdminUser> {
  const response = await fetch(
    `${API_URL}/users/${encodeURIComponent(userId)}/ban`,
    {
      method: "POST",
      headers: {
        ...authHeaders(accessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason }),
    }
  )

  return handleResponse<AdminUser>(response)
}

export async function unbanUser(
  accessToken: string,
  userId: string
): Promise<AdminUser> {
  const response = await fetch(
    `${API_URL}/users/${encodeURIComponent(userId)}/unban`,
    {
      method: "POST",
      headers: authHeaders(accessToken),
    }
  )

  return handleResponse<AdminUser>(response)
}

export async function changeUserRole(
  accessToken: string,
  userId: string,
  role: string
): Promise<AdminUser> {
  const response = await fetch(
    `${API_URL}/users/${encodeURIComponent(userId)}/role`,
    {
      method: "PATCH",
      headers: {
        ...authHeaders(accessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ role }),
    }
  )

  return handleResponse<AdminUser>(response)
}

export async function getAuditLogs(
  accessToken: string,
  filters: AuditLogFilters = {}
): Promise<AuditLogList> {
  const query = buildQuery({
    action: filters.action,
    email: filters.email,
    start_date: filters.start_date,
    end_date: filters.end_date,
    page: filters.page ?? 1,
    page_size: filters.page_size ?? 20,
  })

  const response = await fetch(`${API_URL}/audit-logs${query}`, {
    headers: authHeaders(accessToken),
  })

  return handleResponse<AuditLogList>(response)
}

export async function exportAuditLogs(
  accessToken: string,
  filters: AuditLogFilters = {}
): Promise<Blob> {
  const query = buildQuery({
    action: filters.action,
    email: filters.email,
    start_date: filters.start_date,
    end_date: filters.end_date,
  })

  const response = await fetch(
    `${API_URL}/audit-logs/export${query}`,
    {
      headers: authHeaders(accessToken),
    }
  )

  if (!response.ok) {
    let message = `Export failed (${response.status})`

    try {
      const error = await response.json()
      message = error.detail || error.message || message
    } catch {
      // Keep the default error message.
    }

    throw new Error(message)
  }

  return response.blob()
}
