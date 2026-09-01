#!/usr/bin/env python3
"""Padroniza por renda quatro ondas Datafolha do segundo turno em 2026.

Cada relatório de maio a agosto publica o cruzamento Lula x Flávio por renda e
as bases ponderadas das faixas. O exercício mantém o topline de cada onda como
âncora e soma somente a diferença entre:

1. o topline recomposto pelas bases de renda publicadas; e
2. o topline sob a distribuição da PNADC anual 2025, visita 1, pessoas 16+.

Isto produz uma série de sensibilidade sob uma margem oficial comum. Não é uma
correção da pesquisa, uma previsão ou uma estimativa do resultado real.

Saídas:
  analysis/datafolha_082026/historico_renda.json
  docs/assets/datafolha_082026_historico_renda.json
  docs/assets/datafolha_082026_historico_renda.js
  docs/img/datafolha_082026/historico_2turno_pnadc.png
  docs/img/datafolha_082026/historico_2turno_pnadc_mobile.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "analysis" / "datafolha_082026" / "audit.json"
PNAD_CACHE = ROOT / "data" / "outputs" / "pnad_2025v1_renda_faixas.json"
OUT_ANALYSIS = ROOT / "analysis" / "datafolha_082026" / "historico_renda.json"
OUT_SITE = ROOT / "docs" / "assets" / "datafolha_082026_historico_renda.json"
OUT_JS = ROOT / "docs" / "assets" / "datafolha_082026_historico_renda.js"
OUT_IMG = ROOT / "docs" / "img" / "datafolha_082026" / "historico_2turno_pnadc.png"
OUT_IMG_MOBILE = (
    ROOT / "docs" / "img" / "datafolha_082026" / "historico_2turno_pnadc_mobile.png"
)

OPTIONS = ("lula", "flavio", "branco_nulo", "indecisos")

# Transcrição visual dos cruzamentos de segundo turno. Maio, junho e julho
# publicam quatro faixas; agosto agrega todas as rendas acima de 5 SM.
WAVES = [
    {
        "id": "2026-05-21",
        "label": "20–21/mai",
        "field": "20 e 21/05/2026",
        "report": "data/originals/datafolha_052026/DataFolhaRelatorio052026.pdf",
        "pdf_page": 23,
        "table_page": 23,
        "published": [47, 43, 9, 2],
        "bands": ["ate2", "de2a5", "de5a10", "mais10"],
        "bases": [1001, 682, 170, 71],
        "rows": [
            [55, 35, 8, 1],
            [40, 50, 9, 1],
            [33, 56, 11, 0],
            [35, 61, 5, 0],
        ],
    },
    {
        "id": "2026-06-18",
        "label": "17–18/jun",
        "field": "17 e 18/06/2026",
        "report": "data/originals/datafolha_062026/DataFolhaRelatorio062026.pdf",
        "pdf_page": 25,
        "table_page": 25,
        "published": [47, 43, 8, 1],
        "bands": ["ate2", "de2a5", "de5a10", "mais10"],
        "bases": [1010, 680, 162, 67],
        "rows": [
            [53, 38, 8, 2],
            [41, 49, 9, 1],
            [42, 51, 7, 0],
            [43, 54, 3, 0],
        ],
    },
    {
        "id": "2026-07-23",
        "label": "22–23/jul",
        "field": "22 e 23/07/2026",
        "report": "data/originals/datafolha_072026/DataFolhaRelatorio072026.pdf",
        "pdf_page": 18,
        "table_page": 18,
        "published": [48, 43, 9, 1],
        "bands": ["ate2", "de2a5", "de5a10", "mais10"],
        "bases": [1002, 678, 194, 51],
        "rows": [
            [56, 36, 7, 1],
            [39, 50, 10, 1],
            [38, 51, 11, 0],
            [45, 51, 3, 0],
        ],
    },
    {
        "id": "2026-08-19",
        "label": "18–19/ago",
        "field": "18 e 19/08/2026",
        "report": "data/originals/datafolha_082026/DatafolhaRelatorio082026.pdf",
        "pdf_page": 44,
        "table_page": 22,
        "published": [47, 43, 9, 2],
        "bands": ["ate2", "de2a5", "mais5"],
        "bases": [1031, 704, 249],
        "rows": [
            [55, 35, 8, 1],
            [37, 51, 10, 2],
            [39, 54, 7, 0],
        ],
    },
]

C = {
    "bg": "#f4f0e8",
    "ink": "#151711",
    "muted": "#676a60",
    "grid": "#d8d1c4",
    "lula": "#bb3a2d",
    "flavio": "#245aa5",
    "gold": "#b57b1f",
    "published": "#3f433b",
}


def normalized_rows(rows: np.ndarray) -> np.ndarray:
    totals = rows.sum(axis=1, keepdims=True)
    return np.divide(rows, totals, out=np.zeros_like(rows), where=totals > 0)


def topline(rows: np.ndarray, weights: np.ndarray) -> np.ndarray:
    weights = weights / weights.sum()
    return weights @ normalized_rows(rows) * 100


def load_targets() -> dict[str, dict[str, float]]:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    target3_raw = audit["benchmarks"]["pnad"]["renda"]
    target3 = {
        "ate2": target3_raw["Ate 2 SM"],
        "de2a5": target3_raw["2 a 5 SM"],
        "mais5": target3_raw["Mais de 5 SM"],
    }
    cached = json.loads(PNAD_CACHE.read_text(encoding="utf-8"))["vd5001"]["pessoas_16"]
    high_total = cached["de5a10"] + cached["mais10"]
    target4 = {
        "ate2": target3["ate2"],
        "de2a5": target3["de2a5"],
        "de5a10": target3["mais5"] * cached["de5a10"] / high_total,
        "mais10": target3["mais5"] * cached["mais10"] / high_total,
    }
    return {"tres_faixas": target3, "quatro_faixas": target4}


def rounding_test(
    wave: dict[str, object], target: np.ndarray, draws: int = 10_000
) -> dict[str, float | int]:
    generator = np.random.default_rng(20260825 + int(str(wave["id"])[5:7]))
    original = np.array(wave["rows"], dtype=float)
    bases = np.array(wave["bases"], dtype=float)
    published = np.array(wave["published"], dtype=float)
    gaps = np.empty(draws)
    for index in range(draws):
        perturbed = np.maximum(
            0, original + generator.uniform(-0.5, 0.5, original.shape)
        )
        adjusted = published + (topline(perturbed, target) - topline(perturbed, bases))
        gaps[index] = adjusted[0] - adjusted[1]
    p2, median, p97 = np.quantile(gaps, [0.025, 0.5, 0.975])
    return {
        "draws": draws,
        "gap_p2_5": round(float(p2), 3),
        "gap_median": round(float(median), 3),
        "gap_p97_5": round(float(p97), 3),
        "share_flavio_ahead": round(float(np.mean(gaps < 0)), 4),
    }


def calculate() -> dict[str, object]:
    targets = load_targets()
    output_waves = []
    for wave in WAVES:
        target_key = "quatro_faixas" if len(wave["bands"]) == 4 else "tres_faixas"
        target_map = targets[target_key]
        target = np.array([target_map[band] for band in wave["bands"]], dtype=float)
        rows = np.array(wave["rows"], dtype=float)
        bases = np.array(wave["bases"], dtype=float)
        published = np.array(wave["published"], dtype=float)
        reproduced = topline(rows, bases)
        counterfactual = topline(rows, target)
        adjusted = published + (counterfactual - reproduced)
        source_profile = 100 * bases / bases.sum()
        output_waves.append(
            {
                **wave,
                "source_profile_pct": dict(
                    zip(wave["bands"], np.round(source_profile, 3), strict=False)
                ),
                "target_profile_pct": dict(
                    zip(wave["bands"], np.round(target, 3), strict=False)
                ),
                "reproduced_from_cells": dict(
                    zip(OPTIONS, np.round(reproduced, 3), strict=False)
                ),
                "counterfactual_direct": dict(
                    zip(OPTIONS, np.round(counterfactual, 3), strict=False)
                ),
                "adjusted": dict(zip(OPTIONS, np.round(adjusted, 3), strict=False)),
                "published_gap_lula_minus_flavio": float(published[0] - published[1]),
                "adjusted_gap_lula_minus_flavio": round(
                    float(adjusted[0] - adjusted[1]), 3
                ),
                "rounding_sensitivity": rounding_test(wave, target),
            }
        )

    return {
        "method": {
            "label": "sensibilidade de pós-estratificação por uma margem",
            "formula": "publicado + (topline PNADC - topline recomposto pelas bases de renda)",
            "benchmark": "PNADC anual 2025, visita 1, VD5001, pessoas de 16 anos ou mais",
            "common_rule": "mesmo benchmark em todas as ondas; quatro faixas quando publicadas e três em agosto",
            "limitations": [
                "Não há microdados, pesos individuais, estratos, PSU nem efeito de desenho público.",
                "Renda familiar declarada no Datafolha não é idêntica ao rendimento domiciliar da PNADC.",
                "Ajustar uma margem não identifica interações com escolaridade, região, idade ou religião.",
                "A série mostra tendência sob uma régua comum de renda, não a tendência real da eleição.",
            ],
        },
        "target_profiles_pct": targets,
        "waves": output_waves,
    }


def label_gap(value: float) -> str:
    if abs(value) < 0.25:
        return "empate"
    candidate = "Lula" if value > 0 else "Flávio"
    return f"{candidate} +{abs(value):.1f}".replace(".", ",")


def draw(data: dict[str, object]) -> None:
    waves = data["waves"]
    labels = [wave["label"] for wave in waves]
    x = np.arange(len(waves))
    pub_l = np.array([wave["published"][0] for wave in waves], dtype=float)
    pub_f = np.array([wave["published"][1] for wave in waves], dtype=float)
    adj_l = np.array([wave["adjusted"]["lula"] for wave in waves], dtype=float)
    adj_f = np.array([wave["adjusted"]["flavio"] for wave in waves], dtype=float)
    gap_pub = pub_l - pub_f
    gap_adj = adj_l - adj_f

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.labelcolor": C["ink"],
            "text.color": C["ink"],
            "xtick.color": C["muted"],
            "ytick.color": C["muted"],
        }
    )
    fig = plt.figure(figsize=(12.5, 9.2), facecolor=C["bg"])
    grid = fig.add_gridspec(
        2,
        1,
        height_ratios=[1.45, 1],
        hspace=0.34,
        left=0.09,
        right=0.98,
        top=0.79,
        bottom=0.105,
    )
    ax = fig.add_subplot(grid[0])
    gap_ax = fig.add_subplot(grid[1], sharex=ax)
    for current in (ax, gap_ax):
        current.set_facecolor(C["bg"])
        current.grid(axis="y", color=C["grid"], linewidth=0.8)
        current.set_axisbelow(True)
        for side in ("top", "right", "left"):
            current.spines[side].set_visible(False)
        current.spines["bottom"].set_color(C["grid"])

    ax.plot(x, pub_l, "-o", color=C["lula"], lw=2.8, ms=7, label="Lula, publicado")
    ax.plot(x, pub_f, "-o", color=C["flavio"], lw=2.8, ms=7, label="Flávio, publicado")
    ax.plot(
        x,
        adj_l,
        "--o",
        color=C["lula"],
        lw=2.4,
        ms=7,
        mfc=C["bg"],
        mew=2,
        label="Lula, PNADC",
    )
    ax.plot(
        x,
        adj_f,
        "--o",
        color=C["flavio"],
        lw=2.4,
        ms=7,
        mfc=C["bg"],
        mew=2,
        label="Flávio, PNADC",
    )
    for index in range(len(x)):
        ax.annotate(
            f"{pub_l[index]:.0f}",
            (x[index], pub_l[index]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            color=C["lula"],
            fontsize=10,
            fontweight="bold",
        )
        ax.annotate(
            f"{pub_f[index]:.0f}",
            (x[index], pub_f[index]),
            xytext=(0, -18),
            textcoords="offset points",
            ha="center",
            color=C["flavio"],
            fontsize=10,
            fontweight="bold",
        )
        ax.annotate(
            f"{adj_l[index]:.1f}".replace(".", ","),
            (x[index], adj_l[index]),
            xytext=(-12, -20 if adj_l[index] <= adj_f[index] else 10),
            textcoords="offset points",
            ha="right",
            color=C["lula"],
            fontsize=9.5,
            fontweight="bold",
        )
        ax.annotate(
            f"{adj_f[index]:.1f}".replace(".", ","),
            (x[index], adj_f[index]),
            xytext=(12, 10 if adj_f[index] >= adj_l[index] else -20),
            textcoords="offset points",
            ha="left",
            color=C["flavio"],
            fontsize=9.5,
            fontweight="bold",
        )
    ax.set_ylim(41.5, 49.5)
    ax.set_yticks([42, 44, 46, 48])
    ax.set_ylabel("Intenção de voto, %", fontsize=11)
    ax.tick_params(axis="x", labelbottom=False)
    handles, legend_labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        frameon=False,
        ncol=4,
        fontsize=10.5,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.87),
        columnspacing=1.6,
        handlelength=2.4,
    )

    gap_ax.axhline(0, color=C["ink"], linewidth=1.1)
    gap_ax.plot(
        x, gap_pub, "-o", color=C["published"], lw=2.8, ms=7, label="Saldo publicado"
    )
    gap_ax.plot(
        x,
        gap_adj,
        "--o",
        color=C["gold"],
        lw=2.8,
        ms=7,
        mfc=C["bg"],
        mew=2,
        label="Saldo PNADC",
    )
    gap_ax.fill_between(x, 0, gap_adj, color=C["gold"], alpha=0.08)
    for index, value in enumerate(gap_pub):
        gap_ax.annotate(
            f"Lula +{value:.0f}",
            (x[index], value),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=9.5,
            fontweight="bold",
            color=C["published"],
        )
    for index, value in enumerate(gap_adj):
        label_offset = 10 if value < -0.5 else -20
        gap_ax.annotate(
            label_gap(float(value)),
            (x[index], value),
            xytext=(0, label_offset),
            textcoords="offset points",
            ha="center",
            fontsize=9.5,
            fontweight="bold",
            color=C["gold"],
        )
    gap_ax.set_ylim(-3.6, 6.0)
    gap_ax.set_yticks([-2, 0, 2, 4, 6])
    gap_ax.set_ylabel("Lula menos Flávio, p.p.", fontsize=11)
    gap_ax.set_xticks(x, labels, fontsize=10.5, fontweight="bold")
    gap_ax.legend(
        frameon=False,
        ncol=2,
        fontsize=10,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.28),
    )

    fig.suptitle(
        "A mesma régua de renda apaga a vantagem publicada",
        x=0.055,
        ha="left",
        y=0.975,
        fontsize=23,
        fontweight="bold",
    )
    fig.text(
        0.055,
        0.925,
        "Quatro ondas Datafolha: Lula +4 a +5 no placar divulgado. Com a PNADC 2025, maio e agosto invertem; junho e julho viram empate.",
        fontsize=11.5,
        color=C["muted"],
    )
    fig.text(
        0.055,
        0.018,
        "Sensibilidade por uma margem. Linhas sólidas: publicado. Tracejadas: mesmo benchmark PNADC anual 2025, pessoas 16+. Sem microdados, pesos e deff, não é estimativa do resultado real.",
        fontsize=9,
        color=C["muted"],
    )
    fig.savefig(OUT_IMG, dpi=180, bbox_inches="tight", facecolor=C["bg"])
    plt.close(fig)


def draw_mobile(data: dict[str, object]) -> None:
    waves = data["waves"]
    labels = [wave["label"] for wave in waves]
    x = np.arange(len(waves))
    pub_l = np.array([wave["published"][0] for wave in waves], dtype=float)
    pub_f = np.array([wave["published"][1] for wave in waves], dtype=float)
    adj_l = np.array([wave["adjusted"]["lula"] for wave in waves], dtype=float)
    adj_f = np.array([wave["adjusted"]["flavio"] for wave in waves], dtype=float)
    gap_pub = pub_l - pub_f
    gap_adj = adj_l - adj_f

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(4.8, 7.8),
        gridspec_kw={"height_ratios": [1.35, 1], "hspace": 0.43},
        facecolor=C["bg"],
    )
    ax, gap_ax = axes
    for current in axes:
        current.set_facecolor(C["bg"])
        current.grid(axis="y", color=C["grid"], linewidth=0.7)
        current.set_axisbelow(True)
        for side in ("top", "right", "left"):
            current.spines[side].set_visible(False)
        current.spines["bottom"].set_color(C["grid"])

    ax.plot(x, pub_l, "-o", color=C["lula"], lw=2.2, ms=5.5, label="Lula, publicado")
    ax.plot(
        x, pub_f, "-o", color=C["flavio"], lw=2.2, ms=5.5, label="Flávio, publicado"
    )
    ax.plot(
        x,
        adj_l,
        "--o",
        color=C["lula"],
        lw=2,
        ms=5.5,
        mfc=C["bg"],
        mew=1.6,
        label="Lula, PNADC",
    )
    ax.plot(
        x,
        adj_f,
        "--o",
        color=C["flavio"],
        lw=2,
        ms=5.5,
        mfc=C["bg"],
        mew=1.6,
        label="Flávio, PNADC",
    )
    for index in range(len(x)):
        ax.annotate(
            f"{adj_l[index]:.1f}".replace(".", ","),
            (x[index], adj_l[index]),
            xytext=(-6, -15 if adj_l[index] <= adj_f[index] else 8),
            textcoords="offset points",
            ha="right",
            fontsize=8,
            fontweight="bold",
            color=C["lula"],
        )
        ax.annotate(
            f"{adj_f[index]:.1f}".replace(".", ","),
            (x[index], adj_f[index]),
            xytext=(6, 8 if adj_f[index] >= adj_l[index] else -15),
            textcoords="offset points",
            ha="left",
            fontsize=8,
            fontweight="bold",
            color=C["flavio"],
        )
    ax.set_ylim(41.5, 49.5)
    ax.set_yticks([42, 44, 46, 48])
    ax.set_ylabel("Voto, %", fontsize=8.5)
    ax.tick_params(axis="x", labelbottom=False)
    ax.tick_params(axis="y", labelsize=8)
    ax.legend(
        frameon=False,
        ncol=2,
        fontsize=7.5,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.19),
        columnspacing=1.3,
        handlelength=2.1,
    )

    gap_ax.axhline(0, color=C["ink"], linewidth=1)
    gap_ax.plot(x, gap_pub, "-o", color=C["published"], lw=2.2, ms=5.5)
    gap_ax.plot(
        x, gap_adj, "--o", color=C["gold"], lw=2.2, ms=5.5, mfc=C["bg"], mew=1.6
    )
    gap_ax.fill_between(x, 0, gap_adj, color=C["gold"], alpha=0.08)
    for index, value in enumerate(gap_pub):
        gap_ax.annotate(
            f"Lula +{value:.0f}",
            (x[index], value),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=7.8,
            fontweight="bold",
            color=C["published"],
        )
    for index, value in enumerate(gap_adj):
        label_offset = 8 if value < -0.5 else -15
        gap_ax.annotate(
            label_gap(float(value)),
            (x[index], value),
            xytext=(0, label_offset),
            textcoords="offset points",
            ha="center",
            fontsize=7.8,
            fontweight="bold",
            color=C["gold"],
        )
    gap_ax.set_ylim(-3.6, 6)
    gap_ax.set_yticks([-2, 0, 2, 4, 6])
    gap_ax.set_ylabel("Lula menos Flávio, p.p.", fontsize=8.5)
    gap_ax.set_xticks(x, labels, fontsize=7.8, fontweight="bold")
    gap_ax.tick_params(axis="y", labelsize=8)

    fig.suptitle(
        "A régua comum apaga a vantagem",
        x=0.07,
        ha="left",
        y=0.985,
        fontsize=15,
        fontweight="bold",
    )
    fig.text(
        0.07,
        0.945,
        "Publicado: Lula +4 a +5. PNADC 2025: empate ou Flávio à frente.",
        fontsize=8.3,
        color=C["muted"],
    )
    fig.text(
        0.07,
        0.012,
        "Sensibilidade por renda, não resultado real. Sólida: publicado. Tracejada: PNADC 2025, pessoas 16+.",
        fontsize=6.7,
        color=C["muted"],
    )
    fig.savefig(OUT_IMG_MOBILE, dpi=180, bbox_inches="tight", facecolor=C["bg"])
    plt.close(fig)


def write(data: dict[str, object]) -> None:
    encoded = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    OUT_ANALYSIS.parent.mkdir(parents=True, exist_ok=True)
    OUT_SITE.parent.mkdir(parents=True, exist_ok=True)
    OUT_IMG.parent.mkdir(parents=True, exist_ok=True)
    OUT_ANALYSIS.write_text(encoded, encoding="utf-8")
    OUT_SITE.write_text(encoded, encoding="utf-8")
    OUT_JS.write_text(
        "window.DATAFOLHA_082026_HISTORICO_RENDA = " + encoded.rstrip() + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    data = calculate()
    write(data)
    draw(data)
    draw_mobile(data)
    for wave in data["waves"]:
        result = wave["adjusted"]
        print(
            f'{wave["label"]}: publicado {wave["published"][0]} x {wave["published"][1]}; '
            f'PNADC {result["lula"]:.2f} x {result["flavio"]:.2f}; '
            f'gap {wave["adjusted_gap_lula_minus_flavio"]:+.3f}'
        )


if __name__ == "__main__":
    main()
