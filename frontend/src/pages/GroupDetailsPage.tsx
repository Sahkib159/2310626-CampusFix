
import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react"

import { Link, useNavigate, useParams } from "react-router"

import Header from "../components/Header"
import GroupRequestsSection from "../components/GroupRequestsSection"

import { useAuth } from "../contexts/AuthContext"

import {
  getGroup,
  getGroupMembers,
  addGroupMember,
  updateGroupMemberPermissions,
  removeGroupMember,
  deleteGroup,
} from "../services/groups"

import type {
  Group,
  GroupMember,
  AddGroupMemberData,
  UpdateGroupMemberPermissions,
} from "../types/group"

import "./GroupDetailsPage.css"

export default function GroupDetailsPage() {
  const { groupId } = useParams<{ groupId: string }>()
  const { accessToken } = useAuth()
  const navigate = useNavigate()

  const [group, setGroup] = useState<Group | null>(null)
  const [members, setMembers] = useState<GroupMember[]>([])
  const [loading, setLoading] = useState(true)

  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const [email, setEmail] = useState("")
  const [newPermissions, setNewPermissions] =
    useState<AddGroupMemberData>({
      email: "",
      can_create_requests: false,
      can_edit_requests: false,
      can_assign_requests: false,
    })

  const [permissionDrafts, setPermissionDrafts] =
    useState<Record<string, UpdateGroupMemberPermissions>>({})

  const [addingMember, setAddingMember] = useState(false)
  const [deletingGroup, setDeletingGroup] = useState(false)
  const [workingMember, setWorkingMember] = useState<string | null>(null)

  const loadGroupDetails = useCallback(async () => {
    if (!groupId || !accessToken) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError("")

      const [groupData, memberData] = await Promise.all([
        getGroup(groupId, accessToken),
        getGroupMembers(groupId, accessToken),
      ])

      setGroup(groupData)
      setMembers(memberData)

      const drafts: Record<string, UpdateGroupMemberPermissions> = {}

      memberData.forEach((member) => {
        drafts[member.user_id] = {
          can_create_requests: member.can_create_requests,
          can_edit_requests: member.can_edit_requests,
          can_assign_requests: member.can_assign_requests,
        }
      })

      setPermissionDrafts(drafts)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load group details."
      )
    } finally {
      setLoading(false)
    }
  }, [groupId, accessToken])

  useEffect(() => {
    void loadGroupDetails()
  }, [loadGroupDetails])

  async function handleAddMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!groupId || !accessToken || !email.trim()) return

    try {
      setAddingMember(true)
      setError("")
      setSuccess("")

      const payload: AddGroupMemberData = {
        email: email.trim(),
        can_create_requests: newPermissions.can_create_requests,
        can_edit_requests: newPermissions.can_edit_requests,
        can_assign_requests: newPermissions.can_assign_requests,
      }

      await addGroupMember(groupId, payload, accessToken)

      setEmail("")
      setNewPermissions({
        email: "",
        can_create_requests: false,
        can_edit_requests: false,
        can_assign_requests: false,
      })

      setSuccess("Member added successfully.")
      await loadGroupDetails()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to add member."
      )
    } finally {
      setAddingMember(false)
    }
  }

  function handlePermissionChange(
    userId: string,
    permission: keyof UpdateGroupMemberPermissions,
    checked: boolean
  ) {
    setPermissionDrafts((previous) => ({
      ...previous,
      [userId]: {
        ...previous[userId],
        [permission]: checked,
      },
    }))
  }

  async function handleSavePermissions(userId: string) {
    if (!groupId || !accessToken) return

    try {
      setWorkingMember(userId)
      setError("")
      setSuccess("")

      await updateGroupMemberPermissions(
        groupId,
        userId,
        permissionDrafts[userId],
        accessToken
      )

      setSuccess("Member permissions updated successfully.")
      await loadGroupDetails()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update permissions."
      )
    } finally {
      setWorkingMember(null)
    }
  }

  async function handleRemoveMember(member: GroupMember) {
    if (!groupId || !accessToken) return

    const confirmed = window.confirm(
      `Are you sure you want to remove ${member.user_name} from this group?`
    )

    if (!confirmed) return

    try {
      setWorkingMember(member.user_id)
      setError("")
      setSuccess("")

      await removeGroupMember(
        groupId,
        member.user_id,
        accessToken
      )

      setSuccess("Member removed successfully.")
      await loadGroupDetails()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to remove member."
      )
    } finally {
      setWorkingMember(null)
    }
  }

  async function handleDeleteGroup() {
    if (!groupId || !accessToken || !group?.is_owner || group.is_archived) {
      return
    }

    const confirmed = window.confirm(
      `Permanently delete "${group.name}"? Groups containing service requests cannot be deleted.`
    )

    if (!confirmed) return

    try {
      setDeletingGroup(true)
      setError("")
      setSuccess("")

      await deleteGroup(groupId, accessToken)
      navigate("/groups")
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to delete group."

      setError(
        message.toLowerCase().includes(
          "cannot delete group containing service requests"
        )
          ? "This group contains service requests and cannot be permanently deleted. Archive it instead to preserve its request history."
          : message
      )
    } finally {
      setDeletingGroup(false)
    }
  }

  if (loading) {
    return (
      <>
        <Header />
        <main className="group-details-page">
          <p>Loading group details...</p>
        </main>
      </>
    )
  }

  if (!group) {
    return (
      <>
        <Header />
        <main className="group-details-page">
          <div className="group-details-header">
            <h1>Group not found</h1>
            <p>{error || "This group could not be found or accessed."}</p>
            <Link to="/groups" className="refresh-button">
              Back to Groups
            </Link>
          </div>
        </main>
      </>
    )
  }

  const canManageMembers = group.is_owner && !group.is_archived

  return (
    <>
      <Header />

      <main className="group-details-page">
        <div className="group-details-header">
          <Link to="/groups" className="group-back-link">
            ← Back to Groups
          </Link>

          <div className="group-details-title-row">
            <div>
              <h1>{group.name}</h1>
              <p>
                {group.description || "No group description provided."}
              </p>
            </div>

            <span
              className={
                group.is_archived
                  ? "group-status archived"
                  : "group-status active"
              }
            >
              {group.is_archived ? "Archived" : "Active"}
            </span>
          </div>

          <div className="group-details-stats">
            <div className="group-stat-card">
              <span>Members</span>
              <strong>{members.length}</strong>
            </div>

            <div className="group-stat-card">
              <span>Your role</span>
              <strong>{group.is_owner ? "Owner" : "Member"}</strong>
            </div>

            <div className="group-stat-card">
              <span>Group requests</span>
              <strong>Shared</strong>
            </div>
          </div>
        </div>

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        {success && (
          <p className="success-message" role="status">
            {success}
          </p>
        )}

        {group.is_archived && (
          <div className="group-readonly-notice">
            This group is archived. You can view its members and requests,
            but group modifications are disabled.
          </div>
        )}

        {/* GROUP MEMBERS */}
        <section className="group-members-section">
          <div className="group-section-heading">
            <div>
              <h2>Group Members</h2>
              <p>Manage the people who have access to this group.</p>
            </div>

            <span className="group-member-count">
              {members.length} members
            </span>
          </div>

          {/* ADD MEMBER */}
          {canManageMembers && (
            <div className="group-add-member-panel">
              <h3>Add a member</h3>

              <form
                className="group-add-form"
                onSubmit={handleAddMember}
              >
                <label>
                  Member email
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="Enter registered user email"
                    required
                  />
                </label>

                <div className="group-new-permissions">
                  <p>Initial permissions</p>

                  <label>
                    <input
                      type="checkbox"
                      checked={Boolean(newPermissions.can_create_requests)}
                      onChange={(event) =>
                        setNewPermissions((previous) => ({
                          ...previous,
                          can_create_requests: event.target.checked,
                        }))
                      }
                    />
                    Create requests
                  </label>

                  <label>
                    <input
                      type="checkbox"
                      checked={Boolean(newPermissions.can_edit_requests)}
                      onChange={(event) =>
                        setNewPermissions((previous) => ({
                          ...previous,
                          can_edit_requests: event.target.checked,
                        }))
                      }
                    />
                    Edit requests
                  </label>

                  <label>
                    <input
                      type="checkbox"
                      checked={Boolean(newPermissions.can_assign_requests)}
                      onChange={(event) =>
                        setNewPermissions((previous) => ({
                          ...previous,
                          can_assign_requests: event.target.checked,
                        }))
                      }
                    />
                    Assign requests
                  </label>
                </div>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={addingMember}
                >
                  {addingMember ? "Adding..." : "+ Add Member"}
                </button>
              </form>
            </div>
          )}

          {/* MEMBER LIST */}
          <div className="group-members-list">
            {members.length === 0 ? (
              <div className="groups-empty">
                <h3>No members found</h3>
                <p>There are currently no members in this group.</p>
              </div>
            ) : (
              members.map((member) => {
                const draft = permissionDrafts[member.user_id] || {
                  can_create_requests: false,
                  can_edit_requests: false,
                  can_assign_requests: false,
                }

                return (
                  <article
                    className="group-member-card"
                    key={member.user_id}
                  >
                    <div className="group-member-info">
                      <div className="group-member-avatar">
                        {member.user_name?.charAt(0).toUpperCase() || "U"}
                      </div>

                      <div>
                        <h3>{member.user_name}</h3>
                        <p>{member.user_email}</p>
                      </div>

                      {member.is_owner && (
                        <span className="group-owner-badge">
                          Owner
                        </span>
                      )}
                    </div>

                    {!member.is_owner && (
                      <div className="group-member-management">
                        {canManageMembers ? (
                          <>
                            <div className="group-permission-editors">
                              <label>
                                <input
                                  type="checkbox"
                                  checked={Boolean(draft.can_create_requests)}
                                  onChange={(event) =>
                                    handlePermissionChange(
                                      member.user_id,
                                      "can_create_requests",
                                      event.target.checked
                                    )
                                  }
                                />
                                Create requests
                              </label>

                              <label>
                                <input
                                  type="checkbox"
                                  checked={Boolean(draft.can_edit_requests)}
                                  onChange={(event) =>
                                    handlePermissionChange(
                                      member.user_id,
                                      "can_edit_requests",
                                      event.target.checked
                                    )
                                  }
                                />
                                Edit requests
                              </label>

                              <label>
                                <input
                                  type="checkbox"
                                  checked={Boolean(draft.can_assign_requests)}
                                  onChange={(event) =>
                                    handlePermissionChange(
                                      member.user_id,
                                      "can_assign_requests",
                                      event.target.checked
                                    )
                                  }
                                />
                                Assign requests
                              </label>
                            </div>

                            <div className="group-member-actions">
                              <button
                                type="button"
                                className="primary-button"
                                disabled={workingMember === member.user_id}
                                onClick={() =>
                                  void handleSavePermissions(member.user_id)
                                }
                              >
                                {workingMember === member.user_id
                                  ? "Saving..."
                                  : "Save permissions"}
                              </button>

                              <button
                                type="button"
                                className="group-remove-button"
                                disabled={workingMember === member.user_id}
                                onClick={() =>
                                  void handleRemoveMember(member)
                                }
                              >
                                Remove
                              </button>
                            </div>
                          </>
                        ) : (
                          <div className="group-member-permissions">
                            <span>
                              Create: {member.can_create_requests ? "Yes" : "No"}
                            </span>
                            <span>
                              Edit: {member.can_edit_requests ? "Yes" : "No"}
                            </span>
                            <span>
                              Assign: {member.can_assign_requests ? "Yes" : "No"}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </article>
                )
              })
            )}
          </div>
        </section>

        {/* SHARED SERVICE REQUESTS */}
        <GroupRequestsSection
          group={group}
          accessToken={accessToken}
        />

        <div className="group-details-footer">
          {group.is_owner && !group.is_archived && (
            <button
              type="button"
              className="group-remove-button"
              onClick={() => void handleDeleteGroup()}
              disabled={deletingGroup}
            >
              {deletingGroup ? "Deleting..." : "Delete Group"}
            </button>
          )}

          <button
            type="button"
            className="refresh-button"
            onClick={() => void loadGroupDetails()}
            disabled={loading}
          >
            ↻ Refresh group
          </button>
        </div>
      </main>
    </>
  )
}
