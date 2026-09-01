#!/usr/bin/env python3
"""Compara a pauta tematica dos questionarios Datafolha de maio a agosto de 2026.

Le os quatro questionarios registrados no TSE, extrai cada bloco de pergunta do
texto nativo do PDF e classifica os blocos em categorias declaradas aqui. A
classificacao e nossa e esta aberta; a extracao nao tem digitacao manual.

A pergunta que o modulo responde e simples: em quais ondas o instituto mediu o
efeito eleitoral de um fato concreto, e em quais nao mediu.

Uso:
  python3 scripts/datafolha-082026-pauta.py

Saidas:
  analysis/datafolha_082026/pauta.json
  docs/assets/datafolha_082026_pauta.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / "data" / "originals"
ANALYSIS = ROOT / "analysis" / "datafolha_082026"
ASSETS = ROOT / "docs" / "assets"

ONDAS = [
    (
        "2026-05",
        "20–21/mai",
        ORIGINALS / "datafolha_052026" / "QuestionarioDatafolha052026.pdf",
    ),
    (
        "2026-06",
        "17–18/jun",
        ORIGINALS / "datafolha_062026" / "QuestionarioDatafolha062026.pdf",
    ),
    (
        "2026-07",
        "22–23/jul",
        ORIGINALS / "datafolha_072026" / "QuestionarioDatafolha072026.pdf",
    ),
    (
        "2026-08",
        "18–19/ago",
        ORIGINALS / "datafolha_082026" / "DatafolhaQuestionario082026.pdf",
    ),
]

# Nomes proprios de agentes politicos. Uma pergunta que cita um deles e pede
# juizo sobre um fato e o que chamamos aqui de pergunta de caso.
AGENTES = [
    "flavio bolsonaro",
    "jair bolsonaro",
    "daniel vorcaro",
    "alexandre de moraes",
    "donald trump",
    "michelle bolsonaro",
    "eduardo bolsonaro",
]

# Blocos tematicos de cada onda, declarados a partir da leitura dos PDFs.
# "caso" = mede o efeito eleitoral de um fato concreto com pessoas nomeadas.
PAUTA = {
    "2026-05": [
        (
            "caso",
            "Flávio Bolsonaro e Daniel Vorcaro",
            ["P.3", "P.4", "P.5", "P.6", "P.7", "P.8", "P.9"],
        ),
        (
            "consumo",
            "Apostas online, cassinos e endividamento",
            ["P.10", "P.11", "P.12", "P.13", "P.14", "P.15", "P.16", "P.17", "P.18"],
        ),
    ],
    "2026-06": [
        ("caso", "Apoio de Donald Trump a um candidato", ["P.4"]),
        (
            "caso",
            "Influência de Flávio Bolsonaro na decisão dos EUA sobre facções",
            ["P.14", "P.15"],
        ),
        (
            "politica",
            "Memória de voto de 2022 e conhecimento do Congresso",
            ["P.5a", "P.5b", "P.5c", "P.6a", "P.6b", "P.7", "P.8"],
        ),
        (
            "politica",
            "Economia, facções e maioridade penal",
            ["P.9", "P.10", "P.11", "P.12", "P.13", "P.16", "P.17", "P.18"],
        ),
        (
            "consumo",
            "Inteligência artificial",
            ["P.19", "P.20", "P.21", "P.22", "P.23", "P.24", "P.25"],
        ),
    ],
    "2026-07": [
        (
            "caso",
            "Prisão domiciliar de Jair Bolsonaro e decisões de Alexandre de Moraes",
            ["P.5", "P.6", "P.7"],
        ),
        (
            "caso",
            "Tarifas dos EUA e atribuição de culpa entre Lula e Flávio Bolsonaro",
            ["P.8", "P.9", "P.10", "P.11", "P.12", "P.13"],
        ),
        (
            "politica",
            "Principal problema do país e influência familiar no voto",
            ["P.3", "P.14a", "P.14b", "P.15"],
        ),
        (
            "consumo",
            "Copa do Mundo, seleção, Ancelotti e apostas",
            ["P.16", "P.17", "P.18", "P.19", "P.20", "P.21", "P.22", "P.23", "P.24"],
        ),
        ("politica", "Religiosidade declarada", ["P.25"]),
    ],
    "2026-08": [
        (
            "politica",
            "Interferência estrangeira, comparecimento e interesse por política",
            ["P.2", "P.3", "P.4"],
        ),
    ],
}

PUBLICADAS = {
    "2026-08": {
        "P.2": False,
        "P.3": False,
        "P.4": False,
    }
}

ROTULO = {
    "caso": "mede o efeito de um fato concreto, com pessoas nomeadas",
    "politica": "tema político geral, sem caso nomeado",
    "consumo": "consumo, entretenimento e comportamento",
}


def sem_acento(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn").lower()


def texto_do_pdf(caminho: Path) -> str:
    documento = fitz.open(caminho)
    conteudo = "\n".join(documento[i].get_text() for i in range(documento.page_count))
    documento.close()
    return conteudo


# Um bloco termina no proximo marcador de pergunta, seja ele "P.n" ou um
# identificador em caixa alta como VOTOSEGT22 ou ESCALA_BP. Sem isso o ultimo
# P.n engole o resto do arquivo, inclusive o cartao de candidatos.
MARCADOR = re.compile(
    r"^\s*(P\.\d+[a-c]?\.?|[A-ZÇÃÕÁÉÍÓÚÂÊÔ][A-ZÇÃÕÁÉÍÓÚÂÊÔ_0-9]{3,})[\s\.]",
    flags=re.MULTILINE,
)
PERGUNTA = re.compile(r"^P\.\d+[a-c]?$")


def blocos_de_pergunta(texto: str) -> dict[str, str]:
    """Mapeia P.n -> enunciado, do texto nativo do questionario."""
    marcas = list(MARCADOR.finditer(texto))
    blocos: dict[str, str] = {}
    for indice, marca in enumerate(marcas):
        chave = marca.group(1).rstrip(".")
        if not PERGUNTA.match(chave):
            continue
        fim = marcas[indice + 1].start() if indice + 1 < len(marcas) else len(texto)
        blocos.setdefault(chave, " ".join(texto[marca.start() : fim].split()))
    return blocos


def main() -> None:
    ondas = []
    for identificador, rotulo, caminho in ONDAS:
        texto = texto_do_pdf(caminho)
        blocos = blocos_de_pergunta(texto)
        # Agentes contados apenas dentro dos enunciados P.n. Fora deles, os nomes
        # aparecem no cartao de candidatos e na pergunta de memoria de 2022, o
        # que nao caracteriza pergunta de caso.
        sem = sem_acento(" ".join(blocos.values()))
        modulos = []
        for categoria, titulo, perguntas in PAUTA.get(identificador, []):
            presentes = [p for p in perguntas if p in blocos]
            modulos.append(
                {
                    "categoria": categoria,
                    "rotulo_categoria": ROTULO[categoria],
                    "titulo": titulo,
                    "perguntas": presentes,
                    "quantidade": len(presentes),
                    "publicadas": [
                        p
                        for p in presentes
                        if PUBLICADAS.get(identificador, {}).get(p, True)
                    ],
                    "enunciados": {p: blocos[p][:400] for p in presentes},
                }
            )
        ondas.append(
            {
                "id": identificador,
                "label": rotulo,
                "arquivo": caminho.name,
                "palavras_no_questionario": len(texto.split()),
                "agentes_citados": sorted({a for a in AGENTES if a in sem}),
                "modulos": modulos,
                "perguntas_de_caso": sum(
                    m["quantidade"] for m in modulos if m["categoria"] == "caso"
                ),
                "perguntas_tematicas": sum(m["quantidade"] for m in modulos),
                "perguntas_tematicas_publicadas": sum(
                    len(m["publicadas"]) for m in modulos
                ),
            }
        )

    payload = {
        "pergunta": (
            "Em quais ondas o Datafolha mediu o efeito eleitoral de um fato concreto, "
            "e em quais nao mediu nenhum."
        ),
        "metodo": (
            "Extracao dos blocos P.n do texto nativo dos quatro questionarios registrados "
            "no TSE. A classificacao em caso, tema politico e consumo e declarada no script "
            "e pode ser contestada linha a linha; os enunciados vao junto."
        ),
        "categorias": ROTULO,
        "ondas": ondas,
        "resumo": {
            "perguntas_de_caso_por_onda": {
                o["label"]: o["perguntas_de_caso"] for o in ondas
            },
            "perguntas_tematicas_por_onda": {
                o["label"]: o["perguntas_tematicas"] for o in ondas
            },
            "palavras_por_onda": {
                o["label"]: o["palavras_no_questionario"] for o in ondas
            },
        },
        "leitura": (
            "Maio dedicou sete perguntas a um unico caso envolvendo o candidato de oposicao, "
            "incluindo se ele deveria retirar a candidatura e a quem deveria transferir apoio. "
            "Julho dedicou nove a prisao de Jair Bolsonaro, as decisoes de Alexandre de Moraes "
            "e a atribuicao de culpa pelas tarifas. Agosto nao dedicou nenhuma a fato algum, e "
            "as tres unicas perguntas tematicas que aplicou nao foram publicadas."
        ),
    }

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    texto_json = json.dumps(payload, ensure_ascii=False, indent=2)
    (ANALYSIS / "pauta.json").write_text(texto_json + "\n", encoding="utf-8")
    (ASSETS / "datafolha_082026_pauta.json").write_text(
        texto_json + "\n", encoding="utf-8"
    )

    for onda in ondas:
        print(
            f"{onda['label']}  {onda['palavras_no_questionario']:>5} palavras  "
            f"temáticas {onda['perguntas_tematicas']:>2}  "
            f"de caso {onda['perguntas_de_caso']:>2}  "
            f"agentes: {', '.join(onda['agentes_citados']) or 'nenhum'}"
        )


if __name__ == "__main__":
    main()
