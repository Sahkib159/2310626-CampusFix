Independent University, Bangladesh\
CSE309 Web Application & Internet

# Final Project Submission Report

**Submitted by:**\
Name: Sahkib Ahad Chowdhury\
Student ID: 2310626\
Section: 06\
Team Number: N/A

Project Title: CampusFix\
Vercel URL: https://2310626.vercel.app\
GitHub Repository: https://github.com/Sahkib159/2310626-CampusFix

**Submitted To:**\
Sayef Reyadh\
Adjunct Lecturer\
Department of Computer Science & Engineering\
Independent University, Bangladesh

Semester: Autumn 2026\
Date of Submission: 28.11.2026

> Diagram image files are stored in `docs/images/` and referenced below. Test account credentials are not written in this file; they are provided separately through the approved submission channel.

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
  - [1.1 Project overview](#11-project-overview)
  - [1.2 What was built since the mid assessment](#12-what-was-built-since-the-mid-assessment)
  - [1.3 Live links](#13-live-links)
- [Part A. Product Requirements (PRD)](#part-a-product-requirements-prd)
  - [A1. Problem Statement](#a1-problem-statement)
  - [A2. Users and Roles](#a2-users-and-roles)
  - [A3. Goals and Success Measures](#a3-goals-and-success-measures)
  - [A4. Scope and Non-Goals](#a4-scope-and-non-goals)
  - [A5. User Stories](#a5-user-stories)
- [Part B. Software Requirements (SRS)](#part-b-software-requirements-srs)
  - [B1. Introduction](#b1-introduction)
  - [B2. Functional Requirements](#b2-functional-requirements)
  - [B3. Non-Functional Requirements](#b3-non-functional-requirements)
  - [B4. Roles and Permission Matrix](#b4-roles-and-permission-matrix)
  - [B5. Use Cases](#b5-use-cases)
  - [B6. Acceptance Criteria](#b6-acceptance-criteria)
  - [B7. Traceability Matrix](#b7-traceability-matrix)
- [Part C. Technical Design (TDD)](#part-c-technical-design-tdd)
  - [C1. Technology Stack](#c1-technology-stack)
  - [C2. System Architecture](#c2-system-architecture)
  - [C3. Backend and Frontend Structure](#c3-backend-and-frontend-structure)
  - [C4. Data Model](#c4-data-model)
  - [C5. API Design](#c5-api-design)
  - [C6. JWT Authentication Design](#c6-jwt-authentication-design)
  - [C7. RBAC Design](#c7-rbac-design)
  - [C8. Admin Dashboard Design](#c8-admin-dashboard-design)
  - [C9. Security Design and Threats](#c9-security-design-and-threats)
  - [C10. Deployment on Vercel](#c10-deployment-on-vercel)
  - [C11. Testing](#c11-testing)
- [Part E. Project Management and Conclusion](#part-e-project-management-and-conclusion)
  - [E1. How to Run and Test](#e1-how-to-run-and-test)
  - [E2. GitHub Work](#e2-github-work)
  - [E3. Limitations](#e3-limitations)
  - [E4. Future Work](#e4-future-work)
  - [E5. Sources, Libraries and Tools](#e5-sources-libraries-and-tools)

### List of Figures

| No. | Caption | Section |
|---|---|---|
| Diagram 1 | Use case diagram | B5 |
| Diagram 2 | Detailed system architecture | C2 |
| Diagram 3 | Entity relationship diagram (ERD) | C4 |
| Diagram 4 | JWT authentication and refresh sequence diagram | C6 |
| Diagram 5 | Request authorization flow | C7 |
| Diagram 6 | Admin dashboard pages and API endpoints | C8 |
| Diagram 7 | Deployment architecture | C10 |

---

## 1. Executive Summary

### 1.1 Project overview

CampusFix is a web-based Campus Service Request Management System that organizes the reporting and handling of campus maintenance and service issues. Students create and track requests, authorized staff work with requests assigned to them, and administrators manage user accounts, inspect activity and security information, and perform administrative operations. The system also supports shared groups, in which an owner manages membership and each member receives individual create, edit and assign permissions. The backend enforces authentication and authorization itself and does not rely on frontend visibility.

**Stack:** React 19 and TypeScript (Vite 8) on the frontend; FastAPI (Python), SQLModel and a PostgreSQL-compatible database on the backend; PyJWT, Argon2, pytest; deployed on Vercel.

### 1.2 What was built since the mid assessment

- **JWT authentication:** signup, login, refresh, logout, profile management, password change and session controls.
- **Role-based access control:** server-side checks for STUDENT, STAFF and ADMIN, plus resource ownership and group-level permissions.
- **Shared groups:** owner-controlled membership, permission assignment, archive/unarchive and protected deletion.
- **Admin dashboard:** user search, role/status filters, pagination, user details, ban/unban, role changes, bulk actions, session revocation, group listing/deletion and dashboard statistics.
- **Audit logging and security view:** audit-log filtering, CSV export, and failed-login attempts grouped by account and IP.
- **Hardened authentication:** Argon2 hashing with a server-side pepper for new hashes, short-lived signed access tokens, hashed rotating refresh tokens and login rate limits.
- **Request search:** service-request search in the UI by title, description and request ID.
- **Security fix (PR #45):** prevents an administrator from changing another administrator's role.
- **Deployment on Vercel** (frontend and API under one domain).

### 1.3 Live links

| Item | Link |
|---|---|
| GitHub repository | https://github.com/Sahkib159/2310626-CampusFix |
| Production frontend | https://2310626.vercel.app |
| API base | https://2310626.vercel.app/api |
| API documentation (Swagger) | https://2310626.vercel.app/api/docs |
| Health endpoint | https://2310626.vercel.app/api/health |
| Video demo | https://youtu.be/PFrniyyMCHo |

*Table 1: Live links*

---

## Part A. Product Requirements (PRD)

### A1. Problem Statement

Campus maintenance and service issues need a clear reporting and follow-up process. When reports are handled through informal conversations, messages or disconnected channels, students may not know whether an issue has been received or who is responsible for it. Staff find it hard to organize incoming issues, identify assigned work and keep a consistent record of progress.

A campus service workflow therefore needs reliable request records, clear responsibility and controlled access to information. Shared work also needs permission boundaries: a group owner should control membership, while members should only perform actions that were granted to them. Administrative actions need accountability so that account and security changes can be reviewed.

### A2. Users and Roles

| Role | Who they are | Main tasks | Must never be able to |
|---|---|---|---|
| Visitor | Person who has not authenticated | Open the public frontend; register and sign in | Access protected API data or perform protected actions |
| STUDENT | Registered student | Create and view own requests; take part in groups according to membership permissions; manage own profile and sessions | Read or modify another student's private request; perform staff/admin-only actions |
| STAFF | Authorized service staff account | Work with requests assigned or shared with them; use group actions only when permitted | Access admin endpoints or bypass ownership/group permission checks |
| Group member | User added to a shared group | View group resources; create/edit/assign when the matching flag allows | Manage group ownership or membership; perform an action whose permission is false |
| Group owner | User recorded as the group's owner | Update group details; manage members and permissions; archive/unarchive; delete eligible groups | Delete a group that still contains service requests; override platform-wide admin protections |
| ADMIN | Platform administrator | Manage users and groups; inspect audit/security data; use the admin dashboard | Change their own role or another ADMIN's role; bypass protected deletion safeguards |

*Table 2: Users and roles*

### A3. Goals and Success Measures

| Goal | Success measure |
|---|---|
| Authenticate users securely | Protected endpoints reject missing, invalid, tampered or expired access tokens with HTTP 401. |
| Restrict private data | A user cannot read another user's private service requests unless access is granted through the supported group workflow. |
| Enforce group permissions | Create, edit and assign operations are denied when the matching member permission is disabled. |
| Provide administrative control | Admin user management supports search, role/status filtering and pagination; ban/unban and bulk actions succeed for valid requests. |
| Maintain auditability | Administrative and authentication events can be filtered in the audit log and exported as CSV. |
| Reduce account attacks | Login attempts are limited by account and IP within a 15-minute window. |

*Table 3: Goals and success measures*

### A4. Scope and Non-Goals

**In scope**

- Signup/login and authenticated profile functions.
- Student, staff and admin roles.
- Service-request creation, viewing, update/delete, staff assignment and user-side search.
- Shared groups, owner-managed membership and create/edit/assign member permissions.
- Admin user and group operations, dashboard statistics, audit logs, security view and CSV export.
- Automated backend tests and deployment configuration for Vercel.

**Out of scope or not implemented in this release**

- AI/ML classification, chatbots, recommendation engines, payments, native mobile applications and complex third-party university integrations.
- A complete admin content-moderation interface for all service requests.
- Dedicated category CRUD/administration.
- A complete request lifecycle with enforced transition rules, resolution notes and student cancellation.
- CSV exports for users and service requests (only the audit-log export is implemented).

**Assumptions and constraints**

- A semester-based academic project built with React/TypeScript and FastAPI.
- A modern browser and network access are required.
- Production secrets and database credentials are configured outside source control.
- Hosted behaviour depends on the Vercel project settings and the connected database.
- This report describes only features that work on the deployed URL at submission time.

### A5. User Stories

| ID | User story |
|---|---|
| US-01 | As a visitor, I want to create a student account so that I can use the request system. |
| US-02 | As a registered user, I want to log in and refresh my session so that I can continue using protected features. |
| US-03 | As a user, I want to log out and revoke sessions so that I can end access from a device. |
| US-04 | As a student, I want to create a service request so that a campus issue can be recorded. |
| US-05 | As a student, I want to search requests by title, description or request ID so that I can find a specific record. |
| US-06 | As a group owner, I want to add members and set their permissions so that work can be shared safely. |
| US-07 | As a group member, I want to perform only the actions granted to me so that group data remains controlled. |
| US-08 | As a group owner, I want to archive or delete an eligible group so that inactive groups can be managed. |
| US-09 | As an administrator, I want to search, filter and paginate users so that I can locate accounts efficiently. |
| US-10 | As an administrator, I want to ban or unban users with a reason so that abusive accounts can be restricted. |
| US-11 | As an administrator, I want to inspect user sessions and revoke a session family so that suspicious access can be stopped. |
| US-12 | As an administrator, I want to inspect audit and failed-login records so that security events can be investigated. |
| US-13 | As an administrator, I want to export filtered audit logs so that I can review activity outside the application. |
| US-14 | As an administrator, I want role changes restricted for administrator accounts so that admin privileges cannot be altered by another admin. |

*Table 4: User stories*

---

## Part B. Software Requirements (SRS)

### B1. Introduction

This part records the behaviour of the implemented CampusFix release. It is intended for the course instructor, project evaluator, developers and anyone maintaining the application.

| Term | Definition |
|---|---|
| JWT | JSON Web Token, a signed token carrying claims |
| Access token | Short-lived bearer token sent in the `Authorization` header |
| Refresh token | Longer-lived opaque token used to obtain a new access token |
| RBAC | Role-Based Access Control; access is restricted according to a user's role |
| Role | Account classification: STUDENT, STAFF or ADMIN |
| Permission | A specific allowed operation, including the group create/edit/assign flags |
| Audit log | Persistent record of an event, its actor, target, metadata and timestamp |
| Argon2 | Password-hashing algorithm used through pwdlib |
| Pepper | Server-side secret combined with a password before hashing |

**References:** RFC 7519 (JSON Web Token); FastAPI documentation; SQLModel documentation; PyJWT documentation; OWASP guidance on password storage, authentication and session management.

### B2. Functional Requirements

**Authentication (FR-AUTH)**

| ID | Requirement |
|---|---|
| FR-AUTH-01 | The system shall allow a visitor to register a student account with validated account details. |
| FR-AUTH-02 | The system shall authenticate a user using normalized email and password credentials. |
| FR-AUTH-03 | The system shall store password hashes rather than plaintext passwords. |
| FR-AUTH-04 | The system shall use Argon2 password hashing and a server-side pepper for newly generated password hashes. |
| FR-AUTH-05 | The system shall issue an HS256-signed access JWT containing `sub`, `role`, `token_version`, `type`, `iat` and `exp` claims. |
| FR-AUTH-06 | The system shall limit access-token lifetime to a configured value between 1 and 15 minutes. |
| FR-AUTH-07 | The system shall issue refresh tokens whose hashes, not raw values, are stored in the database. |
| FR-AUTH-08 | The system shall rotate refresh tokens and reject revoked, expired or reused refresh tokens. |
| FR-AUTH-09 | The system shall set the refresh token in an HttpOnly cookie scoped to `/api/auth`. |
| FR-AUTH-10 | The system shall invalidate the refresh session on logout and clear the refresh cookie. |
| FR-AUTH-11 | The system shall reject invalid or expired access tokens with HTTP 401. |
| FR-AUTH-12 | The system shall reject banned or inactive accounts on protected requests. |
| FR-AUTH-13 | The system shall record failed login attempts and apply account/IP-based rate limits. |
| FR-AUTH-14 | The system shall allow authenticated users to update profile information and change passwords subject to validation. |
| FR-AUTH-15 | The system shall provide session information and session revocation controls where exposed by the user/admin interface. |

*Table 5: Authentication functional requirements*

**Role-Based Access Control (FR-RBAC)**

| ID | Requirement |
|---|---|
| FR-RBAC-01 | The system shall support STUDENT, STAFF and ADMIN roles. |
| FR-RBAC-02 | The system shall authenticate protected requests using a bearer access token. |
| FR-RBAC-03 | The system shall verify the token signature, expiry, token type, subject and current account state. |
| FR-RBAC-04 | The system shall restrict private service-request access according to ownership and supported group membership. |
| FR-RBAC-05 | The system shall require group membership and the relevant permission flag for member create/edit/assign actions. |
| FR-RBAC-06 | The system shall reserve group membership and group-management operations for the group owner. |
| FR-RBAC-07 | The system shall prevent members without a required permission from performing that action. |
| FR-RBAC-08 | The system shall prevent an administrator from changing their own role. |
| FR-RBAC-09 | The system shall prevent an administrator from changing another administrator's role, returning HTTP 403. |
| FR-RBAC-10 | The system shall reject banned users on subsequent protected requests. |

*Table 6: Role-based access control functional requirements*

**Administration (FR-ADM)**

| ID | Requirement |
|---|---|
| FR-ADM-01 | The system shall provide an admin-only dashboard with account statistics and recent registrations. |
| FR-ADM-02 | The system shall provide a paginated user list with search, role filter and account-status filter. |
| FR-ADM-03 | The system shall provide an admin-only user detail view with account, group, session and recent activity information where available. |
| FR-ADM-04 | The system shall allow an administrator to ban a non-admin user with a reason. |
| FR-ADM-05 | The system shall allow an administrator to unban an eligible user. |
| FR-ADM-06 | The system shall support bulk ban and bulk unban operations with per-item results. |
| FR-ADM-07 | The system shall allow permitted role transitions between STUDENT and STAFF. |
| FR-ADM-08 | The system shall reject role changes targeting ADMIN accounts and reject self-role changes. |
| FR-ADM-09 | The system shall allow an administrator to revoke a user's refresh-session family. |
| FR-ADM-10 | The system shall provide a paginated admin group list and individual/bulk deletion operations. |
| FR-ADM-11 | The system shall reject permanent deletion of a group containing service requests. |
| FR-ADM-12 | The system shall provide filtered audit-log retrieval for action, email, actor, target and date range. |
| FR-ADM-13 | The system shall export audit-log records as CSV using the selected filters. |
| FR-ADM-14 | The system shall sanitize potentially dangerous CSV formula cells. |
| FR-ADM-15 | The system shall provide failed-login security information grouped by IP and account. |

*Table 7: Administration functional requirements*

**Domain (FR-DOMAIN)**

| ID | Requirement |
|---|---|
| FR-DOMAIN-01 | The system shall allow an authenticated user to create a service request. |
| FR-DOMAIN-02 | The system shall allow an authenticated user to retrieve requests according to access rules. |
| FR-DOMAIN-03 | The system shall allow an authorized user to retrieve a request by its identifier. |
| FR-DOMAIN-04 | The system shall allow an authorized user to update or delete a request according to ownership and group rules. |
| FR-DOMAIN-05 | The system shall allow authorized assignment and unassignment of staff to requests. |
| FR-DOMAIN-06 | The system shall allow users to search visible requests by title, description and request ID in the frontend. |
| FR-DOMAIN-07 | The system shall allow users to create and manage shared groups subject to ownership rules. |
| FR-DOMAIN-08 | The system shall allow group owners to add/remove members and update create/edit/assign permissions. |
| FR-DOMAIN-09 | The system shall allow eligible group requests to be viewed, created, updated, assigned and deleted according to group permissions. |
| FR-DOMAIN-10 | The system shall support group archive and unarchive operations by the owner. |

*Table 8: Service request and group functional requirements*

**Requirements not delivered in this release**

The following planned requirements are *not* claimed as implemented: category administration; student cancellation; resolution notes; a fully enforced request status-transition state machine; admin-wide service-request moderation; CSV exports for users and requests; and a complete set of overview metrics (for example records and groups created in the last seven days). They are deferred work, not passed acceptance criteria.

### B3. Non-Functional Requirements

| ID | Area | Requirement / implementation status |
|---|---|---|
| NFR-SEC-01 | Security | Secrets are read from environment variables; `.env` is not committed. |
| NFR-SEC-02 | Security | New password hashes use Argon2 with a separate server-side pepper. |
| NFR-SEC-03 | Security | Access tokens have a configurable lifetime of no more than 15 minutes. |
| NFR-SEC-04 | Security | Refresh tokens are stored hashed and delivered in an HttpOnly cookie. |
| NFR-SEC-05 | Security | Login failures are limited by account and IP over a 15-minute window. |
| NFR-PERF-01 | Performance | Admin user/group lists are paginated; page size is bounded to 100. |
| NFR-PERF-02 | Performance | Audit-log page size defaults to 50 and is bounded to 100. |
| NFR-USE-01 | Usability | The frontend provides search, filters and loading/error/empty states where implemented. Responsive behaviour was checked manually only. |
| NFR-REL-01 | Reliability | Persistent data relies on the configured relational database. |
| NFR-MAINT-01 | Maintainability | Backend functionality is separated into routers, services, repositories, models and tests. |
| NFR-TEST-01 | Testability | Backend tests use pytest. The frontend package exposes build/type-check scripts but no frontend test script. |

*Table 9: Non-functional requirements*

### B4. Roles and Permission Matrix

| Endpoint group / action | Visitor | STUDENT | STAFF | Group owner | ADMIN |
|---|---|---|---|---|---|
| Signup / login | Yes | Yes | Yes | Yes | Yes |
| Protected profile / session endpoints | No | Own | Own | Own | Own / admin functions |
| Personal service requests | No | Own / authorized | Assigned / authorized | If member permission allows | According to implemented request service rules |
| Group list / details | No | Member / owner | Member / owner | Own group | Admin group list |
| Group membership management | No | No | No | Own group | No implicit group-owner rights |
| Group create / edit / assign actions | No | Only with flag | Only with flag | Owner authority | No implicit member permission |
| Admin user management | No | No | No | No | Yes |
| Audit / security dashboard | No | No | No | No | Yes |
| Admin group deletion | No | No | No | No | Yes, subject to request-history guard |

*Table 10: Role-based endpoint access matrix*

| Permission | Member flag | Meaning |
|---|---|---|
| Create request | `can_create_requests` | Member may create a request within the group |
| Edit request | `can_edit_requests` | Member may edit a group request |
| Assign request | `can_assign_requests` | Member may assign staff to a group request |
| Manage members | Owner-only | Owner adds/removes members and changes their permission flags |
| Rename/update group | Owner-only | Owner updates group metadata |
| Archive/unarchive | Owner-only | Owner controls group archive state |
| Delete group | Owner-only | Owner may delete an eligible group; groups with requests are protected |

*Table 11: Group permission definitions*

| Rule | Expected behaviour |
|---|---|
| Admin changes own role | Rejected (self-role protection) |
| Admin changes another ADMIN's role | Rejected with HTTP 403 (PR #45) |
| Admin changes STUDENT to STAFF | Allowed if the request is otherwise valid |
| Admin changes STAFF to STUDENT | Allowed if the request is otherwise valid |
| Admin bans another ADMIN | Protected by admin service rules |
| Admin deletes a group containing requests | Rejected with HTTP 409 |
| Admin receives automatic group-owner rights | No; admin privileges do not grant owner permissions inside a group |

*Table 12: Administrator authorization rules*

### B5. Use Cases

![Diagram 1: Use case diagram](docs/images/diagram-1-use-case.png)

*Diagram 1: Use case diagram*

| ID | Use case | Actor | Pre-conditions | Post-conditions |
|---|---|---|---|---|
| UC-01 | Login and refresh | Registered user | Account exists, is active and not banned | User has a valid authenticated session |
| UC-02 | Create a service request | Student / authorized group member | Valid access token; group membership and create permission if group-scoped | Request is stored and visible to authorized users |
| UC-03 | Change group member permissions | Group owner | Owner is authenticated and owns the group | Updated permission flags are saved |
| UC-04 | Denied group action | Group member | Member belongs to a group but lacks the required permission | Unauthorized operation is rejected; no change occurs |
| UC-05 | Ban a user | Administrator | Administrator is authenticated; target is an eligible non-admin | Target is banned and an audit event is recorded |
| UC-06 | Read and export audit logs | Administrator | Administrator is authenticated | Filtered records are displayed or exported as CSV |

*Table 13: Use case descriptions*

**UC-01: Login and refresh**

- **Actor:** Registered user.
- **Preconditions:** Account exists, is active and is not banned.
- **Main flow:**
  1. User submits email and password.
  2. API checks login limits.
  3. API verifies the password hash and account status.
  4. API returns an access token and sets an HttpOnly refresh cookie.
  5. When the access token expires, the frontend calls refresh.
  6. Backend validates and rotates the refresh token and returns a new access token.
- **Alternative/error flows:** invalid credentials return 401; rate limit returns 429; invalid, expired or reused refresh token returns 401 and the cookie is cleared.
- **Postcondition:** User has a valid authenticated session.

**UC-02: Create a service request**

- **Actor:** Authenticated student or group member with create permission.
- **Preconditions:** Valid access token; if group-scoped, membership and create permission exist.
- **Main flow:**
  1. User opens the request form.
  2. User enters request information.
  3. Frontend sends a POST request.
  4. Backend authenticates and checks ownership/group permission.
  5. Backend persists the request and returns it.
- **Alternative/error flows:** missing/invalid token returns 401; missing group permission returns 403; invalid input returns a validation error (422).
- **Postcondition:** Request is stored and visible to authorized users.

**UC-03: Change a group member's permissions**

- **Actor:** Group owner.
- **Preconditions:** Owner is authenticated and owns the target group.
- **Main flow:**
  1. Owner opens the group members list.
  2. Owner selects a member.
  3. Owner changes the create/edit/assign flags.
  4. Backend checks ownership.
  5. Backend stores the updated flags.
- **Alternative/error flows:** non-owner attempt is denied; invalid member/group identifiers return an error (404/422).
- **Postcondition:** The member can perform only the actions allowed by the updated flags.

**UC-04: Denied group action**

- **Actor:** Group member without the required permission.
- **Preconditions:** Member belongs to a group but the relevant flag is false.
- **Main flow:**
  1. Member attempts a protected operation.
  2. Backend resolves user and group membership.
  3. Backend checks the required permission.
  4. Backend rejects the operation.
- **Alternative/error flows:** missing token returns 401; insufficient permission returns 403.
- **Postcondition:** No unauthorized data change occurs.

**UC-05: Ban a user**

- **Actor:** Administrator.
- **Preconditions:** Administrator is authenticated; target is an eligible non-admin account.
- **Main flow:**
  1. Admin opens user management.
  2. Admin selects a user and provides a reason.
  3. API validates admin access and target rules.
  4. Account is marked banned.
  5. An audit event is recorded.
  6. Subsequent protected requests from the account are rejected.
- **Alternative/error flows:** non-admin receives 403; invalid target or protected admin target is rejected.
- **Postcondition:** Target account cannot continue using protected functionality.

**UC-06: Read and export audit logs**

- **Actor:** Administrator.
- **Preconditions:** Administrator is authenticated.
- **Main flow:**
  1. Admin opens audit logs.
  2. Admin applies action/email/actor/target/date filters.
  3. API validates the date range and returns paginated results.
  4. Admin selects CSV export.
  5. API exports matching records and records an export event.
- **Alternative/error flows:** invalid date range returns 400; non-admin receives 403.
- **Postcondition:** Filtered activity is visible and downloadable as CSV.

### B6. Acceptance Criteria

| ID | Given | When | Then |
|---|---|---|---|
| AC-01 | No access token is supplied | A protected endpoint is called | API returns 401 |
| AC-02 | Access token is expired or invalid | A protected endpoint is called | API returns 401 |
| AC-03 | A user is banned | The user calls a protected endpoint | API rejects the request with 403 |
| AC-04 | A group member lacks `can_create_requests` | Member attempts group request creation | API returns 403 and no request is created |
| AC-05 | A non-owner attempts to manage group members | The member-management endpoint is called | API rejects the action |
| AC-06 | Admin attempts to change own role | Role-change endpoint is called | API rejects the change |
| AC-07 | Admin targets another ADMIN's role | Role-change endpoint is called | API returns 403 and target role remains ADMIN |
| AC-08 | Admin changes STUDENT to STAFF | A valid role-change request is submitted | Role is updated |
| AC-09 | Group contains one or more service requests | Admin/owner attempts permanent deletion | API rejects deletion with a conflict response |
| AC-10 | Audit filters contain a valid date range | Admin requests audit data/export | Only matching records are returned/exported |
| AC-11 | CSV data begins with spreadsheet formula characters | Audit CSV is generated | Dangerous cells are prefixed/sanitized |
| AC-12 | Login failures exceed the configured threshold | Another login is attempted within the window | API returns 429 |

*Table 14: Acceptance criteria*

### B7. Traceability Matrix

| Requirement IDs | Endpoint / screen | Test / verification |
|---|---|---|
| FR-AUTH-01 to 04 | `/api/auth/signup`, `/api/auth/login` | Auth signup/login/password tests |
| FR-AUTH-05 to 11 | `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout` | JWT and refresh-session tests; token inspection with secrets masked |
| FR-AUTH-12 to 13 | Protected API; admin security view | Banned-user and login-rate-limit tests |
| FR-AUTH-14 to 15 | Profile/session UI and auth endpoints | Profile/password/session tests |
| FR-RBAC-01 to 04 | Request API and role dependencies | Ownership/RBAC tests |
| FR-RBAC-05 to 07 | `/api/groups/...` | Group permission tests |
| FR-RBAC-08 to 10 | Admin user role/ban endpoints | Self-role, admin-target-role and banned-user regression tests |
| FR-ADM-01 to 03 | Admin overview/users/user-detail screens | Admin dashboard/user tests | FR-ADM-04 to 09 | Admin user actions / session endpoint | Ban, bulk, role and session tests |
| FR-ADM-10 to 11 | `/api/admin/groups` and delete endpoints | Group deletion and request-protection tests |
| FR-ADM-12 to 14 | `/api/admin/audit-logs` and `/export` | Audit filter/export/sanitization tests |
| FR-ADM-15 | Admin security view | Failed-login aggregation tests |
| FR-DOMAIN-01 to 10 | `/api/requests` and `/api/groups` | Request and group tests; manual live workflow |

*Table 15: Requirements traceability matrix*

---

## Part C. Technical Design (TDD)

### C1. Technology Stack

| Component | Technology / version | Purpose |
|---|---|---|
| Frontend framework | React ^19.3.0 | Component-based user interface |
| Language | TypeScript ^7.0.2 | Typed frontend code |
| Build/dev server | Vite ^8.3.2 | Development server and production build |
| Routing | react-router ^8.5.1 | Client-side navigation |
| Backend | FastAPI [standard] >=0.141.1 | REST API |
| ORM/model layer | SQLModel >=0.0.22 | Database models and queries |
| Database driver | psycopg[binary] >=3.2 | PostgreSQL connectivity |
| Migrations | Alembic >=1.16 | Schema migration tooling |
| JWT | PyJWT >=2.10 | Signed access tokens |
| Password hashing | pwdlib[argon2] >=0.2 | Argon2 hashing |
| Configuration | python-dotenv >=1.0.0 | Local environment configuration |
| Testing | pytest (development environment) | Backend automated tests |
| Hosting | Vercel | Frontend and API deployment |
| Database hosting | PostgreSQL-compatible hosted database (URL supplied via environment) | Persistent relational storage |

*Table 16: CampusFix technology stack*

### C2. System Architecture

![Diagram 2: Detailed system architecture](docs/images/diagram-2-architecture.png)

*Diagram 2: Detailed system architecture*

The browser loads the React application from Vercel. The frontend sends same-origin `/api/...` requests, which Vercel rewrites to the FastAPI backend. Protected API requests include a Bearer access token in the `Authorization` header. Refresh requests also carry the HttpOnly refresh cookie, which JavaScript cannot read. The backend validates access tokens and refresh sessions, performs the required database operations, and records security-relevant events in the audit-log and login-attempt tables.

### C3. Backend and Frontend Structure

CampusFix is organized into feature-based modules so that each responsibility (authentication, administration, groups, service requests, audit logging) lives in its own place.

**Backend folder tree**

```text
backend/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ main.py
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ database.py
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ requirements.txt
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ alembic.ini
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ app/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ schemas.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ admin/            router.py, service.py, repository.py, schemas.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ audit/            router.py, service.py, repository.py, schemas.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ auth/             router.py, service.py, repository.py, permissions.py,
Ã¢â€â€š   Ã¢â€â€š                     dependencies.py, jwt.py, tokens.py, password.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ groups/           router.py, service.py, repository.py, schemas.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ models/           user.py, service_request.py, group.py,
Ã¢â€â€š   Ã¢â€â€š                     audit_log.py, login_attempt.py, refresh_session.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ service_requests/ router.py, service.py, repository.py
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ staff/            router.py
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ migrations/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ scripts/
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ tests/
```

**Frontend folder tree**

```text
frontend/
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ src/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ App.tsx
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ main.tsx
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ components/   CreateRequestForm, DashboardStats, GroupRequestsSection,
    Ã¢â€â€š                 Header, RequestList, SecurityDashboard
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ contexts/     AuthContext.tsx
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ pages/        AdminPage, GroupDetailsPage, GroupsPage, HomePage,
    Ã¢â€â€š                 LoginPage, ProfilePage, RequestDetailsPage, SignupPage, ...
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ services/     admin.ts, api.ts, auth.ts, groups.ts
    Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ types/        group.ts, request.ts
```

**Where things live (backend)**

- **Entry point and database:** `main.py` creates the FastAPI app and registers the routers; `database.py` holds the connection configuration.
- **Routes:** each feature has a `router.py` (for example `app/auth/router.py`, `app/admin/router.py`, `app/groups/router.py`, `app/service_requests/router.py`).
- **Services:** `service.py` files contain business logic and keep route handlers thin.
- **Repositories:** `repository.py` files contain database access.
- **Models:** `app/models/` has one file per entity.
- **Authentication:** `app/auth/` contains `jwt.py` (token handling), `password.py` (hashing), `tokens.py` (refresh tokens) and `dependencies.py` (auth dependencies).
- **RBAC module:** `app/auth/permissions.py`, supported by the dependencies.
- **Admin and audit code:** `app/admin/` and `app/audit/`.
- **Migrations, scripts, tests:** `migrations/` (Alembic), `scripts/` (admin/staff account creation) and `tests/` (pytest suites for authentication, authorization, admin, groups, requests and audit).

**Where things live (frontend)**

- **Entry and routing:** `main.tsx` starts the app; `App.tsx` defines the routes.
- **Pages:** `src/pages/` holds the screens (home, login, signup, profile, admin, groups, group details, request details).
- **Components:** `src/components/` holds reusable UI pieces.
- **Authentication context:** `contexts/AuthContext.tsx` shares authentication state across the app.
- **API client:** `services/api.ts` is the central client; `auth.ts`, `admin.ts` and `groups.ts` wrap the endpoint groups.
- **Types:** `src/types/` holds the TypeScript definitions.

### C4. Data Model

![Diagram 3: Entity relationship diagram](docs/images/diagram-3-erd.png)

*Diagram 3: Entity relationship diagram (ERD)*

| Table | Important fields | Purpose |
|---|---|---|
| `users` | UUID `id`, unique `email`, `name`, `password_hash`, `role`, `token_version`, active/banned flags, ban reason/timestamps, created/updated timestamps | Account identity, role and ban state |
| `service_requests` | integer `id`, `user_id`, `assigned_to`, `group_id`, `title`, `description`, `category`, `status`, timestamps | Campus service request records |
| `groups` | UUID `id`, `name`, `description`, `owner_id`, `is_archived`, timestamps | Shared workspace and authoritative owner |
| `group_members` | UUID `id`, `group_id`, `user_id`, `can_create_requests`, `can_edit_requests`, `can_assign_requests`, timestamps | Membership and per-member permission flags |
| `refresh_sessions` | UUID `id`, `user_id`, `family_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at` | Hashed refresh-token / session-family state |
| `audit_logs` | UUID `id`, `actor_id`, `target_user_id`, `action`, `email`, IP, user-agent, `details`, `created_at` | Security and administrative event history |
| `login_attempts` | UUID `id`, `email`, IP, `successful`, `attempted_at` | Rate limiting and security aggregation |

*Table 17: CampusFix core database entities*

**Relationships**

1. One user can create many service requests; a request can optionally be assigned to a staff user.
2. One user can own many groups through `owner_id`.
3. One group can have many group-member records.
4. Each group-member record links one user to one group; `(group_id, user_id)` is unique.
5. A request may be personal or belong to a group through the optional `group_id`.
6. One user can have many refresh sessions.
7. Audit-log records can reference an actor and a target user; both are optional, so events without an identified user can still be stored.
8. Login attempts are stored independently and indexed by email, IP address, success status and attempt time to support security monitoring and rate-limit queries.

**How the key concepts are stored:** roles and bans are columns on `users`; sessions use `refresh_sessions` (only a token hash is stored, grouped by `family_id`); group permissions are Boolean flags on `group_members`; the activity log is the `audit_logs` table.

### C5. API Design

All endpoints use the `/api` prefix and exchange JSON. Protected endpoints require authentication, admin endpoints require the ADMIN role, and group endpoints also enforce ownership and membership permissions. There is no numbered version prefix such as `/api/v1`; `/api` is the common base path.

| Method | Path | Authentication | Role / permission | Request body | Success | Errors |
|---|---|---|---|---|---|---|
| POST | `/api/auth/signup` | Public | None | name, email, password | 201 | 400, 422 |
| POST | `/api/auth/login` | Public | None; rate-limited | email, password | 200 | 401, 422, 429 |
| POST | `/api/auth/refresh` | Refresh cookie | Valid refresh session | None | 200 | 401 |
| POST | `/api/auth/logout` | Optional user/session context | None | None | 200 | n/a |
| GET | `/api/auth/me` | Required | Authenticated user | None | 200 | 401 |
| PATCH | `/api/auth/me` | Required | Own profile | profile fields | 200 | 400, 401, 422 |
| POST | `/api/auth/change-password` | Required | Own account | current_password, new_password | 200 | 400, 401 |
| GET | `/api/auth/sessions` | Required | Own sessions | None | 200 | 401 |
| DELETE | `/api/auth/sessions/{session_id}` | Required | Own session | None | 200 | 401, 404, 422 |
| POST | `/api/requests` | Required | STUDENT or ADMIN | title, description, category | 201 | 401, 403, 422 |
| GET | `/api/requests` | Required | Authenticated; accessible requests | None | 200 | 401 |
| GET | `/api/requests/{request_id}` | Required | Request access permission | None | 200 | 401, 404, 422 |
| PUT | `/api/requests/{request_id}` | Required | Owner or authorized user | title, description, category, status | 200 | 400, 401, 403, 404, 422 |
| DELETE | `/api/requests/{request_id}` | Required | Owner or authorized user | None | 200 | 401, 403, 404, 422 |
| PATCH | `/api/requests/{request_id}/assign` | Required | ADMIN or applicable assignment permission | staff_id | 200 | 400, 401, 403, 404, 422 |
| DELETE | `/api/requests/{request_id}/assign` | Required | ADMIN or applicable assignment permission | None | 200 | 400, 401, 403, 404, 422 |
| GET | `/api/staff` | Required | ADMIN | None | 200 | 401, 403 |
| POST | `/api/groups` | Required | Authenticated user | name | 201 | 401, 422 |
| GET | `/api/groups` | Required | Authenticated; accessible groups | None | 200 | 401, 422 |
| GET | `/api/groups/{group_id}` | Required | Group member or owner | None | 200 | 401, 404, 422 |
| PATCH | `/api/groups/{group_id}` | Required | Group owner | group fields | 200 | 401, 404, 422 |
| DELETE | `/api/groups/{group_id}` | Required | Group owner; deletion rules apply | None | 200 | 400, 401, 404 |
| POST | `/api/groups/{group_id}/archive` | Required | Group owner | None | 200 | 400, 401, 404 |
| POST | `/api/groups/{group_id}/unarchive` | Required | Group owner | None | 200 | 400, 401, 404 |
| GET | `/api/groups/{group_id}/members` | Required | Group member or owner | None | 200 | 401, 404, 422 |
| POST | `/api/groups/{group_id}/members` | Required | Group owner | email | 201 | 400, 401, 404, 422 |
| PATCH | `/api/groups/{group_id}/members/{user_id}` | Required | Group owner | permission fields | 200 | 400, 401, 404, 422 |
| DELETE | `/api/groups/{group_id}/members/{user_id}` | Required | Group owner | None | 200 | 400, 401, 404 |
| GET | `/api/groups/{group_id}/requests` | Required | Group member or owner | None | 200 | 401, 404 |
| POST | `/api/groups/{group_id}/requests` | Required | Owner or `can_create_requests` | title, description, category | 201 | 400, 401, 403, 404, 422 |
| GET | `/api/groups/{group_id}/requests/{request_id}` | Required | Group/request access | None | 200 | 401, 404, 422 |
| PUT | `/api/groups/{group_id}/requests/{request_id}` | Required | Owner or `can_edit_requests` | title, description, category | 200 | 400, 401, 403, 404, 422 |
| DELETE | `/api/groups/{group_id}/requests/{request_id}` | Required | Ownership/permission check | None | 200 | 401, 403, 404 |
| PATCH | `/api/groups/{group_id}/requests/{request_id}/assign` | Required | Owner or `can_assign_requests` | staff_id | 200 | 400, 401, 403, 404, 422 |
| DELETE | `/api/groups/{group_id}/requests/{request_id}/assign` | Required | Owner or `can_assign_requests` | None | 200 | 400, 401, 403, 404 |
| GET | `/api/admin/users` | Required | ADMIN | None | 200 | 401, 403, 422 |
| GET | `/api/admin/users/{user_id}` | Required | ADMIN | None | 200 | 401, 403, 404, 422 |
| POST | `/api/admin/users/{user_id}/ban` | Required | ADMIN | reason | 200 | 400, 401, 403, 404, 409 |
| POST | `/api/admin/users/{user_id}/unban` | Required | ADMIN | None | 200 | 400, 401, 403, 404 |
| PATCH | `/api/admin/users/{user_id}/role` | Required | ADMIN | role | 200 | 400, 401, 403, 404, 409 |
| POST | `/api/admin/users/bulk-ban` | Required | ADMIN | user_ids, reason | 200 | 400, 401, 403, 422 |
| POST | `/api/admin/users/bulk-unban` | Required | ADMIN | user_ids | 200 | 400, 401, 403, 422 |
| DELETE | `/api/admin/users/{user_id}/sessions/{family_id}` | Required | ADMIN | None | 200 | 401, 403, 404 |
| GET | `/api/admin/groups` | Required | ADMIN | None | 200 | 401, 403, 422 |
| DELETE | `/api/admin/groups/{group_id}` | Required | ADMIN; deletion eligibility rules | None | 200 | 400, 401, 403, 404, 409 |
| POST | `/api/admin/groups/bulk-delete` | Required | ADMIN; deletion eligibility rules | group_ids | 200 | 400, 401, 403, 422 |
| GET | `/api/admin/dashboard/stats` | Required | ADMIN | None | 200 | 401, 403 |
| GET | `/api/admin/dashboard/recent-users` | Required | ADMIN | None | 200 | 401, 403, 422 |
| GET | `/api/admin/security/failed-logins` | Required | ADMIN | None | 200 | 401, 403, 422 |
| GET | `/api/admin/audit-logs` | Required | ADMIN | None | 200 | 401, 403, 422 |
| GET | `/api/admin/audit-logs/export` | Required | ADMIN | None | 200 | 401, 403, 422 |
| GET | `/api/health` | Public | None | None | 200 | n/a |

*Table 18: CampusFix REST API endpoint reference*

**Error handling and response format**

| Status | Meaning |
|---|---|
| 200 OK | Request processed successfully |
| 201 Created | A new resource was created |
| 400 Bad Request | Input or requested operation violates a business rule |
| 401 Unauthorized | Authentication is missing or invalid |
| 403 Forbidden | Authenticated user lacks sufficient permission |
| 404 Not Found | Resource does not exist or is intentionally hidden |
| 409 Conflict | Operation conflicts with an existing resource or constraint |
| 422 Unprocessable Entity | Request failed input validation |
| 429 Too Many Requests | Rate limit exceeded |
| 500 Internal Server Error | Unexpected server-side error |

Application errors return a JSON object with a descriptive `detail` message; FastAPI validation errors return structured JSON in the same `detail` field.

```json
{
  "detail": "Not enough permissions to perform this action"
}
```

### C6. JWT Authentication Design

![Diagram 4: JWT authentication and refresh sequence](docs/images/diagram-4-jwt-sequence.png)

*Diagram 4: CampusFix JWT authentication and refresh sequence diagram*

**Token claims**

| Claim | Meaning |
|---|---|
| `sub` | User UUID |
| `role` | Role at token creation |
| `token_version` | Account token-version value checked against the database |
| `type` | Must be `access` |
| `iat` | Issued-at timestamp |
| `exp` | Expiration timestamp |

*Table 19: JWT access token claims*

**Signing and secrets.** Access tokens are HS256-signed with `JWT_SECRET_KEY`, which comes from an environment variable.

**Lifetimes.** The access token defaults to 15 minutes (configurable between 1 and 15), which limits the exposure window if one is stolen. The refresh token defaults to seven days so users do not have to re-enter credentials constantly.

**Password handling.** New passwords are preprocessed with HMAC-SHA256 using `PASSWORD_PEPPER` and then hashed with Argon2. The pepper is stored separately from the database and is never committed.

**Refresh tokens.** The refresh token is a random opaque value. Only its hash is stored in `refresh_sessions`; the raw value is delivered in an HttpOnly cookie. On refresh, the current token is validated and rotated. Reuse of a revoked or previously used refresh token is rejected and revokes the whole session family. Logout revokes the session family, increments the user's `token_version` and clears the cookie.

**Browser storage and its risks.** The frontend keeps the access token in application memory, not in `localStorage` or `sessionStorage`, to avoid persistent token theft. The refresh token lives in an HttpOnly cookie that JavaScript cannot read, with the `Secure` flag in production and `SameSite=Lax` to reduce CSRF risk. HttpOnly does not fully stop the effects of XSS, because malicious scripts can still make requests through the browser, so careful input and output handling remains important.

**Checks on every protected request.** The backend verifies the JWT signature and expiry, validates token type and subject, loads the user, checks `token_version`, and rejects banned or inactive accounts.

**Frontend behaviour on 401.** The frontend refreshes the access token with the refresh cookie and retries the original request once. If refresh fails or the retry also returns 401, it clears the authentication state and returns the user to the unauthenticated state. A 403 does not trigger a refresh.

### C7. RBAC Design

![Diagram 5: Request authorization flow](docs/images/diagram-5-authorization-flow.png)

*Diagram 5: CampusFix request authorization flow*

Authorization is done on the backend, in this order: token validation, user validation, role check, ownership/assignment check, group permission check, and finally the handler.

**Roles and permission constants** (defined in `backend/app/auth/permissions.py`)

| Role | Description |
|---|---|
| STUDENT | Submits and manages personal requests; participates in shared groups |
| STAFF | Accesses and updates requests assigned to them |
| ADMIN | Uses administrative functionality and permitted system-wide management operations |

`ALL_ROLES` holds the set of supported roles. Group permissions are Boolean fields on the membership record:

| Permission | Purpose |
|---|---|
| `can_create_requests` | Create service requests in the group |
| `can_edit_requests` | Edit eligible pending group requests |
| `can_assign_requests` | Assign or unassign staff for group requests |

The group owner automatically has all three permissions; other members have only what the owner granted.

**Authorization order**

1. **Token validation:** the Bearer token's signature, expiry, type and claims are verified. Failure returns 401.
2. **User validation:** the user from `sub` must exist, `token_version` must match the database, and banned/inactive accounts are rejected.
3. **Role check:** where an endpoint needs a role, `require_user_role()` verifies it. A mismatch returns 403.
4. **Ownership/assignment check:** students reach their own requests; staff reach requests assigned to them; administrators can reach personal requests without the ownership restriction.
5. **Group permission check:** the user must be the group owner or a member, and must hold the needed flag.
6. **Handler execution:** the operation runs only after all applicable checks pass.

**Ownership enforced in queries.** Ownership is part of the database query, not only a check afterwards. When listing personal requests, the repository filters student requests by the authenticated user's ID and excludes group requests; staff queries filter by `assigned_to`. When fetching a request by ID, the repository combines the ID with ownership, group-membership or staff-assignment conditions in the SQL query. Group request queries filter by both group ID and request ID so a request must belong to the requested group.

**Reusable permission check** (`backend/app/auth/permissions.py`)

```python
def require_user_role(
    current_user: User,
    *allowed_roles: str,
) -> User:
    if not allowed_roles:
        raise ValueError("At least one allowed role must be provided.")

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )

    return current_user
```

*Code Listing 1: Reusable role-based permission check*

**Special rules for administrators and banned users.** Admin endpoints use the `get_current_admin()` dependency, which first requires a valid authenticated user and then checks for the ADMIN role. Administrators have broader access to personal requests and admin functions, but group ownership and membership rules still apply to group operations unless a specific admin endpoint provides separate authority. Banned and inactive users are rejected in the authentication dependency before any role or resource checks, even if their token was previously valid.

**Adding a new role or permission.** To add a role, add the constant to `permissions.py`, include it in `ALL_ROLES`, update endpoint dependencies and service-layer checks to allow it only where intended, and add tests for permitted and denied access. To add a group permission, add a Boolean field to the membership model and a database migration, include it in the request schemas and group-management logic, and check it through the existing group permission mechanism.

### C8. Admin Dashboard Design

The admin dashboard gives ADMIN users one place to monitor activity and manage users, groups, security events and audit records. It has five areas: Overview, User Management, Group Management, Audit Logs and Security Monitoring.

![Diagram 6: Admin dashboard pages and API endpoints](docs/images/diagram-6-admin-endpoints.png)

*Diagram 6: CampusFix admin dashboard pages and API endpoints*

| Page | Endpoint | Filters / data | Action | Audit event |
|---|---|---|---|---|
| Overview | `GET /api/admin/dashboard/stats` | User statistics, role distribution, account status | View statistics | Read-only |
| Overview | `GET /api/admin/dashboard/recent-users` | Recent registrations | View recent users | Read-only |
| User Management | `GET /api/admin/users` | Search by name/email, role, account status | View and filter users | Read-only |
| User Details | `GET /api/admin/users/{user_id}` | Individual user information | View details | Read-only |
| User Management | `POST /api/admin/users/{user_id}/ban` | Selected user | Ban user | `USER_BANNED` |
| User Management | `POST /api/admin/users/{user_id}/unban` | Selected user | Unban user | `USER_UNBANNED` |
| User Management | `PATCH /api/admin/users/{user_id}/role` | Selected user, new role | Change role | `USER_ROLE_CHANGED` |
| User Management | `POST /api/admin/users/bulk-ban` | Selected eligible users | Ban multiple users | `USER_BANNED` per success |
| User Management | `POST /api/admin/users/bulk-unban` | Selected eligible users | Unban multiple users | `USER_UNBANNED` per success |
| User Management | `DELETE /api/admin/users/{user_id}/sessions/{family_id}` | Selected session family | Revoke session | `USER_SESSION_REVOKED` |
| Group Management | `GET /api/admin/groups` | Group records, pagination | View groups | Read-only |
| Group Management | `DELETE /api/admin/groups/{group_id}` | Selected group | Delete group | `GROUP_DELETED` |
| Group Management | `POST /api/admin/groups/bulk-delete` | Selected groups | Delete multiple groups | `GROUP_DELETED` per success |
| Audit Logs | `GET /api/admin/audit-logs` | Action, email, actor, target user, date range | Search and review | Read-only |
| Audit Logs | `GET /api/admin/audit-logs/export` | Current audit filters | Export CSV | `AUDIT_LOG_EXPORTED` |
| Security Monitoring | `GET /api/admin/security/failed-logins` | Date range, account and IP failure data | Review failed logins | Read-only |

*Table 20: Admin dashboard pages, endpoints, filters, actions and audit events*

**Filtering and pagination.** User Management searches by name or email and filters by role and account status. Group Management uses paginated results. Audit Logs filter by action, email, actor, target user and date range. Security Monitoring shows failed logins in a selected date range of at most 90 days. The frontend shows 20 records per page for user, group and audit lists, and up to 50 for failed logins; the backend bounds page sizes.

**Bulk operations.** Bulk ban, bulk unban and bulk group deletion process each item independently, so one failure does not block the others. The backend returns the number of submitted items, the number that succeeded, the number that failed and a result for each item; the frontend shows a success/failure summary. Ineligible users (administrators, already-banned users) are filtered out in the UI before submission where applicable. The API reports failures but has no separate "skipped" counter. Group deletion fails for a group that contains service requests.

**Audit logging and CSV export.** Successful admin operations write an audit event (ban, unban, role change, session revocation, group deletion, audit export). The CSV export uses the current audit filters and drops the pagination parameters so the file is not limited to the visible page. The backend caps the export at 10,000 records and sanitizes formula-like CSV values.

**Security.** Every admin endpoint requires the ADMIN role, checked by a reusable dependency after authentication and account-status checks. Insufficient privileges return 403. Hiding admin pages in the frontend is not treated as security; the backend validates every request independently.

### C9. Security Design and Threats

| Threat | Defence in implementation | Location / remaining concern |
|---|---|---|
| Password database leak | Argon2 hash; HMAC-SHA256 pepper preprocessing for new hashes | `app/auth/password.py`; the pepper must be protected separately |
| Stolen access token | Short expiry (max 15 min), signature validation, account/token-version checks | `app/auth/jwt.py`, `dependencies.py` |
| Stolen refresh token | HttpOnly cookie, hashed DB token, rotation, revocation and reuse detection | `app/auth/tokens.py`, `service.py`, `refresh_sessions` |
| Brute-force login | Account/IP attempt counters with 15-minute thresholds | `app/auth/service.py`; cleanup/retention not verified |
| Privilege escalation | Role dependency, ownership/group checks, admin-target role restrictions | `dependencies.py`, `permissions.py`, service modules |
| Cross-user record access | Request service access checks and group membership permissions | `service_requests/`, `groups/`; all routes should be covered by negative tests |
| XSS | Access token kept in memory rather than `localStorage`; frontend output handling | Frontend; no Content-Security-Policy verification was recorded |
| CSRF | `SameSite` refresh cookie scoped to `/api/auth`; bearer token for protected requests | Production cookie flags and origin protections should be re-verified |
| CORS misuse | Same-origin Vercel rewrite | An explicit CORS allowlist was not verified |
| Secret leakage | Environment variables and `.env.example`; real `.env` excluded from the repository | Vercel values must stay hidden |
| SQL injection | SQLModel/SQLAlchemy parameterized queries | Avoid raw interpolated SQL |
| Over-posting | Pydantic request schemas define accepted fields | Review each schema when adding endpoints |
| CSV formula injection | Cells beginning with formula/control characters are prefixed | `app/audit/router.py` |

*Table 21: CampusFix security threats and mitigations*

### C10. Deployment on Vercel

CampusFix runs on Vercel as a frontend (React/TypeScript/Vite) and a backend API (FastAPI). The repository's `vercel.json` routes requests matching `/api/(.*)` to the backend, and all other requests to the frontend. The frontend uses `/api` as its base path, so API calls are same-origin. The backend connects to a hosted PostgreSQL database through `DATABASE_URL`. Credentials and secrets are set as Vercel environment variables, not in the source code.

**Production URL:** https://2310626.vercel.app

![Diagram 7: Deployment architecture](docs/images/diagram-7-deployment.png)

*Diagram 7: CampusFix deployment architecture*

| Component | Configuration |
|---|---|
| Frontend framework | React |
| Language | TypeScript |
| Frontend build tool | Vite |
| Backend framework | FastAPI |
| API base path | `/api` |
| API routing | `/api/(.*)` forwarded to the backend |
| Frontend routing | Non-API requests handled by the frontend |
| API documentation | `/api/docs` (OpenAPI spec at `/api/openapi.json`) |
| Health check | `/api/health` |

*Table 22: Deployment and API routing configuration*

**Environment variables** (names only; defined in `backend/.env.example`, values set in Vercel)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Connection string for the hosted PostgreSQL database |
| `JWT_SECRET_KEY` | Secret used to sign and verify JWT access tokens |
| `PASSWORD_PEPPER` | Secret value used during password hashing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-token lifetime in days |
| `COOKIE_SECURE` | Whether authentication cookies require HTTPS |
| `COOKIE_SAMESITE` | SameSite policy for authentication cookies |

*Table 23: Backend environment variables*

**How to redeploy**

1. Commit and push approved changes to the configured GitHub branch (`main`).
2. Vercel detects the commit and starts a deployment.
3. Watch the deployment logs for build or configuration errors.
4. Confirm the deployment completes.
5. Check that the frontend loads.
6. Check `/api/health`.
7. Test authentication, API communication and database connectivity.

If an environment variable changes, a new deployment is needed for it to take effect. A successful preview deployment does not mean production was updated, so check the production deployment status and commit separately.

### C11. Testing

**Strategy.** Testing combines backend pytest tests (authentication, authorization, admin operations, groups, service requests and audit), targeted regression tests for security fixes, a TypeScript type check and production build, and manual verification on the live site. The frontend has no unit-test script.

**How to run**

```powershell
# Backend tests (set test-only environment values first)
$env:DATABASE_URL = "sqlite://"
$env:JWT_SECRET_KEY = "test-only-secret-key-at-least-32-bytes"
$env:PASSWORD_PEPPER = "test-only-pepper-at-least-32-bytes"
Set-Location .\backend
..\.venv\Scripts\python.exe -m pytest -vv -p no:cacheprovider tests

# Frontend type check / build
Set-Location ..\frontend
npm run build
```

| Test / check | Requirement area | Result |
|---|---|---|
| Full backend pytest suite | All backend requirements | Passed |
| Frontend `npm run build` (type check and production build) | Frontend compilation | Succeeded |
| PR #45 focused admin-role regression suite | FR-ADM-07/08, FR-RBAC-08/09 | 39 tests and 12 subtests passed; `git diff --check` passed |
| PR #45 GitHub checks | Merge validation | 3 checks passed; merged as commit `4c8be12` |
| PR #43 backend suite | Authentication hardening | 164 tests and 41 subtests passed at that time |
| Live manual tests | Production workflows | Student login, request search by title/description/ID, admin dashboard loading, owner deletion of an empty group, member restriction, and protection of groups containing requests all confirmed |

*Table 24: CampusFix testing results*

---

## Part E. Project Management and Conclusion

### E1. How to Run and Test

**Prerequisites**

- Git
- A Python version compatible with the installed FastAPI dependencies
- Node.js and npm
- A PostgreSQL database or compatible database URL

**Clone and set up the backend**

```powershell
git clone https://github.com/Sahkib159/2310626-CampusFix.git
Set-Location .\2310626-CampusFix
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Set-Location .\backend
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` locally and set the variables below. Keep secrets out of Git, and keep `ACCESS_TOKEN_EXPIRE_MINUTES` between 1 and 15.

```text
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/campusfix
JWT_SECRET_KEY=<random value, at least 32 bytes>
PASSWORD_PEPPER=<a different random value, at least 32 bytes>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

Then run:

```powershell
alembic upgrade head
uvicorn main:app --reload
```

**Frontend** (second terminal, from the repository root)

```powershell
Set-Location .\2310626-CampusFix\frontend
npm install
npm run dev
```

**Tests**

```powershell
# Backend, from the repository root after environment setup
Set-Location .\backend
..\.venv\Scripts\python.exe -m pytest -vv -p no:cacheprovider tests

# Frontend
Set-Location ..\frontend
npm run build
```

**Logging in with test accounts.** Public registration creates STUDENT accounts. STAFF and ADMIN accounts are created with the backend account-creation scripts in `backend/scripts/`. Demo accounts exist for the roles ADMIN, STAFF and STUDENT; their user IDs and passwords are provided separately through the approved submission channel and are intentionally not written in this file or the repository.

### E2. GitHub Work

Repository: https://github.com/Sahkib159/2310626-CampusFix. All commits were made by me (individual project, no team). The work was done feature by feature, each with an issue and a pull request.

| Issue | PR | What it delivered |
|---|---|---|
| #2 | #3 | Initial PRD, SRS, TDD and README documentation |
| #4 | #5 | Service-request CRUD MVP |
| n/a | #6 | Backend import fixes for Vercel deployment |
| #7 | #8 | Production Swagger documentation routing |
| n/a | #9 | Production Swagger documentation URL fixes |
| #10 | #11 | Frontend restructuring and individual request details page |
| #12 | #13 | Authentication, JWT sessions and role-based request management |
| #14 | #15 | User profile management, password changes and frontend routing fixes |
| #16 | #17 | Service-request ownership and reusable RBAC authorization |
| #18 | #19 | Authentication security and account-status enforcement |
| #20 | #21 | Shared groups and fine-grained member permissions |
| #22 | #23 | Admin user management, dashboard and audit logging |
| #24 | #25 | Admin user details and account activity view |
| #26 | #27 | Automatic frontend access-token refresh |
| #28 | #29 | Bulk user ban and unban |
| #30 | #31 | Banned-user login and refresh-token rejection |
| #32 | #33 | Refresh-cookie hardening and access-token invalidation |
| #34 | #35 | Individual admin session revocation |
| #36 | #37 | Admin security dashboard and failed-login monitoring |
| #38 | #39 | Admin group management and group deletion controls |
| #40 | #41 | Owner-only group deletion and request-history protection |
| #42 | #43 | Authentication hardening and self-service session management |
| n/a | #44 | Service-request search by title, description and ID |
| n/a | #45 | Prevented administrators from changing another administrator's role |

*Table 25: CampusFix GitHub issues, pull requests and delivered features*

### E3. Limitations

- The original PRD/SRS/TDD and README in the repository describe older planned requirements and must not be treated as proof of implementation; this report reflects the delivered state.
- Category management is not implemented as a dedicated admin feature.
- Student cancellation and resolution notes are not implemented.
- A complete server-side request status-transition state machine was not verified, so invalid status jumps may be possible.
- Admin-wide service-request moderation is not implemented; only admin group management exists.
- CSV export exists for audit logs only, not for users or service requests.
- Dashboard statistics do not cover every metric in the original course brief.
- Admin group listing is paginated, but a group search/filter interface was not confirmed.
- The frontend has no automated test script or framework.
- The Alembic migration chain was flagged in an audit: the initial migration appears empty while a later migration alters `service_requests`. A clean-database migration has not been validated, so the documented migration process is not claimed to work from scratch.
- No explicit CORS allowlist or Content-Security-Policy was verified.
- Revoking a session family does not immediately invalidate an access token that was already issued; it expires within its short lifetime.

### E4. Future Work

In priority order:

1. **Repair and test the Alembic migration chain** against a fresh disposable database, so the project can be rebuilt from scratch.
2. **Enforce valid request status transitions** and require resolution notes for completed requests, to complete the request lifecycle.
3. **Implement student cancellation** for eligible pending requests.
4. **Add category persistence, validation and admin category management**, which the original brief requested.
5. **Add admin-wide service-request moderation** with safe individual and bulk operations.
6. **Add CSV exports for users and service requests** that respect filters.
7. **Expand dashboard metrics and group search/filter**, to meet the original brief.
8. **Add frontend and browser-level regression tests**, since only the backend is tested automatically.
9. **Improve session revocation semantics**, including access-token behaviour for revoked session families.
10. **Update the README, PRD, SRS and TDD** so they describe the final implementation.

### E5. Sources, Libraries and Tools

| Source / tool | Version / link | Use |
|---|---|---|
| React | ^19.3.0 | Frontend UI |
| TypeScript | ^7.0.2 | Frontend type safety |
| Vite | ^8.3.2 | Frontend build and dev server |
| react-router | ^8.5.1 | Frontend routing |
| FastAPI | >=0.141.1 | Backend REST API |
| SQLModel | >=0.0.22 | ORM and data models |
| psycopg[binary] | >=3.2 | PostgreSQL driver |
| Alembic | >=1.16 | Migration tooling |
| PyJWT | >=2.10 | JWT signing and validation |
| pwdlib[argon2] | >=0.2 | Password hashing |
| python-dotenv | >=1.0.0 | Local environment configuration |
| pytest | Project test environment | Backend automated tests |
| Git / GitHub | https://github.com/Sahkib159/2310626-CampusFix | Version control, issues, pull requests |
| Vercel | https://vercel.com | Hosting and preview/production deployments |
| OpenAPI / Swagger UI | `/api/docs` | API inspection and manual testing |
| ChatGPT | https://chatgpt.com/ | Planning, explaining concepts, reviewing report wording and organizing documentation. Technical claims were checked against the source code and actual test results. |
| GitHub Copilot | https://github.com/features/copilot | Code suggestions, debugging help and explanations of implementation details. I reviewed the suggestions, checked them against the existing project structure, modified them where needed and tested the resulting code before using it. |

*Table 26: Sources, libraries, frameworks and development tools*
