#!/usr/bin/env python3
"""Datafolha 08/2026 - transferencia de voto e graficos.

Gera, a partir do relatorio completo BR-04496/2026:

  1. Sankey Lula x Flavio: fluxo estimado 1o -> 2o turno via matriz de
     afinidade a priori ajustada por IPF (minima entropia cruzada) para
     bater exatamente com as margens publicadas.
  2. Painel consolidado dos quatro cenarios de 2o turno.
  3. Blocos do 1o turno (voto util: oposicao somada x Lula).
  4. Serie historica de resiliencia (jun/25 -> ago/26).
  5. Rejeicao x rendimento eleitoral (teto anti-Lula).

Saidas:
  docs/img/datafolha_082026/*.png
  analysis/datafolha_082026/dados.json (numeros + matriz de fluxo)
  (blocos HTML do futuro dossie sao mantidos a mao em
   analysis/datafolha_082026/blocos/)

Metodo (Sankey): leitura de fluxo agregado em corte transversal, nao painel
individual - mesma gramatica do dossie 06/2026. A matriz a priori codifica
afinidade politica (evidencia: nos cenarios sem Flavio o candidato de
direita herda o bloco e chega a 37-40; Lula fica em 47-48 contra qualquer um,
logo o pool e majoritariamente anti-Lula; crosstabs de junho mostraram
consolidacao ~2:1 pro Flavio). O IPF ajusta essa priori as margens
publicadas de agosto, produzindo a matriz de maxima entropia cruzada
compativel com os totais - sem inventar numero fora das somas do Datafolha.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch, PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "docs" / "img" / "datafolha_082026"
OUT_DIR = ROOT / "analysis" / "datafolha_082026"
BLOCO_DIR = OUT_DIR / "blocos"
for d in (IMG_DIR, OUT_DIR, BLOCO_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Paleta da casa (dossies brasil.arvor.co)
C = {
    "lula": "#c0392b",
    "lula_soft": "#e8b4ad",
    "flavio": "#1f5fa8",
    "flavio_soft": "#a9c4e4",
    "gold": "#b07d10",
    "green": "#1c7d54",
    "violet": "#6b4ea8",
    "gray": "#7b8494",
    "gray_soft": "#c9ced8",
    "ink": "#14171d",
    "muted": "#5e6675",
    "faint": "#8b93a3",
    "paper": "#faf8f3",
    "panel": "#ffffff",
    "line": "#dde2ec",
}

plt.rcParams.update(
    {
        "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"],
        "figure.facecolor": C["paper"],
        "axes.facecolor": C["paper"],
        "savefig.facecolor": C["paper"],
        "text.color": C["ink"],
        "axes.edgecolor": C["line"],
        "axes.labelcolor": C["ink"],
        "xtick.color": C["muted"],
        "ytick.color": C["muted"],
        "svg.fonttype": "none",
    }
)

DPI = 200
CRED = "Análise Arvor · brasil.arvor.co · Datafolha 18–19/08/2026 · BR-04496/2026"

# ---------------------------------------------------------------- dados

PRIMEIRO_TURNO = {
    "Lula (PT)": 39,
    "Flávio Bolsonaro (PL)": 33,
    "Ronaldo Caiado (PSD)": 5,
    "Renan Santos (Missão)": 4,
    "Romeu Zema (Novo)": 3,
    "Augusto Cury (Avante)": 2,
    "Samara (UP)": 1,
    "Rui C. Pimenta (PCO)": 1,
    "Edmilson Costa (PCB)": 1,
    "Wilson Grassi (Democrata)": 1,
    "Branco/nulo/nenhum": 6,
    "Não sabe": 4,
}
PRIMEIRO_TURNO_JUL = {
    "Lula (PT)": 40,
    "Flávio Bolsonaro (PL)": 32,
    "Ronaldo Caiado (PSD)": 4,
    "Romeu Zema (Novo)": 3,
    "Renan Santos (Missão)": 3,
    "Augusto Cury (Avante)": 2,
    "Samara Martins (UP)": 2,
    "Cabo Daciolo (Mobiliza)": 1,
    "Rui C. Pimenta (PCO)": 1,
    "Branco/nulo/nenhum": 7,
    "Não sabe": 4,
}

SEGUNDO_TURNO = {
    "Flávio Bolsonaro (PL)": {"lula": 47, "adversario": 43, "bn": 9, "ns": 2},
    "Ronaldo Caiado (PSD)": {"lula": 47, "adversario": 40, "bn": 11, "ns": 3},
    "Romeu Zema (Novo)": {"lula": 48, "adversario": 38, "bn": 12, "ns": 2},
    "Renan Santos (Missão)": {"lula": 47, "adversario": 37, "bn": 14, "ns": 2},
}

REJEICAO = {
    "Flávio Bolsonaro (PL)": 46,
    "Lula (PT)": 45,
    "Pablo Marçal (PRTB)": 22,
    "Romeu Zema (Novo)": 16,
    "Ronaldo Caiado (PSD)": 14,
    "Renan Santos (Missão)": 14,
    "Rui C. Pimenta (PCO)": 13,
    "Samara (UP)": 10,
    "Edmilson Costa (PCB)": 10,
    "Augusto Cury (Avante)": 8,
}

# Serie Lula x Flavio (2o turno) - rotulos e valores dos graficos publicados
SERIE_LF = {
    "rotulos": [
        "14 jun\n2025",
        "2 ago\n2025",
        "6 dez\n2025",
        "7 mar\n2026",
        "11 abr\n2026",
        "16 mai\n2026",
        "22 mai\n2026",
        "20 jun\n2026",
        "24 jul\n2026",
        "21 ago\n2026",
    ],
    "lula": [47, 48, 51, 46, 45, 45, 47, 47, 48, 47],
    "flavio": [38, 37, 36, 43, 46, 45, 43, 43, 43, 43],
}

# ------------------------------------------------- IPF: matriz de fluxo

SOURCES = list(PRIMEIRO_TURNO.keys())
TARGETS = ["Lula", "Flávio", "Branco/nulo", "Não sabe"]

# Afinidade a priori (linhas = origem 1T, colunas = destino 2T LxF).
# Hipoteses ideologicas (rev. 25/07): bases 100% fieis - voto de Flavio no
# 1T vai INTEIRO para Flavio no 2T (zero para Lula e zero para branco/nulo;
# cruzamento de base seria erro de qualidade da pesquisa, entrevistado
# "trollando"), e o mesmo vale para a base de Lula. Toda a transferencia
# acontece no meio: Daciolo quase integral para Flavio (0 para B/N); Samara
# em totalidade para Lula; Cury majoritariamente Flavio; o branco/nulo do
# 2T e alimentado quase so por Caiado/Zema/Renan (muito Flavio, um pouco
# Lula, resto anula). Zeros sao estruturais: o IPF os preserva.
PRIOR = np.array(
    [
        # Lula  Flavio  B/N    NS
        [0.995, 0.000, 0.000, 0.005],  # Lula: base integral
        [0.000, 0.995, 0.000, 0.005],  # Flavio: base integral
        [0.120, 0.500, 0.360, 0.020],  # Caiado
        [0.060, 0.580, 0.340, 0.020],  # Renan
        [0.080, 0.550, 0.350, 0.020],  # Zema
        [0.250, 0.600, 0.120, 0.030],  # Cury: maioria Flavio
        [0.980, 0.000, 0.010, 0.010],  # Samara: totalidade Lula
        [0.650, 0.030, 0.300, 0.020],  # Pimenta
        [0.850, 0.020, 0.110, 0.020],  # Edmilson
        [0.100, 0.750, 0.120, 0.030],  # Grassi
        [0.100, 0.150, 0.720, 0.030],  # B/N
        [0.180, 0.180, 0.340, 0.300],  # NS
    ]
)


def ipf(
    prior: np.ndarray, rows: np.ndarray, cols: np.ndarray, iters: int = 2000
) -> np.ndarray:
    """Ajuste proporcional iterativo (RAS): minima entropia cruzada vs prior."""
    m = prior * rows[:, None]
    for _ in range(iters):
        m *= (rows / np.maximum(m.sum(axis=1), 1e-12))[:, None]
        m *= (cols / np.maximum(m.sum(axis=0), 1e-12))[None, :]
    return m


rows = np.array([PRIMEIRO_TURNO[s] for s in SOURCES], dtype=float)
cols = np.array([47, 43, 9, 2], dtype=float)
# Somas publicadas: 100 no 1T e 101 no 2T por arredondamento.
# Escalamos as origens para o total do destino e reportamos em pontos do 2T.
rows_scaled = rows * cols.sum() / rows.sum()
FLOW = ipf(PRIOR, rows_scaled, cols)


# ---------------------------------------------------------------- sankey


def draw_sankey() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 11.0), dpi=DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    src_colors = {
        "Lula (PT)": C["lula"],
        "Flávio Bolsonaro (PL)": C["flavio"],
        "Ronaldo Caiado (PSD)": C["gold"],
        "Renan Santos (Missão)": C["violet"],
        "Romeu Zema (Novo)": C["green"],
        "Augusto Cury (Avante)": "#8a6d3b",
        "Samara (UP)": "#a4443c",
        "Rui C. Pimenta (PCO)": "#b06060",
        "Edmilson Costa (PCB)": "#8c3f45",
        "Wilson Grassi (Democrata)": "#4a7fa5",
        "Branco/nulo/nenhum": C["gray"],
        "Não sabe": C["gray_soft"],
    }
    tgt_colors = [C["lula"], C["flavio"], C["gray"], C["gray_soft"]]

    total = cols.sum()
    gap_s, gap_t = 0.012, 0.028
    usable_s = 1.0 - gap_s * (len(SOURCES) - 1) - 0.10
    usable_t = 1.0 - gap_t * (len(TARGETS) - 1) - 0.10

    src_h = rows_scaled / total * usable_s
    tgt_h = cols / total * usable_t

    # posicoes (top -> bottom)
    src_y, y = {}, 0.95
    for s, h in zip(SOURCES, src_h):
        src_y[s] = (y - h, y)
        y -= h + gap_s
    tgt_y, y = {}, 0.95
    for t, h in zip(TARGETS, tgt_h):
        tgt_y[t] = (y - h, y)
        y -= h + gap_t

    x0, x1, bw = 0.235, 0.765, 0.014

    # nos
    for i, s in enumerate(SOURCES):
        yb, yt = src_y[s]
        ax.add_patch(
            FancyBboxPatch(
                (x0 - bw, yb),
                bw,
                yt - yb,
                boxstyle="square,pad=0",
                fc=src_colors[s],
                ec="none",
            )
        )
        v = PRIMEIRO_TURNO[s]
        nome = s.replace(" Bolsonaro", "").replace("Branco/nulo/nenhum", "Branco/nulo")
        fs = 12.5 if v >= 8 else 10.5
        ax.text(
            x0 - bw - 0.012,
            (yb + yt) / 2,
            f"{nome}  {v}",
            ha="right",
            va="center",
            fontsize=fs,
            fontweight="bold" if v >= 8 else "normal",
            color=C["ink"] if v >= 8 else C["muted"],
        )
    for j, t in enumerate(TARGETS):
        yb, yt = tgt_y[t]
        ax.add_patch(
            FancyBboxPatch(
                (x1, yb),
                bw,
                yt - yb,
                boxstyle="square,pad=0",
                fc=tgt_colors[j],
                ec="none",
            )
        )
        v = int(cols[j])
        fs = 13.5 if v >= 9 else 11
        ax.text(
            x1 + bw + 0.012,
            (yb + yt) / 2,
            f"{t}  {v}",
            ha="left",
            va="center",
            fontsize=fs,
            fontweight="bold" if v >= 9 else "normal",
            color=C["ink"] if v >= 9 else C["muted"],
        )

    # fluxos (ribbons bezier), coloridos pelo destino
    src_off = {s: src_y[s][1] for s in SOURCES}
    tgt_off = {t: tgt_y[t][1] for t in TARGETS}
    for i, s in enumerate(SOURCES):
        for j, t in enumerate(TARGETS):
            f = FLOW[i, j]
            if f < 0.08:
                continue
            hs = f / total * usable_s
            ht = f / total * usable_t
            sy1 = src_off[s]
            sy0 = sy1 - hs
            src_off[s] = sy0
            ty1 = tgt_off[t]
            ty0 = ty1 - ht
            tgt_off[t] = ty0
            cx1, cx2 = x0 + 0.30 * (x1 - x0), x0 + 0.70 * (x1 - x0)
            verts = [
                (x0, sy1),
                (cx1, sy1),
                (cx2, ty1),
                (x1, ty1),
                (x1, ty0),
                (cx2, ty0),
                (cx1, sy0),
                (x0, sy0),
                (x0, sy1),
            ]
            codes = [
                MplPath.MOVETO,
                MplPath.CURVE4,
                MplPath.CURVE4,
                MplPath.CURVE4,
                MplPath.LINETO,
                MplPath.CURVE4,
                MplPath.CURVE4,
                MplPath.CURVE4,
                MplPath.CLOSEPOLY,
            ]
            base = i == j and s.split(" ")[0] in ("Lula", "Flávio")
            alpha = 0.32 if base else 0.62
            ax.add_patch(
                PathPatch(
                    MplPath(verts, codes), fc=tgt_colors[j], ec="none", alpha=alpha
                )
            )
            if f >= 1.4 and not base:
                ax.text(
                    (x0 + x1) / 2,
                    (sy1 + sy0 + ty1 + ty0) / 4,
                    f"{f:.1f}",
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontweight="bold",
                    color=tgt_colors[j],
                )

    ax.text(
        x0 - bw,
        0.985,
        "1º TURNO",
        ha="right",
        fontsize=13,
        fontweight="bold",
        color=C["muted"],
    )
    ax.text(
        x1 + bw,
        0.985,
        "2º TURNO  Lula × Flávio",
        ha="left",
        fontsize=13,
        fontweight="bold",
        color=C["muted"],
    )

    fl_ext = FLOW[2:, 1].sum()
    lu_ext = FLOW[2:, 0].sum()
    fig.suptitle(
        "Para onde vai o voto quando a eleição afunila",
        fontsize=21,
        fontweight="bold",
        x=0.5,
        y=0.985,
    )
    ax.set_title(
        f"Fluxo estimado 1º → 2º turno (pontos percentuais). Fora das bases, "
        f"~{fl_ext:.0f} pts consolidam em Flávio contra ~{lu_ext:.0f} em Lula.\n"
        "Matriz de afinidade ajustada por IPF às margens publicadas · leitura agregada (não é painel individual)",
        fontsize=11.5,
        color=C["muted"],
        pad=30,
    )
    fig.text(0.5, 0.012, CRED, ha="center", fontsize=9, color=C["faint"])
    fig.tight_layout(rect=(0, 0.025, 1, 0.94))
    fig.savefig(IMG_DIR / "sankey_lula_flavio.png")
    plt.close(fig)


# ------------------------------------------------------- cenarios 2o turno


def draw_cenarios() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 7.2), dpi=DPI)
    nomes = [
        "Flávio Bolsonaro (PL)",
        "Ronaldo Caiado (PSD)",
        "Romeu Zema (Novo)",
        "Renan Santos (Missão)",
    ]
    curt = ["× FLÁVIO", "× CAIADO", "× ZEMA", "× RENAN"]
    adv_c = [C["flavio"], C["gold"], C["green"], C["violet"]]
    x = np.arange(4)
    w = 0.25

    lula_v = [SEGUNDO_TURNO[n]["lula"] for n in nomes]
    adv_v = [SEGUNDO_TURNO[n]["adversario"] for n in nomes]
    fora_v = [SEGUNDO_TURNO[n]["bn"] + SEGUNDO_TURNO[n]["ns"] for n in nomes]

    b1 = ax.bar(x - w, lula_v, w * 0.92, color=C["lula"], label="Lula (PT)")
    b2 = ax.bar(x, adv_v, w * 0.92, color=adv_c, label="Adversário")
    b3 = ax.bar(
        x + w, fora_v, w * 0.92, color=C["gray_soft"], label="Branco/nulo + não sabe"
    )

    for bars in (b1, b2, b3):
        for r in bars:
            ax.text(
                r.get_x() + r.get_width() / 2,
                r.get_height() + 0.7,
                f"{r.get_height():.0f}",
                ha="center",
                fontsize=15,
                fontweight="bold",
            )
    for i in range(4):
        gap = lula_v[i] - adv_v[i]
        ax.text(
            x[i],
            55.5,
            f"diferença: {gap} pp",
            ha="center",
            fontsize=12.5,
            fontweight="bold",
            color=C["flavio"] if i == 0 else C["muted"],
        )
        ax.text(x[i], 52.3, curt[i], ha="center", fontsize=12, color=C["faint"])

    ax.axhline(43, color=C["flavio"], lw=1.2, ls="--", alpha=0.65)
    ax.text(
        3.48,
        43.6,
        "teto anti-Lula: 43\nsó Flávio alcança",
        fontsize=10.5,
        color=C["flavio"],
        ha="right",
        fontweight="bold",
    )

    ax.set_ylim(0, 59)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [
            "Flávio Bolsonaro\n(PL)",
            "Ronaldo Caiado\n(PSD)",
            "Romeu Zema\n(Novo)",
            "Renan Santos\n(Missão)",
        ],
        fontsize=12,
    )
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_yticks([])
    fig.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 0.035),
        ncol=3,
        fontsize=11.5,
        frameon=False,
    )

    fig.suptitle(
        "Trocar Flávio por 'terceira via' só melhora a vida do Lula",
        fontsize=20,
        fontweight="bold",
        y=0.97,
    )
    ax.set_title(
        "Nos quatro cenários, Lula fica em 47–48. O que muda é o adversário: Flávio faz 43; "
        "Caiado, 40; Zema, 38; Renan, 37.\nA perda reaparece quase inteira em branco, nulo e indecisão.",
        fontsize=12,
        color=C["muted"],
        pad=12,
    )
    fig.text(0.5, 0.012, CRED, ha="center", fontsize=9, color=C["faint"])
    fig.tight_layout(rect=(0, 0.085, 1, 0.93))
    fig.savefig(IMG_DIR / "cenarios_2turno.png")
    plt.close(fig)


# ------------------------------------------------------- blocos 1o turno


def draw_blocos() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 6.8), dpi=DPI)
    ax.axis("off")
    ax.set_xlim(0, 54)
    ax.set_ylim(-0.9, 3.1)

    oposicao = [
        ("Flávio 33", 33, C["flavio"]),
        ("Caiado 5", 5, C["gold"]),
        ("Renan 4", 4, C["violet"]),
        ("Zema 3", 3, C["green"]),
        ("Cury 2", 2, "#8a6d3b"),
        ("Grassi 1", 1, "#4a7fa5"),
    ]
    esquerda = [("Lula 39", 39, C["lula"]), ("UP+PCO+PCB 3", 3, "#a4443c")]
    disponivel = [("Branco/nulo 6", 6, C["gray"]), ("Não sabe 4", 4, C["gray_soft"])]

    def barra(yc, partes, titulo, total_lbl):
        xacc = 0.0
        for lbl, v, cor in partes:
            ax.barh(yc, v, left=xacc, height=0.62, color=cor, ec=C["paper"], lw=1.5)
            txt_c = C["ink"] if cor == C["gray_soft"] else "white"
            if v >= 3:
                ax.text(
                    xacc + v / 2,
                    yc,
                    lbl,
                    ha="center",
                    va="center",
                    fontsize=11.5,
                    fontweight="bold",
                    color=txt_c,
                )
            elif v == 2:
                ax.text(
                    xacc + v / 2,
                    yc,
                    lbl.split()[0],
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color="white",
                    rotation=90,
                )
            xacc += v
        ax.text(xacc + 0.6, yc, total_lbl, va="center", fontsize=17, fontweight="bold")
        ax.text(
            0, yc + 0.46, titulo, fontsize=12.5, fontweight="bold", color=C["muted"]
        )

    barra(2.3, esquerda, "BLOCO LULA (Lula + candidaturas à esquerda)", "42")
    barra(
        1.2,
        oposicao,
        "BLOCO DE OPOSIÇÃO (Flávio + terceiras vias de direita/centro)",
        "48",
    )
    barra(0.1, disponivel, "AINDA EM JOGO", "10")

    ax.axvline(39, color=C["lula"], lw=1.3, ls="--", alpha=0.7)
    ax.text(39, 2.95, " Lula: 39", fontsize=11, color=C["lula"], fontweight="bold")

    fl_ext = FLOW[2:10, 1].sum()
    ax.text(
        0,
        -0.72,
        f"A oposição e o centro somados (48) passam o bloco de Lula (42). Pela matriz estimada, "
        f"cerca de {fl_ext:.0f} dos 16 pontos pulverizados chegam a Flávio no 2º turno.\n"
        "O voto útil antecipa a consolidação que os quatro cenários alternativos tornam observável.",
        fontsize=11.5,
        color=C["ink"],
    )

    fig.suptitle(
        "1º turno: a oposição somada é maior que o bloco de Lula",
        fontsize=20,
        fontweight="bold",
        y=0.97,
    )
    fig.text(0.5, 0.015, CRED, ha="center", fontsize=9, color=C["faint"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    fig.savefig(IMG_DIR / "blocos_1turno.png")
    plt.close(fig)


# ------------------------------------------------------- serie resiliencia


def draw_serie() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 7.0), dpi=DPI)
    x = np.arange(len(SERIE_LF["rotulos"]))
    ax.plot(
        x,
        SERIE_LF["lula"],
        "-o",
        color=C["lula"],
        lw=3,
        ms=8,
        mfc="white",
        mew=2.4,
        label="Lula (PT)",
    )
    ax.plot(
        x,
        SERIE_LF["flavio"],
        "-o",
        color=C["flavio"],
        lw=3,
        ms=8,
        mfc="white",
        mew=2.4,
        label="Flávio Bolsonaro (PL)",
    )
    for xi, (lv, fv) in enumerate(zip(SERIE_LF["lula"], SERIE_LF["flavio"])):
        # quem esta em cima leva o rotulo para cima; empate separa os dois
        if lv > fv:
            off_l, off_f = (0, 11), (0, -21)
        elif fv > lv:
            off_l, off_f = (0, -21), (0, 11)
        else:
            off_l, off_f = (-9, 11), (9, -21)
        ax.annotate(
            str(lv),
            (xi, lv),
            textcoords="offset points",
            xytext=off_l,
            ha="center",
            fontsize=12.5,
            fontweight="bold",
            color=C["lula"],
        )
        ax.annotate(
            str(fv),
            (xi, fv),
            textcoords="offset points",
            xytext=off_f,
            ha="center",
            fontsize=12.5,
            fontweight="bold",
            color=C["flavio"],
        )

    ax.axvspan(4.6, 9.3, color=C["flavio"], alpha=0.055)
    ax.text(
        7.0,
        33.4,
        "maio a agosto:\nFlávio cravado em 43",
        ha="center",
        fontsize=11.5,
        color=C["flavio"],
        fontweight="bold",
    )
    ax.annotate(
        "caso Banco Master\nvira munição (mai)",
        xy=(5.05, 45.4),
        xytext=(5.6, 52.2),
        fontsize=10.5,
        color=C["muted"],
        ha="center",
        arrowprops=dict(arrowstyle="->", color=C["faint"]),
    )
    ax.annotate(
        "Flávio chega a liderar:\n46 × 45 (abr)",
        xy=(3.95, 46.3),
        xytext=(2.9, 51.8),
        fontsize=10.5,
        color=C["muted"],
        ha="center",
        arrowprops=dict(arrowstyle="->", color=C["faint"]),
    )

    ax.set_xticks(x)
    ax.set_xticklabels(SERIE_LF["rotulos"], fontsize=10.5)
    ax.set_ylim(31, 56)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper right", fontsize=12, frameon=False)

    fig.suptitle(
        "Um ano de ataques e o piso de Flávio não cede",
        fontsize=20,
        fontweight="bold",
        y=0.97,
    )
    ax.set_title(
        "2º turno Lula × Flávio. De dez/25 (51 × 36) para 2026: Flávio ganhou 7 pts, liderou em abril e, "
        "de maio a agosto, segura 43 em quatro pesquisas seguidas, enquanto Lula oscila entre 47 e 48.",
        fontsize=12,
        color=C["muted"],
        pad=12,
    )
    fig.text(0.5, 0.015, CRED, ha="center", fontsize=9, color=C["faint"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    fig.savefig(IMG_DIR / "resiliencia_series.png")
    plt.close(fig)


# ------------------------------------------------------- rejeicao x teto


def draw_rejeicao() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 7.2), dpi=DPI)

    pontos = [
        ("Flávio (PL)", 46, 43, C["flavio"], (0, -36), "center"),
        ("Caiado (PSD)", 14, 40, C["gold"], (-26, 28), "right"),
        ("Zema (Novo)", 16, 38, C["green"], (26, 28), "left"),
        ("Renan (Missão)", 14, 37, C["violet"], (-26, -36), "right"),
    ]
    for nome, rej, voto, cor, off, ha in pontos:
        ax.scatter(rej, voto, s=980, color=cor, zorder=3, alpha=0.92)
        ax.annotate(
            f"{voto}",
            (rej, voto),
            ha="center",
            va="center",
            fontsize=13,
            fontweight="bold",
            color="white",
            zorder=4,
        )
        ax.annotate(
            nome,
            (rej, voto),
            textcoords="offset points",
            xytext=off,
            ha=ha,
            fontsize=12.5,
            fontweight="bold",
            color=cor,
        )

    ax.scatter(45, 47.3, s=980, color=C["lula"], zorder=3, alpha=0.92)
    ax.annotate(
        "47–48",
        (45, 47.3),
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color="white",
        zorder=4,
    )
    ax.annotate(
        "Lula (PT) · vs. qualquer um",
        (45, 47.3),
        textcoords="offset points",
        xytext=(-30, 30),
        ha="right",
        fontsize=12.5,
        fontweight="bold",
        color=C["lula"],
    )

    # 1o turno das terceiras vias, para contraste
    ax.annotate(
        "rejeição três vezes menor,\nmas 3 a 6 pontos a menos no 2º turno",
        xy=(14.5, 39),
        xytext=(22, 30.5),
        fontsize=12,
        color=C["ink"],
        arrowprops=dict(arrowstyle="->", color=C["faint"]),
    )

    ax.set_xlabel("Rejeição: 'não votaria de jeito nenhum' (%)", fontsize=12.5)
    ax.set_ylabel("Voto no 2º turno contra Lula (%)", fontsize=12.5)
    ax.set_xlim(4, 56)
    ax.set_ylim(0, 55)
    ax.grid(alpha=0.25, lw=0.7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    fig.suptitle(
        "Rejeição baixa não compra voto", fontsize=20, fontweight="bold", y=0.97
    )
    ax.set_title(
        "A tese da terceira via é 'menos rejeição = mais eleição'. Os números dizem o contrário: Caiado, Zema e Renan\n"
        "têm cerca de um terço da rejeição de Flávio e rendem menos contra Lula. O voto anti-Lula já tem polo.",
        fontsize=12,
        color=C["muted"],
        pad=12,
    )
    fig.text(0.5, 0.015, CRED, ha="center", fontsize=9, color=C["faint"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    fig.savefig(IMG_DIR / "rejeicao_teto.png")
    plt.close(fig)


# ---------------------------------------------------------------- saidas

draw_sankey()
draw_cenarios()
draw_blocos()
draw_serie()
draw_rejeicao()

flow_table = {
    s: {t: round(float(FLOW[i, j]), 2) for j, t in enumerate(TARGETS)}
    for i, s in enumerate(SOURCES)
}
# Consolidacao fora das bases: quanto cada um ganha do 1o para o 2o turno
# descontando o proprio eleitorado de origem. Derivado da matriz, nao fixado.
base_lula = float(FLOW[SOURCES.index("Lula (PT)"), TARGETS.index("Lula")])
base_flavio = float(
    FLOW[SOURCES.index("Flávio Bolsonaro (PL)"), TARGETS.index("Flávio")]
)
ganho_lula = round(SEGUNDO_TURNO["Flávio Bolsonaro (PL)"]["lula"] - base_lula, 2)
ganho_flavio = round(
    SEGUNDO_TURNO["Flávio Bolsonaro (PL)"]["adversario"] - base_flavio, 2
)
consolidacao = {
    "flavio_ganho": ganho_flavio,
    "lula_ganho": ganho_lula,
    "razao": round(ganho_flavio / ganho_lula, 2),
    "julho": {"flavio_ganho": 10.1, "lula_ganho": 6.84, "razao": 1.48},
}

dados = {
    "fonte": "Datafolha, campo 18-19/08/2026, divulgacao 21/08/2026, BR-04496/2026.",
    "primeiro_turno_ago": PRIMEIRO_TURNO,
    "primeiro_turno_jul": PRIMEIRO_TURNO_JUL,
    "segundo_turno_ago": SEGUNDO_TURNO,
    "rejeicao": REJEICAO,
    "avaliacao_governo": {"ruim_pessimo": 41, "otimo_bom": 33, "regular": 25, "ns": 1},
    "aprovacao_governo": {"aprova": 47, "desaprova": 50, "ns": 3},
    "serie_lula_flavio_2t": SERIE_LF,
    "metodo_fluxo": "prior de afinidade + IPF (RAS) ate margens publicadas; "
    "origens escaladas 100->101 para fechar com o 2T; leitura agregada, nao painel",
    "fluxo_1t_2t_lula_x_flavio": flow_table,
    "consolidacao": consolidacao,
}
(OUT_DIR / "dados.json").write_text(
    json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Espelho compacto para o dossie: o Sankey da pagina e desenhado em SVG a
# partir daqui. Script classico porque o dossie tambem abre em file://.
fluxo_site = {
    "fonte": dados["fonte"],
    "metodo": dados["metodo_fluxo"],
    "primeiro_turno": PRIMEIRO_TURNO,
    "segundo_turno": {
        "lula": SEGUNDO_TURNO["Flávio Bolsonaro (PL)"]["lula"],
        "flavio": SEGUNDO_TURNO["Flávio Bolsonaro (PL)"]["adversario"],
        "branco_nulo": SEGUNDO_TURNO["Flávio Bolsonaro (PL)"]["bn"],
        "nao_sabe": SEGUNDO_TURNO["Flávio Bolsonaro (PL)"]["ns"],
    },
    "fluxo": flow_table,
    "consolidacao": consolidacao,
}
SITE_DIR = ROOT / "docs" / "assets"
(SITE_DIR / "datafolha_082026_fluxo.json").write_text(
    json.dumps(fluxo_site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(SITE_DIR / "datafolha_082026_fluxo.js").write_text(
    "window.__DATAFOLHA_FLUXO__ = "
    + json.dumps(fluxo_site, ensure_ascii=False, separators=(",", ":"))
    + ";\n",
    encoding="utf-8",
)

print("PNGs em", IMG_DIR)
print("dados.json em", OUT_DIR)
print("\nMatriz de fluxo (pontos do 2T):")
print(f"{'origem':<26}" + "".join(f"{t:>13}" for t in TARGETS))
for s in SOURCES:
    print(f"{s:<26}" + "".join(f"{flow_table[s][t]:>13.2f}" for t in TARGETS))
ext_f = float(FLOW[2:, 1].sum())
ext_l = float(FLOW[2:, 0].sum())
print(
    f"\nFora das bases: Flavio +{ext_f:.1f} x Lula +{ext_l:.1f} (razao {ext_f/ext_l:.2f}:1)"
)
