"""Legenda e cobertura das duas séries de não escolha."""

import csv
from html import escape

COLORS = {"indecisos": "#8350a0", "branco_nulo": "#28705f"}
LABELS = {"indecisos": "Indecisos", "branco_nulo": "Branco/nulo/não vai votar"}


def summary(data, turn, table, number):
    group = data["agregador"]["nao_escolha"][turn]
    waves = group["ondas"]
    institutes = {p["instituto"] for p in waves}

    def fmt(value):
        return "Sem dado" if value is None else number(value, 2) + "%"

    rows = [
        [
            escape(label),
            fmt(group["ultimo"]["publicado"][key]),
            fmt(group["ultimo"]["ajustado"][key]),
        ]
        for key, label in LABELS.items()
    ]
    coverage = [
        [
            escape(p["instituto"]),
            escape(p["id"]),
            "/".join(reversed(p["campo"]["fim"].split("-"))),
        ]
        for p in waves
    ]
    excluded = [[escape(p["id"]), escape(p["motivo"])] for p in group["excluidas"]]
    return (
        f'<div id="nao-escolha-{turn}"><h3>Indecisos e branco/nulo/não vai votar</h3>'
        + table(["Resposta", "Média móvel publicada", "Média móvel reponderada"], rows)
        + f'<p class="note"><b>Cobertura: {len(waves)} ondas de {len(institutes)} institutos.</b> '
        + escape(group["regra"])
        + "</p><details><summary>Conferir ondas e exclusões destas duas linhas</summary>"
        + table(["Instituto", "Onda utilizada", "Fim do campo"], coverage)
        + table(["Onda excluída", "Motivo"], excluded)
        + '<p><a href="assets/reponderacao_nao_escolha.csv">Baixar valores por onda (CSV)</a></p>'
        + "</details></div>"
    )


def write_csv(path, data):
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "turno",
            "id",
            "instituto",
            "campo_fim",
            "categoria",
            "componentes",
            "publicado",
            "reponderado",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for turn, group in data["agregador"]["nao_escolha"].items():
            for row in group["ondas"]:
                for key in LABELS:
                    writer.writerow(
                        {
                            "turno": turn,
                            "id": row["id"],
                            "instituto": row["instituto"],
                            "campo_fim": row["campo"]["fim"],
                            "categoria": key,
                            "componentes": ";".join(row["componentes"][key]),
                            "publicado": row["publicado"][key],
                            "reponderado": row["ajustado"][key],
                        }
                    )
