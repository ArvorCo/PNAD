"""Gráficos dos cards da thread dos fiscais, desenhados em Python (viewBox 1000 × 600).

Tudo sai de `fiscais.json` (recorte leve) e de `fontes_fiscais.json`."""

from __future__ import annotations

from . import fiscais_cenarios as FC
from .fthread_base import cenarios, fiscais
from .thread_base import (
    GRID,
    INK,
    MONO,
    MUTED,
    PAPER2,
    WHITE,
    H,
    W,
    circ,
    ln,
    num,
    r,
    svg,
    t,
)

COR_NIVEL = {"alta": "#7a3500", "media": "#c27a1d", "baixa": "#8a897c"}
ROT_NIVEL = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
# texto do rótulo sobre o painel claro: tons mais escuros, que passam em WCAG AA
COR_NIVEL_TXT = {"alta": "#7a3500", "media": "#8a5410", "baixa": "#5f6773"}


def _quebra(s: str, n: int) -> list[str]:
    linhas, atual = [], ""
    for p in s.split():
        if atual and len(atual) + 1 + len(p) > n:
            linhas.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    if atual:
        linhas.append(atual)
    return linhas


# ------------------------------------------------------------------ 1 tese


def fig_niveis() -> str:
    """Três níveis: seções, locais e fiscais para cobrir, um bloco por nível."""
    F = fiscais()
    N = F["resumo"]["por_nivel"]
    FI = F["resumo"]["fiscais"]["um_por_local"]
    out = [
        t(
            0,
            26,
            "Seções sinalizadas e locais de votação, por nível de prioridade",
            19,
            INK,
            700,
        )
    ]
    cols = [
        ("alta", "o fiscal vai primeiro"),
        ("media", "fiscal se houver gente"),
        ("baixa", "basta o boletim impresso"),
    ]
    larg = (W - 40) / 3
    for i, (nivel, frase) in enumerate(cols):
        x = i * (larg + 20)
        cor = COR_NIVEL[nivel]
        out.append(r(x, 50, larg, 400, PAPER2, 8))
        out.append(r(x, 50, larg, 10, cor, 0))
        out.append(
            t(
                x + 22,
                100,
                ROT_NIVEL[nivel].upper(),
                22,
                COR_NIVEL_TXT[nivel],
                800,
                family=MONO,
            )
        )
        out.append(t(x + 22, 128, frase, 17, MUTED, 500))
        out.append(t(x + 22, 205, num(N[nivel]["secoes"]), 58, INK, 800))
        out.append(t(x + 22, 232, "seções", 18, MUTED, 500))
        out.append(t(x + 22, 305, num(N[nivel]["locais"]), 44, INK, 800))
        out.append(t(x + 22, 330, "locais de votação", 18, MUTED, 500))
        out.append(t(x + 22, 395, num(N[nivel]["municipios"]), 34, INK, 800))
        out.append(t(x + 22, 420, "municípios", 18, MUTED, 500))
    out.append(
        t(
            0,
            500,
            f"Um fiscal por local: {num(FI['alta'])} cobrem o nível alta, {num(FI['alta_media'])} cobrem alta e média,",
            19,
            INK,
            600,
        )
    )
    out.append(t(0, 528, f"{num(FI['todos'])} cobrem a lista inteira.", 19, INK, 600))
    out.append(
        t(
            0,
            575,
            F["rotulos"]["atipico"] + " " + F["rotulos"]["prioridade"],
            17,
            MUTED,
            500,
        )
    )
    return svg("".join(out), "Seções e locais por nível de prioridade")


# ------------------------------------------------------------------ 2 critérios


def fig_criterios() -> str:
    """Barras por critério, empilhadas pelo nível, e o achado contrário embaixo."""
    F = fiscais()
    crit = sorted(F["criterios"], key=lambda c: -c["secoes"])
    vmax = max(c["secoes"] for c in crit)
    x0, x1, topo, passo = 470, 900, 50, 31
    esc = (x1 - x0) / vmax
    out = [
        t(
            0,
            26,
            "Seções em que cada critério disparou, cor pelo nível final",
            19,
            INK,
            700,
        )
    ]
    for i, c in enumerate(crit):
        y = topo + i * passo
        out.append(
            t(
                x0 - 12,
                y + 19,
                f"{c['id']}. {c['nome']}",
                14,
                INK,
                500,
                "end",
            )
        )
        x = x0
        for nivel in ("alta", "media", "baixa"):
            wv = c["secoes_por_nivel"].get(nivel, 0) * esc
            out.append(r(x, y + 4, wv, passo - 9, COR_NIVEL[nivel]))
            x += wv
        out.append(t(x + 8, y + 20, num(c["secoes"]), 15, INK, 700, family=MONO))
    y = topo + len(crit) * passo + 12
    xl = x0
    for nivel in ("alta", "media", "baixa"):
        out.append(r(xl, y - 13, 15, 15, COR_NIVEL[nivel], 2))
        out.append(t(xl + 22, y, ROT_NIVEL[nivel], 16, INK, 600))
        xl += 110
    EX = F["resumo"]["explicacao_comum"]["por_codigo"]
    yy = y + 40
    out.append(r(0, yy - 26, W, 96, WHITE, 8))
    out.append(
        t(
            18,
            yy,
            "Achado contrário: explicação comum no próprio cadastro",
            17,
            INK,
            700,
        )
    )
    texto = (
        f"zona rural {num(EX.get('zona_rural', 0))} · urna trocada {num(EX.get('urna_trocada', 0))} · "
        f"aldeia {num(EX.get('aldeia', 0))} · trânsito {num(EX.get('transito', 0))} · "
        f"quilombo ou assentamento {num(EX.get('quilombo_assentamento', 0))} · presídio {num(EX.get('presidio', 0))}"
    )
    out.append(t(18, yy + 28, texto, 15.5, MUTED, 500))
    out.append(
        t(
            18,
            yy + 54,
            f"{num(F['resumo']['enclaves_2022'])} seções já votavam assim em 2022 e ficam no nível baixa.",
            15.5,
            MUTED,
            500,
        )
    )
    return svg("".join(out), "Seções por critério e explicação comum")


# ------------------------------------------------------------------ 3 e 4 cenários


def fig_cenarios(familias: tuple[str, ...]) -> str:
    """Matriz curta: cenário, sinal nos dados e o que o fiscal confere."""
    J = cenarios()
    cens = [c for c in J["cenarios"] if c["familia"] in familias]
    topo, passo = 56, min(88, (H - 70) / max(len(cens), 1))
    out = [
        t(0, 22, "Cenário", 16, MUTED, 700, family=MONO),
        t(330, 22, "Sinal nos dados", 16, MUTED, 700, family=MONO),
        t(560, 22, "O que o fiscal confere", 16, MUTED, 700, family=MONO),
        ln(0, 34, W, 34, INK, 1.5),
    ]
    for i, c in enumerate(cens):
        y = topo + i * passo - 14
        hh = passo - 8
        out.append(r(0, y, W, hh, PAPER2 if i % 2 == 0 else WHITE, 6))
        out.append(r(0, y, 6, hh, FC.COR_FAMILIA[c["familia"]]))
        for j, linha in enumerate(_quebra(c["nome"], 30)[:2]):
            out.append(t(16, y + 28 + j * 22, linha, 18, INK, 700))
        cor = FC.COR_SINAL[c["sinal"]]
        cy = y + hh / 2
        if c["sinal"] == "deixa":
            out.append(circ(342, cy - 6, 9, cor))
        else:
            out.append(circ(342, cy - 6, 8, WHITE, f' stroke="{cor}" stroke-width="3"'))
            if c["sinal"] == "parcial":
                out.append(
                    f'<path d="M342 {cy - 14:.1f} A8 8 0 0 1 342 {cy + 2:.1f} Z" fill="{cor}"/>'
                )
        out.append(t(360, cy, FC.CURTO_SINAL[c["sinal"]], 17, cor, 700))
        crit = c["criterios"]
        out.append(
            t(
                360,
                cy + 22,
                ("critérios " + ", ".join(crit)) if crit else "só o fiscal vê",
                15,
                MUTED,
                500,
                family=MONO,
            )
        )
        for j, linha in enumerate(_quebra(c["confere_curto"], 44)[:2]):
            out.append(t(560, y + 28 + j * 22, linha, 16.5, INK, 500))
    nome = " e ".join(FC.ROT_FAMILIA[f].lower() for f in familias)
    return svg(
        "".join(out), f"Cenários {nome}: sinal nos dados e o que o fiscal confere"
    )


# ------------------------------------------------------------------ 5 casos


def fig_casos() -> str:
    """Linha do tempo dos casos documentados, eixo só com os anos que têm caso."""
    J = cenarios()
    casos = FC.casos_ordenados(J)
    cens = FC.por_id(J["cenarios"])
    anos = sorted({c["ano"] for c in casos})
    x0, x1, base = 40, W - 40, 120
    passo = (x1 - x0) / max(len(anos) - 1, 1)
    pos = {a: x0 + i * passo for i, a in enumerate(anos)}
    por_ano: dict[int, list[dict]] = {}
    for c in casos:
        por_ano.setdefault(c["ano"], []).append(c)
    pilha = max(len(v) for v in por_ano.values())
    passo_y = min(44, (H - base - 110) / max(pilha, 1))
    raio = min(15, passo_y / 2 - 2)
    out = [
        t(
            0,
            26,
            f"{num(len(casos))} casos documentados, um marcador por caso",
            19,
            INK,
            700,
        ),
        ln(x0 - 20, base, x1 + 20, base, INK, 2),
    ]
    for a in anos:
        out.append(ln(pos[a], base - 7, pos[a], base + 7, INK, 2))
        out.append(
            t(
                pos[a],
                base - 16,
                a,
                16 if len(anos) < 14 else 13,
                INK,
                700,
                "middle",
                MONO,
            )
        )
    for a, lista in por_ano.items():
        for j, c in enumerate(lista):
            cor = FC.COR_FAMILIA[cens[c["cenario"]]["familia"]]
            out.append(
                circ(
                    pos[a],
                    base + 34 + j * passo_y,
                    raio,
                    cor,
                    f' stroke="{WHITE}" stroke-width="2"',
                )
            )
    y = H - 30
    x = 0
    for f in FC.FAMILIAS:
        out.append(circ(x + 9, y - 6, 9, FC.COR_FAMILIA[f]))
        out.append(t(x + 26, y, FC.ROT_FAMILIA[f], 16, INK, 600))
        x += 46 + 8.4 * len(FC.ROT_FAMILIA[f])
    out.append(ln(0, y - 34, W, y - 34, GRID))
    return svg("".join(out), "Linha do tempo dos casos documentados")


# ------------------------------------------------------------------ 6 kit


def fig_kit(etapas: list[tuple[str, str]]) -> str:
    """Lista numerada do dia do fiscal: o que conferir, na ordem."""
    out = []
    n = len(etapas)
    passo = (H - 10) / n
    for i, (titulo, sub) in enumerate(etapas):
        y = 4 + i * passo
        out.append(r(0, y, W, passo - 8, PAPER2 if i % 2 == 0 else WHITE, 8))
        cy = y + (passo - 8) / 2
        out.append(circ(34, cy, 19, "#1457aa"))
        out.append(t(34, cy + 7, str(i + 1), 19, WHITE, 800, "middle", MONO))
        out.append(t(72, cy - 5, titulo, 19, INK, 700))
        out.append(t(72, cy + 19, sub, 15.5, MUTED, 500))
    return svg("".join(out), "O kit do fiscal, na ordem do dia")


__all__ = ["fig_casos", "fig_cenarios", "fig_criterios", "fig_kit", "fig_niveis"]
