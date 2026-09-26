import csv
import importlib.util
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOADER = ROOT / "load_seed.py"


def _seed_contents(filename: str) -> tuple[list[str], list[list[str]]]:
    with (ROOT / "seed" / filename).open(newline="", encoding="utf-8") as source:
        rows = list(csv.reader(source))
    return rows[0], rows[1:]


def _database_contents() -> dict[str, tuple[list[str], list[tuple[str, ...]]]]:
    with sqlite3.connect(ROOT / "app.db") as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        contents = {}
        for table in ("tickets", "customers"):
            columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
            rows = connection.execute(f"SELECT * FROM {table}").fetchall()
            contents[table] = columns, rows
    assert tables == {"tickets", "customers"}
    return contents


def test_loader_creates_tables_with_seed_columns_and_rows() -> None:
    result = subprocess.run(
        [sys.executable, str(LOADER)], cwd=ROOT, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr
    database = _database_contents()
    for table, filename in (("tickets", "tickets.csv"), ("customers", "customers.csv")):
        headers, seed_rows = _seed_contents(filename)
        columns, rows = database[table]
        assert columns == headers
        assert rows == [tuple(row) for row in seed_rows]


def test_loader_replaces_existing_tables_without_duplicates() -> None:
    first = subprocess.run(
        [sys.executable, str(LOADER)], cwd=ROOT, capture_output=True, text=True
    )
    assert first.returncode == 0, first.stderr
    initial = _database_contents()

    second = subprocess.run(
        [sys.executable, str(LOADER)], cwd=ROOT, capture_output=True, text=True
    )
    assert second.returncode == 0, second.stderr
    assert _database_contents() == initial


def test_loader_fails_clearly_when_a_seed_file_is_missing(tmp_path: Path) -> None:
    temporary_root = tmp_path / "repo"
    (temporary_root / "seed").mkdir(parents=True)
    shutil.copy2(LOADER, temporary_root / LOADER.name)
    shutil.copy2(ROOT / "seed" / "tickets.csv", temporary_root / "seed" / "tickets.csv")

    result = subprocess.run(
        [sys.executable, str(temporary_root / LOADER.name)],
        cwd=temporary_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "could not read seed file" in result.stderr
    assert "customers.csv" in result.stderr
    assert "Loaded " not in result.stdout


def test_loader_fails_clearly_when_a_seed_file_is_unreadable(tmp_path: Path) -> None:
    temporary_root = tmp_path / "repo"
    (temporary_root / "seed").mkdir(parents=True)
    shutil.copy2(LOADER, temporary_root / LOADER.name)
    shutil.copy2(ROOT / "seed" / "tickets.csv", temporary_root / "seed" / "tickets.csv")
    (temporary_root / "seed" / "customers.csv").mkdir()

    result = subprocess.run(
        [sys.executable, str(temporary_root / LOADER.name)],
        cwd=temporary_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "could not read seed file" in result.stderr
    assert "customers.csv" in result.stderr
    assert "Loaded " not in result.stdout


def test_mcp_queries_work_after_loading_seed() -> None:
    result = subprocess.run(
        [sys.executable, str(LOADER)], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr

    server_path = ROOT / "mcp" / "triage_server.py"
    spec = importlib.util.spec_from_file_location("local_triage_server", server_path)
    assert spec is not None and spec.loader is not None
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)

    assert server.get_ticket("T-1042")["customer_id"] == "C-77"
    assert server.get_customer_history("C-77")["ticket_ids"]
