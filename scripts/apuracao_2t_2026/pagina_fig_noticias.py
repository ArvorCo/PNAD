"""Figura do capítulo `noticias`: a noite de 25/10 nas fontes, em linha do tempo.

Em cima, uma escada com os marcos da prorrogação (um por linha, rótulo sem
colisão); embaixo, todos os registros com hora, em faixas por tema e cor por tipo
de evidência. Faixas de fundo: votação regular, prorrogação e parada da
totalização do TSE segundo as fontes. Tudo lido de `noticias_noite.json`.
"""

from __future__ import annotations

import re

from apuracao_2026.pagina_fig_base import (
    GRADE,
    INK,
    LULA,
    MUTED,
    Tips,
    W,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    r,
    svg_abre,
    t,
)

from . import pagina_texto_noticias as TN

COR_TIPO = {
    "fato": INK,
    "declaracao": "#7d5b00",
    "relato": "#0f7f5f",
    "hipotese": "#6b4a92",
}
NOME_TIPO = {k: v[1] for k, v in TN.TIPO.items()}
FAIXAS = [
    "Prorrogação",
    "Totalização",
    "Transporte",
    "Ocorrências",
    "Campanhas",
    "Outros",
]
INI, FIM = 7 * 60, 23 * 60


def _faixa(item: dict) -> str:
    g = TN.grupo(item)
    if g in ("Boletins do TSE", "Resultado"):
        return "Totalização"
    if g == "Instituições":
        return "Campanhas"
    return g if g in FAIXAS else "Outros"


def _rot_h(m: float) -> str:
    m = round(m)
    return f"{m // 60:02d}h" if m % 60 == 0 else f"{m // 60:02d}h{m % 60:02d}"


def _votacao(N: dict) -> tuple[float, float] | None:
    """Horário regular de votação pelo registro do calendário ('das 8h às 17h')."""
    for i in N["itens"]:
        if i.get("tema") == "calendario":
            m = re.search(r"das (\d{1,2})h às (\d{1,2})h", i["resumo"])
            if m:
                return int(m.group(1)) * 60, int(m.group(2)) * 60
    return None


def _prorrogada(N: dict) -> float | None:
    for m in TN.marcos(N):
        if m["chave"] == "zanin":
            x = re.search(r"até (\d{1,2})h", m["item"]["resumo"])
            if x:
                return int(x.group(1)) * 60
    return None


def fig_linha(N: dict) -> str:
    ms = TN.marcos(N)
    itens = [i for i in N["itens"] if TN.minutos(i) is not None]
    esq, dir_ = 150, W - 30
    X = escala(INI, FIM, esq, dir_)
    passo_m = 30
    topo = 70
    y_lad = topo
    h_lad = passo_m * len(ms)
    y_fx = y_lad + h_lad + 50
    passo_f = 34
    base = y_fx + passo_f * len(FAIXAS)
    H = base + 60
    tips = Tips()
    out = [
        svg_abre(
            W,
            H,
            "A noite do 2º turno nas fontes",
            "Em cima, os marcos da prorrogação, um por linha; embaixo, cada registro com hora em faixas "
            "por tema, com cor pelo tipo de evidência. Faixas de fundo: votação regular, prorrogação e "
            "parada da totalização do TSE.",
        )
    ]
    vot = _votacao(N)
    pro = _prorrogada(N)
    par = TN.janela_parada(N)
    if vot:
        out.append(
            r(X(vot[0]), topo - 24, X(vot[1]) - X(vot[0]), base - topo + 24, "#efe9da")
        )
        out.append(t(X(vot[0]) + 6, topo - 30, "votação regular", 12.5, MUTED))
    if vot and pro:
        out.append(
            r(X(vot[1]), topo - 24, X(pro) - X(vot[1]), base - topo + 24, "#f3dcd5")
        )
        out.append(
            t(
                X(vot[1]) + 4,
                topo - 44,
                "prorrogação onde a urna seguia aberta",
                12.5,
                LULA,
                weight="700",
            )
        )
    if par:
        out.append(
            r(
                X(par[0]),
                y_fx - 16,
                X(par[1]) - X(par[0]),
                base - y_fx + 16,
                "none",
                f' stroke="{INK}" stroke-width="1.6" stroke-dasharray="5 3"',
            )
        )
        out.append(
            t(
                (X(par[0]) + X(par[1])) / 2,
                y_fx - 22,
                "TSE parado",
                12.5,
                INK,
                "middle",
                "700",
            )
        )
    for hh in range(INI // 60, FIM // 60 + 1):
        x = X(hh * 60)
        out.append(ln(x, topo - 10, x, base, GRADE, 0.8))
        if hh % 2 == 1 or hh in (17, 19):
            out.append(t(x, base + 20, f"{hh:02d}h", 12.5, MUTED, "middle", mono=True))
    out.append(t(dir_, base + 42, "25/10, horário de Brasília", 12.5, MUTED, "end"))
    # escada de marcos
    for k, m in enumerate(ms):
        y = y_lad + k * passo_m + passo_m / 2
        x = X(m["min"])
        it = m["item"]
        texto = f"{_rot_h(m['min'])} {m['rotulo']}"
        largura = 7.1 * len(texto)
        direita = x + 12 + largura < dir_
        cor = COR_TIPO.get(TN.tipo_exibido(it), INK)
        g = [
            ln(esq - 6, y, dir_, y, GRADE, 0.5, ' stroke-dasharray="1 4"'),
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{cor}"/>',
            t(
                x + 12 if direita else x - 12,
                y + 5,
                texto,
                13,
                INK,
                "start" if direita else "end",
                "600",
            ),
        ]
        k_ = tips.add(
            ficha(
                m["rotulo"],
                it["veiculo"],
                [
                    ("Hora no eixo", _rot_h(m["min"])),
                    ("Tipo", NOME_TIPO.get(TN.tipo_exibido(it), TN.tipo_exibido(it))),
                    ("Registro", TN.limpa(it["resumo"])[:220]),
                ],
                TN.limpa(it.get("nota", "")),
            )
        )
        out.append(
            hit(
                area(esq - 6, y - passo_m / 2, dir_ - esq + 6, passo_m) + "".join(g),
                k_,
                foco=True,
            )
        )
    out.append(t(10, y_lad + 4, "Marcos", 13, INK, weight="700"))
    # faixas por tema
    ocup: dict[tuple[str, int], int] = {}
    for j, f in enumerate(FAIXAS):
        y = y_fx + j * passo_f
        out.append(ln(esq - 6, y + passo_f / 2, dir_, y + passo_f / 2, GRADE, 0.6))
        out.append(t(esq - 12, y + passo_f / 2 + 5, f, 13, INK, "end"))
    for i in sorted(itens, key=lambda x: x["quando"]):
        f = _faixa(i)
        j = FAIXAS.index(f)
        m = TN.minutos(i)
        if m is None:
            continue
        bal = int(m // 6)
        n = ocup.get((f, bal), 0)
        ocup[(f, bal)] = n + 1
        y = y_fx + j * passo_f + passo_f / 2 + (n % 3 - 1) * 8
        x = X(m)
        cor = COR_TIPO.get(TN.tipo_exibido(i), INK)
        k_ = tips.add(
            ficha(
                i["veiculo"],
                f"{TN.rotulo_hora(i)} · {NOME_TIPO.get(TN.tipo_exibido(i), TN.tipo_exibido(i))}",
                [("Tema", TN.grupo(i)), ("Registro", TN.limpa(i["resumo"])[:240])],
                TN.limpa(i.get("nota", "")),
            )
        )
        forma = (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.6" fill="{cor}"/>'
            if i["tipo"] != "hipotese"
            else f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="{cor}"/>'
        )
        out.append(hit(area(x - 6, y - 6, 12, 12) + forma, k_))
    out.append("</svg>")
    leg = legenda_html(
        [(NOME_TIPO[k], COR_TIPO[k]) for k in COR_TIPO]
        + [("votação regular", "#efe9da"), ("prorrogação", "#f3dcd5")],
        "Tipo de evidência",
    )
    n_sem = len(N["itens"]) - len(itens)
    legenda = (
        f"{len(itens)} registros de 25/10 com hora; {n_sem} sem hora ou de outro dia ficam só na tabela. "
        "A hora é a do fato quando a fonte a informa, e a de publicação quando não. O retângulo tracejado "
        "é a parada da totalização segundo as fontes, não a medida do coletor da casa. Fonte: "
        "noticias_noite.json."
    )
    return figura_html(
        "p2t_noticias_linha",
        "".join(out),
        legenda,
        tips,
        minw=980,
        dim=False,
        apos=leg,
        foco=(X(16 * 60), X(22 * 60), X(16 * 60)),
    )
