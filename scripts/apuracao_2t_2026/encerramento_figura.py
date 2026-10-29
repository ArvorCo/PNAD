"""Prancha editorial em PNG/PDF, derivada dos BUs e dos cômputos auditáveis dos logs."""

from __future__ import annotations

import os
from pathlib import Path

from .encerramento_dados import ROOT

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/encerramento_2t_2026/mpl"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

PAPEL = "#f5f2e9"
INK = "#182f2a"
MUTED = "#53635c"
VERDE = "#227c68"
ABERTAS = "#d7ddd4"
FLAVIO = "#2356a0"
LULA = "#b7403e"
FONTES = Path.home() / ".codex/skills/canvas-design/canvas-fonts"
FONT = {
    "sans": "InstrumentSans-Regular.ttf",
    "bold": "InstrumentSans-Bold.ttf",
    "title": "BricolageGrotesque-Bold.ttf",
    "mono": "GeistMono-Regular.ttf",
}
W, H, DPI = 2800, 3200, 200


def numero(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def pct(v: float, casas: int = 2) -> str:
    if 0 < v < 10 ** (-casas):
        return "<" + f"{10 ** (-casas):.{casas}f}".replace(".", ",") + "%"
    if v < 100 and round(v, casas) == 100:
        return ">" + f"{100 - 10 ** (-casas):.{casas}f}".replace(".", ",") + "%"
    return f"{v:.{casas}f}".replace(".", ",") + "%"


def desenhar(d: dict, saida: Path):
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=PAPEL)
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, W), ylim=(H, 0))
    ax.set_axis_off()
    textos = []

    def t(x, y, texto, size=28, cor=INK, font="sans", align="left"):
        artist = ax.text(
            x,
            y,
            texto,
            fontsize=size * 72 / DPI,
            color=cor,
            fontproperties=FontProperties(fname=FONTES / FONT[font]),
            ha=align,
            va="top",
            linespacing=1.25,
        )
        textos.append(artist)
        return artist

    def rect(x, y, w, h, cor):
        ax.add_patch(Rectangle((x, y), w, h, color=cor, linewidth=0))

    def line(x0, y, x1, cor="#d1d7ce", lw=1):
        ax.plot([x0, x1], [y, y], color=cor, linewidth=lw * 72 / DPI)

    # A hierarquia acompanha a pergunta: volume primeiro, composição depois.
    t(90, 65, "ARVOR  /  DADOS ELEITORAIS", 28, font="bold")
    t(2710, 65, "2º TURNO · 25 OUT 2026 · BRASIL SEM EXTERIOR", 25, align="right")
    rect(90, 125, 85, 9, VERDE)
    r10 = d["linhas"][10]
    t(90, 163, "Em dez minutos,", 88, font="title")
    t(90, 262, f"{pct(r10['encerradas_pct'])} já tinham encerrado.", 88, font="title")
    t(
        90,
        382,
        "O encerramento das seções, segundo o horário registrado no boletim de urna.",
        34,
    )
    t(
        90,
        434,
        f"{numero(d['total']['secoes'])} seções · fusos convertidos para Brasília (UTC−3) · precisão de segundos",
        29,
        MUTED,
    )

    # Três marcos explicam por que 17:02 não é uma divisão natural do processo.
    marcos = [(2, 90, "ATÉ 17h02"), (14, 990, "ATÉ 17h30"), (19, 1890, "APÓS 19h00")]
    for i, x, label in marcos:
        r = d["linhas"][i]
        value = r["restantes_pct"] if i == 19 else r["encerradas_pct"]
        count = r["restantes"] if i == 19 else r["encerradas_acumuladas"]
        t(x, 525, label, 25, MUTED, "bold")
        t(x, 564, pct(value), 66, VERDE, "title")
        t(x + 270, 585, f"{numero(count)} seções", 28)
    line(90, 670, 2710, INK, 2)

    # Três medidas distintas, com o intervalo impresso em todas as linhas.
    t(90, 700, "01 / ACUMULADO DE SEÇÕES", 27, font="bold")
    t(1420, 700, "03 / SEÇÕES QUE ENCERRARAM NO INTERVALO", 27, font="bold")
    t(1010, 700, "02 / LOGS", 27, font="bold")
    t(1010, 751, "Todas as seções cobertas", 22, MUTED)
    t(1250, 808, "VOTOS NO INTERVALO", 22, MUTED, "bold", "right")
    t(1250, 843, "e % acumulada nos logs", 20, MUTED, align="right")
    rect(330, 756, 20, 20, VERDE)
    t(362, 751, "encerradas", 25)
    rect(533, 756, 20, 20, ABERTAS)
    t(565, 751, "ainda sem encerramento", 25)
    t(90, 808, "CORTE EXATO", 24, MUTED, "bold")
    t(330, 808, "PROPORÇÃO DO TOTAL", 24, MUTED, "bold")
    t(950, 808, "RESTANTES", 24, MUTED, "bold", "right")
    t(1500, 808, "SEÇÕES", 24, MUTED, "bold", "right")
    t(1730, 808, "COMPARECIMENTO", 20, MUTED, "bold", "right")
    t(1940, 808, "VÁLIDOS", 24, MUTED, "bold", "right")
    t(1990, 808, "FLÁVIO", 24, FLAVIO, "bold")
    t(2380, 808, "LULA", 24, LULA, "bold", "right")
    t(2450, 808, "PRINCIPAIS UFs", 24, MUTED, "bold")
    t(2450, 843, "% das seções da linha", 20, MUTED)
    t(1730, 843, "pessoas e % dos aptos", 20, MUTED, align="right")
    t(2380, 843, "% e votos do dia inteiro", 20, MUTED, align="right")
    line(90, 888, 2710, INK)

    y0, passo = 914, 88
    for i, r in enumerate(d["linhas"]):
        y = y0 + i * passo
        if i in {2, 10, 14, 19}:
            rect(75, y - 9, 2650, passo - 1, "#e5ece2")
        elif i % 2 == 0:
            rect(75, y - 9, 2650, passo - 1, "#eeeee5")
        tail = r["corte_s"] is None
        label = "Após 19h00" if tail else r["hora"][:5].replace(":", "h")
        t(90, y, label, 34, font="bold")
        if i == 0:
            detalhe = "até 17:00:00"
        elif tail:
            detalhe = "> 19:00:00"
        else:
            prev = d["linhas"][i - 1]["hora"][:5]
            detalhe = f"{prev} a {r['hora'][:5]}"
        t(90, y + 47, detalhe, 22, MUTED)
        if tail:
            t(330, y + 4, "Todos os encerramentos", 29, VERDE, "bold")
        else:
            rect(330, y + 7, 420, 29, ABERTAS)
            rect(330, y + 7, 420 * r["encerradas_pct"] / 100, 29, VERDE)
        t(330, y + 47, pct(r["encerradas_pct"]), 28, VERDE, "bold")
        t(750, y + 47, f"{pct(r['restantes_pct'])} restantes", 23, MUTED, align="right")
        t(950, y + 4, numero(r["restantes"]), 30, font="mono", align="right")
        t(
            1250,
            y + 4,
            numero(r["logs_computados_intervalo"]),
            30,
            "#785139",
            "mono",
            "right",
        )
        t(
            1250,
            y + 47,
            pct(r["logs_computados_acumulados_pct"], 3) + " acum.",
            23,
            "#785139",
            align="right",
        )
        t(1500, y + 4, numero(r["secoes"]), 30, font="mono", align="right")
        t(1500, y + 47, pct(r["parcela_secoes_pct"]), 23, MUTED, align="right")
        t(1730, y + 4, numero(r["comparecimento"]), 30, font="mono", align="right")
        t(
            1730,
            y + 47,
            (
                pct(r["comparecimento_pct"])
                if r["comparecimento_pct"] is not None
                else "n/a"
            ),
            23,
            MUTED,
            align="right",
        )
        t(1940, y + 4, numero(r["validos"]), 30, font="mono", align="right")
        if r["validos"]:
            f = r["flavio_pct"]
            rect(1990, y + 40, 390 * f / 100, 7, FLAVIO)
            rect(1990 + 390 * f / 100, y + 40, 390 * (100 - f) / 100, 7, LULA)
            t(1990, y, pct(f), 30, FLAVIO, "bold")
            t(2380, y, pct(r["lula_pct"]), 30, LULA, "bold", "right")
            t(1990, y + 53, numero(r["flavio"]), 23, FLAVIO, "mono")
            t(2380, y + 53, numero(r["lula"]), 23, LULA, "mono", "right")
        else:
            t(1990, y + 6, "Nenhuma seção", 27, MUTED)
        for j, u in enumerate(r["ufs"][:3]):
            t(2450, y - 1 + j * 26, f"{u['uf']}  {pct(u['pct'], 1)}", 23, MUTED, "mono")
    fim = y0 + len(d["linhas"]) * passo
    line(90, fim + 4, 2710, INK, 2)
    t(90, fim + 31, "COMO LER", 25, font="bold")
    t(
        330,
        fim + 28,
        "A barra acumula seções. A coluna de logs conta os votos computados naquele intervalo, em todas as seções cobertas.",
        29,
    )
    t(
        330,
        fim + 73,
        "Cortes em HH:MM:00. Cada intervalo exclui o início e inclui o fim. As durações dos intervalos variam.",
        27,
    )
    t(90, fim + 138, "DOIS RELÓGIOS, DUAS MEDIDAS", 27, font="bold")
    t(
        90,
        fim + 182,
        "Logs: cômputos no horário, sem candidato identificado. BU: placar do dia inteiro nas seções que encerraram na faixa.",
        29,
    )
    t(
        90,
        fim + 226,
        f"Logs utilizáveis: {numero(d['logs']['cobertas'])} seções ({pct(d['logs']['cobertura_secoes_pct'])}); {numero(d['logs']['computados'])} cômputos ({pct(d['logs']['cobertura_comparecimento_pct'])} do comparecimento).",
        29,
    )
    t(
        90,
        3090,
        "Fonte: BUs e logs do TSE · seções principais, sem duplicar agregadas · logs não medem chegada à fila nem transmissão ao TSE",
        24,
        MUTED,
    )
    t(90, 3136, "ARVOR / BRASIL.ARVOR.CO", 24, font="bold")
    t(
        2710,
        3136,
        "Dados e reprodução: github.com/ArvorCo/PNAD · 29 out 2026",
        23,
        MUTED,
        align="right",
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for artist in textos:
        box = artist.get_window_extent(renderer)
        if box.x0 < 50 or box.x1 > W - 50 or box.y0 < 25 or box.y1 > H - 25:
            raise ValueError(f"Texto fora das margens: {artist.get_text()}")
    for ext in ("png", "pdf"):
        fig.savefig(saida / f"encerramento-2t-2026.{ext}", dpi=DPI, facecolor=PAPEL)
    plt.close(fig)
