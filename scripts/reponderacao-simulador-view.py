"""Primeira tela do 2º turno: placar estático, controles e evidência recolhida."""

import importlib
import json
from html import escape as esc

COUNT = importlib.import_module("reponderacao-contagem")
PROJECTION = importlib.import_module("reponderacao-projecao-view")
TURNOUT = importlib.import_module("reponderacao-comparecimento-view")
PRESENCE = importlib.import_module("reponderacao-presenca-view")
UNDECIDED = importlib.import_module("reponderacao-indecisos-view")

PRESETS = [
    ("central", "Central selecionada", {}),
    ("igual", "Sem ajuste extra · 0%", {"presenca_relativa": 0}),
    ("fmenos", "Flávio −5%", {"presenca_relativa": -5}),
    ("fcinco", "Hipótese anterior +5%", {"presenca_relativa": 5}),
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
    counts = COUNT.counts(c, data["electorate"])
    electorate_label = f"{counts['eleitorado']:,}".replace(",", ".")
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
        + PROJECTION.central_cards(data)
        + '<div class="rs-app"><div class="rs-result">'
        '<div class="rs-result-top"><span id="rs-label">Central Média Arvor</span>'
        f'<span id="rs-reference">{esc(data["reference"])}</span></div>'
        '<p class="rs-unit">Votos válidos · projeção condicional</p>'
        '<div class="rs-score" aria-live="polite" aria-atomic="true">'
        f'<div class="rs-flavio"><span>Flávio Bolsonaro</span><strong id="rs-flavio">{fmt(c["flavio"])}<small>%</small></strong>'
        f'<span class="rs-vote-count" id="rs-count-flavio">{fmt(counts["flavio"] / 1e6)} milhões de votos</span></div>'
        f'<div class="rs-lula"><span>Lula</span><strong id="rs-lula">{fmt(c["lula"])}<small>%</small></strong>'
        f'<span class="rs-vote-count" id="rs-count-lula">{fmt(counts["lula"] / 1e6)} milhões de votos</span></div></div>'
        '<div class="rs-duel" aria-hidden="true">'
        f'<span id="rs-bar-flavio" style="width:{c["flavio"]}%"></span><span id="rs-bar-lula" style="width:{c["lula"]}%"></span><i></i></div>'
        f'<p class="rs-gap">Flávio − Lula <b id="rs-gap">{signed(c["diferenca_flavio_lula"])} pp</b></p>'
        f'<p class="rs-gap-volume" id="rs-count-gap">{signed(counts["diferenca_flavio_lula"] / 1e6)} milhões de votos</p>'
        '<p id="rs-versus">Positivo favorece Flávio; negativo favorece Lula.</p>'
        '<div class="rs-account" aria-live="polite" aria-atomic="true"><div><span>Abstenção</span>'
        f'<b id="rs-count-abstencao">{fmt(counts["abstencao"] / 1e6)} <small>milhões</small></b>'
        f'<small><span id="rs-absent">{fmt(c["abstencao"])}%</span> do eleitorado</small></div><div><span>Brancos e nulos</span>'
        f'<b id="rs-count-branco_nulo">{fmt(counts["branco_nulo"] / 1e6)} <small>milhões</small></b>'
        f'<small><span id="rs-invalid">{fmt(100 * c["branco_nulo"] / c["comparecimento"])}%</span> de quem comparece</small></div>'
        "<div><span>Total de votos válidos</span>"
        f'<b id="rs-count-validos">{fmt(counts["validos"] / 1e6)} <small>milhões</small></b>'
        "<small>Flávio + Lula</small></div><div><span>Compareceriam</span>"
        f'<b id="rs-count-comparecimento">{fmt(counts["comparecimento"] / 1e6)} <small>milhões</small></b>'
        f'<small><span id="rs-attendance">{fmt(c["comparecimento"])}%</span> do eleitorado</small></div>'
        '<p class="rs-count-base">Base: <span id="rs-count-eleitorado">'
        f'{fmt(counts["eleitorado"] / 1e6)} milhões de eleitores · TSE 2026 · Brasil, sem exterior</span>. '
        "Totais condicionais, arredondados a 0,1 milhão.</p></div>"
        + TURNOUT.readout(data)
        + '<div id="rs-uncertainty" class="rs-uncertainty" hidden aria-live="polite"><p class="rs-unit">Monte Carlo · faixa central de 90% dos sorteios</p><div id="rs-mc-ranges"></div><p id="rs-mc-frequency"></p><p class="rs-mc-note">Comparecimento fixado no cenário escolhido. Faixa condicional às hipóteses; cobertura contra a urna não validada. Não é chance de vitória medida.</p></div>'
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
            0.1,
            "%",
            "Multiplica a taxa de presença de Flávio; a de Lula é a referência. +3,8% é relativo, não +3,8 pontos. O total é recalibrado.",
            "rs-primary",
        )
        + '<p id="rs-rates" class="rs-rates"></p>'
        + PRESENCE.note(data)
        + UNDECIDED.controls(data, slider)
        + slider(
            data,
            "comparecimento",
            "Comparecimento nacional",
            40,
            95,
            0.5,
            "%",
            "Central: comparecimento observado em 2026, sem mudança automática entre turnos. A ausência uniforme reduz o volume; os válidos só mudam se uma taxa atingir 100%.",
        )
        + TURNOUT.controls(data)
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
        + '<details class="rs-advanced"><summary>Mais hipóteses: base, idade e saídas desiguais</summary>'
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
            "vies_pp",
            "Erro comum na diferença Flávio − Lula",
            -10,
            10,
            0.25,
            " pp",
            "Cenário livre: desloca a diferença nos válidos, sem adicionar votos. Zero na central; não é correção estimada do erro das pesquisas.",
        )
        + '</details><button type="button" id="rs-reset" class="rs-reset">Restaurar central selecionada</button>'
        '<p id="rs-warning" role="status"></p></div></div>'
        '<noscript><p class="note">Placar central disponível sem JavaScript. Ative JavaScript para criar e compartilhar cenários.</p></noscript>'
        '<p class="rs-central-note"><b>Hipótese compartilhada:</b> <span id="rs-relative-explanation">as duas centrais usam propensão Nexus + ajuste relativo de Flávio +3,8%, referência residual do 1º turno transportada como hipótese. Não é presença medida por candidato.</span> '
        '<span id="rs-base-explanation">Média com peso igual nas casas que permitem sensibilidade de renda.</span> '
        "<b>Não há probabilidade de vitória ou intervalo preditivo validado contra a urna.</b></p>"
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
        + '</div><p class="note">Eleitorado = válidos + brancos/nulos + abstenção. A Média normaliza válidos por pesquisa antes de agregar; a Projeção normaliza a âncora ponderada. As parcelas são cenários por 100 eleitores, não totais medidos.</p></div>'
        '<details class="rs-evidence" id="projecao-validos"><summary>De onde vem a Central Média Arvor e quais pesquisas entram</summary>'
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
        "São inferências ecológicas; a pergunta de presença antecede o 1º turno. A taxa nacional central vem da apuração de 2026 e da comparação de regras históricas entre turnos, não da intenção agregada Vox. "
        "Não há cruzamentos atuais suficientes para opções territoriais por UF neste simulador.</p>"
        "<p>Ajustamos uma margem de renda, conservamos o restante dos pesos do instituto e normalizamos cada vetor completo. "
        "Não escolha sem cruzamento de renda conserva a parcela publicada; a transferência de indecisos tem régua própria e hipótese de destino explícita. "
        "A média usa peso igual por casa. Piso de branco/nulo: zero; teto de presença: 100%; votos válidos nunca negativos.</p>"
        f"<p>Contagem absoluta: {electorate_label} eleitores aptos nas 27 UFs "
        f'(<a href="{esc(data["electorate"]["source_page"])}">apuração presidencial TSE 2026</a>), '
        "excluindo o exterior. A base fica congelada na versão do cenário; não estimamos mudanças de aptidão entre turnos. "
        "Multiplicamos essa base pelas parcelas por 100 eleitores; a diferença em votos usa o total de válidos, não o eleitorado inteiro. "
        "Brancos e nulos são agregados: o modelo não estima a separação entre eles. O arredondamento exibido pode diferir em 0,1 milhão na soma.</p>"
        '<p><a href="assets/reponderacao_simulador.json">Motor, hipóteses e parcelas (JSON)</a> · '
        '<a href="assets/reponderacao_validos.csv">Modos e sensibilidades anteriores (CSV)</a> · '
        '<a href="nexus_btg_28092026.html#modelo">Construção e limites da Nexus</a> · '
        '<a href="reponderacao_pnad_log.html">Histórico documental</a>.</p>'
        "<p>O link registra os parâmetros e a versão dos dados. A imagem leva data, hipóteses e identificação do cenário. "
        "Cada alteração em relação à central é uma sensibilidade escolhida pelo leitor.</p></details>"
        + PROJECTION.evidence(data, table)
        + TURNOUT.evidence(data, table)
        + PRESENCE.evidence(data, table)
        + UNDECIDED.evidence(data, table)
        + f'<script id="rs-data" type="application/json">{encoded}</script></div></section>'
    )
