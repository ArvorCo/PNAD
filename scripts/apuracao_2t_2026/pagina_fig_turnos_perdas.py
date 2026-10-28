"""Figura e tabelas da subparte "Onde Flávio teve menos votos no 2º turno do que no 1º".

Capítulo "1º turno × 2º turno" do dossiê do 2º turno. Todo número sai dos resumos de
``turnos_perdas`` (``comparacao_1t.json`` e ``governadores.json``); nada é digitado
aqui. Figura ``tu_perdas_uf``: barras por UF com os municípios em que cada finalista
teve menos votos absolutos, ao lado do total de municípios da UF, com versão
empilhada abaixo de 720 px. Tabelas completas ordenáveis (``table[data-ordena]``),
com cabeçalho fixo e rolagem, adiadas em ``<noscript class="fig-src">`` dentro de
``<details class="ct-det">``.
"""

from __future__ import annotations

from html import escape
from typing import Any

from apuracao_2026.pagina_comum import GOLD, NOME_UF, inteiro, num, sinal_int
from apuracao_2026.pagina_fig_base import (
    FLAVIO,
    GRADE,
    INK,
    LULA,
    MUTED,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    larga_estreita,
    legenda_html,
    ln,
    nome_bonito,
    pp,
    r,
    svg_abre,
    t,
    ticks,
)

from . import turnos_perdas as TP
from .pagina_fig_turnos_util import details_adiado

NOME_FIG = "tu_perdas_uf"
COR = {"flavio": FLAVIO, "lula": LULA}
ESTILO = (
    "<style>.ct-lista.tu-p td:nth-child(2),.ct-lista.tu-p th:nth-child(2)"
    "{text-align:left}.tu-leg{font:13.5px/1.45 var(--sans);color:var(--muted);"
    "margin:10px 0 0}</style>"
)


# ------------------------------------------------------------------ figura


def _itens(RF: dict[str, Any], RL: dict[str, Any]) -> list[dict[str, Any]]:
    lula = {u["uf"]: u for u in RL["por_uf"]}
    itens = [
        {
            "uf": u["uf"],
            "nome": u["nome"],
            "n_uf": u["n_uf"],
            "gov": u["governador_2t"],
            "flavio": u["n"],
            "lula": lula[u["uf"]]["n"],
            "perda_flavio": u["perda"],
            "perda_lula": lula[u["uf"]]["perda"],
        }
        for u in RF["por_uf"]
    ]
    return sorted(itens, key=lambda x: (-x["flavio"], -x["lula"], x["uf"]))


def _marcas(vmax: float) -> list[float]:
    """Marcas redondas que fecham acima do maior valor."""
    m = ticks(0, vmax, 5)
    if len(m) > 1 and m[-1] < vmax:
        m.append(m[-1] + (m[1] - m[0]))
    return m


def _losango(x: float, y: float, s: float = 5) -> str:
    return f'<path d="M{x:.1f} {y - s:.1f}l{s} {s} {-s} {s} {-s} {-s}z" fill="{GOLD}"/>'


def _fichas(itens: list[dict[str, Any]], tips: Tips) -> dict[str, str]:
    out = {}
    for x in itens:
        out[x["uf"]] = tips.add(
            ficha(
                x["nome"],
                "municípios com menos votos no 2º turno do que no 1º",
                [
                    ("Flávio", f"{inteiro(x['flavio'])} de {inteiro(x['n_uf'])}"),
                    ("Votos que Flávio perdeu neles", inteiro(x["perda_flavio"])),
                    ("Lula", f"{inteiro(x['lula'])} de {inteiro(x['n_uf'])}"),
                    ("Votos que Lula perdeu neles", inteiro(x["perda_lula"])),
                    ("2º turno de governador", "sim" if x["gov"] else "não"),
                ],
                TP.ROTULO[:1].upper() + TP.ROTULO[1:] + ".",
            )
        )
    return out


def _legenda_svg(x: float, y: float, fonte: float, larga: bool) -> str:
    itens = [
        ("Flávio teve menos votos", FLAVIO),
        ("Lula teve menos votos", LULA),
    ]
    out, cx = [], x
    for nome, cor in itens:
        out.append(r(cx, y - fonte + 2, fonte, fonte - 2, cor))
        out.append(t(cx + fonte + 6, y, nome, fonte, INK))
        cx += fonte + 22 + 0.55 * fonte * len(nome)
    gov = "UF com 2º turno de governador"
    if larga:
        out.append(_losango(cx + 5, y - fonte / 2 + 1))
        out.append(t(cx + 16, y, gov, fonte, INK))
    else:
        y2 = y + fonte + 8
        out.append(_losango(x + 5, y2 - fonte / 2 + 1))
        out.append(t(x + 16, y2, gov, fonte, INK))
    return "".join(out)


def _svg(itens: list[dict[str, Any]], chaves: dict[str, str], larga: bool) -> str:
    w = 1100 if larga else 380
    f_rot, f_num = (14, 13) if larga else (16, 14)
    x0 = 250 if larga else 58
    x1 = w - (120 if larga else 100)
    rh, alt, passo = (34, 11, 14) if larga else (38, 12, 15)
    out: list[str] = []
    y = 26.0
    titulo = (
        ["Municípios com menos votos no 2º turno do que no 1º, por UF"]
        if larga
        else ["Municípios com menos votos no", "2º turno do que no 1º, por UF"]
    )
    for linha in titulo:
        out.append(t(8, y, linha, 15 if larga else 16, INK, weight="700"))
        y += 20
    y += 6
    out.append(_legenda_svg(8, y, 14, larga))
    y += 18 if larga else 40
    y += 10
    vmax = max(max(x["flavio"], x["lula"]) for x in itens) or 1
    marcas = _marcas(vmax)
    sx = escala(0, marcas[-1], x0, x1)
    y_ini = y
    for x in itens:
        partes = [area(0, y - 2, w, rh)]
        if larga:
            partes.append(t(x0 - 10, y + 18, x["nome"], f_rot, INK, "end"))
            if x["gov"]:
                partes.append(_losango(14, y + 13))
        else:
            partes.append(t(20, y + 20, x["uf"], f_rot, INK, weight="600"))
            if x["gov"]:
                partes.append(_losango(8, y + 15))
        for i, quem in enumerate(TP.CANDIDATOS):
            v = x[quem]
            yb = y + 2 + i * passo
            if v > 0:
                partes.append(r(x0, yb, sx(v) - x0, alt, COR[quem]))
            partes.append(
                t(
                    sx(v) + 6,
                    yb + alt,
                    f"{inteiro(v)} de {inteiro(x['n_uf'])}",
                    f_num,
                    INK if v else MUTED,
                    mono=True,
                    weight="600" if v else None,
                )
            )
        out.append(hit("".join(partes), chaves[x["uf"]], foco=True))
        y += rh
    for m in marcas:
        out.insert(0, ln(sx(m), y_ini - 4, sx(m), y, GRADE, 1))
        out.append(t(sx(m), y + 16, inteiro(m), 12, MUTED, "middle", mono=True))
    out.append(t(x1, y + 34, "municípios", 12, MUTED, "end"))
    h = y + 46
    cab = svg_abre(
        w,
        h,
        "Municípios com menos votos no 2º turno do que no 1º, por UF",
        "Duas barras por UF: municípios em que Flávio teve menos votos absolutos no 2º "
        "turno do que no 1º e municípios em que Lula teve menos votos, com o total de "
        "municípios da UF ao lado; losango marca UF com 2º turno de governador.",
    )
    return cab + "".join(out) + "</svg>"


def fig_perdas_uf(RF: dict[str, Any], RL: dict[str, Any], gov: list[str]) -> str:
    itens = _itens(RF, RL)
    tips = Tips()
    chaves = _fichas(itens, tips)
    corpo = larga_estreita(_svg(itens, chaves, True), _svg(itens, chaves, False))
    nomes_gov = [NOME_UF.get(u, u) for u in gov]
    gov_txt = (
        ", ".join(nomes_gov[:-1]) + " e " + nomes_gov[-1]
        if len(nomes_gov) > 1
        else "".join(nomes_gov)
    )
    legenda = (
        f"Municípios em que cada finalista teve menos votos absolutos no 2º turno do que no "
        f"1º, por UF, com o total de municípios da UF: {inteiro(RF['n'])} de Flávio e "
        f"{inteiro(RL['n'])} de Lula, entre {inteiro(RF['n_universo'])} municípios do Brasil "
        f"sem o exterior. Losango: UF com 2º turno de governador ({gov_txt}). Votos absolutos, "
        "não fatia dos válidos. Fontes: comparacao_1t.json (flavio_perdeu_votos, "
        "lula_perdeu_votos e ufs) e governadores.json."
    )
    leg = legenda_html(
        [
            ("Flávio teve menos votos", FLAVIO),
            ("Lula teve menos votos", LULA),
            ("UF com 2º turno de governador (losango)", GOLD),
        ]
    )
    return figura_html(NOME_FIG, corpo, legenda, tips, modo="full", apos=leg)


# ------------------------------------------------------------------ tabelas completas


def _td(texto: str, valor: float | int | None = None) -> str:
    dv = "" if valor is None else f" data-v={valor}"
    return f"<td{dv}>{escape(texto)}"


def _pct(v: float | None) -> str:
    return "s/d" if v is None else f"{num(v, 2)}%"


def cabecalho(quem: str) -> list[str]:
    a, b = TP.NOME[quem], TP.NOME[TP.ADVERSARIO[quem]]
    return [
        "UF",
        "Município",
        "Eleitores",
        f"{a} 1º turno",
        f"{a} 2º turno",
        f"Diferença de {a}",
        f"{b} 1º turno",
        f"{b} 2º turno",
        f"Diferença de {b}",
        "Comparecimento 1º turno",
        "Comparecimento 2º turno",
        "Saldo do comparecimento",
        f"Mudança da parte de {a}",
        "Perda na queda do comparecimento",
        "Perda fora dela",
    ]


def linha(m: dict[str, Any], quem: str) -> str:
    adv = TP.ADVERSARIO[quem]
    swing = m["swing_h2h_flavio_pp"]
    parte = swing if quem == "flavio" else (None if swing is None else -swing)
    cels = [
        _td(m["uf"]),
        _td(nome_bonito(m["nome"])),
        _td(inteiro(m["aptos"]), m["aptos"]),
        _td(inteiro(m[f"t1_{quem}"]), m[f"t1_{quem}"]),
        _td(inteiro(m[f"t2_{quem}"]), m[f"t2_{quem}"]),
        _td(sinal_int(m[f"delta_votos_{quem}"]), m[f"delta_votos_{quem}"]),
        _td(inteiro(m[f"t1_{adv}"]), m[f"t1_{adv}"]),
        _td(inteiro(m[f"t2_{adv}"]), m[f"t2_{adv}"]),
        _td(sinal_int(m[f"delta_votos_{adv}"]), m[f"delta_votos_{adv}"]),
        _td(_pct(m["t1_pct_comparecimento"]), m["t1_pct_comparecimento"]),
        _td(_pct(m["t2_pct_comparecimento"]), m["t2_pct_comparecimento"]),
        _td(
            sinal_int(m["delta_comparecimento_votos"]), m["delta_comparecimento_votos"]
        ),
        _td(pp(parte), parte),
        _td(
            inteiro(m["proporcional_comparecimento"]),
            round(m["proporcional_comparecimento"], 1),
        ),
        _td(inteiro(m["alem_proporcional"]), round(m["alem_proporcional"], 1)),
    ]
    return "<tr>" + "".join(cels)


def tabela_ordenavel(ms: list[dict[str, Any]], quem: str, legenda: str) -> str:
    """Legenda fora da rolagem (quebra na largura da tela) e tabela ordenável dentro."""
    th = "".join(f"<th scope=col>{escape(c)}</th>" for c in cabecalho(quem))
    corpo = "".join(linha(m, quem) for m in ms)
    rotulo = f"Municípios em que {TP.NOME[quem]} teve menos votos no 2º turno"
    return (
        f'<p class="tu-leg">{escape(legenda)}</p>'
        f'<div class="ct-lista-c" tabindex="0"><table class="ct-lista tu-p" data-ordena="1" '
        f'aria-label="{escape(rotulo)}"><thead><tr>{th}</tr></thead>'
        f"<tbody>{corpo}</tbody></table></div>"
    )


def lista_completa(ms: list[dict[str, Any]], quem: str) -> str:
    nome = TP.NOME[quem]
    legenda = (
        f"Os {inteiro(len(ms))} municípios em que {nome} teve menos votos no 2º turno do que "
        "no 1º, da maior perda para a menor; o botão do cabeçalho reordena. Votos absolutos. "
        "Comparecimento sobre o eleitorado de cada turno; eleitores do 2º turno. As duas "
        "últimas colunas repartem a perda pela régua proporcional (quem deixou de votar "
        "votaria como o município no 1º turno): conta sob hipótese, não identificação de "
        "eleitor. Fonte: comparacao_1t.json."
    )
    return details_adiado(
        f"tu-lista-{quem}-menos-votos",
        f"Lista completa: os {inteiro(len(ms))} municípios em que {nome} teve menos votos "
        "no 2º turno (da maior perda para a menor, ordenável)",
        tabela_ordenavel(ms, quem, legenda),
    )
