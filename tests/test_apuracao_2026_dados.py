"""Partes puras dos dados da apuração de 2026, sem o banco de 10 GB."""

import json
import zipfile
from pathlib import Path

import pytest
from apuracao_2026 import dados as D
from apuracao_2026 import presidente as P
from apuracao_2026 import tse2022 as T

ROOT = Path(__file__).resolve().parents[1]
EXTERIOR = ROOT / "apuracao/public/exterior_cidades.json"


# ---------------------------------------------------------------- regiões


def test_regiao_de_todas_as_ufs_e_do_exterior():
    assert len(D.REGIAO_UF) == 28
    assert D.regiao("SP") == "Sudeste"
    assert D.regiao("ba") == "Nordeste"
    assert D.regiao("zz") == "Exterior"
    contagem = {r: sum(1 for v in D.REGIAO_UF.values() if v == r) for r in D.REGIOES}
    assert contagem == {
        "Norte": 7,
        "Nordeste": 9,
        "Centro-Oeste": 4,
        "Sudeste": 4,
        "Sul": 3,
    }


def test_centro_sul_soma_sudeste_sul_e_centro_oeste():
    centro_sul = {uf for uf in D.REGIAO_UF if D.grupo_regional(uf) == "Centro-Sul"}
    assert centro_sul == {
        "df",
        "go",
        "ms",
        "mt",
        "es",
        "mg",
        "rj",
        "sp",
        "pr",
        "rs",
        "sc",
    }
    assert D.grupo_regional("PE") == "Nordeste"
    assert D.grupo_regional("am") == "Norte"
    assert D.grupo_regional("ZZ") == "Exterior"


def test_regiao_desconhecida_e_erro():
    with pytest.raises(KeyError):
        D.regiao("xx")


# ---------------------------------------------------------------- continentes


def test_tabela_de_continentes_cobre_as_186_cidades_do_exterior():
    cidades = json.loads(EXTERIOR.read_text(encoding="utf-8"))
    assert len(cidades) == 186
    for cidade in cidades:
        assert D.continente(cidade["pais"]) in D.CONTINENTES
        assert D.pais_nome(cidade["pais"])


def test_continentes_declarados_pelo_m49():
    assert D.continente("US") == D.AMERICA_NORTE
    assert D.continente("ca") == D.AMERICA_NORTE
    assert D.continente("MX") == D.AMERICA_CENTRAL
    assert D.continente("GF") == D.AMERICA_SUL
    assert D.continente("TR") == D.ASIA
    assert D.continente("CY") == D.ASIA
    assert D.continente("RU") == D.EUROPA
    assert D.continente("NZ") == D.OCEANIA
    assert D.continente("EG") == D.AFRICA
    assert D.pais_nome("PT") == "Portugal"
    assert set(D.CONTINENTES) == {c for _, c in D.PAISES.values()}


def test_pais_desconhecido_e_erro_e_nao_palpite():
    with pytest.raises(KeyError):
        D.continente("ZZ")


# ---------------------------------------------------------------- contas


def test_num_le_o_formato_do_tse():
    assert D.num("47,03") == pytest.approx(47.03)
    assert D.num("1.234,5") == pytest.approx(1234.5)
    assert D.num("123") == 123
    assert D.num("3.5") == pytest.approx(3.5)
    assert D.num("") is None
    assert D.num(None) is None
    assert D.num(7) == 7


def test_pct_e_dif():
    assert D.pct(1, 4) == 25.0
    assert D.pct(1, 0) is None
    assert D.pct(None, 10) is None
    assert D.dif(47.03, 43.2) == pytest.approx(3.83)
    assert D.dif(None, 1.0) is None


def test_swing_com_os_totais_nacionais():
    # Flávio 2026 contra Bolsonaro no 1º turno de 2022 (totais do TSE).
    s = D.swing(56_104_503, 119_300_788, 51_072_345, 118_229_719)
    assert s["pct_a"] == pytest.approx(47.0278, abs=1e-4)
    assert s["pct_b"] == pytest.approx(43.1976, abs=1e-4)
    assert s["pp"] == pytest.approx(3.8302, abs=1e-4)
    assert s["votos"] == 5_032_158


def test_swing_sem_um_dos_lados():
    s = D.swing(10, 100, None, None)
    assert s["pp"] is None
    assert s["votos"] is None


def test_percentil_interpola_como_o_numpy():
    assert D.percentil([1, 2, 3, 4], 50) == pytest.approx(2.5)
    assert D.percentil(list(range(1, 101)), 95) == pytest.approx(95.05)
    assert D.percentil([7], 95) == 7.0
    assert D.percentil([], 50) is None
    with pytest.raises(ValueError):
        D.percentil([1, 2], 101)


def test_comparar_flavio_contra_bolsonaro_e_lula_contra_lula():
    b26 = {
        "votos": {"flavio": 60, "lula": 30, "terceiros": 10},
        "pct": {"flavio": 60.0, "lula": 30.0, "terceiros": 10.0},
        "validos": 100,
        "pct_comparecimento": 80.0,
        "eleitores": 1000,
    }
    t1 = {
        "votos": {"bolsonaro": 50, "lula": 40, "terceiros": 10},
        "pct": {"bolsonaro": 50.0, "lula": 40.0, "terceiros": 10.0},
        "validos": 100,
        "pct_comparecimento": 79.0,
        "eleitores": 950,
    }
    t2 = {
        "votos": {"bolsonaro": 55, "lula": 45, "terceiros": 0},
        "pct": {"bolsonaro": 55.0, "lula": 45.0, "terceiros": 0.0},
        "validos": 100,
        "pct_comparecimento": 81.0,
        "eleitores": 950,
    }
    c = P.comparar(b26, t1, t2)
    assert c["flavio_vs_bolsonaro_1t"]["pp"] == 10.0
    assert c["lula_vs_lula_1t"]["votos"] == -10
    assert c["margem_flavio_lula_2026_pp"] == 30.0
    assert c["virada_margem_vs_1t_pp"] == 20.0
    assert c["virada_margem_vs_2t_pp"] == 20.0
    assert c["comparecimento_vs_1t_pp"] == 1.0
    assert c["eleitores_variacao"] == 50


def test_faixas_de_lula_2022_somam_votos_e_ignoram_incompletos():
    base = {
        "completo": True,
        "eleitores": 100,
        "comparecimento": 80,
        "validos": 70,
        "flavio": 40,
        "lula": 25,
        "terceiros": 5,
        "eleitores_2022": 100,
        "comparecimento_2022": 78,
        "validos_2022_1t": 70,
        "bolsonaro_2022_1t": 35,
        "lula_2022_1t": 30,
    }
    linhas = [
        {**base, "pct_lula_2022_1t": 20.0},
        {**base, "pct_lula_2022_1t": 25.0},
        {**base, "pct_lula_2022_1t": 80.0, "completo": False},
    ]
    faixas = P.por_faixa_lula_2022(linhas)
    primeira = faixas[0]
    assert primeira["municipios"] == 2
    assert primeira["flavio"] == 80
    assert primeira["delta_votos_flavio"] == 10
    assert primeira["swing_lula_pp"] == pytest.approx(-7.1429, abs=1e-4)
    assert primeira["delta_comparecimento_pp"] == pytest.approx(2.0)
    assert faixas[-1]["municipios"] == 0


# ---------------------------------------------------------------- tempo


def test_brt_e_hora():
    assert D.brt("2026-10-04T22:14:08.000Z") == "2026-10-04 19:14:08"
    assert D.hora_brt("2026-10-05T02:59:00Z") == "2026-10-04 23h"
    assert D.minutos("2026-10-04T21:48:59Z", "2026-10-04T22:14:08Z") == pytest.approx(
        25.15
    )
    with pytest.raises(ValueError):
        D.utc("2026-10-04T22:14:08")


def test_deslocamento_e_fuso_de_wellington_e_katmandu():
    wellington = D.deslocamento_horas(
        "05/10/2026", "09:19:47", "2026-10-04T20:21:13.000Z"
    )
    assert wellington == pytest.approx(15.9761, abs=1e-4)
    assert D.fuso_inferido(wellington) == 13.0
    katmandu = D.deslocamento_horas(
        "05/10/2026", "04:59:11", "2026-10-04T23:30:08.000Z"
    )
    assert D.fuso_inferido(katmandu) is None
    acre = D.deslocamento_horas("04/10/2026", "18:54:23", "2026-10-04T23:54:39.000Z")
    assert D.fuso_inferido(acre) == -5.0
    assert D.deslocamento_horas(None, None, "2026-10-04T20:00:00Z") is None


# ---------------------------------------------------------------- versões e travamentos


def _snap(i, gerado, st=0, ts=100, capturado=None):
    return {
        "id": i,
        "gerado_em": gerado,
        "capturado_em": capturado or gerado,
        "st": st,
        "ts": ts,
    }


def test_versoes_genuinas_descartam_copia_antiga_e_repeticao():
    snaps = [
        _snap(1, "2026-10-04T20:00:00Z", 10),
        _snap(2, "2026-10-04T20:05:00Z", 20),
        _snap(3, "2026-10-04T20:03:00Z", 15),  # cópia antiga servida depois
        _snap(4, "2026-10-04T20:05:00Z", 20),  # mesma geração
        _snap(5, "2026-10-04T20:09:00Z", 30),
    ]
    assert [s["id"] for s in D.versoes_genuinas(snaps)] == [1, 2, 5]
    classes = dict(D.classificar_copias(snaps))
    assert classes == {
        1: "primeira",
        2: "nova",
        3: "antiga",
        4: "mesma_geracao",
        5: "nova",
    }


def test_versoes_genuinas_ordenam_pela_captura():
    snaps = [_snap(9, "2026-10-04T20:09:00Z"), _snap(1, "2026-10-04T20:00:00Z")]
    assert [s["id"] for s in D.versoes_genuinas(snaps)] == [1, 9]


def test_travamentos_em_serie_sintetica():
    versoes = [
        _snap(1, "2026-10-04T20:00:00Z", 0),  # antes de começar: não conta
        _snap(2, "2026-10-04T20:20:00Z", 10),
        _snap(3, "2026-10-04T20:28:00Z", 20),  # 8 min exatos: não passa do limiar
        _snap(4, "2026-10-04T20:53:00Z", 60),  # 25 min parado
        _snap(5, "2026-10-04T20:55:00Z", 100),
        _snap(6, "2026-10-04T23:00:00Z", 100),  # completo: não é travamento
    ]
    lacunas = D.travamentos(versoes, 8)
    assert len(lacunas) == 1
    lac = lacunas[0]
    assert lac["minutos"] == 25.0
    assert lac["st_de"] == 20
    assert lac["secoes_no_salto"] == 40
    assert lac["pst_de"] == 20.0
    assert lac["de_brt"] == "2026-10-04 17:28:00"


def test_lacunas_da_uniao_de_varios_arquivos():
    tempos = [
        "2026-10-04T22:00:00Z",
        "2026-10-04T22:05:00Z",
        "2026-10-04T22:05:00Z",
        "2026-10-04T22:32:47Z",
        "2026-10-04T23:01:55Z",
    ]
    lacunas = D.lacunas_da_uniao(tempos, 8)
    assert [x["minutos"] for x in lacunas] == [27.78, 29.13]


def test_estado_em_escolhe_a_ultima_ate_o_instante():
    versoes = [
        _snap(1, "2026-10-04T21:00:00Z", 10, capturado="2026-10-04T21:00:30Z"),
        _snap(2, "2026-10-04T21:10:00Z", 20, capturado="2026-10-04T21:10:40Z"),
    ]
    instante = D.utc("2026-10-04T21:10:10Z")
    assert D.estado_em(versoes, instante, "gerado_em")["id"] == 2
    assert D.estado_em(versoes, instante, "capturado_em")["id"] == 1
    assert D.estado_em(versoes, D.utc("2026-10-04T20:00:00Z")) is None


# ---------------------------------------------------------------- arquivos do TSE


def test_resultado_do_documento_le_totais_partidos_e_candidaturas():
    doc = {
        "s": {"st": "5", "ts": "6"},
        "e": {"te": "1000", "c": "800", "a": "200"},
        "v": {"vv": "750", "vb": "20", "vn": "29", "vnt": "1", "tvn": "30"},
        "carg": [
            {
                "agr": [
                    {
                        "n": "1",
                        "par": [
                            {
                                "n": "22",
                                "sg": "PL",
                                "tvtn": "400",
                                "tvtl": "0",
                                "cand": [{"sqcand": "11", "vap": "400"}],
                            },
                            {
                                "n": "13",
                                "sg": "PT",
                                "tvtn": "350",
                                "cand": [{"sqcand": "22", "vap": "350"}],
                            },
                        ],
                    }
                ]
            }
        ],
    }
    r = D.resultado_do_documento(doc)
    assert r["st"] == 5
    assert r["comparecimento"] == 800
    assert r["tvn"] == 30
    assert r["votos"] == {"11": 400, "22": 350}
    assert [p["sigla"] for p in r["partidos"]] == ["PL", "PT"]
    assert r["partidos"][1]["tvtl"] == 0


def test_entradas_ab():
    doc = {
        "abr": [
            {
                "tpabr": "br",
                "cdabr": "br",
                "dt": "05/10/2026",
                "ht": "09:19:47",
                "s": {"st": "9"},
            },
            {"tpabr": "mun", "cdabr": "07471", "s": {"st": "61", "ts": "61"}},
        ]
    }
    e = D.entradas_ab(doc)
    assert e["br"]["ht"] == "09:19:47"
    assert e["07471"]["st"] == 61
    assert e["07471"]["tpabr"] == "mun"


# ---------------------------------------------------------------- tabelas e campos


def test_colunar_e_extremos():
    linhas = [
        {"cd": "1", "v": 3.0, "eleitores": 50_000},
        {"cd": "2", "v": -1.0, "eleitores": 5_000},
        {"cd": "3", "v": None, "eleitores": 90_000},
        {"cd": "4", "v": 9.0, "eleitores": 20_000},
    ]
    tabela = D.colunar(["cd", "v"], linhas)
    assert tabela["colunas"] == ["cd", "v"]
    assert tabela["linhas"][2] == ["3", None]
    ext = D.extremos(linhas, "v", 2, ["cd"])
    assert [x["cd"] for x in ext["maiores"]] == ["4", "1"]
    assert [x["cd"] for x in ext["menores"]] == ["2", "1"]
    filtrado = D.extremos(linhas, "v", 1, ["cd"], {"eleitores": 10_000})
    assert filtrado["menores"][0]["cd"] == "1"


def test_campo_de_respeita_excecao_partido_e_federacao():
    cl = D.classificador(
        {
            "partidos": {
                "PL": "direita",
                "psdb/cidadania": "centro-esquerda",
                "X": "nada",
            },
            "excecoes": {"99": "centro-direita"},
        }
    )
    assert "X" not in cl["partidos"]
    assert D.campo_de(cl, "99", "PL") == "centro-direita"
    assert D.campo_de(cl, None, "pl") == "direita"
    assert D.campo_de(cl, None, "PSDB", "PSDB/CIDADANIA") == "centro-esquerda"
    assert D.campo_de(cl, "1", "AGIR") == "indefinido"
    assert D.bloco_de("centro-direita") == "direita + centro-direita"
    assert D.bloco_de("centro-esquerda") == "esquerda + centro-esquerda"
    assert D.bloco_de("centro") == "centro"


# ---------------------------------------------------------------- 2022 em streaming


def _zip(tmp_path: Path, membro: str, linhas: list[str]) -> Path:
    caminho = tmp_path / "fonte.zip"
    with zipfile.ZipFile(caminho, "w") as zf:
        zf.writestr(membro, ("\n".join(linhas) + "\n").encode("latin-1"))
    return caminho


def test_munzona_soma_zonas_e_turnos_por_municipio(tmp_path):
    cab = (
        '"SG_UF";"CD_MUNICIPIO";"NM_MUNICIPIO";"NR_ZONA";"CD_CARGO";"NR_TURNO";'
        '"NR_CANDIDATO";"QT_VOTOS_NOMINAIS_VALIDOS"'
    )
    linhas = [
        cab,
        '"SP";71072;"SÃO PAULO";1;1;1;22;100',
        '"SP";71072;"SÃO PAULO";2;1;1;22;50',
        '"SP";71072;"SÃO PAULO";2;1;1;13;70',
        '"SP";71072;"SÃO PAULO";2;1;1;12;5',
        '"SP";71072;"SÃO PAULO";1;1;2;13;90',
        '"SP";71072;"SÃO PAULO";1;3;1;45;999',
    ]
    mun, zonas = T.ler_munzona(_zip(tmp_path, T.MEMBRO_MUNZONA, linhas))
    sp = mun[71072]
    assert sp["uf"] == "sp"
    assert sp["nome"] == "SÃO PAULO"
    assert sp["t1"] == {"22": 150, "13": 70, "12": 5, "validos": 225}
    assert sp["t2"] == {"13": 90, "validos": 90}
    assert zonas[(71072, 2)] == {"22": 50, "13": 70, "validos": 125}


def test_detalhe_agrega_secoes_de_presidente(tmp_path):
    cab = (
        '"NR_TURNO";"CD_MUNICIPIO";"NR_ZONA";"CD_CARGO";"QT_APTOS";'
        '"QT_COMPARECIMENTO";"QT_VOTOS_BRANCOS";"QT_VOTOS_NULOS";"NM_LOCAL_VOTACAO"'
    )
    linhas = [
        cab,
        '1;1392;9;1;339;266;4;12;"ESCOLA; COM PONTO E VÍRGULA"',
        '1;1392;9;1;300;250;2;3;"OUTRA"',
        '1;1392;9;3;339;266;4;12;"GOVERNADOR NÃO ENTRA"',
        '2;1392;9;1;339;270;1;1;"SEGUNDO TURNO"',
    ]
    por_mun, por_zona = T.ler_detalhe(_zip(tmp_path, T.MEMBRO_DETALHE, linhas))
    assert por_mun[1][1392] == {
        "aptos": 639,
        "comparecimento": 516,
        "brancos": 6,
        "nulos": 15,
    }
    assert por_mun[2][1392]["comparecimento"] == 270
    assert por_zona[(1392, 9)]["aptos"] == 639


def test_api_2022_le_os_dois_turnos(tmp_path):
    for eleicao, lula in (("544", "40"), ("545", "45")):
        doc = {
            "e": "100",
            "c": "80",
            "a": "20",
            "vv": "75",
            "vb": "2",
            "tvn": "3",
            "s": "4",
            "cand": [
                {"n": "13", "nm": "LULA", "vap": lula},
                {"n": "22", "nm": "JAIR BOLSONARO", "vap": "30"},
            ],
        }
        (tmp_path / f"ac-c0001-e000{eleicao}-r.json").write_text(
            json.dumps(doc), "utf-8"
        )
    r = T.ler_api(tmp_path, ["ac"])
    assert r["ac"][1]["votos"] == {"13": 40, "22": 30}
    assert r["ac"][2]["votos"]["13"] == 45
    bloco = P.bloco_2022(r["ac"][1])
    assert bloco["votos"]["terceiros"] == 5
    assert bloco["pct_comparecimento"] == 80.0
