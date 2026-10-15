"""Distribuição descritiva de durações, publicada em SVG e PNG."""

from __future__ import annotations

import os

from .coleta import ROOT
from .publicacao import PUBLICO


def gerar(indice):
    for campo, corte in (("tempos", 180), ("processo", 300), ("cadencia", 300)):
        gerar_medida(indice, campo, corte)


def gerar_medida(indice, campo, corte):
    n_bins = corte // 10 + 1
    unidade = {"tempos": "ciclos", "processo": "processos", "cadencia": "intervalos"}[
        campo
    ]
    os.environ.setdefault(
        "MPLCONFIGDIR", str(ROOT / "analysis/apuracao_2026/logs_urnas/qa/matplotlib")
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    papel, tinta = "#f4f1e8", "#182e34"
    histogramas = {}
    for pais, d in indice.get(campo, {}).items():
        bins = [0] * n_bins
        for tempo, frequencia in d["histograma"]:
            bins[min(tempo // 10, n_bins - 1)] += frequencia
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
                figsize=(4.0, 8.2) if mobile else (10.4, 7.0),
                layout="constrained",
            )
            fig.set_facecolor(papel)
            for ax, pais, cor in zip(
                axes, ("brasil", "exterior"), ("#216577", "#8b5b20"), strict=True
            ):
                d = indice.get(campo, {}).get(pais)
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
                ax.bar(range(n_bins), histogramas[pais], width=0.86, color=cor)
                titulo = "Brasil" if pais == "brasil" else "Exterior"
                base = f'{d["ciclos"]:,}'.replace(",", ".")
                titulo = (
                    f"{titulo}\n{base}\n{unidade} elegíveis"
                    if mobile
                    else f"{titulo} · {base} {unidade} elegíveis"
                )
                ax.set_title(
                    titulo,
                    loc="left",
                    color=tinta,
                    fontweight="bold",
                    pad=14,
                )
                ticks = list(
                    range(0, n_bins, (corte // 30) if mobile else (corte // 60))
                )
                ax.set_xticks(
                    ticks,
                    [
                        f"{t*10}–{t*10+9}" if t < n_bins - 1 else f"≥{corte}"
                        for t in ticks
                    ],
                )
                ax.set_xlabel(
                    {
                        "tempos": "Após habilitação (segundos)",
                        "processo": "Processo observado (segundos)",
                        "cadencia": "Entre cômputos (segundos)",
                    }[campo],
                    color=tinta,
                )
                ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
                ax.set_ylabel(f"Parcela dos {unidade}", color=tinta)
                ax.set_ylim(0, teto)
                ax.spines[["top", "right"]].set_visible(False)
                ax.spines[["bottom", "left"]].set_color("#b7c4c4")
                ax.tick_params(colors=tinta, labelsize=11 if mobile else 10)
                ax.grid(axis="y", color="#b7c4c4", alpha=0.5)
                ax.set_axisbelow(True)
            for ext in ("svg", "png"):
                nome = campo + ("-mobile" if mobile else "")
                fig.savefig(PUBLICO / f"{nome}.{ext}", dpi=160, facecolor=papel)
            plt.close(fig)
