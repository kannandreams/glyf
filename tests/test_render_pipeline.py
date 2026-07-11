import json
from pathlib import Path

import duckdb
import pytest

from glyf.execution import execute_sql
from glyf.pipeline import RenderError, render_project
from tests.helpers import copy_basic_project


def test_render_project_writes_compiled_sql_and_artifacts(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = render_project(project)

    assert len(result.charts) == 1
    assert result.charts[0].data.columns == ("month", "revenue")

    compiled_sql = project / "target" / "glyf" / "compiled" / "revenue.sql"
    metadata_json = project / "target" / "glyf" / "charts" / "revenue.json"
    data_json = project / "target" / "glyf" / "data" / "normalized" / "revenue.data.json"
    png = project / "target" / "glyf" / "charts" / "revenue.png"
    svg = project / "target" / "glyf" / "charts" / "revenue.svg"

    assert compiled_sql.read_text(encoding="utf-8") == (
        "SELECT month, revenue\nFROM main.fct_orders\n"
    )
    assert json.loads(metadata_json.read_text(encoding="utf-8")) == {
        "name": "revenue",
        "chart_type": "line",
        "compiled_sql_path": "target/glyf/compiled/revenue.sql",
        "data_json_path": "target/glyf/data/normalized/revenue.data.json",
        "metadata_path": "target/glyf/charts/revenue.json",
        "png_path": "target/glyf/charts/revenue.png",
        "svg_path": "target/glyf/charts/revenue.svg",
        "title": "Monthly Revenue",
        "x": "month",
        "y": "revenue",
    }
    assert json.loads(data_json.read_text(encoding="utf-8")) == {
        "name": "revenue",
        "fields": ["month", "revenue"],
        "rows": [
            {"month": "2026-01", "revenue": 1200},
            {"month": "2026-02", "revenue": 1800},
            {"month": "2026-03", "revenue": 2100},
            {"month": "2026-04", "revenue": 2400},
        ],
    }
    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "<svg" in svg.read_text(encoding="utf-8")
    assert "Monthly Revenue" in svg.read_text(encoding="utf-8")
    assert 'font-family="Hanken Grotesk"' in svg.read_text(encoding="utf-8")
    assert 'font-size="15px"' in svg.read_text(encoding="utf-8")


def test_duckdb_execution_loads_seed_tables(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    data = execute_sql(
        project,
        "select month, revenue from main.fct_orders order by month",
    )

    assert list(data.rows) == [
        {"month": "2026-01", "revenue": 1200},
        {"month": "2026-02", "revenue": 1800},
        {"month": "2026-03", "revenue": 2100},
        {"month": "2026-04", "revenue": 2400},
    ]


def test_render_project_writes_interactive_metadata_and_vega_json(
    tmp_path: Path,
) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, revenue from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW line\n"
        "INTERACT tooltip, zoom\n",
        encoding="utf-8",
    )

    render_project(project)

    metadata_json = project / "target" / "glyf" / "charts" / "revenue.json"
    metadata = json.loads(metadata_json.read_text(encoding="utf-8"))
    assert metadata["interactions"] == ["tooltip", "zoom"]
    assert metadata["vega_json_path"] == "target/glyf/data/vega/revenue.vega.json"
    assert (project / metadata["vega_json_path"]).exists()
    vega_json = json.loads((project / metadata["vega_json_path"]).read_text(encoding="utf-8"))
    assert vega_json["config"]["axis"]["labelFont"] == "Hanken Grotesk"
    assert vega_json["config"]["title"]["font"] == "Hanken Grotesk"


def test_duckdb_execution_uses_project_target_database(tmp_path: Path) -> None:
    project = tmp_path / "simple_dbt"
    project.mkdir()
    target_dir = project / "target"
    target_dir.mkdir()
    database = target_dir / "simple_dbt.duckdb"
    with duckdb.connect(database.as_posix()) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS main")
        connection.execute(
            "CREATE TABLE main.fct_orders AS "
            "SELECT '2026-01' AS month, 1200 AS revenue"
        )

    data = execute_sql(
        project,
        'select month, revenue from "simple_dbt"."main"."fct_orders"',
    )

    assert list(data.rows) == [
        {"month": "2026-01", "revenue": 1200}
    ]


def test_render_project_reports_unsupported_chart_type(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, revenue from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW heatmap\n",
        encoding="utf-8",
    )

    with pytest.raises(RenderError, match="unsupported chart type 'heatmap'"):
        render_project(project)
