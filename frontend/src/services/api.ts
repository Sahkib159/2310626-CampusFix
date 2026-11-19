
import type {
  EditForm,
  RequestForm,
  ServiceRequest,
} from "../types/request"

const API_URL = "/api"

export interface StaffMember {
  id: string
  name: string
  email: string
  role: "STAFF"
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed (${response.status})`

    try {
      const error = await response.json()
      message = error.detail || error.message || message
    } catch {
      // Keep the default error message if the response isn't JSON.
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

// GET: Retrieve all service requests
export async function getRequests(
  accessToken: string
): Promise<ServiceRequest[]> {
  const response = await fetch(`${API_URL}/requests`, {
    headers: getAuthHeaders(accessToken),
  })

  return handleResponse<ServiceRequest[]>(response)
}

// GET: Retrieve one service request by ID
export async function getRequestById(
  id: number,
  accessToken: string
): Promise<ServiceRequest> {
  const response = await fetch(`${API_URL}/requests/${id}`, {
    headers: getAuthHeaders(accessToken),
  })

  return handleResponse<ServiceRequest>(response)
}

// POST: Create a service request
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

// PUT: Update a service request
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

// DELETE: Delete a service request
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

// GET: Retrieve all staff members (Admin only)
export async function getStaff(
  accessToken: string
): Promise<StaffMember[]> {
  const response = await fetch(`${API_URL}/staff`, {
    headers: getAuthHeaders(accessToken),
  })

  return handleResponse<StaffMember[]>(response)
}

// PATCH: Assign a staff member to a service request (Admin only)
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
      body: JSON.stringify({
        staff_id: staffId,
      }),
    }
  )

  return handleResponse<ServiceRequest>(response)
}

// DELETE: Unassign staff from a service request (Admin only)
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
