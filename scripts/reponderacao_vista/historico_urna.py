"""Referência de primeiro turno e comparação da última onda realmente comparável."""

import json
from html import escape

from apuracao_2026.pesquisas import NAO_ESCOLHA, validos
from reponderacao_vista.context import D, curto, sinal
from reponderacao_vista.urna_dados import AUDIT, OFFICIAL, RESIDUAL, URNA
from svgkit import br

PAIR = ("flavio", "lula")
OFF = json.loads(OFFICIAL.read_text(encoding="utf-8"))["nacional"]


def urna(mode):
    # Counted presidential ballots, including blank/null; never registered voters.
    denominator = (
        OFF["validos"]
        if mode == "validos"
        else (OFF["validos"] + OFF["brancos"] + OFF["nulos"])
    )
    return {c: 100 * OFF["votos"][c] / denominator for c in PAIR}


def reference(projected=False):
    # Keep ALL first-round candidates in the valid denominator, not just F + L.
    return urna("validos" if projected else "total")


def latest_comparison(name):
    rows = [
        p
        for p in AUDIT["pesquisas"]
        if p["instituto"] == name and p["ultima_onda_da_casa"]
    ]
    if rows:
        return max(rows, key=lambda p: (p["campo"]["fim"], p["divulgacao"]))
    # Older comparable ballots remain informative, with their date explicit.
    for poll in D["pesquisas"] + D.get("nao_reponderaveis", []):
        values = poll.get("publicado", {}).get("1t")
        if (
            poll["instituto"] != name
            or not values
            or poll.get("substituida")
            or poll.get("primeiro_turno_com_marcal")
            or poll["divulgacao"] > "2026-10-04"
            or poll["campo"]["fim"] > "2026-10-04"
        ):
            continue
        if any(
            v > 0 and k not in URNA.keys() | RESIDUAL | NAO_ESCOLHA
            for k, v in values.items()
        ):
            continue
        normalized, _ = validos(values)
        rows.append({**poll, "publicado": {"total": values, "validos": normalized}})
    return (
        max(rows, key=lambda p: (p["campo"]["fim"], p["divulgacao"])) if rows else None
    )


def comparison_html(name):
    poll = latest_comparison(name)
    if poll is None:
        return '<p class="note history-urna-empty">Urna do 1º turno: sem última onda comparável divulgada até 04/10 no acervo. Não há resultado do 2º turno.</p>'
    body, gaps = [], {}
    for mode, label in (("total", "Totais"), ("validos", "Válidos")):
        actual = urna(mode)
        values = poll["publicado"][mode]
        errors = {c: values[c] - actual[c] for c in PAIR}
        gap = errors["flavio"] - errors["lula"]
        gaps[mode] = gap
        body.append(
            f'<tr><th>{label}</th><td>{br(values["flavio"], 2)} / {br(values["lula"], 2)}</td>'
            f'<td>{sinal(errors["flavio"], 2)} / {sinal(errors["lula"], 2)}</td>'
            f"<td>{sinal(gap, 2)}</td></tr>"
        )
    return (
        f'<div class="history-error"><span>Último 1º turno × urna · erro da vantagem F−L</span>'
        f'<b>Totais {sinal(gaps["total"], 2)} pp · válidos {sinal(gaps["validos"], 2)} pp</b>'
        "<small>Positivo: mais favorável a Flávio que a urna; negativo: a Lula.</small></div>"
        '<details class="history-urna"><summary>Conferir último 1º turno × urna, por candidato</summary>'
        f'<p class="note">{escape(name)} · campo até {curto(poll["campo"]["fim"])} · '
        f'divulgada {curto(poll["divulgacao"])}. Erro = publicado − urna, em pp.</p>'
        '<div class="table-scroll"><table><caption>Flávio / Lula. Comparação da cédula de primeiro turno.</caption>'
        "<thead><tr><th>Base</th><th>Pesquisa F / L</th><th>Erro F / L</th><th>Erro da vantagem F−L</th></tr></thead>"
        f'<tbody>{"".join(body)}</tbody></table></div>'
        '<p class="note">Totais: intenção sobre entrevistados versus votos depositados (válidos + brancos + nulos); '
        "universos distintos, com indecisos apenas na pesquisa. Válidos: todas as candidaturas, sem filtro de presença retrospectivo. "
        "Não usamos o cenário hipotético de 2º turno para medir erro contra a urna do 1º. "
        '<a href="apuracao_1o_turno_2026.html#pesquisas">Auditoria e fontes →</a></p></details>'
    )
