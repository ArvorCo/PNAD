#!/usr/bin/env python3
"""Quaest e Atlas de 24/10: preservar total, válido oficial e universo do modelo."""

import importlib
import shutil
from copy import deepcopy
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
EVENING = importlib.import_module("pesquisas-241026-noite-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-24"


def quaest():
    refs = COMMON.archive("quaest_102026_24")
    note = (
        "G1 publica amostra completa 46/45/8/1 (F/L/BN/I) e válidos oficiais "
        "51/49 pelo modelo de eleitor provável. Os 8% reúnem branco, nulo e não "
        "vai votar; não identificam abstenção. Campo 23–24/10, n=3.702. "
        "Voto por renda atual disponível na API, mas perfil atual e cruzamentos "
        "do likely voter não localizados. Não transportar perfil de 21/10. "
        "O publicado oficial em válidos entra na Projeção sem novo ajuste de "
        "presença. O total permanece documental; são dois resultados da mesma "
        "onda, nunca duas casas. Sem microdados ou pesos do modelo, o efeito "
        "exato da seleção não é recuperável dos números arredondados."
    )
    p = EVENING.base(
        "quaest",
        "Quaest",
        "BR-09158/2026",
        "23",
        "24",
        3702,
        "presencial domiciliar; válido oficial por modelo de eleitor provável",
        [46, 45, 8, 1],
        note,
    )
    p["contratante"] = "TV Globo e O Globo"
    p["fonte"] = {
        **COMMON.source(refs, "g1-estimulada.json"),
        "tipo": "painel",
        "rotulo": "G1, Quaest de 24/10",
        "conferido_em": DAY,
        "nota": note,
        "status": "Totais e válidos oficiais conferidos; íntegra pendente.",
        "complementos": [
            {**COMMON.source(refs, name), "rotulo": label}
            for name, label in [
                ("g1-validos.json", "G1: votos válidos oficiais"),
                ("g1-painel.html.gz", "G1: ficha técnica"),
                (
                    "divulgacao.html.gz",
                    "Rede 98: divulgação e metodologia likely voter",
                ),
            ]
        ],
    }
    p["publicado_validos"] = {"2t": {"flavio": 51, "lula": 49}}
    p["eleitor_provavel_oficial"] = {
        "usar_na_projecao": True,
        "validos": {"flavio": 51, "lula": 49},
        "fonte": COMMON.source(refs, "g1-validos.json"),
        "regra": "Publicado oficial da casa; sem reaplicar presença Arvor, renda ou indecisos da amostra completa.",
    }
    p["cruzamentos_sem_perfil"] = {
        "universo": "Amostra completa, não eleitor provável",
        "opcoes": ["flavio", "lula", "branco_nulo", "indecisos"],
        "renda": {
            "rotulos": ["Até 2 SM", "Mais de 2 a 5 SM", "Mais de 5 SM"],
            "linhas": [[32, 58, 9, 1], [49, 42, 8, 1], [57, 36, 6, 1]],
        },
        "sexo": {
            "rotulos": ["Masculino", "Feminino"],
            "linhas": [[51, 41, 7, 1], [41, 49, 9, 1]],
        },
    }
    p.update(
        ignorar=True,
        cruzamentos={},
        motivo="Perfil atual de renda e cruzamentos likely voter ausentes; sem PNAD nesta onda.",
    )
    return p


def atlas():
    note = (
        "Íntegra de 18 páginas, n=4.990, campo 18–23/10, BR-06380/2026. "
        "Total 49,9/48,4/1,7, com branco/nulo/não sei agregado, sem indecisos "
        "separáveis. Válidos oficiais 50,8/49,2 na p. 8. Perfil familiar atual "
        "19,4/11,5/26/26,7/16,4 na p. 5; cruzamentos p. 9. Etapa pré/pós-pesos "
        "não explicitada: sensibilidade PNAD condicional ao perfil publicado. "
        "Cortes em R$ 2/3/5/10 mil; p. 4 declara pós-estratificação por "
        "comportamento eleitoral anterior sem identificar a eleição usada."
    )
    p = EVENING.base(
        "atlas",
        "AtlasIntel",
        "BR-06380/2026",
        "18",
        "23",
        4990,
        "recrutamento digital aleatório Atlas RDR; pós-estratificação",
        [49.9, 48.4, 1.7, 0],
        note,
        {
            "metodologia": 4,
            "perfil_renda": 5,
            "2t_topline": 7,
            "2t_validos": 8,
            "2t_renda": 9,
            "sexo": 9,
        },
        18,
    )
    del p["publicado"]["2t"]["indecisos"]
    p["contratante"] = "Bloomberg"
    p["publicado_validos"] = {"2t": {"flavio": 50.8, "lula": 49.2}}
    old = COMMON.read(ROOT / "analysis/reponderacao/pesquisas/atlas_2026-10-18.json")
    weights = [19.4, 11.5, 26, 26.7, 16.4]
    rows = [
        [45.9, 52.7, 1.4],
        [51.4, 45.8, 2.8],
        [51.6, 47, 1.4],
        [52, 46.7, 1.4],
        [47.6, 49.9, 2.5],
    ]
    options = ["flavio", "lula", "branco_nulo"]
    p["renda"] = {**deepcopy(old["renda"]), "amostra_pct": weights, "nota": note}
    p["cruzamentos"] = {"2t": {"opcoes": options, "linhas": rows, "nota": note}}
    p["controles"] = {
        "2t": {
            "renda": PREVIOUS.control(p["publicado"]["2t"], rows, weights, options),
            "sexo": PREVIOUS.control(
                p["publicado"]["2t"],
                [[58.9, 38.5, 2.6], [41.9, 57.1, 0.9]],
                [47.1, 52.9],
                options,
            ),
        }
    }
    return p


def main():
    polls = [quaest(), atlas()]
    for p in polls:
        COMMON.write(ROOT / "analysis/reponderacao/pesquisas" / (p["id"] + ".json"), p)
    shutil.copyfile(
        ROOT / "data/originals/atlas_102026_24/relatorio.pdf",
        ROOT / "docs/fontes/atlas_24102026.pdf",
    )
    audit = {
        "data": DAY,
        "pesquisas": polls,
        "busca": "Quaest confirmada às 19h; Atlas nacional às 19h30. Catálogos e buscas não confirmaram outra nacional nova de Futura, Veritá, Phoenix ou Simplex neste corte. Agenda não equivale a divulgação.",
        "regra": "Uma onda por casa. Quaest: provável oficial na Projeção, amostra completa no histórico; sem transportar pesos de renda ou aplicar presença novamente. Atlas: PNAD com perfil atual.",
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261024_final.json", audit)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261024_final.json", audit)
    path = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
    presence = COMMON.read(path)
    houses = {p["instituto"] for p in polls}
    presence["auditoria_ultima_onda"] = [
        p for p in presence["auditoria_ultima_onda"] if p["instituto"] not in houses
    ] + [
        {
            "instituto": p["instituto"],
            "id": p["id"],
            "tipo": "oficial" if p.get("eleitor_provavel_oficial") else "neutro",
            "fonte": p["fonte"]["url"],
            "arquivo": p["fonte"]["arquivo"],
            "nota": p.get("eleitor_provavel_oficial", {}).get(
                "regra",
                "Sem cruzamento de presença incorporado nesta onda; não transportar taxas anteriores.",
            ),
        }
        for p in polls
    ]
    COMMON.write(path, presence)


if __name__ == "__main__":
    main()
