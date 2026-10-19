"""Figuras científicas exportáveis, produzidas dos números do modelo."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .fontes import ROOT

BLUE, GREEN, INK = "#185a9d", "#087f72", "#172b2b"


def figures(data):
    out = ROOT / "docs/img/projecao_secoes_2t"
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": INK,
            "text.color": INK,
            "figure.facecolor": "#f8f6ef",
            "axes.facecolor": "#f8f6ef",
            "svg.fonttype": "none",
            "svg.hashsalt": "projecao-secoes-2t",
        }
    )
    validation = data["validacao"]["resultados"]
    names = list(validation)
    labels = [
        validation[k]["rotulo"].replace("histórico ", "").replace(", encolhido", "")
        for k in names
    ]
    fig, ax = plt.subplots(figsize=(11, 4.5), layout="constrained")
    values = [validation[k]["rmse_uf_pp"] for k in names]
    ax.barh(
        labels,
        values,
        color=[GREEN if k == data["selecionado"] else "#a0abaa" for k in names],
    )
    for i, v in enumerate(values):
        ax.text(v + 0.12, i, f"{v:.2f}".replace(".", ","), va="center")
    ax.invert_yaxis()
    ax.set(
        xlabel="Erro por UF em pontos percentuais • menor é melhor",
        xlim=(0, max(values) + 1.5),
        title="Aprender em 2018, prever 2022: a complexidade não venceu",
    )
    for ext in ("svg", "pdf"):
        fig.savefig(
            out / f"validacao.{ext}",
            metadata={"Date": None} if ext == "svg" else {"CreationDate": None},
        )
    plt.close(fig)
    states = pd.DataFrame(data["ufs"]["linhas"], columns=data["ufs"]["colunas"])
    first = 100 * states.direita_1 / (states.direita_1 + states.esquerda_1)
    last = (
        100
        * states.combinado_direita
        / (states.combinado_direita + states.combinado_esquerda)
    )
    order = np.argsort(last.to_numpy())
    fig, ax = plt.subplots(figsize=(11, 9), layout="constrained")
    for y, i in enumerate(order):
        ax.plot([first.iloc[i], last.iloc[i]], [y, y], color="#9aa5a0", lw=2)
    ax.scatter(
        first.iloc[order],
        np.arange(len(order)),
        c="#6a7875",
        marker="o",
        s=25,
        label="1º turno, entre finalistas",
    )
    ax.scatter(
        last.iloc[order],
        np.arange(len(order)),
        c=GREEN,
        marker="D",
        s=25,
        label="Combinação experimental, 2º turno",
    )
    ax.axvline(50, color=INK, ls="--", lw=1)
    ax.set(
        yticks=np.arange(len(order)),
        yticklabels=states.uf.iloc[order],
        xlabel="Flávio, % entre os dois finalistas",
        title="A mudança projetada, estado por estado",
    )
    ax.legend(loc="lower right", fontsize=9)
    for ext in ("svg", "pdf"):
        fig.savefig(
            out / f"estados.{ext}",
            metadata={"Date": None} if ext == "svg" else {"CreationDate": None},
        )
    plt.close(fig)
