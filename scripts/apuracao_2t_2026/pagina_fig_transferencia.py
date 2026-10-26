"""Sankey da transferência 1º → 2º turno (capítulo "De onde veio o voto").

Fonte: ``transferencia.json`` (``ipf.central.matriz`` e ``ipf.central.tipos``).
Origens do 1º turno à esquerda, destinos do 2º à direita, largura proporcional
aos votos, sem espessura mínima (fluxo de cem mil eleitores aparece fino). A
fita tem a cor do destino; o preenchimento diz a natureza do elo: sólida quando a
prior da linha vem de matriz publicada por instituto, pontilhada quando vem da
regressão sobre as urnas (quem faltou no 1º turno), hachurada quando é hipótese
declarada da casa. Em todos os casos a largura final sai do ajuste às margens.
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
    ficha,
    figura_html,
    hit,
    legenda_html,
    svg_abre,
    t,
)

ORIGENS = (
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
DESTINOS = ("lula", "flavio", "brancos", "nulos", "abstencao")
NOME = {
    "lula": "Lula",
    "flavio": "Flávio",
    "cury": "Augusto Cury",
    "renan": "Renan Santos",
    "caiado": "Ronaldo Caiado",
    "zema": "Romeu Zema",
    "outros": "Demais",
    "brancos": "Brancos",
    "nulos": "Nulos",
    "abstencao": "Abstenção",
}
COR_DEST = {
    "lula": LULA,
    "flavio": FLAVIO,
    "brancos": "#b9a77a",
    "nulos": "#7a6a4a",
    "abstencao": "#8f938b",
}
COR_ORIG = {
    "lula": LULA,
    "flavio": FLAVIO,
    "cury": "#0f7f5f",
    "renan": "#3d8a74",
    "caiado": "#6aa392",
    "zema": "#8fb8aa",
    "outros": "#a9b8b1",
    "brancos": "#b9a77a",
    "nulos": "#7a6a4a",
    "abstencao": "#8f938b",
}
NATUREZA = {
    "medido": "prior em linha publicada por instituto (voto lembrado × intenção), ajustada às urnas",
    "regressao": "regressão sobre as urnas (quem faltou no 1º turno), fixa no ajuste",
    "estimado": "hipótese declarada da casa, ajustada às urnas",
}
PERMANENCIA = {
    ("lula", "lula"),
    ("flavio", "flavio"),
    ("brancos", "brancos"),
    ("nulos", "nulos"),
    ("abstencao", "abstencao"),
}
TINTA_LEG = "#4f5d58"
LEG_SOLIDA = TINTA_LEG
LEG_HACHURA = f"repeating-linear-gradient(45deg,{TINTA_LEG} 0 3px,{PAPER} 3px 6px)"
LEG_PONTO = f"radial-gradient(circle,{PAPER} 1.4px,{TINTA_LEG} 1.6px) 0 0/5px 5px"


def mi(v: float) -> str:
    return f"{num(v / 1e6, 2)} mi"


def _defs(prefixo: str) -> str:
    out = ["<defs>"]
    for k, cor in COR_DEST.items():
        out.append(
            f'<pattern id="{prefixo}-h-{k}" patternUnits="userSpaceOnUse" width="7" height="7" '
            f'patternTransform="rotate(40)"><rect width="7" height="7" fill="{PAPER}"/>'
            f'<rect width="3.6" height="7" fill="{cor}"/></pattern>'
        )
        out.append(
            f'<pattern id="{prefixo}-p-{k}" patternUnits="userSpaceOnUse" width="6" height="6">'
            f'<rect width="6" height="6" fill="{cor}"/>'
            f'<circle cx="1.5" cy="1.5" r="1.25" fill="{PAPER}"/>'
            f'<circle cx="4.5" cy="4.5" r="1.25" fill="{PAPER}"/></pattern>'
        )
    out.append("</defs>")
    return "".join(out)


def _preenche(tipo: str, destino: str, prefixo: str) -> str:
    if tipo == "medido":
        return f'fill="{COR_DEST[destino]}" fill-opacity="0.74"'
    if tipo == "regressao":
        return f'fill="url(#{prefixo}-p-{destino})"'
    return f'fill="url(#{prefixo}-h-{destino})"'


def sankey(
    matriz: dict[str, dict[str, float]],
    tipos: dict[str, dict[str, str]],
    *,
    prefixo: str,
    titulo: str,
    desc: str,
    excluir: set[tuple[str, str]] | frozenset = frozenset(),
    altura_util: float = 640.0,
) -> tuple[str, Tips, dict]:
    """Desenha o Sankey; devolve (svg, fichas, estatística das fitas por natureza)."""
    celulas = [
        (a, b, float(matriz[a][b]))
        for a in ORIGENS
        for b in DESTINOS
        if (a, b) not in excluir and float(matriz[a][b]) > 0
    ]
    tot_o = {a: sum(v for x, _, v in celulas if x == a) for a in ORIGENS}
    tot_d = {b: sum(v for _, y, v in celulas if y == b) for b in DESTINOS}
    total = sum(tot_o.values())
    escala = altura_util / total
    gap_e, gap_d = 16.0, 22.0
    alt_e = altura_util + gap_e * (sum(1 for a in ORIGENS if tot_o[a] > 0) - 1)
    alt_d = altura_util + gap_d * (sum(1 for b in DESTINOS if tot_d[b] > 0) - 1)
    topo = 70.0
    alto = max(alt_e, alt_d)
    y_e = topo + (alto - alt_e) / 2
    y_d = topo + (alto - alt_d) / 2
    x0, x1, larg = 300.0, 800.0, 12.0
    pos_e: dict[str, float] = {}
    for a in ORIGENS:
        if tot_o[a] <= 0:
            continue
        pos_e[a] = y_e
        y_e += tot_o[a] * escala + gap_e
    pos_d: dict[str, float] = {}
    for b in DESTINOS:
        if tot_d[b] <= 0:
            continue
        pos_d[b] = y_d
        y_d += tot_d[b] * escala + gap_d
    h = topo + alto + 30
    out = [svg_abre(1100, h, titulo, desc), _defs(prefixo)]
    out.append(
        t(x0 + larg, 36, "1º TURNO, 04/10", 12, MUTED, "end", weight="700", mono=True)
    )
    out.append(
        t(x1, 36, "2º TURNO, 25/10", 12, MUTED, "start", weight="700", mono=True)
    )
    tips = Tips()
    cursor_e = dict(pos_e)
    cursor_d = dict(pos_d)
    estat: dict[str, dict[str, float]] = {}
    fitas = []
    for a in ORIGENS:
        for b in DESTINOS:
            if (a, b) in excluir:
                continue
            v = float(matriz[a][b])
            if v <= 0:
                continue
            esp = v * escala
            ya, yb = cursor_e[a], cursor_d[b]
            cursor_e[a] += esp
            cursor_d[b] += esp
            tipo = tipos[a][b]
            e = estat.setdefault(tipo, {"elos": 0, "votos": 0.0})
            e["elos"] += 1
            e["votos"] += v
            xa, xb = x0 + larg, x1
            xm1, xm2 = xa + (xb - xa) * 0.42, xa + (xb - xa) * 0.58
            d = (
                f"M{xa:.1f} {ya:.2f}C{xm1:.1f} {ya:.2f} {xm2:.1f} {yb:.2f} {xb:.1f} {yb:.2f}"
                f"L{xb:.1f} {yb + esp:.2f}C{xm2:.1f} {yb + esp:.2f} {xm1:.1f} {ya + esp:.2f} {xa:.1f} {ya + esp:.2f}Z"
            )
            k = tips.add(
                ficha(
                    f"{NOME[a]} → {NOME[b]}",
                    "elo da matriz de hipótese",
                    [
                        ("Votos", inteiro(round(v))),
                        ("Parte da origem", f"{num(100 * v / tot_o[a], 1)}%"),
                        ("Parte do destino", f"{num(100 * v / tot_d[b], 1)}%"),
                        ("Espessura", f"{num(esp, 2)} px"),
                    ],
                    NATUREZA[tipo],
                )
            )
            fitas.append(
                hit(
                    f'<path d="{d}" {_preenche(tipo, b, prefixo)} data-votos="{v:.0f}" '
                    f'data-esp="{esp:.3f}" data-tipo="{tipo}"/>',
                    k,
                )
            )
    out.extend(fitas)
    for a, y in pos_e.items():
        alt = tot_o[a] * escala
        out.append(
            f'<rect x="{x0:.1f}" y="{y:.2f}" width="{larg:.0f}" height="{alt:.2f}" fill="{COR_ORIG[a]}"/>'
        )
        out.append(
            t(x0 - 10, y + alt / 2 + 5, f"{NOME[a]} {mi(tot_o[a])}", 14, INK, "end")
        )
    for b, y in pos_d.items():
        alt = tot_d[b] * escala
        out.append(
            f'<rect x="{x1:.1f}" y="{y:.2f}" width="{larg:.0f}" height="{alt:.2f}" fill="{COR_DEST[b]}"/>'
        )
        cor = COR_DEST[b] if b in ("lula", "flavio") else INK
        out.append(
            t(
                x1 + larg + 10,
                y + alt / 2 + 5,
                f"{NOME[b]} {mi(tot_d[b])}",
                15,
                cor,
                weight="600",
            )
        )
    out.append("</svg>")
    tot_v = sum(e["votos"] for e in estat.values())
    for e in estat.values():
        e["pct_votos"] = 100 * e["votos"] / tot_v
    return "".join(out), tips, {"escala_px_por_voto": escala, "natureza": estat}


def legenda_natureza(estat: dict) -> str:
    n = estat["natureza"]

    def item(tipo: str, rotulo: str) -> str:
        e = n.get(tipo, {"elos": 0, "pct_votos": 0.0})
        return f"{rotulo}: {e['elos']} elos, {num(e['pct_votos'], 1)}% dos votos"

    itens = [
        (item("medido", "Sólida, linha publicada por instituto"), LEG_SOLIDA),
        (item("regressao", "Pontilhada, regressão sobre as urnas"), LEG_PONTO),
        (item("estimado", "Hachurada, hipótese da casa"), LEG_HACHURA),
    ]
    cores = [(f"Para {NOME[b]}", COR_DEST[b]) for b in DESTINOS]
    return legenda_html(itens, "Natureza do elo") + legenda_html(
        cores, "Cor = destino no 2º turno"
    )


def fig_sankey(T: dict) -> str:
    c = T["ipf"]["central"]
    svg, tips, est = sankey(
        c["matriz"],
        c["tipos"],
        prefixo="trs",
        titulo="De onde veio o voto do 2º turno: matriz de hipótese, Brasil",
        desc=(
            "Origens do 1º turno à esquerda (Lula, Flávio, quatro candidaturas de terceira via, demais, brancos, "
            "nulos e abstenção), destinos do 2º turno à direita. Largura proporcional aos votos, sem espessura mínima."
        ),
    )
    m = c["metricas"]
    legenda = (
        f"Soma das matrizes das 27 UFs e do exterior, cada uma ajustada às duas urnas. As três fitas largas são permanência: "
        f"{mi(c['matriz']['lula']['lula'])} de Lula a Lula, {mi(c['matriz']['flavio']['flavio'])} de Flávio a Flávio e "
        f"{mi(m['ausentes_nos_dois'])} de ausentes nos dois turnos. Escala: {num(est['escala_px_por_voto'] * 1e6, 2)} px por milhão de votos. "
        "Fonte: transferencia.json (ipf.central)."
    )
    return figura_html(
        "tr_sankey",
        svg,
        legenda,
        tips,
        modo="scroll",
        minw=760,
        apos=legenda_natureza(est),
    )


def fig_sankey_mudou(T: dict) -> str:
    c = T["ipf"]["central"]
    svg, tips, est = sankey(
        c["matriz"],
        c["tipos"],
        prefixo="trm",
        titulo="Só o voto que mudou de lugar entre os turnos",
        desc=(
            "A mesma matriz sem as fitas de permanência (Lula a Lula, Flávio a Flávio, branco a branco, nulo a nulo, "
            "ausente a ausente). Cada lado soma só os votos que trocaram de categoria."
        ),
        excluir=set(PERMANENCIA),
        altura_util=560.0,
    )
    m = c["metricas"]
    total = sum(
        float(c["matriz"][a][b])
        for a in ORIGENS
        for b in DESTINOS
        if (a, b) not in PERMANENCIA
    )
    legenda = (
        f"{mi(total)} de votos trocaram de categoria. À direita, Lula recebe {mi(m['ganho_fora_base_lula'])} fora da própria base "
        f"e Flávio {mi(m['ganho_fora_base_flavio'])}: razão de {num(m['razao_consolidacao_flavio_lula'], 2)} para 1. "
        f"Escala: {num(est['escala_px_por_voto'] * 1e6, 2)} px por milhão, sem espessura mínima. Fonte: transferencia.json (ipf.central)."
    )
    return figura_html(
        "tr_sankey_mudou",
        svg,
        legenda,
        tips,
        modo="scroll",
        minw=760,
        apos=legenda_natureza(est),
    )


def tabela_matriz(T: dict) -> str:
    """A matriz central em números, com a natureza de cada elo (sem JS)."""
    c = T["ipf"]["central"]
    M = c["matriz"]
    marca = {"medido": "", "regressao": " ·", "estimado": " *"}
    cab = "".join(f"<th scope=col class=num>{escape(NOME[b])}</th>" for b in DESTINOS)
    linhas = []
    for a in ORIGENS:
        tot = sum(M[a][b] for b in DESTINOS)
        cels = "".join(
            f"<td class=num>{inteiro(round(M[a][b]))}{marca[c['tipos'][a][b]]}</td>"
            for b in DESTINOS
        )
        linhas.append(
            f"<tr><th scope=row>{escape(NOME[a])}</th>{cels}<td class=num>{inteiro(round(tot))}</td></tr>"
        )
    tot_d = "".join(
        f"<td class=num>{inteiro(round(sum(M[a][b] for a in ORIGENS)))}</td>"
        for b in DESTINOS
    )
    return (
        '<div class="table-scroll" tabindex="0"><table><caption>Matriz central em votos (linhas: 1º turno; colunas: 2º turno). '
        "· regressão; * hipótese da casa; sem marca, prior em linha publicada.</caption>"
        f"<thead><tr><th scope=col>1º turno</th>{cab}<th scope=col class=num>Total</th></tr></thead>"
        f"<tbody>{''.join(linhas)}<tr><th scope=row>Total</th>{tot_d}<td></td></tr></tbody></table></div>"
    )
