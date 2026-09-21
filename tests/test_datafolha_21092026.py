"""Evidence checks: rounded margins, missing state and synthetic non-identification."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
D = json.loads((ASSETS / "datafolha_21092026_data.json").read_text())
T = json.loads((ASSETS / "datafolha_21092026_cruzamentos.json").read_text())["tabelas"]
IDENTIFICATION = json.loads(
    (ASSETS / "datafolha_21092026_identificacao.json").read_text()
)


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_full_annex_new_party_columns_and_candidate_order():
    assert len(T) == 13
    assert sum(len(t["blocks"]) for t in T.values()) == 39
    for table in T.values():
        blocks = list(table["blocks"].values())
        assert all(list(b["rows"]) == list(blocks[0]["rows"]) for b in blocks)
        assert all(len(b["columns"]) == 11 for b in blocks)
    assert T["turno2_flavio"]["blocks"]["bloco3"]["base"]["PT"] == 528
    # Minor candidate order changed in this PDF, so a previous-order zip is wrong.
    p = D["poll"]
    names = p["cruzamentos"]["1t"]["opcoes"]
    low = p["cruzamentos"]["1t"]["linhas"][0]
    assert low[names.index("edmilson")] == 1
    assert low[names.index("clariana")] == 0


def test_two_closed_partitions_reproduce_each_turn():
    assert len(D["proofs"]) == 8
    assert all(abs(p["recomposed"] - p["published"]) < 1 for p in D["proofs"])
    assert {p["dimension"] for p in D["proofs"]} == {"sexo", "regiao"}


def test_income_uses_vote_bases_and_anchored_delta():
    poll = D["poll"]
    bands = ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"]
    for key in ["estimulada_b", "turno2_flavio"]:
        assert [T[key]["blocks"]["bloco2"]["base"][k] for k in bands] == [992, 655, 266]
    source = np.array(poll["renda"]["bases"]) / 1913
    target = np.array(D["reweight"]["renda"]["pnad_pct"]["pessoas16_efetivo"]) / 100
    for turn in ["1t", "2t"]:
        rows = np.array(poll["cruzamentos"][turn]["linhas"])
        expected = np.array(list(poll["publicado"][turn].values())) + np.einsum(
            "i,ij->j", target - source, rows
        )
        result = D["reweight"]["turnos"][turn]["cenarios"]["pessoas16_efetivo"][
            "ajustado"
        ]
        np.testing.assert_allclose(list(result.values()), expected, atol=0.002)
    assert (
        D["missing_share_preserved"]["2t"]["flavio"]
        > D["missing_share_preserved"]["2t"]["lula"]
    )


def test_southeast_is_not_a_lula_lead_and_es_is_not_imputed():
    g = D["geography"]
    assert len(g["states"]) == 3
    assert {s["uf"] for s in g["states"]} == {"SP", "RJ", "MG"}
    assert sum(g["weights"].values()) == pytest.approx(1)
    assert g["weights"]["ES"] == pytest.approx(0.04508447654)
    assert g["comparisons"][0]["regional"]["flavio"] == 47
    assert g["comparisons"][1]["regional"]["flavio"] == 46
    assert all(c["regional"]["lula"] == 42 for c in g["comparisons"])
    assert g["known_conditional"]["lula"] == pytest.approx(42.8313691527)
    assert g["known_conditional"]["flavio"] == pytest.approx(46.8887895590)
    assert g["gap_bounds"][0] < -5 < -4 < g["gap_bounds"][1]
    assert "Não localizado" in g["es_status"]


def test_synthetic_certificates_preserve_exact_same_projections():
    cells = np.array(IDENTIFICATION["cell_indices"])
    a, b = [np.array(c["cells"]) for c in IDENTIFICATION["certificates"]]
    assert IDENTIFICATION["n_cells"] == 128 and IDENTIFICATION["constraint_rank"] == 32
    assert min(a) >= -1e-8 and min(b) >= -1e-8
    assert a.sum() == pytest.approx(2001) and b.sum() == pytest.approx(2001)
    bases = {}
    rows = {}
    for block in T["turno2_flavio"]["blocks"].values():
        bases.update(block["base"])
        for label, values in block["rows"].items():
            rows.setdefault(label, {}).update(values)
    for dim, key in [(1, "income"), (2, "region"), (3, "sex")]:
        for j, group in enumerate(IDENTIFICATION["dimensions"][key]):
            mask = cells[:, dim] == j
            np.testing.assert_allclose(a[mask].sum(), b[mask].sum(), atol=1e-7)
            for o, outcome in enumerate(IDENTIFICATION["dimensions"]["outcome"]):
                m = mask & (cells[:, 0] == o)
                np.testing.assert_allclose(a[m].sum(), b[m].sum(), atol=1e-7)
                if group in rows[outcome]:
                    assert (
                        abs(
                            a[m].sum() / bases[group] * 100
                            - (rows[outcome][group] or 0)
                        )
                        <= 0.500001
                    )
    hidden = (cells[:, 0] == 0) & (cells[:, 1] == 0) & (cells[:, 2] == 0)
    assert a[hidden].sum() == pytest.approx(0, abs=1e-6)
    assert b[hidden].sum() > 340
    assert not np.allclose(a, b)


def test_territorial_sergipe_not_confused_with_southeast():
    t = D["territory"]
    assert t["regions"] == {"CO": 154, "N": 168, "NE": 545, "S": 294, "SE": 840}
    assert t["uf"]["SE"] == 28 and t["uf"]["ES"] == 28
    assert all(len(uf) == 2 for uf in t["uf"])
    assert sum(t["uf"].values()) == 2001
    assert len(t["rows"]) == t["sectors"] == 302
    assert len({r["setor"][:7] for r in t["rows"]}) == t["municipalities"] == 126


def test_measured_transfers_and_hypothesized_bases_close():
    f = D["transfer"]
    m = np.array(f["matrix"])
    rows = np.array(f["row_targets"])
    np.testing.assert_allclose(m.sum(axis=1), rows)
    np.testing.assert_allclose(m.sum(axis=0), f["column_targets"])
    np.testing.assert_allclose(m[2] / rows[2], [0.32, 0.44, 0.24])
    np.testing.assert_allclose(m[3] / rows[3], [0.27, 0.42, 0.31])
    assert m[0, 1] == m[0, 2] == m[1, 0] == m[1, 2] == 0
    assert f["normalization"]["factor"] == 99 / 101


def test_aggregator_includes_complete_report_without_redating_poll():
    agg = json.loads((ASSETS / "reponderacao_pnad.json").read_text())
    p = next(p for p in agg["pesquisas"] if p["id"] == "datafolha_2026-09-17")
    assert p["turnos"] == D["reweight"]["turnos"]
    assert p["divulgacao"] == "2026-09-17"
    assert p["fonte"]["relatorio_completo"] == "2026-09-21"
    html = (ROOT / "docs/reponderacao_pnad.html").read_text()
    assert "Relatório completo disponibilizado em 21/09/2026" in html


def test_extractor_reproduces_saved_native_tables():
    source = ROOT / "docs/fontes/datafolha_21092026.pdf"
    assert load("datafolha-21092026-extract").extract(source) == T
