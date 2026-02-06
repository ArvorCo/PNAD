import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pnad import build_sqlite_from_csv, main, _resolve_pipeline_target_and_min_wage  # type: ignore


def test_build_sqlite_from_csv(tmp_path: Path):
    inp = tmp_path / "sample.csv"
    db = tmp_path / "sample.sqlite"

    with inp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "amount", "name"])
        w.writerow(["1", "10.5", "Ana"])
        w.writerow(["2", "20.0", "Bruno"])

    result = build_sqlite_from_csv(inp, db, table="sample_table")
    assert result["rows"] == 2

    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM sample_table").fetchone()[0]
        assert rows == 2


def test_main_legacy_passthrough(tmp_path: Path):
    inp = tmp_path / "in.csv"
    inp.write_text("id;name\n1;Ana\n", encoding="utf-8")

    rc = main(["inspect", str(inp)])
    assert rc == 0


def test_resolve_pipeline_target_and_min_wage_auto(tmp_path: Path):
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"
    with ipca.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "index"])
        w.writerow(["2025-11", "100"])
        w.writerow(["2025-12", "101"])
    with sm.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "value"])
        w.writerow(["2025-11", "1518"])
        w.writerow(["2025-12", "1518"])

    target, mw, month_used = _resolve_pipeline_target_and_min_wage(
        target_arg="",
        min_wage_arg=None,
        ipca_csv=ipca,
        salario_minimo_csv=sm,
    )
    assert target == "2025-12"
    assert mw == 1518.0
    assert month_used == "2025-12"


def test_resolve_pipeline_target_and_min_wage_override(tmp_path: Path):
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"
    with ipca.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "index"])
        w.writerow(["2025-12", "101"])
    with sm.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "value"])
        w.writerow(["2025-12", "1518"])

    target, mw, month_used = _resolve_pipeline_target_and_min_wage(
        target_arg="2025-12",
        min_wage_arg=2000.0,
        ipca_csv=ipca,
        salario_minimo_csv=sm,
    )
    assert target == "2025-12"
    assert mw == 2000.0
    assert month_used == "2025-12"
