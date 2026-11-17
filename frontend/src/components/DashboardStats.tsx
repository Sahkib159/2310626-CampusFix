
import type { RequestStatus, ServiceRequest } from "../types/request"

type DashboardStatsProps = {
  requests: ServiceRequest[]
}

export default function DashboardStats({
  requests,
}: DashboardStatsProps) {
  const countByStatus = (status: RequestStatus) =>
    requests.filter((request) => request.status === status).length

  return (
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
  )
}
