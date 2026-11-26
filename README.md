# CampusFix — Campus Service Request Management System

CampusFix is a web-based campus service request management system designed to help students report campus service issues and enable authorized staff to manage, assign, track, and resolve them.

The project is being developed as part of a university software engineering course using React.js with TypeScript, FastAPI with Python, and REST APIs.

> **Project status:** Beta implementation in progress. Authentication, role-based request access, and staff assignment workflows have been implemented. Additional verification and integration work is ongoing.

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

Follow these instructions to run CampusFix locally.

### Prerequisites

- Python 3.10+
- Node.js and npm
- Git
- A PostgreSQL database (local PostgreSQL or Supabase)

### 1. Clone the Repository

```powershell
git clone https://github.com/Sahkib159/2310626-CampusFix.git
cd 2310626-CampusFix
```

### 2. Backend Setup

Create and activate a Python virtual environment from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies and configure environment variables:

```powershell
cd backend
pip install -r requirements.txt

if (!(Test-Path .env)) {
    Copy-Item .env.example .env
}
```

Edit `backend/.env` and provide your database URL, a cryptographically random
`JWT_SECRET_KEY`, and a separate `PASSWORD_PEPPER` (each at least 32 bytes).

Keep `ACCESS_TOKEN_EXPIRE_MINUTES` between 1 and 15, and use
`COOKIE_SECURE=true` with an appropriate `COOKIE_SAMESITE` setting in
production. Use the placeholders in `backend/.env.example` only as a template;
never use them as deployed secrets.

Apply database migrations:

```powershell
alembic upgrade head
```

Start the backend server:

```powershell
uvicorn main:app --reload
```

The backend will be available at:

- API: `http://127.0.0.1:8000`
- API documentation: `http://127.0.0.1:8000/api/docs`

### 3. Frontend Setup

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your terminal.

### 4. Environment Configuration

The backend uses `backend/.env` for database and authentication configuration.

A template is provided in `backend/.env.example`. Never commit your actual `.env` file or expose database credentials and secret keys.

### 5. Database and Account Setup

Run database migrations before starting the application.

Public registration creates student accounts. Staff and administrator accounts must be provisioned through the backend's account creation scripts.


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
