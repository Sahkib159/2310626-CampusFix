# CampusFix — Campus Service Request Management System

CampusFix is a web-based campus service request management system designed to help students report campus service issues and enable authorized staff to manage, assign, track, and resolve them.

The project is being developed as part of a university software engineering course using React.js with TypeScript, FastAPI with Python, and REST APIs.

> **Project status:** Documentation and planning. Features listed below are planned requirements and should not be considered implemented until verified.

## Documentation

| Document                                                    | Description                                                                                     |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| [Product Requirements Document (PRD)](docs/01-prd.md)       | Project goals, scope, target users, priorities, and release plan                                |
| [Software Requirements Specification (SRS)](docs/02-srs.md) | Functional requirements, non-functional requirements, user roles, APIs, and acceptance criteria |
| [Technical Design Document (TDD)](docs/03-tdd.md)           | System architecture, database design, API design, security, testing, and deployment             |

## Project Goals

* Provide a structured process for submitting campus service requests.
* Allow students to track the progress of their requests.
* Enable service staff to process assigned requests and document resolutions.
* Provide administrators with request assignment and management capabilities.
* Apply authentication, authorization, role-based access control (RBAC), and permission scopes in the final release.

## Release Plan

### MVP — Mid-term Release

The MVP focuses on the core functionality required to demonstrate the system locally.

Planned features:

* Create, view, update, and delete service requests through REST APIs.
* Create and manage service categories.
* Validate request data and handle errors.
* Integrate the React frontend with the FastAPI backend.
* Run the application locally.

### Beta — Final Release

The Beta expands the MVP with security and role-specific functionality.

Planned features:

* User authentication and authorization.
* Role-based access control for students, service staff, and administrators.
* Permission scopes and resource-level access checks.
* Student request tracking and cancellation of eligible pending requests.
* Staff assignment, status updates, and resolution notes.
* Administrative management of users and categories.
* Role-specific dashboards.
* Security testing and deployment.

## Technology Stack

| Technology          | Purpose                           |
| ------------------- | --------------------------------- |
| React.js            | Frontend user interface           |
| TypeScript          | Frontend development              |
| FastAPI             | Python backend and REST APIs      |
| Pydantic            | Request and response validation   |
| SQLAlchemy          | Database access, if adopted       |
| SQLite / PostgreSQL | Relational database options       |
| Pytest              | Backend testing                   |
| Git and GitHub      | Version control and collaboration |

The final database and dependency versions will be confirmed during implementation.

## User Roles

* **Student:** Submit service requests and, in Beta, track and manage eligible requests.
* **Service Staff:** View assigned requests, update progress, and add resolution notes.
* **Administrator:** Assign requests, manage users and categories, and access authorized administrative functions.

## Planned Request Lifecycle

`PENDING → ASSIGNED → IN PROGRESS → RESOLVED`

Eligible pending requests may also be cancelled:

`PENDING → CANCELLED`

The backend will enforce valid status transitions and role-specific permissions in the Beta release.

## Getting Started

The application setup instructions will be completed alongside implementation. The commands below are illustrative and may need to be adjusted to match the final repository structure.

### Prerequisites

* Python
* Node.js and npm
* Git

### Backend

After the FastAPI backend and its dependency file have been implemented:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install the project's dependencies:

```bash
pip install -r requirements.txt
```

Start the backend using the entry point configured by the project. For example, if the application is exposed as `app.main:app`:

```bash
uvicorn app.main:app --reload
```

### Frontend

After the React application has been configured:

```bash
cd frontend
npm install
npm run dev
```

Check the frontend and backend configuration for the correct API URL before running the application.

### API Documentation

FastAPI normally provides interactive API documentation at:

`http://127.0.0.1:8000/docs`

This URL will be available when the backend is running and its API documentation is enabled.

## Development Workflow

CampusFix uses an issue-based GitHub workflow:

1. Create a GitHub issue describing the task.
2. Create a feature branch linked to the issue.
3. Implement the changes and test them.
4. Commit changes with descriptive messages.
5. Open a pull request targeting `main`.
6. Reference the issue using `Closes #issue_number` in the pull request description.
7. Review and merge the pull request.

## Project Scope

CampusFix focuses on campus service request management. AI/ML features, chatbots, payment processing, native mobile applications, and complex external integrations are outside the planned MVP and Beta scope.

## Academic Project

CampusFix is an academic software engineering project. Its requirements and technical design may be refined based on faculty feedback and implementation findings.
