#!/usr/bin/env python3
"""Converte as transcrições de governador já feitas para o mapa do voto útil
(analysis/voto_util/outros/*.json: Real Time Big Data, AtlasIntel, PoderData e
Instituto França, campo de setembro) para o esquema de uma pesquisa por onda de
analysis/governador_2026/CONTRATO.md. Nenhum número é redigitado: tudo sai do
JSON de origem, que cita PDF, página e SHA-256.

Quaest e Datafolha ficam de fora porque o painel do G1 (senado-2026-g1.py
--cargo governador) traz a série completa das duas casas.

    python3 scripts/governador-2026-acervo.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGEM = ROOT / "analysis/voto_util/outros"
DESTINO = ROOT / "analysis/governador_2026/pesquisas"
SLUGS = {
    "realtimebigdata": "realtime",
    "atlasintel": "atlas",
    "poderdata": "poderdata",
    "franca": "franca",
}
NAO_CANDIDATO = {"Branco/nulo", "Indecisos", "Outros", "pagina", "soma", "nota"}


def campo(texto: str | None) -> dict | None:
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2}) a (\d{4}-\d{2}-\d{2})", texto or "")
    return {"inicio": m.group(1), "fim": m.group(2)} if m else None


def metodo(texto: str | None) -> str:
    t = (texto or "").lower()
    if "presencial" in t or "domicil" in t:
        return "presencial"
    if "telefon" in t or "ivr" in t:
        return "telefonico"
    if "online" in t or "painel" in t or "digital" in t or "rdr" in t:
        return "online"
    return "nao informado"


def partido(sigla: str | None) -> str | None:
    if not sigla:
        return None
    return sigla.upper().replace("PC DO B", "PCDOB")


def bloco_1t(g: dict) -> dict:
    return {
        "candidatos": [
            {
                "nome": c["nome"],
                "partido": partido(c.get("partido")),
                "valor": c["valor"],
            }
            for c in g["candidatos"]
        ],
        "indecisos": g.get("Indecisos"),
        "branco_nulo": g.get("Branco/nulo"),
        "outros": g.get("Outros"),
    }


def pares_2t(g2: dict | None, por_nome: dict[str, str | None]) -> list[dict]:
    if not g2:
        return []
    saida = []
    for c in g2.get("cenarios", []):
        nomes = [k for k in c if k not in NAO_CANDIDATO]
        if len(nomes) != 2:
            continue
        saida.append(
            {
                "codigo": "SEGUNDO-TURNO",
                "pagina": c.get("pagina"),
                "candidatos": [
                    {"nome": n, "partido": por_nome.get(n), "valor": c[n]}
                    for n in nomes
                ],
                "indecisos": c.get("Indecisos"),
                "branco_nulo": c.get("Branco/nulo"),
                "soma_total": round(
                    sum(c[n] for n in nomes)
                    + (c.get("Indecisos") or 0)
                    + (c.get("Branco/nulo") or 0),
                    2,
                ),
            }
        )
    return saida


def converter(d: dict, origem: str) -> dict | None:
    g = d.get("governador_1t")
    chave = origem.split("_")[0]
    if not g or chave not in SLUGS:
        return None
    c = campo(d.get("campo"))
    if not c:
        return None
    b = bloco_1t(g)
    por_nome = {x["nome"]: x["partido"] for x in b["candidatos"]}
    soma = sum(x["valor"] for x in b["candidatos"]) + sum(
        b[k] or 0 for k in ("indecisos", "branco_nulo", "outros")
    )
    notas = [
        "Convertido de analysis/voto_util/outros/"
        f"{origem} por scripts/governador-2026-acervo.py; nenhum número redigitado."
    ]
    if g.get("nota"):
        notas.append(str(g["nota"]))
    if g.get("cenario"):
        notas.append(f"Cenário transcrito: {g['cenario']}.")
    alternativos = []
    for k, v in d.items():
        if (
            k.startswith("governador_1t_")
            and isinstance(v, dict)
            and v.get("candidatos")
        ):
            alt = bloco_1t(v)
            alternativos.append(
                {"cenario": v.get("cenario") or k, "pagina": v.get("pagina"), **alt}
            )
    return {
        "instituto": d["instituto"],
        "instituto_slug": SLUGS[chave],
        "uf": d["uf"],
        "cargo": "governador",
        "registro_tse": d.get("registro_tse_estadual") or d.get("registro_tse"),
        "campo": c,
        "divulgacao": d.get("divulgacao"),
        "n": d.get("n"),
        "margem_pp": _margem(d.get("margem")),
        "metodo": metodo(d.get("metodo")),
        "contratante": d.get("contratante") or "nao informado",
        "fonte": {
            "tipo": "pdf",
            "url": d.get("url_pdf"),
            "arquivo": d.get("arquivo"),
            "sha256": d.get("sha256"),
            "pagina": g.get("pagina"),
            "imagem": None,
            "capturado_em": None,
            "materia": [],
            "transcricao_origem": f"analysis/voto_util/outros/{origem}",
        },
        "pergunta": {
            "codigo": "ESTIMULADA-ACERVO",
            "tipo": "estimulada",
            "cenario": g.get("cenario"),
            "votos_por_eleitor": 1,
            "soma_total": round(soma, 2),
            "nota": None,
        },
        **b,
        "cenarios_alternativos": alternativos,
        "segundo_turno": pares_2t(d.get("governador_2t"), por_nome),
        "observacoes": notas,
    }


def _margem(texto) -> float | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*p\.?p", str(texto or ""))
    return float(m.group(1).replace(",", ".")) if m else None


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    gravados = []
    for arq in sorted(ORIGEM.glob("*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        onda = converter(d, arq.name)
        if onda is None:
            continue
        nome = f"{onda['instituto_slug']}_{onda['uf']}_{onda['campo']['fim']}.json"
        destino = DESTINO / nome
        if destino.exists():
            existente = json.loads(destino.read_text(encoding="utf-8"))
            if "transcricao_origem" not in (existente.get("fonte") or {}):
                print(f"{nome}: já transcrito direto do PDF; mantido")
                continue
        destino.write_text(
            json.dumps(onda, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        gravados.append(nome)
    print(f"{len(gravados)} ondas convertidas em {DESTINO}")
    for g in gravados:
        print(" ", g)
    return 0


if __name__ == "__main__":
    sys.exit(main())
