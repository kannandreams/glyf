from pathlib import Path

import duckdb

from glyf.execution.base import SqlExecutionError, sql_executor
from glyf.execution.result import QueryResult


class DuckDbExecutor:
    def execute(self, project_root: Path, sql: str) -> QueryResult:
        database = _duckdb_database(project_root)
        try:
            with duckdb.connect(database=database) as connection:
                if database == ":memory:":
                    _load_seed_tables(connection, project_root / "seeds")
                return QueryResult.from_pandas(connection.execute(sql).fetchdf())
        except duckdb.Error as exc:
            raise SqlExecutionError(str(exc)) from exc


@sql_executor("duckdb_dbapi")
def _duckdb_executor() -> DuckDbExecutor:
    return DuckDbExecutor()


def _duckdb_database(project_root: Path) -> str:
    database_name = f"{project_root.name}.duckdb"
    for database_path in (
        project_root / "target" / database_name,
        project_root / database_name,
    ):
        if database_path.exists():
            return database_path.as_posix()
    return ":memory:"


def _load_seed_tables(connection: object, seeds_dir: Path) -> None:
    if not seeds_dir.exists():
        return

    for csv_path in sorted(seeds_dir.glob("*.csv")):
        table_name = _quote_identifier(csv_path.stem)
        csv_literal = _quote_literal(csv_path.as_posix())
        connection.execute(
            f"CREATE OR REPLACE VIEW {table_name} AS "
            f"SELECT * FROM read_csv_auto({csv_literal}, header = true)"
        )


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
