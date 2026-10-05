"""Aritmética pura do confronto entre pesquisas, previsões e urna (1º turno de 2026)."""

import math

import pytest
import voto_util_modelo as VU
from apuracao_2026 import pesquisas as P
from apuracao_2026 import pesquisas_casa as C
from apuracao_2026 import pesquisas_estaduais as E
from apuracao_2026 import pesquisas_memo as M

URNA = {
    "flavio": 47.0,
    "lula": 45.0,
    "cury": 3.0,
    "renan_santos": 2.5,
    "caiado": 2.0,
    "zema": 0.3,
    "samara": 0.2,
}


# ---------------------------------------------------------------- válidos


def test_validos_tira_nao_escolha_e_renormaliza():
    v, aud = P.validos(
        {"lula": 40, "flavio": 40, "cury": 10, "branco_nulo": 6, "indecisos": 4}
    )
    assert v == pytest.approx(
        {"lula": 44.4444, "flavio": 44.4444, "cury": 11.1111}, abs=1e-4
    )
    assert aud["soma_candidaturas_pct_total"] == 90
    assert aud["nao_escolha_pct_total"] == 10
    assert aud["negativos_truncados_pp"] == 0


def test_validos_trunca_negativo_da_reponderacao():
    v, aud = P.validos({"lula": 50, "flavio": 50, "zema": -0.5, "branco_nulo": 3})
    assert v["zema"] == 0
    assert v["lula"] == pytest.approx(50)
    assert aud["negativos_truncados_pp"] == pytest.approx(0.5)


def test_validos_exige_os_dois_finalistas():
    with pytest.raises(ValueError):
        P.validos({"lula": 50, "cury": 10})


def test_quebra_terceiros_nao_inventa_zero():
    agrupado = {"lula": 50, "flavio": 40, "outros": 10}
    assert P.quebra_terceiros(agrupado) is None
    aberto = {
        "lula": 45,
        "flavio": 45,
        "cury": 4,
        "renan_santos": 3,
        "caiado": 2,
        "zema": 0.5,
    }
    q = P.quebra_terceiros(aberto)
    assert q["demais"] == pytest.approx(0.5)
    assert P.vetor_terceiros(aberto)["flavio"] == 45


def test_blocos_fecham_cem():
    b = P.blocos(URNA)
    assert b["terceira_via"] == pytest.approx(8.0)
    assert sum(b.values()) == pytest.approx(100)


# ---------------------------------------------------------------- erros


def test_erro_na_diferenca_tem_sinal_da_casa():
    pesquisa = {**URNA, "flavio": 44.0, "lula": 48.0}
    e = P.erros_vs_urna(pesquisa, URNA, ["flavio", "lula", "cury"])
    # Pesquisa L−F = +4; urna L−F = −2: superestima Lula em 6.
    assert e["diferenca_lula_menos_flavio"]["erro"] == pytest.approx(6.0)
    assert e["erro_pp"]["flavio"] == pytest.approx(-3.0)
    assert e["eam_candidatos_pp"] == pytest.approx(2.0)
    assert e["eam_blocos_pp"] == pytest.approx(2.0)


def test_eam_some_quando_candidatura_nao_e_aberta():
    pesquisa = {"flavio": 47.0, "lula": 45.0, "outros": 8.0}
    e = P.erros_vs_urna(pesquisa, URNA, ["flavio", "lula", "cury"])
    assert e["eam_candidatos_pp"] is None
    assert e["eam_blocos_pp"] == pytest.approx(0.0)


def test_margem_da_diferenca_sob_aas():
    # p_L = p_F = 0,5 e n = 1000: var = 1/1000.
    m = P.margem_diferenca_aas(1000, 1.0, 50, 50)
    assert m == pytest.approx(100 * P.Z95 * math.sqrt(1 / 1000))
    assert P.margem_diferenca_aas(2000, 0.5, 50, 50) == pytest.approx(m)


def test_ordenar_por_erro_absoluto_com_ausentes_no_fim():
    linhas = [
        {"id": "a", "e": -3.0},
        {"id": "b", "e": None},
        {"id": "c", "e": 0.5},
        {"id": "d", "e": 1.0},
    ]
    out = P.ordenar_por_erro(linhas, lambda x: x["e"])
    assert [x["id"] for x in out] == ["c", "d", "a", "b"]


def test_resumo_erros():
    r = P.resumo_erros([1.0, 3.0, -2.0])
    assert r["media"] == pytest.approx(2 / 3)
    assert r["mediana"] == 1.0
    assert (r["positivos"], r["negativos"]) == (2, 1)
    assert r["media_absoluta"] == pytest.approx(2.0)


def test_percentil_de_histograma_uniforme():
    contagens, limites = [10, 10, 10, 10], [0, 1, 2, 3, 4]
    assert P.percentil_histograma(2.0, contagens, limites) == pytest.approx(0.5)
    assert P.percentil_histograma(0.5, contagens, limites) == pytest.approx(0.125)
    assert P.percentil_histograma(9.0, contagens, limites) == pytest.approx(1.0)
    assert P.percentil_histograma(-1.0, contagens, limites) == pytest.approx(0.0)
    with pytest.raises(ValueError):
        P.percentil_histograma(1.0, [1, 2], [0, 1])


def test_chance_de_alguma_casa_perto_de_zero():
    assert P.prob_alguma_perto_de_zero(0.0, 1.0, 1, 1.959963984540054) == pytest.approx(
        0.95
    )
    um = P.prob_alguma_perto_de_zero(3.0, 3.0, 1, 0.5)
    assert P.prob_alguma_perto_de_zero(3.0, 3.0, 5, 0.5) == pytest.approx(
        1 - (1 - um) ** 5
    )


def test_brier_e_calibracao():
    pares = [(0.9, 1), (0.2, 0), (0.6, 0), (0.95, 1)]
    assert P.brier(pares) == pytest.approx((0.01 + 0.04 + 0.36 + 0.0025) / 4)
    cal = P.calibracao_por_faixa(pares, (0.0, 0.5, 1.0))
    assert [c["n"] for c in cal] == [1, 3]
    assert cal[1]["frequencia"] == pytest.approx(2 / 3)
    assert cal[1]["observados"] == 2
    assert cal[1]["esperados"] == pytest.approx(0.9 + 0.6 + 0.95)
    with pytest.raises(ValueError):
        P.brier([])


# ---------------------------------------------------------------- consolidação


def test_partilhas_somam_um():
    linha = {"Flávio": 56, "Lula": 8, "Branco/nulo": 37, "Indecisos": 0}
    f, lu = P.partilha(linha, "renormalizada")
    assert (f, lu) == pytest.approx((56 / 64, 8 / 64))
    f2, l2 = P.partilha(linha, "com_vazamento", 40.0, 60.0)
    assert f2 + l2 == pytest.approx(1.0)
    assert f2 == pytest.approx(56 / 101 + (37 / 101) * 0.4)
    with pytest.raises(ValueError):
        P.partilha(linha, "com_vazamento")


def test_decomposicao_fecha_a_conta():
    pesquisa = {
        "flavio": 43.0,
        "lula": 45.0,
        "cury": 4.0,
        "renan_santos": 4.0,
        "caiado": 3.0,
        "zema": 1.0,
    }
    urna = {
        "flavio": 47.0,
        "lula": 45.5,
        "cury": 3.0,
        "renan_santos": 2.5,
        "caiado": 1.5,
        "zema": 0.5,
    }
    part = dict.fromkeys(("cury", "renan_santos", "caiado", "zema"), (0.7, 0.3))
    d = P.decompor_consolidacao(pesquisa, urna, part)
    assert d["queda_terceira_via_pp"] == pytest.approx(4.5)
    assert d["explicado_flavio_pp"] + d["explicado_lula_pp"] == pytest.approx(
        d["ganho_flavio_pp"] + d["ganho_lula_pp"]
    )
    assert d["residuo_flavio_pp"] == pytest.approx(-d["residuo_lula_pp"])
    assert d["explicado_diferenca_pp"] + d["residuo_diferenca_pp"] == pytest.approx(
        d["erro_diferenca_lula_menos_flavio_pp"]
    )


def test_consolidacao_pura_nao_deixa_residuo():
    pesquisa = {"flavio": 43.0, "lula": 45.0, "cury": 6.0, "caiado": 6.0}
    part = {"cury": (0.6, 0.4), "caiado": (0.25, 0.75)}
    # Cury perde 2 e Caiado perde 4, repartidos exatamente pela partilha.
    urna = {
        "flavio": 43.0 + 2 * 0.6 + 4 * 0.25,
        "lula": 45.0 + 2 * 0.4 + 4 * 0.75,
        "cury": 4.0,
        "caiado": 2.0,
    }
    d = P.decompor_consolidacao(pesquisa, urna, part)
    assert d["residuo_diferenca_pp"] == pytest.approx(0.0, abs=1e-12)
    assert d["fracao_explicada_diferenca"] == pytest.approx(1.0)


def test_decomposicao_recusa_terceiro_sem_partilha():
    pesquisa = {"flavio": 45.0, "lula": 45.0, "cury": 10.0}
    with pytest.raises(ValueError):
        P.decompor_consolidacao(pesquisa, dict(pesquisa), {})


# ---------------------------------------------------------------- reserva


@pytest.mark.parametrize(("lam", "theta"), [(0.6, 0.1), (1.2, -0.3), (0.0, 0.8)])
def test_resolver_reserva_inverte_o_cenario_do_mapa(lam, theta):
    e = VU.Estado(
        "XX", 1.0, F1=40.0, L1=42.0, T1=10.0, I1=4.0, B1=4.0, F2=46.0, L2=47.0
    )
    e.fT_flavio, e.fT_lula = 0.75, 0.7
    c = VU.cenario(e, lam, theta)
    f, lu = 100 * c["F"] / c["validos"], 100 * c["L"] / c["validos"]
    entrada = {
        "F": 40.0,
        "L": 42.0,
        "T": 10.0,
        "F2": 46.0,
        "L2": 47.0,
        "fT_flavio": 0.75,
        "fT_lula": 0.7,
    }
    sol = P.resolver_reserva(entrada, f, lu)
    assert sol["lambda_flavio"] == pytest.approx(lam)
    assert sol["theta_lula"] == pytest.approx(theta)
    assert sol["consistente"]


def test_resolver_reserva_sem_reserva_devolve_none():
    entrada = {
        "F": 40.0,
        "L": 42.0,
        "T": 10.0,
        "F2": 39.0,
        "L2": 47.0,
        "fT_flavio": 0.5,
        "fT_lula": 0.5,
    }
    sol = P.resolver_reserva(entrada, 45.0, 45.0)
    assert sol["lambda_flavio"] is None
    assert sol["reserva_flavio_pp"] == 0.0


def test_fracao_terceira_da_regra_do_mapa():
    t = {
        "terceira_flavio": 0.4,
        "indecisos_flavio": 0.3,
        "branco_flavio": 0.1,
        "terceira_lula": 0.3,
        "indecisos_lula": 0.3,
        "branco_lula": 0.1,
    }
    ff, fl = P.fracao_terceira(t, {"T": 10.0, "I": 2.0, "B": 4.0})
    assert ff == pytest.approx(4.0 / (4.0 + 0.6 + 0.4))
    assert fl == pytest.approx(3.0 / (3.0 + 0.6 + 0.4))
    assert P.fracao_terceira(t, {"T": 0.0, "I": 0.0, "B": 0.0}) == (0.5, 0.5)


def test_resolver_2d_sistema_linear():
    def f(x, y):
        return (2 * x + y, x - 3 * y)

    x, y = P.resolver_2d(f, (5.0, -1.0))
    assert (x, y) == pytest.approx((2.0, 1.0))


def test_interpolar_curva():
    curva = [{"lam": 0.0, "v": 40.0}, {"lam": 0.5, "v": 44.0}, {"lam": 1.0, "v": 48.0}]
    assert P.interpolar_curva(curva, "v", 46.0) == pytest.approx(0.75)
    assert P.interpolar_curva(curva, "v", 50.0) is None


def test_media_vetores_usa_chaves_comuns():
    m = P.media_vetores([{"a": 1.0, "b": 2.0}, {"a": 3.0}])
    assert m == {"a": 2.0}


# ---------------------------------------------------------------- previsão da casa


def test_comparar_blocos_da_central():
    prev = C.pct_validos({"lula": 45.0, "flavio": 45.0, "outros": 10.0})
    c = C.comparar_blocos(prev, URNA)
    assert c["erro_pp"]["terceira_via"] == pytest.approx(2.0)
    assert c["erro_diferenca_lula_menos_flavio"] == pytest.approx(2.0)


# ---------------------------------------------------------------- Senado


class BancoFalso:
    """Imita a interface de leitura do banco da apuração com uma UF."""

    def __init__(self, cands):
        self.cands = cands

    def arquivo(self, eleicao, cargo, nivel, uf):
        return 1

    def snapshot(self, arquivo_id, **_):
        return {"id": 7, "gerado_em": "x", "sha256": "y", "tf": 1, "pst": 100.0}

    def candidatos(self, snapshot_id):
        return self.cands


def test_senado_brier_e_duas_vagas():
    cands = [
        {"sqcand": 1, "nome": "A", "partido": "PL", "pct": 30.0, "st": "Eleito"},
        {"sqcand": 2, "nome": "B", "partido": "PT", "pct": 25.0, "st": "Eleito"},
        {"sqcand": 3, "nome": "C", "partido": "MDB", "pct": 20.0, "st": "Não eleito"},
    ]
    prob = [
        {"nome": "A", "nome_urna": "A", "sq_candidato": "1", "p_eleito": 0.9},
        {"nome": "C", "nome_urna": "C", "sq_candidato": "3", "p_eleito": 0.6},
        {"nome": "B", "nome_urna": "B", "sq_candidato": "2", "p_eleito": 0.5},
        {"nome": "D", "nome_urna": "D", "sq_candidato": "4", "p_eleito": 0.0},
    ]
    pred = {
        "estados": {
            "XX": {
                "cobertura": "recente",
                "probabilidades": prob,
                "media": [
                    {"sq_candidato": "1", "validos": 31.0},
                    {"sq_candidato": "3", "validos": 26.0},
                    {"sq_candidato": "2", "validos": 24.0},
                ],
                "duplas": [
                    {"nomes": ["A", "C"], "p": 0.5},
                    {"nomes": ["A", "B"], "p": 0.4},
                ],
                "dupla_mais_provavel": ["A", "C"],
                "p_dupla_mais_provavel": 0.5,
            }
        }
    }
    s = E.senado(BancoFalso(cands), pred, 6259)
    r = s["resumo"]
    # Três na urna mais a prevista ausente dela (p = 0, não eleita).
    assert r["n_candidaturas"] == 4
    assert r["brier"] == pytest.approx((0.01 + 0.25 + 0.36 + 0.0) / 4)
    assert r["acertos_top2"] == 1
    assert r["acertos_top2_esperados"] == pytest.approx(1.5)
    assert s["linhas"][0]["p_dupla_eleita"] == pytest.approx(0.4)


# ---------------------------------------------------------------- memorando


def test_numero_em_portugues_sem_travessao():
    assert M.num(-1.5) == "−1,50"
    assert M.num(3.546, sinal=True) == "+3,55"
    assert M.num(1234.5, 1) == "1.234,5"
    assert M.num(None) == "n/d"
    assert M.nome_proprio("SAMANDA DE LULA") == "Samanda de Lula"
    assert M.hora_brasilia("2026-10-05T05:59:31.000Z") == "05/10 às 02:59 (Brasília)"
    assert "\u2014" not in M.num(-0.004)
