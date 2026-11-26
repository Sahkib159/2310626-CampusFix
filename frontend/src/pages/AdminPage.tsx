
import { useCallback, useEffect, useState, type FormEvent } from "react"

import Header from "../components/Header"
import SecurityDashboard from "../components/SecurityDashboard"
import { useAuth } from "../contexts/AuthContext"

import {
  banAdminUser,
  bulkBanAdminUsers,
  bulkDeleteAdminGroups,
  bulkUnbanAdminUsers,
  changeAdminUserRole,
  deleteAdminGroup,
  exportAdminAuditLogs,
  getAdminAuditLogs,
  getAdminDashboardStats,
  getAdminGroups,
  getAdminUserDetail,
  getAdminUsers,
  getRecentAdminUsers,
  revokeAdminUserSession,
  unbanAdminUser,
  type AdminGroup,
  type AdminGroupDeleteResult,
  type AdminDashboardStats,
  type AdminGroupList,
  type AdminSession,
  type AdminUser,
  type AdminUserDetail,
  type AdminUserFilters,
  type AuditLog,
  type AuditLogFilters,
  type BulkAdminGroupDeleteResponse,
  type RecentAdminUser,
} from "../services/api"

import "./AdminPage.css"

type AdminTab = "overview" | "users" | "groups" | "audit" | "security"

const EMPTY_STATS: AdminDashboardStats = {
  total_users: 0,
  total_students: 0,
  total_staff: 0,
  total_admins: 0,
  active_users: 0,
  inactive_users: 0,
  banned_users: 0,
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "—"

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleString()
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong."
}

function getUserStatus(user: AdminUser): string {
  if (user.is_banned) return "Banned"
  return user.is_active ? "Active" : "Inactive"
}

export default function AdminPage() {
  const { user, accessToken } = useAuth()

  const [activeTab, setActiveTab] = useState<AdminTab>("overview")

  const [stats, setStats] = useState<AdminDashboardStats>(EMPTY_STATS)
  const [recentUsers, setRecentUsers] = useState<RecentAdminUser[]>([])

  const [users, setUsers] = useState<AdminUser[]>([])
  const [usersTotal, setUsersTotal] = useState(0)
  const [usersTotalPages, setUsersTotalPages] = useState(0)
  const [usersPage, setUsersPage] = useState(1)
  const [userSearch, setUserSearch] = useState("")
  const [appliedSearch, setAppliedSearch] = useState("")
  const [userRoleFilter, setUserRoleFilter] = useState("")
  const [userStatusFilter, setUserStatusFilter] = useState("")

  const [groups, setGroups] = useState<AdminGroup[]>([])
  const [groupsTotal, setGroupsTotal] = useState(0)
  const [groupsTotalPages, setGroupsTotalPages] = useState(0)
  const [groupsPage, setGroupsPage] = useState(1)
  const [selectedGroupIds, setSelectedGroupIds] = useState<Set<string>>(
    new Set()
  )
  const [groupOperationResults, setGroupOperationResults] = useState<
    AdminGroupDeleteResult[]
  >([])

  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [auditTotal, setAuditTotal] = useState(0)
  const [auditTotalPages, setAuditTotalPages] = useState(0)
  const [auditPage, setAuditPage] = useState(1)
  const [auditAction, setAuditAction] = useState("")
  const [auditEmail, setAuditEmail] = useState("")
  const [auditStartDate, setAuditStartDate] = useState("")
  const [auditEndDate, setAuditEndDate] = useState("")

  const [loadingOverview, setLoadingOverview] = useState(false)
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [loadingGroups, setLoadingGroups] = useState(false)
  const [loadingAudit, setLoadingAudit] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [workingUserId, setWorkingUserId] = useState<string | null>(null)
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set())
  const [bulkRunning, setBulkRunning] = useState(false)
  const [workingGroupId, setWorkingGroupId] = useState<string | null>(null)
  const [groupBulkRunning, setGroupBulkRunning] = useState(false)

  const [selectedUserDetail, setSelectedUserDetail] =
    useState<AdminUserDetail | null>(null)

  const [loadingUserDetail, setLoadingUserDetail] = useState(false)
  const [userDetailError, setUserDetailError] = useState("")
  const [workingSessionId, setWorkingSessionId] = useState<string | null>(null)
  const [sessionActionError, setSessionActionError] = useState("")
  const [sessionActionSuccess, setSessionActionSuccess] = useState("")

  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const [userFilters, setUserFilters] = useState<AdminUserFilters>({})
  const [auditFilters, setAuditFilters] = useState<AuditLogFilters>({})

  const loadOverview = useCallback(async () => {
    if (!accessToken) return false

    setLoadingOverview(true)

    try {
      const [statsResult, recentResult] = await Promise.all([
        getAdminDashboardStats(accessToken),
        getRecentAdminUsers(accessToken, 5),
      ])

      setStats(statsResult)
      setRecentUsers(recentResult)
      return true
    } catch (err) {
      setError(getErrorMessage(err))
      return false
    } finally {
      setLoadingOverview(false)
    }
  }, [accessToken])

  const loadUsers = useCallback(async () => {
    if (!accessToken) return false

    setLoadingUsers(true)

    try {
      const result = await getAdminUsers(accessToken, userFilters)

      setUsers(result.users)
      setUsersTotal(result.total)
      setUsersTotalPages(result.total_pages)
      return true
    } catch (err) {
      setError(getErrorMessage(err))
      return false
    } finally {
      setLoadingUsers(false)
    }
  }, [accessToken, userFilters])

  const loadGroups = useCallback(async () => {
    if (!accessToken) return false

    setLoadingGroups(true)

    try {
      const result: AdminGroupList = await getAdminGroups(
        accessToken,
        groupsPage,
        20
      )
      const lastPage = Math.max(result.total_pages, 1)

      if (groupsPage > lastPage) {
        setGroupsPage(lastPage)
        return true
      }

      setGroups(result.groups)
      setGroupsTotal(result.total)
      setGroupsTotalPages(result.total_pages)
      const currentPageGroupIds = new Set(
        result.groups.map((group) => group.id)
      )
      setSelectedGroupIds((current) =>
        new Set(
          Array.from(current).filter((groupId) =>
            currentPageGroupIds.has(groupId)
          )
        )
      )
      return true
    } catch (err) {
      setError(getErrorMessage(err))
      return false
    } finally {
      setLoadingGroups(false)
    }
  }, [accessToken, groupsPage])

  const loadAuditLogs = useCallback(async () => {
    if (!accessToken) return

    setLoadingAudit(true)

    try {
      const result = await getAdminAuditLogs(accessToken, auditFilters)

      setAuditLogs(result.logs)
      setAuditTotal(result.total)
      setAuditTotalPages(result.total_pages)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoadingAudit(false)
    }
  }, [accessToken, auditFilters])

  useEffect(() => {
    void loadOverview()
  }, [loadOverview])

  useEffect(() => {
    if (activeTab === "users") {
      void loadUsers()
    }
  }, [activeTab, loadUsers])

  useEffect(() => {
    if (activeTab === "groups") {
      void loadGroups()
    }
  }, [activeTab, loadGroups])

  useEffect(() => {
    if (activeTab === "audit") {
      void loadAuditLogs()
    }
  }, [activeTab, loadAuditLogs])

  function clearMessages() {
    setError("")
    setSuccess("")
  }

  function showError(message: string) {
    setSuccess("")
    setError(message)
  }

  function showSuccess(message: string) {
    setError("")
    setSuccess(message)
  }

  function closeUserDetails() {
    if (workingSessionId !== null) return

    setSelectedUserDetail(null)
    setUserDetailError("")
    setLoadingUserDetail(false)
    setSessionActionError("")
    setSessionActionSuccess("")
  }

  async function handleViewUserDetails(target: AdminUser) {
    if (!accessToken || workingSessionId !== null) return

    setSelectedUserDetail(null)
    setUserDetailError("")
    setSessionActionError("")
    setSessionActionSuccess("")
    setLoadingUserDetail(true)

    try {
      const result = await getAdminUserDetail(target.id, accessToken)
      setSelectedUserDetail(result)
    } catch (err) {
      setUserDetailError(getErrorMessage(err))
    } finally {
      setLoadingUserDetail(false)
    }
  }

  async function handleRevokeSession(session: AdminSession) {
    const target = selectedUserDetail

    if (
      !accessToken ||
      !target ||
      !session.is_active ||
      workingSessionId !== null
    ) {
      return
    }

    const confirmed = window.confirm(
      `Revoke login session ${session.id} for ${target.user.name} (${target.user.email}), created ${formatDate(session.created_at)}?`
    )

    if (!confirmed) return

    setSessionActionError("")
    setSessionActionSuccess("")
    setWorkingSessionId(session.id)

    try {
      const result = await revokeAdminUserSession(
        target.user.id,
        session.id,
        accessToken
      )
      const revokedAt = new Date().toISOString()
      setSelectedUserDetail((current) =>
        current?.user.id === target.user.id
          ? {
              ...current,
              sessions: current.sessions.map((currentSession) =>
                currentSession.id === session.id
                  ? {
                      ...currentSession,
                      is_active: false,
                      revoked_at: currentSession.revoked_at ?? revokedAt,
                    }
                  : currentSession
              ),
            }
          : current
      )
      setSessionActionSuccess(result.message)

      try {
        const refreshedDetails = await getAdminUserDetail(
          target.user.id,
          accessToken
        )
        setSelectedUserDetail((current) =>
          current?.user.id === target.user.id
            ? refreshedDetails
            : current
        )
      } catch (err) {
        setSessionActionError(
          `The session was revoked, but user details could not be refreshed: ${getErrorMessage(err)}`
        )
      }

    } catch (err) {
      setSessionActionError(getErrorMessage(err))
    } finally {
      setWorkingSessionId(null)
    }
  }

  function applyUserFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    clearMessages()
    setSelectedUserIds(new Set())

    setUsersPage(1)

    const nextFilters: AdminUserFilters = {
      page: 1,
      page_size: 20,
    }

    if (appliedSearch.trim()) {
      nextFilters.search = appliedSearch.trim()
    }

    if (userRoleFilter) {
      nextFilters.role = userRoleFilter
    }

    if (userStatusFilter === "active") {
      nextFilters.is_active = true
    } else if (userStatusFilter === "inactive") {
      nextFilters.is_active = false
    }

    setUserFilters(nextFilters)
  }

  function resetUserFilters() {
    setUserSearch("")
    setAppliedSearch("")
    setUserRoleFilter("")
    setUserStatusFilter("")
    setUsersPage(1)
    setSelectedUserIds(new Set())
    setUserFilters({ page: 1, page_size: 20 })
    clearMessages()
  }

  function changeUsersPage(nextPage: number) {
    if (nextPage < 1 || nextPage > usersTotalPages) return

    setSelectedUserIds(new Set())
    setUsersPage(nextPage)
    setUserFilters((current) => ({
      ...current,
      page: nextPage,
    }))
  }

  function applyAuditFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    clearMessages()

    if (
      auditStartDate &&
      auditEndDate &&
      auditStartDate > auditEndDate
    ) {
      showError("Start date cannot be later than end date.")
      return
    }

    setAuditPage(1)

    const nextFilters: AuditLogFilters = {
      page: 1,
      page_size: 20,
    }

    if (auditAction.trim()) {
      nextFilters.action = auditAction.trim()
    }

    if (auditEmail.trim()) {
      nextFilters.email = auditEmail.trim()
    }

    if (auditStartDate) {
      nextFilters.start_date = `${auditStartDate}T00:00:00`
    }

    if (auditEndDate) {
      nextFilters.end_date = `${auditEndDate}T23:59:59`
    }

    setAuditFilters(nextFilters)
  }

  function resetAuditFilters() {
    setAuditAction("")
    setAuditEmail("")
    setAuditStartDate("")
    setAuditEndDate("")
    setAuditPage(1)
    setAuditFilters({ page: 1, page_size: 20 })
    clearMessages()
  }

  function changeAuditPage(nextPage: number) {
    if (nextPage < 1 || nextPage > auditTotalPages) return

    setAuditPage(nextPage)
    setAuditFilters((current) => ({
      ...current,
      page: nextPage,
    }))
  }

  async function handleBanUser(target: AdminUser) {
    if (!accessToken) return

    if (target.id === user?.id) {
      showError("You cannot ban your own administrator account.")
      return
    }

    if (target.role === "ADMIN") {
      showError("Administrator accounts cannot be banned here.")
      return
    }

    const reason = window.prompt(
      `Enter a reason for banning ${target.name}:`
    )

    if (reason === null) return

    if (reason.trim().length < 3) {
      showError("The ban reason must contain at least 3 characters.")
      return
    }

    if (reason.trim().length > 500) {
      showError("The ban reason cannot exceed 500 characters.")
      return
    }

    const confirmed = window.confirm(
      `Ban ${target.name} (${target.email})? Their active sessions will be revoked.`
    )

    if (!confirmed) return

    clearMessages()
    setWorkingUserId(target.id)

    try {
      await banAdminUser(target.id, reason.trim(), accessToken)
      showSuccess(`${target.name} has been banned.`)
      await loadUsers()
      await loadOverview()
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setWorkingUserId(null)
    }
  }

  async function handleUnbanUser(target: AdminUser) {
    if (!accessToken) return

    const confirmed = window.confirm(
      `Unban ${target.name} (${target.email})?`
    )

    if (!confirmed) return

    clearMessages()
    setWorkingUserId(target.id)

    try {
      await unbanAdminUser(target.id, accessToken)
      showSuccess(`${target.name} has been unbanned.`)
      await loadUsers()
      await loadOverview()
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setWorkingUserId(null)
    }
  }

  function isBulkSelectable(target: AdminUser): boolean {
    return target.id !== user?.id && target.role !== "ADMIN"
  }

  function toggleUserSelection(target: AdminUser) {
    if (bulkRunning || !isBulkSelectable(target)) return

    setSelectedUserIds((current) => {
      const next = new Set(current)
      if (next.has(target.id)) {
        next.delete(target.id)
      } else {
        next.add(target.id)
      }
      return next
    })
  }

  function toggleSelectAllUsers() {
    if (bulkRunning) return

    const selectableIds = users
      .filter(isBulkSelectable)
      .map((target) => target.id)
    const allSelected =
      selectableIds.length > 0 &&
      selectableIds.every((id) => selectedUserIds.has(id))

    setSelectedUserIds((current) => {
      const next = new Set(current)
      if (allSelected) {
        selectableIds.forEach((id) => next.delete(id))
      } else {
        selectableIds.forEach((id) => next.add(id))
      }
      return next
    })
  }

  async function handleBulkBanUsers() {
    if (!accessToken || bulkRunning) return

    const selectedTargets = users.filter((target) =>
      selectedUserIds.has(target.id)
    )
    const eligibleTargets = selectedTargets.filter(
      (target) => isBulkSelectable(target) && !target.is_banned
    )

    if (eligibleTargets.length === 0) {
      showError(
        "Select at least one eligible, not-yet-banned user for bulk ban."
      )
      return
    }

    const reason = window.prompt(
      `Enter a reason for banning ${eligibleTargets.length} selected user${eligibleTargets.length === 1 ? "" : "s"}:`
    )

    if (reason === null) return

    if (reason.trim().length < 3) {
      showError("The ban reason must contain at least 3 characters.")
      return
    }

    if (reason.trim().length > 500) {
      showError("The ban reason cannot exceed 500 characters.")
      return
    }

    const confirmed = window.confirm(
      `Ban ${eligibleTargets.length} selected user${eligibleTargets.length === 1 ? "" : "s"}? Their active sessions will be revoked.`
    )

    if (!confirmed) return

    clearMessages()
    setBulkRunning(true)

    try {
      const result = await bulkBanAdminUsers(
        accessToken,
        eligibleTargets.map((target) => target.id),
        reason.trim()
      )

      const failures = result.results.filter((item) => !item.success)
      const usersRefreshed = await loadUsers()
      const overviewRefreshed = await loadOverview()
      const refreshFailed = !usersRefreshed || !overviewRefreshed

      if (failures.length > 0) {
        setSuccess("")
        const failureMessages = failures
            .map((item) => {
              const target = users.find(
                (candidate) => candidate.id === item.user_id
              )
              return `${target ? `${target.name} (${target.email})` : item.user_id}: ${item.message}`
            })
            .join(" ")
        const refreshWarning = refreshFailed
          ? " Refresh users or overview data failed; the operation completed but the displayed data may be stale."
          : ""

        setError(
          `Bulk ban complete: ${result.failed} failed, ${result.succeeded} succeeded. ` +
          failureMessages +
          refreshWarning
        )
      } else if (refreshFailed) {
        setSuccess("")
        setError(
          `Bulk ban operation completed: ${result.succeeded} succeeded, 0 failed. ` +
          "Refreshing users or overview data failed; the operation completed but the displayed data may be stale."
        )
      } else {
        setError("")
        setSuccess(
          `Bulk ban complete: ${result.succeeded} succeeded, 0 failed.`
        )
      }
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setSelectedUserIds(new Set())
      setBulkRunning(false)
    }
  }

  async function handleBulkUnbanUsers() {
    if (!accessToken || bulkRunning) return

    const eligibleTargets = users.filter(
      (target) =>
        selectedUserIds.has(target.id) &&
        isBulkSelectable(target) &&
        target.is_banned
    )

    if (eligibleTargets.length === 0) {
      showError("Select at least one banned user for bulk unban.")
      return
    }

    const confirmed = window.confirm(
      `Unban ${eligibleTargets.length} selected user${eligibleTargets.length === 1 ? "" : "s"}?`
    )

    if (!confirmed) return

    clearMessages()
    setBulkRunning(true)

    try {
      const result = await bulkUnbanAdminUsers(
        accessToken,
        eligibleTargets.map((target) => target.id)
      )

      const failures = result.results.filter((item) => !item.success)
      const usersRefreshed = await loadUsers()
      const overviewRefreshed = await loadOverview()
      const refreshFailed = !usersRefreshed || !overviewRefreshed

      if (failures.length > 0) {
        setSuccess("")
        const failureMessages = failures
            .map((item) => {
              const target = users.find(
                (candidate) => candidate.id === item.user_id
              )
              return `${target ? `${target.name} (${target.email})` : item.user_id}: ${item.message}`
            })
            .join(" ")
        const refreshWarning = refreshFailed
          ? " Refresh users or overview data failed; the operation completed but the displayed data may be stale."
          : ""

        setError(
          `Bulk unban complete: ${result.failed} failed, ${result.succeeded} succeeded. ` +
          failureMessages +
          refreshWarning
        )
      } else if (refreshFailed) {
        setSuccess("")
        setError(
          `Bulk unban operation completed: ${result.succeeded} succeeded, 0 failed. ` +
          "Refreshing users or overview data failed; the operation completed but the displayed data may be stale."
        )
      } else {
        setError("")
        setSuccess(
          `Bulk unban complete: ${result.succeeded} succeeded, 0 failed.`
        )
      }
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setSelectedUserIds(new Set())
      setBulkRunning(false)
    }
  }

  function toggleGroupSelection(groupId: string) {
    if (groupBulkRunning || workingGroupId !== null) return

    setSelectedGroupIds((current) => {
      const next = new Set(current)
      if (next.has(groupId)) {
        next.delete(groupId)
      } else {
        next.add(groupId)
      }
      return next
    })
  }

  function toggleSelectAllGroups() {
    if (groupBulkRunning || workingGroupId !== null) return

    const allSelected =
      groups.length > 0 &&
      groups.every((group) => selectedGroupIds.has(group.id))

    setSelectedGroupIds((current) => {
      const next = new Set(current)
      if (allSelected) {
        groups.forEach((group) => next.delete(group.id))
      } else {
        groups.forEach((group) => next.add(group.id))
      }
      return next
    })
  }

  async function handleDeleteGroup(group: AdminGroup) {
    if (!accessToken || workingGroupId !== null || groupBulkRunning) return

    const confirmed = window.confirm(
      `Permanently delete "${group.name}"? Groups containing service requests cannot be deleted.`
    )

    if (!confirmed) return

    clearMessages()
    setGroupOperationResults([])
    setWorkingGroupId(group.id)

    try {
      const result = await deleteAdminGroup(group.id, accessToken)
      setGroupOperationResults([result])

      if (!result.success) {
        showError(result.message)
        return
      }

      setSelectedGroupIds((current) => {
        const next = new Set(current)
        next.delete(group.id)
        return next
      })

      const refreshed = await loadGroups()
      if (refreshed) {
        showSuccess(result.message)
      } else {
        showError(
          `${result.message} The group list could not be refreshed; its display may be stale.`
        )
      }
    } catch (err) {
      const message = getErrorMessage(err)
      setGroupOperationResults([
        {
          group_id: group.id,
          group_name: group.name,
          success: false,
          message,
        },
      ])
      showError(message)
    } finally {
      setWorkingGroupId(null)
    }
  }

  async function handleBulkDeleteGroups() {
    if (!accessToken || groupBulkRunning || workingGroupId !== null) return

    const groupIds = Array.from(selectedGroupIds)
    if (groupIds.length === 0) {
      showError("Select at least one group to delete.")
      return
    }

    const confirmed = window.confirm(
      `Permanently delete ${groupIds.length} selected group${groupIds.length === 1 ? "" : "s"}? Groups containing service requests will fail individually.`
    )

    if (!confirmed) return

    clearMessages()
    setGroupOperationResults([])
    setGroupBulkRunning(true)

    try {
      const result: BulkAdminGroupDeleteResponse =
        await bulkDeleteAdminGroups(accessToken, groupIds)
      setGroupOperationResults(result.results)
      setSelectedGroupIds(
        new Set(
          result.results
            .filter((item) => !item.success)
            .map((item) => item.group_id)
        )
      )

      const refreshed = await loadGroups()
      const summary =
        `Bulk delete complete: ${result.succeeded} succeeded, ` +
        `${result.failed} failed.`

      if (!refreshed) {
        showError(
          `${summary} The group list could not be refreshed; its display may be stale.`
        )
      } else if (result.failed > 0) {
        showError(`${summary} Review the per-group results below.`)
      } else {
        showSuccess(summary)
      }
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setGroupBulkRunning(false)
    }
  }

  async function handleRoleChange(
    target: AdminUser,
    newRole: string
  ) {
    if (!accessToken || newRole === target.role) return

    if (target.id === user?.id) {
      showError("You cannot change your own administrator role.")
      return
    }

    const confirmed = window.confirm(
      `Change ${target.name}'s role from ${target.role} to ${newRole}?`
    )

    if (!confirmed) {
      await loadUsers()
      return
    }

    clearMessages()
    setWorkingUserId(target.id)

    try {
      await changeAdminUserRole(target.id, newRole, accessToken)
      showSuccess(`${target.name}'s role has been changed to ${newRole}.`)
      await loadUsers()
      await loadOverview()
    } catch (err) {
      showError(getErrorMessage(err))
      await loadUsers()
    } finally {
      setWorkingUserId(null)
    }
  }

  async function handleExportAuditLogs() {
    if (!accessToken) return

    setExporting(true)
    clearMessages()

    try {
      const blob = await exportAdminAuditLogs(accessToken, auditFilters)
      const downloadUrl = window.URL.createObjectURL(blob)
      const anchor = document.createElement("a")

      anchor.href = downloadUrl
      anchor.download = "campusfix-audit-logs.csv"

      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()

      window.URL.revokeObjectURL(downloadUrl)

      showSuccess("Audit log CSV export downloaded.")
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setExporting(false)
    }
  }

  async function refreshCurrentTab() {
    clearMessages()

    if (activeTab === "overview") {
      await loadOverview()
    } else if (activeTab === "users") {
      await loadUsers()
    } else if (activeTab === "groups") {
      await loadGroups()
    } else {
      await loadAuditLogs()
    }
  }

  const rolePercent = (count: number) => {
    if (!stats.total_users) return 0
    return Math.min(100, (count / stats.total_users) * 100)
  }

  const selectableUserIds = users
    .filter(isBulkSelectable)
    .map((target) => target.id)
  const allSelectableUsersSelected =
    selectableUserIds.length > 0 &&
    selectableUserIds.every((id) => selectedUserIds.has(id))
  const selectedBannableCount = users.filter(
    (target) =>
      selectedUserIds.has(target.id) &&
      isBulkSelectable(target) &&
      !target.is_banned
  ).length
  const selectedUnbannableCount = users.filter(
    (target) =>
      selectedUserIds.has(target.id) &&
      isBulkSelectable(target) &&
      target.is_banned
  ).length
  const allGroupsSelected =
    groups.length > 0 &&
    groups.every((group) => selectedGroupIds.has(group.id))

  return (
    <div className="app admin-app">
      <Header />

      <div className="admin-heading">
        <div>
          <span className="admin-eyebrow">CAMPUSFIX CONTROL CENTER</span>
          <h2>Administration</h2>
          <p>Manage users, monitor activity, and oversee the platform.</p>
        </div>

        <button
          className="admin-refresh-button"
          onClick={() => void refreshCurrentTab()}
          disabled={
            loadingOverview ||
            loadingUsers ||
            loadingGroups ||
            loadingAudit ||
            groupBulkRunning ||
            workingGroupId !== null
          }
        >
          ↻ Refresh data
        </button>
      </div>

      {error && (
        <div className="admin-message admin-error" role="alert">
          <span>{error}</span>
          <button onClick={() => setError("")} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      {success && (
        <div className="admin-message admin-success" role="status">
          <span>{success}</span>
          <button onClick={() => setSuccess("")} aria-label="Dismiss message">
            ×
          </button>
        </div>
      )}

      <nav className="admin-tabs" aria-label="Admin sections">
        <button
          className={activeTab === "overview" ? "active" : ""}
          onClick={() => {
            clearMessages()
            setActiveTab("overview")
          }}
        >
          Overview
        </button>

        <button
          className={activeTab === "users" ? "active" : ""}
          onClick={() => {
            clearMessages()
            setActiveTab("users")
          }}
        >
          User Management
        </button>

        <button
          className={activeTab === "groups" ? "active" : ""}
          onClick={() => {
            clearMessages()
            setActiveTab("groups")
          }}
        >
          Groups
        </button>

        <button
          className={activeTab === "audit" ? "active" : ""}
          onClick={() => {
            clearMessages()
            setActiveTab("audit")
          }}
        >
          Audit Logs
        </button>

        <button
          className={activeTab === "security" ? "active" : ""}
          onClick={() => {
            clearMessages()
            setActiveTab("security")
          }}
        >
          Security
        </button>
      </nav>

      {activeTab === "overview" && (
        <section className="admin-section">
          <div className="admin-section-heading">
            <div>
              <h3>Platform overview</h3>
              <p>Current account and platform activity statistics.</p>
            </div>
          </div>

          {loadingOverview ? (
            <div className="admin-panel admin-loading">
              Loading dashboard statistics...
            </div>
          ) : (
            <>
              <div className="admin-stats-grid">
                <article className="admin-stat-card">
                  <span>Total users</span>
                  <strong>{stats.total_users}</strong>
                  <small>All registered accounts</small>
                </article>

                <article className="admin-stat-card">
                  <span>Students</span>
                  <strong>{stats.total_students}</strong>
                  <small>Student accounts</small>
                </article>

                <article className="admin-stat-card">
                  <span>Staff</span>
                  <strong>{stats.total_staff}</strong>
                  <small>Staff accounts</small>
                </article>

                <article className="admin-stat-card">
                  <span>Administrators</span>
                  <strong>{stats.total_admins}</strong>
                  <small>Admin accounts</small>
                </article>

                <article className="admin-stat-card">
                  <span>Active users</span>
                  <strong>{stats.active_users}</strong>
                  <small>Accounts currently active</small>
                </article>

                <article className="admin-stat-card">
                  <span>Inactive users</span>
                  <strong>{stats.inactive_users}</strong>
                  <small>Inactive accounts</small>
                </article>

                <article className="admin-stat-card">
                  <span>Banned users</span>
                  <strong>{stats.banned_users}</strong>
                  <small>Accounts currently banned</small>
                </article>
              </div>

              <div className="admin-overview-grid">
                <section className="admin-panel">
                  <div className="admin-panel-heading">
                    <div>
                      <h3>User distribution</h3>
                      <p>Accounts grouped by role.</p>
                    </div>
                  </div>

                  <div className="admin-role-bars">
                    {[
                      ["Students", stats.total_students],
                      ["Staff", stats.total_staff],
                      ["Administrators", stats.total_admins],
                    ].map(([label, count]) => (
                      <div key={label}>
                        <div className="admin-role-bar-label">
                          <span>{label}</span>
                          <strong>{count}</strong>
                        </div>

                        <div className="admin-progress-track">
                          <div
                            className="admin-progress-fill"
                            style={{
                              width: `${rolePercent(Number(count))}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="admin-panel">
                  <div className="admin-panel-heading">
                    <div>
                      <h3>Account status</h3>
                      <p>Current account availability.</p>
                    </div>
                  </div>

                  <div className="admin-status-summary">
                    <div>
                      <span className="admin-status-dot active-dot" />
                      <span>Active accounts</span>
                      <strong>{stats.active_users}</strong>
                    </div>

                    <div>
                      <span className="admin-status-dot inactive-dot" />
                      <span>Inactive accounts</span>
                      <strong>{stats.inactive_users}</strong>
                    </div>

                    <div>
                      <span className="admin-status-dot banned-dot" />
                      <span>Banned accounts</span>
                      <strong>{stats.banned_users}</strong>
                    </div>
                  </div>
                </section>
              </div>

              <section className="admin-panel admin-recent-panel">
                <div className="admin-panel-heading">
                  <div>
                    <h3>Recent registrations</h3>
                    <p>The latest accounts registered on CampusFix.</p>
                  </div>

                  <button
                    className="admin-text-button"
                    onClick={() => setActiveTab("users")}
                  >
                    Manage users →
                  </button>
                </div>

                {recentUsers.length === 0 ? (
                  <div className="admin-empty">
                    No recent registrations found.
                  </div>
                ) : (
                  <div className="admin-table-wrap">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>User</th>
                          <th>Role</th>
                          <th>Registered</th>
                        </tr>
                      </thead>

                      <tbody>
                        {recentUsers.map((recent) => (
                          <tr key={recent.id}>
                            <td>
                              <div className="admin-user-cell">
                                <div className="admin-user-avatar">
                                  {recent.name.charAt(0).toUpperCase()}
                                </div>

                                <div>
                                  <strong>{recent.name}</strong>
                                  <span>{recent.email}</span>
                                </div>
                              </div>
                            </td>

                            <td>
                              <span className="admin-role-badge">
                                {recent.role}
                              </span>
                            </td>

                            <td>{formatDate(recent.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          )}
        </section>
      )}

      {activeTab === "users" && (
        <section className="admin-section">
          <div className="admin-section-heading">
            <div>
              <h3>User management</h3>
              <p>Search accounts, update roles, and manage account access.</p>
            </div>

            <span className="admin-result-count">
              {usersTotal} users
            </span>
          </div>

          <form className="admin-filter-panel" onSubmit={applyUserFilters}>
            <label>
              Search users
              <input
                type="search"
                placeholder="Name or email..."
                value={userSearch}
                onChange={(event) => {
                  setUserSearch(event.target.value)
                  setAppliedSearch(event.target.value)
                }}
              />
            </label>

            <label>
              Role
              <select
                value={userRoleFilter}
                onChange={(event) => setUserRoleFilter(event.target.value)}
              >
                <option value="">All roles</option>
                <option value="STUDENT">Student</option>
                <option value="STAFF">Staff</option>
                <option value="ADMIN">Admin</option>
              </select>
            </label>

            <label>
              Account status
              <select
                value={userStatusFilter}
                onChange={(event) => setUserStatusFilter(event.target.value)}
              >
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </label>

            <button className="admin-export-button" type="submit">
              Apply filters
            </button>

            <button
              className="admin-secondary-button"
              type="button"
              onClick={resetUserFilters}
            >
              Reset
            </button>
          </form>

          <div className="admin-bulk-toolbar">
            <div className="admin-bulk-selection">
              <label>
                <input
                  type="checkbox"
                  checked={allSelectableUsersSelected}
                  disabled={bulkRunning || selectableUserIds.length === 0}
                  onChange={toggleSelectAllUsers}
                  aria-label="Select eligible users on this page"
                />
                <span>Select all eligible</span>
              </label>
              <strong>
                {selectedUserIds.size} selected
              </strong>
            </div>

            <div className="admin-bulk-actions">
              <button
                type="button"
                className="admin-action-button ban"
                disabled={bulkRunning || selectedBannableCount === 0}
                onClick={() => void handleBulkBanUsers()}
              >
                {bulkRunning ? "Working..." : `Bulk ban (${selectedBannableCount})`}
              </button>
              <button
                type="button"
                className="admin-action-button unban"
                disabled={bulkRunning || selectedUnbannableCount === 0}
                onClick={() => void handleBulkUnbanUsers()}
              >
                {bulkRunning ? "Working..." : `Bulk unban (${selectedUnbannableCount})`}
              </button>
            </div>
          </div>

          <section className="admin-panel">
            {loadingUsers ? (
              <div className="admin-loading">Loading users...</div>
            ) : users.length === 0 ? (
              <div className="admin-empty">No users found.</div>
            ) : (
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th className="admin-select-column">
                        <input
                          type="checkbox"
                          checked={allSelectableUsersSelected}
                          disabled={bulkRunning || selectableUserIds.length === 0}
                          onChange={toggleSelectAllUsers}
                          aria-label="Select all eligible users on this page"
                        />
                      </th>
                      <th>User</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Registered</th>
                      <th>Details</th>
                      <th>Change role</th>
                      <th>Account action</th>
                    </tr>
                  </thead>

                  <tbody>
                    {users.map((target) => {
                      const isSelf = target.id === user?.id
                      const isWorking = workingUserId === target.id

                      return (
                        <tr key={target.id}>
                          <td className="admin-select-column">
                            <input
                              type="checkbox"
                              checked={selectedUserIds.has(target.id)}
                              disabled={bulkRunning || !isBulkSelectable(target)}
                              onChange={() => toggleUserSelection(target)}
                              aria-label={`Select ${target.name}`}
                            />
                          </td>
                          <td>
                            <div className="admin-user-cell">
                              <div className="admin-user-avatar">
                                {target.name.charAt(0).toUpperCase()}
                              </div>

                              <div>
                                <strong>{target.name}</strong>
                                <span>{target.email}</span>
                              </div>
                            </div>
                          </td>

                          <td>
                            <span className="admin-role-badge">
                              {target.role}
                            </span>
                          </td>

                          <td>
                            <span
                              className={`admin-status-badge ${
                                target.is_banned
                                  ? "banned"
                                  : target.is_active
                                    ? "active"
                                    : "inactive"
                              }`}
                            >
                              {getUserStatus(target)}
                            </span>
                          </td>

                          <td>{formatDate(target.created_at)}</td>

                          <td>
                            <button
                              className="admin-secondary-button admin-details-button"
                              type="button"
                              disabled={
                                loadingUserDetail ||
                                workingSessionId !== null
                              }
                              onClick={() => void handleViewUserDetails(target)}
                            >
                              View details
                            </button>
                          </td>

                          <td>
                            {isSelf ? (
                              <span className="admin-self-note">
                                Your account
                              </span>
                            ) : (
                              <select
                                className="admin-role-select"
                                value={target.role}
                                disabled={isWorking}
                                onChange={(event) =>
                                  void handleRoleChange(
                                    target,
                                    event.target.value
                                  )
                                }
                                aria-label={`Change role for ${target.name}`}
                              >
                                <option value="STUDENT">Student</option>
                                <option value="STAFF">Staff</option>
                                <option value="ADMIN">Admin</option>
                              </select>
                            )}
                          </td>

                          <td>
                            {isSelf || target.role === "ADMIN" ? (
                              <span className="admin-self-note">
                                Protected
                              </span>
                            ) : target.is_banned ? (
                              <button
                                className="admin-action-button unban"
                                disabled={isWorking}
                                onClick={() => void handleUnbanUser(target)}
                              >
                                {isWorking ? "Wait..." : "Unban"}
                              </button>
                            ) : (
                              <button
                                className="admin-action-button ban"
                                disabled={isWorking}
                                onClick={() => void handleBanUser(target)}
                              >
                                {isWorking ? "Wait..." : "Ban"}
                              </button>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <div className="admin-pagination">
              <span>
                Page {usersPage} of {Math.max(usersTotalPages, 1)}
              </span>

              <div>
                <button
                  disabled={usersPage <= 1 || loadingUsers}
                  onClick={() => changeUsersPage(usersPage - 1)}
                >
                  Previous
                </button>

                <button
                  disabled={
                    usersPage >= usersTotalPages || loadingUsers
                  }
                  onClick={() => changeUsersPage(usersPage + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </section>
        </section>
      )}

      {activeTab === "groups" && (
        <section className="admin-section">
          <div className="admin-section-heading">
            <div>
              <h3>Group management</h3>
              <p>
                Review campus groups and remove groups without service
                requests.
              </p>
            </div>

            <span className="admin-result-count">
              {groupsTotal} groups
            </span>
          </div>

          <div className="admin-bulk-toolbar">
            <div className="admin-bulk-selection">
              <label>
                <input
                  type="checkbox"
                  checked={allGroupsSelected}
                  disabled={
                    groupBulkRunning ||
                    workingGroupId !== null ||
                    groups.length === 0
                  }
                  onChange={toggleSelectAllGroups}
                  aria-label="Select all groups on this page"
                />
                <span>Select all on this page</span>
              </label>
              <strong>{selectedGroupIds.size} selected</strong>
            </div>

            <div className="admin-bulk-actions">
              <button
                type="button"
                className="admin-action-button ban"
                disabled={
                  groupBulkRunning ||
                  workingGroupId !== null ||
                  selectedGroupIds.size === 0
                }
                onClick={() => void handleBulkDeleteGroups()}
              >
                {groupBulkRunning
                  ? "Deleting..."
                  : `Delete selected (${selectedGroupIds.size})`}
              </button>
            </div>
          </div>

          <section className="admin-panel">
            {loadingGroups ? (
              <div className="admin-loading">Loading groups...</div>
            ) : groups.length === 0 ? (
              <div className="admin-empty">No groups found.</div>
            ) : (
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th className="admin-select-column">
                        <input
                          type="checkbox"
                          checked={allGroupsSelected}
                          disabled={
                            groupBulkRunning ||
                            workingGroupId !== null ||
                            groups.length === 0
                          }
                          onChange={toggleSelectAllGroups}
                          aria-label="Select all groups on this page"
                        />
                      </th>
                      <th>Group</th>
                      <th>Owner</th>
                      <th>Members</th>
                      <th>Requests</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Action</th>
                    </tr>
                  </thead>

                  <tbody>
                    {groups.map((group) => (
                      <tr key={group.id}>
                        <td className="admin-select-column">
                          <input
                            type="checkbox"
                            checked={selectedGroupIds.has(group.id)}
                            disabled={
                              groupBulkRunning || workingGroupId !== null
                            }
                            onChange={() => toggleGroupSelection(group.id)}
                            aria-label={`Select ${group.name}`}
                          />
                        </td>
                        <td>
                          <div className="admin-group-name">
                            <strong className="admin-user-name">
                              {group.name}
                            </strong>
                            <span className="admin-group-description">
                              {group.description || "No description"}
                            </span>
                          </div>
                        </td>
                        <td>
                          <div className="admin-group-owner">
                            <strong>{group.owner_name}</strong>
                            <span>{group.owner_email}</span>
                          </div>
                        </td>
                        <td>{group.member_count}</td>
                        <td>{group.request_count}</td>
                        <td>
                          <span
                            className={`admin-status-badge ${
                              group.is_archived ? "inactive" : "active"
                            }`}
                          >
                            {group.is_archived ? "Archived" : "Active"}
                          </span>
                        </td>
                        <td>{formatDate(group.created_at)}</td>
                        <td>
                          <button
                            type="button"
                            className="admin-action-button ban"
                            disabled={
                              groupBulkRunning || workingGroupId !== null
                            }
                            onClick={() => void handleDeleteGroup(group)}
                          >
                            {workingGroupId === group.id
                              ? "Deleting..."
                              : "Delete"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="admin-pagination">
              <span>
                Page {groupsPage} of {Math.max(groupsTotalPages, 1)}
              </span>

              <div>
                <button
                  disabled={
                    groupsPage <= 1 ||
                    loadingGroups ||
                    groupBulkRunning ||
                    workingGroupId !== null
                  }
                  onClick={() => {
                    setSelectedGroupIds(new Set())
                    setGroupsPage((page) => page - 1)
                  }}
                >
                  Previous
                </button>

                <button
                  disabled={
                    groupsPage >= groupsTotalPages ||
                    loadingGroups ||
                    groupBulkRunning ||
                    workingGroupId !== null
                  }
                  onClick={() => {
                    setSelectedGroupIds(new Set())
                    setGroupsPage((page) => page + 1)
                  }}
                >
                  Next
                </button>
              </div>
            </div>
          </section>

          {groupOperationResults.length > 0 && (
            <section
              className="admin-panel admin-group-results"
              aria-live="polite"
            >
              <div className="admin-panel-heading">
                <div>
                  <h3>Deletion results</h3>
                  <p>Each selected group is reported separately.</p>
                </div>
              </div>

              <ul>
                {groupOperationResults.map((result) => {
                  const groupName =
                    result.group_name ||
                    groups.find((group) => group.id === result.group_id)
                      ?.name ||
                    result.group_id

                  return (
                    <li
                      className={
                        result.success
                          ? "admin-group-result success"
                          : "admin-group-result failure"
                      }
                      key={result.group_id}
                    >
                      <span className="admin-group-result-status">
                        {result.success ? "Succeeded" : "Failed"}
                      </span>
                      <strong>{groupName}</strong>
                      <span>{result.message}</span>
                    </li>
                  )
                })}
              </ul>
            </section>
          )}
        </section>
      )}

      {activeTab === "audit" && (
        <section className="admin-section">
          <div className="admin-section-heading">
            <div>
              <h3>Audit logs</h3>
              <p>Review recorded account and administrator activities.</p>
            </div>

            <button
              className="admin-export-button"
              onClick={() => void handleExportAuditLogs()}
              disabled={exporting}
            >
              {exporting ? "Exporting..." : "↓ Export CSV"}
            </button>
          </div>

          <form
            className="admin-filter-panel admin-audit-filters"
            onSubmit={applyAuditFilters}
          >
            <label>
              Action
              <input
                type="text"
                placeholder="e.g. LOGIN_SUCCESS"
                value={auditAction}
                onChange={(event) => setAuditAction(event.target.value)}
              />
            </label>

            <label>
              Email
              <input
                type="search"
                placeholder="Search email..."
                value={auditEmail}
                onChange={(event) => setAuditEmail(event.target.value)}
              />
            </label>

            <label>
              Start date
              <input
                type="date"
                value={auditStartDate}
                onChange={(event) => setAuditStartDate(event.target.value)}
              />
            </label>

            <label>
              End date
              <input
                type="date"
                value={auditEndDate}
                onChange={(event) => setAuditEndDate(event.target.value)}
              />
            </label>

            <button className="admin-export-button" type="submit">
              Apply filters
            </button>

            <button
              className="admin-secondary-button"
              type="button"
              onClick={resetAuditFilters}
            >
              Reset
            </button>
          </form>

          <section className="admin-panel">
            <div className="admin-panel-heading">
              <div>
                <h3>Activity history</h3>
                <p>{auditTotal} matching audit events</p>
              </div>
            </div>

            {loadingAudit ? (
              <div className="admin-loading">Loading audit logs...</div>
            ) : auditLogs.length === 0 ? (
              <div className="admin-empty">No audit events found.</div>
            ) : (
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Action</th>
                      <th>Email</th>
                      <th>IP address</th>
                      <th>Details</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>

                  <tbody>
                    {auditLogs.map((log) => (
                      <tr key={log.id}>
                        <td>
                          <span className="admin-action-badge">
                            {log.action}
                          </span>
                        </td>

                        <td>{log.email || "—"}</td>
                        <td>{log.ip_address || "—"}</td>

                        <td>
                          <div className="admin-audit-details">
                            {log.details || "—"}
                          </div>
                        </td>

                        <td>{formatDate(log.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="admin-pagination">
              <span>
                Page {auditPage} of {Math.max(auditTotalPages, 1)}
              </span>

              <div>
                <button
                  disabled={auditPage <= 1 || loadingAudit}
                  onClick={() => changeAuditPage(auditPage - 1)}
                >
                  Previous
                </button>

                <button
                  disabled={
                    auditPage >= auditTotalPages || loadingAudit
                  }
                  onClick={() => changeAuditPage(auditPage + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </section>
        </section>
      )}

      {activeTab === "security" && (
        <SecurityDashboard accessToken={accessToken} />
      )}

      {(loadingUserDetail || selectedUserDetail || userDetailError) && (
        <div className="admin-detail-overlay">
          <section
            className="admin-detail-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="admin-detail-title"
          >
            <div className="admin-detail-heading">
              <div>
                <span className="admin-eyebrow">CAMPUSFIX ACCOUNT</span>
                <h2 id="admin-detail-title">User details</h2>
                <p>Account information and activity.</p>
              </div>

              <button
                type="button"
                className="admin-secondary-button"
                disabled={workingSessionId !== null}
                onClick={closeUserDetails}
              >
                Close
              </button>
            </div>

            {loadingUserDetail ? (
              <div className="admin-loading">
                Loading user details...
              </div>
            ) : userDetailError ? (
              <div className="admin-message admin-error" role="alert">
                {userDetailError}
              </div>
            ) : selectedUserDetail ? (
              <>
                <section className="admin-detail-section">
                  <h3>Profile information</h3>

                  <div className="admin-detail-profile">
                    <div className="admin-user-avatar admin-detail-avatar">
                      {selectedUserDetail.user.name.charAt(0).toUpperCase()}
                    </div>

                    <div>
                      <strong>{selectedUserDetail.user.name}</strong>
                      <span>{selectedUserDetail.user.email}</span>
                    </div>
                  </div>

                  <div className="admin-detail-grid">
                    <div>
                      <span>Role</span>
                      <strong>{selectedUserDetail.user.role}</strong>
                    </div>

                    <div>
                      <span>Account status</span>
                      <strong>{getUserStatus(selectedUserDetail.user)}</strong>
                    </div>

                    <div>
                      <span>Registration date</span>
                      <strong>
                        {formatDate(selectedUserDetail.user.created_at)}
                      </strong>
                    </div>

                    <div>
                      <span>Ban date</span>
                      <strong>
                        {formatDate(selectedUserDetail.user.banned_at)}
                      </strong>
                    </div>
                  </div>

                  {selectedUserDetail.user.is_banned && (
                    <div className="admin-detail-note">
                      <strong>Ban reason</strong>
                      <p>
                        {selectedUserDetail.user.ban_reason ||
                          "No reason provided"}
                      </p>
                    </div>
                  )}
                </section>

                <section className="admin-detail-section">
                  <h3>
                    Service requests (
                    {selectedUserDetail.service_requests.length})
                  </h3>

                  {selectedUserDetail.service_requests.length === 0 ? (
                    <div className="admin-empty">
                      No service requests found.
                    </div>
                  ) : (
                    <div className="admin-detail-list">
                      {selectedUserDetail.service_requests.map((request) => (
                        <article
                          key={request.id}
                          className="admin-detail-item"
                        >
                          <strong>{request.title}</strong>
                          <p>{request.description}</p>

                          <div className="admin-detail-meta">
                            <span>Category: {request.category}</span>
                            <span>Status: {request.status}</span>
                            <span>
                              Created: {formatDate(request.created_at)}
                            </span>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <section className="admin-detail-section">
                  <h3>
                    Groups ({selectedUserDetail.groups.length})
                  </h3>

                  {selectedUserDetail.groups.length === 0 ? (
                    <div className="admin-empty">
                      This user does not belong to any groups.
                    </div>
                  ) : (
                    <div className="admin-detail-list">
                      {selectedUserDetail.groups.map((group) => (
                        <article
                          key={group.id}
                          className="admin-detail-item"
                        >
                          <div className="admin-detail-item-heading">
                            <strong>{group.name}</strong>
                            <span className="admin-role-badge">
                              {group.is_owner ? "Owner" : "Member"}
                            </span>
                          </div>

                          <p>{group.description || "No description"}</p>

                          <div className="admin-permission-list">
                            <span>
                              Create requests:{" "}
                              {group.can_create_requests ? "Allowed" : "Denied"}
                            </span>

                            <span>
                              Edit requests:{" "}
                              {group.can_edit_requests ? "Allowed" : "Denied"}
                            </span>

                            <span>
                              Assign requests:{" "}
                              {group.can_assign_requests ? "Allowed" : "Denied"}
                            </span>
                          </div>

                          {group.is_archived && (
                            <span className="admin-status-badge inactive">
                              Archived
                            </span>
                          )}
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <section className="admin-detail-section">
                  <h3>
                    Login sessions ({selectedUserDetail.sessions.length})
                  </h3>

                  {sessionActionError && (
                    <div className="admin-message admin-error" role="alert">
                      {sessionActionError}
                    </div>
                  )}

                  {sessionActionSuccess && (
                    <div className="admin-message admin-success" role="status">
                      {sessionActionSuccess}
                    </div>
                  )}

                  {selectedUserDetail.sessions.length === 0 ? (
                    <div className="admin-empty">
                      No sessions found.
                    </div>
                  ) : (
                    <div className="admin-detail-list">
                      {selectedUserDetail.sessions.map((session) => (
                        <article
                          key={session.id}
                          className="admin-detail-item"
                        >
                          <div className="admin-detail-item-heading">
                            <strong>Session</strong>

                            <span
                              className={`admin-status-badge ${
                                session.is_active ? "active" : "inactive"
                              }`}
                            >
                              {session.is_active ? "Active" : "Inactive"}
                            </span>
                          </div>

                          <div className="admin-detail-meta">
                            <span>
                              Created: {formatDate(session.created_at)}
                            </span>

                            <span>
                              Expires: {formatDate(session.expires_at)}
                            </span>

                            <span>
                              Revoked:{" "}
                              {session.revoked_at
                                ? formatDate(session.revoked_at)
                                : "No"}
                            </span>
                          </div>

                          {session.is_active && (
                            <button
                              type="button"
                              className="admin-action-button ban"
                              disabled={workingSessionId !== null}
                              onClick={() => void handleRevokeSession(session)}
                              aria-busy={workingSessionId === session.id}
                              aria-label={
                                workingSessionId === session.id
                                  ? `Revoking session ${session.id}`
                                  : `Revoke session ${session.id}`
                              }
                            >
                              {workingSessionId === session.id
                                ? "Revoking..."
                                : "Revoke"}
                            </button>
                          )}
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <section className="admin-detail-section">
                  <h3>
                    Recent activity (
                    {selectedUserDetail.recent_activity.length})
                  </h3>

                  {selectedUserDetail.recent_activity.length === 0 ? (
                    <div className="admin-empty">
                      No recent activity found.
                    </div>
                  ) : (
                    <div className="admin-detail-list">
                      {selectedUserDetail.recent_activity.map((activity) => (
                        <article
                          key={activity.id}
                          className="admin-detail-item"
                        >
                          <div className="admin-detail-item-heading">
                            <strong>{activity.action}</strong>
                            <span>
                              {formatDate(activity.created_at)}
                            </span>
                          </div>

                          <div className="admin-detail-meta">
                            <span>Email: {activity.email || "—"}</span>
                            <span>
                              IP address: {activity.ip_address || "—"}
                            </span>
                          </div>

                          {activity.details && (
                            <p>{activity.details}</p>
                          )}
                        </article>
                      ))}
                    </div>
                  )}
                </section>
              </>
            ) : null}
          </section>
        </div>
      )}
    </div>
  )
}
