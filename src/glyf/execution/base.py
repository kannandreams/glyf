from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from glyf.execution.result import QueryResult


class SqlExecutionError(ValueError):
    """Raised when compiled SQL cannot be executed."""


class SqlExecutor(Protocol):
    def execute(self, project_root: Path, sql: str) -> QueryResult:
        ...


SqlExecutorFactory = Callable[[], SqlExecutor]

_EXECUTORS: dict[str, SqlExecutorFactory] = {}


def sql_executor(name: str) -> Callable[[SqlExecutorFactory], SqlExecutorFactory]:
    normalized = _normalize_name(name)

    def decorator(factory: SqlExecutorFactory) -> SqlExecutorFactory:
        _EXECUTORS[normalized] = factory
        return factory

    return decorator


def get_sql_executor(name: str = "duckdb") -> SqlExecutor:
    normalized = _normalize_name(name)
    try:
        factory = _EXECUTORS[normalized]
    except KeyError as exc:
        available = ", ".join(sorted(_EXECUTORS)) or "none"
        raise ValueError(
            f"Unknown SQL executor '{name}'. Available: {available}"
        ) from exc
    return factory()


def execute_sql(project_root: Path, sql: str, executor: str = "duckdb") -> QueryResult:
    return get_sql_executor(executor).execute(project_root, sql)


def _normalize_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    if not normalized:
        raise ValueError("SQL executor name must not be empty")
    return normalized
