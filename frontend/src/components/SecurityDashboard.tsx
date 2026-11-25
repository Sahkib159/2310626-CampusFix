import { useEffect, useState, type FormEvent } from "react"

import {
  getAdminSecurityDashboard,
  type AdminSecurityDashboard as SecurityDashboardData,
} from "../services/api"

type Props = {
  accessToken: string | null
}

type DateFilters = {
  start_date: string
  end_date: string
}

const MAX_RANGE_DAYS = 90
const PAGE_SIZE = 50
const DAY_IN_MILLISECONDS = 24 * 60 * 60 * 1000

function getUtcDate(value: Date): string {
  return value.toISOString().slice(0, 10)
}

function getDefaultDateFilters(): DateFilters {
  const end = new Date()
  const start = new Date(end)
  start.setUTCDate(start.getUTCDate() - 6)

  return {
    start_date: getUtcDate(start),
    end_date: getUtcDate(end),
  }
}

function toUtcDateRange(filters: DateFilters): DateFilters {
  return {
    start_date: `${filters.start_date}T00:00:00.000Z`,
    end_date: `${filters.end_date}T23:59:59.999Z`,
  }
}

function formatDate(value: string | null): string {
  if (!value) return "—"

  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong."
}

function isRangeValid(filters: DateFilters): boolean {
  const start = Date.parse(`${filters.start_date}T00:00:00.000Z`)
  const end = Date.parse(`${filters.end_date}T00:00:00.000Z`)

  if (Number.isNaN(start) || Number.isNaN(end) || start > end) {
    return false
  }

  const inclusiveDays = Math.floor((end - start) / DAY_IN_MILLISECONDS) + 1
  return inclusiveDays <= MAX_RANGE_DAYS
}

export default function SecurityDashboard({ accessToken }: Props) {
  const [dateInputs, setDateInputs] = useState<DateFilters>(
    getDefaultDateFilters
  )
  const [appliedDates, setAppliedDates] = useState<DateFilters>(
    getDefaultDateFilters
  )
  const [page, setPage] = useState(1)
  const [dashboard, setDashboard] = useState<SecurityDashboardData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    if (!accessToken) {
      setDashboard(null)
      setError("")
      setLoading(false)
      return () => {
        cancelled = true
      }
    }

    const currentAccessToken = accessToken
    setLoading(true)
    setError("")
    setDashboard(null)

    async function loadDashboard() {
      try {
        const result = await getAdminSecurityDashboard(currentAccessToken, {
          ...toUtcDateRange(appliedDates),
          page,
          page_size: PAGE_SIZE,
        })

        if (!cancelled) {
          setDashboard(result)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadDashboard()

    return () => {
      cancelled = true
    }
  }, [accessToken, appliedDates, page])

  function applyDateFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")

    if (!isRangeValid(dateInputs)) {
      setError(
        `Choose a valid date range of no more than ${MAX_RANGE_DAYS} days.`
      )
      return
    }

    setPage(1)
    setAppliedDates(dateInputs)
  }

  function updateDate(
    field: keyof DateFilters,
    value: string
  ) {
    setDateInputs((current) => ({
      ...current,
      [field]: value,
    }))
  }

  return (
    <section className="admin-section security-dashboard">
      <div className="admin-section-heading">
        <div>
          <h3>Login security</h3>
          <p>
            Review failed logins and rate-limited activity. Maximum date range:
            {" "}{MAX_RANGE_DAYS} days.
          </p>
        </div>
      </div>

      <form
        className="admin-filter-panel security-filters"
        onSubmit={applyDateFilters}
      >
        <label>
          Start date
          <input
            type="date"
            value={dateInputs.start_date}
            onChange={(event) => updateDate("start_date", event.target.value)}
            required
          />
        </label>

        <label>
          End date
          <input
            type="date"
            value={dateInputs.end_date}
            onChange={(event) => updateDate("end_date", event.target.value)}
            required
          />
        </label>

        <button className="admin-export-button" type="submit">
          Apply dates
        </button>
      </form>

      {error && (
        <div className="admin-message admin-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="admin-panel admin-loading">
          Loading login security events...
        </div>
      ) : error ? null : dashboard?.total === 0 ? (
        <div className="admin-panel admin-empty">
          No login security data is available.
        </div>
      ) : dashboard ? (
        <>
          <div className="security-stat-grid">
            <article className="admin-stat-card">
              <span>Failed logins</span>
              <strong>{dashboard.total_failed}</strong>
              <small>Credential failures only</small>
            </article>
            <article className="admin-stat-card security-rate-limited-card">
              <span>Rate-limited activity</span>
              <strong>{dashboard.total_rate_limited}</strong>
              <small>Tracked separately from failures</small>
            </article>
            <article className="admin-stat-card">
              <span>Repeated IPs</span>
              <strong>
                {dashboard.by_ip.filter((item) => item.repeated).length}
              </strong>
              <small>Threshold reached within 15 minutes</small>
            </article>
            <article className="admin-stat-card">
              <span>Repeated accounts</span>
              <strong>
                {dashboard.by_email.filter((item) => item.repeated).length}
              </strong>
              <small>Threshold reached within 15 minutes</small>
            </article>
          </div>

          <div className="security-summary-grid">
            <section className="admin-panel">
              <div className="admin-panel-heading">
                <div>
                  <h3>Failures by IP address</h3>
                  <p>20 or more failures in a rolling 15-minute window are highlighted.</p>
                </div>
              </div>

              {dashboard.by_ip.length === 0 ? (
                <div className="admin-empty">No IP activity in this range.</div>
              ) : (
                <div className="admin-table-wrap">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>IP address</th>
                        <th>Failed</th>
                        <th>Rate-limited</th>
                        <th>Last failure</th>
                        <th>Indicator</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.by_ip.map((item) => (
                        <tr key={item.ip_address}>
                          <td>{item.ip_address}</td>
                          <td>{item.failed_count}</td>
                          <td>{item.rate_limited_count}</td>
                          <td>{formatDate(item.last_failed_at)}</td>
                          <td>
                            {item.repeated ? (
                              <span className="security-indicator repeated">
                                Repeated failures
                              </span>
                            ) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className="admin-panel">
              <div className="admin-panel-heading">
                <div>
                  <h3>Failures by account</h3>
                  <p>5 or more failures in a rolling 15-minute window are highlighted.</p>
                </div>
              </div>

              {dashboard.by_email.length === 0 ? (
                <div className="admin-empty">No account activity in this range.</div>
              ) : (
                <div className="admin-table-wrap">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Email</th>
                        <th>Failed</th>
                        <th>Rate-limited</th>
                        <th>Last failure</th>
                        <th>Indicator</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.by_email.map((item) => (
                        <tr key={item.email}>
                          <td>{item.email}</td>
                          <td>{item.failed_count}</td>
                          <td>{item.rate_limited_count}</td>
                          <td>{formatDate(item.last_failed_at)}</td>
                          <td>
                            {item.repeated ? (
                              <span className="security-indicator repeated">
                                Repeated failures
                              </span>
                            ) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>

          <section className="admin-panel security-event-panel">
            <div className="admin-panel-heading">
              <div>
                <h3>Login events</h3>
                <p>{dashboard.total} matching events</p>
              </div>
            </div>

            {dashboard.events.length === 0 ? (
              <div className="admin-empty">No login security events found.</div>
            ) : (
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Event</th>
                      <th>Email</th>
                      <th>IP address</th>
                      <th>Failure reason</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.events.map((event) => (
                      <tr key={event.id}>
                        <td>
                          <span
                            className={`security-indicator ${
                              event.action === "LOGIN_RATE_LIMITED"
                                ? "rate-limited"
                                : "failed"
                            }`}
                          >
                            {event.action === "LOGIN_RATE_LIMITED"
                              ? "Rate limited"
                              : "Login failed"}
                          </span>
                        </td>
                        <td>{event.email || "—"}</td>
                        <td>{event.ip_address || "—"}</td>
                        <td>{event.reason || "—"}</td>
                        <td>{formatDate(event.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="admin-pagination">
              <span>
                Page {dashboard.page} of {Math.max(dashboard.total_pages, 1)}
              </span>
              <div>
                <button
                  disabled={page <= 1 || loading}
                  onClick={() => setPage((current) => current - 1)}
                >
                  Previous
                </button>
                <button
                  disabled={page >= dashboard.total_pages || loading}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </section>
  )
}
