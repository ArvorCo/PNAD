#!/usr/bin/env python3
"""Integra CNT/MDA e França de 24/10 a partir dos documentos arquivados."""

import importlib
import shutil
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-24"


def mda():
    note = (
        "173ª rodada, 39 páginas, campo 21–23/10, n=2.032 em 140 municípios, "
        "BR-02136/2026. P. 2 distribui o campo em 4%/52%/44% nos três dias e "
        "declara ponderação socioeconômica e pelo voto declarado no 1º turno. "
        "Perfil atual p. 22: renda familiar 42,4/36,0/20,6 e NS/NR 1,0%; "
        "sexo 47,2/52,8. Etapa do perfil antes/depois dos pesos não explicitada: "
        "ajuste condicional ao perfil publicado, limitado aos 99% declarantes. "
        "P. 6: F/L/BN/I 46,3/45,0/5,8/2,9; renda e sexo p. 7 conferidos "
        "visualmente e recompostos. Válidos oficiais 50,7/49,3 na p. 8 ficam "
        "separados da normalização dos totais arredondados. Decisão de voto e "
        "potencial de voto não medem comparecimento."
    )
    poll = PREVIOUS.base(
        "mda_2026-10-23",
        "MDA",
        "BR-02136/2026",
        ("2026-10-21", "2026-10-23"),
        DAY,
        2032,
        "presencial, domiciliar e pontos de fluxo, 140 municípios",
        "mda_102026_24",
        {
            "metodologia": 2,
            "2t_topline": 6,
            "2t_renda": 7,
            "sexo": 7,
            "2t_validos": 8,
            "perfil_renda": 22,
        },
        39,
        [46.3, 45, 5.8, 2.9],
        note,
    )
    poll["fonte"]["conferido_em"] = DAY
    poll["contratante"] = "Confederação Nacional do Transporte (CNT)"
    poll["publicado_validos"] = {"2t": {"flavio": 50.7, "lula": 49.3}}
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [42.4, 36, 20.6],
        [[37, 53, 5, 5], [49, 42, 7, 2], [59, 35, 5, 1]],
        [[53, 40, 6, 1], [41, 50, 6, 4]],
        [47.2, 52.8],
        note,
        99,
    )
    poll["renda"]["perfil_tipo"] = "perfil_publicado"
    poll["metodologia_onda"] = {"ponderacao_voto_1t_2026": True, "pagina": 2}
    poll["distribuicao_campo_pct"] = {
        "2026-10-21": 4,
        "2026-10-22": 52,
        "2026-10-23": 44,
    }
    return poll


def franca():
    note = (
        "Material para imprensa de 7 páginas, n=1.537, BR-04863/2026. "
        "Campo 21–23/10 e divulgação 24/10 confirmados na matéria do Poder360 "
        "arquivada; o PDF não informa as datas do campo. Pp. 2/7: "
        "F/L/BN/NS 45,6/43,1/7,4/3,9 e válidos oficiais 51,4/48,6. "
        "Pp. 5/7 publicam voto por renda familiar, mas não as bases ou pesos "
        "atuais das faixas. Sem perfil atual, não recompor nem ajustar pela PNAD. "
        "Não transportar o perfil da onda de 20/10 nem usar alvos registrados "
        "como pesos observados. P. 6 declara seleção por cotas, sem informar "
        "o modo de entrevista. Somente publicado na Projeção."
    )
    poll = PREVIOUS.base(
        "franca_2026-10-23",
        "Instituto França",
        "BR-04863/2026",
        ("2026-10-21", "2026-10-23"),
        DAY,
        1537,
        "seleção por cotas; modo de entrevista não informado no material consultado",
        "franca_102026_24",
        {"metodologia": 6, "2t_topline": 2, "2t_validos": 2, "sexo": 7, "2t_renda": 7},
        7,
        [45.6, 43.1, 7.4, 3.9],
        note,
    )
    poll["fonte"].update(
        {
            "conferido_em": DAY,
            "rotulo": "Material para imprensa conferido",
            "status": "Material para imprensa arquivado; perfil de renda atual ausente.",
        }
    )
    poll["fonte_divulgacao"] = COMMON.source(
        COMMON.archive("franca_102026_24"), "divulgacao.html"
    )
    poll["contratante"] = "Instituto França, recursos próprios, segundo a divulgação"
    poll["publicado_validos"] = {"2t": {"flavio": 51.4, "lula": 48.6}}
    poll["ignorar"] = True
    poll["cruzamentos"] = {}
    poll["motivo"] = (
        "Voto por renda publicado sem bases ou pesos atuais; somente publicado na Projeção."
    )
    poll["cruzamentos_sem_perfil"] = {
        "paginas": [5, 7],
        "opcoes": PREVIOUS.OPTIONS,
        "renda": {
            "faixas": PREVIOUS.bands([2, 5, None]),
            "linhas": [
                [38.4, 49, 8.3, 4.3],
                [55.6, 36.6, 6.1, 1.7],
                [52.6, 36.8, 7.3, 3.3],
            ],
        },
        "sexo": {
            "rotulos": ["Masculino", "Feminino"],
            "linhas": [[48.1, 42.1, 6.6, 3.2], [40.4, 47.5, 8, 4.1]],
        },
    }
    return poll


def main():
    polls = [mda(), franca()]
    for poll in polls:
        COMMON.write(
            ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
        )
        slug = poll["id"].split("_")[0]
        shutil.copyfile(
            ROOT / poll["fonte"]["pdf"], ROOT / f"docs/fontes/{slug}_24102026.pdf"
        )
        print(poll["id"], "publicado" if poll.get("ignorar") else "PNAD condicional")
    path = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
    presence = COMMON.read(path)
    presence["conferido_em"] = DAY
    houses = {p["instituto"] for p in polls}
    presence["auditoria_ultima_onda"] = [
        p for p in presence["auditoria_ultima_onda"] if p["instituto"] not in houses
    ] + [
        {
            "instituto": p["instituto"],
            "id": p["id"],
            "tipo": "neutro",
            "fonte": p["fonte"]["url"],
            "arquivo": p["fonte"]["arquivo"],
            "nota": "Sem cruzamento de presença incorporado nesta onda; não transportar taxas anteriores.",
        }
        for p in polls
    ]
    COMMON.write(path, presence)
    audit = {
        "data": DAY,
        "conferido_em": DAY,
        "pesquisas": polls,
        "regra": "Uma onda por casa; renda atual quando verificável; sem imputar pesos ausentes.",
        "pendencias": [p["motivo"] for p in polls if p.get("ignorar")],
        "integra_baixada": [p["id"] for p in polls],
        "corte_consulta": "2026-10-24T16:43:00-03:00",
        "nota_corte": "Rodadas de 23/10 já integradas. Outras divulgações previstas para 24/10 "
        "sem resultado confirmado nesta consulta não são novas observações.",
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261024.json", audit)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261024.json", audit)


if __name__ == "__main__":
    main()
