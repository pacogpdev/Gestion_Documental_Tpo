# UploadInvoice Specification

## Purpose

Integration tests for the UploadInvoice page (`/upload`). Validates file upload lifecycle, AI extraction results display, error handling, and role-based access via MSW + test-utils.

## Requirements

### Requirement: Happy Path — successful upload and extraction display

The test MUST verify that selecting a valid PDF and clicking "Upload & Analyze" triggers `POST /api/invoices/upload` and transitions to the extracted data review form.

#### Scenario: Upload shows extraction form on success

- GIVEN a valid `application/pdf` File is selected via the file input
- WHEN the user clicks "Upload & Analyze"
- THEN `POST /api/invoices/upload` is called with `multipart/form-data`
- AND the button shows "Processing AI Extraction..." during the request
- AND the extracted data review form replaces the file input view

### Requirement: API Error — user-friendly notification on server failure

The test MUST display an error notification when the upload API responds with a 5xx error.

#### Scenario: Server error shows alert and preserves form

- GIVEN a valid PDF file is selected
- WHEN the upload API responds with 500
- THEN `window.alert` is called with an error message
- AND the file input and upload button remain available for retry

### Requirement: Validation — reject invalid input before API call

The test MUST reject non-PDF files or oversized uploads without calling the API.

#### Scenario: Non-PDF file triggers client-side validation

- GIVEN a non-PDF file (e.g., `.txt`, `.exe`) or a file exceeding the size limit is selected
- WHEN the user clicks "Upload & Analyze"
- THEN a validation error is displayed
- AND `POST /api/invoices/upload` is never called

### Requirement: Role Access — Viewer role restriction

The test MUST verify that users with the 'Viewer' role cannot upload invoices.

#### Scenario: Upload button disabled for Viewer role

- GIVEN the user has `['Viewer']` roles in localStorage
- WHEN the page renders
- THEN the "Upload & Analyze" button is disabled or hidden
- AND the file input is disabled or not rendered
