
import type {
  EditForm,
  RequestForm,
  ServiceRequest,
} from "../types/request"

const API_URL = "/api"

// ==========================================
// TYPES
// ==========================================

export interface StaffMember {
  id: string
  name: string
  email: string
  role: "STAFF"
}

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

export interface RecentAdminUser {
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

export interface AdminUserFilters {
  search?: string
  role?: string
  is_active?: boolean
  page?: number
  page_size?: number
}

export interface AuditLogFilters {
  action?: string
  email?: string
  actor_id?: string
  target_user_id?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

// ==========================================
// SHARED HELPERS
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

function getAuthHeaders(accessToken: string): HeadersInit {
  return {
    Authorization: `Bearer ${accessToken}`,
  }
}

function buildQueryString(values: object): string {
  const params = new URLSearchParams()

  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value))
    }
  })

  const query = params.toString()
  return query ? `?${query}` : ""
}

// ==========================================
// SERVICE REQUEST APIs
// ==========================================

export async function getRequests(
  accessToken: string
): Promise<ServiceRequest[]> {
  const response = await fetch(`${API_URL}/requests`, {
    headers: getAuthHeaders(accessToken),
  })

  return handleResponse<ServiceRequest[]>(response)
}

export async function getRequestById(
  id: number,
  accessToken: string
): Promise<ServiceRequest> {
  const response = await fetch(`${API_URL}/requests/${id}`, {
    headers: getAuthHeaders(accessToken),
  })

  return handleResponse<ServiceRequest>(response)
}

export async function createRequest(
  data: RequestForm,
  accessToken: string
): Promise<ServiceRequest> {
  const response = await fetch(`${API_URL}/requests`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(accessToken),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  return handleResponse<ServiceRequest>(response)
}

export async function updateRequest(
  id: number,
  data: EditForm,
  accessToken: string
): Promise<ServiceRequest> {
  const response = await fetch(`${API_URL}/requests/${id}`, {
    method: "PUT",
    headers: {
      ...getAuthHeaders(accessToken),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  return handleResponse<ServiceRequest>(response)
}

export async function deleteRequest(
  id: number,
  accessToken: string
): Promise<void> {
  const response = await fetch(`${API_URL}/requests/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(accessToken),
  })

  return handleResponse<void>(response)
}

export async function getStaff(
  accessToken: string
): Promise<StaffMember[]> {
  const response = await fetch(`${API_URL}/staff`, {
    headers: getAuthHeaders(accessToken),
  })

  return handleResponse<StaffMember[]>(response)
}

export async function assignStaff(
  requestId: number,
  staffId: string,
  accessToken: string
): Promise<ServiceRequest> {
  const response = await fetch(
    `${API_URL}/requests/${requestId}/assign`,
    {
      method: "PATCH",
      headers: {
        ...getAuthHeaders(accessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ staff_id: staffId }),
    }
  )

  return handleResponse<ServiceRequest>(response)
}

export async function unassignStaff(
  requestId: number,
  accessToken: string
): Promise<ServiceRequest> {
  const response = await fetch(
    `${API_URL}/requests/${requestId}/assign`,
    {
      method: "DELETE",
      headers: getAuthHeaders(accessToken),
    }
  )

  return handleResponse<ServiceRequest>(response)
}

// ==========================================
// ADMIN DASHBOARD APIs
// ==========================================

export async function getAdminDashboardStats(
  accessToken: string
): Promise<AdminDashboardStats> {
  const response = await fetch(`${API_URL}/admin/dashboard/stats`, {
    headers: getAuthHeaders(accessToken),
  })

  return handleResponse<AdminDashboardStats>(response)
}

export async function getRecentAdminUsers(
  accessToken: string,
  limit = 5
): Promise<RecentAdminUser[]> {
  const response = await fetch(
    `${API_URL}/admin/dashboard/recent-users${buildQueryString({ limit })}`,
    {
      headers: getAuthHeaders(accessToken),
    }
  )

  return handleResponse<RecentAdminUser[]>(response)
}

export async function getAdminUsers(
  accessToken: string,
  filters: AdminUserFilters = {}
): Promise<AdminUserList> {
  const response = await fetch(
    `${API_URL}/admin/users${buildQueryString(filters)}`,
    {
      headers: getAuthHeaders(accessToken),
    }
  )

  return handleResponse<AdminUserList>(response)
}

export async function banAdminUser(
  userId: string,
  reason: string,
  accessToken: string
): Promise<AdminUser> {
  const response = await fetch(
    `${API_URL}/admin/users/${encodeURIComponent(userId)}/ban`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders(accessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason }),
    }
  )

  return handleResponse<AdminUser>(response)
}

export async function unbanAdminUser(
  userId: string,
  accessToken: string
): Promise<AdminUser> {
  const response = await fetch(
    `${API_URL}/admin/users/${encodeURIComponent(userId)}/unban`,
    {
      method: "POST",
      headers: getAuthHeaders(accessToken),
    }
  )

  return handleResponse<AdminUser>(response)
}

export async function changeAdminUserRole(
  userId: string,
  role: string,
  accessToken: string
): Promise<AdminUser> {
  const response = await fetch(
    `${API_URL}/admin/users/${encodeURIComponent(userId)}/role`,
    {
      method: "PATCH",
      headers: {
        ...getAuthHeaders(accessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ role }),
    }
  )

  return handleResponse<AdminUser>(response)
}

// ==========================================
// AUDIT LOG APIs
// ==========================================

export async function getAdminAuditLogs(
  accessToken: string,
  filters: AuditLogFilters = {}
): Promise<AuditLogList> {
  const response = await fetch(
    `${API_URL}/admin/audit-logs${buildQueryString(filters)}`,
    {
      headers: getAuthHeaders(accessToken),
    }
  )

  return handleResponse<AuditLogList>(response)
}

export async function exportAdminAuditLogs(
  accessToken: string,
  filters: AuditLogFilters = {}
): Promise<Blob> {
  const exportFilters = { ...filters }

  delete exportFilters.page
  delete exportFilters.page_size

  const response = await fetch(
    `${API_URL}/admin/audit-logs/export${buildQueryString(exportFilters)}`,
    {
      headers: getAuthHeaders(accessToken),
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
