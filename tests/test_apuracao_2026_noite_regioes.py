"""A noite por região e os estados lentos: partes puras, com fixtures pequenas."""

import sqlite3

import pytest
from apuracao_2026 import lentidao as L
from apuracao_2026 import lentidao_dados as LD
from apuracao_2026 import lentidao_fontes as LF
from apuracao_2026 import noite_regioes as NR

UFS_FIXTURE = {"am": "Norte", "ba": "Nordeste", "df": "Centro-Oeste", "sp": "Sudeste"}


def _v(hora: str, st: int, ts: int, vv: int, fl: int, lu: int) -> dict:
    """Versão de arquivo de UF com a hora de Brasília `HH:MM:SS` de 04/10/2026."""
    h, m, s = (int(x) for x in hora.split(":"))
    dia = 4 + (h + 3) // 24
    return {
        "gerado": f"2026-10-{dia:02d}T{(h + 3) % 24:02d}:{m:02d}:{s:02d}Z",
        "st": st,
        "ts": ts,
        "vv": vv,
        "flavio": fl,
        "lula": lu,
    }


@pytest.fixture
def series():
    # Seis arquivos, um por região. O Sudeste e o Sul chegam cedo e são de Flávio;
    # o Nordeste chega tarde e é de Lula.
    return {
        "sp": [
            _v("16:00:00", 0, 10, 0, 0, 0),
            _v("17:20:00", 5, 10, 500, 300, 150),
            _v("17:40:00", 10, 10, 1000, 560, 340),
        ],
        "rs": [
            _v("16:00:00", 0, 4, 0, 0, 0),
            _v("17:21:00", 4, 4, 400, 260, 120),
        ],
        "df": [
            _v("16:00:00", 0, 2, 0, 0, 0),
            _v("17:25:00", 2, 2, 200, 120, 60),
        ],
        "am": [
            _v("16:00:00", 0, 2, 0, 0, 0),
            _v("17:30:00", 1, 2, 100, 50, 40),
            _v("18:30:00", 2, 2, 200, 90, 100),
        ],
        "ba": [
            _v("16:00:00", 0, 8, 0, 0, 0),
            _v("17:35:00", 2, 8, 200, 60, 130),
            _v("18:10:00", 8, 8, 800, 200, 560),
        ],
        "zz": [
            _v("16:00:00", 0, 1, 0, 0, 0),
            _v("17:22:00", 1, 1, 50, 20, 25),
        ],
    }


@pytest.fixture
def nacional():
    # O nacional parou entre 17:30 e 18:20 e mostrou, às 18:20, o retrato das 17:40.
    return [
        _v("17:00:00", 0, 27, 0, 0, 0),
        _v("17:30:00", 13, 27, 1300, 790, 435),
        _v("18:20:00", 20, 27, 2000, 1160, 760),
        _v("18:40:00", 27, 27, 2850, 1400, 1135),
        _v("23:00:00", 27, 27, 2850, 1400, 1135),
    ]


INICIO = "2026-10-04T20:00:00Z"
FIM = "2026-10-04T22:00:00Z"


def test_totais_e_contribuicao_somam_a_diferenca(series):
    tot = NR.totais_por_regiao(series)
    assert tot["Sudeste"]["ts"] == 10 and tot["Nordeste"]["vv"] == 800
    c = NR.contribuicao_final(tot)
    soma = sum(r["votos"] for r in c["regioes"].values())
    assert (
        soma
        == c["diferenca_votos"]
        == (560 + 260 + 120 + 90 + 200 + 20) - (340 + 120 + 60 + 100 + 560 + 25)
    )
    assert c["regioes"]["Nordeste"]["votos"] == -360
    pp = sum(r["pp_dos_validos_do_pais"] for r in c["regioes"].values())
    assert pp == pytest.approx(c["diferenca_pp"], abs=0.01)


def test_grade_lotes_e_minutos_fecham_com_o_final(series):
    pontos = NR.grade(series, INICIO, FIM)
    assert len(pontos) == 121
    tot = NR.totais_por_regiao(series)
    fim = pontos[-1][1]
    for r in NR.REGIOES_NOITE:
        assert fim[r]["vv"] == tot[r]["vv"]
    lts = NR.lotes(pontos, 5)
    assert sum(x["vv"] for x in lts) == sum(v["vv"] for v in tot.values())
    reg, nac = NR.tabela_minutos(pontos, tot)
    cols = nac["colunas"]
    linhas = [dict(zip(cols, x, strict=True)) for x in nac["linhas"]]
    assert sum(x["d_vv"] for x in linhas) == 2650
    l1730 = next(x for x in linhas if x["hora_brt"] == "2026-10-04 17:30")
    # Às 17:30 só SP (500), RS, DF, AM (100) e exterior tinham votos; BA ainda não.
    assert l1730["vv"] == 500 + 400 + 200 + 100 + 50
    assert l1730["dif_pp_peso_final"] is None
    l1740 = next(x for x in linhas if x["hora_brt"] == "2026-10-04 17:40")
    assert l1740["dif_pp_peso_final"] is not None
    ultimo = linhas[-1]
    assert ultimo["dif_pp"] == pytest.approx(ultimo["dif_pp_peso_final"], abs=1e-6)
    rc = reg["colunas"]
    ne = [
        dict(zip(rc, x, strict=True))
        for x in reg["linhas"]
        if x[rc.index("regiao")] == "Nordeste"
    ]
    lote_ba = next(x for x in ne if x["hora_brt"] == "2026-10-04 18:10")
    assert lote_ba["d_vv"] == 600 and lote_ba["lote_pct_lula"] == pytest.approx(
        100 * 430 / 600, abs=0.01
    )
    assert lote_ba["parcela_do_lote_pct"] == 100.0


def test_marcos_das_regioes(series):
    tot = NR.totais_por_regiao(series)
    m = NR.marcos_regioes(series, tot)
    assert m["Sudeste"]["50"] == "2026-10-04 17:20:00"
    assert m["Sudeste"]["100"] == "2026-10-04 17:40:00"
    assert m["Nordeste"]["50"] == "2026-10-04 18:10:00"
    assert m["Norte"]["90"] == "2026-10-04 18:30:00"
    # País: 27 seções; 50% = 14 seções, alcançadas às 17:35 (5+4+2+1+1+2 = 15).
    assert m["Brasil"]["50"] == "2026-10-04 17:35:00"
    assert m["Brasil"]["100"] == "2026-10-04 18:30:00"


def test_lideranca_e_decomposicao(series):
    pontos = NR.grade(series, INICIO, FIM)
    tot = NR.totais_por_regiao(series)
    _, nac = NR.tabela_minutos(pontos, tot)
    lid = NR.lideranca(nac)
    assert lid["virada"] is False
    assert lid["final"]["votos"] == 1250 - 1205
    d = NR.decomposicao(nac)
    assert d["queda_pp"] == pytest.approx(
        d["entre_regioes_pp"] + d["dentro_das_regioes_pp"], abs=1e-3
    )


def test_padronizada_pondera_pelo_peso_final():
    tot = {r: {"ts": 1, "vv": 0, "flavio": 0, "lula": 0} for r in NR.REGIOES_NOITE}
    tot["Sudeste"]["vv"], tot["Nordeste"]["vv"] = 600, 400
    for r in ("Norte", "Centro-Oeste", "Sul", "Exterior"):
        tot[r]["vv"] = 0
    est = {r: {"st": 1, "vv": 10, "flavio": 5, "lula": 5} for r in NR.REGIOES_NOITE}
    est["Sudeste"] = {"st": 1, "vv": 100, "flavio": 60, "lula": 30}
    est["Nordeste"] = {"st": 1, "vv": 10, "flavio": 2, "lula": 8}
    # 0,6 × 30% + 0,4 × (−60%) = −6 pontos
    assert NR.padronizada(est, tot) == pytest.approx(-6.0)
    est["Sul"]["vv"] = 0
    assert NR.padronizada(est, tot) is None


def test_nordeste_passa_a_ser_o_que_falta(series):
    pontos = NR.grade(series, INICIO, FIM)
    tot = NR.totais_por_regiao(series)
    lts = NR.lotes(pontos, 5)
    ne = NR.nordeste_no_fluxo(pontos, tot, lts, ("2026-10-04 17:40",))
    # Às 17:40 faltavam 600 da BA e 100 do AM: o Nordeste é a maior parte.
    assert ne["maior_do_que_faltava"]["hora_brt"] <= "2026-10-04 17:40"
    assert ne["o_que_faltava"]["2026-10-04 17:40"]["faltavam_validos"] == 700
    assert ne["o_que_faltava"]["2026-10-04 17:40"]["parcela_pct"]["Nordeste"] == (
        pytest.approx(100 * 600 / 700, abs=0.01)
    )


def test_painel_nacional_e_um_retrato_atrasado(series, nacional):
    p = NR.painel_nacional(nacional, series)
    assert [x["st"] for x in p] == [13, 20, 27]  # para na primeira versão completa
    # A soma das UFs chegou a 20 seções às 17:40; o nacional as mostrou às 18:20.
    assert p[1]["soma_ufs_alcancou_brt"] == "2026-10-04 17:40:00"
    assert p[1]["atraso_do_retrato_min"] == pytest.approx(40.0)
    # Logo antes da versão das 18:40 a soma já tinha 27 seções, 7 à frente.
    assert p[1]["soma_ufs_a_frente_antes_da_proxima"] == 7
    assert p[1]["idade_do_retrato_antes_da_proxima_min"] == pytest.approx(60.0)


def test_lacuna_da_soma(series):
    lac = NR.lacuna_da_soma(series, "2026-10-04T20:20:00Z", "2026-10-04T21:40:00Z")
    assert lac["de_brt"] == "2026-10-04 17:40:00"
    assert lac["ate_brt"] == "2026-10-04 18:10:00"
    assert lac["minutos"] == 30.0


def test_depois_de(series):
    pontos = NR.grade(series, INICIO, FIM)
    d = NR.depois_de(pontos, "2026-10-04T21:00:00Z")
    assert d["st"] == 6 + 1 and d["vv"] == 600 + 100


# ------------------------------------------------------------------ lentidão


def test_marco_tempos_regra_do_teto():
    tempos = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    m = L.marco_tempos(tempos)
    assert m == {"50": 50, "90": 90, "99": 100, "100": 100}
    # Universo maior que os tempos: 100% não é alcançado.
    assert "100" not in L.marco_tempos(tempos, 11)


def test_marco_serie_e_curvas():
    pontos = [(5.0, 2), (12.0, 5), (40.0, 9), (60.0, 10)]
    assert L.marco_serie(pontos, 10) == {
        "50": 12.0,
        "90": 40.0,
        "99": 60.0,
        "100": 60.0,
    }
    assert L.curva_serie(pontos, 10, [0, 10, 50, 60]) == [0.0, 20.0, 90.0, 100.0]
    assert L.curva_tempos([1, 2, 3, 4], 4, [0, 2, 10]) == [0.0, 50.0, 100.0]


def test_spearman_e_postos():
    assert L.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert L.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    assert L.postos([3, 1, 3, 2]) == [3.5, 1.0, 3.5, 2.0]
    assert L.spearman([1, 2], [1, 2]) is None
    assert L.spearman([1, 1, 1], [1, 2, 3]) is None


def test_hora_e_janela():
    assert L.hora(0) == "17:00"
    assert L.hora(119.9) == "18:59"
    assert L.hora(431) == "00:11 (+1)"
    assert L.hora(None) is None
    assert L.dentro(5.0, (4.0, 6.0)) and not L.dentro(None, (0, 1))


def test_classificacao_e_fuso():
    m22 = {"ac": 300.0, "am": 350.0, "sp": 250.0, "df": 180.0}
    m26 = {"ac": 190.0, "am": 290.0, "sp": 240.0, "df": 130.0}
    c = L.classificar(m22, m26)
    assert c["lentas_nos_dois"] == ["am"]
    assert c["so_2022"] == ["ac"] and c["so_2026"] == ["sp"]
    assert c["rapidas_nos_dois"] == ["df"]
    f = L.teste_fuso(m22, m26)
    assert f["ufs_fora_de_brasilia"] == ["ac", "am"]
    assert f["mediana_2026_fora"] == 240.0 and f["mediana_2026_brasilia"] == 185.0
    assert L.fuso("AC") == -5 and L.fuso("ba") == -3


def test_maior_lacuna_e_por_minuto():
    lac = L.maior_lacuna([150.0, 151.5, 151.8, 179.4, 180.0], 120, 210)
    assert lac["de"] == 151.8 and lac["ate"] == 179.4
    assert lac["minutos"] == pytest.approx(27.6)
    assert L.por_minuto([120.2, 120.9, 121.0, 209.9, 210.0], 120, 210)[:2] == [2, 1]


CAB_2022 = (
    '"DT_GERACAO";"NR_TURNO";"SG_UF";"CD_MUNICIPIO";"NM_MUNICIPIO";"NR_ZONA";"CD_CARGO";'
    '"DT_RECEBIMENTO_BU_HOR_TSE";"DT_PRIM_TOT_PARCIAL_HOR_TSE";"NM_LOCAL_VOTACAO"'
)


def _linha_2022(turno, uf, cd, nome, cargo, rec, tot):
    return (
        f'"15/02/2024";{turno};"{uf}";{cd};"{nome}";1;{cargo};"{rec}";"{tot}";'
        '"ESCOLA; COM PONTO E VÍRGULA"'
    )


def test_ler_2022_filtra_turno_e_cargo():
    linhas = [
        CAB_2022,
        _linha_2022(
            1, "AM", 2550, "TABATINGA", 1, "02/10/2022 17:30:00", "02/10/2022 17:30:45"
        ),
        _linha_2022(
            1, "AM", 2550, "TABATINGA", 1, "03/10/2022 01:00:00", "03/10/2022 01:01:00"
        ),
        _linha_2022(
            1, "AM", 2550, "TABATINGA", 5, "02/10/2022 18:00:00", "02/10/2022 18:00:10"
        ),
        _linha_2022(
            2, "AM", 2550, "TABATINGA", 1, "30/10/2022 18:00:00", "30/10/2022 18:00:10"
        ),
        _linha_2022(1, "DF", 97012, "BRASÍLIA", 1, "02/10/2022 18:00:00", "#NULO#"),
    ]
    s = LF.ler_2022(iter(x + "\n" for x in linhas))
    assert s["secoes"] == {"am": 2, "df": 1}
    assert s["recebimento"]["am"] == [30.0, 480.0]
    assert s["totalizacao"]["am"] == [30.75, 481.0]
    assert s["sem_carimbo"] == {"df:totalizacao": 1}
    assert s["municipios"]["02550"]["tot"] == 481.0
    assert s["municipios"]["02550"]["secoes"] == 2
    assert s["atraso_totalizacao_s"] == [45.0, 60.0]


def test_recebimento_2026_sobre_banco_pequeno(tmp_path):
    caminho = tmp_path / "secoes.sqlite"
    con = sqlite3.connect(caminho)
    con.executescript("""
        CREATE TABLE secao (uf TEXT, mun TEXT, zona INT, secao INT, status_aux TEXT,
          dr_hr TEXT, nsp INT);
        CREATE TABLE bu (uf TEXT, encerramento TEXT);
        CREATE TABLE meta (chave TEXT, valor TEXT);
        INSERT INTO secao VALUES ('ac','01',1,1,'Totalizada','2026-10-04 17:30:00',NULL),
          ('ac','01',1,2,'Totalizada','2026-10-04 18:00:30',NULL),
          ('ac','01',1,3,'aux_404',NULL,2),
          ('ac','01',1,4,'Recebida','2026-10-05 13:00:00',NULL),
          ('ce','02',1,1,NULL,NULL,NULL);
        INSERT INTO bu VALUES ('ac','2026-10-04 15:00:17'),('ac','2026-10-04 15:30:00');
        INSERT INTO meta VALUES ('fonte','teste');
        """)
    con.commit()
    con.close()
    r = LF.recebimento_2026(caminho)
    assert r["tempos"]["ac"] == [30.0, 60.5]
    assert r["contagens"]["ac"] == {
        "agregadas": 1,
        "proprias": 3,
        "totalizadas_com_carimbo": 2,
        "recebidas_depois": 1,
    }
    assert r["contagens"]["ce"] == {"proprias": 1, "sem_carimbo": 1}
    assert r["encerramento_local"]["ac"]["primeiro"] == "2026-10-04 15:00:17"
    assert r["meta"] == {"fonte": "teste"}


def test_montar_ufs_e_resumos(series):
    s22 = {
        "recebimento": {
            "sp": [100.0, 150.0] * 5,
            "ba": [200.0] * 8,
            "am": [100.0, 500.0],
        },
        "totalizacao": {
            "sp": [101.0, 151.0] * 5,
            "ba": [201.0] * 8,
            "am": [101.0, 501.0],
        },
        "secoes": {"sp": 10, "ba": 8, "am": 2},
        "municipios": {
            "00001": {
                "uf": "sp",
                "nome": "A",
                "secoes": 10,
                "rec": 150.0,
                "tot": 151.0,
            },
            "00002": {"uf": "ba", "nome": "B", "secoes": 8, "rec": 200.0, "tot": 201.0},
            "00003": {"uf": "am", "nome": "C", "secoes": 2, "rec": 500.0, "tot": 501.0},
        },
        "atraso_totalizacao_s": [10.0, 50.0, 70.0],
    }
    r26 = {
        "tempos": {"am": [25.0, 85.0]},
        "contagens": {"am": {"proprias": 2, "totalizadas_com_carimbo": 2}},
    }
    ab26 = {
        "00001": {"uf": "sp", "nome": "A", "secoes": 10, "min": 40.0},
        "00002": {"uf": "ba", "nome": "B", "secoes": 8, "min": 70.0},
        "00003": {"uf": "am", "nome": "C", "secoes": 2, "min": 90.0},
    }
    ser = {k: v for k, v in series.items() if k in ("sp", "ba", "am", "zz")}
    ufs = LD.montar_ufs(ser, s22, r26, ab26, (60.0, 69.0), (55.0, 84.0))
    assert [u["uf"] for u in ufs] == ["SP", "BA", "AM"]  # pela hora do 99% de 2026
    am = ufs[-1]
    assert am["marcos"]["2026_totalizado"] == {
        "50": 30.0,
        "90": 90.0,
        "99": 90.0,
        "100": 90.0,
    }
    assert am["marcos"]["2026_recebido"]["100"] == 85.0
    assert am["marcos_logo_apos_pausa"]["2026_recebido"] == ["90", "99", "100"]
    assert am["recebido_2026"]["completa"] is True
    assert ufs[0]["recebido_2026"]["completa"] is False
    assert ufs[0]["marcos"]["2026_recebido"] == {}
    assert am["ultimos_municipios_2026"][0]["nome"] == "C"
    assert am["repetem_entre_os_5_ultimos"] == ["C"]
    assert am["cauda_votos_2026"]["vv"] == 100
    assert len(am["curva_2026"]) == len(LD.GRADE)
    res = LD.resumo_marcos(ufs, "99")
    assert res["mais_rapidas_em_2026"] == 3
    est = LD.estrutural(ufs, s22, ab26)
    assert est["spearman_nacional"] == 1.0 and est["municipios_comparados"] == 3
    at = LD.atraso_2022(s22)
    assert at["mediana_s"] == 50.0 and at["ate_60s_pct"] == pytest.approx(66.67)
    nac = LD.nacional(ser, s22)
    assert nac["secoes_2026"] == 20 and nac["secoes_2022"] == 20
    assert LD.hms(151.833) == "19:31:50"
