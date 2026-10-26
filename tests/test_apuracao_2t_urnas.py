"""IDs das urnas por seção: classificação dos repetidos, troca entre turnos e log."""

import json

import pandas as pd
from apuracao_2t_2026 import urnas_analise as an


def secao(s, urna, **kw):
    base = {
        "uf": "sp",
        "mun": "71072",
        "zona": 1,
        "secao": s,
        "local": 1000,
        "modelo_urna": "UE2020",
        "modelo_fonte": "log_mesma_urna",
        "numero_interno_urna": urna,
        "tipo_urna": 1,
        "tipo_arquivo": 1,
        "n_cargas": 1,
        "carga_em": "2026-09-23 10:00:00",
        "codigo_carga": f"c{s}",
        "abertura": "2026-10-25 08:00:01",
        "encerramento": "2026-10-25 17:00:00",
        "emissao": "2026-10-25 17:02:00",
        "fase": 2,
        "pleito": 3221,
        "aptos": 300,
        "comparecimento": 240,
        "log_urnas": json.dumps(
            [{"id": f"{urna:08d}", "modelos": ["UE2020"], "linhas": 9}]
        ),
        "id_confere": 1,
        "sa_junta": None,
        "sa_motivo": None,
        "bu_sha256": f"sha{s}",
        "hash_transmissao": f"h{s}",
        "lula": 100,
        "flavio": 120,
    }
    return base | kw


def tabela(linhas):
    return an.preparar(pd.DataFrame(linhas))


def test_mesma_urna_votando_ao_mesmo_tempo_fica_sem_explicacao():
    g = an.classificar_grupo([secao(1, 7), secao(2, 7, tipo_urna=4)])
    assert g["classe"] == "sobreposicao" and not g["explicada"]
    assert g["geografia"] == "mesmo_local"


def test_reserva_com_horarios_disjuntos_e_troca_compativel():
    a = secao(1, 7, encerramento="2026-10-25 10:00:00")
    b = secao(2, 7, tipo_urna=4, abertura="2026-10-25 10:30:00", local=2000)
    g = an.classificar_grupo([a, b])
    assert g["classe"] == "troca_compativel" and g["explicada"]
    assert g["geografia"] == "mesma_zona"
    sem = an.classificar_grupo([a, b | {"tipo_urna": 1}])
    assert sem["classe"] == "sem_contingencia" and not sem["explicada"]


def test_mesmo_bu_e_sistema_de_apuracao_vem_antes_do_horario():
    assert (
        an.classificar_grupo([secao(1, 7, bu_sha256="x"), secao(2, 7, bu_sha256="x")])[
            "classe"
        ]
        == "mesmo_bu"
    )
    sa = an.classificar_grupo(
        [
            secao(1, 7, tipo_arquivo=5, abertura=None),
            secao(2, 7, tipo_arquivo=5, abertura=None, uf="zz"),
        ]
    )
    assert sa["classe"] == "sistema_apuracao" and sa["geografia"] == "ufs_diferentes"
    assert (
        an.classificar_grupo([secao(1, 7, abertura=None), secao(2, 7)])["classe"]
        == "sem_horario"
    )


def test_repetidos_conta_ids_e_secoes_por_classe():
    df = tabela([secao(1, 7), secao(2, 7), secao(3, 8), secao(4, 9, mun="1")])
    r = an.repetidos(df)
    assert (r["ids_distintos"], r["ids_repetidos"], r["secoes_envolvidas"]) == (3, 1, 2)
    assert r["por_classe"]["sobreposicao"]["secoes"] == 2
    assert r["sem_explicacao_pela_regra"] == 1


def test_id_no_log_e_numero_generico_de_2022():
    df = tabela(
        [
            secao(1, 7),
            secao(2, 8, tipo_arquivo=2, log_urnas=json.dumps([{"id": "00000009"}])),
            secao(3, 10, log_urnas=json.dumps([{"id": an.ID_LOG_2022}])),
        ]
    )
    r = an.id_no_log(df)
    assert r["id_do_bu_ausente_do_log"] == 2
    assert r["ausentes_por_tipo_arquivo"] == {"2": 1, "1": 1}
    assert r["secoes_com_id_67305985_no_log"] == 1


def test_entre_turnos_separa_mesma_urna_troca_e_diferenca_em_diferencas():
    t1 = tabela([secao(s, 100 + s, pleito=3220) for s in range(1, 7)])
    t2 = tabela(
        [secao(s, 100 + s) for s in range(1, 6)]
        + [secao(6, 999, tipo_urna=4, flavio=200)]
    )
    r = an.entre_turnos(t1, t2)
    assert (r["mesma_urna"], r["urna_diferente"]) == (5, 1)
    assert r["trocadas_por_origem_da_urna"] == {"urna_sem_bu_no_1t": 1}
    did = r["diferenca_em_diferencas"]["trocada_reserva_no_2t"]["fatia_flavio"]
    assert did["n"] == 1 and did["media_pp"] > 0
    assert (
        r["diferenca_em_diferencas"]["trocada_urna_de_secao_no_2t"]["fatia_flavio"]["n"]
        == 0
    )


def test_carga_no_dia_e_depois_do_primeiro_voto_com_reserva():
    df = tabela(
        [
            secao(1, 1, carga_em="2026-10-25 09:45:00", tipo_urna=4, n_cargas=2),
            secao(2, 2, carga_em="2026-10-12 10:00:00"),
            secao(3, 3),
        ]
    )
    r = an.carga(df, "2026-10-25")
    assert r["carga_no_dia_da_eleicao"]["secoes"] == 1
    assert r["carga_depois_do_primeiro_voto"] == 1
    assert r["carga_depois_do_primeiro_voto_sem_contingencia"] == 0
    assert r["carga_depois_do_1t"]["secoes"] == 2


def test_codigo_de_carga_repetido():
    df = tabela(
        [secao(1, 1, codigo_carga="x"), secao(2, 2, codigo_carga="x"), secao(3, 3)]
    )
    assert an.codigo_carga_repetido(df)["codigos_repetidos"] == 1
