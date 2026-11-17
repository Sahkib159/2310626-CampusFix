
import { useEffect, useState, type FormEvent } from "react"

import Header from "../components/Header"
import DashboardStats from "../components/DashboardStats"
import CreateRequestForm from "../components/CreateRequestForm"
import RequestList from "../components/RequestList"

import {
  createRequest,
  deleteRequest,
  getRequests,
  updateRequest,
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
      const data = await getRequests()
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
      await createRequest(form)

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
      await updateRequest(editingId, editForm)

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
      await deleteRequest(id)

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
      <Header onRefresh={() => void loadRequests()} />

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
        />
      </section>
    </main>
  )
}
