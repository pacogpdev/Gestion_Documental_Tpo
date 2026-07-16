# Azure SQL Specification

## Purpose

Support SQLite for development and Azure SQL Server for production, and provide a transactional migration path for invoice-management data.

## Requirements

### Requirement: Environment-Selected Database Engine

`DatabaseManager` MUST select its SQLAlchemy engine from `DATABASE_URL`. SQLite URLs MUST remain supported for development; `mssql+pymssql` URLs MUST select Azure SQL Server for production. Session creation MUST use the selected engine.

#### Scenario: Development uses SQLite

- GIVEN `DATABASE_URL` is a SQLite URL
- WHEN the database manager is initialized
- THEN its engine dialect is SQLite and sessions can create and query local tables

#### Scenario: Production uses Azure SQL

- GIVEN `DATABASE_URL` is an `mssql+pymssql` URL for `pedro-ortiz-sql` and `pedro-ortiz-db_2`
- WHEN the database manager is initialized
- THEN its engine targets that Azure SQL database and sessions use it

### Requirement: Azure SQL Configuration and Failure Reporting

The backend MUST support the `pymssql` SQLAlchemy driver and MUST obtain Azure SQL credentials and endpoint information from configuration rather than hardcoded secrets. Connection failures MUST be surfaced to the caller without silently falling back to SQLite.

#### Scenario: Azure SQL connection failure

- GIVEN an invalid or unreachable Azure SQL configuration
- WHEN a connection or database operation is attempted
- THEN the operation returns the driver/database error and does not use the SQLite engine

### Requirement: SQL Server GUID Compatibility

All GUID-backed identifiers and relationships MUST round-trip as UUID values on SQLite and as native `UNIQUEIDENTIFIER` values on SQL Server, without changing IDs or foreign-key relationships.

#### Scenario: GUID round trip on Azure SQL

- GIVEN a record with a UUID primary key and related foreign key
- WHEN it is inserted and read through the SQL Server engine
- THEN both identifiers retain their values and the relationship remains valid

### Requirement: SQLite-to-Azure Migration

`backend/migrate_to_azure_sql.py` MUST migrate suppliers, invoices, line_items, users, roles, user_roles, and audit_logs from SQLite to Azure SQL. It MUST create the required schema, preserve IDs and field values, and execute the migration transactionally.

#### Scenario: Complete migration

- GIVEN a populated SQLite database and an empty reachable Azure SQL database
- WHEN the migration is executed
- THEN all seven tables and their rows are present in Azure SQL with preserved relationships

#### Scenario: Migration rollback

- GIVEN a migration that fails while copying data
- WHEN the failure is reported
- THEN the Azure SQL transaction is rolled back and no partial migration is presented as complete

### Requirement: Engine-Neutral Seed Data

`seed_db.py` MUST seed the configured database engine, create all required tables when absent, remain safe to run repeatedly, and commit seed data atomically on both SQLite and Azure SQL.

#### Scenario: Seed both supported engines

- GIVEN either a SQLite or reachable Azure SQL `DATABASE_URL`
- WHEN the seed command runs twice
- THEN the first run creates the fixture data, the second adds no duplicates, and both runs leave valid related records
