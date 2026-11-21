
import type { RequestStatus } from "./request"

export interface GroupPermissions {
  can_create_requests: boolean
  can_edit_requests: boolean
  can_assign_requests: boolean
}

export interface Group {
  id: string
  name: string
  description: string | null
  owner_id: string
  is_archived: boolean
  created_at: string
  updated_at: string
  is_owner: boolean
  permissions: GroupPermissions | null
}

export interface GroupMember {
  id: string
  group_id: string
  user_id: string
  user_name: string
  user_email: string
  role: string
  is_owner: boolean
  can_create_requests: boolean
  can_edit_requests: boolean
  can_assign_requests: boolean
  created_at: string
}

export interface GroupRequest {
  id: number
  title: string
  description: string
  category: string
  status: RequestStatus
  user_id: string
  assigned_to: string | null
  group_id: string
}

export interface CreateGroupData {
  name: string
  description?: string | null
}

export interface UpdateGroupData {
  name?: string
  description?: string | null
}

export interface AddGroupMemberData {
  email: string
  can_create_requests?: boolean
  can_edit_requests?: boolean
  can_assign_requests?: boolean
}

export interface UpdateGroupMemberPermissions {
  can_create_requests?: boolean
  can_edit_requests?: boolean
  can_assign_requests?: boolean
}

export interface CreateGroupRequestData {
  title: string
  description: string
  category: string
}

export interface UpdateGroupRequestData {
  title: string
  description: string
  category: string
}
