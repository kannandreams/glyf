# glyf

[![Tests](https://github.com/kannandreams/glyf/actions/workflows/test.yml/badge.svg)](https://github.com/kannandreams/glyf/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/kannandreams/glyf/branch/main/graph/badge.svg)](https://codecov.io/gh/kannandreams/glyf)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](/Users/atlas/Documents/orbital/forge/glyf/pyproject.toml)
[![Rust 1.83+](https://img.shields.io/badge/rust-1.83%2B-DEA584.svg?logo=rust&logoColor=white)](/Users/atlas/Documents/orbital/forge/glyf/crates/glyf-core/Cargo.toml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Open Source Visualization build tool to data pipeline.

`glyf` turns analytical metadata and SQL-first visualisation files into
versioned chart artifacts and static dashboards. Its first integration reads dbt
project artifacts, resolves dbt `ref()` and `source()` calls from
`target/manifest.json`, executes chart SQL with DuckDB, renders PNG/SVG charts
with Altair, and exports publishable dashboard sites.

`glyf` is artifact-driven, not dbt-runtime-driven. Run dbt first, then run
`glyf` against the resulting artifacts and relations.


## Installation

Install from a GitHub Release wheel:

```bash
uv tool install \
  https://github.com/kannandreams/glyf/releases/download/v0.2.0/glyf-0.2.0-<platform>.whl
```

Replace `<platform>` with the wheel asset that matches your OS and architecture.

PyPI publishing is intentionally deferred for now.

When developing from this repository, install dependencies with `uv`:

```bash
uv sync
```

For the included dbt examples, dev dependencies include `dbt-core` and
`dbt-duckdb`.

## CI Run

This project uses Taskfile to run the same checks locally and in GitHub Actions.
Install Task before running these commands:

```bash
brew install go-task
task --version
```

Run the full CI pipeline:

```bash
task ci
```

Run CI with a specific Python version:

```bash
task ci PYTHON_VERSION=3.12
```

Run individual CI steps:

```bash
task install
task test
task coverage
task build
task dashboard-ci
```

`task test` runs pytest with coverage and writes `coverage.xml`; CI uploads that
report to Codecov for the README coverage badge.

## Copy-Paste Quickstart

In a dbt project:

```bash
glyf init
dbt build
glyf doctor
glyf build
glyf serve
```

For the included example project:

```bash
uv sync
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run glyf build
uv run glyf serve
```

This creates the example DuckDB database at
`examples/simple_dbt/target/simple_dbt.duckdb`.

Open:

```text
examples/simple_dbt/target/glyf/site/index.html
```

## CLI

High-level workflow commands:

```bash
uv run glyf init
uv run glyf doctor
uv run glyf build
uv run glyf serve
```

Low-level control commands:

```bash
uv run glyf list
uv run glyf validate
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean --zip
```

Point at another project:

```bash
uv run glyf build --project-dir examples/sales_dashboard
```

Preview a generated dashboard locally:

```bash
uv run glyf build --project-dir examples/simple_dbt
uv run glyf serve --project-dir examples/simple_dbt
uv run glyf serve --project-dir examples/simple_dbt --host 127.0.0.1 --port 8080
```

## Example Output

Generated files are written under `target/glyf/`:

```text
target/glyf/
  compiled/
  charts/
  dashboards/
  site/
  index.html
```

The publish-ready site lives in:

```text
target/glyf/site/
```

## Examples

See [examples/README.md](examples/README.md).

- `examples/simple_dbt`
- `examples/sales_dashboard`
- `examples/product_analytics`
- `examples/finance_metrics`

## Documentation

The Docusaurus docs site source lives in [docs-site](docs-site/). It is intended
to be the primary documentation experience with a landing page, quickstart,
examples gallery, command reference, integrations, AI context, and community
resources.

Run it locally after installing Node.js:

```bash
cd docs-site
npm install
npm start
```

Existing Markdown docs are still available while the site is being introduced:

- [Getting started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Visualisation syntax](docs/visualisation-syntax.md)
- [Dashboard YAML](docs/dashboard-yaml.md)
- [dbt integration](docs/dbt-integration.md)
- [CI/CD](docs/ci-cd.md)
- [Release process](docs/release.mdxplain)
- [Troubleshooting](docs/troubleshooting.md)

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the detailed future roadmap.

Near-term themes:

- richer chart syntax while keeping the parser small
- more dashboard layouts
- better error messages for dbt adapter-specific execution failures
- snapshot tests for generated HTML
- optional publish helpers for common static hosts
- local `serve` and `watch` workflows after the release baseline is stable
