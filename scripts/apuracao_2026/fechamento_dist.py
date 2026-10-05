"""Pergunta 1 do fechamento: quando a votação termina, por região, UF, tamanho e local.

Toda comparação entre 2022 e 2026 usa o mesmo conjunto de UFs (as completas na
coleta de 2026), para que a diferença não seja composição. Medidas em minutos
depois das 17h de Brasília (ver `fechamento_base`).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from . import secoes_base
from .dados import regiao
from .fechamento_base import (
    FAIXAS_APTOS,
    GRADE,
    ORDEM_TIPO,
    acumulada,
    lacuna,
    resumo_tempo,
)
from .secoes_base import r2

REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]


def _resumo(serie: pd.Series, curva: bool) -> dict[str, Any] | None:
    r = resumo_tempo(serie)
    if r is not None and curva:
        r["acumulada"] = acumulada(serie)
    return r


def _decomposicao(g: pd.DataFrame) -> dict[str, Any] | None:
    """Fila (17h até o último voto) e transmissão (último voto até o TSE), 2026."""
    ok = g.dropna(subset=["enc_min", "rec_min"])
    if ok.empty:
        return None
    fila = ok["enc_min"]
    trans = ok["rec_min"] - ok["enc_min"]
    return {
        "secoes": len(ok),
        "fila_mediana_min": r2(fila.median(), 1),
        "fila_p90_min": r2(fila.quantile(0.9), 1),
        "transmissao_mediana_min": r2(trans.median(), 1),
        "transmissao_p90_min": r2(trans.quantile(0.9), 1),
        "recebimento_mediana_min": r2(ok["rec_min"].median(), 1),
    }


def grupo(
    chave: str,
    nivel: str,
    g26: pd.DataFrame,
    g22: pd.DataFrame,
    completa: bool,
    curva: bool,
    regiao: str | None = None,
) -> dict[str, Any]:
    return {
        "chave": chave,
        "nivel": nivel,
        "regiao": regiao,
        "completa_2026": completa,
        "encerramento_2026": _resumo(g26["enc_min"], curva) if len(g26) else None,
        "recebimento_2026": _resumo(g26["rec_min"], curva) if len(g26) else None,
        "recebimento_2022": _resumo(g22["rec_min"], curva) if len(g22) else None,
        "decomposicao_2026": _decomposicao(g26) if len(g26) else None,
    }


def distribuicao(
    d26: pd.DataFrame, d22: pd.DataFrame, completas: list[str]
) -> dict[str, Any]:
    comp = {u.lower() for u in completas}
    c26 = d26[d26["uf"].isin(comp)]
    c22 = d22[d22["uf"].isin(comp)]
    regioes = [
        grupo(
            rg,
            "regiao",
            c26[c26["regiao"] == rg],
            c22[c22["regiao"] == rg],
            True,
            True,
            rg,
        )
        for rg in REGIOES
        if (c26["regiao"] == rg).any()
    ]
    ufs = []
    for uf in sorted(set(d22["uf"]) | set(d26["uf"])):
        g26 = d26[d26["uf"] == uf]
        g22 = d22[d22["uf"] == uf]
        ufs.append(
            grupo(
                uf.upper(),
                "uf",
                g26,
                g22,
                uf in comp,
                False,
                regiao(uf),
            )
        )
    return {
        "grade_min": list(GRADE),
        "conjunto": (
            "Brasil e regiões só com as UFs completas na coleta de 2026, nos dois anos; "
            "UFs em coleta aparecem na tabela por UF com a marca de parcial"
        ),
        "brasil": grupo("Brasil", "brasil", c26, c22, True, True),
        "lacuna_recebimento": {
            "2026": lacuna(d26["rec_min"]),
            "2022": lacuna(d22["rec_min"]),
            "leitura": (
                "maior intervalo sem nenhum boletim registrado como recebido no TSE entre "
                "17h e meia-noite, em todas as seções com hora"
            ),
        },
        "regioes": regioes,
        "ufs": ufs,
    }


def _tardias(g: pd.DataFrame, total_tardias: int) -> float | None:
    n = int((g["enc_min"] >= 60).sum())
    return r2(100 * n / total_tardias) if total_tardias else None


def por_tamanho(
    d26: pd.DataFrame, d22: pd.DataFrame, completas: list[str]
) -> dict[str, Any]:
    comp = {u.lower() for u in completas}
    c26 = d26[d26["uf"].isin(comp)]
    c22 = d22[d22["uf"].isin(comp)]
    tardias = int((c26["enc_min"] >= 60).sum())
    linhas = []
    for nome, lo, hi in FAIXAS_APTOS:
        g26 = c26[c26["faixa_aptos"] == nome]
        g22 = c22[c22["faixa_aptos"] == nome]
        linhas.append(
            {
                "faixa": nome,
                "min": lo,
                "max": hi,
                "secoes_2026": len(g26),
                "secoes_2022": len(g22),
                "votantes_medio_2026": r2(g26["comparecimento"].mean(), 1),
                "encerramento_2026": resumo_tempo(g26["enc_min"]),
                "recebimento_2026": resumo_tempo(g26["rec_min"]),
                "recebimento_2022": resumo_tempo(g22["rec_min"]),
                "pct_das_tardias_2026": _tardias(g26, tardias),
            }
        )
    return {
        "base": "eleitorado apto da seção (aptos da eleição federal, com trânsito)",
        "secoes_tardias_2026": tardias,
        "definicao_tardia": "encerramento às 18h de Brasília ou depois",
        "linhas": linhas,
    }


def por_tipo(
    d26: pd.DataFrame, d22: pd.DataFrame, completas: list[str]
) -> dict[str, Any]:
    comp = {u.lower() for u in completas}
    c26 = d26[d26["uf"].isin(comp)]
    c22 = d22[d22["uf"].isin(comp)]
    tardias = int((c26["enc_min"] >= 60).sum())
    linhas = []
    for tipo in ORDEM_TIPO:
        g26 = c26[c26["grupo_tipo"] == tipo]
        g22 = c22[c22["grupo_tipo"] == tipo]
        if g26.empty and g22.empty:
            continue
        linhas.append(
            {
                "tipo": tipo,
                "secoes_2026": len(g26),
                "secoes_2022": len(g22),
                "aptos_medio_2026": r2(g26["aptos"].mean(), 1),
                "encerramento_2026": resumo_tempo(g26["enc_min"]),
                "recebimento_2026": resumo_tempo(g26["rec_min"]),
                "recebimento_2022": resumo_tempo(g22["rec_min"]),
                "pct_das_tardias_2026": _tardias(g26, tardias),
            }
        )
    return {
        "regras": secoes_base.regras_local_json(),
        "agrupamento": {
            "zona rural, assentamento ou quilombo": [
                "zona rural",
                "assentamento",
                "quilombo",
            ],
            "escola fora de zona rural": ["escola ou universidade"],
            "outro local": [
                "hospital ou unidade de saúde",
                "voto em trânsito",
                "outro",
                "sem cadastro",
            ],
        },
        "aviso": (
            "Tipo de local é inferência por palavra-chave no nome, bairro e endereço do "
            "local de votação, na ordem das regras: a primeira que casa decide. Escola "
            "num povoado conta como zona rural. Em 2022 o arquivo não tem bairro, só "
            "nome e endereço."
        ),
        "linhas": linhas,
    }
