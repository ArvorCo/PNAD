"""Primeira tela do 2º turno: placar estático, controles e evidência recolhida."""

import json
from html import escape as esc

PRESETS = [
    ("central", "Central Arvor", {}),
    ("igual", "Presença relativa neutra", {"presenca_relativa": 0}),
    ("fmenos", "Flávio −5%", {"presenca_relativa": -5}),
    ("fmais", "Flávio +10%", {"presenca_relativa": 10}),
    ("bn", "Brancos/nulos +3 pp", {"branco_nulo_pp": 3}),
    ("u", "Indecisos não escolhem", {"indecisos_validos": 0}),
]


def fmt(n):
    return f"{n:.1f}".replace(".", ",")


def signed(n):
    return ("+" if n > 0 else "−" if n < 0 else "") + fmt(abs(n))


def slider(data, key, label, low, high, step, suffix, help_text, cls=""):
    value = data["defaults"][key]
    return (
        f'<div class="rs-control {cls}"><label for="rs-{key}">{label}'
        f'<output id="rs-out-{key}" for="rs-{key}">{fmt(value)}{suffix}</output></label>'
        f'<input id="rs-{key}" data-param="{key}" type="range" min="{low}" max="{high}" '
        f'step="{step}" value="{value}" aria-describedby="rs-help-{key}">'
        f'<p id="rs-help-{key}">{help_text}</p></div>'
    )


def section_html(data, table):
    c = data["central"]
    presets = "".join(
        f'<button type="button" data-rs-preset="{k}" aria-pressed="{str(k == "central").lower()}">{name}</button>'
        for k, name, _ in PRESETS
    )
    encoded = json.dumps(
        {
            **data,
            "presets": [{"id": k, "nome": n, "parametros": p} for k, n, p in PRESETS],
        },
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    poll_rows = [
        [
            f'<a href="#pesquisa-{esc(p["id"])}">{esc(p["instituto"])}</a>',
            esc(p["divulgacao"]),
            f"{fmt(p['flavio'])} × {fmt(p['lula'])}",
            signed(p["flavio"] - p["lula"]),
        ]
        for p in c["polls"]
    ]
    exclusions = "".join(
        f"<li>{esc(p['instituto'])}: {esc(p['reason'])}</li>" for p in data["excluded"]
    )
    balance = "".join(
        f'<span class="rs-mass rs-{k}" data-mass="{k}" style="width:{v:.6f}%" title="{esc(k)}: {fmt(v)} por 100 eleitores"></span>'
        for k, v in c["por_100_eleitores"].items()
    )
    return (
        '<section id="simulador" class="rs-section"><div class="wrap">'
        '<header class="rs-intro"><div><p class="eyebrow">Eleições 2026 · 2º turno · Agregador Arvor</p>'
        "<h1>O voto conta.<br><em>A presença decide.</em></h1></div>"
        "<p>As pesquisas sob a renda do IBGE, com o comparecimento que você quer testar. "
        "Mova as hipóteses. Compare os votos válidos. Compartilhe seu cenário.</p></header>"
        '<div class="rs-app"><div class="rs-result">'
        '<div class="rs-result-top"><span id="rs-label">Central Arvor</span>'
        f'<span id="rs-reference">{esc(data["reference"])}</span></div>'
        '<p class="rs-unit">Votos válidos · projeção condicional</p>'
        '<div class="rs-score" aria-live="polite" aria-atomic="true">'
        f'<div class="rs-flavio"><span>Flávio Bolsonaro</span><strong id="rs-flavio">{fmt(c["flavio"])}<small>%</small></strong></div>'
        f'<div class="rs-lula"><span>Lula</span><strong id="rs-lula">{fmt(c["lula"])}<small>%</small></strong></div></div>'
        '<div class="rs-duel" aria-hidden="true">'
        f'<span id="rs-bar-flavio" style="width:{c["flavio"]}%"></span><span id="rs-bar-lula" style="width:{c["lula"]}%"></span><i></i></div>'
        f'<p class="rs-gap">Flávio − Lula <b id="rs-gap">{signed(c["diferenca_flavio_lula"])} pp</b></p>'
        '<p id="rs-versus">Positivo favorece Flávio; negativo favorece Lula.</p>'
        '<div class="rs-account"><div><span>Abstenção</span>'
        f'<b id="rs-absent">{fmt(c["abstencao"])}%</b><small>do eleitorado</small></div><div><span>Brancos e nulos</span>'
        f'<b id="rs-invalid">{fmt(100 * c["branco_nulo"] / c["comparecimento"])}%</b><small>de quem comparece</small></div></div>'
        '<div id="rs-response" class="rs-response"><p>Como a presença relativa muda o placar</p>'
        '<svg id="rs-curve" viewBox="0 0 480 155" role="img" aria-label="Sensibilidade à presença relativa de Flávio, mantendo as outras hipóteses"></svg>'
        '<p id="rs-threshold">O gráfico de sensibilidade aparece com o simulador.</p></div>'
        '<div class="rs-share" hidden><button id="rs-copy" type="button">Copiar link</button>'
        '<button id="rs-image" type="button">Baixar imagem</button><button id="rs-share" type="button" hidden>Compartilhar</button></div>'
        '<p id="rs-share-state" role="status"></p>'
        '</div><div class="rs-controls" hidden><div class="rs-presets" role="group" aria-label="Cenários prontos">'
        + presets
        + "</div>"
        + slider(
            data,
            "presenca_relativa",
            "Presença relativa de Flávio",
            -30,
            30,
            0.5,
            "%",
            "Multiplica a taxa de presença de Flávio; a de Lula é a referência. +5% é relativo, não +5 pontos. O total é recalibrado.",
            "rs-primary",
        )
        + '<p id="rs-rates" class="rs-rates"></p>'
        + slider(
            data,
            "comparecimento",
            "Comparecimento nacional",
            40,
            95,
            0.5,
            "%",
            "A ausência uniforme reduz o volume de votos; o placar muda se uma taxa encostar no teto de 100%.",
        )
        + slider(
            data,
            "branco_nulo_pp",
            "Mudança de brancos e nulos",
            -10,
            20,
            0.25,
            " pp",
            "Pontos entre os votantes. A saída comum é proporcional; o piso é zero. Use a saída desigual abaixo para mudar a disputa.",
        )
        + '<details class="rs-advanced"><summary>Mais hipóteses: indecisos, idade e saídas desiguais</summary>'
        '<label for="rs-modo">Base do cenário<select id="rs-modo" data-param="modo"><option value="modelo">PNAD + comparecimento</option><option value="pnad">PNAD, sem propensão Nexus</option><option value="publicado">Publicado, sem propensão Nexus</option></select></label>'
        '<label for="rs-idade">Hipótese de idade na Nexus<select id="rs-idade" data-param="idade"><option value="central">Central histórica</option><option value="idosos60">Presença de 60+ em 60%</option><option value="idosos80">Presença de 60+ em 80%</option></select></label>'
        + slider(
            data,
            "nulo_diferencial_pp",
            "Saída extra para branco/nulo",
            -20,
            20,
            0.5,
            "%",
            "Positivo: percentual dos votos válidos potenciais de Flávio que vira branco/nulo. Negativo: saída equivalente de Lula. Preserva o comparecimento.",
        )
        + slider(
            data,
            "indecisos_validos",
            "Indecisos que escolhem candidato",
            0,
            100,
            5,
            "%",
            "O restante vira branco/nulo entre os votantes. Não vira abstenção.",
        )
        + '<label for="rs-indecisos_flavio">Destino dos indecisos que escolhem<select id="rs-indecisos_flavio" data-param="indecisos_flavio"><option value="p">Proporcional aos que comparecem</option><option value="0">Todos para Lula</option><option value="25">25% para Flávio</option><option value="50">Metade para cada um</option><option value="75">75% para Flávio</option><option value="100">Todos para Flávio</option></select></label>'
        + slider(
            data,
            "vies_pp",
            "Erro comum na diferença Flávio − Lula",
            -10,
            10,
            0.25,
            " pp",
            "Cenário livre: desloca a diferença nos válidos, sem adicionar votos. Zero na central; não é correção estimada do erro das pesquisas.",
        )
        + '</details><button type="button" id="rs-reset" class="rs-reset">Restaurar central Arvor</button>'
        '<p id="rs-warning" role="status"></p></div></div>'
        '<noscript><p class="note">Placar central disponível sem JavaScript. Ative JavaScript para criar e compartilhar cenários.</p></noscript>'
        '<p class="rs-central-note"><b>Central da casa:</b> PNAD + propensão Nexus + presença relativa de Flávio +5%. '
        "A escolha de +5% foi feita após o 1º turno; é hipótese declarada, sem taxa por candidato medida na urna. "
        "<b>Não há probabilidade de vitória ou intervalo preditivo validado.</b></p>"
        '<div class="rs-balance"><h3>Para cada 100 eleitores</h3><div class="rs-mass-bar" aria-hidden="true">'
        + balance
        + '</div><div class="rs-mass-labels">'
        + "".join(
            f'<span class="rs-mass-key rs-{k}">{name} <b id="rs-mass-{k}">{fmt(c["por_100_eleitores"][k])}</b></span>'
            for k, name in [
                ("flavio", "Flávio"),
                ("lula", "Lula"),
                ("branco_nulo", "Brancos/nulos"),
                ("abstencao", "Ausentes"),
            ]
        )
        + '</div><p class="note">Eleitorado = válidos + brancos/nulos + abstenção. Percentuais válidos são calculados em cada pesquisa antes da média; as parcelas são cenários por 100 eleitores, não totais medidos.</p></div>'
        '<details class="rs-evidence" id="projecao-validos"><summary>De onde vem a central e quais pesquisas entram</summary>'
        f"<p>{esc(data['method']['selection'])} {len(data['polls'])} casas com cruzamento elegível. "
        "As comparações usam as mesmas casas. Não reaproveitamos uma onda antiga de uma casa cuja última divulgação é incompleta.</p>"
        + table(
            [
                "Instituto",
                "Divulgação",
                "Flávio × Lula / válidos",
                "Flávio − Lula / pp",
            ],
            poll_rows,
        )
        + "<ul>"
        + exclusions
        + "</ul>"
        "<p>Taxas por candidato são transportadas da tabela sintética de renda × idade × região da Nexus de 28/09. "
        "São inferências ecológicas; a pergunta de presença antecede o 1º turno. A taxa nacional central vem da âncora histórica, não da intenção agregada Vox. "
        "Não há cruzamentos atuais suficientes para opções territoriais por UF neste simulador.</p>"
        "<p>Ajustamos uma margem de renda, conservamos o restante dos pesos do instituto e normalizamos cada vetor completo. "
        "Não escolha sem cruzamento de renda conserva a parcela publicada; o tamanho desconhecido não muda os válidos quando a alocação de indecisos é proporcional. "
        "A média usa peso igual por casa. Piso de branco/nulo: zero; teto de presença: 100%; votos válidos nunca negativos.</p>"
        '<p><a href="assets/reponderacao_simulador.json">Motor, hipóteses e parcelas (JSON)</a> · '
        '<a href="assets/reponderacao_validos.csv">Modos e sensibilidades anteriores (CSV)</a> · '
        '<a href="nexus_btg_28092026.html#modelo">Construção e limites da Nexus</a> · '
        '<a href="reponderacao_pnad_log.html">Histórico documental</a>.</p>'
        "<p>O link registra os parâmetros e a versão dos dados. A imagem leva data, hipóteses e identificação do cenário. "
        "Cada alteração em relação à central é uma sensibilidade escolhida pelo leitor.</p></details>"
        f'<script id="rs-data" type="application/json">{encoded}</script></div></section>'
    )
