import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pnad import main  # type: ignore


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for row in rows:
            w.writerow(row)


def test_renda_por_faixa_sm_country(capsys, tmp_path: Path):
    inp = tmp_path / "base_labeled.csv"
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"

    _write_csv(
        inp,
        [
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "35",
                "UF_label": "Sao Paulo",
                "dom_id": "d1",
                "V1028": "100",
                "VD4020__rendim_efetivo_qq_trabalho": "1000",
            },
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "35",
                "UF_label": "Sao Paulo",
                "dom_id": "d1",
                "V1028": "100",
                "VD4020__rendim_efetivo_qq_trabalho": "",
            },
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "33",
                "UF_label": "Rio de Janeiro",
                "dom_id": "d2",
                "V1028": "50",
                "VD4020__rendim_efetivo_qq_trabalho": "6000",
            },
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "33",
                "UF_label": "Rio de Janeiro",
                "dom_id": "d3",
                "V1028": "10",
                "VD4020__rendim_efetivo_qq_trabalho": "30000",
            },
        ],
    )
    _write_csv(ipca, [{"date": "2025-06", "index": "100"}, {"date": "2025-07", "index": "110"}])
    _write_csv(sm, [{"date": "2025-06", "value": "1518.00"}])

    rc = main(
        [
            "renda-por-faixa-sm",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--target",
            "2025-07",
            "--ranges",
            "0-2;2-5;5-10;10+",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert payload["group_by"] == "pais"
    assert payload["sm_reference_value"] > 0
    assert "ranges_money" in payload
    assert "R$" in payload["ranges_money"][0]["money_label"]
    assert len(payload["groups"]) == 1
    g = payload["groups"][0]
    assert abs(g["households_total"] - 160.0) < 1e-9
    assert abs(g["persons_total"] - 260.0) < 1e-9
    assert g["households_sample"] == 3
    assert g["persons_sample"] == 4

    by_band = {x["range"]: x for x in g["bands"]}
    assert abs(by_band["0-2"]["households"] - 100.0) < 1e-9
    assert abs(by_band["2-5"]["households"] - 50.0) < 1e-9
    assert abs(by_band["5-10"]["households"] - 0.0) < 1e-9
    assert abs(by_band["10+"]["households"] - 10.0) < 1e-9
    assert abs(by_band["0-2"]["households_pct"] - 62.5) < 1e-6
    assert abs(by_band["2-5"]["households_pct"] - 31.25) < 1e-6
    assert abs(by_band["10+"]["households_pct"] - 6.25) < 1e-6

    assert abs(by_band["0-2"]["persons"] - 200.0) < 1e-9
    assert abs(by_band["2-5"]["persons"] - 50.0) < 1e-9
    assert abs(by_band["10+"]["persons"] - 10.0) < 1e-9
    assert abs(by_band["0-2"]["persons_pct"] - 76.9231) < 1e-4
    assert abs(by_band["2-5"]["persons_pct"] - 19.2308) < 1e-4
    assert abs(by_band["10+"]["persons_pct"] - 3.8462) < 1e-4


def test_renda_por_faixa_sm_group_by_uf_and_filter(capsys, tmp_path: Path):
    inp = tmp_path / "base_labeled.csv"
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"

    _write_csv(
        inp,
        [
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "35",
                "UF_label": "Sao Paulo",
                "dom_id": "d1",
                "V1028": "100",
                "VD4020__rendim_efetivo_qq_trabalho": "2000",
            },
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "33",
                "UF_label": "Rio de Janeiro",
                "dom_id": "d2",
                "V1028": "10",
                "VD4020__rendim_efetivo_qq_trabalho": "2000",
            },
        ],
    )
    _write_csv(ipca, [{"date": "2025-06", "index": "100"}, {"date": "2025-07", "index": "110"}])
    _write_csv(sm, [{"date": "2025-06", "value": "1518.00"}])

    rc = main(
        [
            "renda-por-faixa-sm",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--target",
            "2025-07",
            "--ranges",
            "0-2;2-5;5-10;10+",
            "--group-by",
            "uf",
            "--state",
            "35",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert payload["group_by"] == "uf"
    assert len(payload["groups"]) == 1
    assert payload["groups"][0]["group"] == "35"


def test_renda_por_faixa_sm_requires_weight_by_default(capsys, tmp_path: Path):
    inp = tmp_path / "base_labeled.csv"
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"

    _write_csv(
        inp,
        [
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "35",
                "UF_label": "Sao Paulo",
                "dom_id": "d1",
                "VD4020__rendim_efetivo_qq_trabalho": "2000",
            }
        ],
    )
    _write_csv(ipca, [{"date": "2025-06", "index": "100"}, {"date": "2025-07", "index": "110"}])
    _write_csv(sm, [{"date": "2025-06", "value": "1518.00"}])

    rc = main(
        [
            "renda-por-faixa-sm",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--target",
            "2025-07",
            "--ranges",
            "0-2;2-5;5-10;10+",
            "--format",
            "json",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "weight column not found" in err


def test_renda_por_faixa_sm_uf_ordering(capsys, tmp_path: Path):
    inp = tmp_path / "base_labeled.csv"
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"

    _write_csv(
        inp,
        [
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "35",
                "UF_label": "Sao Paulo",
                "dom_id": "d1",
                "V1028": "100",
                "VD4020__rendim_efetivo_qq_trabalho": "3000",
            },
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "33",
                "UF_label": "Rio de Janeiro",
                "dom_id": "d2",
                "V1028": "100",
                "VD4020__rendim_efetivo_qq_trabalho": "1000",
            },
        ],
    )
    _write_csv(ipca, [{"date": "2025-06", "index": "100"}, {"date": "2025-07", "index": "110"}])
    _write_csv(sm, [{"date": "2025-06", "value": "1518.00"}])

    rc = main(
        [
            "renda-por-faixa-sm",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--target",
            "2025-07",
            "--group-by",
            "uf",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["groups"][0]["group"] == "35"  # richer first by default

    rc = main(
        [
            "renda-por-faixa-sm",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--target",
            "2025-07",
            "--group-by",
            "uf",
            "--uf-order",
            "alfabetica",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    # Alphabetical by label: Rio... before Sao...
    assert payload["groups"][0]["group"] == "33"
