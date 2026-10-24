"""Referência de abstenção municipal e exposição meteorológica, sem efeito causal.

O cenário de persistência repete a taxa do 1º turno. A chuva só define exposição
logística; não altera a taxa nem identifica voto de quem pode faltar.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRESIDENTE = ROOT / "analysis/apuracao_2026/dados/presidente.json"
INDICE = ROOT / "analysis/clima_1t_2026/indice_celulas_05.json"


def fonte(path: Path) -> dict:
    raw = path.read_bytes()
    return {
        "caminho": str(path.relative_to(ROOT)),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def calcular(presidente: dict, indice: dict, previsao: dict) -> dict:
    """Cruza códigos TSE com UF; não usa nomes nem imputa clima ausente."""
    exposicao = defaultdict(
        lambda: {
            "alto": 0,
            "medio": 0,
            "baixo": 0,
            "sem_dado": 0,
            "chuva_soma": 0.0,
            "chuva_peso": 0,
        }
    )
    for chave, itens in indice["celulas"].items():
        cel = previsao["celulas"].get(chave, {})
        nivel = cel.get("risco", "sem_dado")
        for uf, codigo, _nome, _locais, eleitores in itens:
            if uf == "ZZ":
                continue
            item = exposicao[(uf, str(codigo).zfill(5))]
            item[nivel] += eleitores
            chuva = cel.get("chuva_mm")
            if chuva is not None:
                item["chuva_soma"] += chuva * eleitores
                item["chuva_peso"] += eleitores

    ufs = []
    for u in presidente["ufs"]:
        if u["uf"] == "ZZ":
            continue
        ufs.append(
            {
                "uf": u["uf"],
                "aptos": u["eleitores"],
                "comparecimento": u["comparecimento"],
                "abstencao_pct": 100 * (1 - u["comparecimento"] / u["eleitores"]),
            }
        )
    aptos = sum(u["aptos"] for u in ufs)
    presentes = sum(u["comparecimento"] for u in ufs)
    nacional = 100 * (1 - presentes / aptos)
    municipios = []
    for linha in presidente["municipios"]["linhas"]:
        m = dict(zip(presidente["municipios"]["colunas"], linha, strict=True))
        if m["uf"] == "ZZ" or not m["eleitores"] or not m["completo"]:
            continue
        if m["comparecimento"] is None:
            continue
        e = exposicao.get((m["uf"], str(m["cd_tse"]).zfill(5)), {})
        total = sum(e.get(k, 0) for k in ("alto", "medio", "baixo", "sem_dado"))
        cobertos = total - e.get("sem_dado", 0)
        abst = 100 * (1 - m["comparecimento"] / m["eleitores"])
        alto_pct = 100 * e.get("alto", 0) / total if total else None
        municipios.append(
            {
                "uf": m["uf"],
                "codigo_tse": str(m["cd_tse"]).zfill(5),
                "ibge": m["ibge"],
                "municipio": m["nome"],
                "aptos_1t": m["eleitores"],
                "comparecimento_1t": m["comparecimento"],
                "abstencao_1t_pct": abst,
                "cenario_persistencia_2t_pct": abst,
                "eleitores_cadastro_mapeados": total,
                "cobertura_previsao_pct": 100 * cobertos / total if total else None,
                "eleitores_risco_alto": e.get("alto", 0),
                "risco_alto_pct": alto_pct,
                "chuva_media_mm": (
                    e["chuva_soma"] / e["chuva_peso"] if e.get("chuva_peso") else None
                ),
                "atencao_conjunta": bool(
                    m["eleitores"] >= 10000
                    and abst > nacional
                    and alto_pct is not None
                    and alto_pct >= 50
                    and cobertos == total
                ),
            }
        )
    return {
        "previsao_gerada_em": previsao["gerado_em"],
        "alvo": previsao["alvo"],
        "metodo": "Cenário de persistência: taxa municipal do 2º turno igual à do 1º. "
        "Sem incremento por chuva, sem validação preditiva municipal e sem IC de previsão.",
        "regra_atencao": "Municípios com pelo menos 10 mil aptos, abstenção do 1º turno "
        "acima da taxa nacional sem exterior e ao menos 50% do cadastro mapeado em risco "
        "climático alto; exige previsão em todas as células mapeadas. Ordem por eleitores expostos.",
        "universos": "Abstenção: aptos e presentes da totalização municipal do TSE. "
        "Exposição: cadastro georreferenciado do 1º turno; não desloca locais realocados. "
        "Cadastros e totalização têm denominadores distintos; faltantes não viram risco baixo.",
        "brasil": {
            "aptos": aptos,
            "comparecimento": presentes,
            "abstencao_pct": nacional,
        },
        "ufs": sorted(ufs, key=lambda u: -u["abstencao_pct"]),
        "municipios": sorted(
            municipios,
            key=lambda m: (-m["eleitores_risco_alto"], m["uf"], m["codigo_tse"]),
        ),
    }


def carregar(previsao: dict) -> dict:
    doc = calcular(
        json.loads(PRESIDENTE.read_text()), json.loads(INDICE.read_text()), previsao
    )
    doc["fontes"] = [fonte(PRESIDENTE), fonte(INDICE)]
    return doc
