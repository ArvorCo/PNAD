"""Sankey da transferência 1º → 2º turno, por cenário de cruzamento (capítulo "De onde veio o voto").

Fonte: ``transferencia.json`` (``cruzamento.cenarios.<k>.figura``). Nove origens do
1º turno à esquerda (Lula, Flávio, as quatro candidaturas de terceira via, demais,
brancos e nulos, quem não votou), quatro destinos do 2º turno à direita (Lula,
Flávio, brancos e nulos, quem não votou). Largura proporcional aos votos, uma
escala só e sem espessura mínima. A fita tem a cor do destino e leva o número na
própria fita (milhões com uma casa e parte da origem) quando passa de meio milhão
de votos; as menores vão para a lista ao lado. A textura diz de onde veio a
partida do elo: sólida, linha publicada por instituto; pontilhada, regressão sobre
as urnas; hachurada, estimativa da casa. Em todas, a largura final sai do ajuste
às duas urnas.

Abaixo de 720 px a figura vira barras empilhadas (de cada 100 eleitores de cada
origem). Os quatro cenários são trocados por botões; sem script, fica o padrão.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import inteiro, num
from apuracao_2026.pagina_fig_base import (
    FLAVIO,
    INK,
    LULA,
    MUTED,
    PAPER,
    Tips,
    botoes,
    ficha,
    figura_html,
    hit,
    larga_estreita,
    legenda_html,
    svg_abre,
    t,
)

W = 1100
H_UTIL = 900.0
TOPO = 70.0
GAP_O = 22.0
XL, X0, X1 = 196.0, 204.0, 630.0
LARG = 12.0
XP = 818.0
ROT = 12.5
PASSO_ROT = 22.0
"""Altura de um rótulo de fita mais o respiro; o espaço entre origens cresce para caber a pilha."""
ORIGENS = (
    "lula",
    "flavio",
    "cury",
    "renan",
    "caiado",
    "zema",
    "outros",
    "bn",
    "abstencao",
)
DESTINOS = ("lula", "flavio", "bn", "abstencao")
NOME_O = {
    "lula": "Lula",
    "flavio": "Flávio",
    "cury": "Augusto Cury",
    "renan": "Renan Santos",
    "caiado": "Ronaldo Caiado",
    "zema": "Romeu Zema",
    "outros": "Demais",
    "bn": "Brancos e nulos",
    "abstencao": "Não votou",
}
NOME_D = {
    "lula": "Lula",
    "flavio": "Flávio",
    "bn": "Brancos e nulos",
    "abstencao": "Não votou",
}
CURTO_O = {
    "lula": "Lula",
    "flavio": "Flávio",
    "cury": "Cury",
    "renan": "Renan",
    "caiado": "Caiado",
    "zema": "Zema",
    "outros": "Demais",
    "bn": "Br. e nulo",
    "abstencao": "Não votou",
}
CURTO_D = {
    "lula": "Lula",
    "flavio": "Flávio",
    "bn": "br. e nulo",
    "abstencao": "não votou",
}
COR_D = {"lula": LULA, "flavio": FLAVIO, "bn": "#b39a5c", "abstencao": "#8f938b"}
TXT_D = {"lula": LULA, "flavio": FLAVIO, "bn": "#7d5b00", "abstencao": MUTED}
COR_O = {
    "lula": LULA,
    "flavio": FLAVIO,
    "cury": "#0f7f5f",
    "renan": "#3d8a74",
    "caiado": "#6aa392",
    "zema": "#8fb8aa",
    "outros": "#a9b8b1",
    "bn": "#b39a5c",
    "abstencao": "#8f938b",
}
NATUREZA = {
    "medido": "partida em linha publicada por instituto (voto lembrado × intenção); a largura sai do ajuste às urnas",
    "regressao": "regressão sobre as urnas (quem não votou no 1º turno); fixa no ajuste",
    "estimado": "estimativa da casa (hipótese declarada); a largura sai do ajuste às urnas",
    "zero": "zerada pelo cenário",
}
TINTA_LEG = "#4f5d58"
LEG = {
    "medido": TINTA_LEG,
    "regressao": f"radial-gradient(circle,{PAPER} 1.4px,{TINTA_LEG} 1.6px) 0 0/5px 5px",
    "estimado": f"repeating-linear-gradient(45deg,{TINTA_LEG} 0 3px,{PAPER} 3px 6px)",
}
ROTULO_LEG = {
    "medido": "Sólida: partida em linha publicada por instituto",
    "regressao": "Pontilhada: regressão sobre as urnas",
    "estimado": "Hachurada: estimativa da casa",
}


def mi1(v: float) -> str:
    return f"{num(v / 1e6, 1)} mi"


def mil(v: float) -> str:
    """Votos de fita fina: milhar inteiro (abaixo de mil, "menos de 1 mil")."""
    if v < 500:
        return "< 1 mil"
    return f"{inteiro(round(v / 1000))} mil"


def pc(v: float, casas: int = 1) -> str:
    return f"{num(v, casas)}%"


def pc_curto(v: float) -> str:
    """Parte da origem no rótulo da fita: inteiro de 10% para cima, uma casa abaixo."""
    return f"{num(v, 0)}%" if v >= 9.95 else f"{num(v, 1)}%"


def rotulo_fita(v: float, p_origem: float) -> str:
    return f"{mi1(v)} · {pc_curto(p_origem)}"


def _defs(pref: str) -> str:
    out = ["<defs>"]
    for k, cor in COR_D.items():
        out.append(
            f'<pattern id="{pref}-h-{k}" patternUnits="userSpaceOnUse" width="7" height="7" '
            f'patternTransform="rotate(40)"><rect width="7" height="7" fill="{PAPER}"/>'
            f'<rect width="3.6" height="7" fill="{cor}"/></pattern>'
        )
        out.append(
            f'<pattern id="{pref}-p-{k}" patternUnits="userSpaceOnUse" width="6" height="6">'
            f'<rect width="6" height="6" fill="{cor}"/>'
            f'<circle cx="1.5" cy="1.5" r="1.25" fill="{PAPER}"/>'
            f'<circle cx="4.5" cy="4.5" r="1.25" fill="{PAPER}"/></pattern>'
        )
    out.append("</defs>")
    return "".join(out)


def _preenche(tipo: str, destino: str, pref: str) -> str:
    if tipo == "medido":
        return f'fill="{COR_D[destino]}" fill-opacity="0.78"'
    if tipo == "regressao":
        return f'fill="url(#{pref}-p-{destino})"'
    return f'fill="url(#{pref}-h-{destino})"'


def _largura_chip(txt: str, size: float = ROT) -> float:
    return 0.56 * size * len(txt) + 14


def _chip(x0: float, cy: float, destino: str, txt: str) -> tuple[str, float]:
    """Rótulo na fita, à esquerda, com o destino na cor dele e o número em tinta."""
    cab = f"→ {NOME_D[destino]} "
    w = _largura_chip(cab + txt)
    svg = (
        f'<g class="rot-fita"><rect x="{x0:.1f}" y="{cy - 9.5:.1f}" width="{w:.1f}" height="19" rx="3" '
        f'fill="#ffffff" stroke="{COR_D[destino]}" stroke-width="1.6"/>'
        f'<text x="{x0 + 7:.1f}" y="{cy + 4.4:.1f}" font-size="{ROT}" fill="{INK}" font-weight="600" '
        f'font-family="Archivo, Helvetica, Arial, sans-serif"><tspan fill="{TXT_D[destino]}" font-weight="700">'
        f"{escape(cab)}</tspan>{escape(txt)}</text></g>"
    )
    return svg, w


def _espalha(desejado: list[float], topo: float, base: float) -> list[float]:
    """Centros de rótulos numa coluna: o mais perto do desejado sem sobrepor, dentro de [topo, base]."""
    y = list(desejado)
    meio = PASSO_ROT / 2
    for i in range(len(y)):
        y[i] = max(y[i], topo + meio, y[i - 1] + PASSO_ROT if i else -1e9)
    excesso = y[-1] - (base - meio) if y else 0
    if excesso > 0:
        y = [v - excesso for v in y]
        for i in range(len(y)):
            y[i] = max(y[i], topo + meio, y[i - 1] + PASSO_ROT if i else -1e9)
    return y


def _celulas(fig: dict) -> list[tuple[str, str, float, str]]:
    return [
        (a, b, float(fig["votos"][a][b]), fig["tipos"][a][b])
        for a in ORIGENS
        for b in DESTINOS
        if float(fig["votos"][a][b]) > 0
    ]


def _fichas(cen: dict, tips: Tips) -> dict[tuple[str, str], str]:
    fig = cen["figura"]
    chaves = {}
    for a, b, v, tipo in _celulas(fig):
        chaves[(a, b)] = tips.add(
            ficha(
                f"{NOME_O[a]} (1º turno) → {NOME_D[b]} (2º turno)",
                cen["nome"],
                [
                    ("Eleitores", inteiro(round(v, -3))),
                    ("Parte da origem", pc(fig["pct_origem"][a][b])),
                    ("Parte do destino", pc(fig["pct_destino"][a][b])),
                ],
                NATUREZA[tipo] + ". Estimativa, não medição.",
            )
        )
    return chaves


def sankey_largo(cen: dict, chaves: dict, pref: str) -> tuple[str, dict]:
    """Sankey de 1.100 px com rótulos no começo de cada fita e a lista das fitas finas ao lado.

    O rótulo fica colado à origem, na altura em que a fita sai dela, e diz o destino;
    quando os rótulos de uma origem não cabem na altura dela, o espaço até a origem
    seguinte cresce. Fita abaixo do limiar vai para a lista.
    """
    fig = cen["figura"]
    lim = fig["limiar_rotulo_votos"]
    cel = _celulas(fig)
    tot_o = {a: sum(v for x, _y, v, _t in cel if x == a) for a in ORIGENS}
    tot_d = {b: sum(v for _x, y, v, _t in cel if y == b) for b in DESTINOS}
    total = sum(tot_o.values())
    esc = H_UTIL / total
    rotulaveis = {
        a: [b for b in DESTINOS if float(fig["votos"][a][b]) >= lim] for a in ORIGENS
    }
    faixa_o: dict[str, tuple[float, float]] = {}
    pos_o: dict[str, float] = {}
    y = TOPO
    for a in ORIGENS:
        alt = tot_o[a] * esc
        pilha = PASSO_ROT * len(rotulaveis[a])
        caixa = max(alt, pilha)
        pos_o[a] = y + (caixa - alt) / 2
        faixa_o[a] = (y, y + caixa)
        y += caixa + GAP_O
    alt_e = y - GAP_O - TOPO
    gap_d = (alt_e - H_UTIL) / (len(DESTINOS) - 1)
    pos_d, y = {}, TOPO
    for b in DESTINOS:
        pos_d[b] = y
        y += tot_d[b] * esc + gap_d
    h = TOPO + alt_e + 30
    out = [
        svg_abre(
            W,
            h,
            f"De onde veio o voto do 2º turno: {cen['nome'].lower()}",
            "Nove escolhas do 1º turno à esquerda, quatro do 2º turno à direita; largura proporcional aos eleitores, "
            "uma escala só, sem espessura mínima. Estimativa ajustada às duas urnas, não medição.",
        ),
        _defs(pref),
        t(
            X0 + LARG,
            30,
            "1º TURNO, 4 DE OUTUBRO",
            12.5,
            MUTED,
            "end",
            weight="700",
            mono=True,
        ),
        t(
            X1,
            30,
            "2º TURNO, 25 DE OUTUBRO",
            12.5,
            MUTED,
            "start",
            weight="700",
            mono=True,
        ),
        t(
            XP,
            30,
            "FITAS FINAS (MENOS DE 0,5 MI)",
            12.5,
            MUTED,
            "start",
            weight="700",
            mono=True,
        ),
    ]
    cur_o, cur_d = dict(pos_o), dict(pos_d)
    fitas = []
    saida: dict[tuple[str, str], float] = {}
    for a in ORIGENS:
        for b in DESTINOS:
            v = float(fig["votos"][a][b])
            if v <= 0:
                continue
            tipo = fig["tipos"][a][b]
            e = v * esc
            ya, yb = cur_o[a], cur_d[b]
            cur_o[a] += e
            cur_d[b] += e
            saida[(a, b)] = ya + e / 2
            xa, xb = X0 + LARG, X1
            m1, m2 = xa + (xb - xa) * 0.42, xa + (xb - xa) * 0.58
            d = (
                f"M{xa:.1f} {ya:.2f}C{m1:.1f} {ya:.2f} {m2:.1f} {yb:.2f} {xb:.1f} {yb:.2f}"
                f"L{xb:.1f} {yb + e:.2f}C{m2:.1f} {yb + e:.2f} {m1:.1f} {ya + e:.2f} {xa:.1f} {ya + e:.2f}Z"
            )
            fitas.append(
                hit(
                    f'<path d="{d}" {_preenche(tipo, b, pref)} data-votos="{v:.0f}" '
                    f'data-esp="{e:.3f}" data-tipo="{tipo}"/>',
                    chaves[(a, b)],
                )
            )
    out.extend(fitas)
    rotulos, finas = [], []
    for a in ORIGENS:
        bs = rotulaveis[a]
        ys = _espalha([saida[(a, b)] for b in bs], *faixa_o[a])
        for b, cy in zip(bs, ys, strict=True):
            v = float(fig["votos"][a][b])
            svg, _w = _chip(
                X0 + LARG + 6, cy, b, rotulo_fita(v, fig["pct_origem"][a][b])
            )
            rotulos.append(svg)
        for b in DESTINOS:
            v = float(fig["votos"][a][b])
            if 0 < v < lim:
                finas.append((a, b, v, fig["tipos"][a][b]))
    out.extend(rotulos)
    for a, yy in pos_o.items():
        alt = tot_o[a] * esc
        out.append(
            f'<rect x="{X0:.1f}" y="{yy:.2f}" width="{LARG:.0f}" height="{max(alt, 0.01):.2f}" fill="{COR_O[a]}"/>'
        )
        out.append(
            f'<text x="{XL - 4:.1f}" y="{yy + alt / 2 + 5:.1f}" font-size="14.5" fill="{INK}" '
            f'font-family="Archivo, Helvetica, Arial, sans-serif" text-anchor="end">'
            f'<tspan font-weight="700">{escape(NOME_O[a])}</tspan>'
            f'<tspan fill="{MUTED}"> {escape(mi1(tot_o[a]))}</tspan></text>'
        )
    for b, yy in pos_d.items():
        alt = tot_d[b] * esc
        out.append(
            f'<rect x="{X1:.1f}" y="{yy:.2f}" width="{LARG:.0f}" height="{alt:.2f}" fill="{COR_D[b]}"/>'
        )
        meio = yy + alt / 2
        out.append(t(X1 + LARG + 10, meio - 2, NOME_D[b], 16, TXT_D[b], weight="700"))
        out.append(t(X1 + LARG + 10, meio + 17, mi1(tot_d[b]), 14, INK))
    out.append(_lista_finas(finas, fig, pref))
    out.append("</svg>")
    return "".join(out), {
        "escala_px_por_voto": esc,
        "rotuladas": len(rotulos),
        "finas": len(finas),
    }


def _lista_finas(finas: list, fig: dict, pref: str) -> str:
    out = [t(XP, 50, "eleitores · parte da origem", 12, MUTED)]
    y = 74.0
    for a, b, v, tipo in finas:
        out.append(
            f'<rect x="{XP:.1f}" y="{y - 10:.1f}" width="11" height="11" {_preenche(tipo, b, pref)} '
            f'stroke="{COR_D[b]}" stroke-width="0.8"/>'
        )
        out.append(t(XP + 17, y, f"{CURTO_O[a]} → {CURTO_D[b]}", 12.5, INK))
        out.append(
            t(
                W - 6,
                y,
                f"{mil(v)} · {pc(fig['pct_origem'][a][b])}",
                12,
                INK,
                "end",
                mono=True,
            )
        )
        y += 20
    zeros = [(a, b) for a in ORIGENS for b in DESTINOS if fig["tipos"][a][b] == "zero"]
    if zeros:
        y += 8
        out.append(t(XP, y, "Zeradas neste cenário:", 12.5, INK, weight="700"))
        for a, b in zeros:
            y += 19
            out.append(t(XP + 17, y, f"{CURTO_O[a]} → {CURTO_D[b]}: 0", 12.5, INK))
    y += 30
    out.append(t(XP, y, "Todas somam as duas urnas:", 12.5, INK, weight="700"))
    out.append(t(XP, y + 19, "aptos = válidos + brancos e", 12.5, INK))
    out.append(t(XP, y + 37, "nulos + quem não votou.", 12.5, INK))
    return "".join(out)


def sankey_estreito(cen: dict, chaves: dict, pref: str) -> str:
    """Versão de celular: uma barra de 100% por origem, com os números embaixo."""
    fig = cen["figura"]
    w = 400
    x0, x1 = 8.0, 392.0
    blocos, y = [], 40.0
    for a in ORIGENS:
        tot = sum(float(fig["votos"][a][b]) for b in DESTINOS)
        blocos.append(
            f'<text x="{x0:.0f}" y="{y:.1f}" font-size="15" fill="{INK}" font-family="Archivo, Helvetica, Arial, sans-serif">'
            f'<tspan font-weight="700">{escape(NOME_O[a])}</tspan>'
            f'<tspan fill="{MUTED}" font-size="13.5"> · {escape(mi1(tot))} no 1º turno</tspan></text>'
        )
        y += 8
        xc = x0
        for b in DESTINOS:
            p = float(fig["pct_origem"][a][b])
            if p <= 0:
                continue
            lw = (x1 - x0) * p / 100
            tipo = fig["tipos"][a][b]
            blocos.append(
                hit(
                    f'<rect x="{xc:.2f}" y="{y:.1f}" width="{lw:.2f}" height="24" {_preenche(tipo, b, pref)}/>',
                    chaves[(a, b)],
                )
            )
            xc += lw
        blocos.append(
            f'<rect x="{x0:.1f}" y="{y:.1f}" width="{x1 - x0:.1f}" height="24" fill="none" stroke="{INK}" stroke-width="0.6"/>'
        )
        y += 24 + 18
        xt = x0
        for b in DESTINOS:
            p = float(fig["pct_origem"][a][b])
            if p < 1:
                continue
            txt = f"{NOME_D[b]} {pc(p)}"
            lw = 0.56 * 13.5 * len(txt) + 14
            if xt + lw > x1 + 14 and xt > x0:
                y += 19
                xt = x0
            blocos.append(t(xt, y, txt, 13.5, TXT_D[b], weight="600"))
            xt += lw
        y += 30
    out = [
        svg_abre(
            w,
            y,
            f"De cada 100 eleitores de cada escolha do 1º turno, para onde foram: {cen['nome'].lower()}",
            "Uma barra por escolha do 1º turno; cada pedaço é a parte que foi para Lula, Flávio, brancos e nulos ou "
            "não votou no 2º turno. Estimativa ajustada às duas urnas, não medição.",
        ),
        _defs(pref),
        t(
            x0,
            18,
            "DE CADA 100 NO 1º TURNO, NO 2º:",
            12,
            MUTED,
            weight="700",
            mono=True,
        ),
        *blocos,
        "</svg>",
    ]
    return "".join(out)


def legenda_natureza(cen: dict) -> str:
    cont = cen["figura"]["contagem_tipos"]
    itens = []
    for tipo in ("medido", "regressao", "estimado"):
        c = cont[tipo]
        itens.append(
            (
                f"{ROTULO_LEG[tipo]}: {c['fitas']} fitas, {num(c['pct_votos'], 1)}% dos eleitores",
                LEG[tipo],
            )
        )
    if cont["zero"]["fitas"]:
        itens.append(
            (
                f"Zeradas pelo cenário: {cont['zero']['fitas']} (Lula → Flávio e Flávio → Lula)",
                PAPER,
            )
        )
    cores = [(f"Para {NOME_D[b]}", COR_D[b]) for b in DESTINOS]
    return legenda_html(itens, "Textura: de onde veio a partida do elo") + legenda_html(
        cores, "Cor: destino no 2º turno"
    )


def frase_cenario(cen: dict) -> str:
    """Uma frase por cenário, acima do desenho, trocada com o botão."""
    m = cen["metricas"]
    tc = m["terceira"]
    if cen["tipo_cruzamento"] == "zero":
        cruz = "nenhum eleitor de Lula no 1º turno foi para Flávio, nem o contrário"
    else:
        cruz = (
            f"{num(m['lula_para_flavio'] / 1e6, 2)} milhão de eleitores de Lula ({pc(m['lula_para_flavio_pct'], 2)} da base) "
            f"foi para Flávio e {num(m['flavio_para_lula'] / 1e6, 2)} milhão de eleitores de Flávio "
            f"({pc(m['flavio_para_lula_pct'], 2)}) foi para Lula"
        )
    return (
        f'<p class="tr-frase"><b>{escape(cen["nome"])}:</b> {cruz}. De cada 100 eleitores da terceira via, '
        f"{num(tc['flavio_pct'], 1)} foram para Flávio e {num(tc['lula_pct'], 1)} para Lula. Fora da própria base, Lula "
        f"ganhou {num(m['ganho_fora_base_lula'] / 1e6, 2)} milhões e Flávio {num(m['ganho_fora_base_flavio'] / 1e6, 2)} "
        f"(razão de {num(m['razao_consolidacao_flavio_lula'], 2)} para 1).</p>"
    )


def tabela_cem(cen: dict) -> str:
    """De cada 100 eleitores de cada origem, quantos foram para cada destino, com os votos."""
    fig = cen["figura"]
    cab = "".join(
        f'<th scope="col" class="num">{escape(NOME_D[b])}</th>' for b in DESTINOS
    )
    linhas = []
    tot_d = dict.fromkeys(DESTINOS, 0.0)
    for a in ORIGENS:
        tot = sum(float(fig["votos"][a][b]) for b in DESTINOS)
        cels = []
        for b in DESTINOS:
            v = float(fig["votos"][a][b])
            tot_d[b] += v
            marca = (
                " *"
                if fig["tipos"][a][b] == "estimado"
                else " ·" if fig["tipos"][a][b] == "regressao" else ""
            )
            cels.append(
                f'<td class="num"><b>{num(fig["pct_origem"][a][b], 1)}</b>{marca}'
                f'<span class="tr-n">{inteiro(round(v, -3))}</span></td>'
            )
        linhas.append(
            f'<tr><th scope="row">{escape(NOME_O[a])}</th><td class="num">{inteiro(round(tot, -3))}</td>{"".join(cels)}</tr>'
        )
    soma = sum(tot_d.values())
    cels = "".join(
        f'<td class="num"><b>{num(100 * tot_d[b] / soma, 1)}</b><span class="tr-n">{inteiro(round(tot_d[b], -3))}</span></td>'
        for b in DESTINOS
    )
    linhas.append(
        f'<tr class="tr-tot"><th scope="row">Todos</th><td class="num">{inteiro(round(soma, -3))}</td>{cels}</tr>'
    )
    return (
        '<div class="table-scroll tr-cem" tabindex="0"><table>'
        f"<caption>De cada 100 eleitores de cada escolha do 1º turno, quantos foram para cada destino no 2º turno "
        f"({escape(cen['nome'].lower())}). Em negrito, a parte da origem; embaixo, os eleitores, arredondados ao milhar. "
        "* estimativa da casa; · regressão sobre as urnas; sem marca, partida em linha publicada por instituto. Brancos e "
        "nulos somados. Estimativa, não medição. Fonte: transferencia.json (cruzamento.cenarios).</caption>"
        f'<thead><tr><th scope="col">No 1º turno</th><th scope="col" class="num">Eleitores</th>{cab}</tr></thead>'
        f"<tbody>{''.join(linhas)}</tbody></table></div>"
    )


def fig_sankey(T: dict) -> str:
    """A figura do capítulo: quatro cenários de cruzamento trocados por botões."""
    cz = T["cruzamento"]
    padrao = cz["padrao"]
    tips = Tips()
    blocos, frases, apos = [], [], []
    escala = None
    for k in cz["ordem"]:
        cen = cz["cenarios"][k]
        chaves = _fichas(cen, tips)
        larga, info = sankey_largo(cen, chaves, f"trl-{k}")
        estreita = sankey_estreito(cen, chaves, f"tre-{k}")
        escala = info["escala_px_por_voto"]
        esc = "" if k == padrao else " hidden"
        blocos.append(
            f'<div data-alt-show="{k}"{esc}>{larga_estreita(larga, estreita)}</div>'
        )
        frases.append(f'<div data-alt-show="{k}"{esc}>{frase_cenario(cen)}</div>')
        apos.append(
            f'<div data-alt-show="{k}"{esc}>{legenda_natureza(cen)}{tabela_cem(cen)}</div>'
        )
    opcoes = [(k, cz["cenarios"][k]["botao"]) for k in cz["ordem"]]
    ctl = botoes(opcoes, padrao, "Cruzamento entre as bases") + "".join(frases)
    legenda = (
        "Soma das matrizes das 27 UFs e do exterior, cada uma ajustada às duas urnas: aptos = válidos + brancos e nulos "
        f"+ quem não votou, nos dois turnos. Uma escala só ({num(escala * 1e6, 2)} px por milhão de eleitores) e nenhuma "
        "espessura mínima: fita fina é fluxo pequeno. Os quatro cenários batem as mesmas margens; muda só a divisão "
        "interna. Estimativa, não medição: nenhuma fita identifica o voto de um eleitor. Fonte: transferencia.json "
        "(cruzamento.cenarios)."
    )
    return figura_html(
        "tr_sankey",
        "".join(blocos),
        legenda,
        tips,
        controles=ctl,
        modo="full",
        apos="".join(apos),
    )


def tabela_matriz(T: dict) -> str:
    """A matriz do cenário padrão em votos, brancos e nulos separados, com a natureza de cada elo."""
    c = T["ipf"]["central"]
    M = c["matriz"]
    org = (
        "lula",
        "flavio",
        "cury",
        "renan",
        "caiado",
        "zema",
        "outros",
        "brancos",
        "nulos",
        "abstencao",
    )
    dst = ("lula", "flavio", "brancos", "nulos", "abstencao")
    nome = dict(NOME_O, brancos="Brancos", nulos="Nulos")
    marca = {"medido": "", "regressao": " ·", "estimado": " *", "zero": " 0"}
    cab = "".join(f'<th scope="col" class="num">{escape(nome[b])}</th>' for b in dst)
    linhas = []
    for a in org:
        tot = sum(M[a][b] for b in dst)
        cels = "".join(
            f'<td class="num">{inteiro(round(M[a][b]))}{marca[c["tipos"][a][b]]}</td>'
            for b in dst
        )
        linhas.append(
            f'<tr><th scope="row">{escape(nome[a])}</th>{cels}<td class="num">{inteiro(round(tot))}</td></tr>'
        )
    tot_d = "".join(
        f'<td class="num">{inteiro(round(sum(M[a][b] for a in org)))}</td>' for b in dst
    )
    return (
        '<div class="table-scroll" tabindex="0"><table><caption>Matriz do cenário padrão em votos, brancos e nulos '
        "separados (linhas: 1º turno; colunas: 2º turno). · regressão; * estimativa da casa; 0 zerada pelo cenário; sem "
        "marca, partida em linha publicada. Fonte: transferencia.json (ipf.central).</caption>"
        f'<thead><tr><th scope="col">1º turno</th>{cab}<th scope="col" class="num">Total</th></tr></thead>'
        f'<tbody>{"".join(linhas)}<tr><th scope="row">Total</th>{tot_d}<td></td></tr></tbody></table></div>'
    )
