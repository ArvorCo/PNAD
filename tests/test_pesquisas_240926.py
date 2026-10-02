"""Fontes da rodada de 24/09: integridade, cobertura e contas independentes."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/reponderacao"
DATA = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


AUDIT = json.loads((BASE / "atualizacao_20260924/verificacao.json").read_text())


def test_every_new_pdf_matches_archived_checksum_and_lfs_rule():
    assert "*.pdf filter=lfs" in (ROOT / ".gitattributes").read_text()
    for source in AUDIT["fontes"]:
        if not source.get("pdf"):
            continue
        payload = (ROOT / source["pdf"]).read_bytes()
        assert payload.startswith(b"%PDF")
        assert len(payload) == source["bytes"]
        assert hashlib.sha256(payload).hexdigest() == source["sha256"]


def test_each_eligible_turn_recomposes_income_and_sex():
    assert len(AUDIT["controles"]) == 8
    for check in AUDIT["controles"]:
        assert check["renda_residuo_max_pp"] <= 1.5
        assert check["controle_independente"]["residuo_max_pp"] <= 1.5
    palver = json.loads((BASE / "atualizacao_20260924/palver-margens.json").read_text())
    for margin in palver.values():
        assert margin["identified"]
        assert margin["rank"] == len(margin["groups"])
        assert margin["max_residual"] < 1e-10
        assert margin["reconstructed_neff"] == pytest.approx(
            margin["published_neff"], abs=1e-6
        )


def test_missing_crossbreaks_and_new_unusable_waves_do_not_enter_means():
    polls = {p["id"]: p for p in DATA["pesquisas"]}
    for ident in ["atlas_2026-09-22", "realtime_2026-09-23"]:
        assert set(polls[ident]["turnos"]) == {"1t"}
    assert polls["poderdata_2026-09-23"]["turnos"]["2t"]["opcoes"] == ["lula", "flavio"]
    skipped = {p["id"] for p in DATA["nao_reponderaveis"]}
    assert {
        "futura_2026-09-23",
        "verita_2026-09-19",
        "american_analytics_2026-09-20",
    } <= skipped
    # A íntegra tardia de 28/09 resolveu a pendência da Datafolha de 24/09.
    assert set(polls["datafolha_2026-09-23"]["turnos"]) == {"1t", "2t"}
    assert polls["datafolha_2026-09-23"]["fonte"]["relatorio_completo"] == "2026-09-28"
    for turn in ["1t", "2t"]:
        current = module("reponderacao-janela").coverage(
            [p for p in DATA["pesquisas"] if turn in p["turnos"]], ["2026-09-24"]
        )[0]
        assert current["data"] == "2026-09-24"
        assert not skipped.intersection(current["ondas"])
        assert "nexus_2026-09-20" in current["ondas"]


def test_quaest_complete_report_replaces_partial_without_new_wave():
    poll = next(p for p in DATA["pesquisas"] if p["id"] == "quaest_2026-09-20")
    assert poll["divulgacao"] == "2026-09-21"
    assert poll["fonte"]["total_paginas"] == 247
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    assert set(poll["turnos"]) == {"1t", "2t"}
    assert poll["turnos"]["2t"]["recomposto"] == pytest.approx(
        {"lula": 40.99, "flavio": 41.67, "branco_nulo": 13.84, "indecisos": 3.5}
    )


def test_quaest_state_archives_have_exact_bytes_and_distinct_universes():
    manifest = json.loads((ROOT / AUDIT["quaest_estaduais"]).read_text())
    assert {p["uf"] for p in manifest["estaduais"]} == {"SP", "RJ", "MG", "PE", "DF"}
    for p in [*manifest["estaduais"], manifest["nacional_recebida"]]:
        payload = (ROOT / p["arquivo"]).read_bytes()
        assert len(payload) == p["bytes"]
        assert hashlib.sha256(payload).hexdigest() == p["sha256"]
    national_registries = {p["registro_tse"] for p in DATA["pesquisas"]}
    assert not national_registries.intersection(
        p["registro_presidencial_estadual"] for p in manifest["estaduais"]
    )


def test_update_covers_both_release_days_and_pending_documents():
    # Test this historical update at its own date, not the mutable latest page.
    historical = copy.deepcopy(DATA)
    archived_sources = {s["id"]: s for s in AUDIT["fontes"]}
    for key in ("pesquisas", "nao_reponderaveis"):
        historical[key] = [
            p
            for p in historical[key]
            if (p.get("divulgacao") or p["campo"]["fim"]) <= "2026-09-24"
            and (p["id"] in archived_sources or max(
                p.get("fonte", {}).get("conferido_em", ""),
                p.get("fonte", {}).get("atualizado_em", ""),
            ) <= "2026-09-24")
        ]
        for poll in historical[key]:
            if poll["id"] in archived_sources:
                # Later documentary rechecks must not move a historical fixture.
                poll["fonte"] = copy.deepcopy(archived_sources[poll["id"]])
    fragment = module("reponderacao-cobertura").coverage_html(
        historical, lambda headers, rows: " ".join(str(c) for row in rows for c in row)
    )
    html = BeautifulSoup(fragment, "html.parser")
    section = html.find(id="atualizacao")
    text = section.get_text(" ", strip=True)
    for name in [
        "AtlasIntel",
        "Real Time Big Data",
        "Futura",
        "PoderData",
        "Palver",
        "Quaest",
        "Veritá",
        "Datafolha",
        "American Analytics",
    ]:
        assert name in text
    assert "23/09/2026" in text and "24/09/2026" in text
    assert "Substitui a fonte parcial" in text
    assert section.find("a", href="assets/reponderacao_20260924.json")
