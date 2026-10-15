"""Contrato da API arquivada e confronto independente com o DOM fornecido."""

import csv
import json
from copy import deepcopy

import pytest
from quaest_141026 import g1
from quaest_141026.g1 import SOURCE, controls, panel, parse_chart, summary


@pytest.fixture(scope="module")
def questions():
    return panel()


def test_five_current_questions_have_complete_strata_and_distinct_totals(questions):
    assert len(questions) == 5
    assert all(len(q["estratos"]) == 26 for q in questions.values())
    assert all(len(q["dimensoes"]) == 8 for q in questions.values())
    assert questions["estimulada"]["total"]["valores_pct"] == {
        "Flávio Bolsonaro": 46,
        "Lula": 44,
        "Indecisos": 1,
        "Branco/Nulo/Não Vai Votar": 9,
    }
    assert questions["espontanea"]["total"]["valores_pct"] == {
        "Flávio Bolsonaro": 43,
        "Lula": 42,
        "Outros": 0,
        "Indecisos": 7,
        "Branco/Nulo/Não Vai Votar": 8,
    }
    assert questions["rejeicao"]["total"]["valores_pct"] == {
        "Flávio Bolsonaro": 54,
        "Lula": 53,
    }
    assert questions["aprovacao"]["total"]["valores_pct"] == {
        "Aprova": 45,
        "Desaprova": 48,
        "Não Sabe / Não Respondeu": 7,
    }
    assert questions["avaliacao"]["total"]["valores_pct"] == {
        "Positivo": 34,
        "Regular": 24,
        "Negativo": 40,
        "Não Sabe / Não Respondeu": 2,
    }
    assert all(r["base"] is None for q in questions.values() for r in q["estratos"])


def test_every_observed_dom_cell_agrees_and_absent_labels_stay_absent(questions):
    path = SOURCE / "g1-painel-extraido.json"
    dom = json.loads(path.read_text())
    api = {r["id"]: r for r in questions["estimulada"]["estratos"]}
    names = {
        "flavio": "Flávio Bolsonaro",
        "lula": "Lula",
        "indecisos": "Indecisos",
        "branco_nulo": "Branco/Nulo/Não Vai Votar",
    }
    matches = 0
    missing = []
    for row in dom["graficos"]:
        if row["id"] not in api:
            continue
        for key, value in row["votos"].items():
            actual = api[row["id"]]["valores_pct"][names[key]]
            if value is None:
                missing.append((row["id"], key, actual))
            else:
                assert actual == value
                matches += 1
    assert matches == 100  # 25 recortes completos, quatro respostas cada.
    assert len(missing) == 4
    assert all("lulista" in row[0] for row in missing)
    assert {key: value for _, key, value in missing} == {
        "flavio": 2,
        "lula": 97,
        "indecisos": 0,
        "branco_nulo": 1,
    }


def test_controls_use_named_strata_and_current_registered_quotas(questions):
    question = deepcopy(questions["estimulada"])
    actual = controls(question)
    question["estratos"].reverse()
    assert controls(question) == actual
    assert actual["Renda"]["recomposto"] == {
        "flavio": 46.05,
        "lula": 44.18,
        "branco_nulo": 9.04,
        "indecisos": 0.73,
    }
    assert [c["residuo_max_abs"] for c in actual.values()] == [0.27, 0.47, 0.23, 0.23]
    assert summary(questions)["perguntas"]["rejeicao"]["recortes"] == 26


def test_public_exports_keep_missing_bases_and_match_source_totals(
    tmp_path, monkeypatch, questions
):
    monkeypatch.setattr(g1, "PUBLIC", tmp_path)
    result = g1.write()
    assert json.loads((tmp_path / "index.json").read_text()) == result
    with (tmp_path / "recortes.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 486
    assert all(row["base"] == "" for row in rows)
    for key, question in questions.items():
        assert json.loads((tmp_path / f"{key}.json").read_text()) == question
    rejection = {
        row["resposta"]: float(row["pct"])
        for row in rows
        if row["pergunta"] == "Rejeição" and row["dimensao"] == "Total"
    }
    assert rejection == {"Flávio Bolsonaro": 54, "Lula": 53}


@pytest.mark.parametrize(
    "failure", ["date", "question", "duplicate", "missing", "nan", "range"]
)
def test_parser_rejects_mixed_waves_duplicates_and_invalid_values(failure):
    raw = json.loads((SOURCE / "g1_estimulada.json").read_text())
    chart = raw["resultado"]["cenarios"][0]
    if failure == "date":
        chart["data"][0]["date"] = "2026-10-03T00:00:00Z"
    elif failure == "question":
        chart["pergunta"]["codigo"] = "SEGTURNO-PRE-001"
    elif failure == "duplicate":
        chart["data"].append(chart["data"][0])
    else:
        chart["data"][0]["value"] = {"missing": None, "nan": float("nan"), "range": 46}[
            failure
        ]
    with pytest.raises(ValueError):
        parse_chart(chart, "ESTIMULADA-PRE-201")
