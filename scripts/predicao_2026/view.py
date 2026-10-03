"""Renderização estática completa; JS acrescenta cenários, não esconde o laudo."""

from __future__ import annotations

import json
import re
from html import escape as esc

from .base import GROUPS, REGIONS
from .mapa import explorer

NAMES = {
    "lula": "Lula",
    "flavio": "Flávio Bolsonaro",
    "outros": "Demais candidaturas",
    "renan_santos": "Renan Santos",
    "cury": "Augusto Cury",
    "caiado": "Ronaldo Caiado",
    "zema": "Romeu Zema",
    "restantes": "Demais nomes sem abertura uniforme",
}
COLORS = {"lula": "#b02f21", "flavio": "#1457aa", "outros": "#0f7f5f"}


def number(x, places=1):
    return f"{x:,.{places}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def millions(x):
    return number(x / 1e6, 2) + " mi"


NUMERIC_CELL = re.compile(
    r"^[+\-\u2212\u2013]?\d[\d.,]*(\s?(%|pp|mi|mil|pts?|dias?|casas?|ondas?|\u00d7))?$"
)


def is_numeric_cell(value):
    text = re.sub(r"<[^>]+>", "", str(value)).strip()
    return bool(NUMERIC_CELL.match(text))


def numeric_columns(rows, width):
    """Colunas em que quase todas as células são números: alinhadas à direita."""
    columns = set()
    for j in range(width):
        cells = [row[j] for row in rows if j < len(row) and str(row[j]).strip()]
        if cells and sum(map(is_numeric_cell, cells)) >= 0.8 * len(cells):
            columns.add(j)
    return columns


def table(headers, rows, label, sortable=False):
    numeric = numeric_columns(rows, len(headers))

    def cls(j):
        return ' class="num"' if j in numeric else ""

    head = "".join(
        f'<th scope="col"{cls(j)}>{esc(h)}</th>' for j, h in enumerate(headers)
    )
    body = "".join(
        "<tr>" + "".join(f"<td{cls(j)}>{v}</td>" for j, v in enumerate(row)) + "</tr>"
        for row in rows
    )
    return (
        f'<div class="table-scroll" tabindex="0" role="region" aria-label="{esc(label)}">'
        f'<table{" data-sortable" if sortable else ""}><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def percent_bar(key, point, low, high, top):
    """Barra de placar: a estimativa pontual e a faixa de 90% na mesma escala."""

    def pct(x):
        return f"{100 * x / top:.2f}"

    label = (
        f"{NAMES[key]}: estimativa {number(point)}%, "
        f"faixa de 90% de {number(low)}% a {number(high)}%, escala de 0 a {top:.0f}%"
    )
    return (
        f'<div class="pbar {key}" role="img" aria-label="{label}">'
        f'<div class="pbar-fill" style="width:{pct(point)}%"></div>'
        f'<div class="pbar-band" style="left:{pct(low)}%;width:{pct(high - low)}%"></div>'
        "</div>"
    )


def hero(data):
    b, uncertainty = data["central"]["brasil"], data["incerteza"]
    quantiles = {k: uncertainty["candidatos"][k]["percentual"] for k in GROUPS[:3]}
    top = float(max(10, -(-max(q["p95"] for q in quantiles.values()) // 10) * 10))
    cards = []
    for k in GROUPS[:3]:
        q = quantiles[k]
        cards.append(
            f'<div class="candidate {k}"><span>{NAMES[k]}</span>'
            f'<b>{number(b["percentuais"][k])}<small>%</small></b>'
            f"<strong>{millions(b[k])} votos</strong>"
            f'{percent_bar(k, b["percentuais"][k], q["p05"], q["p95"], top)}'
            f'<p>Faixa de 90%: {number(q["p05"])}% a {number(q["p95"])}%</p></div>'
        )
    return '<div class="scoreboard">' + "".join(cards) + "</div>"


def accounting(data):
    b = data["central"]["brasil"]
    return "".join(
        f"<div><b>{millions(b[k])}</b><span>{label}</span></div>"
        for k, label in (
            ("eleitorado", "eleitores aptos"),
            ("abstencao", "abstenções esperadas"),
            ("branco_nulo", "brancos e nulos esperados"),
            ("validos", "votos válidos esperados"),
        )
    )


def region_chart(data):
    rows = [(name, data["central"]["regioes"][name]) for name in REGIONS]
    parts = [
        '<svg viewBox="0 0 980 340" role="img" aria-label="Votos válidos previstos por região, em milhões" xmlns="http://www.w3.org/2000/svg">'
    ]
    maximum = max(v["validos"] for _, v in rows)
    for i, (name, v) in enumerate(rows):
        y, x = 40 + 54 * i, 180.0
        parts.append(
            f'<text x="0" y="{y+21}" fill="#192e2b" font-size="17">{esc(name)}</text>'
        )
        for k in GROUPS[:3]:
            w = 650 * v[k] / maximum
            parts.append(
                f'<rect data-region="{esc(name)}" data-candidate="{k}" x="{x:.2f}" y="{y}" width="{w:.2f}" height="32" fill="{COLORS[k]}"><title>{NAMES[k]}: {millions(v[k])} votos</title></rect>'
            )
            if w > 45:
                parts.append(
                    f'<text x="{x+w/2:.2f}" y="{y+21}" text-anchor="middle" fill="#fff" font-size="15">{number(v[k]/1e6,1)}</text>'
                )
            x += w
        parts.append(
            f'<text x="{x+12:.2f}" y="{y+21}" fill="#192e2b" font-size="15">{millions(v["validos"])}</text>'
        )
    parts.append(
        '<text x="180" y="328" font-size="13" fill="#535b54">Comprimento = volume de votos, não superfície territorial. Exterior no quadro próprio.</text></svg>'
    )
    return "".join(parts)


def region_table(data):
    rows = []
    for name, b in data["central"]["regioes"].items():
        rows.append(
            [
                esc(name),
                millions(b["eleitorado"]),
                number(100 * b["comparecimento"] / b["eleitorado"]) + "%",
                millions(b["validos"]),
                *[number(b["percentuais"][k]) + "%" for k in GROUPS[:3]],
            ]
        )
    return table(
        [
            "Região",
            "Eleitorado",
            "Comparecimento",
            "Votos válidos",
            "Lula",
            "Flávio",
            "Demais",
        ],
        rows,
        "Previsão central por região",
    )


def state_table(data):
    scenarios = {s["uf"]: s for s in data["central"]["ufs"]}
    rows = []
    for s in sorted(data["estados"], key=lambda s: -s["eleitorado"]):
        b = scenarios[s["uf"]]
        pct = {k: 100 * b[k] / sum(b[k] for k in GROUPS[:3]) for k in GROUPS[:3]}
        rows.append(
            [
                f'<a href="#estado-{s["uf"]}">{s["uf"]}</a>',
                esc(s["regiao"]),
                millions(b["eleitorado"]),
                number(100 * b["comparecimento"] / b["eleitorado"]) + "%",
                *[number(pct[k]) + "%" for k in GROUPS[:3]],
                str(len(s["pesquisas"])) if s["pesquisas"] else "Prior, sem pesquisa",
            ]
        )
    return table(
        [
            "UF",
            "Região",
            "Eleitorado",
            "Comparecimento",
            "Lula",
            "Flávio",
            "Demais",
            "Pesquisas",
        ],
        rows,
        "Previsão central das 27 UFs e exterior",
        sortable=True,
    )


def map_svg(data):
    return explorer(data)


def sensitivity(data):
    rows = []
    for name, result in data["sensibilidades"].items():
        b = result["brasil"]
        rows.append(
            [
                esc(name),
                *[number(b["percentuais"][k], 2) + "%" for k in GROUPS[:3]],
                number(b["margem_flavio_lula"], 2) + " pp",
                millions(b["validos"]),
            ]
        )
    return table(
        ["Hipótese", "Lula", "Flávio", "Demais", "Diferença F−L", "Válidos"],
        rows,
        "Sensibilidade às hipóteses do modelo",
    )


def house_table(data):
    rows = []
    for name, values in data["nacional"]["efeitos_casa"].items():
        d = values["desvio_margem_pp"]
        rows.append(
            [
                esc(name),
                str(values["n_ondas"]),
                number(d, 2) + " pp",
                "Mais Lula" if d > 0 else "Mais Flávio",
                "Exploratório" if values["n_ondas"] >= 3 else "Poucas ondas",
            ]
        )
    return table(
        [
            "Casa",
            "Ondas comparáveis",
            "Desvio L−F nos válidos",
            "Direção relativa",
            "Evidência",
        ],
        rows,
        "Diferenças contemporâneas entre institutos",
    )


LEVEL = {
    "pdf_do_instituto": "PDF do instituto",
    "infografico_do_instituto": "Infográfico do instituto",
    "materia_do_contratante": "Matéria do contratante",
    "imprensa_concordante": "Imprensa, dois veículos",
    "imprensa_divergente": "Imprensa divergente",
}
E22_GROUPS = ("lula", "bolsonaro", "tebet", "ciro")


def pp_signed(x, places=2):
    """Número com sinal explícito e menos tipográfico, para colunas de erro."""
    return (("+" if x > 0 else "") + number(x, places)).replace("-", "\u2212")


def _e22_source(house):
    doc = house["documentos"][0]
    title = f"Arquivado em {doc['arquivo']} (SHA-256 {doc['sha256'][:12]})"
    level = str(house["nivel"])
    label = LEVEL.get(level) or level
    return (
        f'<a href="{esc(doc["url"], quote=True)}" title="{esc(title, quote=True)}">'
        f"{esc(label)}</a>"
    )


def erro_2022_table(data):
    """Erro de cada casa no 1º turno de 2022 contra o TSE, com média e dispersão."""
    e = data["erro_2022"]
    media = e["media_das_casas"]
    included = set(media["casas"])
    houses = sorted(
        e["por_casa"],
        key=lambda h: (
            h["id"] not in included,
            -h["diferenca_lula_menos_bolsonaro"]["erro"],
        ),
    )

    def row(h):
        name = esc(h["casa"])
        if h["id"] not in included:
            name += " <small>(fora da média)</small>"
        c = h["campo"]
        start = f"{c['inicio'][8:10]}/{c['inicio'][5:7]}"
        end = f"{c['fim'][8:10]}/{c['fim'][5:7]}"
        field = start if start == end else f"{start} a {end}"
        return [
            name,
            esc(h["registro"]),
            field,
            pp_signed(h["diferenca_lula_menos_bolsonaro"]["erro"]),
            *[pp_signed(h["erro_pp"][k]) for k in E22_GROUPS],
            _e22_source(h),
        ]

    rows = [row(h) for h in houses if h["id"] in included]
    common = media["erro_comum_pp"]
    sd = media["desvio_padrao_entre_casas_pp"]
    rows.append(
        [
            f"<strong>Média das {media['n_casas']} casas (erro comum)</strong>",
            "",
            "",
            "<strong>"
            + pp_signed(media["erro_comum_diferenca_lula_menos_bolsonaro"])
            + "</strong>",
            *[pp_signed(common[k]) for k in E22_GROUPS],
            "TSE, eleição 544",
        ]
    )
    rows.append(
        [
            "Dispersão entre casas (desvio padrão)",
            "",
            "",
            number(sd["diferenca_lula_menos_bolsonaro"], 2),
            *[number(sd[k], 2) for k in E22_GROUPS],
            "",
        ]
    )
    rows += [row(h) for h in houses if h["id"] not in included]
    return table(
        [
            "Casa",
            "Registro TSE",
            "Campo (2022)",
            "Erro na diferença L−B",
            "Lula",
            "Bolsonaro",
            "Tebet",
            "Ciro",
            "Fonte",
        ],
        rows,
        "Erro das pesquisas no 1º turno de 2022, pontos dos válidos, pesquisa menos urna",
    )


def erro_2022_vs_2026(data):
    """Erro de 2022 ao lado do desvio relativo de 2026; o segundo não é erro."""
    lines = sorted(
        data["erro_2022"]["comparacao_2026"]["linhas"],
        key=lambda r: -r["erro_2022_diferenca_lula_menos_bolsonaro_pp"],
    )
    rows = [
        [
            esc(r["casa_2022"]),
            esc(r["casa_2026"]),
            esc(r["ligacao"]),
            pp_signed(r["erro_2022_diferenca_lula_menos_bolsonaro_pp"]),
            pp_signed(r["desvio_relativo_2026_lula_menos_flavio_pp"]),
            str(r["ondas_2026"]),
        ]
        for r in lines
    ]
    return table(
        [
            "Casa em 2022",
            "Casa em 2026",
            "Ligação",
            "Erro 2022 na diferença L−B",
            "Desvio relativo 2026 L−F",
            "Ondas 2026",
        ],
        rows,
        "Erro de 2022 contra o TSE e desvio relativo de 2026 contra as outras casas",
    )


def poll_table(data):
    chosen = {p["id"] for p in data["nacional"]["pareadas"]}
    rows = []
    for p in data["nacional"]["selecionadas"]:
        v = p["pnad_vetor"] if p["id"] in chosen else p["publicado_vetor"]
        rows.append(
            [
                f'<a href="reponderacao_pnad.html#pesquisas">{esc(p["instituto"])}</a>',
                esc(p["campo"]["fim"]),
                esc(p["divulgacao"]),
                number(p["n"], 0),
                number(p["idade_campo_dias"], 1),
                number(p["participacao_central_pct"], 2) + "%",
                number(v[0] * 100) + "%",
                number(v[1] * 100) + "%",
                (
                    "Central, renda transportada PNAD"
                    if p["id"] in chosen
                    else "Central, placar publicado; sem voto × renda"
                ),
            ]
        )
    return table(
        [
            "Casa",
            "Fim do campo",
            "Divulgação",
            "n",
            "Idade do campo (dias)",
            "Peso na central",
            "Lula",
            "Flávio",
            "Uso",
        ],
        rows,
        "Ondas nacionais selecionadas",
    )


def state_details(data):
    blocks = []
    for s in sorted(data["estados"], key=lambda s: s["uf"]):
        rows = []
        for p in s["pesquisas"]:
            source = (
                f'<a href="{esc(p["fonte"], quote=True)}">Fonte</a>'
                if p["fonte"] and p["fonte"].startswith("https://")
                else "Acervo, hash no JSON"
            )
            rows.append(
                [
                    esc(p["instituto"]),
                    esc(p["campo"]["fim"]),
                    number(p["idade_dias"], 1),
                    number(
                        100
                        * p["peso_modelo"]
                        / (
                            data["configuracao"]["peso_prior"]
                            + sum(x["peso_modelo"] for x in s["pesquisas"])
                        ),
                        2,
                    )
                    + "%",
                    str(p["n"]),
                    esc(p["registro"] or "Não localizado"),
                    f'p. {p["pagina"]}',
                    source,
                    esc(p["disponibilidade"]),
                ]
            )
        t = s["tse"]
        coverage = 100 * t["pareados_eleitores"] / t["eleitorado"]
        blocks.append(
            f'<details id="estado-{s["uf"]}" class="state-file"><summary><b>{s["uf"]}</b><span>{esc(s["regiao"])} · {millions(s["eleitorado"])} eleitores · {len(rows)} pesquisas</span></summary>'
            f'<p>{number(coverage)}% dos eleitores de 2026 estão em seções com chave também encontrada em 2022. A prior territorial pesa {number(s["peso_prior"]*100)}% no pooling. '
            f'{"Há cruzamento publicado por hábito de comparecimento." if s["sinal_comparecimento"] else "Sem cruzamento elegível por comparecimento: fator neutro, sem extrapolar de outra UF."}</p>'
            + (
                table(
                    [
                        "Casa",
                        "Campo final",
                        "Idade (dias)",
                        "Peso territorial com prior",
                        "n",
                        "Registro",
                        "Página",
                        "Documento",
                        "Disponibilidade",
                    ],
                    rows,
                    f"Fontes de {s['uf']}",
                )
                if rows
                else "<p>Exterior: prior histórica de 2022 com movimento nacional de 2026. Transporte entre Jair e Flávio é hipótese; nenhum eleitor individual é identificado.</p>"
            )
            + "</details>"
        )
    return "".join(blocks)


def source_updates(data):
    rows = [
        [
            esc(p["instituto"]),
            esc(p["uf"]),
            esc(p["status"]),
            f'<a href="{esc(p["url"], quote=True)}">Documento localizado</a>',
            esc(p["motivo"]),
        ]
        for p in data["fontes_inspecionadas"]
    ]
    return table(
        ["Casa", "UF", "Situação", "Fonte", "Motivo"],
        rows,
        "Fontes localizadas que não entraram na atualização",
    )


def turnout_checks(data):
    rows = []
    for s in sorted(data["estados"], key=lambda x: x["uf"]):
        p = s["sinal_comparecimento"]
        if not p or "recomposicao_envelope_arredondamento_pct" not in p:
            continue
        lo, hi = p["recomposicao_envelope_arredondamento_pct"]
        rows.append(
            [
                s["uf"],
                esc(p["rodada"]),
                f'{p["pagina_grupos"]} / {p["pagina_voto"]}',
                number(p["cobertura_pct"], 0) + "%",
                " / ".join(
                    number(v, 2) for v in p["recomposicao_residuo_lula_flavio_pp"]
                ),
                f"{number(lo[0], 2)} a {number(hi[0], 2)}%",
                f"{number(lo[1], 2)} a {number(hi[1], 2)}%",
            ]
        )
    return table(
        [
            "UF",
            "Campo",
            "Páginas hábito / voto",
            "Cobertura",
            "Resíduo L / F, pp",
            "Envelope Lula",
            "Envelope Flávio",
        ],
        rows,
        "Conferência aritmética dos cruzamentos de comparecimento",
    )


def abstention(data):
    ufs = [s for s in data["estados"] if s["uf"] != "ZZ"]
    total = sum(s["eleitorado"] for s in ufs)
    rows = []
    for band in ("0 a 10%", "10 a 20%", "20 a 30%", "30 a 40%", "40% ou mais"):
        bins = [b for s in ufs for b in s["tse"]["bins"] if b["faixa"] == band]
        e = sum(b["eleitores_2026"] for b in bins)
        rows.append(
            [
                band,
                number(sum(b["secoes"] for b in bins), 0),
                millions(e),
                number(100 * e / total) + "%",
                (
                    number(
                        sum(
                            b["abstencao_historica_pct"] * b["eleitores_2026"]
                            for b in bins
                        )
                        / e
                    )
                    + "%"
                    if e
                    else "Sem dados"
                ),
            ]
        )
    band_table = table(
        [
            "Abstenção da seção em 2022",
            "Seções pareadas",
            "Eleitores em 2026",
            "Peso no Brasil",
            "Média histórica ponderada",
        ],
        rows,
        "Concentração territorial da abstenção",
    )
    tops = sorted(
        [r for s in ufs for r in s["tse"]["top"]],
        key=lambda r: -r["abstencao_2022_pct"],
    )[:20]
    top_table = table(
        [
            "UF",
            "Município",
            "Zona / seção",
            "Aptos 2022",
            "Eleitores 2026",
            "Abstenção 2022",
        ],
        [
            [
                r["uf"],
                esc(r["municipio"]),
                f'{r["zona"]} / {r["secao"]}',
                number(r["aptos_2022"], 0),
                number(r["eleitores_2026"], 0),
                number(r["abstencao_2022_pct"]) + "%",
            ]
            for r in tops
        ],
        "Seções de maior abstenção, mínimo de 100 eleitores nos dois anos",
    )
    return (
        band_table
        + "<details><summary>Onde a abstenção foi maior: vinte seções, mínimo de 100 aptos em ambos os anos</summary>"
        + top_table
        + "</details>"
    )


def validation(data):
    v = data["validacao"]
    rows = [
        [
            u["uf"],
            number(u["comparecimento_real_pct"]) + "%",
            number(u["previsto_secoes_pct"]) + "%",
            number(u["erro_secoes_pp"], 2) + " pp",
            number(u["erro_uf_pp"], 2) + " pp",
        ]
        for u in v["ufs"]
    ]
    return table(
        [
            "UF",
            "Comparecimento real 2022",
            "Previsão usando seções 2018",
            "Erro por seção",
            "Erro repetindo UF 2018",
        ],
        rows,
        "Validação retrospectiva de comparecimento",
    )


def dlm_table(data):
    """Trajetória filtrada e efeitos de casa do modelo dinâmico."""
    d = data["nacional"]["dinamico"]
    par, final = d["parametros"], d["estado_final"]
    summary = (
        f"<p>{d['n_ondas']} ondas de {len(d['casas'])} casas. Variância de evolução por "
        f"máxima verossimilhança: desvio diário de {number(par['dp_diario_nivel_pp']['lula'], 2)} pp "
        f"no nível de Lula. Variância amostral n/deff multiplicada por "
        f"{number(par['phi_variancia_nao_amostral'], 2)} (erro não amostral estimado). "
        f"Estado em {esc(final['data'])}: Lula {number(final['validos_pct']['lula'], 2)}%, "
        f"Flávio {number(final['validos_pct']['flavio'], 2)}% dos válidos; diferença F−L "
        f"{number(final['margem_flavio_lula_validos_pp'], 2)} pp, desvio "
        f"{number(final['dp_margem_pp'], 2)} pp.</p>"
    )
    path = table(
        ["Data", "Lula", "Flávio", "Demais", "Indecisos", "Branco/nulo", "F−L válidos"],
        [
            [
                esc(r["data"]),
                *[
                    f"{number(v)}% ± {number(e)}"
                    for v, e in zip(r["vetor_pct"], r["dp_pp"], strict=True)
                ],
                f"{number(r['margem_flavio_lula_validos_pp'], 2)} ± {number(r['dp_margem_pp'], 2)}",
            ]
            for r in d["trajetoria"]
            if r["ondas_acumuladas"]
        ],
        "Trajetória filtrada do modelo dinâmico, com um desvio padrão",
    )
    houses = table(
        ["Casa", "Ondas", "Efeito L−F nos válidos", "Desvio", "Lula", "Flávio"],
        [
            [
                esc(name),
                str(h["n_ondas"]),
                number(h["efeito_margem_lula_flavio_validos_pp"], 2) + " pp",
                number(h["dp_margem_pp"], 2) + " pp",
                number(h["efeito_pp"]["lula"], 2) + " pp",
                number(h["efeito_pp"]["flavio"], 2) + " pp",
            ]
            for name, h in d["efeitos_casa"].items()
        ],
        "Efeitos de casa do modelo dinâmico, soma zero entre casas",
    )
    return summary + path + houses


def predictive_table(data):
    """Validação de origem móvel: previsão de pesquisas futuras, não da urna."""
    v = data["validacao_preditiva"]

    def rows(section):
        return [
            [
                esc(m["rotulo"]),
                str(m["n_pares"]),
                number(m["mae_margem_pp"], 2),
                number(m["rmse_margem_pp"], 2),
                number(m["vies_margem_pp"], 2),
                number(m["mae_parcelas_pp"], 2),
            ]
            for m in v[section]["metricas"].values()
        ]

    headers = [
        "Âncora",
        "Pares",
        "MAE L−F (pp)",
        "RMSE L−F (pp)",
        "Viés L−F (pp)",
        "MAE parcelas (pp)",
    ]
    groups = v["origem_movel"].get("por_grupo_horizonte", {})
    by_horizon = table(
        [
            "Horizonte",
            "Âncora",
            "Pares",
            "MAE L−F (pp)",
            "Viés L−F (pp)",
            "Viés Lula (pp)",
            "Viés Flávio (pp)",
            "Viés terceira via (pp)",
        ],
        [
            [
                f"{esc(label)} dias",
                esc(m["rotulo"]),
                str(m["n_pares"]),
                number(m["mae_margem_pp"], 2),
                number(m["vies_margem_pp"], 2),
                number(m["vies_lula_pp"], 2),
                number(m["vies_flavio_pp"], 2),
                number(m["vies_outros_pp"], 2),
            ]
            for label, g in groups.items()
            for m in g["metricas"].values()
        ],
        "Origem móvel por horizonte, com viés por candidatura (previsto menos observado)",
    )
    acceleration = v.get("aceleracao")
    accel = (
        table(
            headers,
            [
                [
                    esc(m["rotulo"]),
                    str(m["n_pares"]),
                    number(m["mae_margem_pp"], 2),
                    number(m["rmse_margem_pp"], 2),
                    number(m["vies_margem_pp"], 2),
                    number(m["mae_parcelas_pp"], 2),
                ]
                for m in acceleration["metricas"].values()
            ],
            "Inclinação constante contra inclinação que muda",
        )
        if acceleration
        else ""
    )
    return (
        f"<p>{esc(v['natureza'])}</p>"
        + table(headers, rows("origem_movel"), "Origem móvel, todas as casas")
        + by_horizon
        + accel
        + table(headers, rows("deixa_uma_casa_fora"), "Deixando a casa do alvo fora")
        + table(
            headers,
            rows("com_casa_do_alvo"),
            "Prevendo a próxima onda de uma casa conhecida",
        )
    )


def minor_table(data):
    b = data["central"]["brasil"]
    return table(
        ["Candidatura", "Votos modelados", "% dos válidos"],
        [
            [NAMES[k], millions(v), number(100 * v / b["validos"], 2) + "%"]
            for k, v in b["demais"].items()
        ],
        "Abertura modelada das demais candidaturas",
    )


def histogram(data):
    mc = data["incerteza"]
    counts, limits = mc["distribuicao_margem"], mc["limites_histograma"]
    lo, hi, peak = limits[0], limits[-1], max(counts)
    parts = [
        '<svg viewBox="0 0 800 255" role="img" aria-label="Distribuição simulada da diferença Flávio menos Lula, no cenário central" xmlns="http://www.w3.org/2000/svg">'
    ]
    for i, c in enumerate(counts):
        x, h = 45 + 700 * i / len(counts), 170 * c / peak
        color = (
            COLORS["flavio"] if (limits[i] + limits[i + 1]) / 2 > 0 else COLORS["lula"]
        )
        parts.append(
            f'<rect x="{x:.2f}" y="{200-h:.2f}" width="{700/len(counts)-2:.2f}" height="{h:.2f}" fill="{color}"/>'
        )
    zero = 45 + 700 * (0 - lo) / (hi - lo)
    parts.append(
        f'<line x1="{zero:.2f}" x2="{zero:.2f}" y1="10" y2="211" stroke="#192e2b" stroke-dasharray="4 3"/><text x="{zero:.2f}" y="230" font-size="14" text-anchor="middle" fill="#192e2b">Empate</text>'
    )
    parts.append(
        '<text x="45" y="252" font-size="14" fill="#535b54">Lula à frente</text><text x="745" y="252" font-size="14" text-anchor="end" fill="#535b54">Flávio à frente</text></svg>'
    )
    return "".join(parts)


def simulator(data):
    from .simulador import render as render_simulator

    return render_simulator(data, region_table(data))


def render(data, template):
    from .texto import values

    replacements = {
        "HERO": hero(data),
        "ACCOUNTING": accounting(data),
        "REGION_CHART": region_chart(data),
        "REGION_TABLE": region_table(data),
        "STATE_TABLE": state_table(data),
        "MAP": map_svg(data),
        "SENSITIVITY": sensitivity(data),
        "HOUSE_TABLE": house_table(data),
        "ERRO_2022_TABLE": erro_2022_table(data),
        "ERRO_2022_VS_2026": erro_2022_vs_2026(data),
        "POLL_TABLE": poll_table(data),
        "STATE_DETAILS": state_details(data),
        "SOURCE_UPDATES": source_updates(data),
        "TURNOUT_CHECKS": turnout_checks(data),
        "ABSTENTION": abstention(data),
        "VALIDATION": validation(data),
        "DLM_TABLE": dlm_table(data),
        "PREDICTIVE_TABLE": predictive_table(data),
        "MINOR_TABLE": minor_table(data),
        "HISTOGRAM": histogram(data),
        "SIMULATOR": simulator(data),
        "DATE": data["referencia"],
        "N_STATES": str(sum(len(s["pesquisas"]) for s in data["estados"])),
        "N_HOUSES": str(len(data["nacional"]["pareadas"])),
        "N_ALL": str(len(data["nacional"]["selecionadas"])),
        "N_NEW_STATES": str(data["qualidade"]["n_estaduais_novas_integradas"]),
        "N_TURNOUT": str(data["qualidade"]["n_ufs_cruzamento_comparecimento"]),
        "HALF_NATIONAL": number(data["configuracao"]["meia_vida_nacional_dias"], 1),
        "HALF_STATE": number(data["configuracao"]["meia_vida_estadual_dias"], 1),
        "MATCH": number(data["qualidade"]["pareamento_eleitores_pct"]),
        "RMSE_SECTION": number(data["validacao"]["metricas"]["rmse_ufs_secoes_pp"], 2),
        "RMSE_UF": number(data["validacao"]["metricas"]["rmse_ufs_constante_pp"], 2),
        "SECTIONS": number(data["qualidade"]["secoes_2022"], 0),
        "PROFILE_DIFF": number(
            data["qualidade"]["diferenca_locais_perfil_eleitores"], 0
        ),
        "LOCALS_DATE": esc(data["tse_metadata"]["locais_metadata"]["DT_GERACAO"]),
        "PROFILE_DATE": esc(data["tse_metadata"]["perfil_metadata"]["DT_GERACAO"]),
        "P_FLAVIO_AHEAD": number(
            100 * data["incerteza"]["p_flavio_a_frente_de_lula"], 1
        ),
        "P_LULA_MAJORITY": number(100 * data["incerteza"]["p_lula_maioria"], 1),
        "P_FLAVIO_MAJORITY": number(100 * data["incerteza"]["p_flavio_maioria"], 1),
        "GAP_LOW": number(data["incerteza"]["margem"]["p05"], 2),
        "GAP_HIGH": number(data["incerteza"]["margem"]["p95"], 2),
        "MODEL_HASH": data["hash_modelo"],
        "DATA": json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
            "<", "\\u003c"
        ),
    }
    replacements.update(values(data))
    for key, value in replacements.items():
        template = template.replace("{{" + key + "}}", value)
    if "{{" in template or "—" in template:
        raise ValueError("Template incompleto ou travessão no texto público")
    return template
