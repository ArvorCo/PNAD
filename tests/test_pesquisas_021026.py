"""Integração das íntegras de outubro, sem imputar cruzamentos nem duplicar ondas."""

import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
BASE = ROOT / "analysis/reponderacao"
AUDIT = json.loads((BASE / "atualizacao_20261002/auditoria.json").read_text())
DATA = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
MODEL = json.loads((ROOT / "docs/assets/reponderacao_validos.json").read_text())


def raw(ident):
    return json.loads((BASE / f"pesquisas/{ident}.json").read_text())


def test_full_sources_and_catalogue_variants_match_their_checksums():
    assert len(AUDIT["fontes"]) == 6
    assert sum("pdf" in p["fonte"] for p in AUDIT["fontes"]) == 5
    for p in AUDIT["fontes"]:
        src = p["fonte"]
        payload = (ROOT / src.get("pdf", src.get("arquivo"))).read_bytes()
        assert len(payload) == src["bytes"]
        assert hashlib.sha256(payload).hexdigest() == src["sha256"]
    catalogue = json.loads((BASE / "atualizacao_20261002/catalogo-fontes.json").read_text())
    assert len(catalogue) == 14
    for src in catalogue:
        payload = (ROOT / src["arquivo"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == src["sha256"]


def test_five_new_income_crossbreaks_pass_independent_controls():
    assert len(AUDIT["controles"]) == 5
    for c in AUDIT["controles"]:
        assert c["renda_residuo_max_pp"] <= 1.5
        assert c["controles_independentes"]
        assert all(x["residuo_max_pp"] < 1 for x in c["controles_independentes"])


def test_datafolha_extracts_whole_annex_and_uses_vote_bases():
    p = raw("datafolha_2026-10-01")
    assert p["renda"]["bases"] == [1209, 856, 344]
    assert p["n"] - sum(p["renda"]["bases"]) == p["renda"]["nao_publicada_n"] == 97
    annex = json.loads((ROOT / p["fonte"]["extracao"]).read_text())
    assert len(annex["tabelas"]) == 18
    for table in annex["tabelas"].values():
        assert set(table["blocks"]) == {"bloco1", "bloco2", "bloco3"}
        assert all(b["base"]["Total"] >= 1 for b in table["blocks"].values())
    for turn in ["1t", "2t"]:
        controls = next(c for c in AUDIT["controles"] if c["id"] == p["id"] and c["turno"] == turn)
        assert {c["particao"] for c in controls["controles_independentes"]} == {"sexo", "regiao"}
    assert p["divulgacao"] == "2026-10-01"
    assert p["fonte"]["relatorio_completo"] == "2026-10-02"


def test_indexa_preserves_nonchoice_partition_without_filling_missing_candidates():
    p = raw("indexa_2026-09-29")
    assert sum(p["publicado"]["1t"].values()) == 100
    assert sum(p["publicado"]["2t"].values()) == 100
    assert p["cruzamentos"]["2t"]["linhas"][0] == [47, 34, 14, 5]
    assert p["publicado"]["2t"]["branco_nulo"] == 11  # 7 + 4 não iria votar
    assert "samara" not in p["cruzamentos"]["1t"]["opcoes"]
    assert p["publicado"]["1t"]["samara"] == 0
    processed = next(q for q in DATA["pesquisas"] if q["id"] == p["id"])
    row = importlib.import_module("reponderacao-validos").prepare(processed, "2t")
    assert set(row["published"]) == {"lula", "flavio"}
    assert sum(row["published"].values()) == 85


def test_latest_real_time_keeps_partial_table_and_is_excluded_from_valid_vote_model():
    p = raw("realtime_2026-09-30")
    assert set(p["cruzamentos"]) == {"1t"}
    assert p["publicado"]["1t"]["outros"] == 1
    assert "outros" not in p["cruzamentos"]["1t"]["opcoes"]
    for turn in ["1t", "2t"]:
        block = MODEL["ballots"][turn]
        assert any(x["id"] == p["id"] for x in block["excluded"])
        assert not any(x["instituto"] == p["instituto"] for x in block["scenarios"]["central"]["polls"])


def test_unidentified_income_votes_remain_outside_every_income_average():
    ids = {"futura_2026-09-29", "vox_brasil_2026-10-01", "alfa_2026-09-23"}
    assert ids <= {p["id"] for p in DATA["nao_reponderaveis"]}
    assert not ids & {p["id"] for p in DATA["pesquisas"]}
    for ident in ids:
        assert not raw(ident)["cruzamentos"]
    assert raw("futura_2026-09-29")["n"] == 2000
    assert raw("futura_2026-09-29")["divulgacao"] == "2026-09-30"


def test_both_models_and_public_page_use_new_waves_at_original_publication_dates():
    for turn in ["1t", "2t"]:
        block = MODEL["ballots"][turn]
        polls = block["scenarios"]["central"]["polls"]
        for house, ident in [("Datafolha", "datafolha_2026-10-01"),
                             ("Indexa/Broadcast", "indexa_2026-09-29")]:
            chosen = next(p for p in polls if p["instituto"] == house)
            assert chosen["id"] == ident
            assert chosen["divulgacao"] == raw(ident)["divulgacao"]
        for scenario in block["scenarios"].values():
            assert sum(scenario["aggregate"]["modelo"].values()) == pytest.approx(100)
    page = BeautifulSoup((ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser")
    text = page.find(id="atualizacao").get_text(" ", strip=True)
    assert "02/10/2026" in text and "Indexa/Broadcast" in text
    assert "97 dos 2.506" in page.get_text(" ", strip=True)
