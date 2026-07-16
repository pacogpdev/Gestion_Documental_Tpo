"""Azure Blob Storage boundary for persisted invoice PDFs."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    ContentSettings,
    generate_blob_sas,
)

from backend.app.core.config import settings


class StorageConfigError(RuntimeError):
    """Raised when Blob Storage cannot be configured safely."""


class StorageUploadError(RuntimeError):
    """Raised when Azure rejects a blob operation required for upload."""


class BlobStorageService:
    """Small, injectable wrapper around the Azure Blob Storage SDK.

    Configuration and client-construction failures are rejected before any
    upload attempt. SDK failures during upload are translated to
    ``StorageUploadError`` so the API layer does not expose Azure exceptions.
    Cleanup is deliberately best effort because it is used after a database
    failure and cannot restore the distributed transaction on its own.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        container_name: str | None = None,
        client: BlobServiceClient | None = None,
    ) -> None:
        self.connection_string = (
            settings.AZURE_STORAGE_CONNECTION_STRING
            if connection_string is None
            else connection_string
        )
        self.container_name = (
            settings.AZURE_STORAGE_CONTAINER
            if container_name is None
            else container_name
        )
        self.account_name, self.account_key = self._parse_connection_string(
            self.connection_string
        )

        if not self.connection_string or not self.connection_string.strip():
            raise StorageConfigError("Azure Blob Storage connection string is missing")
        if not self.container_name or not self.container_name.strip():
            raise StorageConfigError("Azure Blob Storage container is missing")

        if client is not None:
            self.client = client
            return

        try:
            self.client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        except Exception as error:
            raise StorageConfigError(
                "Azure Blob Storage client could not be configured"
            ) from error

    def build_blob_name(self, supplier_id: object, invoice_id: object) -> str:
        """Return a unique PDF path grouped by supplier and invoice."""
        return f"{supplier_id}/{invoice_id}/{uuid.uuid4()}.pdf"

    @staticmethod
    def _parse_connection_string(
        connection_string: str,
    ) -> tuple[str | None, str | None]:
        values = {}
        for component in connection_string.split(";"):
            if "=" in component:
                key, value = component.split("=", 1)
                values[key] = value
        return values.get("AccountName"), values.get("AccountKey")

    def upload_pdf(self, pdf_bytes: bytes, supplier_id: object, invoice_id: object) -> str:
        """Upload PDF bytes and return Azure's retrievable blob URL."""
        blob_name = self.build_blob_name(supplier_id, invoice_id)
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name,
            )
            blob_client.upload_blob(
                pdf_bytes,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/pdf"),
            )
            return blob_client.url
        except Exception as error:
            raise StorageUploadError("Azure Blob Storage upload failed") from error

    def delete_blob(self, blob_name: str) -> None:
        """Best-effort cleanup for a blob uploaded before DB commit failed."""
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name,
            )
            blob_client.delete_blob()
        except Exception:
            # Cleanup must never hide the original database failure.
            return

    def get_blob_sas_url(self, blob_name: str, expiry_hours: int = 1) -> str:
        """Return a read-only, short-lived URL for an invoice blob."""
        if not self.account_name or not self.account_key:
            raise StorageConfigError(
                "Azure Blob Storage account credentials are missing for SAS generation"
            )

        try:
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
            )
        except Exception as error:
            raise StorageConfigError(
                "Azure Blob Storage SAS generation failed"
            ) from error

        return (
            f"https://{self.account_name}.blob.core.windows.net/"
            f"{self.container_name}/{blob_name}?{sas_token}"
        )

    def extract_blob_name_from_url(self, url: str) -> str | None:
        """Extract a configured-container blob name from an Azure URL."""
        if not isinstance(url, str) or not url:
            return None

        parsed = urlparse(url)
        expected_host = f"{self.account_name}.blob.core.windows.net"
        if parsed.scheme != "https" or parsed.hostname != expected_host:
            return None

        path = parsed.path.lstrip("/")
        prefix = f"{self.container_name}/"
        if not path.startswith(prefix):
            return None

        blob_name = path[len(prefix):]
        return blob_name or None
