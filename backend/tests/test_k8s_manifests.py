from copy import deepcopy
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_OVERLAY = PROJECT_ROOT / "k8s" / "overlays" / "prod"
HOSTNAME = "facturas.pedroortiz.com"


def _merge(base, patch):
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = deepcopy(base)
        for key, value in patch.items():
            merged[key] = _merge(merged[key], value) if key in merged else value
        return merged
    return deepcopy(patch)


def _load_documents(path):
    return [document for document in yaml.safe_load_all(path.read_text()) if document]


def _render(kustomization_path):
    kustomization = yaml.safe_load(kustomization_path.read_text())
    documents = []

    for resource in kustomization.get("resources", []):
        resource_path = kustomization_path.parent / resource
        if resource_path.is_dir():
            documents.extend(_render(resource_path / "kustomization.yaml"))
        else:
            documents.extend(_load_documents(resource_path))

    for patch_config in kustomization.get("patches", []):
        patch = _load_documents(kustomization_path.parent / patch_config["path"])[0]
        target = patch_config["target"]
        for index, document in enumerate(documents):
            metadata = document.get("metadata", {})
            if (
                document.get("kind") == target["kind"]
                and metadata.get("name") == target["name"]
            ):
                documents[index] = _merge(document, patch)
                break
        else:
            raise AssertionError(f"Patch target was not rendered: {target}")

    return documents


def _manifest(documents, kind, name):
    return next(
        document
        for document in documents
        if document["kind"] == kind and document["metadata"]["name"] == name
    )


def _render_production_overlay():
    return _render(PRODUCTION_OVERLAY / "kustomization.yaml")


def test_production_render_uses_external_secret_references_only():
    documents = _render_production_overlay()
    rendered_text = yaml.safe_dump_all(documents)
    backend = _manifest(documents, "Deployment", "backend")
    config = _manifest(documents, "ConfigMap", "backend-config")
    issuer = _manifest(documents, "ClusterIssuer", "letsencrypt-production")

    assert not any(document["kind"] == "Secret" for document in documents)
    assert "stringData:" not in rendered_text
    assert "DATABASE_URL" not in config["data"]
    assert {"secretRef": {"name": "backend-secrets"}} in backend["spec"]["template"]["spec"]["containers"][0]["envFrom"]
    assert issuer["spec"]["acme"]["solvers"][0]["dns01"]["azureDNS"]["clientSecretSecretRef"] == {
        "name": "cert-manager-azuredns",
        "key": "client-secret",
    }
    for forbidden_value in ("facturas_pass", "tu-azure-key-aqui", "tu-connection-string-aqui", "user:password@"):
        assert forbidden_value not in rendered_text


def test_production_render_wires_issuer_certificate_and_tls_hostname():
    documents = _render_production_overlay()
    issuer = _manifest(documents, "ClusterIssuer", "letsencrypt-production")
    ingress = _manifest(documents, "Ingress", "facturas-ingress")

    assert issuer["spec"]["acme"]["server"] == "https://acme-v02.api.letsencrypt.org/directory"
    assert issuer["spec"]["acme"]["privateKeySecretRef"]["name"] == "letsencrypt-production-account-key"
    assert ingress["metadata"]["annotations"]["cert-manager.io/cluster-issuer"] == "letsencrypt-production"
    assert ingress["spec"]["tls"] == [{"hosts": [HOSTNAME], "secretName": "facturas-tls"}]
    assert ingress["spec"]["rules"][0]["host"] == HOSTNAME


def test_production_render_preserves_http_routing_while_deferring_redirect():
    documents = _render_production_overlay()
    ingress = _manifest(documents, "Ingress", "facturas-ingress")
    config = _manifest(documents, "ConfigMap", "backend-config")
    annotations = ingress["metadata"]["annotations"]
    routes = ingress["spec"]["rules"][0]["http"]["paths"]

    assert annotations["nginx.ingress.kubernetes.io/ssl-redirect"] == "false"
    assert "nginx.ingress.kubernetes.io/force-ssl-redirect" not in annotations
    assert config["data"]["BACKEND_CORS_ORIGINS"] == f"https://{HOSTNAME}"
    assert [(route["path"], route["backend"]["service"]["name"], route["backend"]["service"]["port"]["number"]) for route in routes] == [
        ("/api", "backend", 8000),
        ("/health", "backend", 8000),
        ("/", "frontend", 80),
    ]


def test_base_ingress_remains_http_only_outside_the_production_overlay():
    documents = _render(PROJECT_ROOT / "k8s" / "base" / "kustomization.yaml")
    ingress = _manifest(documents, "Ingress", "facturas-ingress")

    assert "tls" not in ingress["spec"]
    assert "cert-manager.io/cluster-issuer" not in ingress["metadata"]["annotations"]
    assert [(route["path"], route["backend"]["service"]["name"]) for route in ingress["spec"]["rules"][0]["http"]["paths"]] == [
        ("/api", "backend"),
        ("/health", "backend"),
        ("/", "frontend"),
    ]
