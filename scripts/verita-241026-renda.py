#!/usr/bin/env python3
"""Veritá final: sensibilidade PNAD com hipótese explícita de perfil condicional."""

import importlib
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
INCOME = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]


def poll():
    refs = COMMON.archive("verita_102026_24")
    p = COMMON.read(ROOT / "analysis/reponderacao/pesquisas/verita_2026-10-22.json")
    p.update(
        id="verita_2026-10-23",
        registro_tse="BR-03181/2026",
        campo={"inicio": "2026-10-19", "fim": "2026-10-23"},
        divulgacao="2026-10-24",
        publicado={
            "2t": {
                "flavio": 49.44,
                "lula": 46.46,
                "branco_nulo": 1.43,
                "indecisos": 2.67,
            }
        },
        publicado_validos={"2t": {"flavio": 51.56, "lula": 48.44}},
    )
    p["fonte"] = {
        **COMMON.source(refs, "relatorio.pdf"),
        "url_publica": "https://brasil.arvor.co/fontes/verita_24102026.pdf",
        "pagina_oficial": COMMON.read(
            ROOT / "data/originals/verita_102026_24/fonte.json"
        )["pagina_oficial"],
        "pdf": "data/originals/verita_102026_24/relatorio.pdf",
        "tipo": "relatorio",
        "rotulo": "Veritá: relatório oficial de 24/10",
        "total_paginas": 13,
        "paginas": {
            "metodologia": 3,
            "perfil_renda": 4,
            "presenca": 5,
            "2t_topline": 9,
            "2t_validos": 9,
            "2t_renda": 10,
            "sexo": 10,
        },
        "conferido_em": "2026-10-24",
        "status": "Íntegra conferida; PNAD com hipótese de perfil condicional entre declarantes.",
        "nota": (
            "Publicação oficial de 24/10, 13 páginas, BR-03181/2026, campo 19–23/10, "
            "n=15.554 em 905 municípios, URA. Totais F/L/BN/NS na p. 9: "
            "49,44/46,46/1,43/2,67; válidos oficiais 51,56/48,44. "
            "Perfil familiar p. 4: 40,4/40,9/18,7 e frequências 6.283/6.362/2.909 "
            "já somam 100% e 15.554. NS/NR adicional 1,7% e 260 gera 101,7% "
            "e 15.814, incompatível com a amostra. Por solicitação do usuário, "
            "a sensibilidade assume 40,4/40,9/18,7 como composição entre declarantes "
            "e parcela ajustável (15.554−260)/15.554 = 98,33%. Os sem renda "
            "conservam o publicado no ajuste por delta. É hipótese de reconciliação, "
            "não perfil identificado nem contagem corrigida pelo instituto. "
            "Cruzamentos atuais p. 10 entram nas duas centrais e nos gráficos. "
            "'Ausente' na tabela de voto reúne BN+NS (4,10%), não abstenção. "
            "Certeza declarada de votar 97,51% (p. 5) não é comparecimento calibrado "
            "nem modelo de eleitor provável. Expectativa de vitória p. 11 não é voto."
        ),
    }
    p["perfil_economico_publicado"].update(
        percentuais=[40.4, 40.9, 18.7, 1.7], frequencias=[6283, 6362, 2909, 260]
    )
    p["cruzamentos_diagnosticos"].update(
        pagina=10,
        linhas=[
            [43.5, 52.0, 1.6, 2.9],
            [53.5, 42.6, 1.4, 2.5],
            [53.5, 43.0, 0.9, 2.6],
            [44.1, 44.4, 1.9, 9.6],
        ],
    )
    p["controle_leitura_sexo"] = INCOME.control(
        p["publicado"]["2t"],
        [[57.4, 38.2, 1.6, 2.8], [42.4, 53.8, 1.3, 2.5]],
        [47.2, 52.8],
    )
    p.pop("motivo", None)
    p.pop("ignorar", None)
    INCOME.income(
        p,
        [2, 5, None],
        [40.4, 40.9, 18.7],
        p["cruzamentos_diagnosticos"]["linhas"][:3],
        [[57.4, 38.2, 1.6, 2.8], [42.4, 53.8, 1.3, 2.5]],
        [47.2, 52.8],
        p["fonte"]["nota"],
        fraction=100 * (15554 - 260) / 15554,
    )
    p["renda"]["perfil_tipo"] = "hipotese_perfil_condicional"
    p["renda"]["ns_nr_frequencia_publicada"] = 260
    p["renda"]["nota"] += " A etapa pré/pós-ponderação do perfil não está explicitada."
    return p


def main():
    p = poll()
    COMMON.write(ROOT / f"analysis/reponderacao/pesquisas/{p['id']}.json", p)
    audit = {
        "data": "2026-10-24",
        "consultado_em": COMMON.read(
            ROOT / "data/originals/verita_102026_24/fonte.json"
        )["consultado_em"],
        "pesquisas": [p],
        "regra": "Substitui a onda Veritá de 23/10 na Projeção e volta à Média, sem duplicar a casa. PNAD sob hipótese explícita de composição condicional e parcela ajustável de 98,33%, solicitada pelo usuário; não é reconciliação confirmada pelo instituto. Presença declarada não altera o motor; Quaest conserva o likely voter oficial sem reaplicar presença.",
    }
    for rel in [
        "analysis/reponderacao/auditoria_verita_20261024.json",
        "docs/assets/reponderacao_verita_20261024.json",
    ]:
        COMMON.write(ROOT / rel, audit)
    path = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
    presence = COMMON.read(path)
    presence["auditoria_ultima_onda"] = [
        r for r in presence["auditoria_ultima_onda"] if r["instituto"] != "Veritá"
    ] + [
        {
            "instituto": "Veritá",
            "id": p["id"],
            "tipo": "neutro",
            "fonte": p["fonte"]["url"],
            "arquivo": p["fonte"]["arquivo"],
            "nota": "P. 5: 97,51% têm certeza de votar, 1,56% talvez e 0,93% certeza de não votar. Autodeclaração, sem cruzamento por candidato; não é likely voter nem substitui comparecimento Arvor.",
        }
    ]
    COMMON.write(path, presence)


if __name__ == "__main__":
    main()
