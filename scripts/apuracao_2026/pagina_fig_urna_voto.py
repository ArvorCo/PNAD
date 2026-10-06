"""Figuras do capítulo 12: voto por modelo de urna, no país e em cada UF.

- `voto_por_modelo_nacional`: barras por modelo, do mais velho ao mais novo, com
  Flávio e Lula nos válidos e, por botão, abstenção, brancos e nulos; linha fina
  com o valor do país (`secoes.json → urna.bruto`).
- `voto_por_modelo_uf`: 27 painéis, um por UF, com a parcela de cada candidato
  por modelo (ponto do tamanho do número de seções) e a parcela da UF como
  referência (`secoes.json → urna.voto_por_uf_modelo`).

As duas são comparação bruta: misturam modelo com geografia. A leitura controlada
(dentro da zona, do prédio, contra 2022) está em `urna_reguas` e `modelo_urna_zona`.
Cada figura tem a versão larga e a empilhada abaixo de 720 px (`larga_estreita`).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from .pagina_comum import FLAVIO, LULA, NOME_UF, inteiro, num, sinal
from .pagina_fig_base import (
    GRADE,
    HALO,
    INK,
    MUTED,
    PAPER,
    REGIOES,
    Tips,
    area,
    botoes,
    escala,
    ficha,
    figura_html,
    hit,
    larga_estreita,
    legenda_html,
    ln,
    r,
    registra,
    svg_abre,
    t,
    ticks,
)
from .pagina_fig_secoes import nota_cobertura, regiao_da_uf, secoes

MINIMO_SECOES = 20
"""Modelo com menos seções que isso numa UF fica fora do painel daquela UF."""
LARGA, ESTREITA = 1100, 380
CINZA = "#5f6773"
OCRE = "#7d6e33"
ROXO = "#6b4a92"
FRASE_BRUTA = (
    "Comparação bruta: mistura o modelo com a geografia, porque os modelos novos vão "
    "primeiro para capitais e cidades grandes. A leitura controlada está nas figuras "
    "seguintes."
)


def _pct(x: float | None, casas: int = 1) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


def _mi(v: float) -> str:
    return f"{num(v / 1e6, 2)} mi" if v >= 1e6 else f"{num(v / 1e3, 0)} mil"


# ------------------------------------------------------------------ dados


def modelos_ordenados(U: dict) -> list[str]:
    return [m for m in U["modelos"] if m != "sem modelo"]


def referencia_nacional(U: dict) -> dict[str, float]:
    """Parcelas do país a partir de `bruto` (todas as seções válidas, com e sem modelo)."""
    B = U["bruto"]
    val = sum(b["validos"] for b in B) or 1
    vot = sum(b["votantes"] for b in B) or 1
    aptos = sum(b["votantes"] / (1 - b["abstencao_pct"] / 100) for b in B) or 1
    return {
        "flavio_pct": sum(b["flavio_pct"] * b["validos"] for b in B) / val,
        "lula_pct": sum(b["lula_pct"] * b["validos"] for b in B) / val,
        "abstencao_pct": 100 * (1 - vot / aptos),
        "brancos_pct": sum(b["brancos_pct"] * b["votantes"] for b in B) / vot,
        "nulos_pct": sum(b["nulos_pct"] * b["votantes"] for b in B) / vot,
    }


def por_uf(U: dict, minimo: int = MINIMO_SECOES) -> dict[str, dict[str, Any]]:
    """Por UF: parcela da UF (todas as seções), células exibidas e omitidas.

    `dif` é a urna mais nova menos a mais velha entre os modelos exibidos (com ao
    menos `minimo` seções na UF), por candidato. Exterior fica de fora.
    """
    ordem = {m: i for i, m in enumerate(modelos_ordenados(U))}
    out: dict[str, dict[str, Any]] = {}
    for x in U["voto_por_uf_modelo"]:
        uf = x["uf"]
        if regiao_da_uf(uf) not in REGIOES:
            continue
        o = out.setdefault(
            uf, {"validos": 0, "lula": 0, "flavio": 0, "celulas": [], "omitidas": []}
        )
        o["validos"] += x["validos"]
        o["lula"] += x["lula"]
        o["flavio"] += x["flavio"]
        if x["modelo"] in ordem and x["secoes"] >= minimo:
            o["celulas"].append(x)
        else:
            o["omitidas"].append(x)
    for o in out.values():
        o["celulas"].sort(key=lambda c: ordem[c["modelo"]])
        v = o["validos"] or 1
        o["flavio_pct"] = 100 * o["flavio"] / v
        o["lula_pct"] = 100 * o["lula"] / v
        cs = o["celulas"]
        o["dif"] = (
            {
                "flavio": cs[-1]["flavio_pct"] - cs[0]["flavio_pct"],
                "lula": cs[-1]["lula_pct"] - cs[0]["lula_pct"],
                "velho": cs[0]["modelo"],
                "novo": cs[-1]["modelo"],
            }
            if len(cs) > 1
            else None
        )
    return out


def ufs_por_regiao(ufs: Sequence[str]) -> list[str]:
    return sorted(ufs, key=lambda u: (REGIOES.index(regiao_da_uf(u)), u))


# ------------------------------------------------------------------ 1 nacional

SERIES = [
    (
        "cand",
        "Flávio e Lula",
        [("flavio_pct", "Flávio", FLAVIO), ("lula_pct", "Lula", LULA)],
    ),
    ("abstencao_pct", "Abstenção", [("abstencao_pct", "Abstenção", CINZA)]),
    ("brancos_pct", "Brancos", [("brancos_pct", "Brancos", OCRE)]),
    ("nulos_pct", "Nulos", [("nulos_pct", "Nulos", ROXO)]),
]
BASE = {
    "flavio_pct": "% dos válidos",
    "lula_pct": "% dos válidos",
    "abstencao_pct": "% dos aptos",
    "brancos_pct": "% do comparecimento",
    "nulos_pct": "% do comparecimento",
}


def _nacional_svg(
    w: int, modelos: list[str], B: dict, ref: dict, keys: dict[str, str]
) -> str:
    estreito = w < 600
    rot_h = 40 if estreito else 0
    linha_h = rot_h + (60 if estreito else 70)
    topo, base = 64, 56
    h = topo + linha_h * len(modelos) + base
    x0 = 20 if estreito else 260
    x1 = w - (64 if estreito else 90)
    out = [
        svg_abre(
            w,
            h,
            "Voto por modelo de urna no país",
            "Uma linha por modelo de urna, do mais velho ao mais novo, com a parcela de Flávio e de Lula nos "
            "válidos; por botão, abstenção, brancos e nulos. Linha fina: o valor do país.",
        )
    ]
    for chave, _nome, itens in SERIES:
        vals = [B[m][c] for m in modelos for c, _n, _k in itens if B[m][c] is not None]
        hi = max([*vals, *(ref[c] for c, _n, _k in itens)]) * 1.12
        marcas = ticks(0, hi, 4 if estreito else 6)
        X = escala(0, max(hi, marcas[-1]), x0, x1)
        g = []
        yb = topo + linha_h * len(modelos)
        for v in marcas:
            g.append(ln(X(v), topo - 6, X(v), yb, GRADE, 0.8))
            g.append(t(X(v), yb + 18, f"{num(v, 0)}%", 13, MUTED, "middle", mono=True))
        for j, m in enumerate(modelos):
            y = topo + linha_h * j
            b = B[m]
            sub = f"{inteiro(b['secoes'])} seções · {_mi(b['votantes'])} de votantes"
            if estreito:
                g.append(t(x0, y + 16, m, 15, INK, weight="700"))
                g.append(t(x0, y + 33, sub, 13, MUTED))
            else:
                g.append(t(x0 - 16, y + 24, m, 16, INK, "end", "700"))
                g.append(
                    t(
                        x0 - 16,
                        y + 42,
                        f"{inteiro(b['secoes'])} seções",
                        13,
                        MUTED,
                        "end",
                    )
                )
                g.append(
                    t(
                        x0 - 16,
                        y + 58,
                        f"{_mi(b['votantes'])} de votantes",
                        13,
                        MUTED,
                        "end",
                    )
                )
            alt = 22 if len(itens) == 2 else 28
            yy = y + rot_h + (8 if len(itens) == 2 else 16)
            for c, _nome, cor in itens:
                v = b[c]
                if v is None:
                    continue
                barra = r(X(0), yy, X(v) - X(0), alt, cor)
                rot = t(X(v) + 6, yy + alt - 6, _pct(v), 13, INK, mono=True, extra=HALO)
                g.append(
                    hit(
                        barra + rot + area(X(0), yy - 2, X(v) - X(0) + 56, alt + 4),
                        keys[f"{m}|{c}"],
                    )
                )
                yy += alt + 4
        for i, (c, nome, cor) in enumerate(itens):
            xv = X(ref[c])
            g.append(ln(xv, topo - 8, xv, yb, cor, 1.2, ' stroke-dasharray="4 3"'))
            rot = (
                f"País, {nome}: {_pct(ref[c])}"
                if len(itens) == 2
                else f"País: {_pct(ref[c])}"
            )
            yt = topo - 16 if i == 0 else yb + 38
            anc = "end" if xv > (x0 + x1) / 2 else "start"
            g.append(
                t(xv + (4 if anc == "start" else -4), yt, rot, 13, cor, anc, "600")
            )
        disp = "" if chave == "cand" else ' display="none"'
        out.append(f'<g data-alt-show="{chave}"{disp}>{"".join(g)}</g>')
    out.append("</svg>")
    return "".join(out)


@registra("voto_por_modelo_nacional")
def voto_por_modelo_nacional(d, **_op) -> str:
    S = secoes(d)
    U = S["urna"]
    modelos = [
        m for m in modelos_ordenados(U) if any(b["modelo"] == m for b in U["bruto"])
    ]
    B = {b["modelo"]: b for b in U["bruto"]}
    ref = referencia_nacional(U)
    tips = Tips()
    keys: dict[str, str] = {}
    for m in modelos:
        b = B[m]
        for _ch, _nome, itens in SERIES:
            for c, nome, _cor in itens:
                keys[f"{m}|{c}"] = tips.add(
                    ficha(
                        f"{m}: {nome}",
                        BASE[c],
                        [
                            (nome, _pct(b[c], 2)),
                            ("País", _pct(ref[c], 2)),
                            ("Diferença para o país", f"{sinal(b[c] - ref[c], 2)} pp"),
                            ("Seções", inteiro(b["secoes"])),
                            ("Votantes", inteiro(b["votantes"])),
                            ("Válidos", inteiro(b["validos"])),
                        ],
                        "comparação bruta, sem controle de lugar",
                    )
                )
    larga = _nacional_svg(LARGA, modelos, B, ref, keys)
    estreita = _nacional_svg(ESTREITA, modelos, B, ref, keys)
    ctl = botoes([(k, n) for k, n, _ in SERIES], "cand", "Série")
    sem = B.get("sem modelo")
    leg = legenda_html(
        [("Flávio", FLAVIO), ("Lula", LULA), ("valor do país (linha tracejada)", PAPER)]
    )
    legenda = (
        f"{FRASE_BRUTA} Flávio e Lula em % dos válidos; abstenção em % dos aptos; brancos e nulos em % do "
        "comparecimento. Modelos do mais velho (em cima) ao mais novo."
        + (
            f" Fora do gráfico: {inteiro(sem['secoes'])} seções sem modelo identificado (boletim sem log da urna)."
            if sem
            else ""
        )
        + f" {nota_cobertura(S)} Fonte: secoes.json (urna.bruto)."
    )
    return figura_html(
        "voto_por_modelo_nacional",
        larga_estreita(larga, estreita),
        legenda,
        tips,
        controles=ctl,
        modo="full",
        apos=leg,
    )


# ------------------------------------------------------------------ 2 por UF


def _span(P: dict[str, dict[str, Any]]) -> float:
    """Meia-altura comum dos painéis: o maior desvio de um modelo contra a UF."""
    m = 2.0
    for o in P.values():
        for c in o["celulas"]:
            m = max(
                m,
                abs(c["flavio_pct"] - o["flavio_pct"]),
                abs(c["lula_pct"] - o["lula_pct"]),
            )
    return math.ceil(m * 1.08)


def _painel(
    o: dict[str, Any],
    uf: str,
    px: float,
    py: float,
    pw: float,
    modelos: list[str],
    span: float,
    rmax: int,
    keys: dict[str, str],
) -> str:
    g = [r(px, py, pw, PH_PLOT + 58, "#efe9da")]
    g.append(t(px + 8, py + 19, uf, 15, INK, weight="700"))
    yt, yb = py + 30, py + 30 + PH_PLOT
    xa, xb = px + 22, px + pw - 22
    xs = {
        m: (xa + (xb - xa) * i / max(len(modelos) - 1, 1))
        for i, m in enumerate(modelos)
    }
    curto = (xb - xa) / max(len(modelos) - 1, 1) < 36
    for m in modelos:
        g.append(
            t(
                xs[m],
                yb + 20,
                m[-2:] if curto else m[-4:],
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    for cand, cor in (("flavio", FLAVIO), ("lula", LULA)):
        ref = o[f"{cand}_pct"]
        Y = escala(ref - span, ref + span, yb, yt)
        s = []
        guia = 10 if span > 12 else 5
        for dv in (-guia, guia):
            s.append(ln(px + 4, Y(ref + dv), px + pw - 4, Y(ref + dv), GRADE, 0.8))
        s.append(
            ln(px + 4, Y(ref), px + pw - 4, Y(ref), INK, 1, ' stroke-dasharray="3 3"')
        )
        dif = o["dif"]
        if dif:
            s.append(
                t(
                    px + pw - 8,
                    py + 19,
                    f"{sinal(dif[cand], 1)} pp",
                    13,
                    cor,
                    "end",
                    "600",
                )
            )
        cs = o["celulas"]
        if len(cs) > 1:
            pts = " ".join(
                f"{xs[c['modelo']]:.1f},{Y(c[f'{cand}_pct']):.1f}" for c in cs
            )
            s.append(
                f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="1.6"/>'
            )
        for c in cs:
            x, y = xs[c["modelo"]], Y(c[f"{cand}_pct"])
            raio = 2.5 + 5.5 * math.sqrt(c["secoes"] / rmax)
            ponto = (
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{raio:.1f}" fill="{cor}" '
                f'stroke="{PAPER}" stroke-width="1"/>'
            )
            s.append(
                hit(ponto + area(x - 12, y - 12, 24, 24), keys[f"{uf}|{c['modelo']}"])
            )
        disp = "" if cand == "flavio" else ' display="none"'
        g.append(f'<g data-alt-show="{cand}"{disp}>{"".join(s)}</g>')
    return "".join(g)


PH_PLOT = 96
PH = PH_PLOT + 58 + 12


def _uf_svg(
    w: int,
    P: dict[str, dict[str, Any]],
    modelos: list[str],
    span: float,
    keys: dict[str, str],
) -> str:
    cols = 6 if w >= 600 else 2
    gap = 12
    pw = (w - 2 * 14 - gap * (cols - 1)) / cols
    rmax = max((c["secoes"] for o in P.values() for c in o["celulas"]), default=1)
    corpo, y = [], 8
    for reg in REGIOES:
        ufs = [u for u in ufs_por_regiao(P) if regiao_da_uf(u) == reg]
        if not ufs:
            continue
        corpo.append(t(14, y + 18, reg, 14, MUTED, weight="700"))
        corpo.append(ln(14, y + 26, w - 14, y + 26, GRADE, 0.8))
        y += 34
        for i, uf in enumerate(ufs):
            px = 14 + (i % cols) * (pw + gap)
            py = y + (i // cols) * PH
            corpo.append(_painel(P[uf], uf, px, py, pw, modelos, span, rmax, keys))
        y += PH * math.ceil(len(ufs) / cols) + 4
    h = y + 8
    return (
        svg_abre(
            w,
            h,
            "Voto por modelo de urna em cada UF",
            "Um painel por UF, agrupados por região: a parcela do candidato em cada modelo de urna, do mais velho "
            "ao mais novo, com o ponto do tamanho do número de seções e a linha tracejada na parcela da UF.",
        )
        + "".join(corpo)
        + "</svg>"
    )


@registra("voto_por_modelo_uf")
def voto_por_modelo_uf(d, **_op) -> str:
    S = secoes(d)
    U = S["urna"]
    P = por_uf(U)
    modelos = [
        m
        for m in modelos_ordenados(U)
        if any(c["modelo"] == m for o in P.values() for c in o["celulas"])
    ]
    span = _span(P)
    tips = Tips()
    keys: dict[str, str] = {}
    for uf, o in P.items():
        for c in o["celulas"]:
            keys[f"{uf}|{c['modelo']}"] = tips.add(
                ficha(
                    f"{NOME_UF.get(uf, uf)}: {c['modelo']}",
                    "comparação bruta, dentro da UF",
                    [
                        ("Seções", inteiro(c["secoes"])),
                        ("Votantes", inteiro(c["votantes"])),
                        (
                            "Flávio",
                            f"{_pct(c['flavio_pct'], 2)} (UF {_pct(o['flavio_pct'], 2)})",
                        ),
                        (
                            "Lula",
                            f"{_pct(c['lula_pct'], 2)} (UF {_pct(o['lula_pct'], 2)})",
                        ),
                        ("Abstenção", _pct(c["abstencao_pct"], 2)),
                    ],
                    "Flávio e Lula em % dos válidos; abstenção em % dos aptos",
                )
            )
    larga = _uf_svg(LARGA, P, modelos, span, keys)
    estreita = _uf_svg(ESTREITA, P, modelos, span, keys)
    ctl = botoes([("flavio", "Flávio"), ("lula", "Lula")], "flavio", "Candidato")
    omit = [x for o in P.values() for x in o["omitidas"]]
    ext = [x for x in U["voto_por_uf_modelo"] if regiao_da_uf(x["uf"]) not in REGIOES]
    guia = 10 if span > 12 else 5
    legenda = (
        f"{FRASE_BRUTA} Cada painel vai de {num(span, 0)} pontos abaixo a {num(span, 0)} pontos acima da parcela "
        f"da UF (linha tracejada), a mesma escala nos 27; linhas claras a {guia} pontos da UF. O número no canto "
        "é a urna mais nova menos a mais velha da UF, em pontos. Eixo: ano do modelo (UE)."
        f" Fora dos painéis: {len(omit)} combinações de UF e modelo com menos de {MINIMO_SECOES} seções ou sem "
        f"modelo ({inteiro(sum(x['secoes'] for x in omit))} seções), que entram só na parcela da UF"
        + (
            f", e o exterior ({inteiro(sum(x['secoes'] for x in ext))} seções)"
            if ext
            else ""
        )
        + f". {nota_cobertura(S)} Fonte: secoes.json (urna.voto_por_uf_modelo)."
    )
    leg = legenda_html(
        [
            ("Flávio, % dos válidos", FLAVIO),
            ("Lula, % dos válidos", LULA),
            ("parcela da UF (linha tracejada)", PAPER),
        ],
        "Ponto do tamanho do número de seções do modelo na UF",
    )
    return figura_html(
        "voto_por_modelo_uf",
        larga_estreita(larga, estreita),
        legenda,
        tips,
        controles=ctl,
        modo="full",
        apos=leg,
    )
