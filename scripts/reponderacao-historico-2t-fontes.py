#!/usr/bin/env python3
"""Arquiva transcrições conferidas em 20/10; uso exclusivo nos gráficos históricos.

Não altera fichas de cálculo, centrais, o arquivo do primeiro turno ou snapshots.
Os PDFs já baixados ficam em data/originals/historico_2t_20261020; as cinco
íntegras Gerp anteriores estão nos caminhos das fichas originais.
"""

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/originals/historico_2t_20261020"
PUBLIC = ROOT / "docs/fontes/historico_2t"
OUTPUT = ROOT / "analysis/reponderacao/historico_2t/complementos.json"
MEIO = "https://www.canalmeio.com.br/wp-content/uploads/2026/"

# Campo inicial/final, divulgação, registro, página e F/L/BN/I lidos na imagem.
MEIO_ROWS = [
    (
        "01-08",
        "01-12",
        "01-13",
        "06731",
        "01/Pesquisa-Meio-Ideia-Janeiro.pdf",
        14,
        2000,
        [36, 46.2, 9.8, 8],
    ),
    (
        "01-30",
        "02-02",
        "02-04",
        "08425",
        "02/Pesquisa-Meio_Ideia-Fevereiro-2026-2.pdf",
        18,
        1500,
        [41.1, 45.8, 7.4, 5.7],
    ),
    (
        "03-06",
        "03-10",
        "03-11",
        "00386",
        "03/Pesquisa-Meio_Ideia-Marco-2026.pdf",
        25,
        1500,
        [45.3, 47.4, 4.1, 3.2],
    ),
    (
        "04-03",
        "04-07",
        "04-08",
        "00605",
        "04/Pesquisa-Meio_Ideia-Abril-2026.pdf",
        13,
        1500,
        [45.8, 45.5, 6.6, 2.1],
    ),
    (
        "05-01",
        "05-05",
        "05-06",
        "05356",
        "05/Pesquisa-Meio_Ideia-Maio-1.pdf",
        39,
        1500,
        [45.3, 44.7, 6.5, 3.5],
    ),
    (
        "05-23",
        "05-27",
        "05-28",
        "02918",
        "05/Pesquisa-Meio_Ideia-Maio-2.pdf",
        8,
        1500,
        [41.4, 46.5, 7.1, 5.1],
    ),
    (
        "07-03",
        "07-06",
        "07-08",
        "05628",
        "07/Pesquisa-Meio_Ideia-Julho.pdf",
        8,
        1500,
        [40, 45, 10.5, 4.5],
    ),
    (
        "07-31",
        "08-03",
        "08-05",
        "04579",
        "08/Pesquisa-Meio_Ideia-Agosto-1.pdf",
        38,
        1500,
        [43, 48.5, 4, 4.5],
    ),
]
GERP_ROWS = [
    ("2026-05-12", 19, [50, 43, 5, 3]),
    ("2026-05-21", 15, [47, 44, 7, 2]),
    ("2026-06-05", 19, [44.7, 39.1, 13.1, 3.2]),
    ("2026-06-18", 19, [41.5, 40.2, 14.8, 3.5]),
    ("2026-07-17", 23, [46, 45, 8, 1]),
]
PARANA_ROWS = [
    (
        "01-25",
        "01-28",
        "01-29",
        "08254",
        "https://static.poder360.com.br/2026/03/paranapesquisas_Nacional_Jan26.pdf",
        17,
        [42.2, 44.8, 8.3, 4.7],
    ),
    (
        "02-22",
        "02-25",
        "02-27",
        "07974",
        "https://static.poder360.com.br/2026/02/ParanPesquisas-Nacional-fev26.pdf",
        16,
        [44.4, 43.8, 6.9, 5],
    ),
    (
        "03-25",
        "03-28",
        "03-30",
        "00873",
        "https://paranapesquisas.com.br/wp-content/uploads/2026/03/Nacional_Mar26-3.pdf",
        12,
        [45.2, 44.1, 6.2, 4.5],
    ),
]


def archive(path, name, url, page=None):
    target = PUBLIC / name
    if path.exists():
        shutil.copyfile(path, target)
    elif not target.exists():
        raise FileNotFoundError(f"Baixe {url} para {path}")
    content = target.read_bytes()
    return {
        "arquivo": str(target.relative_to(ROOT)),
        "url": url,
        "url_publica": "fontes/historico_2t/"
        + name
        + (f"#page={page}" if page else ""),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "paginas": {"2t": page} if page else {},
        "conferido_em": "2026-10-20",
        "conferencia": (
            "PDF renderizado e lido visualmente"
            if page
            else "Matéria do contratante, texto integral"
        ),
    }


def published(values):
    return {
        "2t": dict(
            zip(("flavio", "lula", "branco_nulo", "indecisos"), values, strict=True)
        )
    }


def metadata(prefix, institute, start, end, release, registration, n):
    return {
        "id": f"{prefix}_2026-{end}",
        "instituto": institute,
        "campo": {"inicio": "2026-" + start, "fim": "2026-" + end},
        "divulgacao": "2026-" + release,
        "registro_tse": f"BR-{registration}/2026" if registration else None,
        "n": n,
    }


def main():
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows = []
    for end, page, values in GERP_ROWS:
        old = json.loads(
            (ROOT / f"analysis/reponderacao/pesquisas/gerp_{end}.json").read_text()
        )
        rows.append(
            {
                **{
                    key: old[key]
                    for key in (
                        "id",
                        "instituto",
                        "campo",
                        "divulgacao",
                        "registro_tse",
                        "n",
                    )
                },
                "publicado": published(values),
                "fonte": archive(
                    ROOT / old["fonte"]["pdf"],
                    f"gerp_{end}.pdf",
                    old["fonte"]["url"],
                    page,
                ),
                "nota": "Simulação nacional Flávio × Lula. Consolidado do relatório, sobre o total; valores preservados mesmo quando o arredondamento não soma 100. Nenhum deles é mantido na rubrica de não escolha. Não foi calculado ajuste PNAD para esta pergunta. Em junho, o consolidado decimal difere do gráfico inteiro da página seguinte; a série usa o consolidado decimal.",
            }
        )
    for start, end, release, reg, filename, page, n, values in MEIO_ROWS:
        rows.append(
            {
                **metadata("meio_ideia", "Meio/Ideia", start, end, release, reg, n),
                "publicado": published(values),
                "fonte": archive(
                    INPUT / filename.split("/")[-1],
                    "meio_ideia_2026-" + end + ".pdf",
                    MEIO + filename,
                    page,
                ),
                "nota": "Simulação nacional estimulada Flávio × Lula. Transcrição visual do total; nenhuma preferência ou distribuição de renda de outra onda é transportada. Catálogo: https://www.canalmeio.com.br/pesquisa-meio-ideia/.",
            }
        )
    for start, end, release, reg, url, page, values in PARANA_ROWS:
        rows.append(
            {
                **metadata(
                    "parana", "Paraná Pesquisas", start, end, release, reg, 2080
                ),
                "publicado": published(values),
                "fonte": archive(
                    INPUT / url.split("/")[-1], "parana_2026-" + end + ".pdf", url, page
                ),
                "nota": "Simulação nacional estimulada Flávio × Lula; valores sobre o total. Nenhum/branco/nulo é mantido em não escolha. Apenas as ondas de 2026 com campo conferido são transcritas; a tabela retrospectiva também mostra meses de 2025, sem datas de campo. Não foi calculado ajuste PNAD.",
            }
        )
    url = "https://tmc.com.br/politica/pesquisa-alfa-inteligencia-tmc-lula-lidera-segundo-turno-contra-flavio-bolsonaro-por-48-a-41/"
    rows.append(
        {
            **metadata(
                "alfa", "Alfa Inteligência/TMC", "07-23", "07-28", "07-31", None, 2700
            ),
            "publicado": published([41, 48, 10, 1]),
            "fonte": archive(
                INPUT / "alfa-julho.html", "alfa_2026-07-28.html.txt", url
            ),
            "nota": "Matéria do contratante TMC. Cenário Flávio × Lula 41/48; não confundir com Caiado × Lula 40/45. Registro não informado na matéria. Sem ajuste PNAD nesta transcrição.",
        }
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "conferido_em": "2026-10-20",
                "contrato": "Complementos documentais somente do histórico nacional Flávio × Lula de 2026. Não alimentam médias/projeções nem alteram arquivos ou snapshots. Totais e válidos não se misturam. Sem ajuste PNAD quando não calculado com os dados da própria onda.",
                "pesquisas": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"{len(rows)} complementos e documentos arquivados em {PUBLIC}")


if __name__ == "__main__":
    main()
