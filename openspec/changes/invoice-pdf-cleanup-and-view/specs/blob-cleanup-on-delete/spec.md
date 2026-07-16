# Delta for Blob Storage

## MODIFIED Requirements

### Requirement: Storage Failure Consistency

If Azure configuration is invalid or blob upload fails, the endpoint MUST return a controlled service error, MUST NOT commit an invoice with a local or missing URL, and MUST leave the invoice transaction uncommitted. When an invoice is deleted, the system MUST also attempt to remove its associated Azure PDF blob, but blob cleanup MUST be best effort and MUST NOT prevent database deletion. The blob name MUST be derived from the invoice's `file_url`. Legacy local paths beginning with `/uploads/` MUST NOT trigger Azure blob deletion. Automated tests MUST replace Azure operations with mocks.

(Previously: Storage failure consistency covered upload failures and cleanup only after a database error during upload.)

#### Scenario: Azure upload failure

- GIVEN extraction succeeds but Azure rejects the blob upload
- WHEN the upload endpoint is called
- THEN it returns a controlled 503 error and no new invoice is committed

#### Scenario: Successful blob deletion on invoice delete

- GIVEN an invoice has an Azure Blob URL and a mocked storage service accepts deletion
- WHEN the invoice is deleted
- THEN the associated blob is requested for deletion and the invoice is absent from the database

#### Scenario: Legacy file URL skips blob deletion

- GIVEN an invoice `file_url` starts with `/uploads/`
- WHEN the invoice is deleted
- THEN no Azure blob deletion is requested and the invoice is absent from the database

#### Scenario: Blob deletion failure does not block database deletion

- GIVEN an invoice has an Azure Blob URL and a mocked storage service reports not-found or network failure
- WHEN the invoice is deleted
- THEN the failure is ignored for the delete operation and the invoice is absent from the database
