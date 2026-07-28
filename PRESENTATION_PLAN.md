# Presentation Plan — FacturasControl Project Defense

> Target audience: Expert software development tribunal
> Repo: https://github.com/pacogpdev/Gestion_Documental_Tpo
> Estimated slides: 18-20 | Estimated time: 20-25 minutes
> Code intelligence: CodeGraph index (653 nodes, 1,321 edges, 87 files) drives every code reference below — call paths, blast radius, and per-symbol test coverage are derived from the graph, not hand-traced.

---

## Sequential Index

| # | Slide | Focus | Code Reference (CodeGraph-verified) |
|---|-------|-------|----------------|
| 1 | Title & Overview | Project name, author, context | — |
| 2 | Problem Statement | What problem does this solve | — |
| 3 | Solution Overview | Architecture at a glance | [Architecture diagram prompt](#slide-3-prompt) |
| 4 | Tech Stack | Technologies with code evidence | [Stack slide prompt](#slide-4-prompt) |
| 5 | Project Structure | Directory tree + CodeGraph symbol map | [Structure slide prompt](#slide-5-prompt) |
| 6 | Backend: API Design | Endpoints table + blast radius per endpoint | [API slide prompt](#slide-6-prompt) |
| 7 | Backend: AI Extraction Pipeline | Azure Content Understanding + call path | [`ai_service.py`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/services/ai_service.py) |
| 8 | Backend: Blob Storage Service | Upload, delete, SAS + error taxonomy | [`storage_service.py`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/services/storage_service.py) |
| 9 | Backend: Multi-Engine DatabaseManager | SQLite → Azure SQL, GUID compatibility | [`database.py`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/core/database.py) / [`schemas.py`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/models/schemas.py) |
| 10 | Backend: Migration Script | Transactional SQLite → Azure SQL | [`migrate_to_azure_sql.py`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/migrate_to_azure_sql.py) |
| 11 | Frontend: Component Architecture | AppRoutes dynamic dispatch + React Query | [Frontend slide prompt](#slide-11-prompt) |
| 12 | Frontend: Approval Dashboard | Invoice list, PDF viewer, actions | [`ApprovalDashboard.tsx`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/frontend/src/pages/ApprovalDashboard.tsx) |
| 13 | Frontend: Supplier Stats Dashboard | Recharts, KPIs, dynamic currency | [`SupplierDashboard.tsx`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/frontend/src/pages/SupplierDashboard.tsx) |
| 14 | Security & RBAC | Entra ID JWT, RoleChecker, dev bypass + blast radius | [`security.py`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/core/security.py) |
| 15 | Testing Strategy (TDD) | RED → GREEN → REFACTOR + per-symbol coverage | [Testing slide prompt](#slide-15-prompt) |
| 16 | Deployment: Docker + Kubernetes | Dockerfiles, k8s manifests, kustomize | [`docker-compose.yml`](https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/docker-compose.yml) / [`k8s/`](https://github.com/pacogpdev/Gestion_Documental_Tpo/tree/main/k8s) |
| 17 | Challenges & Technical Decisions | Tradeoffs, CRITICAL findings from 4R review | [Challenges slide prompt](#slide-17-prompt) |
| 18 | Metrics & Results | Tests, performance, CodeGraph index stats | [Metrics slide prompt](#slide-18-prompt) |
| 19 | Future Improvements | Roadmap, open items | — |
| 20 | References & Q&A | GitHub repo, docs, contact | — |

---

## Slide Prompts

### Slide 1: Title & Overview

```
Create a professional title slide for a software project presentation:

Project: FacturasControl — Automated Invoice Extraction & Management System
Subtitle: Full-stack application with Azure AI, Blob Storage, SQL Server, and React
Context: Project defense presentation for an expert software development tribunal
Visual style: Clean, modern, dark accent on blue/indigo. Show a subtle invoice/document icon.
```

---

### Slide 2: Problem Statement

```
Create a slide explaining the business problem this project solves:

Problem: Manual invoice processing is slow, error-prone, and does not scale.
- Companies receive hundreds of supplier invoices as PDFs monthly
- Manual data entry: invoice number, date, amounts, line items, supplier info
- Risk of duplicates, human error, and delayed approvals
- No centralized storage for PDF documents
- No real-time analytics on supplier spending

Solution: An automated system that:
- Extracts invoice data from PDFs using Azure AI Content Understanding
- Persists PDFs to Azure Blob Storage with SAS token access
- Stores structured data in Azure SQL Server
- Provides a React dashboard for review, approval, and supplier analytics
- Enforces role-based access control (Admin, Approver, Clerk, Viewer)

Visual: Split layout — left side "Pain points" with red icons, right side "Solution" with green checkmarks.
```

---

### Slide 3: Solution Overview (Architecture Diagram)

<a id="slide-3-prompt"></a>

```
Create an architecture diagram slide for a full-stack invoice management system:

Layers (top to bottom):
1. CLIENT LAYER
   - React 18 + TypeScript frontend (Vite)
   - AppRoutes (routes/index.tsx:9) dynamically dispatches to 4 pages:
     ApprovalDashboard, UploadInvoice, Suppliers, SupplierDashboard
   - Navbar → useAuth (9 callers across the frontend — auth hub)
   - React Query (stale-while-revalidate cache, 30s staleTime)
   - Tailwind CSS + Recharts 3

2. API LAYER
   - FastAPI 0.139 backend (Python 3.12)
   - 3 routers: invoices.py, suppliers.py, users.py
   - 13 route nodes indexed by CodeGraph
   - JWT auth (Azure Entra ID) with dev bypass
   - RoleChecker RBAC middleware (get_current_user: 6 callers, RoleChecker: 2 callers)

3. SERVICE LAYER
   - AI Extraction Service (Azure Content Understanding SDK)
     extract_invoice_data (ai_service.py:128) — 10 callers, hub symbol
   - BlobStorageService (upload, delete, SAS token generation)
     StorageUploadError / StorageConfigError — 5 callers, typed error taxonomy
   - Audit logging

4. DATA LAYER
   - SQLAlchemy 2.0 ORM with multi-engine support
   - SQLite (development) / Azure SQL Server (production)
   - GUID TypeDecorator: UNIQUEIDENTIFIER (MSSQL) / CHAR(36) (SQLite) / PG_UUID (PostgreSQL)
   - 7 tables: suppliers, invoices, line_items, users, roles, user_roles, audit_logs
   - UniqueConstraint('supplier_id', 'invoice_number') as race-condition safety net

5. CLOUD LAYER
   - Azure AI Content Understanding (prebuilt-invoice analyzer)
   - Azure Blob Storage (pedroortizst / facturas-proveedores container)
   - Azure SQL Server (pedro-ortiz-sql / pedro-ortiz-db_2)
   - Azure Entra ID (JWT authentication)

6. DEPLOYMENT LAYER
   - Docker (Dockerfile.backend + Dockerfile.frontend + nginx)
   - Kubernetes (kustomize: base + dev overlay + prod overlay)
   - Ingress controller with host-based routing

Data flow arrows (CodeGraph-verified call path):
  Upload PDF → upload_invoice (invoices.py:132) → extract_invoice_data (ai_service.py:128)
  → _extract_currency / _extract_amount helpers → Blob Storage upload → Azure SQL → React Dashboard
  Dashboard → API (SAS token URLs via _sas_url_for_invoice) → Browser opens PDF in new tab

Visual: Layered diagram with distinct colors per layer, data flow arrows, Azure cloud icons.
```

---

### Slide 4: Tech Stack

<a id="slide-4-prompt"></a>

```
Create a tech stack slide with code evidence for an expert tribunal:

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| Backend | FastAPI | 0.139.0 | Async REST API, auto-docs (Swagger) |
| ORM | SQLAlchemy | 2.0.41 | Multi-engine (SQLite/MSSQL), GUID compatibility |
| Auth | python-jose + Entra ID | 3.5.0 | JWT validation, RBAC |
| AI | Azure Content Understanding SDK | 1.1.0 | Prebuilt-invoice analyzer, field extraction |
| Storage | azure-storage-blob | 12.25.1 | PDF persistence, SAS token URLs |
| DB Driver | pymssql | 2.3.2 | Azure SQL Server connection |
| Frontend | React 18 + TypeScript | 18.2 | Component-based, type-safe |
| Build | Vite 5 | 5.0.11 | Fast HMR, ESM, tree-shaking |
| Charts | Recharts 3 | 3.9.2 | AreaChart, PieChart, BarChart |
| Cache | @tanstack/react-query | 5.101 | Stale-while-revalidate, mutation invalidation |
| Testing | pytest 9 + Vitest 1 | — | Strict TDD, 86 backend + 53 frontend tests |
| Deploy | Docker + Kubernetes | — | kustomize overlays (dev/prod) |
| Code Intel | CodeGraph | — | SQLite symbol graph, 653 nodes / 1,321 edges |

Code snippet to include (from backend/app/core/database.py):
```python
class DatabaseManager:
    def __init__(self, db_url: str | None = None):
        self.db_url = settings.DATABASE_URL if db_url is None else db_url
        engine_options = {}
        if self.db_url.startswith("sqlite"):
            engine_options["connect_args"] = {"check_same_thread": False}
        self._engine = create_engine(self.db_url, **engine_options)
```

Visual: Table with technology icons, code snippet in a dark code block on the right.
```

---

### Slide 5: Project Structure (CodeGraph Symbol Map)

<a id="slide-5-prompt"></a>

```
Create a directory tree slide showing the project structure, enriched with CodeGraph
symbol counts per area (graph-derived, not hand-counted):

CodeGraph index summary (top of slide):
  87 files | 653 nodes | 1,321 edges | 2.19 MB SQLite | WAL journal
  Languages: 39 Python (backend) · 14 TSX + 13 TS + 2 JS (frontend) · 19 YAML (skills/config)
  Node kinds: 276 imports · 181 functions · 68 files · 29 classes · 27 variables
              23 methods · 19 constants · 13 interfaces · 13 routes · 4 type aliases

Directory tree with per-folder symbol evidence:
```
PROYECTO_FACTURAS_PROVEEDORES/
├── backend/                              # 39 Python files indexed
│   ├── app/
│   │   ├── api/endpoints/                # 3 routers, 13 route nodes
│   │   │   ├── invoices.py               # upload_invoice, list_invoices, delete_invoice,
│   │   │   │                             #   update_invoice_status, _resolve_supplier,
│   │   │   │                             #   _normalize_invoice_number, _cleanup_uploaded_blob,
│   │   │   │                             #   _sas_url_for_invoice
│   │   │   ├── suppliers.py             # CRUD + get_supplier_stats + delete with 409 guard
│   │   │   └── users.py                 # get_current_user_profile
│   │   ├── core/
│   │   │   ├── config.py                # Pydantic settings (env-aware)
│   │   │   ├── database.py              # DatabaseManager (multi-engine)
│   │   │   └── security.py             # get_current_user (6 callers),
│   │   │                               #   RoleChecker (2 callers), SecurityService,
│   │   │                               #   OptionalHTTPBearer, DEV_USER bypass
│   │   ├── models/schemas.py           # 6 SQLAlchemy models + 8 Pydantic responses +
│   │   │                               #   GUID TypeDecorator (3 dialects)
│   │   ├── services/
│   │   │   ├── ai_service.py           # extract_invoice_data (10 callers — hub),
│   │   │   │                           #   get_ai_client, _extract_dev_mode,
│   │   │   │                           #   _extract_amount, _extract_currency,
│   │   │   │                           #   _get_value, _detect_mime_type
│   │   │   └── storage_service.py      # BlobStorageService,
│   │   │                               #   StorageUploadError (5 callers),
│   │   │                               #   StorageConfigError
│   │   └── main.py                     # FastAPI app + CORS + health endpoint
│   ├── tests/                          # 86 tests (pytest, strict TDD)
│   ├── seed_db.py                     # Engine-neutral, idempotent seeder
│   ├── migrate_to_azure_sql.py        # Transactional SQLite → Azure SQL migration
│   ├── requirements.txt              # All deps pinned to latest
│   ├── mypy.ini                       # SQLAlchemy type plugin
│   └── pytest.ini                     # Warning filters
├── frontend/                           # 29 TS/TSX/JS files indexed
│   ├── src/
│   │   ├── pages/                     # 4 page components + co-located tests + MSW
│   │   │   ├── ApprovalDashboard.tsx   # Invoice list, PDF viewer, PaginationBar
│   │   │   ├── UploadInvoice.tsx       # PDF upload + extracted data review
│   │   │   ├── Suppliers.tsx           # CRUD + delete + stats icon
│   │   │   └── SupplierDashboard.tsx   # Recharts stats: KpiCard, ChartCard, EmptyChart
│   │   ├── routes/index.tsx           # AppRoutes — single source of routing truth,
│   │   │                             #   dynamic dispatch to 4 pages
│   │   ├── api/client.ts             # Axios + JWT interceptor
│   │   ├── hooks/useAuth.ts          # useAuth — 9 callers (frontend auth hub)
│   │   ├── components/Navbar.tsx      # Navigation + role visibility
│   │   └── test-utils.tsx            # RTL + React Query test wrapper
│   ├── Dockerfile.frontend
│   └── package.json
├── Dockerfile.backend
├── docker-compose.yml
├── nginx.conf
├── k8s/                               # Kubernetes manifests
│   ├── base/                          # Namespace, deployments, services, ingress
│   └── overlays/
│       ├── dev/                       # PostgreSQL statefulset + db-init
│       └── prod/                      # Azure SQL configmap + db-init
├── skills/                           # 8 project-specific AI skills
├── openspec/                         # SDD specs + archived changes
└── README.md
```

Visual: Clean tree diagram with color-coded sections (backend=blue, frontend=green, infra=orange).
Overlay the CodeGraph symbol counts as badges on each folder.
```

---

### Slide 6: Backend API Design (Blast Radius per Endpoint)

<a id="slide-6-prompt"></a>

```
Create an API endpoints slide for a FastAPI invoice management system, enriched with
CodeGraph blast radius (callers + covering tests) per endpoint:

| Method | Endpoint | Description | Roles | CodeGraph blast radius |
|--------|----------|-------------|-------|------------------------|
| POST | /api/invoices/upload | Upload PDF → AI extraction → Blob → DB | Clerk, Admin | upload_invoice (invoices.py:132), 0 internal callers (HTTP entry), tests: test_invoices.py |
| GET | /api/invoices | List invoices with SAS token PDF URLs | All | list_invoices, calls _sas_url_for_invoice per invoice |
| PATCH | /api/invoices/{id}/approve | Approve/Reject invoice | Approver, Admin | update_invoice_status |
| DELETE | /api/invoices/{id} | Delete invoice + line items + PDF | Clerk, Admin | delete_invoice, calls _cleanup_uploaded_blob (best-effort) |
| GET | /api/suppliers | List suppliers | All | via get_current_user |
| POST | /api/suppliers | Create supplier | Admin | RoleChecker guard |
| PUT | /api/suppliers/{id} | Update supplier | Admin | RoleChecker guard |
| DELETE | /api/suppliers/{id} | Delete supplier (409 if invoices exist) | Admin | delete_supplier, invoice_count guard |
| GET | /api/suppliers/{id}/stats | 12-month aggregation, KPIs | Admin, Approver | get_supplier_stats |
| GET | /api/users/me | Authenticated user profile | All | get_current_user_profile (users.py:14) |

Call path verified by CodeGraph (upload flow):
  upload_invoice (invoices.py:132)
    → extract_invoice_data (ai_service.py:128)   [10 callers — hub]
      → _extract_currency (ai_service.py:94)
      → _extract_amount (ai_service.py:75)
      → _get_value (ai_service.py:55)
    → _resolve_supplier (invoices.py:22)
    → _normalize_invoice_number (invoices.py:57)
    → storage.upload_pdf → StorageUploadError (5 callers)
    → _cleanup_uploaded_blob (invoices.py:89) [on failure]

Code snippet to include (from backend/app/api/endpoints/invoices.py — upload flow,
simplified; full source is 105 lines with 5 numbered edge cases):
```python
@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(RoleChecker(["Clerk", "Admin"])),
    storage: BlobStorageService = Depends(get_storage_service),
):
    if storage is None:
        raise HTTPException(status_code=503, detail="Blob storage is unavailable")
    content = await file.read()
    extraction_result = await extract_invoice_data(content, filename=file.filename)
    supplier, supplier_name = _resolve_supplier(db, extraction_result)
    invoice_number = _normalize_invoice_number(extraction_result.get("invoice_number"))
    # ... duplicate check (edge case #2: replace if Rejected, else 409) ...
    invoice_id = uuid.uuid4()
    blob_url = storage.upload_pdf(content, str(supplier.id), str(invoice_id))
    # ... DB persist + commit + IntegrityError cleanup (edge case #3) ...
```

Visual: REST table on left, code snippet on right, arrow showing upload flow with
CodeGraph call-path annotations.

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/api/endpoints/invoices.py
```

---

### Slide 7: AI Extraction Pipeline

```
Create a slide showing the Azure AI Content Understanding extraction pipeline,
with the CodeGraph-verified call path and field mapping:

CodeGraph call path:
  extract_invoice_data (ai_service.py:128)           [10 callers — hub symbol]
    → get_ai_client (ai_service.py:11)                [creds resolution]
    → _extract_dev_mode (ai_service.py:26)            [dev fallback]
    → _detect_mime_type (ai_service.py:108)           [format dispatch]
    → client.begin_analyze(analyzer_id="prebuilt-invoice")
    → _extract_amount (ai_service.py:75)              [NumberField | ObjectField]
    → _extract_currency (ai_service.py:94)            [CurrencyCode sub-field]
    → _get_value (ai_service.py:55)                   [string | number | date | int]

Pipeline:
  PDF bytes → AnalysisInput(data, mime_type) → client.begin_analyze("prebuilt-invoice")
  → poller.result() → fields dict → extracted data

Key fields extracted (with helper dispatch):
- InvoiceId → _get_value → invoice_number
- InvoiceDate → value_date → date
- TotalAmount → _extract_amount + _extract_currency (handles both direct number and
                {Amount, CurrencyCode} object — Azure schema is non-uniform)
- TotalTaxAmount → 3-level fallback chain:
    1. TotalTaxAmount / TotalTax direct
    2. TaxDetails[] array iteration (sum Amount sub-fields)
    3. Estimate: TotalAmount - SubtotalAmount
- VendorName → value_string with \n sanitize → supplier_name
- VendorTaxId → _get_value → tax_id
- LineItems[] / Items[] → description, quantity, unit_price, total_price
  (legacy "Items"/"Amount" + new "LineItems"/"TotalAmount" both supported)

Code snippet (from backend/app/services/ai_service.py):
```python
async def extract_invoice_data(file_stream, filename="invoice.pdf"):
    client = get_ai_client()
    if client is None:
        return _extract_dev_mode(filename)  # dev fallback — filename-derived mock

    file_bytes = file_stream.read() if hasattr(file_stream, 'read') else file_stream
    mime_type = _detect_mime_type(filename)
    poller = client.begin_analyze(
        analyzer_id="prebuilt-invoice",
        inputs=[AnalysisInput(data=file_bytes, mime_type=mime_type)],
    )
    result = poller.result()
    if not result.contents:
        # Azure did not detect an invoice → dev-mode fallback
        return _extract_dev_mode(filename)
    fields = result.contents[0].fields or {}
    return {
        "invoice_number": _get_value(fields.get("InvoiceId")),
        "total_amount": _extract_amount(fields.get("TotalAmount")),
        # ... full field mapping ...
    }
```

Dev mode fallback: _extract_dev_mode derives supplier_name from filename
("factura_acme.pdf" → "Acme") and generates uuid-based tax_id/invoice_number
so each test upload feels unique and verifiable — not a static mock.

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/services/ai_service.py
Visual: Pipeline diagram (PDF → Azure AI → dict → DB), code snippet below,
helper dispatch tree on the right.
```

---

### Slide 8: Blob Storage Service

```
Create a slide showing the Azure Blob Storage integration, with CodeGraph-verified
error taxonomy and blast radius:

Typed error classes (storage_service.py:19-24):
- StorageConfigError — "Blob Storage cannot be configured safely" (initialization failure)
- StorageUploadError — "Azure rejects a blob operation required for upload" (runtime)

Blast radius (CodeGraph):
- StorageUploadError: 5 callers (invoices.py + storage_service.py)
  tests: test_invoices.py + test_storage_service.py ✅
- StorageConfigError: 5 callers
  tests: test_storage_service.py ✅

Key capabilities:
- Upload PDF with content_type="application/pdf"
- Blob naming: {supplier_id}/{invoice_id}/{uuid}.pdf
  (invoice_id assigned BEFORE upload so blob is namespaced by the persisted ID)
- Generate read-only SAS token URLs (1 hour expiry) for frontend access
- Best-effort blob deletion on invoice delete — moved AFTER db.commit() (4R fix)
- _cleanup_uploaded_blob (invoices.py:89): compensatory cleanup on DB failure
  to prevent orphaned blobs in Azure

Code snippet (from backend/app/services/storage_service.py — SAS generation):
```python
def get_blob_sas_url(self, blob_name: str, expiry_hours: int = 1) -> str:
    sas_token = generate_blob_sas(
        account_name=self.account_name,
        container_name=self.container_name,
        blob_name=blob_name,
        account_key=self.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
    )
    return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
```

Compensatory cleanup pattern (invoices.py:89):
```python
def _cleanup_uploaded_blob(blob_url, storage):
    # Skip legacy /uploads/ paths and non-Azure URLs
    if (storage is None or not blob_url
        or blob_url.startswith("/uploads/")
        or not blob_url.startswith("https://")):
        return
    try:
        blob_name = _blob_name_from_url(blob_url, storage)
        if blob_name:
            storage.delete_blob(blob_name)
    except Exception as error:
        logger.warning("Unable to clean up invoice blob %s: %s", blob_url, error)
```

Critical fix from 4R review: blob deletion moved AFTER db.commit() to prevent
orphaned invoices with dead file_url.

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/services/storage_service.py
Visual: Diagram showing upload flow and SAS token flow, error taxonomy box, code block.
```

---

### Slide 9: Multi-Engine DatabaseManager + GUID

```
Create a slide showing the multi-engine database architecture:

Challenge: Support SQLite (dev) and Azure SQL Server (prod) with the same ORM models.

Solution:
1. DatabaseManager selects engine from DATABASE_URL (no silent fallback)
2. SQLite gets check_same_thread=False; MSSQL gets no special args
3. GUID TypeDecorator maps to 3 dialects:
   - PostgreSQL → PG_UUID (native)
   - MSSQL → UNIQUEIDENTIFIER (native SQL Server)
   - SQLite/others → CHAR(36) (stringified hex)

CodeGraph-verified schema model (schemas.py):
- 6 SQLAlchemy models: Supplier, Invoice, LineItem, User, Role, AuditLog
- 1 many-to-many link table: user_roles (users ↔ roles)
- UniqueConstraint('supplier_id', 'invoice_number', name='uq_supplier_invoice')
  — DB-level race-condition safety net (complements the app-level check in upload_invoice)
- 8 Pydantic response models (camelCase for frontend): InvoiceResponse,
  MonthlyAmount, TopLineItem, StatusDistribution, TopInvoice, SupplierStatsResponse
- Invoice.line_items relationship uses cascade="all, delete-orphan"
- LineItem.invoice_id FK uses ondelete="CASCADE"

Code snippet (from backend/app/models/schemas.py — GUID TypeDecorator):
```python
class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        elif dialect.name == 'mssql':
            return UNIQUEIDENTIFIER()
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        elif dialect.name == 'mssql':
            return str(value if isinstance(value, uuid.UUID) else uuid.UUID(value))
        else:
            return "%.32x" % (value if isinstance(value, uuid.UUID) else uuid.UUID(value)).int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value
```

Code snippet (from backend/app/core/database.py):
```python
class DatabaseManager:
    def __init__(self, db_url: str | None = None):
        self.db_url = settings.DATABASE_URL if db_url is None else db_url
        engine_options = {}
        if self.db_url.startswith("sqlite"):
            engine_options["connect_args"] = {"check_same_thread": False}
        self._engine = create_engine(self.db_url, **engine_options)
```

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/core/database.py
Visual: Side-by-side: SQLite (dev) vs Azure SQL (prod), GUID mapping table with 3 dialects.
```

---

### Slide 10: Migration Script

```
Create a slide showing the SQLite → Azure SQL migration:

Transaction flow:
  Source SQLite → create_all(target) → copy in FK order → commit or rollback

Migration order (FK dependencies, verified from migrate_to_azure_sql.py):
  roles → users → suppliers → invoices → user_roles → line_items → audit_logs

Critical fix from 4R review: source schema validation BEFORE create_all.
  If any table is missing in source → ValueError → abort (not silent success).

Code snippet (from backend/migrate_to_azure_sql.py):
```python
TABLE_MIGRATION_ORDER = (
    "roles", "users", "suppliers", "invoices",
    "user_roles", "line_items", "audit_logs",
)

def migrate_database(source_manager, target_manager):
    source_tables = set(inspect(source_manager.engine).get_table_names())
    missing = [t for t in TABLE_MIGRATION_ORDER if t not in source_tables]
    if missing:
        raise ValueError(f"Source database is missing required tables: {missing}")

    Base.metadata.create_all(bind=target_manager.engine)
    with target_session.begin():
        for table_name in TABLE_MIGRATION_ORDER:
            _copy_table(source_session, target_session, table, source_tables, progress_callback)
```

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/migrate_to_azure_sql.py
Visual: Arrow diagram: SQLite → validate → create_all → copy (7 tables) → commit.
```

---

### Slide 11: Frontend Architecture (AppRoutes Dynamic Dispatch)

<a id="slide-11-prompt"></a>

```
Create a slide showing the frontend component architecture, with CodeGraph-verified
dynamic dispatch and auth hub:

Routing (react-router-dom v6) — single source of truth: AppRoutes (routes/index.tsx:9):
CodeGraph dynamic-dispatch map:
  AppRoutes → Navbar          [renders <Navbar>]
  AppRoutes → ApprovalDashboard  [route /dashboard]
  AppRoutes → UploadInvoice     [route /upload]
  AppRoutes → Suppliers         [route /suppliers]
  AppRoutes → SupplierDashboard [route /suppliers/:id/dashboard]
  / → redirect to /dashboard
  /* → "Page not found"

Auth hub: useAuth (hooks/useAuth.ts:20) — 9 callers across the frontend
  Callers: Navbar, SupplierDashboard, Suppliers, UploadInvoice
  Exposes: { user, loading, login, logout, hasRole }
  localStorage-backed (user_profile + auth_token)

Navbar auto-bootstrap (Navbar.tsx:6):
  On mount, if no stored user → GET /users/me → login(profile, 'dev-token')
  This is the dev-mode handshake that populates the auth context.

State management:
  - React Query (useQuery + invalidateQueries)
    - ['invoices'] → cached, stale-while-revalidate
    - ['suppliers'] → cached, mutation invalidation
    - ['supplier-stats', id] → per-supplier cache, enabled: !!id && canViewStats
  - useAuth hook → role-based UI (hasRole('Admin'))

API client:
  - Axios with JWT interceptor (Authorization header)
  - Dev mode: fake JWT token, auto-fetch /users/me via Navbar

Key pattern — cache prevents empty table on remount:
  BEFORE: Navigate to /upload → back to /dashboard → "Loading..." → empty table
  AFTER:  Navigate to /upload → back to /dashboard → cached data shows immediately → refetch in background

Code snippet (routes/index.tsx — full routing source, 27 lines):
```tsx
const AppRoutes: React.FC = () => (
  <Router>
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<ApprovalDashboard />} />
          <Route path="/upload" element={<UploadInvoice />} />
          <Route path="/suppliers" element={<Suppliers />} />
          <Route path="/suppliers/:id/dashboard" element={<SupplierDashboard />} />
          <Route path="*" element={<div className="text-center p-10 text-slate-500">Page not found</div>} />
        </Routes>
      </main>
    </div>
  </Router>
);
```

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/tree/main/frontend/src
Visual: Component tree diagram with AppRoutes as root, routing arrows,
React Query cache boxes, useAuth hub badge with "9 callers".
```

---

### Slide 12: Approval Dashboard

```
Create a slide showing the Approval Dashboard features:

Features:
- Invoice list with: number, supplier, date, amount, currency, status
- Status filters: All / Pending / Approved / Rejected (with count badges)
- Search by invoice number or supplier name
- Sort by date or amount (asc/desc, visible indicators)
- Pagination: 15 per page (top + bottom controls) — PaginationBar component (line 352)
- PDF viewer icon: opens Azure Blob URL with SAS token in new tab
  (uses _sas_url_for_invoice from invoices.py — per-invoice try/except)
- Actions: Approve/Reject (Approver+), Delete (Clerk+) with blob cleanup

Code snippet (from ApprovalDashboard.tsx — React Query + mutation invalidation):
```tsx
const { data: invoices = [], isLoading: loading } = useQuery({
  queryKey: ['invoices'],
  queryFn: async () => {
    const response = await apiClient.get('/invoices');
    return response.data;
  },
});

const handleDelete = async (id: string) => {
  await apiClient.delete(`/invoices/${id}`);
  queryClient.invalidateQueries({ queryKey: ['invoices'] });
};
```

CodeGraph blast radius:
- ApprovalDashboard.tsx — PaginationBar sub-component (line 352), Invoice interface (line 5)
- Backend pairing: list_invoices (invoices.py) calls _sas_url_for_invoice per row;
  one SAS failure is logged and skipped (dashboard stays usable)

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/frontend/src/pages/ApprovalDashboard.tsx
Visual: Screenshot mockup of dashboard table with icons, code snippet.
```

---

### Slide 13: Supplier Stats Dashboard

```
Create a slide showing the Supplier Statistics Dashboard, with CodeGraph-verified
component tree and normalization adapter:

CodeGraph dynamic-dispatch tree:
  SupplierDashboard (SupplierDashboard.tsx:112)   [4 callers, tested ✅]
    → KpiCard       [renders 5 instances]
    → ChartCard     [wraps Recharts containers]
    → EmptyChart    [empty-state fallback]

Blast radius:
- SupplierDashboard: 4 callers in routes/index.tsx
  tests: SupplierDashboard.test.tsx + routes/index.test.tsx ✅
- normalizeStats adapter (line 92): handles 3 backend field-name variants
  (annualTotal | annualAccumulated | totalAmount) — resilience to API evolution

Features:
- KPI Cards (5): Annual total, % of total, Average invoice, Invoice count, Top invoice
  - Colored top border accent + circular icon badge (KPI_COLORS palette)
- Monthly billing chart: Recharts AreaChart with linearGradient fill, currency-aware
- Supplier share: Donut PieChart with % label on each slice
- Status distribution: Pie chart with count labels (Approved: N)
- Top 10 line items: Horizontal BarChart with truncated descriptions + amount labels
- Dynamic currency: EUR (€), USD ($), GBP (£) from API response
- Empty states: EmptyChart component for monthly/items when no data
- Error state: per-invoice error message extraction (response.data.detail)
- Access guard: canViewStats = hasRole('Admin') || hasRole('Approver')
  → if not, renders role="alert" accessibility message

Code snippet (from SupplierDashboard.tsx — currency-aware formatting + adapter):
```tsx
const CURRENCY_SYMBOLS: Record<string, string> = { EUR: '€', USD: '$', GBP: '£' };
const currencySymbol = (currency: string) => CURRENCY_SYMBOLS[currency] || currency + ' ';
const formatMoney = (amount: number, currency: string) =>
  `${currencySymbol(currency)}${amount.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;

// Adapter: handles 3 backend field-name variants for annual total
const normalizeStats = (response: SupplierStatsApiResponse): SupplierStats => ({
  supplierName: response.supplierName || 'Supplier',
  annualTotal: response.annualTotal ?? response.annualAccumulated ?? response.totalAmount ?? 0,
  annualPercentage: response.annualPercentage || 0,
  grandTotal: response.grandTotal ?? response.grandTotalAllSuppliers ?? 0,
  // ... full normalization ...
});

const { data: stats } = useQuery({
  queryKey: ['supplier-stats', id],
  queryFn: async () => {
    const response = await apiClient.get(`/suppliers/${id}/stats`);
    return normalizeStats(response.data);
  },
  enabled: !!id && canViewStats,
});
```

Backend pairing (suppliers.py):
```python
@router.get("/{id}/stats")
def get_supplier_stats(
    id: uuid.UUID,
    db = Depends(get_db),
    _ = Depends(RoleChecker(["Admin", "Approver"]))
):
    # Trailing 12-month aggregation, % of all suppliers, top 10 items, status distribution
    # Returns SupplierStatsResponse (schemas.py:152) — 11 fields
```

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/frontend/src/pages/SupplierDashboard.tsx
Visual: Dashboard mockup with KPI cards + charts grid layout, component tree on the right.
```

---

### Slide 14: Security & RBAC (Blast Radius)

```
Create a slide showing the security architecture, with CodeGraph-verified blast radius
for each auth primitive:

Authentication (backend/app/core/security.py):
- Azure Entra ID JWT validation (python-jose, RS256)
- SecurityService._get_jwks: caches JWKS keys from Microsoft (key rotation support)
- validate_token: header.kid → JWKS match → jwk.construct → jwt.decode with
  audience=ENTRA_ID_CLIENT_ID, issuer=sts.windows.net/{TENANT_ID}/
- OptionalHTTPBearer: when ENTRA_ID_JWKS_URL is empty → returns None (dev bypass)
- DEV_USER: mock user with Admin role for local development

Authorization (RoleChecker):
- 4 roles: Admin, Approver, Clerk, Viewer
- RoleChecker dependency: Depends(RoleChecker(["Admin", "Approver"]))
- Per-endpoint enforcement (backend, not just frontend)

CodeGraph blast radius (security primitives):
| Primitive | Location | Callers | Tests |
|-----------|----------|---------|-------|
| get_current_user | security.py:72 | 6 (invoices, suppliers, users) | test_supplier_stats.py, conftest.py ✅ |
| RoleChecker | security.py:87 | 2 (invoices, suppliers) | ⚠️ no direct test |
| useAuth (frontend) | hooks/useAuth.ts:20 | 9 (Navbar, SupplierDashboard, Suppliers, UploadInvoice) | useAuth.test.ts ✅ |

Code snippet (from backend/app/core/security.py):
```python
class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: dict = Depends(get_current_user)):
        # DEVELOPMENT MODE: Skip role check when Azure is not configured
        if not settings.ENTRA_ID_JWKS_URL:
            return user
        user_roles = user.get("roles", [])
        if not any(role in self.allowed_roles for role in user_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
```

Frontend: useAuth hook with hasRole() for conditional rendering.

Security findings from 4R review:
- SAS tokens are read-only, 1-hour expiry (no write access from frontend)
- No secrets in code — all via .env (gitignored)
- Blob container is PRIVATE (SAS required for access)

⚠️ Honest finding surfaced by CodeGraph (worth mentioning to the tribunal):
- Frontend UserRole type (useAuth.ts:3) = 'Admin' | 'Approver' | 'Viewer'
- Backend RoleChecker allows 'Clerk' on POST /upload and DELETE /invoices/{id}
- The frontend type omits 'Clerk' — a Clerk logging in via Entra ID would not see
  the Upload/Suppliers nav links even though the backend authorizes them.
  This is a type-consistency gap, not a security hole (backend still enforces),
  but it shows the value of cross-layer static analysis.

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/backend/app/core/security.py
Visual: Role permission matrix table, JWT flow diagram, blast-radius badges.
```

---

### Slide 15: Testing Strategy (TDD + Per-Symbol Coverage)

<a id="slide-15-prompt"></a>

```
Create a slide showing the TDD testing strategy, enriched with CodeGraph per-symbol
test coverage (graph-derived, not hand-traced):

Methodology: Strict TDD — RED → GREEN → REFACTOR
- Every feature implemented test-first
- 86 backend tests (pytest) + 53 frontend tests (Vitest + RTL + MSW)
- Total: 139 tests, 0 failures

Backend testing layers:
- Unit: BlobStorageService (mocked Azure), AI extraction helpers
- Integration: API endpoints with TestClient + test SQLite
- Quality: mypy (0 errors), pytest.ini (0 warnings)

Frontend testing layers:
- Component: React Testing Library (RTL)
- API mocking: MSW (Mock Service Worker)
- Cache behavior: React Query test utilities (isolated QueryClient per test)

CodeGraph per-symbol test coverage (honest report — strengths AND gaps):

✅ Covered symbols:
| Symbol | File:line | Tests |
|--------|-----------|-------|
| extract_invoice_data | ai_service.py:128 | test_ai_service.py |
| StorageUploadError | storage_service.py:23 | test_invoices.py + test_storage_service.py |
| get_current_user | security.py:72 | test_supplier_stats.py + conftest.py |
| User (backend model) | schemas.py:99 | conftest.py + test_migrate_to_azure_sql.py + test_seed_db.py |
| useAuth (frontend) | useAuth.ts:20 | useAuth.test.ts |
| SupplierDashboard | SupplierDashboard.tsx:112 | SupplierDashboard.test.tsx + routes/index.test.tsx |
| uploadInvoiceHandlers | UploadInvoice.handlers.ts:19 | UploadInvoice.test.tsx |

⚠️ Gaps surfaced by CodeGraph (call them out — tribunals value honesty):
| Symbol | File:line | Issue |
|--------|-----------|-------|
| RoleChecker | security.py:87 | No direct test — only exercised transitively |
| UploadInvoice | UploadInvoice.tsx:24 | No direct component test — only MSW handlers tested |
| Suppliers | Suppliers.tsx:15 | No covering test found |
| Navbar | Navbar.tsx:6 | No covering test found |
| User (frontend) | useAuth.ts:5 | Interface, no direct test |

Coverage highlights (behaviors verified):
- Upload flow: extraction → blob upload → DB persistence → 503 on failure
- Delete flow: DB commit first → blob cleanup (best-effort, compensatory)
- SAS generation: per-invoice try/except (one failure doesn't break list)
- Supplier stats: 12-month aggregation, percentage, top items, empty state
- React Query: cached data renders on remount (no "Loading..." flash)

Code snippet (test example from backend/tests/api/test_invoices.py):
```python
def test_delete_invoice_calls_blob_cleanup_after_commit(db_session, mock_storage):
    invoice = create_test_invoice(db_session, file_url="https://...blob.pdf")
    response = client.delete(f"/api/invoices/{invoice.id}")
    assert response.status_code == 200
    db_session.commit.assert_called_before(mock_storage.delete_blob)
```

Visual: TDD cycle diagram (RED → GREEN → REFACTOR), test count badges,
two-column coverage table (green ✅ / amber ⚠️).

GitHub: https://github.com/pacogpdev/Gestion_Documental_Tpo/tree/main/backend/tests
```

---

### Slide 16: Deployment (Docker + Kubernetes)

```
Create a slide showing the Docker + Kubernetes deployment:

Docker:
- Dockerfile.backend: Python 3.12 slim + pip install + uvicorn
- Dockerfile.frontend: Node 20 + npm build + nginx serve (multi-stage)
- docker-compose.yml: backend + frontend + postgres (dev)
- nginx.conf: reverse proxy /api/* → backend, /* → frontend

Kubernetes (kustomize):
- Base: namespace, deployments, services, configmap, secret, ingress
- Dev overlay: PostgreSQL statefulset + db-init job
- Prod overlay: Azure SQL configmap + db-init job

Health checks:
- /health endpoint for k8s liveness/readiness probes

Config (container-aware):
- All settings via environment variables (no .env file in containers)
- ConfigMap for non-sensitive, Secret for credentials

GitHub:
- Dockerfiles: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/Dockerfile.backend
- K8s: https://github.com/pacogpdev/Gestion_Documental_Tpo/tree/main/k8s
- Compose: https://github.com/pacogpdev/Gestion_Documental_Tpo/blob/main/docker-compose.yml

Visual: K8s deployment diagram (pods, services, ingress), Docker layers.
```

---

### Slide 17: Challenges & Technical Decisions

<a id="slide-17-prompt"></a>

```
Create a slide showing key technical challenges and decisions, with CodeGraph-verified
evidence anchors:

| Challenge | Decision | Rationale | CodeGraph evidence |
|-----------|----------|-----------|--------------------|
| Blob vs DB transaction | Delete blob AFTER db.commit() | Prevents orphaned invoice with dead file_url (4R) | _cleanup_uploaded_blob (invoices.py:89), 1 caller |
| Private blob container | SAS token URLs (1hr, read-only) | Secure frontend PDF access without storage creds | _sas_url_for_invoice (invoices.py:110), per-invoice try/except |
| SAS failure breaks list | Per-invoice try/except | One failure doesn't block dashboard | _sas_url_for_invoice guards /uploads/ + non-https |
| Multi-engine DB | DATABASE_URL selector | SQLite dev, Azure SQL prod, no silent fallback | DatabaseManager (database.py) |
| GUID compatibility | TypeDecorator (3 dialects) | Native types per engine, UUID round-trip | GUID (schemas.py:11), PG_UUID/UNIQUEIDENTIFIER/CHAR(36) |
| Migration data loss | Source schema validation | Missing tables → abort (not silent success) | migrate_database raises ValueError on missing |
| Records disappear on navigate | React Query cache | Stale-while-revalidate, 30s staleTime | useQuery(['invoices']) in ApprovalDashboard |
| Currency display | Dynamic from API response | EUR/USD/GBP (not hardcoded €) | CURRENCY_SYMBOLS + currencySymbol (SupplierDashboard.tsx:77-79) |
| Code review quality | 4R adversarial review | Risk + Resilience + Readability + Reliability | 3 CRITICAL findings found and fixed |
| Duplicate invoice race | 3-layer defense | App check + DB constraint + IntegrityError catch | upload_invoice: explicit check → uq_supplier_invoice → except IntegrityError |
| Cross-layer role drift | Backend allows Clerk, frontend type omits it | Type-consistency gap (not security) | UserRole (useAuth.ts:3) vs RoleChecker(["Clerk"]) (invoices.py:136) |

Visual: Decision matrix table, with checkmarks for resolved and arrows for tradeoffs.
CodeGraph evidence column shows file:line anchors the tribunal can verify live.
```

---

### Slide 18: Metrics & Results (incl. CodeGraph Index)

<a id="slide-18-prompt"></a>

```
Create a metrics slide showing project results, including CodeGraph index stats
as a codebase-intelligence metric:

Code metrics:
- 87 indexed files (39 Python + 29 TS/TSX/JS + 19 YAML)
- 653 nodes (181 functions · 29 classes · 23 methods · 13 interfaces · 13 routes)
- 1,321 edges (call/reference relationships)
- 28 backend source files + 8 frontend page/component files
- 139 tests (86 backend + 53 frontend), 0 failures
- 0 mypy errors, 0 deprecation warnings

Infrastructure:
- 3 Azure services integrated (AI, Blob Storage, SQL Server)
- 7 database tables (suppliers, invoices, line_items, users, roles, user_roles, audit_logs)
- 10 REST API endpoints (13 route nodes indexed)
- 4 frontend routes (AppRoutes dynamic dispatch)

Hub symbols (high blast radius — architectural keystones):
- extract_invoice_data (ai_service.py:128) — 10 callers
- get_current_user (security.py:72) — 6 callers
- useAuth (useAuth.ts:20) — 9 callers (frontend auth hub)
- StorageUploadError (storage_service.py:23) — 5 callers

Deployment:
- Docker (2 Dockerfiles + compose + nginx)
- Kubernetes (kustomize: base + dev + prod overlays)
- Production: http://facturas.mi-dominio.com:8888

Quality process:
- SDD (Spec-Driven Development): 3 changes archived (azure-persistence, invoice-pdf-cleanup, supplier-stats)
- 4R adversarial review: 3 CRITICAL findings found and fixed
- TDD: strict RED → GREEN → REFACTOR on every feature
- CodeGraph: structural analysis + impact assessment before every edit

Visual: KPI cards / dashboard style — tests count, endpoints, Azure services,
CodeGraph nodes/edges, hub symbols, deployment.
```

---

### Slide 19: Future Improvements

```
Create a roadmap slide for future improvements:

Short-term:
- Add TypeScript strict mode + tsconfig.json for frontend
- Code-split Recharts to reduce bundle (654KB → ~200KB)
- Add pytest-cov for backend coverage reporting
- Add CI/CD pipeline (GitHub Actions: test → build → deploy)
- Fix cross-layer role drift: add 'Clerk' to frontend UserRole (surfaced by CodeGraph)
- Add direct component tests for UploadInvoice, Suppliers, Navbar (CodeGraph-identified gaps)

Medium-term:
- Multiple currency support with conversion
- Invoice OCR for scanned (non-digital) PDFs
- Email notifications for approval workflow
- Audit log dashboard with timeline view

Long-term:
- Multi-tenant architecture (SaaS)
- Azure Functions for async extraction (serverless)
- Mobile app (React Native)
- Machine learning for anomaly detection (duplicate suppliers, unusual amounts)

Visual: Timeline roadmap (Now → Next → Later) with horizontal arrow.
```

---

### Slide 20: References & Q&A

```
Create a final slide with references and Q&A prompt:

GitHub Repository: https://github.com/pacogpdev/Gestion_Documental_Tpo

Key documentation:
- README.md — installation, architecture, endpoints, deployment
- deploy-kubernetes.md — K8s deployment guide
- openspec/specs/ — SDD specifications
- openspec/changes/archive/ — 3 archived SDD changes with review reports

Code intelligence:
- CodeGraph index (local .codegraph/, gitignored) — 653 nodes / 1,321 edges
- Used for: structural queries, call-path analysis, blast-radius impact assessment,
  per-symbol test coverage, hub-symbol identification

Technologies:
- FastAPI: https://fastapi.tiangolo.com
- Azure Content Understanding: https://learn.microsoft.com/azure/ai-services
- React Query: https://tanstack.com/query
- Recharts: https://recharts.org
- Kubernetes: https://kubernetes.io

Visual: Clean slide with repo QR code, contact info, "Questions?" prompt.
```

---

## Additional Recommendations

### For the tribunal defense:

1. **Live demo** (optional, 2-3 min): Upload a test invoice, show AI extraction, show PDF viewer, show supplier stats dashboard. Use the 4 fictional invoices generated by `generate_test_invoices.py`.

2. **Code walkthrough with CodeGraph** (be prepared): The tribunal may ask to see specific code. Have these files ready to open — and mention you can also answer structural questions via the CodeGraph index:
   - `backend/app/services/ai_service.py` (AI extraction, 10 callers — hub)
   - `backend/app/services/storage_service.py` (SAS tokens, blob cleanup, typed errors)
   - `backend/app/core/database.py` (multi-engine pattern)
   - `backend/app/models/schemas.py` (GUID TypeDecorator, 3 dialects)
   - `backend/app/core/security.py` (RBAC, 6+2 callers blast radius)
   - `backend/app/api/endpoints/invoices.py` (upload_invoice, 5 edge cases, 3-layer duplicate defense)
   - `frontend/src/routes/index.tsx` (AppRoutes — single routing source)
   - `frontend/src/pages/SupplierDashboard.tsx` (Recharts + React Query + normalizeStats adapter)

3. **Be ready to explain tradeoffs**: The tribunal cares about WHY you chose something, not just WHAT. Key tradeoffs:
   - Why SAS tokens instead of public container or backend proxy
   - Why React Query instead of Redux or Zustand
   - Why kustomize instead of Helm
   - Why TDD instead of test-after
   - Why a 3-layer duplicate defense (app check + DB constraint + IntegrityError catch)

4. **Mention the 4R review process**: Expert tribunals value when you can show you found and fixed critical issues through adversarial review, not just that the code works.

5. **Surface the honest findings from CodeGraph**: Tribunals respect engineers who report gaps, not just successes. Specifically:
   - Frontend UserRole type omits 'Clerk' (cross-layer drift, not a security hole)
   - RoleChecker has no direct test (only transitively exercised)
   - UploadInvoice, Suppliers, Navbar lack direct component tests
   These show you can do cross-layer static analysis and self-assess coverage honestly.

6. **Highlight hub symbols as architectural keystones**: When discussing impact analysis, mention that `extract_invoice_data` (10 callers), `get_current_user` (6 callers), and `useAuth` (9 callers) are the high-blast-radius nodes — touching them requires verifying many dependents. This demonstrates systems thinking.
