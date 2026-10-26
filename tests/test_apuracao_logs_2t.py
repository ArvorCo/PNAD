"""Logs do 2º turno: dia do pleito, guarda compacta, identidade da urna e cadência."""

import hashlib
import io
import sqlite3
import zipfile

import pytest
from apuracao_logs import coleta, compacto, pleito
from apuracao_logs.parser import analisar, analisar_textos, dias_do_pleito
from apuracao_logs.processamento import identidade_no_log, processar, reconciliar
from apuracao_logs.turnos import comparar

URNA = "02027601"


def linhas(dia, eventos, urna=URNA):
    return [
        f"{dia} {e[0]}\t{e[3] if len(e) > 3 else 'INFO'}\t{urna}\t{e[1]}\t{e[2]}\t{i:016X}"
        for i, e in enumerate(eventos)
    ]


def ciclo(h="08"):
    return [
        (f"{h}:00:00", "VOTA", "Identificador do eleitor digitado pelo mesário"),
        (f"{h}:00:10", "VOTA", "Tipo de habilitação do eleitor [biométrica]"),
        (f"{h}:00:10", "VOTA", "Eleitor foi habilitado"),
        (f"{h}:00:20", "VOTA", "Voto confirmado para [Presidente]"),
        (f"{h}:00:21", "VOTA", "O voto do eleitor foi computado"),
    ]


def zipar(texto: str) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("logd.dat", texto.encode("latin1"))
    return b.getvalue()


CARGA = [
    ("10:00:00", "SCUE", "Município: 71072"),
    ("10:00:00", "SCUE", "Zona Eleitoral: 1"),
    ("10:00:00", "SCUE", "Seção Eleitoral: 1"),
    ("10:00:00", "SCUE", "Fase da UE: Oficial"),
    ("10:00:01", "SCUE", "Identificação do Modelo de Urna: UE2020"),
    (
        "10:00:02",
        "SCUE",
        "Código de carga 123.456 gravado na tabela de correspondência",
    ),
    ("10:00:03", "SCUE", "Identificador da mídia de carga: 9B12FA3"),
]
TEXTO_1T = (
    "\n".join(
        linhas("22/09/2026", CARGA)
        + linhas("04/10/2026", ciclo("08") + ciclo("09") + ciclo("10"))
    )
    + "\n"
)
TEXTO_2T = TEXTO_1T + "\n".join(
    linhas(
        "25/10/2026",
        [
            ("05:00:00", "GAP", "Problema ao desmontar a MR", "ERRO"),
            ("07:00:00", "VOTA", "Gerando relatório [ZERÉSIMA] [TÉRMINO]"),
            *ciclo("08"),
            *ciclo("13"),
        ],
    )
)


def test_dia_do_pleito_e_padrao_do_primeiro_turno():
    assert dias_do_pleito("04/10/2026") == {"04/10/2026": 0, "05/10/2026": 86400}
    assert dias_do_pleito("25/10/2026") == {"25/10/2026": 0, "26/10/2026": 86400}
    assert pleito.obter(3221).dia_ordem == "20261025"
    assert pleito.obter(3220).raw == coleta.DESTINO
    with pytest.raises(ValueError):
        pleito.obter(9999)


def test_segundo_turno_conta_so_o_proprio_dia_e_le_carga_anterior():
    r1 = analisar(zipar(TEXTO_2T))  # padrão: dia do 1º turno
    r2 = analisar(zipar(TEXTO_2T), None, "25/10/2026")
    assert r1["contagens"]["computados"] == 3
    assert r2["contagens"]["computados"] == 2
    assert r2["computados_por_hora"] == {"8": 1, "13": 1}
    assert r2["urnas_log"] == [URNA]
    assert r2["cargas_log"] == {URNA: ["123456"]}
    assert r2["midias_log"] == {URNA: ["9B12FA3"]}
    assert r2["contagens"]["erro_mr_pre_zeresima"] == 1
    assert r2["contagens"]["erros"] == 1  # critério publicado intocado


def test_identidade_da_urna_do_bu_contra_o_log():
    r = analisar(zipar(TEXTO_2T), None, "25/10/2026")
    ok = identidade_no_log(
        r, {"numero_interno_urna": 2027601, "codigo_carga": "123456"}
    )
    assert ok == {
        "urna_bu_no_log": True,
        "outras_urnas_no_log": [],
        "carga_bu_no_log": True,
    }
    outra = identidade_no_log(r, {"numero_interno_urna": 2027602, "codigo_carga": "1"})
    assert outra["urna_bu_no_log"] is False and outra["carga_bu_no_log"] is None
    assert identidade_no_log(r, {})["urna_bu_no_log"] is None


def test_pacote_compacto_reproduz_leitura_e_texto_integral():
    raw1, raw2 = zipar(TEXTO_1T), zipar(TEXTO_2T)
    p = compacto.empacotar(raw2, raw1)
    assert p["formato"] == "prefixo_1t"
    assert len(p["blob"]) < len(raw2)
    arquivos, omitidas = compacto.ler_para_analise(p)
    assert analisar_textos(arquivos, None, "25/10/2026", omitidas) == analisar(
        raw2, None, "25/10/2026"
    )
    [(nome, texto)] = compacto.reconstruir(p, raw1)
    assert nome == "logd.dat" and texto == TEXTO_2T.encode("latin1")
    with pytest.raises(AssertionError):
        compacto.reconstruir(p, zipar(TEXTO_1T.replace("08:00:21", "08:00:22")))
    # Sem referência válida, o texto inteiro vai comprimido, sem perda.
    q = compacto.empacotar(raw2, zipar("outro\n"))
    assert q["formato"] == "xz_completo"
    assert compacto.reconstruir(q)[0][1] == TEXTO_2T.encode("latin1")


def test_processamento_le_pacote_compacto_e_confere_pleito():
    raw1, raw2 = zipar(TEXTO_1T), zipar(TEXTO_2T)
    p = compacto.empacotar(raw2, raw1)
    bu = {
        "mun": "71072",
        "zona": 1,
        "secao": 1,
        "numero_interno_urna": 2027601,
        "comparecimento": 2,
        "fase": 2,
        "pleito": 3221,
        "codigo_carga": "123456",
    }
    sha = hashlib.sha256(raw2).hexdigest()
    a = processar((("sp", "71072", 1, 1), None, sha, bu, 3221, "25/10/2026", p))
    b = processar((("sp", "71072", 1, 1), raw2, sha, bu, 3221, "25/10/2026", None))
    assert a[-2] == b[-2] == "ok"
    ra = reconciliar(analisar(raw2, bu, "25/10/2026"), bu, 3221)
    assert ra["contagem_confere"]
    assert "fase_ou_pleito_incompativel" not in ra["motivos_tempo"]
    assert (
        "fase_ou_pleito_incompativel"
        in reconciliar(analisar(raw2, bu, "25/10/2026"), bu, 3220)["motivos_tempo"]
    )
    falso = processar(
        (("sp", "71072", 1, 1), None, "0" * 64, bu, 3221, "25/10/2026", p)
    )
    assert falso[-2] == "erro"


def test_coleta_compacta_grava_pacote_e_preserva_hash(tmp_path, monkeypatch):
    ref = tmp_path / "logs_1t.sqlite"
    con = coleta.abrir(ref)
    con.execute(
        "INSERT INTO arquivos VALUES ('sp','71072',1,1,'x','ok',200,'d',NULL,?)",
        (zipar(TEXTO_1T),),
    )
    con.commit()
    con.close()
    db = tmp_path / "logs_2t.sqlite"
    con = coleta.abrir(db)
    con.execute(
        "INSERT INTO catalogo VALUES ('sp','71072',1,1,'h','log.jez',NULL,1,'ok')"
    )
    con.commit()
    con.close()
    raw2 = zipar(TEXTO_2T)

    def obter(self, r):
        sha = hashlib.sha256(raw2).hexdigest()
        return (
            r["uf"],
            r["mun"],
            r["zona"],
            r["secao"],
            sha,
            "ok",
            200,
            "t",
            None,
            raw2,
        )

    monkeypatch.setattr(coleta.Cliente, "obter", obter)
    coleta.coletar(db, 0, 1, 1, [], guardar="compacto", referencia=ref)
    con = sqlite3.connect(db)
    zip_, sha = con.execute("SELECT zip, sha256 FROM arquivos").fetchone()
    assert zip_ is None and sha == hashlib.sha256(raw2).hexdigest()
    p = coleta.ler_compacto(con, ("sp", "71072", 1, 1))
    assert p["formato"] == "prefixo_1t" and p["sha256_zip"] == sha
    con.execute("UPDATE compacto SET blob=x'00'")
    with pytest.raises(ValueError):
        coleta.ler_compacto(con, ("sp", "71072", 1, 1))
    con.close()


def test_comparacao_entre_turnos_cruza_atencao_e_diagnosticos():
    s1 = {("SP", 1, 1): ["assinatura"], ("SP", 1, 2): [], ("SP", 1, 3): ["bateria"]}
    s2 = {("SP", 1, 1): ["assinatura"], ("SP", 1, 2): ["reinicios"], ("SP", 1, 4): []}
    d = comparar(s1, s2)
    assert d["secoes_nos_dois"] == 2
    assert d["atencao_1t_x_2t"] == {"0x1": 1, "3x3": 1}
    assert d["por_criterio"]["assinatura"]["ambos"] == 1
    assert d["por_criterio"]["reinicios"]["so_2t"] == 1
    assert d["persistencia"]["atencao_3"]["pct_2t_dado_1t"] == 100.0


def test_regra_2_tira_erro_da_mr_antes_da_zeresima_do_erro_tecnico():
    from apuracao_logs.criterios import VERSAO_REGRAS, erros_tecnicos

    assert VERSAO_REGRAS == "2"
    assert erros_tecnicos({"erros": 1, "erro_mr_pre_zeresima": 1}) == 0
    assert erros_tecnicos({"erros": 3, "erro_mr_pre_zeresima": 1}) == 2
    assert erros_tecnicos({"erros": 2}) == 2  # métricas antigas sem o campo


def test_metadados_da_urna_e_partidas_com_votos_antes_e_depois():
    extra = [
        ("10:00:04", "GAP", "Versão da aplicação: 10.23.0.0 - Praia da Barra do Cahy"),
        ("10:00:05", "GAP", "Número de série da MR: 1A2B3C4D"),
    ]
    texto = (
        TEXTO_2T.replace(
            linhas("22/09/2026", CARGA)[-1],
            "\n".join([linhas("22/09/2026", CARGA)[-1], *linhas("22/09/2026", extra)]),
        )
        + "\n"
        + "\n".join(
            linhas(
                "25/10/2026",
                [
                    ("13:30:00", "LOGD", "Urna ligada em 25/10/2026 às 13:30:00"),
                    *ciclo("14"),
                ],
            )
        )
    )
    r = analisar(zipar(texto), None, "25/10/2026")
    m = r["metadados_urna"][URNA]
    assert m["versao_aplicacao"] == ["10.23.0.0 - Praia da Barra do Cahy"]
    assert m["serie_mr"] == ["1A2B3C4D"]
    assert m["carga_registrada_em"] == "22/09/2026 10:00:02"
    assert m["modelos"] == ["UE2020"]
    assert r["zeresima_s"] == 7 * 3600
    [p] = [p for p in r["partidas_dia"] if p["tipo"] == "sistema"]
    assert (p["fase"], p["votos_antes"], p["votos_depois"]) == ("votacao", 2, 1)
    assert r["contagens"]["reinicios_sistema_em_votacao"] == 1
