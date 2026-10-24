"""Proveniência e limites da rodada de 24/10, sem alterar contratos históricos."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROUND = importlib.import_module("pesquisas-241026-renda")
SIM = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["mda", "franca"])
def test_sources_and_transcriptions(name, assert_json_close):
    poll = getattr(ROUND, name)()  # Valida bytes e SHA-256 de todas as fontes.
    path = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
    assert_json_close(poll, json.loads(path.read_text()))
    assert poll["divulgacao"] == "2026-10-24"
    assert poll["campo"] == {"inicio": "2026-10-21", "fim": "2026-10-23"}
    assert sum(poll["publicado"]["2t"].values()) == pytest.approx(100)
    assert sum(poll["publicado_validos"]["2t"].values()) == pytest.approx(100)
    public_pdf = ROOT / f"docs/fontes/{name}_24102026.pdf"
    assert (
        hashlib.sha256(public_pdf.read_bytes()).hexdigest() == poll["fonte"]["sha256"]
    )


def test_mda_current_income_and_independent_sex_control():
    poll = ROUND.mda()
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    assert poll["renda"]["parcela_ajustada_pct"] == 99
    assert sum(poll["renda"]["amostra_pct"]) == pytest.approx(99)
    for control in poll["controles"]["2t"].values():
        assert control["residuo_max_abs"] < 0.5
    assert sum(poll["distribuicao_campo_pct"].values()) == 100


def test_franca_without_current_weights_never_borrows_old_profile():
    poll = ROUND.franca()
    assert poll["ignorar"] and not poll["cruzamentos"] and "renda" not in poll
    for key in ["renda", "sexo"]:
        cross = poll["cruzamentos_sem_perfil"][key]
        assert "pesos" not in cross and "bases" not in cross
        for row in cross["linhas"]:
            assert sum(row) == pytest.approx(100)
    assert poll["fonte_divulgacao"]["arquivo"].endswith("/divulgacao.html")


def test_snapshot_selects_new_waves_once_and_preserves_accounting(assert_json_close):
    payload = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/0fe265d14c2bbaf3.json").read_text()
    )
    selected = {p["instituto"]: p for p in payload["projection"]["selected"]}
    mean = {p["instituto"]: p for p in payload["polls"]}
    assert len(selected) == len(payload["projection"]["selected"]) == 20
    assert len(mean) == len(payload["polls"]) == 11
    assert selected["MDA"]["id"] == mean["MDA"]["id"] == "mda_2026-10-23"
    assert selected["MDA"]["income_available"]
    france = selected["Instituto França"]
    assert france["id"] == "franca_2026-10-23" and not france["income_available"]
    assert france["pnad"] == france["published"]
    assert "Instituto França" not in mean
    assert sum(p["weight"] for p in selected.values()) == pytest.approx(1)
    for key, params in [
        ("central", {}),
        ("central_projection", {"centro": "projecao"}),
    ]:
        result = SIM.evaluate(payload, params)
        assert_json_close(result, payload[key])
        assert result["flavio"] + result["lula"] == pytest.approx(100)
        assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
