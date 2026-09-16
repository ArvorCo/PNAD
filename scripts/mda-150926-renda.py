#!/usr/bin/env python3
"""Registra a 170ª CNT/MDA e comprova a transcrição para o agregador PNAD.

Fonte: PDF integral, páginas 3, 8, 9, 12, 13 e 40. Os gráficos são imagens:
valores conferidos visualmente, preservando os arredondamentos impressos.
"""

import hashlib
import importlib.util
import json
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/pesquisas/cnt-mda/2026-09-15"
PDF_URL = "https://admin.cnnbrasil.com.br/wp-content/uploads/sites/12/2026/09/41c8cf7e-63b9-4165-be91-3f4545ba7649-1.pdf"
# p.40: as três faixas cobrem 98,6%; 1,4% NS/NR não é faixa de renda.
PROFILE = [43.8, 33.8, 21.0]
NONRESPONSE = 1.4
# p.9: Lula, Flávio, outros, branco/nulo, indecisos.
FIRST_ROWS = [[47, 24, 13, 7, 8], [37, 33, 18, 5, 7], [34, 40, 17, 5, 5]]
# p.13: Lula, Flávio, branco/nulo, indecisos.
SECOND_ROWS = [[54, 33, 10, 4], [45, 43, 11, 2], [39, 50, 10, 1]]
# p.8: abertura do total 'outros' no cruzamento, incluindo Cury.
OTHER_CANDIDATES = {
    "cury": 6.0,
    "caiado": 3.0,
    "renan": 2.7,
    "marcal": 1.8,
    "zema": 1.0,
    "outros_nomes": 1.1,
}
SEX_WEIGHTS = [47.6, 52.4]  # p.40, masculino/feminino
SEX_FIRST = [[38, 35], [43, 26]]  # p.9, Lula/Flávio
SEX_SECOND = [[43, 45], [51, 35]]  # p.13, Lula/Flávio


def engine():
    spec = importlib.util.spec_from_file_location(
        "reweight", ROOT / "scripts/reponderacao-pnad.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record():
    old = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/mda_2026-08-09.json").read_text()
    )
    return {
        "id": "mda_2026-09-13",
        "instituto": "MDA",
        "contratante": "Confederação Nacional do Transporte (CNT)",
        "registro_tse": "BR-06902/2026",
        "campo": {"inicio": "2026-09-09", "fim": "2026-09-13"},
        "divulgacao": "2026-09-15",
        "n": 2002,
        "metodo": "presencial, domiciliar e ponto de fluxo; cotas de gênero, idade, renda e instrução; sem ponderação posterior declarada",
        "fonte": {
            "tipo": "relatorio",
            "rotulo": "Relatório CNT/MDA, 170ª rodada",
            "pdf": str((FOLDER / "relatorio.pdf").relative_to(ROOT)),
            "url": PDF_URL,
            "paginas": {
                "metodologia": 3,
                "perfil_renda": 40,
                "1t": 8,
                "1t_renda": 9,
                "2t": 12,
                "2t_renda": 13,
            },
            "status": "Relatório completo conferido.",
            "nota": "A p.3 declara que não houve ponderação dos dados. A composição publicada na p.40 é a distribuição das entrevistas, com 1,4% de renda NS/NR. Capa e metodologia trazem BR-06902/2026; a contracapa repete BR-06935/2026, código da onda anterior.",
        },
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "faixas": old["renda"]["faixas"],
            "amostra_pct": PROFILE,
            "perfil_tipo": "perfil_publicado",
            "nota": "P.40: menos de 2 SM = 43,8%; de 2 até 5 SM = 33,8%; mais de 5 SM = 21,0%; NS/NR = 1,4%. O motor exclui NS/NR da distribuição de renda e renormaliza as três faixas (44,42% / 34,28% / 21,30%), mantendo o placar total como âncora, sem imputar o voto de quem não declarou renda. A metodologia da p.3 inclui renda nas variáveis de controle e afirma que não foi utilizada ponderação nos dados. Cortes nominais em salários mínimos de 2026; não confundir renda familiar com per capita.",
        },
        "publicado": {
            "1t": {
                "lula": 40.5,
                "flavio": 30.4,
                "outros": round(sum(OTHER_CANDIDATES.values()), 1),
                "branco_nulo": 6.0,
                "indecisos": 7.5,
            },
            "2t": {"lula": 47.3, "flavio": 40.0, "branco_nulo": 10.2, "indecisos": 2.5},
        },
        "cruzamentos": {
            "1t": {
                "opcoes": ["lula", "flavio", "outros", "branco_nulo", "indecisos"],
                "linhas": FIRST_ROWS,
                "nota": "P.9, três linhas de renda conferidas visualmente. Outros agrupa Cury, Caiado, Renan, Marçal, Zema e demais nomes da p.8, total 15,6%. As linhas somam 99, 100 e 101; preservamos os arredondamentos publicados, sem preencher células por resíduo.",
            },
            "2t": {
                "opcoes": ["lula", "flavio", "branco_nulo", "indecisos"],
                "linhas": SECOND_ROWS,
                "nota": "P.13, Lula x Flávio. Valores conferidos na renderização, incluindo os rótulos de indecisos na borda direita: 4, 2 e 1. As linhas somam 101, 101 e 100; preservadas como publicadas.",
            },
        },
        "notas": "170ª rodada CNT/MDA. Sensibilidade de uma margem com a mesma fórmula e os três universos PNAD do agregador. Recomposta também por sexo como controle independente da leitura. Os percentuais ajustados não são um novo resultado oficial nem uma previsão; podem não somar exatamente 100 devido aos arredondamentos das tabelas originais.",
    }


def main():
    pdf = FOLDER / "relatorio.pdf"
    with fitz.open(pdf) as doc:
        pages = [{"pagina": i + 1, "texto": p.get_text()} for i, p in enumerate(doc)]
    assert len(pages) == 57
    assert "BR-06902/2026" in pages[0]["texto"]
    assert "Não foi utilizada ponderação" in pages[2]["texto"]
    assert sum(PROFILE) + NONRESPONSE == 100
    (FOLDER / "paginas-nativas.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2) + "\n"
    )
    p = record()
    e = engine()
    result = e.process_poll(p, e.Benchmark(), e.load_ipca())
    proofs = {}
    for turno, rows in [("1t", SEX_FIRST), ("2t", SEX_SECOND)]:
        sex = e.compose(rows, SEX_WEIGHTS)
        errors = [
            abs(v - p["publicado"][turno][key])
            for v, key in zip(sex, ["lula", "flavio"], strict=True)
        ]
        assert max(errors) < 0.5
        assert result["turnos"][turno]["residuo_max"] < 0.5
        proofs[turno] = {
            "recomposto_sexo_lula_flavio": sex,
            "residuo_sexo_max": max(errors),
            "recomposto_renda": result["turnos"][turno]["recomposto"],
            "residuo_renda_max": result["turnos"][turno]["residuo_max"],
        }
    target = ROOT / "analysis/reponderacao/pesquisas/mda_2026-09-13.json"
    target.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n")
    data = {
        "fonte": p["fonte"],
        "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "bytes": pdf.stat().st_size,
        "perfil_renda_incluindo_nsr": [*PROFILE, NONRESPONSE],
        "outros_1t": OTHER_CANDIDATES,
        "controle_sexo": {"pesos": SEX_WEIGHTS, "1t": SEX_FIRST, "2t": SEX_SECOND},
        "provas": proofs,
        "resultado": result,
    }
    for path in [FOLDER / "manifesto.json", ROOT / "docs/assets/mda_150926_renda.json"]:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {"renda": result["renda"], "turnos": result["turnos"], "provas": proofs},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
