"""Evidence and arithmetic invariants for the complete September Datafolha report."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
D = json.loads((ASSETS / "datafolha_14092026_data.json").read_text())
T = json.loads((ASSETS / "datafolha_14092026_cruzamentos.json").read_text())["tabelas"]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_extracts_all_questions_and_blocks():
    assert len(T) == 15
    assert sum(len(t["blocks"]) for t in T.values()) == 45
    for t in T.values():
        blocks = list(t["blocks"].values())
        assert all(list(b["rows"]) == list(blocks[0]["rows"]) for b in blocks)
        assert all(set(b["base"]) == set(b["columns"]) for b in blocks)


def test_income_rows_and_bases_verified_against_original_page():
    block = T["turno2_flavio"]["blocks"]["bloco2"]
    bands = ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"]
    assert [block["base"][b] for b in bands] == [991, 689, 234]
    assert [block["rows"]["Lula (PT)"][b] for b in bands] == [55, 39, 32]
    assert [block["rows"]["Flavio Bolsonaro (PL)"][b] for b in bands] == [35, 52, 60]
    assert block["pdf_page"] == 49


def test_two_closed_crossbreaks_reconstruct_toplines():
    closed = [p for p in D["proofs"] if p["dimensao"] in ["sexo", "regiao"]]
    assert len(closed) == 8
    assert all(p["base"] == 2002 and abs(p["residuo"]) < 0.5 for p in closed)


def test_conditional_universes_do_not_become_income_weights():
    assert T["definicao"]["blocks"]["bloco1"]["base"]["Total"] == 1931
    assert T["motivacao"]["blocks"]["bloco1"]["base"]["Total"] == 1821
    assert sum(D["poll"]["renda"]["bases"]) == 1914
    assert D["market"]["mercado_aberto_pct_aproximado"] == pytest.approx(
        (71 + 0.25 * 1931) / 2002 * 100
    )


def test_anchored_income_delta_and_preserved_missing_share():
    poll = D["poll"]
    weights = np.array(poll["renda"]["bases"], float)
    weights /= weights.sum()
    # Benchmark is saved in percent to 3 decimals, allowing <0.002 pp rounding.
    target = np.array(D["reweight"]["renda"]["pnad_pct"]["pessoas16_efetivo"]) / 100
    for t in ["1t", "2t"]:
        vote = np.array(poll["cruzamentos"][t]["linhas"], float)
        expected = (
            np.array(list(poll["publicado"][t].values())) + (target - weights) @ vote
        )
        actual = list(
            D["reweight"]["turnos"][t]["cenarios"]["pessoas16_efetivo"][
                "ajustado"
            ].values()
        )
        np.testing.assert_allclose(actual, expected, atol=0.002)
    p = D["missing_share_preserved"]["2t"]
    assert p["flavio"] > p["lula"]
    assert (
        D["reweight"]["turnos"]["1t"]["cenarios"]["domicilios_efetivo"]["ajustado"][
            "lula"
        ]
        > D["reweight"]["turnos"]["1t"]["cenarios"]["domicilios_efetivo"]["ajustado"][
            "flavio"
        ]
    )


def test_sankey_measured_rows_and_structural_zeros_survive_all_priors():
    flow = D["transfer"]
    targets = np.array(flow["row_targets"])
    for matrix in [flow["matrix"]] + flow["alternative_matrices"]:
        m = np.array(matrix)
        np.testing.assert_allclose(m.sum(axis=1), targets, atol=1e-8)
        np.testing.assert_allclose(m.sum(axis=0), flow["column_targets"], atol=1e-8)
        assert m[0, 1] == m[0, 2] == m[1, 0] == m[1, 2] == 0
        np.testing.assert_allclose(m[2] / targets[2], [0.37, 0.39, 0.24])
        np.testing.assert_allclose(m[3] / targets[3], [0.33, 0.45, 0.22])
    assert flow["normalization"]["factor"] == 99 / 103


def test_territorial_split_columns_reconcile_with_profile():
    source = ROOT / "data/pesquisas/datafolha/2026-09-11/bairros.pdf"
    if not source.exists():
        pytest.skip("local source PDF not present")
    rows, profile = load("datafolha-14092026-territorio").extract(source)
    assert len(rows) == len({r["setor"] for r in rows}) == 303
    assert len({r["codigo_municipio"] for r in rows}) == 125
    assert sum(r["entrevistas"] for r in rows) == 2002
    assert all(r["municipio"] and r["bairro"] and len(r["uf"]) == 2 for r in rows)
    assert profile[10:14] == [1027, 656, 236, 83]


def test_published_aggregator_matches_dossier():
    agg = json.loads((ASSETS / "reponderacao_pnad.json").read_text())
    p = next(p for p in agg["pesquisas"] if p["id"] == "datafolha_2026-09-10")
    assert p["turnos"] == D["reweight"]["turnos"]
    assert p["dossie"] == "datafolha_14092026.html"
