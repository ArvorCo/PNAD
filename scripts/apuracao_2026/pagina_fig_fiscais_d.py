"""Figuras do capítulo 13 (onde colocar fiscal), parte 4: os cenários que o fiscal
existe para impedir (`fiscais_cenarios`) e a linha do tempo dos casos brasileiros
documentados (`fiscais_casos`).

Lê `analysis/apuracao_2026/fontes_fiscais.json` por `fiscais_cenarios.carregar` e,
para os nomes dos critérios, `fiscais.json`. Os cenários são hipótese de risco e os
casos são passado documentado com fonte; nenhum dos dois é atribuído a 2026.
"""

from __future__ import annotations

from html import escape

from . import fiscais_cenarios as FC
from .pagina_fig_base import (
    GRADE,
    INK,
    MUTED,
    PAPER,
    Tips,
    area,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    r,
    registra,
    svg_abre,
    t,
)


def _json() -> dict:
    J = FC.carregar()
    if J is None:
        raise KeyError("fontes_fiscais.json")
    return J


def _nomes_criterios(d) -> dict[str, str]:
    F = d.get("fiscais") if isinstance(d, dict) else None
    if not F:
        return {}
    return {c["id"]: c["nome"] for c in F.get("criterios", [])}


def quebra(s: str, n: int) -> list[str]:
    """Quebra por palavra em linhas de até `n` caracteres."""
    linhas, atual = [], ""
    for palavra in s.split():
        if atual and len(atual) + 1 + len(palavra) > n:
            linhas.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    if atual:
        linhas.append(atual)
    return linhas


def _leis(J: dict, ids: list[str]) -> str:
    leis = FC.por_id(J["base_legal"])
    return "; ".join(f"{leis[b]['norma']}, {leis[b]['dispositivo']}" for b in ids)


# ------------------------------------------------------------------ matriz de cenários


@registra("fiscais_cenarios")
def fiscais_cenarios(d, **_op) -> str:
    J = _json()
    nomes = _nomes_criterios(d)
    tips = Tips()
    ordem = {f: i for i, f in enumerate(FC.FAMILIAS)}
    sinal_ordem = {s: i for i, s in enumerate(FC.SINAIS)}
    cens = sorted(
        J["cenarios"], key=lambda c: (ordem[c["familia"]], sinal_ordem[c["sinal"]])
    )
    w, topo, passo, cab = 1100, 48, 58, 30
    xs, xc, xf = 300, 560, 575
    n_fam = len({c["familia"] for c in cens})
    h = topo + passo * len(cens) + cab * n_fam + 16
    out = [
        svg_abre(
            w,
            h,
            "Os cenários clássicos de manipulação do voto, o sinal que deixam nos dados e o que o fiscal confere",
            "Uma linha por cenário, agrupada por onde ele acontece. A segunda coluna diz se o cenário deixa sinal "
            "nos dados que o capítulo mede, e por quais critérios; a terceira, o que o fiscal confere. Hipótese de "
            "risco, nenhum atribuído a 2026.",
        ),
        t(0, 22, "Cenário", 14, MUTED, weight="700"),
        t(xs, 22, "Sinal nos dados do capítulo", 14, MUTED, weight="700"),
        t(xf, 22, "O que o fiscal confere", 14, MUTED, weight="700"),
        ln(0, 34, w, 34, INK, 1.5),
    ]
    fam_atual = None
    y = topo
    for i, c in enumerate(cens):
        if c["familia"] != fam_atual:
            fam_atual = c["familia"]
            y += cab
            out.append(
                t(
                    4,
                    y - 10,
                    FC.ROT_FAMILIA[fam_atual].upper(),
                    13,
                    FC.COR_FAMILIA[fam_atual],
                    weight="700",
                    mono=True,
                )
            )
        crit = c["criterios"]
        k = tips.add(
            ficha(
                c["nome"],
                f"{FC.ROT_FAMILIA[c['familia']]} · hipótese de risco",
                [
                    ("Sinal nos dados", FC.ROT_SINAL[c["sinal"]]),
                    (
                        "Critérios",
                        (
                            "; ".join(f"{x}. {nomes.get(x, x)}" for x in crit)
                            if crit
                            else "nenhum"
                        ),
                    ),
                    ("Base legal", _leis(J, c["base_legal"])),
                    ("Casos documentados", str(len(FC.casos_do_cenario(J, c["id"])))),
                ],
                f"{c['o_que_e']} {c['sinal_texto']}",
            )
        )
        corpo = [
            r(0, y, w, passo - 8, PAPER if i % 2 else "#ebe5d6"),
            r(0, y, 5, passo - 8, FC.COR_FAMILIA[c["familia"]]),
        ]
        for j, linha in enumerate(quebra(c["nome"], 34)[:2]):
            corpo.append(t(14, y + 20 + j * 18, linha, 14.5, INK, weight="700"))
        cor = FC.COR_SINAL[c["sinal"]]
        cy = y + (passo - 8) / 2
        if c["sinal"] == "deixa":
            corpo.append(f'<circle cx="{xs + 9}" cy="{cy:.1f}" r="8" fill="{cor}"/>')
        elif c["sinal"] == "parcial":
            corpo.append(
                f'<circle cx="{xs + 9}" cy="{cy:.1f}" r="7" fill="{PAPER}" stroke="{cor}" stroke-width="3"/>'
                f'<path d="M{xs + 9} {cy - 7:.1f} A7 7 0 0 1 {xs + 9} {cy + 7:.1f} Z" fill="{cor}"/>'
            )
        else:
            corpo.append(
                f'<circle cx="{xs + 9}" cy="{cy:.1f}" r="7" fill="{PAPER}" stroke="{cor}" stroke-width="3"/>'
            )
        corpo.append(
            t(xs + 24, cy - 2, FC.CURTO_SINAL[c["sinal"]], 13.5, cor, weight="700")
        )
        corpo.append(
            t(
                xs + 24,
                cy + 15,
                ("critérios " + ", ".join(crit)) if crit else "só o fiscal vê",
                13,
                MUTED,
                mono=True,
            )
        )
        for j, linha in enumerate(quebra(c["confere_curto"], 62)[:2]):
            corpo.append(t(xf, y + 20 + j * 18, linha, 13.5, INK))
        corpo.append(area(0, y, w, passo - 8))
        out.append(hit("".join(corpo), k, foco=True))
        y += passo
    out.append(ln(xc, 34, xc, h - 10, GRADE))
    out.append("</svg>")
    leg = legenda_html(
        [(FC.ROT_SINAL[s], FC.COR_SINAL[s]) for s in FC.SINAIS],
        "Sinal nos dados",
    )
    n = FC.contagem_sinal(J)
    legenda = (
        f"{len(cens)} cenários: {n['deixa']} deixam sinal nos dados que o capítulo mede, {n['parcial']} deixam sinal "
        f"fraco ou indireto e {n['nenhum']} não deixam sinal nenhum. As letras são os critérios de "
        "<code>fiscais.json</code>. Hipótese de risco, não descrição desta eleição. Fonte: fontes_fiscais.json, com a "
        "base legal de cada linha na ficha."
    )
    return figura_html(
        "fiscais_cenarios", "".join(out), legenda, tips, minw=900, apos=leg
    )


# ------------------------------------------------------------------ linha do tempo dos casos


@registra("fiscais_casos")
def fiscais_casos(d, **_op) -> str:
    J = _json()
    casos = FC.casos_ordenados(J)
    if not casos:
        raise ValueError("sem casos")
    cens = FC.por_id(J["cenarios"])
    fontes = FC.por_id(J["fontes"])
    tips = Tips()
    linha = FC.linha_do_tempo(J)
    meio = (len(linha) + 1) // 2
    colunas = [linha[:meio], linha[meio:]]
    w, topo, passo = 1100, 62, 34
    h = topo + passo * (meio - 1) + 76
    anos = sorted({c["ano"] for c in casos})
    out = [
        svg_abre(
            w,
            h,
            "Linha do tempo dos casos brasileiros documentados de manipulação do voto",
            "Duas colunas, do caso mais antigo ao mais recente: o ano, um marcador com a cor de onde o cenário "
            "acontece e o rótulo curto do caso. Cada caso tem data, instância, resultado e fonte na ficha e na "
            "tabela abaixo. Os registros de 2026 têm marcador vazado cinza: alegação ou fato em apuração, sem "
            "conclusão.",
        ),
        t(
            0,
            22,
            "Casos documentados, do mais antigo ao mais recente, cor pela família do cenário",
            14,
            MUTED,
            weight="700",
        ),
    ]
    raio = 9
    for k, col in enumerate(colunas):
        xa = k * 560 + 70
        if col:
            out.append(
                ln(xa, topo - 14, xa, topo + passo * (len(col) - 1) + 14, INK, 1.5)
            )
        ano_ant = None
        for i, c in enumerate(col):
            y = topo + i * passo
            cen = cens[c["cenario"]]
            cor = FC.COR_FAMILIA[cen["familia"]]
            if c["ano"] != ano_ant:
                out.append(
                    t(xa - 16, y + 5, c["ano"], 14, INK, "end", weight="700", mono=True)
                )
                ano_ant = c["ano"]
            fts = [fontes[f] for f in c["fontes"]]
            fonte_txt = "; ".join(
                f"{f['veiculo']}, {FC.data_br(f['data'])}" for f in fts
            )
            if c["em_apuracao"]:
                cor = FC.COR_APURACAO
                k_ = tips.add(
                    ficha(
                        c["titulo"],
                        f"{FC.data_br(c['data'])} · {c['local']} · {c['orgao']}",
                        [
                            ("Natureza", FC.ROT_APURACAO),
                            ("O que é", c["tipo_fato"]),
                            ("Estágio", c["estagio"]),
                            ("Fonte", f"{c['natureza']}: {fonte_txt}"),
                        ],
                        f"{c['resumo']} {c.get('versao') or ''}".strip(),
                    )
                )
                marca = (
                    f'<circle cx="{xa:.1f}" cy="{y:.1f}" r="{raio - 1}" fill="{PAPER}" '
                    f'stroke="{cor}" stroke-width="3"/>'
                )
            else:
                k_ = tips.add(
                    ficha(
                        c["titulo"],
                        f"fato em {c['ano']}, ato em {FC.data_br(c['data'])} · {c['local']}",
                        [
                            ("Cenário", cen["nome"]),
                            ("Instância", c["instancia"]),
                            ("Resultado", c["resultado"]),
                            ("Fonte", fonte_txt),
                        ],
                        f"Verificado. {c['resumo']}",
                    )
                )
                marca = (
                    f'<circle cx="{xa:.1f}" cy="{y:.1f}" r="{raio}" fill="{cor}" '
                    f'stroke="{PAPER}" stroke-width="2"/>'
                )
            corpo = (
                marca
                + t(xa + 18, y + 5, c["rotulo_curto"], 15, cor, weight="700")
                + area(xa - raio - 4, y - passo / 2, 420, passo)
            )
            out.append(hit(corpo, k_, foco=True))
    ly = h - 14
    lx = 0
    out.append(ln(0, ly - 24, w, ly - 24, GRADE))
    for f in FC.FAMILIAS:
        out.append(
            f'<circle cx="{lx + 7}" cy="{ly - 5}" r="7" fill="{FC.COR_FAMILIA[f]}"/>'
        )
        out.append(t(lx + 20, ly, FC.ROT_FAMILIA[f], 13.5, INK))
        lx += 34 + 7.2 * len(FC.ROT_FAMILIA[f])
    out.append(
        f'<circle cx="{lx + 7}" cy="{ly - 5}" r="6" fill="{PAPER}" stroke="{FC.COR_APURACAO}" stroke-width="3"/>'
    )
    out.append(t(lx + 20, ly, "Em apuração, 2026", 13.5, INK))
    out.append("</svg>")
    linhas = []
    for c in casos:
        lk = " ".join(
            f'<a href="{escape(fontes[f]["url"])}" rel="noopener">{escape(fontes[f]["veiculo"])}, '
            f"{escape(FC.data_br(fontes[f]['data']))}</a>"
            for f in c["fontes"]
        )
        linhas.append(
            f'<tr><td class="num">{c["ano"]}<br><small>{escape(FC.data_br(c["data"]))}</small></td>'
            f"<th scope=\"row\">{escape(c['titulo'])}<br><small>{escape(c['local'])} · "
            f"{escape(cens[c['cenario']]['nome'])}</small></th>"
            f"<td>{escape(c['instancia'])}</td><td>{escape(c['resultado'])}</td><td>{lk}</td></tr>"
        )
    tabela = (
        '<div class="table-scroll" tabindex="0"><table class="fs-casos"><caption>Os casos, do mais antigo ao mais '
        "recente, com instância, resultado e a fonte lida.</caption>"
        '<thead><tr><th scope="col" class="num">Ano do fato e data do ato</th><th scope="col">Caso</th><th scope="col">Instância</th>'
        '<th scope="col">Resultado</th><th scope="col">Fonte</th></tr></thead>'
        f"<tbody>{''.join(linhas)}</tbody></table></div>"
    )
    legenda = (
        f"{len(casos)} casos de {anos[0]} a {anos[-1]}, todos com fonte lida e data, com o rótulo curto ao lado do marcador. "
        f"Os {len(linha) - len(casos)} marcadores vazados cinza são registros de 2026, alegação ou fato em apuração, "
        "sem conclusão; ficam fora da tabela e aparecem no bloco Em apuração nesta eleição. "
        "O ano é o do fato; a data abaixo do ano, na tabela, é a do ato documentado (decisão, operação, "
        "relatório). Investigação, denúncia e condenação são coisas diferentes, e a coluna de resultado diz qual é qual. "
        "Fonte: fontes_fiscais.json."
    )
    return figura_html(
        "fiscais_casos",
        "".join(out),
        legenda,
        tips,
        minw=860,
        apos=tabela,
    )


__all__ = ["fiscais_casos", "fiscais_cenarios", "quebra"]
