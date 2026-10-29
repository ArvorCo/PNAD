"""Prancha de três etapas: panorama proporcional e tabela gráfica integral."""

from __future__ import annotations

from datetime import timedelta
from itertools import pairwise
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

from .encerramento_figura import (
    ABERTAS,
    DPI,
    FLAVIO,
    FONT,
    FONTES,
    INK,
    LULA,
    MUTED,
    PAPEL,
    numero,
    pct,
)
from .supertimeline_dados import BASE

W = 3840
LOG = "#a76328"
FECHO = "#227c68"
TSE = "#70509a"
PALE = "#dedfd5"
XLOG, XFECHO, XTSE = 330, 1030, 2440
LOGW, BUW = 570, 1280
PASSO = 210


def desenhar(d: dict, saida: Path):
    # A primeira faixa fica oculta apenas quando é explicitamente vazia nas três fontes.
    linhas = d["linhas"]
    antes8 = linhas[0]
    vazio = not any(
        [
            antes8["logs"]["intervalo"],
            antes8["fecho"]["secoes"],
            antes8["recebido"]["secoes"],
        ]
    )
    visiveis = linhas[1:] if vazio else linhas
    topo = 1350
    separacoes = 3 * 78
    fim = topo + len(visiveis) * PASSO + separacoes
    H = fim + 980
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=PAPEL)
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, W), ylim=(H, 0))
    ax.set_axis_off()
    textos = []

    def t(x, y, texto, size=30, cor=INK, font="sans", align="left", limite=None):
        a = ax.text(
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
        textos.append((a, limite))
        return a

    def rect(x, y, w, h, cor):
        ax.add_patch(Rectangle((x, y), w, h, linewidth=0, facecolor=cor))

    def linha(y, x0=80, x1=W - 80, cor=PALE, lw=1):
        ax.plot([x0, x1], [y, y], color=cor, linewidth=lw * 72 / DPI)

    def barra(x, y, w, valor, cor, size=30):
        rect(x, y + 5, w - 155, 18, ABERTAS)
        rect(x, y + 5, (w - 155) * valor / 100, 18, cor)
        t(
            x + w,
            y - 3,
            pct(valor, 3 if valor > 99.9 else 2),
            size,
            cor,
            "bold",
            "right",
        )

    def logcard(r, y):
        a = r["logs"]
        barra(XLOG, y, LOGW, a["acumulado_pct"], LOG)
        t(XLOG, y + 37, f"{numero(a['acumulado'])} acumulados", 27, MUTED, limite=LOGW)
        t(XLOG, y + 84, numero(a["intervalo"]), 47, LOG, "mono", limite=LOGW)
        t(XLOG, y + 143, "cômputos nesta faixa", 27, MUTED)

    def bucard(a, x, y, cor, tipo):
        barra(x, y, BUW, a["encerradas_pct"], cor)
        t(
            x,
            y + 35,
            f"{numero(a['encerradas_acumuladas'])} {'acumulada' if a['encerradas_acumuladas'] == 1 else 'acumuladas'} · faltam {numero(a['restantes'])} ({pct(a['restantes_pct'])})",
            27,
            MUTED,
            limite=BUW,
        )
        if tipo == "recebido" and a.get("cronologia_divergente"):
            t(
                x + BUW,
                y + 35,
                f"* {a['cronologia_divergente']} com ordem divergente",
                24,
                MUTED,
                align="right",
                limite=BUW / 2,
            )
        if not a["secoes"]:
            t(x, y + 90, "—  nenhuma seção nesta faixa", 32, MUTED)
            return
        t(
            x,
            y + 73,
            f"{numero(a['secoes'])} {'seção' if a['secoes'] == 1 else 'seções'} ({pct(a['parcela_secoes_pct'])})  ·  {numero(a['validos'])} votos válidos",
            32,
            cor,
            "bold",
            limite=BUW,
        )
        t(
            x,
            y + 113,
            f"Comparecimento: {numero(a['comparecimento'])} ({pct(a['comparecimento_pct'])} dos aptos)",
            27,
            MUTED,
            limite=BUW,
        )
        t(
            x,
            y + 151,
            f"Flávio {pct(a['flavio_pct'])} · {numero(a['flavio'])}",
            28,
            FLAVIO,
            "bold",
            limite=BUW / 2,
        )
        t(
            x + BUW,
            y + 151,
            f"Lula {pct(a['lula_pct'])} · {numero(a['lula'])}",
            28,
            LULA,
            "bold",
            "right",
            limite=BUW / 2,
        )
        # As três UFs seguem junto à própria faixa; nunca escondidas em outra página.
        ufs = "  ·  ".join(f"{u['uf']} {pct(u['pct'], 1)}" for u in a["ufs"][:3])
        t(x + BUW, y + 113, ufs, 25, MUTED, align="right", limite=BUW / 2)

    t(80, 64, "ARVOR  /  DADOS ELEITORAIS", 30, font="bold")
    t(W - 80, 64, "2º TURNO 2026  ·  BRASIL SEM EXTERIOR", 29, align="right")
    rect(80, 125, 85, 9, LOG)
    rect(174, 125, 85, 9, FECHO)
    rect(268, 125, 85, 9, TSE)
    t(80, 167, "Do primeiro voto ao último recebimento.", 108, font="title")
    t(
        80,
        304,
        "Três etapas do mesmo dia: votar, encerrar a seção e receber o resultado no TSE.",
        43,
    )
    t(
        80,
        369,
        "25 → 26 de outubro de 2026  ·  todos os horários em Brasília (UTC−3)  ·  horários originais preservados até o segundo",
        31,
        MUTED,
    )

    for x, cor, valor, label in [
        (
            80,
            LOG,
            numero(d["logs_cobertura"]["computados"]),
            "CÔMPUTOS NOS LOGS UTILIZÁVEIS",
        ),
        (1380, FECHO, numero(d["total"]["secoes"]), "SEÇÕES COM ENCERRAMENTO"),
        (2680, TSE, numero(d["total"]["secoes"]), "PACOTES RECEBIDOS PELO TSE"),
    ]:
        t(x, 455, valor, 63, cor, "title")
        t(x, 535, label, 25, MUTED, "bold")
    t(80, 590, "01 / O DIA INTEIRO", 29, font="bold")
    t(
        570,
        593,
        "Acumulados em % de cada base · logs nos cortes; demais carimbos por segundo",
        29,
        MUTED,
    )
    for x, cor, nome in [
        (2110, LOG, "votos nos logs"),
        (2680, FECHO, "seções encerradas"),
        (3310, TSE, "recebidas"),
    ]:
        rect(x, 598, 30, 10, cor)
        t(x + 45, 590, nome, 29, cor, "bold")
    # Panorama: eventos por segundo para BUs/recebimentos; pontos horários para logs.
    plot = fig.add_axes(
        [150 / W, (H - 1050) / H, (W - 270) / W, 370 / H], facecolor=PAPEL
    )
    for chave, cor in [("fecho", FECHO), ("recebido", TSE)]:
        serie = d["trilhas"][chave]["segundos"]
        xs = [
            8,
            *[s / 3600 for s, _ in serie],
            d["linhas"][-1]["fim_inclusivo_s"] / 3600,
        ]
        ys = [
            0,
            *list(np.cumsum([v for _, v in serie]) * 100 / d["total"]["secoes"]),
            100,
        ]
        plot.step(xs, ys, where="post", color=cor, lw=2.2)
    plot.plot(
        [r["fim_inclusivo_s"] / 3600 for r in linhas],
        [r["logs"]["acumulado_pct"] for r in linhas],
        color=LOG,
        lw=2.4,
        marker="o",
        markersize=2.5,
    )
    plot.set_xlim(8, linhas[-1]["fim_inclusivo_s"] / 3600)
    plot.set_ylim(-2, 105)
    plot.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    plot.set_xticks(
        list(range(8, 25)),
        [f"{h:02d}h" if h < 24 else "00h\n26/10" for h in range(8, 25)],
    )
    plot.tick_params(axis="both", labelsize=10, colors=MUTED, length=0, pad=7)
    plot.grid(axis="y", color=PALE, linewidth=0.5)
    plot.axvline(17, color=MUTED, linewidth=0.6, linestyle=":")
    serie = d["trilhas"]["recebido"]["segundos"]
    ant, prox = max(pairwise(serie), key=lambda p: p[1][0] - p[0][0])
    grupo = sum(n for s, n in serie if s <= ant[0])
    x0, x1 = ant[0] / 3600, prox[0] / 3600
    plot.plot([x0, x0, x1, x1], [4, 10, 10, 4], color=TSE, lw=0.7)
    hora_ant = (BASE + timedelta(seconds=ant[0])).strftime("%H:%M:%S")
    hora_prox = (BASE + timedelta(seconds=prox[0])).strftime("%H:%M:%S")
    plot.text(
        (x0 + x1) / 2,
        17,
        f"{numero(grupo)} pacotes no primeiro grupo\n{hora_ant} → {hora_prox}\nsem novos carimbos nesse intervalo",
        ha="center",
        color=TSE,
        fontsize=8.8,
        linespacing=1.25,
    )
    for spine in plot.spines.values():
        spine.set_visible(False)
    t(80, 1130, "02 / FAIXA A FAIXA", 29, font="bold")
    t(
        570,
        1130,
        "As linhas abaixo têm durações diferentes. Barras de 0 a 100% mostram o acumulado; números mostram a faixa.",
        30,
        MUTED,
    )
    linha(1190, cor=INK, lw=2)
    for x, cor, titulo, sub in [
        (XLOG, LOG, "VOTOS COMPUTADOS", "Evento do log · sem identificar candidato"),
        (
            XFECHO,
            FECHO,
            "SEÇÕES ENCERRADAS",
            "Placar do dia nas seções que encerraram na faixa",
        ),
        (
            XTSE,
            TSE,
            "RECEBIDOS PELO TSE",
            "Placar do dia nas seções recebidas na faixa",
        ),
    ]:
        t(x, 1220, titulo, 39, cor, "bold")
        t(x, 1278, sub, 29, MUTED)
    t(80, 1220, "HORÁRIO", 29, font="bold")
    t(80, 1275, "BRASÍLIA", 25, MUTED)
    y = topo
    for r in visiveis:
        s = r["fim_inclusivo_s"]
        if s in {9 * 3600 - 1, 17 * 3600, 20 * 3600}:
            fase = (
                "25 OUT · VOTAÇÃO · HORA A HORA"
                if s < 17 * 3600
                else (
                    "25 OUT · ENCERRAMENTOS · MINUTOS EM DETALHE"
                    if s == 17 * 3600
                    else "25 → 26 OUT · RECEBIMENTO · ATÉ O FIM DO EXTRATO"
                )
            )
            rect(80, y, W - 160, 56, "#e7e9df")
            t(100, y + 13, fase, 27, font="bold")
            y += 78
        if s < 17 * 3600:
            h = (s + 1) // 3600
            label = f"{h-1:02d}–{h:02d}h" if h > 8 else "Antes 08h"
            detalhe = "hora completa" if h > 8 else "antes das 8h"
        elif s == 86400:
            label, detalhe = "00h00", "23:00 → 00:00"
        else:
            label = f"{s//3600%24:02d}h{s%3600//60:02d}"
            prev = r["inicio_exclusivo_s"]
            detalhe = (
                "segundo 17h00"
                if s == 61200
                else f"{prev//3600%24:02d}:{prev%3600//60:02d} → {s//3600%24:02d}:{s%3600//60:02d}"
            )
        t(80, y + 10, label, 38, font="bold", limite=220)
        t(80, y + 65, detalhe, 23, MUTED, limite=220)
        if s == 86400:
            t(80, y + 109, "26 OUTUBRO", 23, TSE)
        logcard(r, y)
        bucard(r["fecho"], XFECHO, y, FECHO, "fecho")
        bucard(r["recebido"], XTSE, y, TSE, "recebido")
        linha(y + PASSO - 12)
        y += PASSO
    # Preservar o subtotal literal "após 19h" da versão anterior, sem dupla contagem.
    y += 20
    t(80, y, "APÓS 19h", 34, font="bold")
    t(80, y + 49, "SUBTOTAL", 25, MUTED)
    t(80, y + 89, "das linhas finais", 23, MUTED)
    a = d["apos19_subtotal"]
    logcard(
        {
            "logs": {
                "intervalo": a["logs_computados_intervalo"],
                "acumulado": d["logs_cobertura"]["computados"],
                "acumulado_pct": 100,
            }
        },
        y,
    )
    bucard(a, XFECHO, y, FECHO, "fecho")
    ultimo = d["trilhas"]["recebido"]["ultimo_s"]
    t(XTSE, y + 12, "ÚLTIMO RECEBIMENTO REGISTRADO", 27, TSE, "bold")
    t(
        XTSE,
        y + 59,
        f"25/10 · {ultimo//3600:02d}h{ultimo%3600//60:02d}min{ultimo%60:02d}s",
        45,
        TSE,
        "title",
    )
    t(
        XTSE,
        y + 124,
        (
            "Sem recebimentos de 26/10 neste extrato."
            if ultimo < 86400
            else "Data e hora do último pacote deste extrato."
        ),
        29,
        MUTED,
    )
    linha(y + 205, cor=INK, lw=2)
    y += 244
    t(80, y, "COMO LER SEM MISTURAR OS RELÓGIOS", 30, font="bold")
    t(
        80,
        y + 58,
        "Logs contam cômputos no horário. Encerramento e recebimento carregam o placar do dia inteiro das seções daquela faixa.",
        33,
    )
    t(
        80,
        y + 106,
        "Flávio/Lula: % dos válidos e número de votos. UFs: as três com mais seções, com % das seções da própria faixa.",
        31,
        MUTED,
    )
    t(
        80,
        y + 154,
        "Recebimento é o carimbo dr/hr do pacote no TSE; não mede início do envio nem instante em que o voto entrou na totalização.",
        31,
        MUTED,
    )
    t(80, y + 217, "COBERTURA E PRECISÃO", 28, font="bold")
    cobertura = d["logs_cobertura"]
    t(
        80,
        y + 264,
        f"Logs: {numero(cobertura['cobertas'])} seções ({pct(cobertura['cobertura_secoes_pct'],3)}); {pct(cobertura['cobertura_comparecimento_pct'],3)} do comparecimento. Sem imputar horário aos {numero(cobertura['comparecimento_excluido'])} presentes excluídos.",
        30,
        MUTED,
    )
    t(
        80,
        y + 309,
        "Das 8h às 17h: horas completas, até HH:59:59. A linha 17h00 acrescenta apenas esse segundo. Depois, intervalos (início, fim].",
        30,
        MUTED,
    )
    t(
        80,
        y + 354,
        "* Recebimento: uma seção por pacote, 100% da base. Dezesseis seções têm ordem cronológica divergente; carimbos preservados.",
        30,
        MUTED,
    )
    t(
        80,
        y + 399,
        "O subtotal após 19h repete as linhas finais: não somar novamente. O panorama usa tempo proporcional; a tabela amplia minutos e comprime horas.",
        30,
        MUTED,
    )
    t(80, H - 90, "ARVOR / BRASIL.ARVOR.CO", 28, font="bold")
    t(
        W - 80,
        H - 90,
        "Fonte: BUs, logs e aux.json do TSE · seções principais · 29 out 2026",
        28,
        MUTED,
        align="right",
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for a, limite in textos:
        b = a.get_window_extent(renderer)
        if b.x0 < 50 or b.x1 > W - 50 or b.y0 < 25 or b.y1 > H - 25:
            raise ValueError(f"Texto fora das margens: {a.get_text()}")
        if limite and b.width > limite:
            raise ValueError(
                f"Texto excede coluna ({b.width:.0f}>{limite}): {a.get_text()}"
            )
    for ext in ("png", "pdf"):
        fig.savefig(saida / f"supertimeline-2t-2026.{ext}", dpi=DPI, facecolor=PAPEL)
    plt.close(fig)
    print(f"Imagem: {W} × {H} px")
