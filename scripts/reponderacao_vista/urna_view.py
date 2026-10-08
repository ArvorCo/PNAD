"""Comparação resumida do primeiro turno com a urna, no desenho do agregador."""

from __future__ import annotations

from html import escape
from statistics import fmean

from reponderacao_vista.context import (
    GREEN,
    INK,
    LINE,
    MUTED,
    PANEL,
    curto,
    rotulo,
    sinal,
)
from reponderacao_vista.urna_dados import AUDIT, URNA, comparison, write
from svgkit import Canvas, br

LINK = "apuracao_1o_turno_2026.html#pesquisas"


def error(row):
    return row["diferenca_lula_menos_flavio"]["erro"]


def error_chart(rows):
    rows = sorted(rows, key=lambda p: error(p["publicado"]))
    cv = Canvas(
        940,
        100 + 40 * len(rows),
        aria="Erro na diferença Lula menos Flávio, por instituto. Zero reproduz a diferença da urna. Publicado e PNAD em votos válidos.",
    )
    cv.rect(0, 0, cv.width, cv.height, PANEL)
    left, right, top = 205, 795, 66
    values = [error(p[m]) for p in rows for m in ("publicado", "reponderado") if p[m]]
    low = min(-2, int(min(values)) - 1)
    high = max(8, int(max(values)) + 1)

    def x(v):
        return left + (right - left) * (v - low) / (high - low)

    cv.text(left, 23, "← Mais favorável a Flávio", size=13, fill=MUTED)
    cv.text(right, 23, "Mais favorável a Lula →", size=13, fill=MUTED, anchor="end")
    for tick in range(low, high + 1, 2):
        cv.line(x(tick), 44, x(tick), cv.height - 40, stroke=LINE)
        cv.label(x(tick), cv.height - 18, sinal(tick, 0), anchor="middle", size=12)
    cv.line(x(0), 42, x(0), cv.height - 40, stroke=INK, width=2)
    for i, p in enumerate(rows):
        y = top + i * 40
        pub = error(p["publicado"])
        adj = error(p["reponderado"]) if p["reponderado"] else None
        star = " *" if p["perfil_renda"] == "hipotese_onda_anterior" else ""
        cv.text(16, y + 5, p["instituto"] + star, size=15, fill=INK)
        if adj is not None:
            cv.line(x(pub), y, x(adj), y, stroke=MUTED, width=2)
            cv.circle(x(adj), y, 5, GREEN)
        cv.circle(x(pub), y, 5, PANEL, stroke=INK, stroke_width=2)
        cv.text(816, y + 5, sinal(pub, 2), size=13, fill=INK)
        cv.text(
            879, y + 5, sinal(adj, 2) if adj is not None else "s/r", size=13, fill=GREEN
        )
    cv.text(816, 45, "Publ.", size=12, fill=INK)
    cv.text(879, 45, "PNAD", size=12, fill=GREEN)
    return cv.render()


def candidate_chart(rows):
    paired = [p for p in rows if p["reponderado"]]
    cv = Canvas(
        900,
        254,
        aria=f"Erro médio por bloco, nas mesmas {len(paired)} casas: Flávio, Lula e demais candidaturas. Publicado versus PNAD, em pontos dos válidos.",
    )
    cv.rect(0, 0, 900, 254, PANEL)
    left, right = 190, 765
    means = {
        m: {
            k: fmean(p[m]["erro_blocos_pp"][k] for p in paired)
            for k in ("flavio", "lula", "terceira_via")
        }
        for m in ("publicado", "reponderado")
    }
    extent = max(2, max(abs(v) for vals in means.values() for v in vals.values())) + 1

    def x(v):
        return left + (right - left) * (v + extent) / (2 * extent)

    cv.text(left, 24, "← Subestimou", size=13, fill=MUTED)
    cv.text(right, 24, "Superestimou →", size=13, fill=MUTED, anchor="end")
    cv.line(x(0), 40, x(0), 210, stroke=INK, width=1.5)
    for i, (key, label) in enumerate(
        (("flavio", "Flávio"), ("lula", "Lula"), ("terceira_via", "Demais candidatos"))
    ):
        y = 69 + 60 * i
        cv.text(14, y + 8, label, size=15, fill=INK)
        for mode, offset in (("publicado", -9), ("reponderado", 13)):
            v = means[mode][key]
            cv.rect(
                min(x(0), x(v)),
                y + offset - 8,
                abs(x(v) - x(0)),
                15,
                INK if mode == "publicado" else GREEN,
            )
            cv.text(
                789,
                y + offset + 4,
                sinal(v, 2),
                size=13,
                fill=INK if mode == "publicado" else GREEN,
            )
    cv.text(
        190,
        239,
        f"Mesmas {len(paired)} casas · preto: publicado · verde: PNAD · pontos percentuais",
        size=13,
        fill=MUTED,
    )
    return cv.render()


def section(table):
    data = write()
    rows = data["pesquisas"]
    paired = [p for p in rows if p["reponderado"]]
    mae_pub = fmean(abs(error(p["publicado"])) for p in paired)
    mae_adj = fmean(abs(error(p["reponderado"])) for p in paired)
    summary = data["resumo"]["publicado"]
    effect = data["efeito_pareado"]
    lines = []
    for p in sorted(rows, key=lambda p: abs(error(p["publicado"]))):
        pub, adj = p["publicado"], p["reponderado"]
        label = escape(p["instituto"])
        if p["perfil_renda"] == "hipotese_onda_anterior":
            label += " *"
        lines.append(
            [
                label,
                curto(p["campo"]["fim"]),
                f'{br(pub["validos"]["lula"], 2)} × {br(pub["validos"]["flavio"], 2)}',
                sinal(error(pub), 2),
                (
                    f'{br(adj["validos"]["lula"], 2)} × {br(adj["validos"]["flavio"], 2)}'
                    if adj
                    else "Sem renda"
                ),
                sinal(error(adj), 2) if adj else "s/r",
            ]
        )
    return (
        '<div class="urna-summary"><p class="kicker">04/10/2026 · resultado encerrado · votos válidos</p>'
        '<div class="urna-result">'
        f'<div><span>Flávio</span><strong class="flavio">{br(URNA["flavio"], 2)}%</strong></div>'
        f'<div><span>Lula</span><strong class="lula">{br(URNA["lula"], 2)}%</strong></div>'
        f'<div><span>Demais candidaturas</span><strong>{br(100 - URNA["lula"] - URNA["flavio"], 2)}%</strong></div></div>'
        f'<p>Flávio terminou <b>{br(URNA["flavio"] - URNA["lula"], 2)} pontos à frente</b>. '
        f'{br(data["urna"]["validos_votos"], 0)} votos válidos; todas as {br(data["urna"]["secoes_total"], 0)} seções totalizadas. '
        f'<a href="{LINK}">Apuração completa e auditoria do erro →</a></p></div>'
        '<div class="metrics three">'
        f'<article><strong>{summary["positivos"]}/{summary["n"]}</strong><p>últimas ondas favoreceram Lula em relação à diferença da urna.</p></article>'
        f'<article><strong>{sinal(summary["media"], 2)} pp</strong><p>erro médio publicado na diferença Lula − Flávio, nas {summary["n"]} casas.</p></article>'
        f"<article><strong>{br(mae_pub, 2)} → {br(mae_adj, 2)}</strong><p>erro absoluto médio da diferença, publicado → PNAD, nas mesmas {len(paired)} casas.</p></article></div>"
        '<figure class="chart-shell"><p class="kicker">Última onda por casa · erro na diferença L−F</p>'
        "<h3>Quanto cada instituto se afastou da urna</h3>"
        f'<div class="fig urna-figure" tabindex="0" role="region" aria-label="Erros por instituto">{error_chart(rows)}</div>'
        '<figcaption class="note">Zero reproduz a diferença da urna. Círculo vazado: publicado; cheio: PNAD. '
        "A linha liga a mesma onda nos dois cálculos. A ordem usa o erro com sinal, do mais favorável a Flávio ao mais favorável a Lula; não é ranking de qualidade. s/r: sem reponderação por renda.</figcaption></figure>"
        '<p class="note"><b>Ajuste parcial, como no relatório da apuração:</b> candidaturas sem voto por renda preservam sua parcela publicada. Isso ocorre no Atlas (Zema e candidaturas menores), MDA (Cury, Caiado, Renan e Zema) e Real Time (Outros). A projeção com comparecimento no início da página exige vetor completo e exclui essas três ondas; por isso usa sete casas, e este balanço de renda usa dez.</p>'
        f'<p class="plain">A PNAD aproximou <b>{effect["aproximou"]}</b> casas, afastou <b>{effect["afastou"]}</b> e deixou <b>{effect["neutro"]}</b> praticamente igual. '
        "A troca de uma margem é uma sensibilidade; o resultado mostra onde ela ajudou e onde falhou. "
        "Acertar a diferença entre os líderes também pode esconder erros que se compensam entre candidaturas.</p>"
        '<figure class="chart-shell"><p class="kicker">Erro por candidato · comparação pareada</p><h3>Onde ficou o erro médio</h3>'
        f'<div class="fig urna-figure" tabindex="0" role="region" aria-label="Erros por bloco">{candidate_chart(rows)}</div>'
        '<figcaption class="note">Pesquisa menos urna, em pontos dos válidos. Demais candidatos inclui todas as candidaturas além de Lula e Flávio. Ambos os cálculos usam apenas as dez casas com renda, com peso igual.</figcaption></figure>'
        '<details class="urna-details"><summary>Conferir os placares e o erro de cada instituto</summary>'
        f'<p>Urna, Lula × Flávio: <b>{br(URNA["lula"], 2)} × {br(URNA["flavio"], 2)}</b>. Ordem pelo menor erro absoluto publicado da diferença.</p>'
        + table(
            [
                "Instituto",
                "Fim do campo",
                "Publicado / válidos",
                "Erro L−F / pp",
                "PNAD / válidos",
                "Erro L−F / pp",
            ],
            lines,
        )
        + f'<p class="note">{escape(data["regra"])} * Datafolha e Quaest: composição de renda assumida da onda anterior, condicionada ao perfil final. Os motivos de exclusão e os erros por candidatura estão no <a href="{LINK}">relatório completo</a>. Erro da diferença, erro por candidato e qualidade do desenho são critérios distintos; este recorte não valida a metodologia inteira de um instituto.</p>'
        '<p class="note"><a href="assets/reponderacao_urna_1t.json">Recorte auditável (JSON)</a> · <a href="assets/reponderacao_urna_1t.csv">Erros por candidatura (CSV)</a>. A base é a mesma da apuração, sem ajuste posterior das pesquisas à urna.</p></details>'
    )


def poll_table(poll, table, scenarios=None):
    comp = comparison(poll)
    if comp is None:
        return ""
    pub, adj = comp["publicado"], comp["pnad"]
    keys = [k for k in pub["validos"] if k in URNA]
    keys.sort(key=lambda k: -URNA[k])
    rows = [
        [
            escape(rotulo(k)),
            br(pub["validos"][k], 2),
            br(adj["validos"][k], 2),
            br(URNA[k], 2),
            sinal(pub["erro_pp"][k], 2),
            sinal(adj["erro_pp"][k], 2),
        ]
        for k in keys
    ]
    rows.append(
        [
            "Diferença Lula − Flávio",
            sinal(pub["diferenca_lula_menos_flavio"]["pesquisa"], 2),
            sinal(adj["diferenca_lula_menos_flavio"]["pesquisa"], 2),
            sinal(URNA["lula"] - URNA["flavio"], 2),
            sinal(error(pub), 2),
            sinal(error(adj), 2),
        ]
    )
    final = any(
        p["id"] == poll["id"] and p["ultima_onda_da_casa"] for p in AUDIT["pesquisas"]
    )
    scenario_rows = []
    for key, label in (scenarios or {}).items():
        adjusted = comparison(poll, key)["pnad"]
        scenario_rows.append(
            [
                escape(label),
                br(adjusted["validos"]["lula"], 2),
                br(adjusted["validos"]["flavio"], 2),
                f'{br(URNA["lula"], 2)} × {br(URNA["flavio"], 2)}',
                sinal(error(adjusted), 2),
                "principal" if key == "pessoas16_efetivo" else "robustez",
            ]
        )
    return (
        '<details class="urna-details poll-urna"><summary>1º turno: comparar esta onda com a urna</summary>'
        + table(
            [
                "Candidatura",
                "Publicado % válidos",
                "PNAD % válidos",
                "Urna % válidos",
                "Erro publ. / pp",
                "Erro PNAD / pp",
            ],
            rows,
        )
        + (
            "<h4>Cenários de renda do 1º turno, em válidos</h4>"
            + table(
                [
                    "Cenário PNAD",
                    "Lula %",
                    "Flávio %",
                    "Urna L × F %",
                    "Erro L−F / pp",
                    "Uso",
                ],
                scenario_rows,
            )
            if scenario_rows
            else ""
        )
        + '<p class="note">Normalização pelo vetor de candidaturas, incluindo os nomes agrupados; não escolha fica fora. '
        "Erro = pesquisa menos urna. Resíduos negativos do ajuste são retirados antes de normalizar. "
        + (
            "Última onda da casa incluída no recorte final."
            if final
            else "Onda histórica: a distância até a urna inclui mudanças de preferência entre o campo e a eleição; não entra no ranking final."
        )
        + (
            " Candidaturas sem cruzamento mantidas no publicado: "
            + escape(", ".join(rotulo(k) for k in comp["sem_cruzamento"]))
            + "."
            if comp["sem_cruzamento"]
            else ""
        )
        + f' A PNAD continua sendo sensibilidade de uma margem. <a href="{LINK}">Ver auditoria da apuração</a>.</p></details>'
    )


def institute_note(name):
    p = next(
        (
            p
            for p in AUDIT["pesquisas"]
            if p["instituto"] == name and p["ultima_onda_da_casa"]
        ),
        None,
    )
    if not p:
        return ""
    pub, adj = p["publicado"], p["reponderado"]
    return (
        f'<p class="note urna-institute"><b>Última onda × urna · válidos.</b> '
        f"Erro L−F: publicado <b>{sinal(error(pub), 2)} pp</b>"
        + (
            f"; PNAD <b>{sinal(error(adj), 2)} pp</b>"
            if adj
            else "; sem cruzamento de renda"
        )
        + (
            ". Perfil de renda assumido da onda anterior"
            if p["perfil_renda"] == "hipotese_onda_anterior"
            else ""
        )
        + '. <a href="#primeiro-turno">Comparação completa</a>.</p>'
    )
