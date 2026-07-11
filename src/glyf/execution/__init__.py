"""SQL execution helpers."""

from glyf.execution.base import (
    SqlExecutionError,
    SqlExecutor,
    execute_sql,
    get_sql_executor,
    sql_executor,
)
from glyf.execution.result import QueryResult

from . import adbc as _adbc  # noqa: F401
from . import duckdb as _duckdb  # noqa: F401

__all__ = [
    "QueryResult",
    "SqlExecutionError",
    "SqlExecutor",
    "execute_sql",
    "get_sql_executor",
    "sql_executor",
]
