"""Comparação 2022 × 2026: campos dos partidos antigos, cadeiras e regiões."""

from __future__ import annotations

import io
import json
import math
import zipfile
from pathlib import Path

import pytest
from apuracao_2026 import tse_cargos
from apuracao_2026.comparacao import (
    BLOCOS,
    CAMPOS_PRES,
    agregar,
    campo_historico,
    eleito,
    fluxo,
    gallagher,
    membros_regionais,
    metricas_presidente,
    por_bloco,
    por_campo,
    proporcionalidade,
    segundo_turno,
    sigla_2026,
    troca_no_segundo_turno,
    trocas_de_bloco,
)
from apuracao_2026.comparacao_texto import dec, mil, pts
from apuracao_2026.dados import classificador

RAIZ = Path(__file__).resolve().parents[1]
CAMPOS_JSON = RAIZ / "apuracao/public/campos.json"

# Recorte da tabela da casa, com as mesmas regras (tucano na centro-esquerda,
# PMB na centro-direita).
CL = classificador(
    {
        "partidos": {
            "PL": "direita",
            "REPUBLICANOS": "direita",
            "NOVO": "direita",
            "UNIÃO": "centro-direita",
            "PP": "centro-direita",
            "PODE": "centro-direita",
            "PRD": "centro-direita",
            "MOBILIZA": "centro-direita",
            "AGIR": "centro-direita",
            "PMB": "centro-direita",
            "DEMOCRATA": "direita",
            "MDB": "centro",
            "PSD": "centro",
            "PSDB": "centro-esquerda",
            "CIDADANIA": "centro-esquerda",
            "SOLIDARIEDADE": "centro-esquerda",
            "PT": "esquerda",
            "PC do B": "esquerda",
            "PCDOB": "esquerda",
        },
        "excecoes": {},
    }
)
UFS_28 = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
    "ZZ",
]


# ---------------------------------------------------------------- partidos


@pytest.mark.parametrize(
    ("sigla", "sucessor", "campo", "via"),
    [
        ("PSC", "PODE", "centro-direita", "sucessor"),
        ("PTB", "PRD", "centro-direita", "sucessor"),
        ("PATRIOTA", "PRD", "centro-direita", "sucessor"),
        ("PROS", "SOLIDARIEDADE", "centro-esquerda", "sucessor"),
        ("PMN", "MOBILIZA", "centro-direita", "sucessor"),
        ("PC do B", "PCDOB", "esquerda", "direto"),
        ("PSDB", "PSDB", "centro-esquerda", "direto"),
        ("UNIÃO", "UNIÃO", "centro-direita", "direto"),
        ("PL", "PL", "direita", "direto"),
    ],
)
def test_campo_dos_partidos_de_2022(sigla, sucessor, campo, via):
    assert sigla_2026(sigla) == sucessor
    assert campo_historico(sigla, CL) == (campo, via)


def test_tabela_da_casa_vence_o_sucessor():
    # PMB está na tabela como centro-direita; o sucessor DEMOCRATA é direita.
    assert sigla_2026("PMB") == "DEMOCRATA"
    assert campo_historico("PMB", CL) == ("centro-direita", "direto")


@pytest.mark.parametrize(
    ("sigla", "sucessor", "campo"),
    [
        ("PSL", "UNIÃO", "centro-direita"),
        ("DEM", "UNIÃO", "centro-direita"),
        ("PRB", "REPUBLICANOS", "direita"),
        ("PR", "PL", "direita"),
        ("PPS", "CIDADANIA", "centro-esquerda"),
        ("PHS", "PODE", "centro-direita"),
        ("PRP", "PRD", "centro-direita"),
        ("PPL", "PCDOB", "esquerda"),
        ("PTC", "AGIR", "centro-direita"),
    ],
)
def test_campo_dos_partidos_de_2018_segue_a_cadeia(sigla, sucessor, campo):
    assert sigla_2026(sigla) == sucessor
    assert campo_historico(sigla, CL)[0] == campo


def test_sigla_desconhecida_fica_indefinida():
    assert campo_historico("XYZ", CL) == ("indefinido", "sem classificação")
    assert campo_historico(None, CL) == ("indefinido", "sem classificação")


@pytest.mark.skipif(not CAMPOS_JSON.exists(), reason="campos.json ausente")
def test_todos_os_partidos_de_2022_tem_campo_na_tabela_real():
    cl = classificador(json.loads(CAMPOS_JSON.read_text(encoding="utf-8")))
    partidos_2022 = [
        "AGIR",
        "AVANTE",
        "CIDADANIA",
        "DC",
        "MDB",
        "NOVO",
        "PATRIOTA",
        "PCB",
        "PCO",
        "PDT",
        "PL",
        "PMB",
        "PMN",
        "PODE",
        "PP",
        "PROS",
        "PRTB",
        "PSB",
        "PSC",
        "PSD",
        "PSDB",
        "PSOL",
        "PSTU",
        "PT",
        "PTB",
        "PV",
        "REDE",
        "REPUBLICANOS",
        "SOLIDARIEDADE",
        "UNIÃO",
        "UP",
        "PC do B",
    ]
    sem = [s for s in partidos_2022 if campo_historico(s, cl)[0] == "indefinido"]
    assert sem == []
    assert campo_historico("PSDB", cl)[0] == "centro-esquerda"


# ---------------------------------------------------------------- cadeiras


@pytest.mark.parametrize(
    ("situacao", "esperado"),
    [
        ("ELEITO", True),
        ("ELEITO POR QP", True),
        ("ELEITO POR MÉDIA", True),
        ("ELEITO POR MEDIA", True),
        (" eleito por qp ", True),
        ("NÃO ELEITO", False),
        ("SUPLENTE", False),
        ("2º TURNO", False),
        ("#NULO#", False),
        ("", False),
        (None, False),
    ],
)
def test_eleito_pela_situacao_do_tse(situacao, esperado):
    assert eleito(situacao) is esperado


def test_segundo_turno_pela_situacao():
    assert segundo_turno("2º TURNO")
    assert not segundo_turno("ELEITO")
    assert not segundo_turno("NÃO ELEITO")


def test_contagem_de_cadeiras_por_campo_e_bloco():
    situacoes = [
        ("PL", "ELEITO POR QP"),
        ("PL", "ELEITO POR MÉDIA"),
        ("PSC", "ELEITO POR QP"),
        ("PT", "ELEITO POR QP"),
        ("PROS", "ELEITO POR MÉDIA"),
        ("MDB", "ELEITO POR QP"),
        ("PT", "SUPLENTE"),
        ("PL", "NÃO ELEITO"),
    ]
    campos = [campo_historico(p, CL)[0] for p, st in situacoes if eleito(st)]
    contagem = por_campo(campos)
    assert contagem == {
        "esquerda": 1,
        "centro-esquerda": 1,
        "centro": 1,
        "centro-direita": 1,
        "direita": 2,
    }
    assert por_bloco(contagem) == {
        "esquerda + centro-esquerda": 2,
        "centro": 1,
        "direita + centro-direita": 3,
    }


def test_trocas_de_bloco_somam_ganhos_dentro_de_cada_uf():
    antes = {
        "AA": {BLOCOS[0]: 3, BLOCOS[1]: 1, BLOCOS[2]: 4},
        "BB": {BLOCOS[0]: 2, BLOCOS[1]: 0, BLOCOS[2]: 0},
    }
    depois = {
        "AA": {BLOCOS[0]: 1, BLOCOS[1]: 1, BLOCOS[2]: 6},
        "BB": {BLOCOS[0]: 1, BLOCOS[1]: 1, BLOCOS[2]: 0},
    }
    trocas = trocas_de_bloco(antes, depois)
    assert trocas["cadeiras"] == 3
    assert trocas["ganhos"][BLOCOS[2]] == 2
    assert trocas["perdas"][BLOCOS[0]] == 3
    with pytest.raises(ValueError):
        trocas_de_bloco({"AA": {BLOCOS[0]: 1}}, {"AA": {BLOCOS[0]: 2}})


def test_fluxo_entre_blocos():
    matriz = fluxo(
        [(BLOCOS[0], BLOCOS[2]), (BLOCOS[0], BLOCOS[2]), (BLOCOS[1], BLOCOS[1])]
    )
    assert matriz[BLOCOS[0]][BLOCOS[2]] == 2
    assert matriz[BLOCOS[1]][BLOCOS[1]] == 1
    assert sum(sum(linha.values()) for linha in matriz.values()) == 3


def test_troca_de_bloco_com_segundo_turno_aberto():
    esq, cen, dir_ = BLOCOS
    assert troca_no_segundo_turno(esq, [dir_, cen]) is True
    assert troca_no_segundo_turno(dir_, [dir_, dir_]) is False
    assert troca_no_segundo_turno(esq, [esq, dir_]) is None
    with pytest.raises(ValueError):
        troca_no_segundo_turno(esq, [])


def test_gallagher_e_proporcionalidade():
    assert math.isclose(gallagher({"A": 50.0, "B": 50.0}, {"A": 60.0, "B": 40.0}), 10.0)
    prop = proporcionalidade({"A": 600, "B": 400, "C": 0}, {"A": 3, "B": 1})
    linhas = {x["chave"]: x for x in prop["linhas"]}
    assert linhas["A"]["votos_por_cadeira"] == 200
    assert linhas["C"]["votos_por_cadeira"] is None
    assert linhas["A"]["cadeiras_menos_votos_pp"] == pytest.approx(15.0)
    assert prop["gallagher_pp"] == pytest.approx(15.0)


# ---------------------------------------------------------------- regiões


def test_membros_regionais_sem_dupla_contagem():
    membros = membros_regionais(UFS_28)
    assert len(membros["Nordeste"]) == 9
    assert len(membros["Norte"]) == 7
    assert len(membros["Centro-Sul"]) == 11
    assert (
        len(membros["Centro-Oeste"]) + len(membros["Sudeste"]) + len(membros["Sul"])
        == 11
    )
    assert membros["Exterior"] == ["ZZ"]
    assert len(membros["Brasil sem exterior"]) == 27
    assert len(membros["Brasil"]) == 28
    for nome, ufs in membros.items():
        assert len(ufs) == len(set(ufs)), nome


def test_agregacao_regional_soma_cada_uf_uma_vez():
    linhas = {uf: {"x": 1, "y": i} for i, uf in enumerate(UFS_28)}
    soma = agregar(linhas, ("x", "y"), membros_regionais(UFS_28))
    assert soma["Nordeste"]["x"] == 9
    assert soma["Norte"]["x"] == 7
    assert soma["Brasil"]["x"] == 28
    assert soma["Brasil"]["y"] == sum(range(28))
    partes = sum(soma[g]["y"] for g in ("Nordeste", "Norte", "Centro-Sul", "Exterior"))
    assert partes == soma["Brasil"]["y"]
    with pytest.raises(ValueError):
        agregar({"AC": {"x": None}}, ("x",), {"Norte": ["AC"]})


def _linha_presidente(**sobrescreve: int) -> dict[str, int]:
    base = dict.fromkeys(CAMPOS_PRES, 0)
    base.update(
        e26=1000,
        c26=800,
        a26=200,
        vv26=760,
        vb26=20,
        vn26=20,
        flavio=380,
        lula26=342,
        cury=19,
        renan=10,
        caiado=7,
        outros26=2,
        e22_1=980,
        c22_1=790,
        a22_1=190,
        vv22_1=750,
        vb22_1=20,
        vn22_1=20,
        bolsonaro_1=330,
        lula22_1=360,
        ciro_1=30,
        tebet_1=25,
        outros22_1=5,
        e22_2=980,
        c22_2=780,
        a22_2=200,
        vv22_2=740,
        vb22_2=15,
        vn22_2=25,
        bolsonaro_2=370,
        lula22_2=370,
    )
    base.update(sobrescreve)
    return base


def test_metricas_presidente_contra_os_dois_turnos():
    m = metricas_presidente(_linha_presidente())
    assert m["pct_2026"]["flavio"] == pytest.approx(50.0)
    assert m["pct_2022_2t"]["bolsonaro"] == pytest.approx(50.0)
    assert m["comparacao"]["vs_1t"]["direita_votos"] == 50
    assert m["comparacao"]["vs_2t"]["direita_votos"] == 10
    assert m["comparacao"]["vs_1t"]["terceiros_votos"] == 38 - 60
    assert m["votos_2026"]["terceiros"] == 38
    assert not m["flavio_supera_bolsonaro_2t"]
    assert m["flavio_menos_bolsonaro_2t_votos_equivalentes"] == 0
    assert m["pct_2026"]["comparecimento"] == pytest.approx(80.0)
    assert m["pct_2026"]["brancos"] == pytest.approx(2.5)
    m2 = metricas_presidente(_linha_presidente(flavio=400, lula26=322))
    assert m2["flavio_supera_bolsonaro_2t"]
    assert m2["flavio_menos_bolsonaro_2t_votos_equivalentes"] == 20


# ---------------------------------------------------------------- leitura do TSE

CABECALHO = (
    "DT_GERACAO;HH_GERACAO;ANO_ELEICAO;CD_TIPO_ELEICAO;NM_TIPO_ELEICAO;NR_TURNO;"
    "CD_ELEICAO;DS_ELEICAO;DT_ELEICAO;TP_ABRANGENCIA;SG_UF;SG_UE;NM_UE;CD_MUNICIPIO;"
    "NM_MUNICIPIO;NR_ZONA;CD_CARGO;DS_CARGO;SQ_CANDIDATO;NR_CANDIDATO;NM_CANDIDATO;"
    "NM_URNA_CANDIDATO;NR_PARTIDO;SG_PARTIDO;SG_FEDERACAO;QT_VOTOS_NOMINAIS;"
    "QT_VOTOS_NOMINAIS_VALIDOS;DS_SIT_TOT_TURNO"
)


def _linha_csv(tipo, eleicao, zona, cargo, sq, nome, partido, votos, situacao):
    campos = [
        "26/08/2026",
        "03:16:39",
        "2022",
        str(tipo),
        "Eleição",
        "1",
        str(eleicao),
        "ELEIÇÕES GERAIS",
        "02/10/2022",
        "E",
        "XX",
        "XX",
        "ESTADO",
        "1",
        "SÃO JOÃO",
        str(zona),
        str(cargo),
        "Deputado",
        sq,
        "1234",
        nome,
        nome,
        "22",
        partido,
        "#NULO#",
        str(votos),
        str(votos),
        situacao,
    ]
    return ";".join(c if c.isdigit() else f'"{c}"' for c in campos)


def test_leitura_soma_zonas_e_separa_suplementar(tmp_path):
    linhas = [
        CABECALHO,
        _linha_csv(2, 546, 1, 6, "1", "FULANA", "PL", 100, "ELEITO POR QP"),
        _linha_csv(2, 546, 2, 6, "1", "FULANA", "PL", 50, "ELEITO POR QP"),
        _linha_csv(2, 546, 1, 7, "2", "BELTRANO", "PT", 70, "SUPLENTE"),
        _linha_csv(1, 6278, 1, 3, "3", "CICLANO", "PSD", 9, "NÃO ELEITO"),
        _linha_csv(2, 546, 1, 5, "4", "OUTRO", "MDB", 30, "ELEITO"),
    ]
    caminho = tmp_path / "votacao_candidato_munzona_2022.zip"
    with zipfile.ZipFile(caminho, "w") as zf:
        zf.writestr(
            "votacao_candidato_munzona_2022_XX.csv", "\n".join(linhas).encode("latin-1")
        )
    lidas = tse_cargos.ler_candidaturas(caminho, 2022, {"XX": {3, 6}})
    assert set(lidas) == {(546, "1", 1), (6278, "3", 1)}
    fulana = lidas[(546, "1", 1)]
    assert fulana.votos == 150
    assert fulana.nome_urna == "FULANA"
    assert eleito(fulana.situacao)
    assert fulana.federacao is None
    assert lidas[(6278, "3", 1)].suplementar


def test_leitura_recusa_situacao_divergente(tmp_path):
    linhas = [
        CABECALHO,
        _linha_csv(2, 546, 1, 6, "1", "FULANA", "PL", 100, "ELEITO POR QP"),
        _linha_csv(2, 546, 2, 6, "1", "FULANA", "PL", 50, "SUPLENTE"),
    ]
    caminho = tmp_path / "votacao_candidato_munzona_2022.zip"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(
            "votacao_candidato_munzona_2022_XX.csv", "\n".join(linhas).encode("latin-1")
        )
    caminho.write_bytes(buffer.getvalue())
    with pytest.raises(ValueError, match="divergente"):
        tse_cargos.ler_candidaturas(caminho, 2022, {"XX": {6}})


# ---------------------------------------------------------------- texto


def test_formatos_do_memorando():
    assert dec(1.865004) == "1,87"
    assert dec(-3.2679, 2, True) == "−3,27"
    assert dec(0.25, 2, True) == "+0,25"
    assert mil(5032158, True) == "+5.032.158"
    assert mil(-2101851) == "−2.101.851"
    assert pts(1.87) == "1,87 ponto"
    assert pts(-0.14, 2, True) == "−0,14 ponto"
    assert pts(7.098) == "7,10 pontos"
