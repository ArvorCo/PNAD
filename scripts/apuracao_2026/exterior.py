"""`exterior.json`: as 186 cidades do exterior, por país e continente, contra 2022."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from .contexto import EXTERIOR_JSON, ORDEM_2026, Contexto, numero_do_municipio
from .dados import (
    CONTINENTES,
    brt,
    continente,
    deslocamento_horas,
    dif,
    fuso_inferido,
    pais_nome,
    pct,
)

CASAS = 4


def _cidades(ctx: Contexto) -> list[dict[str, Any]]:
    cadastro = {
        c["cd"]: c for c in json.loads(EXTERIOR_JSON.read_text(encoding="utf-8"))
    }
    saida = []
    for cd, arq in sorted(ctx.municipios.items()):
        if arq.uf != "zz":
            continue
        snap = arq.vigente
        info = cadastro[cd]
        votos = ctx.agrupar(ctx.votos_vigentes[snap["id"]])
        vv = snap["vv"] or 0
        primeira = next((s for s in arq.versoes if s["dt"]), None)
        desloc = (
            deslocamento_horas(primeira["dt"], primeira["ht"], primeira["gerado_em"])
            if primeira
            else None
        )
        numero = numero_do_municipio(cd)
        r22 = ctx.mun2022.get(numero)
        d22 = ctx.det2022[1].get(numero)
        linha: dict[str, Any] = {
            "cd_tse": cd,
            "nome": info["nm"],
            "pais": info["pais"],
            "pais_nome": pais_nome(info["pais"]),
            "continente": continente(info["pais"]),
            "lat": info["lat"],
            "lon": info["lon"],
            "secoes": snap["st"],
            "eleitores": snap["te"],
            "comparecimento": snap["comparecimento"],
            "pct_comparecimento": pct(snap["comparecimento"], snap["te"], CASAS),
            "validos": vv,
            "brancos": snap["vb"],
            "nulos": snap["tvn"],
            "votos": votos,
            "pct": {k: pct(v, vv, CASAS) for k, v in votos.items()},
            "lider": max(votos, key=lambda k: votos[k]),
            "primeira_versao_totalizada_gerada_brt": (
                brt(primeira["gerado_em"]) if primeira else None
            ),
            "totalizacao_impressa": (
                f"{primeira['dt']} {primeira['ht']}" if primeira else None
            ),
            "deslocamento_aparente_h": desloc,
            "fuso_utc_inferido": fuso_inferido(desloc),
        }
        if r22:
            t1, t2 = r22["t1"], r22["t2"]
            linha["r2022"] = {
                "validos_1t": t1.get("validos"),
                "bolsonaro_1t": t1.get("22", 0),
                "lula_1t": t1.get("13", 0),
                "validos_2t": t2.get("validos"),
                "bolsonaro_2t": t2.get("22", 0),
                "lula_2t": t2.get("13", 0),
                "eleitores": d22["aptos"] if d22 else None,
                "comparecimento": d22["comparecimento"] if d22 else None,
            }
        else:
            linha["r2022"] = None
        saida.append(linha)
    return saida


def _agregar(cidades: list[dict[str, Any]], chave: str) -> list[dict[str, Any]]:
    grupos: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in cidades:
        grupos[c[chave]].append(c)
    saida = []
    for nome, membros in grupos.items():
        votos = {k: sum(c["votos"][k] for c in membros) for k in ORDEM_2026}
        vv = sum(c["validos"] for c in membros)
        te = sum(c["eleitores"] for c in membros)
        comp = sum(c["comparecimento"] for c in membros)
        com22 = [c for c in membros if c["r2022"]]
        b22 = sum(c["r2022"]["bolsonaro_1t"] for c in com22)
        l22 = sum(c["r2022"]["lula_1t"] for c in com22)
        v22 = sum(c["r2022"]["validos_1t"] or 0 for c in com22)
        b22_2 = sum(c["r2022"]["bolsonaro_2t"] for c in com22)
        l22_2 = sum(c["r2022"]["lula_2t"] for c in com22)
        v22_2 = sum(c["r2022"]["validos_2t"] or 0 for c in com22)
        linha = {
            chave: nome,
            "cidades": len(membros),
            "eleitores": te,
            "comparecimento": comp,
            "pct_comparecimento": pct(comp, te, CASAS),
            "validos": vv,
            "votos": votos,
            "pct": {k: pct(v, vv, CASAS) for k, v in votos.items()},
            "r2022_mesmas_cidades": {
                "cidades": len(com22),
                "pct_bolsonaro_1t": pct(b22, v22, CASAS),
                "pct_lula_1t": pct(l22, v22, CASAS),
                "pct_bolsonaro_2t": pct(b22_2, v22_2, CASAS),
                "pct_lula_2t": pct(l22_2, v22_2, CASAS),
            },
        }
        linha["swing_flavio_vs_bolsonaro_1t_pp"] = dif(
            linha["pct"]["flavio"], linha["r2022_mesmas_cidades"]["pct_bolsonaro_1t"]
        )
        linha["swing_lula_vs_lula_1t_pp"] = dif(
            linha["pct"]["lula"], linha["r2022_mesmas_cidades"]["pct_lula_1t"]
        )
        if chave == "pais":
            linha["pais_nome"] = pais_nome(nome)
            linha["continente"] = continente(nome)
        saida.append(linha)
    return sorted(saida, key=lambda x: -x["validos"])


def montar(ctx: Contexto) -> dict[str, Any]:
    cidades = _cidades(ctx)
    total_snap = ctx.ufs["zz"].vigente
    deslocadas = sorted(
        (c for c in cidades if c["deslocamento_aparente_h"] is not None),
        key=lambda c: -c["deslocamento_aparente_h"],
    )
    continentes = _agregar(cidades, "continente")
    ordem = {nome: i for i, nome in enumerate(CONTINENTES)}
    continentes.sort(key=lambda x: ordem[x["continente"]])
    return {
        "nota_continentes": (
            "Continentes pela divisão M49 da ONU, com a América em três partes; a tabela "
            "está em scripts/apuracao_2026/dados.py (PAISES)."
        ),
        "total": {
            "cidades": len(cidades),
            "paises": len({c["pais"] for c in cidades}),
            "secoes": total_snap["st"],
            "eleitores": total_snap["te"],
            "comparecimento": total_snap["comparecimento"],
            "pct_comparecimento": pct(
                total_snap["comparecimento"], total_snap["te"], CASAS
            ),
            "validos": total_snap["vv"],
        },
        "cidades": cidades,
        "paises": _agregar(cidades, "pais"),
        "continentes": continentes,
        "hora_local": {
            "nota": (
                "O TSE imprime a hora de totalização no relógio local da cidade. Lida como "
                "Brasília, ela fica deslocada da hora de geração do arquivo pelo fuso da "
                "cidade (menos o atraso de geração). fuso_utc_inferido só aparece quando o "
                "deslocamento cai a menos de 15 minutos de uma hora inteira."
            ),
            "mais_adiantadas": [
                {
                    k: c[k]
                    for k in (
                        "nome",
                        "pais_nome",
                        "totalizacao_impressa",
                        "primeira_versao_totalizada_gerada_brt",
                        "deslocamento_aparente_h",
                        "fuso_utc_inferido",
                    )
                }
                for c in deslocadas[:12]
            ],
            "mais_atrasadas": [
                {
                    k: c[k]
                    for k in (
                        "nome",
                        "pais_nome",
                        "totalizacao_impressa",
                        "primeira_versao_totalizada_gerada_brt",
                        "deslocamento_aparente_h",
                        "fuso_utc_inferido",
                    )
                }
                for c in deslocadas[-8:]
            ],
            "cidades_com_data_impressa_de_05_10_e_arquivo_de_04_10": sum(
                1
                for c in cidades
                if (c["totalizacao_impressa"] or "").startswith("05/10")
                and (c["primeira_versao_totalizada_gerada_brt"] or "").startswith(
                    "2026-10-04"
                )
            ),
            "cidades_com_hora_impressa_antes_da_geracao_em_mais_de_1h": sum(
                1
                for c in cidades
                if c["deslocamento_aparente_h"] is not None
                and c["deslocamento_aparente_h"] < -1
            ),
        },
    }
