
import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react"
import { useNavigate } from "react-router"

import Header from "../components/Header"
import { useAuth } from "../contexts/AuthContext"
import { getGroups, createGroup } from "../services/groups"
import type { Group } from "../types/group"

import "./GroupsPage.css"

export default function GroupsPage() {
  const { accessToken } = useAuth()
  const navigate = useNavigate()

  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")

  const loadGroups = useCallback(async () => {
    if (!accessToken) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError("")

      const data = await getGroups(accessToken)
      setGroups(data)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load groups."
      )
    } finally {
      setLoading(false)
    }
  }, [accessToken])

  useEffect(() => {
    void loadGroups()
  }, [loadGroups])

  async function handleCreateGroup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!accessToken || !name.trim()) return

    try {
      setCreating(true)
      setError("")
      setSuccess("")

      await createGroup(
        {
          name: name.trim(),
          description: description.trim() || null,
        },
        accessToken
      )

      setName("")
      setDescription("")
      setSuccess("Your group has been created successfully.")

      await loadGroups()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create group."
      )
    } finally {
      setCreating(false)
    }
  }

  function openGroup(groupId: string) {
    navigate(`/groups/${groupId}`)
  }

  function handleGroupKeyDown(
    event: KeyboardEvent<HTMLElement>,
    groupId: string
  ) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      openGroup(groupId)
    }
  }

  const activeGroups = groups.filter(
    (group) => !group.is_archived
  ).length

  const archivedGroups = groups.length - activeGroups

  const ownedGroups = groups.filter(
    (group) => group.is_owner
  ).length

  return (
    <>
      <Header />

      <main className="app groups-page">
        <section className="groups-hero">
          <div>
            <p className="eyebrow">CAMPUSFIX COLLABORATION</p>
            <h1>Shared Groups</h1>

            <p className="groups-subtitle">
              Bring your campus community together. Create groups,
              collaborate with members, and manage shared service requests.
            </p>
          </div>

          <div className="groups-hero-icon" aria-hidden="true">
            <span>♧</span>
          </div>
        </section>

        <section className="groups-stats">
          <article className="group-stat-card">
            <span className="group-stat-icon blue">♧</span>
            <div>
              <p>Total groups</p>
              <strong>{groups.length}</strong>
            </div>
          </article>

          <article className="group-stat-card">
            <span className="group-stat-icon green">✓</span>
            <div>
              <p>Active groups</p>
              <strong>{activeGroups}</strong>
            </div>
          </article>

          <article className="group-stat-card">
            <span className="group-stat-icon purple">★</span>
            <div>
              <p>Groups you own</p>
              <strong>{ownedGroups}</strong>
            </div>
          </article>

          <article className="group-stat-card">
            <span className="group-stat-icon amber">▣</span>
            <div>
              <p>Archived groups</p>
              <strong>{archivedGroups}</strong>
            </div>
          </article>
        </section>

        <section className="groups-layout">
          <div className="panel groups-create-panel">
            <div className="groups-section-heading">
              <div className="groups-heading-icon">＋</div>

              <div>
                <h2>Create a group</h2>
                <p>
                  Start collaborating with your campus community.
                </p>
              </div>
            </div>

            <form className="groups-form" onSubmit={handleCreateGroup}>
              <label htmlFor="group-name">
                Group name <span>*</span>

                <input
                  id="group-name"
                  type="text"
                  placeholder="e.g. CSE Project Team"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  maxLength={100}
                  required
                />
              </label>

              <label htmlFor="group-description">
                Description

                <textarea
                  id="group-description"
                  placeholder="Describe what this group is about..."
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  rows={4}
                />
              </label>

              <button
                className="primary-button groups-submit"
                type="submit"
                disabled={creating || !name.trim()}
              >
                {creating ? "Creating group..." : "＋ Create Group"}
              </button>
            </form>

            {error && <p className="error-message">{error}</p>}
            {success && <p className="success-message">{success}</p>}

            <div className="groups-tip">
              <strong>💡 Good to know</strong>
              <p>
                As the group owner, you'll be able to invite members
                and manage their permissions.
              </p>
            </div>
          </div>

          <div className="panel groups-list-panel">
            <div className="groups-list-heading">
              <div>
                <h2>Your groups</h2>
                <p className="panel-description">
                  Groups you've created or joined.
                </p>
              </div>

              <button
                className="refresh-button"
                type="button"
                onClick={() => void loadGroups()}
                disabled={loading}
              >
                {loading ? "Loading..." : "↻ Refresh"}
              </button>
            </div>

            {loading ? (
              <div className="groups-empty">
                <div className="groups-empty-icon">↻</div>
                <h3>Loading your groups</h3>
                <p>Please wait while we retrieve your groups.</p>
              </div>
            ) : groups.length === 0 ? (
              <div className="groups-empty">
                <div className="groups-empty-icon">♧</div>
                <h3>No groups yet</h3>
                <p>
                  You haven't joined any groups. Create your first group
                  to start collaborating!
                </p>
              </div>
            ) : (
              <div className="groups-card-list">
                {groups.map((group) => (
                  <article
                    className="group-card clickable"
                    key={group.id}
                    onClick={() => openGroup(group.id)}
                    onKeyDown={(event) =>
                      handleGroupKeyDown(event, group.id)
                    }
                    role="button"
                    tabIndex={0}
                    aria-label={`Open group ${group.name}`}
                  >
                    <div className="group-card-top">
                      <div className="group-card-icon">♧</div>

                      <span
                        className={`group-status ${
                          group.is_archived ? "archived" : "active"
                        }`}
                      >
                        {group.is_archived ? "Archived" : "Active"}
                      </span>
                    </div>

                    <h3>{group.name}</h3>

                    <p className="group-card-description">
                      {group.description || "No description provided."}
                    </p>

                    <div className="group-card-footer">
                      <span className="group-role">
                        {group.is_owner ? "★ Owner" : "♧ Member"}
                      </span>

                      <span className="group-date">
                        {new Date(
                          group.created_at
                        ).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="group-card-open">
                      View group details →
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </>
  )
}
