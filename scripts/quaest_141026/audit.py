"""Série comparável, incerteza e sensibilidade ao perfil publicado."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path

from .g1 import PUBLIC as G1_PUBLIC
from .g1 import reference as g1_reference
from .history import MANIFEST as HISTORY_MANIFEST
from .history import build as history_build
from .income import build as income_build

ROOT = Path(__file__).resolve().parents[2]
SLUG = "quaest_14102026"
SOURCE = ROOT / "data/originals/quaest_102026_14"
POLL = ROOT / "analysis/reponderacao/pesquisas/quaest_2026-10-13.json"
KEYS = ("flavio", "lula", "branco_nulo", "indecisos")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def wave(poll):
    v = poll["publicado"]["2t"]
    chosen = v["flavio"] + v["lula"]
    return {
        "id": poll["id"],
        "campo": poll["campo"],
        "divulgacao": poll["divulgacao"],
        "n": poll["n"],
        "publicado": v,
        "gap_total_pp": v["flavio"] - v["lula"],
        "gap_binario_pp": 100 * (v["flavio"] - v["lula"]) / chosen,
        "flavio_binario_pct": 100 * v["flavio"] / chosen,
        "arquivo": (
            str(POLL.relative_to(ROOT))
            if poll["id"] == POLL.stem
            else f"analysis/reponderacao/pesquisas/{poll['id']}.json"
        ),
        "fonte": {
            k: poll["fonte"][k]
            for k in ("rotulo", "url", "arquivo")
            if k in poll["fonte"]
        },
    }


def aas(poll):
    """Apenas referência multinomial AAS; não estima o desenho real da Quaest."""
    v = poll["publicado"]["2t"]
    flavio, lula = v["flavio"] / 100, v["lula"] / 100
    gap = 100 * (flavio - lula)
    variance = 10000 * (flavio + lula - (flavio - lula) ** 2) / poll["n"]
    margin = 1.959963984540054 * math.sqrt(variance)
    return {
        "variancia_pp2": variance,
        "margem_gap_95_pp": margin,
        "intervalo_gap_95_pp": [gap - margin, gap + margin],
    }


def build():
    poll = read(POLL)
    # O dossiê é da onda de 14/10. Novas divulgações não reescrevem sua série.
    archived = [
        row
        for p in sorted(POLL.parent.glob("quaest_*.json"))
        if (row := read(p))["divulgacao"] <= poll["divulgacao"]
    ]
    series = sorted(
        [wave(p) for p in archived if "2t" in p["publicado"]],
        key=lambda p: p["divulgacao"],
    )
    old = next(p for p in archived if p["id"] == "quaest_2026-10-03")
    a, b = old["publicado"]["2t"], poll["publicado"]["2t"]
    mass = b["flavio"] + b["lula"]
    projection = {
        k: mass * a[k] / (a["flavio"] + a["lula"]) for k in ("flavio", "lula")
    }
    uncertainty = aas(poll)
    uncertainty["mudanca_gap_total_pp"] = (b["flavio"] - b["lula"]) - (
        a["flavio"] - a["lula"]
    )
    uncertainty["margem_mudanca_independente_aas_95_pp"] = (
        1.959963984540054
        * math.sqrt(uncertainty["variancia_pp2"] + aas(old)["variancia_pp2"])
    )
    urna = read(ROOT / "docs/assets/reponderacao_urna_1t.json")["urna"]
    # Pesquisa domiciliar no Brasil: recorte oficial sem exterior.
    result = urna["validos_sem_exterior"]
    pair_f = 100 * result["flavio"] / (result["flavio"] + result["lula"])
    return {
        "slug": SLUG,
        "status": "integra_conferida",
        "conferido_em": "2026-10-15",
        "pesquisa": poll,
        "serie": series,
        "evolucao_renda_historica": history_build(archived),
        "aas": uncertainty,
        "decomposicao": {
            "variacoes_total_pp": {k: b[k] - a[k] for k in KEYS},
            "proporcao_anterior_aplicada_a_massa_atual": projection,
            "residuo_proporcional_pp": {k: b[k] - projection[k] for k in projection},
            "mudanca_gap_binario_pp": series[-1]["gap_binario_pp"]
            - series[-2]["gap_binario_pp"],
        },
        "urna_1t": {
            "universo": "Brasil sem exterior; válidos oficiais do 1º turno",
            "validos": {k: result[k] for k in ("flavio", "lula")},
            "flavio_entre_finalistas_pct": pair_f,
            "nota": "Renormalização entre finalistas, não resultado observado de 2º turno nem destino da terceira via.",
        },
        "campo": [
            {
                "data": f"2026-10-{day}",
                "weekday": date(2026, 10, day).weekday(),
                "tipo": {
                    10: "sábado",
                    11: "domingo",
                    12: "feriado nacional, segunda",
                    13: "terça-feira",
                }[day],
                "entrevistas": None,
            }
            for day in range(10, 14)
        ],
        "identificacao_renda": income_build(poll, old),
        "painel_g1": g1_reference(),
        "pendencias": [
            "Bases brutas e ponderadas de cada pergunta e cruzamento; votos e perfil de renda agora conferidos na íntegra.",
            "Etapa antes/depois da ponderação do perfil publicado, pesos individuais, tamanho efetivo e não resposta à renda.",
            "Salvar o PDF do questionário; anexo territorial não disponível na reconsulta de 15/10 às 01h12 BRT, ainda dentro do prazo mostrado.",
            "Entrevistas, contatos, ausências, recusas e revisitas por dia/horário e estrato.",
            "Implementação do MrP ou rake, eventual calibração pelo voto lembrado e regra de eleitor provável, se houver.",
        ],
    }


def write():
    data = build()
    folder = ROOT / "analysis/quaest_141026"
    folder.mkdir(exist_ok=True)
    sources = [p for p in SOURCE.iterdir() if p.is_file() and p.name != "fonte.json"]
    sources += sorted((SOURCE / "referencias").glob("*.pdf"))
    sources += [ROOT / "docs/fontes/quaest_14102026_registro.txt", POLL]
    sources += sorted((ROOT / "analysis/quaest_141026/integra").rglob("*.json"))
    sources += sorted(p for p in G1_PUBLIC.iterdir() if p.is_file())
    sources += [
        HISTORY_MANIFEST,
        *sorted(
            p for p in (ROOT / "docs/fontes/quaest_14102026").iterdir() if p.is_file()
        ),
    ]
    manifest = {
        "consulta": "2026-10-15",
        "arquivos": [
            {
                "arquivo": str(p.relative_to(ROOT)),
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in sorted(sources)
        ],
    }
    for path, value in [
        (folder / "auditoria.json", data),
        (ROOT / f"docs/assets/{SLUG}_data.json", data),
        (ROOT / f"docs/assets/{SLUG}_sources.json", manifest),
        (SOURCE / "fonte.json", manifest),
    ]:
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return data
