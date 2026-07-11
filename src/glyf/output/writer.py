import json
from dataclasses import dataclass
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart
from glyf.output.paths import artifact_paths


@dataclass(frozen=True)
class ChartArtifacts:
    compiled_sql: Path
    metadata_json: Path
    data_json: Path
    png: Path
    svg: Path
    vega_json: Path


def chart_artifact_paths(
    project_root: Path,
    chart: GgsqlChart,
    config: GlyfConfig | None = None,
) -> ChartArtifacts:
    paths = artifact_paths(project_root, config)
    paths.compiled_dir.mkdir(parents=True, exist_ok=True)
    paths.charts_dir.mkdir(parents=True, exist_ok=True)
    paths.normalized_data_dir.mkdir(parents=True, exist_ok=True)
    paths.vega_data_dir.mkdir(parents=True, exist_ok=True)

    return ChartArtifacts(
        compiled_sql=paths.compiled_dir / f"{chart.name}.sql",
        metadata_json=paths.charts_dir / f"{chart.name}.json",
        data_json=paths.normalized_data_dir / f"{chart.name}.data.json",
        png=paths.charts_dir / f"{chart.name}.png",
        svg=paths.charts_dir / f"{chart.name}.svg",
        vega_json=paths.vega_data_dir / f"{chart.name}.vega.json",
    )


def write_compiled_sql(compiled_path: Path, compiled_sql: str) -> None:
    compiled_path.parent.mkdir(parents=True, exist_ok=True)
    compiled_path.write_text(compiled_sql.strip() + "\n", encoding="utf-8")


def write_chart_metadata(project_root: Path, chart: GgsqlChart, artifacts: ChartArtifacts) -> None:
    metadata = {
        "name": chart.name,
        "title": chart.title,
        "chart_type": chart.draw_type,
        "x": chart.field_for_role("x"),
        "y": chart.field_for_role("y"),
        "compiled_sql_path": artifacts.compiled_sql.relative_to(project_root).as_posix(),
        "data_json_path": artifacts.data_json.relative_to(project_root).as_posix(),
        "metadata_path": artifacts.metadata_json.relative_to(project_root).as_posix(),
        "png_path": artifacts.png.relative_to(project_root).as_posix(),
        "svg_path": artifacts.svg.relative_to(project_root).as_posix(),
    }
    if chart.is_interactive:
        metadata["interactions"] = list(chart.interactions)
        metadata["vega_json_path"] = artifacts.vega_json.relative_to(
            project_root
        ).as_posix()
    artifacts.metadata_json.parent.mkdir(parents=True, exist_ok=True)
    artifacts.metadata_json.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_chart_data(
    project_root: Path,
    chart: GgsqlChart,
    artifacts: ChartArtifacts,
    data: QueryResult,
) -> None:
    payload = {
        "name": chart.name,
        "fields": list(data.columns),
        "rows": list(data.rows),
    }
    artifacts.data_json.parent.mkdir(parents=True, exist_ok=True)
    artifacts.data_json.write_text(
        json.dumps(payload, indent=2, default=str, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def cleanup_legacy_chart_artifacts(project_root: Path, chart: GgsqlChart, config: GlyfConfig | None = None) -> None:
    paths = artifact_paths(project_root, config)
    legacy_paths = (
        paths.charts_dir / f"{chart.name}.data.json",
        paths.charts_dir / f"{chart.name}.vega.json",
    )
    for legacy_path in legacy_paths:
        if legacy_path.exists():
            legacy_path.unlink()
