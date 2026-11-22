
import type {
  Group,
  GroupMember,
  GroupRequest,
  CreateGroupData,
  UpdateGroupData,
  AddGroupMemberData,
  UpdateGroupMemberPermissions,
  CreateGroupRequestData,
  UpdateGroupRequestData,
} from "../types/group"

import { authenticatedFetch } from "./auth"

const API_URL = "/api/groups"

// Handle API responses and errors
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

  return response.json() as Promise<T>
}

// Authentication headers
function getAuthHeaders(accessToken: string): HeadersInit {
  return {
    Authorization: `Bearer ${accessToken}`,
  }
}

// JSON headers
function getJsonHeaders(accessToken: string): HeadersInit {
  return {
    ...getAuthHeaders(accessToken),
    "Content-Type": "application/json",
  }
}

// ============================================
// GROUP MANAGEMENT
// ============================================

// GET: Retrieve the current user's groups
export async function getGroups(
  accessToken: string,
  includeArchived = true
): Promise<Group[]> {
  const response = await authenticatedFetch(
    `${API_URL}?include_archived=${includeArchived}`,
    {
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<Group[]>(response)
}

// POST: Create a group
export async function createGroup(
  data: CreateGroupData,
  accessToken: string
): Promise<Group> {
  const response = await authenticatedFetch(
    API_URL,
    {
      method: "POST",
      headers: getJsonHeaders(accessToken),
      body: JSON.stringify(data),
    },
    accessToken
  )

  return handleResponse<Group>(response)
}

// GET: Retrieve one group
export async function getGroup(
  groupId: string,
  accessToken: string
): Promise<Group> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}`,
    {
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<Group>(response)
}

// PATCH: Update group details
export async function updateGroup(
  groupId: string,
  data: UpdateGroupData,
  accessToken: string
): Promise<Group> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}`,
    {
      method: "PATCH",
      headers: getJsonHeaders(accessToken),
      body: JSON.stringify(data),
    },
    accessToken
  )

  return handleResponse<Group>(response)
}

// POST: Archive a group
export async function archiveGroup(
  groupId: string,
  accessToken: string
): Promise<Group> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/archive`,
    {
      method: "POST",
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<Group>(response)
}

// POST: Unarchive a group
export async function unarchiveGroup(
  groupId: string,
  accessToken: string
): Promise<Group> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/unarchive`,
    {
      method: "POST",
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<Group>(response)
}

// DELETE: Delete an empty group
export async function deleteGroup(
  groupId: string,
  accessToken: string
): Promise<Record<string, string>> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<Record<string, string>>(response)
}

// ============================================
// GROUP MEMBERS
// ============================================

// GET: Retrieve group members
export async function getGroupMembers(
  groupId: string,
  accessToken: string
): Promise<GroupMember[]> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/members`,
    {
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<GroupMember[]>(response)
}

// POST: Add a member to a group
export async function addGroupMember(
  groupId: string,
  data: AddGroupMemberData,
  accessToken: string
): Promise<GroupMember> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/members`,
    {
      method: "POST",
      headers: getJsonHeaders(accessToken),
      body: JSON.stringify(data),
    },
    accessToken
  )

  return handleResponse<GroupMember>(response)
}

// PATCH: Update a member's permissions
export async function updateGroupMemberPermissions(
  groupId: string,
  userId: string,
  data: UpdateGroupMemberPermissions,
  accessToken: string
): Promise<GroupMember> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}`,
    {
      method: "PATCH",
      headers: getJsonHeaders(accessToken),
      body: JSON.stringify(data),
    },
    accessToken
  )

  return handleResponse<GroupMember>(response)
}

// DELETE: Remove a member or leave a group
export async function removeGroupMember(
  groupId: string,
  userId: string,
  accessToken: string
): Promise<Record<string, string>> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<Record<string, string>>(response)
}

// ============================================
// GROUP SERVICE REQUESTS
// ============================================

// GET: Retrieve requests belonging to a group
export async function getGroupRequests(
  groupId: string,
  accessToken: string
): Promise<GroupRequest[]> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/requests`,
    {
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<GroupRequest[]>(response)
}

// POST: Create a request inside a group
export async function createGroupRequest(
  groupId: string,
  data: CreateGroupRequestData,
  accessToken: string
): Promise<GroupRequest> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/requests`,
    {
      method: "POST",
      headers: getJsonHeaders(accessToken),
      body: JSON.stringify(data),
    },
    accessToken
  )

  return handleResponse<GroupRequest>(response)
}

// GET: Retrieve one group request
export async function getGroupRequest(
  groupId: string,
  requestId: number,
  accessToken: string
): Promise<GroupRequest> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/requests/${requestId}`,
    {
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<GroupRequest>(response)
}

// PUT: Update a group request
export async function updateGroupRequest(
  groupId: string,
  requestId: number,
  data: UpdateGroupRequestData,
  accessToken: string
): Promise<GroupRequest> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/requests/${requestId}`,
    {
      method: "PUT",
      headers: getJsonHeaders(accessToken),
      body: JSON.stringify(data),
    },
    accessToken
  )

  return handleResponse<GroupRequest>(response)
}

// DELETE: Delete a group request
export async function deleteGroupRequest(
  groupId: string,
  requestId: number,
  accessToken: string
): Promise<Record<string, string>> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/requests/${requestId}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<Record<string, string>>(response)
}

// PATCH: Assign staff to a group request
export async function assignGroupRequestStaff(
  groupId: string,
  requestId: number,
  staffId: string,
  accessToken: string
): Promise<GroupRequest> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/requests/${requestId}/assign`,
    {
      method: "PATCH",
      headers: getJsonHeaders(accessToken),
      body: JSON.stringify({
        staff_id: staffId,
      }),
    },
    accessToken
  )

  return handleResponse<GroupRequest>(response)
}

// DELETE: Unassign staff from a group request
export async function unassignGroupRequestStaff(
  groupId: string,
  requestId: number,
  accessToken: string
): Promise<GroupRequest> {
  const response = await authenticatedFetch(
    `${API_URL}/${encodeURIComponent(groupId)}/requests/${requestId}/assign`,
    {
      method: "DELETE",
      headers: getAuthHeaders(accessToken),
    },
    accessToken
  )

  return handleResponse<GroupRequest>(response)
}
