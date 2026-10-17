"""Fontes de 15/10, rejeição de onda antiga e inclusão sem renda inventada."""

import importlib
import json
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
M = importlib.import_module("pesquisas-151026-renda")
ENGINE = importlib.import_module("reponderacao-pnad")
PROJECTION = importlib.import_module("reponderacao-projecao")
SIM = importlib.import_module("reponderacao-simulador")


@pytest.mark.parametrize("name", ["datafolha", "palver", "indexa"])
def test_frozen_sources_reproduce_poll_manifest(name):
    poll = getattr(M, name)()
    # Inventário inicial: a renda Datafolha foi completada na revisão de 16/10.
    inventory = json.loads(
        (ROOT / "docs/assets/reponderacao_20261015.json").read_text()
    )
    saved = next(p for p in inventory["pesquisas"] if p["id"] == poll["id"])
    assert poll == saved
    assert poll["divulgacao"] == "2026-10-15"
    assert sum(poll["publicado"]["2t"].values()) == 100


def test_datafolha_uses_new_release_and_rejects_old_panel_crossbreaks():
    poll = M.datafolha()
    panel = json.loads((ROOT / poll["conferencia_painel"]["arquivo"]).read_text())[
        "resultado"
    ]
    assert {v["date"][:10] for v in panel["cenarios"][0]["data"]} == {"2026-10-08"}
    assert poll["registro_tse"] == "BR-00466/2026"
    assert poll["campo"] == {"inicio": "2026-10-13", "fim": "2026-10-14"}
    assert poll["publicado"]["2t"] == {
        "flavio": 47,
        "lula": 45,
        "branco_nulo": 6,
        "indecisos": 2,
    }
    assert poll["ignorar"] and not poll["cruzamentos"] and "renda" not in poll
    assert poll["cruzamentos_documentais"]["linhas"][-1] == [None, None]
    assert not poll["conferencia_painel"]["usado_na_onda_nova"]


def test_palver_uses_current_weighted_profile_and_checks_independent_margin():
    poll = M.palver()
    assert poll["renda"]["amostra_pct"] == [36, 41, 23]
    assert poll["metodologia_onda"]["versao"] == "v3"
    assert not poll["metodologia_onda"]["comparavel_onda_anterior"]
    assert poll["registro_tse"] == "BR-08028/2026"
    assert poll["fonte"]["paginas"]["2t_renda"] == 24
    controls = poll["controles"]["2t"]
    assert controls["renda"]["recomposto"]["flavio"] == pytest.approx(50.56)
    assert controls["sexo"]["recomposto"]["lula"] == pytest.approx(48.88)
    assert max(c["residuo_max_abs"] for c in controls.values()) < 1
    processed = ENGINE.process_poll(poll, ENGINE.Benchmark(), ENGINE.load_ipca())
    adjusted = processed["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]["ajustado"]
    assert adjusted["flavio"] == pytest.approx(50.03, abs=0.01)
    assert adjusted["lula"] == pytest.approx(48.98, abs=0.01)


def test_indexa_keeps_nonvoters_distinct_and_does_not_invent_income_weights():
    poll = M.indexa()
    assert poll["instituto"] == "Indexa/Broadcast"
    pub = poll["publicado"]["2t"]
    assert pub["branco_nulo"] == 4 and pub["nao_vai_votar"] == 8
    assert poll["cruzamentos_documentais"]["perfil_pct"] is None
    assert poll["ignorar"] and not poll["cruzamentos"]
    preferences = SIM.preferences(pub, pub)
    assert preferences == {"flavio": 44, "lula": 42, "branco_nulo": 12, "indecisos": 2}
    # Publicados válidos arredondados não substituem os totais no motor.
    assert 100 * pub["flavio"] / (pub["flavio"] + pub["lula"]) != 51


def test_projection_replaces_datafolha_once_and_keeps_unadjustable_toplines():
    projection = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/f0d3e5a2ebd1076f.json").read_text()
    )["projection"]
    selected = {p["instituto"]: p for p in projection["selected"]}
    assert len(selected) == len(projection["selected"]) == 11
    assert selected["Datafolha"]["id"] == "datafolha_2026-10-14"
    assert selected["Palver"]["id"] == "palver_2026-10-13"
    assert "AtlasIntel" not in selected  # Campo de 03–08/10 atravessa o 1º turno.
    for house in ["Datafolha", "Indexa/Broadcast"]:
        assert not selected[house]["income_available"]
        assert selected[house]["pnad"] == selected[house]["published"]
    assert selected["Palver"]["income_available"]
    assert sum(p["weight"] for p in selected.values()) == pytest.approx(1)


def test_palver_documentary_history_respects_archive_cutoff_and_absent_turn():
    view = importlib.import_module("reponderacao-palver-view")
    close = importlib.import_module("reponderacao-arquivo").close
    data = ENGINE.build(date(2026, 10, 15))
    frozen = close(data, "2026-10-04")
    assert "palver_2026-10-13" not in {p["id"] for p in view.history_polls(frozen)}
    tables = []

    def collect_table(headers, rows):
        tables.append(rows)
        return ""

    view.audit_html(data, collect_table)
    wave7 = next(row for row in tables[0] if "onda 7" in row[0])
    assert wave7[1:3] == ["—", "—"]
    assert wave7[-1] == "Só 2º turno"
