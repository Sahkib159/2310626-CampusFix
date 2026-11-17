
import type {
  EditForm,
  RequestForm,
  ServiceRequest,
} from "../types/request"

const API_URL = "/api"

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

// GET: Retrieve all service requests
export async function getRequests(): Promise<ServiceRequest[]> {
  const response = await fetch(`${API_URL}/requests`)
  return handleResponse<ServiceRequest[]>(response)
}

// GET: Retrieve one service request by ID
export async function getRequestById(id: number): Promise<ServiceRequest> {
  const response = await fetch(`${API_URL}/requests/${id}`)
  return handleResponse<ServiceRequest>(response)
}

// POST: Create a service request
export async function createRequest(
  data: RequestForm
): Promise<ServiceRequest> {
  const response = await fetch(`${API_URL}/requests`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  return handleResponse<ServiceRequest>(response)
}

// PUT: Update a service request
export async function updateRequest(
  id: number,
  data: EditForm
): Promise<ServiceRequest> {
  const response = await fetch(`${API_URL}/requests/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  return handleResponse<ServiceRequest>(response)
}

// DELETE: Delete a service request
export async function deleteRequest(id: number): Promise<void> {
  const response = await fetch(`${API_URL}/requests/${id}`, {
    method: "DELETE",
  })

  return handleResponse<void>(response)
}
