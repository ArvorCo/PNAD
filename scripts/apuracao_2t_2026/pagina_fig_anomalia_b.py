"""Figuras do capítulo "Grupos" do dossiê do 2º turno, parte 2: o grupo atípico.

- ``fig_pca``: dispersão da amostra de seções nos dois componentes principais, cor
  pelo grupo (ou pela região), as menos prováveis com contorno e a elipse do grupo
  atípico (figura pesada, em ``<noscript class="fig-src">`` quando passa do limite);
- ``fig_voto``: fatia de Flávio no 2º turno contra as vizinhas e diferença em
  diferenças contra o 1º turno, com IC de 95% por bootstrap;
- ``tabela_sinais`` e ``tabela_modelo``: cruzamento dos grupos com os sinais do
  capítulo anterior e com o modelo da urna;
- ``fig_mapa``: municípios com seções do grupo atípico sobre o contorno do Brasil
  (lê o arquivo pesado; sem ele, aviso padrão);
- ``tabela_amostras``: as 50 amostras do grupo atípico com link para o Politize-se.
"""

from __future__ import annotations

import math
import re
from html import escape

from apuracao_2026.pagina_comum import inteiro, num, tabela
from apuracao_2026.pagina_fig_base import (
    COR_REGIAO,
    GRADE,
    INK,
    LIMA,
    MUTED,
    REGIOES,
    Tips,
    botoes,
    chip,
    escala,
    ficha,
    figura_html,
    legenda_html,
    ln,
    nome_bonito,
    svg_abre,
    t,
    ticks,
)
from apuracao_2026.pagina_fig_secoes_c import CINZA_ELIPSE, elipse_cov, topo_elipse
from apuracao_2026.pagina_mapas import pontos_brasil

from . import pagina_fig_anomalia_base as B
from .pagina_fig_espelho import efeitos

LULA_TXT = "#b02f21"
FLAVIO_TXT = "#1457aa"


def pendente(nome: str, motivo: str) -> str:
    """Figura em preparação, no formato de ``pagina_fig_base.registra``."""
    return (
        f'<figure class="pendente" id="fig-{nome}"><figcaption>figura em preparação: '
        f"<code>{escape(nome)}</code> ({escape(motivo)})</figcaption></figure>"
    )


# ------------------------------------------------------------------ PCA


def _pontos(P: dict) -> list[dict]:
    cols = P["colunas"]
    pts = [dict(zip(cols, p, strict=False)) for p in P["pontos"]]
    for p in pts:
        p["top"] = bool(p.get("top") or p.get("top200") or p.get("top300"))
        p["cluster"] = int(p["cluster"])
    return pts


def _nivel(P: dict) -> float:
    """Quantos desvios os semieixos publicados cobrem (`elipse_nivel`, texto ou número)."""
    v = P.get("elipse_nivel")
    if isinstance(v, (int, float)) and v > 0:
        return float(v)
    m = re.match(r"\s*([\d,.]+)", str(v or ""))
    if m:
        try:
            n = float(m.group(1).replace(",", "."))
            if n > 0:
                return n
        except ValueError:
            pass
    return 2.0


def _cov_de(e: dict, nivel: float = 2.0) -> tuple[float, float, float]:
    """(sxx, syy, sxy) da elipse publicada: por `cov` ou por (rx, ry, ang) a `nivel` desvios."""
    if "cov" in e:
        (sxx, sxy), (_, syy) = e["cov"]
        return float(sxx), float(syy), float(sxy)
    a = math.radians(float(e.get("ang") or 0))
    l1, l2 = (float(e["rx"]) / nivel) ** 2, (float(e["ry"]) / nivel) ** 2
    c, s = math.cos(a), math.sin(a)
    return l1 * c * c + l2 * s * s, l1 * s * s + l2 * c * c, (l1 - l2) * s * c


def _elipse_grupo(P: dict, k: int, X, Y, pontos: list[dict]):
    e = next((e for e in P.get("elipses") or [] if int(e["cluster"]) == k), None)
    ax = X(1.0) - X(0.0)
    ay = Y(0.0) - Y(1.0)
    if e is not None:
        sxx, syy, sxy = _cov_de(e, _nivel(P))
        cx, cy = float(B.g(e, "cx", "x")), float(B.g(e, "cy", "y"))
        return elipse_cov(X(cx), Y(cy), ax * ax * sxx, ay * ay * syy, -ax * ay * sxy)
    pts = [(p["x"], p["y"]) for p in pontos if p["cluster"] == k and not p["top"]]
    if len(pts) < 3:
        return None
    n = len(pts)
    mx, my = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts) / n
    syy = sum((p[1] - my) ** 2 for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
    return elipse_cov(X(mx), Y(my), ax * ax * sxx, ay * ay * syy, -ax * ay * sxy)


def _centros(P: dict, pontos: list[dict]) -> list[dict]:
    if P.get("centros"):
        return [
            {"cluster": int(c["cluster"]), "x": c["x"], "y": c["y"]}
            for c in P["centros"]
        ]
    acc: dict[int, list[float]] = {}
    for p in pontos:
        a = acc.setdefault(p["cluster"], [0.0, 0.0, 0])
        a[0] += p["x"]
        a[1] += p["y"]
        a[2] += 1
    return [
        {"cluster": k, "x": a[0] / a[2], "y": a[1] / a[2]}
        for k, a in sorted(acc.items())
        if a[2]
    ]


def _larg_chip(texto: str, size: float = 13) -> float:
    return 0.53 * size * len(texto) + 12


def _colide(a, b) -> bool:
    return not (
        a[0] + a[2] + 4 <= b[0]
        or b[0] + b[2] + 4 <= a[0]
        or a[1] + a[3] + 3 <= b[1]
        or b[1] + b[3] + 3 <= a[1]
    )


def fig_pca(A: dict) -> str:
    P = A.get("pca") or {}
    if not P.get("pontos"):
        raise KeyError("pca.pontos")
    pontos = _pontos(P)
    w, h = 780, 620
    x0, x1, y0, y1 = 70, 760, 24, 560
    xs, ys = [p["x"] for p in pontos], [p["y"] for p in pontos]
    pad_x = (max(xs) - min(xs)) * 0.04 or 1
    pad_y = (max(ys) - min(ys)) * 0.04 or 1
    lox, hix, loy, hiy = (
        min(xs) - pad_x,
        max(xs) + pad_x,
        min(ys) - pad_y,
        max(ys) + pad_y,
    )
    X, Y = escala(lox, hix, x0, x1), escala(loy, hiy, y1, y0)
    ve = P.get("variancia_explicada") or [None, None]
    ve_txt = ["s/d" if v is None else num(100 * float(v), 1) for v in ve[:2]]
    k = B.k_de(A)
    out = [
        svg_abre(
            w,
            h,
            f"{B.extenso(k).capitalize()} grupos de seções na projeção em dois componentes principais",
            "Cada ponto é uma seção da amostra; cor pelo grupo da mistura gaussiana; as seções menos prováveis "
            "têm contorno preto; a elipse cinza tracejada marca o grupo mais atípico (centro e covariância, dois desvios).",
            ' data-near="1"',
        )
    ]
    for v in ticks(lox, hix, 6):
        out.append(ln(X(v), y0, X(v), y1, GRADE, 0.8))
        out.append(t(X(v), y1 + 20, num(v, 1), 13, MUTED, "middle", mono=True))
    for v in ticks(loy, hiy, 6):
        out.append(ln(x0, Y(v), x1, Y(v), GRADE, 0.8))
        out.append(t(x0 - 8, Y(v) + 5, num(v, 1), 13, MUTED, "end", mono=True))
    out.append(
        t(
            (x0 + x1) / 2,
            h - 22,
            f"Componente principal 1 ({ve_txt[0]}% da variância)",
            14,
            INK,
            "middle",
            "600",
        )
    )
    yy = (y0 + y1) / 2
    out.append(
        t(
            20,
            yy,
            f"Componente 2 ({ve_txt[1]}%)",
            14,
            INK,
            "middle",
            "600",
            extra=f' transform="rotate(-90 20 {yy:.0f})"',
        )
    )
    ma = B.id_atipico(A)
    el = _elipse_grupo(P, ma, X, Y, pontos)
    grupos: dict[tuple[int, str], list[str]] = {}
    linhas, xy, top = [], [], []
    n_top = 0
    for p in pontos:
        x, y = X(p["x"]), Y(p["y"])
        kk, reg = p["cluster"], B.regiao_da_uf(p.get("uf"))
        if p["top"]:
            top.append((x, y, kk, reg))
            n_top += 1
            raio = 4.5
        else:
            grupos.setdefault((kk, reg), []).append(f"M{x:.0f} {y:.0f}h0")
            raio = 2
        linha = [
            f"Grupo {kk + 1} · {p.get('uf') or 's/d'}",
            "entre as menos prováveis" if p["top"] else "",
        ]
        linhas.append(linha)
        xy.append([round(x), round(y), raio])
    for (kk, reg), segs in sorted(grupos.items()):
        out.append(
            f'<path d="{"".join(segs)}" stroke="{B.cor(kk)}" data-as="regiao>{COR_REGIAO.get(reg, MUTED)}" '
            'stroke-width="4" stroke-linecap="round" stroke-opacity="0.5" fill="none"/>'
        )
    for x, y, kk, reg in top:
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{B.cor(kk)}" '
            f'data-af="regiao>{COR_REGIAO.get(reg, MUTED)}" stroke="{INK}" stroke-width="1.3"/>'
        )
    caixas: list[tuple[float, float, float, float]] = []
    rot_el_svg = ""
    if el:
        cx, cy, rx, ry, ang = el
        out.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{max(ry, 6):.1f}" '
            f'transform="rotate({ang:.1f} {cx:.1f} {cy:.1f})" fill="{CINZA_ELIPSE}" fill-opacity="0.06" '
            f'stroke="{CINZA_ELIPSE}" stroke-width="2.2" stroke-dasharray="7 5" pointer-events="none"/>'
        )
        rot_el = f"Grupo {ma + 1}, o mais atípico"
        larg_el = _larg_chip(rot_el)
        bx_el, by_el = topo_elipse(cx, cy, rx, max(ry, 6), ang)
        y_el = min(max(by_el + 5, y0 + 17), y1 - 6)
        x_el = min(max(bx_el - larg_el / 2, x0 + 4), x1 - larg_el - 4)
        caixas.append((x_el, y_el - 15, larg_el, 21))
        rot_el_svg = f'<g pointer-events="none">{chip(x_el, y_el, rot_el, 13)}</g>'
    centros = _centros(P, pontos)
    caixas += [(X(c["x"]) - 8, Y(c["y"]) - 8, 16, 16) for c in centros]
    guias, cruzes, chips = [], [], []
    for c in sorted(centros, key=lambda c: Y(c["y"])):
        cx, cy = X(c["x"]), Y(c["y"])
        texto = f"Grupo {c['cluster'] + 1}"
        larg = _larg_chip(texto)
        bx = cx - 12 - larg if cx > x1 - 120 else cx + 12
        by, passo = cy - 12, -26
        while any(_colide((bx, by - 15, larg, 21), cx_) for cx_ in caixas):
            by += passo
            if by - 15 < y0:
                by, passo = cy + 30, 26
        caixas.append((bx, by - 15, larg, 21))
        guias.append(
            ln(cx, cy, bx + (larg if bx < cx else 0), by - 4, INK, 0.8)
            if abs(by - (cy - 12)) > 1
            else ""
        )
        cruzes.append(
            ln(cx - 8, cy, cx + 8, cy, INK, 3) + ln(cx, cy - 8, cx, cy + 8, INK, 3)
        )
        chips.append(chip(bx, by, texto, 13))
    out.append(
        f'<g pointer-events="none">{"".join(guias)}{"".join(cruzes)}{"".join(chips)}</g>'
    )
    out.append(rot_el_svg)
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        ["Seção", "Marca"], linhas, xy=xy, nota="rótulo de cada grupo no painel acima"
    )
    ctl = botoes(
        [("cluster", "Cor pelo grupo"), ("regiao", "Cor pela região")], "cluster", "Cor"
    )
    leg_cl = (
        '<div data-alt-show="cluster">'
        + legenda_html(
            [(B.rotulo_grupo(A, c["id"]), B.cor(c["id"])) for c in B.componentes(A)],
            "Grupo da mistura gaussiana",
        )
        + "</div>"
    )
    leg_rg = (
        '<div data-alt-show="regiao" hidden>'
        + legenda_html([(rg, COR_REGIAO[rg]) for rg in REGIOES], "Região da seção")
        + "</div>"
    )
    legenda = (
        f"Projeção de {inteiro(len(pontos))} seções (amostra estratificada por UF mais as {inteiro(n_top)} menos "
        f"prováveis, com contorno preto) nos dois primeiros componentes principais das nove frações padronizadas. "
        f"Mistura gaussiana com k = {k}, covariância completa. Elipse cinza tracejada: centro e covariância do grupo "
        "mais atípico, a dois desvios. O botão troca a cor do grupo pela região, para ver se grupo é geografia. "
        "Fonte: anomalia_ml.json."
    )
    return figura_html(
        "an_pca",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=640,
        dim=False,
        apos=leg_cl + leg_rg,
    )


# ------------------------------------------------------------------ voto do grupo atípico


def fig_voto(A: dict) -> str:
    fatia, ic_f = B.medida_voto(A, "fatia")
    did, ic_d = B.medida_voto(A, "did")
    if fatia is None and did is None:
        raise KeyError("mais_anomalo.voto")
    v = B.voto(A)
    itens = [
        {"nome": nome, "valor": val, "intervalo": ic}
        for nome, val, ic in [
            ("2º turno: grupo atípico contra vizinhas", fatia, ic_f),
            ("Entre turnos: diferença em diferenças", did, ic_d),
        ]
        if val is not None
    ]
    return efeitos(
        "an_voto",
        itens,
        "Lula e Flávio no grupo atípico contra as vizinhas",
        f"Grupo atípico: {inteiro(B.g(v, 'n', 'n_sinal_comparavel'))} seções comparáveis contra "
        f"{inteiro(B.g(v, 'n_vizinhas'))} vizinhas em {inteiro(B.g(v, 'n_municipios'))} municípios; "
        f"IC de 95% por bootstrap de {inteiro(B.g(v, 'bootstrap', 'reamostragens', padrao=2000))} reamostragens. "
        "Publicado qualquer que seja o sinal. Fonte: anomalia_ml.json.",
    )


def ficha_voto(nome: str, val: float, ic: tuple | None, v: dict) -> str:
    linhas = [("Diferença", B.pp_txt(val, 2))]
    if ic:
        linhas.append(("IC de 95%", f"{B.pp_txt(ic[0], 2)} a {B.pp_txt(ic[1], 2)}"))
    linhas += [
        ("Seções do grupo", inteiro(B.g(v, "n", "n_sinal_comparavel"))),
        ("Vizinhas", inteiro(B.g(v, "n_vizinhas"))),
    ]
    return ficha(nome, "grupo atípico contra vizinhas", linhas, B.ROTULO)


# ------------------------------------------------------------------ cruzamentos


def tabela_sinais(A: dict) -> str:
    ma = B.id_atipico(A)
    chaves = [
        k
        for k in B.SINAL_NOME
        if any(B.g(c.get("sinais") or {}, k) is not None for c in A["componentes"])
    ]
    if not chaves:
        return ""
    linhas = []
    for c in B.componentes(A):
        s = c.get("sinais") or {}
        nome = B.rotulo_grupo(A, c["id"], curto=True)
        if c["id"] == ma:
            nome = f"<b>{nome}</b> (atípico)"
        linhas.append(
            [nome, inteiro(c["secoes"]), *[B.pct_txt(B.g(s, k), 2) for k in chaves]]
        )
    return tabela(
        ["grupo", "seções", *[B.SINAL_NOME[k] for k in chaves]],
        linhas,
        "Parcela das seções de cada grupo com cada sinal do capítulo anterior (escore 0 a 6), BU do sistema "
        "de apuração, urna de contingência e mudança de local entre os turnos.",
    )


def tabela_modelo(A: dict) -> str:
    linhas_m = A.get("cluster_modelo") or []
    if not linhas_m:
        return ""
    ma = B.id_atipico(A)
    modelos = sorted({str(x["modelo"]) for x in linhas_m})
    por: dict[int, dict[str, float]] = {}
    for x in linhas_m:
        por.setdefault(int(x["cluster"]), {})[str(x["modelo"])] = x.get(
            "pct_do_cluster"
        )
    linhas = []
    for c in B.componentes(A):
        nome = B.rotulo_grupo(A, c["id"], curto=True)
        if c["id"] == ma:
            nome = f"<b>{nome}</b> (atípico)"
        linhas.append(
            [nome, *[B.pct_txt(por.get(c["id"], {}).get(m), 1) for m in modelos]]
        )
    return tabela(
        ["grupo", *modelos],
        linhas,
        f"Modelo da urna por grupo, % das seções do grupo. V de Cramér entre grupo e modelo: {num(A.get('cramer_v_modelo'), 2)}.",
    )


def tabela_seis_sinais(A: dict) -> str:
    """Os seis sinais do capítulo anterior dentro do grupo atípico contra o país."""
    seis = B.g(A["mais_anomalo"], "seis_sinais", padrao=[]) or []
    if not seis:
        return ""
    linhas = []
    for s in seis:
        razao = B.g(s, "razao")
        linhas.append(
            [
                escape(str(B.g(s, "descricao", "sinal", padrao=""))),
                inteiro(B.g(s, "secoes_no_grupo")),
                B.pct_txt(B.g(s, "pct_grupo"), 2),
                B.pct_txt(B.g(s, "pct_pais"), 2),
                "s/d" if razao is None else f"{num(razao, 2)}×",
            ]
        )
    return tabela(
        ["sinal", "seções do grupo com o sinal", "% no grupo", "% no país", "razão"],
        linhas,
        "Cada sinal operacional foi definido sem olhar o voto; razão acima de 1 significa que o grupo atípico "
        "concentra o sinal mais que o país. Concentração não é causa.",
    )


# ------------------------------------------------------------------ mapa


def fig_mapa(A: dict) -> str:
    try:
        agreg = B.atipicas_por_municipio(A)
    except ValueError as erro:
        return pendente("an_mapa", str(erro))
    if agreg is None:
        return pendente(
            "an_mapa", "arquivo pesado anomalia_secoes.json.gz ausente nesta máquina"
        )
    muns = B.municipios_politize()
    if not muns:
        return pendente(
            "an_mapa", "índice do Politize (coordenadas dos municípios) ausente"
        )
    ma = B.id_atipico(A)
    cor = B.cor(ma)
    com_coord = [
        x
        for x in agreg
        if muns.get((x["uf"], x["mun"]))
        and muns[(x["uf"], x["mun"])]["lat"] is not None
    ]
    if not com_coord:
        return pendente("an_mapa", "nenhum município do grupo com coordenada")
    vmax = max(x["anomalas"] for x in com_coord)
    pontos = []
    for x in sorted(com_coord, key=lambda x: -x["anomalas"]):
        m = muns[(x["uf"], x["mun"])]
        parc = 100 * x["anomalas"] / x["secoes"]
        pontos.append(
            {
                "lat": m["lat"],
                "lon": m["lon"],
                "raio": 1.6 + 11 * math.sqrt(x["anomalas"] / vmax),
                "cor": cor,
                "titulo": f"{m['nome']} ({x['uf']}): {inteiro(x['anomalas'])} de {inteiro(x['secoes'])} seções no grupo atípico ({num(parc, 1)}%)",
                "rotulo": f"{m['nome']} {inteiro(x['anomalas'])}",
            }
        )
    svg = pontos_brasil(
        pontos,
        "Onde estão as seções do grupo atípico",
        "Um círculo por município, área proporcional ao número de seções do grupo mais atípico; rótulo nos doze maiores.",
        rotulos=12,
    )
    svg = svg.replace('viewBox="0 0 640 640"', 'viewBox="0 0 800 640"', 1)
    total = sum(x["anomalas"] for x in agreg)
    legenda = (
        f"{inteiro(total)} seções do grupo atípico em {inteiro(len(agreg))} municípios ({inteiro(len(com_coord))} com "
        "coordenada no cadastro do Politize). O círculo é o município, não o eleitor; o Politize-se mostra a seção. "
        "Fonte: anomalia_secoes.json.gz e indice.json do Politize."
    )
    leg = legenda_html(
        [(B.rotulo_grupo(A, ma), cor)], "Grupo mais atípico (área: seções)"
    )
    return figura_html("an_mapa", svg, legenda, Tips(), modo="fit", apos=leg, dim=False)


# ------------------------------------------------------------------ amostras


def _par(a, b, casas: int = 0, sufixo: str = "") -> str:
    fa = "s/d" if a is None else f"{num(a, casas)}{sufixo}"
    fb = "s/d" if b is None else f"{num(b, casas)}{sufixo}"
    return f"{fa} → {fb}"


def tabela_amostras(A: dict) -> str:
    am = B.amostras(A)
    if not am:
        return ""
    linhas = []
    for a in am:
        lk = escape(B.link_politize(a), quote=True)
        linhas.append(
            [
                f'<a href="{lk}">{escape(a["uf"])} {inteiro(a["zona"])}/{inteiro(a["secao"])}</a>',
                escape(nome_bonito(B.municipio_de(a))),
                _par(B.g(a, "aptos_1t", "aptos1"), B.g(a, "aptos_2t", "aptos2")),
                _par(
                    B.g(a, "comparecimento_1t", "comp1", "comparecimento1"),
                    B.g(a, "comparecimento_2t", "comp2", "comparecimento2"),
                ),
                _par(B.g(a, "lula_1t", "lula1"), B.g(a, "lula_2t", "lula2")),
                _par(B.g(a, "flavio_1t", "flavio1"), B.g(a, "flavio_2t", "flavio2")),
                _par(
                    B.g(a, "brancos_1t", "brancos1"), B.g(a, "brancos_2t", "brancos2")
                ),
                _par(B.g(a, "nulos_1t", "nulos1"), B.g(a, "nulos_2t", "nulos2")),
                escape(str(B.g(a, "modelo_urna", "modelo", padrao="s/d"))),
                inteiro(B.g(a, "escore")),
                escape(
                    str(B.g(a, "explicacao", "explicacao_provavel", padrao="") or "")
                ),
            ]
        )
    ma = B.id_atipico(A)
    return (
        f'<details class="ranking"><summary>Ver as {len(am)} amostras do grupo atípico</summary>'
        + tabela(
            [
                "UF zona/seção",
                "município",
                "aptos 1º → 2º",
                "votantes 1º → 2º",
                "Lula 1º → 2º",
                "Flávio 1º → 2º",
                "brancos 1º → 2º",
                "nulos 1º → 2º",
                "modelo",
                "escore",
                "explicação provável (regra declarada)",
            ],
            linhas,
            f"As {len(am)} seções de menor log-verossimilhança dentro do {escape(B.rotulo_grupo(A, ma))}. "
            f"O link abre a seção no Politize-se. {escape(B.ROTULO)}",
        )
        + "</details>"
    )


__all__ = [
    "fig_mapa",
    "fig_pca",
    "fig_voto",
    "pendente",
    "tabela_amostras",
    "tabela_modelo",
    "tabela_seis_sinais",
    "tabela_sinais",
]
