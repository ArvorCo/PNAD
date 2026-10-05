#!/usr/bin/env python3
"""Extrato estratégico de data/boletins/final.json para o roteiro do boletim.

Uso: python3 scripts/boletim-bancadas.py > data/boletins/bancadas-HHMM.json
Resume Câmara, Senado de 2027, assembleias e governadores por espectro e por partido,
sem listas longas, para caber no prompt do roteirista.
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FINAL = RAIZ / "data" / "boletins" / "final.json"


def top_partidos(d: dict, n: int = 8) -> dict:
    itens = sorted(d.items(), key=lambda kv: -kv[1])[:n]
    return dict(itens)


def main() -> None:
    f = json.loads(FINAL.read_text(encoding="utf-8"))
    c = f["camara"]
    s = f["senado"]["senado_2027"]
    g = f["governadores"]
    p = f["presidente"]
    pares = g.get("segundo_turno_pares")
    assembleias = [
        {
            "uf": a["uf"],
            "casa": a["casa"],
            "fonte": a["fonte"],
            "vagas": a["vagas"],
            "por_campo": a["por_campo"],
            "blocos": a["blocos"],
            "partidos": top_partidos(a["por_partido"], 6),
        }
        for a in f["assembleias"]
    ]
    saida = {
        "gerado_em": f.get("gerado_em"),
        "presidente": {
            k: p[k]
            for k in p
            if k
            in (
                "pst",
                "segundo_turno",
                "par_2t",
                "diferenca_pp",
                "diferenca_votos",
                "top5",
                "venceu_em",
                "maiores_margens",
                "exterior",
                "pct_comparecimento",
                "pct_brancos",
                "pct_nulos",
            )
        },
        "camara": {
            "vagas": c["vagas_total"],
            "ufs_fechadas_pelo_tse": c["n_ufs_tse"],
            "ufs_provisorias": c["n_ufs_provisorio"],
            "por_campo": c["por_campo"],
            "blocos": c["blocos"],
            "partidos": top_partidos(c["por_partido"], 10),
            "votos_por_campo_pct": c.get("votos_por_campo_pct"),
            "nota": "cadeiras pelo TSE onde a UF já fechou; nas demais, alocação provisória pelo quociente eleitoral, que bateu nome a nome com o TSE nas UFs já fechadas",
        },
        "senado_2027": {
            "total": s["total"],
            "continuam": s["continuam"],
            "novos": s["novos"],
            "por_campo": s["por_campo"],
            "por_bloco": s["por_bloco"],
            "partidos": top_partidos(s["por_partido"], 8),
        },
        "assembleias": assembleias,
        "governadores": {
            "eleitos_1t": g["n_eleitos_1t"],
            "segundo_turno": g["n_segundo_turno"],
            "eleitos_1t_por_campo": g["eleitos_1t_por_campo"],
            "segundo_turno_candidatos_por_campo": g[
                "segundo_turno_candidatos_por_campo"
            ],
            "pares_segundo_turno": pares,
            "ufs": [
                {
                    "uf": u["uf"],
                    "decisao": u["decisao"],
                    "fonte": u["fonte"],
                    "candidatos": [
                        f"{c['nome']} ({c['partido']}, {c['campo']}) {c['pct']}%"
                        for c in u["candidatos"][:2]
                    ],
                }
                for u in g["ufs"]
            ],
        },
    }
    print(json.dumps(saida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
