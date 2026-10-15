#!/usr/bin/env python3
"""Integra divulgações de 15/10 a partir de fontes arquivadas e conferidas."""

from __future__ import annotations

import importlib
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
POLLS = ROOT / "analysis/reponderacao/pesquisas"
DAY = "2026-10-15"
OPTIONS = ["flavio", "lula", "branco_nulo", "indecisos"]


def source(folder, filename, label, note, pages=None):
    items = COMMON.archive(folder)
    item = COMMON.source(items, filename)
    return {
        **item,
        "tipo": "relatorio" if filename.endswith(".pdf") else "materia_contratante",
        "rotulo": label,
        "paginas": pages or {},
        "conferido_em": DAY,
        "nota": note,
    }


def base(house, registry, field, n, method, published, origin):
    return {
        "id": f"{house.lower()}_{field[1]}",
        "instituto": house,
        "registro_tse": registry,
        "campo": {"inicio": field[0], "fim": field[1]},
        "divulgacao": DAY,
        "n": n,
        "metodo": method,
        "publicado": {"2t": dict(zip(OPTIONS, published, strict=True))},
        "fonte": origin,
    }


def datafolha():
    note = (
        "Folha, 15/10 às 18h30: 47/45/6/2 nos totais e 51/49 nos válidos. "
        "Campo efetivo 13–14/10, 2.520 entrevistas em 153 municípios, BR-00466/2026. "
        "A agenda prévia previa 13–15/10; prevalece o campo informado na divulgação. "
        "O painel e a API do G1 consultados ainda devolvem a onda de 08/10, "
        "BR-02949/2026, 49/45/5/1. Esses cruzamentos não são da nova pesquisa. "
        "A matéria atual informa renda até 2 SM (47% da amostra, Flávio 38 e Lula 53) "
        "e de 2 a 5 SM (37%, Flávio 55 e Lula 40), mas falta a faixa superior e "
        "a cobertura completa de renda. Entra pelo publicado na Projeção, sem ajuste PNAD."
    )
    poll = base(
        "Datafolha",
        "BR-00466/2026",
        ("2026-10-13", "2026-10-14"),
        2520,
        "presencial, pontos de fluxo",
        [47, 45, 6, 2],
        source("datafolha_102026_15", "folha.html", "Folha: divulgação de 15/10", note),
    )
    poll.update(
        contratante="Folha de S.Paulo e TV Globo",
        publicado_validos={"2t": {"flavio": 51, "lula": 49}},
        ignorar=True,
        motivo=(
            "Nova onda de 15/10 confirmada. Sem ajuste PNAD: cruzamentos e perfil "
            "atuais incompletos; o G1 consultado ainda mostrava 08/10. "
            "A onda anterior não substitui os dados novos."
        ),
        cruzamentos={},
        cruzamentos_documentais={
            "opcoes": ["flavio", "lula"],
            "faixas": ["Até 2 SM", "De 2 a 5 SM", "Mais de 5 SM"],
            "linhas": [[38, 53], [55, 40], [None, None]],
            "perfil_pct_sobre_total": [47, 37, None],
            "nota": "Trechos da matéria atual; não completar por resíduo ou por onda anterior.",
        },
        conferencia_painel={
            "onda_devolvida": "2026-10-08",
            "onda_solicitada": DAY,
            "usado_na_onda_nova": False,
            "arquivo": "data/originals/datafolha_102026_15/g1-estimulada.json",
        },
    )
    return poll


def palver():
    note = (
        "Onda 7: PDF de 107 páginas, perfil ponderado na p. 20, totais na p. 23 "
        "e renda/sexo na p. 24, conferidos visualmente. Usam-se 36/41/23 do perfil "
        "final arredondado, não as contagens brutas 1.872/2.103/1.025 nem as metas "
        "36,36/41,01/22,63 da p. 16. Votos e perfis arredondados ao inteiro; "
        "indecisos 0% é publicação arredondada, não prova de ausência absoluta. "
        "O explorador consultado ainda terminava na onda 6. Método v3: "
        "PNADC 2025, 1ª entrevista, e voto declarado no 1º turno de 2026 por região "
        "nos pesos, além de voto de 2022 e filiação partidária. A mudança de "
        "calibração impede interpretar a diferença ante a onda 6 como evolução pura do voto. "
        "Ficha técnica pp. 14, 16 e 20 confirma BR-08028/2026 e campo 10–13/10; "
        "o release contém códigos divergentes (BR-00198 e BR-09028), preservados no arquivo."
    )
    poll = base(
        "Palver",
        "BR-08028/2026",
        ("2026-10-10", "2026-10-13"),
        5000,
        "online, recrutamento por anúncios em redes sociais, amostra não probabilística; raking v3",
        [50, 49, 1, 0],
        source(
            "palver_102026_15",
            "relatorio.pdf",
            "Palver: relatório completo da onda 7",
            note,
            {
                "metodologia": "12–18",
                "perfil_renda": 20,
                "2t_topline": 23,
                "2t_renda": 24,
                "sexo": 24,
            },
        ),
    )
    poll["contratante"] = "Palver (iniciativa própria)"
    poll["fonte"].update(
        pdf=poll["fonte"]["arquivo"],
        total_paginas=107,
        status="Íntegra atual conferida; perfil ponderado e cruzamentos arredondados.",
    )
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [36, 41, 23],
        [[48, 51, 1, 0], [52, 48, 0, 0], [52, 48, 1, 0]],
        [[60, 39, 1, 0], [41, 58, 0, 0]],
        [48, 52],
        note,
    )
    poll["renda"]["perfil_tipo"] = "perfil_ponderado"
    poll["metodologia_onda"] = {
        "versao": "v3",
        "pnad": "PNADC 2025, 1ª entrevista",
        "voto_1t_2026_por_regiao": True,
        "comparavel_onda_anterior": False,
        "n_efetivo": 1783,
        "efeito_pesos": 2.80,
        "margem_publicada_pp": 2.3,
    }
    return poll


def indexa():
    note = (
        "Divulgação do contratante Broadcast em 15/10: Flávio 44, Lula 42, "
        "branco/nulo 4, não iria votar 8 e indecisos 2; válidos publicados 51/49. "
        "As três faixas de renda têm votos dos candidatos, mas o perfil ponderado, "
        "as bases e a não resposta por faixa não foram localizados. "
        "Sem pesos verificados, não há reponderação identificável. "
        "Entra na Projeção pelo publicado. Os 8% que dizem não votar ficam separados "
        "na transcrição; no motor integram a não escolha, sem substituir o parâmetro "
        "de comparecimento nem produzir previsão de abstenção."
    )
    poll = base(
        "Indexa/Broadcast",
        "BR-04629/2026",
        ("2026-10-13", "2026-10-14"),
        2000,
        "entrevistas individuais por telefone",
        [44, 42, 4, 2],
        source(
            "indexa_102026_15",
            "broadcast.html",
            "Indexa/Broadcast: divulgação do contratante",
            note,
        ),
    )
    poll["id"] = "indexa_2026-10-14"
    poll["publicado"]["2t"]["nao_vai_votar"] = 8
    poll.update(
        contratante="Agência Estado (Broadcast)",
        publicado_validos={"2t": {"flavio": 51, "lula": 49}},
        ignorar=True,
        motivo="Voto por renda publicado, mas perfil ponderado e bases atuais não localizados. Sem ajuste PNAD; publicado preservado na Projeção.",
        cruzamentos={},
        cruzamentos_documentais={
            "opcoes": ["flavio", "lula"],
            "faixas": ["Até 2 SM", "De 2 a 5 SM", "Mais de 5 SM"],
            "linhas": [[36.2, 45.8], [44.5, 41.7], [49.7, 38.9]],
            "perfil_pct": None,
            "nota": "Publicado pelo Broadcast; sem pesos, não resolver perfil por inversão de toplines arredondados.",
        },
    )
    return poll


def main():
    polls = [datafolha(), palver(), indexa()]
    for poll in polls:
        COMMON.write(POLLS / (poll["id"] + ".json"), poll)
    inventory = {
        "data": DAY,
        "pesquisas": polls,
        "fontes": {
            name: COMMON.archive(name)
            for name in [
                "datafolha_102026_15",
                "palver_102026_15",
                "indexa_102026_15",
                "atlas_102026_15_conferencia",
            ]
        },
        "varredura": [
            {
                "instituto": "AtlasIntel",
                "status": "Nenhuma nova onda nacional localizada em 15/10",
                "conclusao": "A aba Exclusive Polls do instituto continua com divulgação nacional de 09/10, campo 03–08/10, n = 5.026. Mantida a onda existente, sem duplicação. Notícias de agenda apontam próxima divulgação em 19/10; agenda não é resultado.",
                "fontes": ["https://www.atlasintel.org/polls/exclusive-polls"],
                "resumo": True,
            },
            {
                "instituto": "Datafolha",
                "status": "Publicado incorporado; renda atual incompleta",
                "conclusao": "Conferir a íntegra ou a atualização do G1. A resposta arquivada da API é de 08/10 e não serve para reponderar a onda de 15/10.",
                "fontes": [
                    "https://especiaisg1.globo/politica/eleicoes/2026/pesquisas-eleitorais/presidente/2-turno/Datafolha/internal/"
                ],
                "pendente": True,
            },
            {
                "instituto": "Indexa/Broadcast",
                "status": "Publicado incorporado; pesos de renda ausentes",
                "conclusao": "O contratante publica o voto por renda, mas não os pesos de composição. Sem ajuste PNAD até localizar o perfil atual.",
                "fontes": [polls[2]["fonte"]["url"]],
                "pendente": True,
            },
        ],
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261015.json", inventory)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261015.json", inventory)
    print("Integradas: " + ", ".join(p["id"] for p in polls))


if __name__ == "__main__":
    main()
