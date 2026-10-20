#!/usr/bin/env python3
"""Integra Ipespe, Atlas, Futura e Vox conferidas nas íntegras em 19/10."""

import importlib
import shutil
from pathlib import Path

PREVIOUS = importlib.import_module("pesquisas-131026-renda")
COMMON = importlib.import_module("pesquisas-081026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-19"


def base(
    ident, house, registry, field, release, n, method, folder, pages, count, pub, note
):
    poll = PREVIOUS.base(
        ident,
        house,
        registry,
        field,
        release,
        n,
        method,
        folder,
        pages,
        count,
        pub,
        note,
    )
    poll["fonte"]["conferido_em"] = DAY
    return poll


def ipespe():
    note = (
        "2ª rodada do tracking, divulgada em 17/10; campo 13–15/10, 1.500 entrevistas CATI. "
        "Íntegra de 39 páginas. Estimulada 48/46/3/3 na p. 5; válidos publicados "
        "51,2/48,8 preservados separadamente da divisão dos inteiros. Perfil familiar "
        "41/38/22 na p. 38, soma 101 por arredondamento; cruzamentos atuais na p. 6. "
        "Etapa do perfil antes/depois dos pesos não explicitada: sensibilidade condicional. "
        "Ficha p. 37 declara controle de renda e recall do voto no 1º turno de 2026. "
        "Os 89% que declaram máxima chance de comparecer e o placar desse subconjunto "
        "(pp. 12–13) não substituem o total da amostra nem a âncora de comparecimento."
    )
    poll = base(
        "ipespe_2026-10-15",
        "Ipespe",
        "BR-00223/2026",
        ("2026-10-13", "2026-10-15"),
        "2026-10-17",
        1500,
        "telefônico CATI, eleitores de 16 anos ou mais",
        "ipespe_102026_17",
        {
            "metodologia": 37,
            "perfil_renda": 38,
            "2t_topline": 5,
            "2t_validos": 5,
            "2t_renda": 6,
            "sexo": 6,
            "comparecimento": "12–13",
        },
        39,
        [48, 46, 3, 3],
        note,
    )
    poll["contratante"] = "Ipespe/Abrapel"
    poll["publicado_validos"] = {"2t": {"flavio": 51.2, "lula": 48.8}}
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [41, 38, 22],
        [[40, 54, 3, 3], [54, 41, 3, 2], [54, 40, 2, 4]],
        [[53, 41, 3, 3], [43, 51, 3, 2]],
        [47, 53],
        note,
    )
    poll["renda"]["perfil_tipo"] = "perfil_publicado"
    poll["metodologia_onda"] = {"controle_recall_voto_1t_2026": True, "pagina": 37}
    return poll


def atlas():
    note = (
        "Íntegra de 20 páginas. Campo 13–18/10 integralmente posterior ao primeiro turno; "
        "4.998 entrevistas efetivas. Perfil familiar atual p. 5: 18/12,2/25,9/26,6/17,2, "
        "soma 99,9 por arredondamento; cortes nominais R$ 2/3/5/10 mil. Cruzamentos p. 9. "
        "Sensibilidade condicional ao perfil publicado, sem etapa pré/pós-pesos explícita. "
        "A p. 4 declara pós-estratificação por comportamento eleitoral anterior sem "
        "especificar qual eleição; a existência de recall na p. 9 não prova seu uso como alvo. "
        "Branco/nulo/não sei (2,6%) permanece agregado, sem indecisos imputados. "
        "Cortes de outubro deflacionados somente até o último IPCA arquivado, sem extrapolação."
    )
    poll = base(
        "atlas_2026-10-18",
        "AtlasIntel",
        "BR-02418/2026",
        ("2026-10-13", "2026-10-18"),
        DAY,
        4998,
        "recrutamento digital aleatório Atlas RDR; pós-estratificação",
        "atlas_102026_19",
        {
            "metodologia": 4,
            "perfil_renda": 5,
            "2t_topline": 7,
            "2t_validos": 8,
            "2t_renda": 9,
            "sexo": 9,
        },
        20,
        [49.8, 47.6, 2.6, 0],
        note,
    )
    # O agregado do PDF não permite medir indecisos separadamente.
    del poll["publicado"]["2t"]["indecisos"]
    poll["contratante"] = "Bloomberg"
    poll["publicado_validos"] = {"2t": {"flavio": 51.1, "lula": 48.9}}
    options = ["flavio", "lula", "branco_nulo"]
    rows = [
        [39.7, 55.7, 4.6],
        [57.5, 42.4, 0.1],
        [52.4, 45.3, 2.2],
        [53, 44, 3],
        [46.2, 51.7, 2.1],
    ]
    weights = [18, 12.2, 25.9, 26.6, 17.2]
    prior = COMMON.read(ROOT / "analysis/reponderacao/pesquisas/atlas_2026-10-08.json")
    poll["renda"] = {
        "unidade": "reais_nominais",
        "mes_precos": "202610",
        "faixas": prior["renda"]["faixas"],
        "amostra_pct": weights,
        "perfil_tipo": "perfil_publicado",
        "nota": note,
    }
    poll["cruzamentos"] = {"2t": {"opcoes": options, "linhas": rows, "nota": note}}
    poll["controles"] = {
        "2t": {
            "renda": PREVIOUS.control(poll["publicado"]["2t"], rows, weights, options),
            "sexo": PREVIOUS.control(
                poll["publicado"]["2t"],
                [[61.7, 35, 3.3], [39.2, 58.9, 1.9]],
                [47.1, 52.9],
                options,
            ),
        }
    }
    poll["fonte"]["rotulos_opcoes"] = {"branco_nulo": "Branco/nulo/não sei (agregado)"}
    return poll


def futura():
    note = (
        "3ª rodada de outubro, 18 páginas, campo 16–17/10 e divulgação 19/10. "
        "Estimulada p. 10: 48,3/47,5/2,4/1,9, soma 100,1 por arredondamento. "
        "Válidos publicados 50,4/49,6 na p. 12. Perfil familiar p. 7 existe, "
        "mas o cruzamento p. 11 contém somente sexo, região e idade. Sem voto por renda, "
        "somente publicado na Projeção. A nota de escolaridade PNAD da p. 5 já constava "
        "nas ondas de 13 e 16/10; não identifica nova mudança nesta rodada."
    )
    poll = base(
        "futura_2026-10-17",
        "Futura",
        "BR-06715/2026",
        ("2026-10-16", "2026-10-17"),
        DAY,
        2000,
        "telefônico CATI, eleitores de 16 anos ou mais",
        "futura_102026_19",
        {
            "metodologia": "4–5",
            "perfil_renda": 7,
            "2t_topline": 10,
            "sexo": 11,
            "2t_validos": 12,
        },
        18,
        [48.3, 47.5, 2.4, 1.9],
        note,
    )
    poll.update(
        publicado_validos={"2t": {"flavio": 50.4, "lula": 49.6}},
        ignorar=True,
        motivo="Íntegra atual sem voto por renda; somente publicado na Projeção.",
        cruzamentos={},
        perfil_economico_publicado={
            "unidade": "renda familiar em salários mínimos",
            "pagina": 7,
            "faixas_sm": [1, 2, 5, 10, None],
            "pct": [28, 22.7, 22.7, 8.9, 5.6],
            "ns_nr": 12,
        },
    )
    poll["controles"] = {
        "2t": {
            "sexo": PREVIOUS.control(
                poll["publicado"]["2t"],
                [[55.5, 39.8, 2.5, 2.2], [41.4, 54.7, 2.3, 1.6]],
                [47.2, 52.9],
            )
        }
    }
    return poll


def vox():
    note = (
        "Íntegra de 53 páginas, campo 15–17/10, publicação 18/10, 2.100 entrevistas. "
        "Estimulada p. 13: 44,6/46,4/5/3,9, soma 99,9 por arredondamento; válidos 49/51. "
        "Esta onda traz voto por renda na p. 18, ao contrário da íntegra anterior. "
        "Perfil econômico p. 6: 84/12,4/2,7/1, soma 100,1. O documento não define "
        "renda familiar, individual ou per capita; não é defensável trocar essa régua "
        "pela renda familiar PNAD. Cruzamentos preservados como diagnóstico, sem ajuste. "
        "Recomposição por sexo e renda reproduz o topline dentro do arredondamento; "
        "isso não identifica o conceito de renda nem valida a amostragem. Somente publicado na Projeção."
    )
    poll = base(
        "vox_brasil_2026-10-17",
        "Vox Brasil",
        "BR-04332/2026",
        ("2026-10-15", "2026-10-17"),
        "2026-10-18",
        2100,
        "presencial domiciliar",
        "vox_102026_18",
        {
            "metodologia": 2,
            "perfil_renda": 6,
            "2t_topline": 13,
            "2t_validos": 13,
            "sexo": 15,
            "2t_renda": 18,
        },
        53,
        [44.6, 46.4, 5, 3.9],
        note,
    )
    rows = [
        [43.8, 46.5, 5.6, 4.1],
        [47.3, 47.3, 2.3, 3.1],
        [45.6, 50.9, 1.8, 1.8],
        [80, 15, 5, 0],
    ]
    weights = [84, 12.4, 2.7, 1]
    poll.update(
        publicado_validos={"2t": {"flavio": 49, "lula": 51}},
        ignorar=True,
        motivo="Há voto por renda, mas o conceito do perfil econômico não é definido. Sem ajuste PNAD; somente publicado na Projeção.",
        cruzamentos={},
        perfil_economico_publicado={
            "pagina": 6,
            "faixas_sm": [2, 5, 10, None],
            "percentuais": weights,
            "conceito": "não definido",
        },
        cruzamentos_diagnosticos={
            "pagina": 18,
            "opcoes": PREVIOUS.OPTIONS,
            "linhas": rows,
            "nota": "Última barra NS/NR ausente; zero aritmético para recomposição, não estimativa precisa de zero.",
        },
    )
    poll["controles"] = {
        "2t": {
            "renda": PREVIOUS.control(poll["publicado"]["2t"], rows, weights),
            "sexo": PREVIOUS.control(
                poll["publicado"]["2t"],
                [[48.9, 47.6, 2.4, 1.1], [40.8, 45.4, 7.4, 6.4]],
                [47, 53],
            ),
        }
    }
    return poll


def datatrends():
    items = COMMON.archive("datatrends_102026_19")
    source = COMMON.source(items, "materia.html")
    note = (
        "Resultado divulgado em 19/10 no blog de Edmar Lyra, dirigente da DataTrends, "
        "e corroborado pelo Bastidor. Campo 15–17/10, 2.000 entrevistas IVR, BR-04454/2026. "
        "Total 49/46/4/1 e válidos publicados 51,5/48,5, separados da normalização dos inteiros. "
        "Íntegra desta onda não localizada; sem perfil e voto por renda atuais conferidos. "
        "Não transportar o perfil ambíguo de renda da onda de 11/10. Somente publicado na Projeção."
    )
    return {
        "id": "datatrends_2026-10-17",
        "instituto": "DataTrends",
        "registro_tse": "BR-04454/2026",
        "campo": {"inicio": "2026-10-15", "fim": "2026-10-17"},
        "divulgacao": DAY,
        "n": 2000,
        "metodo": "telefônico automatizado IVR, 27 UFs",
        "contratante": "não informado na divulgação consultada",
        "publicado": {"2t": PREVIOUS.vector([49, 46, 4, 1])},
        "publicado_validos": {"2t": {"flavio": 51.5, "lula": 48.5}},
        "ignorar": True,
        "cruzamentos": {},
        "motivo": "Resultado publicado; íntegra e renda da onda atual ainda não localizadas. Somente publicado na Projeção.",
        "fonte": {
            **source,
            "tipo": "divulgacao",
            "rotulo": "Divulgação de Edmar Lyra/DataTrends",
            "conferido_em": DAY,
            "status": "Resultado conferido na divulgação; íntegra pendente.",
            "nota": note,
        },
    }


def main():
    polls = [ipespe(), atlas(), futura(), vox(), datatrends()]
    for poll in polls:
        target = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
        existing = COMMON.read(target) if target.exists() else {}
        # Reexecutar o inventário histórico não pode apagar revisão posterior.
        if existing.get("revisao", {}).get("data", DAY) <= DAY:
            COMMON.write(target, poll)
        if "pdf" not in poll["fonte"]:
            continue
        name = {
            "Ipespe": "ipespe_17102026",
            "AtlasIntel": "atlas_19102026",
            "Futura": "futura_19102026",
            "Vox Brasil": "vox_18102026",
        }[poll["instituto"]]
        shutil.copyfile(
            ROOT / poll["fonte"]["pdf"], ROOT / "docs/fontes" / (name + ".pdf")
        )
        print(
            poll["id"],
            {k: v["residuo_max_abs"] for k, v in poll["controles"]["2t"].items()},
        )
    audit = {
        "data": DAY,
        "pesquisas": polls,
        "regra": "Uma onda por casa; preservar os snapshots publicados.",
        "pendencias": [
            {
                "instituto": "DataTrends",
                "registro": "BR-04454/2026",
                "status": "Resultado integrado pelo publicado; íntegra e renda atual não localizadas.",
                "fontes": [
                    "https://www.poder360.com.br/tag/datatrends/",
                    "https://institutodatatrends.com/noticias?p=1",
                ],
            }
        ],
        "fora_do_universo_nacional": [
            {
                "instituto": "Paraná",
                "registro": "BR-09051/2026",
                "universo": "Tocantins",
                "fonte": "https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/19/pesquisas-do-2-turno-veja-quais-serao-publicadas-nesta-semana.html",
            }
        ],
    }
    COMMON.write(
        ROOT / "analysis/reponderacao/auditoria_20261019_complemento.json", audit
    )
    COMMON.write(ROOT / "docs/assets/reponderacao_20261019_complemento.json", audit)


if __name__ == "__main__":
    main()
