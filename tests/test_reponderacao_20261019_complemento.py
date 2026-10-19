"""Novas ondas: fonte atual, separação de conceitos e seleção sem duplicação."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

M = importlib.import_module("pesquisas-191026-complemento")
SIM = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["ipespe", "atlas", "futura", "vox", "datatrends"])
def test_ingestion_matches_archived_sources(name, assert_json_close):
    poll = getattr(M, name)()  # Confere os hashes e tamanhos das fontes.
    saved = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
    assert_json_close(poll, json.loads(saved.read_text()))
    assert poll["fonte"]["conferido_em"] == "2026-10-19"
    assert poll["campo"]["inicio"] > "2026-10-04"
    assert sum(poll["publicado"]["2t"].values()) == pytest.approx(100, abs=0.11)
    for control in poll.get("controles", {}).get("2t", {}).values():
        assert control["residuo_max_abs"] < 0.54


def test_atlas_does_not_invent_undecided_split_or_reuse_prior_income():
    poll = M.atlas()
    assert poll["n"] == 4998
    assert poll["renda"]["amostra_pct"] == [18, 12.2, 25.9, 26.6, 17.2]
    assert poll["renda"]["unidade"] == "reais_nominais"
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    assert "indecisos" not in poll["publicado"]["2t"]
    assert "indecisos" not in poll["cruzamentos"]["2t"]["opcoes"]
    assert poll["publicado_validos"]["2t"] == {"flavio": 51.1, "lula": 48.9}
    assert max(c["residuo_max_abs"] for c in poll["controles"]["2t"].values()) < 0.05


def test_ipespe_uses_all_interviewees_not_self_selected_likely_voters():
    poll = M.ipespe()
    assert poll["publicado"]["2t"] == {
        "flavio": 48,
        "lula": 46,
        "branco_nulo": 3,
        "indecisos": 3,
    }
    assert poll["renda"]["amostra_pct"] == [41, 38, 22]
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    assert poll["divulgacao"] == "2026-10-17"
    assert poll["publicado_validos"]["2t"]["flavio"] == 51.2
    assert 100 * 48 / 94 != 51.2


def test_unidentified_or_missing_income_is_never_adjusted():
    for poll in [M.vox(), M.futura(), M.datatrends()]:
        assert poll["ignorar"] and not poll["cruzamentos"] and "renda" not in poll
    assert M.vox()["perfil_economico_publicado"]["conceito"] == "não definido"
    assert M.vox()["cruzamentos_diagnosticos"]["pagina"] == 18
    assert M.futura()["perfil_economico_publicado"]["ns_nr"] == 12
    assert M.datatrends()["fonte"]["tipo"] == "divulgacao"
    assert "pdf" not in M.datatrends()["fonte"]


def test_frozen_snapshot_contains_new_waves_and_preserves_accounting(assert_json_close):
    data = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/e80ccbd307ca96a8.json").read_text()
    )
    assert len(data["polls"]) == 10
    selected = {p["instituto"]: p for p in data["projection"]["selected"]}
    assert len(selected) == len(data["projection"]["selected"]) == 14
    for name in ["ipespe", "atlas", "futura", "vox", "datatrends"]:
        poll = getattr(M, name)()
        row = selected[poll["instituto"]]
        assert row["id"] == poll["id"]
        assert row["income_available"] == (name in ["ipespe", "atlas"])
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


def test_public_pdf_copies_are_identical():
    for name, slug in [
        ("ipespe", "ipespe_17102026"),
        ("atlas", "atlas_19102026"),
        ("futura", "futura_19102026"),
        ("vox", "vox_18102026"),
    ]:
        poll = getattr(M, name)()
        content = (ROOT / "docs/fontes" / (slug + ".pdf")).read_bytes()
        assert content == (ROOT / poll["fonte"]["pdf"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == poll["fonte"]["sha256"]
