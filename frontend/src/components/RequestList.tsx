
import { useState, type FormEvent } from "react"
import { Link } from "react-router"

import type {
  EditForm,
  RequestStatus,
  ServiceRequest,
} from "../types/request"

import type { StaffMember } from "../services/api"

type RequestListProps = {
  requests: ServiceRequest[]
  loading: boolean
  error: string
  message: string
  editingId: number | null
  editForm: EditForm
  onEditFormChange: (form: EditForm) => void
  onUpdate: (event: FormEvent<HTMLFormElement>) => void
  onDelete: (id: number) => void
  onStartEditing: (request: ServiceRequest) => void
  onCancelEditing: () => void

  isAdmin: boolean
  staff: StaffMember[]
  selectedStaffIds: Record<number, string>
  onSelectStaff: (requestId: number, staffId: string) => void
  onAssignStaff: (requestId: number) => void
  onUnassignStaff: (requestId: number) => void
}

const statuses: RequestStatus[] = [
  "pending",
  "assigned",
  "in_progress",
  "resolved",
  "cancelled",
]

export default function RequestList({
  requests,
  loading,
  error,
  message,
  editingId,
  editForm,
  onEditFormChange,
  onUpdate,
  onDelete,
  onStartEditing,
  onCancelEditing,
  isAdmin,
  staff,
  selectedStaffIds,
  onSelectStaff,
  onAssignStaff,
  onUnassignStaff,
}: RequestListProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const normalizedSearch = searchTerm.trim().toLowerCase()
  const matchingRequests = requests.filter((request) => {
    if (!normalizedSearch) return true

    return (
      request.title.toLowerCase().includes(normalizedSearch) ||
      request.description.toLowerCase().includes(normalizedSearch) ||
      String(request.id).includes(normalizedSearch)
    )
  })

  return (
    <section className="panel requests-panel">
      <div className="section-heading">
        <div>
          <h2>Service requests</h2>

          <p className="panel-description">
            View and manage submitted requests.
          </p>
        </div>

        <span className="request-count">
          {normalizedSearch
            ? `${matchingRequests.length} of ${requests.length} shown`
            : `${requests.length} total`}
        </span>
      </div>

      <div className="request-search">
        <label htmlFor="service-request-search">
          Search service requests
        </label>

        <div className="request-search-controls">
          <input
            id="service-request-search"
            type="search"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search by title, description, or request ID"
          />

          <button
            className="secondary-button"
            type="button"
            disabled={!searchTerm}
            onClick={() => setSearchTerm("")}
          >
            Clear search
          </button>
        </div>
      </div>

      {error && <p className="error-message">{error}</p>}

      {message && <p className="success-message">{message}</p>}

      {loading ? (
        <p>Loading requests...</p>
      ) : requests.length === 0 ? (
        <p className="empty-state">
          No service requests yet.
        </p>
      ) : matchingRequests.length === 0 ? (
        <p className="empty-state">
          No matching service requests found.
        </p>
      ) : (
        <div className="request-list">
          {matchingRequests.map((request) => {
            const assignedTo = (
              request as ServiceRequest & {
                assigned_to?: string | null
              }
            ).assigned_to

            const assignedStaff = staff.find(
              (member) => member.id === assignedTo
            )

            return (
              <article className="request-card" key={request.id}>
                <div className="request-heading">
                  <div>
                    <span className="request-id">
                      REQUEST #{request.id}
                    </span>

                    <h3>{request.title}</h3>
                  </div>

                  <span className={`status status-${request.status}`}>
                    {request.status.replace("_", " ")}
                  </span>
                </div>

                <p className="request-description">
                  {request.description}
                </p>

                <p className="request-category">
                  Category: {request.category}
                </p>

                {/* Admin staff assignment controls */}
                {isAdmin && (
                  <div className="staff-assignment">
                    <div className="staff-assignment-heading">
                      <div>
                        <h4>Staff assignment</h4>
                        <p className="panel-description">
                          Assign this request to a staff member.
                        </p>
                      </div>

                      <span
                        className={`staff-assignment-status ${
                          assignedTo ? "is-assigned" : "is-unassigned"
                        }`}
                      >
                        {assignedTo ? "Assigned" : "Unassigned"}
                      </span>
                    </div>

                    {assignedStaff && (
                      <p className="staff-current-assignment">
                        Currently assigned to{" "}
                        <strong>{assignedStaff.name}</strong>
                      </p>
                    )}

                    <div className="staff-select-group">
                      <label htmlFor={`staff-select-${request.id}`}>
                        Select staff member
                      </label>

                      <select
                        id={`staff-select-${request.id}`}
                        className="staff-member-select"
                        value={
                          selectedStaffIds[request.id] ??
                          assignedTo ??
                          ""
                        }
                        onChange={(event) =>
                          onSelectStaff(request.id, event.target.value)
                        }
                      >
                        <option value="">
                          Choose a staff member
                        </option>

                        {staff.map((member) => (
                          <option key={member.id} value={member.id}>
                            {member.name} ({member.email})
                          </option>
                        ))}
                      </select>
                    </div>

                    {staff.length === 0 && (
                      <p className="empty-state">
                        No staff accounts found. Create a staff account
                        before assigning requests.
                      </p>
                    )}

                    <div className="request-actions staff-assignment-actions">
                      <button
                        className="primary-button small-button"
                        type="button"
                        disabled={
                          !selectedStaffIds[request.id] ||
                          staff.length === 0
                        }
                        onClick={() => onAssignStaff(request.id)}
                      >
                        {assignedTo ? "Assign / Reassign" : "Assign Staff"}
                      </button>

                      {assignedTo && (
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => onUnassignStaff(request.id)}
                        >
                          Unassign
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Full editing form */}
                {editingId === request.id && (
                  <form
                    className="request-form edit-form"
                    onSubmit={onUpdate}
                  >
                    <h3>Edit service request</h3>

                    <label>
                      Request title

                      <input
                        required
                        minLength={3}
                        maxLength={150}
                        value={editForm.title}
                        onChange={(event) =>
                          onEditFormChange({
                            ...editForm,
                            title: event.target.value,
                          })
                        }
                      />
                    </label>

                    <label>
                      Description

                      <textarea
                        required
                        minLength={5}
                        rows={4}
                        value={editForm.description}
                        onChange={(event) =>
                          onEditFormChange({
                            ...editForm,
                            description: event.target.value,
                          })
                        }
                      />
                    </label>

                    <label>
                      Category

                      <select
                        value={editForm.category}
                        onChange={(event) =>
                          onEditFormChange({
                            ...editForm,
                            category: event.target.value,
                          })
                        }
                      >
                        <option value="Electrical">Electrical</option>
                        <option value="Plumbing">Plumbing</option>
                        <option value="Cleaning">Cleaning</option>
                        <option value="Equipment">Equipment</option>
                        <option value="Other">Other</option>
                      </select>
                    </label>

                    <label>
                      Status

                      <select
                        value={editForm.status}
                        onChange={(event) =>
                          onEditFormChange({
                            ...editForm,
                            status: event.target.value as RequestStatus,
                          })
                        }
                      >
                        {statuses.map((status) => (
                          <option key={status} value={status}>
                            {status.replace("_", " ")}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="request-actions">
                      <button
                        className="primary-button small-button"
                        type="submit"
                      >
                        Save changes
                      </button>

                      <button
                        className="secondary-button"
                        type="button"
                        onClick={onCancelEditing}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}

                {/* Request actions */}
                <div className="request-actions">
                  <Link
                    className="secondary-button"
                    to={`/requests/${request.id}`}
                  >
                    View Details
                  </Link>

                  {editingId === request.id ? (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={onCancelEditing}
                    >
                      Close editor
                    </button>
                  ) : (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => onStartEditing(request)}
                    >
                      Edit request
                    </button>
                  )}

                  <button
                    className="delete-button"
                    type="button"
                    onClick={() => onDelete(request.id)}
                  >
                    Delete
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
