#!/usr/bin/env python3
"""Registra as quatro pesquisas de 17/09/2026 e prova a leitura dos PDFs.

Gerp/PoderData: tabelas extraídas do texto nativo. Atlas: transcrição visual
integral das pp. 17–18, com recomposição independente por sexo (p. 5).
Futura: perfil e placares arquivados; sem cruzamento por renda, sem ajuste.
"""

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLLS = ROOT / "analysis/reponderacao/pesquisas"
URLS = {
    "atlas": "https://cdn1.atlasintel.org/pesquisa_atlas_bloomberg__nacional_260916__e482014325df7284.pdf",
    "gerp": "https://static.poder360.com.br/uploads/2026/09/pesquisa-gerp-presidencia-republica-17set2026.pdf",
    "poderdata": "https://static.poder360.com.br/uploads/2026/09/poderdata-presidente-17set.pdf",
    "futura": "https://static.poder360.com.br/uploads/2026/09/Pesquisa-Presidente-Brasil-Futura-Setembro.pdf",
}
# Atlas pp.17–18, ordem: Lula, Flávio, Renan, Cury, Caiado, Zema,
# Samara, branco/nulo, não sei. Uma linha por faixa de renda da p.5.
ATLAS_ROWS = [
    [40.4, 45.8, 2.8, 2.4, 2.4, 0.5, 2.8, 3.0, 0.0],
    [38.4, 50.7, 5.7, 1.8, 1.2, 1.1, 0.2, 0.6, 0.4],
    [44.3, 44.8, 4.2, 3.4, 1.4, 0.8, 0.1, 0.7, 0.4],
    [42.8, 40.9, 7.2, 5.0, 1.6, 0.8, 0.2, 0.5, 0.8],
    [54.3, 26.4, 5.4, 3.5, 2.1, 2.8, 0.4, 4.4, 0.6],
]
ATLAS_SEX = [[34.2, 49.3], [52.7, 35.1]]  # p.17, homens/mulheres
PODER_SECOND_IMAGE = (
    "pd-pesquisa-eleitoral-intencao-presidente-16-set-2026-05-scaled.png"
)
PODER_ARTICLE = "https://www.poder360.com.br/poderdata/flavio-tem-46-e-lula-44-no-2o-turno-diz-poderdata-aya/"


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def template(slug, previous, start, end, registry, n):
    old = json.loads((POLLS / f"{slug}_{previous}.json").read_text())
    folder = ROOT / f"data/originals/{slug}_092026_17"
    pdf = folder / "relatorio.pdf"
    payload = pdf.read_bytes()
    assert payload.startswith(b"%PDF")
    text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    (folder / "relatorio.txt").write_text(text)
    pages = text.split("\f")
    source = {
        "tipo": "relatorio",
        "pdf": str(pdf.relative_to(ROOT)),
        "url": URLS[slug],
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "total_paginas": len(pages) - 1,
        "status": "Relatório completo conferido.",
    }
    poll = {k: old[k] for k in ["instituto", "contratante", "metodo", "renda"]}
    poll.update(
        id=f"{slug}_{end}",
        registro_tse=registry,
        n=n,
        campo={"inicio": start, "fim": end},
        divulgacao="2026-09-17",
        fonte=source,
        publicado={},
        cruzamentos={},
    )
    poll["renda"]["mes_precos"] = "202609"
    return poll, pages


def percentage_rows(page, count):
    """Lê linhas de percentuais com largura exata; não preenche células ausentes."""
    rows = []
    for line in page.splitlines():
        values = re.findall(r"(\d+)%", line)
        if len(values) == count and not line.strip().startswith("Total"):
            rows.append([int(v) for v in values])
    return rows


def native_table(options, rows, first, last, total):
    assert len(options) == len(rows), (options, rows)
    return (
        {
            "opcoes": options,
            "linhas": list(map(list, zip(*(r[first:last] for r in rows), strict=True))),
        },
        dict(zip(options, (r[total] for r in rows), strict=True)),
    )


def records():
    atlas, _ = template(
        "atlas", "2026-09-09", "2026-09-11", "2026-09-16", "BR-06221/2026", 5018
    )
    atlas["fonte"]["paginas"] = {
        "perfil_renda": 5,
        "1t_topline": 14,
        "1t_renda": "17–18",
        "2t_topline": 21,
    }
    atlas["fonte"][
        "nota"
    ] = "Íntegra baixada na aba Exclusive Polls da AtlasIntel. Cruzamentos das pp. 17–18 conferidos visualmente e recompostos por renda e sexo."
    atlas["renda"]["amostra_pct"] = [17.8, 12.4, 27.0, 26.3, 16.5]
    atlas["renda"][
        "nota"
    ] = "Perfil desta onda, p. 5, em renda familiar nominal. As cinco faixas somam 100%. Não reutiliza o perfil da onda de 09/09; a primeira faixa passou de 20,0% para 17,8%. Não há bases não ponderadas por renda."
    options = [
        "lula",
        "flavio",
        "renan_santos",
        "cury",
        "caiado",
        "zema",
        "samara",
        "branco_nulo",
        "indecisos",
    ]
    atlas["publicado"] = {
        "1t": dict(
            zip(options, [44.1, 41.7, 5.1, 3.5, 1.7, 1.1, 0.7, 1.6, 0.5], strict=True)
        ),
        "2t": {"lula": 46.8, "flavio": 47.2, "branco_nulo": 6.0},
    }
    atlas["cruzamentos"]["1t"] = {
        "opcoes": options,
        "linhas": ATLAS_ROWS,
        "nota": "Transcrição integral das faixas de renda das pp. 17–18. Arredondamentos mantidos; linhas somam de 99,8 a 100,1. Os nomes com 0% citados no rodapé da p.14 não têm linha no cruzamento.",
    }
    atlas["sem_cruzamento"] = {
        "2t": "As pp. 21–23 publicam cenários, votos válidos e série histórica, sem cruzamento por renda. Não se transfere o ajuste do 1º para o 2º turno."
    }

    gerp, gp = template(
        "gerp", "2026-09-08", "2026-09-14", "2026-09-16", "BR-00535/2026", 2400
    )
    gerp["contratante"] = "Gerp Mercadologia, recursos próprios"
    gerp["fonte"]["paginas"] = {
        "perfil_renda": 8,
        "1t_topline": 13,
        "1t_renda": 15,
        "2t_topline": 21,
        "2t_renda": 23,
    }
    gerp["renda"]["amostra_pct"] = [23, 23, 33, 14, 5, 2]
    gerp["renda"][
        "nota"
    ] = "Perfil ponderado da p. 8, conferido nesta onda. As pp. 15 e 23 declaram percentuais ponderados; as bases n = 511, 501, 803, 376, 146 e 63 são contagens não ponderadas e não substituem esse perfil. Cortes em salários mínimos de 2026 (R$ 1.621)."
    gerp_native = {}
    for turn, page, options in [
        (
            "1t",
            15,
            [
                "flavio",
                "lula",
                "cury",
                "caiado",
                "renan_santos",
                "zema",
                "marcal",
                "branco_nulo",
                "indecisos",
            ],
        ),
        ("2t", 23, ["flavio", "lula", "branco_nulo", "indecisos"]),
    ]:
        rows = percentage_rows(gp[page - 1], 14)
        table, pub = native_table(options, rows, 8, 14, 0)
        table["nota"] = (
            f"Extração programática da p. {page}, confirmada na página renderizada. Arredondamentos preservados."
        )
        gerp["cruzamentos"][turn], gerp["publicado"][turn] = table, pub
        gerp_native[turn] = rows
    gerp["fonte"][
        "nota"
    ] = "P. 15 exibe 9 de 13 categorias; as quatro omitidas têm 0% no total. Não imputamos células de renda para essas candidaturas. P. 7 declara confiança de 95%, enquanto p. 8 mostra 95,55%."

    poder, pp = template(
        "poderdata", "2026-09-02", "2026-09-13", "2026-09-16", "BR-00360/2026", 3000
    )
    poder["fonte"]["paginas"] = {
        "perfil_renda": 4,
        "1t_topline": 7,
        "1t_renda": 12,
        "2t_topline": 16,
    }
    poder["renda"]["amostra_pct"] = [46, 33, 21]
    poder["renda"][
        "nota"
    ] = "Perfil ponderado desta onda, p. 4: sem rendimentos até 2 SM = 46%; mais de 2 a 5 SM = 33%; mais de 5 SM = 21%. O cartão não imprime valores em reais; usamos o mínimo de 2026 (R$ 1.621)."
    options = [
        "lula",
        "flavio",
        "cury",
        "renan_santos",
        "caiado",
        "marcal",
        "hertz",
        "clariana",
        "zema",
        "rui",
        "edmilson",
        "samara",
        "grassi",
        "branco_nulo",
        "indecisos",
    ]
    table, pub = native_table(options, percentage_rows(pp[11], 4), 0, 3, 3)
    # Mantém a convenção das ondas anteriores: nomes menores em "outros".
    # Um topline arredondado a zero não permite ajuste individual subdecimal.
    minor = {"hertz", "clariana", "rui", "edmilson", "grassi"}
    keep = [c for c in options if c not in minor]
    columns = [options.index(c) for c in keep]
    grouped = [
        [row[i] for i in columns] + [sum(row[options.index(c)] for c in minor)]
        for row in table["linhas"]
    ]
    table = {"opcoes": [*keep, "outros"], "linhas": grouped}
    pub = {**{c: pub[c] for c in keep}, "outros": sum(pub[c] for c in minor)}
    table["nota"] = (
        "Todas as 15 opções extraídas do texto nativo da p. 12. Outros reúne Hertz Dias, Clariana Barão, Rui Costa Pimenta, Edmilson Costa e Wilson Grassi, como nas ondas anteriores, evitando inferência subdecimal para nomes com topline arredondado a zero. Colunas arredondadas somam 100%, 101% e 99%; não se inventa complemento para fechar 100%."
    )
    poder["cruzamentos"]["1t"], poder["publicado"]["1t"] = table, pub
    poder["publicado"]["2t"] = {
        "lula": 44,
        "flavio": 46,
        "branco_nulo": 8,
        "indecisos": 2,
    }
    image = ROOT / "data/originals/poderdata_092026_17" / PODER_SECOND_IMAGE
    poder["cruzamentos"]["2t"] = {
        "opcoes": ["lula", "flavio"],
        "linhas": [[50, 39], [35, 52], [42, 50]],
        "nota": "Imagem oficial de estratificação de Lula × Flávio, na matéria do Poder360 de 17/09. O PDF não traz este cruzamento. A imagem identifica o campo de 13 a 16/09 e BR-00360/2026. Só Lula e Flávio são medidos por faixa; não se imputam brancos ou indecisos.",
    }
    poder["fonte"]["complementos"] = [
        {
            "rotulo": "PoderData: estratificação do 2º turno por renda",
            "url": "https://static.poder360.com.br/uploads/2026/09/"
            + PODER_SECOND_IMAGE,
            "arquivo": str(image.relative_to(ROOT)),
            "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            "materia": PODER_ARTICLE,
            "localizador": "bloco renda familiar; campo 13–16/09/2026",
        }
    ]
    poder["fonte"][
        "nota"
    ] = "PDF localizado no catálogo público de mídia do Poder360, complementado pelo gráfico oficial de estratificação do 2º turno na matéria. O relatório declara 752 municípios; matéria e gráfico citam 623. Mantemos os metadados do documento e registramos a divergência."

    futura, _ = template(
        "futura", "2026-09-01", "2026-09-11", "2026-09-15", "BR-00749/2026", 2000
    )
    futura["contratante"] = "Futura/100% Cidades, recursos próprios segundo Poder360"
    futura["metodo"] = "telefônico, CATI, abrangência nacional"
    futura["fonte"]["paginas"] = {"perfil_renda": 7, "1t_topline": 22, "2t_topline": 26}
    futura["fonte"][
        "nota"
    ] = "PDF disponibilizado publicamente pelo Poder360; preservado como recebido, inclusive as marcas-d’água."
    futura["renda"]["amostra_pct"] = [28.2, 20.5, 23.9, 9.4, 5.1]
    futura["renda"][
        "nota"
    ] = "P. 7: cinco faixas de renda e 13,0% NS/NR. A soma impressa é 100,1% por arredondamento. NS/NR não é uma faixa."
    futura["publicado"] = {
        "1t": {
            "lula": 38.3,
            "flavio": 37.7,
            "cury": 6.5,
            "caiado": 4.5,
            "renan_santos": 3.4,
            "marcal": 1.9,
            "zema": 1.0,
            "samara": 0.2,
            "clariana": 0.1,
            "edmilson": 0.1,
            "grassi": 0.1,
            "hertz": 0,
            "rui": 0,
            "branco_nulo": 2.7,
            "indecisos": 3.4,
        },
        "2t": {"lula": 43.7, "flavio": 48.1, "branco_nulo": 6.5, "indecisos": 1.7},
    }
    futura["ignorar"] = True
    futura["motivo"] = (
        "O perfil de renda está na p. 7, mas o voto não é cruzado por renda: pp. 23–25 (1º turno) e p. 27 (Lula × Flávio no 2º turno) cruzam sexo, região, idade e posição política. Sem voto por faixa não há reponderação em nenhum turno."
    )
    return [atlas, gerp, poder, futura], gerp_native


def main():
    spec = importlib.util.spec_from_file_location(
        "engine", ROOT / "scripts/reponderacao-pnad.py"
    )
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    polls, gerp_native = records()
    audit = {"divulgacao": "2026-09-17", "pesquisas": []}
    for poll in polls:
        proof = {}
        if not poll.get("ignorar"):
            result = engine.process_poll(poll, engine.Benchmark(), engine.load_ipca())
            for turn, calculation in result["turnos"].items():
                assert calculation["residuo_max"] <= 1.5, (
                    poll["id"],
                    turn,
                    calculation,
                )
                proof[turn] = {
                    k: calculation[k]
                    for k in ["publicado", "recomposto", "residuo_max"]
                }
                if poll["instituto"] == "AtlasIntel":
                    independent = engine.compose(ATLAS_SEX, [46.7, 53.3])
                elif poll["instituto"] == "Gerp":
                    # Primeiras duas linhas do PDF são Flávio/Lula; devolve Lula/Flávio.
                    rows = gerp_native[turn]
                    independent = engine.compose(
                        [[rows[1][i], rows[0][i]] for i in [1, 2]], [47, 53]
                    )
                elif poll["instituto"] == "PoderData" and turn == "2t":
                    independent = engine.compose([[37, 54], [51, 38]], [47, 53])
                else:
                    independent = None
                if independent:
                    proof[turn]["recomposto_sexo_lula_flavio"] = [
                        round(x, 4) for x in independent
                    ]
                    assert (
                        max(
                            abs(v - poll["publicado"][turn][c])
                            for c, v in zip(
                                ["lula", "flavio"], independent, strict=True
                            )
                        )
                        < 1.5
                    )
        dump(POLLS / f"{poll['id']}.json", poll)
        audit["pesquisas"].append(
            {
                "id": poll["id"],
                "fonte": poll["fonte"],
                "provas": proof,
                "turnos_reponderaveis": list(poll["cruzamentos"]),
            }
        )
        print(poll["id"], proof)
    dump(ROOT / "analysis/reponderacao/auditoria_20260917.json", audit)


if __name__ == "__main__":
    main()
