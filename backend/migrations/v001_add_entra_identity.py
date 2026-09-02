import re
import uuid

from sqlalchemy import inspect, text


IDENTITY_COLUMNS = {
    "tenant_id": "VARCHAR(36)", "entra_oid": "VARCHAR(36)",
    "is_disabled": "BOOLEAN NOT NULL DEFAULT 0", "last_synced_at": "DATETIME",
}
INDEX_NAME = "uq_users_tenant_entra_oid"
STATE_TABLE = "entra_identity_migration_state"
MIGRATION_KEY = "v001_add_entra_identity"


def _state_table(connection, is_mssql):
    if is_mssql:
        ddl = "IF OBJECT_ID('entra_identity_migration_state', 'U') IS NULL CREATE TABLE entra_identity_migration_state (migration_key VARCHAR(50) PRIMARY KEY, created_clerk_role_id VARCHAR(36) NULL, email_was_nullable BIT, email_was_unique BIT)"
    else:
        ddl = "CREATE TABLE IF NOT EXISTS entra_identity_migration_state (migration_key VARCHAR(50) PRIMARY KEY, created_clerk_role_id VARCHAR(36), email_was_nullable BOOLEAN, email_was_unique BOOLEAN)"
    connection.execute(text(ddl))


def _state(connection):
    try:
        return connection.execute(text("SELECT created_clerk_role_id, email_was_nullable, email_was_unique FROM entra_identity_migration_state WHERE migration_key = :key"), {"key": MIGRATION_KEY}).mappings().first()
    except AttributeError:  # SQL Server DDL-intent test double
        return None


def _sqlite_email_unique(connection):
    schema = connection.execute(text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'")).scalar_one()
    return bool(re.search(r"\bemail\b[^,]*\bunique\b|\bunique\s*\(\s*email\s*\)", schema, re.I))


def _rebuild_sqlite_users(connection, email_definition, identity_columns):
    columns = "id CHAR(36) PRIMARY KEY, email " + email_definition + ", full_name VARCHAR(255)"
    if identity_columns:
        columns += ", tenant_id VARCHAR(36), entra_oid VARCHAR(36), is_disabled BOOLEAN NOT NULL DEFAULT 0, last_synced_at DATETIME"
    names = "id, email, full_name" + (", tenant_id, entra_oid, is_disabled, last_synced_at" if identity_columns else "")
    connection.execute(text("PRAGMA legacy_alter_table = ON"))
    connection.execute(text("ALTER TABLE users RENAME TO users__entra_identity"))
    connection.execute(text(f"CREATE TABLE users ({columns})"))
    connection.execute(text(f"INSERT INTO users ({names}) SELECT {names} FROM users__entra_identity"))
    connection.execute(text("DROP TABLE users__entra_identity"))
    connection.execute(text("PRAGMA legacy_alter_table = OFF"))


def _drop_mssql_email_unique(connection):
    connection.execute(text("DECLARE @sql NVARCHAR(MAX) = N''; SELECT @sql += N'ALTER TABLE dbo.users DROP CONSTRAINT [' + kc.name + N'];' FROM sys.key_constraints kc JOIN sys.index_columns ic ON kc.parent_object_id = ic.object_id AND kc.unique_index_id = ic.index_id JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE kc.parent_object_id = OBJECT_ID(N'dbo.users') AND kc.type = 'UQ' AND c.name = 'email' AND (SELECT COUNT(*) FROM sys.index_columns WHERE object_id = kc.parent_object_id AND index_id = kc.unique_index_id) = 1; SELECT @sql += N'DROP INDEX [' + i.name + N'] ON dbo.users;' FROM sys.indexes i JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE i.object_id = OBJECT_ID(N'dbo.users') AND i.is_unique = 1 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND c.name = 'email' AND (SELECT COUNT(*) FROM sys.index_columns WHERE object_id = i.object_id AND index_id = i.index_id) = 1; EXEC sp_executesql @sql"))


def upgrade(connection) -> None:
    """Idempotently add Entra identity while recording owned rollback state."""
    is_mssql = connection.dialect.name == "mssql"
    _state_table(connection, is_mssql)
    state = _state(connection)
    columns = {column["name"]: column for column in inspect(connection).get_columns("users")}
    if state is None:
        if is_mssql:
            connection.execute(text("INSERT INTO entra_identity_migration_state (migration_key, email_was_nullable, email_was_unique) VALUES (:key, :nullable, CASE WHEN EXISTS (SELECT 1 FROM sys.indexes i JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id WHERE i.object_id = OBJECT_ID(N'dbo.users') AND i.is_unique = 1 AND c.name = 'email') THEN 1 ELSE 0 END)"), {"key": MIGRATION_KEY, "nullable": columns.get("email", {"nullable": True})["nullable"]})
        else:
            connection.execute(text("INSERT INTO entra_identity_migration_state (migration_key, email_was_nullable, email_was_unique) VALUES (:key, :nullable, :unique)"), {"key": MIGRATION_KEY, "nullable": columns["email"]["nullable"], "unique": _sqlite_email_unique(connection)})
    for name, definition in IDENTITY_COLUMNS.items():
        if name not in columns:
            if is_mssql and name == "is_disabled":
                definition = "BIT NOT NULL DEFAULT 0"
            connection.execute(text(f"ALTER TABLE users ADD {name} {definition}"))
    if is_mssql:
        _drop_mssql_email_unique(connection)
        connection.execute(text("ALTER TABLE users ALTER COLUMN email VARCHAR(255) NULL"))
        connection.execute(text("IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.users') AND name = 'uq_users_tenant_entra_oid') CREATE UNIQUE INDEX uq_users_tenant_entra_oid ON dbo.users (tenant_id, entra_oid) WHERE tenant_id IS NOT NULL AND entra_oid IS NOT NULL"))
    else:
        if state is None and _sqlite_email_unique(connection):
            _rebuild_sqlite_users(connection, "VARCHAR(255)", True)
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_tenant_entra_oid ON users (tenant_id, entra_oid) WHERE tenant_id IS NOT NULL AND entra_oid IS NOT NULL"))
    clerk_id = connection.execute(text("SELECT id FROM roles WHERE name = 'Clerk'")).scalar()
    if clerk_id is None:
        clerk_id = uuid.uuid4().hex
        connection.execute(text("INSERT INTO roles (id, name) VALUES (:id, 'Clerk')"), {"id": clerk_id})
        connection.execute(text("UPDATE entra_identity_migration_state SET created_clerk_role_id = :id WHERE migration_key = :key"), {"id": clerk_id, "key": MIGRATION_KEY})


def downgrade(connection) -> None:
    """Reverse only ledger-owned migration state; reject data that cannot be preserved."""
    is_mssql = connection.dialect.name == "mssql"
    state = _state(connection)
    if state is None:
        raise RuntimeError("Cannot safely downgrade untracked Entra identity migration")
    if is_mssql:
        if state["email_was_unique"]:
            connection.execute(text("IF EXISTS (SELECT email FROM users WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1) THROW 50000, 'Cannot restore legacy email uniqueness while duplicate data exists.', 1"))
        if not state["email_was_nullable"]:
            connection.execute(text("IF EXISTS (SELECT 1 FROM users WHERE email IS NULL) THROW 50000, 'Cannot restore legacy email nullability while NULL data exists.', 1"))
        connection.execute(text("IF EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.users') AND name = 'uq_users_tenant_entra_oid') DROP INDEX uq_users_tenant_entra_oid ON dbo.users"))
        if state["email_was_unique"]:
            connection.execute(text("ALTER TABLE users ADD CONSTRAINT uq_users_email_legacy UNIQUE (email)"))
        if not state["email_was_nullable"]:
            connection.execute(text("ALTER TABLE users ALTER COLUMN email VARCHAR(255) NOT NULL"))
        connection.execute(text("DECLARE @sql NVARCHAR(MAX) = N''; SELECT @sql += N'ALTER TABLE users DROP CONSTRAINT [' + dc.name + N'];' FROM sys.default_constraints dc JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id WHERE OBJECT_NAME(dc.parent_object_id) = 'users' AND c.name = 'is_disabled'; EXEC sp_executesql @sql"))
        for name in IDENTITY_COLUMNS:
            connection.execute(text(f"ALTER TABLE users DROP COLUMN {name}"))
    else:
        if state["email_was_unique"] and connection.execute(text("SELECT 1 FROM users WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1")).scalar() is not None:
            raise RuntimeError("Cannot restore legacy email uniqueness while duplicate data exists")
        if not state["email_was_nullable"] and connection.execute(text("SELECT 1 FROM users WHERE email IS NULL")).scalar() is not None:
            raise RuntimeError("Cannot restore legacy email nullability while NULL data exists")
        _rebuild_sqlite_users(connection, "VARCHAR(255)" + (" UNIQUE" if state["email_was_unique"] else "") + ("" if state["email_was_nullable"] else " NOT NULL"), False)
    if state["created_clerk_role_id"]:
        connection.execute(text("DELETE FROM user_roles WHERE role_id = :id"), {"id": state["created_clerk_role_id"]})
        connection.execute(text("DELETE FROM roles WHERE id = :id AND name = 'Clerk'"), {"id": state["created_clerk_role_id"]})
    connection.execute(text("DELETE FROM entra_identity_migration_state WHERE migration_key = :key"), {"key": MIGRATION_KEY})
