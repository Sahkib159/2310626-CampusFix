# CampusFix — Product Requirements Document (PRD)

| Field             | Details                                              |
| ----------------- | ---------------------------------------------------- |
| Project           | CampusFix — Campus Service Request Management System |
| Document          | Product Requirements Document                        |
| Version           | 1.0                                                  |
| Status            | Draft                                                |
| Release Plan      | MVP (Mid-term) and Beta (Final)                      |
| Related Documents | [SRS](02-srs.md) · [TDD](03-tdd.md)                  |

## 1. Purpose

CampusFix is a web-based system for managing campus service requests. It aims to replace informal reporting methods with a structured process for submitting, tracking, assigning, and resolving campus maintenance and service issues.

## 2. Problem Statement

Students may have difficulty reporting campus problems and knowing whether they are being addressed. Staff may lack a centralized way to organize requests, track progress, and record resolutions. CampusFix will provide a central system for managing this workflow.

## 3. Goals and Objectives

* Provide a simple way to submit and manage campus service requests.
* Allow users to track request status.
* Help staff organize and resolve assigned requests.
* Restrict access according to user roles and permissions in the Beta release.
* Deliver a practical, maintainable application within the semester.

## 4. Target Users

| User          | Description                                                            |
| ------------- | ---------------------------------------------------------------------- |
| Student       | Submits campus service requests and tracks their progress.             |
| Service Staff | Handles assigned requests and records progress and resolution details. |
| Administrator | Manages users, categories, assignments, and overall requests.          |

## 5. Release Plan

### MVP — Mid-term

The MVP focuses on the core request workflow and local execution.

* Create, view, update, and delete service requests through REST APIs.
* Create and view request categories.
* Provide a basic React and TypeScript frontend connected to the FastAPI backend.
* Run the application locally for demonstration.

### Beta — Final

The Beta release adds controlled access and a fuller service workflow.

* Authentication and authorization.
* Role-based access control (RBAC) and permission scopes.
* Student request ownership and status tracking.
* Staff assignment, progress updates, and resolution notes.
* Administrative user and category management.
* Security improvements and deployment.

## 6. Scope

### In Scope

* Campus maintenance and service requests.
* Request categories and status tracking.
* Student, staff, and administrator roles.
* REST API integration between frontend and backend.
* Local development for MVP and deployment planning for Beta.

### Out of Scope

* AI/ML-based request classification.
* Chatbots and recommendation systems.
* Payment processing.
* Native mobile applications.
* Complex enterprise integrations.

## 7. Feature Priorities

MoSCoW means Must have, Should have, Could have, and Won't have for the current project scope.

| Feature                                | Priority    | Release      |
| -------------------------------------- | ----------- | ------------ |
| Create and manage service requests     | Must have   | MVP          |
| View requests and categories           | Must have   | MVP          |
| React frontend and FastAPI integration | Must have   | MVP          |
| Local setup and API documentation      | Must have   | MVP          |
| Authentication and authorization       | Must have   | Beta         |
| RBAC and permission scopes             | Must have   | Beta         |
| Staff assignment and status updates    | Must have   | Beta         |
| Resolution notes                       | Should have | Beta         |
| Admin user and category management     | Should have | Beta         |
| Basic administrative statistics        | Could have  | Beta         |
| AI/ML features                         | Won't have  | Out of scope |

## 8. User Stories

### MVP

* As a project user, I want to create a service request so that a campus issue can be recorded.
* As a project user, I want to view and update requests so that request information remains current.
* As a project user, I want to delete a request so that an incorrect test request can be removed.
* As a project user, I want to view request categories so that requests can be organized.

### Beta

* As a student, I want to view my own requests and their statuses so that I can track progress.
* As a student, I want to cancel an eligible pending request.
* As service staff, I want to view assigned requests and update their status.
* As service staff, I want to record resolution notes when completing a request.
* As an administrator, I want to assign requests and manage users and categories.

## 9. Success Metrics

### MVP

* All planned MVP API operations pass basic functional tests.
* The frontend successfully communicates with the backend.
* The application starts locally using documented instructions.
* Required request data is validated and errors are handled clearly.

### Beta

* Unauthenticated users cannot access protected endpoints.
* Users cannot access requests or actions beyond their permissions.
* Valid requests can progress through the defined workflow.
* Staff can record resolutions and administrators can assign requests.
* The application can be deployed using documented configuration.

## 10. Assumptions and Constraints

* The project is developed for a university course within a semester.
* The required stack is React.js with TypeScript and FastAPI with Python.
* The frontend and backend communicate through REST APIs.
* A suitable relational database will be selected and documented in the TDD.
* Authentication and role-based restrictions will be introduced in Beta.
* The MVP must remain small enough to demonstrate reliably.

## 11. Milestones

| Milestone                                            | Target                |
| ---------------------------------------------------- | --------------------- |
| Documentation and project planning                   | Before implementation |
| Core request and category APIs                       | MVP                   |
| Frontend/backend integration and local demo          | Mid-term              |
| Authentication, RBAC, and permission scopes          | Beta                  |
| Assignment, status tracking, and resolution workflow | Beta                  |
| Security checks, testing, and deployment             | Final                 |
| Final demonstration                                  | End of semester       |

## 12. Dependencies and Risks

**Dependencies**

* Python and FastAPI development environment.
* Node.js and a React/TypeScript development environment.
* Database configuration and connectivity.
* Agreement on request fields, status transitions, and role permissions.

**Risks**

* Scope growth may delay core deliverables.
* Incorrect permission checks could expose requests to unauthorized users.
* Frontend/backend contract changes may cause integration issues.
* Deployment configuration may differ from local development.

**Mitigation:** Prioritize the MVP, document API contracts, test role permissions before Beta completion, and keep configuration and secrets out of version control.

## 13. Definition of Success

CampusFix will be considered successful when the MVP demonstrates a working request-management flow and the Beta adds secure, role-based request handling with documented setup and deployment instructions.
