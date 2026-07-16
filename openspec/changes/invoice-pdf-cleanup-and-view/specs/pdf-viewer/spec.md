# PDF Viewer Specification

## Purpose

Expose each invoice's stored PDF URL to the invoice list and provide a safe way to open available Azure-hosted PDFs.

## Requirements

### Requirement: Invoice Response Includes File URL

The invoice-list API response MUST include a camelCase `fileUrl` field for every invoice. Its value MUST preserve the invoice's stored file URL or path, including an Azure Blob URL, a legacy `/uploads/` path, or a missing value represented as null.

#### Scenario: Invoice response returns the stored Azure URL

- GIVEN an invoice has an Azure Blob URL stored with it
- WHEN the invoice list is requested
- THEN that invoice's response includes the same value in `fileUrl`

### Requirement: PDF View Icon in Invoice List

The invoice list MUST provide a view-PDF icon control for invoices with an eligible Azure Blob URL. Activating the control MUST open that URL in a new browser tab. The control MUST be hidden or disabled when `fileUrl` is null or is a legacy local path beginning with `/uploads/`.

#### Scenario: Azure Blob URL opens in a new tab

- GIVEN an invoice has an eligible Azure Blob URL
- WHEN the user activates its view-PDF control
- THEN the PDF URL opens in a separate browser tab

#### Scenario: Legacy or missing URL hides the control

- GIVEN an invoice has a `/uploads/` path or a null `fileUrl`
- WHEN the invoice row is rendered
- THEN its view-PDF control is hidden or disabled and cannot open a PDF

#### Scenario: Icon is visible only for an eligible file URL

- GIVEN one invoice has an Azure Blob URL and another has no eligible URL
- WHEN the invoice list is rendered
- THEN only the first invoice has an enabled view-PDF control
