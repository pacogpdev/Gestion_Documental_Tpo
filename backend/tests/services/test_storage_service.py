import re
from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.storage_service import (
    BlobStorageService,
    StorageConfigError,
    StorageUploadError,
)


def make_service_client():
    service_client = MagicMock()
    blob_client = MagicMock()
    blob_client.url = "https://storage.example/facturas-proveedores/supplier/invoice/file.pdf"
    service_client.get_blob_client.return_value = blob_client
    return service_client, blob_client


def test_build_blob_name_uses_supplier_invoice_namespace_and_unique_pdf_names():
    service = BlobStorageService(
        connection_string="UseDevelopmentStorage=true",
        container_name="facturas-proveedores",
        client=MagicMock(),
    )

    first = service.build_blob_name("supplier-1", "invoice-1")
    second = service.build_blob_name("supplier-1", "invoice-1")

    assert re.fullmatch(r"supplier-1/invoice-1/[0-9a-f-]{36}\.pdf", first)
    assert re.fullmatch(r"supplier-1/invoice-1/[0-9a-f-]{36}\.pdf", second)
    assert first != second


def test_upload_pdf_sends_original_bytes_and_pdf_content_type_returns_blob_url():
    service_client, blob_client = make_service_client()
    with patch(
        "backend.app.services.storage_service.BlobServiceClient.from_connection_string",
        return_value=service_client,
    ) as from_connection_string:
        service = BlobStorageService(
            connection_string="UseDevelopmentStorage=true",
            container_name="facturas-proveedores",
        )

    pdf_bytes = b"%PDF-original-bytes"
    blob_url = service.upload_pdf(pdf_bytes, "supplier-1", "invoice-1")

    assert blob_url == blob_client.url
    from_connection_string.assert_called_once_with("UseDevelopmentStorage=true")
    service_client.get_blob_client.assert_called_once()
    blob_client.upload_blob.assert_called_once()
    uploaded_bytes = blob_client.upload_blob.call_args.args[0]
    content_settings = blob_client.upload_blob.call_args.kwargs["content_settings"]
    assert uploaded_bytes == pdf_bytes
    assert content_settings.content_type == "application/pdf"


def test_missing_connection_string_raises_config_error_without_calling_azure():
    with patch(
        "backend.app.services.storage_service.BlobServiceClient.from_connection_string"
    ) as from_connection_string:
        with pytest.raises(StorageConfigError, match="connection string"):
            BlobStorageService(connection_string="", container_name="facturas-proveedores")

    from_connection_string.assert_not_called()


def test_missing_container_raises_config_error_without_calling_azure():
    with patch(
        "backend.app.services.storage_service.BlobServiceClient.from_connection_string"
    ) as from_connection_string:
        with pytest.raises(StorageConfigError, match="container"):
            BlobStorageService(connection_string="UseDevelopmentStorage=true", container_name="")

    from_connection_string.assert_not_called()


def test_upload_sdk_failure_raises_controlled_storage_error():
    service_client, blob_client = make_service_client()
    blob_client.upload_blob.side_effect = RuntimeError("Azure unavailable")
    service = BlobStorageService(
        connection_string="UseDevelopmentStorage=true",
        container_name="facturas-proveedores",
        client=service_client,
    )

    with pytest.raises(StorageUploadError, match="upload") as error:
        service.upload_pdf(b"pdf", "supplier-1", "invoice-1")

    assert isinstance(error.value.__cause__, RuntimeError)


def test_delete_blob_gets_named_blob_and_calls_delete():
    service_client, blob_client = make_service_client()
    service = BlobStorageService(
        connection_string="UseDevelopmentStorage=true",
        container_name="facturas-proveedores",
        client=service_client,
    )

    service.delete_blob("supplier-1/invoice-1/file.pdf")

    service_client.get_blob_client.assert_called_once_with(
        container="facturas-proveedores",
        blob="supplier-1/invoice-1/file.pdf",
    )
    blob_client.delete_blob.assert_called_once_with()
