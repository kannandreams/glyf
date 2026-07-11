from __future__ import annotations

import importlib.util
from pathlib import Path

import adbc_driver_manager.dbapi

from glyf.execution.base import SqlExecutionError, sql_executor
from glyf.execution.duckdb import _duckdb_database, _load_seed_tables
from glyf.execution.result import QueryResult


class AdbcDuckDbExecutor:
    def execute(self, project_root: Path, sql: str) -> QueryResult:
        database = _duckdb_database(project_root)
        try:
            with adbc_driver_manager.dbapi.connect(
                driver=_duckdb_driver_path(),
                entrypoint="duckdb_adbc_init",
                db_kwargs=_duckdb_connection_kwargs(database),
            ) as connection:
                if database == ":memory:":
                    _load_seed_tables(connection, project_root / "seeds")
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    return QueryResult.from_arrow(cursor.fetch_arrow_table())
        except Exception as exc:
            raise SqlExecutionError(str(exc)) from exc


@sql_executor("duckdb")
@sql_executor("adbc_duckdb")
def _adbc_duckdb_executor() -> AdbcDuckDbExecutor:
    return AdbcDuckDbExecutor()


def _duckdb_driver_path() -> str:
    duckdb_module_spec = importlib.util.find_spec("_duckdb")
    if duckdb_module_spec is None or duckdb_module_spec.origin is None:
        raise SqlExecutionError(
            "Could not find DuckDB shared library for the ADBC executor"
        )
    return duckdb_module_spec.origin


def _duckdb_connection_kwargs(database: str) -> dict[str, str]:
    if database == ":memory:":
        return {}
    return {"path": database}
