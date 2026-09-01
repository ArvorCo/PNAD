#!/usr/bin/env python3
"""Quando cada documento da pesquisa passou a existir, nas quatro ondas.

Todo PDF carrega no proprio arquivo a data em que foi produzido. Este modulo le
esse metadado nos questionarios, anexos territoriais e relatorios completos das
ondas de maio a agosto de 2026 e compara com as datas de campo e de divulgacao.

A leitura e literal: um arquivo criado no dia 24 nao podia estar disponivel no
dia 21. O metadado nao diz quando o arquivo foi publicado, diz o instante antes
do qual ele nao existia.

Uso:
  python3 scripts/datafolha-082026-documentos.py

Saidas:
  analysis/datafolha_082026/documentos.json
  docs/assets/datafolha_082026_documentos.json
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / "data" / "originals"
ANALYSIS = ROOT / "analysis" / "datafolha_082026"
ASSETS = ROOT / "docs" / "assets"

ONDAS = [
    {
        "id": "2026-05",
        "label": "20–21/mai",
        "pasta": "datafolha_052026",
        "campo": ["2026-05-20", "2026-05-21"],
        "divulgacao": "2026-05-22",
    },
    {
        "id": "2026-06",
        "label": "17–18/jun",
        "pasta": "datafolha_062026",
        "campo": ["2026-06-17", "2026-06-18"],
        "divulgacao": "2026-06-19",
    },
    {
        "id": "2026-07",
        "label": "22–23/jul",
        "pasta": "datafolha_072026",
        "campo": ["2026-07-22", "2026-07-23"],
        "divulgacao": "2026-07-24",
    },
    {
        "id": "2026-08",
        "label": "18–19/ago",
        "pasta": "datafolha_082026",
        "campo": ["2026-08-18", "2026-08-19"],
        "divulgacao": "2026-08-21",
    },
]

TIPOS = {
    "questionario": "Questionário aplicado",
    "relatorio": "Relatório completo",
    "bairros": "Anexo de municípios e bairros",
}

DATA_PDF = re.compile(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})?")


def criado_em(caminho: Path) -> datetime | None:
    documento = fitz.open(caminho)
    metadados = documento.metadata or {}
    documento.close()
    achado = DATA_PDF.match(str(metadados.get("creationDate") or ""))
    if not achado:
        return None
    ano, mes, dia, hora, minuto = (int(achado.group(i)) for i in range(1, 6))
    return datetime(ano, mes, dia, hora, minuto)


def tipo_do_arquivo(nome: str) -> str | None:
    minusculo = nome.lower()
    for chave in TIPOS:
        if chave in minusculo:
            return chave
    return None


def main() -> None:
    ondas = []
    for onda in ONDAS:
        divulgacao = date.fromisoformat(onda["divulgacao"])
        documentos = []
        for pdf in sorted((ORIGINALS / onda["pasta"]).glob("*.pdf")):
            chave = tipo_do_arquivo(pdf.name)
            if not chave:
                continue
            instante = criado_em(pdf)
            if instante is None:
                continue
            atraso = (instante.date() - divulgacao).days
            documentos.append(
                {
                    "tipo": chave,
                    "rotulo": TIPOS[chave],
                    "arquivo": pdf.name,
                    "criado_em": instante.isoformat(timespec="minutes"),
                    "dias_apos_divulgacao": atraso,
                    "existia_na_divulgacao": atraso <= 0,
                }
            )
        relatorio = next((d for d in documentos if d["tipo"] == "relatorio"), None)
        ondas.append(
            {
                **{k: onda[k] for k in ("id", "label", "campo", "divulgacao")},
                "documentos": sorted(documentos, key=lambda d: d["criado_em"]),
                "atraso_do_relatorio_em_dias": (
                    relatorio["dias_apos_divulgacao"] if relatorio else None
                ),
            }
        )

    atrasos = [
        o["atraso_do_relatorio_em_dias"]
        for o in ondas
        if o["atraso_do_relatorio_em_dias"] is not None
    ]
    payload = {
        "pergunta": (
            "Em que momento passou a existir o documento que permite conferir a "
            "manchete, comparado com o momento em que a manchete foi publicada."
        ),
        "metodo": (
            "Leitura do campo creationDate do proprio PDF, que registra quando o "
            "arquivo foi produzido. Nao informa a data de publicacao; estabelece o "
            "instante antes do qual o arquivo nao existia."
        ),
        "ondas": ondas,
        "resumo": {
            "atraso_do_relatorio_por_onda": {
                o["label"]: o["atraso_do_relatorio_em_dias"] for o in ondas
            },
            "ondas_com_relatorio_disponivel_na_divulgacao": sum(
                1 for a in atrasos if a <= 0
            ),
            "total_de_ondas": len(atrasos),
            "atraso_minimo": min(atrasos) if atrasos else None,
            "atraso_maximo": max(atrasos) if atrasos else None,
        },
        "leitura": (
            "Nas quatro ondas o questionario ficou pronto antes do campo e o anexo "
            "territorial no dia da divulgacao ou no seguinte. O relatorio completo, "
            "que traz as tabelas cruzadas, o perfil da amostra e as margens por "
            "recorte, foi produzido tres dias depois da divulgacao em todas elas. "
            "Durante esses tres dias a discussao publica corre sobre dois numeros e "
            "o documento que permite conferí-los ainda nao existe."
        ),
    }

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(payload, ensure_ascii=False, indent=2)
    (ANALYSIS / "documentos.json").write_text(texto + "\n", encoding="utf-8")
    (ASSETS / "datafolha_082026_documentos.json").write_text(
        texto + "\n", encoding="utf-8"
    )

    for onda in ondas:
        print(
            f"\n{onda['label']}  campo {onda['campo'][0]} a {onda['campo'][1]}  divulgação {onda['divulgacao']}"
        )
        for documento in onda["documentos"]:
            sinal = "+" if documento["dias_apos_divulgacao"] > 0 else ""
            print(
                f"   {documento['rotulo']:<32} criado {documento['criado_em']}  "
                f"({sinal}{documento['dias_apos_divulgacao']} dias)"
            )
    print(
        f"\natraso do relatório completo: {payload['resumo']['atraso_do_relatorio_por_onda']}"
    )


if __name__ == "__main__":
    main()
