"""Não confundir painel, universo, hipótese de perfil ou publicação com campo."""

import importlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

MODULE = importlib.import_module("pesquisas-081026-renda")
ROOT = Path(__file__).resolve().parents[1]
POLLS = ROOT / "analysis/reponderacao/pesquisas"
SCENARIO = "pessoas16_efetivo"


def read(path):
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def output():
    return read(ROOT / "docs/assets/reponderacao_pnad.json")


def test_current_g1_schema_is_second_round_and_matches_archived_source(output):
    items = MODULE.archive("datafolha_102026_08")
    raw = MODULE.datafolha(items)
    assert raw == read(POLLS / "datafolha_2026-10-08.json")
    assert set(raw["publicado"]) == set(raw["cruzamentos"]) == {"2t"}
    assert raw["registro_tse"] == "BR-02949/2026"
    assert raw["n"] == 2520
    assert raw["publicado"]["2t"] == {
        "lula": 45,
        "flavio": 49,
        "branco_nulo": 5,
        "indecisos": 1,
    }
    assert raw["publicado_validos"]["2t"] == {"lula": 48, "flavio": 52}
    assert raw["cruzamentos"]["2t"]["linhas"] == [
        [52, 41, 5, 2],
        [38, 56, 5, 1],
        [39, 55, 5, 1],
    ]
    poll = next(p for p in output["pesquisas"] if p["id"] == raw["id"])
    adjusted = poll["turnos"]["2t"]["cenarios"][SCENARIO]["ajustado"]
    assert adjusted["lula"] == pytest.approx(43.01, abs=0.01)
    assert adjusted["flavio"] == pytest.approx(51.14, abs=0.01)
    assert raw["renda"]["perfil_tipo"] == "hipotese_onda_anterior"
    assert "não comprovam" in raw["renda"]["nota"]
    assert "6–7/10" in raw["fonte"]["nota"]


def test_g1_rejects_stale_wave_and_hash_mismatch(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="outra onda"):
        MODULE.panel_row(
            [{"date": "2026-10-03T00:00:00Z", "option": "Lula", "value": 0.47}]
        )
    folder = tmp_path / "data/originals/test"
    folder.mkdir(parents=True)
    (folder / "fonte.json").write_text(
        json.dumps(
            {
                "arquivos": [
                    {
                        "arquivo": "data/originals/test/source.json",
                        "bytes": 2,
                        "sha256": "invalid",
                    }
                ]
            }
        )
    )
    (folder / "source.json").write_text("{}")
    monkeypatch.setattr(MODULE, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Fonte arquivada mudou"):
        MODULE.archive("test")


def test_poderdata_uses_current_profile_and_total_vote_tables(output):
    raw = MODULE.poderdata(MODULE.archive("poderdata_102026_08"))
    assert raw == read(POLLS / "poderdata_2026-10-07.json")
    assert raw["renda"]["amostra_pct"] == [46, 33, 21]
    assert raw["publicado"]["2t"] == {
        "lula": 44,
        "flavio": 49,
        "branco_nulo": 5,
        "indecisos": 2,
    }
    assert set(raw["cruzamentos"]) == {"2t"}
    for dim in ("renda", "sexo"):
        assert raw["controles"]["2t"][dim]["residuo_max_abs"] <= 0.68
    poll = next(p for p in output["pesquisas"] if p["id"] == raw["id"])
    adjusted = poll["turnos"]["2t"]["cenarios"][SCENARIO]["ajustado"]
    assert adjusted["lula"] == pytest.approx(43.21, abs=0.01)
    assert adjusted["flavio"] == pytest.approx(50.53, abs=0.01)


def test_latest_waves_replace_old_ones_only_in_the_measured_ballot(output):
    latest = output["agregador"]["ultimo"]
    assert output["referencia"] >= "2026-10-08"
    second = latest["2t"]["cobertura_movel"]["ondas"]
    first = latest["1t"]["cobertura_movel"]["ondas"]
    assert {"datafolha_2026-10-08", "poderdata_2026-10-07"} <= set(second)
    assert {"datafolha_2026-10-03", "poderdata_2026-10-02"}.isdisjoint(second)
    assert "datafolha_2026-10-03" in first
    assert "poderdata_2026-10-02" in first


def test_verita_valid_only_publication_never_enters_total_vote_averages(output):
    raw = read(POLLS / "verita_2026-10-02.json")
    assert raw["ignorar"] and not raw["publicado"] and not raw["cruzamentos"]
    assert raw["campo"]["fim"] < raw["divulgacao"]
    assert raw["publicado_validos"]["2t"] == {"lula": 48.44, "flavio": 51.56}
    assert raw["id"] not in {p["id"] for p in output["pesquisas"]}
    skipped = next(p for p in output["nao_reponderaveis"] if p["id"] == raw["id"])
    assert skipped["publicado_validos"] == raw["publicado_validos"]
    for ballot in output["agregador"]["cobertura_movel"].values():
        assert all(raw["id"] not in row["ondas"] for row in ballot)


def test_page_exposes_hypothesis_valid_vote_label_and_search_limits():
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    card = page.find(id="pesquisa-datafolha_2026-10-08")
    assert "O perfil assumido tem" in card.get_text(" ", strip=True)
    assert "PERFIL ASSUMIDO" in card.get_text(" ", strip=True)
    assert "não comprovam" in card.get_text(" ", strip=True)
    log = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad_log.html").read_text(), "html.parser"
    )
    update = log.get_text(" ", strip=True)
    assert "48,4 × 51,6 (válidos)" in update
    assert "Não foi localizada outra nova onda nacional" in update
    assert "anterior ao 1º turno" in update
