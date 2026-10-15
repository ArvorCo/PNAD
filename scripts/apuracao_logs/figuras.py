"""Distribuição descritiva de durações, publicada em SVG e PNG."""

from __future__ import annotations

import os

from .coleta import ROOT
from .publicacao import PUBLICO


def gerar(indice):
    os.environ.setdefault(
        "MPLCONFIGDIR", str(ROOT / "analysis/apuracao_2026/logs_urnas/qa/matplotlib")
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    papel, tinta = "#f4f1e8", "#182e34"
    histogramas = {}
    for pais, d in indice["tempos"].items():
        bins = [0] * 19
        for tempo, frequencia in d["histograma"]:
            bins[min(tempo // 10, 18)] += frequencia
        histogramas[pais] = [100 * n / d["ciclos"] for n in bins]
    teto = max((max(v) for v in histogramas.values()), default=10) * 1.15
    for mobile in (False, True):
        with plt.rc_context(
            {
                "font.family": "DejaVu Sans",
                "font.size": 11.5 if mobile else 11,
                "svg.fonttype": "path",
            }
        ):
            fig, axes = plt.subplots(
                2,
                1,
                figsize=(4.0, 7.8) if mobile else (10.4, 7.0),
                layout="constrained",
            )
            fig.set_facecolor(papel)
            for ax, pais, cor in zip(
                axes, ("brasil", "exterior"), ("#216577", "#8b5b20"), strict=True
            ):
                d = indice["tempos"].get(pais)
                ax.set_facecolor(papel)
                if not d:
                    ax.text(
                        0.5,
                        0.5,
                        "Sem ciclos elegíveis",
                        ha="center",
                        transform=ax.transAxes,
                    )
                    ax.set_axis_off()
                    continue
                ax.bar(range(19), histogramas[pais], width=0.86, color=cor)
                titulo = "Brasil" if pais == "brasil" else "Exterior"
                separador = "\n" if mobile else " · "
                ax.set_title(
                    f'{titulo}{separador}{d["ciclos"]:,} ciclos elegíveis'.replace(
                        ",", "."
                    ),
                    loc="left",
                    color=tinta,
                    fontweight="bold",
                    pad=14,
                )
                ticks = [0, 6, 12, 18] if mobile else [0, 3, 6, 9, 12, 15, 18]
                ax.set_xticks(
                    ticks, [f"{t*10}–{t*10+9}" if t < 18 else "≥180" for t in ticks]
                )
                ax.set_xlabel("Duração da votação (segundos)", color=tinta)
                ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
                ax.set_ylabel("Parcela dos ciclos", color=tinta)
                ax.set_ylim(0, teto)
                ax.spines[["top", "right"]].set_visible(False)
                ax.spines[["bottom", "left"]].set_color("#b7c4c4")
                ax.tick_params(colors=tinta, labelsize=11 if mobile else 10)
                ax.grid(axis="y", color="#b7c4c4", alpha=0.5)
                ax.set_axisbelow(True)
            for ext in ("svg", "png"):
                nome = "tempos-mobile" if mobile else "tempos"
                fig.savefig(PUBLICO / f"{nome}.{ext}", dpi=160, facecolor=papel)
            plt.close(fig)
