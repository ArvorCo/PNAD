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


def test_dashboard_json_sm_modes(capsys, tmp_path: Path):
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
                "Capital_label": "Capital",
                "dom_id": "d1",
                "V1028": "100",
                "V2007_label": "Homem",
                "V2010_label": "Branca",
                "V3009A_label": "Superior completo",
                "V2009__idade_na_data_de_referncia": "40",
                "VD4020__rendim_efetivo_qq_trabalho": "4000",
            },
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "33",
                "UF_label": "Rio de Janeiro",
                "Capital_label": "Nao capital",
                "dom_id": "d2",
                "V1028": "100",
                "V2007_label": "Mulher",
                "V2010_label": "Parda",
                "V3009A_label": "Medio completo",
                "V2009__idade_na_data_de_referncia": "28",
                "VD4020__rendim_efetivo_qq_trabalho": "1000",
            },
        ],
    )
    _write_csv(ipca, [{"date": "2025-06", "index": "100"}, {"date": "2025-07", "index": "110"}])
    _write_csv(sm, [{"date": "2025-06", "value": "1518.00"}, {"date": "2025-07", "value": "1518.00"}])

    rc = main(
        [
            "dashboard",
            "--input",
            str(inp),
            "--ipca-csv",
            str(ipca),
            "--salario-minimo-csv",
            str(sm),
            "--sm-mode",
            "both",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sm_mode"] == "both"
    assert "periodo" in payload["modes"]
    assert "alvo" in payload["modes"]
    assert payload["modes"]["periodo"]["top5_uf"][0]["group"] == "35"
    assert "top10_uf_population" in payload["modes"]["periodo"]
    assert payload["modes"]["periodo"]["top10_uf_population"][0]["group"] == "35"
    assert "macro_regions" in payload["modes"]["periodo"]
    assert payload["modes"]["periodo"]["macro_regions"][0]["group"] == "Sudeste"
    assert "top10_uf_low_income" in payload["modes"]["periodo"]
    assert "top10_uf_high_income" in payload["modes"]["periodo"]
    assert "ranges_money" in payload["modes"]["periodo"]
    assert payload["modes"]["periodo"]["sm_reference_value"] > 0
    assert "R$" in payload["modes"]["periodo"]["ranges_money"][0]["money_label"]
    assert "age_pyramid" in payload["modes"]["periodo"]
    assert payload["modes"]["periodo"]["age_pyramid"][0]["age"] == "25-39"
    assert "insights" in payload["modes"]["periodo"]
    assert payload["modes"]["periodo"]["insights"]["richest_uf_by_avg_sm"] == "Sao Paulo"
    assert "R$" in payload["modes"]["periodo"]["insights"]["national_low_income_money"]
    assert "dimension_labels" in payload
    assert payload["dimension_labels"]["macro_region"] == "Macro-regiao"
    assert payload["modes"]["periodo"]["demographics"]["age"][0]["label"] == "25-39"
    assert "education_by_band" in payload["modes"]["periodo"]["cross"]


def test_dashboard_non_applicable_buckets(capsys, tmp_path: Path):
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
                "Capital_label": "Capital",
                "dom_id": "d1",
                "V1028": "100",
                "V2007_label": "Homem",
                "V2010_label": "Branca",
                "V3009A_label": "Superior completo",
                "V2009__idade_na_data_de_referncia": "40",
                "VD4020__rendim_efetivo_qq_trabalho": "4000",
                "VD4009_label": "Conta-própria",
                "VD4009__posio_na_ocupao_trab_princ": "09",
                "VD4005_label": "",
                "VD4005__pessoas_desalentadas": "",
                "V4010_label": "",
                "V4010__ocupao_no_trab_principal": "5221",
                "RM_RIDE_label": "",
                "RM_RIDE__reg_metr_e_reg_adm_int_des": "",
            },
            {
                "Ano__ano_de_referncia": "2025",
                "Trimestre__trimestre_de_referncia": "2",
                "UF__unidade_da_federao": "35",
                "UF_label": "Sao Paulo",
                "Capital_label": "Nao capital",
                "dom_id": "d2",
                "V1028": "100",
                "V2007_label": "Mulher",
                "V2010_label": "Parda",
                "V3009A_label": "Medio completo",
                "V2009__idade_na_data_de_referncia": "30",
                "VD4020__rendim_efetivo_qq_trabalho": "1000",
                "VD4009_label": "",
                "VD4009__posio_na_ocupao_trab_princ": "",
                "VD4005_label": "",
                "VD4005__pessoas_desalentadas": "",
                "V4010_label": "",
                "V4010__ocupao_no_trab_principal": "",
                "RM_RIDE_label": "",
                "RM_RIDE__reg_metr_e_reg_adm_int_des": "",
            },
        ],
    )
    _write_csv(ipca, [{"date": "2025-06", "index": "100"}, {"date": "2025-07", "index": "110"}])
    _write_csv(sm, [{"date": "2025-06", "value": "1518.00"}, {"date": "2025-07", "value": "1518.00"}])

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
    mode = payload["modes"]["alvo"]
    occ_labels = [x["label"] for x in mode["demographics"]["occupation_status"]]
    labor_labels = [x["label"] for x in mode["demographics"]["labor_type"]]
    pos_labels = [x["label"] for x in mode["demographics"]["occupation_position"]]
    metro_labels = [x["label"] for x in mode["demographics"]["metro_region"]]
    assert "Nao se aplica (fora da ocupacao)" in occ_labels
    assert "Nao desalentado/ou nao se aplica" in labor_labels
    assert "Grande grupo 5: Servicos e vendedores" in pos_labels
    assert "Fora de RM/RIDE" in metro_labels
