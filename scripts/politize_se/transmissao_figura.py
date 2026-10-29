"""Gráfico nacional: intervalos máximos e contrastes dentro de cada local."""

from __future__ import annotations

from apuracao_2t_2026.encerramento_figura import (
    DPI,
    FONT,
    FONTES,
    INK,
    MUTED,
    PAPEL,
    FontProperties,
    Rectangle,
    plt,
)

from .transmissao import CORES, SAIDA


def inteiro(n):
    return f"{n:,}".replace(",", ".")


def duracao(s, segundos=False):
    v = round(s)
    h, m, seg = v // 3600, v // 60 % 60, v % 60
    return f"{h}h{m:02d}" + (f"min{seg:02d}s" if segundos else "min")


def hora(s):
    return f"{s//3600:02d}:{s//60%60:02d}:{s%60:02d}"


def nome(s, maximo=62):
    s = s.title()
    return s if len(s) <= maximo else s[: maximo - 1].rsplit(" ", 1)[0] + "…"


def desenhar(d):
    w, altura = 2400, 3200
    fig = plt.figure(figsize=(w / DPI, altura / DPI), dpi=DPI, facecolor=PAPEL)
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, w), ylim=(altura, 0))
    ax.set_axis_off()
    textos = []

    def t(x, y, s, size=28, cor=INK, font="sans", align="left"):
        a = ax.text(
            x,
            y,
            s,
            fontsize=size * 72 / DPI,
            color=cor,
            fontproperties=FontProperties(fname=FONTES / FONT[font]),
            ha=align,
            va="top",
            linespacing=1.22,
        )
        textos.append(a)

    def rect(x, y, larg, alt, cor):
        ax.add_patch(Rectangle((x, y), larg, alt, color=cor, linewidth=0))

    def line(x, y, x2, color="#cbd2c8", lw=1):
        ax.plot([x, x2], [y, y], color=color, linewidth=lw * 72 / DPI)

    t(90, 65, "ARVOR / DADOS ELEITORAIS", 28, font="bold")
    t(2310, 65, "2º TURNO · 25 OUT 2026 · HORÁRIO DE BRASÍLIA", 25, align="right")
    rect(90, 124, 85, 9, CORES[-1])
    t(90, 163, "Quanto tempo entre encerrar", 86, font="title")
    t(90, 262, "e chegar ao TSE?", 86, font="title")
    t(
        90,
        378,
        "O intervalo registrado no BU e no pacote recebido, seção por seção, local por local.",
        33,
    )
    t(
        90,
        430,
        f"{inteiro(d['secoes'])} seções em {inteiro(d['locais'])} locais · Brasil sem exterior · fusos normalizados",
        29,
        MUTED,
    )
    itens = [
        (
            "MEDIANA DAS SEÇÕES",
            duracao(d["quantis_s"]["p50"], True),
            "O intervalo longo foi frequente no país.",
        ),
        (
            "MAIOR INTERVALO",
            duracao(d["quantis_s"]["max"], True),
            "Salvador/BA · seção 374 · zona 4",
        ),
        (
            "LOCAIS COM ALGUMA SEÇÃO >5h",
            str(d["faixas"][-1]["locais"]),
            "Corte exploratório de muita atenção.",
        ),
    ]
    for i, (rot, v, nota) in enumerate(itens):
        x = 90 + i * 750
        t(x, 525, rot, 23, MUTED, "bold")
        t(x, 570, v, 53, CORES[-1], "title")
        t(x, 646, nota, 25)
    line(90, 705, 2310, INK, 2)
    t(90, 742, "01 / DISTRIBUIÇÃO DOS LOCAIS", 28, font="bold")
    t(
        90,
        790,
        "Cada local entra uma vez, pela seção com maior intervalo utilizável.",
        27,
        MUTED,
    )
    for i, f in enumerate(d["faixas"]):
        x = 90 + i * 375
        rect(x, 850, 335, 15, f["cor"])
        t(x, 888, f["nome"], 26, font="bold")
        t(x, 932, inteiro(f["locais"]), 43, font="title")
        t(
            x,
            989,
            f"{100*f['locais']/d['locais_cobertos']:.2f}% dos locais".replace(".", ","),
            24,
            MUTED,
        )
    t(
        90,
        1045,
        f"Cobertura: {inteiro(d['cobertas'])} seções utilizáveis; {len(d['auditoria'])} com cronologia inconsistente, em separado.",
        25,
        MUTED,
    )
    line(90, 1098, 2310, INK, 2)
    t(90, 1137, "02 / OS DEZ MAIORES INTERVALOS POR LOCAL", 28, font="bold")
    t(
        90,
        1187,
        "Barra: maior intervalo de uma seção. Losango: mediana das outras seções do local.",
        27,
        MUTED,
    )
    x0, larg, escala = 1110, 950, 7 * 3600
    for h in range(8):
        x = x0 + larg * h / 7
        t(x, 1250, f"{h}h", 23, MUTED, align="center")
        ax.plot([x, x], [1287, 2320], color="#d9ddd4", lw=0.4, zorder=0)
    for i, r in enumerate(d["principais"][:10]):
        y = 1300 + i * 102
        if i % 2 == 0:
            rect(75, y - 7, 2250, 100, "#eceee5")
        t(90, y, f"{i+1:02d}  {r['municipio']}/{r['uf']}", 31, font="bold")
        t(90, y + 41, nome(r["nome"]), 25)
        t(
            90,
            y + 73,
            f"Seção {r['secao_max']} · zona {r['zona']} · {hora(r['enc_s'])} → {hora(r['recebido_s'])}",
            22,
            MUTED,
        )
        rect(x0, y + 31, larg * r["max_s"] / escala, 24, CORES[-1])
        if r["mediana_outras_s"] is not None:
            ax.scatter(
                [x0 + larg * r["mediana_outras_s"] / escala],
                [y + 43],
                marker="D",
                s=32,
                c=INK,
                edgecolors=PAPEL,
                linewidths=0.7,
                zorder=4,
            )
        t(2310, y + 23, duracao(r["max_s"], True), 29, CORES[-1], "bold", "right")
        t(
            2310,
            y + 65,
            f"{r['cobertas']}/{r['secoes']} seções",
            22,
            MUTED,
            align="right",
        )
    line(90, 2343, 2310, INK, 2)
    t(90, 2380, "03 / ONDE UMA SEÇÃO SE DISTANCIOU DAS DEMAIS", 28, font="bold")
    t(
        90,
        2428,
        "Três maiores diferenças para a mediana das outras seções do local. Sem ajuste da logística.",
        27,
        MUTED,
    )
    for i, r in enumerate(d["maior_contraste_local"][:3]):
        x = 90 + i * 750
        t(x, 2500, f"{r['municipio']}/{r['uf']}", 32, font="bold")
        t(x, 2547, nome(r["nome"], 38), 24, MUTED)
        t(x, 2590, f"+{duracao(r['excesso_outras_s'],True)}", 44, CORES[-1], "title")
        t(x, 2653, f"Seção {r['secao_max']}: {duracao(r['max_s'],True)}", 26)
        t(
            x,
            2695,
            f"Outras {r['cobertas']-1}: mediana {duracao(r['mediana_outras_s'],True)}",
            26,
        )
        t(
            x,
            2737,
            f"{hora(r['enc_s'])} → {hora(r['recebido_s'])} · zona {r['zona']}",
            24,
            MUTED,
        )
    line(90, 2807, 2310, INK, 2)
    t(
        90,
        2844,
        "O INTERVALO É OBSERVÁVEL. A CAUSA PRECISA DE DOCUMENTOS.",
        28,
        font="bold",
    )
    t(
        90,
        2896,
        "Emissão do BU, coleta, transporte, espera e recepção são etapas distintas. Na base, a mediana",
        28,
    )
    t(
        90,
        2938,
        f"entre encerramento e emissão foi de {duracao(d['preparo_quantis_s']['p50'], True)}. Os carimbos não identificam o início do envio",
        28,
    )
    t(
        90,
        2980,
        "nem demonstram alteração dos votos. Compare atas, registros de transmissão e o BU impresso.",
        28,
    )
    t(
        90,
        3055,
        "Fonte: BU + dr/hr do pacote selecionado no aux.json do TSE. Máximo sempre calculado dentro de uma mesma seção.",
        23,
        MUTED,
    )
    t(
        90,
        3094,
        "Acima de 4h: atenção. Acima de 5h: muita atenção. Faixas exploratórias, sem validação como teste de irregularidade.",
        23,
        MUTED,
    )
    t(90, 3128, "ARVOR / BRASIL.ARVOR.CO", 24, font="bold")
    t(2310, 3128, "Mapa e dados: Politize-se · 29 out 2026", 23, MUTED, align="right")
    fig.canvas.draw()
    for a in textos:
        b = a.get_window_extent(fig.canvas.get_renderer())
        if b.x0 < 50 or b.x1 > w - 50 or b.y0 < 20 or b.y1 > altura - 25:
            raise ValueError(f"Texto fora da margem: {a.get_text()}")
    for ext in ["png", "pdf"]:
        fig.savefig(
            SAIDA / f"encerramento-recebimento-2t-2026.{ext}", dpi=DPI, facecolor=PAPEL
        )
    plt.close(fig)
