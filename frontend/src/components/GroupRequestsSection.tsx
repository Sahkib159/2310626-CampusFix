
import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react"

import type { Group, GroupRequest } from "../types/group"

import {
  getGroupRequests,
  createGroupRequest,
  updateGroupRequest,
  deleteGroupRequest,
  assignGroupRequestStaff,
  unassignGroupRequestStaff,
} from "../services/groups"

import "./GroupRequestsSection.css"

interface Props {
  group: Group
  accessToken: string | null
}

interface RequestFormData {
  title: string
  description: string
  category: string
}

const emptyForm: RequestFormData = {
  title: "",
  description: "",
  category: "",
}

export default function GroupRequestsSection({
  group,
  accessToken,
}: Props) {
  const [requests, setRequests] = useState<GroupRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<RequestFormData>(emptyForm)

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<RequestFormData>(emptyForm)

  const [staffIds, setStaffIds] = useState<Record<number, string>>({})
  const [workingId, setWorkingId] = useState<number | null>(null)

  const canCreate =
    group.is_owner ||
    Boolean(group.permissions?.can_create_requests)

  const canEdit =
    group.is_owner ||
    Boolean(group.permissions?.can_edit_requests)

  const canAssign =
    group.is_owner ||
    Boolean(group.permissions?.can_assign_requests)

  const canDelete = group.is_owner && !group.is_archived
  const isReadOnly = group.is_archived

  const loadRequests = useCallback(async () => {
    if (!accessToken) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError("")

      const data = await getGroupRequests(group.id, accessToken)
      setRequests(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load shared requests."
      )
    } finally {
      setLoading(false)
    }
  }, [accessToken, group.id])

  useEffect(() => {
    void loadRequests()
  }, [loadRequests])

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!accessToken) return

    try {
      setCreating(true)
      setError("")
      setSuccess("")

      await createGroupRequest(
        group.id,
        {
          title: form.title.trim(),
          description: form.description.trim(),
          category: form.category.trim(),
        },
        accessToken
      )

      setForm(emptyForm)
      setSuccess("Shared request created successfully.")
      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create request."
      )
    } finally {
      setCreating(false)
    }
  }

  function startEditing(request: GroupRequest) {
    setEditingId(request.id)

    setEditForm({
      title: request.title,
      description: request.description,
      category: request.category,
    })

    setError("")
    setSuccess("")
  }

  async function handleUpdate(
    event: FormEvent<HTMLFormElement>,
    requestId: number
  ) {
    event.preventDefault()

    if (!accessToken) return

    try {
      setWorkingId(requestId)
      setError("")
      setSuccess("")

      await updateGroupRequest(
        group.id,
        requestId,
        {
          title: editForm.title.trim(),
          description: editForm.description.trim(),
          category: editForm.category.trim(),
        },
        accessToken
      )

      setEditingId(null)
      setSuccess("Shared request updated successfully.")
      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update request."
      )
    } finally {
      setWorkingId(null)
    }
  }

  async function handleDelete(request: GroupRequest) {
    if (!accessToken) return

    const confirmed = window.confirm(
      `Are you sure you want to delete "${request.title}"?`
    )

    if (!confirmed) return

    try {
      setWorkingId(request.id)
      setError("")
      setSuccess("")

      await deleteGroupRequest(
        group.id,
        request.id,
        accessToken
      )

      setSuccess("Shared request deleted successfully.")
      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete request."
      )
    } finally {
      setWorkingId(null)
    }
  }

  async function handleAssign(requestId: number) {
    if (!accessToken) return

    const staffId = staffIds[requestId]?.trim()

    if (!staffId) {
      setError("Please enter a staff user ID.")
      return
    }

    try {
      setWorkingId(requestId)
      setError("")
      setSuccess("")

      await assignGroupRequestStaff(
        group.id,
        requestId,
        staffId,
        accessToken
      )

      setStaffIds((previous) => ({
        ...previous,
        [requestId]: "",
      }))

      setSuccess("Staff member assigned successfully.")
      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to assign staff."
      )
    } finally {
      setWorkingId(null)
    }
  }

  async function handleUnassign(requestId: number) {
    if (!accessToken) return

    try {
      setWorkingId(requestId)
      setError("")
      setSuccess("")

      await unassignGroupRequestStaff(
        group.id,
        requestId,
        accessToken
      )

      setSuccess("Staff member unassigned successfully.")
      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to unassign staff."
      )
    } finally {
      setWorkingId(null)
    }
  }

  return (
    <section className="group-requests-section">
      <div className="group-section-heading">
        <div>
          <h2>Shared Service Requests</h2>
          <p>Manage service requests shared with this group.</p>
        </div>

        <span className="group-member-count">
          {requests.length} requests
        </span>
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

      {isReadOnly && (
        <div className="group-readonly-notice">
          This group is archived. Shared requests are read-only.
        </div>
      )}

      {canCreate && !isReadOnly && (
        <form
          className="group-request-form"
          onSubmit={handleCreate}
        >
          <h3>Create a shared request</h3>

          <label>
            Request title
            <input
              value={form.title}
              onChange={(event) =>
                setForm({
                  ...form,
                  title: event.target.value,
                })
              }
              placeholder="e.g. Projector not working"
              required
            />
          </label>

          <label>
            Description
            <textarea
              value={form.description}
              onChange={(event) =>
                setForm({
                  ...form,
                  description: event.target.value,
                })
              }
              placeholder="Describe the problem..."
              rows={3}
              required
            />
          </label>

          <label>
            Category
            <input
              value={form.category}
              onChange={(event) =>
                setForm({
                  ...form,
                  category: event.target.value,
                })
              }
              placeholder="e.g. Electrical, IT, Maintenance"
              required
            />
          </label>

          <button
            type="submit"
            className="primary-button"
            disabled={creating}
          >
            {creating ? "Creating..." : "+ Create Shared Request"}
          </button>
        </form>
      )}

      {!canCreate && !isReadOnly && (
        <p className="group-request-hint">
          You don't have permission to create shared requests.
        </p>
      )}

      <div className="group-request-list">
        {loading ? (
          <p>Loading shared requests...</p>
        ) : requests.length === 0 ? (
          <div className="groups-empty">
            <h3>No shared requests yet</h3>
            <p>
              Requests created for this group will appear here.
            </p>
          </div>
        ) : (
          requests.map((request) => (
            <article
              className="group-request-card"
              key={request.id}
            >
              {editingId === request.id ? (
                <form
                  className="group-request-form"
                  onSubmit={(event) =>
                    void handleUpdate(event, request.id)
                  }
                >
                  <h3>Edit request</h3>

                  <label>
                    Title
                    <input
                      value={editForm.title}
                      onChange={(event) =>
                        setEditForm({
                          ...editForm,
                          title: event.target.value,
                        })
                      }
                      required
                    />
                  </label>

                  <label>
                    Description
                    <textarea
                      value={editForm.description}
                      onChange={(event) =>
                        setEditForm({
                          ...editForm,
                          description: event.target.value,
                        })
                      }
                      rows={3}
                      required
                    />
                  </label>

                  <label>
                    Category
                    <input
                      value={editForm.category}
                      onChange={(event) =>
                        setEditForm({
                          ...editForm,
                          category: event.target.value,
                        })
                      }
                      required
                    />
                  </label>

                  <div className="group-request-actions">
                    <button
                      type="submit"
                      className="primary-button"
                      disabled={workingId === request.id}
                    >
                      {workingId === request.id
                        ? "Saving..."
                        : "Save changes"}
                    </button>

                    <button
                      type="button"
                      className="refresh-button"
                      onClick={() => setEditingId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  <div className="group-request-top">
                    <div>
                      <span className="group-request-category">
                        {request.category}
                      </span>

                      <h3>{request.title}</h3>
                    </div>

                    <span className="group-request-status">
                      {String(request.status).replaceAll("_", " ")}
                    </span>
                  </div>

                  <p className="group-request-description">
                    {request.description}
                  </p>

                  <div className="group-request-meta">
                    <span>Request #{request.id}</span>

                    <span>
                      {request.assigned_to
                        ? `Assigned staff: ${request.assigned_to}`
                        : "Not assigned"}
                    </span>
                  </div>

                  {!isReadOnly && (
                    <div className="group-request-actions">
                      {canEdit && (
                        <button
                          type="button"
                          className="refresh-button"
                          onClick={() => startEditing(request)}
                        >
                          Edit
                        </button>
                      )}

                      {canDelete && (
                        <button
                          type="button"
                          className="group-remove-button"
                          disabled={workingId === request.id}
                          onClick={() => void handleDelete(request)}
                        >
                          Delete
                        </button>
                      )}

                      {canAssign && (
                        <div className="group-assignment-controls">
                          <input
                            value={staffIds[request.id] || ""}
                            onChange={(event) =>
                              setStaffIds((previous) => ({
                                ...previous,
                                [request.id]: event.target.value,
                              }))
                            }
                            placeholder="Staff user ID"
                            aria-label={`Staff user ID for request ${request.id}`}
                          />

                          <button
                            type="button"
                            className="primary-button"
                            disabled={
                              workingId === request.id ||
                              !staffIds[request.id]?.trim()
                            }
                            onClick={() =>
                              void handleAssign(request.id)
                            }
                          >
                            Assign
                          </button>

                          {request.assigned_to && (
                            <button
                              type="button"
                              className="refresh-button"
                              disabled={workingId === request.id}
                              onClick={() =>
                                void handleUnassign(request.id)
                              }
                            >
                              Unassign
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </article>
          ))
        )}
      </div>

      <div className="group-details-footer">
        <button
          type="button"
          className="refresh-button"
          onClick={() => void loadRequests()}
          disabled={loading}
        >
          ↻ Refresh requests
        </button>
      </div>
    </section>
  )
}
