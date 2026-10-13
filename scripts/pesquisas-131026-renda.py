#!/usr/bin/env python3
"""Integra as íntegras de outubro conferidas em 13/10, sem consultas vivas."""

from __future__ import annotations

import importlib
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
ROOT = Path(__file__).resolve().parents[1]
POLLS = ROOT / "analysis/reponderacao/pesquisas"
DAY = "2026-10-13"
OPTIONS = ["flavio", "lula", "branco_nulo", "indecisos"]


def source(folder, pages, count, note):
    items = COMMON.archive(folder)
    item = COMMON.source(items, "relatorio.pdf")
    return {
        **item,
        "pdf": item["arquivo"],
        "tipo": "relatorio",
        "rotulo": "Relatório completo conferido",
        "paginas": pages,
        "total_paginas": count,
        "conferido_em": DAY,
        "status": "Íntegra arquivada e conferida visualmente.",
        "nota": note,
    }


def vector(values):
    return dict(zip(OPTIONS, values, strict=True))


def control(published, rows, weights, options=OPTIONS):
    recomposed = {
        k: sum(row[i] * w for row, w in zip(rows, weights, strict=True)) / sum(weights)
        for i, k in enumerate(options)
    }
    residual = {k: recomposed[k] - published[k] for k in options}
    maximum = max(abs(v) for v in residual.values())
    if maximum > 1.5:
        raise ValueError(f"Recomposição incompatível: {residual}")
    return {
        "pesos": weights,
        "linhas": rows,
        "opcoes": options,
        "recomposto": recomposed,
        "residuo": residual,
        "residuo_max_abs": maximum,
    }


def bands(cuts):
    previous, result = 0, []
    for cut in cuts:
        result.append(
            {
                "rotulo": f"{previous} a {cut} SM" if cut else f"Mais de {previous} SM",
                "max": cut,
            }
        )
        previous = cut
    return result


def base(
    ident, house, registry, field, release, n, method, folder, pages, count, pub, note
):
    return {
        "id": ident,
        "instituto": house,
        "registro_tse": registry,
        "contratante": house + ", recursos próprios",
        "campo": {"inicio": field[0], "fim": field[1]},
        "divulgacao": release,
        "n": n,
        "metodo": method,
        "publicado": {"2t": vector(pub)},
        "fonte": source(folder, pages, count, note),
    }


def income(poll, cuts, weights, rows, sex_rows, sex_weights, note, fraction=100):
    poll["renda"] = {
        "unidade": "salarios_minimos",
        "ano_referencia": 2026,
        "mes_precos": "202610",
        "faixas": bands(cuts),
        "amostra_pct": weights,
        "perfil_tipo": "perfil_ponderado",
        "nota": note,
    }
    if fraction != 100:
        poll["renda"]["parcela_ajustada_pct"] = fraction
    poll["cruzamentos"] = {"2t": {"opcoes": OPTIONS, "linhas": rows, "nota": note}}
    poll["controles"] = {
        "2t": {
            "renda": control(poll["publicado"]["2t"], rows, weights),
            "sexo": control(poll["publicado"]["2t"], sex_rows, sex_weights),
        }
    }
    return poll


def gerp():
    note = (
        "Campo em 08, 09 e 12/10, não uma coleta contínua: p. 7. Publicação oficial 13/10 no manifesto; "
        "a divulgação na TMC começou na noite de 12/10. P. 8: percentuais ponderados de renda "
        "20/20/28/12/5/2 e recusa 14, soma arredondada 101. As bases de campo da p. 16 não são pesos. "
        "O ajuste troca renda somente entre declarantes: 87/101 do total; o restante permanece "
        "no placar publicado, sem voto por renda imputado. Topline 53/44/1/3 soma 101 por arredondamento."
    )
    poll = base(
        "gerp_2026-10-12",
        "Gerp",
        "BR-07877/2026",
        ("2026-10-08", "2026-10-12"),
        DAY,
        2400,
        "telefônico, CATI/GerpCati; ponderação por sexo, idade, escolaridade, renda familiar e região",
        "gerp_102026_13",
        {
            "metodologia": 7,
            "perfil_renda": 8,
            "2t_topline": 14,
            "2t_renda": 16,
            "sexo": 16,
            "2t_validos": 21,
        },
        57,
        [53, 44, 1, 3],
        note,
    )
    poll["datas_de_campo"] = ["2026-10-08", "2026-10-09", "2026-10-12"]
    poll["publicado_validos"] = {"2t": {"flavio": 55, "lula": 45}}
    return income(
        poll,
        [1, 2, 5, 10, 20, None],
        [20, 20, 28, 12, 5, 2],
        [
            [37, 60, 1, 2],
            [53, 42, 2, 3],
            [62, 35, 1, 2],
            [57, 40, 1, 2],
            [54, 37, 1, 8],
            [64, 35, 1, 1],
        ],
        [[62, 35, 1, 2], [44, 52, 1, 3]],
        [47, 53],
        note,
        100 * 87 / 101,
    )


def poderdata():
    note = (
        "Íntegra correta: campo 10–12/10, registro BR-01209/2026, 27 páginas. O índice de PDFs "
        "na matéria de 13/10 ainda apontava para 05–07/10; a íntegra atual foi localizada na "
        "síntese do próprio Poder360. Perfil desta onda na p. 4: 46/33/21; não é emprestado da anterior. "
        "Total 48/46/5/2 (101 por arredondamento), renda p. 9 e controle independente por sexo p. 7."
    )
    poll = base(
        "poderdata_2026-10-12",
        "PoderData",
        "BR-01209/2026",
        ("2026-10-10", "2026-10-12"),
        DAY,
        3000,
        "telefônico automatizado, URA/IVR, celulares e fixos; 686 municípios nas 27 UFs",
        "poderdata_102026_13",
        {
            "metodologia": 2,
            "perfil_renda": 4,
            "2t_topline": 6,
            "sexo": 7,
            "2t_renda": 9,
        },
        27,
        [48, 46, 5, 2],
        note,
    )
    poll["contratante"] = "Poder360, recursos próprios; divulgação com Aya Bancah"
    poll["publicado_validos"] = {"2t": {"flavio": 51, "lula": 49}}
    return income(
        poll,
        [2, 5, None],
        [46, 33, 21],
        [[43, 48, 6, 2], [53, 43, 3, 2], [51, 44, 4, 1]],
        [[57, 38, 4, 1], [39, 53, 6, 3]],
        [47, 53],
        note,
    )


def nexus():
    note = (
        "17ª rodada: campo 10–12/10, 2.002 entrevistas, divulgação 13/10. "
        "Perfil atual p. 99: renda familiar 19/18/40/23. Voto por renda p. 41; sexo p. 40. "
        "Não transporta preferências ou rejeição de setembro. P. 15 declara 89% de presença decidida "
        "e 6% provável: declaração de intenção (95%), não previsão calibrada de comparecimento. "
        "Não substitui automaticamente a referência oficial de 79,16% do primeiro turno."
    )
    poll = base(
        "nexus_2026-10-12",
        "Nexus",
        "BR-07997/2026",
        ("2026-10-10", "2026-10-12"),
        DAY,
        2002,
        "telefônico CATI; cotas de sexo, idade, escolaridade, tipo de telefonia e DDD",
        "nexus_102026_13",
        {
            "metodologia": 4,
            "perfil_renda": 99,
            "2t_topline": 21,
            "2t_validos": 23,
            "sexo": 40,
            "2t_renda": 41,
            "comparecimento": 15,
        },
        102,
        [48, 45, 5, 2],
        note,
    )
    poll["contratante"] = "Banco BTG Pactual"
    poll["publicado_validos"] = {"2t": {"flavio": 52, "lula": 48}}
    poll["comparecimento_publicado"] = {
        "pagina": 15,
        "categorias": [
            "decidiu comparecer",
            "provavelmente comparecerá",
            "provavelmente não comparecerá",
            "decidiu não comparecer",
            "NS/NR",
        ],
        "pct": [89, 6, 1, 3, 1],
        "uso": "Declaração, não âncora de comparecimento nem taxa observada por candidato.",
    }
    return income(
        poll,
        [1, 2, 5, None],
        [19, 18, 40, 23],
        [[32, 58, 3, 7], [47, 44, 5, 4], [50, 43, 7, 1], [57, 40, 2, 0]],
        [[57, 36, 5, 1], [39, 54, 4, 3]],
        [47, 53],
        note,
    )


def ipespe():
    note = (
        "Primeira rodada do tracking Ipespe/ABRAPEL, 06–08/10, publicada 10/10; íntegra de 35 páginas. "
        "A metodologia p. 33 declara CATI, diferente do recrutamento digital citado por parte da imprensa. "
        "A p. 5 informa 49/44/5/3, soma 101 por arredondamento: os indecisos são 3%, não 1%. "
        "Perfil de renda familiar da própria onda na p. 34: 41/39/20. Cruzamentos p. 6. "
        "Válidos divulgados 52,7/47,3 preservados separadamente da normalização dos totais arredondados."
    )
    poll = base(
        "ipespe_2026-10-08",
        "Ipespe",
        "BR-00933/2026",
        ("2026-10-06", "2026-10-08"),
        "2026-10-10",
        1500,
        "telefônico CATI/IPESPE; cotas de sexo, idade e localidade; controle de instrução, renda e recall do 1º turno",
        "ipespe_102026_10",
        {
            "metodologia": 33,
            "perfil_renda": 34,
            "2t_topline": 5,
            "2t_validos": 5,
            "2t_renda": 6,
            "sexo": 6,
        },
        35,
        [49, 44, 5, 3],
        note,
    )
    poll["contratante"] = "IPESPE/ABRAPEL, recursos próprios"
    poll["publicado_validos"] = {"2t": {"flavio": 52.7, "lula": 47.3}}
    return income(
        poll,
        [2, 5, None],
        [41, 39, 20],
        [[40, 51, 6, 3], [55, 37, 5, 3], [54, 42, 3, 1]],
        [[53, 38, 6, 3], [44, 49, 4, 3]],
        [47, 53],
        note,
    )


def datafolha():
    poll = COMMON.read(POLLS / "datafolha_2026-10-08.json")
    note = (
        "Relatório de 34 páginas recebido do usuário em 13/10, preservado sem alterações. "
        "Pp. 2 e 19–21: campo 06–07/10 (corrige 06–08/10 da notícia), 2.520 entrevistas, "
        "registro BR-02949/2026. P. 26 (p. 8 do anexo): bases ponderadas atuais de renda "
        "1.187/874/337, total 2.398 declarantes; sem renda, 122/2.520. Não reutiliza mais "
        "1.209/856/344 da onda anterior. Ajuste limitado a 2.398/2.520 da base, restante "
        "preservado no topline. P. 23 publica o perfil; sexo e região atuais conferem o placar. "
        "O id legado e a divulgação de 08/10 são preservados: é revisão documental, não uma nova onda."
    )
    poll["campo"] = {"inicio": "2026-10-06", "fim": "2026-10-07"}
    weights = [1187, 874, 337]
    poll["renda"].update(
        bases=weights,
        perfil_tipo="perfil_ponderado",
        parcela_ajustada_pct=100 * sum(weights) / 2520,
        nota=note,
    )
    rows = poll["cruzamentos"]["2t"]["linhas"]
    options = poll["cruzamentos"]["2t"]["opcoes"]
    poll["cruzamentos"]["2t"]["nota"] = note
    published = poll["publicado"]["2t"]
    poll["controles"] = {
        "2t": {
            "renda": control(published, rows, weights, options),
            "sexo": control(
                published, [[41, 53, 5, 0], [50, 44, 4, 2]], [1210, 1310], options
            ),
            "regiao": control(
                published,
                [[42, 50, 6, 1], [35, 58, 5, 2], [61, 35, 4, 1], [37, 58, 3, 2]],
                [1069, 384, 669, 398],
                options,
            ),
        }
    }
    poll["fonte"] = source(
        "datafolha_102026_13",
        {
            "metodologia": 2,
            "perfil_renda": 23,
            "2t_topline": 26,
            "2t_renda": 26,
            "sexo": 26,
            "regiao": 26,
            "2t_validos": 27,
        },
        34,
        note,
    )
    poll["fonte"].update(
        relatorio_completo=DAY,
        proveniencia="Arquivo fornecido pelo usuário; URL é cópia pública preservada, não origem do download.",
    )
    poll["fonte"]["complementos"] = [
        {
            "url": "https://g1.globo.com/politica/eleicoes/2026/pesquisa-eleitoral/presidente-br-2-turno-datafolha/",
            "rotulo": "Painel da divulgação inicial, preservado",
        }
    ]
    return poll


def futura():
    note = (
        "Íntegra de 18 páginas publicada 13/10, campo 07–10/10. P. 7 fornece renda familiar "
        "26,9/21,8/24,1/10/6, NS/NR 11,3%; p. 11 abre voto apenas por sexo, região e idade. "
        "Não há voto por renda nas 18 páginas: perfil sozinho não permite reponderar. "
        "Entram totais 50/46,6/1,7/1,7 na Projeção; sem renda imputada e fora da Central Média."
    )
    poll = base(
        "futura_2026-10-10",
        "Futura",
        "BR-00650/2026",
        ("2026-10-07", "2026-10-10"),
        DAY,
        2000,
        "telefônico CATI, eleitores de 16 anos ou mais",
        "futura_102026_13",
        {
            "metodologia": 4,
            "perfil_renda": 7,
            "2t_topline": 10,
            "2t_validos": 12,
            "sexo": 11,
        },
        18,
        [50, 46.6, 1.7, 1.7],
        note,
    )
    poll.update(
        ignorar=True,
        motivo="Perfil de renda publicado, sem cruzamento de voto por renda. Sem ajuste identificável.",
        cruzamentos={},
    )
    poll["contratante"] = "Futura/100% Cidades"
    poll["publicado_validos"] = {"2t": {"flavio": 51.8, "lula": 48.2}}
    poll["perfil_economico_publicado"] = {
        "pagina": 7,
        "unidade": "renda familiar em salários mínimos",
        "pct": [26.9, 21.8, 24.1, 10, 6],
        "ns_nr_pct": 11.3,
    }
    return poll


def datatrends():
    note = (
        "Íntegra localizada: 31 páginas, campo 07–09/10 e publicação 11/10. P. 25 abre voto por renda; "
        "p. 3 declara pesos 46,7/34,6/18,7. Contudo a p. 7 rotula renda domiciliar per capita, "
        "e a p. 4 diz renda domiciliar total: universos diferentes, sem reconciliação verificável. "
        "Não trocar essa margem por renda familiar da PNAD até esclarecer a variável. "
        "Placar publicado da p. 12, 50/44/5/1, entra sem ajuste na Projeção. P. 4 informa NS/NR 2%, "
        "em vez de 1% na p. 12; preservadas as duas versões, com preferência pelo gráfico principal. "
        "Válidos 53,1/46,9 da p. 13 não são usados para inventar não escolha."
    )
    poll = base(
        "datatrends_2026-10-09",
        "DataTrends",
        "BR-03576/2026",
        ("2026-10-07", "2026-10-09"),
        "2026-10-11",
        2000,
        "telefônico automatizado URA/DTMF; ponderação por UF, gênero, idade, escolaridade e renda",
        "datatrends_102026_11",
        {
            "metodologia": 2,
            "perfil_renda": 3,
            "perfil_rotulo": 7,
            "2t_topline": 12,
            "2t_validos": 13,
            "2t_renda": 25,
        },
        31,
        [50, 44, 5, 1],
        note,
    )
    poll.update(
        ignorar=True,
        motivo="Cruzamento disponível, mas a definição de renda conflita (per capita versus total). Publicado sem ajuste na Projeção.",
        cruzamentos={},
    )
    poll["publicado_validos"] = {"2t": {"flavio": 53.1, "lula": 46.9}}
    poll["perfil_economico_publicado"] = {
        "pagina": 3,
        "pct": [46.7, 34.6, 18.7],
        "rotulo_p7": "Renda domiciliar per capita",
        "rotulo_p4": "Renda domiciliar total",
    }
    poll["cruzamentos_documentais"] = {
        "pagina": 25,
        "opcoes": OPTIONS,
        "linhas": [
            [47.8, 47.3, 3.7, 1.2],
            [51.2, 42.2, 5.3, 1.3],
            [50.9, 37.4, 8.6, 3.1],
        ],
        "uso": "Documental, sem calibração enquanto a variável de renda não for reconciliada.",
    }
    poll["publicado_alternativo"] = {"pagina": 4, "2t": vector([50, 44, 5, 2])}
    return poll


def main():
    records = [
        gerp(),
        poderdata(),
        nexus(),
        ipespe(),
        datafolha(),
        futura(),
        datatrends(),
    ]
    for poll in records:
        COMMON.write(POLLS / (poll["id"] + ".json"), poll)
    audit = {
        "conferencia": DAY,
        "pesquisas": [p["id"] for p in records],
        "controles": {p["id"]: p.get("controles", {}) for p in records},
        "limites": {p["id"]: p["fonte"]["nota"] for p in records},
    }
    COMMON.write(ROOT / "docs/assets/reponderacao_20261013.json", audit)
    print(
        f"{len(records)} registros conferidos: seis ondas novas e revisão da íntegra Datafolha."
    )


if __name__ == "__main__":
    main()
