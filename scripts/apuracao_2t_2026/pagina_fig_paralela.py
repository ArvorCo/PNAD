"""Figuras do capítulo "Totalização paralela" do dossiê do 2º turno.

- ``fig_cobertura``: BUs recebidos por UF e a parcela das seções da UF;
- ``fig_relogios``: para cada BU, a hora em que chegou à paralela pelo QR contra a hora
  de recebimento registrada pelo TSE;
- ``qr_html``: o QR que leva ao aplicativo, copiado para ``docs/img/apuracao_2t/``.

Números de ``paralela.json``. Rótulo fixo: soma dos BUs recebidos, não projeção.
"""

from __future__ import annotations

import shutil

from apuracao_2026.pagina_comum import FLAVIO, INK, LULA, MUTED, ROOT, inteiro, num
from apuracao_2026.pagina_fig_base import (
    GRADE,
    HALO,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    r,
    svg_abre,
    t,
)

TEAL = "#0c7a72"
QR_DOCS = ROOT / "docs/img/qr_totalizacao.svg"
QR_ORIGEM = ROOT / "apuracao/public/img/qr_totalizacao.svg"
QR_DESTINO = ROOT / "docs/img/apuracao_2t/qr_totalizacao.svg"
LINK = "https://brasil.arvor.co/totalizacao"


def minutos(s: str | None) -> float | None:
    """'2026-10-25 18:10:11' vira minutos depois das 17:00 de Brasília."""
    if not s:
        return None
    h, m, *resto = s.strip().split(" ")[-1].split(":")
    seg = int(resto[0]) if resto else 0
    return int(h) * 60 + int(m) + seg / 60 - 17 * 60


def hhmm(m: float) -> str:
    v = round(17 * 60 + m)
    return f"{v // 60:02d}:{v % 60:02d}"


def fig_cobertura(P: dict) -> str:
    cob = sorted(P["cobertura_uf"], key=lambda c: -(c.get("bus") or 0))
    w, esq, dir_ = 760, 60, 170
    topo, passo = 30, 28
    h = topo + passo * len(cob) + 16
    vmax = max(c.get("bus") or 0 for c in cob) or 1
    x = escala(0, vmax, esq, w - dir_ - 50)
    out = [
        svg_abre(
            w,
            h,
            "Totalização paralela: BUs recebidos por UF",
            "Barras horizontais com o número de BUs conferidos em cada UF e, à direita, a parcela das seções da UF.",
        )
    ]
    out.append(t(w - dir_ + 14, 18, "parcela das seções da UF", 12, MUTED))
    tips = Tips()
    for i, c in enumerate(cob):
        y = topo + i * passo
        partes = [
            t(esq - 10, y + 16, c["uf"], 14, INK, "end", "600"),
            r(esq, y + 4, x(c["bus"]) - esq, 18, TEAL),
            t(x(c["bus"]) + 6, y + 18, inteiro(c["bus"]), 13, INK, mono=True),
            t(
                w - dir_ + 14,
                y + 18,
                f"{num(c.get('pct'), 2)}% de {inteiro(c.get('secoes_total'))}",
                13,
                INK,
                mono=True,
            ),
        ]
        kk = tips.add(
            ficha(
                c["uf"],
                "totalização paralela",
                [
                    ("BUs conferidos", inteiro(c["bus"])),
                    ("seções da UF", inteiro(c.get("secoes_total"))),
                ],
            )
        )
        out.append(hit("".join(partes) + area(0, y, w, passo), kk, foco=True))
    out.append("</svg>")
    legenda = "Cobertura da paralela por UF. A amostra é de quem enviou. Fonte: paralela.json (cobertura_uf)."
    return figura_html("paralela_cobertura", "".join(out), legenda, tips, modo="fit")


def pares_relogio(P: dict) -> list[tuple[float, float, dict]]:
    out = []
    for b in P.get("bus") or []:
        a, c = minutos(b.get("recebido_brt")), minutos(b.get("tse_recebido_brt"))
        if a is not None and c is not None:
            out.append((a, c, b))
    return out


def fig_relogios(P: dict) -> str:
    pares = pares_relogio(P)
    w = h = 600
    m = 70
    todos = [v for a, c, _ in pares for v in (a, c)] or [0, 300]
    lo = 30 * int(min(todos) // 30)
    hi = 30 * (int(max(todos) // 30) + 1)
    x = escala(lo, hi, m, w - 20)
    y = escala(lo, hi, h - m, 20)
    out = [
        svg_abre(
            w,
            h,
            "Quando cada BU chegou: paralela pelo QR contra o recebimento do TSE",
            "Um ponto por BU: hora em que chegou à totalização paralela no eixo horizontal e hora de "
            "recebimento registrada pelo TSE no vertical. Acima da diagonal, a paralela recebeu antes.",
        )
    ]
    v = lo
    while v <= hi:
        out.append(ln(x(v), 20, x(v), h - m, GRADE, 1))
        out.append(ln(m, y(v), w - 20, y(v), GRADE, 1))
        if v % 60 == 0:
            out.append(t(x(v), h - m + 20, hhmm(v), 12, MUTED, "middle", mono=True))
            out.append(t(m - 8, y(v) + 4, hhmm(v), 12, MUTED, "end", mono=True))
        v += 30
    if lo <= 120 <= hi:
        out.append(ln(x(120), 20, x(120), h - m, MUTED, 1.2, ' stroke-dasharray="4 3"'))
        out.append(ln(m, y(120), w - 20, y(120), MUTED, 1.2, ' stroke-dasharray="4 3"'))
        out.append(t(x(120) + 4, 34, "19:00", 12, INK, weight="600", extra=HALO))
    out.append(ln(x(lo), y(lo), x(hi), y(hi), INK, 1.2))
    out.append(t(x(hi) - 6, y(hi) + 40, "mesma hora", 12, INK, "end", extra=HALO))
    out.append(
        t(
            (m + w) / 2,
            h - 22,
            "chegou à paralela (QR lido pelo cidadão)",
            13,
            INK,
            "middle",
        )
    )
    out.append(
        t(
            18,
            h / 2,
            "recebido pelo TSE",
            13,
            INK,
            "middle",
            extra=f' transform="rotate(-90 18 {h / 2})"',
        )
    )
    tips = Tips()
    for a, c, b in pares:
        cor = TEAL if a < c else MUTED
        kk = tips.add(
            ficha(
                f"{b['uf']}, zona {b['zona']}, seção {b['secao']}",
                f"BU {b.get('situacao')} ao oficial",
                [
                    ("chegou à paralela", (b.get("recebido_brt") or "")[-8:-3]),
                    ("recebido pelo TSE", (b.get("tse_recebido_brt") or "")[-8:-3]),
                    (
                        "Flávio × Lula",
                        f"{inteiro(b.get('flavio'))} × {inteiro(b.get('lula'))}",
                    ),
                    (
                        "comparecimento",
                        f"{inteiro(b.get('comparecimento'))} de {inteiro(b.get('aptos'))}",
                    ),
                ],
            )
        )
        out.append(
            hit(
                f'<circle cx="{x(a):.1f}" cy="{y(c):.1f}" r="4.5" fill="{cor}" fill-opacity="0.8" '
                'stroke="#ffffff" stroke-width="0.8"/>',
                kk,
            )
        )
    out.append("</svg>")
    antes = sum(1 for a, c, _ in pares if a < c)
    leg = legenda_html(
        [("paralela recebeu antes do TSE", TEAL), ("TSE recebeu antes", MUTED)]
    )
    legenda = (
        f"{inteiro(antes)} de {inteiro(len(pares))} BUs chegaram à paralela antes de o TSE registrar o "
        "recebimento. Hora de Brasília. Fonte: paralela.json (recebido_brt, tse_recebido_brt)."
    )
    return figura_html(
        "paralela_relogios", "".join(out), legenda, tips, modo="fit", apos=leg
    )


def qr_caminho() -> str | None:
    """Endereço do QR relativo a ``docs/``; copia o do aplicativo quando falta."""
    if QR_DOCS.exists():
        return "img/qr_totalizacao.svg"
    if QR_ORIGEM.exists():
        if not QR_DESTINO.exists() or QR_DESTINO.read_bytes() != QR_ORIGEM.read_bytes():
            QR_DESTINO.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(QR_ORIGEM, QR_DESTINO)
        return "img/apuracao_2t/qr_totalizacao.svg"
    return None


def qr_html() -> str:
    src = qr_caminho()
    img = (
        f'<img src="{src}" width="180" height="180" alt="QR que abre brasil.arvor.co/totalizacao" '
        'style="display:block;background:#fff;padding:8px">'
        if src
        else ""
    )
    return (
        '<figure class="qr-totalizacao" style="display:flex;gap:18px;align-items:center;flex-wrap:wrap">'
        f"{img}<figcaption>Aponte a câmera para abrir o aplicativo, ou acesse "
        f'<a href="{LINK}">brasil.arvor.co/totalizacao</a>. O aplicativo lê os QR do BU impresso, '
        "confere a assinatura da urna e envia; nada sai do aparelho além do próprio BU.</figcaption></figure>"
    )


def placar_svg(P: dict) -> str:
    pres = P["placar_bus"]["presidente"]
    pf, pl = pres.get("pct_flavio_nominais") or 0, pres.get("pct_lula_nominais") or 0
    w, h = 760, 70
    x = escala(0, 100, 10, w - 10)
    return (
        svg_abre(
            w,
            h,
            "Soma dos BUs recebidos, presidente",
            "Barra de 100% dos votos nominais nos BUs recebidos.",
        )
        + r(x(0), 10, x(pf) - x(0), 34, FLAVIO)
        + r(x(pf), 10, x(100) - x(pf), 34, LULA)
        + t(x(0) + 8, 33, f"Flávio {num(pf, 2)}%", 15, "#ffffff", weight="700")
        + t(x(100) - 8, 33, f"Lula {num(pl, 2)}%", 15, "#ffffff", "end", "700")
        + t(10, 64, "soma dos BUs recebidos, não projeção", 13, MUTED)
        + "</svg>"
    )
