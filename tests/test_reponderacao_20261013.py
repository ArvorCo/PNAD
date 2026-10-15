"""Íntegras, massa conhecida, oito casas inclusivas e revisão sem onda dupla."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
M = importlib.import_module("pesquisas-131026-renda")
ENGINE = importlib.import_module("reponderacao-pnad")
SIM = importlib.import_module("reponderacao-simulador")
ARCHIVE = importlib.import_module("reponderacao-arquivo")
NAMES = ["gerp", "poderdata", "nexus", "ipespe", "datafolha", "futura", "datatrends"]


def read(path):
    return json.loads((ROOT / path).read_text())


@pytest.mark.parametrize("name", NAMES)
def test_transcription_sources_hashes_and_controls(name):
    raw = getattr(M, name)()
    assert raw == read("analysis/reponderacao/pesquisas/" + raw["id"] + ".json")
    source = raw["fonte"]
    payload = (ROOT / source["pdf"]).read_bytes()
    assert payload.startswith(b"%PDF")
    assert len(payload) == source["bytes"]
    assert hashlib.sha256(payload).hexdigest() == source["sha256"]
    assert raw["campo"]["inicio"] > "2026-10-04"
    assert raw["divulgacao"] <= "2026-10-13"
    for dimension in raw.get("controles", {}).get("2t", {}).values():
        assert dimension["residuo_max_abs"] < 1.0


@pytest.mark.parametrize("name", ["datafolha", "gerp"])
def test_delta_is_limited_to_known_income_mass_without_imputing_missing(name):
    raw = getattr(M, name)()
    poll = ENGINE.process_poll(raw, ENGINE.Benchmark(), ENGINE.load_ipca())
    adjusted = poll["turnos"]["2t"]
    fraction = raw["renda"]["parcela_ajustada_pct"] / 100
    expected = 2398 / 2520 if name == "datafolha" else 87 / 101
    assert fraction == pytest.approx(expected, abs=1e-15)
    for scenario in adjusted["cenarios"].values():
        for key, value in scenario["ajustado"].items():
            independent = raw["publicado"]["2t"][key] + fraction * (
                scenario["contrafactual"][key]
                - raw["controles"]["2t"]["renda"]["recomposto"][key]
            )
            # Contrafactual e saída são publicados com três casas decimais.
            assert value == pytest.approx(independent, abs=0.001)
    # Uma troca nula precisa preservar exatamente o topline, com ou sem NS/NR.
    control = ENGINE.reweight_table(
        raw["cruzamentos"]["2t"],
        raw["publicado"]["2t"],
        ENGINE.source_profile(raw),
        {"identity": ENGINE.source_profile(raw)},
        fraction,
    )
    assert control["cenarios"]["identity"]["ajustado"] == raw["publicado"]["2t"]


def test_datafolha_revision_uses_actual_weighted_bases_and_keeps_wave_identity():
    raw = M.datafolha()
    assert raw["id"] == "datafolha_2026-10-08"
    assert raw["campo"] == {"inicio": "2026-10-06", "fim": "2026-10-07"}
    assert raw["renda"]["bases"] == [1187, 874, 337]
    assert raw["renda"]["perfil_tipo"] == "perfil_ponderado"
    assert raw["fonte"]["paginas"]["perfil_renda"] == 23
    assert raw["fonte"]["paginas"]["2t_renda"] == 26
    assert raw["fonte"]["relatorio_completo"] == "2026-10-13"
    assert (ROOT / raw["fonte"]["pdf"]).read_bytes() == (
        ROOT / "docs/fontes/datafolha_2t_08102026_integra.pdf"
    ).read_bytes()


def test_futura_profile_and_datatrends_ambiguous_unit_do_not_become_income_votes():
    futura, dt = M.futura(), M.datatrends()
    assert futura["ignorar"] and not futura["cruzamentos"]
    assert futura["perfil_economico_publicado"]["pct"] == [26.9, 21.8, 24.1, 10, 6]
    assert dt["ignorar"] and not dt["cruzamentos"]
    assert len(dt["cruzamentos_documentais"]["linhas"]) == 3
    assert "per capita" in dt["motivo"] and "total" in dt["motivo"]
    assert dt["publicado"]["2t"]["indecisos"] == 1
    assert dt["publicado_alternativo"]["2t"]["indecisos"] == 2
    assert M.ipespe()["publicado"]["2t"]["indecisos"] == 3
    assert "CATI" in M.ipespe()["metodo"]


def test_both_updated_centres_use_correct_houses_and_preserve_accounting():
    # Contrato da rodada de 13/10: a página corrente continua recebendo ondas.
    data = read("docs/assets/reponderacao_cenarios/dae267a6d8ba1054.json")
    assert data["reference"] == "2026-10-13"
    assert {p["instituto"] for p in data["polls"]} == {
        "Datafolha",
        "Gerp",
        "PoderData",
        "Nexus",
        "Ipespe",
    }
    selected = data["projection"]["selected"]
    assert len(selected) == len({p["instituto"] for p in selected}) == 8
    for p in selected:
        if p["instituto"] in {"Futura", "DataTrends", "Vox Brasil"}:
            assert not p["income_available"] and p["pnad"] == p["published"]
    assert sum(p["weight"] for p in selected) == pytest.approx(1)
    assert data["defaults"]["presenca_relativa"] == 3.8
    assert data["defaults"]["comparecimento"] == pytest.approx(79.15788247440102)
    for key, params in [
        ("central", {}),
        ("central_projection", {"centro": "projecao"}),
    ]:
        result = SIM.evaluate(data, params)
        assert result == data[key]
        assert result["flavio"] + result["lula"] == pytest.approx(100)
        assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
    assert data["central"]["flavio"] == pytest.approx(54.662267836284606)
    assert data["central_projection"]["flavio"] == pytest.approx(53.99260407775258)
    assert not data["projection"]["trend"]["pnad"]["available"]


def test_states_cover_only_df_without_counting_each_house_as_extra_electorate():
    states = read("docs/assets/reponderacao_estaduais.json")
    assert states["covered_ufs"] == ["DF"] and len(states["selected"]) == 2
    assert states["coverage_pct"] == pytest.approx(1.4308653402587033)
    assert states["covered_electorate"] == states["selected"][0]["electorate"]
    row = next(p for p in states["selected"] if p["instituto"] == "Quaest")
    assert row["n"] == 1104 and row["campo"]["inicio"] == "2026-10-08"
    assert row["publicado"] == {
        "flavio": 50,
        "lula": 40,
        "branco_nulo": 6,
        "indecisos": 4,
    }
    assert row["validos_normalizados"]["flavio"] == pytest.approx(100 * 50 / 90)
    assert "não altera" in states["use"]


def test_first_round_archive_keeps_coverage_on_election_day_as_live_window_expires():
    live = read("docs/assets/reponderacao_pnad.json")
    before = json.dumps(live, sort_keys=True)
    closed = ARCHIVE.close(live, "2026-10-04")
    assert json.dumps(live, sort_keys=True) == before
    assert (
        closed["referencia"]
        == closed["agregador"]["serie"]["datas"][-1]
        == "2026-10-04"
    )
    assert all(p["divulgacao"] <= "2026-10-04" for p in closed["pesquisas"])
    assert (
        "atlas_2026-10-02"
        in closed["agregador"]["ultimo"]["1t"]["cobertura_movel"]["ondas"]
    )
    assert (
        closed["agregador"]["nao_escolha"]["1t"]["ultimo"]["publicado"]["indecisos"] > 0
    )
    assert not live["agregador"]["ultimo"]["1t"]["cobertura_movel"]["ondas"]
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad_1o_turno_2026.html").read_text(), "html.parser"
    )
    assert "VOTOS VÁLIDOS · 2026-10-04" in page.select_one(
        "#projecao-validos"
    ).get_text(" ", strip=True)
    coverage = page.select_one("#primeiro-turno").get_text(" ", strip=True)
    assert (
        "Sem pesquisa na janela"
        not in coverage.split("Cobertura atual", 1)[1].split("Conferir", 1)[0]
    )


def test_rendering_first_round_does_not_overwrite_current_second_round_data():
    assets = [
        ROOT / "docs/assets/reponderacao_validos.json",
        ROOT / "docs/assets/reponderacao_validos.csv",
    ]
    before = [p.read_bytes() for p in assets]
    reference = read("docs/assets/reponderacao_validos.json")["ballots"]["2t"][
        "reference"
    ]
    closed = ARCHIVE.close(read("docs/assets/reponderacao_pnad.json"), "2026-10-04")
    html = importlib.import_module("reponderacao-validos-view").section_html(
        closed, lambda headers, rows: "", ("1t",)
    )
    assert "2026-10-04" in html
    assert [p.read_bytes() for p in assets] == before
    assert (
        read("docs/assets/reponderacao_validos.json")["ballots"]["2t"]["reference"]
        == reference
    )


def test_current_cards_evidence_and_diary_disclose_revisions_without_duplication():
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    for name in ["gerp", "poderdata", "nexus", "ipespe", "datafolha"]:
        raw = getattr(M, name)()
        assert page.select_one("#pesquisa-" + raw["id"])
    df = page.select_one("#pesquisa-datafolha_2026-10-08").get_text(" ", strip=True)
    assert "PERFIL ASSUMIDO" not in df and "1.187/874/337" in df
    card = page.select_one('.rs-central-card[data-central-card="media"]')
    assert all(
        name in card.get_text() for name in ["DataTrends", "Futura", "Vox Brasil"]
    )
    projection = page.select_one('.rs-central-card[data-central-card="projecao"]')
    current = read("docs/assets/reponderacao_simulador.json")
    futura = next(
        p for p in current["projection"]["selected"] if p["instituto"] == "Futura"
    )
    weight = f'{100 * futura["weight"]:.1f}%'.replace(".", ",")
    assert "Futura" in projection.get_text() and weight in projection.get_text()
    evidence = page.select_one("#modelo-projecao").get_text(" ", strip=True)
    assert "+0,24 pp" in evidence and "2,29 e 2,53" in evidence
    assert page.select_one(
        '#modelo-projecao a[href="apuracao_1o_turno_2026.html#pesquisas"]'
    )
    assert page.select_one('#estados-projecao a[href*="quaest-no-df"]')
    history = read("analysis/reponderacao/log.json")
    assert len([w for w in history["waves"] if w["id"] == "datafolha_2026-10-08"]) == 1
    new = [w for w in history["waves"] if w["id"] == "gerp_2026-10-12"]
    assert len(new) == 1 and new[0]["added"] == "2026-10-13"
