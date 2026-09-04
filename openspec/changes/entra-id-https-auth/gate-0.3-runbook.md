# Runbook operativo para cerrar Gate 0.3

Este documento define la secuencia controlada para instalar cert-manager, habilitar DNS-01 en Azure DNS, conectar el Ingress con un certificado de producción y demostrar HTTPS antes de iniciar Task 1.6.

> Estado inicial: Gate 0.3 permanece cerrado. Ninguna fase posterior puede comenzar si la fase anterior no conserva evidencia verificable. Task 1.6 no puede habilitar el redirect hasta completar y aprobar este runbook.

## Alcance y reglas de seguridad

- Host público: `facturas.pedroortiz.com`.
- Zona Azure DNS delegada: `facturas.pedroortiz.com`.
- Namespace de aplicación: `facturas-control`.
- Ingress: `facturas-ingress`, clase `nginx`.
- ClusterIssuer de producción: `letsencrypt-production`.
- Secret TLS: `facturas-tls`.
- Secret DNS-01: `cert-manager-azuredns`, clave `client-secret`, normalmente en `cert-manager`.
- Mantener `nginx.ingress.kubernetes.io/ssl-redirect: "false"` hasta Task 1.6.
- No aplicar `k8s/overlays/prod` mientras incluya `db-init-job.yaml` y Gate 0.2 siga cerrado.
- No registrar secretos, tokens, kubeconfig, `tls.key`, YAML de Secrets ni variables de entorno.
- Los comandos de este documento usan Bash/Azure Cloud Shell.

## Responsables

| Área | Responsable esperado |
|---|---|
| cert-manager y clúster | Operador Kubernetes |
| Identidad, Azure RBAC y zona hija | Administrador Azure |
| Almacenamiento y rotación del secreto | Seguridad/plataforma |
| Delegación desde `pedroortiz.com` | Responsable DNS |
| Ingress y pruebas HTTP/HTTPS | Plataforma y aplicación |
| Cierre de Gate 0.3 | Operador de plataforma y responsable de aplicación |

## Fase 0 — Preparar una unidad TLS segura

### Objetivo

Separar cert-manager, staging y TLS de producción de las migraciones, seeds, imágenes y rollout de la aplicación.

### Acciones

1. Crear unidades renderizables independientes para plataforma, staging y producción.
2. Cambiar `hostedZoneName` a `facturas.pedroortiz.com`.
3. Sustituir los placeholders de email ACME e identificadores Azure.
4. Añadir un ClusterIssuer y Certificate de staging que no se conecten al Ingress.
5. Mantener el redirect desactivado.
6. Renderizar y revisar cada unidad antes de aplicarla.

```bash
kubectl kustomize <tls-staging-overlay>
kubectl kustomize <tls-production-overlay>
kubectl kustomize <tls-production-overlay> | grep -n "REPLACE_WITH"
kubectl diff -k <tls-staging-overlay>
```

### Criterio de salida

- [ ] Ningún render contiene placeholders.
- [ ] Ningún render contiene Secrets con datos reales.
- [ ] No aparece `db-init-job`, una migración ni una imagen `latest`.
- [ ] El redirect permanece desactivado.
- [ ] Staging y producción pueden aplicarse y revertirse por separado.

### Parada y rollback

Detenerse ante cualquier recurso ajeno a TLS. Revertir solamente los manifiestos de esta preparación; no tocar clúster, DNS ni datos.

## Fase 1 — Instalar y validar cert-manager

### Precondiciones

```bash
CLUSTER_CONTEXT="<cluster-context>"
CERT_MANAGER_VERSION="<pinned-version>"
CERT_MANAGER_NAMESPACE="cert-manager"

kubectl config current-context
kubectl cluster-info
kubectl version
helm version
helm list --all-namespaces | grep cert-manager
kubectl get deployment --all-namespaces | grep cert-manager
kubectl get crd certificates.cert-manager.io
```

No instalar encima de una instancia existente hasta identificar propietario, versión y método de gestión.

### Instalación

```bash
helm upgrade --install cert-manager \
  oci://quay.io/jetstack/charts/cert-manager \
  --namespace "$CERT_MANAGER_NAMESPACE" \
  --create-namespace \
  --version "$CERT_MANAGER_VERSION" \
  --set crds.enabled=true \
  --wait \
  --timeout 10m
```

La configuración productiva debe fijar réplicas, recursos, NetworkPolicies y versión mediante infraestructura versionada.

### Comprobaciones

```bash
helm status cert-manager -n cert-manager
kubectl api-resources --api-group=cert-manager.io
kubectl api-resources --api-group=acme.cert-manager.io

kubectl wait --for=condition=Established --timeout=120s \
  crd/certificates.cert-manager.io \
  crd/certificaterequests.cert-manager.io \
  crd/issuers.cert-manager.io \
  crd/clusterissuers.cert-manager.io \
  crd/orders.acme.cert-manager.io \
  crd/challenges.acme.cert-manager.io

kubectl -n cert-manager rollout status deployment/cert-manager --timeout=5m
kubectl -n cert-manager rollout status deployment/cert-manager-webhook --timeout=5m
kubectl -n cert-manager rollout status deployment/cert-manager-cainjector --timeout=5m
kubectl -n cert-manager get pods -o wide
cmctl check api --wait=2m
```

### Criterio de salida

- [ ] Release Helm `deployed` con versión fijada.
- [ ] CRDs principales `Established`.
- [ ] Controller, webhook y cainjector `Available`.
- [ ] Pods `Running/Ready`, sin reinicios crecientes.
- [ ] `cmctl check api` satisfactorio.

### Parada y rollback

Detenerse ante incompatibilidad, ownership ambiguo, webhook inaccesible, errores RBAC o `CrashLoopBackOff`. No desinstalar una instancia compartida ni eliminar CRDs sin análisis de dependencias.

## Fase 2 — Crear identidad y entregar el secreto DNS

### Configuración Azure

```bash
SUBSCRIPTION_ID="<subscription-id>"
TENANT_ID="<tenant-id>"
DNS_RESOURCE_GROUP="<dns-resource-group>"
DNS_ZONE_NAME="facturas.pedroortiz.com"
ACME_EMAIL="<shared-operations-email>"

DNS_ZONE_ID=$(az network dns zone show \
  --subscription "$SUBSCRIPTION_ID" \
  --resource-group "$DNS_RESOURCE_GROUP" \
  --name "$DNS_ZONE_NAME" \
  --query id \
  --output tsv)

printf '%s\n' "$DNS_ZONE_ID"
```

El ID debe terminar en `/Microsoft.Network/dnsZones/facturas.pedroortiz.com`.

### Identidad y RBAC

1. Preferir Workload Identity si el clúster AKS y la política de plataforma lo permiten.
2. Si se mantiene el diseño actual, crear un service principal exclusivo.
3. Asignar `DNS Zone Contributor` solamente a `$DNS_ZONE_ID`.
4. Comprobar que no posea roles amplios sobre la suscripción o Resource Group.

```bash
az role assignment list --assignee "<client-id>" --all --output table
```

### Entrega del secreto

Ruta recomendada:

```text
Azure Key Vault -> External Secrets Operator -> cert-manager-azuredns -> cert-manager
```

Comprobar sin revelar el valor:

```bash
kubectl -n cert-manager get secret cert-manager-azuredns
kubectl -n cert-manager get secret cert-manager-azuredns \
  -o go-template='{{if index .data "client-secret"}}client-secret-present{{else}}client-secret-missing{{end}}{{"\n"}}'
kubectl auth can-i get secret/cert-manager-azuredns \
  --namespace cert-manager \
  --as system:serviceaccount:cert-manager:cert-manager
kubectl -n cert-manager get deployment cert-manager \
  -o jsonpath='{.spec.template.spec.containers[0].args}'
```

### Criterio de salida

- [ ] Identidad exclusiva y scope limitado a la zona hija.
- [ ] Secret almacenado fuera de Git y sincronizado en el cluster-resource namespace.
- [ ] Nombre `cert-manager-azuredns` y clave `client-secret` correctos.
- [ ] Controller autorizado para leerlo.
- [ ] Responsable, vencimiento y rotación documentados.

### Parada y rollback

Detenerse ante permisos amplios, namespace incorrecto, clave ausente o exposición de credenciales. El rollback revoca RBAC, sincronización y credencial después de detener solicitudes pendientes.

## Fase 3 — Dejar DNS e Ingress operativos

### Delegación de la zona hija

```bash
az network dns zone show \
  --resource-group "$DNS_RESOURCE_GROUP" \
  --name "$DNS_ZONE_NAME" \
  --query nameServers \
  --output tsv
```

En la zona padre `pedroortiz.com`, crear `facturas NS` con los cuatro nameservers reales de Azure. No utilizar `ns1-xx` ni mantener un CNAME incompatible llamado `facturas`.

```bash
dig +short NS facturas.pedroortiz.com
dig +trace facturas.pedroortiz.com
dig @1.1.1.1 NS facturas.pedroortiz.com
dig @8.8.8.8 NS facturas.pedroortiz.com
```

### Ingress y dirección pública

```bash
kubectl get ingressclass
kubectl get deployment,service --all-namespaces | grep ingress-nginx
kubectl -n "<ingress-namespace>" rollout status \
  deployment/ingress-nginx-controller --timeout=5m
kubectl -n "<ingress-namespace>" get pods
kubectl -n "<ingress-namespace>" get service ingress-nginx-controller
```

Crear el registro apex `@ A <ingress-public-ip>` en la zona hija y comprobar:

```bash
dig @1.1.1.1 A facturas.pedroortiz.com
dig @8.8.8.8 A facturas.pedroortiz.com
kubectl -n facturas-control get ingress facturas-ingress
kubectl -n facturas-control describe ingress facturas-ingress
kubectl -n facturas-control get service,endpointslices
curl -v -H "Host: facturas.pedroortiz.com" "http://<ingress-public-ip>/health"
```

### Criterio de salida

- [ ] Delegación NS coherente desde resolvers independientes.
- [ ] Zona hija responde con SOA de Azure.
- [ ] Apex resuelve a la dirección estable del Ingress.
- [ ] ingress-nginx y puertos 80/443 operativos.
- [ ] Ingress admitido y servicios con endpoints.
- [ ] `/health` funciona y el redirect continúa desactivado.

### Parada y rollback

Detenerse ante DNSSEC/CAA incompatibles, delegación parcial, dirección cambiante, clase incorrecta, puertos cerrados o endpoints vacíos. Restaurar el registro padre previo sin borrar la zona hija durante el diagnóstico.

## Fase 4 — Validar DNS-01 con Let’s Encrypt Staging

### Ejecución

1. Aplicar `ClusterIssuer/letsencrypt-staging` con endpoint staging.
2. Solicitar un Certificate separado con Secret `facturas-tls-staging`.
3. No conectar ese Secret al Ingress.

```bash
kubectl apply -f <staging-clusterissuer>
kubectl apply -f <staging-certificate>
kubectl get clusterissuer letsencrypt-staging
kubectl describe clusterissuer letsencrypt-staging
kubectl -n facturas-control get certificate,certificaterequest,order,challenge --watch
cmctl status certificate facturas-tls-staging --namespace facturas-control
dig @1.1.1.1 TXT _acme-challenge.facturas.pedroortiz.com
```

### Criterio de salida

- [ ] ClusterIssuer staging `Ready=True`.
- [ ] Challenge presentado y validado.
- [ ] Order `valid`.
- [ ] Certificate staging `Ready=True`.
- [ ] Secret `facturas-tls-staging` creado.
- [ ] TXT temporal eliminado por cert-manager.

### Parada y rollback

Detenerse ante `Unauthorized`, `Forbidden`, TXT en otra zona, timeout o uso accidental del endpoint de producción. Retirar solamente Certificate y Secret de staging tras capturar evidencia.

## Fase 5 — Emitir y comprobar el certificado de producción

### Ejecución

```bash
kubectl diff -k <tls-production-overlay>
kubectl apply -k <tls-production-overlay>
kubectl wait --for=condition=Ready --timeout=5m \
  clusterissuer/letsencrypt-production
kubectl -n facturas-control wait --for=condition=Ready --timeout=10m \
  certificate/facturas-tls
kubectl -n facturas-control get certificate,certificaterequest,order,challenge
cmctl status certificate facturas-tls --namespace facturas-control
```

Comprobar el Secret sin mostrar la clave privada:

```bash
kubectl -n facturas-control get secret facturas-tls \
  -o jsonpath='{.type}{"\n"}'
kubectl -n facturas-control get secret facturas-tls \
  -o go-template='{{if index .data "tls.crt"}}cert-present{{else}}cert-missing{{end}} {{if index .data "tls.key"}}key-present{{else}}key-missing{{end}}{{"\n"}}'
kubectl -n facturas-control get secret facturas-tls \
  -o jsonpath='{.data.tls\.crt}' | base64 --decode | \
  openssl x509 -noout -subject -issuer -dates -fingerprint -sha256 -ext subjectAltName
```

### Criterio de salida

- [ ] ClusterIssuer y Certificate con generación actual y `Ready=True`.
- [ ] Secret tipo `kubernetes.io/tls` con `tls.crt` y `tls.key`.
- [ ] SAN exacto `facturas.pedroortiz.com`.
- [ ] Issuer Let’s Encrypt y fechas válidas.
- [ ] Sin rate limits ni inestabilidad de renovación.

### Parada y rollback

Detenerse ante `Ready=False/Unknown`, SAN o issuer incorrectos, Secret ausente o fechas inválidas. Mantener el redirect desactivado y preservar cualquier certificado válido anterior.

## Fase 6 — Demostrar HTTPS externamente

```bash
dig +short NS facturas.pedroortiz.com
dig +short A facturas.pedroortiz.com
openssl s_client \
  -connect facturas.pedroortiz.com:443 \
  -servername facturas.pedroortiz.com </dev/null 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates -fingerprint -sha256 -ext subjectAltName
curl --fail --show-error --verbose https://facturas.pedroortiz.com/
curl --fail --show-error --verbose https://facturas.pedroortiz.com/health
curl --include http://facturas.pedroortiz.com/health
```

No utilizar `curl -k`. Repetir desde dos resolvers y, preferentemente, dos redes externas durante 10–15 minutos.

### Criterio de salida

- [ ] Cadena TLS confiable y hostname/SAN correcto.
- [ ] No se sirve el certificado por defecto de ingress-nginx.
- [ ] Frontend y `/health` responden de forma estable.
- [ ] DNS e IP remota son coherentes.
- [ ] HTTP todavía no redirige.

### Parada y rollback

Detenerse ante necesidad de `-k`, timeout 443, certificado incorrecto, DNS intermitente, rutas fallidas o redirect prematuro. No iniciar Task 1.6.

## Fase 7 — Cerrar Gate 0.3

El paquete de evidencia debe contener:

- [ ] Versión y estado de cert-manager.
- [ ] CRDs, controller, webhook, cainjector y API operativos.
- [ ] Zona hija y delegación NS verificadas públicamente.
- [ ] Identidad con RBAC limitado y Secret externo presente.
- [ ] Ingress, dirección pública, servicios y endpoints operativos.
- [ ] Emisión staging satisfactoria.
- [ ] Emisión de producción y `Certificate Ready=True`.
- [ ] SAN, issuer, fingerprint y vigencia del certificado.
- [ ] Pruebas HTTPS externas sin bypass de validación.
- [ ] Confirmación de que HTTP aún no redirige.
- [ ] Rollback y responsables identificados.
- [ ] Aprobación del operador de plataforma y responsable de aplicación.

Registrar comandos, timestamps UTC, versiones, condiciones e identificadores no secretos. No registrar valores secretos ni claves privadas.

## Registro de ejecución

| Fase | Fecha UTC | Responsable | Resultado | Evidencia | Rollback necesario |
|---|---|---|---|---|---|
| 0. Preparación TLS |  |  | Pendiente |  |  |
| 1. cert-manager |  |  | Pendiente |  |  |
| 2. Identidad y Secret |  |  | Pendiente |  |  |
| 3. DNS e Ingress |  |  | Pendiente |  |  |
| 4. Staging |  |  | Pendiente |  |  |
| 5. Producción |  |  | Pendiente |  |  |
| 6. HTTPS externo |  |  | Pendiente |  |  |
| 7. Cierre Gate 0.3 |  |  | Pendiente |  |  |

## Continuación hacia Task 1.6

Task 1.6 puede comenzar solamente después del cierre explícito de Gate 0.3. La secuencia posterior será: test RED del redirect, activación HTTP→HTTPS, repetición de pruebas TLS, piloto de autenticación con Admin/Approver/Clerk/Viewer y validación del rollback sin eliminar el certificado válido.
