"""Cobertura documental do agregador, inclusive ondas sem ajuste identificável."""

from html import escape


def number(value):
    return f"{value:.1f}".replace(".", ",")


def score(values):
    if not all(k in values for k in ["lula", "flavio"]):
        return "Não publicado"
    return f"{number(values['lula'])} × {number(values['flavio'])}"


def source_link(poll):
    url = (poll.get("fonte") or {}).get("url")
    if not url:
        return escape(poll["instituto"])
    return f'<a href="{escape(url, quote=True)}">{escape(poll["instituto"])}</a>'


def coverage_html(data, table):
    """Exibe a última divulgação e a última onda não reponderável por instituto."""
    polls = data["pesquisas"] + data.get("nao_reponderaveis", [])
    latest = max(p.get("divulgacao") or p["campo"]["fim"] for p in polls)
    recent = sorted(
        (p for p in polls if p.get("divulgacao") == latest),
        key=lambda p: p["instituto"],
    )
    rows, notes = [], []
    scenario = data["benchmark"]["cenario_principal"]
    for p in recent:
        turns = p.get("turnos", {})
        pub = p.get("publicado", {})
        cells = [source_link(p)]
        for turn in ["1t", "2t"]:
            result = turns.get(turn)
            original = pub.get(turn, (result or {}).get("publicado", {}))
            adjusted = (
                score(result["cenarios"][scenario]["ajustado"])
                if result
                else "Sem cruzamento de renda"
            )
            if turn == "1t" and p.get("selecao_1t", {}).get("status") == "excluido_com_marcal":
                adjusted = "Excluído: cenário com Marçal"
            cells += [score(original), adjusted]
        rows.append(cells)
        reasons = list((p.get("sem_cruzamento") or {}).values())
        if p.get("motivo"):
            reasons.append(p["motivo"])
        if reasons:
            notes.append(
                f'<p class="note"><b>{escape(p["instituto"])}.</b> {escape(" ".join(reasons))}</p>'
            )
        for extra in p.get("fonte", {}).get("complementos", []):
            notes.append(
                f'<p class="note"><a href="{escape(extra["url"], quote=True)}">'
                f'{escape(extra["rotulo"])}</a>: fonte complementar ao PDF.</p>'
            )
    day = "/".join(reversed(latest.split("-")))
    recent_html = (
        '<section id="atualizacao" class="chapter"><div class="wrap">'
        f'<p class="eyebrow">Última divulgação · {day}</p>'
        "<h2>O que entrou nesta atualização</h2>"
        "<p>Todos os placares abaixo estão na ordem <b>Lula × Flávio</b>, em %. "
        "O ajuste troca apenas a distribuição de renda pela PNAD. "
        "Sem voto por faixa no mesmo turno, o resultado permanece apenas como publicação do instituto.</p>"
        + table(
            [
                "Instituto e PDF",
                "1º publicado",
                "1º reponderado",
                "2º publicado",
                "2º reponderado",
            ],
            rows,
        )
        + "".join(notes)
        + '<p class="note">As médias publicada e reponderada usam o mesmo conjunto de pesquisas com cruzamento '
        "de renda em cada turno, usando somente cenários sem Marçal no 1º turno. Os placares sem ajuste desta tabela não entram em nenhuma das duas médias. "
        "Reponderação é sensibilidade de uma margem, não previsão nem voto corrigido.</p>"
        "</div></section>"
    )
    skipped = {}
    for poll in sorted(
        data.get("nao_reponderaveis", []), key=lambda p: p["campo"]["fim"]
    ):
        skipped[poll["instituto"]] = poll
    excluded_rows = [
        [
            source_link(p),
            "/".join(reversed(p["campo"]["fim"].split("-"))),
            escape(p["motivo"]),
        ]
        for p in skipped.values()
    ]
    return recent_html + (
        '<section id="sem-cruzamento" class="chapter"><div class="wrap">'
        "<details><summary>Ondas sem reponderação: última ficha por instituto</summary>"
        + table(
            [
                "Instituto e fonte",
                "Fim do campo",
                "Por que esta onda não entra na média",
            ],
            excluded_rows,
        )
        + "</details></div></section>"
    )
