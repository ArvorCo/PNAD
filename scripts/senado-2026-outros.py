#!/usr/bin/env python3
"""Valida os JSONs de pesquisas de Senado e resume a cobertura dos institutos que não são Datafolha nem Quaest.

Os valores transcritos ficam em analysis/senado_2026/pesquisas/*.json (um por onda) e as
referências não transcritas em analysis/senado_2026/referencias_nao_transcritas.json.
Uso:
    python3 scripts/senado-2026-outros.py            # valida e imprime a tabela
    python3 scripts/senado-2026-outros.py --cobertura  # também grava cobertura_outros.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "analysis" / "senado_2026"
PESQUISAS = PASTA / "pesquisas"
REFERENCIAS = PASTA / "referencias_nao_transcritas.json"
COBERTURA = PASTA / "cobertura_outros.json"
CORTE_RECENTE = "2026-09-28"
EXCLUIDOS = {"datafolha", "quaest"}
UFS = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
]
OBRIGATORIOS = (
    "instituto",
    "instituto_slug",
    "uf",
    "cargo",
    "campo",
    "n",
    "fonte",
    "pergunta",
    "candidatos",
)


def data_iso(texto: object) -> date:
    return date.fromisoformat(str(texto))


def soma_declarada(doc: dict) -> float:
    """Soma de candidatos, indecisos, branco/nulo e outros, como o relatório publica."""
    total = sum(c["valor"] for c in doc["candidatos"])
    for chave in ("indecisos", "branco_nulo", "outros"):
        total += doc.get(chave) or 0
    return round(total, 2)


def validar(doc: dict) -> list[str]:
    """Devolve a lista de problemas de esquema de uma onda (vazia quando está correta)."""
    erros = [f"falta {k}" for k in OBRIGATORIOS if k not in doc]
    if erros:
        return erros
    if doc["uf"] not in UFS:
        erros.append(f"UF inválida {doc['uf']}")
    if doc["campo"] is not None:
        ini, fim = data_iso(doc["campo"]["inicio"]), data_iso(doc["campo"]["fim"])
        if fim < ini:
            erros.append("campo com fim anterior ao início")
    if doc.get("divulgacao"):
        data_iso(doc["divulgacao"])
    for c in doc["candidatos"]:
        partido = c.get("partido")
        if partido is not None and partido != partido.upper():
            erros.append(f"partido fora de caixa alta: {partido}")
        if not isinstance(c.get("valor"), (int, float)):
            erros.append(f"valor ausente em {c.get('nome')}")
    perg = doc["pergunta"]
    if perg.get("base") == "validos" or perg.get("soma_total") is None:
        return erros
    dif = abs(soma_declarada(doc) - perg["soma_total"])
    limite = 3 if perg["votos_por_eleitor"] == 1 else 1
    if dif > limite:
        erros.append(f"soma_total {perg['soma_total']} difere de {soma_declarada(doc)}")
    return erros


def carregar() -> list[tuple[Path, dict]]:
    return [
        (p, json.loads(p.read_text(encoding="utf-8")))
        for p in sorted(PESQUISAS.glob("*.json"))
    ]


def recente(doc: dict) -> bool:
    return bool(doc["campo"]) and doc["campo"]["fim"] >= CORTE_RECENTE


def resumo(doc: dict, arquivo: Path) -> dict:
    return {
        "arquivo": arquivo.name,
        "instituto": doc["instituto"],
        "campo": doc["campo"],
        "registro_tse": doc.get("registro_tse"),
        "n": doc["n"],
        "votos_por_eleitor": doc["pergunta"]["votos_por_eleitor"],
        "soma_total": doc["pergunta"]["soma_total"],
        "pagina": doc["fonte"].get("pagina"),
        "url": doc["fonte"].get("url"),
    }


def cobertura(ondas: list[tuple[Path, dict]]) -> dict:
    refs = (
        json.loads(REFERENCIAS.read_text(encoding="utf-8"))
        if REFERENCIAS.exists()
        else []
    )
    saida = {}
    for uf in UFS:
        proprias = [
            (p, d)
            for p, d in ondas
            if d["uf"] == uf and d["instituto_slug"] not in EXCLUIDOS
        ]
        achadas = [resumo(d, p) for p, d in proprias if recente(d)]
        antigas = [resumo(d, p) for p, d in proprias if not recente(d)]
        saida[uf] = {
            "recentes_transcritas": achadas,
            "anteriores_a_28_09_transcritas": antigas,
            "existem_nao_transcritas": [r for r in refs if r["uf"] == uf],
            "situacao": (
                "recente" if achadas else "sem_pesquisa_recente_de_outros_institutos"
            ),
        }
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--cobertura", action="store_true", help="grava cobertura_outros.json"
    )
    args = ap.parse_args()
    ondas = carregar()
    problemas = 0
    linhas = []
    for arquivo, doc in ondas:
        erros = validar(doc)
        if erros:
            problemas += 1
            print(f"ERRO {arquivo.name}: {'; '.join(erros)}", file=sys.stderr)
        if doc["instituto_slug"] in EXCLUIDOS:
            continue
        campo = doc["campo"]["fim"] if doc["campo"] else "sem data"
        linhas.append(
            (
                doc["instituto"],
                doc["uf"],
                campo,
                doc["pergunta"]["soma_total"],
                doc["pergunta"]["votos_por_eleitor"],
            )
        )
    print(
        f"{'instituto':<22}{'UF':<4}{'fim do campo':<14}{'soma':>7}{'votos/eleitor':>15}"
    )
    for inst, uf, campo, soma, vpe in sorted(linhas, key=lambda x: (x[1], x[2])):
        print(f"{inst:<22}{uf:<4}{campo:<14}{soma:>7}{vpe:>15}")
    cob = cobertura(ondas)
    sem = [uf for uf, v in cob.items() if v["situacao"] != "recente"]
    print(f"\nSem pesquisa recente de outros institutos ({len(sem)}): {' '.join(sem)}")
    if args.cobertura:
        COBERTURA.write_text(
            json.dumps(
                {"corte": CORTE_RECENTE, "ufs": cob}, ensure_ascii=False, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"gravado {COBERTURA.relative_to(RAIZ)}")
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
