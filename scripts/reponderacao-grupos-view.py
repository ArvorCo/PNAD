"""Rótulos e quadro de cobertura das linhas editoriais do primeiro turno."""

import csv
from html import escape

GROUP_COLORS = {
    "outros_centro_direita": "#626262",
    "outros_esquerda_nanicos": "#000000",
}
GROUP_LABELS = {
    "outros_centro_direita": "Outros (centro-direita)",
    "outros_esquerda_nanicos": "Outros (esquerda + nanicos)",
}


def end_labels(cv, pub, adj, right, top, bottom, py, colors, number):
    """Quatro rótulos com espaçamento mínimo, sem colisão nas duas caudas."""
    keys = ("lula", "flavio", *GROUP_LABELS)
    blocks = sorted((py(adj[k][-1]), k) for k in keys if adj[k][-1] is not None)
    height, gap = 84, 10
    positions = []
    for center, key in blocks:
        y = max(top, center - height / 2)
        if positions:
            y = max(y, positions[-1][0] + height + gap)
        positions.append([y, center, key])
    for i in range(len(positions) - 1, -1, -1):
        ceiling = (
            bottom - height
            if i == len(positions) - 1
            else positions[i + 1][0] - height - gap
        )
        positions[i][0] = min(positions[i][0], ceiling)
    for y, center, key in positions:
        x = right + 18
        color = colors[key]
        cv.line(right, center, x - 7, y + height / 2, stroke=color, width=1.2)
        title = {"lula": "LULA", "flavio": "FLÁVIO"}.get(key, "OUTROS")
        subtitle = {
            "outros_centro_direita": "(centro-direita)",
            "outros_esquerda_nanicos": "(esquerda + nanicos)",
        }.get(key, "")
        cv.text(x, y + 13, title, size=12, fill=color, weight=700)
        if subtitle:
            cv.text(x, y + 29, subtitle, size=12, fill=color, weight=600)
        cv.number(x, y + 58, number(adj[key][-1], 1) + "%", size=29, fill=color)
        cv.text(
            x,
            y + 77,
            "publicado " + number(pub[key][-1], 1) + "%",
            size=12,
            fill="#535b54",
        )


def group_summary(data, table, number):
    groups = data["agregador"]["grupos_1t"]
    current = groups["ultimo"]
    def fmt(value):
        return "Sem dado" if value is None else number(value, 2) + "%"
    rows = [
        [
            escape(label),
            fmt(current["kernel"]["publicado"][key]),
            fmt(current["kernel"]["ajustado"][key]),
            fmt(current["media_simples"]["ajustado"][key]),
        ]
        for key, label in GROUP_LABELS.items()
    ]
    eligible = groups["ondas"]
    institutes = sorted({p["instituto"] for p in eligible})
    last_field = max((p["campo"]["fim"] for p in eligible), default=None)
    last_date = "/".join(reversed(last_field.split("-"))) if last_field else "sem dado"
    coverage = [
        [escape(name), escape(ident)]
        for name, ident in groups["ultima_onda_por_instituto"].items()
    ]
    excluded = [[escape(p["id"]), escape(p["motivo"])] for p in groups["excluidas"]]
    return (
        '<div id="grupos-primeiro-turno"><h3>Os outros candidatos, em dois grupos</h3>'
        + table(
            [
                "Grupo",
                "Média Arvor publicada",
                "Média Arvor reponderada",
                "Média simples reponderada",
            ],
            rows,
        )
        + f'<p class="note">{escape(groups["regra"])}</p>'
        + f'<p class="note"><b>Cobertura: {len(eligible)} ondas de {len(institutes)} institutos; último campo em {last_date}.</b> '
        + escape(groups["cobertura"])
        + " Mesma meia-vida de 14 dias, mesma régua PNAD e mesmos pesos entre publicado e reponderado. "
        "A média simples usa a última onda elegível de cada instituto, que pode ser anterior à sua última publicação.</p>"
        "<details><summary>Conferir ondas utilizadas e exclusões</summary>"
        + table(["Instituto", "Última onda elegível"], coverage)
        + table(["Onda excluída dos grupos", "Motivo"], excluded)
        + '<p><a href="assets/reponderacao_grupos_1t.csv">Baixar as somas por onda (CSV)</a></p>'
        "</details></div>"
    )


def selection_note(poll):
    selection = poll.get("selecao_1t")
    if not selection:
        return ""
    label = (
        "1º turno excluído: cenário com Marçal."
        if selection["status"] == "excluido_com_marcal"
        else "1º turno selecionado: sem Marçal."
    )
    return f'<p class="note"><b>{label}</b> {escape(selection["nota"])}</p>'


def scenario_summary(data, table):
    polls = [p for p in data["pesquisas"] if p.get("selecao_1t")]
    rows = [
        [
            escape(p["id"]),
            (
                "Excluído do 1º turno"
                if p["selecao_1t"]["status"] == "excluido_com_marcal"
                else "Cenário sem Marçal"
            ),
            escape(p["selecao_1t"]["nota"]),
        ]
        for p in polls
    ]
    return (
        '<div id="selecao-primeiro-turno"><p class="note"><b>Seleção de cenários:</b> '
        "o primeiro turno usa apenas cenários sem Marçal. Quando o relatório oferece uma alternativa "
        "com cruzamento de renda, usamos essa tabela e seu próprio placar. Sem alternativa documentada, "
        "o cenário fica fora das médias e dos gráficos de 1º turno; o 2º turno é preservado. "
        "Não redistribuímos os votos de Marçal. Os manifestos originais permanecem arquivados.</p>"
        "<details><summary>Conferir a seleção de cenários por onda</summary>"
        + table(["Onda", "Seleção", "Documento e critério"], rows)
        + "</details></div>"
    )


def write_group_csv(path, data):
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "id",
            "instituto",
            "campo_fim",
            "grupo",
            "componentes",
            "publicado",
            "reponderado",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in data["agregador"]["grupos_1t"]["ondas"]:
            for group in GROUP_LABELS:
                writer.writerow(
                    {
                        "id": row["id"],
                        "instituto": row["instituto"],
                        "campo_fim": row["campo"]["fim"],
                        "grupo": group,
                        "componentes": ";".join(row["componentes"][group]),
                        "publicado": row["publicado"][group],
                        "reponderado": row["ajustado"][group],
                    }
                )
