"""Rebuild the local SQLite database from the repository's seed CSV files."""

import csv
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "app.db"
SEED_FILES = {
    "tickets": ROOT / "seed" / "tickets.csv",
    "customers": ROOT / "seed" / "customers.csv",
}


def _read_seed(path: Path) -> tuple[list[str], list[list[str]]]:
    """Read a seed CSV, preserving its header names and row values."""
    try:
        with path.open("r", newline="", encoding="utf-8") as source:
            rows = list(csv.reader(source))
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"could not read seed file {path}: {exc}") from exc

    if not rows or not rows[0] or any(not column for column in rows[0]):
        raise RuntimeError(f"seed file {path} has no usable header")
    headers = rows[0]
    if len(set(headers)) != len(headers):
        raise RuntimeError(f"seed file {path} has duplicate column names")

    data = rows[1:]
    for line_number, row in enumerate(data, start=2):
        if len(row) != len(headers):
            raise RuntimeError(
                f"seed file {path} has {len(row)} values on line {line_number}; "
                f"expected {len(headers)}"
            )
    return headers, data


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _replace_table(
    connection: sqlite3.Connection,
    table_name: str,
    headers: list[str],
    rows: list[list[str]],
) -> None:
    table = _quote_identifier(table_name)
    columns = ", ".join(f"{_quote_identifier(header)} TEXT" for header in headers)
    placeholders = ", ".join("?" for _ in headers)

    connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(f"CREATE TABLE {table} ({columns})")
    connection.executemany(
        f"INSERT INTO {table} VALUES ({placeholders})",
        rows,
    )


def load_seed() -> tuple[int, int]:
    """Replace both database tables with the contents of the seed files."""
    seeds = {table: _read_seed(path) for table, path in SEED_FILES.items()}

    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("BEGIN")
            _replace_table(connection, "tickets", *seeds["tickets"])
            _replace_table(connection, "customers", *seeds["customers"])
    except sqlite3.Error as exc:
        raise RuntimeError(f"could not rebuild database {DB_PATH}: {exc}") from exc

    return len(seeds["tickets"][1]), len(seeds["customers"][1])


def main() -> int:
    try:
        ticket_count, customer_count = load_seed()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Loaded {ticket_count} tickets and {customer_count} customers into {DB_PATH}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
