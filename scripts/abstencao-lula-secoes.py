#!/usr/bin/env python3
"""Abstenção × voto em Lula por seção eleitoral em 2026 (1º e 2º turnos): dispersão, curvas e histogramas.

Lê as seções do Politize (`docs/assets/politize/dados/zona/<UF>/<zona>.json`: aptos, comparecimento
em contagem, Lula em % dos válidos), exclui o exterior e seções com menos de `APTOS_MIN` aptos,
e desenha um gráfico conjunto: densidade (hexbin) de x = abstenção (% dos aptos) por y = Lula
(% dos válidos), curva de médias por faixa de abstenção com faixa interquartil, reta de mínimos
quadrados, histogramas marginais, Pearson simples e ponderado por aptos, e as curvas por região.

Saída: `docs/img/abstencao_lula_secoes_1t.png` (2400×2400) e `analysis/apuracao_2026/abstencao_lula_secoes.json`.

Com `--turno 2` a fonte é o banco de boletins do 2º turno (`apuracao/data/secoes_2t_2026.sqlite`, aberto
só para leitura, inclusive com a coleta em andamento): Lula em % dos votos nominais (Lula + Flávio), mesmos
filtros do 1º turno. Grava `docs/img/<eixo>_lula_secoes_2t.png`, o JSON em `analysis/apuracao_2t_2026/dados/`
com `cobertura`, `gerado_em` e o 1º turno recalculado nas mesmas seções, as versões de 1200 px em
`docs/img/apuracao_2t/` e, no eixo comparecimento, o painel da variação 2T menos 1T na mesma seção.

Uso: python3 scripts/abstencao-lula-secoes.py [--eixo abstencao|comparecimento] [--turno 1|2]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
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
REGIAO_MIN = 200

BANCO_2T = ROOT / "apuracao" / "data" / "secoes_2t_2026.sqlite"
DADOS_2T = ROOT / "analysis" / "apuracao_2t_2026" / "dados"
IMG = ROOT / "docs" / "img"
REDUZIDAS = IMG / "apuracao_2t"
LARGURA_REDUZIDA = 1200
LULA_NUM, FLAVIO_NUM = 13, 22

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


def desenhar(
    d: dict[str, np.ndarray],
    eixo: str,
    txt: dict | None = None,
    png: Path | None = None,
) -> dict:
    e = EIXO[eixo]
    png = png or SAIDAS[eixo][0]
    txt = txt or textos_1t(eixo)
    x, y, w, uf = d["abst"], d["lula"], d["aptos"], d["uf"]
    r = pearson(x, y)
    rw = pearson(x, y, w)
    b, a = np.polyfit(x, y, 1)
    bordas = np.arange(e["xmin"], e["xmax"] + 0.01, 2.5)
    geral = curva(x, y, bordas)
    regioes = {}
    for nome in REGIAO:
        sel = np.isin(uf, REGIAO[nome].split())
        if sel.sum() < REGIAO_MIN:
            regioes[nome] = {"curva": None, "r": None, "n": int(sel.sum())}
            regioes[nome].update(abst_media=None, lula_medio=None)
            continue
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
        f"{txt['lula_rotulo']}: {pt(np.average(y, weights=w))}%",
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
        if c is None:
            continue
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
        txt["titulo"],
        fontsize=24,
        fontweight="bold",
        color=TINTA,
        va="top",
    )
    fig.text(
        0.075,
        0.915,
        txt["subtitulo"],
        fontsize=11,
        color=SUAVE,
        va="top",
    )
    fig.text(
        0.075,
        0.012,
        txt["rodape"],
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

    if txt.get("selo"):
        fig.text(
            0.975,
            0.955,
            txt["selo"],
            fontsize=11,
            fontweight="bold",
            color=FUNDO,
            va="top",
            ha="right",
            family=MONO,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": OURO, "edgecolor": OURO},
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
                "curva": (
                    {k: v.tolist() for k, v in info["curva"].items()}
                    if info["curva"] is not None
                    else None
                ),
            }
            for nome, info in regioes.items()
        },
    }


def textos_1t(eixo: str) -> dict:
    e = EIXO[eixo]
    return {
        "titulo": e["titulo"],
        "subtitulo": "1º turno de 2026 · cada ponto é uma seção eleitoral · boletins de urna do TSE lidos pelo Politize sua vizinhança",
        "rodape": "Fonte: TSE, boletins de urna por seção, totalização de 05/10/2026; Lula em % dos válidos; eixo x em % dos aptos; seções com 50+ aptos.\n"
        f"Correlação não é causa: {e['nota']}, e dentro de cada região o sinal é outro; a leitura por região separa os dois efeitos.",
        "lula_rotulo": "Lula no país",
    }


def politize_indice() -> dict[tuple[str, str, int, int], tuple]:
    """Seções do 1º turno no Politize: (UF, município TSE, zona, seção) -> (aptos, comparecimento, Lula % válidos, Lula, Flávio)."""
    idx = {}
    for pasta in sorted(ZONAS.iterdir()):
        if pasta.name == "ZZ" or not pasta.is_dir():
            continue
        for arquivo in sorted(pasta.glob("*.json")):
            z = json.loads(arquivo.read_text(encoding="utf-8"))
            col = {c: i for i, c in enumerate(z["secoes"]["colunas"])}
            for r in z["secoes"]["linhas"]:
                chave = (pasta.name, r[col["mun_tse"]], int(z["zona"]), r[col["secao"]])
                idx[chave] = (
                    r[col["aptos"]] or 0,
                    r[col["comparecimento"]],
                    r[col["lula_v"]],
                    r[col["lula"]],
                    r[col["flavio"]],
                )
    return idx


def carregar_2t(eixo: str) -> tuple[dict[str, np.ndarray], dict]:
    """Boletins do 2º turno no banco da casa (só leitura). Exclui exterior, agregadas e seções pequenas."""
    con = sqlite3.connect(f"file:{BANCO_2T}?mode=ro", uri=True)
    sql = f"""
        SELECT b.uf, b.mun, b.zona, b.secao, b.aptos, b.comparecimento,
               SUM(CASE WHEN v.numero = {LULA_NUM} THEN v.votos ELSE 0 END),
               SUM(CASE WHEN v.numero = {FLAVIO_NUM} THEN v.votos ELSE 0 END)
        FROM bu b
        JOIN secao s USING (uf, mun, zona, secao)
        LEFT JOIN voto_secao v
          ON v.uf = b.uf AND v.mun = b.mun AND v.zona = b.zona AND v.secao = b.secao
         AND v.cargo = 1 AND v.tipo = 1
        WHERE s.nsp IS NULL AND b.uf <> 'zz'
        GROUP BY b.uf, b.mun, b.zona, b.secao
    """
    linhas = con.execute(sql).fetchall()
    total_cs = con.execute(
        "SELECT COUNT(*) FROM secao WHERE nsp IS NULL AND uf <> 'zz'"
    ).fetchone()[0]
    con.close()
    x, y, w, uf_l, chaves = [], [], [], [], []
    por_uf: dict[str, int] = {}
    for uf, mun, zona, secao, a, comp, lu, fl in linhas:
        uf = uf.upper()
        por_uf[uf] = por_uf.get(uf, 0) + 1
        a = a or 0
        if a < APTOS_MIN or comp is None or (lu or 0) + (fl or 0) == 0:
            continue
        x.append(100.0 * (a - comp) / a if eixo == "abstencao" else 100.0 * comp / a)
        y.append(100.0 * lu / (lu + fl))
        w.append(float(a))
        uf_l.append(uf)
        chaves.append((uf, mun, int(zona), int(secao), a, comp, lu, fl))
    d = {
        "abst": np.array(x),
        "lula": np.array(y),
        "aptos": np.array(w),
        "uf": np.array(uf_l),
    }
    meta = {
        "lidas": len(linhas),
        "total_cs": total_cs,
        "por_uf": por_uf,
        "chaves": chaves,
    }
    return d, meta


def cobertura(meta: dict, idx: dict) -> dict:
    total_uf: dict[str, int] = {}
    for uf, *_ in idx:
        total_uf[uf] = total_uf.get(uf, 0) + 1
    total = sum(total_uf.values())
    ufs = sorted(meta["por_uf"])
    regioes = {
        nome: {
            "lidas": sum(meta["por_uf"].get(u, 0) for u in ufs_.split()),
            "total_1t": sum(total_uf.get(u, 0) for u in ufs_.split()),
        }
        for nome, ufs_ in REGIAO.items()
    }
    pct_ = 100.0 * meta["lidas"] / total if total else 0.0
    return {
        "secoes_lidas": meta["lidas"],
        "secoes_total_1t": total,
        "pct": pct_,
        "secoes_no_cadastro_2t": meta["total_cs"],
        "parcial": pct_ < 99.5,
        "ufs_lidas": ufs,
        "por_uf": {
            u: {"lidas": meta["por_uf"].get(u, 0), "total_1t": total_uf.get(u, 0)}
            for u in sorted(total_uf)
        },
        "por_regiao": regioes,
        "nota": (
            "Boletins do 2º turno coletados até a hora de geração; a coleta avança por UF, então a amostra "
            "parcial não é aleatória e o número nacional pesa mais as UFs já lidas."
        ),
    }


def resumo_1t_mesmas(meta: dict, idx: dict, eixo: str) -> dict:
    """Mesmas estatísticas do 1º turno, só nas seções do 2º turno já lidas (Lula em % dos válidos, como no 1T)."""
    x, y, y2, w, uf_l = [], [], [], [], []
    for uf, mun, zona, secao, *_ in meta["chaves"]:
        v = idx.get((uf, mun, zona, secao))
        if v is None:
            continue
        a, comp, lv, lu, fl = v
        if a < APTOS_MIN or comp is None or lv is None or not (lu or 0) + (fl or 0):
            continue
        x.append(100.0 * (a - comp) / a if eixo == "abstencao" else 100.0 * comp / a)
        y.append(float(lv))
        y2.append(100.0 * lu / (lu + fl))
        w.append(float(a))
        uf_l.append(uf)
    xa, ya, ya2, wa, ua = map(np.array, (x, y, y2, w, uf_l))
    b2, a2 = np.polyfit(xa, ya2, 1)
    b, a_ = np.polyfit(xa, ya, 1)
    reg = {}
    for nome, ufs in REGIAO.items():
        sel = np.isin(ua, ufs.split())
        reg[nome] = {
            "n": int(sel.sum()),
            "r": pearson(xa[sel], ya[sel]) if sel.sum() >= REGIAO_MIN else None,
        }
    return {
        "n": len(xa),
        "pearson": pearson(xa, ya),
        "pearson_ponderado": pearson(xa, ya, wa),
        "ols": {"intercepto": float(a_), "inclinacao": float(b)},
        "abst_media_pond": float(np.average(xa, weights=wa)),
        "lula_medio_pond": float(np.average(ya, weights=wa)),
        "regioes": reg,
        "lula_entre_finalistas": {
            "definicao": "Lula em % de Lula + Flávio no 1º turno, mesma régua do 2º",
            "pearson": pearson(xa, ya2),
            "pearson_ponderado": pearson(xa, ya2, wa),
            "ols": {"intercepto": float(a2), "inclinacao": float(b2)},
        },
    }


def nota_regional(regioes: dict, eixo: str, r_nac: float) -> str:
    """Frase do rodapé gerada dos números: qual região lidera cada eixo e onde o sinal inverte."""
    val = {k: v for k, v in regioes.items() if v.get("r") is not None}
    if len(val) < 2:
        return "há regiões demais sem dados para separar o efeito regional"
    ry = max(val, key=lambda k: val[k]["lula_medio"])
    if eixo == "comparecimento":
        rx = max(val, key=lambda k: val[k]["abst_media"])
        frase = (
            f"o {ry} tem mais comparecimento e mais Lula"
            if rx == ry
            else (f"a região de mais comparecimento ({rx}) não é a de mais Lula ({ry})")
        )
    else:
        rx = min(val, key=lambda k: val[k]["abst_media"])
        frase = (
            f"o {ry} tem menos abstenção e mais Lula"
            if rx == ry
            else (f"a região de menos abstenção ({rx}) não é a de mais Lula ({ry})")
        )
    opostas = [k for k, v in val.items() if np.sign(v["r"]) != np.sign(r_nac)]
    if opostas:
        return (
            frase
            + f", e dentro {' e '.join('do ' + k for k in opostas)} o sinal é outro"
        )
    return (
        frase
        + ", e dentro de cada região a força da relação muda; a leitura por região separa os dois efeitos"
    )


def textos_2t(eixo: str, cob: dict, gerado: str, regioes: dict, r: float) -> dict:
    e = EIXO[eixo]
    hora = gerado[11:16]
    parcial = cob["parcial"]
    ausentes = [k for k, v in cob["por_regiao"].items() if v["lidas"] == 0]
    sub = "2º turno de 2026 · cada ponto é uma seção eleitoral · boletins de urna do TSE lidos pelo banco da casa"
    if parcial:
        sub = (
            f"2º turno de 2026 · cobertura parcial e não aleatória (coleta por UF): {milhar(cob['secoes_lidas'])} de "
            f"{milhar(cob['secoes_total_1t'])} seções ({pt(cob['pct'])}%) em {len(cob['ufs_lidas'])} UFs"
            + (f", sem {', '.join(ausentes)}" if ausentes else "")
        )
    return {
        "titulo": e["titulo"],
        "subtitulo": sub,
        "rodape": f"Fonte: TSE, boletins de urna do 2º turno por seção, lidos até {gerado[8:10]}/{gerado[5:7]} às {hora}; "
        "Lula em % dos votos nominais; eixo x em % dos aptos; 50+ aptos.\n"
        f"Correlação não é causa: {nota_regional(regioes, eixo, r)}.",
        "lula_rotulo": "Lula nas seções lidas" if parcial else "Lula no país",
        "selo": f"COBERTURA PARCIAL · {pt(cob['pct'])}%" if parcial else "",
    }


def variacao(meta: dict, idx: dict, cob: dict, gerado: str) -> dict:
    """Painel 2T menos 1T na mesma seção: variação do comparecimento × variação de Lula entre Lula e Flávio."""
    dx, dy, w, uf_l = [], [], [], []
    for uf, mun, zona, secao, a2, c2, lu2, fl2 in meta["chaves"]:
        v = idx.get((uf, mun, zona, secao))
        if v is None:
            continue
        a1, c1, _, lu1, fl1 = v
        if a1 < APTOS_MIN or c1 is None or not lu1 or not fl1:
            continue
        dx.append(100.0 * c2 / a2 - 100.0 * c1 / a1)
        dy.append(100.0 * lu2 / (lu2 + fl2) - 100.0 * lu1 / (lu1 + fl1))
        w.append(float(a2))
        uf_l.append(uf)
    x, y, w, uf = map(np.array, (dx, dy, w, uf_l))
    r, rw = pearson(x, y), pearson(x, y, w)
    b, a = np.polyfit(x, y, 1)
    bordas = np.arange(-15.0, 15.01, 1.0)
    geral = curva(x, y, bordas, minimo=150)
    reg = {}
    for nome, ufs in REGIAO.items():
        sel = np.isin(uf, ufs.split())
        if sel.sum() < REGIAO_MIN:
            reg[nome] = {"n": int(sel.sum()), "r": None}
            continue
        reg[nome] = {
            "n": int(sel.sum()),
            "r": pearson(x[sel], y[sel]),
            "dcomp_medio": float(np.average(x[sel], weights=w[sel])),
            "dlula_medio": float(np.average(y[sel], weights=w[sel])),
        }
    quad = {
        "comp_sobe_lula_sobe": float(np.mean((x > 0) & (y > 0)) * 100),
        "comp_sobe_lula_cai": float(np.mean((x > 0) & (y < 0)) * 100),
        "comp_cai_lula_sobe": float(np.mean((x < 0) & (y > 0)) * 100),
        "comp_cai_lula_cai": float(np.mean((x < 0) & (y < 0)) * 100),
        "lula_sobe": float(np.mean(y > 0) * 100),
        "lula_sobe_onde_comp_sobe": float(np.mean(y[x > 0] > 0) * 100),
        "lula_sobe_onde_comp_cai": float(np.mean(y[x < 0] > 0) * 100),
        "comp_sobe": float(np.mean(x > 0) * 100),
    }

    fig = plt.figure(figsize=(12, 10), dpi=200)
    ax = fig.add_axes((0.085, 0.14, 0.86, 0.68))
    cmap = LinearSegmentedColormap.from_list(
        "arvor",
        [FUNDO1, "#163a63", "#1f6f87", "#2a9ab0", "#5fd3e6", "#f0c86b", "#ff8a7a"],
    )
    hb = ax.hexbin(
        x,
        y,
        gridsize=(70, 60),
        extent=(-15, 15, -15, 15),
        norm=LogNorm(vmin=1),
        cmap=cmap,
        linewidths=0.15,
        edgecolors=FUNDO,
    )
    ax.axhline(0, color=SUAVE, lw=0.8)
    ax.axvline(0, color=SUAVE, lw=0.8)
    ax.fill_between(geral["x"], geral["q1"], geral["q3"], color=OURO, alpha=0.16, lw=0)
    ax.plot(
        geral["x"],
        geral["media"],
        color=OURO,
        lw=2.8,
        marker="o",
        ms=4.5,
        mec=FUNDO,
        label="média da variação de Lula por faixa de 1 ponto",
    )
    xs = np.array([-15.0, 15.0])
    ax.plot(
        xs,
        a + b * xs,
        color="#f4f0e6",
        lw=1.4,
        ls="--",
        label=f"mínimos quadrados: y = {pt(a, 2, sinal=True)} {pt(b, 2, sinal=True)}·x",
    )
    ax.set_xlim(-15, 15)
    ax.set_ylim(-15, 15)
    ax.set_xlabel(
        "Variação do comparecimento na seção, 2º turno menos 1º, pontos", fontsize=12
    )
    ax.set_ylabel("Variação de Lula entre Lula e Flávio, pontos", fontsize=12)
    ax.grid(color=LINHA, lw=0.5, alpha=0.6)
    ax.legend(
        loc="upper left",
        facecolor=FUNDO,
        edgecolor=LINHA,
        fontsize=9.5,
        labelcolor=TINTA,
    )
    cax = fig.add_axes([0.77, 0.865, 0.175, 0.016])
    cb = fig.colorbar(hb, cax=cax, orientation="horizontal")
    cb.set_label(
        "seções por célula (escala log)", color=SUAVE, fontsize=8.5, labelpad=3
    )
    cb.ax.tick_params(labelsize=8, colors=SUAVE)
    cb.outline.set_edgecolor(LINHA)
    regs = " · ".join(
        f"{k} r = {pt(v['r'], 2, sinal=True)}"
        for k, v in reg.items()
        if v["r"] is not None
    )
    fig.text(
        0.62,
        0.20,
        "\n".join(
            [
                f"Pearson r = {pt(r, 3, sinal=True)} (peso igual)",
                f"Pearson r = {pt(rw, 3, sinal=True)} (ponderado por aptos)",
                f"n = {milhar(len(x))} seções casadas",
            ]
        ),
        fontsize=10,
        color=TINTA,
        va="top",
        family=MONO,
        linespacing=1.6,
        bbox={"boxstyle": "round,pad=0.6", "facecolor": FUNDO1, "edgecolor": LINHA},
    )
    fig.text(
        0.085,
        0.965,
        "Mudou o comparecimento, mudou o voto?",
        fontsize=24,
        fontweight="bold",
        va="top",
    )
    fig.text(
        0.085,
        0.92,
        "A mesma seção nos dois turnos de 2026 · Lula em % de Lula + Flávio nos dois turnos",
        fontsize=11,
        color=SUAVE,
        va="top",
    )
    if cob["parcial"]:
        fig.text(
            0.945,
            0.965,
            f"COBERTURA PARCIAL · {pt(cob['pct'])}%",
            fontsize=11,
            fontweight="bold",
            color=FUNDO,
            va="top",
            ha="right",
            family=MONO,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": OURO, "edgecolor": OURO},
        )
    fig.text(
        0.085,
        0.015,
        f"Fonte: TSE, boletins de urna por seção; 1º turno pelo Politize sua vizinhança, 2º turno pelo banco da casa até {gerado[11:16]} de 25/10.\n"
        f"Por região: {regs}. Leitura ecológica: a variação de uma seção não identifica quem passou a votar.",
        fontsize=8.2,
        color=SUAVE,
        va="bottom",
        linespacing=1.5,
    )
    png = IMG / "variacao_comparecimento_lula_secoes_2t.png"
    fig.savefig(png, dpi=200)
    plt.close(fig)
    reduzir(png)
    return {
        "eixo": "variacao",
        "n": len(x),
        "aptos_min": APTOS_MIN,
        "pearson": r,
        "pearson_ponderado": rw,
        "ols": {"intercepto": float(a), "inclinacao": float(b)},
        "dcomp_medio_pond": float(np.average(x, weights=w)),
        "dlula_medio_pond": float(np.average(y, weights=w)),
        "quadrantes_pct": quad,
        "curva_geral": {k: v.tolist() for k, v in geral.items()},
        "regioes": reg,
        "cobertura": cob,
        "gerado_em": gerado,
    }


def reduzir(png: Path) -> Path | None:
    """Versão de 1200 px em JPEG q85 para a página do dossiê."""
    if not png.exists():
        return None
    from PIL import Image

    REDUZIDAS.mkdir(parents=True, exist_ok=True)
    dst = REDUZIDAS / f"{png.stem}.jpg"
    with Image.open(png) as im:
        im = im.convert("RGB")
        im = im.resize(
            (LARGURA_REDUZIDA, round(im.height * LARGURA_REDUZIDA / im.width)),
            Image.LANCZOS,
        )
        im.save(dst, "JPEG", quality=85, optimize=True, progressive=True)
    return dst


def rodar_2t(eixo: str) -> dict:
    gerado = datetime.now().astimezone().isoformat(timespec="seconds")
    d, meta = carregar_2t(eixo)
    idx = politize_indice()
    cob = cobertura(meta, idx)
    png = IMG / f"{eixo}_lula_secoes_2t.png"
    # Primeira passada só para as regiões (o texto do rodapé depende delas), sem desenhar.
    x, y, w, uf = d["abst"], d["lula"], d["aptos"], d["uf"]
    reg = {}
    for nome, ufs in REGIAO.items():
        sel = np.isin(uf, ufs.split())
        reg[nome] = (
            {
                "r": pearson(x[sel], y[sel]),
                "abst_media": float(np.average(x[sel], weights=w[sel])),
                "lula_medio": float(np.average(y[sel], weights=w[sel])),
            }
            if sel.sum() >= REGIAO_MIN
            else {"r": None}
        )
    txt = textos_2t(eixo, cob, gerado, reg, pearson(x, y))
    saida = desenhar(d, eixo, txt, png)
    saida["eixo"] = eixo
    saida["turno"] = 2
    saida["lula_definicao"] = "Lula em % dos votos nominais (Lula + Flávio)"
    saida["cobertura"] = cob
    saida["gerado_em"] = gerado
    saida["nota_rodape"] = txt["rodape"]
    saida["primeiro_turno_mesmas_secoes"] = resumo_1t_mesmas(meta, idx, eixo)
    DADOS_2T.mkdir(parents=True, exist_ok=True)
    (DADOS_2T / f"{eixo}_lula_secoes.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    reduzir(png)
    reduzir(SAIDAS[eixo][0])
    if eixo == "comparecimento":
        var = variacao(meta, idx, cob, gerado)
        (DADOS_2T / "variacao_comparecimento_lula_secoes.json").write_text(
            json.dumps(var, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(
            f"variação: n={var['n']} r={var['pearson']:+.3f} r_pond={var['pearson_ponderado']:+.3f} "
            f"b={var['ols']['inclinacao']:+.3f}"
        )
    print(
        f"cobertura: {cob['secoes_lidas']}/{cob['secoes_total_1t']} ({cob['pct']:.1f}%)"
    )
    return saida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("--eixo", choices=sorted(EIXO), default="abstencao")
    parser.add_argument("--turno", type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    if args.turno == 2:
        saida = rodar_2t(args.eixo)
        png = IMG / f"{args.eixo}_lula_secoes_2t.png"
    else:
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
        if info["r"] is None:
            print(f"  {nome}: sem dados (n={info['n']})")
            continue
        print(
            f"  {nome}: r={info['r']:+.3f} n={info['n']} x={info['abst_media']:.1f} "
            f"lula={info['lula_medio']:.1f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
