"""Regressões documentais: nova renda por onda, cobertura por turno e agregação."""

import importlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
POLL_DIR = ROOT / "analysis/reponderacao/pesquisas"


def read(path):
    return json.loads((ROOT / path).read_text())


@pytest.fixture(scope="module")
def output():
    return read("docs/assets/reponderacao_pnad.json")


@pytest.mark.parametrize(
    "slug,turns,topline",
    [
        ("atlas_2026-09-16", {"1t"}, [46.8, 47.2]),
        ("poderdata_2026-09-16", {"1t", "2t"}, [44, 46]),
        ("gerp_2026-09-16", {"1t", "2t"}, [43, 50]),
        ("futura_2026-09-15", set(), [43.7, 48.1]),
    ],
)
def test_documented_coverage_is_not_imputed(output, slug, turns, topline):
    raw = json.loads((POLL_DIR / f"{slug}.json").read_text())
    assert set(raw["cruzamentos"]) == turns
    assert [raw["publicado"]["2t"][c] for c in ["lula", "flavio"]] == topline
    if turns:
        p = next(p for p in output["pesquisas"] if p["id"] == slug)
        expected_turns = turns - (
            {"1t"} if "marcal" in raw.get("publicado", {}).get("1t", {}) else set()
        )
        assert set(p["turnos"]) == expected_turns
        if expected_turns != turns:
            assert p["selecao_1t"]["status"] == "excluido_com_marcal"
            assert "1t" in p["turnos_arquivados"]
        assert p["publicado"]["2t"] == raw["publicado"]["2t"]
    else:
        assert raw["ignorar"]
        assert any(p["id"] == slug for p in output["nao_reponderaveis"])
        assert not any(p["id"] == slug for p in output["pesquisas"])


def test_atlas_uses_current_income_profile_and_independent_check(output):
    p = next(p for p in output["pesquisas"] if p["id"] == "atlas_2026-09-16")
    assert p["renda"]["amostra_pct"] == [17.8, 12.4, 27.0, 26.3, 16.5]
    r = p["turnos"]["1t"]
    assert r["residuo_max"] == pytest.approx(0.052)
    assert r["cenarios"]["pessoas16_efetivo"]["ajustado"]["lula"] == pytest.approx(
        44.443
    )
    audit = read("analysis/reponderacao/auditoria_20260917.json")
    atlas = next(p for p in audit["pesquisas"] if p["id"].startswith("atlas_"))
    assert atlas["provas"]["1t"]["recomposto_sexo_lula_flavio"] == [44.0605, 41.7314]


def test_gerp_uses_weighted_shares_not_raw_counts(output):
    p = next(p for p in output["pesquisas"] if p["id"] == "gerp_2026-09-16")
    assert p["renda"]["amostra_pct"] == [23, 23, 33, 14, 5, 2]
    r = p["turnos"]["2t"]
    assert r["recomposto"]["lula"] == pytest.approx(42.44)
    assert r["recomposto"]["flavio"] == pytest.approx(49.65)
    adj = r["cenarios"]["pessoas16_efetivo"]["ajustado"]
    assert [adj[c] for c in ["lula", "flavio"]] == pytest.approx([41.612, 51.751])


def test_new_results_stay_in_bounds_and_recompose(output):
    for p in output["pesquisas"]:
        if p["id"] not in {
            "atlas_2026-09-16",
            "poderdata_2026-09-16",
            "gerp_2026-09-16",
        }:
            continue
        for r in p["turnos"].values():
            assert r["residuo_max"] <= 0.65
            for scenario in r["cenarios"].values():
                assert all(0 <= v <= 100 for v in scenario["ajustado"].values())


def test_latest_comparable_mean_includes_gerp_and_poderdata(output):
    latest = {}
    for p in sorted(output["pesquisas"], key=lambda p: p["campo"]["fim"]):
        if "2t" in p["turnos"]:
            latest[p["instituto"]] = p
    assert latest["Gerp"]["id"] == "gerp_2026-09-16"
    assert latest["PoderData"]["id"] == "poderdata_2026-09-16"
    assert not ({"AtlasIntel", "Futura"} & latest.keys())
    avg = sum(
        p["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]["ajustado"]["flavio"]
        for p in latest.values()
    ) / len(latest)
    assert output["agregador"]["ultimo"]["2t"]["media_simples"]["ajustado"][
        "flavio"
    ] == round(avg, 2)


def test_page_shows_all_four_sources_without_fake_adjustments(output, monkeypatch):
    """Exercita a cobertura histórica sem exigir que 17/09 seja sempre a última onda."""
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    builder = importlib.import_module("reponderacao-build")
    historical = {
        **output,
        **{
            key: [
                p
                for p in output[key]
                if max(
                    p.get("divulgacao") or p["campo"]["fim"],
                    p.get("fonte", {}).get("relatorio_completo", ""),
                )
                <= "2026-09-17"
            ]
            for key in ["pesquisas", "nao_reponderaveis"]
        },
    }
    html = BeautifulSoup(
        builder.coverage_html(historical, builder.tabela), "html.parser"
    )
    section = html.find(id="atualizacao")
    text = section.get_text(" ", strip=True)
    for name in ["AtlasIntel", "PoderData", "Gerp", "Futura", "17/09/2026"]:
        assert name in text
    assert text.count("Sem cruzamento de renda") == 2
    assert text.count("Excluído: cenário com Marçal") == 3
    assert len(section.select('a[href$=".pdf"]')) == 4
    assert "Lula × Flávio" in text
    assert "mesmo conjunto" in text
    assert html.find(id="sem-cruzamento")


def test_sources_have_integrity_metadata():
    audit = read("analysis/reponderacao/auditoria_20260917.json")
    assert len(audit["pesquisas"]) == 4
    for p in audit["pesquisas"]:
        raw = json.loads((POLL_DIR / f"{p['id']}.json").read_text())
        assert raw["fonte"] == p["fonte"]
        assert len(p["fonte"]["sha256"]) == 64
        assert p["fonte"]["bytes"] > 100_000
        assert p["fonte"]["total_paginas"] > 20


def test_poderdata_second_round_comes_from_official_graph(output):
    p = next(p for p in output["pesquisas"] if p["id"] == "poderdata_2026-09-16")
    r = p["turnos"]["2t"]
    assert r["opcoes"] == ["lula", "flavio"]
    assert r["recomposto"] == {"lula": 43.37, "flavio": 45.6}
    assert r["residuo_max"] == pytest.approx(0.63)
    source = p["fonte"]["complementos"][0]
    assert source["url"].endswith("16-set-2026-05-scaled.png")
    assert len(source["sha256"]) == 64
    audit = read("analysis/reponderacao/auditoria_20260917.json")
    poder = next(p for p in audit["pesquisas"] if p["id"].startswith("poderdata_"))
    assert poder["provas"]["2t"]["recomposto_sexo_lula_flavio"] == [44.42, 45.52]
