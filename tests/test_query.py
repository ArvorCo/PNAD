import io
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pnad import main  # type: ignore


def _build_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE base (uf TEXT, renda REAL, peso REAL)")
        conn.executemany(
            "INSERT INTO base (uf, renda, peso) VALUES (?, ?, ?)",
            [
                ("SP", 4000.0, 2.0),
                ("SP", 2000.0, 1.0),
                ("RJ", 2500.0, 1.0),
                ("BA", 1500.0, 1.0),
            ],
        )
        conn.commit()


def test_query_json_default(capsys, tmp_path: Path):
    db = tmp_path / "sample.sqlite"
    _build_db(db)

    rc = main(
        [
            "query",
            "--db",
            str(db),
            "--sql",
            "SELECT uf, ROUND(AVG(renda), 2) AS renda_media FROM base GROUP BY uf ORDER BY renda_media DESC",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["columns"] == ["uf", "renda_media"]
    assert payload["rows"][0]["uf"] == "SP"
    assert payload["read_only"] is True


def test_query_table_output_and_truncate(capsys, tmp_path: Path):
    db = tmp_path / "sample.sqlite"
    _build_db(db)

    rc = main(
        [
            "query",
            "--db",
            str(db),
            "--sql",
            "SELECT uf, renda FROM base ORDER BY renda DESC",
            "--format",
            "table",
            "--max-rows",
            "2",
            "--no-color",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "PNAD QUERY" in out
    assert "| uf" in out
    assert "[truncated]" in out


def test_query_rejects_write_by_default(capsys, tmp_path: Path):
    db = tmp_path / "sample.sqlite"
    _build_db(db)

    rc = main(["query", "--db", str(db), "--sql", "DELETE FROM base"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "read-only" in err.lower()


def test_query_sql_file_and_stdin(capsys, tmp_path: Path, monkeypatch):
    db = tmp_path / "sample.sqlite"
    _build_db(db)

    sql_file = tmp_path / "q.sql"
    sql_file.write_text("SELECT COUNT(*) AS n FROM base", encoding="utf-8")
    rc = main(["query", "--db", str(db), "--sql-file", str(sql_file)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"][0]["n"] == 4

    monkeypatch.setattr(sys, "stdin", io.StringIO("SELECT 1 AS x"))
    rc = main(["query", "--db", str(db)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"][0]["x"] == 1
