
import { useEffect, useState } from "react"
import { Link, useParams } from "react-router"

import { useAuth } from "../contexts/AuthContext"
import { getRequestById } from "../services/api"
import type { ServiceRequest } from "../types/request"

export default function RequestDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const { accessToken } = useAuth()

  const [request, setRequest] = useState<ServiceRequest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    async function loadRequest() {
      if (!accessToken) {
        setError("Your session has expired. Please log in again.")
        setLoading(false)
        return
      }

      if (!id || !/^\d+$/.test(id) || Number(id) < 1) {
        setError("Invalid service request ID.")
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError("")

        const data = await getRequestById(Number(id), accessToken)

        if (!cancelled) {
          setRequest(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load the service request."
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadRequest()

    return () => {
      cancelled = true
    }
  }, [id, accessToken])

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">CAMPUS SERVICE MANAGEMENT</p>
          <h1>Request Details</h1>
          <p className="subtitle">
            View the complete information about this service request.
          </p>
        </div>

        <Link className="secondary-button" to="/">
          Back to dashboard
        </Link>
      </header>

      <section className="panel">
        {loading ? (
          <p>Loading request details...</p>
        ) : error ? (
          <p className="error-message">{error}</p>
        ) : request ? (
          <>
            <div className="request-heading">
              <div>
                <span className="request-id">
                  REQUEST #{request.id}
                </span>
                <h2>{request.title}</h2>
              </div>

              <span className={`status status-${request.status}`}>
                {request.status.replace("_", " ")}
              </span>
            </div>

            <div className="details-content">
              <h3>Description</h3>
              <p className="request-description">
                {request.description}
              </p>

              <h3>Category</h3>
              <p>{request.category}</p>

              <h3>Status</h3>
              <p>{request.status.replace("_", " ")}</p>
            </div>
          </>
        ) : (
          <p className="empty-state">
            Service request not found.
          </p>
        )}

        <Link className="secondary-button" to="/">
          Back to dashboard
        </Link>
      </section>
    </main>
  )
}
