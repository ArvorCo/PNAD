"""Onde está o voto da terceira via, cidade por cidade (scripts/apuracao_2026/terceira_via*.py).

As contas puras rodam sobre fixtures pequenas, sem o banco da apuração. A conferência
nacional usa os totais do arquivo nacional de presidente do TSE (499.248 de 499.248
seções) e as linhas da Nexus, os mesmos de ``test_apuracao_2026_estrategia.py``. O
último bloco lê ``analysis/apuracao_2026/dados/terceira_via.json``, gerado por
``scripts/apuracao-2026-terceira-via.py``, e confere as invariantes do arquivo.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
from apuracao_2026 import estrategia as E
from apuracao_2026 import pagina_texto_reguas as PR
from apuracao_2026 import pagina_texto_terceira_via as PT
from apuracao_2026 import terceira_via as T
from apuracao_2026 import terceira_via_agregados as A
from apuracao_2026 import terceira_via_leitura as L
from apuracao_2026 import terceira_via_regua as RU
from apuracao_2026 import terceira_via_reguas as RG
from apuracao_2026 import terceira_via_secoes as S
from apuracao_2026 import terceira_via_texto as X

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "analysis/apuracao_2026/dados/terceira_via.json"
TRAVESSAO = chr(0x2014)

NEXUS = {
    "Cury": {"Lula": 30, "Flávio": 44, "Branco/nulo": 23, "Indecisos": 2},
    "Caiado": {"Lula": 36, "Flávio": 30, "Branco/nulo": 26, "Indecisos": 7},
    "Renan": {"Lula": 8, "Flávio": 56, "Branco/nulo": 37, "Indecisos": 0},
    "Zema": {"Lula": 13, "Flávio": 59, "Branco/nulo": 29, "Indecisos": 0},
    "Samara": {"Lula": 58, "Flávio": 6, "Branco/nulo": 36, "Indecisos": 0},
}
LINHAS = {k: E.normalizar_linha(v) for k, v in NEXUS.items()}
LINHA_POR_NUMERO = {
    70: "Cury",
    14: "Renan",
    55: "Caiado",
    30: "Zema",
    80: "Samara",
    16: "Samara",
    27: "Zema",
    21: "Samara",
    35: "Zema",
    29: "Samara",
}
NACIONAL = {
    22: 56_104_503,
    13: 53_879_538,
    70: 3_448_569,
    14: 2_675_887,
    55: 2_605_148,
    30: 326_488,
    80: 122_911,
    16: 43_103,
    27: 40_043,
    21: 22_693,
    35: 16_881,
    29: 15_024,
}


# ---------------------------------------------------------------- contas puras


@pytest.mark.parametrize(
    ("margem", "classe"),
    [
        (10.0, "venceu_folga"),
        (35.4, "venceu_folga"),
        (9.99, "venceu_apertado"),
        (0.01, "venceu_apertado"),
        (0.0, "perdeu_apertado"),
        (-9.99, "perdeu_apertado"),
        (-10.0, "perdeu_folga"),
    ],
)
def test_classe_de_margem(margem, classe):
    assert T.classe_margem(margem) == classe


def test_grupos_por_numero():
    assert [T.grupo(n) for n in (14, 30, 70, 55, 80, 29)] == [
        "renan",
        "zema",
        "cury",
        "caiado",
        "outros",
        "outros",
    ]


def test_destinos_ignora_finalistas_e_reparte_toda_a_terceira_via():
    votos = {22: 1000, 13: 900, 14: 101, 55: 99}
    d = T.destinos(votos, LINHA_POR_NUMERO, LINHAS)
    assert math.isclose(d["para_flavio"], 56 + 30)
    assert math.isclose(d["para_lula"], 8 + 36)
    assert math.isclose(d["para_flavio"] + d["para_lula"] + d["fora"], 200)
    assert math.isclose(d["saldo"], d["para_flavio"] - d["para_lula"])


def test_destinos_nacional_bate_com_o_capitulo_13():
    """Saldo da matriz Nexus sobre os votos nacionais: 3.895.146 − 2.224.965."""
    d = T.destinos(NACIONAL, LINHA_POR_NUMERO, LINHAS)
    assert round(d["para_flavio"]) == 4_041_993
    assert round(d["para_lula"]) == 2_371_813
    assert round(d["saldo"]) == 3_895_146 - 2_224_965


def test_percentis_empates_ausentes_e_extremos():
    p = T.percentis([3.0, None, 1.0, 3.0, 2.0])
    assert p[2] == 0.0
    assert p[1] == 0.5
    assert p[0] == p[3] == pytest.approx((2 + 3) / 2 / 3)
    assert p[4] == pytest.approx(1 / 3)
    assert T.percentis([None, None]) == [0.5, 0.5]
    assert T.percentis([7.0]) == [0.5]


def test_fator_pesos_e_so_volume():
    pos = {"vao_local": 1.0, "matriz": 0.0, "ambiente_2022": 0.5, "margem": 0.5}
    assert T.fator(pos, {}) == 1.0
    assert T.fator(pos, {"vao_local": 1.0}) == 1.0
    esperado = 0.35 * 1.0 + 0.25 * 0.0 + 0.25 * 0.5 + 0.15 * 0.5
    assert T.fator(pos, T.PESOS) == pytest.approx(esperado)
    assert sum(T.PESOS.values()) == pytest.approx(1.0)


def test_vao_local_e_teto():
    assert T.vao_local({"A": 120, "B": 90}, 100) == ("A", 20)
    assert T.vao_local({}, 100) == (None, -100)
    assert T.teto(500, 20) == 520
    assert T.teto(500, -300) == 500


def test_indice_cem_quando_rende_como_flavio():
    assert T.indice(30, 100, 300, 1000, 50, 100, 500, 1000) == pytest.approx(100.0)
    assert T.indice(60, 100, 300, 1000, 50, 100, 500, 1000) == pytest.approx(200.0)
    assert T.indice(10, 100, 0, 1000, 50, 100, 500, 1000) is None


def test_regressao_e_minimos_quadrados_recuperam_a_reta():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2 * x - 1 for x in xs]
    reg = T.regressao_ponderada(xs, ys, [1, 2, 1, 3, 1])
    assert reg["inclinacao"] == pytest.approx(2.0)
    assert reg["intercepto"] == pytest.approx(-1.0)
    assert reg["correlacao"] == pytest.approx(1.0)
    linhas = [(1.0, x, float(i % 2)) for i, x in enumerate(xs * 2)]
    y2 = [1 + 2 * x + 3 * dd for (_, x, dd) in linhas]
    coef = T.minimos_quadrados(linhas, y2, [1.0] * len(linhas))
    assert coef == pytest.approx([1.0, 2.0, 3.0])
    assert T.minimos_quadrados([(1.0, 1.0), (1.0, 1.0)], [1.0, 2.0], [1, 1]) is None


def test_taxa_de_nulo_e_conversao():
    assert T.taxa_nulo(100, 125, 1000) == pytest.approx(0.025)
    assert T.taxa_nulo(100, 125, 0) is None
    c = T.conversao(7_111_293, 3_072_523, 9_864_826)
    assert c["saldo"] == pytest.approx((7_111_293 - 3_072_523) / 9_864_826)
    assert T.conversao(1, 1, 0)["saldo"] is None


def test_brancos_nulos_pct():
    assert T.brancos_nulos_pct(10, 30, 1000) == pytest.approx(4.0)
    assert T.brancos_nulos_pct(0, 0, 0) is None


# ---------------------------------------------------------------- montagem


def _municipio(cd, uf, regiao, estoque, margem, vao, b22, saldo, **extra):
    m = {
        "cd": cd,
        "ibge": f"9{cd}",
        "uf": uf,
        "nome": f"CIDADE {cd}",
        "regiao": regiao,
        "capital": extra.pop("capital", False),
        "eleitores": 10 * estoque,
        "comparecimento": 8 * estoque,
        "validos": 7 * estoque,
        "flavio": 3 * estoque,
        "lula": 3 * estoque,
        "renan": estoque // 2,
        "zema": 0,
        "cury": estoque - estoque // 2,
        "caiado": 0,
        "outros": 0,
        "estoque": estoque,
        "estoque_pct": 100 / 7,
        "margem_pp": margem,
        "classe": T.classe_margem(margem),
        "para_flavio": saldo + 10,
        "para_lula": 10,
        "fora": estoque - saldo - 20,
        "saldo": saldo,
        "saldo_df": saldo + 5,
        "saldo_por_voto": saldo / estoque,
        "b22_2t_pct": b22,
        "local_nomes": [
            {"nome": "GOV", "cargo": "governador", "votos": 0, "indice": 120.0}
        ],
        "local_lider": "GOV",
        "vao_votos": vao,
        "vao_votos_estrito": vao,
        "vao_pp": 100 * vao / (8 * estoque),
        "teto": T.teto(estoque, vao),
    }
    m.update(extra)
    return m


@pytest.fixture
def brasil():
    return [
        _municipio("00001", "SP", "Sudeste", 1000, 15.0, 300, 60.0, 200, capital=True),
        _municipio("00002", "SP", "Sudeste", 800, -5.0, -50, 45.0, 150),
        _municipio("00003", "BA", "Nordeste", 600, -30.0, 900, 25.0, 100, capital=True),
        _municipio("00004", "PR", "Sul", 400, 40.0, 10, 75.0, 90),
        _municipio("00005", "GO", "Centro-Oeste", 300, 20.0, -20, 65.0, 5),
        _municipio("00006", "AM", "Norte", 200, 8.0, 40, 55.0, 40),
    ]


def test_prioridade_ordem_e_sensibilidades(brasil):
    A.aplicar_prioridade(brasil)
    assert sorted(m["posicao"] for m in brasil) == list(range(1, 7))
    for m in brasil:
        assert 0.0 <= m["fator"] <= 1.0
        assert m["prioridade_volume"] == m["estoque"]
        assert m["prioridade"] == pytest.approx(m["estoque"] * m["fator"])
    P = A.prioridade(brasil, 2_224_965)
    assert [x["posicao"] for x in P["top"]] == list(range(1, 7))
    assert P["soma_top"]["estoque"] == sum(m["estoque"] for m in brasil)
    assert P["soma_top"]["saldo"] == sum(m["saldo"] for m in brasil)
    volume = next(s for s in P["sensibilidade"] if s["nome"] == "volume")
    assert volume["em_comum_com_central"] == 6
    assert volume["primeiros"][0] == {"nome": "CIDADE 00001", "uf": "SP"}
    vao = next(s for s in P["sensibilidade"] if s["nome"] == "vao_local")
    assert [f"{x['nome']} ({x['uf']})" for x in vao["primeiros"][:2]] == [
        "CIDADE 00001 (SP)",
        "CIDADE 00003 (BA)",
    ]


def test_agregados_classes_somam_o_estoque(brasil):
    ag = A.agregados(brasil, [])
    nac = ag["brasil"]
    assert sum(c["estoque"] for c in nac["por_classe"].values()) == nac["estoque"]
    assert sum(
        c["estoque_parcela"] for c in nac["por_classe"].values()
    ) == pytest.approx(100, abs=0.05)
    assert nac["onde_flavio_venceu"] == 1000 + 400 + 300 + 200
    assert nac["vao_positivo"] == 300 + 900 + 10 + 40
    assert nac["teto"] == nac["estoque"] + nac["vao_positivo"]
    assert ag["capitais"]["estoque"] == 1600
    assert ag["regioes"]["Nordeste"]["lideres"][0] == {
        "nome": "GOV",
        "municipios": 1,
        "vao_votos": 900,
    }


def test_teto_por_uf(brasil):
    A.aplicar_prioridade(brasil)
    te = A.teto(brasil)
    sp = te["ufs"]["SP"]
    assert sp["estoque"] == 1800 and sp["vao_positivo"] == 300
    assert sp["teto"] == 2100
    assert [x["cd"] for x in sp["top"]] == ["00001", "00002"]


def test_contrario_e_riscos(brasil):
    A.aplicar_prioridade(brasil)
    ag = A.agregados(brasil, [])
    co = A.contrario(brasil, ag)
    assert co["nordeste_capitais"]["municipios"] == 1
    assert co["fortes_lula_folga"]["municipios"] == 1
    nulo = {"nacional": {"acrescimo": 1, "taxa": 0.1}, "risco_2026": {"votos": 7}}
    ri = A.riscos(brasil, ag, nulo)
    assert ri["lula_com_folga"]["estoque"] == 600
    assert ri["nulo"]["risco_2026_ufs_governador"] == 7


def _com_2022(brasil):
    for i, m in enumerate(brasil):
        gov = m["uf"] in ("SP", "BA")
        m.update(
            {
                "tv22": 100 + 10 * i,
                "tv22_pct": 5.0 + i,
                "ciro22_pct": 2.0,
                "tebet22_pct": 3.0 + i / 2,
                "comp22_1t": 1000,
                "comp22_2t": 1000,
                "bn22_1t": 40,
                "bn22_2t": 50 if gov else 35,
                "bn22_1t_pct": 4.0,
                "bn22_2t_pct": 5.0 if gov else 3.5,
                "delta_bn22_pp": 1.0 if gov else -0.5,
                "gov22_2t": gov,
                "gov26_2t": m["uf"] == "AM",
                "ganho_b22": 60,
                "ganho_l22": 20,
            }
        )
    return brasil


def test_nulo_2022_separa_o_2o_turno_de_governador(brasil):
    brasil = _com_2022(brasil)
    ag = A.agregados(brasil, [])
    api = {
        1: {"comparecimento": 6000, "brancos": 100, "nulos": 140},
        2: {"comparecimento": 6000, "brancos": 100, "nulos": 160},
    }
    N = A.nulo_2022(brasil, api, ag)
    assert N["nacional"]["acrescimo"] == 20
    assert N["com_2t_governador"]["ufs"] == ["BA", "SP"]
    assert N["com_2t_governador"]["delta_pp"] == pytest.approx(1.0)
    assert N["sem_2t_governador"]["delta_pp"] == pytest.approx(-0.5)
    assert N["modelo"]["c_governador"] == pytest.approx(1.5)
    assert N["risco_2026"]["ufs"] == ["AM"]
    assert N["risco_2026"]["votos"] == round(0.01 * ag["ufs"]["AM"]["comparecimento"])


def test_conversao_2022_por_classe(brasil):
    C = A.conversao_2022(_com_2022(brasil))
    assert C["brasil"]["saldo"] == pytest.approx(
        6 * 40 / sum(100 + 10 * i for i in range(6))
    )
    assert C["por_classe"]["perdeu_folga"]["municipios"] == 1


def test_direita_local_escolhe_governador_e_senado():
    fontes = {
        "gov": {
            "candidatos": {
                "1": {"uf": "MA", "nome_urna": "EDUARDO BRAIDE"},
                "2": {"uf": "SP", "nome_urna": "TARCÍSIO"},
            }
        },
        "governadores": {
            "vao_estadual": {
                "lista": [
                    {
                        "uf": "sp",
                        "finalista": "flavio",
                        "governador": "TARCISIO",
                        "partido": "REPUBLICANOS",
                        "campo": "direita",
                        "decisao": "eleito",
                        "comparacao": "mesmo bloco",
                        "pct_governador": 62.65,
                    },
                    {
                        "uf": "ma",
                        "finalista": "flavio",
                        "governador": "EDUARDO BRAIDE",
                        "partido": "PSD",
                        "campo": "centro",
                        "decisao": "eleito",
                        "comparacao": "sem apoio declarado",
                        "pct_governador": 54.02,
                    },
                    {
                        "uf": "pi",
                        "finalista": "lula",
                        "governador": "X",
                        "pct_governador": 70.0,
                    },
                ]
            }
        },
        "senado_x_flavio": {
            "carregadores": {
                "candidatos": [
                    {
                        "uf": "SP",
                        "sqcand": "9",
                        "nome": "DERRITE",
                        "partido": "PP",
                        "campo": "centro-direita",
                    }
                ]
            },
            "ufs": [
                {
                    "uf": "SP",
                    "melhor": {
                        "sqcand": "9",
                        "nome": "DERRITE",
                        "partido": "PP",
                        "campo": "centro-direita",
                        "eleito": True,
                    },
                },
                {
                    "uf": "PI",
                    "melhor": {
                        "sqcand": "8",
                        "nome": "CIRO NOGUEIRA",
                        "partido": "PP",
                        "campo": "centro-direita",
                        "eleito": False,
                    },
                },
            ],
        },
    }
    loc = S.direita_local(fontes)
    assert loc["SP"]["governador"]["sqcand"] == "2"
    assert [s["nome"] for s in loc["SP"]["senado"]] == ["DERRITE"]
    assert loc["MA"]["governador"]["comparacao"] == "sem apoio declarado"
    assert loc["PI"]["governador"] is None
    assert loc["PI"]["senado"][0]["eleito"] is False


def test_nulo_por_municipio():
    det = {
        1: {"aptos": 100, "comparecimento": 80, "brancos": 2, "nulos": 2},
        2: {"aptos": 100, "comparecimento": 80, "brancos": 3, "nulos": 3},
    }
    n = S._nulo_2022(det)
    assert n["bn22_1t_pct"] == pytest.approx(5.0)
    assert n["delta_bn22_pp"] == pytest.approx(2.5)
    assert S._nulo_2022({1: det[1]}) == {}


def test_regras_sem_travessao():
    mat = {"fonte_nexus": "Nexus, p. 79", "fonte_datafolha": "Datafolha, p. 7"}
    texto = json.dumps(X.regras(mat), ensure_ascii=False)
    assert TRAVESSAO not in texto
    assert "teto endereçável" in texto


# ---------------------------------------------------------------- arquivo gerado


@pytest.fixture(scope="module")
def tv():
    if not DADOS.exists():
        pytest.skip("terceira_via.json ainda não gerado")
    return json.loads(DADOS.read_text(encoding="utf-8"))


def test_arquivo_confere_com_o_nacional(tv):
    cf = tv["conferencia"]
    assert cf["soma_municipal_igual_nacional"]
    assert cf["detalhe_2022_igual_arquivo_nacional"]
    ag = tv["agregados"]
    assert (
        ag["brasil"]["estoque"] + ag["exterior"]["estoque"] == ag["total_com_exterior"]
    )
    assert (
        sum(c["estoque"] for c in ag["brasil"]["por_classe"].values())
        == ag["brasil"]["estoque"]
    )
    assert sum(r["estoque"] for r in ag["regioes"].values()) == ag["brasil"]["estoque"]


def test_arquivo_listas_e_colunas(tv):
    P = tv["prioridade"]
    assert len(P["top"]) == 100
    assert [x["posicao"] for x in P["top"]] == list(range(1, 101))
    assert all(len(v) <= 10 for v in P["por_uf"].values())
    assert all(0 <= s["em_comum_com_central"] <= 100 for s in P["sensibilidade"])
    M = tv["municipios"]
    assert len(M["linhas"]) == tv["agregados"]["brasil"]["municipios"]
    i_teto, i_est = M["colunas"].index("teto"), M["colunas"].index("estoque")
    assert all(linha[i_teto] >= linha[i_est] for linha in M["linhas"])
    assert DADOS.stat().st_size < 3_000_000


def test_textos_do_arquivo_sem_travessao(tv):
    memo = X.memorando(tv)
    assert TRAVESSAO not in memo
    assert "## 5. O risco do voto nulo, medido em 2022" in memo
    html = PT.bloco(tv, lambda nome: f"<figure>{nome}</figure>")
    assert TRAVESSAO not in html
    assert "<h3>Onde está o voto da terceira via, cidade por cidade</h3>" in html
    assert "<h3>O risco do voto nulo, medido em 2022</h3>" in html
    assert 'class="io"' in html and 'class="hyp"' in html
    for nome in (
        "terceira_via_mapa",
        "terceira_via_teto_uf",
        "terceira_via_prioridade",
        "nulo_2022_municipios",
    ):
        assert f"<figure>{nome}</figure>" in html


# ---------------------------------------------------------------- duas réguas


def _sintetico(
    ruido: float = 0.0, n_por_uf: int = 60, semente: int = 7
) -> tuple[list[dict], dict]:
    """Municípios em três UFs com inclinações conhecidas por classe e efeito fixo de UF."""
    rng = np.random.default_rng(semente)
    verdade_b = {
        "venceu_folga": 0.6,
        "venceu_apertado": 0.5,
        "perdeu_apertado": 0.4,
        "perdeu_folga": 0.3,
    }
    verdade_l = {
        "venceu_folga": 0.3,
        "venceu_apertado": 0.4,
        "perdeu_apertado": 0.45,
        "perdeu_folga": 0.5,
    }
    a_uf = {"AA": (0.02, 0.01), "BB": (-0.01, 0.0), "CC": (0.03, -0.02)}
    linhas = []
    for uf, (ab, al) in a_uf.items():
        for i in range(n_por_uf):
            classe = T.CLASSES[i % 4]
            V = float(rng.integers(2_000, 200_000))
            x_tv = rng.uniform(0.02, 0.2)
            x_bn = rng.uniform(0.02, 0.08)
            yb = ab + verdade_b[classe] * x_tv - 0.1 * x_bn + ruido * rng.normal()
            yl = al + verdade_l[classe] * x_tv + 0.05 * x_bn + ruido * rng.normal()
            linhas.append(
                {
                    "cd": f"{uf}{i:03d}",
                    "uf": uf,
                    "regiao": "Sudeste" if uf != "CC" else "Sul",
                    "classe": classe,
                    "comp22_1t": V,
                    "tv22": x_tv * V,
                    "bn22_1t": x_bn * V,
                    "ganho_b22": yb * V,
                    "ganho_l22": yl * V,
                    "estoque": int(x_tv * V),
                }
            )
    return linhas, {c: verdade_b[c] - verdade_l[c] for c in T.CLASSES}


def test_regua_recupera_inclinacoes_com_efeito_fixo():
    linhas, saldo = _sintetico()
    m = RU.modelo(linhas, "classe", T.CLASSES, n_boot=20)
    for c in T.CLASSES:
        g = m["grupos"][c]
        assert g["saldo"] == pytest.approx(saldo[c], abs=1e-9)
        assert g["saldo_ic95"][0] == pytest.approx(saldo[c], abs=1e-9)
        assert g["saldo"] == pytest.approx(g["bolsonaro"] - g["lula"], abs=1e-4)
    assert m["brancos_nulos"]["saldo"] == pytest.approx(-0.15, abs=1e-9)


def test_regua_com_ruido_intervalo_contem_o_ponto_e_e_reproduzivel():
    linhas, _ = _sintetico(ruido=0.01)
    a = RU.modelo(linhas, "classe", T.CLASSES, n_boot=80)
    b = RU.modelo(linhas, "classe", T.CLASSES, n_boot=80)
    for c in T.CLASSES:
        lo, hi = a["grupos"][c]["saldo_ic95"]
        assert lo <= a["grupos"][c]["saldo"] <= hi
        assert a["grupos"][c]["saldo_ic95"] == b["grupos"][c]["saldo_ic95"]
    unico = RU.modelo(linhas, None, [], n_boot=20)
    assert list(unico["grupos"]) == ["todos"]


def test_regua_sem_efeito_fixo_tem_constante():
    linhas, _ = _sintetico()
    sfe = RU.sem_efeito_fixo(linhas)
    assert set(sfe) == {"saldo_terceira_via", "saldo_brancos_nulos", "constante"}


def test_aplicar_e_total_ic():
    linhas, _ = _sintetico(ruido=0.01)
    classe = RU.modelo(linhas, "classe", T.CLASSES, n_boot=50)
    for m in linhas:
        m["regiao"] = "Sudeste"
    regiao = RU.modelo(linhas, "regiao", ["Sudeste"], n_boot=10)
    razao = {c: {"saldo": 0.5} for c in T.CLASSES}
    RU.aplicar(linhas, classe, regiao, razao)
    for m in linhas:
        assert m["saldo_urna"] == pytest.approx(
            m["estoque"] * classe["grupos"][m["classe"]]["saldo"]
        )
        assert m["saldo_razao"] == pytest.approx(0.5 * m["estoque"])
    lo, hi = RU.total_ic(linhas, classe)
    total = sum(m["saldo_urna"] for m in linhas)
    assert lo <= total + 1 and total - 1 <= hi


def test_decompor_motivo_piso_situacao():
    d = T.decompor(0.25, 0.18, -0.12, 0.05)
    assert d["composicao"] + d["nivel"] + d["classe"] == pytest.approx(d["total"])
    assert d["total"] == pytest.approx(0.37)
    assert T.motivo(d) == "classe"
    assert T.motivo(T.decompor(0.02, 0.18, 0.15, 0.05)) == "composicao"
    assert T.piso_teto(5, -3) == (-3, 5)
    assert [
        T.situacao(*x)
        for x in ((True, True), (True, False), (False, True), (False, False))
    ] == [
        "robusto",
        "so_pesquisa",
        "so_urna",
        "fora",
    ]


def _com_reguas(brasil):
    for m, urna in zip(brasil, (-0.05, 0.1, -0.2, 0.3, 0.25, 0.0), strict=True):
        m.update(
            {
                "pv_urna": urna,
                "saldo_urna": m["estoque"] * urna,
                "saldo_urna_regiao": m["estoque"] * 0.01,
                "saldo_razao": m["estoque"] * 0.4,
                "para_flavio_urna": m["estoque"] * 0.5,
                "para_lula_urna": m["estoque"] * (0.5 - urna),
                "direita_menor": 3,
            }
        )
    return brasil


def test_reguas_rankings_e_totais(brasil, monkeypatch):
    brasil = _com_reguas(brasil)
    monkeypatch.setattr(RG, "N_TOP", 3)
    nac = RG.preparar(brasil)
    assert nac["pv_urna"] == pytest.approx(
        sum(m["saldo_urna"] for m in brasil) / sum(m["estoque"] for m in brasil)
    )
    rk = RG.rankings(brasil)
    pesq = [x["cd"] for x in rk["top"]["pesquisa"]]
    urna = [x["cd"] for x in rk["top"]["urna"]]
    assert pesq == ["00001", "00002", "00003"]
    assert urna == ["00004", "00002", "00005"]
    assert rk["robustos"] == 1 and rk["so_pesquisa"] == 2 and rk["so_urna"] == 2
    assert {x["situacao"] for x in rk["divergentes"]} == {"so_pesquisa", "so_urna"}
    comb = rk["top"]["combinacao"]
    assert [x["piso"] for x in comb] == sorted((x["piso"] for x in comb), reverse=True)
    assert all(x["piso"] <= x["teto"] for x in comb)
    tot = RG.totais(brasil, [0, 1])
    assert sum(r["urna"] for r in tot["regioes"].values()) == pytest.approx(
        tot["brasil"]["urna"], abs=3
    )


def test_movimentos_pelas_duas_reguas(brasil):
    brasil = _com_reguas(brasil)
    RG.preparar(brasil)
    estrategia = {
        "movimentos": [
            {"id": "renan", "ordem": 1, "titulo": "Renan", "votos_esperados": 100},
            {
                "id": "sp_tarcisio",
                "ordem": 3,
                "titulo": "Tarcísio",
                "votos_esperados": 50,
            },
            {
                "id": "ne_interior",
                "ordem": 5,
                "titulo": "Nordeste",
                "votos_esperados": 40,
            },
        ]
    }
    mv = RG.movimentos(brasil, estrategia)
    renan = mv[0]
    assert renan["urna"] == round(sum(m["renan"] * m["pv_urna"] for m in brasil))
    assert mv[1]["urna"] is None and "governador" in mv[1]["nota"]
    assert mv[2]["urna"] == round(
        sum(m["saldo_urna"] for m in brasil if m["regiao"] == "Nordeste")
    )
    assert mv[2]["concordam"] is False


def test_retrovisao_procura_no_acervo(tmp_path, monkeypatch):
    pasta = tmp_path / "pesquisas_2022"
    (pasta / "casa_a").mkdir(parents=True)
    (pasta / "casa_a" / "README.md").write_text(
        "Última onda do 1º turno.", encoding="utf-8"
    )
    trans = tmp_path / "pesquisas_2022.json"
    trans.write_text(
        json.dumps(
            {
                "descricao": "Transcrição, teste",
                "pesquisas": [{"casa": "A", "totais": {}}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(L, "ROOT", tmp_path)
    monkeypatch.setattr(L, "PESQUISAS_2022", pasta)
    monkeypatch.setattr(L, "TRANSCRICAO_2022", trans)
    rv = L.retrovisao()
    assert rv["disponivel"] is False and rv["casas_no_acervo"] == 1
    (pasta / "casa_b").mkdir()
    (pasta / "casa_b" / "README.md").write_text(
        "Primeira onda do 2º turno, com migração.", encoding="utf-8"
    )
    rv = L.retrovisao()
    assert rv["disponivel"] is True and rv["achados"][0]["casa"] == "casa_b"


def test_arquivo_reguas(tv):
    R = tv["reguas"]
    m = R["modelos"]["classe"]["grupos"]
    for g in m.values():
        lo, hi = g["saldo_ic95"]
        assert lo <= g["saldo"] <= hi
    T_ = R["totais"]
    br = T_["brasil"]
    assert sum(c["urna"] for c in T_["classes"].values()) == pytest.approx(
        br["urna"], abs=4
    )
    assert br["urna_ic95"][0] <= br["urna"] <= br["urna_ic95"][1]
    assert br["nexus"] == tv["agregados"]["brasil"]["saldo"]
    rk = R["rankings"]
    assert rk["robustos"] + rk["so_pesquisa"] == 100
    assert len(rk["top"]["combinacao"]) == 100
    assert {mv["id"] for mv in R["movimentos"]} >= {
        "renan",
        "cury",
        "caiado_go",
        "direita_menor",
    }
    assert R["retrovisao"]["disponivel"] in (True, False)
    html = PR.bloco(tv, lambda nome: f"<figure>{nome}</figure>")
    assert TRAVESSAO not in html
    assert "<h3>Pesquisa contra urna: duas réguas para o mesmo estoque</h3>" in html
    assert (
        "<figure>conversao_2022_classes</figure>" in html
        and "<figure>reguas_divergencia_mapa</figure>" in html
    )
