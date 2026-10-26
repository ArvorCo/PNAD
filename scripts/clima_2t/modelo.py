"""Clima de 25/10/2026 por célula de 0,25° na Open-Meteo (modelo ou reanálise).

``ifs``: arquivo da Open-Meteo com ``models=ecmwf_ifs`` (modelo operacional do ECMWF a
9 km, montado com as primeiras horas de cada rodada). É análise operacional, provisória,
não medição nem reanálise. ``era5``: ``models=era5`` (ERA5/ERA5T), que em 26/10 só ia até
20/10 23h UTC; a troca é ``--fonte era5`` quando a série alcançar 25/10 21h UTC.

Reaproveita o cliente com cota, espera em 429 e retomada de ``clima_1t.coleta``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clima_1t import grade
from clima_1t.coleta import ARCHIVE, Cliente, agora, baixar_lotes
from clima_1t.grade import arquivo_da_chave

ROOT = Path(__file__).resolve().parents[2]
DIA = "2026-10-25"
MODELOS = {
    "ifs": {
        "models": "ecmwf_ifs",
        "nome": "ECMWF IFS (análise operacional, provisória) via Open-Meteo",
        "rotulo": "modelo, provisório",
    },
    "era5": {
        "models": "era5",
        "nome": "ERA5/ERA5T (reanálise) via Open-Meteo",
        "rotulo": "reanálise ERA5",
    },
}
DIARIAS = [
    "precipitation_sum",
    "precipitation_hours",
    "wind_gusts_10m_max",
    "temperature_2m_max",
]
HORARIAS = ["precipitation", "wind_gusts_10m", "temperature_2m"]


def raw(fonte: str) -> Path:
    return ROOT / f"data/originals/clima_2t_2026/{fonte}"


def params(fonte: str) -> dict[str, Any]:
    return {
        "start_date": DIA,
        "end_date": DIA,
        "daily": ",".join(DIARIAS),
        "hourly": ",".join(HORARIAS),
        "timezone": "America/Sao_Paulo",
        "models": MODELOS[fonte]["models"],
    }


def celulas_1t() -> dict[str, tuple[float, float]]:
    """As mesmas 6.539 células de 0,25° do 1º turno."""
    return grade.celulas(grade.ler_locais(), grade.PASSO_ARCHIVE)


def cobre_25_10(fonte: str) -> bool:
    """Confere num ponto (São Paulo) se a série tem 25/10 até 18h de Brasília."""
    cli = Cliente()
    r = cli.get(
        ARCHIVE, {**params(fonte), "latitude": "-23.625", "longitude": "-46.625"}
    )
    h = r.get("hourly", {})
    horas = [
        v
        for t, v in zip(h.get("time", []), h.get("precipitation", []), strict=False)
        if t.startswith(DIA) and "07" <= t[11:13] <= "18"
    ]
    return len(horas) == 12 and all(v is not None for v in horas)


def coletar(fonte: str, lote: int = 100) -> dict[str, Any]:
    if fonte == "era5" and not cobre_25_10("era5"):
        raise SystemExit(
            "ERA5 ainda não cobre 25/10 07h a 18h de Brasília; tente depois"
        )
    pasta = raw(fonte)
    pasta.mkdir(parents=True, exist_ok=True)
    cel = celulas_1t()
    cliente = Cliente(registro=pasta.parent / f"{fonte}_requisicoes.jsonl")

    def gravar(c: str, item: dict, url: str, pos: int) -> None:
        doc = {
            "coletado_em": agora(),
            "celula": c,
            "url": url,
            "posicao_no_lote": pos,
            "resposta": item,
        }
        (pasta / arquivo_da_chave(c)).write_text(json.dumps(doc, ensure_ascii=False))

    feitas = [c for c in cel if (pasta / arquivo_da_chave(c)).exists()]
    cliente.avisar(f"{len(cel) - len(feitas)} de {len(cel)} células a baixar ({fonte})")
    estado = baixar_lotes(
        cliente, ARCHIVE, params(fonte), cel, lote, gravar, pular=feitas
    )
    estado["chamadas_nesta_execucao"] = cliente.chamadas
    return estado


def ler(fonte: str) -> dict[str, dict[str, Any]]:
    """Por célula: chuva por hora de Brasília (00 a 23), rajada, temperatura e diárias."""
    saida: dict[str, dict[str, Any]] = {}
    for arq in sorted(raw(fonte).glob("*.json")):
        doc = json.loads(arq.read_text())
        r = doc["resposta"]
        h, d = r.get("hourly", {}), r.get("daily", {})
        idx = [i for i, t in enumerate(h.get("time", [])) if t.startswith(DIA)]
        saida[doc["celula"]] = {
            "ponto": [r.get("latitude"), r.get("longitude"), r.get("elevation")],
            "horas": [h["time"][i][11:13] for i in idx],
            "chuva": [h["precipitation"][i] for i in idx],
            "rajada": [h["wind_gusts_10m"][i] for i in idx],
            "temp": [h["temperature_2m"][i] for i in idx],
            "diario": {v: (d.get(v) or [None])[0] for v in DIARIAS},
        }
    return saida
