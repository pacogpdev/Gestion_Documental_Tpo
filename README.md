# FacturasControl

Sistema de extracción automatizada de datos de facturas mediante IA, con flujo de aprobación, gestión de proveedores y control de duplicados.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy, SQLite (dev) / Azure SQL Server (prod) |
| **Frontend** | Vite 5, React 18, TypeScript, Tailwind CSS 3 |
| **IA** | Azure AI Content Understanding SDK |
| **Storage** | Azure Blob Storage (persistencia de PDFs de facturas) |
| **Auth** | Azure Entra ID (JWT) con bypass en desarrollo |
| **Testing** | Vitest + React Testing Library + MSW (frontend), pytest (backend) |

## Instalación y Ejecución

### Requisitos

- Python 3.12+
- Node.js 20+
- npm

### Backend

```powershell
# 1. Clonar el repositorio
cd C:\Users\Paco Gómez\Documents\PROYECTO_FACTURAS_PROVEEDORES

# 2. Crear y activar virtual env (si no existe)
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r backend\requirements.txt

# 4. Copiar y configurar variables de entorno
copy backend\.env.example backend\.env
# Editar backend\.env según sea necesario

# 5. Sembrar DB con datos de prueba
python backend\seed_db.py

# 6. Iniciar servidor
python -m uvicorn backend.app.main:app --reload
```

API disponible en `http://localhost:8000`. Documentación interactiva en `http://localhost:8000/docs`.

### Frontend

```powershell
# Desde la raíz del proyecto
cd frontend

# 1. Instalar dependencias
npm install

# 2. Iniciar servidor de desarrollo
npm run dev
```

Frontend disponible en `http://localhost:5173`.

### Tests

```powershell
# Frontend (29 tests)
cd frontend && npx vitest run

# Backend (52 tests)
cd backend && pytest -v
```

## Estructura del Proyecto

```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/       # FastAPI routers (invoices, suppliers, users)
│   │   ├── core/                # Config, database engine (multi-engine), security/auth
│   │   ├── models/              # SQLAlchemy models + Pydantic schemas
│   │   ├── services/            # AI extraction + Blob Storage integration
│   │   └── main.py              # FastAPI app entry point
│   ├── tests/                   # Backend tests (pytest)
│   ├── seed_db.py               # Database seeder (engine-neutral, idempotent)
│   ├── migrate_to_azure_sql.py  # SQLite → Azure SQL migration script
│   ├── requirements.txt
│   └── .env                     # Variables de entorno (local)
│
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios client con JWT interceptor
│   │   ├── components/          # Componentes compartidos (Navbar)
│   │   ├── hooks/               # Custom hooks (useAuth)
│   │   ├── mocks/               # MSW handlers globales
│   │   ├── pages/               # Páginas + tests + handlers colocalizados
│   │   │   ├── ApprovalDashboard.tsx
│   │   │   ├── UploadInvoice.tsx
│   │   │   └── Suppliers.tsx
│   │   ├── test-utils.tsx       # Render personalizado con MemoryRouter
│   │   ├── index.css            # Tailwind directives
│   │   └── main.tsx             # Entry point
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── skills/                      # Skills para asistentes IA
│   ├── invoices-api/
│   ├── invoices-db/
│   ├── invoices-components/
│   ├── invoices-theme/
│   ├── invoices-testing/
│   └── invoices-e2e/
│
├── AGENTS.md                    # Registro de skills del proyecto
└── README.md
```

## Funcionalidades Principales

### Backend (FastAPI)

| Endpoint | Método | Descripción | Roles |
|----------|--------|-------------|-------|
| `POST /api/invoices/upload` | Subir factura (PDF) → extracción IA → persistencia en Azure Blob Storage → guardado en BD | Clerk, Admin |
| `GET /api/invoices` | Listar todas las facturas con datos del proveedor | Todos |
| `PATCH /api/invoices/{id}/approve` | Aprobar o rechazar una factura | Approver, Admin |
| `DELETE /api/invoices/{id}` | Eliminar una factura y sus line items | Clerk, Admin |
| `GET /api/suppliers` | Listar proveedores | Todos |
| `POST /api/suppliers` | Crear nuevo proveedor | Admin |
| `GET /api/users/me` | Obtener perfil del usuario autenticado | Todos |

### Frontend (React)

| Página | Descripción | Acceso |
|--------|-------------|--------|
| **Approval Dashboard** (`/dashboard`) | Lista de facturas con filtros por estado, búsqueda, ordenamiento por fecha/importe, paginación (15/page), acciones de aprobar/rechazar/eliminar | Admin, Approver |
| **Upload Invoice** (`/upload`) | Subir PDF para extracción automática con revisión de datos extraídos | Admin, Approver |
| **Suppliers** (`/suppliers`) | Gestión de proveedores con búsqueda y filtro | Admin |

### Lógica de Negocio

- **Extracción por IA**: Azure Content Understanding extrae automáticamente número de factura, fecha, importe, proveedor, y line items del PDF
- **Persistencia de PDF en Azure Blob Storage**: cada factura subida se guarda en `pedroortizst` / `facturas-proveedores` con naming `{supplier_id}/{invoice_id}/{uuid}.pdf`. El `file_url` almacenado es la URL real del blob
- **Multi-engine database**: `DatabaseManager` selecciona SQLite (dev) o Azure SQL Server (prod) según `DATABASE_URL`. Sin fallback silencioso
- **Migración SQLite → Azure SQL**: script `migrate_to_azure_sql.py` migra las 7 tablas en orden FK, transaccional, con rollback ante fallos
- **Seed engine-neutral**: `seed_db.py` funciona con cualquier engine configurado, idempotente, transaccional
- **Detección de duplicados**: Mismo `invoice_number` + `supplier_id` → error 409. Rejected invoices se reemplazan automáticamente
- **Normalización de proveedor**: Búsqueda por tax_id, auto-actualización del nombre si cambia
- **Estados**: `Pending` → `Approved` / `Rejected`. Upload siempre guarda como Pending
- **Paginación**: 15 facturas por página con controles superior e inferior
- **Ordenamiento**: Por fecha y por importe, ascendente/descendente, indicadores siempre visibles

## Usuarios y Roles

### En desarrollo local

Cuando Azure Entra ID no está configurado (dev mode), el sistema **saltea la autenticación** y utiliza un usuario administrador por defecto:

```
Email:    dev@facturascontrol.local
Nombre:   Dev User
Rol:      Admin (acceso completo)
```

No se requiere contraseña. El frontend auto-obtiene el perfil llamando a `GET /api/users/me` al cargar.

### Roles del sistema

| Rol | Permisos |
|-----|----------|
| **Admin** | Acceso completo: subir facturas, aprobar/rechazar, eliminar, gestionar proveedores |
| **Approver** | Subir facturas, aprobar/rechazar facturas pendientes |
| **Clerk** | Subir facturas, eliminar facturas (backend) |
| **Viewer** | Solo lectura: ver dashboard y lista de proveedores |

### En producción (Azure Entra ID)

Los usuarios y roles son gestionados por Azure Entra ID. El sistema valida tokens JWT y extrae los roles del claim `roles` del token.
