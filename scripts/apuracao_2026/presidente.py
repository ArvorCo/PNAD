"""`presidente.json`: resultado final, UFs, regiões, municípios e capitais contra 2022."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .contexto import (
    CHAVE_NACIONAL,
    CHAVES_2022,
    ELE_EST,
    ELE_FED,
    NOME_UF,
    ORDEM_2026,
    UFS,
    Contexto,
    numero_do_municipio,
)
from .dados import (
    GRUPOS,
    REGIOES,
    brt,
    colunar,
    dif,
    entradas_ab,
    extremos,
    grupo_regional,
    pct,
    regiao,
    swing,
)

CASAS = 6


def _r(x: float | None, casas: int = CASAS) -> float | None:
    return None if x is None else round(x, casas)


def bloco_2026(snap: dict[str, Any], votos: dict[str, int]) -> dict[str, Any]:
    """Totais e votos agrupados de uma versão de resultado de 2026."""
    vv = snap["vv"] or 0
    comp = snap["comparecimento"] or 0
    agrupados = dict(votos)
    agrupados["terceiros"] = vv - votos["flavio"] - votos["lula"]
    return {
        "secoes": snap["st"],
        "secoes_total": snap["ts"],
        "eleitores": snap["te"],
        "comparecimento": comp,
        "pct_comparecimento": pct(comp, snap["te"], CASAS),
        "abstencao": snap["abstencao"],
        "validos": vv,
        "brancos": snap["vb"],
        "nulos": snap["tvn"],
        "pct_brancos": pct(snap["vb"], comp, CASAS),
        "pct_nulos": pct(snap["tvn"], comp, CASAS),
        "votos": agrupados,
        "pct": {k: pct(v, vv, CASAS) for k, v in agrupados.items()},
    }


def bloco_2022(r: dict[str, Any]) -> dict[str, Any]:
    """Resultado de 2022 (arquivo da API do TSE) com as mesmas chaves curtas."""
    vv = r["validos"]
    votos = {nome: r["votos"].get(numero, 0) for numero, nome in CHAVES_2022.items()}
    votos["terceiros"] = vv - votos["bolsonaro"] - votos["lula"]
    return {
        "arquivo": r["arquivo"],
        "eleitores": r["eleitores"],
        "comparecimento": r["comparecimento"],
        "pct_comparecimento": pct(r["comparecimento"], r["eleitores"], CASAS),
        "validos": vv,
        "brancos": r["brancos"],
        "nulos": r["nulos"],
        "votos": votos,
        "pct": {k: pct(v, vv, CASAS) for k, v in votos.items()},
    }


def comparar(
    b26: dict[str, Any], t1: dict[str, Any], t2: dict[str, Any]
) -> dict[str, Any]:
    """Flávio contra Bolsonaro e Lula contra Lula, nos dois turnos de 2022."""
    v26, vv26 = b26["votos"], b26["validos"]
    saida: dict[str, Any] = {}
    for rotulo, ref in (("1t", t1), ("2t", t2)):
        saida[f"flavio_vs_bolsonaro_{rotulo}"] = swing(
            v26["flavio"], vv26, ref["votos"]["bolsonaro"], ref["validos"], CASAS
        )
        saida[f"lula_vs_lula_{rotulo}"] = swing(
            v26["lula"], vv26, ref["votos"]["lula"], ref["validos"], CASAS
        )
        margem22 = dif(ref["pct"]["bolsonaro"], ref["pct"]["lula"])
        saida[f"margem_direita_2022_{rotulo}_pp"] = margem22
    margem26 = dif(b26["pct"]["flavio"], b26["pct"]["lula"])
    saida["margem_flavio_lula_2026_pp"] = margem26
    saida["virada_margem_vs_1t_pp"] = dif(margem26, saida["margem_direita_2022_1t_pp"])
    saida["virada_margem_vs_2t_pp"] = dif(margem26, saida["margem_direita_2022_2t_pp"])
    saida["terceiros_vs_1t_pp"] = dif(b26["pct"]["terceiros"], t1["pct"]["terceiros"])
    saida["comparecimento_vs_1t_pp"] = dif(
        b26["pct_comparecimento"], t1["pct_comparecimento"]
    )
    saida["comparecimento_vs_2t_pp"] = dif(
        b26["pct_comparecimento"], t2["pct_comparecimento"]
    )
    saida["eleitores_variacao"] = b26["eleitores"] - t1["eleitores"]
    return saida


def _soma(blocos: list[dict[str, Any]], chaves: tuple[str, ...]) -> dict[str, Any]:
    """Soma blocos de 2026 ou de 2022 e recalcula as fatias."""
    total: dict[str, Any] = dict.fromkeys(("eleitores", "comparecimento", "validos"), 0)
    votos: dict[str, int] = dict.fromkeys(chaves, 0)
    for b in blocos:
        for k in total:
            total[k] += b[k] or 0
        for k in chaves:
            votos[k] += b["votos"].get(k, 0)
    total["votos"] = votos
    total["pct"] = {k: pct(v, total["validos"], CASAS) for k, v in votos.items()}
    total["pct_comparecimento"] = pct(
        total["comparecimento"], total["eleitores"], CASAS
    )
    return total


def nacional(ctx: Contexto) -> dict[str, Any]:
    snap = ctx.nacional.vigente
    votos_sq = ctx.votos_vigentes[snap["id"]]
    bloco = bloco_2026(snap, ctx.agrupar(votos_sq))
    candidaturas = []
    for sq, vap in sorted(votos_sq.items(), key=lambda kv: -kv[1]):
        c = ctx.candidatos[sq]
        candidaturas.append(
            {
                "sqcand": sq,
                "numero": c["numero"],
                "nome": c["nome_urna"],
                "partido": c["partido"],
                "chave": ctx.chave_de[sq],
                "votos": vap,
                "pct_validos": pct(vap, snap["vv"], CASAS),
            }
        )
    flavio, lula = bloco["votos"]["flavio"], bloco["votos"]["lula"]
    return {
        "arquivo": CHAVE_NACIONAL,
        "snapshot_id": snap["id"],
        "gerado_em": snap["gerado_em"],
        "gerado_em_brt": brt(snap["gerado_em"]),
        "capturado_em_brt": brt(snap["capturado_em"]),
        "versoes_capturadas": len(ctx.nacional.snapshots),
        "versoes_genuinas": len(ctx.nacional.versoes),
        **bloco,
        "nulos_tecnicos": snap["vnt"],
        "candidaturas": candidaturas,
        "diferenca_votos": flavio - lula,
        "diferenca_pp": pct(flavio - lula, snap["vv"], CASAS),
    }


def ufs(ctx: Contexto) -> list[dict[str, Any]]:
    saida = []
    for uf in [*UFS, "zz"]:
        arq = ctx.ufs[uf]
        snap = arq.vigente
        b26 = bloco_2026(snap, ctx.agrupar(ctx.votos_vigentes[snap["id"]]))
        t1 = bloco_2022(ctx.api2022[uf][1])
        t2 = bloco_2022(ctx.api2022[uf][2])
        lider = "flavio" if b26["votos"]["flavio"] >= b26["votos"]["lula"] else "lula"
        saida.append(
            {
                "uf": uf.upper(),
                "nome": NOME_UF[uf],
                "regiao": regiao(uf),
                "grupo": grupo_regional(uf),
                "snapshot_id": snap["id"],
                "gerado_em_brt": brt(snap["gerado_em"]),
                **b26,
                "lider": lider,
                "margem_votos": b26["votos"]["flavio"] - b26["votos"]["lula"],
                "r2022": {"t1": t1, "t2": t2},
                "comparacao": comparar(b26, t1, t2),
            }
        )
    return saida


def regioes(lista_ufs: list[dict[str, Any]], nac: dict[str, Any]) -> dict[str, Any]:
    """Agregados por grupo (Nordeste, Norte, Centro-Sul) e por grande região."""
    chaves26 = (*ORDEM_2026, "terceiros")
    chaves22 = (*CHAVES_2022.values(), "terceiros")
    grupos: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for u in lista_ufs:
        for nome in {u["grupo"], u["regiao"]}:
            grupos[nome].append(u)
        if u["uf"] != "ZZ":
            grupos["Brasil sem exterior"].append(u)
        grupos["Brasil"].append(u)
    nomes = [*GRUPOS, *REGIOES, "Exterior", "Brasil sem exterior", "Brasil"]
    saida: dict[str, Any] = {}
    tot26 = _soma(grupos["Brasil"], chaves26)
    tot22 = {
        t: _soma([u["r2022"][t] for u in grupos["Brasil"]], chaves22)
        for t in ("t1", "t2")
    }
    for nome in nomes:
        membros = grupos[nome]
        b26 = _soma(membros, chaves26)
        t1 = _soma([u["r2022"]["t1"] for u in membros], chaves22)
        t2 = _soma([u["r2022"]["t2"] for u in membros], chaves22)
        comp = comparar(b26, t1, t2)
        contrib = {
            "flavio_menos_bolsonaro_1t": _parcela(
                b26["votos"]["flavio"] - t1["votos"]["bolsonaro"],
                tot26["votos"]["flavio"] - tot22["t1"]["votos"]["bolsonaro"],
            ),
            "lula_menos_lula_1t": _parcela(
                b26["votos"]["lula"] - t1["votos"]["lula"],
                tot26["votos"]["lula"] - tot22["t1"]["votos"]["lula"],
            ),
            "fatia_validos_2026": pct(b26["validos"], tot26["validos"], CASAS),
            "fatia_validos_2022_1t": pct(t1["validos"], tot22["t1"]["validos"], CASAS),
        }
        saida[nome] = {
            "ufs": [u["uf"] for u in membros],
            "r2026": b26,
            "r2022": {"t1": t1, "t2": t2},
            "comparacao": comp,
            "contribuicao_pct_da_variacao_nacional": contrib,
        }
    if saida["Brasil"]["r2026"]["validos"] != nac["validos"]:
        raise RuntimeError("soma das UFs difere do arquivo nacional em válidos")
    return saida


def _parcela(parte: int, total: int) -> float | None:
    return pct(parte, total, CASAS) if total else None


COLUNAS_MUN = (
    "cd_tse",
    "ibge",
    "uf",
    "nome",
    "capital",
    "regiao",
    "grupo",
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
    "terceiros",
    "pct_flavio",
    "pct_lula",
    "pct_terceiros",
    "eleitores_2022",
    "comparecimento_2022",
    "pct_comparecimento_2022",
    "validos_2022_1t",
    "bolsonaro_2022_1t",
    "lula_2022_1t",
    "pct_bolsonaro_2022_1t",
    "pct_lula_2022_1t",
    "validos_2022_2t",
    "bolsonaro_2022_2t",
    "lula_2022_2t",
    "pct_bolsonaro_2022_2t",
    "pct_lula_2022_2t",
    "swing_flavio_pp",
    "swing_lula_pp",
    "virada_margem_pp",
    "delta_votos_flavio",
    "delta_votos_lula",
    "delta_comparecimento_pp",
    "snapshot_id",
    "gerado_em_brt",
)


def linha_municipio(ctx: Contexto, cd: str) -> dict[str, Any]:
    arq = ctx.municipios[cd]
    snap = arq.vigente
    cad = ctx.cadastro[cd]
    votos = ctx.agrupar(ctx.votos_vigentes[snap["id"]])
    vv = snap["vv"] or 0
    linha: dict[str, Any] = {
        "cd_tse": cd,
        "ibge": cad["ibge"],
        "uf": cad["uf"].upper(),
        "nome": cad["nome"],
        "capital": bool(cad["capital"]),
        "regiao": regiao(cad["uf"]),
        "grupo": grupo_regional(cad["uf"]),
        "completo": snap["st"] == snap["ts"],
        "secoes": snap["st"],
        "secoes_total": snap["ts"],
        "eleitores": snap["te"],
        "comparecimento": snap["comparecimento"],
        "pct_comparecimento": pct(snap["comparecimento"], snap["te"]),
        "validos": vv,
        "brancos": snap["vb"],
        "nulos": snap["tvn"],
        **votos,
        "terceiros": vv - votos["flavio"] - votos["lula"],
        "snapshot_id": snap["id"],
        "gerado_em_brt": brt(snap["gerado_em"]),
    }
    linha["pct_flavio"] = pct(votos["flavio"], vv)
    linha["pct_lula"] = pct(votos["lula"], vv)
    linha["pct_terceiros"] = pct(linha["terceiros"], vv)
    numero = numero_do_municipio(cd)
    r22 = ctx.mun2022.get(numero)
    d22 = ctx.det2022[1].get(numero)
    if d22:
        linha["eleitores_2022"] = d22["aptos"]
        linha["comparecimento_2022"] = d22["comparecimento"]
        linha["pct_comparecimento_2022"] = pct(d22["comparecimento"], d22["aptos"])
        linha["delta_comparecimento_pp"] = dif(
            linha["pct_comparecimento"], linha["pct_comparecimento_2022"]
        )
    if r22:
        t1, t2 = r22["t1"], r22["t2"]
        linha["validos_2022_1t"] = t1.get("validos")
        linha["bolsonaro_2022_1t"] = t1.get("22", 0)
        linha["lula_2022_1t"] = t1.get("13", 0)
        linha["pct_bolsonaro_2022_1t"] = pct(t1.get("22", 0), t1.get("validos"))
        linha["pct_lula_2022_1t"] = pct(t1.get("13", 0), t1.get("validos"))
        linha["validos_2022_2t"] = t2.get("validos")
        linha["bolsonaro_2022_2t"] = t2.get("22", 0)
        linha["lula_2022_2t"] = t2.get("13", 0)
        linha["pct_bolsonaro_2022_2t"] = pct(t2.get("22", 0), t2.get("validos"))
        linha["pct_lula_2022_2t"] = pct(t2.get("13", 0), t2.get("validos"))
        linha["swing_flavio_pp"] = dif(
            linha["pct_flavio"], linha["pct_bolsonaro_2022_1t"]
        )
        linha["swing_lula_pp"] = dif(linha["pct_lula"], linha["pct_lula_2022_1t"])
        linha["virada_margem_pp"] = dif(
            linha["swing_flavio_pp"], linha["swing_lula_pp"]
        )
        linha["delta_votos_flavio"] = votos["flavio"] - linha["bolsonaro_2022_1t"]
        linha["delta_votos_lula"] = votos["lula"] - linha["lula_2022_1t"]
    return linha


def municipios(ctx: Contexto) -> list[dict[str, Any]]:
    cds = sorted(
        (cd for cd, a in ctx.municipios.items() if a.uf != "zz"),
        key=lambda cd: (ctx.cadastro[cd]["uf"], ctx.cadastro[cd]["nome"]),
    )
    return [linha_municipio(ctx, cd) for cd in cds]


CAMPOS_EXTREMO = ("cd_tse", "nome", "uf", "eleitores", "pct_flavio", "pct_lula")


def maiores_variacoes(linhas: list[dict[str, Any]], n: int = 30) -> dict[str, Any]:
    """As n maiores variações em cada direção, com e sem piso de eleitorado."""
    completos = [x for x in linhas if x["completo"]]
    piso = {"eleitores": 10_000}
    return {
        "nota": (
            "Só municípios com o arquivo presidencial completo; pontos percentuais dos "
            "válidos contra o 1º turno de 2022. O piso de 10 mil eleitores tira o ruído "
            "de municípios muito pequenos."
        ),
        "swing_flavio_pp": extremos(completos, "swing_flavio_pp", n, CAMPOS_EXTREMO),
        "swing_flavio_pp_10mil": extremos(
            completos, "swing_flavio_pp", n, CAMPOS_EXTREMO, piso
        ),
        "swing_lula_pp": extremos(completos, "swing_lula_pp", n, CAMPOS_EXTREMO),
        "swing_lula_pp_10mil": extremos(
            completos, "swing_lula_pp", n, CAMPOS_EXTREMO, piso
        ),
        "virada_margem_pp_10mil": extremos(
            completos, "virada_margem_pp", n, CAMPOS_EXTREMO, piso
        ),
        "delta_votos_flavio": extremos(
            completos, "delta_votos_flavio", n, CAMPOS_EXTREMO
        ),
        "delta_votos_lula": extremos(completos, "delta_votos_lula", n, CAMPOS_EXTREMO),
    }


def _secoes_governador(ctx: Contexto, uf: str, cd: str) -> list[int | None]:
    """Seções totalizadas e total no arquivo municipal de governador (mesmo município)."""
    vig = ctx.banco.versoes_de(f"u:{ELE_EST}:3:mu:{uf}:{cd}:")[-1]
    return [vig["st"], vig["ts"]]


def conferencia(
    ctx: Contexto, linhas: list[dict[str, Any]], nac: dict[str, Any]
) -> dict:
    """Soma dos municípios e das UFs contra o arquivo nacional."""
    soma_uf = dict.fromkeys(("secoes", "comparecimento", "validos", *ORDEM_2026), 0)
    for arq in ctx.ufs.values():
        snap = arq.vigente
        votos = ctx.agrupar(ctx.votos_vigentes[snap["id"]])
        soma_uf["secoes"] += snap["st"]
        soma_uf["comparecimento"] += snap["comparecimento"]
        soma_uf["validos"] += snap["vv"]
        for k in ORDEM_2026:
            soma_uf[k] += votos[k]
    soma_mun = dict.fromkeys(soma_uf, 0)
    for arq in ctx.municipios.values():
        snap = arq.vigente
        votos = ctx.agrupar(ctx.votos_vigentes[snap["id"]])
        soma_mun["secoes"] += snap["st"]
        soma_mun["comparecimento"] += snap["comparecimento"]
        soma_mun["validos"] += snap["vv"]
        for k in ORDEM_2026:
            soma_mun[k] += votos[k]
    alvo = {
        "secoes": nac["secoes"],
        "comparecimento": nac["comparecimento"],
        "validos": nac["validos"],
        **{k: nac["votos"][k] for k in ORDEM_2026},
    }
    incompletos = []
    andamento: dict[str, dict[str, dict[str, Any]]] = {}
    for x in linhas:
        if x["completo"]:
            continue
        arq = ctx.municipios[x["cd_tse"]]
        uf = arq.uf or ""
        if uf not in andamento:
            final_ab = ctx.banco.versoes_de(f"ab:{ELE_FED}::uf:{uf}::")[-1]
            andamento[uf] = entradas_ab(ctx.banco.documento(final_ab["sha256"]))
            ctx.banco.esquecer_documentos()
        ab = andamento[uf].get(x["cd_tse"], {})
        depois = ctx.banco.leituras(arq.id, arq.vigente["capturado_em"], "9999")
        incompletos.append(
            {
                "cd_tse": x["cd_tse"],
                "uf": x["uf"],
                "nome": x["nome"],
                "secoes": x["secoes"],
                "secoes_total": x["secoes_total"],
                "secoes_no_andamento_ab": ab.get("st"),
                "secoes_governador": _secoes_governador(ctx, uf, x["cd_tse"]),
                "gerado_em_brt": x["gerado_em_brt"],
                "leituras_depois_da_ultima_versao": depois["por_classe"],
                "ultima_leitura_brt": (
                    brt(depois["ultima"]) if depois["ultima"] else None
                ),
            }
        )
    sem_2022 = [
        {"cd_tse": x["cd_tse"], "uf": x["uf"], "nome": x["nome"]}
        for x in linhas
        if x.get("bolsonaro_2022_1t") is None
    ]
    return {
        "soma_ufs_menos_nacional": {k: soma_uf[k] - alvo[k] for k in alvo},
        "soma_municipios_menos_nacional": {k: soma_mun[k] - alvo[k] for k in alvo},
        "municipios_incompletos": incompletos,
        "municipios_sem_2022": sem_2022,
        "nota": (
            "Os municípios incompletos têm o arquivo presidencial parado numa versão "
            "gerada entre "
            + (min(x["gerado_em_brt"] for x in incompletos) if incompletos else "-")
            + " e "
            + (max(x["gerado_em_brt"] for x in incompletos) if incompletos else "-")
            + " (Brasília); o andamento (-ab) da UF já os dava completos e as "
            "requisições seguintes receberam 304 (não modificado)."
        ),
    }


FAIXAS_LULA_2022 = ((0, 30), (30, 45), (45, 55), (55, 70), (70, 101))


def por_faixa_lula_2022(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Municípios agrupados pela fatia de Lula no 1º turno de 2022.

    Só municípios completos e com 2022; somas de votos, não médias de municípios.
    """
    saida = []
    for baixo, alto in FAIXAS_LULA_2022:
        grupo = [
            x
            for x in linhas
            if x["completo"]
            and x.get("pct_lula_2022_1t") is not None
            and baixo <= x["pct_lula_2022_1t"] < alto
        ]
        soma = {
            k: sum(x.get(k) or 0 for x in grupo)
            for k in (
                "eleitores",
                "comparecimento",
                "validos",
                "flavio",
                "lula",
                "terceiros",
                "eleitores_2022",
                "comparecimento_2022",
                "validos_2022_1t",
                "bolsonaro_2022_1t",
                "lula_2022_1t",
            )
        }
        pf, pb = pct(soma["flavio"], soma["validos"]), pct(
            soma["bolsonaro_2022_1t"], soma["validos_2022_1t"]
        )
        pl, pl22 = pct(soma["lula"], soma["validos"]), pct(
            soma["lula_2022_1t"], soma["validos_2022_1t"]
        )
        comp = pct(soma["comparecimento"], soma["eleitores"])
        comp22 = pct(soma["comparecimento_2022"], soma["eleitores_2022"])
        saida.append(
            {
                "faixa_lula_2022_pct": f"{baixo} a {min(alto, 100)}",
                "municipios": len(grupo),
                **soma,
                "pct_flavio": pf,
                "pct_bolsonaro_2022_1t": pb,
                "swing_flavio_pp": dif(pf, pb),
                "pct_lula": pl,
                "pct_lula_2022_1t": pl22,
                "swing_lula_pp": dif(pl, pl22),
                "pct_comparecimento": comp,
                "pct_comparecimento_2022": comp22,
                "delta_comparecimento_pp": dif(comp, comp22),
                "delta_votos_flavio": soma["flavio"] - soma["bolsonaro_2022_1t"],
                "delta_votos_lula": soma["lula"] - soma["lula_2022_1t"],
            }
        )
    return saida


def capitais(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((x for x in linhas if x["capital"]), key=lambda x: x["uf"])


def montar(ctx: Contexto) -> dict[str, Any]:
    nac = nacional(ctx)
    lista_ufs = ufs(ctx)
    mun = municipios(ctx)
    br22 = {t: bloco_2022(ctx.api2022["br"][t]) for t in (1, 2)}
    return {
        "nacional": {
            **nac,
            "r2022": {"t1": br22[1], "t2": br22[2]},
            "comparacao": comparar(nac, br22[1], br22[2]),
        },
        "ufs": lista_ufs,
        "regioes": regioes(lista_ufs, nac),
        "municipios": colunar(COLUNAS_MUN, mun),
        "maiores_variacoes": maiores_variacoes(mun),
        "capitais": capitais(mun),
        "por_faixa_lula_2022": por_faixa_lula_2022(mun),
        "conferencia": conferencia(ctx, mun, nac),
    }
