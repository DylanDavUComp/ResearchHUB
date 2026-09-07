import logging
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


logger = logging.getLogger(__name__)


@lru_cache
def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def database_is_ready() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def initialize_database_schema() -> None:
    try:
        import app.modules.usuarios.models  # noqa: F401

        Base.metadata.create_all(bind=get_engine())
    except Exception as exc:
        logger.warning("Database schema initialization skipped: %s", exc)


def list_database_tables() -> list[dict[str, object]]:
    inspector = inspect(get_engine())
    excluded_schemas = {"information_schema", "pg_catalog"}
    tables: list[dict[str, object]] = []

    for schema in sorted(inspector.get_schema_names()):
        if schema in excluded_schemas or schema.startswith("pg_"):
            continue

        for table_name in sorted(inspector.get_table_names(schema=schema)):
            columns = inspector.get_columns(table_name, schema=schema)
            tables.append(
                {
                    "schema": schema,
                    "name": table_name,
                    "type": "table",
                    "column_count": len(columns),
                    "columns": [
                        {
                            "name": column["name"],
                            "type": str(column["type"]),
                            "nullable": bool(column.get("nullable", True)),
                        }
                        for column in columns
                    ],
                }
            )

        for view_name in sorted(inspector.get_view_names(schema=schema)):
            columns = inspector.get_columns(view_name, schema=schema)
            tables.append(
                {
                    "schema": schema,
                    "name": view_name,
                    "type": "view",
                    "column_count": len(columns),
                    "columns": [
                        {
                            "name": column["name"],
                            "type": str(column["type"]),
                            "nullable": bool(column.get("nullable", True)),
                        }
                        for column in columns
                    ],
                }
            )

    return tables
