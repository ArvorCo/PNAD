from pathlib import Path
from tempfile import TemporaryDirectory
import csv

import sys
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from npv_deflators import read_ipca_csv, build_deflators, apply_deflator_to_csv  # type: ignore


def test_build_deflators_from_sample():
    ipca_path = Path("samples/ipca_sample.csv")
    ipca = read_ipca_csv(ipca_path)
    assert ipca["2025-06"] == 100.0
    assert ipca["2025-07"] == 101.0

    factors = build_deflators(ipca, target="2025-07")
    assert round(factors["2025-07"], 8) == 1.0
    assert round(factors["2025-06"], 8) == round(101.0 / 100.0, 8)
    assert round(factors["2025-03"], 8) == round(101.0 / 95.0, 8)


def test_apply_deflator_streams_and_emits_columns(tmp_path: Path):
    # Input CSV with Ano/Trimestre and two income columns
    inp = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    rows = [
        {
            "Ano__ano_de_referncia": "2025",
            "Trimestre__trimestre_de_referncia": "2",
            "VD4019__rendim_habitual_qq_trabalho": "1000",
            "VD4020__rendim_efetivo_qq_trabalho": "500",
        },
        {
            "Ano__ano_de_referncia": "2025",
            "Trimestre__trimestre_de_referncia": "3",
            "VD4019__rendim_habitual_qq_trabalho": "2000",
            "VD4020__rendim_efetivo_qq_trabalho": "1000",
        },
    ]
    with inp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    ipca = read_ipca_csv(Path("samples/ipca_sample.csv"))
    factors = build_deflators(ipca, target="2025-07")

    cols = [
        "VD4019__rendim_habitual_qq_trabalho",
        "VD4020__rendim_efetivo_qq_trabalho",
    ]
    apply_deflator_to_csv(inp, out, factors, cols, target_label="jul2025", min_wage=1518.0)

    with out.open("r", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        out_rows = list(r)

    # Row 1: quarter 2 => month 06 -> factor 101/100 = 1.01
    r1 = out_rows[0]
    adj1 = float(r1["VD4019__rendim_habitual_qq_trabalho_jul2025"])  # 1000 * 1.01
    assert round(adj1, 2) == 1010.00
    mw1 = float(r1["VD4019__rendim_habitual_qq_trabalho_mw"])  # 1010/1518
    assert round(mw1, 6) == round(1010.0 / 1518.0, 6)

    # Row 2: quarter 3 => month 09 missing from sample -> expect blank
    r2 = out_rows[1]
    assert r2["VD4019__rendim_habitual_qq_trabalho_jul2025"] == ""
    assert r2["VD4019__rendim_habitual_qq_trabalho_mw"] == ""
