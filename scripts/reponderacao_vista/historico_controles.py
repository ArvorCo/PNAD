"""Controles e leitura dos deltas das séries documentais."""

from html import escape as esc

from reponderacao_vista.context import curto, sinal
from reponderacao_vista.historico_projecao import evidence, project
from reponderacao_vista.historico_urna import urna
from svgkit import br

LABELS = {
    "oficial": "Publicado oficial · likely voter",
    "direto": "Presença por voto · declarada",
    "proxy_renda": "Presença por renda · hipótese",
    "neutro": "Presença igual · sem diferencial identificado",
}


def delta(poll):
    if poll["pnad"] is None:
        return "PNAD indisponível"
    differences = {c: poll["pnad"][c] - poll["placar"][c] for c in ("flavio", "lula")}
    return (
        f"F {sinal(differences['flavio'], 2)} · L {sinal(differences['lula'], 2)} pp"
        f" · vantagem F−L {sinal(differences['flavio'] - differences['lula'], 2)} pp"
    )


def method(poll):
    projection = poll.get("projecao") or project(poll)
    entry = projection["evidencia"]
    label = LABELS[entry["tipo"]]
    text = entry["regra"]
    if poll.get("base_original", poll.get("denominador")) == "validos" and (
        not poll.get("modo_projecao") or poll.get("base_original") == "validos"
    ):
        label = "Somente válidos publicados"
        text = "Somente válidos publicados: preservados, sem inferir total, indecisos ou aplicar filtro de presença."
    ref = entry.get("fonte")
    link = (
        f' <a href="{esc(ref["url"], quote=True)}">Fonte, pp. {", ".join(map(str, ref["paginas"]))}</a>.'
        if ref
        else ""
    )
    details = ""
    if entry["tipo"] == "oficial":
        return (
            f'<span class="history-badge">{label}</span><p class="note">{esc(text)}</p>'
            '<p class="note">A normalização dos totais arredondados é uma comparação separada; '
            "não identifica o efeito exato do modelo. Sem pesos ou cruzamentos desse universo, PNAD indisponível.</p>"
        )
    if poll.get("modo_projecao") and poll.get("base_original") != "validos":
        model = projection["modos"]["placar"]
        q, effect = model["taxas"], model["delta_presenca_pp"]
        details = (
            (
                '<p class="note">Sem filtro diferencial: normalização simples. '
                if entry["tipo"] == "neutro"
                else f'<p class="note">Seleção F {br(100 * q["flavio"], 2)}% / L {br(100 * q["lula"], 2)}%; '
            )
            + f"efeito sobre válidos simples: F {sinal(effect['flavio'], 2)} / L {sinal(effect['lula'], 2)} pp. "
            + (
                f"Indecisos identificados: {br(model['indecisos'], 2)}% da base."
                if model["indecisos"] is not None
                else "Indecisos não separados: nenhuma massa inventada."
            )
            + "</p>"
        )
        original_valids = (poll.get("publicado_validos") or {}).get("2t")
        if original_valids:
            details += f'<p class="note">Válidos divulgados pelo instituto, antes deste cenário: F {br(original_valids["flavio"], 2)} × L {br(original_valids["lula"], 2)}.</p>'
    return f'<span class="history-badge">{label}</span><p class="note">{esc(text)}{link}</p>{details}'


def summary(poll):
    from reponderacao_vista.historico_2t import score

    projected = poll.get("modo_projecao")
    title = "Projeção do publicado" if projected else "Publicado"
    if projected and poll.get("eleitor_provavel_oficial"):
        title = "Publicado oficial · likely voter"
    preview = poll.get("renda", {}).get("perfil_tipo") == "hipotese_onda_anterior"
    return (
        (
            '<p class="history-badge">PRÉVIA PNAD · perfil da onda anterior</p>'
            if preview
            else ""
        )
        + f'<p class="kicker">Última onda · campo até {curto(poll["campo"]["fim"])} · divulgação {curto(poll["divulgacao"])}</p>'
        '<div class="history-scores">'
        f"<div><span>{title}</span><strong>{score(poll['placar'])}</strong></div>"
        f"<div><span>{'Prévia PNAD' if preview else ('Projeção PNAD' if projected else 'PNAD')}</span><strong>{score(poll['pnad']) if poll['pnad'] else 's/r'}</strong></div></div>"
        f'<p class="history-delta"><b>Δ PNAD − publicado</b><br>{delta(poll)}</p>'
        + (
            f'<span class="history-badge">{LABELS[poll["projecao"]["evidencia"]["tipo"]]}</span>'
            if projected
            else ""
        )
    )


def controls(rows):
    counts = dict.fromkeys(LABELS, 0)
    for poll in rows:
        counts[project(poll)["evidencia"]["tipo"]] += 1
    totals, valids = urna("total"), urna("validos")
    audit = "".join(
        f"<tr><th>{esc(p['instituto'])}</th><td>{esc(p['id'].split('_', 1)[-1])}</td>"
        f"<td>{LABELS[p['tipo']]}</td><td>{esc(p['nota'])} "
        + (f'<a href="{esc(p["fonte"], quote=True)}">Fonte</a>' if p["fonte"] else "")
        + "</td></tr>"
        for p in evidence()["auditoria_ultima_onda"]
    )
    return (
        '<div class="history-controls"><div><p class="kicker">Uma base comum para comparar</p>'
        '<label class="history-switch"><input type="checkbox" id="history-valids-all" disabled>'
        "<span>Ver todas em votos válidos projetados</span></label>"
        '<p class="note" id="history-mode-status" aria-live="polite">Exibindo os totais publicados. Cada instituto também tem seu próprio controle.</p></div>'
        '<p class="note">F × L em %. Vazado/tracejado: publicado; cheio/contínuo: PNAD. '
        "Azul: Flávio; vermelho: Lula. Valores e deltas estão nas fichas e tabelas.</p></div>"
        '<details class="history-method"><summary>Como funciona a projeção e o nosso likely voter</summary>'
        "<p>É um cenário de seleção de eleitores prováveis, não um modelo validado de comparecimento. "
        f"{counts['direto']} versões têm presença por voto, {counts['proxy_renda']} usam aproximação por renda "
        f"e {counts['neutro']} conservam presença igual por falta de cruzamento incorporado na própria onda. "
        f"{counts['oficial']} preservam o likely voter oficial, sem nova seleção. "
        "As regras de seleção diferem entre pesquisas: mudanças na série também podem refletir essa cobertura.</p>"
        "<ol><li>Selecionamos a massa de cada candidato usando respostas da própria onda. Ipespe: nota máxima de chance de comparecer. "
        "Nexus: ida certa/provável por renda. Veritá: ida certa por renda. "
        "Na aproximação por renda, presença e voto são tratados como independentes dentro da faixa: hipótese ecológica, não observação individual.</li>"
        "<li>Distribuímos 100% dos indecisos identificados na proporção dos candidatos após a seleção. "
        "Brancos/nulos ficam de fora. Quando BN e NS vêm juntos, não os separamos artificialmente.</li>"
        "<li>Dividimos cada massa pelo total F + L. A alocação proporcional dos indecisos aumenta as massas, "
        "mas não altera essa razão. Sem diferencial de presença, o resultado coincide com a normalização simples.</li></ol>"
        "<p>Na PNAD, as taxas por renda são recompostas com a distribuição PNAD da própria onda. "
        "A Ipespe conserva as taxas por candidato, assumindo estabilidade após o ajuste de renda. "
        "Os deltas mostram o efeito conjunto da mudança de composição e dessa seleção. "
        "Não há transporte de taxas entre ondas, tendência ou acréscimo relativo de 3,8% nestes gráficos. "
        "As centrais do início da página mantêm suas regras. Valores publicados só em válidos são preservados sem nova seleção.</p>"
        "<p>Arredondamentos podem produzir diferenças em relação aos válidos que o instituto divulga. "
        "O cenário recalculado não substitui esses números. "
        '<a href="https://www.pewresearch.org/methods/2016/01/07/measuring-the-likelihood-to-vote/">Referência sobre modelos de likely voter</a>.</p>'
        '<div class="table-scroll"><table><caption>Auditoria da última onda de cada casa; fontes e limites</caption>'
        "<thead><tr><th>Instituto</th><th>Campo até</th><th>Tratamento</th><th>Evidência e limite</th></tr></thead>"
        f"<tbody>{audit}</tbody></table></div></details>"
        '<div class="history-urna-reference"><p class="kicker">◆ Urna de 04/10 · primeiro turno</p>'
        f"<p><b>Totais: F {br(totals['flavio'], 2)}% · L {br(totals['lula'], 2)}%</b> "
        f"&nbsp; Válidos: F {br(valids['flavio'], 2)}% · L {br(valids['lula'], 2)}%.</p>"
        '<p class="note">O losango na linha de 04/10 marca a urna do 1º turno, incluindo exterior. '
        "Totais usam válidos + brancos + nulos; válidos incluem todas as candidaturas. "
        "É uma referência de outra cédula, não resultado nem previsão do 2º turno. "
        "O balanço de erro em cada card usa a última pesquisa de primeiro turno comparável, divulgada antes da eleição.</p></div>"
        "<noscript><p>Ative JavaScript para alternar os gráficos; os dados de todas as projeções estão no JSON/CSV.</p></noscript>"
    )
