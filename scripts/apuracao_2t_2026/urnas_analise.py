"""IDs das urnas por seção: modelos, IDs repetidos, troca entre turnos e carga.

Rótulo de tudo o que sai daqui: atipicidade pede explicação, não prova
irregularidade. Cada classificação testa antes as explicações legítimas
documentadas (seção agregada com o mesmo BU, BU emitido pelo sistema de
apuração, urna de contingência ou reserva sem sobreposição de horário).

Fatia de Flávio = votos de Flávio / (Flávio + Lula) na seção, presidente.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
import pandas as pd

from .urnas_base import CHAVE

TIPO_URNA = {
    1: "seção",
    3: "contingência",
    4: "reserva da seção",
    6: "reserva ao encerrar",
}
TIPO_ARQUIVO = {
    1: "votação na urna",
    2: "votação recuperada (RED)",
    3: "sistema de apuração",
    4: "sistema de apuração",
    5: "sistema de apuração",
    6: "sistema de apuração",
}
CONTINGENCIA = {3, 4, 6}
SISTEMA_APURACAO = {3, 4, 5, 6}
ID_LOG_2022 = "67305985"
CLASSES = {
    "mesmo_bu": "Mesmo BU (seção agregada): o mesmo arquivo responde por mais de uma seção",
    "sistema_apuracao": "BU emitido pelo sistema de apuração: o número é o do equipamento da junta, não de uma urna de votação",
    "troca_compativel": "Contingência, reserva ou recarga com horários de votação que não se sobrepõem",
    "sem_contingencia": "Horários não se sobrepõem, mas nenhuma seção do grupo declara contingência, reserva ou recarga",
    "sobreposicao": "A mesma urna aparece votando em duas seções no mesmo intervalo de horário",
    "sem_horario": "Sem horário de votação em alguma seção do grupo para testar sobreposição",
}
EXPLICADAS = ("mesmo_bu", "sistema_apuracao", "troca_compativel")


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    validos = df.flavio + df.lula
    df["validos_fl"] = validos
    df["fatia_flavio"] = np.where(
        validos > 0, 100 * df.flavio / validos.clip(lower=1), np.nan
    )
    df["comparecimento_pct"] = np.where(
        df.aptos > 0, 100 * df.comparecimento / df.aptos.clip(lower=1), np.nan
    )
    df["carga_dia"] = df.carga_em.str[:10]
    return df


def _contagem(serie: pd.Series, rotulos: dict | None = None) -> list[dict]:
    total = int(serie.size)
    out = []
    for valor, n in serie.fillna("sem informação").value_counts().items():
        chave = valor.item() if hasattr(valor, "item") else valor
        out.append(
            {
                "valor": chave,
                "rotulo": (rotulos or {}).get(chave, str(chave)),
                "secoes": int(n),
                "pct": round(100 * n / total, 3) if total else None,
            }
        )
    return out


def modelos(df: pd.DataFrame) -> dict:
    return {
        "secoes": len(df),
        "modelo": _contagem(df.modelo_urna),
        "fonte_modelo": _contagem(df.modelo_fonte),
        "tipo_urna": _contagem(df.tipo_urna, TIPO_URNA),
        "tipo_arquivo": _contagem(df.tipo_arquivo, TIPO_ARQUIVO),
        "n_cargas": _contagem(df.n_cargas),
        "modelo_por_tipo_urna": {
            str(k): {
                str(m): int(n)
                for m, n in g.modelo_urna.fillna("sem").value_counts().items()
            }
            for k, g in df.groupby("tipo_urna")
        },
    }


def _sobrepoe(a: dict, b: dict) -> bool | None:
    if not (
        a["abertura"] and a["encerramento"] and b["abertura"] and b["encerramento"]
    ):
        return None
    return a["abertura"] <= b["encerramento"] and b["abertura"] <= a["encerramento"]


def geografia(linhas: list[dict]) -> str:
    def todos(*campos):
        return len({tuple(r[c] for c in campos) for r in linhas}) == 1

    if todos("uf", "mun", "zona", "local"):
        return "mesmo_local"
    if todos("uf", "mun", "zona"):
        return "mesma_zona"
    if todos("uf", "mun"):
        return "mesmo_municipio"
    if todos("uf"):
        return "mesma_uf"
    return "ufs_diferentes"


def classificar_grupo(linhas: list[dict]) -> dict:
    """Uma urna (número interno) presente em mais de uma seção do mesmo turno."""
    shas = {r["bu_sha256"] for r in linhas}
    contingencia = any(
        (r["tipo_urna"] in CONTINGENCIA) or (r["n_cargas"] or 0) > 1 for r in linhas
    )
    sa = any(r["tipo_arquivo"] in SISTEMA_APURACAO for r in linhas)
    pares = [_sobrepoe(a, b) for a, b in combinations(linhas, 2)]
    sobreposicao = any(p is True for p in pares)
    sem_horario = any(p is None for p in pares)
    fusos = len({r["uf"] for r in linhas}) > 1
    if len(shas) == 1 and None not in shas:
        classe = "mesmo_bu"
    elif sa:
        classe = "sistema_apuracao"
    elif sobreposicao:
        classe = "sobreposicao"
    elif sem_horario:
        classe = "sem_horario"
    elif contingencia:
        classe = "troca_compativel"
    else:
        classe = "sem_contingencia"
    return {
        "classe": classe,
        "explicada": classe in EXPLICADAS,
        "geografia": geografia(linhas),
        "contingencia_declarada": contingencia,
        "sistema_apuracao": sa,
        "horarios_sobrepostos": sobreposicao,
        "ufs_com_fusos_possivelmente_diferentes": fusos,
    }


def _linha_publica(r: dict) -> dict:
    return {
        k: (None if isinstance(r.get(k), float) and math.isnan(r[k]) else r.get(k))
        for k in (
            "uf",
            "mun",
            "zona",
            "secao",
            "local",
            "modelo_urna",
            "tipo_urna",
            "tipo_arquivo",
            "n_cargas",
            "carga_em",
            "abertura",
            "encerramento",
            "comparecimento",
            "fatia_flavio",
        )
    }


def repetidos(df: pd.DataFrame) -> dict:
    """IDs em mais de uma seção do mesmo turno, classificados por explicação candidata."""
    contagem = df.groupby("numero_interno_urna").size()
    ids = contagem[contagem > 1].index
    sub = df[df.numero_interno_urna.isin(ids)]
    grupos = []
    for urna, g in sub.groupby("numero_interno_urna"):
        linhas = g.to_dict("records")
        grupos.append(
            {
                "numero_interno_urna": int(urna),
                "secoes": len(linhas),
                **classificar_grupo(linhas),
                "linhas": [_linha_publica(r) for r in linhas],
            }
        )
    classes = Counter(g["classe"] for g in grupos)
    secoes_classe = Counter()
    for g in grupos:
        secoes_classe[g["classe"]] += g["secoes"]
    return {
        "ids_distintos": int(df.numero_interno_urna.nunique()),
        "ids_repetidos": len(grupos),
        "secoes_envolvidas": int(sum(g["secoes"] for g in grupos)),
        "por_classe": {
            k: {"descricao": v, "ids": classes[k], "secoes": secoes_classe[k]}
            for k, v in CLASSES.items()
        },
        "por_geografia": dict(Counter(g["geografia"] for g in grupos)),
        "sem_explicacao_pela_regra": sum(not g["explicada"] for g in grupos),
        "grupos": sorted(grupos, key=lambda g: (g["explicada"], -g["secoes"])),
    }


def codigo_carga_repetido(df: pd.DataFrame) -> dict:
    """O código de carga deriva do ID da urna, da seção e da hora da carga."""
    cont = df.dropna(subset=["codigo_carga"]).groupby("codigo_carga").size()
    rep = cont[cont > 1]
    linhas = df[df.codigo_carga.isin(rep.index)]
    return {
        "codigos_repetidos": int(rep.size),
        "secoes": int(linhas.shape[0]),
        "por_tipo_arquivo": {
            str(k): int(v) for k, v in linhas.tipo_arquivo.value_counts().items()
        },
        "exemplos": [
            _linha_publica(r) | {"codigo_carga": r["codigo_carga"]}
            for r in linhas.head(20).to_dict("records")
        ],
    }


def id_no_log(df: pd.DataFrame) -> dict:
    """Número interno do BU contra as urnas que escreveram linhas no log da seção."""
    com_log = df[df.log_urnas.notna()]
    ausentes, n_urnas, id_2022 = [], Counter(), 0
    por_modelo = defaultdict(Counter)
    for r in com_log[
        [
            "numero_interno_urna",
            "log_urnas",
            "tipo_arquivo",
            "tipo_urna",
            "modelo_urna",
            *CHAVE,
        ]
    ].to_dict("records"):
        urnas = json.loads(r["log_urnas"])
        n_urnas[len(urnas)] += 1
        ids = {u["id"] for u in urnas}
        id_2022 += ID_LOG_2022 in ids
        presente = f"{int(r['numero_interno_urna']):08d}" in ids
        por_modelo[str(r["modelo_urna"])]["secoes"] += 1
        por_modelo[str(r["modelo_urna"])]["id_do_bu_no_log"] += presente
        if not presente:
            ausentes.append(
                {
                    **{k: r[k] for k in CHAVE},
                    "tipo_arquivo": r["tipo_arquivo"],
                    "tipo_urna": r["tipo_urna"],
                    "ids_no_log": sorted(ids),
                }
            )
    return {
        "secoes_com_log": len(com_log),
        "secoes_sem_log": int(df.log_urnas.isna().sum()),
        "urnas_no_log": {str(k): v for k, v in sorted(n_urnas.items())},
        "id_do_bu_ausente_do_log": len(ausentes),
        "ausentes_por_tipo_arquivo": dict(
            Counter(str(a["tipo_arquivo"]) for a in ausentes)
        ),
        "ausentes": ausentes[:50],
        "secoes_com_id_67305985_no_log": id_2022,
        "por_modelo": {k: dict(v) for k, v in sorted(por_modelo.items())},
    }


def carga(df: pd.DataFrame, dia_eleicao: str, dia_1t: str = "2026-10-04") -> dict:
    datas = df.carga_dia.fillna("sem data").value_counts().sort_index()
    apos_1t = df[df.carga_dia > dia_1t] if dia_eleicao > dia_1t else df.iloc[0:0]
    apos_eleicao = df[df.carga_dia > dia_eleicao]
    depois_abertura = (
        df.carga_em.notna() & df.abertura.notna() & (df.carga_em > df.abertura)
    )
    declarada = df.tipo_urna.isin(CONTINGENCIA) | (df.n_cargas.fillna(1) > 1)
    return {
        "por_dia": {str(k): int(v) for k, v in datas.items()},
        "primeira": df.carga_em.min(),
        "ultima": df.carga_em.max(),
        "sem_data": int(df.carga_em.isna().sum()),
        "fase": _contagem(df.fase),
        "pleito": _contagem(df.pleito),
        "carga_depois_do_1t": {
            "secoes": len(apos_1t),
            "por_tipo_urna": {
                str(k): int(v) for k, v in apos_1t.tipo_urna.value_counts().items()
            },
            "por_n_cargas": {
                str(k): int(v) for k, v in apos_1t.n_cargas.value_counts().items()
            },
        },
        "carga_depois_da_eleicao": len(apos_eleicao),
        "carga_no_dia_da_eleicao": {
            "secoes": int((df.carga_dia == dia_eleicao).sum()),
            "por_tipo_urna": {
                str(k): int(v)
                for k, v in df[df.carga_dia == dia_eleicao]
                .tipo_urna.value_counts()
                .items()
            },
        },
        "carga_depois_do_primeiro_voto": int(depois_abertura.sum()),
        "carga_depois_do_primeiro_voto_sem_contingencia": int(
            (depois_abertura & ~declarada).sum()
        ),
        "exemplos_carga_no_dia": [
            _linha_publica(r)
            for r in df[df.carga_dia == dia_eleicao].head(50).to_dict("records")
        ],
        "id_nao_confere_caminho": int((df.id_confere == 0).sum()),
    }


def _media_ic(v: pd.Series, pesos: pd.Series | None = None) -> dict:
    v = v.dropna()
    n = int(v.size)
    if n == 0:
        return {"n": 0, "media_pp": None, "ep_pp": None, "ic95_pp": None}
    m = float(v.mean())
    ep = float(v.std(ddof=1) / math.sqrt(n)) if n > 1 else None
    out = {
        "n": n,
        "media_pp": round(m, 3),
        "ep_pp": round(ep, 3) if ep is not None else None,
        "ic95_pp": [round(m - 1.96 * ep, 3), round(m + 1.96 * ep, 3)] if ep else None,
    }
    if pesos is not None:
        p = pesos.loc[v.index]
        out["media_ponderada_pp"] = (
            round(float((v * p).sum() / p.sum()), 3) if p.sum() else None
        )
    return out


def excesso_vizinhas(df: pd.DataFrame, marca: pd.Series, campo: str) -> pd.Series:
    """Valor da seção marcada menos a média das seções não marcadas do mesmo município."""
    base = (
        df[~marca & df[campo].notna()]
        .groupby(["uf", "mun"])[campo]
        .agg(["mean", "size"])
    )
    alvo = df[marca].join(base, on=["uf", "mun"])
    alvo = alvo[alvo["size"] >= 3]
    return alvo[campo] - alvo["mean"]


def entre_turnos(t1: pd.DataFrame, t2: pd.DataFrame) -> dict:
    """A mesma seção teve a mesma urna nos dois turnos? E as trocadas votam diferente?"""
    j = t2.merge(
        t1[
            [
                *CHAVE,
                "numero_interno_urna",
                "tipo_urna",
                "n_cargas",
                "codigo_carga",
                "carga_em",
                "fatia_flavio",
                "comparecimento_pct",
                "modelo_urna",
            ]
        ],
        on=CHAVE,
        how="left",
        suffixes=("", "_1t"),
    )
    j = j[j.numero_interno_urna_1t.notna()].copy()
    j["mesma_urna"] = j.numero_interno_urna == j.numero_interno_urna_1t
    j["mesma_carga"] = j.codigo_carga == j.codigo_carga_1t
    ids_1t = t1.set_index("numero_interno_urna")[["uf", "mun", "zona", "secao"]]
    ids_1t = ids_1t[~ids_1t.index.duplicated()]
    trocadas = j[~j.mesma_urna].copy()
    origem = trocadas.join(ids_1t, on="numero_interno_urna", rsuffix="_origem")

    def destino(r):
        if pd.isna(r.uf_origem):
            return "urna_sem_bu_no_1t"
        if (r.uf_origem, r.mun_origem, r.zona_origem) == (r.uf, r.mun, r.zona):
            return "veio_de_outra_secao_da_zona"
        if (r.uf_origem, r.mun_origem) == (r.uf, r.mun):
            return "veio_de_outra_zona_do_municipio"
        return "veio_de_outro_municipio"

    origem["origem"] = origem.apply(destino, axis=1) if len(origem) else []
    j["d_fatia"] = j.fatia_flavio - j.fatia_flavio_1t
    j["d_comparecimento"] = j.comparecimento_pct - j.comparecimento_pct_1t
    marca = ~j.mesma_urna
    grupos = {
        "todas_trocadas": marca,
        "trocada_reserva_no_2t": marca & j.tipo_urna.isin(CONTINGENCIA),
        "trocada_urna_de_secao_no_2t": marca & (j.tipo_urna == 1),
    }
    did = {}
    for nome, m in grupos.items():
        did[nome] = {
            "fatia_flavio": _media_ic(excesso_vizinhas(j, m, "d_fatia"), j.validos_fl),
            "comparecimento": _media_ic(
                excesso_vizinhas(j, m, "d_comparecimento"), j.aptos
            ),
        }
    return {
        "secoes_pareadas": len(j),
        "mesma_urna": int(j.mesma_urna.sum()),
        "urna_diferente": int((~j.mesma_urna).sum()),
        "mesma_urna_mesma_carga": int((j.mesma_urna & j.mesma_carga).sum()),
        "mesma_urna_carga_diferente": int((j.mesma_urna & ~j.mesma_carga).sum()),
        "trocadas_por_tipo_urna_2t": {
            str(k): int(v) for k, v in trocadas.tipo_urna.value_counts().items()
        },
        "trocadas_por_tipo_urna_1t": {
            str(int(k)): int(v) for k, v in trocadas.tipo_urna_1t.value_counts().items()
        },
        "trocadas_por_origem_da_urna": (
            {str(k): int(v) for k, v in origem.origem.value_counts().items()}
            if len(origem)
            else {}
        ),
        "modelo_mudou": int((trocadas.modelo_urna != trocadas.modelo_urna_1t).sum()),
        "diferenca_em_diferencas": did,
        "nota_did": "Para cada seção com urna trocada: variação da fatia de Flávio (ou do comparecimento) do 1º para o 2º turno menos a variação média das seções do mesmo município que mantiveram a urna (mínimo de 3). Em pontos percentuais; IC de 95% pela aproximação normal. Não é efeito causal: a troca de urna acontece por defeito, e defeito não é sorteado.",
    }


def descrever_repetidos(rep: dict) -> str:
    """Frase gerada dos grupos: classe, geografia e UFs, sem texto fixo."""
    if not rep["grupos"]:
        return "nenhum"
    partes = Counter(
        (
            g["classe"],
            g["geografia"],
            ",".join(sorted({r["uf"].upper() for r in g["linhas"]})),
        )
        for g in rep["grupos"]
    )
    return "; ".join(
        f"{n} ID(s) de classe {c}, {geo.replace('_', ' ')}, UF {ufs}"
        for (c, geo, ufs), n in partes.most_common()
    )


def resultado_dos_repetidos(
    df: pd.DataFrame, rep: dict, t1: pd.DataFrame | None = None
) -> dict:
    """Fatia de Flávio das seções com ID repetido contra vizinhas e contra o próprio 1º turno."""
    chaves = {
        (r["uf"], r["mun"], r["zona"], r["secao"])
        for g in rep["grupos"]
        for r in g["linhas"]
    }
    if not chaves:
        return {
            "secoes": 0,
            "contra_vizinhas": _media_ic(pd.Series(dtype=float)),
            "nota": "Nenhuma seção com ID repetido neste turno.",
        }
    idx = pd.MultiIndex.from_frame(df[CHAVE])
    marca = pd.Series(idx.isin(list(chaves)), index=df.index)
    out = {
        "secoes": int(marca.sum()),
        "contra_vizinhas": _media_ic(
            excesso_vizinhas(df, marca, "fatia_flavio"), df.validos_fl
        ),
    }
    if t1 is not None:
        j = df.merge(
            t1[[*CHAVE, "fatia_flavio"]], on=CHAVE, how="left", suffixes=("", "_1t")
        )
        j["d_fatia"] = j.fatia_flavio - j.fatia_flavio_1t
        m = pd.Series(
            pd.MultiIndex.from_frame(j[CHAVE]).isin(list(chaves)), index=j.index
        )
        out["contra_o_proprio_1t_e_vizinhas"] = _media_ic(
            excesso_vizinhas(j, m, "d_fatia"), j.validos_fl
        )
    return out


def ids_entre_turnos_em_outra_secao(t1: pd.DataFrame, t2: pd.DataFrame) -> dict:
    """Urna que votou numa seção no 1º turno e em outra no 2º (mudança de alocação)."""
    a = t1[[*CHAVE, "numero_interno_urna"]].drop_duplicates("numero_interno_urna")
    j = t2[[*CHAVE, "numero_interno_urna", "tipo_urna"]].merge(
        a, on="numero_interno_urna", suffixes=("", "_1t")
    )
    outra = j[
        (j[CHAVE].to_numpy() != j[[f"{c}_1t" for c in CHAVE]].to_numpy()).any(axis=1)
    ]
    mesmo_mun = (outra.uf == outra.uf_1t) & (outra.mun == outra.mun_1t)
    return {
        "urnas_em_outra_secao": len(outra),
        "mesmo_municipio": int(mesmo_mun.sum()),
        "outro_municipio": int((~mesmo_mun).sum()),
        "por_tipo_urna_2t": {
            str(k): int(v) for k, v in outra.tipo_urna.value_counts().items()
        },
    }


ROTULO_URNAS = "pede explicação, não prova irregularidade"
