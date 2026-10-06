"""Figuras do capítulo 13 (onde colocar fiscal), parte 1: critérios, UFs, municípios,
locais, seções de nível alta, as duas listas do PL e o contexto de risco.

Lê `fiscais.json` (contrato em `analysis/apuracao_2026/CONTRATO_FISCAIS.md`). Nenhum
número digitado: tudo sai do JSON. O bloco `risco` (contrato 1.1) é opcional: sem ele,
as colunas de risco somem e `fiscais_risco` fica pendente, sem derrubar o resto. O mapa
navegável e os mapas por UF estão em `pagina_fig_fiscais_b.py`; cartões das seções,
listas do PL e risco, em `pagina_fig_fiscais_c.py`.
"""

from __future__ import annotations

from collections import Counter
from html import escape

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    GRADE,
    INK,
    MUTED,
    Tips,
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
    r,
    registra,
    sobre,
    svg_abre,
    t,
    ticks,
)

NIVEIS = ("alta", "media", "baixa")
ROT_NIVEL = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
COR_NIVEL = {"alta": "#7a3500", "media": "#c27a1d", "baixa": "#a3a294"}
RISCOS = ("alto", "medio", "baixo")
ROT_RISCO = {"alto": "Alto", "medio": "Médio", "baixo": "Baixo", "": "Sem base"}
COR_RISCO = {"alto": "#5b2a86", "medio": "#9a7cc0", "baixo": "#cfc6dd", "": "#d8d4c8"}
# camada de risco: (código, rótulo curto, teste sobre o bloco `risco`)
CAMADAS = (
    ("terra_indigena", "terra indígena", lambda x: x.get("terra_indigena")),
    ("quilombo", "quilombo", lambda x: x.get("quilombo")),
    ("favela", "favela ou comunidade", lambda x: x.get("favela")),
    ("prisional", "unidade prisional", lambda x: x.get("unidade_prisional")),
    ("rural", "zona rural", lambda x: x.get("rural_urbano") == "rural"),
    ("fronteira", "fronteira", lambda x: x.get("fronteira")),
    ("garimpo", "garimpo", lambda x: x.get("garimpo")),
    (
        "crime",
        "crime organizado em mapeamento público",
        lambda x: bool(x.get("crime_organizado"))
        and not str(x.get("crime_organizado")).lower().startswith("sem"),
    ),
    (
        "homicidios",
        "homicídios no quintil mais alto",
        lambda x: x.get("homicidios_quintil") == 5,
    ),
)
ROT_CAMADA = {c: rot for c, rot, _ in CAMADAS}
NUMC = ' class="num"'


def fiscais(d) -> dict:
    return dado(d, "fiscais")


def nivel_txt(n: str | None) -> str:
    return ROT_NIVEL.get(n or "", n or "")


def risco_nivel(x: dict) -> str:
    """Nível de risco fiscal do item (seção ou local), '' quando a base não existe."""
    rr = x.get("risco")
    return (rr or {}).get("nivel_risco_fiscal") or "" if isinstance(rr, dict) else ""


def camadas(x: dict) -> list[str]:
    """Camadas de risco presentes no item; base ausente devolve lista vazia."""
    rr = x.get("risco")
    if not isinstance(rr, dict):
        return []
    return [c for c, _, teste in CAMADAS if teste(rr)]


def tem_risco(F: dict) -> bool:
    return any(isinstance(s.get("risco"), dict) for s in F.get("secoes", []))


def risco_txt(x: dict) -> str:
    """'Alto: terra indígena, fronteira' ou 'sem base' (desconhecido, nunca zero)."""
    n = risco_nivel(x)
    if not n:
        return "sem base"
    cam = [ROT_CAMADA[c] for c in camadas(x)]
    return ROT_RISCO.get(n, n) + (": " + ", ".join(cam) if cam else "")


def chips_risco(x: dict) -> str:
    n = risco_nivel(x)
    if not n:
        return '<span class="fs-chip fs-chip-vazio">sem base</span>'
    out = f'<span class="fs-chip fs-risco-{n}">{escape(ROT_RISCO.get(n, n))}</span>'
    out += "".join(
        f'<span class="fs-chip">{escape(ROT_CAMADA[c])}</span>' for c in camadas(x)
    )
    return out


def lugar(x: dict) -> str:
    return f"{nome_bonito(x['municipio'])} ({x['uf']})"


def criterios_txt(cr) -> str:
    """{'a': 2, 'b': 1} vira 'a×2, b'; lista vira 'a, b'."""
    if isinstance(cr, dict):
        return ", ".join(f"{k}×{v}" if v > 1 else k for k, v in sorted(cr.items()) if v)
    return ", ".join(cr or [])


def links(x: dict) -> str:
    lm = x.get("link_mapa") or {}
    if not lm and x.get("lat") is not None:
        lm = {
            "osm": f"https://www.openstreetmap.org/?mlat={x['lat']}&mlon={x['lon']}#map=17/{x['lat']}/{x['lon']}",
            "google": f"https://www.google.com/maps?q={x['lat']},{x['lon']}",
        }
    if not lm:
        return "sem coordenada"
    return (
        f'<a href="{escape(lm["osm"])}" target="_blank" rel="noopener">OSM ↗</a> '
        f'<a href="{escape(lm["google"])}" target="_blank" rel="noopener">Google ↗</a>'
    )


def corta(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _empilhada(
    x0: float, y: float, h: float, partes: list[tuple[str, float]], esc, k: str
) -> str:
    out, x = [], x0
    for nivel, v in partes:
        w = esc(v) - esc(0)
        if w > 0:
            out.append(r(x, y, w, h, COR_NIVEL[nivel]))
            x += w
    return hit("".join(out) + area(x0, y - 3, max(x - x0, 6), h + 6), k)


def _legenda_niveis(titulo: str = "Nível do sinal") -> str:
    return legenda_html([(ROT_NIVEL[n], COR_NIVEL[n]) for n in NIVEIS], titulo)


# ------------------------------------------------------------------ critérios


@registra("fiscais_criterios")
def fiscais_criterios(d, **_op) -> str:
    F = fiscais(d)
    crit = sorted(F["criterios"], key=lambda c: -c["secoes"])
    tips = Tips()
    passo, topo, x0, w = 34, 44, 360, 1100
    vmax = max((c["secoes"] for c in crit), default=1) or 1
    esc = escala(0, vmax, x0, w - 130)
    h = topo + passo * len(crit) + 40
    out = [
        svg_abre(
            w,
            h,
            "Seções sinalizadas por critério, empilhadas pelo nível",
            "Uma barra por critério com o número de seções em que ele disparou; a cor separa o nível final da seção. "
            "Uma seção pode disparar mais de um critério.",
        ),
        t(x0, 24, "Seções em que o critério disparou", 14, MUTED, weight="600"),
    ]
    for v in ticks(0, vmax, 5):
        out.append(ln(esc(v), topo - 6, esc(v), h - 34, GRADE))
        out.append(t(esc(v), h - 16, inteiro(v), 13, MUTED, "middle", mono=True))
    for i, c in enumerate(crit):
        y = topo + i * passo
        k = tips.add(
            ficha(
                f"{c['id']}. {c['nome']}",
                f"peso {c['peso']}",
                [
                    ("Seções", inteiro(c["secoes"])),
                    *(
                        (nivel_txt(n), inteiro(c["secoes_por_nivel"].get(n, 0)))
                        for n in NIVEIS
                    ),
                    ("Só este critério", inteiro(c.get("so_este"))),
                    ("Aptos nessas seções", inteiro(c.get("aptos"))),
                ],
                f"Explicação comum: {c.get('explicacao_comum', '')} O que conferir: {c.get('o_que_conferir', '')}",
            )
        )
        out.append(
            t(x0 - 12, y + 21, corta(f"{c['id']}. {c['nome']}", 44), 14, INK, "end")
        )
        partes = [(n, c["secoes_por_nivel"].get(n, 0)) for n in NIVEIS]
        out.append(_empilhada(x0, y + 6, passo - 12, partes, esc, k))
        out.append(
            t(esc(c["secoes"]) + 8, y + 22, inteiro(c["secoes"]), 13.5, INK, mono=True)
        )
    out.append("</svg>")
    linhas = "".join(
        f"<tr><th scope=\"row\">{escape(c['id'])}. {escape(c['nome'])}</th>"
        f"<td class=\"num\">{inteiro(c['secoes'])}</td>"
        f"<td>{escape(c.get('explicacao_comum', ''))}</td>"
        f"<td>{escape(c.get('o_que_conferir', ''))}</td></tr>"
        for c in crit
    )
    tabela = (
        '<div class="table-scroll" tabindex="0"><table class="fs-crit"><caption>Cada critério com a '
        "explicação comum, que não exige nada de errado, e o que o fiscal confere.</caption>"
        '<thead><tr><th scope="col">Critério</th><th scope="col" class="num">Seções</th>'
        '<th scope="col">Explicação comum</th><th scope="col">O que o fiscal confere</th></tr></thead>'
        f"<tbody>{linhas}</tbody></table></div>"
    )
    legenda = (
        f"{len(crit)} critérios declarados no JSON, com a regra e o limiar exatos em <code>meta.criterios</code>. "
        "As barras não somam o total de seções, porque uma seção pode disparar vários critérios. "
        "Fonte: fiscais.json."
    )
    return figura_html(
        "fiscais_criterios",
        "".join(out),
        legenda,
        tips,
        minw=760,
        apos=_legenda_niveis() + tabela,
        foco=(x0 - 340, esc(vmax) + 60, x0),
    )


# ------------------------------------------------------------------ por UF


@registra("fiscais_por_uf")
def fiscais_por_uf(d, **_op) -> str:
    F = fiscais(d)
    ufs = sorted(
        (u for u in F["por_uf"] if u.get("secoes")), key=lambda u: -u["secoes"]
    )
    tips = Tips()
    passo, topo, x0, w = 26, 40, 210, 1100
    h = topo + passo * len(ufs) + 40
    vs = max((u["secoes"] for u in ufs), default=1) or 1
    va = max((u["aptos_secoes"] for u in ufs), default=1) or 1
    es, ea = escala(0, vs, x0, w - 150), escala(0, va, x0, w - 150)
    out = [
        svg_abre(
            w,
            h,
            "Seções sinalizadas por UF, pelo nível, e o eleitorado que elas cobrem",
            "Uma barra por UF, da que tem mais seções sinalizadas para a que tem menos; a outra aba mostra os aptos "
            "dessas seções.",
        )
    ]
    for aba, e, vmax, rot in (
        ("secoes", es, vs, "Seções sinalizadas"),
        ("aptos", ea, va, "Aptos nas seções sinalizadas"),
    ):
        oculto = "" if aba == "secoes" else ' display="none"'
        g = [
            f'<g data-alt-show="{aba}"{oculto}>',
            t(x0, 22, rot, 14, MUTED, "start", "600"),
        ]
        for v in ticks(0, vmax, 5):
            g.append(ln(e(v), topo - 6, e(v), h - 34, GRADE))
            g.append(
                t(
                    e(v),
                    h - 16,
                    inteiro(v) if aba == "secoes" else f"{num(v / 1000, 0)} mil",
                    13,
                    MUTED,
                    "middle",
                    mono=True,
                )
            )
        for i, u in enumerate(ufs):
            y = topo + i * passo
            k = f"r{i}"
            if aba == "secoes":
                partes = [(n, u.get(n, 0)) for n in NIVEIS]
                g.append(_empilhada(x0, y + 4, passo - 8, partes, e, k))
                g.append(
                    t(
                        e(u["secoes"]) + 8,
                        y + 18,
                        inteiro(u["secoes"]),
                        13,
                        INK,
                        mono=True,
                    )
                )
            else:
                g.append(
                    hit(
                        r(x0, y + 4, e(u["aptos_secoes"]) - x0, passo - 8, "#4d5a52")
                        + area(x0, y + 1, max(e(u["aptos_secoes"]) - x0, 6), passo - 2),
                        k,
                    )
                )
                g.append(
                    t(
                        e(u["aptos_secoes"]) + 8,
                        y + 18,
                        inteiro(u["aptos_secoes"]),
                        13,
                        INK,
                        mono=True,
                    )
                )
        g.append("</g>")
        out.append("".join(g))
    for i, u in enumerate(ufs):
        y = topo + i * passo
        out.append(t(x0 - 10, y + 18, NOME_UF.get(u["uf"], u["uf"]), 13.5, INK, "end"))
    out.append("</svg>")
    tips.tabela(
        [
            "UF",
            "Seções sinalizadas",
            "Alta",
            "Média",
            "Baixa",
            "Locais",
            "Locais de nível alta",
            "Aptos nessas seções",
            "Pontuação somada",
            "Seções da UF",
        ],
        [
            [
                NOME_UF.get(u["uf"], u["uf"]),
                inteiro(u["secoes"]),
                inteiro(u.get("alta")),
                inteiro(u.get("media")),
                inteiro(u.get("baixa")),
                inteiro(u.get("locais")),
                inteiro(u.get("locais_alta")),
                inteiro(u.get("aptos_secoes")),
                inteiro(u.get("pontuacao_soma")),
                inteiro(u.get("secoes_universo")),
            ]
            for u in ufs
        ],
    )
    ctl = botoes(
        [("secoes", "Seções por nível"), ("aptos", "Eleitorado coberto")],
        "secoes",
        "Mostrar",
    )
    legenda = (
        f"{len(ufs)} UFs com ao menos uma seção sinalizada, da maior contagem para a menor. "
        "Aptos são os eleitores das seções sinalizadas, não os do local inteiro. Fonte: fiscais.json, por_uf."
    )
    return figura_html(
        "fiscais_por_uf",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=720,
        apos=_legenda_niveis(),
        foco=(0, es(vs) + 60, x0),
    )


# ------------------------------------------------------------------ municípios


def _risco_municipio(F: dict) -> dict[tuple[str, str], dict]:
    """Nível de risco mais alto e camadas presentes entre as seções sinalizadas."""
    out: dict[tuple[str, str], dict] = {}
    for s in F.get("secoes", []):
        n = risco_nivel(s)
        if not n:
            continue
        o = out.setdefault((s["uf"], s["mun_tse"]), {"n": "baixo", "c": Counter()})
        if RISCOS.index(n) < RISCOS.index(o["n"]):
            o["n"] = n
        o["c"].update(camadas(s))
    return out


def _celula(v, texto: str | None = None, classe: str = "num") -> str:
    tx = texto if texto is not None else inteiro(v)
    dv = f' data-v="{v}"' if isinstance(v, (int, float)) else ""
    return f'<td class="{classe}"{dv}>{tx}</td>'


@registra("fiscais_municipios")
def fiscais_municipios(d, **_op) -> str:
    F = fiscais(d)
    mun = sorted(
        F["por_municipio"],
        key=lambda m: (m.get("posicao_pontuacao") or 10**6, -m["pontuacao_soma"]),
    )
    top = mun[:30]
    tips = Tips()
    passo, topo, x0, w = 26, 40, 300, 1100
    h = topo + passo * len(top) + 40
    vmax = max((m["secoes"] for m in top), default=1) or 1
    esc = escala(0, vmax, x0, w - 160)
    out = [
        svg_abre(
            w,
            h,
            "Os 30 municípios de maior pontuação somada",
            "Barras com as seções sinalizadas de cada município, empilhadas pelo nível, na ordem da pontuação somada.",
        ),
        t(
            x0,
            22,
            "Seções sinalizadas (ordem: pontuação somada)",
            14,
            MUTED,
            weight="600",
        ),
    ]
    for v in ticks(0, vmax, 5):
        out.append(ln(esc(v), topo - 6, esc(v), h - 34, GRADE))
        out.append(t(esc(v), h - 16, inteiro(v), 13, MUTED, "middle", mono=True))
    rm = _risco_municipio(F)
    for i, m in enumerate(top):
        y = topo + i * passo
        k = f"r{i}"
        out.append(t(x0 - 10, y + 18, corta(lugar(m), 36), 13.5, INK, "end"))
        partes = [(n, m.get(n, 0)) for n in NIVEIS]
        out.append(_empilhada(x0, y + 4, passo - 8, partes, esc, k))
        out.append(
            t(
                esc(m["secoes"]) + 8,
                y + 18,
                f"{inteiro(m['secoes'])} · {inteiro(m['pontuacao_soma'])} pts",
                13,
                INK,
                mono=True,
            )
        )
    out.append("</svg>")
    tips.tabela(
        [
            "Município",
            "Posição",
            "Seções sinalizadas",
            "Alta",
            "Média",
            "Baixa",
            "Locais",
            "Pontuação somada",
            "Flávio no município",
            "Lula no município",
            "Risco",
        ],
        [
            [
                lugar(m),
                f"{m.get('posicao_pontuacao', '')}º",
                inteiro(m["secoes"]),
                inteiro(m.get("alta")),
                inteiro(m.get("media")),
                inteiro(m.get("baixa")),
                inteiro(m.get("locais")),
                inteiro(m["pontuacao_soma"]),
                pct(m.get("flavio_pct"), 1),
                pct(m.get("lula_pct"), 1),
                _risco_mun_txt(rm.get((m["uf"], m["mun_tse"]))),
            ]
            for m in top
        ],
    )
    risco = tem_risco(F)
    cab = [
        ("#", True),
        ("Município", False),
        ("UF", False),
        ("Seções sinalizadas", True),
        ("Alta", True),
        ("Média", True),
        ("Locais", True),
        ("Aptos nessas seções", True),
        ("Pontuação", True),
        ("Flávio %", True),
        ("Lula %", True),
    ] + ([("Risco", False)] if risco else [])
    th = "".join(f'<th scope="col"{NUMC if n else ""}>{escape(c)}</th>' for c, n in cab)
    corpo = []
    for m in mun[:100]:
        rmun = rm.get((m["uf"], m["mun_tse"]))
        cel = (
            _celula(m.get("posicao_pontuacao"))
            + f"<th scope=\"row\">{escape(nome_bonito(m['municipio']))}</th>"
            + f"<td>{m['uf']}</td>"
            + _celula(m["secoes"])
            + _celula(m.get("alta", 0))
            + _celula(m.get("media", 0))
            + _celula(m.get("locais", 0))
            + _celula(m.get("aptos_secoes", 0))
            + _celula(m["pontuacao_soma"])
            + _celula(m.get("flavio_pct"), num(m.get("flavio_pct"), 1))
            + _celula(m.get("lula_pct"), num(m.get("lula_pct"), 1))
        )
        if risco:
            cel += f'<td data-v="{_ordem_risco(rmun)}">{_chips_mun(rmun)}</td>'
        corpo.append(f"<tr>{cel}</tr>")
    tabela = (
        '<div class="table-scroll fs-tab" tabindex="0"><table data-ordena="1" data-sortable>'
        "<caption>Os 100 municípios de maior pontuação somada; clique no cabeçalho para ordenar. "
        "Flávio e Lula em % dos válidos do município inteiro.</caption>"
        f"<thead><tr>{th}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"
    )
    legenda = (
        "Pontuação somada é a soma dos pesos dos critérios de cada seção sinalizada do município; "
        "município grande soma mais por ter mais seções, e a tabela traz a contagem ao lado para isso ficar visível. "
        "Fonte: fiscais.json, por_municipio."
    )
    return figura_html(
        "fiscais_municipios",
        "".join(out),
        legenda,
        tips,
        minw=760,
        apos=_legenda_niveis() + tabela,
        foco=(0, esc(vmax) + 100, x0),
    )


def _risco_mun_txt(o: dict | None) -> str:
    if not o:
        return "sem base"
    cam = [ROT_CAMADA[c] for c, _ in o["c"].most_common()]
    return ROT_RISCO[o["n"]] + (": " + ", ".join(cam) if cam else "")


def _chips_mun(o: dict | None) -> str:
    if not o:
        return '<span class="fs-chip fs-chip-vazio">sem base</span>'
    return (
        f'<span class="fs-chip fs-risco-{o["n"]}">{ROT_RISCO[o["n"]]}</span>'
        + "".join(
            f'<span class="fs-chip">{escape(ROT_CAMADA[c])}</span>'
            for c, _ in o["c"].most_common(3)
        )
    )


def _ordem_risco(o) -> int:
    if not o:
        return 9
    n = o if isinstance(o, str) else o["n"]
    return RISCOS.index(n) if n in RISCOS else 9


# ------------------------------------------------------------------ downloads


def exportaveis(F: dict) -> dict[str, dict]:
    """Exportáveis de `meta.exportaveis` pelo caminho publicado (`assets/...`)."""
    out = {}
    for e in F.get("meta", {}).get("exportaveis", []):
        out[e["caminho"].removeprefix("docs/")] = e
    return out


def tamanho(b: int | None) -> str:
    if not b:
        return "tamanho s/d"
    if b >= 1_000_000:
        return f"{num(b / 1_000_000, 1)} MB"
    return f"{num(b / 1000, 0)} KB"


DOWNLOADS = (
    ("assets/fiscais_2026.xlsx", "Baixar Excel (lista completa)"),
    ("assets/fiscais_2026.csv", "CSV por seção"),
    ("assets/fiscais_2026_por_local.csv", "CSV por local"),
)


def bloco_download(F: dict, frase: str = "") -> str:
    ex = exportaveis(F)
    itens = []
    for cam, rot in DOWNLOADS:
        e = ex.get(cam, {})
        det = f"{tamanho(e.get('bytes'))}"
        if e.get("linhas"):
            det += f", {inteiro(e['linhas'])} linhas"
        sha = e.get("sha256") or ""
        itens.append(
            f'<li><a class="fs-baixar" href="{cam}" download>{escape(rot)}</a>'
            f'<span class="fs-det">{det}{f"<br>SHA-256 <code>{sha}</code>" if sha else ""}</span></li>'
        )
    return (
        '<aside class="io fs-down"><b>Baixe a lista</b>'
        f'<ul class="fs-downs">{"".join(itens)}</ul>'
        + (f"<p>{frase}</p>" if frase else "")
        + "<p>Os CSV usam ponto e vírgula e vírgula decimal e abrem direto no Excel em português; "
        "o Excel traz as abas Leia-me, Seções, Locais, Municípios, UFs e Critérios.</p></aside>"
    )


# ------------------------------------------------------------------ locais


@registra("fiscais_locais")
def fiscais_locais(d, **_op) -> str:
    F = fiscais(d)
    loc = [x for x in F["por_local"] if x.get("secoes", 0) >= 3]
    risco = tem_risco(F)
    # histograma: locais por número de seções sinalizadas, empilhado pelo nível do local
    faixas = ["3", "4", "5", "6 a 9", "10 ou mais"]

    def faixa(n: int) -> str:
        return "10 ou mais" if n >= 10 else "6 a 9" if n >= 6 else str(n)

    cont = {f: Counter() for f in faixas}
    for x in loc:
        cont[faixa(x["secoes"])][x["nivel"]] += 1
    tips = Tips()
    w, h, x0 = 1100, 60 + 34 * len(faixas) + 30, 210
    vmax = max((sum(c.values()) for c in cont.values()), default=1) or 1
    esc = escala(0, vmax, x0, w - 130)
    out = [
        svg_abre(
            w,
            h,
            "Locais de votação com três ou mais seções sinalizadas",
            "Quantos locais têm 3, 4, 5, 6 a 9 e 10 ou mais seções sinalizadas, pelo nível mais alto entre as seções do local.",
        ),
        t(
            x0,
            24,
            "Locais (nível do local = a seção mais alta)",
            14,
            MUTED,
            weight="600",
        ),
    ]
    for i, f in enumerate(faixas):
        y = 44 + i * 34
        c = cont[f]
        k = tips.add(
            ficha(
                f"Locais com {f} seções sinalizadas",
                "",
                [("Locais", inteiro(sum(c.values())))]
                + [(nivel_txt(n), inteiro(c.get(n, 0))) for n in NIVEIS],
            )
        )
        out.append(t(x0 - 10, y + 20, f"{f} seções", 14, INK, "end"))
        out.append(
            _empilhada(x0, y + 6, 22, [(n, c.get(n, 0)) for n in NIVEIS], esc, k)
        )
        out.append(
            t(
                esc(sum(c.values())) + 8,
                y + 22,
                inteiro(sum(c.values())),
                13.5,
                INK,
                mono=True,
            )
        )
    out.append("</svg>")
    cab = [
        "UF",
        "Município",
        "Local",
        "Endereço",
        "Bairro",
        "Seções",
        "Seções sinalizadas",
        "Critérios",
        "Nível",
    ]
    if risco:
        cab.append("Risco")
    cab.append("Mapa")
    numericas = {"Seções"}
    th = "".join(
        f'<th scope="col"{NUMC if c in numericas else ""}>{escape(c)}</th>' for c in cab
    )
    corpo = []
    for x in loc:
        cel = (
            f"<td>{x['uf']}</td><td>{escape(nome_bonito(x['municipio']))}</td>"
            f"<th scope=\"row\">{escape(nome_bonito(x['local']))}</th>"
            f"<td>{escape(nome_bonito(x.get('endereco') or ''))}</td>"
            f"<td>{escape(nome_bonito(x.get('bairro') or ''))}</td>"
            + _celula(x["secoes"])
            + f"<td>{escape(', '.join(str(s) for s in x.get('lista_secoes', [])))}<br><small>zona {x['zona']}</small></td>"
            + f"<td>{escape(criterios_txt(x.get('criterios')))}</td>"
            + f'<td data-v="{NIVEIS.index(x["nivel"])}"><span class="fs-chip fs-nivel-{x["nivel"]}">{nivel_txt(x["nivel"])}</span></td>'
        )
        if risco:
            cel += f'<td data-v="{_ordem_risco(risco_nivel(x) or None)}">{chips_risco(x)}</td>'
        cel += f'<td class="fs-links">{links(x)}</td>'
        corpo.append(f"<tr>{cel}</tr>")
    tabela = (
        '<div class="table-scroll fs-tab fs-tab-locais" tabindex="0"><table data-ordena="1" data-sortable>'
        f"<caption>Todos os {inteiro(len(loc))} locais com três ou mais seções sinalizadas, na ordem da pontuação somada; "
        "clique no cabeçalho para ordenar. Os links abrem o mapa externo em nova aba.</caption>"
        f"<thead><tr>{th}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"
    )
    legenda = (
        f"{inteiro(len(loc))} locais de votação com três ou mais seções sinalizadas (critério l). "
        "Endereço, bairro e coordenada vêm do cadastro de locais do TSE. Fonte: fiscais.json, por_local."
    )
    return figura_html(
        "fiscais_locais",
        "".join(out),
        legenda,
        tips,
        controles=bloco_download(F),
        minw=720,
        apos=_legenda_niveis("Nível do local") + tabela,
    )


__all__ = [
    "COR_NIVEL",
    "COR_RISCO",
    "NIVEIS",
    "ROT_NIVEL",
    "ROT_RISCO",
    "bloco_download",
    "camadas",
    "chips_risco",
    "exportaveis",
    "fiscais",
    "links",
    "lugar",
    "nivel_txt",
    "risco_nivel",
    "risco_txt",
    "sobre",
    "tem_risco",
]
