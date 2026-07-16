# Blob Storage Specification

## Purpose

Persist uploaded invoice PDFs in the configured Azure Blob Storage account and store their retrievable blob URLs with invoice records.

## Requirements

### Requirement: Azure Blob Storage Service

The system MUST provide a storage service that authenticates with the configured connection string and uploads PDF bytes to Azure Storage account `pedroortizst` and container `facturas-proveedores`. Configuration MUST be supplied through the existing storage settings, and Azure calls MUST be replaceable by a mock in automated tests.

#### Scenario: Successful service upload with a mocked client

- GIVEN valid PDF bytes, storage configuration, and a mocked Azure blob client
- WHEN the storage service uploads the bytes
- THEN the mock receives the bytes and the service returns the blob URL without network access

#### Scenario: Missing connection string

- GIVEN the storage connection string is empty or unavailable
- WHEN an upload is requested
- THEN the service MUST raise a controlled configuration error and MUST NOT call Azure

### Requirement: Invoice Blob Naming

Each uploaded PDF MUST use a unique blob name in the form `{supplier_id}/{invoice_id}/{uuid}.pdf`. The name MUST preserve supplier and invoice organization and MUST end in `.pdf`.

#### Scenario: Namespaced unique blob name

- GIVEN a supplier ID and newly assigned invoice ID
- WHEN a PDF upload name is generated twice
- THEN both names MUST match the required namespace and MUST be different

### Requirement: Invoice Upload Persistence

`POST /api/invoices/upload` MUST upload the original PDF bytes after extraction and MUST persist the returned Azure blob URL in `Invoice.file_url`. It MUST NOT persist the previous local `/uploads/{filename}` path.

#### Scenario: Successful invoice upload persists the blob URL

- GIVEN extraction succeeds and Azure returns `https://.../supplier/invoice/file.pdf`
- WHEN the upload endpoint completes
- THEN the created invoice has that exact URL in `file_url` and remains `Pending`

#### Scenario: Storage service receives the original PDF

- GIVEN an uploaded PDF with known bytes and successful extraction
- WHEN the endpoint invokes storage
- THEN storage receives the same bytes and the resulting URL is used for persistence

### Requirement: Storage Failure Consistency

If Azure configuration is invalid or blob upload fails, the endpoint MUST return a controlled service error, MUST NOT commit an invoice with a local or missing URL, and MUST leave the invoice transaction uncommitted.

#### Scenario: Azure upload failure

- GIVEN extraction succeeds but Azure rejects the blob upload
- WHEN the upload endpoint is called
- THEN it returns a controlled 503 error and no new invoice is committed
