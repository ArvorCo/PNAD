"""Índice de prioridade, listas, agregados, riscos e o nulo de 2022.

Recebe as linhas por município de ``terceira_via_secoes.municipios`` e devolve os
blocos do JSON. Contas elementares em ``terceira_via.py``.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from statistics import median
from typing import Any

from . import terceira_via as T
from .terceira_via_secoes import (
    GRANDE,
    MIN_COMPARECIMENTO_NULO,
    N_NULO,
    N_REGIAO,
    N_TOP,
    N_UF,
    REGIOES,
)

VARIAVEIS = {
    "vao_local": "vao_pp",
    "matriz": "saldo_por_voto",
    "ambiente_2022": "b22_2t_pct",
    "margem": "margem_pp",
}
SOMAS = (
    "eleitores",
    "comparecimento",
    "validos",
    "flavio",
    "lula",
    *T.GRUPOS,
    "estoque",
    "para_flavio",
    "para_lula",
    "fora",
    "saldo",
    "saldo_df",
)


def _r(x: float | None, casas: int = 2) -> float | None:
    return T.r2(x, casas)


def _i(x: float | None) -> int | None:
    return None if x is None else round(x)


# ---------------------------------------------------------------- prioridade


def aplicar_prioridade(brasil: list[dict]) -> None:
    """Posições, fator e prioridade (central e sensibilidades) em cada linha."""
    posicoes = {
        nome: T.percentis([m.get(campo) for m in brasil])
        for nome, campo in VARIAVEIS.items()
    }
    for i, m in enumerate(brasil):
        pos = {nome: posicoes[nome][i] for nome in VARIAVEIS}
        m["posicoes"] = pos
        m["fator"] = T.fator(pos, T.PESOS)
        m["prioridade"] = m["estoque"] * m["fator"]
        for nome, pesos in T.SENSIBILIDADES.items():
            m[f"prioridade_{nome}"] = m["estoque"] * T.fator(pos, pesos)
    for k, m in enumerate(T.ranking(brasil, "prioridade", len(brasil)), start=1):
        m["posicao"] = k


def carregadores(m: dict) -> list[dict]:
    """Nomes do bloco que rendem acima de Flávio ali (índice maior que 100)."""
    saida = [
        {
            "nome": x["nome"],
            "cargo": x["cargo"],
            "eleito": x.get("eleito", True),
            "indice": _r(x["indice"], 1),
            "votos": x["votos"],
        }
        for x in m["local_nomes"]
        if x["indice"] is not None and x["indice"] > 100
    ]
    return sorted(saida, key=lambda x: -x["indice"])


def item(m: dict) -> dict[str, Any]:
    """Linha compacta das listas (prioridade, teto, contrário)."""
    gov = next((x for x in m["local_nomes"] if x["cargo"] == "governador"), None)
    return {
        "posicao": m.get("posicao"),
        "cd": m["cd"],
        "ibge": m["ibge"],
        "uf": m["uf"],
        "nome": m["nome"],
        "regiao": m["regiao"],
        "capital": m["capital"],
        "eleitores": m["eleitores"],
        "comparecimento": m["comparecimento"],
        "estoque": m["estoque"],
        "estoque_pct": _r(m["estoque_pct"]),
        **{g: m[g] for g in T.GRUPOS},
        "margem_pp": _r(m["margem_pp"]),
        "classe": m["classe"],
        "b22_2t_pct": _r(m.get("b22_2t_pct")),
        "delta_bn22_pp": _r(m.get("delta_bn22_pp")),
        "para_flavio": _i(m["para_flavio"]),
        "para_lula": _i(m["para_lula"]),
        "fora": _i(m["fora"]),
        "saldo": _i(m["saldo"]),
        "saldo_df": _i(m["saldo_df"]),
        "local_lider": m["local_lider"],
        "vao_votos": m["vao_votos"],
        "vao_pp": _r(m["vao_pp"]),
        "governador": gov and {"nome": gov["nome"], "indice": _r(gov["indice"], 1)},
        "carregadores": carregadores(m),
        "teto": m["teto"],
        "fator": _r(m["fator"], 3),
        "posicoes": {k: _r(v, 3) for k, v in m["posicoes"].items()},
        "prioridade": _i(m["prioridade"]),
    }


def _resumo_top(linhas: Sequence[dict]) -> dict[str, Any]:
    s = T.somar(
        linhas,
        ("estoque", "saldo", "saldo_df", "fora", "para_flavio", "para_lula", "teto"),
    )
    por_regiao = defaultdict(int)
    por_classe = defaultdict(int)
    for m in linhas:
        por_regiao[m["regiao"]] += 1
        por_classe[m["classe"]] += 1
    return {
        "municipios": len(linhas),
        **{k: _i(v) for k, v in s.items()},
        "por_regiao": {r: por_regiao.get(r, 0) for r in REGIOES},
        "por_classe": {c: por_classe.get(c, 0) for c in T.CLASSES},
        "capitais": sum(1 for m in linhas if m["capital"]),
    }


def prioridade(brasil: list[dict], diferenca: int) -> dict[str, Any]:
    """Ranking nacional, os 10 por UF e por região, a soma dos 100 e as sensibilidades."""
    top = T.ranking(brasil, "prioridade", N_TOP)
    resumo = _resumo_top(top)
    resumo["saldo_sobre_diferenca_pct"] = _r(T.pct(resumo["saldo"], diferenca))
    resumo["fora_sobre_diferenca_pct"] = _r(T.pct(resumo["fora"], diferenca))
    por_uf: dict[str, list] = defaultdict(list)
    por_regiao: dict[str, list] = defaultdict(list)
    for m in T.ranking(brasil, "prioridade", len(brasil)):
        if len(por_uf[m["uf"]]) < N_UF:
            por_uf[m["uf"]].append(item(m))
        if len(por_regiao[m["regiao"]]) < N_REGIAO:
            por_regiao[m["regiao"]].append(item(m))
    centrais = [m["cd"] for m in top]
    sens = []
    for nome in T.SENSIBILIDADES:
        lista = T.ranking(brasil, f"prioridade_{nome}", N_TOP)
        r = _resumo_top(lista)
        sens.append(
            {
                "nome": nome,
                "pesos": T.SENSIBILIDADES[nome],
                "em_comum_com_central": T.sobreposicao(
                    centrais, (m["cd"] for m in lista)
                ),
                **r,
                "primeiros": [{"nome": m["nome"], "uf": m["uf"]} for m in lista[:10]],
            }
        )
    return {
        "pesos": T.PESOS,
        "variaveis": VARIAVEIS,
        "diferenca_nacional": diferenca,
        "top": [item(m) for m in top],
        "soma_top": resumo,
        "por_uf": dict(sorted(por_uf.items())),
        "por_regiao": {r: por_regiao[r] for r in REGIOES},
        "sensibilidade": sens,
    }


# ---------------------------------------------------------------- teto


def teto(brasil: list[dict]) -> dict[str, Any]:
    """Teto endereçável local: os 10 maiores por UF e as somas de cada UF."""
    por_uf: dict[str, list[dict]] = defaultdict(list)
    for m in brasil:
        por_uf[m["uf"]].append(m)
    ufs = {}
    for uf, lista in sorted(por_uf.items()):
        vao_pos = sum(max(0, m["vao_votos"]) for m in lista)
        estoque = sum(m["estoque"] for m in lista)
        top = T.ranking(lista, "teto", N_UF)
        ufs[uf] = {
            "estoque": estoque,
            "vao_positivo": vao_pos,
            "teto": estoque + vao_pos,
            "municipios_vao_positivo": sum(1 for m in lista if m["vao_votos"] > 0),
            "municipios": len(lista),
            "top": [item(m) for m in top],
            "top_teto": sum(m["teto"] for m in top),
        }
    return {
        "regra": "teto = votos de terceira via + max(0; votos da direita local − votos de Flávio), no município",
        "ufs": ufs,
        "nacional_top": [item(m) for m in T.ranking(brasil, "teto", 20)],
    }


# ---------------------------------------------------------------- agregados


def _agrega(linhas: Iterable[dict]) -> dict[str, Any]:
    linhas = list(linhas)
    s = T.somar(linhas, SOMAS)
    por_classe = {}
    for c in T.CLASSES:
        dentro = [m for m in linhas if m["classe"] == c]
        e = sum(m["estoque"] for m in dentro)
        por_classe[c] = {
            "municipios": len(dentro),
            "estoque": e,
            "estoque_parcela": _r(T.pct(e, s["estoque"])),
            "saldo": _i(sum(m["saldo"] for m in dentro)),
            "fora": _i(sum(m["fora"] for m in dentro)),
            **{g: sum(m[g] for m in dentro) for g in T.GRUPOS},
        }
    venceu = (
        por_classe["venceu_folga"]["estoque"] + por_classe["venceu_apertado"]["estoque"]
    )
    vao_pos = sum(max(0, m.get("vao_votos", 0)) for m in linhas)
    vao_estrito = sum(max(0, m.get("vao_votos_estrito", 0)) for m in linhas)
    return {
        "municipios": len(linhas),
        **{k: _i(v) for k, v in s.items()},
        "estoque_pct_validos": _r(T.pct(s["estoque"], s["validos"])),
        "por_grupo_pct": {g: _r(T.pct(s[g], s["estoque"])) for g in T.GRUPOS},
        "saldo_por_voto": _r(s["saldo"] / s["estoque"], 4) if s["estoque"] else None,
        "por_classe": por_classe,
        "onde_flavio_venceu": venceu,
        "onde_flavio_venceu_parcela": _r(T.pct(venceu, s["estoque"])),
        "vao_positivo": vao_pos,
        "vao_positivo_sem_governador_sem_apoio": vao_estrito,
        "municipios_vao_positivo": sum(1 for m in linhas if m.get("vao_votos", 0) > 0),
        "teto": s["estoque"] + vao_pos,
        "margem_pp": _r(T.pct(s["flavio"] - s["lula"], s["validos"])),
    }


def lideres(linhas: Iterable[dict], n: int = 5) -> list[dict]:
    """Quem da direita local mais passa Flávio: municípios e votos acima dele."""
    soma: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for m in linhas:
        if m.get("vao_votos", 0) > 0 and m.get("local_lider"):
            soma[m["local_lider"]][0] += 1
            soma[m["local_lider"]][1] += m["vao_votos"]
    ordem = sorted(soma.items(), key=lambda kv: (-kv[1][1], kv[0]))[:n]
    return [{"nome": k, "municipios": v[0], "vao_votos": v[1]} for k, v in ordem]


def agregados(brasil: list[dict], exterior: list[dict]) -> dict[str, Any]:
    nac = _agrega(brasil)
    nac["renan_zema_pct"] = _r(T.pct(nac["renan"] + nac["zema"], nac["estoque"]))
    nac["lideres"] = lideres(brasil, 10)
    por_regiao = {r: _agrega(m for m in brasil if m["regiao"] == r) for r in REGIOES}
    for r, a in por_regiao.items():
        a["parcela_do_estoque"] = _r(T.pct(a["estoque"], nac["estoque"]))
        a["renan_zema_pct"] = _r(T.pct(a["renan"] + a["zema"], a["estoque"]))
        a["regiao"] = r
        a["lideres"] = lideres(m for m in brasil if m["regiao"] == r)
    ufs = {}
    for uf in sorted({m["uf"] for m in brasil}):
        dentro = [m for m in brasil if m["uf"] == uf]
        a = _agrega(dentro)
        a["regiao"] = dentro[0]["regiao"]
        a["parcela_do_estoque"] = _r(T.pct(a["estoque"], nac["estoque"]))
        a["renan_zema_pct"] = _r(T.pct(a["renan"] + a["zema"], a["estoque"]))
        a["lideres"] = lideres(dentro, 3)
        ufs[uf] = a
    capitais = _agrega(m for m in brasil if m["capital"])
    grandes = _agrega(m for m in brasil if m["eleitores"] >= GRANDE)
    cap_ou_grande = _agrega(
        m for m in brasil if m["capital"] or m["eleitores"] >= GRANDE
    )
    ext = _agrega(exterior)
    total = nac["estoque"] + ext["estoque"]
    return {
        "brasil": nac,
        "exterior": ext,
        "total_com_exterior": total,
        "regioes": por_regiao,
        "ufs": ufs,
        "capitais": {
            **capitais,
            "parcela_do_estoque": _r(T.pct(capitais["estoque"], nac["estoque"])),
        },
        "grandes": {
            **grandes,
            "corte_eleitores": GRANDE,
            "parcela_do_estoque": _r(T.pct(grandes["estoque"], nac["estoque"])),
        },
        "capitais_ou_grandes": {
            **cap_ou_grande,
            "parcela_do_estoque": _r(T.pct(cap_ou_grande["estoque"], nac["estoque"])),
        },
    }


# ---------------------------------------------------------------- riscos e contrário


def riscos(brasil: list[dict], ag: dict, nulo: dict) -> dict[str, Any]:
    nac = ag["brasil"]
    folga = nac["por_classe"]["perdeu_folga"]
    lula_folga = [m for m in brasil if m["classe"] == "perdeu_folga"]
    return {
        "concentracao": {
            "capitais_parcela": ag["capitais"]["parcela_do_estoque"],
            "grandes_parcela": ag["grandes"]["parcela_do_estoque"],
            "capitais_ou_grandes_parcela": ag["capitais_ou_grandes"][
                "parcela_do_estoque"
            ],
            "capitais_ou_grandes_municipios": ag["capitais_ou_grandes"]["municipios"],
        },
        "lula_com_folga": {
            "municipios": folga["municipios"],
            "estoque": folga["estoque"],
            "parcela": folga["estoque_parcela"],
            "saldo": folga["saldo"],
            "saldo_por_voto": (
                _r(folga["saldo"] / folga["estoque"], 4) if folga["estoque"] else None
            ),
            "maiores": [item(m) for m in T.ranking(lula_folga, "estoque", 10)],
        },
        "nulo": {
            "fora_matriz": nac["fora"],
            "acrescimo_2022": nulo["nacional"]["acrescimo"],
            "taxa_2022": nulo["nacional"]["taxa"],
            "risco_2026_ufs_governador": nulo["risco_2026"]["votos"],
        },
    }


def contrario(brasil: list[dict], ag: dict) -> dict[str, Any]:
    """Onde a terceira via é forte e Flávio perdeu com folga: o trabalho rende menos."""
    corte = median(m["estoque_pct"] for m in brasil if m["estoque_pct"] is not None)
    fortes = [
        m
        for m in brasil
        if m["classe"] == "perdeu_folga" and (m["estoque_pct"] or 0) >= corte
    ]
    s = T.somar(
        fortes,
        ("estoque", "saldo", "saldo_df", "caiado", "cury", "renan", "zema", "outros"),
    )
    nordeste_capitais = [
        m for m in brasil if m["regiao"] == "Nordeste" and m["capital"]
    ]
    ncap = T.somar(
        nordeste_capitais,
        (
            "estoque",
            "saldo",
            "saldo_df",
            "caiado",
            "cury",
            "renan",
            "zema",
            "outros",
            "flavio",
            "lula",
            "validos",
        ),
    )
    go = ag["ufs"].get("GO", {})
    caiado_go = go.get("caiado", 0)
    return {
        "corte_estoque_pct": _r(corte),
        "fortes_lula_folga": {
            "municipios": len(fortes),
            **{k: _i(v) for k, v in s.items()},
            "saldo_por_voto": (
                _r(s["saldo"] / s["estoque"], 4) if s["estoque"] else None
            ),
            "maiores": [item(m) for m in T.ranking(fortes, "estoque", 10)],
        },
        "nordeste_capitais": {
            "municipios": len(nordeste_capitais),
            **{k: _i(v) for k, v in ncap.items()},
            "saldo_por_voto": (
                _r(ncap["saldo"] / ncap["estoque"], 4) if ncap["estoque"] else None
            ),
            "margem_pp": _r(T.pct(ncap["flavio"] - ncap["lula"], ncap["validos"])),
        },
        "caiado_goias": {
            "votos": caiado_go,
            "pct_estoque_go": _r(T.pct(caiado_go, go.get("estoque", 0))),
        },
    }


# ---------------------------------------------------------------- conversão de 2022


def _conv(linhas: Iterable[dict]) -> dict[str, Any]:
    linhas = [m for m in linhas if m.get("tv22") is not None]
    gb = sum(m["ganho_b22"] for m in linhas)
    gl = sum(m["ganho_l22"] for m in linhas)
    tv = sum(m["tv22"] for m in linhas)
    c = T.conversao(gb, gl, tv)
    return {
        "municipios": len(linhas),
        "terceira_via_2022": tv,
        "ganho_bolsonaro": gb,
        "ganho_lula": gl,
        **{k: _r(v, 4) for k, v in c.items()},
    }


def conversao_2022(brasil: list[dict]) -> dict[str, Any]:
    """O que cada voto de terceira via de 2022 rendeu entre os turnos, por classe e região.

    Classe é a margem de Flávio em 2026 no município; o rendimento é o de 2022
    no mesmo município (Bolsonaro e Lula, 2º turno menos 1º turno, sobre os
    votos de terceira via do 1º turno). Analogia de uma eleição.
    """
    return {
        "brasil": _conv(brasil),
        "por_classe": {
            c: _conv(m for m in brasil if m["classe"] == c) for c in T.CLASSES
        },
        "por_regiao": {
            r: _conv(m for m in brasil if m["regiao"] == r) for r in REGIOES
        },
        "capitais_nordeste": _conv(
            m for m in brasil if m["regiao"] == "Nordeste" and m["capital"]
        ),
    }


# ---------------------------------------------------------------- nulo de 2022


def _grupo_nulo(linhas: list[dict], quintis: bool = True) -> dict[str, Any]:
    b1 = sum(m["bn22_1t"] for m in linhas)
    b2 = sum(m["bn22_2t"] for m in linhas)
    c1 = sum(m["comp22_1t"] for m in linhas)
    c2 = sum(m["comp22_2t"] for m in linhas)
    t22 = sum(m["tv22"] for m in linhas)
    p1, p2 = T.pct(b1, c1), T.pct(b2, c2)
    reg = T.regressao_ponderada(
        [m["tv22_pct"] for m in linhas],
        [m["delta_bn22_pp"] for m in linhas],
        [m["comp22_2t"] for m in linhas],
    )
    return {
        "municipios": len(linhas),
        "ufs": sorted({m["uf"] for m in linhas}),
        "bn_1t_pct": _r(p1),
        "bn_2t_pct": _r(p2),
        "delta_pp": _r(p2 - p1, 3) if p1 is not None and p2 is not None else None,
        "acrescimo": b2 - b1,
        "terceira_via_2022": t22,
        "taxa": _r(T.taxa_nulo(b1, b2, t22), 4),
        "regressao_terceira_via": {
            k: _r(v, 4) if isinstance(v, float) else v for k, v in reg.items()
        },
        "quintis_terceira_via": _quintis(linhas) if quintis else [],
    }


def nulo_2022(brasil: list[dict], api22: dict, ag: dict) -> dict[str, Any]:
    """Brancos e nulos do 1º para o 2º turno de 2022, contra a terceira via e o 2º turno estadual.

    Mede, no mesmo município, quanto o branco e nulo de presidente cresceu entre
    os turnos de 2022 (pontos dos votantes). Separa as 12 UFs que tiveram 2º turno
    de governador em 2022, onde o eleitor voltou à urna também pelo governador.
    """
    com = [
        m
        for m in brasil
        if m.get("delta_bn22_pp") is not None and m.get("tv22_pct") is not None
    ]
    a1, a2 = api22[1], api22[2]
    bn1 = T.brancos_nulos_pct(a1["brancos"], a1["nulos"], a1["comparecimento"])
    bn2 = T.brancos_nulos_pct(a2["brancos"], a2["nulos"], a2["comparecimento"])
    tv22 = sum(m["tv22"] for m in com)
    acrescimo = (a2["brancos"] + a2["nulos"]) - (a1["brancos"] + a1["nulos"])
    ys = [m["delta_bn22_pp"] for m in com]
    ws = [m["comp22_2t"] for m in com]
    reg_tv = T.regressao_ponderada([m["tv22_pct"] for m in com], ys, ws)
    modelo = T.minimos_quadrados(
        [(1.0, m["tv22_pct"], 1.0 if m["gov22_2t"] else 0.0) for m in com], ys, ws
    )
    reg_ciro = T.regressao_ponderada([m["ciro22_pct"] for m in com], ys, ws)
    reg_tebet = T.regressao_ponderada([m["tebet22_pct"] for m in com], ys, ws)
    com_gov = _grupo_nulo([m for m in com if m["gov22_2t"]])
    sem_gov = _grupo_nulo([m for m in com if not m["gov22_2t"]])
    por_uf = {}
    for uf in sorted({m["uf"] for m in com}):
        d = [m for m in com if m["uf"] == uf]
        g = _grupo_nulo(d, quintis=False)
        por_uf[uf] = {
            k: g[k]
            for k in (
                "bn_1t_pct",
                "bn_2t_pct",
                "delta_pp",
                "acrescimo",
                "terceira_via_2022",
                "taxa",
            )
        }
        por_uf[uf]["gov22_2t"] = d[0]["gov22_2t"]
        por_uf[uf]["gov26_2t"] = d[0]["gov26_2t"]
        por_uf[uf]["estoque_2026"] = ag["ufs"][uf]["estoque"]
        por_uf[uf]["comparecimento_2026"] = ag["ufs"][uf]["comparecimento"]
    grandes = [m for m in com if m["comp22_2t"] >= MIN_COMPARECIMENTO_NULO]
    maiores = sorted(grandes, key=lambda m: (-m["delta_bn22_pp"], m["cd"]))[:N_NULO]
    ufs26 = sorted(uf for uf, u in por_uf.items() if u["gov26_2t"])
    comp26 = sum(por_uf[uf]["comparecimento_2026"] for uf in ufs26)
    estoque26 = sum(por_uf[uf]["estoque_2026"] for uf in ufs26)
    risco = (com_gov["delta_pp"] or 0) / 100 * comp26
    return {
        "nacional": {
            "bn_1t_pct": _r(bn1),
            "bn_2t_pct": _r(bn2),
            "delta_pp": _r(bn2 - bn1),
            "acrescimo": acrescimo,
            "comparecimento_1t": a1["comparecimento"],
            "comparecimento_2t": a2["comparecimento"],
            "terceira_via_2022": tv22,
            "taxa": _r(acrescimo / tv22, 4) if tv22 else None,
            "municipios": len(com),
            "municipios_nulo_subiu": sum(1 for m in com if m["delta_bn22_pp"] > 0),
        },
        "com_2t_governador": com_gov,
        "sem_2t_governador": sem_gov,
        "modelo": {
            "formula": "aumento de branco e nulo (pontos) = a + b × terceira via de 2022 (% dos válidos) + c × (UF com 2º turno de governador em 2022), ponderado pelos votantes do 2º turno",
            "a": _r(modelo[0], 4) if modelo else None,
            "b_terceira_via": _r(modelo[1], 4) if modelo else None,
            "c_governador": _r(modelo[2], 4) if modelo else None,
        },
        "regressao_terceira_via": {
            k: _r(v, 4) if isinstance(v, float) else v for k, v in reg_tv.items()
        },
        "regressao_ciro": {
            k: _r(v, 4) if isinstance(v, float) else v for k, v in reg_ciro.items()
        },
        "regressao_tebet": {
            k: _r(v, 4) if isinstance(v, float) else v for k, v in reg_tebet.items()
        },
        "por_uf": por_uf,
        "maiores": [
            {
                "cd": m["cd"],
                "uf": m["uf"],
                "nome": m["nome"],
                "comparecimento_2t": m["comp22_2t"],
                "bn_1t_pct": _r(m["bn22_1t_pct"]),
                "bn_2t_pct": _r(m["bn22_2t_pct"]),
                "delta_pp": _r(m["delta_bn22_pp"]),
                "tv22_pct": _r(m["tv22_pct"]),
                "gov22_2t": m["gov22_2t"],
                "estoque_2026": m["estoque"],
            }
            for m in maiores
        ],
        "corte_comparecimento": MIN_COMPARECIMENTO_NULO,
        "risco_2026": {
            "regra": (
                "aumento médio de branco e nulo nas UFs com 2º turno de governador em 2022 "
                "(pontos dos votantes) × votantes de 2026 nas UFs com 2º turno de governador em 2026"
            ),
            "ufs": ufs26,
            "comparecimento": comp26,
            "estoque": estoque26,
            "votos": _i(risco),
        },
    }


def _quintis(com: list[dict]) -> list[dict]:
    """Municípios em cinco grupos de mesmo tamanho pela terceira via de 2022."""
    ordem = sorted(com, key=lambda m: (m["tv22_pct"], m["cd"]))
    n = len(ordem)
    saida: list[dict] = []
    if n < 5:
        return saida
    for q in range(5):
        parte = ordem[q * n // 5 : (q + 1) * n // 5]
        b1 = sum(m["bn22_1t"] for m in parte)
        b2 = sum(m["bn22_2t"] for m in parte)
        c1 = sum(m["comp22_1t"] for m in parte)
        c2 = sum(m["comp22_2t"] for m in parte)
        t22 = sum(m["tv22"] for m in parte)
        v22 = sum(m["tv22"] / (m["tv22_pct"] / 100) for m in parte if m["tv22_pct"])
        p1, p2 = T.pct(b1, c1), T.pct(b2, c2)
        saida.append(
            {
                "quinto": q + 1,
                "municipios": len(parte),
                "tv22_min_pct": _r(parte[0]["tv22_pct"]),
                "tv22_max_pct": _r(parte[-1]["tv22_pct"]),
                "tv22_pct": _r(T.pct(t22, v22)),
                "bn_1t_pct": _r(p1),
                "bn_2t_pct": _r(p2),
                "delta_pp": _r(p2 - p1) if p1 is not None and p2 is not None else None,
                "taxa": _r(T.taxa_nulo(b1, b2, t22), 4),
            }
        )
    return saida
