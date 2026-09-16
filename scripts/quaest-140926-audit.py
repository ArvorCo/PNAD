#!/usr/bin/env python3
"""Auditoria reproduzível das ondas Quaest de 7 e 14/09/2026."""

import csv
import hashlib
import importlib.util
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/pesquisas/quaest/2026-09-14"
OLD = ROOT / "data/pesquisas/quaest/2026-09-07"
OUT = ROOT / "docs/assets/quaest_140926_data.json"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


T = module("quaest-140926-tables")


def transfer(prior=None):
    """4 origens medidas, 2 bases fixas por hipótese e 2 origens residuais IPF."""
    names = (
        ["Lula", "Flávio"]
        + [x["name"] for x in T.TRANSFERS]
        + ["Indecisos", "B/N/não vota"]
    )
    shares = [36, 31] + [x["share"] for x in T.TRANSFERS] + [10, 7]
    cols = [40, 42, 5, 13]
    fixed = [[36.0, 0, 0, 0], [0, 31.0, 0, 0]]
    fixed += [[x["share"] * v / 100 for v in x["row"]] for x in T.TRANSFERS]
    target = [cols[j] - sum(row[j] for row in fixed) for j in range(4)]
    if min(target) < 0:
        raise ValueError("Medições e hipóteses incompatíveis com margens")
    a = [list(r) for r in (prior or [[1, 3, 3, 3], [0.2, 0.5, 1, 8.3]])]
    for _ in range(10000):
        for i, row in enumerate(a):
            fac = shares[i + 6] / sum(row)
            a[i] = [v * fac for v in row]
        for j in range(4):
            fac = target[j] / sum(row[j] for row in a)
            for row in a:
                row[j] *= fac
        if max(abs(sum(a[i]) - shares[i + 6]) for i in range(2)) < 1e-12:
            break
    matrix = fixed + a
    assert max(abs(sum(r) - s) for r, s in zip(matrix, shares, strict=True)) < 1e-9
    assert max(abs(sum(r[j] for r in matrix) - cols[j]) for j in range(4)) < 1e-9
    return {
        "origins": names,
        "shares": shares,
        "destinations": ["Lula", "Flávio", "Indecisos", "B/N/não vota"],
        "targets": cols,
        "matrix": matrix,
        "kinds": ["hipotese"] * 2 + ["medido"] * 4 + ["estimado"] * 2,
        "residual_targets": target,
        "consolidation": {
            "lula": 4,
            "flavio": 11,
            "ratio": 2.75,
            "previous_ratio": 2.4,
        },
        "prior": prior or [[1, 3, 3, 3], [0.2, 0.5, 1, 8.3]],
    }


def record():
    poll = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/quaest_2026-09-06.json").read_text()
    )
    poll.update(
        id="quaest_2026-09-13",
        registro_tse="BR-03607/2026",
        campo={"inicio": "2026-09-10", "fim": "2026-09-13"},
        divulgacao="2026-09-14",
        dossie="quaest_14092026.html",
    )
    poll["fonte"] = {
        "tipo": "relatorio",
        "rotulo": "Relatório completo (205 páginas)",
        "pdf": str((FOLDER / "relatorio.pdf").relative_to(ROOT)),
        "url": T.PDF,
        "paginas": {
            "perfil_renda": 199,
            "1t_renda": 22,
            "1t_topline": 16,
            "2t_renda": 33,
            "2t_topline": 28,
        },
        "status": "Relatório completo conferido.",
        "nota": "Íntegra de 14/09 confirma perfil 31/42/27 e cruzamento de 2º turno anteriormente obtido no g1; acrescenta o primeiro turno sem Marçal. O PDF chama essa lista de cenário 1, embora ela corresponda à lista do cenário 2 registrado.",
    }
    poll["renda"].update(
        amostra_pct=T.PROFILE,
        perfil_tipo="perfil_publicado",
        nota="Perfil publicado na p.199, idêntico às cotas registradas: 31/42/27. Renda domiciliar total, cartão em salários mínimos de 2026 (R$ 1.621); fonte declarada PNADC anual 2025, visita 1. Não são bases brutas de campo. O instituto não publica os pesos individuais nem quantifica aqui a recusa de renda. A primeira faixa é 4,19 pontos menor que a referência Arvor de pessoas 16+.",
    )
    poll["publicado"] = {
        "1t": dict(zip(T.FIRST_OPTIONS, T.FIRST, strict=True)),
        "2t": dict(zip(T.SECOND_OPTIONS, T.SECOND, strict=True)),
    }
    poll["cruzamentos"] = {
        "1t": {
            "opcoes": T.FIRST_OPTIONS,
            "linhas": T.FIRST_INCOME,
            "nota": "p.22, coluna 14/9: seis categorias publicadas, sem imputação. As duas primeiras linhas somam 101 por arredondamento; preservadas. Cenário sem Marçal. Não misturar com o cenário com Marçal da onda anterior.",
        },
        "2t": {
            "opcoes": T.SECOND_OPTIONS,
            "linhas": T.SECOND_INCOME,
            "nota": "p.33, coluna 14/9, quatro opções em cada faixa, somas 100. Confirma integralmente a transcrição provisória do g1.",
        },
    }
    poll["notas"] = (
        "Sensibilidade de uma margem, ancorada no placar publicado. Relatório completo substitui a fonte parcial sem alterar o 2º turno. O 1º turno anterior no agregador contém Marçal; a comparação temporal do dossiê usa o cenário equivalente sem Marçal, explicitamente identificado."
    )
    (ROOT / "analysis/reponderacao/pesquisas/quaest_2026-09-13.json").write_text(
        json.dumps(poll, ensure_ascii=False, indent=2) + "\n"
    )
    return poll


def territories():
    tool = module("quaest-territory-audit")
    a = tool.parse_pdf(OLD / "bairros.pdf", "07/09", "BR-01720/2026")
    b = tool.parse_pdf(FOLDER / "bairros.pdf", "14/09", "BR-03607/2026")
    am = {x.municipality_code for x in a}
    bm = {x.municipality_code for x in b}
    common = {x.sector_code for x in a} & {x.sector_code for x in b}
    rows = [asdict(x) for x in a + b]
    path = ROOT / "docs/assets/quaest_140926_territorio.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return {
        "municipalities_each": 120,
        "sectors_each": 334,
        "interviews_each": 2004,
        "common_municipalities": len(am & bm),
        "common_sectors": len(common),
        "new_sector_pct": 100 * (334 - len(common)) / 334,
        "interviews_common_municipalities": sum(
            x.interviews for x in b if x.municipality_code in am
        ),
        "common_sector_codes": sorted(common),
        "regions": {
            r: sum(x.interviews for x in b if x.region == r)
            for r in sorted({x.region for x in b})
        },
        "rows": rows,
    }


def main():
    engine = module("reponderacao-pnad")
    p = record()
    bench = engine.Benchmark()
    ipca = engine.load_ipca()
    result = engine.process_poll(p, bench, ipca)
    proofs = {}
    for turno in ["1t", "2t"]:
        vals = engine.compose(T.SEX[turno], T.SEX["weights"])
        pub = p["publicado"][turno]
        assert (
            max(abs(vals[i] - pub[k]) for i, k in enumerate(["lula", "flavio"])) < 0.51
        )
        proofs[turno] = {
            "sex_recomposed": vals,
            "income_recomposed": result["turnos"][turno]["recomposto"],
            "income_max_residual": result["turnos"][turno]["residuo_max"],
        }
    assert result["turnos"]["2t"]["residuo_max"] <= 0.12
    targets = {
        key: bench.shares(key, engine.band_cuts_brl(p, ipca))
        for key in engine.SCENARIOS
    }
    alts = []
    for x in T.ALTERNATIVES:
        r = engine.reweight_table(
            {
                "opcoes": ["lula", "adversario", "branco_nulo", "indecisos"],
                "linhas": x["income"],
            },
            dict(
                zip(
                    ["lula", "adversario", "branco_nulo", "indecisos"],
                    x["published"],
                    strict=True,
                )
            ),
            T.PROFILE,
            targets,
        )
        assert r["residuo_max"] < 0.75
        alts.append({**x, "sensitivity": r})
    ledger = module("quaest-140926-ledger").extract(FOLDER / "questionario.pdf")
    # A contagem é estritamente do PDF. Divulgação externa nunca vira "ocultação".
    assert sum(x["report_page"] is not None for x in ledger) == 38
    gap = engine.compose(
        [
            [r[1] - v[1]]
            for r, v in zip(T.APPROVAL_INCOME, T.SECOND_INCOME, strict=True)
        ],
        T.PROFILE,
    )[0]
    data = {
        "meta": {
            "published": "2026-09-14",
            "audited": "2026-09-15",
            "registry": p["registro_tse"],
            "pdf": T.PDF,
            "old_pdf": T.OLD_PDF,
            "n": 2004,
            "price_month": max(ipca),
        },
        "tables": {
            k: getattr(T, k)
            for k in [
                "PROFILE",
                "FIRST",
                "FIRST_OPTIONS",
                "FIRST_INCOME",
                "SECOND",
                "SECOND_OPTIONS",
                "SECOND_INCOME",
                "SEX",
                "POLITICAL",
                "TRANSFERS",
                "HISTORY",
                "FIRST_HISTORY",
                "MOVEMENT",
                "APPROVAL_INCOME",
                "BEST_RESULT",
                "BEST_FIRST",
                "BEST_SECOND",
                "OLD_USEFUL",
            ]
        },
        "reweight": result,
        "proofs": proofs,
        "alternatives": alts,
        "transfer": transfer(),
        "transfer_alternative": transfer([[3, 1, 3, 3], [1, 3, 1, 5]]),
        "territory": territories(),
        "questions": ledger,
        "derived": {
            "disapproval_minus_flavio_income": gap,
            "open_vote_approx": 83 * 0.27 + 10,
            "flavio_definite_old": 29 * 0.78,
            "flavio_definite_new": 31 * 0.72,
            "lula_definite_new": 36 * 0.8,
            "difference_margin_2t_aas": engine.difference_margin(40, 42, 2004),
            "difference_margin_1t_aas": engine.difference_margin(36, 31, 2004),
        },
        "external": {
            "stf": T.G1_STF,
            "reforms": T.G1_REFORMS,
            "stf_impact": [67, 22, 7, 4],
            "note": "Somente fontes conferidas. Não é levantamento exaustivo de publicações externas. A lista de respostas à Q47 na matéria de reformas soma 108%; não incorporada como partição válida.",
        },
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    public = ROOT / "docs/fontes/quaest_140926"
    public.mkdir(parents=True, exist_ok=True)
    files = []
    for folder in [OLD, FOLDER]:
        for name in [
            "relatorio.pdf",
            "questionario.pdf",
            "bairros.pdf",
            "registro.txt",
        ]:
            f = folder / name
            files.append(
                {
                    "arquivo": str(f.relative_to(ROOT)),
                    "bytes": f.stat().st_size,
                    "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                }
            )
        for name in ["questionario.pdf", "bairros.pdf"]:
            shutil.copy2(folder / name, public / f"{folder.name}_{name}")
    for name in [
        "g1-stf.html",
        "g1-stf.txt",
        "g1-reformas.html",
        "g1-reformas.txt",
        "catalogo-pdfs.json",
        "cnn-placar.html",
    ]:
        f = FOLDER / name
        if f.exists():
            files.append(
                {
                    "arquivo": str(f.relative_to(ROOT)),
                    "bytes": f.stat().st_size,
                    "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                }
            )
    manifest = {
        "registro_tse": p["registro_tse"],
        "fontes": p["fonte"],
        "arquivos": files,
        "ocr": "426 páginas processadas; OCR serve como índice, não como transcrição numérica validada. Tabelas do dossiê conferidas visualmente com páginas citadas.",
        "externas": data["external"],
    }
    (FOLDER / "manifesto-completo.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    (ROOT / "docs/assets/quaest_140926_fontes.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "sensitivity": result["turnos"],
                "proofs": proofs,
                "derived": data["derived"],
                "territory": {
                    k: v for k, v in data["territory"].items() if k != "rows"
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
