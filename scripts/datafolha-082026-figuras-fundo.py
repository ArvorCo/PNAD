#!/usr/bin/env python3
"""Figuras da segunda camada de auditoria do Datafolha BR-04496/2026.

Le analysis/datafolha_082026/aprofundamento.json e desenha o que o relatorio
mediu e nao mostrou. Nenhuma figura anterior e sobrescrita.

Uso:
  python3 scripts/datafolha-082026-cruzamentos.py
  python3 scripts/datafolha-082026-aprofundamento.py
  python3 scripts/datafolha-082026-figuras-fundo.py

Saida:
  docs/img/datafolha_082026/fundo_*.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "datafolha_082026" / "aprofundamento.json"
IMG = ROOT / "docs" / "img" / "datafolha_082026"
IMG.mkdir(parents=True, exist_ok=True)

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
    }
)

DPI = 200
CRED = "Análise Arvor · brasil.arvor.co · Datafolha 18–19/08/2026 · BR-04496/2026"
SHORT = {
    "Lula (PT)": "Lula",
    "Flavio Bolsonaro (PL)": "Flávio",
    "Ronaldo Caiado (PSD)": "Caiado",
    "Renan Santos (MISSAO)": "Renan Santos",
    "Zema (NOVO)": "Zema",
    "Pablo Marcal (PRTB)": "Marçal",
    "Augusto Cury (AVANTE)": "Cury",
}
ACCENT = {
    "Nao alinhados": "Não alinhados",
    "Sem partido": "Sem partido",
    "Regiao metropolitana": "Região metrop.",
    "Centro-Oeste/Norte": "C.-Oeste/Norte",
    "Medio": "Médio",
    "Nao PEA": "Fora da PEA",
    "Catolica": "Católica",
    "Evangelica": "Evangélica",
    "Genero": "Gênero",
    "Religiao": "Religião",
    "Cor": "Cor",
    "Regiao": "Região",
    "Ocupacao": "Ocupação",
    "Identificacao politica": "Identificação política",
    "Natureza do municipio": "Natureza do município",
    "Ate 2 SM": "Até 2 SM",
    "Mais de 5 SM": "Mais de 5 SM",
    "Partido de preferencia": "Partido de preferência",
    "Escolaridade": "Escolaridade",
}


def label(text: str) -> str:
    return ACCENT.get(text, SHORT.get(text, text))


def frame(ax: plt.Axes) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(C["line"])
    ax.spines["bottom"].set_color(C["line"])
    ax.grid(axis="x", color=C["line"], linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)


def note(fig: plt.Figure, text: str, bottom: float = 0.22, y: float = 0.045) -> None:
    """Nota de rodape sem colisao com titulo ou eixo."""
    fig.subplots_adjust(bottom=bottom)
    fig.text(0.012, y, text, fontsize=9.6, color=C["muted"], va="bottom")


def finish(fig: plt.Figure, name: str) -> None:
    fig.text(0.012, 0.012, CRED, fontsize=7.4, color=C["faint"])
    fig.savefig(IMG / name, dpi=DPI, bbox_inches="tight", pad_inches=0.26)
    plt.close(fig)
    print("  ", name)


# --------------------------------------------------------------------------


def mercado_aberto(data: dict) -> None:
    market = data["mercado_aberto"]
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(11.4, 7.6), gridspec_kw={"height_ratios": [1, 1.5]}
    )

    fixed = market["voto_cristalizado_pct"]
    movable = market["pontos_moveis_no_total"]
    undecided = market["indecisos_pct"]
    gap = market["gap_publicado_1turno"]

    ax1.barh([0], [fixed], color=C["gray_soft"], height=0.52, label="voto cristalizado")
    ax1.barh(
        [0],
        [movable],
        left=fixed,
        color=C["gold"],
        height=0.52,
        label="declara que pode mudar",
    )
    ax1.barh(
        [0],
        [undecided],
        left=fixed + movable,
        color=C["violet"],
        height=0.52,
        label="indeciso",
    )
    ax1.barh([-0.75], [gap], color=C["ink"], height=0.3)

    ax1.text(
        fixed / 2,
        0,
        f"{fixed:.0f}%",
        ha="center",
        va="center",
        color=C["ink"],
        fontsize=13,
        fontweight="bold",
    )
    ax1.text(
        fixed + movable / 2,
        0,
        f"{movable:.0f}%",
        ha="center",
        va="center",
        color="white",
        fontsize=13,
        fontweight="bold",
    )
    ax1.text(
        fixed + movable + undecided / 2,
        0,
        f"{undecided:.0f}%",
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
    )
    ax1.text(
        gap + 1.4,
        -0.75,
        f"diferença publicada no 1º turno: {gap} pontos",
        va="center",
        fontsize=10.5,
        color=C["ink"],
        fontweight="bold",
    )

    ax1.set_yticks([0, -0.75])
    ax1.set_yticklabels(["o eleitorado", "a manchete"], fontsize=11)
    ax1.set_xlim(0, 104)
    ax1.set_ylim(-1.3, 0.6)
    ax1.set_xticks([])
    for side in ("top", "right", "left", "bottom"):
        ax1.spines[side].set_visible(False)
    ax1.legend(
        handles=[
            Patch(color=C["gray_soft"], label="voto cristalizado"),
            Patch(color=C["gold"], label="declara que o voto ainda pode mudar"),
            Patch(color=C["violet"], label="indeciso"),
        ],
        loc="lower right",
        frameon=False,
        fontsize=9.4,
        ncol=3,
        bbox_to_anchor=(1.0, -0.30),
    )
    ax1.set_title(
        "O mercado aberto é cinco vezes maior do que a diferença",
        fontsize=16.5,
        fontweight="bold",
        loc="left",
        pad=14,
    )

    rows = market["detalhe_por_candidato"]
    names = [label(row["candidato"]) for row in rows]
    change = [row["pode_mudar_pct"] for row in rows]
    points = [row["pontos_do_eleitorado"] for row in rows]
    y = np.arange(len(rows))[::-1]

    ax2.barh(y, change, color=C["gold"], height=0.46, zorder=3)
    for index, (value, point, row) in enumerate(zip(change, points, rows)):
        ax2.text(
            value - 1.5,
            y[index],
            f"{value}%",
            va="center",
            ha="right",
            fontsize=11.5,
            color="white",
            fontweight="bold",
        )
        ax2.text(
            value + 2.0,
            y[index],
            f"{point:.1f} pontos do eleitorado nacional  ·  {row['entrevistas']} entrevistas",
            va="center",
            fontsize=9.8,
            color=C["muted"],
        )
    ax2.set_yticks(y)
    ax2.set_yticklabels(names, fontsize=11.5)
    ax2.set_xlim(0, 108)
    ax2.set_xlabel(
        "declara que o voto ainda pode mudar, em % dos eleitores do candidato",
        fontsize=10,
    )
    frame(ax2)
    ax2.set_title(
        "Página 12 do relatório: quem ainda pode mudar de ideia",
        fontsize=13.5,
        fontweight="bold",
        loc="left",
        pad=10,
    )
    fig.tight_layout()
    finish(fig, "fundo_mercado_aberto.png")


def campo_versus_peso(data: dict) -> None:
    weight = data["campo_versus_peso"]
    rows = weight["linhas"]
    fig, ax = plt.subplots(figsize=(11.4, 6.0))

    y = np.arange(len(rows))[::-1]
    for index, row in enumerate(rows):
        raw = row["campo_pct"]
        weighted = row["ponderado_pct"]
        color = C["flavio"] if weighted > raw else C["lula"]
        ax.plot(
            [raw, weighted],
            [y[index], y[index]],
            color=color,
            linewidth=3.2,
            zorder=3,
            alpha=0.55,
        )
        ax.scatter(
            [raw],
            [y[index]],
            s=150,
            color=C["gray"],
            zorder=4,
            edgecolor=C["paper"],
            linewidth=1.6,
        )
        ax.scatter(
            [weighted],
            [y[index]],
            s=190,
            color=color,
            zorder=5,
            edgecolor=C["paper"],
            linewidth=1.6,
        )
        ax.text(
            raw,
            y[index] + 0.28,
            f"{raw:.1f} em campo",
            ha="center",
            fontsize=9.2,
            color=C["muted"],
        )
        ax.text(
            weighted,
            y[index] - 0.36,
            f"{weighted} publicado",
            ha="center",
            fontsize=9.8,
            color=color,
            fontweight="bold",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(
        [
            f"{label(row['candidato'])}\n{row['entrevistas']} entrevistas"
            for row in rows
        ],
        fontsize=10.5,
    )
    ax.set_xlim(0, 48)
    ax.set_ylim(-0.85, len(rows) - 0.35)
    ax.set_xlabel("intenção de voto no 1º turno, em %", fontsize=10)
    frame(ax)
    ax.set_title(
        "A diferença de campo é 12,1 pontos. A publicada é 6.",
        fontsize=17,
        fontweight="bold",
        loc="left",
        pad=16,
    )
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.28)
    fig.text(
        0.012,
        0.055,
        "Cinza: entrevistas realmente colhidas, declaradas na linha de bases da página 12 do relatório. "
        "Cor: percentual ponderado publicado.\n"
        "A ponderação está declarada no registro do TSE e é legítima. O que não está declarado é que a linha de bases "
        "da divulgação conta entrevistas,\ne a do anexo conta base ponderada. A mesma pergunta aparece com 1.836 numa "
        "página e 1.850 na outra.",
        fontsize=9.6,
        color=C["muted"],
        va="bottom",
    )
    finish(fig, "fundo_campo_versus_peso.png")


def piso_de_ruido(data: dict) -> None:
    floor = data["piso_de_ruido"]
    total = next(row for row in floor["por_recorte"] if row["recorte"] == "Total")
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(13.2, 6.6), gridspec_kw={"width_ratios": [1.05, 1]}
    )

    names = [
        "Flavio Bolsonaro (PL)",
        "Lula (PT)",
        "Pablo Marcal (PRTB)",
        "Zema (NOVO)",
        "Renan Santos (MISSAO)",
        "Ronaldo Caiado (PSD)",
        "Augusto Cury (AVANTE)",
    ]
    net = [total[name] for name in names]
    gross = [value + total["piso_pct"] for value in net]
    y = np.arange(len(names))[::-1]

    ax1.barh(
        y, gross, color=C["gray_soft"], height=0.6, zorder=2, label="rejeição publicada"
    )
    ax1.barh(
        y, net, color=C["lula"], height=0.6, zorder=3, label="acima do piso de ruído"
    )
    ax1.axvline(
        total["piso_pct"], color=C["ink"], linestyle="--", linewidth=1.4, zorder=4
    )
    ax1.text(
        total["piso_pct"] + 0.6,
        y[0] + 0.55,
        f"piso de ruído {total['piso_pct']:.1f}%",
        fontsize=9.8,
        color=C["ink"],
        fontweight="bold",
    )
    for index, (g, n) in enumerate(zip(gross, net)):
        ax1.text(
            g + 0.8, y[index], f"{g:.0f}", va="center", fontsize=10, color=C["muted"]
        )
        if n > 3:
            ax1.text(
                n - 1.2,
                y[index],
                f"{n:.0f}",
                va="center",
                ha="right",
                fontsize=10,
                color="white",
                fontweight="bold",
            )
    ax1.set_yticks(y)
    ax1.set_yticklabels([label(name) for name in names], fontsize=11)
    ax1.set_xlim(0, 52)
    ax1.set_xlabel("rejeição, em %", fontsize=10)
    frame(ax1)
    ax1.legend(
        handles=[
            Patch(color=C["gray_soft"], label="rejeição publicada"),
            Patch(color=C["lula"], label="acima do piso de ruído"),
        ],
        loc="lower right",
        frameon=False,
        fontsize=9.4,
    )
    ax1.set_title(
        "Quanto da rejeição é opinião",
        fontsize=15,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    segments = [row for row in floor["por_recorte"] if row["recorte"] != "Total"]
    segments = sorted(segments, key=lambda row: row["piso_pct"])
    chosen = segments[:4] + segments[-4:]
    values = [row["piso_pct"] for row in chosen]
    y2 = np.arange(len(chosen))[::-1]
    colors = [C["green"]] * 4 + [C["gold"]] * 4
    ax2.barh(y2, values, color=colors, height=0.6, zorder=3)
    for index, value in enumerate(values):
        ax2.text(
            value + 0.25,
            y2[index],
            f"{value:.1f}%",
            va="center",
            fontsize=10,
            color=C["muted"],
        )
    ax2.set_yticks(y2)
    ax2.set_yticklabels([label(row["recorte"]) for row in chosen], fontsize=10.5)
    ax2.set_xlim(0, 17)
    ax2.set_xlabel("piso de ruído do recorte, em %", fontsize=10)
    frame(ax2)
    ax2.set_title(
        "O piso varia 2,4 vezes entre recortes",
        fontsize=15,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    fig.suptitle(
        "Seis nomes que ninguém sabe citar recebem 9,7% de rejeição média",
        fontsize=17.5,
        fontweight="bold",
        x=0.012,
        ha="left",
        y=1.02,
    )
    fig.tight_layout()
    note(
        fig,
        "Piso de ruído: rejeição média das seis candidaturas com 1% ou menos de voto na estimulada. "
        "Nomes que quase ninguém sabe citar recebem\nde 8% a 13% de recusa, porque a pergunta é múltipla, "
        "com cartão e com insistência. Comparar rejeição entre recortes sem descontar\no piso mistura opinião "
        "com estilo de resposta: entre eleitores de ensino fundamental o piso é 13,7%; entre os de 16 a 24 anos, 5,7%.",
        bottom=0.24,
        y=0.04,
    )
    finish(fig, "fundo_piso_de_ruido.png")


def vao(data: dict) -> None:
    rows = [
        row
        for row in data["vao"]["por_recorte"]
        if row["recorte"] not in {"PL", "PT", "Bolsonaristas", "Petistas", "Total"}
    ]
    rows = sorted(rows, key=lambda row: row["vao_pp"])[-14:]
    fig, ax = plt.subplots(figsize=(11.6, 8.2))
    y = np.arange(len(rows))

    for index, row in enumerate(rows):
        ax.plot(
            [row["voto_oposicao_2turno_pct"], row["desaprova_pct"]],
            [y[index], y[index]],
            color=C["gold"],
            linewidth=4.4,
            alpha=0.5,
            zorder=3,
            solid_capstyle="round",
        )
        ax.scatter(
            [row["voto_oposicao_2turno_pct"]],
            [y[index]],
            s=140,
            color=C["flavio"],
            zorder=5,
            edgecolor=C["paper"],
            linewidth=1.5,
        )
        ax.scatter(
            [row["desaprova_pct"]],
            [y[index]],
            s=140,
            color=C["ink"],
            zorder=5,
            edgecolor=C["paper"],
            linewidth=1.5,
        )
        middle = (row["voto_oposicao_2turno_pct"] + row["desaprova_pct"]) / 2
        ax.text(
            middle,
            y[index] + 0.3,
            f"{row['vao_pp']:.0f}",
            ha="center",
            fontsize=10.5,
            color=C["gold"],
            fontweight="bold",
        )
        ax.text(
            row["desaprova_pct"] + 1.2,
            y[index],
            f"não escolhe ninguém: {row['nao_escolha_pct']}%",
            va="center",
            fontsize=9,
            color=C["faint"],
        )

    ax.set_yticks(y)
    ax.set_yticklabels(
        [f"{label(row['recorte'])}  ·  {row['base']}" for row in rows], fontsize=10.6
    )
    ax.set_xlim(20, 88)
    ax.set_xlabel("em % do recorte", fontsize=10)
    frame(ax)
    ax.scatter([], [], s=110, color=C["ink"], label="desaprova o governo")
    ax.scatter([], [], s=110, color=C["flavio"], label="vota na oposição no 2º turno")
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    ax.set_title(
        "O vão: quem já rejeita o governo e ainda não vota na oposição",
        fontsize=17.5,
        fontweight="bold",
        loc="left",
        pad=16,
    )
    fig.tight_layout()
    note(
        fig,
        "Teto endereçável, não previsão: desaprovar um governo não é o mesmo que estar disponível para o adversário. "
        "O número ao lado de cada recorte\né a base ponderada. Nas seis partições fechadas do relatório o vão nacional "
        "fica entre 6,4 e 7,1 pontos.",
        bottom=0.16,
        y=0.035,
    )
    finish(fig, "fundo_vao.png")


def substituicao(data: dict) -> None:
    sub = data["substituicao"]
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(13.2, 6.4), gridspec_kw={"width_ratios": [1.15, 1]}
    )

    pretty_names = {
        "Flavio Bolsonaro": "Flávio Bolsonaro",
        "Ronaldo Caiado": "Ronaldo Caiado",
        "Zema": "Zema",
        "Renan Santos": "Renan Santos",
    }
    names = [pretty_names[row["adversario"]] for row in sub["cenarios"]]
    x = np.arange(len(names))
    lula = [row["lula_pct"] for row in sub["cenarios"]]
    opposition = [row["oposicao_pct"] for row in sub["cenarios"]]
    blank = [row["branco_nulo_pct"] + row["indecisos_pct"] for row in sub["cenarios"]]

    ax1.plot(
        x,
        lula,
        marker="o",
        markersize=11,
        linewidth=3,
        color=C["lula"],
        zorder=4,
        label="Lula",
    )
    ax1.plot(
        x,
        opposition,
        marker="o",
        markersize=11,
        linewidth=3,
        color=C["flavio"],
        zorder=4,
        label="o adversário do dia",
    )
    ax1.plot(
        x,
        blank,
        marker="o",
        markersize=11,
        linewidth=3,
        color=C["gray"],
        zorder=4,
        label="não escolhe ninguém",
    )
    for index in range(len(names)):
        ax1.text(
            x[index],
            lula[index] + 2.0,
            str(lula[index]),
            ha="center",
            fontsize=11,
            color=C["lula"],
            fontweight="bold",
        )
        ax1.text(
            x[index],
            opposition[index] - 3.4,
            str(opposition[index]),
            ha="center",
            fontsize=11,
            color=C["flavio"],
            fontweight="bold",
        )
        ax1.text(
            x[index],
            blank[index] + 2.0,
            str(blank[index]),
            ha="center",
            fontsize=10,
            color=C["muted"],
            fontweight="bold",
        )
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, fontsize=11)
    ax1.set_ylim(0, 58)
    ax1.set_ylabel("em % do total da amostra", fontsize=10)
    ax1.grid(axis="y", color=C["line"], linewidth=0.7)
    ax1.set_axisbelow(True)
    for side in ("top", "right"):
        ax1.spines[side].set_visible(False)
    ax1.legend(frameon=False, fontsize=10, loc="upper right")
    ax1.set_title(
        "Trocar o adversário move o adversário, não o presidente",
        fontsize=14.5,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    segments = [
        "Nao alinhados",
        "Superior",
        "Sem partido",
        "Mais de 5 SM",
        "Bolsonaristas",
        "Evangelica",
    ]
    per = sub["por_recorte"]
    y = np.arange(len(segments))[::-1]
    width = 0.19
    palette = {
        "Flavio Bolsonaro": C["flavio"],
        "Ronaldo Caiado": C["gold"],
        "Zema": C["green"],
        "Renan Santos": C["violet"],
    }
    pretty = {
        "Flavio Bolsonaro": "Flávio",
        "Ronaldo Caiado": "Caiado",
        "Zema": "Zema",
        "Renan Santos": "Renan Santos",
    }
    for offset, candidate in enumerate(
        ["Flavio Bolsonaro", "Ronaldo Caiado", "Zema", "Renan Santos"]
    ):
        values = [per[segment][candidate] for segment in segments]
        ax2.barh(
            y + (1.5 - offset) * width,
            values,
            height=width,
            color=palette[candidate],
            label=pretty[candidate],
            zorder=3,
        )
    ax2.set_yticks(y)
    ax2.set_yticklabels([label(segment) for segment in segments], fontsize=10.5)
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("voto no 2º turno contra Lula, em % do recorte", fontsize=10)
    frame(ax2)
    ax2.legend(
        frameon=False,
        fontsize=9.4,
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, -0.11),
    )
    ax2.set_title(
        "Onde o substituto bate o preferido",
        fontsize=14.5,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    fig.suptitle(
        "Quatro segundos turnos, a mesma amostra, o mesmo dia",
        fontsize=17.5,
        fontweight="bold",
        x=0.012,
        ha="left",
        y=1.02,
    )
    fig.tight_layout()
    note(
        fig,
        "Lula varia um ponto entre os quatro cenários. A variação inteira fica no desafiante, que cai de 43 para 37, "
        "e na não escolha, que sobe de 11 para 16.\nÉ a medida mais direta de voto útil que existe em pesquisa "
        "brasileira publicada, e ela corta nos dois sentidos.",
        bottom=0.26,
        y=0.035,
    )
    finish(fig, "fundo_substituicao.png")


def serie_congelada(data: dict) -> None:
    series = data["series"]
    first = series["primeiro_turno"]
    runoff = series["segundo_turno"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.6, 8.4), sharex=False)

    waves = first["waves"]
    x = np.arange(len(waves))
    ax1.plot(
        x,
        first["series"]["Lula (PT)"],
        marker="o",
        linewidth=3,
        markersize=9,
        color=C["lula"],
        label="Lula",
    )
    ax1.plot(
        x,
        first["series"]["Flavio Bolsonaro (PL)"],
        marker="o",
        linewidth=3,
        markersize=9,
        color=C["flavio"],
        label="Flávio",
    )
    ax1.plot(
        x,
        first["series"]["Branco/nulo/nenhum"],
        marker="s",
        linewidth=2.2,
        markersize=7,
        color=C["gray"],
        label="branco/nulo",
    )
    for index in range(len(waves)):
        ax1.text(
            x[index],
            first["series"]["Lula (PT)"][index] + 1.4,
            str(first["series"]["Lula (PT)"][index]),
            ha="center",
            fontsize=9.6,
            color=C["lula"],
            fontweight="bold",
        )
        ax1.text(
            x[index],
            first["series"]["Flavio Bolsonaro (PL)"][index] - 2.6,
            str(first["series"]["Flavio Bolsonaro (PL)"][index]),
            ha="center",
            fontsize=9.6,
            color=C["flavio"],
            fontweight="bold",
        )
    ax1.axhspan(32.4, 33.6, color=C["flavio"], alpha=0.08, zorder=0)
    ax1.set_xticks(x)
    ax1.set_xticklabels(waves, fontsize=8.8)
    ax1.set_ylim(0, 48)
    ax1.set_ylabel("1º turno, em %", fontsize=10)
    ax1.grid(axis="y", color=C["line"], linewidth=0.7)
    ax1.set_axisbelow(True)
    for side in ("top", "right"):
        ax1.spines[side].set_visible(False)
    ax1.legend(frameon=False, fontsize=10, ncol=3, loc="lower left")
    ax1.set_title(
        "Março: 33. Agosto: 33. O desafiante voltou ao ponto de partida.",
        fontsize=14.5,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    waves2 = runoff["waves"]
    x2 = np.arange(len(waves2))
    ax2.plot(
        x2,
        runoff["series"]["Lula (PT)"],
        marker="o",
        linewidth=3,
        markersize=9,
        color=C["lula"],
        label="Lula",
    )
    ax2.plot(
        x2,
        runoff["series"]["Flavio Bolsonaro (PL)"],
        marker="o",
        linewidth=3,
        markersize=9,
        color=C["flavio"],
        label="Flávio",
    )
    for index in range(len(waves2)):
        ax2.text(
            x2[index],
            runoff["series"]["Lula (PT)"][index] + 1.5,
            str(runoff["series"]["Lula (PT)"][index]),
            ha="center",
            fontsize=9.6,
            color=C["lula"],
            fontweight="bold",
        )
        ax2.text(
            x2[index],
            runoff["series"]["Flavio Bolsonaro (PL)"][index] - 3.0,
            str(runoff["series"]["Flavio Bolsonaro (PL)"][index]),
            ha="center",
            fontsize=9.6,
            color=C["flavio"],
            fontweight="bold",
        )
    ax2.axvspan(5.6, 9.4, color=C["gold"], alpha=0.10, zorder=0)
    ax2.text(
        7.5,
        20,
        "quatro ondas em 43",
        ha="center",
        fontsize=11,
        color=C["gold"],
        fontweight="bold",
    )
    ax2.set_xticks(x2)
    ax2.set_xticklabels(waves2, fontsize=8.4)
    ax2.set_ylim(0, 58)
    ax2.set_ylabel("2º turno, em %", fontsize=10)
    ax2.grid(axis="y", color=C["line"], linewidth=0.7)
    ax2.set_axisbelow(True)
    for side in ("top", "right"):
        ax2.spines[side].set_visible(False)
    ax2.legend(frameon=False, fontsize=10, ncol=2, loc="lower left")
    ax2.set_title(
        "E o segundo turno não se mexe há três meses",
        fontsize=14.5,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    fig.tight_layout()
    note(
        fig,
        "A diferença do primeiro turno caiu de dez para seis pontos entre junho e agosto, e a queda é de Lula: o "
        "desafiante marcava 33 em março e marca 33 agora.\nNo segundo turno ele repete 43 em quatro ondas seguidas. "
        "A convergência do primeiro turno é voto útil que o segundo turno já contava.",
        bottom=0.13,
        y=0.028,
    )
    finish(fig, "fundo_serie_congelada.png")


def consolidacao(data: dict) -> None:
    rows = data["consolidacao_de_base"]["linhas"]
    pretty = {"Flavio Bolsonaro": "Flávio Bolsonaro"}
    fig, ax = plt.subplots(figsize=(11.4, 6.2))
    y = np.arange(len(rows))[::-1]

    for index, row in enumerate(rows):
        ax.plot(
            [row["entre_nao_alinhados_pct"], row["na_base_bolsonarista_pct"]],
            [y[index], y[index]],
            color=C["gray_soft"],
            linewidth=5.5,
            zorder=2,
            solid_capstyle="round",
        )
        ax.scatter(
            [row["entre_nao_alinhados_pct"]],
            [y[index]],
            s=190,
            color=C["gold"],
            zorder=4,
            edgecolor=C["paper"],
            linewidth=1.6,
        )
        ax.scatter(
            [row["na_base_bolsonarista_pct"]],
            [y[index]],
            s=190,
            color=C["flavio"],
            zorder=4,
            edgecolor=C["paper"],
            linewidth=1.6,
        )
        ax.text(
            row["entre_nao_alinhados_pct"] - 1.6,
            y[index],
            str(row["entre_nao_alinhados_pct"]),
            ha="right",
            va="center",
            fontsize=11,
            color=C["gold"],
            fontweight="bold",
        )
        ax.text(
            row["na_base_bolsonarista_pct"] + 1.6,
            y[index],
            str(row["na_base_bolsonarista_pct"]),
            va="center",
            fontsize=11,
            color=C["flavio"],
            fontweight="bold",
        )
        middle = (row["entre_nao_alinhados_pct"] + row["na_base_bolsonarista_pct"]) / 2
        ax.text(
            middle,
            y[index] + 0.26,
            f"abismo de {row['abismo_pp']} pontos",
            ha="center",
            fontsize=9.6,
            color=C["muted"],
        )

    ax.set_yticks(y)
    ax.set_yticklabels(
        [
            f"{pretty.get(row['candidato'], row['candidato'])}\nnacional {row['nacional_reconstruido_pct']:.1f}%"
            for row in rows
        ],
        fontsize=10.6,
    )
    ax.set_xlim(28, 100)
    ax.set_ylim(-0.7, len(rows) - 0.25)
    ax.set_xlabel("voto no 2º turno contra Lula, em % do recorte", fontsize=10)
    frame(ax)
    ax.legend(
        handles=[
            Patch(color=C["flavio"], label="entre bolsonaristas (34% do eleitorado)"),
            Patch(color=C["gold"], label="entre não alinhados (24% do eleitorado)"),
        ],
        frameon=False,
        fontsize=10,
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.5, -0.13),
    )
    ax.set_title(
        "A base já está toda dentro. O crescimento restante está fora dela.",
        fontsize=17,
        fontweight="bold",
        loc="left",
        pad=18,
    )
    fig.tight_layout()
    note(
        fig,
        "O percentual nacional ao lado de cada nome é reconstruído a partir dos três blocos de identificação política "
        "e reproduz o publicado.\nFlávio é o adversário mais forte no agregado, por 3,4 pontos sobre Caiado, e é o que "
        "menos alcança quem não se declara nem bolsonarista nem petista.",
        bottom=0.30,
        y=0.04,
    )
    finish(fig, "fundo_consolidacao.png")


def cobertura(data: dict) -> None:
    rows = sorted(data["cobertura_dos_recortes"], key=lambda row: row["cobertura_pct"])
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    y = np.arange(len(rows))[::-1]
    colors = [C["lula"] if not row["particao_fechada"] else C["green"] for row in rows]
    ax.barh(
        y, [row["cobertura_pct"] for row in rows], color=colors, height=0.58, zorder=3
    )
    for index, row in enumerate(rows):
        ax.text(
            row["cobertura_pct"] + 0.7,
            y[index],
            f"{row['cobertura_pct']:.1f}%"
            + (
                f"  ·  {row['eleitores_sem_coluna']} eleitores sem coluna"
                if row["eleitores_sem_coluna"] > 2
                else ""
            ),
            va="center",
            fontsize=10,
            color=C["muted"],
        )
    ax.set_yticks(y)
    ax.set_yticklabels([label(row["dimensao"]) for row in rows], fontsize=11)
    ax.set_xlim(0, 118)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel(
        "parcela da amostra que aparece em alguma coluna do recorte, em %", fontsize=10
    )
    frame(ax)
    ax.set_title(
        "Um em cada quatro entrevistados não tem coluna de religião",
        fontsize=17,
        fontweight="bold",
        loc="left",
        pad=16,
    )
    fig.tight_layout()
    note(
        fig,
        "Sem religião (11%), espírita, umbanda e outras respostas somam 491 entrevistados que nunca aparecem cruzados. "
        "Amarela e indígena somam 72.\nO relatório publica uma coluna para o Sul, que pesa 15% da amostra, e nenhuma "
        "para quem não tem religião, que pesa 11%.\nVerde: partição fechada, todo entrevistado tem coluna. "
        "Vermelho: parte da amostra fica fora de qualquer coluna do recorte.",
        bottom=0.26,
        y=0.04,
    )
    finish(fig, "fundo_cobertura.png")


def motivacao(data: dict) -> None:
    deck = data["paginas_da_divulgacao"]["motivacao"]
    decision = data["paginas_da_divulgacao"]["decisao"]
    fig, ax = plt.subplots(figsize=(11.4, 6.4))

    order = [
        "Renan Santos (MISSAO)",
        "Lula (PT)",
        "Ronaldo Caiado (PSD)",
        "Zema (NOVO)",
        "Flavio Bolsonaro (PL)",
    ]
    y = np.arange(len(order))[::-1]
    for index, name in enumerate(order):
        row = deck["por_candidato"][name]
        ax.barh(y[index], row["propostas"], color=C["green"], height=0.56, zorder=3)
        ax.barh(
            y[index],
            row["evitar"],
            left=row["propostas"],
            color=C["lula"],
            height=0.56,
            zorder=3,
        )
        rest = 100 - row["propostas"] - row["evitar"]
        ax.barh(
            y[index],
            rest,
            left=row["propostas"] + row["evitar"],
            color=C["gray_soft"],
            height=0.56,
            zorder=3,
        )
        ax.text(
            row["propostas"] / 2,
            y[index],
            f"{row['propostas']}",
            ha="center",
            va="center",
            color="white",
            fontsize=12,
            fontweight="bold",
        )
        ax.text(
            row["propostas"] + row["evitar"] / 2,
            y[index],
            f"{row['evitar']}",
            ha="center",
            va="center",
            color="white",
            fontsize=12,
            fontweight="bold",
        )
        ratio = row["propostas"] / row["evitar"]
        ax.text(
            101.5,
            y[index],
            f"{ratio:.1f} proposta por rejeição",
            va="center",
            fontsize=9.8,
            color=C["muted"],
        )

    ax.set_yticks(y)
    ax.set_yticklabels(
        [
            f"{label(name)}\n{deck['por_candidato'][name]['entrevistas']} entrevistas · "
            f"{decision['por_candidato'][name]['pode_mudar']}% pode mudar"
            for name in order
        ],
        fontsize=10.2,
    )
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("em % dos eleitores de cada candidato", fontsize=10)
    frame(ax)
    ax.legend(
        handles=[
            Patch(color=C["green"], label="vota pelas propostas e pelo preparo"),
            Patch(color=C["lula"], label="vota para evitar que outro seja eleito"),
            Patch(color=C["gray_soft"], label="outras respostas e não sabe"),
        ],
        frameon=False,
        fontsize=9.8,
        loc="upper center",
        ncol=3,
        bbox_to_anchor=(0.5, -0.12),
    )
    ax.set_title(
        "O eleitor da terceira via vota por proposta. Não se compra com voto útil.",
        fontsize=17,
        fontweight="bold",
        loc="left",
        pad=16,
    )
    fig.tight_layout()
    note(
        fig,
        "Página 13 do relatório completo, nunca citada em manchete. Renan Santos tem a base mais propositiva da "
        "pesquisa; Flávio, a menos.\nA razão à direita é quantos votos por proposta existem para cada voto de rejeição "
        "dentro do eleitorado de cada candidato.",
        bottom=0.30,
        y=0.04,
    )
    finish(fig, "fundo_motivacao.png")


def conversao(data: dict) -> None:
    rows = [
        row
        for row in data["conversao"]["por_recorte"]
        if row["recorte"]
        in {
            "Total",
            "Masculino",
            "Feminino",
            "16-24",
            "60+",
            "Fundamental",
            "Superior",
            "Ate 2 SM",
            "Mais de 5 SM",
            "Catolica",
            "Evangelica",
            "Nordeste",
            "Sudeste",
            "Sem partido",
            "Nao alinhados",
        }
    ]
    fig, ax = plt.subplots(figsize=(11.4, 7.0))
    y = np.arange(len(rows))[::-1]
    width = 0.36
    ax.barh(
        y + width / 2,
        [row["lula_2turno_sobre_aprovacao"] for row in rows],
        height=width,
        color=C["lula"],
        zorder=3,
        label="Lula: voto no 2º turno sobre aprovação do governo",
    )
    ax.barh(
        y - width / 2,
        [row["flavio_2turno_sobre_desaprovacao"] for row in rows],
        height=width,
        color=C["flavio"],
        zorder=3,
        label="Flávio: voto no 2º turno sobre desaprovação",
    )
    ax.axvline(100, color=C["ink"], linestyle="--", linewidth=1.3, zorder=4)
    for index, row in enumerate(rows):
        ax.text(
            row["lula_2turno_sobre_aprovacao"] + 1.4,
            y[index] + width / 2,
            f"{row['lula_2turno_sobre_aprovacao']:.0f}",
            va="center",
            fontsize=9.2,
            color=C["lula"],
        )
        ax.text(
            row["flavio_2turno_sobre_desaprovacao"] + 1.4,
            y[index] - width / 2,
            f"{row['flavio_2turno_sobre_desaprovacao']:.0f}",
            va="center",
            fontsize=9.2,
            color=C["flavio"],
        )
    ax.set_yticks(y)
    ax.set_yticklabels([label(row["recorte"]) for row in rows], fontsize=10.4)
    ax.set_xlim(0, 145)
    ax.set_xlabel("voto dividido pelo tamanho do próprio polo, em %", fontsize=10)
    frame(ax)
    ax.legend(
        frameon=False,
        fontsize=9.8,
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.5, -0.11),
    )
    ax.set_title(
        "Lula converte o próprio polo inteiro. A oposição, não.",
        fontsize=17,
        fontweight="bold",
        loc="left",
        pad=16,
    )
    fig.tight_layout()
    note(
        fig,
        "Linha tracejada em 100: o candidato leva exatamente o tamanho do próprio polo. Acima de 100 ele recruta fora dele; "
        "abaixo, deixa voto na mesa.\nPolo de Lula: quem aprova o governo. Polo da oposição: quem desaprova. "
        "Entre eleitores de ensino superior a oposição converte 72 e Lula, 112.",
        bottom=0.27,
        y=0.035,
    )
    finish(fig, "fundo_conversao.png")


def alvos(data: dict) -> None:
    """Mapa de alvos da oposicao: tamanho do bloco x vao x mobilidade."""
    gap_rows = {row["recorte"]: row for row in data["vao"]["por_recorte"]}
    offsets = {
        "Nao alinhados": (0, 26),
        "Sem partido": (0, 24),
        "Superior": (0, 22),
        "2 a 5 SM": (0, 18),
        "Mais de 5 SM": (0, 15),
        "25-34": (0, 15),
        "PEA": (0, -26),
        "Branca": (0, 17),
        "Sudeste": (0, -26),
        "Medio": (-46, 0),
        "45-59": (0, 17),
        "Feminino": (0, 18),
        "Regiao metropolitana": (0, -26),
        "Interior": (0, 16),
        "Ate 2 SM": (0, -26),
        "Catolica": (48, 0),
        "60+": (0, -22),
        "Fundamental": (0, 16),
    }
    fig, ax = plt.subplots(figsize=(12.4, 7.6))

    for name, offset in offsets.items():
        row = gap_rows[name]
        share = 100 * row["base"] / 2058
        size = 120 + row["nao_escolha_pct"] * 46
        color = (
            C["gold"]
            if row["vao_pp"] >= 9
            else (C["flavio"] if row["vao_pp"] >= 6 else C["gray"])
        )
        ax.scatter(
            [share],
            [row["vao_pp"]],
            s=size,
            color=color,
            alpha=0.72,
            zorder=4,
            edgecolor=C["paper"],
            linewidth=1.4,
        )
        align = "center" if offset[0] == 0 else ("right" if offset[0] < 0 else "left")
        ax.annotate(
            label(name),
            (share, row["vao_pp"]),
            textcoords="offset points",
            xytext=offset,
            ha=align,
            va="center" if offset[0] else "bottom",
            fontsize=9.6,
            color=C["ink"],
        )

    ax.axhline(
        data["vao"]["vao_nacional_pp"],
        color=C["ink"],
        linestyle="--",
        linewidth=1.2,
        zorder=2,
    )
    ax.text(
        1.5,
        data["vao"]["vao_nacional_pp"] + 0.35,
        "vão nacional: 7 pontos",
        fontsize=9.6,
        color=C["muted"],
    )
    ax.set_xlim(2, 62)
    ax.set_ylim(-3, 29)
    ax.set_xlabel("tamanho do bloco, em % do eleitorado", fontsize=10.5)
    ax.set_ylabel("vão, em pontos percentuais", fontsize=10.5)
    ax.grid(color=C["line"], linewidth=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_title(
        "Onde há voto anti-governo que a oposição ainda não recolheu",
        fontsize=17.5,
        fontweight="bold",
        loc="left",
        pad=16,
    )
    fig.tight_layout()
    note(
        fig,
        "O diâmetro do círculo é a parcela do recorte que não escolhe ninguém no segundo turno, ou seja, o tamanho do "
        "reservatório.\nAlto e à direita: alvo grande e caro. Alto e à esquerda: alvo concentrado e barato. "
        "Baixo: já convertido ou fora de alcance.",
        bottom=0.20,
        y=0.035,
    )
    finish(fig, "fundo_alvos.png")


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    print("figuras:")
    mercado_aberto(data)
    campo_versus_peso(data)
    piso_de_ruido(data)
    vao(data)
    substituicao(data)
    serie_congelada(data)
    consolidacao(data)
    cobertura(data)
    motivacao(data)
    conversao(data)
    alvos(data)


if __name__ == "__main__":
    main()
