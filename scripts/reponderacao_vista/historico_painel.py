"""Duas leituras sincronizadas por instituto, com fonte e diferença em cada onda."""

from html import escape as esc

from reponderacao_vista.historico_controles import method, summary
from reponderacao_vista.historico_projecao import projected_row
from reponderacao_vista.historico_urna import comparison_html


def figures(rows, projected=False):
    from reponderacao_vista.historico_2t_chart import chart

    recent = [p for p in rows if p["campo"]["fim"] >= "2026-10-01"]
    if len(recent) >= 2 and len(recent) < len(rows):
        return (
            '<p class="kicker">Outubro em detalhe</p>'
            f'<div class="fig">{chart(recent)}</div>'
            "<details><summary>Ver toda a série desde a primeira onda</summary>"
            f'<div class="fig">{chart(rows)}</div></details>'
        )
    return f'<div class="fig">{chart(rows)}</div>'


def panel(name, rows):
    from reponderacao_vista.historico_2t import table, wave_count

    total = [p for p in rows if p["denominador"] == "total"]
    valid_only = [p for p in rows if p["denominador"] == "validos"]
    projected = [projected_row(p) for p in rows]
    latest = next(p for p in reversed(rows) if not p.get("substituida"))
    total_latest = next(
        (p for p in reversed(total) if not p.get("substituida")), latest
    )
    special = ""
    if valid_only:
        special = (
            "<details><summary>Resultados disponíveis só em votos válidos</summary>"
            '<p class="note">Base distinta; não entram no gráfico de totais.</p>'
            f"{figures(valid_only)}</details>"
        )
    note = (
        '<p class="note">Palver: onda 2 original substituída, documentada sem dupla contagem e fora das médias. '
        "Desde 15/10, calibração por PNAD 2025 e voto declarado no 1º turno/2026; "
        "a variação também pode refletir mudança de método.</p>"
        if name == "Palver"
        else ""
    )
    return (
        f'<article class="panel reveal history-panel" data-instituto="{esc(name)}" data-turno="2t">'
        f"<h3>{esc(name)} <small>Flávio × Lula</small></h3>"
        f'<p class="note"><b>{wave_count(rows)} ondas · {len(rows)} versões</b> · '
        f'{sum(p["pnad"] is not None for p in rows)} com PNAD</p>'
        '<label class="history-switch history-switch-local"><input type="checkbox" data-history-toggle disabled>'
        "<span>Votos válidos · projeção</span></label>"
        '<div data-history-view="total">'
        f"{summary(total_latest)}{figures(total)}{special}{table(rows)}</div>"
        '<div data-history-view="validos" hidden>'
        f"{summary(projected_row(latest))}{figures(projected, True)}"
        "<details><summary>Como projetamos esta onda</summary>"
        f"{method(projected_row(latest))}</details>{table(projected)}</div>"
        f"{note}{comparison_html(name)}</article>"
    )
