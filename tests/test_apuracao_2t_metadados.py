"""Metadados das urnas: repetição por escopo, colisão de 32 bits, coerência BU × .vsc × log e voto."""

import json
import sqlite3

import pandas as pd
import pytest
from apuracao_2t_2026 import metadados_base as mb
from apuracao_2t_2026 import metadados_regras as rg
from apuracao_2t_2026.urnas_analise import preparar


def secao(s, urna, uf="sp", **kw):
    base = {
        "uf": uf,
        "mun": "71072",
        "zona": 1,
        "secao": s,
        "local": 1000,
        "modelo_urna": "UE2022",
        "numero_interno_urna": urna,
        "tipo_urna": 1,
        "tipo_arquivo": 1,
        "n_cargas": 1,
        "carga_em": "2026-09-23 10:00:00",
        "codigo_carga": f"c{urna}",
        "numero_serie_fc": "aaaa0001",
        "numero_serie_fv": f"{urna:08x}",
        "gerador_midia": "ZSP001 - TPM - 1",
        "versao_votacao": "10.23.0.0",
        "abertura": "2026-10-25 08:00:01",
        "encerramento": "2026-10-25 17:00:00",
        "emissao": "2026-10-25 17:02:00",
        "aptos": 300,
        "comparecimento": 240,
        "bu_sha256": f"bu{s}",
        "hash_transmissao": f"h{s}",
        "nsp": None,
        "nsa": None,
        "lula": 100,
        "flavio": 120,
    }
    return base | kw


def test_colisao_esperada_e_quantil():
    c = rg.colisoes_esperadas(499_177, 32)
    assert c["pares_esperados"] == pytest.approx(29.01, abs=0.01)
    assert 40 <= c["limite_999"] <= 50
    assert rg.colisoes_esperadas(10, 32)["limite_999"] == 0
    assert rg.pares([2, 3, 1]) == 4


def test_numero_interno_sa_explicado_e_sobreposicao_sem_explicacao():
    df = pd.DataFrame(
        [
            secao(1, 7, tipo_arquivo=5),
            secao(2, 7, tipo_arquivo=5),
            secao(3, 9),
            secao(4, 9),
            secao(5, 11),
        ]
    )
    r = rg.repeticao(df, "numero_interno_urna")
    assert r["grupos_repetidos"] == 2
    assert r["por_explicacao"]["sistema_apuracao"]["secoes"] == 2
    assert r["sem_explicacao"]["grupos"] == 1
    assert r["sem_explicacao"]["casos"][0]["valor"] == "9"
    assert ("sp", "71072", 1, 3) in r["_chaves_sem_explicacao"]


def test_fv_colisao_preenchimento_e_mesma_urna():
    df = pd.DataFrame(
        [
            secao(1, 1, numero_serie_fv="0000abcd"),
            secao(2, 2, uf="rj", numero_serie_fv="0000abcd"),
            secao(3, 3, tipo_arquivo=2, numero_serie_fv="00000000"),
            secao(4, 4, tipo_arquivo=5, numero_serie_fv="00000000"),
        ]
    )
    r = rg.repeticao(df, "numero_serie_fv")
    assert r["colisao_aleatoria"]["pares_observados"] == 1
    # com 3 identificadores o esperado é ~0 e o limite 0: um par excede e fica sem explicação
    assert r["por_explicacao"]["preenchimento"]["secoes"] == 2
    assert r["sem_explicacao"]["grupos"] == 1


def test_fc_compartilhada_e_entre_ufs():
    df = pd.DataFrame(
        [
            secao(1, 1),
            secao(2, 2),
            secao(3, 3, uf="rj", numero_serie_fc="bbbb0002", gerador_midia="ZRJ - A"),
            secao(4, 4, uf="es", numero_serie_fc="bbbb0002", gerador_midia="ZES - B"),
        ]
    )
    r = rg.repeticao(df, "numero_serie_fc")
    assert r["por_explicacao"]["midia_compartilhada"]["secoes"] == 2
    assert r["sem_explicacao"]["secoes"] == 2
    g = rg.repeticao(df, "gerador_midia")
    assert g["sem_explicacao"]["grupos"] == 0


def test_global_coerente_e_incoerente():
    df = pd.DataFrame([secao(1, 1), secao(2, 2, versao_votacao="9.9")])
    r = rg.repeticao(df, "versao_votacao")
    assert r["coerente"] is False and r["valores_distintos"] == 2
    assert rg.repeticao(df, "log_versao")["situacao"] == "sem dados"


def vsc_linha(s, serie, **kw):
    base = {
        "status": "ok",
        "origem": "vota",
        "mesmo_hash_bu": 1,
        "hw_serial": str(serie),
        "modelo_codigo": 22,
        "ac": "AC UE2022",
        "cadeia_valida": 1,
        "hw_assinatura_ok": 1,
        "hw_bu_assinatura_ok": 1,
        "listas_ok": 1,
        "hw_resumo_ok": 1,
        "sw_resumo_ok": 1,
        "cn_confere_usuario": 1,
        "bu_confere_vsc": 1,
        "cert_validade_inicio": "2025-08-20T19:57:11Z",
        "cert_validade_fim": "2037-12-31T23:00:00Z",
        "hw_criado_em": "20261025T170300",
        "cert_sha256": f"cert{serie}",
    }
    return base | kw


def test_coerencia_vsc_detecta_cada_falha():
    bu = pd.DataFrame([secao(1, 1), secao(2, 2), secao(3, 3), secao(4, 4)])
    v = pd.DataFrame(
        [
            {"uf": "sp", "mun": "71072", "zona": 1, "secao": 1, **vsc_linha(1, 1)},
            {"uf": "sp", "mun": "71072", "zona": 1, "secao": 2, **vsc_linha(2, 99)},
            {
                "uf": "sp",
                "mun": "71072",
                "zona": 1,
                "secao": 3,
                **vsc_linha(3, 3, ac="AC URNA"),
            },
            {
                "uf": "sp",
                "mun": "71072",
                "zona": 1,
                "secao": 4,
                **vsc_linha(4, 4, bu_confere_vsc=0, hw_criado_em="20261025T120000"),
            },
        ]
    )
    resumo, falhas = rg.coerencia_vsc(
        bu.merge(v, on=["uf", "mun", "zona", "secao"]), "2026-10-25"
    )
    assert resumo["id_bu_igual_serie_hw"] == {"sim": 3, "nao": 1}
    assert falhas["id_bu_diferente_da_serie_hw"] == [("sp", "71072", 1, 2)]
    assert falhas["ac_incompativel_com_modelo"] == [("sp", "71072", 1, 3)]
    assert falhas["bu_diferente_do_vsc"] == [("sp", "71072", 1, 4)]
    assert falhas["vsc_antes_da_emissao_do_bu"] == [("sp", "71072", 1, 4)]


def test_red_assinado_por_outra_urna_nao_e_falha():
    bu = pd.DataFrame([secao(1, 1, tipo_arquivo=2)])
    v = pd.DataFrame(
        [
            {
                "uf": "sp",
                "mun": "71072",
                "zona": 1,
                "secao": 1,
                **vsc_linha(1, 77, hw_criado_em="20261025T230000"),
            }
        ]
    )
    resumo, falhas = rg.coerencia_vsc(
        bu.merge(v, on=["uf", "mun", "zona", "secao"]), "2026-10-25"
    )
    assert resumo["votacao_recuperada_assinada_por_outra_urna"] == 1
    assert falhas["id_bu_diferente_da_serie_hw"] == []
    assert falhas["vsc_mais_de_4h_depois_da_emissao"] == []


def test_entre_turnos_certificado_e_carga():
    k = {"uf": "sp", "mun": "71072", "zona": 1}
    v1 = pd.DataFrame(
        [{**k, "secao": 1, **vsc_linha(1, 1)}, {**k, "secao": 2, **vsc_linha(2, 2)}]
    )
    v2 = pd.DataFrame(
        [
            {**k, "secao": 1, **vsc_linha(1, 1, cert_sha256="outro")},
            {**k, "secao": 2, **vsc_linha(2, 2)},
        ]
    )
    b1 = pd.DataFrame([secao(1, 1), secao(2, 2)])
    b2 = pd.DataFrame(
        [secao(1, 1, codigo_carga="nova", carga_em="2026-10-16 09:00:00"), secao(2, 2)]
    )
    r, falhas = rg.entre_turnos_vsc(v1, v2, b1, b2)
    assert r["mesma_urna_certificado_diferente"] == 1
    assert falhas["mesma_urna_certificado_diferente"] == [("sp", "71072", 1, 1)]
    assert r["carga"]["mesma_urna_carga_nova"] == 1
    assert r["carga"]["carga_nova_entre_os_turnos"] == 1


def test_coerencia_logs_ausente_e_presente():
    bu = pd.DataFrame([secao(1, 1), secao(2, 2)])
    assert "situacao" in rg.coerencia_logs(bu)[0]
    bu["log_status"] = "ok"
    bu["log_ids"] = [["00000001"], ["00000002"]]
    bu["log_carga_por_urna"] = [{1: "23/09/2026 10:00:00"}, {2: "25/10/2026 09:00:00"}]
    bu["log_reinicios_votacao"] = [0, 2]
    bu["log_partidas_vota"] = [1, 3]
    bu["log_urna_bu_no_log"] = [1, 1]
    bu["log_carga_bu_no_log"] = [1, 0]
    bu["log_outras_urnas"] = [0, 1]
    bu["log_cargas"] = [["c1"], ["outra"]]
    bu["log_midias"] = [["AAAA0001"], ["AAAA0001"]]
    bu["log_midia_computador"] = [["ZSP001 - TPM - 1"], []]
    bu.loc[0, "gerador_midia"] = "ZSP001|TPM|1"
    bu["log_versao"] = [["10.23.0.0"], ["10.23.0.0"]]
    r, falhas = rg.coerencia_logs(bu)
    assert r["id_do_bu_no_log"]["confere"] == 2
    assert falhas["carga_do_bu_no_log"] == [("sp", "71072", 1, 2)]
    assert r["computador_da_midia_no_log"] == {
        "cobertas": 1,
        "confere": 1,
        "nao_confere": 0,
    }
    assert r["midia_fc_do_bu_no_log"]["nao_confere"] == 0
    # o BU registra a carga em setembro: a data do log aponta para o relógio
    assert falhas["carga_registrada_depois_da_abertura"] == []
    assert falhas["data_de_carga_do_log_diverge_do_bu"] == [("sp", "71072", 1, 2)]
    assert r["carga_registrada_vs_abertura"]["carga_no_dia_da_eleicao"] == 1
    assert falhas["reinicio_durante_votacao"] == [("sp", "71072", 1, 2)]
    assert falhas["carga_do_bu_ausente_do_log"] == [("sp", "71072", 1, 2)]
    assert r["secoes_com_outra_urna_no_log"] == 1


def test_mr_mesma_serie_na_zona_e_colisao_entre_zonas():
    df = pd.DataFrame(
        [
            secao(1, 1, log_serie_mr_dia=["C928805E"]),
            secao(2, 2, log_serie_mr_dia=["C928805E", "B12E2356"]),
            secao(3, 3, log_serie_mr_dia=["C928805E"]),
            secao(4, 4, uf="rs", log_serie_mr_dia=["0B65D911"]),
            secao(5, 5, uf="go", log_serie_mr_dia=["0B65D911"]),
        ]
    )
    r = rg.repeticao(df, "log_serie_mr_dia")
    assert r["por_explicacao"]["mr_mesma_serie_na_zona"]["secoes"] == 3
    # um par entre zonas, com esperado ~0 (limite 0), excede o acaso: sem explicação
    assert r["colisao_aleatoria"]["pares_observados"] == 1
    assert r["sem_explicacao"]["grupos"] == 1


def test_cruzar_voto_contra_vizinhas_e_1t():
    linhas2 = [secao(i, i, flavio=120, lula=100) for i in range(1, 6)] + [
        secao(9, 9, flavio=180, lula=40)
    ]
    linhas1 = [secao(i, i, flavio=110, lula=110) for i in (1, 2, 3, 4, 5, 9)]
    t2, t1 = preparar(pd.DataFrame(linhas2)), preparar(pd.DataFrame(linhas1))
    r = rg.cruzar_voto(t2, t1, [("sp", "71072", 1, 9)], "teste")
    assert r["n"] == 1
    assert r["fatia_flavio_2t_menos_vizinhas_do_municipio"][
        "media_pp"
    ] == pytest.approx(100 * 180 / 220 - 100 * 120 / 220, abs=1e-3)
    assert r["dif_em_dif_contra_1t"]["n"] == 1
    assert rg.cruzar_voto(t2, t1, [], "vazio")["n"] == 0


def test_leitores_toleram_ausencia_e_lem_resumo(tmp_path):
    df, info = mb.ler_logs(tmp_path / "nao.sqlite")
    assert df.empty and info["banco"] == "ausente"
    v, s = mb.ler_vsc(tmp_path / "nao.sqlite", 2)
    assert v.empty and s["banco"] == "ausente"
    banco = tmp_path / "logs.sqlite"
    con = sqlite3.connect(banco)
    con.execute(
        "CREATE TABLE metricas (uf TEXT, mun TEXT, zona INTEGER, secao INTEGER, status TEXT, resumo TEXT)"
    )
    resumo = {
        "urnas_log": ["02468149"],
        "cargas_log": {"02468149": ["997198101523282243858675"]},
        "midias_log": {"02468149": ["1B734FA9"]},
        "metadados_urna": {
            "02468149": {"versao_aplicacao": ["10.23.0.0"], "serie_mr": ["X1"]}
        },
    }
    con.execute(
        "INSERT INTO metricas VALUES ('ac','01007',9,1,'ok',?)", (json.dumps(resumo),)
    )
    con.execute("INSERT INTO metricas VALUES ('ac','01007',9,2,'ok','{}')")
    con.commit()
    con.close()
    df, info = mb.ler_logs(banco)
    assert info["com_metadados_urna"] == 1
    r = df.set_index("secao")
    assert r.loc[1, "log_cargas"] == ["997198101523282243858675"]
    assert r.loc[1, "log_serie_mr"] == ["X1"]
    assert r.loc[1, "log_carga_por_urna"] == {}
    assert r.loc[1, "log_ids"] == ["02468149"]
    assert r.loc[2, "log_versao"] == []
