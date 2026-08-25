#!/usr/bin/env python3
"""Gera as figuras de perfil e reponderacao do Datafolha de agosto de 2026."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "analysis" / "datafolha_082026" / "audit.json"
OUT = ROOT / "docs" / "img" / "datafolha_082026"

C = {
    "bg": "#f4f0e8",
    "ink": "#151711",
    "muted": "#676a60",
    "grid": "#d8d1c4",
    "lula": "#bb3a2d",
    "flavio": "#245aa5",
    "gold": "#c58b2b",
    "green": "#1f7a4d",
    "light": "#d9d3c8",
}


def load() -> dict:
    return json.loads(AUDIT.read_text(encoding="utf-8"))


def finish(fig: plt.Figure, name: str) -> None:
    fig.patch.set_facecolor(C["bg"])
    fig.savefig(OUT / name, dpi=180, bbox_inches="tight", facecolor=C["bg"])
    plt.close(fig)


def income_composition(data: dict) -> None:
    source = data["reweighting"]["income_tipping_point"]
    labels = ["Até 2 SM", "2 a 5 SM", "Mais de 5 SM"]
    keys = ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"]
    poll = [source["datafolha_nonmissing_profile"][key] for key in keys]
    pnad = [source["pnad_profile"][key] for key in keys]
    colors = ["#2d7a4d", "#d3a13a", "#406ca8"]

    fig, ax = plt.subplots(figsize=(12, 5.8))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    for y, values in enumerate((poll, pnad)):
        left = 0.0
        for value, label, color in zip(values, labels, colors):
            ax.barh(y, value, left=left, height=0.52, color=color, edgecolor=C["bg"], linewidth=2)
            if value >= 10:
                ax.text(left + value / 2, y, f"{value:.1f}%", ha="center", va="center", color="white", fontsize=15, fontweight="bold")
            left += value
    ax.set_yticks([0, 1], ["Datafolha\nsem NS/recusa", "PNADC 2025\n16+ anos"], fontsize=13, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Distribuição da população, %", fontsize=11, color=C["muted"])
    ax.xaxis.grid(True, color=C["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(C["grid"])
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]
    ax.legend(handles, labels, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.29), fontsize=11)
    fig.suptitle("A amostra mede um Brasil muito mais pobre que a PNADC", x=0.08, ha="left", fontsize=22, fontweight="bold", color=C["ink"])
    ax.set_title("A faixa até dois salários mínimos está 16,7 pontos acima da fonte oficial entre as rendas informadas.", loc="left", fontsize=12, color=C["muted"], pad=14)
    fig.text(0.08, 0.01, "Fontes: Datafolha BR-04496/2026, perfil ponderado; PNADC anual 2025, visita 1. Renda domiciliar efetiva.", fontsize=9, color=C["muted"])
    finish(fig, "renda_composicao.png")


def reweighting(data: dict) -> None:
    single = data["reweighting"]["single_margin"]
    combined = data["reweighting"]["combined_main_effects"]["result"]
    rows = [
        ("Publicado", 47.0, 43.0, False),
        ("Sexo", single["sexo"]["result"]["lula"], single["sexo"]["result"]["flavio"], True),
        ("Idade", single["idade"]["result"]["lula"], single["idade"]["result"]["flavio"], True),
        ("Escolaridade", single["escolaridade"]["result"]["lula"], single["escolaridade"]["result"]["flavio"], True),
        ("Região", single["regiao"]["result"]["lula"], single["regiao"]["result"]["flavio"], True),
        ("Renda", single["renda"]["result"]["lula"], single["renda"]["result"]["flavio"], True),
        ("Cinco margens*", combined["lula"], combined["flavio"], True),
    ]
    labels = [row[0] for row in rows]
    lula = np.array([row[1] for row in rows])
    flavio = np.array([row[2] for row in rows])
    y = np.arange(len(rows))

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_facecolor(C["bg"])
    height = 0.34
    bars_l = ax.barh(y - height / 2, lula, height=height, color=C["lula"], label="Lula")
    bars_f = ax.barh(y + height / 2, flavio, height=height, color=C["flavio"], label="Flávio")
    for i in range(1, len(rows)):
        bars_l[i].set_hatch("////")
        bars_f[i].set_hatch("////")
        bars_l[i].set_edgecolor("white")
        bars_f[i].set_edgecolor("white")
    for bars in (bars_l, bars_f):
        for bar in bars:
            ax.text(bar.get_width() + 0.35, bar.get_y() + bar.get_height() / 2, f"{bar.get_width():.1f}", va="center", fontsize=11, fontweight="bold", color=C["ink"])
    ax.axvline(45, color=C["grid"], linewidth=0.8)
    ax.set_yticks(y, labels, fontsize=12, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlim(0, 51)
    ax.set_xlabel("Intenção de voto no segundo turno, %", fontsize=11, color=C["muted"])
    ax.xaxis.grid(True, color=C["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(C["grid"])
    ax.legend(frameon=False, ncol=2, loc="lower right", fontsize=11)
    fig.suptitle("Quatro margens preservam o placar. Renda troca o sinal.", x=0.08, ha="left", fontsize=22, fontweight="bold", color=C["ink"])
    ax.set_title("Barras sólidas são o resultado publicado. Hachuras são sensibilidades por pós-estratificação.", loc="left", fontsize=12, color=C["muted"], pad=14)
    fig.text(0.08, 0.015, "*Modelo ecológico aditivo com sexo, idade, escolaridade, renda e região. Não substitui os microdados nem a ponderação conjunta do instituto.", fontsize=9, color=C["muted"])
    finish(fig, "reponderacao_margens.png")


def profile_benchmark(data: dict) -> None:
    dimensions = [
        ("Sexo", "sexo"),
        ("Idade", "idade"),
        ("Escolaridade", "escolaridade"),
        ("Renda", "renda"),
        ("Região", "regiao"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.ravel()
    for ax, (title, key) in zip(axes, dimensions):
        rows = data["profile_deltas"][key]
        labels = [row["category"].replace(" a ", "–") for row in rows]
        values = [row["delta"] for row in rows]
        colors = [C["lula"] if value > 0 else C["flavio"] for value in values]
        y = np.arange(len(values))
        ax.barh(y, values, color=colors, height=0.62)
        ax.axvline(0, color=C["ink"], linewidth=0.9)
        ax.set_yticks(y, labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_title(title, loc="left", fontsize=15, fontweight="bold")
        limit = max(3.0, max(abs(value) for value in values) * 1.25)
        ax.set_xlim(-limit, limit)
        ax.xaxis.grid(True, color=C["grid"], linewidth=0.7)
        ax.set_axisbelow(True)
        for i, value in enumerate(values):
            ax.text(value + (0.15 if value >= 0 else -0.15), i, f"{value:+.1f}", va="center", ha="left" if value >= 0 else "right", fontsize=9, fontweight="bold")
        for side in ax.spines.values():
            side.set_visible(False)
        ax.set_facecolor(C["bg"])
    axes[-1].axis("off")
    axes[-1].text(0.05, 0.75, "Desvio em pontos\npercentuais", fontsize=18, fontweight="bold", color=C["ink"])
    axes[-1].text(0.05, 0.46, "vermelho  Datafolha acima\nazul         Datafolha abaixo", fontsize=11, color=C["muted"], linespacing=1.7)
    axes[-1].text(0.05, 0.2, "Renda domina a auditoria.\nAs demais margens estão\npróximas das referências.", fontsize=12, color=C["ink"], fontweight="bold", linespacing=1.5)
    fig.suptitle("O problema de composição tem nome: renda", x=0.06, ha="left", fontsize=24, fontweight="bold", color=C["ink"])
    fig.text(0.06, 0.02, "Referências: TSE para sexo, idade e região; PNADC para escolaridade e renda. Perfil Datafolha ponderado.", fontsize=9, color=C["muted"])
    fig.tight_layout(rect=(0.04, 0.05, 0.99, 0.92), w_pad=2.5, h_pad=2.0)
    finish(fig, "perfil_benchmark.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.labelcolor": C["ink"],
        "text.color": C["ink"],
        "xtick.color": C["muted"],
        "ytick.color": C["ink"],
    })
    data = load()
    income_composition(data)
    reweighting(data)
    profile_benchmark(data)


if __name__ == "__main__":
    main()
