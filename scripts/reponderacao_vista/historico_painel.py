"""Duas leituras sincronizadas por instituto, com fonte e diferença em cada onda."""

from html import escape as esc

from reponderacao_vista.context import CEN, curto
from reponderacao_vista.historico_controles import method, summary
from reponderacao_vista.historico_projecao import projected_row
from reponderacao_vista.historico_urna import comparison_html
from reponderacao_vista.score_view import badge


def figures(rows, projected=False):
    from reponderacao_vista.historico_2t_chart import chart

    recent = [p for p in rows if p["campo"]["fim"] >= "2026-10-01"]
    adjusted = [p for p in rows if p["pnad"] is not None and not p.get("substituida")]
    note = (
        '<p class="note history-pnad-coverage"><b>PNAD em uma única onda</b> · '
        f"campo até {curto(adjusted[0]['campo']['fim'])}. "
        "Os pontos cheios mostram o reponderado; não há linha PNAD porque falta "
        "outro ajuste comparável nesta série. As demais ondas conservam apenas o publicado.</p>"
        if len(adjusted) == 1
        else ""
    )
    if recent and len(recent) < len(rows):
        return (
            '<p class="kicker">Outubro em detalhe</p>'
            f'<div class="fig">{chart(recent)}</div>'
            f"{note}"
            "<details><summary>Ver toda a série desde a primeira onda</summary>"
            f'<div class="fig">{chart(rows)}</div></details>'
        )
    return f'<div class="fig">{chart(rows)}</div>{note}'


def panel(name, rows):
    from reponderacao_vista.historico_2t import score, table, wave_count

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
    if latest.get("renda", {}).get("perfil_tipo") == "hipotese_onda_anterior":
        direct = latest["turnos"]["2t"]["cenarios"][CEN]["contrafactual"]
        note += (
            '<p class="note"><b>Conferência pela soma direta:</b> votos atuais por faixa × '
            f"pesos PNAD 2025, pessoas 16+: <b>{score(direct)}</b> no total. "
            "A prévia do gráfico mantém o método do relatório: publicado + parcela ajustável × "
            "(soma PNAD − recomposição com o perfil de referência).</p>"
        )
        note += f'<p class="note history-preview">{esc(latest["renda"]["nota"])}</p>'
    if latest.get("renda", {}).get("perfil_tipo") == "hipotese_perfil_condicional":
        note += f'<p class="note history-preview">{esc(latest["renda"]["nota"])}</p>'
    if latest.get("eleitor_provavel_oficial"):
        note += (
            '<p class="note"><b>24/10: amostra completa 46 × 45; likely voter oficial 51 × 49.</b> '
            "A normalização dos totais arredondados é 50,55 × 49,45 e não permite isolar o efeito exato do modelo. "
            "Ative votos válidos para ver o resultado oficial; a linha é interrompida na mudança de universo. "
            "Sem perfil atual e cruzamentos do eleitor provável, esta onda não tem PNAD. "
            "Na Central Projeção, entra pelo 51 × 49, sem reaplicar presença.</p>"
        )
    return (
        f'<article class="panel reveal history-panel" data-instituto="{esc(name)}" data-turno="2t">'
        f"<h3>{esc(name)} <small>Flávio × Lula</small></h3>"
        f"{badge(name)}"
        f'<p class="note"><b>{wave_count(rows)} ondas · {len(rows)} versões</b> · '
        f"{sum(p['pnad'] is not None for p in rows)} com PNAD</p>"
        f'<label class="history-switch history-switch-local"><input type="checkbox" aria-label="Votos válidos projetados: {esc(name, quote=True)}" data-history-toggle disabled>'
        "<span>Votos válidos · projeção</span></label>"
        '<div data-history-view="total">'
        f"{summary(total_latest)}{figures(total)}{special}{table(rows)}</div>"
        '<div data-history-view="validos" hidden>'
        f"{summary(projected_row(latest))}{figures(projected, True)}"
        "<details><summary>Como projetamos esta onda</summary>"
        f"{method(projected_row(latest))}</details>{table(projected)}</div>"
        f"{note}{comparison_html(name)}</article>"
    )
