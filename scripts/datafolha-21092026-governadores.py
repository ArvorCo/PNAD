#!/usr/bin/env python3
"""Compare Datafolha state offices; keep marginal disparities separate from errors."""

import importlib.util
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/pesquisas/datafolha/2026-09-10-governadores"
ASSETS = ROOT / "docs/assets"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EXTRACT = module("datafolha-21092026-extract")
EXTRACT.COLUMNS[3] = [
    "Total",
    "Regiao metropolitana",
    "Interior",
    "PT",
    "PL",
    "Outro partido",
    "Nao tem",
]
FLAT = module("datafolha-14092026-audit").flat
PAGES = {
    "SP": {
        "espontanea": [30],
        "estimulada": [31, 32],
        "validos": [33, 34],
        "rejeicao": [35, 36],
        "decisao": [37],
        "motivacao": [38],
        "turno2": [39],
        "senado_espontanea": [40, 41],
        "senado_1": [42, 43, 44],
        "senado_2": [45, 46, 47],
        "senado_total": [48, 49, 50],
        "avaliacao": [51],
        "aprovacao": [52],
    },
    "MG": {
        "espontanea": [31, 32],
        "estimulada": [33, 34],
        "validos": [35, 36],
        "rejeicao": [37, 38],
        "turno2_kalil": [39],
        "turno2": [40],
        "decisao": [41],
        "motivacao": [42],
        "senado_espontanea": [43, 44],
        "senado_1": [45, 46, 47],
        "senado_2": [48, 49, 50],
        "senado_total": [51, 52, 53],
        "avaliacao": [54],
        "aprovacao": [55],
    },
}


def extract(pdf, pages, offset):
    result = {}
    with fitz.open(pdf) as doc:
        for key, numbers in pages.items():
            blocks = {}
            for p in numbers:
                parts = re.split(r"Bloco ([123]) de 3,[^\n]*\n", doc[p - 1].get_text())
                for i in range(1, len(parts), 2):
                    n = int(parts[i])
                    b = EXTRACT.block(parts[i + 1], n, p)
                    b["annex_page"] = p - offset
                    assert f"bloco{n}" not in blocks
                    blocks[f"bloco{n}"] = b
            assert len(blocks) == 3, (key, blocks.keys())
            labels = [list(b["rows"]) for b in blocks.values()]
            assert all(x == labels[0] for x in labels)
            result[key] = {"blocks": blocks}
    return result


def overlap(a, b, rounding=0):
    return [max(0, a + b - 100 - 2 * rounding), min(100, a + rounding, b + rounding)]


def analyze(uf, tables, presidential):
    gov, gb = FLAT(tables["turno2"])
    pres, pb = FLAT(presidential["turno2"])
    assert gb == pb, (uf, gb, pb)
    names = list(gov)
    leader, rival = names[:2]
    lula = "Lula (PT)"
    flavio = "Flavio Bolsonaro (PL)"
    a, b, c, d = [
        gov[leader]["Total"],
        gov[rival]["Total"],
        pres[lula]["Total"],
        pres[flavio]["Total"],
    ]
    proofs = []
    flags = []
    dims = {
        "sexo": ["Masculino", "Feminino"],
        "natureza": ["Regiao metropolitana", "Interior"],
    }
    for key, tab in tables.items():
        rows, bases = FLAT(tab)
        for dim, groups in dims.items():
            total = sum(bases[k] for k in groups)
            for label, row in rows.items():
                val = sum(bases[k] * row[k] for k in groups) / total
                check = {
                    "table": key,
                    "dimension": dim,
                    "candidate": label,
                    "recomposed": val,
                    "published": row["Total"],
                    "residual": val - row["Total"],
                    "base_sum": total,
                    "n": bases["Total"],
                }
                proofs.append(check)
                # Two independent rounding errors can jointly account for ~1 pp.
                if abs(check["residual"]) > 1.05:
                    flags.append(check)
    pt_a, pt_b = gov[leader]["PT"], pres[lula]["PT"]
    first, _ = FLAT(tables["estimulada"])
    pres_first, _ = FLAT(presidential["estimulada"])
    result = {
        "uf": uf,
        "project": "PO4285" if uf == "SP" else "PO4287",
        "n": gb["Total"],
        "field": "08–10/09/2026",
        "leader": leader,
        "rival": rival,
        "governor": [a, b],
        "president": [c, d],
        "gap_governor_flavio": a - d,
        "gap_lula_rival": c - b,
        "overlap_topline": overlap(a, c),
        "overlap_topline_rounding": overlap(a, c, 0.5),
        "pt": {
            "base": gb["PT"],
            "governor": pt_a,
            "lula": pt_b,
            "overlap": overlap(pt_a, pt_b),
            "overlap_rounding": overlap(pt_a, pt_b, 0.5),
            "state_lower": overlap(pt_a, pt_b)[0] * gb["PT"] / gb["Total"],
            "state_lower_rounding": overlap(pt_a, pt_b, 0.5)[0]
            * gb["PT"]
            / gb["Total"],
        },
        "bases_equal": True,
        "base": gb,
        "proofs": proofs,
        "flags_over_1_05pp": flags,
        "first_governor": {k: v["Total"] for k, v in first.items()},
        "first_president": {k: v["Total"] for k, v in pres_first.items()},
        "pages": {
            "governor": PAGES[uf]["turno2"][0],
            "president": 58 if uf == "SP" else 94,
        },
        "assumptions": [
            "Registros, projeto, campo, n e bases ponderadas coincidem. Igualdade dos pesos individuais entre perguntas não é demonstrável sem os microdados.",
            "Limites de interseção condicionados ao mesmo universo e aos mesmos pesos finais. Não são cruzamentos observados nem intervalos populacionais.",
            "Arredondamento: ±0,5 ponto por proporção; bases ponderadas tratadas como exatas, embora publicadas como inteiros.",
            "PT é partido de preferência, não equivale a voto em Lula nem à escala bolsonarista/petista.",
        ],
    }
    if uf == "MG":
        alternative, _ = FLAT(tables["turno2_kalil"])
        result["kalil"] = {k: v["Total"] for k, v in alternative.items()}
    return result


def main():
    all_tables = {}
    results = []
    president = ROOT / "docs/fontes/datafolha_21092026_estaduais.pdf"
    for uf, offset in [("SP", 23), ("MG", 24)]:
        tables = extract(FOLDER / uf / "relatorio.pdf", PAGES[uf], offset)
        pres = extract(
            president,
            {
                "estimulada": [49, 50, 51] if uf == "SP" else [85, 86, 87],
                "turno2": [58] if uf == "SP" else [94],
            },
            42 if uf == "SP" else 78,
        )
        all_tables[uf] = {"governor": tables, "president": pres}
        result = analyze(uf, tables, pres)
        result["source"] = json.loads((FOLDER / uf / "proveniencia.json").read_text())
        (
            ROOT / "docs/fontes" / f"datafolha_21092026_governador_{uf.lower()}.pdf"
        ).write_bytes((FOLDER / uf / "relatorio.pdf").read_bytes())
        results.append(result)
    output = {
        "states": results,
        "tables": all_tables,
        "method": "Limites de Fréchet: max(0,a+b−100) ≤ interseção ≤ min(a,b). Comparações só com presidenciais estaduais do mesmo campo. Diferença entre cargos não é prova de erro.",
    }
    (ASSETS / "datafolha_21092026_governadores.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            [
                {
                    k: v
                    for k, v in r.items()
                    if k
                    not in [
                        "proofs",
                        "source",
                        "first_governor",
                        "first_president",
                        "base",
                    ]
                }
                for r in results
            ],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
