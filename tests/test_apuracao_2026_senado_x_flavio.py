"""Senado contra Flávio: contas, regra declarada dos alinhados, índice e figuras.

Fixtures pequenas, montadas aqui; nenhum teste lê o banco da apuração.
"""

import json
import re

import pytest
from apuracao_2026 import pagina_fig_senado_flavio as FSF
from apuracao_2026 import pagina_texto_senado_flavio as TSF
from apuracao_2026 import senado_x_flavio as SXF
from apuracao_2026.dados import classificador
from apuracao_2026.pagina_comum import Dados
from apuracao_2026.pagina_figuras import FIGURAS

CAMPOS = classificador(
    {
        "partidos": {
            "PL": "direita",
            "REPUBLICANOS": "direita",
            "PP": "centro-direita",
            "UNIÃO": "centro-direita",
            "PSD": "centro",
            "PT": "esquerda",
        },
        "excecoes": {},
    }
)
CHICAO = "140002550780"


def _cand(sq, nome, partido, votos, eleito=False, sub_judice=False):
    return {
        "sqcand": sq,
        "nome": nome,
        "partido": partido,
        "federacao": None,
        "votos": votos,
        "eleito": eleito,
        "sub_judice": sub_judice,
    }


def _uf(cands, comparecimento):
    base = sum(c["votos"] for c in cands)
    return {
        "vv": base,
        "base": base,
        "comparecimento": comparecimento,
        "secoes": 10,
        "secoes_total": 10,
        "gerado_em": "2026-10-05T01:00:00.000Z",
        "candidatos": cands,
    }


def _senado():
    sp = [
        _cand("1", "ANA", "PL", 300, eleito=True),
        _cand("2", "BETO", "PP", 250, eleito=True),
        _cand("3", "CAIO", "PT", 350),
        _cand("4", "DINA", "PSD", 100),
    ]
    pa = [
        _cand(CHICAO, "CHICÃO", "UNIÃO", 400, eleito=True),
        _cand("5", "EDER", "PL", 380),
        _cand("6", "HELDER", "PSD", 420, eleito=True),
    ]
    mun = {}
    votos_sp = [
        {"1": 1500, "2": 1250, "3": 1750, "4": 500},
        {"1": 2400, "2": 1000, "3": 1200, "4": 400},
        {"1": 900, "2": 1500, "3": 2100, "4": 500},
        {"1": 60, "2": 50, "3": 70, "4": 20},
    ]
    for i, v in enumerate(votos_sp, start=1):
        mun[str(i)] = {
            "uf": "SP",
            "votos": v,
            "base_senado": sum(v.values()),
            "comparecimento": sum(v.values()) // 2,
            "completo": True,
        }
    for i in (5, 6):
        v = {CHICAO: 2000, "5": 1900, "6": 2100}
        mun[str(i)] = {
            "uf": "PA",
            "votos": v,
            "base_senado": 6000,
            "comparecimento": 3200,
            "completo": True,
        }
    return {
        "candidatos": {},
        "ufs": {"SP": _uf(sp, 520), "PA": _uf(pa, 650)},
        "municipios": mun,
    }


COLS = [
    "cd_tse",
    "ibge",
    "uf",
    "nome",
    "completo",
    "comparecimento",
    "flavio",
    "validos",
]


def _presidente():
    linhas = [
        ["1", "3500001", "SP", "ALFA", True, 6000, 2600, 5000],
        ["2", "3500002", "SP", "BETA", True, 6000, 2000, 5000],
        ["3", "3500003", "SP", "GAMA", True, 6000, 3000, 5000],
        ["4", "3500004", "SP", "DELTA", True, 100, 50, 90],
        ["5", "1500005", "PA", "EPSILON", True, 3200, 1200, 3000],
        ["6", "1500006", "PA", "ZETA", False, 3200, 1300, 3000],
    ]
    return {
        "ufs": [
            {"uf": "SP", "votos": {"flavio": 260}, "validos": 500, "comparecimento": 520, "eleitores": 700},
            {"uf": "PA", "votos": {"flavio": 250}, "validos": 600, "comparecimento": 650, "eleitores": 800},
            {"uf": "ZZ", "votos": {"flavio": 40}, "validos": 90, "comparecimento": 95, "eleitores": 200},
        ],
        "municipios": {"colunas": COLS, "linhas": linhas},
    }  # fmt: skip


EXCECAO = [{"uf": "MA", "nome": "Fufuca", "alinhado_lula": True}]


@pytest.fixture(scope="module")
def dados():
    col = {CHICAO: {"partidos": ["PSB", "PT", "UNIÃO"]}}
    return SXF.montar(_senado(), _presidente(), CAMPOS, col, EXCECAO)


# ------------------------------------------------------------------ blocos


def test_classificar_tira_alinhado_do_bloco():
    cl = {
        c["sqcand"]: c
        for c in SXF.classificar(_senado()["ufs"]["PA"]["candidatos"], CAMPOS)
    }
    assert cl[CHICAO]["campo"] == "centro-direita"
    assert not cl[CHICAO]["aliado"] and cl[CHICAO]["alinhado_lula"]
    assert cl["5"]["aliado"] and cl["5"]["pl"]
    assert not cl["6"]["aliado"]


def test_conferir_alinhados_acusa_lista_desatualizada():
    cands = [{"sqcand": "99", "uf": "XX", "nome": "NOVO ALIADO", "campo": "direita"}]
    with pytest.raises(ValueError, match="faltam"):
        SXF.conferir_alinhados(cands, {"99": {"partidos": ["PT"]}}, [])
    sem_tse = [
        {
            "sqcand": "100002542867",
            "uf": "MA",
            "nome": "FUFUCA",
            "campo": "centro-direita",
        }
    ]
    assert SXF.conferir_alinhados(sem_tse, {}, EXCECAO) == ["100002542867"]


def test_somas_por_uf(dados):
    sp = next(u for u in dados["ufs"] if u["uf"] == "SP")
    assert sp["flavio"]["pct"] == 52.0
    assert sp["pl"]["votos"] == 300 and sp["pl"]["pct"] == 30.0
    assert sp["pl"]["div_pp"] == -22.0
    assert sp["pl"]["votos_por_voto_flavio"] == round(300 / 260, 3)
    assert sp["aliados"]["votos"] == 550 and sp["aliados"]["div_pp"] == 3.0
    m = sp["melhor"]
    assert m["nome"] == "ANA" and m["vao_pp"] == -22.0
    assert m["vao_votantes_pp"] == round(100 * 300 / 520 - 100 * 260 / 520, 2)


def test_alinhado_fica_fora_da_soma(dados):
    pa = next(u for u in dados["ufs"] if u["uf"] == "PA")
    assert pa["aliados"]["votos"] == 380
    assert pa["aliados"]["n_candidatos"] == 1
    assert pa["melhor"]["nome"] == "EDER"


def test_nacional_sem_exterior(dados):
    n = dados["nacional"]
    assert n["flavio"]["votos"] == 510
    assert n["flavio"]["pct"] == round(100 * 510 / 1100, 2)
    assert n["pl"]["votos"] == 680
    assert n["pl"]["pct"] == round(100 * 680 / 2200, 2)
    assert n["pl"]["div_pp"] == round(100 * 680 / 2200 - 100 * 510 / 1100, 2)


# ------------------------------------------------------------------ índice


def test_indice_formula():
    assert SXF.indice(30, 30, 52, 52) == 100
    assert SXF.indice(45, 30, 52, 52) == pytest.approx(150)
    assert SXF.indice(30, 30, 26, 52) == pytest.approx(200)
    assert SXF.indice(30, 30, 0, 52) is None


def test_carregadores_listas_e_minimo(dados):
    C = {c["nome"]: c for c in dados["carregadores"]["candidatos"]}
    assert set(C) == {"ANA", "BETO"}
    ana = C["ANA"]
    assert ana["municipios"] == 4
    assert ana["elegiveis_lista"] == 3
    nomes_maiores = {x["nome"] for x in ana["maiores"]}
    nomes_menores = {x["nome"] for x in ana["menores"]}
    assert not nomes_maiores & nomes_menores
    assert "DELTA" not in nomes_maiores | nomes_menores
    assert [x["nome"] for x in ana["maiores"]] == ["BETA"]
    assert [x["nome"] for x in ana["menores"]] == ["GAMA"]
    assert ana["maiores"][0]["indice"] == round(100 * (48 / 30) / (40 / 52), 1)


def test_mapa_so_com_eleito_de_direita(dados):
    assert dados["mapa"]["ufs"] == ["SP"]
    P = dados["mapa"]["por_uf"]["SP"]
    assert [c["nome"] for c in P["candidatos"]] == ["ANA", "BETO"]
    assert len(P["linhas"]) == 4
    assert len(P["colunas"]) == len(P["linhas"][0])


# ------------------------------------------------------------------ figuras e texto


def _geo(dados):
    feats = []
    for i, linha in enumerate(dados["mapa"]["por_uf"]["SP"]["linhas"]):
        x, y = -50 + i, -22
        anel = [[x, y], [x + 0.9, y], [x + 0.9, y + 0.9], [x, y + 0.9], [x, y]]
        feats.append(
            {
                "properties": {"codarea": linha[0]},
                "geometry": {"type": "Polygon", "coordinates": [anel]},
            }
        )
    return {"features": feats}


def _tips(h: str) -> dict:
    m = re.search(
        r'<script type="application/json" class="tips">(.*?)</script>', h, re.DOTALL
    )
    return json.loads(m.group(1).replace("<\\/", "</"))


@pytest.mark.parametrize(
    "nome",
    ["senado_pl_x_flavio_uf", "senado_vao_candidatos", "senado_carregadores_mapa"],
)
def test_figuras_sobre_a_fixture(dados, monkeypatch, nome):
    monkeypatch.setattr(FSF, "_geo_municipal", lambda _uf: _geo(dados))
    h = FIGURAS[nome]({"senado_x_flavio": dados})
    assert h.startswith(f'<figure class="reveal fig-i" id="fig-{nome}"')
    assert h.count("<svg") == 1 and "—" not in h
    tips = _tips(h)
    linhas = tips.get("_rows", {}).get("linhas", [])
    for k in re.findall(r'data-k="([^"]+)"', h):
        assert (k in tips) or (k[1:].isdigit() and int(k[1:]) < len(linhas))
    tamanhos = [float(x) for x in re.findall(r'<text[^>]*font-size="([0-9.]+)"', h)]
    assert min(tamanhos, default=13) >= 13


def test_mapa_troca_cor_por_candidatura(dados, monkeypatch):
    monkeypatch.setattr(FSF, "_geo_municipal", lambda _uf: _geo(dados))
    h = FIGURAS["senado_carregadores_mapa"]({"senado_x_flavio": dados})
    assert 'data-alt="SP0"' in h and 'data-alt="SP1"' in h
    assert h.count("data-af=") == 4
    assert h.count('class="car-lista"') == 2 and h.count(" hidden>") == 1


def test_texto_do_capitulo(dados, monkeypatch, tmp_path):
    monkeypatch.setattr(FSF, "_geo_municipal", lambda _uf: _geo(dados))
    (tmp_path / "senado_x_flavio.json").write_text(json.dumps(dados), encoding="utf-8")
    h = TSF.capitulo(Dados(pasta=tmp_path))
    assert h.startswith(
        '<h3 id="senado-x-flavio">Os senadores que rendem mais que o presidenciável</h3>'
    )
    for nome in (
        "senado_pl_x_flavio_uf",
        "senado_vao_candidatos",
        "senado_carregadores_mapa",
    ):
        assert f'id="fig-{nome}"' in h
    assert h.index('id="fig-senado_pl_x_flavio_uf"') < h.index(
        "Somados, os nomes do PL"
    )
    assert "Não é transferência" in h and "Não é previsão" in h and "Dois votos" in h
    assert "achado contrário" in h
    assert "—" not in h


def test_texto_sem_json_vira_pendente(tmp_path):
    h = TSF.capitulo(Dados(pasta=tmp_path))
    assert "pendente" in h and "senado_x_flavio.json" in h
