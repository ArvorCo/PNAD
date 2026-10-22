"""Histórico documental F × L; não participa de médias ou projeções."""

import csv
import importlib
import json
from copy import deepcopy
from html import escape as esc

from reponderacao_vista.context import ROOT, D, ajustado, curto, periodo
from svgkit import br

SUPPLEMENT = ROOT / "analysis/reponderacao/historico_2t/complementos.json"
CUTOFF = "2026-10-04"


def phase(poll):
    if poll["campo"]["fim"] <= CUTOFF:
        return "Simulação antes do 1º turno"
    if poll["campo"]["inicio"] > CUTOFF:
        return "Após o 1º turno"
    return "Campo atravessa o 1º turno"


def history(data=None, supplements=None, palver=None):
    """Une publicados com/sem renda, preservando versões e denominadores."""
    data = D if data is None else data
    supplements = (
        json.loads(SUPPLEMENT.read_text())["pesquisas"]
        if supplements is None
        else supplements
    )
    polls = {
        p["id"]: deepcopy(p)
        for p in data["pesquisas"] + data.get("nao_reponderaveis", [])
    }
    if palver is None:
        palver = importlib.import_module("reponderacao-palver-view").history_polls(data)
    polls.update({p["id"]: deepcopy(p) for p in palver})
    for extra in supplements:
        poll = polls.setdefault(extra["id"], deepcopy(extra))
        # Complementos só preenchem lacunas. Um publicado novo do motor prevalece.
        if not poll.get("publicado", {}).get("2t"):
            poll.setdefault("publicado", {})["2t"] = extra["publicado"]["2t"]
            poll["fonte_historico"] = extra["fonte"]
            poll["nota_historico"] = extra.get("nota", "")
    result = []
    for poll in polls.values():
        if not poll.get("divulgacao") or poll["divulgacao"] > data["referencia"]:
            continue
        turn = poll.get("turnos", {}).get("2t")
        published = turn["publicado"] if turn else poll.get("publicado", {}).get("2t")
        denominator = "total"
        if not published:
            published = (poll.get("publicado_validos") or {}).get("2t")
            denominator = "validos"
        if not published or not all(c in published for c in ("flavio", "lula")):
            continue
        result.append(
            {
                **poll,
                "placar": published,
                "pnad": ajustado(turn) if turn and denominator == "total" else None,
                "denominador": denominator,
                "fase": phase(poll),
                "fonte_historico": poll.get("fonte_historico", poll.get("fonte", {})),
            }
        )
    return sorted(result, key=lambda p: (p["campo"]["fim"], p["instituto"], p["id"]))


def wave_count(rows):
    return len(
        {(p["instituto"], p["campo"]["inicio"], p["campo"]["fim"]) for p in rows}
    )


def score(values):
    if values is None:
        return "não disponível"
    return f"{br(values['flavio'], 2)} × {br(values['lula'], 2)}"


def source(poll):
    ref = poll["fonte_historico"]
    url = ref.get("url_publica") or ref.get("url")
    pages = ref.get("paginas", {})
    page = pages.get("2t") or pages.get("2t_topline")
    label = f"Fonte, p. {page}" if page else "Fonte"
    if url:
        return f'<a href="{esc(url, quote=True)}">{label}</a>'
    return "Documento no acervo" + (f", p. {page}" if page else "")


def tip(poll):
    from reponderacao_vista.historico_controles import delta, method

    base = (
        "votos válidos"
        if poll["denominador"] == "validos"
        else "total de entrevistados"
    )
    version = poll.get("rotulo_historico", "")
    pub_label = "Projeção do publicado" if poll.get("modo_projecao") else "Publicado"
    return (
        f'<p class="tip-head"><b>{esc(poll["instituto"])}</b></p>'
        f'<p class="tip-doc">Campo: {periodo(poll["campo"])}. '
        f'Divulgação: {curto(poll["divulgacao"])}. {esc(version)}</p>'
        f'<p class="tip-nota">{poll["fase"]}. Percentuais sobre {base}.</p>'
        '<table class="tip-tab"><caption>Flávio × Lula (%)</caption><tbody>'
        f'<tr><th>{pub_label}</th><td>{score(poll["placar"])}</td></tr>'
        f'<tr><th>PNAD</th><td>{score(poll["pnad"])}</td></tr>'
        f"<tr><th>Δ PNAD − publicado</th><td>{delta(poll)}</td></tr></tbody></table>"
        + (method(poll) if poll.get("modo_projecao") else "")
        + f'<p class="tip-nota">{source(poll)}. '
        f'{esc(poll.get("nota_historico", poll.get("nota", "")))}</p>'
        + (
            '<p class="tip-nota">Versão substituída, fora das médias.</p>'
            if poll.get("substituida")
            else ""
        )
    )


def table(rows):
    from reponderacao_vista.historico_controles import delta, method

    projected = bool(rows and rows[0].get("modo_projecao"))
    pub_label = "Projeção do publicado" if projected else "Publicado"
    body = []
    for poll in rows:
        base = (
            "Válidos projetados"
            if projected
            else ("Válidos" if poll["denominador"] == "validos" else "Total")
        )
        note = " · versão substituída" if poll.get("substituida") else ""
        if poll.get("renda", {}).get("perfil_tipo") == "hipotese_onda_anterior":
            note += " · PRÉVIA PNAD com perfil da onda anterior"
        version = poll.get("rotulo_historico", "")
        body.append(
            f'<tr data-history-id="{esc(poll["id"])}"><th scope="row">'
            f'{curto(poll["campo"]["inicio"])}–{curto(poll["campo"]["fim"])}'
            f"<br><small>{esc(version)}</small></th>"
            f'<td>{curto(poll["divulgacao"])}</td><td>{base}</td>'
            f'<td>{score(poll["placar"])}</td><td>{score(poll["pnad"])}</td>'
            f'<td>{delta(poll)}</td><td>{poll["fase"]}{note}. {source(poll)}'
            + (method(poll) if poll.get("modo_projecao") else "")
            + "</td></tr>"
        )
    return (
        '<details class="history-table"><summary>Todas as ondas, valores e fontes</summary>'
        '<div class="table-scroll" tabindex="0" role="region" aria-label="Histórico por onda"><table><caption>Flávio × Lula, em %. '
        "Datas de 2026. PNAD ausente significa ajuste não disponível.</caption>"
        "<thead><tr><th>Campo</th><th>Divulgação</th><th>Base</th>"
        f"<th>{pub_label}</th><th>PNAD</th><th>Δ PNAD − publicado</th><th>Contexto e fonte</th></tr></thead>"
        f'<tbody>{"".join(body)}</tbody></table></div></details>'
    )


def panel(name, rows):
    from reponderacao_vista.historico_painel import panel as render

    return render(name, rows)


def section():
    from reponderacao_vista.avaliacao_1t import order_key
    from reponderacao_vista.historico_controles import controls
    from reponderacao_vista.score_view import section as score_section

    rows = history()
    names = sorted({p["instituto"] for p in rows}, key=order_key)
    panels = "".join(
        panel(name, [p for p in rows if p["instituto"] == name]) for name in names
    )
    return (
        '<div id="institutos-2t" class="instituto-group"><header>'
        f'<p class="kicker">{len(names)} institutos · {wave_count(rows)} ondas · {len(rows)} versões</p>'
        "<h3>Flávio × Lula · o histórico completo do acervo</h3>"
        '<p class="note">Inclui simulações anteriores ao primeiro turno, mesmo sem cruzamento de renda. '
        "Pontos vazados e linhas tracejadas: publicado; pontos cheios e linhas contínuas: PNAD. "
        "Azul: Flávio; vermelho: Lula. Datas no eixo são o fim do campo, com espaçamento em dias. "
        "A marca de 04/10 separa as simulações da disputa após o primeiro turno; as linhas param nessa passagem pelo fim do campo. Campos que atravessam a eleição mantêm aviso na ficha. "
        "Lacunas de PNAD não são preenchidas. Percentuais sobre o total; válidos exclusivos ficam separados.</p>"
        '<p class="note">Este histórico não acrescenta ondas antigas às centrais atuais. Mudanças de método '
        "podem afetar a comparação. Cobertura do acervo verificado, não garantia de todas as pesquisas publicadas. "
        '<a href="assets/reponderacao_historico_2t.csv">Baixar histórico (CSV)</a> · '
        '<a href="assets/reponderacao_historico_2t.json">Dados e fontes (JSON)</a>.</p>'
        f'</header>{score_section(names)}{controls(rows)}<div class="grid-3 history-grid">{panels}</div></div>'
    )


def write_assets():
    from reponderacao_vista.historico_projecao import evidence, project

    rows = history()
    assets = ROOT / "docs/assets"
    export_keys = (
        "id",
        "instituto",
        "campo",
        "divulgacao",
        "registro_tse",
        "n",
        "fase",
        "denominador",
        "placar",
        "publicado_validos",
        "pnad",
        "renda",
        "fonte_historico",
        "substituida",
        "rotulo_historico",
        "nota_historico",
        "nota",
    )
    exported = [
        {**{key: p[key] for key in export_keys if key in p}, "projecao": project(p)}
        for p in rows
    ]
    (assets / "reponderacao_historico_presenca.json").write_text(
        json.dumps(evidence(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (assets / "reponderacao_historico_2t.json").write_text(
        '{\n"referencia": '
        + json.dumps(D["referencia"])
        + ',\n"uso": "histórico, sem efeito nas centrais",\n"pesquisas": [\n'
        + ",\n".join(json.dumps(p, ensure_ascii=False) for p in exported)
        + "\n]}\n",
        encoding="utf-8",
    )
    fields = [
        "id",
        "instituto",
        "campo_inicio",
        "campo_fim",
        "divulgacao",
        "fase",
        "denominador",
        "flavio_publicado",
        "lula_publicado",
        "flavio_pnad",
        "lula_pnad",
        "projecao_tipo",
        "flavio_projecao",
        "lula_projecao",
        "flavio_pnad_projecao",
        "lula_pnad_projecao",
        "delta_flavio_pp",
        "delta_lula_pp",
        "substituida",
        "fonte",
    ]
    with (assets / "reponderacao_historico_2t.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for p in rows:
            projection = project(p)
            writer.writerow(
                {
                    **{
                        key: p[key]
                        for key in (
                            "id",
                            "instituto",
                            "divulgacao",
                            "fase",
                            "denominador",
                        )
                    },
                    "campo_inicio": p["campo"]["inicio"],
                    "campo_fim": p["campo"]["fim"],
                    **{f"{c}_publicado": p["placar"][c] for c in ("flavio", "lula")},
                    **{
                        f"{c}_pnad": p["pnad"][c] if p["pnad"] else ""
                        for c in ("flavio", "lula")
                    },
                    "projecao_tipo": projection["evidencia"]["tipo"],
                    **{
                        f"{c}_projecao": projection["modos"]["placar"]["validos"][c]
                        for c in ("flavio", "lula")
                    },
                    **{
                        f"{c}_pnad_projecao": (
                            projection["modos"]["pnad"]["validos"][c]
                            if projection["modos"]["pnad"]
                            else ""
                        )
                        for c in ("flavio", "lula")
                    },
                    **{
                        f"delta_{c}_pp": (
                            p["pnad"][c] - p["placar"][c] if p["pnad"] else ""
                        )
                        for c in ("flavio", "lula")
                    },
                    "substituida": bool(p.get("substituida")),
                    "fonte": p["fonte_historico"].get("url")
                    or p["fonte_historico"].get("pdf", ""),
                }
            )
