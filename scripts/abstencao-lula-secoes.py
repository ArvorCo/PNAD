#!/usr/bin/env python3
"""Abstenção × voto em Lula por seção eleitoral no 1º turno de 2026: dispersão, curvas e histogramas.

Lê as seções do Politize (`docs/assets/politize/dados/zona/<UF>/<zona>.json`: aptos, comparecimento
em contagem, Lula em % dos válidos), exclui o exterior e seções com menos de `APTOS_MIN` aptos,
e desenha um gráfico conjunto: densidade (hexbin) de x = abstenção (% dos aptos) por y = Lula
(% dos válidos), curva de médias por faixa de abstenção com faixa interquartil, reta de mínimos
quadrados, histogramas marginais, Pearson simples e ponderado por aptos, e as curvas por região.

Saída: `docs/img/abstencao_lula_secoes_1t.png` (2400×2400) e `analysis/apuracao_2026/abstencao_lula_secoes.json`.

Uso: python3 scripts/abstencao-lula-secoes.py [--eixo abstencao|comparecimento]
"""

from __future__ import annotations

import argparse
import json
from itertools import pairwise
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import gridspec
from matplotlib.colors import LinearSegmentedColormap, LogNorm

ROOT = Path(__file__).resolve().parents[1]
ZONAS = ROOT / "docs" / "assets" / "politize" / "dados" / "zona"
SAIDAS = {
    "abstencao": (
        ROOT / "docs" / "img" / "abstencao_lula_secoes_1t.png",
        ROOT / "analysis" / "apuracao_2026" / "abstencao_lula_secoes.json",
    ),
    "comparecimento": (
        ROOT / "docs" / "img" / "comparecimento_lula_secoes_1t.png",
        ROOT / "analysis" / "apuracao_2026" / "comparecimento_lula_secoes.json",
    ),
}
EIXO = {
    "abstencao": {
        "nome": "abstenção",
        "titulo": "Abstenção e voto em Lula, seção por seção",
        "rotulo": "Abstenção na seção, % dos aptos",
        "xmin": 0.0,
        "xmax": 60.0,
        "nota": "o Nordeste tem menos abstenção e mais Lula",
    },
    "comparecimento": {
        "nome": "comparecimento",
        "titulo": "Comparecimento e voto em Lula, seção por seção",
        "rotulo": "Comparecimento na seção, % dos aptos",
        "xmin": 40.0,
        "xmax": 100.0,
        "nota": "o Nordeste tem mais comparecimento e mais Lula",
    },
}
APTOS_MIN = 50

REGIAO = {
    "Norte": "AC AM AP PA RO RR TO",
    "Nordeste": "AL BA CE MA PB PE PI RN SE",
    "Centro-Oeste": "DF GO MS MT",
    "Sudeste": "ES MG RJ SP",
    "Sul": "PR RS SC",
}
UF_REGIAO = {uf: r for r, ufs in REGIAO.items() for uf in ufs.split()}
COR_REGIAO = {
    "Norte": "#2bb98a",
    "Nordeste": "#5fd3e6",
    "Centro-Oeste": "#f0c86b",
    "Sudeste": "#ff8a7a",
    "Sul": "#8f9ff5",
}
FUNDO, FUNDO1, TINTA, SUAVE, LINHA = (
    "#060b1a",
    "#0c1a3a",
    "#eef2ff",
    "#9aa6c4",
    "#2a3a60",
)
LULA, OURO, TEAL = "#ea6a5c", "#f0c86b", "#5fd3e6"
MONO = "Menlo"


def carregar(eixo: str) -> dict[str, np.ndarray]:
    abst, lula, aptos, uf_l = [], [], [], []
    for pasta in sorted(ZONAS.iterdir()):
        uf = pasta.name
        if uf == "ZZ" or not pasta.is_dir():
            continue
        for arquivo in sorted(pasta.glob("*.json")):
            z = json.loads(arquivo.read_text(encoding="utf-8"))
            col = {c: i for i, c in enumerate(z["secoes"]["colunas"])}
            for r in z["secoes"]["linhas"]:
                a = r[col["aptos"]] or 0
                comp = r[col["comparecimento"]]
                lv = r[col["lula_v"]]
                if a < APTOS_MIN or comp is None or lv is None:
                    continue
                abst.append(
                    100.0 * (a - comp) / a if eixo == "abstencao" else 100.0 * comp / a
                )
                lula.append(float(lv))
                aptos.append(float(a))
                uf_l.append(uf)
    return {
        "abst": np.array(abst),
        "lula": np.array(lula),
        "aptos": np.array(aptos),
        "uf": np.array(uf_l),
    }


def pt(valor: float, casas: int = 1, sinal: bool = False) -> str:
    texto = f"{valor:+.{casas}f}" if sinal else f"{valor:.{casas}f}"
    return texto.replace(".", ",").replace("-", "−")


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pearson(x: np.ndarray, y: np.ndarray, w: np.ndarray | None = None) -> float:
    if w is None:
        w = np.ones_like(x)
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    return float(
        cov
        / np.sqrt(
            np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w)
        )
    )


def curva(
    x: np.ndarray, y: np.ndarray, bordas: np.ndarray, minimo: int = 200
) -> dict[str, np.ndarray]:
    centros, media, q1, q3, n = [], [], [], [], []
    for a, b in pairwise(bordas):
        sel = (x >= a) & (x < b)
        if sel.sum() < minimo:
            continue
        centros.append((a + b) / 2)
        media.append(np.mean(y[sel]))
        q1.append(np.percentile(y[sel], 25))
        q3.append(np.percentile(y[sel], 75))
        n.append(int(sel.sum()))
    return {
        k: np.array(v)
        for k, v in {"x": centros, "media": media, "q1": q1, "q3": q3, "n": n}.items()
    }


def desenhar(d: dict[str, np.ndarray], eixo: str) -> dict:
    e = EIXO[eixo]
    png = SAIDAS[eixo][0]
    x, y, w, uf = d["abst"], d["lula"], d["aptos"], d["uf"]
    r = pearson(x, y)
    rw = pearson(x, y, w)
    b, a = np.polyfit(x, y, 1)
    bordas = np.arange(e["xmin"], e["xmax"] + 0.01, 2.5)
    geral = curva(x, y, bordas)
    regioes = {}
    for nome in REGIAO:
        sel = np.isin(uf, REGIAO[nome].split())
        regioes[nome] = {
            "curva": curva(x[sel], y[sel], bordas, minimo=120),
            "r": pearson(x[sel], y[sel]),
            "n": int(sel.sum()),
            "abst_media": float(np.average(x[sel], weights=w[sel])),
            "lula_medio": float(np.average(y[sel], weights=w[sel])),
        }

    plt.rcParams.update(
        {
            "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
            "text.color": TINTA,
            "axes.edgecolor": LINHA,
            "axes.labelcolor": TINTA,
            "xtick.color": SUAVE,
            "ytick.color": SUAVE,
            "axes.facecolor": FUNDO1,
            "figure.facecolor": FUNDO,
            "savefig.facecolor": FUNDO,
        }
    )
    fig = plt.figure(figsize=(12, 12), dpi=200)
    gs = gridspec.GridSpec(
        2,
        2,
        width_ratios=[4.2, 1.1],
        height_ratios=[1.1, 4.2],
        hspace=0.04,
        wspace=0.04,
        left=0.075,
        right=0.975,
        bottom=0.245,
        top=0.85,
    )
    ax = fig.add_subplot(gs[1, 0])
    ax_top = fig.add_subplot(gs[0, 0], sharex=ax)
    ax_right = fig.add_subplot(gs[1, 1], sharey=ax)

    xmin, xmax, ymax = e["xmin"], e["xmax"], 100.0
    cmap = LinearSegmentedColormap.from_list(
        "arvor",
        [FUNDO1, "#163a63", "#1f6f87", "#2a9ab0", "#5fd3e6", "#f0c86b", "#ff8a7a"],
    )
    hb = ax.hexbin(
        x,
        y,
        gridsize=(78, 60),
        extent=(xmin, xmax, 0, ymax),
        norm=LogNorm(vmin=1),
        cmap=cmap,
        linewidths=0.15,
        edgecolors="#060b1a",
    )

    # Contornos de densidade sobre histograma 2D suavizado
    h, xe, ye = np.histogram2d(x, y, bins=[120, 100], range=[[xmin, xmax], [0, ymax]])
    k = np.exp(-0.5 * (np.arange(-6, 7) / 2.2) ** 2)
    k = k / k.sum()
    hs = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, h)
    hs = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, hs)
    niveis = np.quantile(hs[hs > 0], [0.80, 0.90, 0.96, 0.99])
    ax.contour(
        (xe[:-1] + xe[1:]) / 2,
        (ye[:-1] + ye[1:]) / 2,
        hs.T,
        levels=niveis,
        colors=["#f4f0e6"],
        linewidths=[0.6, 0.8, 1.0, 1.2],
        alpha=0.55,
    )

    ax.fill_between(
        geral["x"],
        geral["q1"],
        geral["q3"],
        color=OURO,
        alpha=0.16,
        lw=0,
        label=f"faixa interquartil por faixa de {e['nome']}",
    )
    ax.plot(
        geral["x"],
        geral["media"],
        color=OURO,
        lw=2.8,
        marker="o",
        ms=4.5,
        mec=FUNDO,
        label="média de Lula por faixa de 2,5 pontos",
    )
    xs = np.array([xmin, xmax])
    ax.plot(
        xs,
        a + b * xs,
        color="#f4f0e6",
        lw=1.4,
        ls="--",
        alpha=0.9,
        label=f"mínimos quadrados: y = {pt(a)} {pt(b, 2, sinal=True)}·x",
    )
    ax.axhline(np.average(y, weights=w), color=LULA, lw=1.0, ls=":", alpha=0.9)
    ax.text(
        xmax - 0.6,
        np.average(y, weights=w) + 1.2,
        f"Lula no país: {pt(np.average(y, weights=w))}%",
        color=LULA,
        ha="right",
        fontsize=9.5,
    )
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(0, ymax)
    ax.set_xlabel(e["rotulo"], fontsize=12, labelpad=8)
    ax.set_ylabel("Lula na seção, % dos votos válidos", fontsize=12, labelpad=8)
    ax.grid(color=LINHA, lw=0.5, alpha=0.6)
    ax.tick_params(labelsize=10)
    ax.legend(
        loc="upper right",
        frameon=True,
        facecolor=FUNDO,
        edgecolor=LINHA,
        fontsize=9.5,
        labelcolor=TINTA,
    )

    # Histogramas marginais
    ax_top.hist(x, bins=np.arange(xmin, xmax + 0.5, 0.5), color=TEAL, alpha=0.85, lw=0)
    ax_top.axvline(np.average(x, weights=w), color=OURO, lw=1.4, ls="--")
    ax_top.text(
        np.average(x, weights=w) + 0.6,
        ax_top.get_ylim()[1] * 0.82,
        f"média {pt(np.average(x, weights=w))}%",
        color=OURO,
        fontsize=9.5,
    )
    ax_top.tick_params(labelbottom=False, labelsize=9)
    ax_top.set_ylabel("seções", fontsize=10, color=SUAVE)
    ax_top.grid(color=LINHA, lw=0.5, alpha=0.6)
    ax_right.hist(
        y,
        bins=np.arange(0, ymax + 1, 1),
        orientation="horizontal",
        color=LULA,
        alpha=0.85,
        lw=0,
    )
    ax_right.tick_params(labelleft=False, labelsize=9)
    ax_right.set_xlabel("seções", fontsize=10, color=SUAVE)
    ax_right.grid(color=LINHA, lw=0.5, alpha=0.6)
    for a_ in (ax_top, ax_right):
        for s in ("top", "right"):
            a_.spines[s].set_visible(False)

    # Barra de cor
    cax = fig.add_axes([0.80, 0.885, 0.175, 0.016])
    cb = fig.colorbar(hb, cax=cax, orientation="horizontal")
    cb.set_label(
        "seções por célula (escala log)", color=SUAVE, fontsize=8.5, labelpad=3
    )
    cb.ax.tick_params(labelsize=8, colors=SUAVE)
    cb.outline.set_edgecolor(LINHA)

    # Painel inferior: curvas por região e quadro de números
    axr = fig.add_axes((0.075, 0.085, 0.49, 0.1))
    for nome, info in regioes.items():
        c = info["curva"]
        axr.plot(
            c["x"],
            c["media"],
            color=COR_REGIAO[nome],
            lw=2.0,
            label=f"{nome} (r = {pt(info['r'], 2, sinal=True)})",
        )
    axr.set_xlim(xmin, xmax)
    axr.set_ylim(0, 100)
    axr.set_yticks([0, 50, 100])
    axr.tick_params(labelsize=8.5)
    axr.grid(color=LINHA, lw=0.5, alpha=0.6)
    axr.set_title(
        f"Média de Lula por faixa de {e['nome']}, por região",
        fontsize=10,
        color=TINTA,
        loc="left",
        pad=4,
    )
    axr.legend(
        ncol=3,
        fontsize=8,
        frameon=False,
        labelcolor=TINTA,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
    )

    texto = "\n".join(
        [
            f"Pearson r = {pt(r, 3, sinal=True)} (seções com peso igual)",
            f"Pearson r = {pt(rw, 3, sinal=True)} (ponderado por aptos)",
            f"n = {milhar(len(x))} seções com {APTOS_MIN}+ aptos, exterior fora",
            (
                f"r² = {pt(r * r, 3)}: o {e['nome']} explica {pt(100 * r * r, 1)}% da variação"
                if eixo == "comparecimento"
                else f"r² = {pt(r * r, 3)}: a abstenção explica {pt(100 * r * r, 1)}% da variação"
            ),
            "do voto em Lula entre seções",
        ]
    )
    fig.text(
        0.60,
        0.19,
        texto,
        fontsize=10,
        color=TINTA,
        va="top",
        family=MONO,
        linespacing=1.6,
        bbox={"boxstyle": "round,pad=0.6", "facecolor": FUNDO1, "edgecolor": LINHA},
    )

    fig.text(
        0.075,
        0.955,
        e["titulo"],
        fontsize=24,
        fontweight="bold",
        color=TINTA,
        va="top",
    )
    fig.text(
        0.075,
        0.915,
        "1º turno de 2026 · cada ponto é uma seção eleitoral · boletins de urna do TSE lidos pelo Politize sua vizinhança",
        fontsize=11,
        color=SUAVE,
        va="top",
    )
    fig.text(
        0.075,
        0.012,
        "Fonte: TSE, boletins de urna por seção, totalização de 05/10/2026; Lula em % dos válidos; eixo x em % dos aptos; seções com 50+ aptos.\n"
        f"Correlação não é causa: {e['nota']}, e dentro de cada região o sinal é outro; a leitura por região separa os dois efeitos.",
        fontsize=8.2,
        color=SUAVE,
        va="bottom",
        linespacing=1.5,
    )
    fig.text(
        0.975,
        0.012,
        "brasil.arvor.co",
        fontsize=9,
        color=TEAL,
        va="top",
        ha="right",
        family=MONO,
    )

    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=200)
    plt.close(fig)
    return {
        "n": len(x),
        "aptos_min": APTOS_MIN,
        "pearson": r,
        "pearson_ponderado": rw,
        "ols": {"intercepto": float(a), "inclinacao": float(b)},
        "abst_media_pond": float(np.average(x, weights=w)),
        "lula_medio_pond": float(np.average(y, weights=w)),
        "curva_geral": {k: v.tolist() for k, v in geral.items()},
        "regioes": {
            nome: {
                "r": info["r"],
                "n": info["n"],
                "abst_media": info["abst_media"],
                "lula_medio": info["lula_medio"],
                "curva": {k: v.tolist() for k, v in info["curva"].items()},
            }
            for nome, info in regioes.items()
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("--eixo", choices=sorted(EIXO), default="abstencao")
    args = parser.parse_args(argv)
    png, saida_json = SAIDAS[args.eixo]
    d = carregar(args.eixo)
    saida = desenhar(d, args.eixo)
    saida["eixo"] = args.eixo
    saida_json.write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        f"{png.relative_to(ROOT)}: n={saida['n']} r={saida['pearson']:+.3f} "
        f"r_pond={saida['pearson_ponderado']:+.3f}"
    )
    for nome, info in saida["regioes"].items():
        print(
            f"  {nome}: r={info['r']:+.3f} n={info['n']} x={info['abst_media']:.1f} "
            f"lula={info['lula_medio']:.1f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
