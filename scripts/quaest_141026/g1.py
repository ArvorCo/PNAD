"""Extrai o painel arquivado do G1 sem inferir bases ou pesos finais."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/originals/quaest_102026_14"
PUBLIC = ROOT / "docs/assets/quaest_14102026_painel"
PAGE = "https://especiaisg1.globo/politica/eleicoes/2026/pesquisas-eleitorais/presidente/2-turno/Quaest/internal/"
API = "https://especiaisg1.globo/api/pesquisas-eleitorais/graficos/216/"
DATE = "2026-10-14"
QUESTIONS = {
    "estimulada": ("ESTIMULADA-PRE-201", "Intenção estimulada"),
    "espontanea": ("ESPONTANEA-PRE-201", "Intenção espontânea"),
    "aprovacao": ("APROVACAO-PRE-001", "Aprovação do governo"),
    "avaliacao": ("AVALIACAO-PRE-001", "Avaliação do governo"),
    "rejeicao": ("CONVOTA-PRE2", "Rejeição"),
}
VOTES = {
    "Flávio Bolsonaro": "flavio",
    "Lula": "lula",
    "Branco/Nulo/Não Vai Votar": "branco_nulo",
    "Indecisos": "indecisos",
}
# Cotas desta onda, transcritas do BR-08729/2026; não são bases observadas.
QUOTAS = {
    "Renda": {"Até 2 sm": 31, "Mais de 2 a 5 sm": 42, "Mais de 5 sm": 27},
    "Sexo": {"Masculino": 47, "Feminino": 53},
    "Idade": {"16 a 34 anos": 31, "35 a 59 anos": 45, "60 anos ou mais": 24},
    "Escolaridade": {"Fundamental": 42, "Médio": 39, "Superior": 19},
}


def source_record(path, url):
    raw = path.read_bytes()
    return {
        "url": url,
        "arquivo": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def parse_chart(chart, code, *, exhaustive=True):
    if chart["pergunta"]["codigo"] != code:
        raise ValueError("Pergunta inesperada no painel")
    values = {}
    for point in chart["data"]:
        if point["date"] != DATE + "T00:00:00Z":
            raise ValueError("Onda inesperada no painel; não misturar datas")
        option, value = point["option"], point["value"]
        if option in values:
            raise ValueError("Resposta duplicada no painel")
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Resposta ausente ou inválida; não substituir por zero")
        if not 0 <= value <= 1:
            raise ValueError("Percentual fora do intervalo")
        values[option] = round(100 * value, 6)
    if exhaustive and abs(sum(values.values()) - 100) > 0.5 * len(values):
        raise ValueError("Soma incompatível com arredondamento das respostas")
    return {
        "id": chart["identificador"],
        "dimensao": chart["bandeira"],
        "recorte": chart["variavel_cruzamento"],
        "valores_pct": values,
        "margem_publicada_pp": chart["margem"],
        "base": None,
    }


def panel():
    result = {}
    for key, (code, label) in QUESTIONS.items():
        path = SOURCE / f"g1_{key}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))["resultado"]
        if len(raw["cenarios"]) != 1:
            raise ValueError("Esperado um cenário por pergunta")
        total = parse_chart(raw["cenarios"][0], code, exhaustive=key != "rejeicao")
        rows = [
            parse_chart(c, code, exhaustive=key != "rejeicao") for c in raw["estratos"]
        ]
        if len(rows) != 26 or len({r["id"] for r in rows}) != len(rows):
            raise ValueError("Recortes incompletos ou duplicados")
        if any(set(r["valores_pct"]) != set(total["valores_pct"]) for r in rows):
            raise ValueError("Opções incompletas em um recorte")
        result[key] = {
            "codigo": code,
            "rotulo": label,
            "fonte": source_record(
                path, f"{API}?tipo_pergunta={code}&instituto=Quaest"
            ),
            "total": total,
            "estratos": rows,
            "dimensoes": dict(Counter(r["dimensao"] for r in rows)),
        }
    return result


def controls(question):
    """Prova de leitura condicional às cotas; não estima erro amostral."""
    total = question["total"]["valores_pct"]
    result = {}
    for dimension, quotas in QUOTAS.items():
        rows = {
            r["recorte"]: r for r in question["estratos"] if r["dimensao"] == dimension
        }
        if set(rows) != set(quotas):
            raise ValueError(f"Recortes inesperados: {dimension}")
        composed = {
            VOTES[option]: round(
                sum(
                    weight * rows[name]["valores_pct"][option]
                    for name, weight in quotas.items()
                )
                / 100,
                6,
            )
            for option in VOTES
        }
        residual = {VOTES[o]: round(composed[VOTES[o]] - total[o], 6) for o in VOTES}
        result[dimension] = {
            "cotas_previstas_pct": quotas,
            "recomposto": composed,
            "residuo": residual,
            "residuo_max_abs": max(abs(v) for v in residual.values()),
        }
    return result


def summary(data=None):
    data = panel() if data is None else data
    return {
        "pagina": source_record(SOURCE / "g1_painel.html", PAGE),
        "conferido_em": "2026-10-15",
        "origem": "API pública consumida pelo painel do G1; extração arquivada em 15/10/2026.",
        "csv": "assets/quaest_14102026_painel/recortes.csv",
        "perguntas": {
            key: {
                "codigo": value["codigo"],
                "rotulo": value["rotulo"],
                "fonte": value["fonte"],
                "total": value["total"],
                "recortes": len(value["estratos"]),
                "dimensoes": value["dimensoes"],
                "dados": f"assets/quaest_14102026_painel/{key}.json",
            }
            for key, value in data.items()
        },
        "controles_estimulada": controls(data["estimulada"]),
        "limites": "Bases e perfil final não publicados; margens dos recortes são as informadas pelo painel, não margens da diferença. Rejeição não é distribuição exaustiva de votos.",
    }


def reference():
    data = panel()
    return {
        "resumo": "assets/quaest_14102026_painel/index.json",
        "csv": "assets/quaest_14102026_painel/recortes.csv",
        "perguntas": len(data),
        "recortes_por_pergunta": 26,
        "fontes_sha256": {key: value["fonte"]["sha256"] for key, value in data.items()},
    }


def write():
    data = panel()
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for key, value in data.items():
        (PUBLIC / f"{key}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
    result = summary(data)
    (PUBLIC / "index.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    with (PUBLIC / "recortes.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "pergunta",
                "data",
                "dimensao",
                "recorte",
                "resposta",
                "pct",
                "margem_publicada_pp",
                "base",
            ]
        )
        for question in data.values():
            for row in [question["total"], *question["estratos"]]:
                for option, value in row["valores_pct"].items():
                    writer.writerow(
                        [
                            question["rotulo"],
                            DATE,
                            row["dimensao"],
                            row["recorte"],
                            option,
                            value,
                            row["margem_publicada_pp"],
                            row["base"],
                        ]
                    )
    return result
