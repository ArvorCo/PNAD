"""Markers da página de reponderação, compartilhado pelo gerador."""

from __future__ import annotations

import math
from html import escape as esc

from reponderacao_vista.context import (
    PANEL,
    PAR,
    TURNOS,
    ajustado,
    gap,
    longo,
    periodo,
    rotulo,
    sinal,
)
from svgkit import Canvas, br


def _poligono(cx: float, cy: float, r: float, lados: int, giro: float) -> str:
    pontos = []
    for i in range(lados):
        ang = giro + 2 * math.pi * i / lados
        pontos.append(f"{cx + r * math.sin(ang):.1f} {cy - r * math.cos(ang):.1f}")
    return "M" + "L".join(pontos) + "Z"


def _estrela(cx: float, cy: float, r: float) -> str:
    pontos = []
    for i in range(10):
        raio = r * 1.2 if i % 2 == 0 else r * 0.52
        ang = math.pi * i / 5
        pontos.append(
            f"{cx + raio * math.sin(ang):.1f} {cy - raio * math.cos(ang):.1f}"
        )
    return "M" + "L".join(pontos) + "Z"


TIPS: dict[str, str] = {}


def _tip_id(pesquisa: dict, turno: str) -> str:
    return f"{pesquisa['id']}|{turno}"


def registra_tip(chave: str, html: str) -> str:
    """Guarda a ficha de um alvo e devolve a chave usada no atributo data."""
    TIPS[chave] = html
    return chave


def abre_alvo(cv: Canvas, chave: str, rotulo: str) -> None:
    """Abre um grupo sensível ao ponteiro. O desenho continua sendo o do SVG."""
    cv.add(
        f'<g class="hit" role="img" aria-label="{esc(rotulo, quote=True)}"'
        f' data-k="{esc(chave, quote=True)}">'
    )


def fecha_alvo(cv: Canvas) -> None:
    cv.add("</g>")


def area_alvo(cv: Canvas, cx: float, cy: float, r: float) -> None:
    """Alvo circular transparente, maior que o marcador, para o ponteiro pegar."""
    cv.circle(cx, cy, r, "transparent", **{"class": "hit-area"})


def halo(cv: Canvas, cx: float, cy: float, r: float, cor: str) -> None:
    """Anel que só aparece no hover, para dizer qual ponto está sendo lido."""
    cv.circle(
        cx,
        cy,
        r,
        "none",
        stroke=cor,
        stroke_width=2,
        **{"class": "hit-halo"},
    )


def ficha_onda(pesquisa: dict, turno: str) -> str:
    """Ficha completa de uma onda: documento, placar publicado e reponderado."""
    t = pesquisa["turnos"][turno]
    adj = ajustado(t)
    pub = t["publicado"]
    linhas = [
        '<table class="tip-tab"><thead><tr><th></th>'
        + "".join(f"<th>{esc(rotulo(c))}</th>" for c in PAR)
        + "<th>dif.</th></tr></thead><tbody>"
    ]
    for nome, fonte, cls in (
        ("publicado", pub, "pub"),
        ("reponderado", adj, "adj"),
    ):
        linhas.append(
            f'<tr class="{cls}"><th scope="row">{nome}</th>'
            + "".join(f"<td>{br(fonte[c], 1)}</td>" for c in PAR)
            + f"<td>{sinal(gap(fonte), 1)}</td></tr>"
        )
    linhas.append("</tbody></table>")
    extras = [c for c in t["opcoes"] if c not in PAR and pub.get(c, 0) >= 1]
    corpo = [
        f'<p class="tip-head"><b>{esc(pesquisa["instituto"])}</b>'
        f"<span>{esc(TURNOS[turno])}</span></p>",
        f'<p class="tip-doc">campo {esc(periodo(pesquisa["campo"]))} · '
        f'n = {br(pesquisa["n"], 0)} · {esc(pesquisa.get("registro_tse") or "sem registro")}</p>',
        "".join(linhas),
        f'<p class="tip-nota">Margem de 95% da diferença publicada: ±{br(t.get("margem_diferenca_95", 0.0), 1)}.',
    ]
    desvio = pesquisa["desvio_ate_primeira_faixa"]
    if desvio >= 0:
        composicao = f"A amostra tem {br(desvio, 1)} pontos a mais na faixa mais pobre que a PNAD."
    else:
        composicao = f"A amostra tem {br(-desvio, 1)} pontos a menos na faixa mais pobre que a PNAD."
    if pesquisa["renda"].get("perfil_tipo") == "cota_registrada":
        composicao = composicao.replace("A amostra tem", "A cota registrada tem")
    corpo.append(f" {composicao} Prova de leitura: {br(t['residuo_max'], 2)}.</p>")
    if pesquisa["fonte"].get("nota"):
        corpo.append(
            f'<p class="tip-nota"><b>{esc(pesquisa["fonte"].get("status", ""))}</b> {esc(pesquisa["fonte"]["nota"])}</p>'
        )
    if extras:
        itens = ", ".join(f"{esc(rotulo(c))} {br(pub[c], 1)}" for c in extras[:6])
        corpo.append(f'<p class="tip-nota">Também na cédula: {itens}.</p>')
    if turno == "1t" and pesquisa.get("selecao_1t"):
        corpo.append(
            f'<p class="tip-nota">Cenário sem Marçal. {esc(pesquisa["selecao_1t"]["nota"])}</p>'
        )
    return "".join(corpo)


def resumo_onda(pesquisa: dict, turno: str) -> str:
    """Texto curto para leitor de tela, no aria-label do grupo."""
    t = pesquisa["turnos"][turno]
    adj = ajustado(t)
    return (
        f"{pesquisa['instituto']}, campo até {longo(pesquisa['campo']['fim'])}, "
        f"{TURNOS[turno]}: publicado Lula {br(t['publicado']['lula'], 1)} e "
        f"Flávio {br(t['publicado']['flavio'], 1)}; reponderado Lula "
        f"{br(adj['lula'], 1)} e Flávio {br(adj['flavio'], 1)}."
    )


def alvo_onda(cv: Canvas, pesquisa: dict, turno: str) -> str:
    """Abre o grupo de uma onda e devolve a chave da ficha."""
    chave = registra_tip(_tip_id(pesquisa, turno), ficha_onda(pesquisa, turno))
    abre_alvo(cv, chave, resumo_onda(pesquisa, turno))
    return chave


def marcador(
    cv: Canvas, shape: str, cx: float, cy: float, r: float, cor: str, cheio: bool
) -> None:
    """Ponto de pesquisa. Vazado é o publicado; preenchido é o reponderado."""
    fill = cor if cheio else PANEL
    stroke = PANEL if cheio else cor
    sw = 1.2 if cheio else 2.1
    kw = {"stroke": stroke, "stroke_width": sw, "stroke_linejoin": "round"}
    if shape == "quadrado":
        cv.rect(cx - r, cy - r, 2 * r, 2 * r, fill, **kw)
    elif shape == "triangulo":
        cv.path(
            f"M{cx:.1f} {cy - r * 1.2:.1f}L{cx + r * 1.1:.1f} {cy + r * 0.85:.1f}"
            f"L{cx - r * 1.1:.1f} {cy + r * 0.85:.1f}Z",
            fill=fill,
            **kw,
        )
    elif shape == "triangulo_baixo":
        cv.path(
            f"M{cx:.1f} {cy + r * 1.2:.1f}L{cx + r * 1.1:.1f} {cy - r * 0.85:.1f}"
            f"L{cx - r * 1.1:.1f} {cy - r * 0.85:.1f}Z",
            fill=fill,
            **kw,
        )
    elif shape == "losango":
        cv.path(
            f"M{cx:.1f} {cy - r * 1.25:.1f}L{cx + r * 1.25:.1f} {cy:.1f}"
            f"L{cx:.1f} {cy + r * 1.25:.1f}L{cx - r * 1.25:.1f} {cy:.1f}Z",
            fill=fill,
            **kw,
        )
    elif shape == "pentagono":
        cv.path(_poligono(cx, cy, r * 1.2, 5, 0), fill=fill, **kw)
    elif shape == "hexagono":
        cv.path(_poligono(cx, cy, r * 1.15, 6, 0), fill=fill, **kw)
    elif shape == "estrela":
        cv.path(_estrela(cx, cy, r), fill=fill, **kw)
    elif shape == "gravata":
        cv.path(
            f"M{cx - r:.1f} {cy - r:.1f}L{cx + r:.1f} {cy - r:.1f}"
            f"L{cx - r:.1f} {cy + r:.1f}L{cx + r:.1f} {cy + r:.1f}Z",
            fill=fill,
            **kw,
        )
    elif shape == "cruz":
        b = r * 0.48
        cv.path(
            f"M{cx - b:.1f} {cy - r:.1f}H{cx + b:.1f}V{cy - b:.1f}H{cx + r:.1f}"
            f"V{cy + b:.1f}H{cx + b:.1f}V{cy + r:.1f}H{cx - b:.1f}V{cy + b:.1f}"
            f"H{cx - r:.1f}V{cy - b:.1f}H{cx - b:.1f}Z",
            fill=fill,
            **kw,
        )
    else:
        cv.circle(cx, cy, r, fill, **kw)
