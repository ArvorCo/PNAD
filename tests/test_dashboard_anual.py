import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pnad import _calculate_income_composition  # type: ignore
from pnad import _detect_income_source_cols  # type: ignore
from pnad import main  # type: ignore


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for row in rows:
            w.writerow(row)


def test_detect_income_source_cols():
    headers = [
        "VD5001__rend_efetivo_domiciliar",
        "V5001A2__bpc_loas",
        "V5002A2__bolsa_familia",
        "V5004A2__aposentadoria",
        "V5008A2__outros_capital",
    ]
    found = _detect_income_source_cols(headers)
    assert found == {
        "bpc_loas": "V5001A2__bpc_loas",
        "bolsa_familia": "V5002A2__bolsa_familia",
        "aposentadoria_pensao": "V5004A2__aposentadoria",
        "outros_capital": "V5008A2__outros_capital",
    }


def test_calculate_income_composition():
    row = {
        "VD5001__rend_efetivo_domiciliar": "2000",
        "V5001A2__bpc_loas": "200",
        "V5002A2__bolsa_familia": "100",
        "V5004A2__aposentadoria": "500",
        "V5007A2__aluguel": "100",
    }
    source_cols = {
        "bpc_loas": "V5001A2__bpc_loas",
        "bolsa_familia": "V5002A2__bolsa_familia",
        "aposentadoria_pensao": "V5004A2__aposentadoria",
        "aluguel": "V5007A2__aluguel",
    }
    comp = _calculate_income_composition(row, "VD5001__rend_efetivo_domiciliar", source_cols)
    assert comp["bpc_loas"] == pytest.approx(0.10, abs=1e-6)
    assert comp["bolsa_familia"] == pytest.approx(0.05, abs=1e-6)
    assert comp["aposentadoria_pensao"] == pytest.approx(0.25, abs=1e-6)
    assert comp["aluguel"] == pytest.approx(0.05, abs=1e-6)
    assert comp["trabalho"] == pytest.approx(0.55, abs=1e-6)
    assert sum(comp.values()) == pytest.approx(1.0, abs=1e-6)


def test_dashboard_anual_mode_detection(capsys, tmp_path: Path):
    inp = tmp_path / "base_anual.csv"
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"

    _write_csv(
        inp,
        [
            {
                "Ano": "2025",
                "Trimestre": "1",
                "UF": "35",
                "UF_label": "Sao Paulo",
                "dom_id": "d1",
                "V1028": "1",
                "VD5001__rend_efetivo_domiciliar": "3000",
            }
        ],
    )
    _write_csv(ipca, [{"date": "2025-03", "index": "100"}])
    _write_csv(sm, [{"date": "2025-03", "value": "1000"}])

    rc = main(
        [
            "dashboard",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--format",
            "json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "anual"
    assert payload["income_col"].startswith("VD5001")


def test_dashboard_breakdown_output(capsys, tmp_path: Path):
    inp = tmp_path / "base_anual.csv"
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"

    _write_csv(
        inp,
        [
            {
                "Ano": "2025",
                "Trimestre": "1",
                "UF": "22",
                "UF_label": "Piaui",
                "dom_id": "d1",
                "V1028": "1",
                "VD5001__rend_efetivo_domiciliar": "1000",
                "V5001A2__bpc_loas": "100",
                "V5002A2__bolsa_familia": "100",
                "V5003A2__outros_programas": "0",
                "V5004A2__aposentadoria_pensao": "200",
                "V5005A2__seguro_desemprego": "50",
                "V5006A2__pensao_doacao": "0",
                "V5007A2__aluguel": "0",
                "V5008A2__outros_capital": "0",
            },
            {
                "Ano": "2025",
                "Trimestre": "1",
                "UF": "35",
                "UF_label": "Sao Paulo",
                "dom_id": "d2",
                "V1028": "1",
                "VD5001__rend_efetivo_domiciliar": "2000",
                "V5001A2__bpc_loas": "0",
                "V5002A2__bolsa_familia": "50",
                "V5003A2__outros_programas": "50",
                "V5004A2__aposentadoria_pensao": "400",
                "V5005A2__seguro_desemprego": "0",
                "V5006A2__pensao_doacao": "100",
                "V5007A2__aluguel": "100",
                "V5008A2__outros_capital": "50",
            },
        ],
    )
    _write_csv(ipca, [{"date": "2025-03", "index": "100"}])
    _write_csv(sm, [{"date": "2025-03", "value": "1000"}])

    rc = main(
        [
            "dashboard",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--breakdown",
            "--source-detail",
            "--composition-by-band",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    comp = payload["income_composition_national"]
    assert comp["trabalho"]["pct"] == pytest.approx(60.0, abs=0.01)
    assert comp["beneficios_sociais"]["pct"] == pytest.approx(10.0, abs=0.01)
    assert comp["previdencia"]["pct"] == pytest.approx(20.0, abs=0.01)
    assert comp["capital"]["pct"] == pytest.approx(5.0, abs=0.01)
    assert payload["income_sources_detail"]["bpc_loas"]["recipients_pct"] == pytest.approx(50.0, abs=0.01)
    assert "0-2" in payload["composition_by_band"]
    assert "2-5" in payload["composition_by_band"]


def test_dependency_ranking_ordering(capsys, tmp_path: Path):
    inp = tmp_path / "base_anual.csv"
    ipca = tmp_path / "ipca.csv"
    sm = tmp_path / "salario_minimo.csv"

    _write_csv(
        inp,
        [
            {
                "Ano": "2025",
                "Trimestre": "1",
                "UF": "22",
                "UF_label": "Piaui",
                "dom_id": "d1",
                "V1028": "1",
                "VD5001__rend_efetivo_domiciliar": "1000",
                "V5001A2__bpc_loas": "300",
                "V5002A2__bolsa_familia": "200",
                "V5003A2__outros_programas": "0",
                "V5004A2__aposentadoria_pensao": "300",
            },
            {
                "Ano": "2025",
                "Trimestre": "1",
                "UF": "29",
                "UF_label": "Bahia",
                "dom_id": "d2",
                "V1028": "1",
                "VD5001__rend_efetivo_domiciliar": "1000",
                "V5001A2__bpc_loas": "50",
                "V5002A2__bolsa_familia": "50",
                "V5003A2__outros_programas": "0",
                "V5004A2__aposentadoria_pensao": "200",
            },
            {
                "Ano": "2025",
                "Trimestre": "1",
                "UF": "35",
                "UF_label": "Sao Paulo",
                "dom_id": "d3",
                "V1028": "1",
                "VD5001__rend_efetivo_domiciliar": "1000",
                "V5001A2__bpc_loas": "0",
                "V5002A2__bolsa_familia": "0",
                "V5003A2__outros_programas": "0",
                "V5004A2__aposentadoria_pensao": "100",
            },
        ],
    )
    _write_csv(ipca, [{"date": "2025-03", "index": "100"}])
    _write_csv(sm, [{"date": "2025-03", "value": "1000"}])

    rc = main(
        [
            "dashboard",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--dependency-ranking",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    ranking = payload["uf_dependency_ranking"]
    assert ranking[0]["uf_code"] == "22"
    assert ranking[1]["uf_code"] == "29"
    assert ranking[2]["uf_code"] == "35"
    assert ranking[0]["dependency_score"] >= ranking[1]["dependency_score"] >= ranking[2]["dependency_score"]
