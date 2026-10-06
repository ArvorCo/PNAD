"""Figuras do capítulo 13 (onde colocar fiscal), parte 3: as 40 seções de nível alta em
cartões, as duas listas do PL (proteger voto de Flávio, vigiar voto atípico de Lula) e
o contexto de risco do território (`fiscais_risco`, contrato 1.1).

Peças comuns (cores de nível, camadas de risco, links) em `pagina_fig_fiscais`.
"""

from __future__ import annotations

from collections import Counter
from html import escape

from .pagina_comum import inteiro
from .pagina_fig_base import (
    FLAVIO,
    GRADE,
    INK,
    LULA,
    MUTED,
    PAPER,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    larga_estreita,
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
from .pagina_fig_fiscais import (
    CAMADAS,
    NIVEIS,
    ROT_CAMADA,
    _empilhada,
    _legenda_niveis,
    camadas,
    corta,
    criterios_txt,
    fiscais,
    links,
    lugar,
    nivel_txt,
    risco_txt,
    tem_risco,
)

# ------------------------------------------------------------------ seções de nível alta


def _hora(s: str | None) -> str:
    if not s:
        return "s/d"
    dia, _, h = s.partition(" ")
    return f"{dia[8:10]}/{dia[5:7]} {h[:5]}"


def _card(s: dict, F: dict) -> str:
    nomes = {c["id"]: c["nome"] for c in F["criterios"]}
    cr = "".join(
        f"<li><b>{escape(c)}.</b> {escape(nomes.get(c, c))}</li>"
        for c in s["criterios"]
    )
    if s.get("sem_boletim"):
        votos = "<p>Sem boletim publicado: o TSE devolve 404 para o arquivo desta seção.</p>"
    else:
        votos = (
            '<dl class="fs-num">'
            f"<div><dt>Lula</dt><dd>{inteiro(s['lula'])} · {pct(s.get('lula_pct'), 1)}"
            f"<small>zona {pp(s.get('excesso_zona_lula_pp'), 1)}</small></dd></div>"
            f"<div><dt>Flávio</dt><dd>{inteiro(s['flavio'])} · {pct(s.get('flavio_pct'), 1)}"
            f"<small>zona {pp(s.get('excesso_zona_flavio_pp'), 1)}</small></dd></div>"
            f"<div><dt>Aptos e votantes</dt><dd>{inteiro(s['aptos'])} · {inteiro(s.get('votantes'))}</dd></div>"
            f"<div><dt>Modelo de urna</dt><dd>{escape(s.get('modelo_urna') or 's/d')}</dd></div>"
            f"<div><dt>Encerramento</dt><dd>{_hora(s.get('encerramento_brasilia'))}</dd></div>"
            f"<div><dt>Recebido pelo TSE</dt><dd>{_hora(s.get('recebido_tse'))}</dd></div>"
            "</dl>"
        )
    expl = s.get("explicacao_provavel") or "nenhuma explicação comum no cadastro"
    terr = ""
    if isinstance(s.get("risco"), dict):
        terr = (
            f'<p class="fs-terr"><b>Contexto do território:</b> {escape(risco_txt(s))}. '
            "Fonte: meta.fontes_risco. Contexto para o fiscal planejar, não indício.</p>"
        )
    return (
        f'<article class="fs-card"><p class="fs-card-k"><span class="fs-chip fs-nivel-{s["nivel"]}">'
        f"{nivel_txt(s['nivel'])} · {inteiro(s['pontuacao'])} pts</span> {s['uf']}</p>"
        f"<h4>{escape(nome_bonito(s['municipio']))}, zona {s['zona']}, seção {s['secao']}</h4>"
        f"<p class=\"fs-end\">{escape(nome_bonito(s.get('local') or ''))}<br>"
        f"{escape(nome_bonito(s.get('endereco') or ''))}, {escape(nome_bonito(s.get('bairro') or ''))}</p>"
        f'{votos}<p><b>Critérios disparados</b></p><ul class="fs-cr">{cr}</ul>'
        f"<p><b>Explicação provável:</b> {escape(expl)}.</p>"
        f"<p><b>O que o fiscal confere:</b> {escape(s.get('o_que_conferir') or '')}</p>"
        f'{terr}<p class="fs-links">{links(s)}</p></article>'
    )


@registra("fiscais_secoes_amostra")
def fiscais_secoes_amostra(d, **_op) -> str:
    F = fiscais(d)
    altas = sorted(
        (s for s in F["secoes"] if s["nivel"] == "alta"),
        key=lambda s: (-s["pontuacao"], -s["aptos"]),
    )[:40]
    if not altas:
        raise KeyError("secoes de nível alta")
    tips = Tips()
    passo, topo, x0, w = 22, 46, 330, 1100
    h = topo + passo * len(altas) + 44
    esc = escala(0, 100, x0, w - 40)
    out = [
        svg_abre(
            w,
            h,
            "As 40 seções de nível alta de maior pontuação: a seção contra a zona",
            "Para cada seção, o percentual de Lula e o de Flávio na seção (ponto cheio) e no resto da zona (ponto vazado).",
        ),
        t(
            x0,
            22,
            "% dos válidos: seção (cheio) e resto da zona (vazado)",
            14,
            MUTED,
            weight="600",
        ),
    ]
    for v in range(0, 101, 20):
        out.append(ln(esc(v), topo - 8, esc(v), h - 34, GRADE))
        out.append(t(esc(v), h - 14, f"{v}%", 13, MUTED, "middle", mono=True))
    linhas = []
    for i, s in enumerate(altas):
        y = topo + i * passo + passo / 2
        out.append(
            t(
                x0 - 10,
                y + 5,
                corta(
                    f"{s['uf']} {nome_bonito(s['municipio'])} z{s['zona']} s{s['secao']}",
                    40,
                ),
                13,
                INK,
                "end",
            )
        )
        g = []
        for cand, cor in (("lula", LULA), ("flavio", FLAVIO)):
            v, z = s.get(f"{cand}_pct"), s.get(f"zona_{cand}_pct")
            if v is None or z is None:
                continue
            g.append(ln(esc(z), y, esc(v), y, cor, 2))
            g.append(
                f'<circle cx="{esc(z):.1f}" cy="{y:.1f}" r="5" fill="{PAPER}" stroke="{cor}" stroke-width="2"/>'
            )
            g.append(f'<circle cx="{esc(v):.1f}" cy="{y:.1f}" r="5.5" fill="{cor}"/>')
        g.append(area(x0, y - passo / 2, w - 40 - x0, passo))
        out.append(hit("".join(g), f"r{i}"))
        linhas.append(
            [
                f"{lugar(s)}, zona {s['zona']}, seção {s['secao']}",
                pct(s.get("lula_pct"), 1),
                pct(s.get("zona_lula_pct"), 1),
                pct(s.get("flavio_pct"), 1),
                pct(s.get("zona_flavio_pct"), 1),
                criterios_txt(s["criterios"]),
                inteiro(s["pontuacao"]),
                nome_bonito(s.get("local") or ""),
            ]
        )
    out.append("</svg>")
    tips.tabela(
        [
            "Seção",
            "Lula na seção",
            "Lula no resto da zona",
            "Flávio na seção",
            "Flávio no resto da zona",
            "Critérios",
            "Pontuação",
            "Local",
        ],
        linhas,
    )
    cards = (
        '<div class="fs-cards">' + "".join(_card(s, F) for s in altas[:12]) + "</div>"
    )
    if len(altas) > 12:
        cards += (
            f'<details class="fs-mais"><summary>Ver os outros {len(altas) - 12} cartões</summary>'
            '<div class="fs-cards">'
            + "".join(_card(s, F) for s in altas[12:])
            + "</div></details>"
        )
    leg = legenda_html(
        [("Lula", LULA), ("Flávio", FLAVIO)],
        "Ponto cheio: seção. Vazado: resto da zona",
    )
    legenda = (
        f"As {len(altas)} seções de nível alta de maior pontuação, com os cartões completos abaixo. "
        "Seção sem boletim fica sem pontos no gráfico. Fonte: fiscais.json, secoes."
    )
    return figura_html(
        "fiscais_secoes_amostra",
        "".join(out),
        legenda,
        tips,
        minw=760,
        apos=leg + cards,
    )


# ------------------------------------------------------------------ protege e vigia


def _painel_lista(
    itens: list[dict],
    chave: str,
    titulo: str,
    cor: str,
    x0: float,
    y0: float,
    larg: float,
    k0: int,
    fmt,
) -> str:
    passo = 26
    rot_w = 300
    vmax = max((x.get(chave) or 0 for x in itens), default=1) or 1
    esc = escala(0, vmax, x0 + rot_w, x0 + larg - 70)
    out = [t(x0, y0 + 18, titulo, 15, INK, weight="700")]
    for i, x in enumerate(itens):
        y = y0 + 34 + i * passo
        nome = corta(
            f"{i + 1}. {nome_bonito(x['municipio'])} ({x['uf']}) · {nome_bonito(x['local'])}",
            42,
        )
        out.append(t(x0 + rot_w - 8, y + 17, nome, 13, INK, "end"))
        v = x.get(chave) or 0
        out.append(
            hit(
                r(x0 + rot_w, y + 4, esc(v) - esc(0), passo - 8, cor)
                + area(x0, y, larg, passo),
                f"r{k0 + i}",
            )
        )
        out.append(t(esc(v) + 6, y + 17, fmt(v), 13, INK, mono=True))
    return "".join(out)


@registra("fiscais_protege_vigia")
def fiscais_protege_vigia(d, **_op) -> str:
    F = fiscais(d)
    P = F["prioridade_pl"]
    pf = P["protege_flavio"]["locais"][:20]
    vl = P["vigia_lula"]["locais"][:20]
    tips = Tips()
    linhas = []
    for x in pf:
        linhas.append(
            [
                lugar(x) + " · " + nome_bonito(x["local"]),
                "onde o fiscal mais protege voto de Flávio",
                nome_bonito(x.get("endereco") or ""),
                inteiro(x["secoes"]),
                nivel_txt(x["nivel"]),
                f"índice {inteiro(x.get('indice'))}",
                "",
            ]
        )
    for x in vl:
        linhas.append(
            [
                lugar(x) + " · " + nome_bonito(x["local"]),
                "onde mais vigia voto atípico de Lula",
                nome_bonito(x.get("endereco") or ""),
                inteiro(x["secoes"]),
                nivel_txt(x["nivel"]),
                "",
                inteiro(x.get("excesso_votos_lula")),
            ]
        )
    tips.tabela(
        [
            "Local",
            "Lista",
            "Endereço",
            "Seções sinalizadas",
            "Nível",
            "Índice (pontuação × aptos)",
            "Votos de Lula acima da zona",
        ],
        linhas,
        sub=1,
    )
    n = max(len(pf), len(vl))
    hp = 34 + 26 * n + 16

    def pa(x0, y0, larg):
        return _painel_lista(
            pf,
            "indice",
            "Protege voto de Flávio",
            FLAVIO,
            x0,
            y0,
            larg,
            0,
            lambda v: inteiro(v),
        )

    def pv(x0, y0, larg):
        return _painel_lista(
            vl,
            "excesso_votos_lula",
            "Vigia voto atípico de Lula",
            LULA,
            x0,
            y0,
            larg,
            len(pf),
            lambda v: inteiro(v),
        )

    larga = (
        svg_abre(
            1100,
            hp,
            "Duas listas do PL: onde o fiscal protege voto de Flávio e onde vigia voto atípico de Lula",
            "À esquerda, os 20 locais de maior índice em municípios de margem até 5 pontos; à direita, os 20 locais com mais votos de Lula acima do resto da zona.",
        )
        + pa(0, 0, 545)
        + pv(555, 0, 545)
        + "</svg>"
    )
    estreita = (
        svg_abre(
            560,
            2 * hp + 10,
            "Duas listas do PL, empilhadas",
            "A lista de proteção em cima e a de vigilância embaixo.",
        )
        + pa(0, 0, 560)
        + pv(0, hp + 10, 560)
        + "</svg>"
    )
    legenda = (
        f"Proteger: {escape(P['protege_flavio'].get('criterio', ''))} ({escape(P['protege_flavio'].get('regra_municipio', ''))}). "
        f"Vigiar: {escape(P['vigia_lula'].get('criterio', ''))}. As duas são juízo editorial de alocação, sobre sinais que "
        "não são irregularidade. Fonte: fiscais.json, prioridade_pl."
    )
    return figura_html(
        "fiscais_protege_vigia",
        larga_estreita(larga, estreita),
        legenda,
        tips,
        modo="full",
    )


# ------------------------------------------------------------------ risco


@registra("fiscais_risco")
def fiscais_risco(d, **_op) -> str:
    F = fiscais(d)
    if not tem_risco(F):
        raise KeyError("secoes[].risco (contrato 1.1)")
    cont = {c: Counter() for c, _, _ in CAMADAS}
    sem_base = Counter()
    for s in F["secoes"]:
        if not isinstance(s.get("risco"), dict):
            sem_base[s["nivel"]] += 1
            continue
        for c in camadas(s):
            cont[c][s["nivel"]] += 1
    linhas = sorted(cont.items(), key=lambda kv: -sum(kv[1].values()))
    fontes = F.get("meta", {}).get("fontes_risco", [])
    tips = Tips()
    passo, topo, x0, w = 34, 44, 330, 1100
    h = topo + passo * (len(linhas) + 1) + 40
    vmax = max([sum(c.values()) for _, c in linhas] + [sum(sem_base.values()), 1])
    esc = escala(0, vmax, x0, w - 140)
    out = [
        svg_abre(
            w,
            h,
            "Seções sinalizadas por camada de risco do território, pelo nível do sinal",
            "Uma barra por camada de risco com as seções sinalizadas em que ela está presente; a última linha conta as "
            "seções sem base de risco, que ficam como desconhecidas, não como zero.",
        ),
        t(x0, 24, "Seções sinalizadas com a camada presente", 14, MUTED, weight="600"),
    ]
    for v in ticks(0, vmax, 5):
        out.append(ln(esc(v), topo - 6, esc(v), h - 34, GRADE))
        out.append(t(esc(v), h - 16, inteiro(v), 13, MUTED, "middle", mono=True))
    todas = [*linhas, ("sem_base", sem_base)]
    for i, (c, cnt) in enumerate(todas):
        y = topo + i * passo
        rot = "sem base de risco (desconhecido)" if c == "sem_base" else ROT_CAMADA[c]
        k = tips.add(
            ficha(
                rot,
                "",
                [("Seções", inteiro(sum(cnt.values())))]
                + [(nivel_txt(n), inteiro(cnt.get(n, 0))) for n in NIVEIS],
                "Risco é contexto para o fiscal se proteger e planejar, não indício.",
            )
        )
        out.append(
            t(x0 - 10, y + 21, rot, 14, INK if c != "sem_base" else MUTED, "end")
        )
        out.append(
            _empilhada(
                x0, y + 6, passo - 12, [(n, cnt.get(n, 0)) for n in NIVEIS], esc, k
            )
        )
        out.append(
            t(
                esc(sum(cnt.values())) + 8,
                y + 22,
                inteiro(sum(cnt.values())),
                13.5,
                INK,
                mono=True,
            )
        )
    out.append("</svg>")
    cob = "".join(
        f"<li><b>{escape(f.get('base', ''))}</b>: cobertura {escape(str(f.get('cobertura', 's/d')))}, "
        f"{escape(str(f.get('data', 's/d')))}</li>"
        for f in fontes
    )
    apos = _legenda_niveis() + (
        f'<div class="fig-leg"><b class="leg-tit">Cobertura de cada base</b><ul class="fs-cob">{cob}</ul></div>'
        if cob
        else ""
    )
    legenda = (
        "Uma seção pode ter várias camadas. Onde a base não cobre o município, o campo fica desconhecido e a seção "
        "entra na última linha, nunca como ausência de risco. Validar com a PM e o TRE local. Fonte: fiscais.json, "
        "secoes[].risco e meta.fontes_risco."
    )
    return figura_html(
        "fiscais_risco",
        "".join(out),
        legenda,
        tips,
        minw=720,
        apos=apos,
        foco=(0, esc(vmax) + 60, x0),
    )
