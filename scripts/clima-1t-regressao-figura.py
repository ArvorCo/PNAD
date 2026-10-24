#!/usr/bin/env python3
"""Desenha o coeficiente histórico e seu IC; não estima previsão municipal."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]


def gerar():
    fonte = ROOT / "analysis/clima_1t_2026/clima.json"
    d = json.loads(fonte.read_text())
    r = d["resumo"]["abstencao_pp_por_10mm_fe_municipio"]
    xs = list(range(31))
    ys = [r["coef"] * x / 10 for x in xs]
    lo = [r["ic95"][0] * x / 10 for x in xs]
    hi = [r["ic95"][1] * x / 10 for x in xs]
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "svg.fonttype": "none",
            "svg.hashsalt": "arvor-clima-regressao",
            "font.size": 11,
        }
    ):
        fig, ax = plt.subplots(figsize=(9, 5.3), layout="constrained")
        fig.patch.set_facecolor("#f6f2e8")
        ax.set_facecolor("#fffdf8")
        ax.fill_between(
            xs, lo, hi, color="#dcb66d", alpha=0.5, label="IC 95% da associação"
        )
        ax.plot(
            xs,
            ys,
            color="#193c35",
            lw=2.5,
            label="Estimativa com efeito fixo municipal",
        )
        ax.axhline(0, color="#8e4b3d", ls="--", lw=1.2, label="Nenhuma diferença")
        ax.set(
            xlim=(0, 30),
            ylim=(-1.6, 0.6),
            xlabel="Chuva adicional na janela histórica 7h–18h de Brasília (mm)",
            ylabel="Diferença associada de abstenção (p.p.)",
        )
        ax.set_title(
            "Chuva e abstenção: a incerteza atravessa o zero",
            loc="left",
            pad=18,
            fontweight="bold",
        )
        ax.set_yticks([-1.5, -1, -0.5, 0, 0.5])
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ","))
        )
        ax.grid(axis="y", alpha=0.18)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="lower left", frameon=False, fontsize=10)
        fig.supxlabel(
            "1º turno de 2026 · ponderação por aptos · erro agrupado por célula meteorológica\n"
            "Faixa do coeficiente, não intervalo de previsão. A reta não prevê a taxa de cada município.",
            fontsize=9,
        )
        destino = ROOT / "docs/img/clima_regressao_abstencao"
        for formato in ("svg", "png"):
            meta = {"Date": None} if formato == "svg" else {}
            arquivo = destino.with_suffix("." + formato)
            fig.savefig(arquivo, dpi=180, metadata=meta)
            if formato == "svg":
                arquivo.write_text(
                    "\n".join(
                        linha.rstrip() for linha in arquivo.read_text().splitlines()
                    )
                    + "\n"
                )
        plt.close(fig)
    destino = ROOT / "docs/assets/clima_1t/regressao_curva.csv"
    with destino.open("w") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            [
                "chuva_adicional_mm",
                "diferenca_abstencao_pp",
                "ic95_inferior_pp",
                "ic95_superior_pp",
            ]
        )
        writer.writerows(zip(xs, ys, lo, hi, strict=True))
    destino.with_suffix(".json").write_text(
        json.dumps(
            {
                "fonte": str(fonte.relative_to(ROOT)),
                "sha256": hashlib.sha256(fonte.read_bytes()).hexdigest(),
                "coeficiente_por_10mm": r,
                "formula": "delta_abstencao_pp = coeficiente * delta_chuva_mm / 10",
                "interpretacao": "Associação histórica dentro do município. IC do coeficiente reescalado, não previsão municipal ou efeito causal.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    gerar()
