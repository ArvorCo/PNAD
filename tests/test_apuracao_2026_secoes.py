"""Testes da análise por seção (boletins de urna), com dados sintéticos e bancos
SQLite mínimos criados no diretório temporário. Nada aqui lê o banco da coleta."""

import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from apuracao_2026 import secoes_base as sb
from apuracao_2026 import secoes_clusters as sc
from apuracao_2026 import secoes_clusters_leitura as sl
from apuracao_2026 import secoes_texto as st
from apuracao_2026 import secoes_urna as su

RAIZ = Path(__file__).resolve().parents[1]
JSON_SECOES = RAIZ / "analysis/apuracao_2026/dados/secoes.json"


# ---------------------------------------------------------------- transformações


def test_clr_troca_zero_por_0001_e_soma_zero():
    fr = np.array([[0.5, 0.3, 0.2, 0.0], [0.25, 0.25, 0.25, 0.25]])
    z = sb.clr(fr)
    assert np.allclose(z.sum(axis=1), 0.0)
    lx = np.log([0.5, 0.3, 0.2, 1e-4])
    assert z[0, 3] == pytest.approx(lx[3] - lx.mean())
    assert np.allclose(z[1], 0.0)


def test_clr_nao_altera_valores_positivos_pequenos():
    fr = np.array([[0.99995, 0.00005]])
    z = sb.clr(fr)
    lx = np.log([0.99995, 0.00005])
    assert np.allclose(z[0], lx - lx.mean())


def test_logit_com_zero_e_um():
    x = sb.logit(np.array([[0.0, 1.0, 0.5]]))
    assert x[0, 0] == pytest.approx(math.log(1e-4 / (1 - 1e-4)))
    assert x[0, 1] == pytest.approx(math.log((1 - 1e-4) / 1e-4))
    assert x[0, 2] == pytest.approx(0.0)


def test_ilr_e_rotacao_da_clr():
    rng = np.random.default_rng(1)
    fr = rng.dirichlet(np.ones(6), size=200)
    z, x = sc.coordenadas(fr)
    v = sc.ilr_base(6)
    assert np.allclose(v.T @ v, np.eye(5))
    assert np.allclose(x @ v.T, z)
    # distâncias euclidianas preservadas
    assert np.linalg.norm(z[0] - z[1]) == pytest.approx(np.linalg.norm(x[0] - x[1]))


def test_num_em_portugues():
    assert sb.num(1234.5, 1) == "1.234,5"
    assert sb.num(-0.25, 2) == "-0,25"
    assert sb.num(1000000, 0) == "1.000.000"


# ---------------------------------------------------------------- clusters


def test_escolher_anomalo_menor_densidade_e_maior_dispersao():
    # o componente 2 tem a menor log-verossimilhança e a maior dispersão
    assert sc.escolher_anomalo([-1.0, -3.0, -9.0, -2.0], [1.0, 2.0, 8.0, 0.5]) == 2


def test_escolher_anomalo_empate_decide_pela_densidade():
    # soma de postos: 0 → 3+2, 1 → 0+1, 2 → 1+0, 3 → 2+3; empate entre 1 e 2
    assert sc.escolher_anomalo([-1.0, -5.0, -3.0, -2.0], [1.0, 3.0, 5.0, 0.0]) == 1


def test_mistura_separa_grupos_bem_definidos():
    rng = np.random.default_rng(3)
    centros = [np.array([0.6, 0.2, 0.1, 0.1]), np.array([0.2, 0.6, 0.1, 0.1])]
    fr = np.vstack([rng.dirichlet(400 * c, size=300) for c in centros])
    _, x = sc.coordenadas(fr)
    gm = sc.ajustar(x, 2, n_init=3)
    rot = gm.predict(x)
    assert len(set(rot[:300])) == 1
    assert len(set(rot[300:])) == 1
    assert rot[0] != rot[-1]


def test_ordem_estavel_do_mais_lulista_ao_menos():
    rot = np.array([0, 0, 1, 1, 2, 2])
    lula = np.array([10.0, 12.0, 80.0, 82.0, 50.0, 52.0])
    mapa = sc.ordem_estavel(rot, lula, 3)
    assert list(mapa[rot]) == [2, 2, 0, 0, 1, 1]


def test_ajustar_melhor_fica_com_a_maior_verossimilhanca():
    rng = np.random.default_rng(7)
    centros = [np.array([0.6, 0.2, 0.1, 0.1]), np.array([0.2, 0.6, 0.1, 0.1])]
    fr = np.vstack([rng.dirichlet(200 * c, size=200) for c in centros])
    _, x = sc.coordenadas(fr)
    aj = sc.ajustar_melhor(x, 2, sementes=(1, 2, 3), n_init=1, inits=sc.INITS)
    lls = [r["loglik_media"] for r in aj.log]
    assert [(r["semente"], r["init"]) for r in aj.log] == [
        (s, i) for i in sc.INITS for s in (1, 2, 3)
    ]
    assert aj.gm.score(x) == pytest.approx(max(lls), abs=1e-4)
    assert aj.semente in (1, 2, 3) and aj.init in sc.INITS
    assert len(aj.todos) == 6


def test_k_principal_e_cinco_com_bic_de_tres_a_cinco():
    assert sc.K == 5
    assert sc.K_TABELA == (3, 4, 5)
    assert sc.ESCOLHA_K["k"] == sc.K and sc.ESCOLHA_K["anterior"] == 3
    assert len(sc.SEMENTES) == sc.N_SEMENTES == 16
    assert len(sc.SEMENTES_15) == 8 and sc.SEMENTES[:8] == sc.SEMENTES_15
    assert sc.INITS == ("kmeans", "k-means++")
    assert sc.PARTES == ("lula", "flavio", "brancos", "nulos", "abstencao")


def _df_cinco() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "aptos": [100, 200, 50],
            "comparecimento": [80, 150, 50],
            "v13": [40, 60, 0],
            "v22": [30, 70, 40],
            "brancos": [2, 0, 3],
            "nulos": [3, 5, 2],
            "validos": [75, 145, 45],
        }
    )


def test_matriz_cinco_deixa_terceiros_de_fora_e_fecha():
    df = _df_cinco()
    el, fora = sc.matriz_cinco(df)
    # Lula, Flávio, brancos, nulos, abstenção / aptos
    assert el[0].tolist() == pytest.approx([0.40, 0.30, 0.02, 0.03, 0.20])
    # o que falta para 1 é o voto em terceiros / aptos
    terceiros = (df["validos"] - df["v13"] - df["v22"]) / df["aptos"]
    assert fora == pytest.approx(terceiros.to_numpy())
    fe = sc.fechar(el)
    assert fe.sum(axis=1) == pytest.approx(np.ones(3))
    comp = sc.composicao_cinco(df)
    assert comp.chaves == list(sc.PARTES)
    assert comp.unidades.tolist() == pytest.approx([95, 185, 45])
    with pytest.raises(ValueError):
        sc.fechar(np.zeros((1, 5)))


def test_fechar_nao_muda_a_clr_sem_zeros():
    rng = np.random.default_rng(5)
    el = rng.dirichlet(np.ones(6), size=50)[:, :5]  # tira uma parte: soma < 1
    assert np.allclose(sb.clr(el), sb.clr(sc.fechar(el)))


def test_projecao_ilr_igual_a_pca_na_clr():
    from sklearn.decomposition import PCA

    rng = np.random.default_rng(9)
    fr = rng.dirichlet(np.array([8.0, 6.0, 1.0, 1.5, 4.0]), size=400)
    z, x = sc.coordenadas(fr)
    pca, p, cargas = sc.projecao(x)
    ref = PCA(n_components=2).fit(z)
    pz = ref.transform(z)
    for j in range(2):
        sinal = np.sign(p[:, j] @ pz[:, j])
        assert np.allclose(p[:, j], sinal * pz[:, j])
        assert np.allclose(cargas[j], sinal * ref.components_[j])
    assert pca.explained_variance_ratio_ == pytest.approx(ref.explained_variance_ratio_)


def test_degrau_log_usa_as_unidades_da_composicao():
    d = sc.degrau_log(np.array([100.0, 100.0, 100.0]))
    # zero vira 0,0001 e um voto em 100 é 0,01: log(100)
    assert d["mediana"] == pytest.approx(round(math.log(100), 2))


def test_convergencia_em_grupos_separados():
    from apuracao_2026 import secoes_clusters_diag as cd

    rng = np.random.default_rng(13)
    centros = [np.array([0.6, 0.2, 0.1, 0.1]), np.array([0.2, 0.6, 0.1, 0.1])]
    fr = np.vstack([rng.dirichlet(300 * c, size=300) for c in centros])
    _, x = sc.coordenadas(fr)
    aj = sc.ajustar_melhor(x, 2, sementes=(1, 2, 3), n_init=2, inits=sc.INITS)
    diag, gm = cd.convergencia(x, aj)
    ap = diag["apertado"]
    assert ap["tol"] == 1e-6 and ap["max_iter"] == 2000
    assert ap["iteracoes"] >= ap["iteracoes_padrao"]
    assert ap["diferenca_loglik"] == pytest.approx(0.0, abs=1e-3)
    assert ap["ari_padrao_apertado"] == pytest.approx(1.0)
    assert not ap["adotado"] and gm is aj.gm
    rot = gm.predict(x)
    from sklearn.metrics import adjusted_rand_score

    diag["ajustes"] = [
        {**linha, "ari_com_escolhida": adjusted_rand_score(rot, g.predict(x))}
        for linha, (_, _, g) in zip(aj.log, aj.todos, strict=True)
    ]
    cd.resumir(diag)
    assert diag["total"] == 6 and diag["no_maximo"] == 6
    assert diag["por_init"] == {
        "kmeans": {"total": 3, "no_maximo": 3},
        "k-means++": {"total": 3, "no_maximo": 3},
    }
    assert diag["todas_convergiram"] and diag["particao_estavel"]
    assert diag["ari_medio_demais"] is None
    assert diag["frase"].startswith("O EM convergiu nas 6 partidas")
    assert "6 de 6 partidas chegaram ao mesmo máximo" in diag["frase"]
    assert "estável" in diag["frase"] and "—" not in diag["frase"]


def test_resumir_conta_o_maximo_a_um_milesimo():
    from apuracao_2026 import secoes_clusters_diag as cd

    diag = {
        "inits": ["kmeans"],
        "criterio_padrao": {"tol": 1e-4, "max_iter": 500},
        "sementes": 3,
        "partidas_internas": 10,
        "tolerancia_maximo": 1e-3,
        "apertado": {
            "tol": 1e-6,
            "max_iter": 2000,
            "iteracoes": 40,
            "iteracoes_padrao": 20,
            "diferenca_loglik": 0.0,
            "ari_padrao_apertado": 1.0,
            "adotado": False,
        },
        "ajustes": [
            {"semente": 1, "init": "kmeans", "loglik_media": -2.0, "convergiu": True,
             "iteracoes": 10, "ari_com_escolhida": 1.0},
            {"semente": 2, "init": "kmeans", "loglik_media": -2.0005, "convergiu": True,
             "iteracoes": 12, "ari_com_escolhida": 0.98},
            {"semente": 3, "init": "kmeans", "loglik_media": -2.5, "convergiu": False,
             "iteracoes": 500, "ari_com_escolhida": 0.4},
        ],
    }  # fmt: skip
    cd.resumir(diag)
    assert diag["no_maximo"] == 2 and diag["total"] == 3
    assert diag["ari_medio_no_maximo"] == 0.99 and diag["ari_medio_demais"] == 0.4
    assert diag["particao_estavel"] and not diag["todas_convergiram"]
    assert diag["frase"].startswith("O EM não convergiu em 1 das 3 partidas")


def test_separacao_acha_o_corte():
    score = np.array([-3.0, -2.5, -2.0, 1.0, 1.5, 2.0])
    zero = np.array([True, True, True, False, False, False])
    res = sc.separacao(score, zero)
    assert res is not None
    acerto, corte = res
    assert acerto == pytest.approx(100.0)
    assert -2.0 <= corte < 1.0
    # o lado não importa: zeros à direita dão o mesmo acerto
    inverso = sc.separacao(-score, zero)
    assert inverso is not None and inverso[0] == pytest.approx(100.0)
    assert sc.separacao(score, np.zeros(6, dtype=bool)) is None


def _grupos_de_zeros():
    """Três grupos: sem voto em a e b; voto em a; voto em b (partes a, b, c)."""
    zero = np.array(
        [[True, True, False]] * 40
        + [[False, True, False]] * 30
        + [[True, False, False]] * 30
    )
    rot = np.array([0] * 40 + [1] * 30 + [2] * 30)
    return zero, rot


def test_padroes_zeros_pelos_numeros():
    zero, rot = _grupos_de_zeros()
    chaves = ["a", "b", "c"]
    # a é a menos votada, b a seguinte
    pads = sl.padroes_zeros(zero, rot, 3, chaves, [0, 1, 2])
    g0 = pads[0][0]
    assert g0["tipo"] == "sem" and g0["conjunto"] == "menos_votadas"
    assert g0["m"] == 2 and g0["pct_grupo"] == 100.0 and g0["pct_outro"] == 0.0
    nomes = {"a": "Ana", "b": "Bia", "c": "Caio"}
    assert sl.descrever_padrao(pads[0], nomes).startswith(
        "sem voto nas duas candidaturas menos votadas"
    )
    assert sl.descrever_padrao(pads[1], nomes) == "sem voto em Bia e com voto em Ana"
    assert sl.descrever_padrao(pads[2], nomes) == "sem voto em Ana e com voto em Bia"
    # nenhuma parte cobre o grupo inteiro: nenhum padrão
    vazio = sl.padroes_zeros(
        np.zeros((10, 3), dtype=bool), np.array([0, 1] * 5), 2, chaves, [0, 1, 2]
    )
    assert vazio == [[], []]


def test_descrever_padrao_junta_nomes_e_partes():
    itens = [
        {
            "tipo": "sem",
            "conjunto": None,
            "m": None,
            "partes": ["n30"],
            "pct_grupo": 100.0,
        },
        {
            "tipo": "sem",
            "conjunto": None,
            "m": None,
            "partes": ["n80"],
            "pct_grupo": 100.0,
        },
        {
            "tipo": "com",
            "conjunto": None,
            "m": None,
            "partes": ["brancos"],
            "pct_grupo": 99.0,
        },
        {
            "tipo": "parcial_com",
            "conjunto": None,
            "m": None,
            "partes": ["n55"],
            "pct_grupo": 69.4,
        },
    ]
    nomes = {"n30": "Romeu Zema", "n80": "Samara", "n55": "Ronaldo Caiado"}
    assert sl.descrever_padrao(itens, nomes) == (
        "sem voto em Romeu Zema e em Samara, com voto branco e com voto em "
        "Ronaldo Caiado em 69% das seções"
    )


def test_rotulo_sem_padrao_usa_abstencao():
    c = {
        "centro_pct_validos": {"lula": 62.0, "flavio": 30.0},
        "centro_pct_eleitorado": {"abstencao": 21.4},
        "regioes": [{"regiao": "Nordeste", "pct_do_cluster": 50.2}],
        "padrao_zeros": [],
    }
    assert (
        sl.rotulo(c, {})
        == "Lula 62% dos válidos, abstenção 21%, Nordeste 50% das seções"
    )
    c["padrao_zeros"] = [
        {
            "tipo": "sem",
            "conjunto": "menos_votadas",
            "m": 5,
            "partes": [],
            "pct_grupo": 100.0,
        }
    ]
    assert sl.rotulo(c, {}) == (
        "sem voto nas cinco candidaturas menos votadas; Lula 62% dos válidos; "
        "Nordeste 50% das seções"
    )


def test_rotulo_perfil_em_desvios_da_media_nacional():
    from apuracao_2026 import secoes_clusters_perfil as sp

    ref = {
        "lula": {"media_pct": 35.0, "dp_pct": 10.0},
        "flavio": {"media_pct": 35.0, "dp_pct": 10.0},
        "brancos": {"media_pct": 1.5, "dp_pct": 1.0},
        "nulos": {"media_pct": 2.3, "dp_pct": 1.0},
        "abstencao": {"media_pct": 20.0, "dp_pct": 5.0},
        "terceiros": {"media_pct": 6.0, "dp_pct": 3.0},
    }
    c = {
        "centro_pct_eleitorado": {
            "lula": 55.0,  # +2 dp: muito alto
            "flavio": 25.0,  # −1 dp: muito baixo
            "brancos": 0.0,  # −1,5 dp, mas é o artefato do grupo
            "nulos": 2.0,  # −0,3 dp
            "abstencao": 24.0,  # +0,8 dp
        },
        "terceiros_pct_eleitorado": 6.5,
        "regioes": [
            {"regiao": "Nordeste", "pct_do_cluster": 78.4},
            {"regiao": "Norte", "pct_do_cluster": 12.0},
        ],
        "padrao_zeros": [],
    }
    assert sp.rotulo_perfil(c, ref, {}) == (
        "Lula muito alto, brancos muito baixos, Flávio muito baixo; "
        "Nordeste 78% das seções"
    )
    c["regioes"][0]["pct_do_cluster"] = 45.0
    c["padrao_zeros"] = [
        {"tipo": "sem", "conjunto": None, "m": None, "partes": ["brancos"]},
        {"tipo": "com", "conjunto": None, "m": None, "partes": ["nulos"]},
    ]
    c["artefato"] = sp.artefato(c, {})
    assert c["artefato"] == "sem voto branco"
    assert sp.rotulo_perfil(c, ref, {}) == (
        "sem voto branco; Lula muito alto, Flávio muito baixo, abstenção alta; "
        "Nordeste 45% e Norte 12% das seções"
    )
    perto = dict(c, centro_pct_eleitorado={k: v["media_pct"] for k, v in ref.items()})
    perto |= {"terceiros_pct_eleitorado": 6.0, "padrao_zeros": [], "artefato": None}
    assert sp.rotulo_perfil(perto, ref, {}).startswith("perto da média nacional; ")


def test_empates_definem_grupo():
    from apuracao_2026 import secoes_clusters_perfil as sp

    cont = np.array([[10, 5, 3, 3, 4]] * 40 + [[10, 5, 2, 6, 4]] * 60)
    rot = np.array([0] * 40 + [1] * 60)
    pads = sp.padroes_empate(cont, rot, 2, list(sc.PARTES))
    assert pads[1] == []
    assert pads[0][0]["partes"] == ["brancos", "nulos"]
    assert pads[0][0]["pct_grupo"] == 100.0 and pads[0][0]["pct_outro"] == 0.0
    c = {"padrao_zeros": [], "padrao_empates": pads[0]}
    assert sp.artefato(c, {}) == "mesmo número de brancos e de nulos"
    pares = sp.empates_por_par(cont, list(sc.PARTES))
    bn = next(x for x in pares if x["partes"] == ["brancos", "nulos"])
    assert bn["secoes"] == 40 and bn["pct_secoes"] == 40.0


def test_referencia_media_e_desvio_entre_secoes():
    from apuracao_2026 import secoes_clusters_perfil as sp

    comp = sc.composicao_cinco(_df_cinco())
    ref = sp.referencia(comp)
    assert set(ref) == {*sc.PARTES, "terceiros"}
    assert ref["lula"]["media_pct"] == pytest.approx(
        100 * (0.4 + 0.3 + 0.0) / 3, abs=1e-3
    )
    assert ref["terceiros"]["media_pct"] == pytest.approx(
        100 * (0.05 + 0.075 + 0.1) / 3, abs=1e-3
    )


def test_diagnostico_zeros_da_versao_de_quinze_partes():
    c = {
        "features": [f"p{i}" for i in range(15)],
        "cramer_v_regiao": 0.207,
        "zeros_substituidos_pct": 42.66,
        "degrau_log": {"aptos_mediana": 327, "mediana": 3.42, "p10": 3.2, "p90": 3.8},
        "componentes": [
            {
                "id": i,
                "padrao_zeros": [
                    {
                        "tipo": "sem",
                        "conjunto": None,
                        "m": None,
                        "partes": ["p1"],
                        "pct_grupo": 100.0,
                        "outro_grupo": 1 - i,
                        "pct_outro": 0.0,
                    }
                ],
            }
            for i in range(2)
        ],
    }
    f = sl.diagnostico_zeros(c, {"p1": "Zema"})
    assert f.startswith("Com as 15 partes, os dois grupos não são geografia")
    assert "42,7% das células são zero" in f and "3,4 unidades de log" in f
    c["cramer_v_regiao"] = 0.45
    assert "acompanham a geografia" in sl.diagnostico_zeros(c, {})


def test_cramer_associacao_perfeita_e_nula():
    a = pd.Series([0, 0, 1, 1] * 25)
    assert sc.cramer(a, a.map({0: "x", 1: "y"})) == pytest.approx(1.0)
    b = pd.Series(["x", "y", "x", "y"] * 25)
    assert sc.cramer(pd.Series([0, 0, 1, 1] * 25), b) == pytest.approx(0.0)


# ---------------------------------------------------------------- modelo de urna


def _zonas_sinteticas(delta_pp: float, confunde: bool, ruido: bool, semente=11):
    """Zonas com perfil político próprio; o modelo b soma `delta_pp` a Flávio.

    Com `confunde`, o modelo b fica nas zonas mais flavistas (geografia), e a
    comparação bruta erra; dentro da zona o efeito é o verdadeiro.
    """
    rng = np.random.default_rng(semente)
    linhas = []
    for z in range(60):
        p = 0.2 + 0.6 * z / 59
        frac_b = (0.1 + 0.8 * z / 59) if confunde else 0.5
        for s in range(40):
            modelo = "UE2022" if s < round(40 * frac_b) else "UE2015"
            prob = p + (delta_pp / 100 if modelo == "UE2022" else 0.0)
            validos = 300
            flavio = rng.binomial(validos, prob) if ruido else round(validos * prob)
            linhas.append(
                {
                    "uf": "xx",
                    "mun": f"{z:05d}",
                    "zona": z,
                    "secao": s,
                    "local_nr": s // 4,
                    "modelo_urna": modelo,
                    "v22": flavio,
                    "v13": validos - flavio,
                    "validos": validos,
                    "votantes": 320,
                    "comparecimento": 320,
                    "aptos": 400,
                    "abstencao": 80,
                    "brancos": 8,
                    "nulos": 12,
                }
            )
    return pd.DataFrame(linhas)


def test_dentro_da_zona_recupera_efeito_conhecido_sem_ruido():
    df = _zonas_sinteticas(1.0, confunde=False, ruido=False)
    r = su.diferenca_dentro(
        df, ["uf", "mun", "zona"], "UE2015", "UE2022", 1, su.METRICAS_2026
    )
    assert r["unidades"] == 60
    # arredondamento a voto inteiro em 300 válidos: erro máximo de 1/300
    assert r["flavio_pp"]["estimativa"] == pytest.approx(1.0, abs=0.34)
    assert r["lula_pp"]["estimativa"] == pytest.approx(-1.0, abs=0.34)
    assert r["abstencao_pp"]["estimativa"] == pytest.approx(0.0)


def test_geografia_confunde_o_bruto_mas_nao_o_estimador_dentro_da_zona():
    df = _zonas_sinteticas(0.0, confunde=True, ruido=True)
    r = su.diferenca_dentro(
        df, ["uf", "mun", "zona"], "UE2015", "UE2022", 1, su.METRICAS_2026
    )
    f = r["flavio_pp"]
    # o modelo novo está nas zonas flavistas: o bruto mostra efeito grande e falso
    assert f["bruto"] > 10
    # dentro da zona o efeito verdadeiro (zero) volta, com o zero no intervalo
    assert abs(f["estimativa"]) < 0.5
    assert f["ic95"][0] <= 0 <= f["ic95"][1]


def test_dentro_da_zona_com_ruido_cobre_o_efeito_verdadeiro():
    df = _zonas_sinteticas(2.0, confunde=True, ruido=True, semente=5)
    r = su.diferenca_dentro(
        df, ["uf", "mun", "zona"], "UE2015", "UE2022", 1, su.METRICAS_2026
    )
    lo, hi = r["flavio_pp"]["ic95"]
    assert lo <= 2.0 <= hi
    assert lo > 0


def test_minimo_de_secoes_por_modelo_filtra_unidades():
    df = _zonas_sinteticas(0.0, confunde=True, ruido=False)
    r20 = su.diferenca_dentro(
        df, ["uf", "mun", "zona"], "UE2015", "UE2022", 20, su.METRICAS_2026
    )
    r1 = su.diferenca_dentro(
        df, ["uf", "mun", "zona"], "UE2015", "UE2022", 1, su.METRICAS_2026
    )
    assert r20["unidades"] < r1["unidades"]


def test_variacao_contra_2022_usa_quatro_colunas():
    df = _zonas_sinteticas(0.0, confunde=False, ruido=False)
    df["bolsonaro_1t"] = df["v22"] - 30
    df["nominais_1t"] = df["validos"]
    df["lula_1t"] = df["v13"]
    r = su.diferenca_dentro(
        df, ["uf", "mun", "zona"], "UE2015", "UE2022", 1, su.METRICAS_VARIACAO
    )
    assert r["flavio_var_pp"]["estimativa"] == pytest.approx(0.0, abs=1e-9)


def _urna_reguas(estimativas):
    nomes = ["dentro_zona", "dentro_local", "dentro_zona_variacao", "troca_2022_2026"]
    chaves = ["flavio_pp", "flavio_pp", "flavio_var_pp", "flavio_var_pp"]
    u = {}
    for est, ch, e in zip(nomes, chaves, estimativas, strict=True):
        u[est] = {
            "pares": [
                {
                    "a": "mais velha",
                    "b": "mais nova",
                    "unidades": 100,
                    ch: {"estimativa": e, "ic95": [e - 0.1, e + 0.1], "bruto": 2 * e},
                }
            ]
        }
    return u


def test_reguas_com_sinal_que_muda_leem_alocacao():
    u = _urna_reguas([-0.735, 0.11, 0.224, -0.143])
    r = su.reguas(u)
    assert [i["estimador"] for i in r["itens"]] == [
        "dentro_zona",
        "dentro_local",
        "dentro_zona_variacao",
        "troca_2022_2026",
    ]
    assert r["max_abs_pp"] == pytest.approx(0.735)
    assert r["positivas"] == 2 and r["negativas"] == 2
    assert r["leitura"].startswith("As quatro réguas")
    assert "abaixo de um ponto" in r["leitura"]
    assert "não efeito da máquina" in r["leitura"]
    assert "\u2212" in r["leitura"] and "-0," not in r["leitura"]


def test_reguas_com_mesmo_sinal_nao_concluem_alocacao():
    r = su.reguas(_urna_reguas([1.4, 0.8, 0.6, 1.1]))
    assert "todas apontam a favor de Flávio" in r["leitura"]
    assert "chega a 1,40 pontos" in r["leitura"]
    assert "não efeito da máquina" not in r["leitura"]
    assert su.reguas({})["itens"] == []


def test_urna_nao_tem_mais_registro():
    assert not hasattr(su, "REGISTRO")
    assert not hasattr(su, "_registro")


def test_ordenar_modelos():
    assert su.ordenar_modelos(["UE2022", "UE2009", "UE2015"]) == [
        "UE2009",
        "UE2015",
        "UE2022",
    ]


# ---------------------------------------------------------------- local e fuso


@pytest.mark.parametrize(
    ("args", "esperado"),
    [
        (
            ("sp", "Preso provisório", "CDP II", "CENTRO", ""),
            "unidade prisional ou socioeducativa",
        ),
        (
            ("mt", "Convencional", "ESCOLA ESTADUAL INDÍGENA KAMADU", "ALDEIA", ""),
            "aldeia ou terra indígena",
        ),
        (("ba", "Convencional", "ESCOLA MUNICIPAL X", "ZONA RURAL", ""), "zona rural"),
        (
            ("sp", "Convencional", "EMEF JOSÉ", "CENTRO", "RUA A"),
            "escola ou universidade",
        ),
        (("zz", "Convencional", "EMBAIXADA DO BRASIL", "", ""), "exterior"),
        (("pa", "Convencional", "ESCOLA QUILOMBOLA", "", ""), "quilombo"),
        (("sp", "Convencional", "CLUBE", "CENTRO", ""), "outro"),
    ],
)
def test_tipo_local(args, esperado):
    assert sb.tipo_local(*args) == esperado


def test_fuso_pela_hora_de_abertura():
    df = pd.DataFrame(
        {
            "uf": ["ac", "ac", "am", "pe", "zz", "sp"],
            "mun": ["1", "1", "2", "3", "4", "5"],
            "abertura": [
                "2026-10-04 06:00:01",
                "2026-10-04 06:30:00",
                "2026-10-04 07:00:01",
                "2026-10-04 09:00:01",
                "2026-10-04 17:00:00",
                None,
            ],
        }
    )
    f = sb.fusos_por_municipio(df).tolist()
    assert f[:4] == [2.0, 2.0, 1.0, -1.0]
    assert math.isnan(f[4])
    assert f[5] == 0.0


def test_hora_brasilia():
    assert sb.hora_brasilia("2026-10-04 15:07:06", 2.0) == "2026-10-04 17:07:06"
    assert sb.hora_brasilia("2026-10-04 15:07:06", float("nan")) is None


# ---------------------------------------------------------------- montagem


def _bancos(tmp: Path) -> tuple[Path, Path, Path]:
    sec = tmp / "secoes.sqlite"
    con = sqlite3.connect(sec)
    con.executescript("""
        CREATE TABLE cs (uf TEXT, secoes INTEGER, baixado_em TEXT);
        CREATE TABLE secao (uf TEXT, mun TEXT, zona INTEGER, secao INTEGER,
          nsp INTEGER, status_aux TEXT, erro TEXT, bu_gz BLOB, dr_hr TEXT);
        CREATE TABLE bu (uf TEXT, mun TEXT, zona INTEGER, secao INTEGER, local INTEGER,
          modelo_urna TEXT, modelo_fonte TEXT, tipo_urna INTEGER, tipo_arquivo INTEGER,
          aptos INTEGER, aptos_secao INTEGER, aptos_tte INTEGER, comparecimento INTEGER,
          abertura TEXT, encerramento TEXT, n_cargas INTEGER, id_confere INTEGER);
        CREATE TABLE bu_cargo (uf TEXT, mun TEXT, zona INTEGER, secao INTEGER,
          cargo INTEGER, aptos INTEGER, comparecimento INTEGER);
        CREATE TABLE voto_secao (uf TEXT, mun TEXT, zona INTEGER, secao INTEGER,
          cargo INTEGER, tipo INTEGER, numero INTEGER, votos INTEGER);
        CREATE TABLE conferencia_zona (uf TEXT, mun TEXT, zona INTEGER, cargo INTEGER,
          secoes_cs INTEGER, secoes_bu INTEGER, ts_zona INTEGER, st_zona INTEGER,
          ok INTEGER, divergencias TEXT);
        INSERT INTO cs VALUES ('ac', 4, '');
        """)
    secoes = [("01007", 9, 1), ("01007", 9, 2), ("01015", 2, 1), ("01015", 2, 2)]
    for mun, zona, s in secoes:
        con.execute(
            "INSERT INTO secao VALUES ('ac', ?, ?, ?, NULL, 'Totalizada', NULL, x'00', "
            "'2026-10-04 18:00:00')",
            (mun, zona, s),
        )
        con.execute(
            "INSERT INTO bu VALUES ('ac', ?, ?, ?, 1, 'UE2020', 'log_mesma_urna', 1, 1, "
            "300, 300, 0, 240, '2026-10-04 06:00:01', '2026-10-04 15:00:00', 1, 1)",
            (mun, zona, s),
        )
        con.execute(
            "INSERT INTO bu_cargo VALUES ('ac', ?, ?, ?, 1, 300, 240)", (mun, zona, s)
        )
        for tipo, numero, votos in (
            (1, 13, 100),
            (1, 22, 120),
            (1, 28, 2),
            (2, 0, 8),
            (3, 0, 10),
        ):
            con.execute(
                "INSERT INTO voto_secao VALUES ('ac', ?, ?, ?, 1, ?, ?, ?)",
                (mun, zona, s, tipo, numero, votos),
            )
    con.execute("INSERT INTO conferencia_zona VALUES ('ac','01007',9,1,2,2,2,2,1,NULL)")
    con.execute("INSERT INTO conferencia_zona VALUES ('ac','01015',2,1,2,2,3,2,0,'[]')")
    con.commit()
    con.close()

    loc = tmp / "locais.sqlite"
    con = sqlite3.connect(loc)
    con.execute(
        "CREATE TABLE secao (uf TEXT, municipio_cd TEXT, municipio TEXT, zona INTEGER, "
        "secao INTEGER, agregada_cd INTEGER, secao_principal INTEGER, local_nr INTEGER, "
        "local TEXT, tipo_local TEXT, endereco TEXT, bairro TEXT, lat REAL, lon REAL, "
        "eleitores INTEGER, eleitores_federal INTEGER)"
    )
    for mun, zona, s in secoes:
        con.execute(
            "INSERT INTO secao VALUES ('AC', ?, 'BUJARI', ?, ?, 1, NULL, 1104, "
            "'ESCOLA X', 'Convencional', 'RUA', 'CENTRO', -9.8, -67.9, 300, 300)",
            (mun, zona, s),
        )
    con.commit()
    con.close()

    apu = tmp / "apuracao.sqlite"
    con = sqlite3.connect(apu)
    con.executescript("""
        CREATE TABLE candidato (numero INTEGER, nome_urna TEXT, eleicao_cd INTEGER,
          cargo_cd INTEGER);
        CREATE TABLE municipio (cd TEXT, ibge TEXT);
        INSERT INTO candidato VALUES (13, 'LULA', 6257, 1), (22, 'FLAVIO BOLSONARO', 6257, 1);
        INSERT INTO municipio VALUES ('01007', '1200138');
        """)
    con.commit()
    con.close()
    return sec, loc, apu


def test_montar_filtra_zona_divergente_e_trata_nulo_tecnico(tmp_path):
    sec, loc, apu = _bancos(tmp_path)
    base = sb.montar(sec, loc, apu, None)
    assert len(base.secoes) == 2
    assert set(base.secoes["mun"]) == {"01007"}
    e = base.excluidas
    assert set(e["motivo"]) == {"zona_divergente_arquivo_incompleto"}
    linha = base.secoes.iloc[0]
    # voto no número 28 (fora da lista) entra como nulo técnico, não como válido
    assert linha["validos"] == 220
    assert linha["nulos"] == 12
    assert linha["soma_votos"] == linha["comparecimento"] == 240
    assert linha["lula_pct"] == pytest.approx(100 * 100 / 220)
    assert linha["fuso"] == 2.0
    assert linha["ibge"] == "1200138"
    cob = base.cobertura
    # coleta completa mesmo com uma zona divergente (ela só sai da análise)
    assert cob["ufs_completas"] == ["AC"]
    assert cob["secoes_validas"] == 2
    ref = sb.secao_ref(linha.to_dict())
    assert ref["uf"] == "AC"
    assert ref["abertura_brasilia"] == "2026-10-04 08:00:01"


# ---------------------------------------------------------------- contrato


CHAVES_TOPO = {
    "titulo",
    "gerado_em",
    "versao_contrato",
    "aviso",
    "fontes",
    "cobertura",
    "candidatos",
    "extremos",
    "clusters",
    "urna",
    "outras",
    "achados",
    "limites",
}
CHAVES_REF = {
    "uf",
    "regiao",
    "municipio",
    "mun_tse",
    "ibge",
    "zona",
    "secao",
    "local",
    "bairro",
    "tipo_local_tse",
    "tipo_local_inferido",
    "lat",
    "lon",
    "modelo_urna",
    "tipo_urna",
    "tipo_arquivo",
    "aptos",
    "comparecimento",
    "validos",
    "lula",
    "flavio",
    "outros",
    "brancos",
    "nulos",
    "lula_pct",
    "flavio_pct",
    "zona_lula_pct",
    "zona_flavio_pct",
    "mun_lula_pct",
    "mun_flavio_pct",
    "abertura_brasilia",
    "encerramento_brasilia",
    "recebido_tse",
    "explicacao",
}


@pytest.fixture(scope="module")
def dados():
    if not JSON_SECOES.exists():
        pytest.skip("secoes.json ainda não gerado")
    return json.loads(JSON_SECOES.read_text(encoding="utf-8"))


def test_json_tem_as_chaves_do_contrato(dados):
    assert set(dados) >= CHAVES_TOPO
    assert dados["versao_contrato"] == "1.0"
    assert isinstance(dados["cobertura"]["parcial"], bool)
    for chave in ("secoes_cs", "secoes_validas", "secoes_com_bu"):
        assert isinstance(dados["cobertura"][chave], int)


def test_json_secao_ref_completo(dados):
    refs = dados["extremos"]["amostras"]["lula"] + dados["clusters"]["menos_provaveis"]
    assert refs
    for r in refs:
        assert set(r) >= CHAVES_REF
        assert r["uf"] == r["uf"].upper()
        assert len(r["mun_tse"]) == 5


def test_json_figuras(dados):
    h = dados["extremos"]["histograma"]
    assert len(h["lula"]) == len(h["bins_pct"]) - 1
    pca = dados["clusters"]["pca"]
    assert pca["colunas"] == ["x", "y", "cluster", "top200", "uf"]
    assert all(len(p) == 5 for p in pca["pontos"])
    assert sum(p[3] for p in pca["pontos"]) == 200
    assert dados["clusters"]["k"] == sc.K
    assert len(dados["clusters"]["componentes"]) == dados["clusters"]["k"]
    assert [b["k"] for b in dados["clusters"]["bic"]] == [3, 4, 5]
    assert dados["clusters"]["escolha_k"]["k"] == sc.K
    assert len(dados["clusters"]["ajuste"]["sementes"]) == 32
    assert "registro" not in dados["urna"]
    assert len(dados["urna"]["reguas"]["itens"]) == 4
    assert dados["urna"]["interpretacao"][-1] == dados["urna"]["reguas"]["leitura"]
    for est in ("dentro_zona", "dentro_local"):
        for p in dados["urna"][est]["pares"]:
            lo, hi = p["flavio_pp"]["ic95"]
            assert lo <= hi
    mapa = dados["extremos"]["mapa"]
    assert mapa["colunas"] == ["lat", "lon", "lula_90", "flavio_90", "secoes"]


def test_json_clusters_cinco_partes(dados):
    cl = dados["clusters"]
    assert cl["features"] == list(sc.PARTES)
    for c in cl["componentes"]:
        soma = sum(c["centro_pct_eleitorado"].values()) + c["terceiros_pct_eleitorado"]
        assert soma == pytest.approx(100.0, abs=0.01)
        assert set(c) >= {"artefato", "padrao_empates", "padrao_zeros", "rotulo"}
    assert set(cl["leitura"]) == {"geografia", "artefatos", "perfis", "geometria"}
    assert set(cl["referencia_nacional"]) == {*sc.PARTES, "terceiros"}
    assert len(cl["empates_por_par"]) == 10
    assert cl["pca"]["base"].startswith("dois componentes principais das 4")
    dg = cl["ajuste"]["diagnostico_convergencia"]
    assert dg["total"] == len(cl["ajuste"]["sementes"]) == 32
    assert dg["sementes"] == sc.N_SEMENTES and dg["inits"] == list(sc.INITS)
    assert 1 <= dg["no_maximo"] <= dg["total"]
    assert dg["apertado"]["tol"] == 1e-6 and dg["apertado"]["max_iter"] == 2000
    adotado = dg["apertado"]["adotado"]
    assert (cl["ajuste"]["tol"] == 1e-6) == adotado
    assert dg["frase"] in cl["estabilidade"]


def test_json_quinze_partes_so_agregados(dados):
    q = dados["clusters"]["variantes"]["quinze_partes"]
    assert len(q["features"]) == 15
    assert not {"pca", "mais_anomalo", "menos_provaveis", "componentes"} & set(q)
    assert q["ajuste"]["sementes"] == 8
    assert [b["k"] for b in q["bic"]] == [3, 4, 5]
    assert q["diagnostico"].startswith("Com as 15 partes")
    assert len(q["grupos"]) == sc.K
    mv = dados["clusters"]["variantes"]["meio_voto"]
    assert len(mv["grupos"]) == sc.K
    sen = dados["clusters"]["sensibilidade"]
    assert set(sen) == {"ari_principal_vs_quinze_partes", "ari_principal_vs_meio_voto"}


def test_json_sem_travessao(dados):
    assert st.PROIBIDO not in json.dumps(dados, ensure_ascii=False)


def test_memorando_sem_travessao(dados):
    assert st.PROIBIDO not in st.memorando(dados)


def test_memorando_sem_registro_e_com_k(dados):
    m = st.memorando(dados)
    assert "Registro (SP)" not in m
    assert f"## B. Mistura gaussiana (k = {dados['clusters']['k']})" in m


def test_voto_por_uf_modelo_soma_e_ordena():
    df = pd.DataFrame(
        {
            "uf": ["sp", "sp", "sp", "ac"],
            "regiao": ["Sudeste", "Sudeste", "Sudeste", "Norte"],
            "modelo_urna": ["UE2022", "UE2013", "UE2022", None],
            "votantes": [100, 80, 120, 50],
            "validos": [90, 70, 110, 40],
            "v13": [30, 40, 50, 10],
            "v22": [60, 30, 60, 30],
            "abstencao": [20, 20, 30, 10],
            "aptos": [120, 100, 150, 60],
        }
    )
    out = su.voto_por_uf_modelo(df)
    assert [(x["uf"], x["modelo"]) for x in out] == [
        ("AC", "sem modelo"),
        ("SP", "UE2013"),
        ("SP", "UE2022"),
    ]
    sp22 = out[2]
    assert sp22["secoes"] == 2 and sp22["validos"] == 200
    assert sp22["flavio"] == 120 and sp22["flavio_pct"] == 60.0
    assert sp22["lula_pct"] == 40.0 and sp22["abstencao_pct"] == 18.52
