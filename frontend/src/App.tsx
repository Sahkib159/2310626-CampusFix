
import { useEffect, useState, type FormEvent } from "react"
import "./index.css"

type RequestStatus =
  | "pending"
  | "assigned"
  | "in_progress"
  | "resolved"
  | "cancelled"

type ServiceRequest = {
  id: number
  title: string
  description: string
  category: string
  status: RequestStatus
}

type RequestForm = {
  title: string
  description: string
  category: string
}

type EditForm = RequestForm & {
  status: RequestStatus
}

const emptyForm: RequestForm = {
  title: "",
  description: "",
  category: "Electrical",
}

const emptyEditForm: EditForm = {
  title: "",
  description: "",
  category: "Electrical",
  status: "pending",
}

const statuses: RequestStatus[] = [
  "pending",
  "assigned",
  "in_progress",
  "resolved",
  "cancelled",
]

export default function App() {
  const [requests, setRequests] = useState<ServiceRequest[]>([])
  const [form, setForm] = useState<RequestForm>(emptyForm)

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<EditForm>(emptyEditForm)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function loadRequests() {
    try {
      setError("")

      const response = await fetch("/api/requests")

      if (!response.ok) {
        throw new Error("Could not load service requests.")
      }

      const data: ServiceRequest[] = await response.json()
      setRequests(data)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadRequests()
  }, [])

  // Create a service request
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setError("")
    setMessage("")

    try {
      const response = await fetch("/api/requests", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      })

      if (!response.ok) {
        throw new Error("Could not create the service request.")
      }

      setForm(emptyForm)
      setMessage("Service request created successfully.")

      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      )
    }
  }

  // Update a service request
  async function handleUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (editingId === null) return

    setError("")
    setMessage("")

    try {
      const response = await fetch(`/api/requests/${editingId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(editForm),
      })

      if (!response.ok) {
        throw new Error("Could not update the service request.")
      }

      setEditingId(null)
      setEditForm(emptyEditForm)

      setMessage("Service request updated successfully.")

      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      )
    }
  }

  // Delete a service request
  async function handleDelete(id: number) {
    if (!window.confirm("Are you sure you want to delete this request?")) {
      return
    }

    setError("")
    setMessage("")

    try {
      const response = await fetch(`/api/requests/${id}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        throw new Error("Could not delete the service request.")
      }

      if (editingId === id) {
        setEditingId(null)
        setEditForm(emptyEditForm)
      }

      setMessage("Service request deleted successfully.")

      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      )
    }
  }

  // Open the editing form with the existing request data
  function startEditing(request: ServiceRequest) {
    setEditingId(request.id)

    setEditForm({
      title: request.title,
      description: request.description,
      category: request.category,
      status: request.status,
    })

    setError("")
    setMessage("")
  }

  // Cancel editing
  function cancelEditing() {
    setEditingId(null)
    setEditForm(emptyEditForm)
  }

  const countByStatus = (status: RequestStatus) =>
    requests.filter((request) => request.status === status).length

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">CAMPUS SERVICE MANAGEMENT</p>

          <h1>CampusFix</h1>

          <p className="subtitle">
            Manage and track campus service requests.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={() => void loadRequests()}
        >
          Refresh
        </button>
      </header>

      {/* Dashboard statistics */}
      <section className="stats-grid">
        <article className="stat-card">
          <span>Total requests</span>
          <strong>{requests.length}</strong>
        </article>

        <article className="stat-card">
          <span>Pending</span>
          <strong>{countByStatus("pending")}</strong>
        </article>

        <article className="stat-card">
          <span>In progress</span>
          <strong>{countByStatus("in_progress")}</strong>
        </article>

        <article className="stat-card">
          <span>Resolved</span>
          <strong>{countByStatus("resolved")}</strong>
        </article>
      </section>

      <section className="content-grid">

        {/* Create request form */}
        <section className="panel">
          <h2>Create a service request</h2>

          <p className="panel-description">
            Describe the issue that needs attention.
          </p>

          <form className="request-form" onSubmit={handleSubmit}>
            <label>
              Request title

              <input
                required
                minLength={3}
                maxLength={150}
                value={form.title}
                onChange={(event) =>
                  setForm({
                    ...form,
                    title: event.target.value,
                  })
                }
                placeholder="e.g. Broken classroom fan"
              />
            </label>

            <label>
              Description

              <textarea
                required
                minLength={5}
                value={form.description}
                onChange={(event) =>
                  setForm({
                    ...form,
                    description: event.target.value,
                  })
                }
                placeholder="Explain the problem..."
                rows={4}
              />
            </label>

            <label>
              Category

              <select
                value={form.category}
                onChange={(event) =>
                  setForm({
                    ...form,
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

            <button className="primary-button" type="submit">
              Submit request
            </button>
          </form>
        </section>

        {/* Service request list */}
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
                      onSubmit={handleUpdate}
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
                            setEditForm({
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
                            setEditForm({
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
                            setEditForm({
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
                            setEditForm({
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
                          onClick={cancelEditing}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}

                  {/* Request actions */}
                  <div className="request-actions">
                    {editingId === request.id ? (
                      <button
                        className="secondary-button"
                        onClick={cancelEditing}
                      >
                        Close editor
                      </button>
                    ) : (
                      <button
                        className="secondary-button"
                        onClick={() => startEditing(request)}
                      >
                        Edit request
                      </button>
                    )}

                    <button
                      className="delete-button"
                      onClick={() => void handleDelete(request.id)}
                    >
                      Delete
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  )
}
