"""Fontes, revisão sem duplicação e exclusão de renda inconsistente em 20/10."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

M = importlib.import_module("pesquisas-201026-renda")
OLD = importlib.import_module("pesquisas-191026-complemento")
SIM = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "name", ["realtime", "alfa", "datatrends", "franca", "gerp", "ranking"]
)
def test_sources_and_transcriptions(name, assert_json_close):
    poll = getattr(M, name)()
    saved = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
    assert_json_close(poll, json.loads(saved.read_text()))
    assert sum(poll["publicado"]["2t"].values()) == pytest.approx(100)
    for control in poll.get("controles", {}).get("2t", {}).values():
        assert control["residuo_max_abs"] <= 0.75
    if "pdf" in poll["fonte"]:
        day = "19102026" if name == "datatrends" else "20102026"
        data = (ROOT / f"docs/fontes/{name}_{day}.pdf").read_bytes()
        assert hashlib.sha256(data).hexdigest() == poll["fonte"]["sha256"]


def test_datatrends_revision_preserves_identity_and_uses_profile_not_target():
    before, after = OLD.datatrends(), M.datatrends()
    for key in ["id", "campo", "divulgacao", "registro_tse", "publicado"]:
        assert after[key] == before[key]
    assert before["ignorar"] and not after.get("ignorar")
    assert after["renda"]["amostra_pct"] == [46, 35, 19]
    assert after["alvos_renda_declarados"] == [46.7, 34.6, 18.7]
    assert after["renda"]["perfil_tipo"] == "perfil_publicado"


def test_franca_income_is_mathematically_incompatible_and_not_adjusted():
    poll = M.franca()
    assert poll["ignorar"] and not poll["cruzamentos"] and "renda" not in poll
    income = poll["auditoria_cruzamentos"]["renda"]
    assert (
        max(row[3] for row in income["linhas"]) < poll["publicado"]["2t"]["indecisos"]
    )
    assert income["residuo_max_abs"] > 6
    with pytest.raises(ValueError, match="Recomposição incompatível"):
        M.PREVIOUS.control(poll["publicado"]["2t"], income["linhas"], income["pesos"])


def test_gerp_does_not_borrow_income_or_assign_next_wave_registry():
    poll = M.gerp()
    assert poll["registro_tse"] == "não confirmado"
    assert poll["campo"]["fim"] == "2026-10-19"
    assert poll["ignorar"] and "renda" not in poll
    assert poll["publicado_validos"]["2t"] == {"flavio": 53, "lula": 47}
    assert 100 * 50 / 95 != 53


def test_new_snapshot_selection_and_accounting(assert_json_close):
    data = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/70730495a991f8a8.json").read_text()
    )
    assert data["reference"] == "2026-10-20"
    mean = {p["instituto"]: p for p in data["polls"]}
    selected = {p["instituto"]: p for p in data["projection"]["selected"]}
    assert len(mean) == len(data["polls"]) == 12
    assert len(selected) == len(data["projection"]["selected"]) == 18
    assert "Gerp" not in mean
    assert selected["Gerp"]["id"] == "gerp_2026-10-19"
    for name in ["Gerp", "Instituto França", "Data Ranking"]:
        assert not selected[name]["income_available"]
        assert selected[name]["pnad"] == selected[name]["published"]
    for name in ["Real Time Big Data", "Alfa Inteligência/TMC", "DataTrends"]:
        assert selected[name]["income_available"] and name in mean
    for key, params in [
        ("central", {}),
        ("central_projection", {"centro": "projecao"}),
    ]:
        result = SIM.evaluate(data, params)
        assert_json_close(result, data[key])
        assert result["flavio"] + result["lula"] == pytest.approx(100)
        assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
