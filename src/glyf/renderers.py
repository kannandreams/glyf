from collections.abc import Callable
from pathlib import Path

from glyf.config import RenderConfig
from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart

ChartRenderer = Callable[
    [GgsqlChart, QueryResult, Path, Path, RenderConfig, Path | None],
    None,
]

_RENDERERS: dict[str, ChartRenderer] = {}


def chart_renderer(name: str) -> Callable[[ChartRenderer], ChartRenderer]:
    """Register a Python renderer for custom chart output."""

    normalized = _normalize_name(name)

    def decorator(func: ChartRenderer) -> ChartRenderer:
        _RENDERERS[normalized] = func
        return func

    return decorator


def get_chart_renderer(name: str = "altair") -> ChartRenderer:
    normalized = _normalize_name(name)
    try:
        return _RENDERERS[normalized]
    except KeyError as exc:
        available = ", ".join(sorted(_RENDERERS)) or "none"
        raise ValueError(f"Unknown chart renderer '{name}'. Available: {available}") from exc


def _normalize_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    if not normalized:
        raise ValueError("Renderer name must not be empty")
    return normalized
