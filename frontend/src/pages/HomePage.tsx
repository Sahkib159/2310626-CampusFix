
import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react"

import Header from "../components/Header"
import DashboardStats from "../components/DashboardStats"
import CreateRequestForm from "../components/CreateRequestForm"
import RequestList from "../components/RequestList"

import { useAuth } from "../contexts/AuthContext"

import {
  createRequest,
  deleteRequest,
  getRequests,
  updateRequest,
  getStaff,
  assignStaff,
  unassignStaff,
  type StaffMember,
} from "../services/api"

import type {
  EditForm,
  RequestForm,
  ServiceRequest,
} from "../types/request"

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

export default function HomePage() {
  const { accessToken, user } = useAuth()
  const isAdmin = user?.role === "ADMIN"

  const [requests, setRequests] = useState<ServiceRequest[]>([])
  const [staff, setStaff] = useState<StaffMember[]>([])
  const [selectedStaffIds, setSelectedStaffIds] = useState<
    Record<number, string>
  >({})

  const [form, setForm] = useState<RequestForm>(emptyForm)

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<EditForm>(emptyEditForm)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  const loadRequests = useCallback(async () => {
    if (!accessToken) {
      setError("Your session has expired. Please log in again.")
      setLoading(false)
      return
    }

    try {
      setError("")

      const data = await getRequests(accessToken)
      setRequests(data)

      if (isAdmin) {
        const staffData = await getStaff(accessToken)
        setStaff(staffData)

        const assignments: Record<number, string> = {}

        data.forEach((request) => {
          const assignedTo = (
            request as ServiceRequest & {
              assigned_to?: string | null
            }
          ).assigned_to

          if (assignedTo) {
            assignments[request.id] = assignedTo
          }
        })

        setSelectedStaffIds(assignments)
      } else {
        setStaff([])
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      )
    } finally {
      setLoading(false)
    }
  }, [accessToken, isAdmin])

  useEffect(() => {
    void loadRequests()
  }, [loadRequests])

  // Create a service request
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!accessToken) {
      setError("Your session has expired. Please log in again.")
      return
    }

    setError("")
    setMessage("")

    try {
      await createRequest(form, accessToken)

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

    if (!accessToken) {
      setError("Your session has expired. Please log in again.")
      return
    }

    setError("")
    setMessage("")

    try {
      await updateRequest(editingId, editForm, accessToken)

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

    if (!accessToken) {
      setError("Your session has expired. Please log in again.")
      return
    }

    setError("")
    setMessage("")

    try {
      await deleteRequest(id, accessToken)

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

  // Select a staff member for a request
  function handleSelectStaff(requestId: number, staffId: string) {
    setSelectedStaffIds((previous) => ({
      ...previous,
      [requestId]: staffId,
    }))
  }

  // Assign or reassign staff
  async function handleAssignStaff(requestId: number) {
    if (!accessToken) {
      setError("Your session has expired. Please log in again.")
      return
    }

    const staffId = selectedStaffIds[requestId]

    if (!staffId) {
      setError("Please select a staff member first.")
      return
    }

    setError("")
    setMessage("")

    try {
      await assignStaff(requestId, staffId, accessToken)

      setMessage("Staff member assigned successfully.")

      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not assign staff."
      )
    }
  }

  // Remove staff assignment
  async function handleUnassignStaff(requestId: number) {
    if (!accessToken) {
      setError("Your session has expired. Please log in again.")
      return
    }

    setError("")
    setMessage("")

    try {
      await unassignStaff(requestId, accessToken)

      setMessage("Staff assignment removed successfully.")

      await loadRequests()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not unassign staff."
      )
    }
  }

  // Open the editing form with existing request data
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

  return (
    <main className="app">
      <Header onRefresh={loadRequests} />

      <DashboardStats requests={requests} />

      <section className="content-grid">
        <CreateRequestForm
          form={form}
          onFormChange={setForm}
          onSubmit={handleSubmit}
        />

        <RequestList
          requests={requests}
          loading={loading}
          error={error}
          message={message}
          editingId={editingId}
          editForm={editForm}
          onEditFormChange={setEditForm}
          onUpdate={handleUpdate}
          onDelete={(id) => void handleDelete(id)}
          onStartEditing={startEditing}
          onCancelEditing={cancelEditing}
          isAdmin={isAdmin}
          staff={staff}
          selectedStaffIds={selectedStaffIds}
          onSelectStaff={handleSelectStaff}
          onAssignStaff={(id) => void handleAssignStaff(id)}
          onUnassignStaff={(id) => void handleUnassignStaff(id)}
        />
      </section>
    </main>
  )
}
