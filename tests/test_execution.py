from pathlib import Path

import pytest

from glyf.config import load_config
from glyf.execution import QueryResult, execute_sql, get_sql_executor
from tests.helpers import copy_basic_project


def test_query_result_round_trips_to_pandas() -> None:
    result = QueryResult.from_records(
        columns=("month", "revenue"),
        rows=(
            {"month": "2026-01", "revenue": 1200},
            {"month": "2026-02", "revenue": 1800},
        ),
    )

    arrow_table = result.to_arrow()
    polars_frame = result.to_polars()
    frame = result.to_pandas()

    assert arrow_table.column_names == ["month", "revenue"]
    assert polars_frame.columns == ["month", "revenue"]
    assert list(frame.columns) == ["month", "revenue"]
    assert frame.to_dict(orient="records") == list(result.rows)


def test_get_sql_executor_returns_duckdb_by_default() -> None:
    executor = get_sql_executor()

    assert executor.__class__.__name__ == "AdbcDuckDbExecutor"


def test_unknown_sql_executor_reports_available_options() -> None:
    with pytest.raises(ValueError, match="Unknown SQL executor 'missing'"):
        get_sql_executor("missing")


def test_execute_sql_accepts_named_executor(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = execute_sql(
        project,
        "select month, revenue from main.fct_orders order by month",
        executor="duckdb",
    )

    assert result.columns == ("month", "revenue")
    assert list(result.rows) == [
        {"month": "2026-01", "revenue": 1200},
        {"month": "2026-02", "revenue": 1800},
        {"month": "2026-03", "revenue": 2100},
        {"month": "2026-04", "revenue": 2400},
    ]


def test_execute_sql_supports_duckdb_dbapi_fallback(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = execute_sql(
        project,
        "select month, revenue from main.fct_orders order by month",
        executor="duckdb_dbapi",
    )

    assert result.columns == ("month", "revenue")
    assert len(result) == 4


def test_config_loads_execution_backend(tmp_path: Path) -> None:
    config_path = tmp_path / "glyf.yml"
    config_path.write_text(
        "execution:\n"
        "  backend: duckdb\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path, config_path)

    assert config.execution.backend == "duckdb"
