"""Cobertura documental do agregador, inclusive ondas sem ajuste identificável."""

from html import escape
from pathlib import Path


def number(value):
    return f"{value:.1f}".replace(".", ",")


def score(values):
    if not all(k in values for k in ["lula", "flavio"]):
        return "Não publicado"
    return f"{number(values['lula'])} × {number(values['flavio'])}"


def source_link(poll):
    url = (poll.get("fonte") or {}).get("url")
    label = (poll.get("fonte") or {}).get("rotulo", poll["instituto"])
    if not url:
        return escape(label)
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def coverage_html(data, table):
    """Exibe novas divulgações e relatórios completos recebidos na última atualização."""
    polls = data["pesquisas"] + data.get("nao_reponderaveis", [])

    def documentary_date(poll):
        return max(
            poll.get("divulgacao") or poll["campo"]["fim"],
            (poll.get("fonte") or {}).get("relatorio_completo", ""),
            (poll.get("fonte") or {}).get("conferido_em", ""),
            (poll.get("fonte") or {}).get("atualizado_em", ""),
        )

    latest = max(documentary_date(p) for p in polls)
    recent = sorted(
        (p for p in polls if documentary_date(p) == latest),
        key=lambda p: p["instituto"],
    )
    rows, notes = [], []
    scenario = data["benchmark"]["cenario_principal"]
    for p in recent:
        turns = p.get("turnos", {})
        pub = p.get("publicado", {})
        release = p.get("divulgacao")
        cells = [
            source_link(p),
            "/".join(reversed(release.split("-"))) if release else "Não informada",
        ]
        for turn in ["1t", "2t"]:
            result = turns.get(turn)
            original = pub.get(turn, (result or {}).get("publicado", {}))
            adjusted = (
                score(result["cenarios"][scenario]["ajustado"])
                if result
                else "Sem ajuste disponível"
            )
            if (
                turn == "1t"
                and (p.get("selecao_1t") or {}).get("status") == "excluido_com_marcal"
            ):
                adjusted = "Excluído: cenário com Marçal"
            cells += [score(original), adjusted]
        rows.append(cells)
        if p.get("fonte", {}).get("atualizado_em") == latest:
            notes.append(
                f'<p class="note"><b>{escape(p["instituto"])}.</b> '
                f'{escape(p["fonte"].get("nota", ""))}</p>'
            )
        if p.get("fonte", {}).get("relatorio_completo") == latest:
            details = (
                f'<a href="#pesquisa-{escape(p["id"], quote=True)}">'
                "Ver cálculo e cenários de renda</a>"
                if turns
                else ""
            )
            if p.get("dossie"):
                details += (
                    (" · " if details else "")
                    + f'<a href="{escape(p["dossie"], quote=True)}">Ler dossiê completo</a>'
                )
            notes.append(
                f'<p class="note"><b>{escape(p["instituto"])}.</b> Relatório completo '
                f"disponibilizado em {'/'.join(reversed(latest.split('-')))}; "
                f"pesquisa divulgada em {'/'.join(reversed(p['divulgacao'].split('-')))}. "
                "A data nova do documento não transforma o campo em uma nova onda. "
                f"{details}</p>"
            )
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
                f"{escape(extra['rotulo'])}</a>: fonte complementar ao PDF.</p>"
            )
    day = "/".join(reversed(latest.split("-")))
    audit = f"reponderacao_{latest.replace('-', '')}.json"
    audit_link = (
        f'<p class="note"><a href="assets/{audit}">Inventário da atualização: fontes, '
        "arquivos, SHA-256 e conferência das contas</a>.</p>"
        if (Path(__file__).resolve().parents[1] / "docs/assets" / audit).exists()
        else ""
    )
    recent_html = (
        '<section id="atualizacao" class="chapter"><div class="wrap">'
        f'<p class="eyebrow">Atualização documental · {day}</p>'
        "<h2>O que entrou nesta atualização</h2>"
        "<p>Todos os placares abaixo estão na ordem <b>Lula × Flávio</b>, em %. "
        "O ajuste troca apenas a distribuição de renda pela PNAD. "
        "Sem voto por faixa e perfil de renda da mesma onda, o resultado permanece apenas como publicação do instituto.</p>"
        + table(
            [
                "Instituto e fonte",
                "Divulgação",
                "1º publicado",
                "1º reponderado",
                "2º publicado",
                "2º reponderado",
            ],
            rows,
        )
        + "".join(notes)
        + audit_link
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
