"""Figuras do capítulo 14: pesquisa contra urna, duas réguas para o mesmo estoque.

Dados em `analysis/apuracao_2026/dados/terceira_via.json → reguas`
(`scripts/apuracao-2026-terceira-via.py`). Duas figuras:

- `conversao_2022_classes`: saldo por voto de terceira via na urna de 2022
  (regressão ecológica com efeito fixo de UF, intervalo por bootstrap), a razão
  simples e a matriz das pesquisas (Nexus, Datafolha) convertida em saldo por voto
  sobre o estoque de 2026, por classe de margem e por região;
- `reguas_divergencia_mapa`: bolha por município, cor pela diferença por voto
  entre a pesquisa (Nexus) e a urna de 2022, área pelo estoque; abaixo, os totais
  pelas três réguas por região e por UF.
"""

from __future__ import annotations

import math
from html import escape

import voto_util_mapa as VM

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    GRADE,
    INK,
    LIMA,
    MUTED,
    REGIOES,
    Tips,
    W,
    area,
    botoes,
    chip,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    nome_bonito,
    registra,
    svg_abre,
    t,
)
from .pagina_fig_mapas import MH, MW, paths_uf
from .pagina_fig_terceira_via import (
    CLASSES,
    ROT_CLASSE,
    centroides,
    municipios,
    sinal_votos,
    votos_curto,
)

COR_URNA = "#192e2b"
COR_RAZAO = "#7d5b00"
COR_NEXUS = "#5a4a9e"
COR_DF = "#0f7f5f"
CORTES_DIF = (-0.05, 0.05, 0.15, 0.25)
COR_DIF = ["#1b6f5c", "#d6d0c1", "#c3a6db", "#8659b0", "#4b2470"]
ROT_DIF = [
    "urna de 2022 rende mais (5 pontos por voto ou mais)",
    "as duas quase iguais (menos de 5)",
    "pesquisa promete 5 a 15 a mais",
    "pesquisa promete 15 a 25 a mais",
    "pesquisa promete 25 ou mais a mais",
]
ROT_MOTIVO = {
    "composicao": "composição por nome",
    "classe": "classe de margem",
}
CLASSE_CURTA = {
    "venceu_folga": "venceu com folga",
    "venceu_apertado": "venceu apertado",
    "perdeu_apertado": "perdeu apertado",
    "perdeu_folga": "perdeu com folga",
}


def por_voto(x: float | None, casas: int = 2) -> str:
    if x is None:
        return "s/d"
    s = num(abs(x), casas)
    return ("+" if x > 0 else "−" if x < 0 else "") + s


def _faixa_dif(v: float) -> int:
    return sum(v >= c for c in CORTES_DIF)


# ------------------------------------------------------------------ coeficientes


def _linhas_painel(R: dict, conv: dict, painel: str) -> list[dict]:
    T_ = R["totais"]
    if painel == "classe":
        modelo, grupos, totais = (
            R["modelos"]["classe"]["grupos"],
            CLASSES,
            T_["classes"],
        )
        razao = conv["por_classe"]
        nomes = {c: ROT_CLASSE[c] for c in CLASSES}
    else:
        modelo, grupos, totais = (
            R["modelos"]["regiao"]["grupos"],
            REGIOES,
            T_["regioes"],
        )
        razao = conv["por_regiao"]
        nomes = {r: r for r in REGIOES}
    unico = R["modelos"]["unico"]["grupos"]["todos"]
    br = T_["brasil"]
    saida = [
        {
            "nome": "Brasil (inclinação única)",
            "reg": unico,
            "razao": conv["brasil"]["saldo"],
            "nexus": br["pv_nexus"],
            "df": br["pv_datafolha"],
            "tot": br,
        }
    ]
    for g in grupos:
        saida.append(
            {
                "nome": nomes[g],
                "reg": modelo[g],
                "razao": razao[g]["saldo"],
                "nexus": totais[g]["pv_nexus"],
                "df": totais[g]["pv_datafolha"],
                "tot": totais[g],
            }
        )
    return saida


@registra("conversao_2022_classes")
def conversao_2022_classes(d, **_op) -> str:
    TV = dado(d, "terceira_via")
    R, conv = TV["reguas"], TV["conversao_2022"]
    esq, topo, passo = 330, 78, 58
    lo, hi = -0.45, 0.75
    X = escala(lo, hi, esq, W - 40)
    tips = Tips()
    paineis = {"classe": "Classe de margem de Flávio em 2026", "regiao": "Região"}
    n_max = max(len(_linhas_painel(R, conv, p)) for p in paineis)
    base = topo + passo * n_max
    h = base + 96
    out = [
        svg_abre(
            W,
            h,
            "Saldo por voto de terceira via: urna de 2022 contra a matriz das pesquisas",
            "Para cada grupo de municípios: ponto escuro com intervalo de 95%, a regressão ecológica da urna de 2022 "
            "com efeito fixo de UF; losango dourado, a razão simples de 2022; círculo roxo, a matriz Nexus sobre o "
            "estoque de 2026; quadrado verde, a matriz com as linhas do Datafolha para Cury e Caiado.",
        )
    ]
    for painel in paineis:
        g = []
        for v in (-0.4, -0.2, 0, 0.2, 0.4, 0.6):
            g.append(
                ln(
                    X(v),
                    topo - 10,
                    X(v),
                    base,
                    INK if v == 0 else GRADE,
                    1.4 if v == 0 else 1,
                )
            )
            g.append(t(X(v), base + 22, por_voto(v, 1), 13, MUTED, "middle", mono=True))
        g.append(t(X(0) + 8, topo - 22, "a favor de Flávio →", 13, MUTED))
        g.append(t(X(0) - 8, topo - 22, "← a favor de Lula", 13, MUTED, "end"))
        for i, x in enumerate(_linhas_painel(R, conv, painel)):
            y = topo + i * passo + passo / 2
            reg = x["reg"]
            a, b = reg["saldo_ic95"]
            corpo = [
                t(
                    esq - 14,
                    y + 5,
                    x["nome"],
                    14,
                    INK,
                    "end",
                    "700" if i == 0 else None,
                ),
                f'<line x1="{X(a):.1f}" y1="{y:.1f}" x2="{X(b):.1f}" y2="{y:.1f}" stroke="{COR_URNA}" stroke-width="3" stroke-linecap="round"/>',
                f'<circle cx="{X(reg["saldo"]):.1f}" cy="{y:.1f}" r="7" fill="{COR_URNA}"/>',
            ]
            if x["razao"] is not None:
                xr = X(x["razao"])
                corpo.append(
                    f'<path d="M{xr:.1f} {y - 8:.1f}l8 8l-8 8l-8 -8z" fill="#ffffff" stroke="{COR_RAZAO}" stroke-width="2.5"/>'
                )
            corpo.append(
                f'<circle cx="{X(x["nexus"]):.1f}" cy="{y - 15:.1f}" r="6" fill="#ffffff" stroke="{COR_NEXUS}" stroke-width="2.5"/>'
            )
            corpo.append(
                f'<rect x="{X(x["df"]) - 5.5:.1f}" y="{y + 9.5:.1f}" width="11" height="11" fill="#ffffff" stroke="{COR_DF}" stroke-width="2.5"/>'
            )
            tot = x["tot"]
            linhas_f = [
                (
                    "Urna de 2022, regressão",
                    f"{por_voto(reg['saldo'])} (IC 95%: {por_voto(a)} a {por_voto(b)})",
                ),
                (
                    "Bolsonaro, Lula, fora",
                    f"{num(reg['bolsonaro'], 2)} · {num(reg['lula'], 2)} · {num(reg['fora'], 2)}",
                ),
                ("Urna de 2022, razão simples", por_voto(x["razao"])),
                ("Pesquisa, matriz Nexus", por_voto(x["nexus"])),
                ("Pesquisa, Datafolha em Cury e Caiado", por_voto(x["df"])),
                ("Municípios", inteiro(reg["municipios"])),
                ("Terceira via de 2026", inteiro(tot["estoque"])),
                (
                    "Saldo de 2026: Nexus, urna",
                    f"{sinal_votos(tot['nexus'])} · {sinal_votos(tot['urna'])}",
                ),
            ]
            nota = "inferência ecológica: agregado, não eleitor; a terceira via de 2022 era outra"
            if reg["fora"] is not None and reg["fora"] < 0:
                nota = (
                    "Bolsonaro e Lula somam mais de 1 voto por voto de terceira via: a regressão capta aqui algo além "
                    "da terceira via (comparecimento que anda junto); leia com cautela"
                )
            k = tips.add(
                ficha(x["nome"], "saldo por voto de terceira via", linhas_f, nota)
            )
            g.append(hit(area(0, y - passo / 2, W, passo) + "".join(corpo), k))
        mostra = "" if painel == "classe" else ' display="none"'
        out.append(f'<g data-alt-show="{painel}"{mostra}>{"".join(g)}</g>')
    yl = base + 62
    out.append(
        f'<line x1="{esq:.1f}" y1="{yl - 5:.1f}" x2="{esq + 26:.1f}" y2="{yl - 5:.1f}" stroke="{COR_URNA}" stroke-width="3"/>'
        f'<circle cx="{esq + 13:.1f}" cy="{yl - 5:.1f}" r="6" fill="{COR_URNA}"/>'
        + t(esq + 34, yl, "urna de 2022, regressão e IC 95%", 13)
        + f'<path d="M{esq + 290:.1f} {yl - 13:.1f}l8 8l-8 8l-8 -8z" fill="#ffffff" stroke="{COR_RAZAO}" stroke-width="2.5"/>'
        + t(esq + 304, yl, "razão simples", 13)
        + f'<circle cx="{esq + 440:.1f}" cy="{yl - 5:.1f}" r="6" fill="#ffffff" stroke="{COR_NEXUS}" stroke-width="2.5"/>'
        + t(esq + 452, yl, "Nexus", 13)
        + f'<rect x="{esq + 520:.1f}" y="{yl - 10.5:.1f}" width="11" height="11" fill="#ffffff" stroke="{COR_DF}" stroke-width="2.5"/>'
        + t(esq + 538, yl, "Datafolha (Cury e Caiado)", 13)
    )
    out.append("</svg>")
    ctl = botoes(list(paineis.items()), "classe", "Grupos")
    m = R["modelos"]
    legenda_ = (
        "Saldo por voto de terceira via: votos de Bolsonaro (2022) ou Flávio (2026) menos votos de Lula, por voto de "
        "terceira via do 1º turno. Urna de 2022: regressão ecológica da variação do saldo entre os turnos sobre os "
        "votantes, explicada pela terceira via e pelos brancos e nulos do 1º turno, com efeito fixo de UF, ponderada "
        f"pelos votantes; intervalo por bootstrap de {inteiro(m['classe']['n_boot'])} reamostragens de municípios. "
        "Razão simples: todo o movimento entre os turnos dividido pela terceira via. Pesquisa: a matriz aplicada ao "
        "estoque de 2026 do grupo. Inferência ecológica; a terceira via de 2022 era outra. Fonte: terceira_via.json."
    )
    return figura_html(
        "conversao_2022_classes", "".join(out), legenda_, tips, controles=ctl, minw=820
    )


# ------------------------------------------------------------------ mapa da divergência


def _tabela_totais(R: dict) -> str:
    T_ = R["totais"]
    cab = (
        "<thead><tr>"
        '<th scope="col">Território</th><th scope="col" class="num">Terceira via</th>'
        '<th scope="col" class="num">Saldo Nexus</th><th scope="col" class="num">Saldo Datafolha</th>'
        '<th scope="col" class="num">Saldo urna de 2022</th><th scope="col" class="num">Nexus menos urna</th>'
        "</tr></thead>"
    )

    def linha(nome: str, x: dict, forte: bool = False) -> str:
        cls = "" if forte else ' class="tv-sub"'
        return (
            f'<tr><th scope="row"{cls}>{escape(nome)}</th>'
            f'<td class="num">{inteiro(x["estoque"])}</td><td class="num">{sinal_votos(x["nexus"])}</td>'
            f'<td class="num">{sinal_votos(x["datafolha"])}</td><td class="num">{sinal_votos(x["urna"])}</td>'
            f'<td class="num">{sinal_votos(x["diferenca_nexus_urna"])}</td></tr>'
        )

    corpo = [linha("Brasil", T_["brasil"], True)]
    for r in REGIOES:
        corpo.append(linha(r, T_["regioes"][r], True))
        ufs = sorted(
            (uf for uf, x in T_["ufs"].items() if x["regiao"] == r),
            key=lambda uf: -T_["ufs"][uf]["diferenca_nexus_urna"],
        )
        corpo += [linha(NOME_UF[uf], T_["ufs"][uf]) for uf in ufs]
    return (
        '<div class="table-scroll tv-tab tv-nowrap" tabindex="0"><table>'
        "<caption>Saldo esperado da terceira via para Flávio pelas três réguas, por região e UF (votos). "
        "Dentro de cada região, UFs na ordem da diferença.</caption>"
        f"{cab}<tbody>{''.join(corpo)}</tbody></table></div>"
    )


@registra("reguas_divergencia_mapa")
def reguas_divergencia_mapa(d, **_op) -> str:
    TV = dado(d, "terceira_via")
    R = TV["reguas"]
    mun = municipios(d)
    cen = centroides()
    proj, _ = VM._proj(MW, MH, 10.0)
    emax = max(m["estoque"] for m in mun)
    k = 26 / math.sqrt(emax)
    out = [
        svg_abre(
            MW,
            MH,
            "Pesquisa menos urna: a diferença entre as duas réguas, município a município",
            "Bolha no centroide de cada município, área pelos votos de terceira via; cor pela diferença, por voto, "
            "entre o saldo prometido pela matriz Nexus e o saldo que a urna de 2022 entregou na mesma classe de margem.",
            ' data-near="1"',
        )
    ]
    for _uf, g in sorted(paths_uf().items()):
        out.append(
            f'<path d="{g["d"]}" fill="#ebe5d6" stroke="#b9b29f" stroke-width="0.8"/>'
        )
    linhas, xy, grupos = [], [], []
    lotes: dict[tuple[float, int, int], list[str]] = {}
    for m in sorted(mun, key=lambda m: -m["estoque"]):
        c = cen.get(str(m["ibge"]))
        if c is None or not m["estoque"]:
            continue
        x, y = proj(*c)
        raio = max(0.8, round(k * math.sqrt(m["estoque"]) * 2) / 2)
        gi = REGIOES.index(m["regiao"])
        dif = (m["saldo"] - m["saldo_urna"]) / m["estoque"]
        lotes.setdefault((raio, gi, _faixa_dif(dif)), []).append(f"M{x:.0f} {y:.0f}h0")
        linhas.append(
            [
                f"{nome_bonito(m['nome'])} ({m['uf']})",
                votos_curto(m["estoque"]),
                sinal_votos(m["saldo"]),
                sinal_votos(m["saldo_df"]),
                f"{sinal_votos(m['saldo_urna'])} ({CLASSE_CURTA[m['classe']]})",
                por_voto(dif),
                ROT_MOTIVO[m["regua_motivo"]],
            ]
        )
        xy.append([round(x), round(y), raio])
        grupos.append(str(gi))
    for (raio, gi, f), segs in sorted(lotes.items(), key=lambda kv: -kv[0][0]):
        out.append(
            f'<path data-g="{gi}" d="{"".join(segs)}" stroke="{COR_DIF[f]}" stroke-width="{2 * raio}" '
            'stroke-linecap="round" stroke-opacity="0.8" fill="none"/>'
        )
    rot = []
    usados: list[tuple[float, float]] = []
    for m in sorted(mun, key=lambda m: -m["estoque"])[:8]:
        c = cen.get(str(m["ibge"]))
        if c is None:
            continue
        x, y = proj(*c)
        if any(abs(x - a) < 90 and abs(y - b) < 20 for a, b in usados):
            continue
        usados.append((x, y))
        rot.append(chip(x + 10, y - 8, nome_bonito(m["nome"]), 13))
    out.append(f'<g pointer-events="none">{"".join(rot)}</g>')
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        [
            "Município",
            "Terceira via",
            "Saldo Nexus",
            "Saldo Datafolha",
            "Saldo urna de 2022",
            "Nexus menos urna, por voto",
            "O que mais pesa",
        ],
        linhas,
        xy=xy,
        grupos=grupos,
        nota="saldo = votos para Flávio menos votos para Lula; pesquisa e urna são hipóteses, não medição local",
    )
    ctl = botoes(
        [("", "Brasil")] + [(str(i), reg) for i, reg in enumerate(REGIOES)],
        "",
        "Região",
        "filtro",
    )
    leg = legenda_html(
        list(zip(ROT_DIF, COR_DIF, strict=True)),
        "Pesquisa (Nexus) menos urna de 2022, por voto de terceira via",
    )
    br = R["totais"]["brasil"]
    a, b = br["urna_ic95"]
    legenda_ = (
        f"No país, a matriz Nexus promete a Flávio saldo de {inteiro(br['nexus'])} votos sobre a terceira via; a do "
        f"Datafolha em Cury e Caiado, {inteiro(br['datafolha'])}; a urna de 2022, aplicada pela classe de margem, "
        f"{inteiro(br['urna'])} (IC 95%: {inteiro(a)} a {inteiro(b)}). Roxo: a pesquisa promete mais do que a urna de "
        "2022 entregou em municípios da mesma classe; verde: a urna entregou mais. A ficha diz qual parcela pesa mais: "
        "a composição por nome (Renan, Zema, Cury, Caiado) ou a classe de margem. Fonte: terceira_via.json."
    )
    return figura_html(
        "reguas_divergencia_mapa",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        modo="fit",
        dim=False,
        apos=leg + _tabela_totais(R),
    )
