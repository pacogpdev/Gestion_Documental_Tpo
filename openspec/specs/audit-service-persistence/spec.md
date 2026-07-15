# Audit Service Persistence Specification

## Purpose
Automated verification of the audit trail's reliability and persistence in the database.

## Requirements

### Requirement: Audit Log Persistence
The system MUST correctly save an audit record to the database when `log_action` is called.

#### Scenario: Record persistence
- GIVEN the audit service is initialized with a database
- WHEN `log_action` is called with a specific action and metadata
- THEN a record MUST be found in the database with matching metadata.

### Requirement: Persistence Failure Handling
The system MUST propagate exceptions if the database commit fails.

#### Scenario: Database commit failure
- GIVEN a database connection that fails during commit
- WHEN `log_action` is called
- THEN the system MUST propagate the database exception to the caller.
