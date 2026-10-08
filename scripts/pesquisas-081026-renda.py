#!/usr/bin/env python3
"""Integra os arquivos conferidos de 05–08/10/2026, sem consultar fontes dinâmicas."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLLS = ROOT / "analysis/reponderacao/pesquisas"
DAY = "2026-10-08"
OPTIONS = ["lula", "flavio", "branco_nulo", "indecisos"]
NAMES = dict(
    zip(
        ["Lula", "Flavio Bolsonaro", "Em Branco/Nulo/Nenhum", "Indecisos"],
        OPTIONS,
        strict=True,
    )
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def archive(folder):
    data = read(ROOT / "data/originals" / folder / "fonte.json")
    for item in data["arquivos"]:
        payload = (ROOT / item["arquivo"]).read_bytes()
        if (
            len(payload) != item["bytes"]
            or hashlib.sha256(payload).hexdigest() != item["sha256"]
        ):
            raise ValueError(f"Fonte arquivada mudou: {item['arquivo']}")
    return data["arquivos"]


def source(items, filename):
    return next(item for item in items if item["arquivo"].endswith("/" + filename))


def control(published, rows, weights):
    recomposed = {
        key: round(
            sum(r[i] * w for r, w in zip(rows, weights, strict=True)) / sum(weights), 3
        )
        for i, key in enumerate(OPTIONS)
    }
    residual = {k: round(recomposed[k] - published[k], 3) for k in OPTIONS}
    maximum = max(abs(v) for v in residual.values())
    if maximum > 1.5:
        raise ValueError(f"Recomposição incompatível: {residual}")
    return {"recomposto": recomposed, "residuo": residual, "residuo_max_abs": maximum}


def bands():
    return [
        {"rotulo": "Até 2 SM (até R$ 3.242)", "max": 2},
        {"rotulo": "De 2 a 5 SM (R$ 3.242 a 8.105)", "max": 5},
        {"rotulo": "Mais de 5 SM (acima de R$ 8.105)", "max": None},
    ]


def panel_row(data):
    # O painel pós-1º turno tem barras, não a série values do antigo paginaId=100.
    if {x["date"][:10] for x in data} != {DAY}:
        raise ValueError(
            "Painel de outra onda: não reutilizar o painel do primeiro turno"
        )
    result = {}
    for value in data:
        pct = 100 * value["value"]
        if abs(pct - round(pct)) > 1e-8:
            raise ValueError("Percentual não inteiro no painel")
        result[NAMES[value["option"]]] = round(pct)
    return result


def datafolha(items):
    item = source(items, "g1_ESTIMULADA-PRE-001.json")
    result = read(ROOT / item["arquivo"])["resultado"]
    published = panel_row(result["cenarios"][0]["data"])
    strata = {
        e["identificador"].removesuffix("-ESTIMULADA-PRE-001"): panel_row(e["data"])
        for e in result["estratos"]
    }
    income = [
        strata[k]
        for k in [
            "renda-ate-2-sm-2",
            "renda-mais-de-2-a-5-sm-2",
            "renda-mais-de-5-sm-2",
        ]
    ]
    rows = [[r[k] for k in OPTIONS] for r in income]
    previous = read(POLLS / "datafolha_2026-10-01.json")
    weights = previous["renda"]["bases"]
    sex = [[strata[s][k] for k in OPTIONS] for s in ["sexo-masculino", "sexo-feminino"]]
    previous_sex = read(
        ROOT / "analysis/reponderacao/datafolha_20261001_cruzamentos.json"
    )
    base = previous_sex["tabelas"]["estimulada"]["blocks"]["bloco1"]["base"]
    controls = {
        "renda": control(published, rows, weights),
        "sexo": control(published, sex, [base["Masculino"], base["Feminino"]]),
    }
    valid_item = source(items, "g1_VTSVALIDOS-PRE-001.json")
    valid = panel_row(
        read(ROOT / valid_item["arquivo"])["resultado"]["cenarios"][0]["data"]
    )
    note = (
        "Fonte parcial: o G1 publica os votos por renda desta onda, mas não as bases de renda. "
        "A reponderação assume explicitamente o perfil ponderado da onda de 01/10 "
        "(1.209/856/344, PDF de 02/10, pp. 45 e 53), condicionado à confirmação da íntegra atual. "
        "O controle por sexo também assume as bases anteriores (1.215/1.291). "
        "Os controles de recomposição não comprovam que o perfil se manteve. "
        "O registro PesqEle devolveu HTTP 403 nesta consulta. "
        "Há divergência de datas: o texto metodológico do painel diz 6–7/10; "
        "a notícia de divulgação e a agenda do registro informam 6–8/10, período usado nesta ficha."
    )
    return {
        "id": "datafolha_2026-10-08",
        "instituto": "Datafolha",
        "contratante": "Folha de S.Paulo e TV Globo",
        "registro_tse": "BR-02949/2026",
        "n": 2520,
        "campo": {"inicio": "2026-10-06", "fim": "2026-10-08"},
        "divulgacao": DAY,
        "metodo": "presencial, pontos de fluxo",
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "mes_precos": "202610",
            "faixas": bands(),
            "bases": weights,
            "perfil_tipo": "hipotese_onda_anterior",
            "nota": note,
        },
        "publicado": {"2t": published},
        "publicado_validos": {"2t": valid},
        "cruzamentos": {
            "2t": {
                "opcoes": OPTIONS,
                "linhas": rows,
                "nota": "API pública do painel pós-1º turno: paginaId=216, ESTIMULADA-PRE-001, divulgação 08/10. Usam-se votos totais por renda; os válidos arredondados ficam preservados à parte.",
            }
        },
        "controles": {"2t": controls},
        "fonte": {
            **item,
            "tipo": "painel_contratante",
            "rotulo": "Painel do G1: votos por renda",
            "url": source(items, "painel.html")["url"],
            "paginas": {"2t_renda": "API 216, ESTIMULADA-PRE-001, estratos renda"},
            "conferido_em": DAY,
            "status": "Painel atual arquivado; íntegra em PDF pendente.",
            "nota": note,
            "complementos": [
                {**valid_item, "rotulo": "API: votos válidos publicados"},
                {
                    **source(items, "materia_exame.html"),
                    "rotulo": "Divulgação e ficha técnica",
                },
            ],
        },
        "notas": note,
    }


def poderdata(items):
    item = source(items, "relatorio.pdf")
    published = dict(zip(OPTIONS, [44, 49, 5, 2], strict=True))
    rows = [[48, 42, 7, 3], [39, 57, 3, 2], [43, 55, 2, 1]]
    controls = {
        "renda": control(published, rows, [46, 33, 21]),
        "sexo": control(published, [[37, 57, 4, 2], [50, 42, 6, 2]], [47, 53]),
    }
    return {
        "id": "poderdata_2026-10-07",
        "instituto": "PoderData",
        "contratante": "Poder360",
        "registro_tse": "BR-08134/2026",
        "n": 3000,
        "campo": {"inicio": "2026-10-05", "fim": "2026-10-07"},
        "divulgacao": DAY,
        "metodo": "telefônico (IVR/URA, discagem aleatória para celular e fixo)",
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "mes_precos": "202610",
            "faixas": bands(),
            "amostra_pct": [46, 33, 21],
            "perfil_tipo": "perfil_publicado",
            "nota": "Perfil desta onda na p. 4: 46/33/21. A primeira faixa inclui pessoas sem rendimentos. Cruzamentos sobre votos totais na p. 9, inclusive branco/nulo e não sabe.",
        },
        "publicado": {"2t": published},
        "publicado_validos": {"2t": {"lula": 47, "flavio": 53}},
        "cruzamentos": {
            "2t": {
                "opcoes": OPTIONS,
                "linhas": rows,
                "nota": "P. 9, votos totais por renda. P. 7 fornece controle independente por sexo. Conferência visual das pp. 4, 7 e 9 contra a camada de texto.",
            }
        },
        "controles": {"2t": controls},
        "fonte": {
            **item,
            "pdf": item["arquivo"],
            "tipo": "relatorio",
            "rotulo": "PoderData: relatório completo",
            "paginas": {
                "metodologia": 2,
                "perfil_renda": 4,
                "2t_topline": 6,
                "sexo": 7,
                "2t_renda": 9,
            },
            "total_paginas": 39,
            "conferido_em": DAY,
            "status": "Íntegra atual arquivada e conferida.",
            "nota": "Primeira onda PoderData com campo inteiramente após o 1º turno. Entram votos totais 44 × 49, não os válidos arredondados 47 × 53. A média móvel de sete dias ainda inclui outras casas com campo anterior à eleição; não é uma média exclusiva do pós-1º turno.",
            "complementos": [
                {
                    **source(items, "materia.html"),
                    "rotulo": "Divulgação oficial no Poder360",
                }
            ],
        },
    }


def verita(items):
    note = (
        "Divulgada na noite de 05/10 e repercutida em 06/10, com 48,44% Lula × 51,56% Flávio "
        "somente em votos válidos. Campo de 26/09 a 02/10, anterior ao 1º turno, conforme as matérias. "
        "Não foi localizado relatório nacional desta rodada com perfil ponderado e voto por renda "
        "para o 2º turno. O catálogo oficial consultado em 08/10 traz relatórios estaduais novos, "
        "mas o nacional mais recente tem campo de 20–25/09 e não documenta esta divulgação. "
        "Não se transportam cruzamentos ou pesos antigos nem se convertem válidos em votos totais."
    )
    return {
        "id": "verita_2026-10-02",
        "instituto": "Veritá",
        "contratante": "Instituto Veritá",
        "registro_tse": "Registros estaduais; número nacional único não confirmado",
        "n": 40500,
        "campo": {"inicio": "2026-09-26", "fim": "2026-10-02"},
        "divulgacao": "2026-10-05",
        "publicado": {},
        "publicado_validos": {"2t": {"lula": 48.44, "flavio": 51.56}},
        "cruzamentos": {},
        "ignorar": True,
        "motivo": note,
        "fonte": {
            **source(items, "materia.html"),
            "tipo": "materia",
            "rotulo": "Veritá: divulgação repercutida",
            "conferido_em": DAY,
            "nota": "Votos válidos, com campo anterior à eleição; sem ajuste disponível.",
            "complementos": [
                {
                    **source(items, "materia_folha_patrocinio.html"),
                    "rotulo": "Conferência do período de campo",
                },
                {
                    **source(items, "catalogo.json"),
                    "rotulo": "Catálogo oficial de relatórios",
                },
            ],
        },
    }


def main():
    folders = ["datafolha_102026_08", "poderdata_102026_08", "verita_102026_05"]
    sources = {folder: archive(folder) for folder in folders}
    polls = [
        datafolha(sources[folders[0]]),
        poderdata(sources[folders[1]]),
        verita(sources[folders[2]]),
    ]
    for poll in polls:
        write(POLLS / (poll["id"] + ".json"), poll)
        print(poll["id"], poll.get("controles", "sem ajuste"))
    audit = {
        "data": DAY,
        "intervalo_divulgacao": {"inicio": "2026-10-05", "fim": DAY},
        "fontes": [item for items in sources.values() for item in items],
        "controles": {p["id"]: p.get("controles", {}) for p in polls},
        "regra": "Votos totais com troca somente da renda, ancorados no publicado. Datafolha com hipótese explícita de perfil; Veritá somente válidos, excluído das médias. Campo e divulgação são datas distintas.",
        "varredura": read(
            ROOT / "analysis/reponderacao/atualizacao_20261008/varredura.json"
        ),
    }
    write(ROOT / "analysis/reponderacao/auditoria_20261008.json", audit)
    write(ROOT / "docs/assets/reponderacao_20261008.json", audit)


if __name__ == "__main__":
    main()
