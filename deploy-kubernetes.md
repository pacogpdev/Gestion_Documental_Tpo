# Plan de Deployment: Docker + Kubernetes — FacturasControl

> Documento de referencia generado para revisión e impresión.
> Estado: plan definitivo, listo para implementación.

---

## Tabla de contenidos

1. [Condiciones del entorno](#condiciones-del-entorno)
2. [Estado actual del proyecto](#estado-actual-del-proyecto)
3. [Estrategia de base de datos (Opción B)](#estrategia-de-base-de-datos-opción-b)
4. [FASE 0 — Cambios necesarios en el código](#fase-0--cambios-necesarios-en-el-código)
5. [FASE 1 — Dockerfiles](#fase-1--dockerfiles)
6. [FASE 2 — nginx.conf](#fase-2--nginxconf)
7. [FASE 3 — docker-compose.yml](#fase-3--docker-composeyml)
8. [FASE 4 — Estructura de manifiestos Kubernetes](#fase-4--estructura-de-manifiestos-kubernetes)
9. [FASE 5 — Namespace + ConfigMap + Secret](#fase-5--namespace--configmap--secret)
10. [FASE 6 — PostgreSQL en K8s (solo dev/staging)](#fase-6--postgresql-en-k8s-solo-devstaging)
11. [FASE 7 — Backend y Frontend Deployments + Services](#fase-7--backend-y-frontend-deployments--services)
12. [FASE 8 — Ingress + DNS + TLS](#fase-8--ingress--dns--tls)
13. [FASE 9 — Kustomization](#fase-9--kustomization)
14. [FASE 10 — Job de inicialización de DB](#fase-10--job-de-inicialización-de-db)
15. [Secuencia completa de deployment](#secuencia-completa-de-deployment)
16. [Lista completa de archivos a crear](#lista-completa-de-archivos-a-crear)

---

## Condiciones del entorno

| Aspecto | Valor |
|---|---|
| Dominio | `facturas.pedroortiz.com` |
| Subdominio | `facturas` (de `pedroortiz.com`) |
| Ingress Controller | Instalado y corriendo |
| Pod nginx | `nginx-ingress-ingress-nginx-controller-5ccd7547bb-nvn49` (running) |
| Helm release name | `nginx-ingress` (inferido del nombre del pod) |
| Service esperado | `nginx-ingress-ingress-nginx-controller` en namespace `ingress-nginx` |
| DB dev/staging | PostgreSQL (contenedor) |
| DB prod | Azure SQL (externo) |

---

## Estado actual del proyecto

| Componente | Detalle |
|---|---|
| Backend | FastAPI 0.139.0 / Uvicorn 0.51.0 / Pydantic 2.13.4 / SQLAlchemy 2.0.41 |
| Frontend | React 18 / TypeScript / Vite 5 / Tailwind / recharts 3.9.2 |
| DB dev | SQLite (`backend/test.db`) |
| DB prod | Azure SQL (MSSQL) — `pymssql==2.3.2` + `migrate_to_azure_sql.py` |
| DB staging | PostgreSQL (contenedor) — requiere agregar `psycopg2-binary` |
| AI | Azure AI Content Understanding |
| Storage | Azure Blob Storage (`azure-storage-blob==12.25.1`) con SAS URLs |
| Auth | Azure Entra ID JWT (bypass en dev) |
| Dockerfiles / compose / k8s / nginx | CERO. No existe nada. |

### Endpoints del backend (estado actual)

```
GET    /                            → root welcome
GET    /health                      → health check
GET    /api/invoices                → list invoices (SAS URLs)
POST   /api/invoices/upload         → upload + AI extraction (Clerk, Admin)
DELETE /api/invoices/{id}           → delete invoice + blob (Clerk, Admin)
PATCH  /api/invoices/{id}/approve   → set status (Approver, Admin)
GET    /api/suppliers               → list suppliers
POST   /api/suppliers               → create supplier
PUT    /api/suppliers/{id}          → update supplier
DELETE /api/suppliers/{id}          → delete supplier (Admin)
GET    /api/suppliers/{id}/stats    → supplier stats (Admin, Approver)
GET    /api/users/me                → current user profile
GET    /docs                        → Swagger UI
```

### Rutas del frontend (BrowserRouter — nginx debe hacer SPA fallback)

```
/                              → redirect to /dashboard
/dashboard                     → ApprovalDashboard
/upload                        → UploadInvoice
/suppliers                     → Suppliers
/suppliers/:id/dashboard       → SupplierDashboard
*                              → "Page not found"
```

---

## Estrategia de base de datos (Opción B)

| Entorno | Motor | Driver | Bootstrap |
|---|---|---|---|
| Docker Compose (local) | PostgreSQL (contenedor) | `psycopg2-binary` (agregar) | `seed_db.py` |
| K8s staging | PostgreSQL StatefulSet | `psycopg2-binary` | `seed_db.py` (Job) |
| K8s producción | Azure SQL (externo, managed) | `pymssql` (ya existe) | `migrate_to_azure_sql.py` (Job) |

---

## FASE 0 — Cambios necesarios en el código

Antes de tocar Docker, hay que hacer 4 cambios mínimos en el código. Son necesarios, no opcionales.

### 0.1 — Agregar driver PostgreSQL a `backend/requirements.txt`

```
psycopg2-binary==2.9.9
```

El proyecto solo tiene `pymssql` (para Azure SQL/MSSQL). Para que el backend se conecte al contenedor PostgreSQL en dev/staging, necesita el driver de PostgreSQL. En producción usará `pymssql` contra Azure SQL.

### 0.2 — Agregar `BACKEND_CORS_ORIGINS` a `backend/app/core/config.py`

```python
BACKEND_CORS_ORIGINS: str = ""
"""Comma-separated list of allowed CORS origins. Empty = use defaults."""
```

### 0.3 — Leer CORS dinámico en `backend/app/main.py`

Reemplazar la lista hardcodeada por:

```python
import os
origins_str = os.getenv("BACKEND_CORS_ORIGINS", "")
if origins_str:
    origins = [o.strip() for o in origins_str.split(",")]
else:
    origins = ["http://localhost:5173", "http://localhost:4173", "http://localhost:3000"]
```

### 0.4 — Crear `frontend/.env.example`

```env
# API URL — inlined at build time by Vite
# For nginx same-origin reverse proxy, use /api
VITE_API_URL=/api
```

---

## FASE 1 — Dockerfiles

### 1.1 — `.dockerignore` (raíz del proyecto)

```
**/.venv
**/__pycache__
**/node_modules
**/dist
**/.pytest_cache
**/*.db
**/*.sqlite*
backend/.env
frontend/.env
.git
*.pdf
.atl
.windsurf
```

Cuando Docker hace `COPY . .` copia TODO. Sin esto, se metería `node_modules` (500MB+), `.venv`, `.git`, tus PDFs de prueba y —peor— tu `.env` con las claves de Azure dentro de la imagen. Esto es un riesgo de seguridad.

### 1.2 — `Dockerfile.backend`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias primero (cache de capas)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copiar el código del backend
COPY backend/ ./backend/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# WORKDIR es /app porque los imports son backend.app.main:app
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Detalle clave: el `WORKDIR` es `/app` (raíz del proyecto), NO `/app/backend`. Los imports del proyecto son `backend.app.main:app` — si el `WORKDIR` fuera `/app/backend`, el import no resolvería.

### 1.3 — `Dockerfile.frontend` (multi-stage)

```dockerfile
# Stage 1: construir el bundle estático
FROM node:20-alpine AS builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# VITE_API_URL=/api para que nginx haga reverse proxy (same-origin)
ENV VITE_API_URL=/api
COPY frontend/ ./
RUN npm run build

# Stage 2: servir con nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

Multi-stage: el stage 1 instala Node y compila React → genera `dist/` (HTML+JS+CSS estático). El stage 2 solo copia `dist/` a nginx y descarta Node, `node_modules`, TypeScript, etc. La imagen final pesa ~25MB en vez de ~1GB.

`VITE_API_URL=/api` se inyecta al compilar (build-time). El frontend llama a `/api/...` que nginx redirige al backend. Así no hay CORS y no exponemos el puerto 8000 al mundo.

---

## FASE 2 — nginx.conf

### 2.1 — `nginx.conf` (raíz del proyecto)

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # SPA routing: cualquier ruta desconocida → index.html
    # Cubre: /dashboard, /upload, /suppliers, /suppliers/:id/dashboard
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Reverse proxy: /api/* → backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        client_max_body_size 10M;
    }

    # Health check del backend
    location /health {
        proxy_pass http://backend:8000/health;
    }
}
```

| Bloque | Función |
|---|---|
| `location /` | Sirve el frontend React. `try_files` manda todo a `index.html` para que React Router maneje la ruta. |
| `location /api/` | Redirige `/api/invoices`, `/api/suppliers`, etc. al backend en el puerto 8000. |
| `location /health` | Health check del backend (K8s lo usa para saber si el pod está vivo). |
| `client_max_body_size 10M` | Permite subir PDFs de hasta 10MB. |
| `proxy_read_timeout 120s` | Azure AI tarda en procesar facturas; sin esto nginx corta a los 60s. |

---

## FASE 3 — docker-compose.yml

### 3.1 — `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: facturas-postgres
    environment:
      POSTGRES_DB: facturas_db
      POSTGRES_USER: facturas
      POSTGRES_PASSWORD: ${DB_PASSWORD:-facturas_dev_pass}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U facturas"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: facturas-backend
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://facturas:${DB_PASSWORD:-facturas_dev_pass}@postgres:5432/facturas_db
      AZURE_CONTENT_ENDPOINT: ${AZURE_CONTENT_ENDPOINT}
      AZURE_CONTENT_KEY: ${AZURE_CONTENT_KEY}
      AZURE_STORAGE_CONNECTION_STRING: ${AZURE_STORAGE_CONNECTION_STRING}
      AZURE_STORAGE_CONTAINER: ${AZURE_STORAGE_CONTAINER:-facturas-proveedores}
      ENTRA_ID_JWKS_URL: ${ENTRA_ID_JWKS_URL:-}
      ENTRA_ID_TENANT_ID: ${ENTRA_ID_TENANT_ID:-}
      ENTRA_ID_CLIENT_ID: ${ENTRA_ID_CLIENT_ID:-}
      BACKEND_CORS_ORIGINS: ${BACKEND_CORS_ORIGINS:-http://localhost}
    ports:
      - "8000:8000"

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: facturas-frontend
    depends_on:
      - backend
    ports:
      - "80:80"

volumes:
  pgdata:
```

### 3.2 — `.env.docker` (raíz, NO se commitea)

```env
DB_PASSWORD=facturas_dev_pass

AZURE_CONTENT_ENDPOINT=https://aifoundry-resource-9030.services.ai.azure.com/
AZURE_CONTENT_KEY=tu-key-aqui

AZURE_STORAGE_CONNECTION_STRING=tu-connection-string-aqui
AZURE_STORAGE_CONTAINER=facturas-proveedores

ENTRA_ID_JWKS_URL=
ENTRA_ID_TENANT_ID=
ENTRA_ID_CLIENT_ID=

BACKEND_CORS_ORIGINS=http://localhost
```

### 3.3 — Comandos para levantar localmente

```bash
docker compose --env-file .env.docker up --build

# En otra terminal: crear tablas + seed data
docker exec facturas-backend python backend/seed_db.py

# Probar:
# Frontend: http://localhost
# Backend API: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

---

## FASE 4 — Estructura de manifiestos Kubernetes

```
k8s/
├── base/                        ← Compartido por todos los entornos
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
│
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml   ← Agrega postgres + seed_db.py
    │   ├── configmap-patch.yaml
    │   ├── postgres-statefulset.yaml
    │   ├── postgres-service.yaml
    │   └── db-init-job.yaml
    │
    └── prod/
        ├── kustomization.yaml   ← Sin postgres, usa Azure SQL
        ├── configmap-patch.yaml
        └── db-init-job.yaml
```

PostgreSQL vive en el overlay de dev (no en base) porque producción usa Azure SQL externo. Así el overlay de prod nunca referencia los manifiestos de PostgreSQL.

---

## FASE 5 — Namespace + ConfigMap + Secret

### 5.1 — `k8s/base/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: facturas-control
  labels:
    name: facturas-control
```

### 5.2 — `k8s/base/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: facturas-control
data:
  # Dev/staging default — prod overlay sobrescribe con Azure SQL URL
  DATABASE_URL: "postgresql://facturas:facturas_pass@postgres:5432/facturas_db"
  AZURE_CONTENT_ENDPOINT: "https://aifoundry-resource-9030.services.ai.azure.com/"
  AZURE_STORAGE_CONTAINER: "facturas-proveedores"
  BACKEND_CORS_ORIGINS: "https://facturas.pedroortiz.com"
```

Un ConfigMap guarda configuración **no sensible**: URLs, nombres de contenedores, rutas. Los pods lo leen como variables de entorno. Si cambiás un valor acá, todos los pods que lo referencian lo ven automáticamente (al reiniciar).

### 5.3 — `k8s/base/secret.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
  namespace: facturas-control
type: Opaque
stringData:
  AZURE_CONTENT_KEY: "tu-azure-key-aqui"
  AZURE_STORAGE_CONNECTION_STRING: "tu-connection-string-aqui"
  ENTRA_ID_JWKS_URL: ""
  ENTRA_ID_TENANT_ID: ""
  ENTRA_ID_CLIENT_ID: ""
```

Los Secrets están diseñados para datos sensibles. K8s los guarda codificados y (en producción) deberían estar cifrados en reposo con un KMS. Nunca pongas claves en un ConfigMap.

El `stringData` te deja escribir texto plano y K8s lo codifica automáticamente. Es más legible que `data` (que requiere base64 manual). Pero **este archivo NO debe commitearse a git con valores reales**. En producción se usa:

```bash
kubectl create secret generic backend-secrets \
  --namespace=facturas-control \
  --from-literal=AZURE_CONTENT_KEY='tu-key' \
  --from-literal=AZURE_STORAGE_CONNECTION_STRING='tu-conn-string' \
  --from-literal=ENTRA_ID_JWKS_URL='https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys' \
  --from-literal=ENTRA_ID_TENANT_ID='tu-tenant' \
  --from-literal=ENTRA_ID_CLIENT_ID='tu-client-id'
```

Alternativas más seguras para producción:
- **Sealed Secrets** (Bitnami): cifra el secret y SÍ podés commitearlo a git
- **External Secrets Operator**: lee de Azure Key Vault / AWS Secrets Manager

---

## FASE 6 — PostgreSQL en K8s (solo dev/staging)

### 6.1 — `k8s/overlays/dev/postgres-statefulset.yaml`

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: facturas-control
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: "facturas_db"
            - name: POSTGRES_USER
              value: "facturas"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: backend-secrets
                  key: DB_PASSWORD
          volumeMounts:
            - name: pgdata
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
  volumeClaimTemplates:
    - metadata:
        name: pgdata
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

Un Deployment crea pods sin identidad estable. Si PostgreSQL se reinicia y el pod se recrea en otro nodo, necesita que el volumen persistente lo siga. StatefulSet garantiza: (1) identidad estable (`postgres-0`), (2) almacenamiento persistente vinculado al pod, (3) arranque ordenado. Para bases de datos en K8s, siempre StatefulSet.

### 6.2 — `k8s/overlays/dev/postgres-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: facturas-control
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
  type: ClusterIP
```

---

## FASE 7 — Backend y Frontend Deployments + Services

### 7.1 — `k8s/base/backend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: facturas-control
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: facturas-backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: backend-config
            - secretRef:
                name: backend-secrets
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
```

| Concepto | Explicación |
|---|---|
| `replicas: 2` | K8s corre 2 copias del backend. Si una se cae, la otra sigue atendiendo. |
| `envFrom` + `configMapRef` | Inyecta TODAS las variables del ConfigMap como env vars del contenedor. |
| `envFrom` + `secretRef` | Igual pero con los Secrets. |
| `livenessProbe` | K8s llama a `/health` cada 30s. Si falla 3 veces, reinicia el pod. |
| `readinessProbe` | K8s llama a `/health` cada 10s. Si falla, el pod NO recibe tráfico (pero no se reinicia). |

### 7.2 — `k8s/base/backend-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: facturas-control
spec:
  selector:
    app: backend
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

### 7.3 — `k8s/base/frontend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: facturas-control
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: facturas-frontend:latest
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
```

### 7.4 — `k8s/base/frontend-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: facturas-control
spec:
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
```

---

## FASE 8 — Ingress + DNS + TLS

### 8.1 — Verificar el estado actual del nginx ya instalado

Como nginx ya está corriendo, **NO lo instalamos de nuevo**. Solo verificamos 3 cosas.

#### Paso 1: Verificar el IngressClass

El `ingressClassName` en el manifiesto Ingress debe coincidir con el configurado en el controlador:

```bash
kubectl get ingressclass
```

Salida esperada:

```
NAME    CONTROLLER                             PARAMETERS   AGE
nginx   k8s.io/ingress-nginx                   <none>       30d
```

Anotar el valor de la columna `NAME` (probablemente `nginx`). Ese es el `ingressClassName` que se usa en el manifiesto Ingress.

#### Paso 2: Verificar el namespace del controller

```bash
kubectl get pods -A | Select-String ingress-nginx
```

Salida esperada:

```
ingress-nginx   nginx-ingress-ingress-nginx-controller-5ccd7547bb-nvn49   1/1   Running   0   30d
```

#### Paso 3: Obtener la EXTERNAL-IP del Load Balancer

```bash
kubectl get svc -n ingress-nginx
```

Salida esperada:

```
NAME                                       TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)                      AGE
nginx-ingress-ingress-nginx-controller     LoadBalancer   10.96.45.12    20.100.50.25     80:31234/TCP,443:32567/TCP   30d
```

**Anotar el valor de `EXTERNAL-IP`**. Esa es la IP pública a la que se va a apuntar el dominio.

Si `EXTERNAL-IP` dice `<pending>`: el cluster no tiene un Load Balancer cloud provisionado (típico en bare metal / on-prem). Alternativas:
- **MetalLB**: instalarlo para que asigne una IP del rango de la red.
- **NodePort**: cambiar el Service a `type: NodePort` y acceder vía `http://<IP-de-cualquier-nodo>:<puerto>`.

### 8.2 — Diagrama del flujo completo

```
Usuario en internet
    │
    │  https://facturas.pedroortiz.com/dashboard
    ▼
┌──────────────────────────────────┐
│  DNS: facturas.pedroortiz.com      │
│  → A record → 20.100.50.25         │
└──────────────────┬───────────────┘
                   │
                   ▼
┌──────────────────────────────────┐
│  Cloud Load Balancer              │
│  (Service tipo LoadBalancer del   │
│   nginx-ingress-ingress-          │
│   nginx-controller)               │
│  EXTERNAL-IP: 20.100.50.25        │
└──────────────────┬───────────────┘
                   │
                   ▼
┌──────────────────────────────────┐
│  Ingress Controller (nginx pod)   │
│  nginx-ingress-ingress-nginx-     │
│  controller-5ccd7547bb-nvn49      │
│  Lee las reglas del Ingress y     │
│  enruta el tráfico                │
└──────────────────┬───────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
   /api/* → backend     /* → frontend
   (Service ClusterIP)  (Service ClusterIP)
```

### 8.3 — `k8s/base/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: facturas-ingress
  namespace: facturas-control
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
spec:
  ingressClassName: nginx
  rules:
    - host: facturas.pedroortiz.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /health
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

| Petición entrante | Va a |
|---|---|
| `facturas.pedroortiz.com/api/invoices` | backend:8000 |
| `facturas.pedroortiz.com/health` | backend:8000 |
| `facturas.pedroortiz.com/dashboard` | frontend:80 |
| `facturas.pedroortiz.com/upload` | frontend:80 |
| `facturas.pedroortiz.com/suppliers` | frontend:80 |
| `facturas.pedroortiz.com/suppliers/123/dashboard` | frontend:80 |
| `facturas.pedroortiz.com/` | frontend:80 |

### 8.4 — Configurar el DNS en el proveedor (paso a paso)

El DNS es como una agenda telefónica de internet. Cuando alguien escribe `facturas.pedroortiz.com` en el navegador, su computadora pregunta a un servidor DNS: *"¿Cuál es la IP de facturas.pedroortiz.com?"* El servidor responde con la IP configurada. Sin este paso, el dominio no resuelve.

**Paso 1 — Identificar dónde está gestionado `pedroortiz.com`:**

Si se compró el dominio en Namecheap, GoDaddy, Cloudflare, Hostinger, etc., el DNS se gestiona ahí. Para verificar:

```powershell
Resolve-DnsName pedroortiz.com -Type NS
```

Devuelve los nameservers. Si dicen `cloudflare.com` → está en Cloudflare. Si dicen `namecheaphosting.com` → está en Namecheap.

**Paso 2 — Entrar al panel de DNS del proveedor:**

Buscar la sección "DNS Settings", "DNS Management", "Manage DNS", "Advanced DNS" o similar (varía según proveedor).

**Paso 3 — Crear un registro DNS tipo A para el subdominio `facturas`:**

| Campo | Valor | Explicación |
|---|---|---|
| Type | `A` | Vincula un nombre con una IP |
| Name / Host | `facturas` | El subdominio. No poner `facturas.pedroortiz.com` completo — la mayoría de proveedores ya asumen el dominio base. Solo `facturas`. |
| Value / Target | `20.100.50.25` | La EXTERNAL-IP obtenida en el paso 8.1 (usar la real) |
| TTL | `300` (o auto) | Time To Live. 300s = 5 min (corto mientras se configura). Después se puede subir a 3600 (1h). |

Ejemplo visual en Cloudflare:

```
Type    Name       Content          Proxy status  TTL
A       facturas   20.100.50.25     DNS only      Auto
```

En Cloudflare: dejar el proxy status en "DNS only" (nube gris, NO nube naranja) mientras se configura. Después se puede activar el proxy de Cloudflare si se quiere CDN + protección DDoS.

**Paso 4 — (Opcional) Crear registro A para `www.facturas`:**

| Campo | Valor |
|---|---|
| Type | `A` |
| Name | `www.facturas` |
| Value | `20.100.50.25` |
| TTL | `300` |

**Paso 5 — Esperar la propagación DNS (5 min – 48 horas):**

```powershell
# Windows PowerShell — debería devolver la EXTERNAL-IP:
Resolve-DnsName facturas.pedroortiz.com

# Online (verifica desde múltiples servidores del mundo):
# https://dnschecker.org/  → poner "facturas.pedroortiz.com"
```

**Paso 6 — Verificar que todo el flujo funciona:**

```bash
# Debería responder el frontend de React (HTML):
curl http://facturas.pedroortiz.com

# Debería responder {"status":"ok"}:
curl http://facturas.pedroortiz.com/health

# Debería responder la lista de invoices (o error 401 si auth está activo):
curl http://facturas.pedroortiz.com/api/invoices
```

### 8.5 — (Opcional pero recomendado) TLS / HTTPS con cert-manager

Sin HTTPS, los navegadores marcan el sitio como "No seguro" y las claves viajan en texto plano.

**Paso 1 — Instalar cert-manager:**

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# Verificar:
kubectl get pods -n cert-manager
```

**Paso 2 — Crear el ClusterIssuer (`k8s/base/cluster-issuer.yaml`):**

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: tu-email@gmail.com    # ← Cambiar por el email real
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

```bash
kubectl apply -f k8s/base/cluster-issuer.yaml
```

**Paso 3 — Modificar el Ingress para que use TLS:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: facturas-ingress
  namespace: facturas-control
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - facturas.pedroortiz.com
      secretName: facturas-tls
  rules:
    - host: facturas.pedroortiz.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /health
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

```bash
kubectl apply -f k8s/base/ingress.yaml
```

**Paso 4 — Verificar que el certificado se emitió:**

```bash
kubectl get certificate -n facturas-control
```

Salida esperada:

```
NAME            READY   SECRET          AGE
facturas-tls    True    facturas-tls    2m
```

Cuando `READY=True`, el sitio ya es accesible en `https://facturas.pedroortiz.com`. cert-manager renueva el certificado automáticamente cada 60 días.

---

## FASE 9 — Kustomization

Kustomize permite definir la base UNA vez y luego "patchear" solo lo que cambia por entorno. Sin duplicar YAMLs.

### 9.1 — `k8s/base/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: facturas-control

resources:
  - namespace.yaml
  - configmap.yaml
  - secret.yaml
  - backend-deployment.yaml
  - backend-service.yaml
  - frontend-deployment.yaml
  - frontend-service.yaml
  - ingress.yaml
  # cluster-issuer.yaml  # Descomentar cuando se agregue TLS

images:
  - name: facturas-backend
    newTag: latest
  - name: facturas-frontend
    newTag: latest
```

### 9.2 — `k8s/overlays/dev/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: facturas-control-dev

resources:
  - ../../base
  - postgres-statefulset.yaml
  - postgres-service.yaml
  - db-init-job.yaml

patches:
  - path: configmap-patch.yaml
    target:
      kind: ConfigMap
      name: backend-config
  - target:
      kind: Ingress
      name: facturas-ingress
    patch: |-
      - op: replace
        path: /spec/rules/0/host
        value: dev.facturas.pedroortiz.com
```

### 9.3 — `k8s/overlays/dev/configmap-patch.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: facturas-control-dev
data:
  DATABASE_URL: "postgresql://facturas:dev_pass@postgres:5432/facturas_db"
  BACKEND_CORS_ORIGINS: "http://dev.facturas.pedroortiz.com"
```

### 9.4 — `k8s/overlays/prod/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: facturas-control-prod

resources:
  - ../../base
  - db-init-job.yaml

patches:
  - path: configmap-patch.yaml
    target:
      kind: ConfigMap
      name: backend-config
  - target:
      kind: Ingress
      name: facturas-ingress
    patch: |-
      - op: replace
        path: /spec/rules/0/host
        value: facturas.pedroortiz.com
```

### 9.5 — `k8s/overlays/prod/configmap-patch.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: facturas-control-prod
data:
  # Azure SQL en producción
  DATABASE_URL: "mssql+pymssql://user:password@pedro-ortiz-sql.database.windows.net:1433/pedro-ortiz-db_2"
  AZURE_CONTENT_ENDPOINT: "https://aifoundry-resource-9030.services.ai.azure.com/"
  BACKEND_CORS_ORIGINS: "https://facturas.pedroortiz.com"
```

### 9.6 — Aplicar con Kustomize

```bash
# Dev:
kubectl apply -k k8s/overlays/dev/

# Prod:
kubectl apply -k k8s/overlays/prod/

# Dry-run (ver qué se aplicaría sin hacerlo):
kubectl kustomize k8s/overlays/prod/ | less

# Borrar un entorno completo:
kubectl delete -k k8s/overlays/dev/
```

---

## FASE 10 — Job de inicialización de DB

### 10.1 — Dev/staging: `k8s/overlays/dev/db-init-job.yaml`

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-init
  namespace: facturas-control
spec:
  ttlSecondsAfterFinished: 60
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: db-init
          image: facturas-backend:latest
          command: ["python", "backend/seed_db.py"]
          envFrom:
            - configMapRef:
                name: backend-config
            - secretRef:
                name: backend-secrets
```

### 10.2 — Producción: `k8s/overlays/prod/db-init-job.yaml`

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  namespace: facturas-control
spec:
  ttlSecondsAfterFinished: 600
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: db-migrate
          image: facturas-backend:latest
          # Migra datos de SQLite local → Azure SQL
          command: ["python", "-m", "backend.migrate_to_azure_sql"]
          envFrom:
            - configMapRef:
                name: backend-config
            - secretRef:
                name: backend-secrets
          env:
            - name: SOURCE_DATABASE_URL
              value: "sqlite:///backend/test.db"
```

---

## Secuencia completa de deployment

### Pre-requisitos (se asumen ya listos)

- Docker instalado
- Cluster K8s corriendo
- kubectl configurado y conectado al cluster
- nginx Ingress Controller instalado y corriendo (`nginx-ingress-ingress-nginx-controller-5ccd7547bb-nvn49`)
- Dominio `pedroortiz.com` comprado y gestionable

### Pasos secuenciales

| # | Paso | Comando / Acción |
|---|---|---|
| 0 | Cambios en código (FASE 0) | Editar `requirements.txt`, `config.py`, `main.py`, crear `frontend/.env.example` |
| 1 | Crear archivos Docker (FASE 1-2) | `.dockerignore`, `Dockerfile.backend`, `Dockerfile.frontend`, `nginx.conf` |
| 2 | Crear `docker-compose.yml` + `.env.docker` | FASE 3 |
| 3 | Probar local con Docker Compose | `docker compose --env-file .env.docker up --build` |
| 4 | Seed DB local | `docker exec facturas-backend python backend/seed_db.py` |
| 5 | Verificar local | `http://localhost` y `http://localhost:8000/docs` |
| 6 | Construir imágenes para K8s | `docker build -t facturas-backend:latest -f Dockerfile.backend .` y `docker build -t facturas-frontend:latest -f Dockerfile.frontend .` |
| 7 | Cargar imágenes al cluster | Depende del entorno (Docker Desktop usa locales; minikube usa `minikube image load facturas-backend:latest`) |
| 8 | Verificar IngressClass del nginx ya instalado | `kubectl get ingressclass` → anotar el `NAME` (probablemente `nginx`) |
| 9 | Obtener EXTERNAL-IP del nginx ya instalado | `kubectl get svc -n ingress-nginx` → anotar `EXTERNAL-IP` |
| 10 | Crear todos los manifiestos K8s | FASES 5, 6, 7, 8, 9, 10 |
| 11 | Aplicar entorno dev con Kustomize | `kubectl apply -k k8s/overlays/dev/` |
| 12 | Esperar a que Postgres esté listo | `kubectl wait --for=condition=ready pod -l app=postgres -n facturas-control-dev --timeout=120s` |
| 13 | Verificar pods del backend y frontend | `kubectl get pods -n facturas-control-dev` |
| 14 | Configurar DNS en el proveedor | Crear registro A: `facturas` → EXTERNAL-IP del paso 9 |
| 15 | Esperar propagación DNS | `Resolve-DnsName facturas.pedroortiz.com` (en Windows) |
| 16 | Verificar acceso HTTP | `curl http://facturas.pedroortiz.com/health` |
| 17 | (Opcional) Instalar cert-manager | FASE 8.5 |
| 18 | (Opcional) Aplicar Ingress con TLS | `kubectl apply -f k8s/base/cluster-issuer.yaml` y update Ingress |
| 19 | Verificar HTTPS | `curl https://facturas.pedroortiz.com/health` |
| 20 | Deploy prod (con Azure SQL) | `kubectl apply -k k8s/overlays/prod/` |

---

## Lista completa de archivos a crear

```
PROYECTO_FACTURAS_PROVEEDORES/
├── .dockerignore
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── docker-compose.yml
├── .env.docker                                (NO commitear)
└── k8s/
    ├── base/
    │   ├── namespace.yaml
    │   ├── configmap.yaml
    │   ├── secret.yaml
    │   ├── backend-deployment.yaml
    │   ├── backend-service.yaml
    │   ├── frontend-deployment.yaml
    │   ├── frontend-service.yaml
    │   ├── ingress.yaml
    │   ├── cluster-issuer.yaml                 (opcional, para TLS)
    │   └── kustomization.yaml
    └── overlays/
        ├── dev/
        │   ├── kustomization.yaml
        │   ├── configmap-patch.yaml
        │   ├── postgres-statefulset.yaml
        │   ├── postgres-service.yaml
        │   └── db-init-job.yaml
        └── prod/
            ├── kustomization.yaml
            ├── configmap-patch.yaml
            └── db-init-job.yaml
```

---

*Fin del documento.*
