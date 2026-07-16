from sqlalchemy import event, inspect

import pytest

from backend.app.core.database import Base, DatabaseManager
from backend.app.models.schemas import Invoice, LineItem, Role, Supplier, User, user_roles
import backend.seed_db as seed_module


def manager_for(path):
    return DatabaseManager(db_url=f"sqlite:///{path}")


def test_seed_creates_all_tables_and_fixture_data_on_configured_engine(tmp_path):
    manager = manager_for(tmp_path / "seed.sqlite")

    seed_module.seed_data(manager)

    assert set(inspect(manager.engine).get_table_names()) == {
        "roles",
        "users",
        "suppliers",
        "invoices",
        "user_roles",
        "line_items",
        "audit_logs",
    }
    session = manager.get_session()
    assert {role.name for role in session.query(Role).all()} == {
        "Admin",
        "Approver",
        "Clerk",
        "Viewer",
    }
    assert session.query(User).count() == 4
    assert session.query(Supplier).count() >= 1
    assert session.query(Invoice).count() >= 1
    assert session.query(LineItem).count() >= 1
    assert session.execute(user_roles.select()).all()
    session.close()


def test_seed_is_repeatable_without_duplicate_rows_or_relationships(tmp_path):
    manager = manager_for(tmp_path / "repeatable-seed.sqlite")

    seed_module.seed_data(manager)
    first_session = manager.get_session()
    first_counts = {
        "roles": first_session.query(Role).count(),
        "users": first_session.query(User).count(),
        "suppliers": first_session.query(Supplier).count(),
        "invoices": first_session.query(Invoice).count(),
        "line_items": first_session.query(LineItem).count(),
        "user_roles": first_session.execute(user_roles.select()).rowcount,
    }
    first_session.close()

    seed_module.seed_data(manager)
    second_session = manager.get_session()
    second_counts = {
        "roles": second_session.query(Role).count(),
        "users": second_session.query(User).count(),
        "suppliers": second_session.query(Supplier).count(),
        "invoices": second_session.query(Invoice).count(),
        "line_items": second_session.query(LineItem).count(),
        "user_roles": second_session.execute(user_roles.select()).rowcount,
    }

    assert second_counts == first_counts
    second_session.close()


def test_seed_uses_database_manager_factory_when_no_manager_is_passed(tmp_path, monkeypatch):
    configured_manager = manager_for(tmp_path / "configured-seed.sqlite")
    monkeypatch.setattr(seed_module, "DatabaseManager", lambda: configured_manager)

    seed_module.seed_data()

    session = configured_manager.get_session()
    assert session.query(Role).count() == 4
    session.close()


def test_seed_rolls_back_all_fixture_rows_when_a_later_insert_fails(tmp_path):
    manager = manager_for(tmp_path / "atomic-seed.sqlite")

    Base.metadata.create_all(manager.engine)

    def fail_on_users(connection, cursor, statement, parameters, context, executemany):
        if "INSERT INTO users" in statement:
            raise RuntimeError("simulated seed failure")

    event.listen(manager.engine, "before_cursor_execute", fail_on_users)
    try:
        with pytest.raises(RuntimeError, match="simulated seed failure"):
            seed_module.seed_data(manager)
    finally:
        event.remove(manager.engine, "before_cursor_execute", fail_on_users)

    session = manager.get_session()
    assert session.query(Role).count() == 0
    assert session.query(User).count() == 0
    assert session.query(Supplier).count() == 0
    assert session.query(Invoice).count() == 0
    session.close()
