"""Ondas finais da AtlasIntel (campo de 27/09 a 02/10/2026)."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FICHA = ROOT / "analysis/reponderacao/pesquisas/atlas_2026-10-02.json"
ESTADUAIS = ROOT / "analysis/predicao_2026/estaduais"
OUTPUT = ROOT / "docs/assets/reponderacao_pnad.json"
PREDICAO = ROOT / "docs/assets/predicao_2026_1T_presidente.json"
UFS = ["AC", "BA", "CE", "ES", "GO", "MS", "MT", "PA", "PI", "RJ", "SP"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pdf_or_skip(path: Path) -> Path:
    # O CI baixa os PDFs do LFS; fora dele, um ponteiro não é o relatório.
    if path.stat().st_size < 10_000:
        pytest.skip("PDF do LFS ausente")
    return path


def test_national_file_matches_archived_report():
    raw = load(FICHA)
    pdf = pdf_or_skip(ROOT / raw["fonte"]["pdf"])
    assert raw["fonte"]["sha256"] == sha(pdf)
    assert raw["fonte"]["bytes"] == pdf.stat().st_size
    assert raw["registro_tse"] == "BR-00999/2026"
    assert raw["campo"] == {"inicio": "2026-09-27", "fim": "2026-10-02"}
    assert raw["divulgacao"] == "2026-10-03"
    assert raw["n"] == 4945


def test_national_topline_profile_and_crossbreak():
    raw = load(FICHA)
    first = raw["publicado"]["1t"]
    assert (first["lula"], first["flavio"]) == (46.7, 43.8)
    assert sum(first.values()) == pytest.approx(100.1, abs=1e-9)
    assert raw["publicado"]["2t"] == {"lula": 47.6, "flavio": 47.4, "branco_nulo": 5.0}
    assert raw["renda"]["amostra_pct"] == [20.0, 12.0, 24.0, 26.6, 17.4]
    table = raw["cruzamentos"]["1t"]
    assert len(table["linhas"]) == 5
    # Rui, Zema, Samara e Clariana não têm linha no cruzamento: nada imputado.
    assert not {"rui", "zema", "samara", "clariana"} & set(table["opcoes"])
    assert "2t" not in raw["cruzamentos"]


def test_independent_crossbreaks_recompose_the_topline():
    control = load(FICHA)["cruzamentos"]["1t"]["controle"]
    for name in ("sexo", "regiao"):
        block = control[name]
        weights = list(block["pesos"].values())
        for cand, published in (("lula", 46.7), ("flavio", 43.8)):
            value = sum(w * v for w, v in zip(weights, block[cand], strict=True))
            value /= sum(weights)
            assert value == pytest.approx(block["recomposto"][cand], abs=0.001)
            assert abs(value - published) < 0.1


def test_engine_output_residual_and_adjustment():
    poll = next(p for p in load(OUTPUT)["pesquisas"] if p["id"] == "atlas_2026-10-02")
    first = poll["turnos"]["1t"]
    assert first["residuo_max"] < 0.1
    assert first["recomposto"]["lula"] == pytest.approx(46.753, abs=0.001)
    assert first["recomposto"]["flavio"] == pytest.approx(43.748, abs=0.001)
    adjusted = first["cenarios"]["pessoas16_efetivo"]["ajustado"]
    assert adjusted["lula"] == pytest.approx(46.74, abs=0.01)
    assert adjusted["flavio"] == pytest.approx(43.83, abs=0.01)
    assert "2t" not in poll["turnos"]


def test_final_atlas_replaces_previous_wave_in_window():
    data = load(OUTPUT)
    last = data["agregador"]["ultimo"]["1t"]["cobertura_movel"]
    assert "atlas_2026-10-02" in last["ondas"]
    assert "atlas_2026-09-28" not in last["ondas"]
    forecast = load(PREDICAO)
    ids = {p["id"] for p in forecast["nacional"]["selecionadas"]}
    assert "atlas_2026-10-02" in ids and "atlas_2026-09-28" not in ids


@pytest.mark.parametrize("uf", UFS)
def test_state_files_close_and_match_archive(uf):
    raw = load(ESTADUAIS / f"atlasintel_{uf}_20261002.json")
    assert raw["instituto"] == "AtlasIntel" and raw["uf"] == uf
    assert raw["campo"] == "2026-09-27 a 2026-10-02"
    assert raw["registro_tse"].startswith("BR-")
    assert raw["registro_tse_estadual"].startswith(f"{uf}-")
    pdf = pdf_or_skip(ROOT / raw["arquivo"])
    assert raw["sha256_pdf"] == sha(pdf)
    first = raw["pres_1t"]["valores"]
    assert abs(sum(first.values()) - 100) <= 0.25
    assert {"Lula", "Flávio", "Branco/nulo", "Indecisos"} <= set(first)
    second = raw["pres_2t"]["cenarios"][0]
    total = sum(
        v
        for k, v in second.items()
        if k in ("Lula", "Flávio", "Branco/nulo", "Indecisos") and v
    )
    assert abs(total - 100) <= 0.15
    assert "comparecimento_compacto" not in raw


def test_state_toplines_spot_checks():
    expected = {
        "SP": ((42.0, 46.3), (42.9, 49.6)),
        "RJ": ((43.5, 46.6), (46.4, 48.7)),
        "BA": ((59.1, 29.2), (61.6, 34.3)),
        "AC": ((29.0, 59.7), (31.7, 64.2)),
    }
    for uf, (t1, t2) in expected.items():
        raw = load(ESTADUAIS / f"atlasintel_{uf}_20261002.json")
        v = raw["pres_1t"]["valores"]
        s = raw["pres_2t"]["cenarios"][0]
        assert (v["Lula"], v["Flávio"]) == t1
        assert (s["Lula"], s["Flávio"]) == t2


def test_state_waves_replace_previous_atlas_in_forecast():
    forecast = load(PREDICAO)
    chosen = {
        p["uf"]: p["arquivo"]
        for s in forecast["estados"]
        for p in s["pesquisas"]
        if p["instituto"] == "AtlasIntel"
    }
    for uf in UFS:
        assert chosen[uf].endswith(f"atlasintel_{uf}_20261002.json")
    excluded = {e["arquivo"] for e in forecast["estaduais_excluidas"]}
    for uf in UFS:
        previous = load(ESTADUAIS / f"atlasintel_{uf}_20261002.json")["substitui"]
        if previous:
            assert previous in excluded
