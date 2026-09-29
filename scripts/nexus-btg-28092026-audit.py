#!/usr/bin/env python3
"""Extract round 16 and audit income, measured migration and turnout scenarios."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "analysis/nexus_btg_28092026"
PDF = ROOT / "docs/fontes/nexus_btg_28092026.pdf"
OUT = ROOT / "docs/assets/nexus_btg_28092026_data.json"
FIRST = [
    "lula",
    "flavio",
    "cury",
    "caiado",
    "renan_santos",
    "zema",
    "outros",
    "branco_nulo",
    "indecisos",
]
SECOND = ["lula", "flavio", "branco_nulo", "indecisos"]
LABELS = {
    "renda": ["Até 1 S.M.", "De 1 até 2 S.M.", "De 2 até 5 S.M.", "Mais de 5 S.M."],
    "idade": ["16 a 24 anos", "25 a 40 anos", "41 a 59 anos", "60 anos ou mais"],
    "regiao": ["Norte/Centro-Oeste", "Nordeste", "Sudeste", "Sul"],
    "sexo": ["Feminino", "Masculino"],
    "escolaridade": ["Ensino Fundamental", "Ensino Médio", "Ensino Superior"],
}
# p. 84: text extraction alone does not locate unlabelled zero segments.
# Visually verified red/blue/black/grey order. Missing bars recorded as printed zero,
# not a structural impossibility or an exact population zero.
MEASURED = {
    2: [30, 38, 31, 0],
    3: [32, 32, 35, 1],
    4: [13, 43, 43, 0],
    5: [0, 66, 13, 20],
    6: [41, 36, 24, 0],
}
URL = "https://www.nexus.fsb.com.br/wp-content/uploads/2026/09/BTG-Nexus-Eleicoes-2026-Rodada-16-28.set_.2026.pdf"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def table(pages, page, labels, width):
    rows = []
    for label in labels:
        lines = [
            line
            for line in pages[page - 1].splitlines()
            if label in line and "%" in line
        ]
        if len(lines) != 1:
            raise ValueError((page, label, lines))
        vals = [int(x) for x in re.findall(r"(\d+)%", lines[0])]
        if len(vals) != width:
            raise ValueError((page, label, vals))
        rows.append(vals)
    return rows


def profile(pages, labels):
    # p. 142 uses two layout columns: match percentage immediately after the label.
    return [int(re.search(re.escape(s) + r"\s+(\d+)%", pages[141])[1]) for s in labels]


def transfer(retention=0.98, neutral=False):
    rows = np.array([42, 37, 5, 5, 4, 1, 1, 3, 2], float)
    cols = np.array([46, 44, 8, 1], float)
    # Printed runoff totals 99; scale origins to 99, as house convention requires.
    rows *= cols.sum() / rows.sum()
    matrix = np.zeros((9, 4))
    for i, vals in MEASURED.items():
        matrix[i] = rows[i] * np.array(vals) / sum(vals)
    # Retention is a modelling parameter, separate from measured minor-candidate rows.
    matrix[0, 0], matrix[1, 1] = rows[0] * retention, rows[1] * retention
    remrows = rows[[0, 1, 7, 8]] - matrix[[0, 1, 7, 8]].sum(1)
    remcols = cols - matrix.sum(0)
    if remrows[:2].sum() > remcols[2:].sum() + 1e-9:
        raise ValueError("Base leakage exceeds nonchoice capacity with zero crossover")
    if min(remcols) < -1e-9:
        raise ValueError("Retention assumption infeasible with measured rows")
    prior = np.array([[0, 0, 9, 1], [0, 0, 9, 1], [2, 2, 5, 1], [3, 3, 2, 2]], float)
    if neutral:
        prior[2:] = 1
    active = remrows > 1e-12
    sub = prior[active].copy()
    for _iteration in range(20000):
        sub *= remcols / sub.sum(0)
        sub *= (remrows[active] / sub.sum(1))[:, None]
        if max(abs(sub.sum(0) - remcols)) < 1e-10:
            break
    else:
        raise ValueError("IPF convergence failed")
    matrix[np.array([0, 1, 7, 8])[active]] += sub
    assert np.allclose(matrix.sum(0), cols) and np.allclose(matrix.sum(1), rows)
    return {
        "sources": [
            "Lula",
            "Flávio",
            "Cury",
            "Caiado",
            "Renan",
            "Zema",
            "Outros*",
            "B/N",
            "NS/NR",
        ],
        "destinations": ["Lula", "Flávio", "B/N", "NS/NR"],
        "matrix": matrix.tolist(),
        "row_targets": rows.tolist(),
        "column_targets": cols.tolist(),
        "measured_rows": list(MEASURED),
        "estimated_rows": [0, 1, 7, 8],
        "consolidated_rows": [],
        "retention": retention,
        "iterations": _iteration + 1,
        "conditional_printed": MEASURED,
        "pool_points": matrix[2:7].sum(0).tolist(),
        "net_published": {"lula": 4, "flavio": 7, "ratio": 1.75},
        "net_common_scale": {
            "lula": float(cols[0] - rows[0]),
            "flavio": float(cols[1] - rows[1]),
            "ratio": float((cols[1] - rows[1]) / (cols[0] - rows[0])),
        },
    }


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftotext", "-layout", str(PDF), str(WORK / "relatorio.txt")], check=True
    )
    pages = (WORK / "relatorio.txt").read_text().split("\f")
    pages = [p for p in pages if p.strip()]
    assert len(pages) == 145 and "BR-07557/2026" in pages[3]
    appendix = [
        {
            "page": i + 1,
            "text": p,
            "percentage_rows": [
                {
                    "line": line.strip(),
                    "values": [int(x) for x in re.findall(r"(\d+)%", line)],
                }
                for line in p.splitlines()
                if re.search(r"\d+%", line)
            ],
        }
        for i, p in enumerate(pages)
    ]
    save(WORK / "paginas.json", appendix)
    profiles = {key: profile(pages, names) for key, names in LABELS.items()}
    tables = {}
    for key, names in LABELS.items():
        left = key in ("idade", "sexo", "escolaridade")
        tables[key] = {
            "labels": names,
            "weights": profiles[key],
            "1t": table(pages, 36 if left else 37, names, 9),
            "2t": table(pages, 85 if left else 86, names, 4),
            "turnout": table(pages, 15 if left else 16, names, 5),
            "pages": [36 if left else 37, 85 if left else 86, 15 if left else 16, 142],
        }
    eng = module("reponderacao-pnad")
    poll = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/nexus_2026-09-20.json").read_text()
    )
    poll.update(
        id="nexus_2026-09-27",
        registro_tse="BR-07557/2026",
        campo={"inicio": "2026-09-25", "fim": "2026-09-27"},
        divulgacao="2026-09-28",
        n=2000,
        dossie="nexus_btg_28092026.html",
        notas="16ª rodada; 145 páginas. Extração integral; controle por cinco partições.",
    )
    poll["fonte"] = {
        "pdf": str(PDF.relative_to(ROOT)),
        "url": URL,
        "tipo": "relatorio",
        "paginas": {
            "metodologia": 4,
            "perfil_renda": 142,
            "1t_renda": 37,
            "2t_renda": 86,
        },
    }
    poll["renda"]["amostra_pct"] = profiles["renda"]
    poll["renda"]["nota"] = (
        "Perfil publicado p. 142; PNADC anual 2025, visita 1, declarada na p. 4. "
        "O registro atual prevê ponderação por renda, sem alvos numéricos ou diagnóstico dos pesos. "
        "Cortes de 2026 conferidos visualmente na PF15, p. 13 do questionário atual no PesqEle: R$ 1.621, 3.242, 4.863 e 8.105; renda familiar do mês passado. Exportação do questionário indisponível nesta sessão. "
        "Renda familiar declarada e renda domiciliar PNAD, pessoas 16+ e eleitores titulados, não são universos idênticos."
    )
    for ballot, opts, page in [("1t", FIRST, 37), ("2t", SECOND, 86)]:
        total = table(pages, page, ["TOTAL"], len(opts))[0]
        poll["publicado"][ballot] = dict(zip(opts, total, strict=True))
        poll["cruzamentos"][ballot] = {
            "opcoes": opts,
            "linhas": tables["renda"][ballot],
            "nota": f"Extração programática da p. {page}; conferência visual.",
        }
    save(ROOT / "analysis/reponderacao/pesquisas/nexus_2026-09-27.json", poll)
    reweight = eng.process_poll(poll, eng.Benchmark(), eng.load_ipca())
    controls = {}
    for key, t in tables.items():
        controls[key] = {}
        for ballot, opts in [("1t", FIRST), ("2t", SECOND)]:
            vals = eng.compose(t[ballot], t["weights"])
            residual = max(
                abs(vals[j] - poll["publicado"][ballot][opt])
                for j, opt in enumerate(opts)
            )
            assert residual < 1.1, (key, ballot, residual)
            controls[key][ballot] = {
                "recomposed": dict(zip(opts, vals, strict=True)),
                "max_residual": residual,
            }
    transfers = [transfer(r) for r in [0.97, 0.98, 1.0]]
    lv = module("nexus-btg-28092026-turnout").analyse(poll, reweight, tables)
    history = [
        json.loads(p.read_text())
        for p in sorted((ROOT / "analysis/reponderacao/pesquisas").glob("nexus_*.json"))
    ]
    data = {
        "poll": poll,
        "reweight": reweight,
        "tables": tables,
        "controls": controls,
        "transfer": transfers[1],
        "transfer_sensitivity": [*transfers, transfer(0.98, True)],
        "turnout": lv,
        "history": [
            {"date": p["divulgacao"], "publicado": p["publicado"]} for p in history
        ],
        "source": {
            "url": URL,
            "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
            "bytes": PDF.stat().st_size,
            "pages": len(pages),
            "read_at": "2026-09-28",
        },
        "precision": {
            "aas_max_moe": 1.96 * 100 * (0.25 / 2000) ** 0.5,
            "gap_moe": eng.difference_margin(46, 44, 2000),
        },
    }
    save(OUT, data)
    print(
        "Income adjusted:",
        reweight["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]["ajustado"],
    )
    print("LV:", {b: v["valid"][:2] for b, v in lv["central"].items()})
    print("Saved", OUT)


if __name__ == "__main__":
    main()
