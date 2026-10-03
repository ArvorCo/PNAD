"""Marcação estática do simulador: cenários prontos, controles agrupados e placar.

O JavaScript de `docs/assets/predicao_2026.js` lê os cenários prontos do JSON
embutido aqui e usa os mesmos parâmetros do motor Python. Nenhum cenário cria
mecanismo novo: todos combinam parâmetros que `motor.scenario` já aceita.
"""

from __future__ import annotations

import json
from html import escape as esc

from .base import GROUPS, REGIONS

PRESETS = (
    {
        "id": "central",
        "nome": "Central",
        "frase": "A conta do modelo, sem nenhuma hipótese do leitor.",
        "parametros": {},
    },
    {
        "id": "util_direita",
        "nome": "Voto útil à direita",
        "frase": "Flávio antecipa metade da reserva que as pesquisas medem para o 2º turno.",
        "parametros": {"voto_flavio": 0.5},
    },
    {
        "id": "util_esquerda",
        "nome": "Voto útil à esquerda",
        "frase": "Lula antecipa metade da reserva que as pesquisas medem para o 2º turno.",
        "parametros": {"voto_lula": 0.5},
    },
    {
        "id": "dois_consolidam",
        "nome": "Os dois consolidam",
        "frase": "Flávio e Lula antecipam, cada um, metade da própria reserva.",
        "parametros": {"voto_flavio": 0.5, "voto_lula": 0.5},
    },
    {
        "id": "abstencao_nordeste",
        "nome": "Abstenção alta no Nordeste",
        "frase": "Comparecimento 5 pp menor nos nove estados do Nordeste.",
        "parametros": {"regioes": {"Nordeste": {"comparecimento_pp": -5}}},
    },
    {
        "id": "abstencao_sul_sudeste",
        "nome": "Abstenção alta no Sul e Sudeste",
        "frase": "Comparecimento 5 pp menor nos sete estados do Sul e do Sudeste.",
        "parametros": {
            "regioes": {
                "Sudeste": {"comparecimento_pp": -5},
                "Sul": {"comparecimento_pp": -5},
            }
        },
    },
    {
        "id": "erro_flavio",
        "nome": "Erro comum pró-Flávio +3 pp",
        "frase": "As pesquisas subestimam a diferença de Flávio sobre Lula em 3 pp em todas as UFs.",
        "parametros": {"vies_pp": 3},
    },
    {
        "id": "erro_lula",
        "nome": "Erro comum pró-Lula −3 pp",
        "frase": "As pesquisas subestimam a diferença de Lula sobre Flávio em 3 pp em todas as UFs.",
        "parametros": {"vies_pp": -3},
    },
    {
        "id": "indecisos_nao_escolhem",
        "nome": "Indecisos não escolhem",
        "frase": "Nenhum indeciso chega a voto válido: no motor, viram branco ou nulo entre os votantes.",
        "parametros": {"indecisos_validos": 0},
    },
    {
        "id": "diferencial_flavio",
        "nome": "Comparecimento diferencial +3 Flávio",
        "frase": "Quem prefere Flávio comparece 3 pp mais que quem prefere Lula; o total da UF fica igual.",
        "parametros": {"diferencial_pp": 3},
    },
    {
        "id": "diferencial_lula",
        "nome": "Comparecimento diferencial +3 Lula",
        "frase": "Quem prefere Lula comparece 3 pp mais que quem prefere Flávio; o total da UF fica igual.",
        "parametros": {"diferencial_pp": -3},
    },
)

# (parâmetro, título, mínimo, máximo, passo, sufixo); a central é zero em todos.
RANGES = {
    "voto_flavio": ("Reserva antecipada para Flávio", 0, 100, 1, "%"),
    "voto_lula": ("Reserva antecipada para Lula", 0, 100, 1, "%"),
    "comparecimento_pp": ("Mudança geral de comparecimento", -15, 15, 0.5, " pp"),
    "diferencial_pp": ("Comparecimento de Flávio menos o de Lula", -15, 15, 0.5, " pp"),
    "secoes_abstencao_pp": (
        "Comparecimento nas seções com abstenção ≥30% em 2022",
        -15,
        15,
        0.5,
        " pp",
    ),
    "vies_pp": ("Erro comum das pesquisas a favor de Flávio", -8, 8, 0.25, " pp"),
    "branco_nulo_pp": ("Mudança de brancos e nulos", -3, 10, 0.25, " pp"),
}

RESERVA = (
    "Fração da diferença positiva entre o 2º e o 1º turno do candidato na mesma "
    "pesquisa. É um limite de cenário; as margens não revelam de onde saiu cada "
    "eleitor. A origem adicional é o bloco de demais candidaturas. Se os dois "
    "finalistas pedirem mais do que existe, os fluxos são reduzidos na mesma "
    "proporção. Nenhum voto é criado."
)

HELP = {
    "base": "Define a média nacional que calibra as 27 UFs. A central inclusiva pondera cada casa pela recência do campo; as outras opções isolam a recência, a reponderação PNAD, os placares publicados ou o desvio relativo das casas.",
    "comparecimento_modelo": "Taxa de partida de cada UF: a estadual de 2022 ou a soma das seções de 2022 com os pesos territoriais de 2026. Preferência por seção não foi medida.",
    "eleitor_provavel": "Onde a pesquisa publica voto por hábito de comparecimento, os grupos são misturados pela chance declarada de votar. Sem cruzamento publicado, o fator é neutro, sem extrapolar de outra UF.",
    "exterior": "Inclui os eleitores no exterior, com prior de 2022, movimento nacional de 2026 e incerteza própria.",
    "voto_flavio": RESERVA,
    "voto_lula": RESERVA,
    "comparecimento_pp": "Soma pontos percentuais à taxa de comparecimento de todas as UFs. Os ajustes por região e por UF somam-se a este.",
    "diferencial_pp": "Muda a taxa de quem prefere Flávio em relação à de quem prefere Lula e recalibra as taxas para preservar o comparecimento total da UF. É hipótese residual, adicional ao eleitor provável. O TSE não publica voto individual de ausentes.",
    "secoes_abstencao_pp": "Muda o comparecimento só nas seções que tiveram 30% ou mais de abstenção em 2022, na proporção do peso delas na UF. Altera o peso territorial, não a preferência.",
    "vies_pp": "Move a diferença F−L de todas as UFs na mesma direção: +2 pontos transferem um ponto de Lula para Flávio. Ajustar este controle para chegar a um resultado desejado é cenário do leitor, não evidência de viés do instituto.",
    "branco_nulo_pp": "Soma pontos à taxa de brancos e nulos entre os votantes de todas as UFs.",
    "indecisos_validos": "Parcela dos indecisos que chega a voto válido. O restante vira branco ou nulo entre os votantes; o comparecimento não muda.",
    "indecisos_flavio": "Como se dividem os indecisos que escolhem: proporcional às candidaturas na UF ou numa divisão fixa entre os dois finalistas.",
    "regioes": "Pontos de comparecimento por região, somados à mudança geral.",
    "uf": "Muda comparecimento, diferencial ou reserva de uma UF. Campo vazio segue o controle geral; zero desliga a antecipação naquela UF.",
}

ANCHORS = (
    ("inclusivo", "Central inclusiva, com recência"),
    ("sem_recencia", "Mesmas casas centrais, peso temporal igual"),
    ("pnad", "Somente casas com reponderação PNAD"),
    ("publicado", "Publicadas, mesmas casas PNAD"),
    ("todas", "Publicadas, todas as casas elegíveis"),
    ("casas", "Central + remoção do desvio relativo das casas"),
    ("dinamico", "Âncora dinâmica: DLM com efeitos de casa"),
)


def _helpers():
    from . import view

    return view.number, view.millions, view.NAMES


def presets_json():
    return json.dumps(
        [{k: p[k] for k in ("id", "nome", "frase", "parametros")} for p in PRESETS],
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("<", "\\u003c")


def _help(key, title):
    return (
        f'<button type="button" class="help-toggle" aria-expanded="false" '
        f'aria-controls="help-{key}" aria-label="O que é: {esc(title)}">?</button>'
    )


def _help_text(key):
    return f'<p class="help-text" id="help-{key}" hidden>{esc(HELP[key])}</p>'


def _range(key):
    title, lo, hi, step, suffix = RANGES[key]
    shown = "0" + suffix
    return (
        f'<div class="ctl" data-control="{key}"><div class="ctl-head">'
        f'<label for="param-{key}">{esc(title)}</label>'
        f'<output for="param-{key}" id="out-{key}">{shown}</output>{_help(key, title)}</div>'
        f'<input id="param-{key}" data-param="{key}" data-suffix="{suffix}" type="range" '
        f'min="{lo}" max="{hi}" step="{step}" value="0">{_help_text(key)}</div>'
    )


def _select(key, title, options):
    return (
        f'<div class="ctl" data-control="{key}"><div class="ctl-head">'
        f'<label for="param-{key}">{esc(title)}</label>{_help(key, title)}</div>'
        f'<select id="param-{key}">{options}</select>{_help_text(key)}</div>'
    )


def _check(key, title, checked=True):
    return (
        f'<div class="ctl check" data-control="{key}"><div class="ctl-head">'
        f'<input type="checkbox" id="param-{key}"{" checked" if checked else ""}>'
        f'<label for="param-{key}">{esc(title)}</label>{_help(key, title)}</div>{_help_text(key)}</div>'
    )


def bars(current, central):
    """Placar em barras empilhadas: Lula à esquerda, Flávio à direita."""
    number, _, _ = _helpers()

    def track(b, labels):
        p = b["percentuais"]
        parts = []
        for k in ("lula", "outros", "flavio"):
            text = (
                f"<b>{number(p[k])}%</b>"
                if labels and k != "outros" and p[k] > 9
                else ""
            )
            parts.append(f'<div class="seg {k}" style="width:{p[k]:.3f}%">{text}</div>')
        return "".join(parts)

    c = central["percentuais"]
    marks = (
        f'<div class="bar-mark" style="left:{c["lula"]:.3f}%"></div>'
        f'<div class="bar-mark" style="left:{100 - c["flavio"]:.3f}%"></div>'
    )
    return (
        '<div class="bar-row"><span class="bar-label">Cenário</span>'
        f'<div class="bar-track">{track(current, True)}<div class="bar-half"></div>{marks}</div></div>'
        '<div class="bar-row ghost"><span class="bar-label">Central</span>'
        f'<div class="bar-track thin">{track(central, False)}<div class="bar-half"></div></div></div>'
        '<div class="bar-axis"><span>Lula</span><span>50% dos válidos</span><span>Flávio</span></div>'
    )


def render(data, region_table_html):
    number, millions, names = _helpers()
    b = data["central"]["brasil"]
    options = "".join(
        f'<option value="{s["uf"]}">{s["uf"]} · {esc(s["regiao"])}</option>'
        for s in data["estados"]
    )
    regions = "".join(
        f'<label>{esc(r)}<input type="number" data-region="{esc(r)}" min="-20" max="20" step="0.5" value="0"><span>pp</span></label>'
        for r in REGIONS
    )
    anchors = "".join(f'<option value="{k}">{esc(v)}</option>' for k, v in ANCHORS)
    presets = "".join(
        f'<button type="button" class="preset" data-preset="{p["id"]}" aria-pressed="{"true" if p["id"] == "central" else "false"}">'
        f'<b>{esc(p["nome"])}</b><span>{esc(p["frase"])}</span></button>'
        for p in PRESETS
    )
    candidates = "".join(
        f'<div class="sim-candidate {k}"><span>{names[k]}</span><b id="sim-{k}">{number(b["percentuais"][k])}%</b>'
        f'<small id="sim-votos-{k}">{millions(b[k])} votos</small>'
        f'<small class="delta" id="sim-delta-{k}">Igual à central</small></div>'
        for k in GROUPS[:3]
    )
    gap = number(b["margem_flavio_lula"], 2).replace("-", "−")
    groups = (
        (
            "Ponto de partida",
            _select("base", "Âncora nacional", anchors)
            + _select(
                "comparecimento_modelo",
                "Referência de comparecimento",
                '<option value="uf">Taxa estadual de 2022, central</option><option value="secoes">Seções de 2022, pesos territoriais de 2026</option>',
            )
            + _check(
                "eleitor_provavel",
                "Usar cruzamentos de eleitor provável onde publicados",
            )
            + _check("exterior", "Incluir exterior, com prior e incerteza própria"),
        ),
        ("Voto útil", _range("voto_flavio") + _range("voto_lula")),
        (
            "Quem vai votar",
            _range("comparecimento_pp")
            + _range("diferencial_pp")
            + _range("secoes_abstencao_pp")
            + '<details class="ctl-more"><summary>Comparecimento por região</summary>'
            + f'<p class="help-text">{esc(HELP["regioes"])}</p><div class="region-controls">{regions}</div></details>',
        ),
        (
            "Pesquisas e indecisos",
            _range("vies_pp")
            + _range("branco_nulo_pp")
            + _select(
                "indecisos_validos",
                "Indecisos que chegam a voto válido",
                '<option value="1">100%, hipótese central</option><option value="0.75">75%</option><option value="0.5">50%</option><option value="0">0%, viram branco/nulo entre votantes</option>',
            )
            + _select(
                "indecisos_flavio",
                "Destino dos indecisos que escolhem",
                '<option value="">Proporcional às candidaturas na UF</option><option value="0.5">50% Lula, 50% Flávio</option><option value="0.6">40% Lula, 60% Flávio</option><option value="0.4">60% Lula, 40% Flávio</option>',
            ),
        ),
        (
            "Ajuste local",
            f'<ul class="chips" id="uf-edits" aria-label="Ajustes locais"><li class="chip-empty">Nenhuma UF ou região alterada.</li></ul>'
            f'<details class="ctl-more"><summary>Ajustar uma UF</summary>{_help_text("uf").replace(" hidden", "")}'
            f'<label class="field">UF<select id="uf-select">{options}</select></label>'
            '<label class="field">Comparecimento da UF, mudança em pp<input id="uf-turnout" type="number" min="-20" max="20" step=".5" value="0"></label>'
            '<label class="field">Diferença F−L de comparecimento na UF, pp<input id="uf-differential" type="number" min="-20" max="20" step=".5" value="0"></label>'
            '<label class="field">Reserva antecipada para Lula na UF, %<input id="uf-useful-lula" type="number" min="0" max="100" step="1" placeholder="Usar o controle geral"></label>'
            '<label class="field">Reserva antecipada para Flávio na UF, %<input id="uf-useful-flavio" type="number" min="0" max="100" step="1" placeholder="Usar o controle geral"></label>'
            "</details>",
        ),
    )
    controls = "".join(
        f'<fieldset class="ctl-group"><legend>{esc(title)}</legend>{body}</fieldset>'
        for title, body in groups
    )
    central = data["central"]["brasil"]
    return f"""<div class="simulator" id="simulador-app">
      <div class="sim-presets"><p class="eyebrow">Cenários prontos, um clique</p><div class="preset-grid" role="group" aria-label="Cenários prontos">{presets}</div>
      <script type="application/json" id="sim-presets-data">{presets_json()}</script></div>
      <div class="controls"><h3>Sua hipótese, na mesma conta.</h3>{controls}
      <div class="actions"><button id="sim-export" type="button">Baixar meu cenário (JSON)</button></div></div>
      <div class="sim-result" id="sim-result"><div class="sim-head"><p class="eyebrow" id="sim-label">Cenário central</p>
      <div class="sim-head-actions"><button id="sim-reset" type="button">Restaurar central</button><button id="sim-share" type="button">Copiar link do cenário</button></div></div>
      <div class="share-box"><input id="sim-share-url" type="text" readonly hidden aria-label="Link do cenário"><p id="sim-share-status" class="note" role="status"></p></div>
      <div class="sim-bars" id="sim-bars" role="img" aria-label="Placar do cenário em votos válidos, com a central como referência">{bars(central, central)}</div>
      <div class="sim-scores">{candidates}</div>
      <p id="sim-gap" class="gap-readout">Diferença F−L: {gap} pp</p>
      <p id="sim-sentence" class="sim-sentence" aria-live="polite">Sem hipóteses do leitor: cenário central do modelo.</p>
      <div class="mini-account"><span id="sim-attendance">{millions(b['comparecimento'])} votantes</span><span id="sim-absent">{millions(b['abstencao'])} ausentes</span><span id="sim-invalid">{millions(b['branco_nulo'])} brancos/nulos</span></div>
      <div class="sim-table-head"><p class="eyebrow">Resultado por</p><div class="segmented" role="group" aria-label="Agrupar resultado"><button type="button" data-view="regiao" aria-pressed="true">Região</button><button type="button" data-view="uf" aria-pressed="false">UF</button></div></div>
      <div id="sim-region-table">{region_table_html}</div><p class="note" id="sim-conservation">Eleitorado = votos válidos + brancos/nulos + abstenção. A conta fecha.</p>
      <div class="mc"><div class="mc-head"><button class="primary" id="sim-montecarlo" type="button">Simular a incerteza deste cenário</button><button id="sim-cancel" type="button" hidden>Cancelar</button></div>
      <progress id="sim-progress" max="2000" value="0" hidden></progress>
      <p id="sim-uncertainty" role="status">Os intervalos do topo pertencem à previsão central. Mudou hipótese? Simule novamente: são 2.000 sorteios no seu navegador.</p>
      <div class="mc-cards" id="sim-mc-cards" hidden></div><figure class="mc-hist" id="sim-mc-hist" hidden></figure></div>
      <p class="note">As taxas regionais e de UF são somadas à mudança geral. A mudança nas seções afeta o peso territorial dentro da UF; preferência por seção não foi medida. Todo resultado aqui é cenário condicional do leitor, não previsão oficial.</p></div>
      <div class="sim-dock" id="sim-dock"><span><b class="lula" id="dock-lula">{number(b["percentuais"]["lula"])}%</b> Lula</span><span><b class="flavio" id="dock-flavio">{number(b["percentuais"]["flavio"])}%</b> Flávio</span><span id="dock-gap">F−L {gap} pp</span><button type="button" id="dock-reset">Restaurar</button></div></div>"""
