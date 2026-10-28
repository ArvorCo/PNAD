"""Tabelas e listas do capítulo "1º turno × 2º turno" (2º turno de 2026)."""

from __future__ import annotations

from apuracao_2026.pagina_comum import inteiro, num, sinal_int
from apuracao_2026.pagina_fig_base import pp

from .pagina_fig_turnos_util import linhas_de, lista_adiada, municipio, tabela_compacta

CAB_F = [
    "Município",
    "Eleitores",
    "Flávio 1º turno",
    "Flávio 2º turno",
    "Votos ganhos",
    "Mudança da parte",
]
CAB_L = [
    "Município",
    "Eleitores",
    "Lula 1º turno",
    "Lula 2º turno",
    "Votos ganhos",
    "Mudança da parte",
]


def _linha(m: dict, quem: str) -> list:
    if quem == "flavio":
        return [
            municipio(m["nome"], m["uf"]),
            inteiro(m["aptos"]),
            inteiro(m["t1_flavio"]),
            inteiro(m["t2_flavio"]),
            sinal_int(m["delta_votos_flavio"]),
            pp(m["swing_h2h_flavio_pp"]),
        ]
    return [
        municipio(m["nome"], m["uf"]),
        inteiro(m["aptos"]),
        inteiro(m["t1_lula"]),
        inteiro(m["t2_lula"]),
        sinal_int(m["delta_votos_lula"]),
        pp(-m["swing_h2h_flavio_pp"]),
    ]


def tabela(lista: list[dict], quem: str, legenda: str) -> str:
    return tabela_compacta(
        CAB_F if quem == "flavio" else CAB_L, [_linha(m, quem) for m in lista], legenda
    )


def maiores_perdas(C1: dict) -> str:
    """As duas tabelas visíveis das 30 maiores perdas de cada um.

    As listas completas de quem perdeu votos ficam na subparte própria
    (``pagina_texto_turnos_perdas``), com mais colunas e ordenáveis.
    """
    h = '<div class="duas">'
    h += "<div>" + tabela(
        C1["flavio_maiores_perdas"],
        "flavio",
        f"Os 30 municípios em que Flávio mais perdeu votos absolutos ({inteiro(C1['flavio_perdeu_votos']['n'])} perderam).",
    )
    h += "</div><div>" + tabela(
        C1["lula_maiores_perdas"],
        "lula",
        f"Os 30 municípios em que Lula mais perdeu votos absolutos ({inteiro(C1['lula_perdeu_votos']['n'])} perderam).",
    )
    return h + "</div></div>"


def ganhos(C1: dict) -> str:
    """Os 30 maiores ganhos de cada um e as listas completas de quem ganhou votos."""
    h = '<details class="ct-det"><summary>Os 30 maiores ganhos de cada um</summary><div class="duas"><div>'
    h += tabela(
        C1["flavio_maiores_ganhos"],
        "flavio",
        "Os 30 maiores ganhos de votos de Flávio.",
    )
    h += "</div><div>" + tabela(
        C1["lula_maiores_ganhos"], "lula", "Os 30 maiores ganhos de votos de Lula."
    )
    h += "</div></div></details>"
    for chave, quem, rot in (
        ("flavio_ganhou_votos", "flavio", "Flávio ganhou votos"),
        ("lula_ganhou_votos", "lula", "Lula ganhou votos"),
    ):
        bloco = C1.get(chave) or {}
        if not bloco.get("lista"):
            continue
        ms = linhas_de(bloco["lista"])
        campo = "delta_votos_flavio" if quem == "flavio" else "delta_votos_lula"
        ms.sort(key=lambda m, c=campo: m[c], reverse=True)
        h += lista_adiada(
            f"tu-lista-{chave.replace('_', '-')}",
            f"Lista completa: os {inteiro(len(ms))} municípios em que {rot} (ordenados pelo saldo de votos)",
            CAB_F if quem == "flavio" else CAB_L,
            [_linha(m, quem) for m in ms],
        )
    return h


def contagem_viradas(C22: dict) -> dict[str, int]:
    """Viradas contadas na própria lista: no Brasil e com as cidades do exterior."""
    v = (C22 or {}).get("viraram") or {}
    if not v.get("lista"):
        return {}
    ms = linhas_de(v["lista"])
    br = [m for m in ms if m["uf"] != "ZZ"]
    return {
        "br_l_f": sum(
            m["vencedor_2022"] == "lula" and m["vencedor_2026"] == "flavio" for m in br
        ),
        "br_b_l": sum(
            m["vencedor_2022"] == "bolsonaro" and m["vencedor_2026"] == "lula"
            for m in br
        ),
        "tot_l_f": sum(
            m["vencedor_2022"] == "lula" and m["vencedor_2026"] == "flavio" for m in ms
        ),
        "tot_b_l": sum(
            m["vencedor_2022"] == "bolsonaro" and m["vencedor_2026"] == "lula"
            for m in ms
        ),
        "ext": len(ms) - len(br),
    }


def viraram(C22: dict) -> str:
    v = C22.get("viraram") or {}
    if not v.get("lista"):
        return ""
    ms = linhas_de(v["lista"])
    cab = ["Município", "Eleitores", "Lula 2022, %", "Lula 2026, %", "Mudança de Lula"]

    def lin(m):
        return [
            municipio(m["nome"], m["uf"]),
            inteiro(m["aptos"]),
            num(m["r22_pct_lula"], 2),
            num(m["pct_lula"], 2),
            pp(m["swing_lula_pp"]),
        ]

    ms = [m for m in ms if m["uf"] != "ZZ"]
    para_lula = sorted(
        (
            m
            for m in ms
            if m["vencedor_2022"] == "bolsonaro" and m["vencedor_2026"] == "lula"
        ),
        key=lambda m: -m["aptos"],
    )
    para_flavio = sorted(
        (
            m
            for m in ms
            if m["vencedor_2022"] == "lula" and m["vencedor_2026"] == "flavio"
        ),
        key=lambda m: -m["aptos"],
    )
    h = tabela_compacta(
        cab,
        [lin(m) for m in para_lula],
        f"Os {len(para_lula)} municípios do Brasil que votaram em Bolsonaro em 2022 e em Lula em 2026, do maior ao menor "
        "eleitorado (cidades do exterior fora).",
    )
    h += lista_adiada(
        "tu-lista-viraram-flavio",
        f"Lista completa: os {len(para_flavio)} municípios do Brasil que votaram em Lula em 2022 e em Flávio em 2026",
        cab,
        [lin(m) for m in para_flavio],
    )
    return h
