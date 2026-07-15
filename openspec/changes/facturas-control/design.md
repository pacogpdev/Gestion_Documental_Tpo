# Design: facturas-control

## Technical Approach

The `facturas-control` system is designed as a full-stack application to automate the extraction and approval process of supplier invoices. The architecture leverages a React frontend for user interaction, a FastAPI backend for orchestration, Azure AI Document Intelligence for OCR and data extraction, and PostgreSQL for persistent storage. 

The strategy follows a decoupled service-oriented approach where the AI extraction is handled asynchronously to ensure system responsiveness during large file processing.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|------------|
| Backend Framework | FastAPI | Flask, Node.js | Superior performance (async), automatic OpenAPI docs, and strong typing with Pydantic. |
| Database | PostgreSQL | MongoDB, MySQL | Strong ACID compliance and relational structure essential for supplier-invoice-item hierarchies. |
| AI Extraction | Azure AI Document Intelligence (Prebuilt-Invoice) | Tesseract, Custom Model | Drastically reduces development time and provides high accuracy for common invoice formats out-of-the-box. |
| Identity Provider | Azure Entra ID | Auth0, Custom JWT | Seamless integration with Azure ecosystem and enterprise-grade security/RBAC management. |
| Frontend | React | Vue, Angular | Large ecosystem, component-based architecture for complex approval dashboards. |

## Data Flow

```
    [User/React] ──→ [FastAPI] ──→ [Azure Blob Storage]
                         │               │
                         │               └─→ [Azure AI Document Intelligence]
                         │                            │
                         │                            └─→ [FastAPI (Webhook/Polling)]
                         │                                      │
                         └──────────────→ [PostgreSQL] ←────────┘
```

1. **Upload**: User uploads invoice $\rightarrow$ FastAPI saves to Blob Storage $\rightarrow$ Initiates AI Analysis.
2. **Extraction**: Azure AI processes document $\rightarrow$ Returns structured JSON $\rightarrow$ FastAPI parses and saves to `Invoices` and `LineItems` tables.
3. **Approval**: User reviews data $\rightarrow$ FastAPI updates status $\rightarrow$ Record written to `AuditLogs`.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/main.py` | Create | Entry point and API router configuration. |
| `backend/app/models/` | Create | SQLAlchemy schemas for Suppliers, Invoices, LineItems, Users, Roles, AuditLogs. |
| `backend/app/api/endpoints/` | Create | Endpoints for `/upload`, `/status`, `/approve`. |
| `backend/app/services/ai_service.py` | Create | Logic for interacting with Azure AI Document Intelligence SDK. |
| `backend/app/core/security.py` | Create | Entra ID JWT validation and RBAC middleware. |
| `frontend/src/components/` | Create | UI for upload, invoice list, and approval forms. |
| `frontend/src/hooks/` | Create | API integration hooks. |

## Interfaces / Contracts

### Data Model (PostgreSQL)

```sql
-- Suppliers: Master data for vendors
CREATE TABLE suppliers (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255),
    address TEXT
);

-- Invoices: Header information
CREATE TABLE invoices (
    id UUID PRIMARY KEY,
    supplier_id UUID REFERENCES suppliers(id),
    invoice_number VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'Pending', -- Pending, Approved, Rejected
    file_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LineItems: Detailed breakdown per invoice
CREATE TABLE line_items (
    id UUID PRIMARY KEY,
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT,
    quantity DECIMAL(12, 2),
    unit_price DECIMAL(12, 2),
    total_price DECIMAL(12, 2)
);

-- RBAC: Users and Roles
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL -- Admin, Approver, Viewer
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255)
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);

-- AuditLogs: Track all status changes
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

| Method | Endpoint | Description | Auth Role |
|--------|----------|-------------|-----------|
| `POST` | `/api/invoices/upload` | Uploads file and triggers AI extraction | Approver, Admin |
| `GET` | `/api/invoices/{id}/status` | Checks if AI has finished extraction | Viewer, Approver, Admin |
| `PATCH` | `/api/invoices/{id}/approve` | Sets status to Approved/Rejected | Approver, Admin |
| `GET` | `/api/suppliers` | List all known suppliers | Viewer, Approver, Admin |

## AI Integration Detail

- **Model**: `prebuilt-invoice` (Azure AI Document Intelligence).
- **Strategy**: 
    1. **Asynchronous Pattern**: Use `begin_analyze_document` (SDK) to avoid request timeouts.
    2. **Data Mapping**: Map `fields` from the AI response (e.g., `VendorName`, `InvoiceTotal`) directly to `Invoice` and `LineItems` entities.
    3. **Fallback**: If confidence scores for key fields are $< 0.8$, flag the invoice for "Manual Review" in the UI.

## Security Design

- **Authentication**: Azure Entra ID using OAuth 2.0 / OpenID Connect.
- **Token Validation**: Backend validates JWTs issued by Entra ID using `JWKS` (JSON Web Key Sets).
- **RBAC**: 
    - The JWT will contain a `roles` claim.
    - FastAPI dependency `RoleChecker(["Admin", "Approver"])` will intercept requests to protected endpoints and verify the claim.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Business logic in `services/` | Pytest with mocked AI SDK and DB. |
| Integration | API $\rightarrow$ DB $\rightarrow$ AI | TestContainers for PostgreSQL and Azure AI Emulator/Mocks. |
| E2E | Full User Journey | Playwright: Upload $\rightarrow$ Wait for Extraction $\rightarrow$ Approve. |

## Migration / Rollout

No migration required for initial release. 
**Rollout**: 
1. Deploy Infrastructure (PostgreSQL, Blob Storage, Azure AI resource).
2. Deploy Backend (FastAPI) and Frontend (React).
3. Configure Entra ID App Registration and RBAC roles.

## Open Questions

- [ ] Should we support multi-currency conversion to a base currency?
- [ ] Do we need to integrate with an ERP for final approval sync?
