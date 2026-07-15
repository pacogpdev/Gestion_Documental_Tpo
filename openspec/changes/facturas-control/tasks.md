# Tasks: facturas-control

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1500 - 2100 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Foundation) $\rightarrow$ PR 2 (AI/Upload) $\rightarrow$ PR 3 (Mgmt API) $\rightarrow$ PR 4 (FE Core) $\rightarrow$ PR 5 (FE Approval) $\rightarrow$ PR 6 (Testing) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Foundation & Infrastructure | PR 1 | DB Schema, Project Setup, Entra ID Setup |
| 2 | AI Extraction & Upload | PR 2 | AI Service, Blob Storage, Upload API; depends on PR 1 |
| 3 | Management API & Audit | PR 3 | Status/Approve API, Audit Logs, RBAC; depends on PR 2 |
| 4 | Frontend Core & Upload | PR 4 | React Setup, API Hooks, Upload UI; depends on PR 2 |
| 5 | Frontend Approval Workflow | PR 5 | Invoice List, Detail View, Approval UI; depends on PR 3 & PR 4 |
| 6 | Testing & Verification | PR 6 | Pytest, Playwright E2E, Security Audit; depends on PR 5 |

## Phase 1: Foundation & Infrastructure

- [ ] 1.1 Setup PostgreSQL database with `suppliers`, `invoices`, `line_items`, `roles`, `users`, `user_roles`, and `audit_logs` tables.
- [ ] 1.2 Configure Azure AI Document Intelligence and Blob Storage resources in the Azure portal.
- [ ] 1.3 Create Azure Entra ID App Registration and define roles (`Admin`, `Approver`, `Viewer`).
- [ ] 1.4 Initialize FastAPI project structure including `main.py` and core configuration.
- [ ] 1.5 Implement `backend/app/core/security.py` for JWT validation using Entra ID JWKS.

## Phase 2: AI Service & Data Persistence

- [ ] 2.1 Implement `backend/app/models/` using SQLAlchemy to map the PostgreSQL schema.
- [ ] 2.2 Implement `backend/app/services/ai_service.py` using the Azure AI Document Intelligence SDK (`prebuilt-invoice`).
- [ ] 2.3 Implement Blob storage utility for uploading and retrieving invoice files.
- [ ] 2.4 Create `POST /api/invoices/upload` endpoint to save files to Blob Storage and initiate async AI analysis.
- [ ] 2.5 Implement AI response parsing logic to populate `invoices` and `line_items` tables from the SDK JSON.

## Phase 3: Business Logic & Management API

- [ ] 3.1 Create `GET /api/invoices/{id}/status` endpoint to track extraction progress.
- [ ] 3.2 Create `PATCH /api/invoices/{id}/approve` endpoint to update invoice status (Approved/Rejected).
- [ ] 3.3 Implement audit logging in `backend/app/services/` to record every status change in `audit_logs`.
- [ ] 3.4 Create `GET /api/suppliers` endpoint to list all registered vendors.
- [ ] 3.5 Implement `RoleChecker` dependency in FastAPI to enforce RBAC on protected endpoints.

## Phase 4: Frontend Implementation

- [x] 4.1 Initialize React project with necessary dependencies (Axios, Tailwind CSS).
- [x] 4.2 Implement API integration hooks in `frontend/src/hooks/` for upload, status, and approval.
- [x] 4.3 Create the Upload component for invoice submission.
- [x] 4.4 Create the Invoice List view with filtering by status and supplier.
- [x] 4.5 Create the Invoice Detail/Approval view to review extracted data and submit a decision.

## Phase 5: Testing & Verification

- [ ] 5.1 Write unit tests for `ai_service.py` and business logic using Pytest and mocks.
- [ ] 5.2 Write integration tests for the API endpoints using TestContainers for PostgreSQL.
- [ ] 5.3 Implement a Playwright E2E test: Upload $\rightarrow$ Extract $\rightarrow$ Approve.
- [ ] 5.4 Perform a final security audit to ensure RBAC is correctly applied to all endpoints.
