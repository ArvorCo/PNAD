#!/usr/bin/env python3
"""Reproducible income, history, coverage and transfer audit of BR-01833/2026."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import fitz
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/pesquisas/datafolha/2026-09-11"
ASSETS = ROOT / "docs/assets"
BANDS = ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"]
CEN = "pessoas16_efetivo"
KEYS = [
    "lula",
    "flavio",
    "cury",
    "caiado",
    "renan_santos",
    "zema",
    "samara",
    "rui",
    "clariana",
    "edmilson",
    "grassi",
    "hertz",
    "branco_nulo",
    "indecisos",
]


def module(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), ROOT / f"scripts/{name}.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def flat(table):
    rows = {}
    bases = {}
    for b in table["blocks"].values():
        bases.update(b["base"])
        for label, cols in b["rows"].items():
            rows.setdefault(label, {}).update({c: v or 0 for c, v in cols.items()})
    return rows, bases


def poll_record(tables):
    prev = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-09-02.json").read_text()
    )
    poll = {k: prev[k] for k in ["instituto", "contratante", "metodo"]}
    poll.update(
        id="datafolha_2026-09-10",
        registro_tse="BR-01833/2026",
        campo={"inicio": "2026-09-08", "fim": "2026-09-10"},
        divulgacao="2026-09-11",
        n=2002,
        dossie="datafolha_14092026.html",
    )
    poll["fonte"] = {
        "pdf": str((FOLDER / "relatorio.pdf").relative_to(ROOT)),
        "url": "https://brasil.arvor.co/fontes/datafolha_14092026.pdf",
        "paginas": {"perfil_renda": 32, "1t_renda": 42, "2t_renda": 49},
        "nota": "Relatório completo de 57 páginas recebido em 14/09; divulgação da pesquisa em 11/09 e campo em 8 a 10/09. Bases ponderadas extraídas do anexo, não cotas inferidas.",
    }
    rows, bases = flat(tables["turno2_flavio"])
    poll["renda"] = {
        "unidade": "salarios_minimos",
        "ano_referencia": 2026,
        "faixas": prev["renda"]["faixas"],
        "bases": [bases[c] for c in BANDS],
        "nota": "Bases ponderadas 991/689/234, idênticas nas tabelas de intenção de voto dos dois turnos (pp. 42 e 49). Somam 1.914; 88 das 2.002 entrevistas não aparecem nas faixas publicadas. Normalização entre renda declarada, mantendo o placar nacional como âncora. Perfil detalhado p. 32: recusa 2%, não sabe 3%, percentuais arredondados. A sensibilidade não identifica o voto dos sem renda declarada.",
    }
    poll["publicado"] = {}
    poll["cruzamentos"] = {}
    for turno, key, opts in [
        ("1t", "estimulada_b", KEYS),
        ("2t", "turno2_flavio", ["lula", "flavio", "branco_nulo", "indecisos"]),
    ]:
        rows, bases = flat(tables[key])
        assert len(rows) == len(opts)
        poll["publicado"][turno] = {
            k: r["Total"] for k, r in zip(opts, rows.values(), strict=True)
        }
        poll["cruzamentos"][turno] = {
            "opcoes": opts,
            "linhas": [[r[c] for r in rows.values()] for c in BANDS],
            "nota": f"Texto nativo, {key}; traço convertido em zero. Linhas mantidas como publicadas, sem normalizar os votos arredondados. Situação B sem Marçal no 1º turno.",
        }
    return poll


def ras(prior, rows, columns):
    x = np.array(prior, dtype=float)
    for _ in range(10000):
        x *= np.array(rows)[:, None] / x.sum(axis=1)[:, None]
        x *= np.array(columns)[None, :] / x.sum(axis=0)[None, :]
        if max(np.abs(x.sum(axis=1) - rows)) < 1e-10:
            break
    else:
        raise ValueError("IPF did not converge")
    return x


def transfer(poll):
    p = poll["publicado"]
    a = p["1t"]
    b = p["2t"]
    # Integer toplines sum to 103 in 1T and 99 in 2T. House rule: rescale origins.
    raw = [
        a[k]
        for k in ["lula", "flavio", "cury", "caiado", "renan_santos", "zema", "samara"]
    ] + [
        sum(a[k] for k in ["rui", "clariana", "edmilson", "grassi", "hertz"]),
        a["branco_nulo"],
        a["indecisos"],
    ]
    cols = np.array([b["lula"], b["flavio"], b["branco_nulo"] + b["indecisos"]], float)
    mass = np.array(raw) * cols.sum() / sum(raw)
    fixed = np.array(
        [
            [mass[0], 0, 0],
            [0, mass[1], 0],
            mass[2] * np.array([0.37, 0.39, 0.24]),
            mass[3] * np.array([0.33, 0.45, 0.22]),
        ]
    )
    residual = cols - fixed.sum(axis=0)
    priors = [
        [
            [0.03, 0.68, 0.29],
            [0.02, 0.8, 0.18],
            [0.85, 0.01, 0.14],
            [0.8, 0.01, 0.19],
            [0.15, 0.25, 0.6],
            [0.4, 0.4, 0.2],
        ],
        [
            [0.01, 0.8, 0.19],
            [0.01, 0.9, 0.09],
            [0.95, 0.01, 0.04],
            [0.9, 0.01, 0.09],
            [0.25, 0.1, 0.65],
            [0.2, 0.6, 0.2],
        ],
        [
            [0.08, 0.5, 0.42],
            [0.05, 0.6, 0.35],
            [0.7, 0.02, 0.28],
            [0.7, 0.02, 0.28],
            [0.1, 0.35, 0.55],
            [0.6, 0.2, 0.2],
        ],
    ]
    matrices = [np.vstack([fixed, ras(pr, mass[4:], residual)]) for pr in priors]
    main = matrices[0]
    assert np.allclose(main.sum(axis=0), cols) and np.allclose(main.sum(axis=1), mass)
    gain = cols[:2] - mass[:2]
    return {
        "sources": [
            "Lula",
            "Flávio",
            "Cury",
            "Caiado",
            "Renan",
            "Zema",
            "Samara",
            "Outros",
            "Branco/nulo",
            "Indecisos",
        ],
        "destinations": ["Lula", "Flávio", "B/N + indecisos"],
        "raw_origins": raw,
        "row_targets": mass.tolist(),
        "column_targets": cols.tolist(),
        "matrix": main.tolist(),
        "consolidated_rows": [0, 1],
        "measured_rows": [2, 3],
        "estimated_rows": list(range(4, 10)),
        "measured_percentages": {"Cury": [37, 39, 24], "Caiado": [33, 45, 22]},
        "measured_page": 8,
        "measured_note": "Votos nos finalistas publicados no texto da p. 8; não escolha é complemento aritmético (24% e 22%), sem separação de B/N e indecisos. Bases consolidadas por hipótese. Erros dos recortes declarados de ±9 e ±11 pp.",
        "normalization": {
            "origin_sum": sum(raw),
            "target_sum": float(cols.sum()),
            "factor": float(cols.sum() / sum(raw)),
        },
        "gains": gain.tolist(),
        "ratio_flavio_lula": float(gain[1] / gain[0]),
        "alternative_matrices": [m.tolist() for m in matrices[1:]],
        "cell_min": np.min(matrices, axis=0).tolist(),
        "cell_max": np.max(matrices, axis=0).tolist(),
    }


def archive_sources():
    """Keep public copies and provenance synchronized with the evidence used."""
    public = ROOT / "docs/fontes"
    public.mkdir(parents=True, exist_ok=True)
    manifest_path = FOLDER / "fontes.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["arquivos"] = {}
    for name, target in [
        ("relatorio.pdf", "datafolha_14092026.pdf"),
        ("questionario.pdf", "datafolha_14092026_questionario.pdf"),
        ("bairros.pdf", "datafolha_14092026_bairros.pdf"),
        ("registro.txt", "datafolha_14092026_registro.txt"),
    ]:
        payload = (FOLDER / name).read_bytes()
        (public / target).write_bytes(payload)
        manifest["arquivos"][name] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    content = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    manifest_path.write_text(content)
    (ASSETS / "datafolha_14092026_fontes.json").write_text(content)


def main():
    archive_sources()
    tables = json.loads((ASSETS / "datafolha_14092026_cruzamentos.json").read_text())[
        "tabelas"
    ]
    engine = module("reponderacao-pnad")
    bench = engine.Benchmark()
    ipca = engine.load_ipca()
    poll = poll_record(tables)
    (ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-09-10.json").write_text(
        json.dumps(poll, ensure_ascii=False, indent=2) + "\n"
    )
    r = engine.process_poll(poll, bench, ipca)
    proofs = []
    for key in ["estimulada_b", "turno2_flavio"]:
        rows, bases = flat(tables[key])
        for dim, groups in {
            "sexo": ["Masculino", "Feminino"],
            "regiao": ["Sudeste", "Sul", "Nordeste", "Centro-Oeste/Norte"],
            "renda": BANDS,
        }.items():
            for label in ["Lula (PT)", "Flavio Bolsonaro (PL)"]:
                value = sum(rows[label][c] * bases[c] for c in groups) / sum(
                    bases[c] for c in groups
                )
                proofs.append(
                    {
                        "tabela": key,
                        "dimensao": dim,
                        "candidato": label,
                        "recomposto": value,
                        "publicado": rows[label]["Total"],
                        "base": sum(bases[c] for c in groups),
                        "residuo": value - rows[label]["Total"],
                    }
                )
                assert abs(value - rows[label]["Total"]) < 1.5
    current, bases = flat(tables["turno2_flavio"])
    candidates = list(current)
    alternatives = []
    for key in [
        "turno2_flavio",
        "turno2_caiado",
        "turno2_zema",
        "turno2_renan",
        "turno2_cury",
    ]:
        rows, _ = flat(tables[key])
        names = list(rows)
        tab = {
            "opcoes": ["lula", "adversario", "branco_nulo", "indecisos"],
            "linhas": [[rows[n][c] for n in names] for c in BANDS],
        }
        pub = dict(zip(tab["opcoes"], [rows[n]["Total"] for n in names], strict=True))
        adjusted = engine.reweight_table(
            tab,
            pub,
            engine.source_profile(poll),
            {CEN: bench.shares(CEN, engine.band_cuts_brl(poll, ipca))},
        )
        recortes = []
        for c in bases:
            recortes.append(
                {
                    "recorte": c,
                    "lula": rows[names[0]][c],
                    "adversario": rows[names[1]][c],
                    "nao_escolha": rows[names[2]][c] + rows[names[3]][c],
                    "delta_vs_flavio": rows[names[1]][c] - current[candidates[1]][c],
                }
            )
        alternatives.append(
            {
                "key": key,
                "nome": names[1],
                "pagina": tables[key]["blocks"]["bloco2"]["pdf_page"],
                "publicado": pub,
                "reweight": adjusted,
                "recortes": recortes,
            }
        )
    coverage = []
    for dim, groups in {
        "sexo": ["Masculino", "Feminino"],
        "idade": ["16-24", "25-34", "35-44", "45-59", "60+"],
        "escolaridade": ["Fundamental", "Medio", "Superior"],
        "renda": BANDS,
        "ocupacao": ["PEA", "Nao PEA"],
        "cor": ["Branca", "Preta", "Parda"],
        "religiao": ["Catolica", "Evangelica"],
        "regiao": ["Sudeste", "Sul", "Nordeste", "Centro-Oeste/Norte"],
        "natureza": ["Regiao metropolitana", "Interior"],
    }.items():
        total = sum(bases[g] for g in groups)
        coverage.append(
            {
                "dimensao": dim,
                "base": total,
                "faltam": 2002 - total,
                "cobertura_pct": total / 2002 * 100,
            }
        )
    hist = []
    for path in sorted(
        (ROOT / "analysis/reponderacao/pesquisas").glob("datafolha_*.json")
    ):
        p = json.loads(path.read_text())
        rr = engine.process_poll(p, bench, ipca)
        hist.append(
            {
                "id": p["id"],
                "campo": p["campo"],
                "divulgacao": p["divulgacao"],
                "turnos": rr["turnos"],
                "perfil": rr["renda"]["amostra_pct"],
            }
        )
    prev = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-09-02.json").read_text()
    )
    source_prev = engine.source_profile(prev)
    source_now = engine.source_profile(poll)
    decomposition = {}
    for t in ["1t", "2t"]:
        rows = poll["cruzamentos"][t]["linhas"]
        opts = poll["cruzamentos"][t]["opcoes"]
        j = [opts.index("lula"), opts.index("flavio")]
        old = engine.compose(rows, source_prev)
        now = engine.compose(rows, source_now)
        composition_gap = (now[j[0]] - now[j[1]]) - (old[j[0]] - old[j[1]])
        decomposition[t] = {
            "efeito_composicao_gap": composition_gap,
            "variacao_gap_publicado": r["turnos"][t]["gap_publicado"]
            - engine.gap(prev["publicado"][t]),
        }
    dec, decbase = flat(tables["definicao"])
    _mot, motbase = flat(tables["motivacao"])
    may_change = dec["Seu voto ainda pode mudar?"]["Total"]
    market = (2002 - decbase["Total"]) / 2002 * 100 + decbase[
        "Total"
    ] / 2002 * may_change
    previous_factor = sum(prev["publicado"]["2t"].values()) / sum(
        prev["publicado"]["1t"].values()
    )
    previous_gains = [
        prev["publicado"]["2t"][k] - prev["publicado"]["1t"][k] * previous_factor
        for k in ["lula", "flavio"]
    ]
    flow = transfer(poll)
    flow["previous"] = {
        "divulgacao": prev["divulgacao"],
        "factor": previous_factor,
        "gains": previous_gains,
        "ratio_flavio_lula": previous_gains[1] / previous_gains[0],
    }
    territorial = json.loads(
        (ASSETS / "datafolha_14092026_territorio.json").read_text()
    )
    # Apply the same delta to the declared-income share only, leaving the missing share untouched.
    q = sum(poll["renda"]["bases"]) / poll["n"]
    preserved = {
        t: {
            k: round(v + q * (r["turnos"][t]["cenarios"][CEN]["ajustado"][k] - v), 3)
            for k, v in poll["publicado"][t].items()
        }
        for t in ["1t", "2t"]
    }
    data = {
        "territory": territorial,
        "missing_share_preserved": preserved,
        "poll": poll,
        "reweight": r,
        "proofs": proofs,
        "coverage": coverage,
        "history": hist,
        "alternatives": alternatives,
        "transfer": flow,
        "decomposition": decomposition,
        "market": {
            "base_definicao": decbase["Total"],
            "base_motivacao": motbase["Total"],
            "sem_opcao_base": 2002 - decbase["Total"],
            "pode_mudar_pct_condicional": may_change,
            "mercado_aberto_pct_aproximado": market,
        },
        "provenance": {
            "report_sha256": hashlib.sha256(
                (FOLDER / "relatorio.pdf").read_bytes()
            ).hexdigest(),
            "metadata": fitz.open(FOLDER / "relatorio.pdf").metadata,
        },
    }
    (ASSETS / "datafolha_14092026_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "placares": {
                    k: v["cenarios"][CEN]["ajustado"] for k, v in r["turnos"].items()
                },
                "gap": {k: v["gap_ajustado"] for k, v in r["turnos"].items()},
                "market": market,
                "composicao": decomposition,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
