"""Ligações visuais entre médias existentes; nunca preenche a série numérica."""

from html import escape


def bridges(values):
    """Extremos válidos que cercam pelo menos um dia ausente; sem extrapolação."""
    previous = None
    for index, value in enumerate(values):
        if value is None:
            continue
        if previous is not None and index - previous > 1:
            yield previous, index
        previous = index


def draw_bridges(cv, dates, values, px, py, color, kind, label):
    for left, right in bridges(values):
        first, last = dates[left + 1], dates[right - 1]
        note = (
            f"{label}, {kind}: ligação visual por interpolação linear. "
            f"Sem média disponível de {first:%d/%m/%Y} a {last:%d/%m/%Y} "
            f"({right - left - 1} {'dia' if right - left == 2 else 'dias'}). Usa os dois extremos conhecidos; "
            "não representa pesquisa nem entra na média de sete dias."
        )
        cv.add(
            f'<g class="gap-bridge" data-gap-start="{first.isoformat()}" '
            f'data-gap-end="{last.isoformat()}" data-kind="{kind}" '
            f'role="img" aria-label="{escape(note, quote=True)}"><title>{escape(note)}</title>'
        )
        cv.line(
            px(dates[left]),
            py(values[left]),
            px(dates[right]),
            py(values[right]),
            stroke=color,
            width=1.5 if kind == "publicado" else 2.6,
            stroke_dasharray="1 5",
            stroke_linecap="round",
            opacity="0.5" if kind == "publicado" else "0.8",
        )
        cv.add("</g>")


def legend(cv, x, y, color):
    cv.line(
        x,
        y,
        x + 32,
        y,
        stroke=color,
        width=2.6,
        stroke_dasharray="1 5",
        stroke_linecap="round",
    )
    cv.text(
        x + 42,
        y + 4,
        "Pontilhado: ligação visual entre médias disponíveis. Sem média na janela; fora do cálculo.",
        size=12,
        fill=color,
    )
