"""Comparativo auditável por instituto: documentos, critérios e desvios contemporâneos."""

import importlib
import json
from html import escape as esc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "analysis/reponderacao/metodologias"
REFERENCE = "2026-09-21"
OUTPUT = ROOT / "docs/assets/reponderacao_metodologias.json"
HOUSE = importlib.import_module("reponderacao-efeito-casa")
CRITERIA = [
    (
        "Ficha básica",
        "Universo, modalidade, datas, n e contratante identificados e conciliados.",
    ),
    (
        "Recrutamento e seleção",
        "Origem do contato, etapas e regra de seleção da pessoa descritas; cotas explicitadas quando usadas.",
    ),
    (
        "Fontes dos alvos",
        "Fontes e edições identificadas para as variáveis; PNAD com trimestre ou visita, quando aplicável.",
    ),
    (
        "Calibração",
        "Variáveis, alvos e procedimento efetivo especificados; ausência de ponderação explicitamente confirmada também atende.",
    ),
    (
        "Questionário",
        "Instrumento completo da onda acessível, com alternativas e ordem.",
    ),
    (
        "Controle de campo",
        "Procedimento concreto e cobertura quantitativa das verificações declarados.",
    ),
    (
        "Não resposta",
        "Balanço de contatos, elegibilidade, recusas e completas suficiente para calcular resposta ou participação.",
    ),
    (
        "Incerteza",
        "Cálculo adequado ao desenho e aos pesos, ou modelo de seleção com hipóteses e validação; somente AAS explícita, limites ou Kish recebe parcial.",
    ),
    (
        "Diagnóstico da amostra",
        "Perfil e diagnóstico da dispersão dos pesos/tamanho efetivo; somente perfil recebe parcial.",
    ),
    (
        "Reprodução independente",
        "Microdados anônimos, pesos e código da onda disponíveis; código ou alvos executáveis parciais recebem metade.",
    ),
]


def score(row):
    values = row["criterios"]
    if len(values) != len(CRITERIA):
        raise ValueError("A nota exige os dez critérios")
    if any(v["pontos"] not in (0, 0.5, 1) or not v["evidencia"] for v in values):
        raise ValueError("Cada critério exige nota 0, 0,5 ou 1 e evidência")
    return sum(v["pontos"] for v in values)


def load_data():
    rows = [json.loads(p.read_text()) for p in sorted(MANIFESTS.glob("*.json"))]
    polls = [
        json.loads(p.read_text())
        for p in (ROOT / "analysis/reponderacao/pesquisas").glob("*.json")
    ]
    house = HOUSE.compare(polls, REFERENCE)
    for row in rows:
        row["nota"] = score(row)
        row["sinal"] = house[row["instituto"]]
    return {
        "referencia": REFERENCE,
        "escopo": "Últimas ondas nacionais disponíveis no acervo em 21/09/2026; nota dos documentos consultados, não previsão de acerto.",
        "rubrica": [{"criterio": n, "regra": r} for n, r in CRITERIA],
        "efeito_casa": {
            "dias": 45,
            "raio_dias": 7,
            "minimo_outros_institutos": 3,
            "faixa_proximidade_pp": 2,
            "formula": "100 * (Lula - Flavio) / (Lula + Flavio)",
            "resumo": "Mediana dos desvios à mediana de outros institutos, uma onda mais próxima por instituto, datas centrais de campo; revisões substituem a mesma amostra.",
            "limites": "Descritivo e relativo ao conjunto. Não estima erro contra a verdade, causalidade, alinhamento político ou significância. Ondas e pares se sobrepõem.",
        },
        "institutos": sorted(rows, key=lambda r: r["instituto"]),
    }


def fmt(value, signed=False):
    return (f"{value:+.1f}" if signed else f"{value:.1f}").replace(".", ",")


def link(url, label):
    return f'<a href="{esc(url, quote=True)}">{esc(label)}</a>'


def date_label(value):
    return "/".join(value.split("-")[:0:-1])


def row_html(row):
    sig = row["sinal"]
    delta = sig["desvio_mediano"]
    signal = (
        "<b>Sem comparação</b>"
        if delta is None
        else (
            f'<b>{esc(sig["direcao"])}</b><span class="method-delta">{fmt(delta, True)} pp</span>'
            f'<small>{sig["n_ondas"]} onda(s) · {esc(sig["evidencia"])}</small>'
        )
    )
    ident = "ficha-" + row["id"]
    cells = [
        (
            "Instituto",
            f'<b>{esc(row["instituto"])}</b><small>{date_label(row["campo"]["inicio"])} a '
            f'{date_label(row["campo"]["fim"])} · n = {row["n"]:,}</small>'.replace(
                ",", "."
            ),
        ),
        (
            "Coleta",
            f'<span class="method-mode">{esc(row["modo"])}</span><small>{esc(row["subtipo"])}</small>',
        ),
        ("Recrutamento e seleção", esc(row["selecao"])),
        (
            "Fontes e PNAD",
            f'<b>{esc(row["pnad"])}</b><small>{esc(row["fontes"])}</small>',
        ),
        ("Voto de 2022 nos pesos", esc(row["voto"])),
        ("Sinal relativo", signal),
        (
            "Nota documental",
            f'<a class="method-score" href="#{ident}">{fmt(row["nota"])}/10</a>'
            f'<small>{link("#" + ident, "Ficha e evidências")}</small>',
        ),
    ]
    search = esc(
        " ".join(str(row[k]) for k in ["instituto", "modo", "pnad", "fontes"]),
        quote=True,
    )
    header_tag = 'th scope="row"'
    return (
        f'<tr data-method="{esc(row["id"])}" data-mode="{esc(row["modo"])}" data-search="{search}" '
        f'data-score="{row["nota"]}" data-delta="{delta if delta is not None else ""}">'
        + "".join(
            f'<{header_tag if i == 0 else "td"} '
            f'data-label="{esc(label)}">{text}</{"th" if i == 0 else "td"}>'
            for i, (label, text) in enumerate(cells)
        )
        + "</tr>"
    )


def detail_html(row):
    scores = "".join(
        f'<li><b>{esc(name)} <span>{fmt(item["pontos"])}/1</span></b>'
        f'<p>{esc(item["evidencia"])}</p></li>'
        for (name, _), item in zip(CRITERIA, row["criterios"], strict=True)
    )
    report_name = (
        "Excerto do relatório" if row.get("relatorio_excerto") else "Relatório"
    )
    pages = ", ".join(str(p) for p in row["paginas"]) or "metodologia no registro"
    sig = row["sinal"]
    observations = "".join(
        "<tr>"
        + "".join(
            f"<td>{cell}</td>"
            for cell in [
                esc(w["id"]),
                fmt(w["diferenca_validos"], True),
                fmt(w["mediana_outros"], True),
                fmt(w["desvio"], True),
                esc(", ".join(p["instituto"] for p in w["pares"])),
            ]
        )
        + "</tr>"
        for w in sig["ondas"]
    )
    return (
        f'<details class="method-file" id="ficha-{esc(row["id"])}" data-file="{esc(row["id"])}">'
        f'<summary>{esc(row["instituto"])} <span>{fmt(row["nota"])}/10 · documentos e critérios</span></summary>'
        '<div class="method-file-body">'
        f'<p class="note">{esc(row["registro_tse"])} · Campo {date_label(row["campo"]["inicio"])} a '
        f'{date_label(row["campo"]["fim"])} de 2026 · Contratante: {esc(row["contratante"])}</p>'
        '<p class="method-sources">'
        + link(row["fonte_registro"], "Registro TSE: metodologia integral")
        + " · "
        + link(row["fonte_questionario"], "Questionário registrado")
        + " · "
        + link(row["fonte_relatorio"], report_name)
        + f" <small>(páginas de origem: {esc(pages)})</small></p>"
        f'<p><b>Calibração.</b> {esc(row["pesos"])}</p>'
        f'<p><b>Voto passado.</b> {esc(row["voto_detalhe"])}</p>'
        f'<p class="method-caveat"><b>Ponto de atenção.</b> {esc(row["alerta"])}</p>'
        f'<ol class="method-criteria">{scores}</ol>'
        '<details class="method-matches"><summary>Conferir o sinal relativo, onda a onda</summary>'
        '<p class="note">Diferenças Lula − Flávio em votos válidos, sem reponderação. '
        "A última coluna identifica os outros institutos usados naquela data.</p>"
        '<div class="table-scroll" tabindex="0" role="region" aria-label="Comparações de '
        f'{esc(row["instituto"])}"><table><thead><tr>'
        '<th scope="col">Onda</th><th scope="col">Diferença</th><th scope="col">Mediana dos outros</th>'
        '<th scope="col">Desvio</th><th scope="col">Comparadores</th></tr></thead>'
        f"<tbody>{observations}</tbody></table></div></details></div></details>"
    )


def section_html():
    data = load_data()
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    rows = data["institutos"]
    rubric = "".join(f"<li><b>{esc(n)}.</b> {esc(r)}</li>" for n, r in CRITERIA)
    return (
        '<section id="comparar-metodos" class="chapter method-section"><div class="wrap">'
        '<p class="eyebrow">13 institutos · registros conferidos em 21/09/2026</p>'
        "<h2>Quem pergunta, quem responde<br>e como cada voto pesa.</h2>"
        '<p class="lead">A modalidade da entrevista é só o começo. O recrutamento decide quem pode entrar; '
        "a ponderação decide quanto cada resposta vale. Aqui estão as diferenças documentadas, "
        "uma onda nacional por instituto, incluindo os que não entram na reponderação por renda.</p>"
        '<div class="method-highlights">'
        "<article><span>01 · A fonte importa</span><h3>PNAD não é uma edição única.</h3>"
        "<p>Quaest combina renda anual 2025 e escolaridade trimestral 2026. Palver usa 2024. "
        "Futura, PoderData e Real Time ainda declaram Censo 2010 para renda.</p></article>"
        "<article><span>02 · Pergunta não é peso</span><h3>Medir 2022 não significa calibrar por 2022.</h3>"
        "<p>Palver declara o 2º turno nos pesos. Atlas declara voto anterior, sem especificar o turno. "
        "Vários outros perguntam a lembrança de voto, mas não a declaram na calibração.</p></article>"
        "<article><span>03 · Nota com critério</span><h3>Auditabilidade, de zero a dez.</h3>"
        "<p>A nota avalia os documentos desta onda. Não mede simpatia política, acerto futuro "
        "nem cumprimento certificado de padrões internacionais.</p></article></div>"
        '<p class="note">Plano registrado e execução relatada são apresentados separadamente quando divergem. '
        "Os controles de campo são declarações dos institutos, não verificações nossas. "
        "PPT: probabilidade proporcional ao tamanho; RDD: geração aleatória de números; "
        "CATI: entrevista telefônica assistida por computador; IVR/URA: entrevista automatizada por voz.</p>"
        '<div class="method-controls" hidden>'
        '<label>Encontrar instituto ou fonte<input id="method-search" type="search" placeholder="Nome, PNAD, Censo…"></label>'
        '<label>Modalidade<select id="method-mode"><option value="">Todas</option>'
        "<option>Presencial</option><option>Telefônica</option><option>Online</option><option>Híbrida</option>"
        '</select></label><label>Ordenar<select id="method-sort"><option value="name">Instituto</option>'
        '<option value="score">Maior nota documental</option><option value="lula">Sinal mais Lula</option>'
        '<option value="flavio">Sinal mais Flávio</option></select></label>'
        '<p id="method-count" role="status" aria-live="polite">13 institutos</p></div>'
        '<p class="note">No computador, role a tabela para os lados. No celular, cada linha vira uma ficha. '
        "Abra a nota para ver documentos e critérios.</p>"
        '<div class="method-table-scroll" tabindex="0" role="region" aria-label="Comparativo de metodologias">'
        '<table class="method-table"><caption>Última onda nacional de cada instituto no acervo em 21/09/2026</caption>'
        "<thead><tr>"
        + "".join(
            f'<th scope="col">{h}</th>'
            for h in [
                "Instituto / campo",
                "Coleta",
                "Recrutamento e seleção",
                "Fontes e PNAD",
                "Voto de 2022 nos pesos",
                "Sinal relativo¹",
                "Nota documental²",
            ]
        )
        + "</tr></thead><tbody>"
        + "".join(row_html(r) for r in rows)
        + "</tbody></table></div>"
        '<p class="method-empty" hidden>Nenhum instituto corresponde aos filtros.</p>'
        '<div class="method-explainer"><h3>¹ Sinal de efeito da casa: relativo e exploratório</h3>'
        "<p><b>Mais Lula</b> aponta para o candidato do campo da esquerda; <b>mais Flávio</b>, "
        "para o candidato do campo da direita. <b>Próximo da mediana</b> significa desvio de até "
        "±2 pp, uma faixa editorial de descrição, sem teste de significância. Não significa neutralidade política.</p>"
        "<p>Usamos apenas o segundo turno publicado, Lula × Flávio, nos 45 dias anteriores à referência. "
        "Normalizamos a diferença por <code>100 × (Lula − Flávio) / (Lula + Flávio)</code>, excluindo a não escolha. "
        "Para cada onda, comparamos com a mediana de pelo menos três outros institutos, "
        "usando só a onda mais próxima de cada um, dentro de ±7 dias da data central de campo. "
        "A tabela mostra a mediana desses desvios por instituto. Revisões substituem a mesma amostra.</p>"
        '<p class="note">É uma aproximação descritiva ao efeito da casa, não uma estimativa de viés contra a verdade. '
        "A mediana também pode errar. Datas, questionários, universos e métodos mudam; "
        "ondas e comparadores se sobrepõem. Menos de três ondas recebe o aviso “poucas ondas”. "
        "O sinal não autoriza atribuir intenção partidária nem entra na nota. "
        "Futura mudou escolaridade; Palver mudou calibração; o resumo recente pode atravessar versões do método.</p></div>"
        '<details class="method-rubric"><summary>² Como calculamos a nota de qualidade documental</summary>'
        "<p>Dez critérios com o mesmo peso: <b>1</b> quando atendido nos documentos consultados, "
        "<b>0,5</b> quando parcial e <b>0</b> quando não localizado. Zero não prova que o instituto "
        "deixe de realizar o procedimento. A nota é da evidência pública reunida para esta onda, "
        "não um ranking permanente de competência, precisão ou qualidade estatística total.</p>"
        "<ol>" + rubric + "</ol>"
        "<p>Rubrica editorial Arvor, inspirada nos "
        + link(
            "https://aapor.org/standards-and-ethics/disclosure-standards/",
            "padrões de divulgação da AAPOR",
        )
        + ". Não é nota, selo ou auditoria oficial da AAPOR. Sua "
        + link(
            "https://aapor.org/standards-and-ethics/transparency-initiative/",
            "Transparency Initiative",
        )
        + " distingue divulgação de julgamento sobre rigor. Exigir microdados agora é uma escolha nossa: "
        "a AAPOR admite acesso posterior e não exige liberação pública imediata de toda base.</p>"
        "<p>O "
        + link(
            "https://www.pewresearch.org/methods/2023/09/07/comparing-two-types-of-online-survey-samples/",
            "Pew Research Center",
        )
        + " distingue coleta online de recrutamento probabilístico ou opt-in. Por isso, modalidade não rende "
        "bônus ou punição automática. O "
        + link("https://jpsm.umd.edu/node/4585", "JPSM, Universidade de Maryland")
        + " trata qualidade pelo erro total: cobertura, não resposta, amostragem, mensuração e processamento. "
        "Uma margem nominal de erro não resume esses componentes.</p></details>"
        '<h3 class="method-files-title">Documentos e justificativas, instituto por instituto</h3>'
        + "".join(detail_html(r) for r in rows)
        + '<p class="note">'
        + link(
            "assets/reponderacao_metodologias.json",
            "Baixar evidências, notas e todas as comparações em JSON",
        )
        + " · "
        + link(
            "https://pesqele-divulgacao.tse.jus.br/app/pesquisa/listar.xhtml",
            "Consulta original no PesqEle",
        )
        + ". Os excertos preservam integralmente as três seções metodológicas do registro, sem dados pessoais de contato.</p>"
        "</div></section>"
    )
