"""Cobertura diária das médias de sete dias, visível e exportável."""

import csv
from html import escape


def cohorts(data, turn):
    agg = data["agregador"]
    result = {
        "Candidatos": agg["cobertura_movel"][turn],
        "Indecisos e branco/nulo": agg["nao_escolha"][turn]["cobertura_movel"],
    }
    if turn == "1t":
        result["Outros candidatos"] = agg["grupos_1t"]["cobertura_movel"]
    return result


def summary(data, turn, table):
    groups = cohorts(data, turn)
    latest = [
        [
            name,
            str(rows[-1]["n_institutos"]),
            escape(", ".join(rows[-1]["institutos"])) or "Sem pesquisa na janela",
        ]
        for name, rows in groups.items()
    ]
    daily = [
        [
            "/".join(reversed(rows["data"].split("-"))),
            name,
            str(rows["n_institutos"]),
            escape(", ".join(rows["institutos"])) or "Sem média",
        ]
        for name, series in groups.items()
        for rows in reversed(series)
    ]
    return (
        f'<div id="janela-{turn}"><p class="note"><b>Média móvel de 7 dias: dia observado e seis dias anteriores.</b> '
        "A entrada ocorre pela divulgação, nunca antes. Cada instituto tem peso igual e contribui "
        "com sua última onda elegível na janela. Sem pesquisa, deixamos uma lacuna. Entradas e saídas "
        "de institutos também movem a média; uma semana com poucas casas exige mais cautela.</p>"
        + table(["Linhas", "Institutos na janela atual", "Cobertura atual"], latest)
        + "<details><summary>Conferir a cobertura de cada data</summary>"
        + table(["Data", "Linhas", "Institutos", "Casas participantes"], daily)
        + '<p><a href="assets/reponderacao_medias_7d.csv">Baixar médias diárias e ondas utilizadas (CSV)</a></p>'
        + "</details></div>"
    )


def write_csv(path, data):
    agg = data["agregador"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "data",
            "turno",
            "serie",
            "publicado",
            "reponderado",
            "n_institutos",
            "ondas",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for turn in ("1t", "2t"):
            for key, published in agg["serie"][turn]["publicado"].items():
                if key in ("lula", "flavio"):
                    coverage = agg["cobertura_movel"][turn]
                elif key in ("indecisos", "branco_nulo"):
                    coverage = agg["nao_escolha"][turn]["cobertura_movel"]
                else:
                    coverage = agg["grupos_1t"]["cobertura_movel"]
                for i, day in enumerate(agg["serie"]["datas"]):
                    writer.writerow(
                        {
                            "data": day,
                            "turno": turn,
                            "serie": key,
                            "publicado": published[i],
                            "reponderado": agg["serie"][turn]["ajustado"][key][i],
                            "n_institutos": coverage[i]["n_institutos"],
                            "ondas": ";".join(coverage[i]["ondas"]),
                        }
                    )
