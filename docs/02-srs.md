# Software Requirements Specification (SRS)

## CampusFix — Campus Service Request Management System

| Field            | Details                      |
| ---------------- | ---------------------------- |
| Document ID      | SRS-001                      |
| Version          | 1.0                          |
| Status           | Draft                        |
| Project          | CampusFix                    |
| Frontend         | React.js with TypeScript     |
| Backend          | FastAPI with Python          |
| API Style        | REST                         |
| Release Plan     | MVP (Mid-term), Beta (Final) |
| Related Document | [PRD](01-prd.md)             |
| Related Document | [TDD](03-tdd.md)             |

## 1. Introduction

### 1.1 Purpose

This document specifies the functional and non-functional requirements for CampusFix. It defines the expected system behavior, user roles, request lifecycle, API requirements, security requirements, and acceptance criteria.

### 1.2 Scope

CampusFix is a web-based system for managing campus service requests. It provides a structured way for students to submit requests for campus services and allows authorized staff to process and resolve them.

The system will be developed in two releases:

* **MVP (Mid-term):** Core service request and category management through REST APIs, with local execution and frontend-backend integration.
* **Beta (Final):** Authentication, authorization, role-based access control, permission scopes, staff assignment, request tracking, resolution notes, and administrative functionality.

### 1.3 Definitions

| Term             | Definition                                          |
| ---------------- | --------------------------------------------------- |
| MVP              | Minimum Viable Product                              |
| Beta             | Expanded release for the final demonstration        |
| REST             | Representational State Transfer                     |
| API              | Application Programming Interface                   |
| RBAC             | Role-Based Access Control                           |
| Authentication   | Verifying a user's identity                         |
| Authorization    | Determining what a user may access                  |
| Permission scope | A specific permission required to perform an action |
| CRUD             | Create, Read, Update, Delete                        |
| FR               | Functional Requirement                              |
| NFR              | Non-Functional Requirement                          |

## 2. Overall Description

### 2.1 Product Perspective

CampusFix consists of a React.js frontend and a FastAPI backend. The frontend communicates with the backend using REST APIs. The backend validates requests, applies business rules, and interacts with a database.

### 2.2 User Classes

| User role     | Release  | Responsibilities                                                            |
| ------------- | -------- | --------------------------------------------------------------------------- |
| Student       | MVP/Beta | Submit and manage service requests; in Beta, track request progress         |
| Service Staff | Beta     | View assigned requests, update status, and record resolution notes          |
| Administrator | Beta     | View and assign requests, manage categories and users, and monitor activity |

During the MVP, request-management endpoints may be used in a local development environment without production authentication. These endpoints must not be exposed as a publicly deployed, unrestricted service.

### 2.3 Operating Environment

* Modern web browsers.
* React.js and TypeScript frontend.
* Python and FastAPI backend.
* A relational database supported by the selected backend configuration.
* Local development environment for MVP and an appropriate deployment environment for Beta.

### 2.4 Assumptions and Constraints

* The project is intended for a semester-long academic course.
* The initial scope focuses on campus service requests rather than a complete university management system.
* The frontend and backend must communicate through REST APIs.
* Authentication and role-specific permissions are required for Beta.
* AI, machine learning, LLMs, payment processing, and external notification integrations are out of scope unless approved later.

## 3. Use Cases

### 3.1 MVP Use Cases

| ID     | Use case             | Primary actor      | Description                                                      |
| ------ | -------------------- | ------------------ | ---------------------------------------------------------------- |
| UC-M01 | Create Request       | Student / API user | Submit a service request with a title, description, and category |
| UC-M02 | View Requests        | API user           | Retrieve existing requests                                       |
| UC-M03 | View Request Details | API user           | Retrieve a request by its identifier                             |
| UC-M04 | Update Request       | API user           | Update permitted request information                             |
| UC-M05 | Delete Request       | API user           | Delete a request according to MVP rules                          |
| UC-M06 | Manage Categories    | API user           | Create, view, update, and delete request categories              |

### 3.2 Beta Use Cases

| ID     | Use case                 | Primary actor | Description                                                   |
| ------ | ------------------------ | ------------- | ------------------------------------------------------------- |
| UC-B01 | Authenticate             | All users     | Sign in and obtain an authenticated session or token          |
| UC-B02 | View Own Requests        | Student       | View only the student's own requests                          |
| UC-B03 | Track Request            | Student       | View status and resolution information                        |
| UC-B04 | Cancel Request           | Student       | Cancel an eligible pending request                            |
| UC-B05 | Process Assigned Request | Service Staff | View assigned requests and update their progress              |
| UC-B06 | Resolve Request          | Service Staff | Mark an eligible request as resolved and add resolution notes |
| UC-B07 | Assign Request           | Administrator | Assign a request to an appropriate staff member               |
| UC-B08 | Manage Users             | Administrator | Manage user accounts and roles                                |
| UC-B09 | Manage Categories        | Administrator | Manage active request categories                              |

## 4. Functional Requirements

Every requirement is assigned a unique identifier and a release.

### 4.1 MVP Requirements

| ID     | Requirement                                                                                                | Priority | Release |
| ------ | ---------------------------------------------------------------------------------------------------------- | -------- | ------- |
| FR-M01 | The system shall allow a client to create a service request with a title, description, and valid category. | Must     | MVP     |
| FR-M02 | The system shall return a list of existing service requests.                                               | Must     | MVP     |
| FR-M03 | The system shall return the details of a request identified by its ID.                                     | Must     | MVP     |
| FR-M04 | The system shall allow permitted request fields to be updated.                                             | Must     | MVP     |
| FR-M05 | The system shall allow a request to be deleted according to MVP rules.                                     | Should   | MVP     |
| FR-M06 | The system shall provide endpoints to list and manage service categories.                                  | Must     | MVP     |
| FR-M07 | The system shall validate required fields and reject invalid input.                                        | Must     | MVP     |
| FR-M08 | The system shall return appropriate HTTP status codes and structured error responses.                      | Must     | MVP     |
| FR-M09 | The React frontend shall communicate with the FastAPI backend through REST APIs.                           | Must     | MVP     |
| FR-M10 | The application shall run locally using documented setup instructions.                                     | Must     | MVP     |

### 4.2 Beta Requirements

| ID     | Requirement                                                                                       | Priority | Release |
| ------ | ------------------------------------------------------------------------------------------------- | -------- | ------- |
| FR-B01 | The system shall authenticate users before allowing protected operations.                         | Must     | Beta    |
| FR-B02 | The system shall enforce role-based authorization for protected endpoints.                        | Must     | Beta    |
| FR-B03 | The system shall enforce explicit permission scopes for sensitive operations.                     | Must     | Beta    |
| FR-B04 | Students shall be able to view their own service requests.                                        | Must     | Beta    |
| FR-B05 | Students shall be able to cancel eligible pending requests.                                       | Should   | Beta    |
| FR-B06 | Staff shall be able to view requests assigned to them.                                            | Must     | Beta    |
| FR-B07 | Staff shall be able to update the status of assigned requests according to permitted transitions. | Must     | Beta    |
| FR-B08 | Authorized staff shall be able to add resolution notes when resolving requests.                   | Must     | Beta    |
| FR-B09 | Administrators shall be able to assign requests to staff members.                                 | Must     | Beta    |
| FR-B10 | Administrators shall be able to manage user roles and account access.                             | Must     | Beta    |
| FR-B11 | Administrators shall be able to manage service categories.                                        | Must     | Beta    |
| FR-B12 | The system shall prevent users from accessing requests or operations outside their permissions.   | Must     | Beta    |
| FR-B13 | The system shall provide a user-facing dashboard appropriate to each role.                        | Should   | Beta    |
| FR-B14 | The system shall support secure configuration and deployment practices.                           | Must     | Beta    |

## 5. Non-Functional Requirements

| ID     | Requirement                                                                                                                                                | Release  |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| NFR-01 | The API shall validate incoming data using appropriate schemas and business rules.                                                                         | MVP      |
| NFR-02 | API responses shall use consistent JSON structures and appropriate HTTP status codes.                                                                      | MVP      |
| NFR-03 | The project shall use a maintainable separation between frontend, backend, and data-access logic.                                                          | MVP      |
| NFR-04 | Under normal local demonstration conditions, common API operations should generally respond within 2 seconds, excluding network and infrastructure delays. | MVP      |
| NFR-05 | Protected endpoints shall require valid authentication.                                                                                                    | Beta     |
| NFR-06 | Authorization checks shall be performed on the backend and shall not rely only on frontend visibility.                                                     | Beta     |
| NFR-07 | Passwords shall never be stored in plaintext; a suitable password-hashing method shall be used if password-based authentication is implemented.            | Beta     |
| NFR-08 | Secrets and credentials shall be stored in environment configuration rather than committed to version control.                                             | Beta     |
| NFR-09 | The application shall provide understandable validation and error messages without exposing sensitive internal details.                                    | MVP/Beta |
| NFR-10 | The system shall use automated or repeatable tests for critical request and permission workflows where practical.                                          | Beta     |
| NFR-11 | The interface shall provide clear loading, success, empty, and error states for major request workflows.                                                   | MVP/Beta |

## 6. Business Rules and Request Lifecycle

### 6.1 Request Data

A service request shall contain, at minimum:

* Unique request identifier.
* Title.
* Description.
* Category identifier.
* Current status.
* Creation timestamp.
* Last-update timestamp.

For Beta, a request shall additionally support:

* Student/request owner identifier.
* Assigned staff identifier, when assigned.
* Resolution notes, when resolved.
* Relevant assignment and resolution timestamps, where practical.

### 6.2 Validation Rules

* The title and description shall not be empty or contain only whitespace.
* The title and description shall have documented maximum lengths.
* The category must exist and be valid.
* Unknown request IDs shall return a not-found response.
* Invalid field values shall return a validation error.
* A user shall not be allowed to set a request status arbitrarily if that transition is not permitted.
* Beta requests must be associated with an authenticated owner.
* Students may access only their own requests, while staff access is limited to assigned requests unless another explicit permission allows otherwise.

### 6.3 Status Transitions

The intended Beta lifecycle is:

`PENDING → ASSIGNED → IN PROGRESS → RESOLVED`

A student may cancel an eligible request while it is still `PENDING`:

`PENDING → CANCELLED`

Rules:

* New requests begin with `PENDING`.
* Assignment changes an eligible request to `ASSIGNED`.
* Assigned staff may move a request to `IN PROGRESS`.
* Authorized staff may move an eligible request to `RESOLVED`.
* A resolved request must include resolution notes.
* A cancelled request cannot be processed further through the normal workflow.
* Only authorized actors may perform each transition.

The MVP may store a simpler status field, but the full role-based lifecycle is a Beta requirement.

## 7. Beta Permission Matrix

The following permissions must be enforced by the backend. The matrix describes the intended Beta behavior.

| Operation                      | Student                     | Staff                            | Admin         |
| ------------------------------ | --------------------------- | -------------------------------- | ------------- |
| Create request                 | Own request                 | No                               | As authorized |
| Read own request               | Yes                         | Only if assigned/authorized      | Yes           |
| Read all requests              | No                          | No, unless separately authorized | Yes           |
| Update own request             | Limited, according to rules | No                               | Yes           |
| Cancel pending request         | Own request                 | No                               | As authorized |
| Read assigned requests         | No                          | Yes                              | Yes           |
| Update assigned request status | No                          | Yes                              | Yes           |
| Add resolution notes           | No                          | Yes, if assigned                 | As authorized |
| Assign staff                   | No                          | No                               | Yes           |
| Manage users and roles         | No                          | No                               | Yes           |
| Manage categories              | No                          | No                               | Yes           |

### 7.1 Permission Scopes

The Beta implementation should define explicit permission scopes, such as:

* `request:create`
* `request:read_own`
* `request:update_own`
* `request:cancel_own`
* `request:read_assigned`
* `request:update_assigned`
* `request:resolve`
* `request:read_all`
* `request:assign`
* `user:manage`
* `category:manage`

The backend must verify both the relevant permission and resource ownership or assignment where applicable. Possessing a general permission must not automatically grant access to every record.

## 8. REST API Requirements

Exact paths and schemas will be finalized in the TDD. The following endpoints represent the intended API surface.

### 8.1 MVP Endpoints

| Method    | Endpoint                        | Purpose                          | Release |
| --------- | ------------------------------- | -------------------------------- | ------- |
| POST      | `/api/requests`                 | Create a request                 | MVP     |
| GET       | `/api/requests`                 | List requests                    | MVP     |
| GET       | `/api/requests/{request_id}`    | Retrieve request details         | MVP     |
| PUT/PATCH | `/api/requests/{request_id}`    | Update a request                 | MVP     |
| DELETE    | `/api/requests/{request_id}`    | Delete a request                 | MVP     |
| GET       | `/api/categories`               | List categories                  | MVP     |
| POST      | `/api/categories`               | Create a category                | MVP     |
| PUT/PATCH | `/api/categories/{category_id}` | Update a category                | MVP     |
| DELETE    | `/api/categories/{category_id}` | Delete a category when permitted | MVP     |

### 8.2 Beta Endpoints

| Method | Endpoint                             | Purpose                                            | Release |
| ------ | ------------------------------------ | -------------------------------------------------- | ------- |
| POST   | `/api/auth/login`                    | Authenticate a user                                | Beta    |
| GET    | `/api/auth/me`                       | Retrieve the authenticated user's profile          | Beta    |
| GET    | `/api/requests/my`                   | List the current student's requests                | Beta    |
| POST   | `/api/requests/{request_id}/cancel`  | Cancel an eligible request                         | Beta    |
| GET    | `/api/requests/assigned`             | List requests assigned to the current staff member | Beta    |
| PATCH  | `/api/requests/{request_id}/status`  | Update an authorized request's status              | Beta    |
| POST   | `/api/requests/{request_id}/resolve` | Resolve a request with notes                       | Beta    |
| PATCH  | `/api/requests/{request_id}/assign`  | Assign a request to staff                          | Beta    |
| GET    | `/api/admin/users`                   | List users for administration                      | Beta    |
| PATCH  | `/api/admin/users/{user_id}`         | Update permitted user details or role              | Beta    |

Every Beta endpoint shall define its required authentication, permission scope, role restrictions, and resource-level access checks in the TDD.

### 8.3 HTTP Status Codes

| Status code               | Meaning                                                                        |
| ------------------------- | ------------------------------------------------------------------------------ |
| 200 OK                    | Successful retrieval or update                                                 |
| 201 Created               | Resource created successfully                                                  |
| 204 No Content            | Successful operation with no response body                                     |
| 400 Bad Request           | Invalid operation or business-rule violation                                   |
| 401 Unauthorized          | Authentication missing or invalid                                              |
| 403 Forbidden             | Authenticated user lacks permission                                            |
| 404 Not Found             | Resource does not exist or is not accessible under the API's disclosure policy |
| 409 Conflict              | Operation conflicts with the current resource state                            |
| 422 Unprocessable Entity  | Request data fails validation                                                  |
| 500 Internal Server Error | Unexpected server error                                                        |

## 9. Acceptance Criteria

### AC-01: Create a Request — MVP

**Given** the backend is running and a valid category exists,

**When** a client submits a request with a non-empty title, description, and valid category,

**Then** the API creates the request and returns HTTP `201 Created` with the created resource.

### AC-02: Reject Invalid Request Data — MVP

**Given** the API is available,

**When** a client submits a request with a missing title or invalid category,

**Then** the API rejects the input with an appropriate validation response and does not create an invalid record.

### AC-03: Retrieve a Request — MVP

**Given** a request exists,

**When** a client retrieves it using its ID,

**Then** the API returns the request details with HTTP `200 OK`.

If the request does not exist, the API returns HTTP `404 Not Found`.

### AC-04: Authenticate a User — Beta

**Given** a registered user has valid credentials,

**When** the user submits them to the login endpoint,

**Then** the system authenticates the user and returns the configured authentication result.

Invalid credentials must not grant access.

### AC-05: Enforce Student Ownership — Beta

**Given** a student is authenticated,

**When** the student attempts to read or modify another student's request,

**Then** the backend denies the unauthorized operation and does not disclose protected request data.

### AC-06: Process an Assigned Request — Beta

**Given** a staff member is authenticated and has an appropriate permission scope,

**When** the staff member updates a request assigned to them using an allowed status transition,

**Then** the system saves the status change.

Attempts to process unassigned requests without permission must be denied.

### AC-07: Resolve a Request — Beta

**Given** a staff member is authorized to resolve an assigned request,

**When** the staff member submits a valid resolution with notes,

**Then** the request is marked `RESOLVED` and the notes are stored.

### AC-08: Assign a Request — Beta

**Given** an administrator is authenticated and authorized,

**When** the administrator assigns a valid request to an eligible staff member,

**Then** the system records the assignment and updates the request status according to the defined lifecycle.

### AC-09: Enforce Permission Scopes — Beta

**Given** an authenticated user does not have the permission required for an operation,

**When** that user calls the protected endpoint,

**Then** the backend denies the operation even if the frontend displays or allows access to the relevant screen.

### AC-10: Run the Application Locally — MVP

**Given** the documented dependencies and configuration are available,

**When** a developer follows the README instructions,

**Then** the frontend and backend can run locally and communicate through the documented REST APIs.

## 10. Error Handling

The API shall return consistent JSON error responses containing a useful error message and, where appropriate, field-level validation details.

Example:

```json
{
  "detail": "Request title is required"
}
```

The exact response format shall be consistent with FastAPI validation behavior or a documented custom error schema.

The backend shall not expose stack traces, passwords, tokens, database credentials, or other sensitive implementation details in client-facing errors.

## 11. Traceability Matrix

| User story / use case            | Requirements           | API area                         | Release |
| -------------------------------- | ---------------------- | -------------------------------- | ------- |
| Submit a service request         | FR-M01, FR-M07         | Requests CRUD                    | MVP     |
| View and maintain requests       | FR-M02–FR-M05          | Requests CRUD                    | MVP     |
| Select and manage categories     | FR-M06                 | Categories                       | MVP     |
| Run the system locally           | FR-M09, FR-M10         | Frontend/backend integration     | MVP     |
| Sign in securely                 | FR-B01                 | Authentication                   | Beta    |
| Protect role-specific operations | FR-B02, FR-B03, FR-B12 | Authorization and protected APIs | Beta    |
| Track own request                | FR-B04, FR-B05         | Student request APIs             | Beta    |
| Process and resolve requests     | FR-B06–FR-B08          | Staff request APIs               | Beta    |
| Assign requests and manage users | FR-B09, FR-B10         | Administrative APIs              | Beta    |
| Manage categories securely       | FR-B11                 | Category administration          | Beta    |
| Use a role-specific dashboard    | FR-B13                 | Frontend dashboard               | Beta    |

## 12. Out of Scope

The following features are not required for the planned MVP or Beta:

* AI/ML-based request classification or resolution.
* Chatbots or LLM-based assistance.
* Payment processing.
* Native Android or iOS applications.
* Integration with external university systems.
* Complex analytics or predictive reporting.
* Email, SMS, or push notifications unless time permits and the core requirements are complete.

## 13. Document Approval

This SRS is a draft requirements baseline for the CampusFix academic project. Requirements may be refined with faculty feedback, provided that changes remain consistent with the agreed scope, release plan, and technology stack.
