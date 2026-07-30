# FacturasControl

Sistema de extracción automatizada de datos de facturas mediante IA, con flujo de aprobación, gestión de proveedores y control de duplicados.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy, SQLite (dev) / Azure SQL Server (prod) |
| **Frontend** | Vite 5, React 18, TypeScript, Tailwind CSS 3, Recharts 3, React Query (cache) |
| **IA** | Azure AI Content Understanding SDK |
| **Storage** | Azure Blob Storage (persistencia de PDFs de facturas, SAS tokens) |
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
cd C:\Users\Nombre-Usuario\Documents\PROYECTO_FACTURAS_PROVEEDORES

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
# Frontend (53 tests)
cd frontend && npx vitest run

# Backend (86 tests)
cd backend && pytest -v
```

## Despliegue (Docker + Kubernetes)

<!-- NOTE: Replace mi-dominio.com and 192.168.x.x with your actual domain and IP.
     These are anonymized placeholders for documentation purposes. -->

### Endpoint de producción

La aplicación está desplegada y accesible en:

```
http://facturas.mi-dominio.com:8888
```

| Servicio | URL |
|----------|-----|
| Frontend (Dashboard) | `http://facturas.mi-dominio.com:8888/` |
| Backend API (Swagger) | `http://facturas.mi-dominio.com:8888/docs` |
| Health check | `http://facturas.mi-dominio.com:8888/health` |
| Lista de facturas | `http://facturas.mi-dominio.com:8888/api/invoices` |

> **Nota sobre el puerto 8888**: el acceso externo usa el puerto 8888 (no el estándar 80) debido a restricciones de la red del despliegue (Docker Desktop + WSL2 + NAT del ISP). En un entorno cloud gestionado (AKS, EKS, GKE) el tráfico fluiría por el puerto 80/443 estándar con un LoadBalancer real.

### Arquitectura de despliegue

```
Internet
  │
  │  DNS: facturas.mi-dominio.com → IP pública del router
  ▼
Router / Fortigate (NAT + port forwarding)
  │
  │  :8888 → 192.168.x.x:8888
  ▼
Servidor (Windows + Docker Desktop + WSL2)
  │
  │  socat proxy container (:8888 → host.docker.internal:80)
  ▼
kind cluster (Kubernetes 1.36, 4 nodos)
  │
  │  nginx Ingress Controller (Host: facturas.mi-dominio.com)
  ▼
┌─────────────────────┬─────────────────────┐
│  /api/* → backend   │  /* → frontend      │
│  (2 réplicas)        │  (2 réplicas, nginx)│
│  FastAPI + Uvicorn   │  React + Vite build │
└──────────┬──────────┴─────────────────────┘
           │
           ▼
    PostgreSQL StatefulSet
    (PVC 10Gi persistente)
```

### Archivos de despliegue

```
├── .dockerignore                 # Excluye .venv, node_modules, .env, PDFs del build
├── Dockerfile.backend            # Python 3.12-slim + libpq5 + uvicorn
├── Dockerfile.frontend           # Multi-stage: Node 20 build → nginx alpine serve
├── nginx.conf                    # SPA fallback + reverse proxy /api → backend
├── docker-compose.yml            # Testing local: postgres + backend + frontend
├── .env.docker                   # Variables para docker-compose (NO commitear)
├── deploy-kubernetes.md          # Plan de deployment completo (referencia)
└── k8s/
    ├── base/                     # Manifiestos compartidos (dev + prod)
    │   ├── namespace.yaml        # Namespace facturas-control
    │   ├── configmap.yaml        # Config no sensible (DATABASE_URL, CORS, endpoints)
    │   ├── secret.yaml           # Credenciales (Azure keys, DB password)
    │   ├── backend-deployment.yaml   # 2 réplicas + liveness/readiness probes
    │   ├── backend-service.yaml      # ClusterIP :8000
    │   ├── frontend-deployment.yaml  # 2 réplicas
    │   ├── frontend-service.yaml     # ClusterIP :80
    │   ├── ingress.yaml              # Host: facturas.mi-dominio.com
    │   └── kustomization.yaml        # Orquestador base
    └── overlays/
        ├── dev/                  # Dev con PostgreSQL
        │   ├── kustomization.yaml
        │   ├── configmap-patch.yaml      # DATABASE_URL → PostgreSQL
        │   ├── postgres-statefulset.yaml  # PostgreSQL 16 + PVC 10Gi
        │   ├── postgres-service.yaml
        │   └── db-init-job.yaml          # seed_db.py
        └── prod/                 # Prod con Azure SQL
            ├── kustomization.yaml
            ├── configmap-patch.yaml      # DATABASE_URL → Azure SQL (MSSQL)
            └── db-init-job.yaml          # migrate_to_azure_sql.py
```

### Testing local con Docker Compose

```powershell
# 1. Crear .env.docker con credenciales reales de Azure (copiar de backend/.env)
# 2. Construir y levantar
docker compose --env-file .env.docker up --build

# 3. Sembrar la base de datos (en otra terminal)
docker exec facturas-backend python backend/seed_db.py

# 4. Probar
# Frontend: http://localhost:8080
# Backend:  http://localhost:8000/docs
```

> **Importante**: si Docker Compose corre en la misma máquina que un cluster kind con nginx ingress, el puerto 80 del host está tomado por el ingress controller. Por eso el frontend de docker-compose usa el puerto 8080.

### Despliegue en Kubernetes (kind)

```powershell
# 1. Construir imágenes
docker build -t facturas-backend:latest -f Dockerfile.backend .
docker build -t facturas-frontend:latest -f Dockerfile.frontend .

# 2. Cargar imágenes al cluster kind
kind load docker-image facturas-backend:latest --name <cluster-name>
kind load docker-image facturas-frontend:latest --name <cluster-name>

# 3. Crear Secret con credenciales reales de Azure (no usar el placeholder del yaml)
kubectl create secret generic backend-secrets \
  --namespace=facturas-control \
  --from-literal=DB_PASSWORD=facturas_pass \
  --from-literal=AZURE_CONTENT_KEY='tu-key-real' \
  --from-literal=AZURE_STORAGE_CONNECTION_STRING='tu-connection-string-real' \
  --from-literal=ENTRA_ID_JWKS_URL= \
  --from-literal=ENTRA_ID_TENANT_ID= \
  --from-literal=ENTRA_ID_CLIENT_ID=

# 4. Aplicar manifiestos (entorno dev con PostgreSQL)
kubectl apply -k k8s/overlays/dev/

# 5. Verificar pods
kubectl get pods -n facturas-control

# 6. Para producción (Azure SQL), aplicar el overlay prod
kubectl apply -k k8s/overlays/prod/
```

### Recomendaciones para replicar el despliegue

1. **`imagePullPolicy: Never`**: en clusters kind, las imágenes se cargan localmente con `kind load docker-image`. Sin `imagePullPolicy: Never`, Kubernetes intenta bajarlas de Docker Hub y falla con `ImagePullBackOff`.

2. **CORS dinámico**: la variable `BACKEND_CORS_ORIGINS` (en ConfigMap) controla los orígenes permitidos. En dev usar `http://facturas.mi-dominio.com`, en prod `https://facturas.mi-dominio.com`. Vacío = fallback a localhost (para desarrollo local sin Docker).

3. **`VITE_API_URL=/api`**: el frontend se compila con `/api` como base URL. nginx hace reverse proxy de `/api/*` al backend, evitando CORS al ser same-origin.

4. **PostgreSQL vs Azure SQL**: el overlay `dev` despliega PostgreSQL en el cluster (StatefulSet + PVC). El overlay `prod` apunta `DATABASE_URL` a Azure SQL (MSSQL) externo — no necesita StatefulSet de DB.

5. **Secrets**: NUNCA commitear el archivo `k8s/base/secret.yaml` con credenciales reales. Usar `kubectl create secret` desde línea de comandos, o herramientas como Sealed Secrets / External Secrets Operator para producción.

6. **Health checks**: el backend expone `/health` que devuelve `{"status":"ok"}`. Los manifiestos K8s usan este endpoint para liveness (reinicia el pod si falla) y readiness (saca el pod del balanceo si falla) probes.

7. **SPM routing**: el frontend usa `BrowserRouter` de React Router. El `nginx.conf` tiene `try_files $uri $uri/ /index.html` para que deep links como `/dashboard` o `/suppliers/:id/dashboard` no den 404 al recargar la página.

8. **Timeouts de nginx**: el endpoint `/api/invoices/upload` llama a Azure AI Content Understanding que puede tardar 30-60s. El `nginx.conf` tiene `proxy_read_timeout 120s` para que nginx no corte la respuesta.

9. **kind + Docker Desktop en Windows**: Docker Desktop con WSL2 tiene un proxy de puertos (`wslrelay`) que a veces no expone los `hostPort` de kind a la red externa. Si el acceso desde otras máquinas falla, usar un contenedor socat como proxy TCP:

   ```powershell
   docker run -d --name kind-proxy --restart always -p 8888:80 \
     --add-host=host.docker.internal:host-gateway \
     alpine/socat TCP-LISTEN:80,fork,reuseaddr TCP:host.docker.internal:80
   ```

   Y apuntar el port forwarding del router al puerto 8888 en vez del 80.

10. **DNS y NAT**: para acceso desde internet, el DNS apunta a la IP pública del router. El router hace port forwarding al servidor. Si hay múltiples capas de NAT (modem ISP + Fortigate), configurar port forwarding en TODAS las capas, o activar DMZ en el modem ISP hacia el Fortigate.

11. **TLS/HTTPS**: para producción con HTTPS, instalar cert-manager + Let's Encrypt (ver `deploy-kubernetes.md`, FASE 8.5). Esto requiere abrir el puerto 443 en el router además del 80.

12. **Referencia completa**: el archivo `deploy-kubernetes.md` en la raíz del proyecto contiene el plan de deployment paso a paso con todos los detalles, comandos y configuraciones.

## Estructura del Proyecto

```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/       # FastAPI routers (invoices, suppliers, users)
│   │   ├── core/                # Config, database engine (multi-engine), security/auth
│   │   ├── models/              # SQLAlchemy models + Pydantic schemas
│   │   ├── services/            # AI extraction + Blob Storage (upload, delete, SAS URLs)
│   │   └── main.py              # FastAPI app entry point
│   ├── tests/                   # Backend tests (pytest)
│   ├── seed_db.py               # Database seeder (engine-neutral, idempotent)
│   ├── migrate_to_azure_sql.py  # SQLite → Azure SQL migration script
│   ├── requirements.txt
│   ├── mypy.ini                 # Type checking config (SQLAlchemy plugin)
│   ├── pytest.ini               # Test config (warning filters)
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
│   │   │   ├── Suppliers.tsx
│   │   │   └── SupplierDashboard.tsx  # Dashboard de estadísticas con Recharts
│   │   ├── routes/              # Route definitions
│   │   ├── test-utils.tsx       # Render personalizado con MemoryRouter
│   │   ├── index.css            # Tailwind directives
│   │   └── main.tsx             # Entry point
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── skills/                      # Skills para asistentes IA
│   ├── invoices-ai/
│   ├── invoices-api/
│   ├── invoices-auth/
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
| `GET /api/invoices` | Listar facturas con URL de PDF (SAS token de lectura temporal) | Todos |
| `PATCH /api/invoices/{id}/approve` | Aprobar o rechazar una factura | Approver, Admin |
| `DELETE /api/invoices/{id}` | Eliminar factura, line items y PDF asociado en Azure Blob Storage | Clerk, Admin |
| `GET /api/suppliers` | Listar proveedores | Todos |
| `POST /api/suppliers` | Crear nuevo proveedor | Admin |
| `PUT /api/suppliers/{id}` | Actualizar datos de un proveedor | Admin |
| `DELETE /api/suppliers/{id}` | Eliminar proveedor (solo si no tiene facturas asociadas) | Admin |
| `GET /api/suppliers/{id}/stats` | Estadísticas del proveedor (facturación mensual, % total, top items, estados) | Admin, Approver |
| `GET /api/users/me` | Obtener perfil del usuario autenticado | Todos |

### Frontend (React)

| Página | Descripción | Acceso |
|--------|-------------|--------|
| **Approval Dashboard** (`/dashboard`) | Lista de facturas con filtros por estado, búsqueda, ordenamiento por fecha/importe, paginación (15/page), icono de visualización de PDF, acciones de aprobar/rechazar/eliminar | Admin, Approver |
| **Upload Invoice** (`/upload`) | Subir PDF para extracción automática con revisión de datos extraídos | Admin, Approver |
| **Suppliers** (`/suppliers`) | Gestión de proveedores con búsqueda, filtro, editar, eliminar (con validación de facturas) y acceso al dashboard de estadísticas | Admin |
| **Supplier Dashboard** (`/suppliers/:id/dashboard`) | Dashboard de estadísticas por proveedor: KPIs (total anual, % del total, promedio, top factura), facturación mensual (AreaChart), share del proveedor (Donut), distribución por estado (Pie), top 10 items más facturados (BarChart) | Admin, Approver |

### Lógica de Negocio

- **Extracción por IA**: Azure Content Understanding extrae automáticamente número de factura, fecha, importe, proveedor, y line items del PDF
- **Persistencia de PDF en Azure Blob Storage**: cada factura subida se guarda en la cuenta de storage configurada / container `facturas-proveedores` con naming `{supplier_id}/{invoice_id}/{uuid}.pdf`. El `file_url` almacenado es la URL real del blob
- **Visualización de PDF con SAS token**: el endpoint `GET /api/invoices` genera URLs de lectura temporal (SAS token, 1 hora) para que el frontend pueda abrir los PDFs sin exponer las credenciales de storage
- **Cleanup de PDF al borrar factura**: `DELETE /api/invoices/{id}` elimina el PDF del Azure Blob Storage después de confirmar el commit en BD (best-effort, no bloquea si Azure falla)
- **Multi-engine database**: `DatabaseManager` selecciona SQLite (dev) o Azure SQL Server (prod) según `DATABASE_URL`. Sin fallback silencioso
- **Migración SQLite → Azure SQL**: script `migrate_to_azure_sql.py` migra las 7 tablas en orden FK, transaccional, con rollback ante fallos
- **Seed engine-neutral**: `seed_db.py` funciona con cualquier engine configurado, idempotente, transaccional
- **Detección de duplicados**: Mismo `invoice_number` + `supplier_id` → error 409. Rejected invoices se reemplazan automáticamente
- **Normalización de proveedor**: Búsqueda por tax_id, auto-actualización del nombre si cambia
- **Estados**: `Pending` → `Approved` / `Rejected`. Upload siempre guarda como Pending
- **Paginación**: 15 facturas por página con controles superior e inferior
- **Ordenamiento**: Por fecha y por importe, ascendente/descendente, indicadores siempre visibles
- **Eliminación de proveedor con validación**: `DELETE /api/suppliers/{id}` verifica que el proveedor no tenga facturas asociadas (409 si las tiene). Solo Admin
- **Dashboard de estadísticas por proveedor**: `GET /api/suppliers/{id}/stats` devuelve facturación mensual (trailing 12 meses), % del total facturado, top 10 items por importe, distribución por estado, promedio por factura y top factura. Frontend con Recharts (gráficos de área, donut, pie y barras)
- **Formateo de moneda dinámico**: los importes se muestran con el símbolo de la moneda real del proveedor (EUR, USD, GBP) extraído del API, no hardcodeado
- **Cache stale-while-revalidate**: React Query cachea las respuestas del API (facturas, proveedores, estadísticas). Al navegar entre páginas, los datos se muestran inmediatamente del cache mientras se piden datos nuevos en background. `staleTime: 30s`, `refetchOnWindowFocus: true`

## Usuarios y Roles

### Bypass de desarrollo: estado actual

Cuando `ENTRA_ID_JWKS_URL` no está configurada, el backend activa el bypass de desarrollo. Actualmente este modo sigue activo en producción, por lo que **no es una configuración segura para exponer públicamente**:

- Cualquier usuario puede acceder sin iniciar sesión.
- El backend lo identifica como `DEV_USER`.
- `DEV_USER` recibe el rol `Admin` y acceso completo.

```
Email:    dev@facturascontrol.local
Nombre:   Dev User
Rol:      Admin (acceso completo)
```

No se requiere contraseña. El frontend auto-obtiene el perfil llamando a `GET /api/users/me` al cargar. Este comportamiento debe limitarse a desarrollo local.

### Roles del sistema

| Rol | Permisos |
|-----|----------|
| **Admin** | Acceso completo: subir facturas, aprobar/rechazar, eliminar, gestionar proveedores |
| **Approver** | Subir facturas, aprobar/rechazar facturas pendientes |
| **Clerk** | Subir facturas, eliminar facturas (backend) |
| **Viewer** | Solo lectura: ver dashboard y lista de proveedores |

### Qué aporta Microsoft Entra ID

Microsoft Entra ID permite sustituir el bypass por autenticación corporativa gestionada:

- Inicio de sesión corporativo de Microsoft.
- Tokens JWT firmados y validados por el backend.
- Roles reales: `Admin`, `Approver`, `Clerk` y `Viewer`.
- MFA, bloqueo de cuentas y políticas de acceso.
- Sin almacenar contraseñas en la aplicación.
- Revocación y gestión centralizada de usuarios.

### Cómo habilitarlo en producción

1. Activar **HTTPS** antes de enviar credenciales o tokens: nunca deben circular por HTTP.
2. Registrar el frontend y la API en Microsoft Entra ID, y definir scopes y roles de aplicación.
3. Integrar MSAL en React para iniciar sesión y obtener un access token.
4. Enviar el token en cada petición: `Authorization: Bearer <access-token>`.
5. Configurar en el Secret de Kubernetes:

   ```text
   ENTRA_ID_TENANT_ID
   ENTRA_ID_CLIENT_ID
   ENTRA_ID_JWKS_URL
   ```

Con `ENTRA_ID_JWKS_URL` configurada, el backend exige el header `Authorization`, valida la firma del JWT frente al JWKS de Entra ID y verifica issuer y audience antes de aplicar las comprobaciones de rol.

La base de validación de backend ya está preparada. El frontend todavía guarda un token de desarrollo en almacenamiento local y no inicia el flujo real de Entra ID; falta integrar MSAL y retirar el bypass antes de considerar seguro el despliegue productivo.
