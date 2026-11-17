
import type { FormEvent } from "react"
import { Link } from "react-router"

import type {
  EditForm,
  RequestStatus,
  ServiceRequest,
} from "../types/request"

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
}: RequestListProps) {
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
          {requests.length} total
        </span>
      </div>

      {error && <p className="error-message">{error}</p>}

      {message && <p className="success-message">{message}</p>}

      {loading ? (
        <p>Loading requests...</p>
      ) : requests.length === 0 ? (
        <p className="empty-state">
          No service requests yet.
        </p>
      ) : (
        <div className="request-list">
          {requests.map((request) => (
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
                    onClick={onCancelEditing}
                  >
                    Close editor
                  </button>
                ) : (
                  <button
                    className="secondary-button"
                    onClick={() => onStartEditing(request)}
                  >
                    Edit request
                  </button>
                )}

                <button
                  className="delete-button"
                  onClick={() => onDelete(request.id)}
                >
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
