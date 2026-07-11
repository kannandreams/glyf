import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyf.cli import app
from glyf.config import ConfigError, load_config
from glyf.dashboard.generator import generate_dashboards
from glyf.pipeline import render_project
from tests.helpers import write_basic_manifest


runner = CliRunner()


def test_missing_config_uses_defaults(tmp_path: Path) -> None:
    config = load_config(tmp_path)

    assert config.visualisations_path == Path("visualisations")
    assert config.dashboards_path == Path("dashboards")
    assert config.output_path == Path("target/glyf")
    assert config.execution.backend == "duckdb"
    assert config.render.formats == ("svg", "png")
    assert config.render.default_width == 800
    assert config.render.default_height == 400
    assert config.dashboard.embed_charts is True


def test_valid_config_loads_correctly(tmp_path: Path) -> None:
    config_path = tmp_path / "glyf.yml"
    config_path.write_text(
        "visualisations_path: viz\n"
        "dashboards_path: boards\n"
        "output_path: out/glyf\n"
        "compiled_path: out/glyf/sql\n"
        "charts_path: out/glyf/chart-files\n"
        "dashboards_output_path: out/glyf/pages\n"
        "site_path: out/glyf/public\n"
        "execution:\n"
        "  backend: duckdb\n"
        "render:\n"
        "  formats:\n"
        "    - svg\n"
        "  default_width: 640\n"
        "  default_height: 360\n"
        "dashboard:\n"
        "  theme: dark\n"
        "  embed_charts: false\n"
        "  show_compiled_sql: false\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path, config_path)

    assert config.visualisations_path == Path("viz")
    assert config.dashboards_path == Path("boards")
    assert config.compiled_path == Path("out/glyf/sql")
    assert config.execution.backend == "duckdb"
    assert config.render.formats == ("svg",)
    assert config.render.default_width == 640
    assert config.render.default_height == 360
    assert config.dashboard.theme == "dark"
    assert config.dashboard.embed_charts is False
    assert config.dashboard.show_compiled_sql is False


def test_invalid_config_yaml_reports_clear_error(tmp_path: Path) -> None:
    config_path = tmp_path / "glyf.yml"
    config_path.write_text("render: [", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_config(tmp_path, config_path)


def test_custom_paths_are_respected(tmp_path: Path) -> None:
    project = _custom_path_project(tmp_path)
    config = load_config(project, project / "glyf.yml")

    render_project(project, config)
    generate_dashboards(project, config)

    assert (project / "custom_out" / "compiled_sql" / "revenue.sql").exists()
    assert (project / "custom_out" / "chart_artifacts" / "revenue.svg").exists()
    assert not (project / "custom_out" / "chart_artifacts" / "revenue.png").exists()
    assert (project / "custom_out" / "dashboard_pages" / "executive.html").exists()


def test_config_option_works_with_project_dir(tmp_path: Path) -> None:
    project = _custom_path_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "list",
            "--project-dir",
            str(project),
            "--config",
            str(project / "glyf.yml"),
        ],
    )

    assert result.exit_code == 0
    assert "viz/revenue.ggsql" in result.output
    assert "boards/executive.yml" in result.output


def _custom_path_project(tmp_path: Path) -> Path:
    project = tmp_path / "custom"
    shutil.copytree(Path("examples/basic"), project)
    write_basic_manifest(project)
    (project / "visualisations").rename(project / "viz")
    (project / "dashboards").rename(project / "boards")
    (project / "glyf.yml").write_text(
        "visualisations_path: viz\n"
        "dashboards_path: boards\n"
        "output_path: custom_out\n"
        "compiled_path: custom_out/compiled_sql\n"
        "charts_path: custom_out/chart_artifacts\n"
        "dashboards_output_path: custom_out/dashboard_pages\n"
        "site_path: custom_out/site\n"
        "render:\n"
        "  formats:\n"
        "    - svg\n"
        "  default_width: 640\n"
        "  default_height: 360\n",
        encoding="utf-8",
    )
    return project
