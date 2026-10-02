#!/usr/bin/env python3
"""Extrai o anexo completo e integra a onda de 24/09 à régua PNAD."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "docs/fontes/datafolha_28092026.pdf"
OUT = ROOT / "analysis/reponderacao/datafolha_20260923_cruzamentos.json"
PAGES = {
    "espontanea": [34, 35],
    "estimulada": [36, 37, 38],
    "validos": [39, 40],
    "numero_urna": [41],
    "rejeicao": [42, 43, 44],
    "turno2_flavio": [45],
    "turno2_caiado": [46],
    "turno2_zema": [47],
    "turno2_renan": [48],
    "turno2_cury": [49],
    "definicao": [50],
    "segunda_opcao": [51, 52, 53],
    "avaliacao": [54],
    "aprovacao": [55],
}


def main():
    spec = importlib.util.spec_from_file_location(
        "extract_datafolha", ROOT / "scripts/datafolha-21092026-extract.py"
    )
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    parser.PAGES = PAGES
    tables = parser.extract(PDF)
    for table in tables.values():
        for block in table["blocks"].values():
            block["annex_page"] = block["pdf_page"] - 27
    out = {
        "fonte": {
            "pdf": str(PDF.relative_to(ROOT)),
            "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
            "paginas": 55,
            "registro": "BR-00304/2026",
            "metodo": "Extração automática de todas as 14 tabelas do anexo.",
        },
        "tabelas": tables,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    path = ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-09-23.json"
    poll = json.loads(path.read_text())
    previous = json.loads((path.parent / "datafolha_2026-09-17.json").read_text())
    poll.pop("ignorar", None)
    poll.pop("motivo", None)
    poll["metodo"] = "presencial, pontos de fluxo"
    poll["fonte"] = {
        "tipo": "relatorio",
        "pdf": str(PDF.relative_to(ROOT)),
        "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "bytes": PDF.stat().st_size,
        "total_paginas": 55,
        "url": "https://brasil.arvor.co/fontes/datafolha_28092026.pdf",
        "relatorio_completo": "2026-09-28",
        "conferido_em": "2026-10-01",
        "paginas": {"perfil_renda": 32, "1t_renda": 37, "2t_renda": 45},
        "nota": "Íntegra de 55 páginas, gerada em 28/09, fornecida em Downloads. "
        "Campo 22–23/09; divulgação 24/09. Extração integral do anexo arquivada.",
    }
    poll["renda"] = previous["renda"]
    cols = ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"]
    first = tables["estimulada"]["blocks"]["bloco2"]
    second = tables["turno2_flavio"]["blocks"]["bloco2"]
    assert first["base"] == second["base"]
    poll["renda"]["bases"] = [first["base"][c] for c in cols]
    missing = poll["n"] - sum(poll["renda"]["bases"])
    poll["renda"]["nota"] = (
        f"Bases ponderadas da intenção de voto, pp. 37 e 45. "
        f'Somam {sum(poll["renda"]["bases"])}; {missing} casos não aparecem no '
        "cruzamento de renda. Normalização entre renda declarada e delta ancorado "
        "no placar nacional; não identifica o voto dos casos sem renda publicada."
    )
    names = [
        "lula",
        "flavio",
        "cury",
        "caiado",
        "renan_santos",
        "zema",
        "samara",
        "edmilson",
        "rui",
        "grassi",
        "avalanche",
        "clariana",
        "hertz",
        "branco_nulo",
        "indecisos",
    ]
    for turno, key, options in [
        ("1t", "estimulada", names),
        ("2t", "turno2_flavio", ["lula", "flavio", "branco_nulo", "indecisos"]),
    ]:
        blocks = tables[key]["blocks"]
        rows = list(blocks["bloco2"]["rows"].values())
        assert len(rows) == len(options)
        poll["publicado"][turno] = dict(
            zip(options, [r["Total"] for r in rows], strict=True)
        )
        poll["cruzamentos"][turno] = {
            "opcoes": options,
            "linhas": [[r[c] if r[c] is not None else 0 for r in rows] for c in cols],
            "nota": "Extração automática do texto nativo. Traço convertido em zero "
            "apenas na conta; inteiros preservados sem normalização.",
        }
        for b in ["bloco1", "bloco3"]:
            block = blocks[b]
            weights = (
                [block["base"][c] for c in block["columns"][1:3]]
                if b == "bloco1"
                else [block["base"][c] for c in block["columns"][1:5]]
            )
            columns = block["columns"][1:3] if b == "bloco1" else block["columns"][1:5]
            for label, row in list(block["rows"].items())[:2]:
                value = sum(
                    row[c] * w for c, w in zip(columns, weights, strict=True)
                ) / sum(weights)
                assert abs(value - row["Total"]) < 1, (turno, b, label, value)
                print(turno, b, label, round(value, 3), "publicado", row["Total"])
    path.write_text(json.dumps(poll, ensure_ascii=False, indent=2) + "\n")
    print("Bases:", poll["renda"]["bases"], "sem renda:", missing)


if __name__ == "__main__":
    main()
