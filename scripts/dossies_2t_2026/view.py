"""Componentes editoriais e gráficos acessíveis dos dossiês de segundo turno."""

from __future__ import annotations

import json
import math
from html import escape as esc

from ga_tag import injetar

COLORS = ["#386ba6", "#a74247", "#818b78", "#c3b598", "#9a9c96", "#53695f"]
PDF = {
    "nexus": "nexus_btg_13102026.pdf",
    "datafolha": "datafolha_2t_08102026_integra.pdf",
}


def fmt(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def signed(x, digits=1):
    return ("+" if x > 0 else "−" if x < 0 else "") + fmt(abs(x), digits)


def ref(house, *pages):
    return (
        '<span class="refs">Fonte: '
        + " · ".join(
            f'<a href="fontes/{PDF[house]}#page={p}" title="Página física do PDF">p. {p}</a>'
            for p in pages
        )
        + "</span>"
    )


def table(headers, rows):
    return (
        '<div class="table-scroll" tabindex="0" role="region" aria-label="Tabela de evidência"><table><thead><tr>'
        + "".join(f'<th scope="col">{esc(str(h))}</th>' for h in headers)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        + "</tbody></table></div>"
    )


def details(title, body, ident=""):
    return f'<details{f" id={esc(ident)}" if ident else ""}><summary>{title}</summary>{body}</details>'


def note(text):
    return f'<p class="note">{text}</p>'


def callout(title, text):
    return f'<aside class="callout"><b>{title}</b><p>{text}</p></aside>'


def section(number, ident, title, lead, body):
    return f'<section class="chapter" id="{ident}"><div class="section-heading"><span class="section-number">{number:02}</span><div><h2>{title}</h2><p class="lead">{lead}</p></div></div>{body}</section>'


def stats(items):
    return (
        '<div class="stats">'
        + "".join(
            f"<div><b>{value}</b><span>{label}</span></div>" for value, label in items
        )
        + "</div>"
    )


def stacks(title, rows, options, colors=None):
    colors = colors or COLORS
    columns = min(len(options), 3) if len(options) > 4 else len(options)
    if max(map(len, options)) > 32:
        columns = min(columns, 2)
    legend_rows = math.ceil(len(options) / columns)
    top = 40 + 28 * legend_rows
    height = top + 44 + 62 * len(rows)
    items = [
        f'<svg viewBox="0 0 900 {height}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
    ]
    for i, option in enumerate(options):
        x = 12 + (i % columns) * (880 / columns)
        y = 18 + 28 * (i // columns)
        items.append(
            f'<rect x="{x}" y="{y}" width="10" height="10" fill="{colors[i % len(colors)]}"/><text x="{x+16}" y="{y+10}" font-size="12">{esc(option)}</text>'
        )
    for i, (name, values) in enumerate(rows.items()):
        y, x = top + 12 + i * 62, 270
        known = [float(v) if v is not None else 0 for v in values]
        total = (
            max(sum(known), 100)
            if any(v is None for v in values)
            else (sum(known) or 100)
        )
        items.append(
            f'<text x="252" y="{y+22}" text-anchor="end" font-size="15">{esc(name)}</text>'
        )
        for j, v in enumerate(known):
            width = 600 * v / total
            if width:
                label = (
                    fmt(float(values[j]), 0 if float(values[j]).is_integer() else 1)
                    + "%"
                )
                items.append(
                    f'<rect x="{x:.3f}" y="{y}" width="{width:.3f}" height="34" fill="{colors[j % len(colors)]}"><title>{esc(name)}: {esc(options[j])} {label}</title></rect>'
                )
                if width >= 40:
                    items.append(
                        f'<text x="{x+width/2:.3f}" y="{y+23}" text-anchor="middle" fill="{label_color(colors[j % len(colors)])}" font-size="14" font-weight="600">{label}</text>'
                    )
            x += width
    for i in range(0, 101, 25):
        x = 270 + i * 6
        items.append(
            f'<text x="{x}" y="{height-12}" text-anchor="middle" class="muted" font-size="12">{i}%</text>'
        )
    items.append("</svg>")
    accessible = table(
        ["Segmento", *options],
        [
            [
                esc(name),
                *[
                    (
                        "–"
                        if v is None
                        else fmt(v, 0 if float(v).is_integer() else 1) + "%"
                    )
                    for v in values
                ],
            ]
            for name, values in rows.items()
        ],
    )
    return (
        '<figure class="chart stack-chart"><div class="chart-scroll" tabindex="0">'
        + "".join(items)
        + "</div>"
        + mobile_stacks(rows, options, colors)
        + details("Ver os números do gráfico", accessible)
        + "</figure>"
    )


def mobile_stacks(rows, options, colors):
    content = []
    for name, values in rows.items():
        total = (
            max(sum(v or 0 for v in values), 100)
            if any(v is None for v in values)
            else (sum(v or 0 for v in values) or 100)
        )
        parts = []
        for i, value in enumerate(values):
            if value:
                width = 100 * value / total
                color = colors[i % len(colors)]
                label = fmt(value, 0 if float(value).is_integer() else 1) + "%"
                parts.append(
                    f'<span style="width:{width}%;background:{color};color:{label_color(color)}" title="{esc(options[i])}: {label}">{label if width >= 9 else ""}</span>'
                )
        content.append(
            f'<div class="mobile-row"><b>{esc(name)}</b><div class="mobile-bar">{"".join(parts)}</div></div>'
        )
    legend = "".join(
        f'<span><i style="background:{colors[i % len(colors)]}"></i>{esc(o)}</span>'
        for i, o in enumerate(options)
    )
    return (
        '<div class="stack-mobile">'
        + "".join(content)
        + '<div class="mobile-legend">'
        + legend
        + "</div></div>"
    )


def label_color(color):
    rgb = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    luminance = sum(
        v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
    )
    return "#fffdf8" if 1.05 / (luminance + 0.05) >= 4.5 else "#10201c"


def bars(title, rows, suffix="%", color="#28705f"):
    maximum = max(rows.values()) or 1
    height = 48 + len(rows) * 48
    svg = [
        f'<svg viewBox="0 0 900 {height}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
    ]
    for i, (label, value) in enumerate(rows.items()):
        y, width = 14 + 48 * i, 500 * value / maximum
        svg.append(
            f'<text x="310" y="{y+23}" text-anchor="end" font-size="15">{esc(label)}</text><rect x="330" y="{y}" width="{width}" height="32" fill="{color}"/><text x="{340+width}" y="{y+23}" font-size="15" font-weight="600">{fmt(value,0)}{suffix}</text>'
        )
    mobile = (
        '<div class="bar-mobile">'
        + "".join(
            f'<div class="mobile-single"><b><span>{esc(label)}</span><span>{fmt(value,0)}{suffix}</span></b><div><span style="width:{100*value/maximum}%;background:{color}"></span></div></div>'
            for label, value in rows.items()
        )
        + "</div>"
    )
    return (
        '<figure class="chart bars-chart"><div class="chart-scroll" tabindex="0">'
        + "".join(svg)
        + "</svg></div>"
        + mobile
        + "</figure>"
    )


def vote_profiles(data, names):
    table_data = data["tables"]["voto"]["segments"]
    rows = {}
    for name in names:
        response = list(table_data[name]["responses"].values())
        rows[name] = response
    return stacks(
        "Voto dentro de cada segmento",
        rows,
        ["Flávio", "Lula", "Branco/nulo", "Indecisos"],
    )


def raw_tables(data, house):
    groups = []
    for key, t in data["tables"].items():
        total = t["segments"]["total"]
        options = list(total["responses"])
        rows = [
            [
                esc(n),
                *["–" if v is None else str(v) + "%" for v in r["responses"].values()],
                str(r.get("base_ponderada", "não publicada")),
            ]
            for n, r in t["segments"].items()
        ]
        pages = t.get("pages", [t.get("page")])
        groups.append(
            details(
                esc(t.get("title", key.replace("_", " ").capitalize())),
                note(esc(t["universe"]))
                + table(["Segmento", *options, "Base ponderada"], rows)
                + ref(house, *pages),
            )
        )
    return details(
        "Todas as tabelas extraídas: perguntas, bases e segmentos",
        "".join(groups),
        "tabelas-completas",
    )


def explorer(data, house):
    first = data["tables"]["voto"]
    options = '<option value="voto">Intenção de voto</option>' + "".join(
        f'<option value="{key}">{esc(t.get("title",key.replace("_"," ").capitalize()))}</option>'
        for key, t in data["tables"].items()
        if key != "voto"
    )
    payload = json.dumps(
        {"house": house, "tables": data["tables"], "pdf": "fontes/" + PDF[house]},
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return (
        '<div class="explorer" id="explorador"><div class="explorer-head"><h3>Explore as perguntas por segmento</h3><p>Percentuais dentro de cada grupo. Os recortes se sobrepõem; não podem ser somados.</p></div><div class="explorer-controls" hidden><label>Pergunta<select id="d-question">'
        + options
        + '</select></label><label>Recorte<select id="d-dimension"></select></label></div><div id="d-explorer-chart" aria-live="polite">'
        + vote_profiles(data, ["homens", "mulheres"])
        + ref(house, *first.get("pages", [first.get("page")]))
        + '</div><script type="application/json" id="d-explorer-data">'
        + payload
        + "</script></div>"
    )


def income_section(data, house):
    r = data["reweight"]
    profile, turn = r["profile"], r["turn"]
    main = turn["cenarios"]["pessoas16_efetivo"]["ajustado"]
    published = turn["publicado"]
    names = profile["faixas"]
    rows = [
        [esc(n), fmt(a) + "%", fmt(b) + "%", signed(b - a) + " pp"]
        for n, a, b in zip(
            names,
            profile["amostra_pct"],
            profile["pnad_pct"]["pessoas16_efetivo"],
            strict=True,
        )
    ]
    valid = 100 * main["flavio"] / (main["flavio"] + main["lula"])
    result = stats(
        [
            (
                f'{fmt(main["flavio"],2)} × {fmt(main["lula"],2)}',
                "Flávio × Lula / total / sensibilidade PNAD",
            ),
            (
                f"{fmt(valid)}% × {fmt(100-valid)}%",
                "entre os dois candidatos / sensibilidade",
            ),
            (
                signed(
                    (main["flavio"] - main["lula"])
                    - (published["flavio"] - published["lula"]),
                    2,
                )
                + " pp",
                "mudança isolada na diferença F−L",
            ),
        ]
    )
    graphic = stacks(
        "Perfil de renda publicado e régua PNAD",
        {
            (
                "Entre declarantes de renda"
                if house == "datafolha"
                else "Perfil publicado"
            ): profile["amostra_pct"],
            "PNAD 2025": profile["pnad_pct"]["pessoas16_efetivo"],
        },
        names,
        ["#28705f", "#a39153", "#386ba6", "#777b75"],
    )
    return (
        graphic
        + result
        + details(
            "Perfil de renda e três réguas de sensibilidade",
            table(["Faixa", "Perfil normalizado", "PNAD", "Troca da margem"], rows)
            + table(
                ["Régua", "Flávio / total", "Lula / total", "F−L"],
                [
                    [
                        label,
                        fmt(s["ajustado"]["flavio"], 2),
                        fmt(s["ajustado"]["lula"], 2),
                        signed(s["ajustado"]["flavio"] - s["ajustado"]["lula"], 2),
                    ]
                    for key, label in [
                        ("pessoas16_efetivo", "Pessoas 16+, efetivo"),
                        ("pessoas16_habitual", "Pessoas 16+, habitual"),
                        ("domicilios_efetivo", "Domicílios, outro universo"),
                    ]
                    for s in [turn["cenarios"][key]]
                ],
            ),
        )
        + note(
            "Sensibilidade de uma margem: rendimento domiciliar da PNADC anual 2025, visita 1, pessoas 16+, comparado à renda familiar declarada. Não reconstrói todos os pesos nem identifica o voto real. Válidos aqui normalizam apenas as candidaturas; não acrescentam comparecimento, erro comum ou transferência extra de indecisos."
        )
    )


def methodology(data, house):
    reg = data["source"]
    transcript = reg["registry_transcript"].removeprefix("docs/")
    text = (
        "A Nexus declara seleção telefônica estratificada por DDD, controle de região, tipo de telefonia, sexo, idade e escolaridade, com ponderação posterior também por renda e força de trabalho. Referências: PNADC anual 2025, visita 1, e TSE de junho/2026. Os alvos numéricos de renda, pesos individuais, limites e tamanho efetivo não estão no campo consultado. O registro prevê 2.000 entrevistas; o relatório final informa 2.002."
        if house == "nexus"
        else "A Datafolha declara estratificação por região e natureza do município, sorteio de municípios com probabilidade proporcional ao tamanho, pontos de fluxo e cotas de gênero/idade. Prevê ponderação por estratos, gênero e idade e possível ajuste de escolaridade. A referência econômica é 49% até 2 salários, 47% acima e 4% sem resposta; o fator de renda previsto é 1. Referências incluem PNADC-A 2024 e TSE de julho/2026. O campo planejado era 06–08/10; o efetivo informado nas duas fichas técnicas do PDF é 06–07/10."
    )
    return (
        '<div class="method-grid"><div><h3>O que está declarado</h3><p>'
        + text
        + "</p></div><div><h3>Ponderam pelo voto do 1º turno?</h3><p><b>Não há declaração desse ajuste no registro e no relatório consultados.</b> Essa ausência documental não prova que nenhum ajuste interno tenha sido aplicado. Perguntar em quem a pessoa votou e publicar transferências não comprova calibração pelo resultado de 04/10.</p><p>Para identificar o uso, faltam a distribuição do voto lembrado antes/depois, o alvo eleitoral, o tratamento da não resposta e os fatores aplicados. Os pesos e o desenho também são necessários para avaliar a incerteza.</p></div></div>"
        + note(
            f'Conferência de 13/10/2026 no <a href="https://pesqele-divulgacao.tse.jus.br/app/pesquisa/listar.xhtml">PesqEle</a>, buscando {"BR-07997/2026" if house=="nexus" else "BR-02949/2026"}. <a href="{transcript}">Transcrição dos campos visíveis</a>; não é exportação original.'
        )
        + ref(house, 4 if house == "nexus" else 21)
    )


def sources(data, house):
    checks = data["controls"]
    rows = [
        [esc(key), esc(dim), fmt(v["max_residual_pp"], 3) + " pp"]
        for key, t in checks.items()
        for dim, v in t.items()
    ]
    return (
        "<p>Leitura e conferência em 13/10/2026. Fontes preservadas por SHA-256, números publicados e contas derivadas separados. As recomposições abaixo usam cruzamentos independentes e os perfis ou bases ponderadas da própria pesquisa.</p>"
        + details(
            "Controles de recomposição e arredondamento",
            table(["Pergunta", "Dimensão", "Maior resíduo absoluto"], rows)
            + note(
                "Inteiros publicados e perfis arredondados podem produzir resíduos. Estes controles detectam leitura incompatível; não são intervalos de confiança e não certificam recrutamento ou ponderação. Nos gráficos de composição, os rótulos preservam os números publicados e as larguras são normalizadas à soma das partes quando o arredondamento não fecha 100%. Traços permanecem sem número, sem imputação da parcela desconhecida."
            ),
        )
        + f'<div class="downloads"><a href="fontes/{PDF[house]}">Íntegra do relatório</a><a href="assets/{data["slug"]}_data.json">Tabelas, contas e proveniência</a><a href="{data["source"]["registry_transcript"].removeprefix("docs/")}">Registro conferido</a><a href="reponderacao_pnad.html">Duas centrais Arvor e cenários</a></div>'
        + note(
            f'SHA-256 do PDF: <code>{data["source"]["sha256"]}</code>. '
            + (
                "Datafolha: arquivo de 34 páginas fornecido pelo usuário, preservado integralmente; a URL desta cópia não identifica a origem do download."
                if house == "datafolha"
                else "Nexus: íntegra oficial de 102 páginas, 17ª rodada."
            )
        )
    )


def frame(data, house, title, summary, chapters, highlights):
    other = "datafolha_08102026.html" if house == "nexus" else "nexus_btg_13102026.html"
    name = "BTG/Nexus" if house == "nexus" else "Datafolha"
    url = "https://brasil.arvor.co/" + data["slug"] + ".html"
    pub = data["reweight"]["turn"]["publicado"]
    raw = f'{fmt(pub["flavio"],0)} × {fmt(pub["lula"],0)}'
    nav = "".join(
        f'<a href="#{ident}">{label}</a>'
        for ident, label in [
            ("renda", "Renda"),
            ("transferencias", "Transferências"),
            ("segmentos", "Segmentos"),
            ("perguntas", "Perguntas"),
            ("metodo", "Método"),
            ("fontes", "Fontes"),
        ]
    )
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(name)} · {data['release']} · As perguntas por trás do placar | Arvor</title><meta name="description" content="{esc(summary)}"><link rel="canonical" href="{url}"><meta property="og:type" content="article"><meta property="og:title" content="{esc(name)}: {esc(title.replace('<br>',' ').replace('<em>','').replace('</em>',''))}"><meta property="og:description" content="{esc(summary)}"><meta property="og:url" content="{url}"><meta property="og:image" content="https://brasil.arvor.co/img/og/{data['slug']}.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/{data['slug']}.png"><link rel="stylesheet" href="assets/dossies_2t_2026.css"><script src="assets/dossies_2t_2026.js" defer></script></head><body class="{house}"><a class="skip" href="#conteudo">Pular para o conteúdo</a><header class="masthead"><a href="index.html"><img src="img/arvor_logo.png" alt="Arvor Intelligence">Arvor / Brasil</a><span>Dossiê de pesquisa · 2º turno</span><a href="{other}">Comparar com o outro dossiê ↗</a></header><main id="conteudo"><section class="hero"><div class="hero-copy"><p class="eyebrow">{name} · divulgada em {data['release']} · campo {data['field']}</p><h1>{title}</h1><p class="deck">{summary}</p><div class="hero-meta"><span>{format(data['n'], ',').replace(',', '.')} entrevistas</span><span>{"CATI / telefone" if house=='nexus' else "Presencial / pontos de fluxo"}</span><span>±2 pp informados / total</span></div></div><aside class="hero-result"><p>Publicado / Flávio × Lula</p><b>{raw}</b><span>sobre o total de entrevistados</span><div><strong>52% × 48%</strong><span>votos válidos publicados</span></div><p class="hero-foot">Branco/nulo: {fmt(pub['branco_nulo'],0)}% · Indecisos: {fmt(pub['indecisos'],0)}%<br>Diferença F−L: {signed(pub['flavio']-pub['lula'],0)} pp no total</p></aside></section><nav class="chapter-nav" aria-label="Capítulos">{nav}</nav><div class="reading"><p class="eyebrow">O diagnóstico em três pontos</p><div>{''.join(f'<article><span>0{i+1}</span><h3>{h}</h3><p>{p}</p></article>' for i,(h,p) in enumerate(highlights))}</div></div>{''.join(chapters)}</main><footer><a href="index.html">Arvor / Biblioteca</a><p>Percentuais publicados são fotografia das entrevistas. Sensibilidades, contas e leituras editoriais são identificadas; nenhum gráfico mede probabilidade de vitória.</p><a href="{other}">Ler o outro dossiê</a></footer></body></html>"""
    return injetar(html.replace("<section ", "\n<section ")) + "\n"
