import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/pesquisas/estaduais/mg/2026-08/derivados/auditoria.json"
MUNICIPAL = ROOT / "data/pesquisas/estaduais/mg/2026-08/derivados/municipios.csv"
PUBLIC = ROOT / "docs/assets/mg_082026_data.json"
GEO = ROOT / "docs/assets/mg_082026_municipios.geojson"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_mg_outputs_cover_the_complete_state():
    data = load(DATA)
    geo = load(GEO)
    assert data["eleitorado_tse_2026"]["eleitores_2026"] == 16_379_550
    assert len(data["regioes"]) == 13
    assert len(geo["features"]) == 853
    assert len({feature["properties"]["codigo_ibge"] for feature in geo["features"]}) == 853
    assert sum(region["eleitores_2026"] for region in data["regioes"]) == 16_379_550
    assert MUNICIPAL.exists() and PUBLIC.exists()


def test_mg_historical_flip_counts_reproduce_the_received_map():
    geo = load(GEO)
    counts = Counter(feature["properties"]["pres_virada"] for feature in geo["features"])
    assert counts == {
        "Direita nas duas": 285,
        "Esquerda nas duas": 404,
        "Direita→esquerda": 160,
        "Esquerda→direita": 4,
    }


def test_mg_poll_margins_and_recomposition_are_audited():
    data = load(DATA)
    polls = data["pesquisas"]
    assert sum(polls["quaest"]["governador_1t"]["valores"].values()) == 100
    assert sum(polls["real_time"]["governador_1t"]["valores"].values()) == 100
    for values in polls["quaest"]["segundos_turnos"]["cenarios"].values():
        assert sum(values) == 100
    for values in polls["real_time"]["segundos_turnos"]["cenarios"].values():
        assert sum(values) == 100
    assert polls["validacao_quaest"]["governador_1t_sexo"]["max_erro_arredondamento_pp"] <= 0.52
    assert polls["validacao_quaest"]["governador_1t_renda"]["max_erro_arredondamento_pp"] == 1.11


def test_mg_top_twenty_are_unique_and_formula_is_public():
    data = load(DATA)
    cities = data["top_20_pivotais"]
    assert len(cities) == 20
    assert len({city["codigo_ibge"] for city in cities}) == 20
    assert cities[0]["municipio"] == "Belo Horizonte"
    assert cities[0]["indice_pivotal"] == 100
    assert "eleitorado" in data["meta"]["indice_pivotal"]


def test_mg_nikolas_vote_is_municipally_reproduced():
    data = load(DATA)
    geo = load(GEO)
    election = data["eleicoes"]["2022_1_deputado federal"]
    nikolas = election["candidatos"][0]
    assert nikolas["nome"] == "Nikolas Ferreira"
    assert nikolas["votos"] == 1_492_047
    assert round(nikolas["votos"] / election["candidatos"][1]["votos"], 2) == 6.24
    assert sum(feature["properties"]["nikolas_2022_votos"] for feature in geo["features"]) == nikolas["votos"]
    bh = next(region for region in data["regioes"] if region["regiao_intermediaria"] == "Belo Horizonte")
    assert bh["nikolas_2022_votos"] == 649_235


def test_mg_public_copy_avoids_em_dash():
    for path in (
        ROOT / "docs/mg_082026.html",
        ROOT / "docs/assets/mg_082026.js",
        ROOT / "docs/assets/mg_082026.css",
    ):
        assert "—" not in path.read_text(encoding="utf-8")
