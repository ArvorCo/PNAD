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
    aj = sc.ajustar_melhor(x, 2, sementes=(1, 2, 3), n_init=1)
    lls = [r["loglik_media"] for r in aj.log]
    assert [r["semente"] for r in aj.log] == [1, 2, 3]
    assert aj.gm.score(x) == pytest.approx(max(lls), abs=1e-4)
    assert aj.semente in (1, 2, 3) and aj.semente_segundo in (1, 2, 3)
    assert aj.semente != aj.semente_segundo
    assert len(aj.todos) == 3


def test_k_principal_e_tres_com_bic_de_tres_a_cinco():
    assert sc.K == 3
    assert sc.K_TABELA == (3, 4, 5)
    assert sc.ESCOLHA_K["k"] == 3 and sc.ESCOLHA_K["anterior"] == 4
    assert len(sc.SEMENTES) == sc.N_SEMENTES == 8


def test_separacao_acha_o_corte():
    score = np.array([-3.0, -2.5, -2.0, 1.0, 1.5, 2.0])
    zero = np.array([True, True, True, False, False, False])
    acerto, corte = sc.separacao(score, zero)
    assert acerto == pytest.approx(100.0)
    assert -2.0 <= corte < 1.0
    # o lado não importa: zeros à direita dão o mesmo acerto
    assert sc.separacao(-score, zero)[0] == pytest.approx(100.0)
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
    assert dados["clusters"]["k"] == 3
    assert len(dados["clusters"]["componentes"]) == dados["clusters"]["k"]
    assert [b["k"] for b in dados["clusters"]["bic"]] == [3, 4, 5]
    assert dados["clusters"]["escolha_k"]["k"] == 3
    assert len(dados["clusters"]["ajuste"]["sementes"]) == 8
    assert "registro" not in dados["urna"]
    assert len(dados["urna"]["reguas"]["itens"]) == 4
    assert dados["urna"]["interpretacao"][-1] == dados["urna"]["reguas"]["leitura"]
    for est in ("dentro_zona", "dentro_local"):
        for p in dados["urna"][est]["pares"]:
            lo, hi = p["flavio_pp"]["ic95"]
            assert lo <= hi
    mapa = dados["extremos"]["mapa"]
    assert mapa["colunas"] == ["lat", "lon", "lula_90", "flavio_90", "secoes"]


def test_json_sem_travessao(dados):
    assert st.PROIBIDO not in json.dumps(dados, ensure_ascii=False)


def test_memorando_sem_travessao(dados):
    assert st.PROIBIDO not in st.memorando(dados)


def test_memorando_sem_registro_e_com_k(dados):
    m = st.memorando(dados)
    assert "Registro (SP)" not in m
    assert f"## B. Mistura gaussiana (k = {dados['clusters']['k']})" in m
