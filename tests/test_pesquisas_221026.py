"""Conferência da rodada, denominadores e revisão sem duplicação."""

import gzip
import importlib
import json
from pathlib import Path

import pytest
from reponderacao_vista.historico_2t import history
from reponderacao_vista.historico_projecao import project

ROUND = importlib.import_module("pesquisas-221026-renda")
ROOT = Path(__file__).resolve().parents[1]


def test_current_income_and_independent_recomposition():
    for poll in [ROUND.poderdata(), ROUND.gerp(), ROUND.quaest()]:
        for control in poll["controles"]["2t"].values():
            assert control["residuo_max_abs"] < 1
    assert ROUND.gerp()["renda"]["amostra_pct"] == [13, 22, 40, 17, 6, 2]
    assert ROUND.quaest()["renda"]["perfil_tipo"] == "perfil_publicado"


def test_indexa_profile_incompatible_and_nonvoters_separate():
    poll = ROUND.indexa()
    assert poll["ignorar"] and not poll["cruzamentos"]
    assert poll["publicado"]["2t"]["nao_vai_votar"] == 4.8
    assert poll["publicado"]["2t"]["branco_nulo"] == 4.3
    assert poll["controle_documental"]["residuo"]["flavio"] == pytest.approx(-1.394)
    assert poll["publicado_validos"]["2t"] == {"flavio": 50.6, "lula": 49.4}
    assert poll["api_sem_arredondar"]["lula"] == pytest.approx(44.15)


def test_quaest_same_wave_and_gerp_separate_tracking():
    polls = history()
    ids = [p["id"] for p in polls]
    assert ids.count("quaest_2026-10-20") == 1
    assert "gerp_2026-10-19" in ids and "gerp_2026-10-21" in ids
    quaest = next(p for p in polls if p["id"] == "quaest_2026-10-20")
    assert quaest["pnad"] is not None
    assert ROUND.gerp()["campo"] == {"inicio": "2026-10-19", "fim": "2026-10-21"}


def test_presence_is_own_wave_and_official_valids_are_not_overwritten():
    polls = {p["id"]: p for p in history()}
    current = project(polls["poderdata_2026-10-21"])
    assert current["evidencia"]["tipo"] == "direto"
    assert current["modos"]["placar"]["validos"]["flavio"] == pytest.approx(
        100 * 49 * 0.97 / (49 * 0.97 + 48 * 0.95)
    )
    assert project(polls["poderdata_2026-10-18"])["evidencia"]["tipo"] == "neutro"
    assert ROUND.poderdata()["publicado_validos"]["2t"] == {"flavio": 51, "lula": 49}


def test_archived_digital_payload_is_complete_and_registry_matches():
    path = ROOT / "data/originals/indexa_102026_22"
    parts = [
        json.loads(gzip.decompress((path / f"parte-{i}.json.gz").read_bytes()))["part"]
        for i in range(2)
    ]
    raw = gzip.decompress((path / "relatorio.json.gz").read_bytes()).decode()
    assert "".join(parts) == raw
    doc = json.loads(raw)
    assert doc["config"]["rodada"]["registroTSE"] == "BR-02348/2026"
    assert len(doc["docs"]) == 16


@pytest.mark.parametrize("name", ["poderdata", "indexa", "gerp", "quaest"])
def test_current_record_matches_audited_transcription(name, assert_json_close):
    poll = getattr(ROUND, name)()
    saved = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
    assert_json_close(poll, json.loads(saved.read_text()))
