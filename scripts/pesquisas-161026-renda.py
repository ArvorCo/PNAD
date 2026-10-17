#!/usr/bin/env python3
"""Integra quatro divulgações de 16/10/2026 com fontes congeladas e controles."""

from __future__ import annotations

import importlib
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-16"


def base(house, registry, start, end, n, method, pages, count, pub, note):
    poll = PREVIOUS.base(
        f"{house.lower()}_{end}",
        house,
        registry,
        (start, end),
        DAY,
        n,
        method,
        f"{house.lower()}_102026_16",
        pages,
        count,
        pub,
        note,
    )
    poll["fonte"]["conferido_em"] = DAY
    return poll


def gerp():
    note = (
        "Íntegra de 57 páginas, campo 14–16/10, BR-05187/2026. Perfil ponderado "
        "atual p. 8: renda 22/22/32/13/5/2 e recusa 3, soma 99 por arredondamento. "
        "A parcela ajustada é 96/99; a recusa conserva o topline, sem preferência "
        "imputada. As bases de campo da p. 16 não são pesos. P. 14: "
        "50/45/2/3 (Flávio/Lula/nenhum/não sabe). Não somar um branco/nulo adicional "
        "da matéria: o gráfico da íntegra fecha 100%. Válidos publicados 52/48 "
        "(p. 21) ficam separados da normalização de 50/45 arredondados. "
        "Pp. 7–8 declaram ponderação por sexo, idade, escolaridade, renda e região."
    )
    poll = base(
        "Gerp",
        "BR-05187/2026",
        "2026-10-14",
        DAY,
        2400,
        "telefônico CATI (GerpCati), todas as UFs",
        {
            "metodologia": 7,
            "perfil_renda": 8,
            "2t_topline": 14,
            "2t_renda": 16,
            "sexo": 16,
            "2t_validos": 21,
        },
        57,
        [50, 45, 2, 3],
        note,
    )
    poll["publicado_validos"] = {"2t": {"flavio": 52, "lula": 48}}
    return PREVIOUS.income(
        poll,
        [1, 2, 5, 10, 20, None],
        [22, 22, 32, 13, 5, 2],
        [
            [28, 66, 2, 4],
            [45, 49, 2, 3],
            [61, 34, 2, 3],
            [58, 38, 2, 2],
            [62, 36, 2, 0],
            [57, 41, 1, 1],
        ],
        [[58, 38, 2, 2], [42, 52, 2, 4]],
        [47, 53],
        note,
        100 * 96 / 99,
    )


def poderdata():
    note = (
        "Íntegra atual de 33 páginas: campo 13–15/10, BR-04258/2026, "
        "3.000 entrevistas em 644 municípios. Perfil da própria onda p. 4: "
        "46/33/21. Topline 47/47/4/2, renda p. 9, sexo p. 7. A p. 2 declara "
        "ponderação por sexo, idade, instrução, renda, resultado do 1º turno "
        "e região. Renda e resultado do 1º turno não constavam da lista da ficha "
        "de 13/10; isso documenta mudança na declaração, sem identificar quando "
        "cada ajuste interno começou. O perfil publicado não explicita sua etapa antes/depois "
        "dos pesos: a troca dessa margem é sensibilidade condicional. "
        "O índice da matéria-resumo ainda apontava para 12/10; esta íntegra "
        "foi localizada no catálogo de relatórios do PoderData e conferida "
        "pelo campo e registro, sem reutilizar a onda anterior."
    )
    poll = base(
        "PoderData",
        "BR-04258/2026",
        "2026-10-13",
        "2026-10-15",
        3000,
        "telefônico automatizado IVR; discador aleatório, 644 municípios nas 27 UFs",
        {
            "metodologia": 2,
            "perfil_renda": 4,
            "2t_topline": 6,
            "sexo": 7,
            "2t_renda": 9,
        },
        33,
        [47, 47, 4, 2],
        note,
    )
    poll["contratante"] = "Poder360, recursos próprios; divulgação com Aya Bancah"
    poll["publicado_validos"] = {"2t": {"flavio": 50, "lula": 50}}
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [46, 33, 21],
        [[40, 52, 5, 2], [53, 42, 4, 1], [53, 44, 3, 1]],
        [[56, 39, 5, 1], [39, 55, 4, 3]],
        [47, 53],
        note,
    )
    poll["renda"]["perfil_tipo"] = "perfil_publicado"
    poll["metodologia_onda"] = {"ponderacao_voto_1t_2026": True, "pagina": 2}
    return poll


def mda():
    note = (
        "172ª rodada, íntegra de 39 páginas: campo 13–15/10, 2.014 entrevistas "
        "efetivas (não as 2.002 da agenda), BR-00652/2026. P. 6: estimulada "
        "46,8/45,9/4,9/2,4. Cruzamentos por renda e sexo na p. 7, conferidos "
        "visualmente; perfil p. 22: 42,4/36,0/20,6, NS/NR 1,0. "
        "A troca de renda afeta somente os 99% declarantes. O perfil não "
        "explicita etapa antes/depois dos pesos; sensibilidade condicional "
        "ao perfil publicado, não uma margem ponderada comprovada. A p. 2 "
        "declara ponderação socioeconômica e pelo voto declarado no 1º turno "
        "de 2026 entre quem declarou comparecimento, inclusive brancos/nulos. "
        "Isso não identifica a participação futura nem o voto dos ausentes."
    )
    poll = base(
        "MDA",
        "BR-00652/2026",
        "2026-10-13",
        "2026-10-15",
        2014,
        "presencial, domiciliar e pontos de fluxo, 140 municípios",
        {
            "metodologia": 2,
            "2t_topline": 6,
            "2t_renda": 7,
            "sexo": 7,
            "perfil_renda": 22,
        },
        39,
        [46.8, 45.9, 4.9, 2.4],
        note,
    )
    poll["contratante"] = "Confederação Nacional do Transporte (CNT)"
    poll["publicado_validos"] = {"2t": {"flavio": 50.5, "lula": 49.5}}
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [42.4, 36, 20.6],
        [[37, 56, 5, 3], [51, 41, 5, 2], [61, 34, 4, 1]],
        [[52, 42, 4, 2], [42, 50, 5, 3]],
        [47.2, 52.8],
        note,
        99,
    )
    poll["renda"]["perfil_tipo"] = "perfil_publicado"
    poll["metodologia_onda"] = {"ponderacao_voto_1t_2026": True, "pagina": 2}
    return poll


def futura():
    note = (
        "Íntegra atual de 18 páginas, BR-03764/2026. Ficha técnica p. 4 "
        "informa campo 14–15/10; capa p. 1 diz 13–15/10, divergência preservada. "
        "Adotado 14–15/10, confirmado pela divulgação. Estimulada p. 10: "
        "49/47,5/1,5/2,1, soma 100,1 por arredondamento; válidos p. 12: "
        "50,8/49,2. Há perfil de renda p. 7, mas o cruzamento p. 11 contém "
        "somente sexo, região e idade: não há voto por renda. Entra pelo "
        "publicado somente na Projeção. P. 5 declara substituição da referência "
        "de escolaridade TSE pela PNAD Contínua/IBGE, mas a mesma nota já "
        "constava na p. 5 do relatório de 13/10. Não é evidência de nova mudança "
        "de escolaridade entre essas duas ondas."
    )
    poll = base(
        "Futura",
        "BR-03764/2026",
        "2026-10-14",
        "2026-10-15",
        2000,
        "telefônico CATI, eleitores de 16 anos ou mais",
        {
            "metodologia": "4–5",
            "perfil_renda": 7,
            "2t_topline": 10,
            "sexo": 11,
            "2t_validos": 12,
        },
        18,
        [49, 47.5, 1.5, 2.1],
        note,
    )
    poll.update(
        publicado_validos={"2t": {"flavio": 50.8, "lula": 49.2}},
        ignorar=True,
        motivo="Íntegra atual sem voto por renda; perfil sozinho não permite ajuste PNAD. Publicado na Projeção. Nota de escolaridade PNAD já presente em 13/10.",
        cruzamentos={},
        perfil_economico_publicado={
            "unidade": "renda familiar em salários mínimos",
            "faixas": ["Até 1", "1 a 2", "2 a 5", "5 a 10", "Mais de 10"],
            "pct": [27.3, 22.1, 23.7, 10, 6.3],
            "ns_nr": 10.6,
            "pagina": 7,
        },
        metodologia_onda={
            "escolaridade_anterior": "TSE",
            "escolaridade_atual": "PNAD Contínua/IBGE",
            "nota_ja_presente_em": "2026-10-13",
            "nova_mudanca_escolaridade_identificada": False,
            "pagina": 5,
        },
        divergencia_campo={
            "capa": "13–15/10",
            "ficha_tecnica": "14–15/10",
            "criterio": "Ficha técnica p. 4 e divulgação concordantes",
        },
    )
    previous = COMMON.source(COMMON.archive("futura_102026_13"), "relatorio.pdf")
    poll["fonte"]["complementos"] = [
        {
            **previous,
            "rotulo": "Futura de 13/10: mesma nota de escolaridade na p. 5",
        }
    ]
    poll["controles"] = {
        "2t": {
            "sexo": PREVIOUS.control(
                poll["publicado"]["2t"],
                [[57.5, 39.9, 1.1, 1.4], [40.8, 54.7, 1.8, 2.7]],
                [47.2, 52.9],
            )
        }
    }
    return poll


def main():
    polls = [gerp(), poderdata(), mda(), futura()]
    revision = importlib.import_module("datafolha-151026-renda").datafolha()
    for poll in [*polls, revision]:
        COMMON.write(
            ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
        )
    inventory = {
        "data": DAY,
        "pesquisas": polls,
        "revisoes": [revision],
        "fontes": {
            f"{name}_102026_16": COMMON.archive(f"{name}_102026_16")
            for name in ["gerp", "poderdata", "mda", "futura", "varredura"]
        },
        "varredura": [
            {
                "instituto": "Futura",
                "status": "Nova onda incluída pelo publicado",
                "conclusao": "Relatório atual sem voto por renda. Não reutilizar os dados da onda de 13/10. A nota sobre escolaridade PNAD já aparecia na íntegra anterior; não prova nova mudança entre essas ondas.",
                "fontes": [polls[3]["fonte"]["url"]],
                "pendente": True,
            },
            {
                "instituto": "Veritá",
                "status": "Sem novo resultado nacional confirmado nesta conferência",
                "conclusao": "Agenda ou registro não são resultado. Não foi incorporada uma nova onda sem divulgação verificável.",
                "fontes": ["https://institutoverita.com.br/"],
                "resumo": True,
            },
            {
                "instituto": "Datafolha",
                "status": "Pendência resolvida: íntegra oficial de 42 páginas",
                "conclusao": revision["fonte"]["nota"],
                "fontes": [revision["fonte"]["url"]],
                "pendente": False,
            },
            {
                "instituto": "Indexa",
                "status": "Pendência de pesos de renda mantida",
                "conclusao": "Continua pelo publicado: pesos de renda não localizados.",
                "fontes": [
                    "https://brasil.arvor.co/reponderacao_pnad.html#rodada-1510"
                ],
                "pendente": True,
            },
        ],
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261016.json", inventory)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261016.json", inventory)
    print("Integradas: " + ", ".join(p["id"] for p in polls))


if __name__ == "__main__":
    main()
