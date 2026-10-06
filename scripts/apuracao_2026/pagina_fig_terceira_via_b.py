"""Figuras do capítulo 14: os municípios prioritários e o teto endereçável por UF.

Dados em `analysis/apuracao_2026/dados/terceira_via.json`. Duas figuras:

- `terceira_via_prioridade`: os 30 primeiros do índice, barra empilhada por
  candidatura de terceira via, e a tabela ordenável dos 100;
- `terceira_via_teto_uf`: uma aba por UF com o mapa de bolhas do teto
  endereçável local (terceira via mais o vão positivo da direita local) e a
  tabela dos 10 maiores tetos da UF.

A ordenação da tabela é um script pequeno, embutido uma vez; sem ele, a tabela
fica na ordem do índice.
"""

from __future__ import annotations

import math
from html import escape

import voto_util_mapa as VM

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    CINZA,
    GRADE,
    INK,
    MUTED,
    PAPER,
    Tips,
    W,
    area,
    botoes,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    nome_bonito,
    pct,
    pp,
    r,
    registra,
    svg_abre,
    t,
    ticks,
)
from .pagina_fig_mapas import caminho
from .pagina_fig_terceira_via import (
    ROT_CLASSE,
    centroides,
    direita_local,
    municipios,
    sinal_votos,
    votos_curto,
)

GRUPOS = ("renan", "zema", "cury", "caiado", "outros")
COR_GRUPO = {
    "renan": "#5a4a9e",
    "zema": "#e07b1a",
    "cury": "#0f7f5f",
    "caiado": "#7d6e33",
    "outros": CINZA,
}
NOME_GRUPO = {
    "renan": "Renan Santos",
    "zema": "Romeu Zema",
    "cury": "Augusto Cury",
    "caiado": "Ronaldo Caiado",
    "outros": "demais seis",
}
N_BARRAS = 30
N_TIP_UF = 40
COR_TETO = {"terceira": "#0f7f5f", "misto": "#a0893a", "palanque": "#3a6fb8"}
ROT_TETO = {
    "terceira": "teto vem sobretudo da terceira via",
    "misto": "terceira via e direita local em proporção parecida",
    "palanque": "teto vem sobretudo da direita local acima de Flávio",
}


def _composicao(x: dict) -> list[tuple[str, int]]:
    return [(g, x[g]) for g in GRUPOS]


def carregadores_txt(x: dict) -> str:
    cs = x.get("carregadores") or []
    if not cs:
        return "nenhum"
    return "; ".join(f"{nome_bonito(c['nome'])} {num(c['indice'], 0)}" for c in cs[:3])


def _lider(x: dict) -> str:
    if x["vao_votos"] > 0 and x["local_lider"]:
        return f"{nome_bonito(x['local_lider'])} ({sinal_votos(x['vao_votos'])})"
    return "nenhum nome acima de Flávio"


def _ficha_item(x: dict, sub: str) -> str:
    return ficha(
        f"{nome_bonito(x['nome'])} ({x['uf']})",
        sub,
        [
            (
                "Terceira via",
                f"{inteiro(x['estoque'])} ({pct(x['estoque_pct'], 1)} dos válidos)",
            ),
            *((NOME_GRUPO[g], inteiro(v)) for g, v in _composicao(x)),
            ("Margem de Flávio", pp(x["margem_pp"], 1)),
            ("Bolsonaro no 2º turno de 2022", pct(x["b22_2t_pct"], 1)),
            ("Saldo pela matriz Nexus", sinal_votos(x["saldo"])),
            ("Com Datafolha para Cury e Caiado", sinal_votos(x["saldo_df"])),
            ("Fora (branco, nulo, indecisão)", votos_curto(x["fora"])),
            ("Direita local acima de Flávio", _lider(x)),
            ("Carregadores (índice > 100)", carregadores_txt(x)),
            ("Fator de conversão", num(x["fator"], 3)),
        ],
        "matriz nacional aplicada ao município: hipótese, não medição local",
    )


# ------------------------------------------------------------------ prioridade


def _tabela_100(top: list[dict]) -> str:
    cab = [
        "Nº",
        "Município",
        "UF",
        "Eleitores",
        "Terceira via",
        "Renan",
        "Zema",
        "Cury",
        "Caiado",
        "Demais",
        "Margem de Flávio (pp)",
        "Bolsonaro 2022, 2º t. (%)",
        "Nulo 2022, 1º→2º (pp)",
        "Saldo Nexus",
        "Saldo Datafolha",
        "Fora",
        "Direita local acima de Flávio",
        "Carregadores (índice)",
        "Fator",
    ]
    texto = {1, 2, 16, 17}
    num_cls = ' class="num"'
    th = "".join(
        f'<th scope="col"{"" if j in texto else num_cls}>{escape(c)}</th>'
        for j, c in enumerate(cab)
    )
    corpo = []
    for x in top:
        valores = [
            (x["posicao"], str(x["posicao"])),
            (x["nome"], escape(nome_bonito(x["nome"]))),
            (x["uf"], x["uf"]),
            (x["eleitores"], inteiro(x["eleitores"])),
            (x["estoque"], inteiro(x["estoque"])),
            *((x[g], inteiro(x[g])) for g in GRUPOS),
            (x["margem_pp"], pp(x["margem_pp"], 1)[:-3]),
            (
                x["b22_2t_pct"] if x["b22_2t_pct"] is not None else "",
                num(x["b22_2t_pct"], 1),
            ),
            (
                x["delta_bn22_pp"] if x["delta_bn22_pp"] is not None else "",
                pp(x["delta_bn22_pp"], 2)[:-3],
            ),
            (x["saldo"], sinal_votos(x["saldo"])),
            (x["saldo_df"], sinal_votos(x["saldo_df"])),
            (x["fora"], inteiro(x["fora"])),
            (x["vao_votos"], escape(_lider(x))),
            (carregadores_txt(x), escape(carregadores_txt(x))),
            (x["fator"], num(x["fator"], 3)),
        ]
        cels = []
        for j, (v, txt) in enumerate(valores):
            tag = "th" if j == 1 else "td"
            esc = ' scope="row"' if j == 1 else ""
            cls = "" if j in texto else ' class="num"'
            cels.append(f'<{tag}{esc}{cls} data-v="{escape(str(v))}">{txt}</{tag}>')
        corpo.append("<tr>" + "".join(cels) + "</tr>")
    return (
        '<div class="table-scroll tv-tab" tabindex="0"><table data-ordena="1">'
        "<caption>Os 100 municípios prioritários pelo índice da casa. Clique no cabeçalho para ordenar.</caption>"
        f"<thead><tr>{th}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"
    )


@registra("terceira_via_prioridade")
def terceira_via_prioridade(d, **_op) -> str:
    TV = dado(d, "terceira_via")
    P = TV["prioridade"]
    top = P["top"][:N_BARRAS]
    esq, topo, passo = 250, 60, 26
    base = topo + passo * len(top)
    h = base + 64
    segundo = sorted((x["estoque"] for x in top), reverse=True)[1]
    teto_eixo = segundo * 1.12
    tips = Tips()
    out = [
        svg_abre(
            W,
            h,
            "Os 30 municípios prioritários: votos de terceira via por candidatura",
            "Barras empilhadas por candidatura de terceira via (Renan, Zema, Cury, Caiado e demais), na ordem do "
            "índice de prioridade da casa; à direita, o fator de conversão e o saldo pela matriz Nexus.",
        )
    ]
    for modo in ("votos", "composicao"):
        if modo == "votos":
            X = escala(0, teto_eixo, esq, W - 230)
            marcas = ticks(0, teto_eixo, 6)
        else:
            X = escala(0, 100, esq, W - 230)
            marcas = ticks(0, 100, 5)
        g = []
        for v in marcas:
            g.append(ln(X(v), topo - 8, X(v), base, GRADE))
            g.append(
                t(
                    X(v),
                    base + 20,
                    votos_curto(v) if modo == "votos" else f"{num(v, 0)}%",
                    13,
                    MUTED,
                    "middle",
                    mono=True,
                )
            )
        for i, x in enumerate(top):
            y = topo + i * passo
            corpo = [
                t(
                    esq - 10,
                    y + 17,
                    f"{x['posicao']}. {nome_bonito(x['nome'])} ({x['uf']})",
                    13.5,
                    INK,
                    "end",
                )
            ]
            x0 = X(0)
            cortado = modo == "votos" and x["estoque"] > teto_eixo
            fim = X(teto_eixo)
            for gname, v in _composicao(x):
                if modo == "votos":
                    largura = X(v) - X(0)
                else:
                    largura = (X(100 * v / x["estoque"]) - X(0)) if x["estoque"] else 0
                largura = min(largura, max(0.0, fim - x0)) if cortado else largura
                corpo.append(r(x0, y + 4, largura, passo - 9, COR_GRUPO[gname]))
                x0 += largura
            if cortado:
                corpo.append(
                    f'<path d="M{fim - 10:.1f} {y + 2:.1f} l6 {passo - 5:.1f} M{fim - 4:.1f} {y + 2:.1f} l6 {passo - 5:.1f}" '
                    f'stroke="{PAPER}" stroke-width="3"/>'
                )
            fim_txt = x0 + 8 if modo == "votos" else X(100) + 8
            rotulo = (
                f"{votos_curto(x['estoque'])} · fator {num(x['fator'], 2)}"
                if modo == "votos"
                else f"saldo {sinal_votos(x['saldo'])}"
            )
            corpo.append(t(fim_txt, y + 17, rotulo, 13, INK, mono=True))
            k = tips.add(_ficha_item(x, f"{x['posicao']}º no índice de prioridade"))
            g.append(hit(area(0, y, W, passo) + "".join(corpo), k))
        mostra = "" if modo == "votos" else ' display="none"'
        out.append(f'<g data-alt-show="{modo}"{mostra}>{"".join(g)}</g>')
    out.append("</svg>")
    ctl = botoes([("votos", "Votos"), ("composicao", "Composição")], "votos", "Escala")
    leg = legenda_html(
        [(NOME_GRUPO[g], COR_GRUPO[g]) for g in GRUPOS],
        "Votos de terceira via por candidatura",
    )
    soma = P["soma_top"]
    pesos = P["pesos"]
    legenda_ = (
        "Índice de prioridade = votos de terceira via × fator de conversão. O fator é a média ponderada da posição do "
        f"município entre os 5.571 em quatro variáveis: vão local ({num(pesos['vao_local'], 2)}), matriz por nome "
        f"({num(pesos['matriz'], 2)}), Bolsonaro no 2º turno de 2022 ({num(pesos['ambiente_2022'], 2)}) e margem de Flávio "
        f"({num(pesos['margem'], 2)}); os pesos são juízo editorial. Na escala de votos, a barra de São Paulo é cortada "
        f"no eixo. Os 100 somam {inteiro(soma['estoque'])} votos de terceira via e saldo de {inteiro(soma['saldo'])} pela "
        "matriz Nexus. Fonte: terceira_via.json."
    )
    return figura_html(
        "terceira_via_prioridade",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=860,
        apos=leg + _tabela_100(P["top"]),
    )


# ------------------------------------------------------------------ teto por UF


def tipo_teto(x: dict) -> str:
    vao = max(0, x["vao_votos"])
    total = x["estoque"] + vao
    if total <= 0:
        return "terceira"
    parte = vao / total
    if parte >= 2 / 3:
        return "palanque"
    if parte <= 1 / 3:
        return "terceira"
    return "misto"


def _projecao_uf(uf: str, w: float, h: float):
    aneis = VM._features()[uf]
    lons = [p[0] for a in aneis for p in a]
    lats = [p[1] for a in aneis for p in a]
    cosl = math.cos(math.radians((min(lats) + max(lats)) / 2))
    sx, sy = (max(lons) - min(lons)) * cosl, max(lats) - min(lats)
    pad = 14
    esc = min((w - 2 * pad) / sx, (h - 2 * pad) / sy)
    ox = pad + ((w - 2 * pad) - sx * esc) / 2
    oy = pad + ((h - 2 * pad) - sy * esc) / 2
    lon0, lat1 = min(lons), max(lats)

    def proj(lon: float, lat: float) -> tuple[float, float]:
        return ox + (lon - lon0) * cosl * esc, oy + (lat1 - lat) * esc

    return proj, aneis


def _tabela_uf(uf: str, u: dict, mostra: bool) -> str:
    linhas = []
    for i, x in enumerate(u["top"], start=1):
        linhas.append(
            "<tr>"
            f'<td class="num">{i}</td><th scope="row">{escape(nome_bonito(x["nome"]))}</th>'
            f'<td class="num">{inteiro(x["estoque"])}</td>'
            f"<td>{escape(_lider(x))}</td>"
            f'<td class="num">{inteiro(x["teto"])}</td>'
            f'<td class="num">{pct(100 * x["teto"] / x["comparecimento"] if x["comparecimento"] else None, 1)}</td>'
            f'<td class="num">{pp(x["margem_pp"], 1)[:-3]}</td>'
            f"<td>{escape(carregadores_txt(x))}</td>"
            "</tr>"
        )
    oculto = "" if mostra else " hidden"
    cab = (
        f"<p><b>{escape(NOME_UF[uf])}</b>: teto endereçável de {inteiro(u['teto'])} votos, {inteiro(u['estoque'])} de "
        f"terceira via e {inteiro(u['vao_positivo'])} da direita local acima de Flávio em "
        f"{inteiro(u['municipios_vao_positivo'])} de {inteiro(u['municipios'])} municípios. Teto, não previsão.</p>"
    )
    return (
        f'<div class="tv-uf" data-alt-show="{uf}"{oculto}>{cab}<div class="table-scroll" tabindex="0"><table>'
        "<thead><tr>"
        '<th scope="col" class="num">Nº</th><th scope="col">Município</th>'
        '<th scope="col" class="num">Terceira via</th><th scope="col">Direita local acima de Flávio</th>'
        '<th scope="col" class="num">Teto</th><th scope="col" class="num">Teto / votantes</th>'
        '<th scope="col" class="num">Margem de Flávio (pp)</th><th scope="col">Carregadores (índice)</th>'
        f"</tr></thead><tbody>{''.join(linhas)}</tbody></table></div></div>"
    )


@registra("terceira_via_teto_uf")
def terceira_via_teto_uf(d, **_op) -> str:
    TV = dado(d, "terceira_via")
    U = TV["teto"]["ufs"]
    ordem = sorted(U, key=lambda uf: -U[uf]["teto"])
    mun = municipios(d)
    cen = centroides()
    w, h = 640, 560
    tips = Tips()
    linhas_tip: list[list[str]] = []
    grupos, tabelas = [], []
    for j, uf in enumerate(ordem):
        proj, aneis = _projecao_uf(uf, w, h)
        dd = caminho([[(p[0], p[1]) for p in a] for a in aneis], proj, 0.9)
        dentro = sorted((m for m in mun if m["uf"] == uf), key=lambda m: -m["teto"])
        tmax = max(m["teto"] for m in dentro) or 1
        k = 30 / math.sqrt(tmax)
        partes = [f'<path d="{dd}" fill="#ebe5d6" stroke="#b9b29f" stroke-width="1"/>']
        miudos: dict[tuple[float, str], list[str]] = {}
        for pos, m in enumerate(dentro):
            c = cen.get(str(m["ibge"]))
            if c is None:
                continue
            x, y = proj(*c)
            raio = max(1.0, k * math.sqrt(max(m["teto"], 0)))
            cor = COR_TETO[tipo_teto(m)]
            if pos >= N_TIP_UF:
                miudos.setdefault((round(raio * 2) / 2, cor), []).append(
                    f"M{x:.0f} {y:.0f}h0"
                )
                continue
            i = len(linhas_tip)
            linhas_tip.append(
                [
                    f"{nome_bonito(m['nome'])} ({uf})",
                    f"{inteiro(m['teto'])} votos",
                    inteiro(m["estoque"]),
                    direita_local(m),
                    pp(m["margem_pp"], 1),
                    ROT_CLASSE[m["classe"]],
                ]
            )
            partes.append(
                f'<circle class="hit" data-k="r{i}" cx="{x:.1f}" cy="{y:.1f}" r="{raio:.1f}" fill="{cor}" '
                f'fill-opacity="0.78" stroke="{PAPER}" stroke-width="0.8"/>'
            )
        for (raio, cor), segs in sorted(miudos.items(), key=lambda kv: -kv[0][0]):
            partes.insert(
                1,
                f'<path d="{"".join(segs)}" stroke="{cor}" stroke-width="{2 * raio}" stroke-linecap="round" '
                'stroke-opacity="0.55" fill="none" pointer-events="none"/>',
            )
        mostra = "" if j == 0 else ' display="none"'
        grupos.append(f'<g data-alt-show="{uf}"{mostra}>{"".join(partes)}</g>')
        tabelas.append(_tabela_uf(uf, U[uf], j == 0))
    tips.tabela(
        [
            "Município",
            "Teto endereçável",
            "Terceira via",
            "Direita local acima de Flávio",
            "Margem de Flávio",
            "Classe",
        ],
        linhas_tip,
        nota="teto = terceira via + vão positivo da direita local; pode contar o mesmo eleitor duas vezes",
    )
    svg = (
        svg_abre(
            w,
            h,
            "Teto endereçável local por UF: terceira via mais a direita local acima de Flávio",
            "Uma aba por UF; bolha no centroide de cada município, área pelo teto endereçável, cor pela parcela que "
            "vem da terceira via ou da direita local.",
        )
        + "".join(grupos)
        + "</svg>"
    )
    abas = botoes([(uf, uf) for uf in ordem], ordem[0], "UF", "tab")
    leg = legenda_html(
        [(ROT_TETO[k], COR_TETO[k]) for k in ("terceira", "misto", "palanque")],
        "Origem do teto",
    )
    legenda_ = (
        "Teto endereçável local = votos de terceira via + max(0; votos do nome do lado de Flávio com mais votos no "
        "município, ao governo ou ao Senado, menos os votos de Flávio). Mesma urna, cargos diferentes: o teto pode contar "
        "o mesmo eleitor nas duas parcelas e não é previsão. As abas seguem a ordem do teto estadual; a ficha cobre os "
        f"{N_TIP_UF} maiores de cada UF. Fonte: terceira_via.json."
    )
    return figura_html(
        "terceira_via_teto_uf",
        svg,
        legenda_,
        tips,
        controles=abas,
        modo="fit",
        apos=leg + "".join(tabelas),
    )
