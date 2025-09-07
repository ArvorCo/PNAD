from pathlib import Path
import csv

import sys
from pathlib import Path as _Path
ROOT = _Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_income import cmd_vd4020_components, cmd_vd4020_vs_principal  # type: ignore


def test_vd4020_components(tmp_path: Path, capsys):
    # Create synthetic input where VD4020 = comp1 + comp2 exactly
    inp = tmp_path / "in.csv"
    rows = [
        {"VD4020__rendim": "1500", "A": "1000", "B": "500"},
        {"VD4020__rendim": "2000", "A": "1000", "B": "800"},  # mismatch
        {"VD4020__rendim": "",     "A": "100",  "B": "50"},     # no target
    ]
    with inp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["VD4020__rendim", "A", "B"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    args = type("Args", (), {"inp": inp, "target": "VD4020__rendim", "components": "A,B", "tol": 0.5, "limit": 0})
    rc = cmd_vd4020_components(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert '"rows_with_target_and_any_component": 2' in out
    assert '"matches_within_tol": 1' in out


def test_vd4020_vs_principal(tmp_path: Path, capsys):
    inp = tmp_path / "in.csv"
    rows = [
        {"VD4020": "1000", "VD4017": "1000", "V405912": ""},     # equal, no secondary
        {"VD4020": "1200", "VD4017": "1000", "V405912": "200"},  # >=, secondary exists
        {"VD4020": "900",  "VD4017": "1000", "V405912": ""},     # < principal (bad)
    ]
    with inp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["VD4020", "VD4017", "V405912"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    args = type("Args", (), {
        "inp": inp,
        "target": "VD4020",
        "principal": "VD4017",
        "secondary_money": "V405912",
        "tol": 0.5,
        "limit": 0,
    })
    rc = cmd_vd4020_vs_principal(args)
    assert rc == 0
    out = capsys.readouterr().out
    # comparable rows: 3
    assert '"rows_comparable": 3' in out
    # vd4020 >= principal: 2/3
    assert '"vd4020_ge_principal_rate": 0.6666666666666666' in out
    # rows without secondary money: rows 1 and 3 (2 rows), equal_when_no_secondary_rate: 1/2
    assert '"rows_without_secondary_money": 2' in out
    assert '"equal_when_no_secondary_rate": 0.5' in out
