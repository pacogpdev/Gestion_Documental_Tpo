import uuid

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.dialects import mssql
from sqlalchemy.schema import CreateIndex
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.models.schemas import AuditLog, Role, User
from backend.app.services.identity_sync_service import IdentityDisabledError, IdentitySyncService


def _claims(*, roles=("Viewer",), email="person@example.com", **extra):
    return {
        "tid": "tenant-1",
        "oid": "object-1",
        "name": "Person One",
        "preferred_username": email,
        "roles": list(roles),
        **extra,
    }


def _seed_roles(db):
    for name in ("Admin", "Approver", "Clerk", "Viewer"):
        db.add(Role(id=uuid.uuid4(), name=name))
    db.commit()


def test_first_sync_projects_minimal_identity_roles_and_audit(db_session):
    _seed_roles(db_session)

    user = IdentitySyncService.sync(db_session, _claims(roles=("Admin", "Unknown")))

    assert (user.tenant_id, user.entra_oid, user.email, user.full_name) == (
        "tenant-1", "object-1", "person@example.com", "Person One",
    )
    assert [role.name for role in user.roles] == ["Admin"]
    audit = db_session.query(AuditLog).one()
    assert (audit.user_id, audit.action, audit.entity_id) == (user.id, "IDENTITY_SYNCED", user.id)


def test_repeat_sync_replaces_roles_and_records_a_second_audit_projection(db_session):
    _seed_roles(db_session)
    original = IdentitySyncService.sync(db_session, _claims(roles=("Admin",)))

    updated = IdentitySyncService.sync(db_session, _claims(roles=("Viewer",), email="updated@example.com"))

    assert updated.id == original.id
    assert ([role.name for role in updated.roles], updated.email) == (["Viewer"], "updated@example.com")
    assert db_session.query(AuditLog).filter_by(action="IDENTITY_SYNCED").count() == 2


def test_disabled_identity_denies_immediately_and_revoked_roles_cannot_restore_access(db_session):
    _seed_roles(db_session)
    user = IdentitySyncService.sync(db_session, _claims(roles=("Approver",)))
    user.is_disabled = True
    db_session.commit()

    with pytest.raises(IdentityDisabledError):
        IdentitySyncService.sync(db_session, _claims(roles=("Admin",)))

    user.is_disabled = False
    db_session.commit()
    resynced = IdentitySyncService.sync(db_session, _claims(roles=()))
    assert [role.name for role in resynced.roles] == []


def test_unique_identity_race_returns_the_existing_projection(db_session, monkeypatch):
    _seed_roles(db_session)
    existing = User(tenant_id="tenant-1", entra_oid="object-1", email="race@example.com")
    db_session.add(existing)
    db_session.commit()
    original_query = db_session.query

    class _RaceQuery:
        def filter_by(self, **_):
            class _RaceResult:
                def one_or_none(self):
                    return None
            return _RaceResult()

    first_user_lookup = True

    def race_query(model):
        nonlocal first_user_lookup
        if model is User and first_user_lookup:
            first_user_lookup = False
            return _RaceQuery()
        return original_query(model)

    monkeypatch.setattr(db_session, "query", race_query)

    recovered = IdentitySyncService.sync(db_session, _claims(roles=("Viewer",)))

    assert recovered.id == existing.id
    assert db_session.query(User).count() == 1


def test_forbidden_token_group_and_unused_claims_are_not_projected(db_session):
    _seed_roles(db_session)

    user = IdentitySyncService.sync(
        db_session,
        _claims(access_token="secret", refresh_token="secret", groups=["group-1"], ipaddr="10.0.0.1"),
    )

    assert not any(hasattr(user, field) for field in ("access_token", "refresh_token", "groups", "ipaddr"))
    assert set(inspect(User).columns.keys()) == {
        "id", "email", "full_name", "tenant_id", "entra_oid", "is_disabled", "last_synced_at",
    }


def test_versioned_migration_adds_identity_columns_unique_index_and_clerk_role():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id CHAR(36) PRIMARY KEY, email VARCHAR(255), full_name VARCHAR(255))"))
        connection.execute(text("CREATE TABLE roles (id CHAR(36) PRIMARY KEY, name VARCHAR(50) UNIQUE NOT NULL)"))
        from backend.migrations.v001_add_entra_identity import upgrade

        upgrade(connection)
        upgrade(connection)

        assert {"tenant_id", "entra_oid", "is_disabled", "last_synced_at"} <= {
            column["name"] for column in inspect(connection).get_columns("users")
        }
        assert connection.execute(text("SELECT COUNT(*) FROM roles WHERE name = 'Clerk'")).scalar_one() == 1
        assert "uq_users_tenant_entra_oid" in {
            index["name"] for index in inspect(connection).get_indexes("users")
        }


def test_versioned_migration_uses_sql_server_bit_for_disabled_flag(monkeypatch):
    from backend.migrations import v001_add_entra_identity as migration

    statements = []
    state = None

    class _Connection:
        dialect = type("Dialect", (), {"name": "mssql"})()

        def execute(self, statement, _parameters=None):
            nonlocal state
            statement = str(statement)
            statements.append(statement)
            if "SELECT created_clerk_role_id" in statement:
                return type("Result", (), {"mappings": lambda _: type("Rows", (), {"first": lambda _: state})()})()
            if "INSERT INTO entra_identity_migration_state" in statement:
                state = {"created_clerk_role_id": None, "email_was_nullable": True, "email_was_unique": True}
            if "UPDATE entra_identity_migration_state" in statement:
                state["created_clerk_role_id"] = _parameters["id"]
            return type("Result", (), {"scalar": lambda _: None if "SELECT id FROM roles" in statement else 1})()

    monkeypatch.setattr(
        migration, "inspect", lambda _: type("Inspector", (), {"get_columns": lambda _, __: []})()
    )

    migration.upgrade(_Connection())
    migration.downgrade(_Connection())

    assert any("is_disabled BIT NOT NULL DEFAULT 0" in statement for statement in statements)
    assert not any("ADD COLUMN" in statement for statement in statements)
    assert any("DROP INDEX uq_users_tenant_entra_oid ON dbo.users" in statement for statement in statements)
    assert any("sys.key_constraints" in statement and "sys.indexes" in statement for statement in statements)
    assert all(
        "OBJECT_ID(N'dbo.users')" in statement
        for statement in statements if "sys.indexes" in statement
    )
    assert any("DELETE FROM roles WHERE id = :id AND name = 'Clerk'" in statement for statement in statements)


def test_legacy_sqlite_email_projects_before_flush_and_links_migrated_clerk_role():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id CHAR(36) PRIMARY KEY, email VARCHAR(255) NOT NULL, full_name VARCHAR(255))"))
        connection.execute(text("CREATE TABLE roles (id CHAR(36) PRIMARY KEY, name VARCHAR(50) UNIQUE NOT NULL)"))
        Base.metadata.create_all(connection)
        from backend.migrations.v001_add_entra_identity import upgrade

        upgrade(connection)

    db = sessionmaker(bind=engine)()
    user = IdentitySyncService.sync(db, _claims(roles=("Clerk",)))

    assert user.email == "person@example.com"
    assert [role.name for role in user.roles] == ["Clerk"]
    db.close()
    with engine.begin() as connection:
        from backend.migrations.v001_add_entra_identity import downgrade

        downgrade(connection)
        assert {"tenant_id", "entra_oid", "is_disabled", "last_synced_at"}.isdisjoint(
            column["name"] for column in inspect(connection).get_columns("users")
        )


def test_legacy_unique_email_allows_distinct_entra_identities_after_upgrade():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE users (id CHAR(36) PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, "
            "full_name VARCHAR(255))"
        ))
        connection.execute(text("CREATE TABLE roles (id CHAR(36) PRIMARY KEY, name VARCHAR(50) UNIQUE NOT NULL)"))
        Base.metadata.create_all(connection)
        from backend.migrations.v001_add_entra_identity import upgrade

        upgrade(connection)

    db = sessionmaker(bind=engine)()
    try:
        IdentitySyncService.sync(db, _claims(email="shared@example.com"))
        IdentitySyncService.sync(
            db, _claims(email="shared@example.com", tid="tenant-2", oid="object-2")
        )
        assert db.query(User).count() == 2
    finally:
        db.close()
    with engine.begin() as connection:
        from backend.migrations.v001_add_entra_identity import downgrade

        with pytest.raises(RuntimeError, match="email uniqueness"):
            downgrade(connection)
        assert connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one() == 2


def test_sqlite_downgrade_rejects_null_email_before_rebuild():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE users (id CHAR(36) PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, "
            "full_name VARCHAR(255))"
        ))
        connection.execute(text("CREATE TABLE roles (id CHAR(36) PRIMARY KEY, name VARCHAR(50) UNIQUE NOT NULL)"))
        Base.metadata.create_all(connection)
        from backend.migrations.v001_add_entra_identity import downgrade, upgrade

        upgrade(connection)
        connection.execute(text("INSERT INTO users (id, email) VALUES ('user-1', NULL)"))
        schema_before = connection.execute(
            text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'")
        ).scalar_one()

        with pytest.raises(RuntimeError, match="email nullability"):
            downgrade(connection)

        assert connection.execute(
            text("SELECT id, email FROM users WHERE id = 'user-1'")
        ).one() == ("user-1", None)
        assert connection.execute(
            text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'")
        ).scalar_one() == schema_before


def test_downgrade_preserves_preexisting_clerk_role_and_assignment():
    engine = create_engine("sqlite:///:memory:")
    clerk_id, user_id = uuid.uuid4().hex, uuid.uuid4().hex
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id CHAR(36) PRIMARY KEY, email VARCHAR(255), full_name VARCHAR(255))"))
        connection.execute(text("CREATE TABLE roles (id CHAR(36) PRIMARY KEY, name VARCHAR(50) UNIQUE NOT NULL)"))
        Base.metadata.create_all(connection)
        connection.execute(text("INSERT INTO roles (id, name) VALUES (:id, 'Clerk')"), {"id": clerk_id})
        connection.execute(text("INSERT INTO users (id, email) VALUES (:id, 'existing@example.com')"), {"id": user_id})
        connection.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
                           {"user_id": user_id, "role_id": clerk_id})
        from backend.migrations.v001_add_entra_identity import downgrade, upgrade

        upgrade(connection)
        downgrade(connection)

        assert connection.execute(text("SELECT id FROM roles WHERE name = 'Clerk'")).scalar_one() == clerk_id
        assert connection.execute(text("SELECT COUNT(*) FROM user_roles WHERE role_id = :id"), {"id": clerk_id}).scalar_one() == 1


def test_distinct_entra_identities_can_share_an_email(db_session):
    _seed_roles(db_session)

    first = IdentitySyncService.sync(db_session, _claims(email="shared@example.com"))
    second = IdentitySyncService.sync(
        db_session, _claims(email="shared@example.com", tid="tenant-2", oid="object-2")
    )

    assert (first.id != second.id, db_session.query(User).count()) == (True, 2)


def test_fresh_sql_server_schema_uses_filtered_identity_index():
    identity_index = next(index for index in User.__table__.indexes if index.name == "uq_users_tenant_entra_oid")

    ddl = str(CreateIndex(identity_index).compile(dialect=mssql.dialect()))

    assert "WHERE tenant_id IS NOT NULL AND entra_oid IS NOT NULL" in ddl
