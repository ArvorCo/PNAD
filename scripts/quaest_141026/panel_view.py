"""Tabelas acessíveis das cinco perguntas e dos recortes publicados no painel."""

from html import escape as esc

from dossies_2t_2026.view import details, fmt, note, section, table

from .g1 import panel, reference


def panel_section(data):
    questions = panel()
    if data["painel_g1"] != reference():
        raise ValueError("Resumo e perguntas do painel divergentes")
    totals = []
    tables = []
    for question in questions.values():
        labels = list(question["total"]["valores_pct"])
        totals.append(
            [
                esc(question["rotulo"]),
                "; ".join(
                    f"{esc(o)}: {fmt(v,0)}%"
                    for o, v in question["total"]["valores_pct"].items()
                ),
            ]
        )
        rows = [
            [
                esc(row["dimensao"]),
                esc(row["recorte"]),
                *(fmt(row["valores_pct"][o], 0) for o in labels),
                fmt(row["margem_publicada_pp"], 0),
            ]
            for row in sorted(
                question["estratos"], key=lambda r: (r["dimensao"], r["recorte"])
            )
        ]
        tables.append(
            details(
                esc(question["rotulo"]) + " · 26 recortes",
                table(["Dimensão", "Recorte", *labels, "Margem publicada (pp)"], rows)
                + note(
                    f'<a href="{esc(question["fonte"]["url"], quote=True)}">Fonte: API do próprio painel</a> · coluna 14/10/2026 · código {question["codigo"]}. Bases por recorte não publicadas.'
                ),
            )
        )
    return section(
        6,
        "painel",
        "Cinco perguntas.<br><em>130 recortes conferidos.</em>",
        "Oito dimensões: renda, sexo, idade, escolaridade, região, cor, religião e identificação política.",
        table(["Pergunta no painel", "Total publicado"], totals)
        + '<p><a href="assets/quaest_14102026_painel/recortes.csv">Baixar todos os dados em CSV</a> · <a href="assets/quaest_14102026_painel/index.json">JSON, fontes e hashes</a>.</p>'
        + "<p>Espontânea e estimulada são perguntas distintas; a diferença entre elas não mede transferência individual. Rejeição admite rejeitar ambos: 54% e 53% não precisam somar 100%, não são votos e não alteram automaticamente o destino dos indecisos. Aprovação e avaliação do governo também medem coisas diferentes.</p>"
        + note(
            "As margens abaixo são as informadas pelo G1 para os recortes, não margens calculadas por nós para diferenças entre candidatos. O painel não traz bases nem a formulação integral das perguntas; não deduzimos tamanho de amostra das margens. Os recortes se sobrepõem e não devem ser somados."
        )
        + "<p>Conferência independente: os 100 valores dos 25 recortes completos no HTML salvo coincidem com a API. O recorte lulista não tinha rótulos no arquivo salvo; na API há Flávio 2%, Lula 97%, indecisos 0% e branco/nulo/não vai votar 1%. O arquivo original permanece intacto, com as ausências registradas.</p>"
        + "".join(tables),
    )
