"""Contratos do agregador Arvor: régua PNAD, motor de reponderação e média."""

import hashlib
import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLLS = ROOT / "analysis" / "reponderacao" / "pesquisas"
SCENARIO = "pessoas16_efetivo"


def load_module(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def engine():
    return load_module("reponderacao-pnad")


@pytest.fixture(scope="module")
def bench(engine):
    return engine.Benchmark()


@pytest.fixture(scope="module")
def output():
    return json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


def test_benchmark_reproduces_house_target(bench):
    """Os cortes de 2, 5 e 10 salários de 2026 devolvem a régua já publicada."""
    shares = bench.shares(SCENARIO, [3242.0, 8105.0, 16210.0, None])
    assert shares == pytest.approx([35.43, 39.22, 16.93, 8.43], abs=0.1)
    assert sum(shares) == pytest.approx(100.0, abs=1e-6)


def test_benchmark_universes_are_plausible(bench):
    """Pessoas 16+ perto de 168 milhões; domicílios perto de 79 milhões."""
    assert 160e6 < bench.total("pessoas16_efetivo") < 175e6
    assert 75e6 < bench.total("domicilios_efetivo") < 85e6


def test_reweight_is_identity_when_profiles_match(engine):
    table = {"opcoes": ["lula", "flavio"], "linhas": [[60, 40], [40, 60]]}
    published = {"lula": 50, "flavio": 50}
    result = engine.reweight_table(table, published, [50, 50], {"x": [50, 50]})
    assert result["cenarios"]["x"]["ajustado"] == {"lula": 50.0, "flavio": 50.0}
    assert result["residuo_max"] == 0.0


def test_reweight_moves_toward_richer_band(engine):
    table = {"opcoes": ["lula", "flavio"], "linhas": [[60, 40], [40, 60]]}
    published = {"lula": 50, "flavio": 50}
    result = engine.reweight_table(table, published, [50, 50], {"x": [30, 70]})
    assert result["cenarios"]["x"]["ajustado"]["lula"] == pytest.approx(46.0)
    assert result["cenarios"]["x"]["ajustado"]["flavio"] == pytest.approx(54.0)


def test_band_cuts_convert_minimum_wages_of_the_card_year(engine):
    poll = {
        "id": "x",
        "campo": {"fim": "2026-04-30"},
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "faixas": [{"max": 2}, {"max": 5}, {"max": None}],
        },
    }
    cuts = engine.band_cuts_brl(poll, {})
    assert cuts[0] == pytest.approx(3242.0)
    assert cuts[1] == pytest.approx(8105.0)
    assert cuts[2] is None


def test_last_band_must_be_open(engine):
    poll = {
        "id": "x",
        "campo": {"fim": "2026-04-30"},
        "renda": {"unidade": "reais_nominais", "faixas": [{"max": 3000}]},
    }
    with pytest.raises(ValueError):
        engine.band_cuts_brl(poll, {})


def test_difference_margin_matches_datafolha_august(engine):
    """47 × 43 com n = 2.058 dá ±4,1 pontos, o número publicado no dossiê."""
    assert engine.difference_margin(47, 43, 2058) == pytest.approx(4.1, abs=0.05)


def test_every_poll_file_recomposes_its_topline(output):
    """Prova de leitura: o cruzamento de renda recompõe o placar dentro de 1,5 pp."""
    for poll in output["pesquisas"]:
        for turno, result in poll["turnos"].items():
            assert result["residuo_max"] <= 1.5, (
                poll["id"],
                turno,
                result["residuo_max"],
            )


def test_datafolha_series_matches_published_dossier(output):
    """Os quatro gaps ajustados da série Datafolha ficam a 0,2 pp dos publicados no dossiê."""
    expected = {
        "datafolha_2026-05-21": -2.81,
        "datafolha_2026-06-18": -0.16,
        "datafolha_2026-07-23": 0.0,
        "datafolha_2026-08-19": -1.78,
    }
    found = {
        p["id"]: p["turnos"]["2t"]["gap_ajustado"]
        for p in output["pesquisas"]
        if "2t" in p["turnos"]
    }
    for key, value in expected.items():
        assert found[key] == pytest.approx(value, abs=0.2), key


def test_aggregator_series_covers_reference_date(output):
    agg = output["agregador"]
    assert agg["serie"]["datas"][-1] == output["referencia"]
    latest = agg["serie"]["2t"]["ajustado"]["lula"][-1]
    assert latest is not None and 30 < latest < 60


def test_moving_average_excludes_polls_outside_seven_days(engine):
    polls = [
        {
            "instituto": "A",
            "campo": {"fim": "2026-05-01"},
            "divulgacao": "2026-05-02",
            "turnos": {"2t": {"publicado": {"lula": 40.0}, "cenarios": {}}},
        },
        {
            "instituto": "B",
            "campo": {"fim": "2026-06-01"},
            "divulgacao": "2026-06-01",
            "turnos": {"2t": {"publicado": {"lula": 50.0}, "cenarios": {}}},
        },
    ]
    value = engine.kernel_average(polls, "2t", "publicado", "lula", date(2026, 6, 1))
    assert value == 50


def test_poll_files_have_required_fields():
    required = {"instituto", "campo", "n", "renda", "publicado", "cruzamentos", "fonte"}
    for path in POLLS.glob("*.json"):
        poll = json.loads(path.read_text())
        if poll.get("ignorar"):
            assert poll.get("motivo"), path.name
            continue
        missing = required - set(poll)
        assert not missing, (path.name, missing)
        bands = poll["renda"]["faixas"]
        assert bands[-1]["max"] is None, path.name
        for turno, table in poll["cruzamentos"].items():
            assert len(table["linhas"]) == len(bands), (path.name, turno)
            for row in table["linhas"]:
                assert len(row) == len(table["opcoes"]), (path.name, turno)


def test_quaest_september_full_source_and_current_wave(output):
    """A íntegra confirma 2T e perfil, acrescentando 1T sem reutilizar a onda anterior."""
    raw = json.loads((POLLS / "quaest_2026-09-13.json").read_text())
    assert set(raw["cruzamentos"]) == set(raw["publicado"]) == {"1t", "2t"}
    assert raw["cruzamentos"]["2t"]["linhas"] == [
        [51, 32, 12, 5],
        [36, 46, 13, 5],
        [34, 47, 14, 5],
    ]
    assert raw["renda"]["amostra_pct"] == [31, 42, 27]
    assert raw["registro_tse"] == "BR-03607/2026"
    poll = next(p for p in output["pesquisas"] if p["id"] == raw["id"])
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    assert poll["fonte"]["tipo"] == "relatorio"
    assert poll["fonte"]["pdf"].endswith("2026-09-14/relatorio.pdf")
    result = poll["turnos"]["2t"]
    assert result["residuo_max"] == pytest.approx(0.11)
    adjusted = result["cenarios"][SCENARIO]["ajustado"]
    assert adjusted["lula"] == pytest.approx(40.657, abs=0.001)
    assert adjusted["flavio"] == pytest.approx(41.399, abs=0.001)
    assert sum(adjusted.values()) == pytest.approx(100.0)


def test_full_source_labels_reach_the_published_card():
    from bs4 import BeautifulSoup

    html = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    card = html.find(id="pesquisa-quaest_2026-09-13")
    text = card.get_text(" ", strip=True)
    assert "Relatório completo conferido." in text
    assert "Fonte parcial" not in text
    assert "COTA REGISTRADA" not in text
    assert "Relatório completo (205 páginas)" in text
    assert "AMOSTRA DO INSTITUTO" in text


def test_mda_september_profile_excludes_income_nonresponse(output):
    raw = json.loads((POLLS / "mda_2026-09-13.json").read_text())
    assert raw["renda"]["amostra_pct"] == [43.8, 33.8, 21.0]
    assert sum(raw["renda"]["amostra_pct"]) == pytest.approx(98.6)
    assert raw["publicado"]["1t"]["outros"] == pytest.approx(15.6)
    assert raw["registro_tse"] == "BR-06902/2026"
    poll = next(p for p in output["pesquisas"] if p["id"] == raw["id"])
    assert poll["renda"]["amostra_pct"] == pytest.approx([44.422, 34.280, 21.298])
    assert poll["desvio_ate_primeira_faixa"] == pytest.approx(9.235, abs=0.001)
    assert poll["fonte"]["paginas"]["perfil_renda"] == 40


def test_mda_september_anchored_results_and_rounding(output):
    poll = next(p for p in output["pesquisas"] if p["id"] == "mda_2026-09-13")
    assert "1t" not in poll["turnos"]
    assert poll["selecao_1t"]["status"] == "excluido_com_marcal"
    for turno, expected in [("1t", [39.449, 31.529]), ("2t", [46.214, 41.221])]:
        result = (poll["turnos_arquivados"] if turno == "1t" else poll["turnos"])[turno]
        adjusted = result["cenarios"][SCENARIO]["ajustado"]
        assert [adjusted["lula"], adjusted["flavio"]] == pytest.approx(expected)
        assert result["residuo_max"] < 0.5
    raw = json.loads((POLLS / "mda_2026-09-13.json").read_text())
    assert [sum(r) for r in raw["cruzamentos"]["1t"]["linhas"]] == [99, 100, 101]
    assert [sum(r) for r in raw["cruzamentos"]["2t"]["linhas"]] == [101, 101, 100]


def test_mda_september_reading_has_independent_sex_check():
    audit = json.loads((ROOT / "docs/assets/mda_150926_renda.json").read_text())
    assert audit["provas"]["1t"]["recomposto_sexo_lula_flavio"] == pytest.approx(
        [40.62, 30.284]
    )
    assert audit["provas"]["2t"]["recomposto_sexo_lula_flavio"] == pytest.approx(
        [47.192, 39.76]
    )
    assert audit["perfil_renda_incluindo_nsr"] == [43.8, 33.8, 21.0, 1.4]
    assert (
        audit["sha256"]
        == "ce1a1f63a709bcabdbf7fd18a2d0058f7ee9849744294c9e22d9286a5e60e4bc"
    )


def test_latest_wave_mean_uses_new_mda_wave(output):
    # Independent reconstruction ensures August was replaced in the per-institute mean.
    polls = [p for p in output["pesquisas"] if "2t" in p["turnos"]]
    latest = {}
    for p in sorted(polls, key=lambda p: p["campo"]["fim"]):
        latest[p["instituto"]] = p
    assert latest["MDA"]["id"] == "mda_2026-10-02"
    assert latest["Gerp"]["id"] == "gerp_2026-10-02"
    mean = sum(
        p["turnos"]["2t"]["cenarios"][SCENARIO]["ajustado"]["lula"]
        for p in latest.values()
    ) / len(latest)
    assert output["agregador"]["ultimo"]["2t"]["media_simples"]["ajustado"][
        "lula"
    ] == round(mean, 2)


def test_new_gerp_wave_replaces_september_wave_in_window(output):
    poll = next(p for p in output["pesquisas"] if p["id"] == "gerp_2026-10-02")
    assert poll["registro_tse"] == "BR-00509/2026"
    assert poll["turnos"]["1t"]["publicado"]["flavio"] == 43
    assert poll["turnos"]["2t"]["publicado"]["lula"] == 44
    assert poll["turnos"]["1t"]["residuo_max"] < 0.5
    assert poll["turnos"]["2t"]["residuo_max"] < 0.5
    for turno in ("1t", "2t"):
        ondas = output["agregador"]["ultimo"][turno]["cobertura_movel"]["ondas"]
        assert "gerp_2026-10-02" in ondas
        assert "gerp_2026-09-28" not in ondas


def test_palver_wave6_replaces_wave5_in_window(output):
    poll = next(p for p in output["pesquisas"] if p["id"] == "palver_2026-10-03")
    raw = json.loads((POLLS / "palver_2026-10-03.json").read_text())
    assert poll["registro_tse"] == "BR-00198/2026"
    assert raw["publicado_pdf"] == {
        "1t": {"lula": 43, "flavio": 47},
        "2t": {"lula": 44, "flavio": 49},
    }
    assert raw["renda"]["amostra_pct"] == pytest.approx(
        [42.12294136, 39.56309619, 18.31396245], abs=1e-6
    )
    for turno in ("1t", "2t"):
        assert poll["turnos"][turno]["residuo_max"] < 1e-6
        pdf = raw["recomposicao"][turno]["pdf_inteiros_renda"]["residuo_vs_pdf_pp"]
        assert max(abs(v) for v in pdf.values()) < 1.5
        ondas = output["agregador"]["ultimo"][turno]["cobertura_movel"]["ondas"]
        assert "palver_2026-10-03" in ondas
        assert "palver_2026-09-27" not in ondas
    ajustado = poll["turnos"]["2t"]["cenarios"][SCENARIO]["ajustado"]
    assert ajustado["flavio"] == pytest.approx(49.36, abs=0.01)
    assert ajustado["lula"] == pytest.approx(44.44, abs=0.01)


def test_datafolha_eve_wave_from_g1_panel_replaces_october_1(output):
    raw = json.loads((POLLS / "datafolha_2026-10-03.json").read_text())
    assert raw["registro_tse"] == "BR-01708/2026"
    assert raw["n"] == 4006
    assert raw["campo"] == {"inicio": "2026-10-02", "fim": "2026-10-03"}
    assert raw["fonte"]["tipo"] == "painel_contratante"
    assert raw["renda"]["perfil_tipo"] == "hipotese_onda_anterior"
    previous = json.loads((POLLS / "datafolha_2026-10-01.json").read_text())
    assert raw["renda"]["bases"] == previous["renda"]["bases"]
    archive = json.loads(
        (ROOT / "data/originals/datafolha_102026_03/fonte.json").read_text()
    )
    for item in [*archive["api"], *archive["materias"]]:
        payload = (ROOT / item["arquivo"]).read_bytes()
        assert len(payload) == item["bytes"]
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]
    assert archive["relatorio_pdf"] is None
    assert raw["fonte"]["sha256"] == archive["api"][0]["sha256"]
    assert raw["publicado"]["1t"]["lula"] == 42
    assert raw["publicado"]["1t"]["flavio"] == 40
    assert raw["publicado"]["2t"] == {
        "lula": 47,
        "flavio": 46,
        "branco_nulo": 6,
        "indecisos": 2,
    }
    assert raw["cruzamentos"]["2t"]["linhas"] == [
        [55, 37, 6, 2],
        [38, 55, 6, 1],
        [39, 56, 5, 1],
    ]
    for turno in ("1t", "2t"):
        for dim in ("renda", "sexo"):
            assert raw["controles"][turno][dim]["residuo_max_abs"] <= 1.5
    poll = next(p for p in output["pesquisas"] if p["id"] == "datafolha_2026-10-03")
    assert poll["renda"]["perfil_tipo"] == "hipotese_onda_anterior"
    for turno in ("1t", "2t"):
        assert poll["turnos"][turno]["residuo_max"] < 1.5
        ondas = output["agregador"]["ultimo"][turno]["cobertura_movel"]["ondas"]
        assert "datafolha_2026-10-03" in ondas
        assert "datafolha_2026-10-01" not in ondas
    ajustado = poll["turnos"]["2t"]["cenarios"][SCENARIO]["ajustado"]
    assert ajustado["flavio"] == pytest.approx(48.81, abs=0.01)
    assert ajustado["lula"] == pytest.approx(44.56, abs=0.01)


def test_quaest_eve_wave_from_g1_panel_replaces_september_27(output):
    raw = json.loads((POLLS / "quaest_2026-10-03.json").read_text())
    assert raw["registro_tse"] == "BR-02197/2026"
    assert raw["n"] == 3702
    assert raw["campo"] == {"inicio": "2026-10-02", "fim": "2026-10-03"}
    assert raw["fonte"]["tipo"] == "painel_contratante"
    assert raw["renda"]["perfil_tipo"] == "hipotese_onda_anterior"
    previous = json.loads((POLLS / "quaest_2026-09-27.json").read_text())
    assert (
        raw["renda"]["amostra_pct"]
        == previous["renda"]["amostra_pct"]
        == [
            31,
            42,
            27,
        ]
    )
    archive = json.loads(
        (ROOT / "data/originals/quaest_102026_03/fonte.json").read_text()
    )
    for item in [archive["painel"], *archive["api"], *archive["materias"]]:
        payload = (ROOT / item["arquivo"]).read_bytes()
        assert len(payload) == item["bytes"]
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]
    for item in archive["materias"]:
        text = (ROOT / item["texto"]).read_bytes()
        assert hashlib.sha256(text).hexdigest() == item["texto_sha256"]
        assert "BR-02197/2026" in text.decode() and "3.702" in text.decode()
    assert archive["relatorio_pdf"] is None
    assert all(a["ultima_data_serie"] == "2026-10-03" for a in archive["api"])
    assert raw["fonte"]["sha256"] == archive["api"][0]["sha256"]
    assert "sem_cruzamento" not in raw
    assert raw["publicado"]["1t"]["lula"] == 40
    assert raw["publicado"]["1t"]["flavio"] == 38
    assert sum(raw["publicado"]["1t"].values()) == 100
    assert raw["publicado_validos"]["1t"]["lula"] == 46
    assert raw["publicado_validos"]["1t"]["flavio"] == 45
    assert raw["publicado"]["2t"] == {
        "lula": 42,
        "flavio": 44,
        "indecisos": 1,
        "branco_nulo": 13,
    }
    lines_1t = raw["cruzamentos"]["1t"]["linhas"]
    opts = raw["cruzamentos"]["1t"]["opcoes"]
    assert [[r[opts.index(k)] for k in ("lula", "flavio")] for r in lines_1t] == [
        [52, 28],
        [35, 41],
        [34, 45],
    ]
    assert raw["cruzamentos"]["2t"]["linhas"] == [
        [54, 33, 1, 12],
        [37, 47, 2, 14],
        [36, 53, 0, 11],
    ]
    for turno in ("1t", "2t"):
        for dim in ("renda", "sexo"):
            assert raw["controles"][turno][dim]["residuo_max_abs"] < 1.0
    poll = next(p for p in output["pesquisas"] if p["id"] == "quaest_2026-10-03")
    assert poll["renda"]["perfil_tipo"] == "hipotese_onda_anterior"
    for turno in ("1t", "2t"):
        assert poll["turnos"][turno]["residuo_max"] < 0.5
        ondas = output["agregador"]["ultimo"][turno]["cobertura_movel"]["ondas"]
        assert "quaest_2026-10-03" in ondas
        assert "quaest_2026-09-27" not in ondas
    first = poll["turnos"]["1t"]["cenarios"][SCENARIO]["ajustado"]
    assert first["lula"] == pytest.approx(40.73, abs=0.01)
    assert first["flavio"] == pytest.approx(37.40, abs=0.01)
    second = poll["turnos"]["2t"]["cenarios"][SCENARIO]["ajustado"]
    assert second["flavio"] == pytest.approx(43.33, abs=0.01)
    assert second["lula"] == pytest.approx(42.73, abs=0.01)


def test_futura_eve_wave_is_archived_and_enters_unweighted(output):
    raw = json.loads((POLLS / "futura_2026-10-03.json").read_text())
    assert raw["registro_tse"] == "BR-02431/2026"
    assert raw["n"] == 2000
    assert raw["campo"] == {"inicio": "2026-10-02", "fim": "2026-10-03"}
    assert raw["divulgacao"] == "2026-10-03"
    archive = json.loads(
        (ROOT / "data/originals/futura_102026_03/fonte.json").read_text()
    )
    payload = (ROOT / archive["arquivo"]).read_bytes()
    assert len(payload) == archive["bytes"] == raw["fonte"]["bytes"] == 1950280
    assert hashlib.sha256(payload).hexdigest() == archive["sha256"]
    assert archive["sha256"] == raw["fonte"]["sha256"]
    assert archive["sha256"].startswith("b6d58bcd9282fff8")
    manifest = json.loads(
        (ROOT / "data/originals/futura_102026_03/manifesto.json").read_text()
    )
    for item in manifest["arquivos"] + archive["materias"] + archive["site_instituto"]:
        blob = (ROOT / item["arquivo"]).read_bytes()
        assert len(blob) == item["bytes"]
        assert hashlib.sha256(blob).hexdigest() == item["sha256"]
    text = (ROOT / "data/originals/futura_102026_03/relatorio.txt").read_text()
    assert "BR-02431/2026" in text and "2000 entrevistas" in text
    assert "02/out - 03/out de 2026" in text
    # Renda só aparece como perfil; nenhuma página tem cruzamento.
    assert text.count("Sem cruzamento") == 6
    assert raw["ignorar"] and raw["cruzamentos"] == {}
    assert raw["renda"]["amostra_pct"] == [26.3, 22.2, 24.4, 9.1, 5.7]
    assert raw["renda"]["nao_declarada_pct"] == 12.4
    first = raw["publicado"]["1t"]
    assert (first["flavio"], first["lula"]) == (42.5, 40.5)
    assert sum(first.values()) == pytest.approx(100)
    assert "avalanche" not in first
    assert raw["publicado"]["2t"] == {
        "flavio": 48.0,
        "lula": 45.1,
        "branco_nulo": 5.7,
        "indecisos": 1.2,
    }
    assert sum(raw["publicado_validos"]["1t"].values()) == pytest.approx(100)
    skipped = {p["id"] for p in output["nao_reponderaveis"]}
    assert {"futura_2026-10-03", "futura_2026-09-29"} <= skipped
    assert "futura_2026-10-03" not in {p["id"] for p in output["pesquisas"]}
