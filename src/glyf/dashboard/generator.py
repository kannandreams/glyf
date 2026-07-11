from dataclasses import dataclass, replace
from pathlib import Path

from glyf.bundle import write_bundle_manifest
from glyf.config import GlyfConfig
from glyf.dashboard.artifacts import (
    ChartArtifact,
    ChartArtifactError,
)
from glyf.dashboard.loader import Dashboard, load_dashboard
from glyf.dashboard.macros import (
    DashboardMacroError,
    MacroContext,
    DashboardMacroRegistry,
    resolve_dashboard_components,
)
from glyf.dashboard.renderer import DashboardBuildMeta, DashboardRenderer
from glyf.output.paths import artifact_paths
from glyf.project.scanner import ProjectScan, scan_project


class DashboardGenerationError(ValueError):
    """Raised when static dashboard HTML cannot be generated."""


@dataclass(frozen=True)
class GeneratedDashboard:
    dashboard: Dashboard
    path: Path
    charts: tuple[ChartArtifact, ...]


@dataclass(frozen=True)
class DashboardGenerationResult:
    scan: ProjectScan
    dashboards: tuple[GeneratedDashboard, ...]
    index_path: Path


def generate_dashboards(
    project: Path,
    config: GlyfConfig | None = None,
) -> DashboardGenerationResult:
    config = config or GlyfConfig()
    scan = scan_project(project, config)
    paths = artifact_paths(scan.root, config)
    paths.dashboards_dir.mkdir(parents=True, exist_ok=True)
    renderer = DashboardRenderer()
    assets = renderer.prepare_assets(paths.root)
    build_meta = DashboardBuildMeta.now()
    macro_context = MacroContext(scan.root, config)

    dashboards: list[GeneratedDashboard] = []
    for dashboard_path in scan.dashboard_files:
        try:
            dashboard = load_dashboard(dashboard_path)
        except ValueError as exc:
            rel_path = dashboard_path.relative_to(scan.root).as_posix()
            raise DashboardGenerationError(f"{rel_path}: {exc}") from exc
        try:
            _preload_artifacts(dashboard, macro_context)
            dashboard = _resolve_dashboard_filters(dashboard, macro_context)
            macro_registry = DashboardMacroRegistry.from_project(
                scan.dashboards_dir,
                macro_context,
            )
            dashboard = resolve_dashboard_components(dashboard, macro_registry)
        except DashboardMacroError as exc:
            rel_path = dashboard_path.relative_to(scan.root).as_posix()
            raise DashboardGenerationError(f"{rel_path}: {exc}") from exc
        except ChartArtifactError as exc:
            rel_path = dashboard_path.relative_to(scan.root).as_posix()
            raise DashboardGenerationError(f"{rel_path}: {exc}") from exc

        chart_artifacts = {}
        for chart_name in dashboard.chart_names:
            try:
                artifact = macro_context.chart_artifact(chart_name)
                if artifact is None:
                    raise DashboardGenerationError(
                        f"dashboard '{dashboard.name}' could not load chart artifact '{chart_name}'"
                    )
                chart_artifacts[chart_name] = artifact
            except ChartArtifactError as exc:
                rel_path = dashboard_path.relative_to(scan.root).as_posix()
                raise DashboardGenerationError(f"{rel_path}: {exc}") from exc

        ordered_chart_artifacts = tuple(
            chart_artifacts[chart_name] for chart_name in dashboard.chart_names
        )

        output_path = paths.dashboards_dir / f"{dashboard.name}.html"
        output_path.write_text(
            renderer.render_dashboard(
                dashboard,
                chart_artifacts,
                ordered_chart_artifacts,
                config,
                assets,
                build_meta,
            ).html,
            encoding="utf-8",
        )
        dashboards.append(
            GeneratedDashboard(
                dashboard=dashboard,
                path=output_path,
                charts=ordered_chart_artifacts,
            )
        )

    index_path = paths.root / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        renderer.render_index(tuple(dashboards), assets),
        encoding="utf-8",
    )
    write_bundle_manifest(
        scan.root,
        config=config,
        generated_at=build_meta.generated_at_iso,
        dashboards=tuple(dashboards),
    )

    return DashboardGenerationResult(
        scan=scan,
        dashboards=tuple(dashboards),
        index_path=index_path,
    )


def _preload_artifacts(dashboard: Dashboard, macro_context: MacroContext) -> None:
    for chart_name in dashboard.artifact_chart_names:
        artifact = macro_context.chart_artifact(chart_name)
        assert artifact is not None


def _resolve_dashboard_filters(
    dashboard: Dashboard,
    macro_context: MacroContext,
) -> Dashboard:
    resolved_filters = []
    for filter_spec in dashboard.filters:
        if not filter_spec.is_sourced:
            resolved_filters.append(filter_spec)
            continue
        assert filter_spec.source_chart is not None
        assert filter_spec.source_field is not None
        values = tuple(
            str(value).strip()
            for value in macro_context.source(
                filter_spec.source_chart,
                filter_spec.source_field,
            )
            if str(value).strip()
        )
        resolved_filters.append(
            replace(
                filter_spec,
                values=tuple(dict.fromkeys(values)),
            )
        )
    return replace(dashboard, filters=tuple(resolved_filters))
