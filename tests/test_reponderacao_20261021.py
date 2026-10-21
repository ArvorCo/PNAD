"""Rodada de 21/10: proveniência, denominadores e substituição da Quaest."""

import hashlib
import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

M = importlib.import_module("pesquisas-211026-renda")
SIM = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["verita", "palver", "quaest", "futura", "ideia"])
def test_archived_sources_and_transcriptions(name, assert_json_close):
    poll = getattr(M, name)()
    saved = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
    assert_json_close(poll, json.loads(saved.read_text()))
    assert poll["divulgacao"] == "2026-10-21"
    assert poll["campo"]["inicio"] <= poll["campo"]["fim"] < poll["divulgacao"]
    assert 99 <= sum(poll["publicado"]["2t"].values()) <= 101
    for control in poll.get("controles", {}).get("2t", {}).values():
        assert control["residuo_max_abs"] < 0.4
    if "pdf" in poll["fonte"]:
        data = (ROOT / f"docs/fontes/{name}_21102026.pdf").read_bytes()
        assert hashlib.sha256(data).hexdigest() == poll["fonte"]["sha256"]


def test_verita_uses_current_profile_and_never_treats_subtotal_as_abstention():
    poll = M.verita()
    assert poll["renda"]["amostra_pct"] == [41.2, 40.1, 18.7]
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    assert poll["conferencia_denominadores"]["ausente_e_subtotal_bn_ns_nr"]
    assert not poll["conferencia_denominadores"]["abstencao_2t_medida"]
    assert poll["publicado"]["2t"]["branco_nulo"] == 1.4
    assert poll["publicado"]["2t"]["indecisos"] == 0.7
    assert poll["publicado_validos"]["2t"]["flavio"] == 50.7


def test_palver_uses_weighted_profile_and_preserves_rounding():
    poll = M.palver()
    assert poll["renda"]["amostra_pct"] == [36, 41, 23]
    assert poll["renda"]["perfil_tipo"] == "perfil_ponderado"
    assert poll["metodologia_onda"]["comparavel_onda_anterior"]
    assert poll["metodologia_onda"]["n_efetivo"] == 1745
    assert sum(poll["publicado"]["2t"].values()) == 99
    assert poll["cruzamentos"]["2t"]["linhas"][0] == [48, 51, 1, 1]


def test_quaest_selects_current_date_and_does_not_borrow_income_profile():
    poll = M.quaest()
    assert poll["ignorar"] and not poll["cruzamentos"] and "renda" not in poll
    assert poll["publicado"]["2t"]["flavio"] == 45
    low_income = next(
        x for x in poll["cruzamentos_documentais"] if x["recorte"] == "Até 2 sm"
    )
    assert low_income["votos"] == {
        "flavio": 37,
        "lula": 51,
        "branco_nulo": 9,
        "indecisos": 3,
    }
    raw = json.loads((ROOT / poll["fonte"]["arquivo"]).read_text())["resultado"]
    chart = deepcopy(raw["cenarios"][0])
    chart["data"][0]["values"] = chart["data"][0]["values"][:1]
    with pytest.raises(ValueError, match="Onda ou opção inesperada"):
        M.quaest_values(chart)


def test_snapshot_has_one_current_wave_per_house_and_conserves_mass(assert_json_close):
    data = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/3eca9f382e4db9a6.json").read_text()
    )
    assert data["reference"] == "2026-10-21"
    mean = {p["instituto"]: p for p in data["polls"]}
    selected = {p["instituto"]: p for p in data["projection"]["selected"]}
    assert len(mean) == len(data["polls"]) == 11
    assert len(selected) == len(data["projection"]["selected"]) == 19
    assert "Quaest" not in mean
    for name in ["verita", "palver", "quaest", "futura", "ideia"]:
        poll = getattr(M, name)()
        row = selected[poll["instituto"]]
        assert row["id"] == poll["id"]
        assert row["income_available"] == (name in ["verita", "palver"])
        if not row["income_available"]:
            assert row["pnad"] == row["published"]
    for key, params in [
        ("central", {}),
        ("central_projection", {"centro": "projecao"}),
    ]:
        result = SIM.evaluate(data, params)
        assert_json_close(result, data[key])
        assert result["flavio"] + result["lula"] == pytest.approx(100)
        assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
