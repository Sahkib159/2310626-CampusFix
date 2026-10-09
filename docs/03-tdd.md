# Technical Design Document (TDD)

## CampusFix — Campus Service Request Management System

| Field            | Details                      |
| ---------------- | ---------------------------- |
| Document ID      | TDD-001                      |
| Version          | 1.0                          |
| Status           | Draft                        |
| Project          | CampusFix                    |
| Frontend         | React.js with TypeScript     |
| Backend          | FastAPI with Python          |
| API Style        | REST                         |
| Database         | Relational database          |
| Release Plan     | MVP (Mid-term), Beta (Final) |
| Related Document | [PRD](01-prd.md)             |
| Related Document | [SRS](02-srs.md)             |

## 1. Introduction

### 1.1 Purpose

This document describes the technical architecture, application structure, database design, API design, authentication, authorization, security, testing, and deployment approach for CampusFix.

It provides a practical implementation plan for the MVP and Beta releases.

### 1.2 Design Principles

* Keep the architecture simple and suitable for a semester project.
* Separate frontend, backend, and database responsibilities.
* Use REST APIs for communication between frontend and backend.
* Validate input and enforce business rules on the backend.
* Keep authentication and authorization logic separate from UI visibility.
* Implement only the features required for the agreed releases.
* Avoid unnecessary complexity such as microservices, AI/ML, and distributed infrastructure.

## 2. System Architecture

### 2.1 High-Level Architecture

The system will use a client-server architecture.

```text
+-----------------------------------+
|        React + TypeScript         |
|                                   |
|  Pages, Components, Forms, API    |
+----------------+------------------+
                 |
                 | HTTP / JSON
                 | REST API
                 v
+-----------------------------------+
|          FastAPI Backend          |
|                                   |
|  API Routes                       |
|       |                           |
|  Validation and Business Logic    |
|       |                           |
|  Authentication / Authorization   |
|          (Beta)                   |
|       |                           |
|  Data Access Layer                |
+----------------+------------------+
                 |
                 | Database Queries
                 v
+-----------------------------------+
|       Relational Database         |
|                                   |
|  Users, Categories, Requests      |
+-----------------------------------+
```

### 2.2 Component Responsibilities

| Component                | Responsibility                                            | Release  |
| ------------------------ | --------------------------------------------------------- | -------- |
| React frontend           | User interface, forms, request lists, validation feedback | MVP      |
| TypeScript               | Type-safe frontend development                            | MVP      |
| FastAPI                  | REST endpoints, request validation, business logic        | MVP      |
| Pydantic schemas         | Validate incoming data and structure API responses        | MVP      |
| Data access layer        | Database queries and persistence                          | MVP      |
| Relational database      | Store requests and categories; support users in Beta      | MVP/Beta |
| Authentication module    | Verify user identity                                      | Beta     |
| Authorization module     | Enforce roles, scopes, ownership, and assignment          | Beta     |
| Role-specific dashboards | Present appropriate functions to each user role           | Beta     |

### 2.3 Request Processing Flow

1. A user interacts with the React frontend.
2. The frontend sends an HTTP request to a FastAPI endpoint.
3. FastAPI validates the incoming data.
4. For protected Beta endpoints, the backend authenticates the user and checks permissions.
5. The business logic verifies resource ownership, assignment, and allowed status transitions.
6. The data access layer reads or updates the database.
7. FastAPI returns a JSON response with an appropriate HTTP status code.
8. The frontend updates the interface or displays an error.

## 3. Technology Stack

| Technology                                      | Purpose                                        | Release  |
| ----------------------------------------------- | ---------------------------------------------- | -------- |
| React.js                                        | Frontend user interface                        | MVP      |
| TypeScript                                      | Frontend language and type checking            | MVP      |
| FastAPI                                         | Python backend framework                       | MVP      |
| Pydantic                                        | Request and response validation                | MVP      |
| SQLAlchemy                                      | Database access and ORM                        | MVP      |
| Alembic                                         | Database schema migrations                     | MVP/Beta |
| SQLite                                          | Simple local development database, if suitable | MVP      |
| PostgreSQL                                      | Recommended deployment database, if available  | Beta     |
| JWT or another suitable token/session mechanism | Authentication                                 | Beta     |
| Pytest                                          | Backend testing                                | MVP/Beta |
| Git and GitHub                                  | Version control and collaboration              | MVP/Beta |

The initial implementation should use one database configuration at a time. SQLite is a reasonable starting point for local development; PostgreSQL can be adopted for deployment if required by the hosting environment.

Exact dependency versions shall be recorded in the project's dependency files.

## 4. Repository Structure

The proposed directory structure is:

```text
2310626-CampusFix/
├── docs/
│   ├── 01-prd.md
│   ├── 02-srs.md
│   └── 03-tdd.md
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── types/
│   │   ├── hooks/
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── db/
│   ├── tests/
│   ├── requirements.txt
│   └── alembic/
├── .gitignore
├── .env.example
└── README.md
```

This structure is a design proposal. Directories may be created as the corresponding features are implemented; empty directories do not need to be committed.

### 4.1 Directory Responsibilities

* `frontend/src/api/`: API client and HTTP request functions.
* `frontend/src/components/`: Reusable UI components.
* `frontend/src/pages/`: Main application pages and dashboards.
* `frontend/src/types/`: Shared TypeScript interfaces and types.
* `backend/app/api/routes/`: FastAPI route handlers.
* `backend/app/core/`: Configuration, authentication, and security utilities.
* `backend/app/models/`: Database models.
* `backend/app/schemas/`: Pydantic request and response schemas.
* `backend/app/services/`: Business logic and workflow rules.
* `backend/app/repositories/`: Database access operations.
* `backend/app/db/`: Database connection and session management.
* `backend/tests/`: Automated backend tests.
* `backend/alembic/`: Database migration files.

## 5. Database Design

### 5.1 Overview

CampusFix will use a relational data model. The initial core entities are Users, Categories, and Requests.

The user model and authentication-related fields are required for Beta, while the MVP focuses on request and category management.

### 5.2 Entity Relationship Diagram

```text
+------------------+
|      USERS       |
+------------------+
| id (PK)          |
| name             |
| email            |
| password_hash    |  Beta
| role             |  Beta
| is_active        |  Beta
+--------+---------+
         |
         | 1
         |
         | owns many
         |
         v *
+---------------------------+       +------------------+
|         REQUESTS          | *   1 |    CATEGORIES    |
+---------------------------+-------+------------------+
| id (PK)                   |       | id (PK)          |
| title                     |       | name             |
| description               |       | description      |
| status                    |       | is_active (Beta) |
| category_id (FK)          |       +------------------+
| owner_id (FK, Beta)       |
| assigned_staff_id (FK)    |
| resolution_notes          |
| created_at                |
| updated_at                |
+---------------------------+
```

In Beta, each request belongs to one owner and one category. A request may have zero or one assigned staff member. A user may own multiple requests or be assigned multiple requests, depending on their role and permissions.

### 5.3 Users Table — Beta

| Field         | Type                         | Description                               |
| ------------- | ---------------------------- | ----------------------------------------- |
| id            | Integer or UUID, primary key | Unique user identifier                    |
| name          | String                       | User's display name                       |
| email         | String, unique               | Login identity                            |
| password_hash | String                       | Secure password hash; never plaintext     |
| role          | Enum or constrained string   | `STUDENT`, `STAFF`, or `ADMIN`            |
| is_active     | Boolean                      | Whether the account can access the system |
| created_at    | Timestamp                    | Account creation time                     |

Passwords and authentication secrets must never be stored in plaintext.

### 5.4 Categories Table — MVP/Beta

| Field       | Type                         | Description                             |
| ----------- | ---------------------------- | --------------------------------------- |
| id          | Integer or UUID, primary key | Unique category identifier              |
| name        | String, unique               | Category name                           |
| description | String, nullable             | Optional explanation                    |
| is_active   | Boolean                      | Whether the category is available; Beta |

Example categories include:

* IT Support
* Electrical Maintenance
* Plumbing
* Classroom Equipment
* Facilities Maintenance

Categories should be manageable by authorized users. In Beta, deactivating a category is preferable to deleting it if existing requests refer to it.

### 5.5 Requests Table — MVP/Beta

| Field             | Type                             | Description                     |
| ----------------- | -------------------------------- | ------------------------------- |
| id                | Integer or UUID, primary key     | Unique request identifier       |
| title             | String                           | Short request summary           |
| description       | Text                             | Detailed problem description    |
| status            | Enum or constrained string       | Current workflow state          |
| category_id       | Foreign key                      | Associated category             |
| owner_id          | Foreign key, nullable during MVP | Request owner; required in Beta |
| assigned_staff_id | Foreign key, nullable            | Assigned staff member; Beta     |
| resolution_notes  | Text, nullable                   | Resolution details; Beta        |
| created_at        | Timestamp                        | Creation time                   |
| updated_at        | Timestamp                        | Last modification time          |

The database shall enforce valid foreign-key relationships. Status values shall be restricted to the supported lifecycle states.

### 5.6 Data Integrity Rules

* Each entity shall have a unique primary key.
* Category names and user emails shall be unique where applicable.
* Request categories must reference existing category records.
* In Beta, every request must reference a valid owner.
* Assigned staff identifiers must reference eligible user accounts.
* Only valid status values may be stored.
* All timestamps shall be generated consistently by the backend or database.
* Schema changes shall be tracked using migrations.

## 6. API Design

### 6.1 General Conventions

* Base path: `/api`
* Data format: JSON
* HTTP methods shall reflect the operation being performed.
* Resource identifiers shall appear in the URL for individual resources.
* Request and response schemas shall be defined using Pydantic.
* Validation and errors shall use consistent response formats.
* Beta protected routes shall enforce authentication and authorization on the backend.

### 6.2 MVP Endpoints

| Method | Endpoint                        | Purpose                          |
| ------ | ------------------------------- | -------------------------------- |
| POST   | `/api/requests`                 | Create a request                 |
| GET    | `/api/requests`                 | List requests                    |
| GET    | `/api/requests/{request_id}`    | Retrieve one request             |
| PATCH  | `/api/requests/{request_id}`    | Update permitted fields          |
| DELETE | `/api/requests/{request_id}`    | Delete a request under MVP rules |
| GET    | `/api/categories`               | List categories                  |
| POST   | `/api/categories`               | Create a category                |
| PATCH  | `/api/categories/{category_id}` | Update a category                |
| DELETE | `/api/categories/{category_id}` | Delete a category when permitted |

MVP endpoints may use a local development access model. They must not be presented as production-secure until authentication and authorization have been implemented.

### 6.3 Beta Endpoints

| Method | Endpoint                             | Required permission / purpose       |
| ------ | ------------------------------------ | ----------------------------------- |
| POST   | `/api/auth/login`                    | Authenticate a user                 |
| GET    | `/api/auth/me`                       | Retrieve the current user's profile |
| GET    | `/api/requests/my`                   | `request:read_own`                  |
| POST   | `/api/requests/{request_id}/cancel`  | `request:cancel_own`                |
| GET    | `/api/requests/assigned`             | `request:read_assigned`             |
| PATCH  | `/api/requests/{request_id}/status`  | `request:update_assigned`           |
| POST   | `/api/requests/{request_id}/resolve` | `request:resolve`                   |
| PATCH  | `/api/requests/{request_id}/assign`  | `request:assign`                    |
| GET    | `/api/admin/users`                   | `user:manage`                       |
| PATCH  | `/api/admin/users/{user_id}`         | `user:manage`                       |

The final API contract shall be documented and kept consistent with the implemented endpoints.

### 6.4 Example: Create Request

**Request**

```http
POST /api/requests
Content-Type: application/json
```

```json
{
  "title": "Projector not working",
  "description": "The projector in the classroom does not turn on.",
  "category_id": 1
}
```

**Expected response — MVP**

```http
201 Created
```

```json
{
  "id": 101,
  "title": "Projector not working",
  "description": "The projector in the classroom does not turn on.",
  "category_id": 1,
  "status": "PENDING"
}
```

This example omits some database fields for readability. The final response schema shall define all returned fields.

### 6.5 Error Responses

The API shall use suitable HTTP status codes:

* `400 Bad Request`: invalid business operation.
* `401 Unauthorized`: missing or invalid authentication.
* `403 Forbidden`: insufficient permissions.
* `404 Not Found`: resource not found or not accessible under the chosen disclosure policy.
* `409 Conflict`: incompatible operation or state conflict.
* `422 Unprocessable Entity`: input validation failure.
* `500 Internal Server Error`: unexpected server failure.

Client-facing errors shall not expose stack traces, secrets, database credentials, or other sensitive information.

## 7. Authentication and Authorization — Beta

### 7.1 Authentication

Beta shall require users to authenticate before accessing protected resources.

The implementation may use JWT bearer tokens or another suitable session/token mechanism supported by the deployment environment.

If JWT is selected:

1. The user submits credentials to the login endpoint.
2. The backend verifies the credentials.
3. The backend issues a signed token with appropriate identity and expiration information.
4. The client sends the token with protected API requests.
5. The backend validates the token before authorizing the operation.

Passwords shall be hashed using a suitable password-hashing library. Tokens shall have appropriate expiration and signing-secret management.

### 7.2 Role-Based Access Control

The system shall support three roles:

* `STUDENT`
* `STAFF`
* `ADMIN`

Role definitions shall be enforced on the backend. Hiding a button or page in React is not an authorization mechanism.

### 7.3 Permission Scopes

The backend shall define and verify permissions such as:

| Scope                     | Intended capability                                |
| ------------------------- | -------------------------------------------------- |
| `request:create`          | Create a request                                   |
| `request:read_own`        | Read the current user's requests                   |
| `request:update_own`      | Update permitted fields of own requests            |
| `request:cancel_own`      | Cancel eligible own requests                       |
| `request:read_assigned`   | Read requests assigned to the current staff member |
| `request:update_assigned` | Update permitted fields of assigned requests       |
| `request:resolve`         | Resolve eligible assigned requests                 |
| `request:read_all`        | Read all requests                                  |
| `request:assign`          | Assign requests to staff                           |
| `user:manage`             | Manage user accounts and roles                     |
| `category:manage`         | Manage service categories                          |

Each protected operation shall check the necessary permission and, where applicable, verify the request's owner, assigned staff member, status, and other relevant business rules.

### 7.4 Resource-Level Authorization

A student must not access another student's request by changing an ID in the URL.

A staff member must not modify an unassigned request unless an explicit permission permits it.

An administrator may access administrative operations according to the defined permission policy.

The backend shall reject unauthorized operations even if a request is sent manually outside the frontend.

## 8. Frontend Design

### 8.1 Proposed Pages

| Page                | Purpose                                     | Release |
| ------------------- | ------------------------------------------- | ------- |
| Request List        | Display requests returned by the API        | MVP     |
| Create Request      | Submit a request                            | MVP     |
| Request Details     | View and update request information         | MVP     |
| Category Management | Manage request categories                   | MVP     |
| Login               | Authenticate users                          | Beta    |
| Student Dashboard   | View and track own requests                 | Beta    |
| Staff Dashboard     | View and process assigned requests          | Beta    |
| Admin Dashboard     | Assign requests and manage users/categories | Beta    |

### 8.2 Frontend API Client

Frontend API calls shall be centralized in `frontend/src/api/` rather than duplicated throughout components.

The API client shall:

* Use the configured backend base URL.
* Send and receive JSON.
* Handle loading and error states.
* Parse validation errors for display.
* Attach authentication credentials or tokens in Beta.
* Avoid logging credentials, tokens, or other sensitive information.

### 8.3 User Interface Behavior

The interface shall provide:

* Required-field validation.
* Loading indicators during API calls.
* Clear success and failure feedback.
* Empty-state messages when no requests exist.
* Confirmation before destructive operations.
* Role-appropriate navigation in Beta.

Frontend validation improves usability but does not replace backend validation.

## 9. Configuration and Environment Variables

Configuration shall be supplied through environment variables or an equivalent secure configuration mechanism.

An example `.env.example` may contain:

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./campusfix.db
FRONTEND_ORIGIN=http://localhost:5173
SECRET_KEY=replace-with-a-secure-random-value
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

These values are examples, not production-ready secrets or guaranteed final settings. The actual configuration shall match the selected database driver and authentication implementation.

Rules:

* Commit `.env.example` with placeholders.
* Do not commit real `.env` files, credentials, signing keys, or tokens.
* Generate secure secrets outside version control.
* Configure allowed frontend origins explicitly.
* Use HTTPS in production.
* Use separate configuration for development and deployment where needed.

## 10. Database Migrations

Alembic shall be used to track database schema changes if SQLAlchemy is adopted.

The migration workflow shall be:

1. Update the database model.
2. Generate a migration.
3. Review the migration for correctness.
4. Apply it to the development database.
5. Test the application against the updated schema.
6. Commit the migration file.

Destructive schema changes shall be reviewed carefully to avoid accidental data loss. Existing data should be preserved or deliberately migrated when practical.

## 11. Testing Strategy

### 11.1 Backend Testing

Pytest shall be used for backend tests.

| Test category        | Example                                             | Release |
| -------------------- | --------------------------------------------------- | ------- |
| API tests            | Create, retrieve, update, and delete requests       | MVP     |
| Validation tests     | Reject missing fields and invalid category IDs      | MVP     |
| Category tests       | Verify category creation and retrieval              | MVP     |
| Authentication tests | Reject invalid credentials                          | Beta    |
| Authorization tests  | Reject users without required scopes                | Beta    |
| Ownership tests      | Prevent students from reading other users' requests | Beta    |
| Assignment tests     | Prevent staff from processing unauthorized requests | Beta    |
| Lifecycle tests      | Reject invalid status transitions                   | Beta    |

### 11.2 Frontend Testing

The frontend shall be checked to confirm that:

* Forms submit valid data.
* API responses are displayed correctly.
* Loading and error states are understandable.
* Invalid input is communicated clearly.
* Beta navigation and actions reflect user roles.

### 11.3 Integration Testing

Integration tests shall verify that the React frontend communicates correctly with FastAPI and that data persists in the database.

For Beta, tests shall also verify that unauthorized operations are rejected by the backend.

## 12. Security Considerations

The following controls shall be implemented, particularly for Beta:

* Authentication on protected endpoints.
* Role-based authorization and explicit permission checks.
* Ownership and assignment checks for individual requests.
* Server-side input validation.
* Secure password hashing.
* Secure handling of tokens and signing keys.
* Parameterized queries or ORM-managed database access.
* Appropriate CORS configuration.
* No sensitive secrets committed to Git.
* Safe error responses.
* Restricted access to user and administrative operations.
* Tests for common authorization failures.

Authentication alone is insufficient: a valid user must still be denied operations outside their permissions.

## 13. Deployment Strategy

### 13.1 MVP — Local Execution

The MVP shall run locally for development and demonstration.

The developer shall:

1. Install the required Python and Node.js dependencies.
2. Configure the backend database.
3. Apply required database migrations.
4. Start the FastAPI backend.
5. Start the React development server.
6. Verify frontend-backend communication.
7. Test the documented API endpoints.

FastAPI's interactive API documentation may be available through its standard documentation route, such as `/docs`, depending on application configuration.

### 13.2 Beta — Deployment

The Beta release shall target a suitable hosting environment for the frontend and backend.

Deployment requirements include:

* Production environment variables.
* Secure authentication configuration.
* Database setup and migrations.
* HTTPS.
* Correct CORS configuration.
* Restricted administrative access.
* A documented process for starting and updating the application.

The hosting provider and final deployment architecture shall be selected based on availability, course requirements, and project constraints.

## 14. Development Workflow

Development shall follow the project's GitHub workflow:

1. Create an issue describing a task.
2. Create a feature branch associated with that issue.
3. Implement the task and test the changes.
4. Commit changes using descriptive messages.
5. Open a pull request targeting `main`.
6. Reference the issue using `Closes #issue_number` in the pull request description.
7. Review and merge the pull request when ready.

Documentation and code shall be maintained in the project repository. Secrets, generated environments, virtual environments, and unnecessary build files shall be excluded through `.gitignore`.

## 15. Implementation Milestones

| Milestone | Deliverables                                                        | Release |
| --------- | ------------------------------------------------------------------- | ------- |
| M1        | Repository structure, configuration, FastAPI setup, and React setup | MVP     |
| M2        | Database models and category APIs                                   | MVP     |
| M3        | Request CRUD APIs and validation                                    | MVP     |
| M4        | Frontend request forms and API integration                          | MVP     |
| M5        | Authentication and user model                                       | Beta    |
| M6        | Roles, permission scopes, and resource-level authorization          | Beta    |
| M7        | Staff assignment, status workflow, and resolution notes             | Beta    |
| M8        | Role-specific dashboards, tests, and security review                | Beta    |
| M9        | Deployment, documentation, and final demonstration                  | Beta    |

The milestones are a proposed sequence and may be adjusted according to course deadlines and faculty feedback.

## 16. Risks and Mitigation

| Risk                               | Impact                                   | Mitigation                                                            |
| ---------------------------------- | ---------------------------------------- | --------------------------------------------------------------------- |
| Scope becomes too large            | Core features may remain incomplete      | Prioritize MVP requirements before Beta features                      |
| Authentication is implemented late | Beta integration may be delayed          | Define user roles and security boundaries early                       |
| Incorrect permission checks        | Unauthorized data access                 | Add backend authorization and resource-level tests                    |
| Database schema changes            | Data inconsistency or migration problems | Use versioned migrations and test schema updates                      |
| Frontend-backend mismatch          | Integration errors                       | Maintain consistent request/response schemas                          |
| Deployment configuration errors    | Beta may fail during demonstration       | Document setup and test deployment early                              |
| Team coordination issues           | Delays and conflicting changes           | Use issues, feature branches, pull requests, and clear task ownership |

## 17. Definition of Done

### MVP

* [ ] FastAPI backend runs locally.
* [ ] React frontend runs locally.
* [ ] Request CRUD APIs work according to the agreed scope.
* [ ] Category APIs work.
* [ ] Validation and error responses are tested.
* [ ] Frontend-backend integration is demonstrated.
* [ ] Setup instructions are documented.

### Beta

* [ ] User authentication works.
* [ ] Student, staff, and administrator roles are enforced.
* [ ] Permission scopes and resource-level authorization are tested.
* [ ] Students can track their own requests.
* [ ] Staff can process assigned requests and record resolution notes.
* [ ] Administrators can assign requests and manage authorized resources.
* [ ] Critical workflows and permission failures are tested.
* [ ] Configuration and secrets are handled securely.
* [ ] The application is deployed or prepared for the agreed final demonstration.
* [ ] Documentation matches the implemented behavior.

## 18. Conclusion

This design establishes a maintainable and achievable architecture for CampusFix. The MVP focuses on request and category management through REST APIs, while the Beta adds authentication, authorization, permission scopes, request assignment, workflow management, role-specific dashboards, and deployment.

The implementation shall remain aligned with the PRD and SRS. Features described in this document are planned requirements and should not be considered implemented until verified in the repository.
