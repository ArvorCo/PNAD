"""`zonas.json`: os 6.106 pares município-zona do Brasil, em colunas, para o agente de anomalias."""

from __future__ import annotations

from typing import Any

from .contexto import Contexto, numero_do_municipio
from .dados import brt, colunar, pct

COLUNAS = (
    "uf",
    "cd_tse",
    "ibge",
    "municipio",
    "zona",
    "completo",
    "secoes",
    "secoes_total",
    "eleitores",
    "comparecimento",
    "pct_comparecimento",
    "validos",
    "brancos",
    "nulos",
    "flavio",
    "lula",
    "cury",
    "renan",
    "caiado",
    "outros",
    "primeira_secao_gerado_brt",
    "completa_gerado_brt",
    "totalizacao_impressa",
    "gerado_final_brt",
    "eleitores_2022",
    "comparecimento_2022",
    "validos_2022_1t",
    "bolsonaro_2022_1t",
    "lula_2022_1t",
    "snapshot_id",
)


def montar(ctx: Contexto) -> dict[str, Any]:
    linhas = []
    for (cd, zona), arq in ctx.zonas.items():
        if arq.uf == "zz":
            continue
        snap = arq.vigente
        cad = ctx.cadastro[cd]
        votos = ctx.agrupar(ctx.votos_vigentes[snap["id"]])
        primeira = next((s for s in arq.versoes if (s["st"] or 0) > 0), None)
        completa = next(
            (s for s in arq.versoes if s["ts"] and s["st"] == s["ts"]), None
        )
        chave22 = (numero_do_municipio(cd), int(zona))
        r22 = ctx.zona2022.get(chave22) or {}
        d22 = ctx.detzona2022.get(chave22) or {}
        linhas.append(
            {
                "uf": cad["uf"].upper(),
                "cd_tse": cd,
                "ibge": cad["ibge"],
                "municipio": cad["nome"],
                "zona": zona,
                "completo": snap["st"] == snap["ts"],
                "secoes": snap["st"],
                "secoes_total": snap["ts"],
                "eleitores": snap["te"],
                "comparecimento": snap["comparecimento"],
                "pct_comparecimento": pct(snap["comparecimento"], snap["te"], 3),
                "validos": snap["vv"],
                "brancos": snap["vb"],
                "nulos": snap["tvn"],
                **votos,
                "primeira_secao_gerado_brt": (
                    brt(primeira["gerado_em"]) if primeira else None
                ),
                "completa_gerado_brt": brt(completa["gerado_em"]) if completa else None,
                "totalizacao_impressa": (
                    f"{snap['dt']} {snap['ht']}" if snap["dt"] else None
                ),
                "gerado_final_brt": brt(snap["gerado_em"]),
                "eleitores_2022": d22.get("aptos"),
                "comparecimento_2022": d22.get("comparecimento"),
                "validos_2022_1t": r22.get("validos"),
                "bolsonaro_2022_1t": r22.get("22"),
                "lula_2022_1t": r22.get("13"),
                "snapshot_id": snap["id"],
            }
        )
    linhas.sort(key=lambda x: (x["uf"], x["municipio"], x["zona"]))
    return {
        "nota": (
            "Presidente, 1º turno de 2026, versão vigente (última gerada pelo TSE) de cada "
            "arquivo de zona. nulos inclui os nulos técnicos. totalizacao_impressa está no "
            "relógio local da unidade (AC UTC-5; AM, MT, MS, RO e RR UTC-4 com exceções no "
            "oeste do AM; Fernando de Noronha UTC-2); os horários *_gerado_brt são do relógio "
            "de geração do TSE, em Brasília. As colunas de 2022 casam por código TSE do "
            "município e número da zona; rezoneamento entre 2022 e 2026 pode mudar o "
            "território de uma zona com o mesmo número."
        ),
        "n": len(linhas),
        "n_incompletas": sum(1 for x in linhas if not x["completo"]),
        "n_sem_2022": sum(1 for x in linhas if x["validos_2022_1t"] is None),
        "zonas": colunar(COLUNAS, linhas),
    }
