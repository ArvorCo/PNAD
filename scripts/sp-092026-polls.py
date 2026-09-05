#!/usr/bin/env python3
"""Transcrições verificadas, extração integral nativa e testes de recomposição."""

import hashlib
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/pesquisas/estaduais/sp/2026-09"
OUT = ROOT / "docs/assets"
URLS = {
    "atlas": "https://cdn1.atlasintel.org/pesquisa_atlas_estadao__eleicoes_sao_paulo_2026__260901_d7bd2dffe42f5965.pdf",
    "quaest": "https://quaest.com.br/wp-content/uploads/2026/08/QUAEST1SP2508.pdf",
    "parana": "https://paranapesquisas.com.br/wp-content/uploads/2026/08/SP_Ago26.pdf",
    "datafolha": "https://www1.folha.uol.com.br/poder/2026/08/datafolha-tarcisio-lidera-disputa-para-governo-de-sp-com-45-contra-27-de-haddad.shtml",
    "datafolha_pres": "https://www1.folha.uol.com.br/poder/2026/08/datafolha-flavio-tem-47-e-lula-42-em-sp-no-2o-turno-mg-marca-empate.shtml",
    "rt_gov": "https://ultimosegundo.ig.com.br/2026-08-24/realtime-big-data-em-sp--tarcisio-com-54--e-haddad-com-36-.html",
    "rt_pres": "https://www.metropoles.com/sao-paulo/flavio-lidera-disputa-em-sp-com-38-diz-pesquisa-real-time-big-data",
    "verita": "https://goiasnoticia.com.br/verita-em-sp-tarcisio-lidera-governo-e-senado-segue-com-empate-tecnico-prado-derrite-silva-palumbo-e-tebet-disputam/",
}
POLLS = [
    {
        "id": "parana",
        "nome": "Paraná",
        "campo": "16 a 18/08",
        "divulgacao": "19/08/2026",
        "n": 1680,
        "me": 2.4,
        "metodo": "Domiciliar presencial",
        "registro": "SP-08913/2026",
        "governo": [50, 33.8],
        "governo2": [53, 36.9],
        "nao_escolha_gov": 12.3,
        "paginas": "3, 8 e 11",
        "status": "PDF conferido",
    },
    {
        "id": "datafolha",
        "nome": "Datafolha",
        "campo": "18 e 19/08",
        "divulgacao": "21/08/2026",
        "n": 1610,
        "me": 2,
        "metodo": "Presencial em pontos de fluxo",
        "registro": "SP-01806/2026; BR-07185/2026",
        "governo": [45, 27],
        "governo2": [54, 35],
        "nao_escolha_gov": 15,
        "presidente": [37, 33],
        "presidente2": [47, 42],
        "paginas": "2, 8 e 10; Presidência: Folha de 22/08",
        "status": "PDF estadual; Presidência em notícia",
    },
    {
        "id": "rt_gov",
        "nome": "Real Time Big Data",
        "campo": "19 a 22/08",
        "divulgacao": "24/08/2026",
        "n": 2000,
        "me": 2,
        "metodo": "Telefone, segundo iG",
        "registro": "SP-01347/2026; BR-06537/2026",
        "governo": [52, 35],
        "nao_escolha_gov": 11,
        "presidente": [38, 33],
        "presidente2": [44, 49],
        "paginas": "iG e Metrópoles, 24/08",
        "status": "Notícias; PDF pendente",
        "nota": "Cenário presidencial inclui Marçal. Resultado de 2º turno desfavorável a Flávio reproduz a notícia; exige confirmação no PDF. Manchete e corpo do iG usam cenários distintos.",
    },
    {
        "id": "quaest",
        "nome": "Quaest",
        "campo": "21 a 24/08",
        "divulgacao": "25/08/2026",
        "n": 1800,
        "me": 2,
        "metodo": "Domiciliar presencial",
        "registro": "SP-06946/2026; BR-02096/2026",
        "governo": [40, 27],
        "governo2": [47, 30],
        "nao_escolha_gov": 27,
        "presidente": [30, 29],
        "paginas": "2, 8, 20 e 75",
        "status": "PDF conferido",
        "nota": "Presidência sem Marçal (cenário II). Com Marçal: Flávio 30 e Lula 30. Não há 2º turno presidencial neste PDF.",
    },
    {
        "id": "atlas",
        "nome": "Atlas/Estadão",
        "campo": "26 a 31/08",
        "divulgacao": "03/09/2026",
        "n": 1810,
        "me": 1,
        "metodo": "Recrutamento digital RDR",
        "registro": "SP-06964/2026; BR-02563/2026",
        "governo": [51.1, 39.9],
        "governo2": [53.2, 42.6],
        "nao_escolha_gov": 5.5,
        "presidente": [39.9, 36],
        "presidente2": [46.8, 43.3],
        "paginas": "5, 8, 12, 17 e 21",
        "status": "PDF conferido",
        "nota": "A p. 5 declara ±1 pp; o catálogo público da Atlas declara ±2 pp. Divergência preservada.",
    },
]


def native_blocks():
    doc = fitz.open(BASE / "fontes/datafolha.pdf")
    pages = []
    for i in range(19, len(doc)):
        raw = doc[i].get_text()
        blocks = []
        for text in re.split(r"Bloco (\d de \d[^\n]*)\n", raw):
            lines = [s.strip() for s in text.splitlines() if s.strip()]
            runs = []
            j = 0
            while j < len(lines):
                if re.fullmatch(r"\d+|[–—-]", lines[j]):
                    start = j
                    while j < len(lines) and re.fullmatch(r"\d+|[–—-]", lines[j]):
                        j += 1
                    if j - start >= 4:
                        runs.append(
                            {
                                "rotulo_contexto": lines[max(0, start - 2) : start],
                                "valores": [
                                    None if a in ("–", "—", "-") else int(a)
                                    for a in lines[start:j]
                                ],
                            }
                        )
                else:
                    j += 1
            if runs:
                blocks.append(runs)
        pages.append(
            {"pagina_pdf": i + 1, "texto": raw, "sequencias_numericas": blocks}
        )
    (BASE / "derivados/datafolha-anexo-integral.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2) + "\n"
    )
    # Parse the same question, in the block whose base belongs to that question.
    text = doc[26].get_text().split("Bloco 2")[0]

    def vals(label):
        s = text.split(label + "\n")[1]
        r = []
        for line in s.splitlines():
            if not line.isdigit():
                break
            r.append(int(line))
        assert len(r) == 11, (label, len(r))
        return r

    base = vals("Base ponderada")
    checks = {}
    for name in ["Tarcísio (REPUBLICANOS)", "Fernando Haddad (PT)"]:
        v = vals(name)
        checks[name] = {}
        for label, indices in [
            ("sexo", [1, 2]),
            ("idade", [3, 4, 5, 6, 7]),
            ("escolaridade", [8, 9, 10]),
        ]:
            got = sum(v[i] * base[i] for i in indices) / sum(base[i] for i in indices)
            checks[name][label] = {
                "recomposto": got,
                "publicado": v[0],
                "residuo_pp": got - v[0],
            }
            assert abs(got - v[0]) < 1
    return checks


def main():
    checks = {"datafolha_p27": native_blocks()}
    # Atlas p. 5 profile, p. 10 governor and p. 18 president. Visual transcription.
    checks["atlas"] = {}
    for name, expected, sex, income in [
        ("Tarcísio", 51.1, [56.7, 46], [64.1, 51.7, 53.8, 53, 35.4]),
        ("Flávio", 39.9, [40.1, 39.6], [59.7, 47.8, 41.8, 44.6, 11.5]),
    ]:
        checks["atlas"][name] = {}
        for label, values, weights in [
            ("sexo", sex, [46.3, 53.7]),
            ("renda", income, [13, 12.7, 23.9, 30.7, 19.8]),
        ]:
            got = sum(a * b for a, b in zip(values, weights, strict=True)) / sum(
                weights
            )
            checks["atlas"][name][label] = {
                "recomposto": got,
                "publicado": expected,
                "residuo_pp": got - expected,
            }
            assert abs(got - expected) < 0.3
    checks["quaest"] = {
        "Tarcísio_sexo": (34 * 53 + 46 * 47) / 100,
        "Haddad_sexo": (28 * 53 + 27 * 47) / 100,
        "Tarcísio_renda": (25 * 19 + 40 * 44 + 50 * 37) / 100,
        "Haddad_renda": (31 * 19 + 25 * 44 + 28 * 37) / 100,
    }
    files = []
    for p in sorted((BASE / "fontes").glob("*.pdf")):
        files.append(
            {
                "nome": p.name,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes": p.stat().st_size,
                "paginas": len(fitz.open(p)),
            }
        )
    data = {
        "corte": "2026-09-05",
        "pesquisas": POLLS,
        "urls": URLS,
        "validacoes": checks,
        "arquivos": files,
        "perfis_renda_sm": {
            "Quaest": [19, 44, 37],
            "Datafolha": [609 / 1610 * 100, 689 / 1610 * 100, 257 / 1610 * 100],
            "Datafolha_sem_renda_classificada": 55 / 1610 * 100,
        },
        "atlas_alternativos": {
            "Flávio": [46.8, 43.3, 9.9],
            "Caiado": [45.4, 41.1, 13.4],
            "Zema": [43.8, 42.7, 13.5],
            "Renan": [33.5, 43.1, 23.4],
        },
        "senado_quaest": {
            "Guilherme Derrite": [12, 17, 8],
            "Marina Silva": [12, 15, 9],
            "Simone Tebet": [11, 15, 7],
            "André do Prado": [7, 7, 7],
            "Salles": [4, 4, 5],
        },
        "senado_datafolha": {
            "Simone Tebet": 12,
            "Marina Silva": 12,
            "André do Prado": 10,
            "Guilherme Derrite": 7,
            "Ricardo Salles": 6,
        },
        "temas_quaest": {
            "Violência": 34,
            "Saúde": 22,
            "Economia": 8,
            "Educação": 6,
            "Corrupção": 4,
            "Desemprego": 4,
            "Pobreza/desigualdade": 3,
        },
        "temas_atlas": {
            "Criminalidade": 59.4,
            "Educação": 35.9,
            "Saúde": 29.2,
            "Violência contra a mulher": 19.9,
            "Impostos": 17.3,
            "Inflação": 15.4,
        },
        "limites": [
            "Datafolha recebido cobre governo, Senado e avaliação estadual; não contém tabelas presidenciais.",
            "Veritá julho: localizado em notícia, denominador a confirmar no relatório; excluído da comparação em votos totais.",
            "Futura: busca não confirmou relatório estadual recente comparável; pesquisa nacional não substitui SP.",
            "Sem microdados pareados de governo e Presidência, diferenças de margens não identificam voto combinado.",
        ],
    }
    (OUT / "sp_092026_pesquisas.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(checks, ensure_ascii=False))


if __name__ == "__main__":
    main()
