"""Figuras do capítulo `pesquisas` (2º turno): mapa do erro por UF e três eleições.

O mapa usa `apuracao_2026.pagina_mapas.mapa_uf` (malha mínima do IBGE). A
comparação de erro comum usa a orientação do 1º turno (esquerda menos direita),
para os três pontos ficarem na mesma régua.
"""

from __future__ import annotations

from apuracao_2026.pagina_fig_base import (
    FLAVIO,
    GRADE,
    INK,
    LULA,
    MUTED,
    Tips,
    area,
    botoes,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    pp,
    r,
    svg_abre,
    t,
    ticks,
)
from apuracao_2026.pagina_mapas import mapa_uf

from .pagina_comum import NOME_UF, num

CORTES = [2, 3, 4, 5]
AZUIS = ["#dbe5f3", "#b3c9e8", "#7fa3d6", "#4f7fc2", "#1457aa"]
VERMELHOS = ["#f2ded8", "#e4b4a9", "#d18877", "#bf5944", "#a42e1c"]


def _sn(v: float, casas: int = 1) -> str:
    return pp(v, casas)[:-3]


def _cor(v: float | None, paleta=AZUIS) -> str:
    if v is None:
        return "#d8d4c8"
    if v < 0:
        return "#efc3b5"
    return paleta[sum(v >= c for c in CORTES)]


def _mapa(m: dict, rotulo: str, candidato: str = "Flávio") -> str:
    sgn = 1 if candidato == "Flávio" else -1
    paleta = AZUIS if sgn == 1 else VERMELHOS
    vals = {u["uf"]: sgn * u["erro_flavio_pp"] for u in m["ufs"]}
    por = {u["uf"]: u for u in m["ufs"]}

    def titulo(uf, v):
        x = por.get(uf)
        if not x:
            return NOME_UF.get(uf, uf)
        previsto = x["flavio_previsto"] if sgn == 1 else 100 - x["flavio_previsto"]
        urna = x["flavio_urna"] if sgn == 1 else 100 - x["flavio_urna"]
        return (
            f"{NOME_UF.get(uf, uf)}: previsto {candidato} {num(previsto, 2)}%, urna "
            f"{num(urna, 2)}%, afastamento {_sn(v, 2)} na parcela de {candidato}; vencedor "
            f"{'certo' if x['acertou_vencedor'] else 'errado'}"
        )

    def marca(uf, v):
        x = por.get(uf)
        sufixo = "" if not x or x["acertou_vencedor"] else " ✕"
        return f"{uf} {_sn(v, 1)}{sufixo}" if v is not None else uf

    leg = [
        ("abaixo de 2", AZUIS[0]),
        ("2 a 3", AZUIS[1]),
        ("3 a 4", AZUIS[2]),
        ("4 a 5", AZUIS[3]),
        ("5 ou mais", AZUIS[4]),
    ]
    return mapa_uf(
        vals,
        lambda uf, v: _cor(None if v is None else sgn * v, paleta),
        marca,
        titulo,
        f"{candidato}: afastamento por UF, {rotulo}",
        f"Parcela de {candidato} prevista menos urna, por UF: {rotulo}. ✕ marca vencedor errado.",
        legenda=(
            leg
            if sgn == 1
            else [
                ("acima de −2", VERMELHOS[0]),
                ("−3 a −2", VERMELHOS[1]),
                ("−4 a −3", VERMELHOS[2]),
                ("−5 a −4", VERMELHOS[3]),
                ("−5 ou menos", VERMELHOS[4]),
            ]
        ),
        escuro=lambda uf, v: v is not None and sgn * v >= CORTES[2],
    )


def fig_mapa(PP: dict) -> str:
    met = PP["metodos"]
    opcoes = [
        ("projecao_25_10", "Projeção Arvor"),
        ("transportado_25_10", "Repetição do 1º turno"),
    ]
    opcoes = [(k, n) for k, n in opcoes if k in met]
    blocos = []
    for i, (k, nome) in enumerate(opcoes):
        esc = " hidden" if i else ""
        blocos.append(
            f'<div data-alt-show="{k}"{esc}><h4>Flávio: previsto menos urna</h4>{_mapa(met[k], nome)}<h4>Lula: previsto menos urna</h4>{_mapa(met[k], nome, "Lula")}</div>'
        )
    ctl = botoes(opcoes, opcoes[0][0], "Método")
    linhas = []
    for k, nome in opcoes:
        m = met[k]
        linhas.append(
            f"{nome}: vencedor certo em {m['acertou_vencedor']} de {m['n_ufs']}, desvio comum de Flávio "
            f"{_sn(m['vies_flavio_pp_ponderado'], 2)}, resto sem o desvio {num(m['rmse_sem_vies_pp'], 2)}"
        )
    legenda = (
        "Afastamento nas parcelas de Flávio e Lula entre os dois, previsto pela casa menos urna, por UF. Azul: Flávio; vermelho: Lula. O segundo mapa espelha o primeiro com sinal oposto e mesma intensidade. Na diferença "
        "F−L é o dobro. " + "; ".join(linhas) + ". Fonte: projecao_pre_urna.json."
    )
    return figura_html(
        "p2t_mapa_erro_uf",
        "".join(blocos),
        legenda,
        Tips(),
        controles=ctl,
        modo="fit",
        dim=False,
    )


# ------------------------------------------------------------------ três eleições


def fig_tres(PV: dict) -> str:
    pontos = [
        (
            "1º turno de 2022",
            PV["referencia_2022"]["erro_comum_lula_menos_bolsonaro"],
            "Lula − Bolsonaro",
        ),
        (
            "1º turno de 2026",
            PV["primeiro_turno"]["erro_comum_lula_menos_flavio"],
            "Lula − Flávio",
        ),
        (
            "2º turno de 2026",
            -PV["resumo"]["publicado_validos_do_total"]["media"],
            "Lula − Flávio",
        ),
    ]
    pa = PV["painel_1t_2t"]
    W2, H2 = 1100, 470
    tips = Tips()
    out = [
        svg_abre(
            W2,
            H2,
            "Afastamento comum das pesquisas em três eleições e mudança de sinal por casa",
            "À esquerda, afastamento comum na diferença esquerda menos direita; à direita, o afastamento de cada casa "
            "no 1º e no 2º turno de 2026.",
        )
    ]
    # painel esquerdo: barras divergentes
    vm = max(abs(v) for _, v, _ in pontos)
    vm = max(6, int(vm) + 2)
    X = escala(-vm, vm, 190, 520)
    y0 = 90
    out.append(
        t(
            355,
            34,
            "Afastamento comum, esquerda menos direita",
            15,
            INK,
            "middle",
            "700",
        )
    )
    out.append(t(X(0) - 8, 60, "← superestimou a direita", 12.5, FLAVIO, "end", "700"))
    out.append(t(X(0) + 8, 60, "superestimou Lula →", 12.5, LULA, weight="700"))
    for v in ticks(-vm, vm, 6):
        out.append(ln(X(v), y0 - 10, X(v), y0 + 3 * 90 - 20, GRADE))
        out.append(t(X(v), y0 + 3 * 90, _sn(v, 0), 12.5, MUTED, "middle", mono=True))
    out.append(ln(X(0), y0 - 14, X(0), y0 + 3 * 90 - 20, INK, 1.6))
    for i, (nome, v, eixo) in enumerate(pontos):
        y = y0 + i * 90
        cor = LULA if v > 0 else FLAVIO
        x1, x2 = sorted((X(0), X(v)))
        g = [
            r(x1, y + 6, x2 - x1, 34, cor),
            t(10, y + 28, nome, 14, INK, weight="700"),
            t(10, y + 46, eixo, 12, MUTED),
            t(
                X(v) + (8 if v > 0 else -8),
                y + 28,
                _sn(v, 2),
                14,
                INK,
                "start" if v > 0 else "end",
                "700",
                mono=True,
            ),
        ]
        k = tips.add(ficha(nome, eixo, [("Afastamento comum", pp(v))]))
        out.append(hit(area(5, y, 525, 60) + "".join(g), k, foco=True))
    # painel direito: linhas por casa
    vals = [x["erro_1t_lula_menos_flavio"] for x in pa["linhas"]] + [
        x["erro_2t_lula_menos_flavio"] for x in pa["linhas"]
    ]
    lo, hi = min(vals) - 1, max(vals) + 1
    Y = escala(hi, lo, 80, H2 - 50)
    xa, xb = 700, 940
    out.append(
        t(
            820,
            34,
            f"Mesma casa nos dois turnos ({pa['n']} casas)",
            15,
            INK,
            "middle",
            "700",
        )
    )
    for v in ticks(lo, hi, 6):
        out.append(ln(xa - 30, Y(v), xb + 30, Y(v), GRADE))
        out.append(t(xa - 38, Y(v) + 4, _sn(v, 0), 12, MUTED, "end", mono=True))
    out.append(ln(xa - 30, Y(0), xb + 30, Y(0), INK, 1.4))
    out.append(t(xa, H2 - 24, "1º turno", 13, INK, "middle", "700"))
    out.append(t(xb, H2 - 24, "2º turno", 13, INK, "middle", "700"))
    for x in pa["linhas"]:
        a, b = x["erro_1t_lula_menos_flavio"], x["erro_2t_lula_menos_flavio"]
        inv = (a > 0) != (b > 0)
        cor = INK if inv else MUTED
        g = [
            ln(xa, Y(a), xb, Y(b), cor, 1.8 if inv else 1.2),
            f'<circle cx="{xa}" cy="{Y(a):.1f}" r="4.5" fill="{LULA if a > 0 else FLAVIO}"/>',
            f'<circle cx="{xb}" cy="{Y(b):.1f}" r="4.5" fill="{LULA if b > 0 else FLAVIO}"/>',
        ]
        k = tips.add(
            ficha(
                x["instituto"],
                "inverteu o sinal" if inv else "mesmo sinal",
                [
                    ("Afastamento 1º turno (L−F)", pp(a)),
                    ("Afastamento 2º turno (L−F)", pp(b)),
                ],
            )
        )
        out.append(hit("".join(g), k, foco=True))
    out.append(
        t(
            820,
            62,
            f"{pa['inverteram_sinal']} inverteram o sinal; correlação {num(pa['correlacao'], 2)}",
            12.5,
            MUTED,
            "middle",
        )
    )
    out.append("</svg>")
    leg = legenda_html(
        [
            ("superestimou Lula", LULA),
            ("superestimou o candidato da direita", FLAVIO),
            ("casa que inverteu o sinal", INK),
        ]
    )
    legenda = (
        "Afastamento = pesquisa menos urna, em pontos dos válidos, na orientação esquerda menos direita. "
        "Fonte: pesquisas_vs_urna.json (blocos referencia_2022, primeiro_turno e painel_1t_2t)."
    )
    return figura_html(
        "p2t_tres_eleicoes", "".join(out), legenda, tips, minw=900, dim=False, apos=leg
    )
