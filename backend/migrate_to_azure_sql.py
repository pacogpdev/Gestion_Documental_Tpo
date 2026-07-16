"""Transactional migration from the configured source database to Azure SQL.

The copy intentionally uses SQLAlchemy Core rows rather than ORM objects. This
keeps UUID values and every persisted column value intact across SQLite and
SQL Server while making the foreign-key order explicit and observable.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sqlalchemy import inspect, select

# Support both ``python -m backend.migrate_to_azure_sql`` from the project root
# and ``python backend/migrate_to_azure_sql.py`` from the project root.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.app.core.config import settings
from backend.app.core.database import Base, DatabaseManager
from backend.app.models import schemas as _schemas  # noqa: F401 - registers models


TABLE_MIGRATION_ORDER = (
    "roles",
    "users",
    "suppliers",
    "invoices",
    "user_roles",
    "line_items",
    "audit_logs",
)


@dataclass(frozen=True)
class MigrationSummary:
    total_tables: int
    total_rows: int


def _copy_table(
    source_session,
    target_session,
    table,
    source_tables: set[str],
    progress_callback: Callable[[str], None],
) -> int:
    """Copy one table and return its row count.

    A source database with no schema is treated as an empty source. This makes
    a fresh SQLite file a valid migration input without hiding errors from a
    configured target connection.
    """

    if table.name not in source_tables:
        progress_callback(f"{table.name}: 0 row(s)")
        return 0

    rows = source_session.execute(select(table)).mappings()
    row_count = 0
    for row in rows:
        target_session.execute(table.insert().values(**dict(row)))
        row_count += 1

    progress_callback(f"{table.name}: {row_count} row(s)")
    return row_count


def migrate_database(
    source_manager: DatabaseManager,
    target_manager: DatabaseManager,
    progress_callback: Callable[[str], None] = print,
) -> MigrationSummary:
    """Copy all application tables in FK order inside one target transaction."""

    source_session = source_manager.get_session()
    target_session = target_manager.get_session()
    try:
        source_tables = set(inspect(source_manager.engine).get_table_names())
        missing_tables = [
            table_name
            for table_name in TABLE_MIGRATION_ORDER
            if table_name not in source_tables
        ]
        if missing_tables:
            raise ValueError(
                "Source database is missing required tables: "
                f"{', '.join(missing_tables)}. Migration aborted."
            )

        # The target schema is created before the data transaction. A schema
        # creation failure is propagated and never reported as a successful
        # migration.
        Base.metadata.create_all(bind=target_manager.engine)

        total_rows = 0
        with target_session.begin():
            for table_name in TABLE_MIGRATION_ORDER:
                table = Base.metadata.tables[table_name]
                total_rows += _copy_table(
                    source_session,
                    target_session,
                    table,
                    source_tables,
                    progress_callback,
                )

        return MigrationSummary(
            total_tables=len(TABLE_MIGRATION_ORDER),
            total_rows=total_rows,
        )
    except Exception:
        target_session.rollback()
        raise
    finally:
        source_session.close()
        target_session.close()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-url",
        default=os.getenv("SOURCE_DATABASE_URL", "sqlite:///backend/test.db"),
        help="SQLAlchemy URL for the existing SQLite source database",
    )
    parser.add_argument(
        "--target-url",
        default=os.getenv("TARGET_DATABASE_URL", settings.DATABASE_URL),
        help="SQLAlchemy URL for the target Azure SQL database",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        summary = migrate_database(
            DatabaseManager(db_url=args.source_url),
            DatabaseManager(db_url=args.target_url),
        )
    except Exception as error:
        print(f"Migration failed: {error}", file=sys.stderr)
        return 1

    print(
        f"Migration complete: {summary.total_tables} tables, "
        f"{summary.total_rows} rows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
