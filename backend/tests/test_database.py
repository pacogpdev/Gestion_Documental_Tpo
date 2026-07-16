from unittest.mock import Mock, patch

import pytest

from backend.app.core.database import DatabaseManager


def test_sqlite_engine_receives_check_same_thread_false():
    sqlite_url = "sqlite:///test.db"
    fake_engine = Mock()
    fake_engine.dialect.name = "sqlite"

    with patch("backend.app.core.database.create_engine", return_value=fake_engine) as create:
        manager = DatabaseManager(db_url=sqlite_url)

    create.assert_called_once_with(sqlite_url, connect_args={"check_same_thread": False})
    assert manager.engine is fake_engine


def test_mssql_engine_uses_configured_url_without_sqlite_arguments():
    mssql_url = "mssql+pymssql://user:password@server.example.com/database"
    fake_engine = Mock()
    fake_engine.dialect.name = "mssql"

    with patch("backend.app.core.database.create_engine", return_value=fake_engine) as create:
        manager = DatabaseManager(db_url=mssql_url)

    create.assert_called_once_with(mssql_url)
    assert manager.db_url == mssql_url
    assert manager._session_factory.kw["bind"] is fake_engine


def test_connection_error_is_propagated_without_sqlite_fallback():
    mssql_url = "mssql+pymssql://user:password@unreachable/database"
    connection_error = RuntimeError("Azure SQL connection failed")

    with patch(
        "backend.app.core.database.create_engine", side_effect=connection_error
    ) as create:
        with pytest.raises(RuntimeError, match="Azure SQL connection failed"):
            DatabaseManager(db_url=mssql_url)

    create.assert_called_once_with(mssql_url)
