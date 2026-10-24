"""Transcrições, seleção de onda e separação do LVM na rodada noturna."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROUND = importlib.import_module("pesquisas-241026-noite-renda")
SIM = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["palver", "gerp", "nexus", "datafolha", "colectta"])
def test_sources_transcriptions_and_current_wave(name, assert_json_close):
    poll = getattr(ROUND, name)()
    path = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
    assert_json_close(poll, json.loads(path.read_text()))
    assert poll["divulgacao"] == "2026-10-24"
    assert 99 <= sum(poll["publicado"]["2t"].values()) <= 101
    if poll["fonte"].get("pdf"):
        pdf = ROOT / f"docs/fontes/{name}_24102026.pdf"
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == poll["fonte"]["sha256"]
        for control in poll["controles"]["2t"].values():
            assert control["residuo_max_abs"] < 1


def test_gerp_effective_field_and_weighted_profile():
    p = ROUND.gerp()
    assert p["campo"] == {"inicio": "2026-10-22", "fim": "2026-10-24"}
    assert sum(p["renda"]["amostra_pct"]) == 100
    assert p["renda"]["perfil_tipo"] == "perfil_ponderado"
    assert p["publicado_validos"]["2t"]["flavio"] != pytest.approx(49 / 95 * 100)


def test_datafolha_income_is_current_but_without_weights():
    p = ROUND.datafolha_publicada()
    assert p["ignorar"] and "renda" not in p and p["cruzamentos"] == {}
    cross = p["cruzamentos_sem_perfil"]["renda"]
    assert cross["linhas"] == [[41, 53, 3, 3], [55, 41, 4, 1], [57, 39, 3, 0]]
    assert "pesos" not in cross and "bases" not in cross
    assert ROUND.colectta()["ignorar"] and "renda" not in ROUND.colectta()


def test_datafolha_preview_keeps_old_counts_as_reference_only():
    p = ROUND.datafolha()
    assert not p.get("ignorar")
    assert p["n"] == 4050
    assert p["renda"]["perfil_tipo"] == "hipotese_onda_anterior"
    assert p["renda"]["referencia_id"] == "datafolha_2026-10-22"
    assert p["renda"]["bases_referencia"] == [1171, 913, 341]
    assert "bases" not in p["renda"] and "nao_publicada_n" not in p["renda"]
    assert p["renda"]["parcela_ajustada_pct"] == pytest.approx(2425 / 2520 * 100)
    assert p["renda"]["parcela_ajustada_pct"] != pytest.approx(2425 / 4050 * 100)


def test_nexus_uses_full_sample_and_documents_lvm_separately():
    p = ROUND.nexus()
    assert p["publicado"]["2t"] == {
        "flavio": 47,
        "lula": 46,
        "branco_nulo": 5.2,
        "indecisos": 1.8,
    }
    lvm = p["eleitor_provavel_documental"]
    assert not lvm["entra_nas_centrais"]
    assert lvm["validos"] == {"flavio": 52.4, "lula": 47.6}
    assert sum(lvm["por_100_eleitores"].values()) == pytest.approx(99.9)
    assert sum(p["distribuicao_campo_pct"].values()) == 100
    assert p["renda"]["amostra_pct"] == [21, 16, 40, 23]


def test_published_snapshot_selects_latest_wave_and_preserves_accounting(
    assert_json_close,
):
    payload = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/840e838117ea90fb.json").read_text()
    )
    selected = {p["instituto"]: p for p in payload["projection"]["selected"]}
    mean = {p["instituto"]: p for p in payload["polls"]}
    assert len(selected) == len(payload["projection"]["selected"])
    for house in ["Palver", "Gerp", "Nexus", "Datafolha"]:
        assert selected[house]["id"].endswith("2026-10-24")
    assert mean["Datafolha"]["id"] == "datafolha_2026-10-24"
    assert "Colectta" not in mean
    assert selected["Datafolha"]["income_available"]
    for house in ["Colectta"]:
        assert not selected[house]["income_available"]
        assert selected[house]["pnad"] == selected[house]["published"]
    assert sum(p["weight"] for p in selected.values()) == pytest.approx(1)
    for key, params in [
        ("central", {}),
        ("central_projection", {"centro": "projecao"}),
    ]:
        result = SIM.evaluate(payload, params)
        assert_json_close(result, payload[key])
        assert result["flavio"] + result["lula"] == pytest.approx(100)
        assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
