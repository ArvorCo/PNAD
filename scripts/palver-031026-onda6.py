#!/usr/bin/env python3
"""Integra a onda 6 da Palver (BR-00198/2026) ao agregador de reponderação.

Fonte primária: tabelas exatas do Explorer arquivadas em
analysis/reponderacao/palver_explorer_20261003/ (coletadas com as funções de
palver-explorer-extract.py, só a onda 6, dois turnos por total, renda, sexo e
região) e o PDF do relatório em data/originals/palver_102026_03/. O perfil
ponderado de renda é recuperado por sistema linear (palver-explorer-audit.py)
e validado pelo n efetivo; contagens brutas não são pesos. Os placares
inteiros do PDF (pp. 29 e 34) ficam em publicado_pdf.
"""

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
BASE = ROOT / "analysis/reponderacao"
EXPLORER = BASE / "palver_explorer_20261003"
ARCHIVE = ROOT / "data/originals/palver_102026_03"
POLLS = BASE / "pesquisas"
WAVE = "06_pesquisa_2026_10_03"
TODAY = "2026-10-03"
URL_PDF = (
    "https://www.palver.com.br/api/surveys/voting-intention-2026-october-w6/report"
)
PAGES = {
    "metodologia": "16–18",
    "amostra": 20,
    "1t_topline": 29,
    "1t_renda": 30,
    "2t_topline": 34,
    "2t_renda": 35,
}
PDF_TOPLINE = {"1t": {"flavio": 47, "lula": 43}, "2t": {"flavio": 49, "lula": 44}}
PAIR = ["lula", "flavio"]
# Colunas de renda das pp. 30 e 35, lidas na imagem (até 2, 2 a 5, mais de 5 SM).
PDF_INCOME = {
    "1t": {"flavio": [46, 49, 41], "lula": [45, 40, 45]},
    "2t": {"flavio": [48, 52, 47], "lula": [47, 40, 47]},
}


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def pdf_source():
    pdf = ARCHIVE / "relatorio.pdf"
    payload = pdf.read_bytes()
    assert payload.startswith(b"%PDF")
    info = subprocess.run(
        ["pdfinfo", "-isodates", str(pdf)], capture_output=True, text=True, check=True
    ).stdout
    pairs = (line.split(":", 1) for line in info.splitlines() if ":" in line)
    meta = {k.strip(): v.strip() for k, v in pairs}
    text = (ARCHIVE / "relatorio.txt").read_text()
    assert "BR-00198/2026" in text and "30/09/2026 – 03/10/2026" in text
    return {
        "instituto": "Palver",
        "registro_tse": "BR-00198/2026",
        "url": URL_PDF,
        "explorer": f"https://www.palver.com.br/survey/explore?wave={WAVE}",
        "arquivo": str(pdf.relative_to(ROOT)),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "paginas": int(meta["Pages"]),
        "creation_date_pdf": meta["CreationDate"],
        "baixado_em": TODAY,
        "campo": "2026-09-30 a 2026-10-03",
        "divulgacao": TODAY,
        "paginas_usadas": PAGES,
        "renderizacoes": "analysis/predicao_2026/atualizacao_20261003/palver/",
    }


def recompose(weights, matrix, answers, names):
    shares = matrix @ (weights / weights.sum())
    return {names[a]: float(100 * v) for a, v in zip(answers, shares, strict=True)}


def build():
    audit = importlib.import_module("palver-explorer-audit")
    names = importlib.import_module("palver-explorer-integrate").NAMES
    audit.BASE = EXPLORER
    margins = {
        k: audit.recover_margin(WAVE, k) for k in ["inc_std", "sex_std", "reg_std"]
    }
    for m in margins.values():
        assert m["identified"] and m["max_residual"] < 1e-10, m
        assert abs(m["reconstructed_neff"] - m["published_neff"]) < 1e-6
    source = pdf_source()
    dump(ARCHIVE / "fonte.json", source)
    previous = read(POLLS / "palver_2026-09-27.json")
    poll = {k: previous[k] for k in ["instituto", "contratante", "metodo", "renda"]}
    poll.update(
        id="palver_2026-10-03",
        campo={"inicio": "2026-09-30", "fim": "2026-10-03"},
        divulgacao=TODAY,
        registro_tse="BR-00198/2026",
        n=5000,
        publicado={},
        cruzamentos={},
    )
    poll["renda"].update(
        amostra_pct=margins["inc_std"]["weighted_pct"],
        perfil_tipo="perfil_ponderado_reconstituido",
        mes_precos="202610",
        nota="Margem ponderada recuperada das tabelas exatas da onda 6 com posto completo; "
        "recomposição dos dois turnos e n efetivo (1.655,77) conferidos. Contagens brutas "
        "(1.595, 2.127 e 1.278) não são os pesos de composição. Referência da Palver: "
        "PNADC 2024, visita 5, em salários mínimos de 2026; a margem coincide com a das "
        "ondas 4 e 5 porque renda entra no raking (p. 18).",
    )
    poll["fonte"] = {
        "tipo": "explorer",
        "pdf": source["arquivo"],
        "url": "https://www.palver.com.br/survey/explore?"
        f"wave={WAVE}&question=lula_flavio&breakdown=inc_std",
        "paginas": PAGES,
        "sha256": source["sha256"],
        "bytes": source["bytes"],
        "total_paginas": source["paginas"],
        "conferido_em": TODAY,
        "status": "Relatório completo arquivado e conferido.",
        "url_pdf": URL_PDF,
        "onda_explorer": WAVE,
        "snapshot": str(EXPLORER.relative_to(ROOT)),
        "nota": "Onda 6, única versão no catálogo do Explorer em 03/10/2026. PDF e tabelas "
        "exatas do Explorer arquivados. Datas do campo e registro conforme p. 20 do PDF.",
    }
    controls = {}
    for turn, question in audit.BALLOTS.items():
        total = audit.table(WAVE, question)
        inc = audit.table(WAVE, question, "inc_std")
        poll["publicado"][turn] = {
            names[c["answer"]]: c["share"] * 100 for c in total["cells"]
        }
        poll["cruzamentos"][turn] = {
            "opcoes": [names[a] for a in inc["answers"]],
            "linhas": (audit.matrix(inc).T * 100).tolist(),
            "nota": "Extração programática das tabelas exatas do Explorer, onda 6, todas as "
            f"alternativas disponíveis. Mesmo cruzamento na p. {PAGES[turn + '_renda']} do PDF.",
            "proveniencia": {
                kind: read(EXPLORER / WAVE / f"{question}--{key}.json")["source"]
                for kind, key in [("total", "total"), ("renda", "inc_std")]
            },
        }
        controls[turn] = {}
        for key, label in [
            ("inc_std", "renda"),
            ("sex_std", "sexo"),
            ("reg_std", "regiao"),
        ]:
            tab = audit.table(WAVE, question, key)
            weights = np.array(margins[key]["weighted_pct"])
            rec = recompose(weights, audit.matrix(tab), tab["answers"], names)
            controls[turn][label] = {
                "pesos": margins[key]["weighted_pct"],
                "grupos": margins[key]["groups"],
                "recomposto": rec,
                "residuo_max_pp": max(
                    abs(rec[k] - poll["publicado"][turn][k]) for k in rec
                ),
            }
        weights = np.array(margins["inc_std"]["weighted_pct"]) / 100
        pdf_rec = {k: float(weights @ PDF_INCOME[turn][k]) for k in PAIR}
        exact = {
            k: [r[inc["answers"].index(a)] for r in poll["cruzamentos"][turn]["linhas"]]
            for k, a in [("lula", "Lula (PT)"), ("flavio", "Flávio Bolsonaro (PL)")]
        }
        assert all(
            abs(round(x) - y) == 0
            for k in PAIR
            for x, y in zip(exact[k], PDF_INCOME[turn][k], strict=True)
        ), (turn, exact)
        controls[turn]["pdf_inteiros_renda"] = {
            "pagina": PAGES[turn + "_renda"],
            "linhas": PDF_INCOME[turn],
            "recomposto": pdf_rec,
            "residuo_vs_pdf_pp": {k: pdf_rec[k] - PDF_TOPLINE[turn][k] for k in PAIR},
        }
        controls[turn]["pdf_inteiro_menos_exato_pp"] = {
            k: PDF_TOPLINE[turn][k] - poll["publicado"][turn][k] for k in PAIR
        }
    poll["publicado_pdf"] = {
        turn: {k: PDF_TOPLINE[turn][k] for k in PAIR} for turn in PDF_TOPLINE
    }
    poll["recomposicao"] = {
        **controls,
        "nota": "Recomposição do placar exato pelo perfil ponderado recuperado em três "
        "partições independentes (renda, sexo e região). Como as margens são identificadas "
        "pelas próprias tabelas, o resíduo é numérico; a prova independente é o n efetivo "
        "de Kish reconstituído (1.655,77), igual ao publicado pelo Explorer e ao n efetivo "
        "de 1.656 da p. 18. Controle documental: as colunas de renda inteiras das pp. 30 e "
        "35, lidas na imagem, coincidem com o arredondamento do Explorer e, pesadas pelo "
        "perfil recuperado, recompõem o placar inteiro do PDF (pp. 29 e 34).",
    }
    poll["notas"] = (
        "Onda 6 da Palver, última antes do 1º turno; substitui a onda 5 (BR-02990/2026, "
        "campo 24 a 27/09) na última onda por casa. O campo termina em 03/10, mesmo dia da "
        "divulgação (p. 20; creationDate do PDF 03/10/2026 15:44). Divergência documental: "
        "a p. 18 informa efeito dos pesos desiguais de 3,92 e a p. 20, de 3,02; o n efetivo "
        "de 1.656 (p. 18 e Explorer) corresponde a 5.000/3,02. O questionário removeu as "
        "seções de rejeição, problemas do Brasil e políticas públicas (p. 12). Sensibilidade "
        "de uma margem sob régua comum; não é novo resultado oficial nem previsão."
    )
    dump(POLLS / f"{poll['id']}.json", poll)
    dump(
        EXPLORER / "margens.json",
        {"onda": WAVE, "margens": margins, "recomposicao": controls},
    )
    return poll


if __name__ == "__main__":
    p = build()
    print(json.dumps(p["recomposicao"], ensure_ascii=False, indent=1)[:3000])
