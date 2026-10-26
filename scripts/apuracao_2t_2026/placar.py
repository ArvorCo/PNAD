"""Placar final do 2º turno (presidente) por Brasil, UF, região e município, e exterior."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from apuracao_2026.dados import continente, pais_nome

from .base import (
    NOME_UF,
    ROTULO,
    colunar,
    d2,
    hhmm,
    p2,
    placar,
    regiao_de,
    sigla_regiao,
    somar_placares,
    totalizado_corrigido,
)
from .carga import Contexto

COLUNAS_MUN = (
    "cd_tse",
    "ibge",
    "uf",
    "nome",
    "capital",
    "regiao",
    "secoes",
    "secoes_total",
    "pst",
    "completo",
    "aptos",
    "aptos_apurados",
    "comparecimento",
    "abstencao",
    "validos",
    "brancos",
    "nulos",
    "flavio",
    "lula",
    "pct_flavio",
    "pct_lula",
    "margem_lula_pp",
    "pct_comparecimento",
    "pct_abstencao",
    "pct_brancos",
    "pct_nulos",
    "fechou_min",
    "fechou_hhmm",
    "gerado_brt",
)


def linhas_municipais(ctx: Contexto) -> list[dict[str, Any]]:
    """Uma linha por município (inclusive exterior), com o placar vigente."""
    saida = []
    for r in ctx.mus:
        cd = r["municipio_cd"]
        meta = ctx.meta_mun.get(cd, {})
        uf = r["uf"].upper()
        fe = ctx.fechou.get(cd)
        linha = {
            "cd_tse": cd,
            "ibge": meta.get("ibge"),
            "uf": uf,
            "nome": meta.get("nome"),
            "capital": bool(meta.get("capital")),
            "regiao": regiao_de(uf),
            **placar(r),
            "fechou_min": fe["min"] if fe else None,
            "fechou_hhmm": hhmm(fe["min"]) if fe else None,
        }
        saida.append(linha)
    return saida


def _linha_uf(ctx: Contexto, r: dict[str, Any]) -> dict[str, Any]:
    uf = r["uf"].upper()
    corr = totalizado_corrigido(uf, r["totalizado_em"], r["gerado_em"])
    return {
        "uf": uf,
        "nome": NOME_UF[uf],
        "regiao": regiao_de(uf),
        **placar(r),
        "totalizacao_impressa": f"{r['dt']} {r['ht']}" if r["dt"] else None,
        "totalizado_em_corrigido": corr,
    }


def presidente(ctx: Contexto, municipios: list[dict[str, Any]]) -> dict[str, Any]:
    nacional = placar(ctx.br)
    ufs = sorted((_linha_uf(ctx, r) for r in ctx.ufs), key=lambda u: u["uf"])
    brasil_ufs = [u for u in ufs if u["uf"] != "ZZ"]
    regioes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for u in ufs:
        regioes[u["regiao"]].append(u)
    blocos = []
    for nome in ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Exterior"):
        lista = regioes.get(nome, [])
        blocos.append(
            {
                "sigla": sigla_regiao(lista[0]["uf"]) if lista else None,
                "regiao": nome,
                "ufs": [u["uf"] for u in lista],
                **somar_placares(lista),
            }
        )
    soma_ufs = somar_placares(ufs)
    soma_mun = somar_placares(municipios)
    campos_conf = (
        "secoes",
        "comparecimento",
        "abstencao",
        "validos",
        "brancos",
        "nulos",
        "flavio",
        "lula",
    )
    por_uf_mun: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in municipios:
        por_uf_mun[m["uf"]].append(m)
    conf_uf = []
    for u in ufs:
        s = somar_placares(por_uf_mun[u["uf"]])
        dif = {k: s[k] - u[k] for k in campos_conf}
        if any(dif.values()):
            conf_uf.append({"uf": u["uf"], **dif})
    sem_exterior = somar_placares(brasil_ufs)
    incompletos = [
        {k: m[k] for k in ("cd_tse", "uf", "nome", "secoes", "secoes_total", "aptos")}
        for m in municipios
        if not m["completo"]
    ]
    return {
        "rotulo": ROTULO,
        "definicoes": {
            "fatias": "Flávio e Lula sobre os votos válidos (pct_flavio, pct_lula)",
            "abstencao": (
                "sobre o eleitorado das seções já totalizadas (aptos_apurados = "
                "comparecimento + abstenção); aptos = eleitorado total do arquivo"
            ),
            "brancos_nulos": "sobre o comparecimento",
            "identidade": "aptos_apurados = válidos + brancos + nulos + abstenção",
            "margem_lula_pp": "Lula menos Flávio, em pontos dos válidos",
            "fechou_min": (
                "minutos após 17:00 de Brasília (25/10) da primeira versão gerada "
                "com todas as seções do município totalizadas"
            ),
        },
        "nacional": {
            "arquivo": ctx.br["chave"],
            "totalizacao_impressa": f"{ctx.br['dt']} {ctx.br['ht']}",
            **nacional,
        },
        "sem_exterior": sem_exterior,
        "exterior": next((u for u in ufs if u["uf"] == "ZZ"), None),
        "ufs": ufs,
        "regioes": blocos,
        "municipios": colunar(COLUNAS_MUN, (m for m in municipios if m["uf"] != "ZZ")),
        "capitais": [m for m in municipios if m["capital"]],
        "conferencia": {
            "soma_ufs_menos_nacional": {
                k: soma_ufs[k] - nacional[k] for k in campos_conf
            },
            "soma_municipios_menos_nacional": {
                k: soma_mun[k] - nacional[k] for k in campos_conf
            },
            "soma_municipios_menos_uf": conf_uf,
            "municipios_total": len(municipios),
            "municipios_incompletos": incompletos,
            "nota": (
                "Os arquivos de UF, de município e o nacional têm versões geradas em "
                "instantes diferentes; diferença não nula enquanto há seções por "
                "totalizar é defasagem de publicação, não divergência."
            ),
        },
    }


def exterior(ctx: Contexto, municipios: list[dict[str, Any]]) -> dict[str, Any]:
    cidades = []
    for m in municipios:
        if m["uf"] != "ZZ":
            continue
        r1 = ctx.ext_1t.get(m["cd_tse"], {})
        pais = r1.get("pais")
        fe = ctx.fechou.get(m["cd_tse"])
        v1 = r1.get("votos", {})
        validos1 = r1.get("validos")
        comp1, apt1 = r1.get("comparecimento"), r1.get("eleitores")
        pf1 = p2(v1.get("flavio"), validos1)
        pl1 = p2(v1.get("lula"), validos1)
        cidades.append(
            {
                **{
                    k: m[k]
                    for k in COLUNAS_MUN
                    if k not in ("ibge", "capital", "regiao")
                },
                "pais": pais,
                "pais_nome": pais_nome(pais) if pais else None,
                "continente": continente(pais) if pais else None,
                "totalizacao_impressa_local": (
                    f"{fe['dt']} {fe['ht']}" if fe and fe["dt"] else None
                ),
                "fechou_gerado_brt": m["fechou_hhmm"],
                "t1_aptos": apt1,
                "t1_comparecimento": comp1,
                "t1_validos": validos1,
                "t1_flavio": v1.get("flavio"),
                "t1_lula": v1.get("lula"),
                "t1_pct_flavio": pf1,
                "t1_pct_lula": pl1,
                "t1_pct_comparecimento": p2(comp1, apt1),
                "delta_comparecimento_pp": d2(m["pct_comparecimento"], p2(comp1, apt1)),
                "delta_votos_flavio": (
                    m["flavio"] - v1["flavio"] if "flavio" in v1 else None
                ),
                "delta_votos_lula": m["lula"] - v1["lula"] if "lula" in v1 else None,
                "swing_flavio_pp": d2(m["pct_flavio"], pf1),
                "swing_lula_pp": d2(m["pct_lula"], pl1),
            }
        )
    cidades.sort(key=lambda c: -(c["aptos"] or 0))

    def agrupar(chave: str) -> list[dict[str, Any]]:
        grupos: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for c in cidades:
            grupos[c[chave] or "sem_pais"].append(c)
        saida = []
        for k, lista in grupos.items():
            s = somar_placares(lista)
            t1v = sum(c["t1_validos"] or 0 for c in lista)
            t1f = sum(c["t1_flavio"] or 0 for c in lista)
            t1l = sum(c["t1_lula"] or 0 for c in lista)
            t1c = sum(c["t1_comparecimento"] or 0 for c in lista)
            t1a = sum(c["t1_aptos"] or 0 for c in lista)
            saida.append(
                {
                    chave: k,
                    "cidades": len(lista),
                    **{
                        x: s[x]
                        for x in (
                            "secoes",
                            "secoes_total",
                            "aptos",
                            "comparecimento",
                            "abstencao",
                            "validos",
                            "brancos",
                            "nulos",
                            "flavio",
                            "lula",
                            "pct_flavio",
                            "pct_lula",
                            "pct_comparecimento",
                        )
                    },
                    "t1_pct_flavio": p2(t1f, t1v),
                    "t1_pct_lula": p2(t1l, t1v),
                    "t1_pct_comparecimento": p2(t1c, t1a),
                    "delta_comparecimento_pp": d2(
                        s["pct_comparecimento"], p2(t1c, t1a)
                    ),
                }
            )
        return sorted(saida, key=lambda g: -(g["aptos"] or 0))

    zz = next((u for u in ctx.ufs if u["uf"] == "zz"), None)
    fechadas = [c for c in cidades if c["fechou_min"] is not None]
    abertas = [c for c in cidades if not c["completo"]]
    return {
        "rotulo": ROTULO,
        "nota_horario": (
            "A totalização impressa (dt e ht) do exterior está no relógio local da "
            "cidade; fechou_min e fechou_gerado_brt vêm da hora de geração do arquivo "
            "pelo TSE, em Brasília."
        ),
        "total": {
            **somar_placares(cidades),
            "cidades": len(cidades),
            "cidades_fechadas": len(fechadas),
            "arquivo_uf_zz": placar(zz) if zz else None,
        },
        "cidades": cidades,
        "paises": agrupar("pais"),
        "continentes": agrupar("continente"),
        "ultimas_a_fechar": sorted(fechadas, key=lambda c: -c["fechou_min"])[:20],
        "abertas": [
            {k: c[k] for k in ("cd_tse", "nome", "pais_nome", "secoes", "secoes_total")}
            for c in abertas
        ],
    }
