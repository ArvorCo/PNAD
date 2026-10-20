"""Previsão para o 2º turno (25/10/2026) por célula de 0,5°, com regra de risco.

Fonte: Open-Meteo Forecast API (modelos globais combinados pela própria API), diário,
oito dias a partir do dia da consulta, relógio de Brasília. Regra de risco declarada
(``REGRA``), aplicada ao dia alvo de cada célula; o resumo soma locais e eleitores do
cadastro do 1º turno por nível. Só biblioteca padrão: roda no workflow sem instalar nada.

O índice de locais por célula (``INDICE``) é versionado para o workflow não depender do
cadastro do TSE, que não está no git; ``reindexar`` o refaz a partir do cadastro local.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from clima_1t import coleta, grade

ROOT = Path(__file__).resolve().parents[2]
SAIDA = ROOT / "docs/assets/fiscais_mapa/clima/previsao.json"
INDICE = ROOT / "analysis/clima_1t_2026/indice_celulas_05.json"
REGISTRO = ROOT / "data/originals/clima_1t_2026/previsao_requisicoes.jsonl"
ALVO = "2026-10-25"
DIARIAS = [
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_gusts_10m_max",
    "weather_code",
]
PARAMS = {
    "daily": ",".join(DIARIAS),
    "forecast_days": 8,
    "timezone": "America/Sao_Paulo",
}
REGRA = {
    "alto": "chuva >= 30 mm ou rajada >= 70 km/h ou (probabilidade >= 80% e chuva >= 15 mm)",
    "medio": "chuva >= 10 mm ou rajada >= 50 km/h ou probabilidade >= 60%",
    "baixo": "o resto",
    "sem_dado": "a previsão ainda não alcança o dia alvo ou a célula não respondeu",
    "dia": ALVO,
    "variaveis": {
        "chuva": "precipitation_sum do dia (mm)",
        "probabilidade": "precipitation_probability_max do dia (%)",
        "rajada": "wind_gusts_10m_max do dia (km/h)",
    },
}
ROTULO = (
    "Previsão de modelo global a 0,5°, que muda todo dia. É indicativo de atenção "
    "para a logística da fiscalização, não previsão do que vai acontecer no prédio."
)
NIVEIS = ("alto", "medio", "baixo", "sem_dado")


def risco(chuva: float | None, prob: float | None, rajada: float | None) -> str:
    """Nível de risco pela regra declarada; ``sem_dado`` sem nenhum dos três."""
    if chuva is None and prob is None and rajada is None:
        return "sem_dado"
    c = chuva if chuva is not None else 0.0
    p = prob if prob is not None else 0.0
    r = rajada if rajada is not None else 0.0
    if c >= 30 or r >= 70 or (p >= 80 and c >= 15):
        return "alto"
    if c >= 10 or r >= 50 or p >= 60:
        return "medio"
    return "baixo"


def reindexar() -> dict[str, Any]:
    """Índice célula de 0,5° -> municípios com locais e eleitores, do cadastro local."""
    locais = grade.ler_locais()
    acc: dict[str, dict[tuple[str, str], list]] = defaultdict(dict)
    for lc in locais:
        if lc.lat is None or lc.lon is None:
            continue
        c = grade.chave(lc.lat, lc.lon, grade.PASSO_PREVISAO)
        item = acc[c].setdefault((lc.uf, lc.mun), [lc.uf, lc.mun, lc.municipio, 0, 0])
        item[3] += 1
        item[4] += lc.eleitores
    sem = [lc for lc in locais if lc.lat is None]
    doc = {
        "gerado_em": coleta.agora(),
        "fonte": "data/outputs/locais_votacao_2026.sqlite (cadastro do 1º turno, TSE)",
        "celula_graus": grade.PASSO_PREVISAO,
        "colunas": ["uf", "mun_tse", "municipio", "locais", "eleitores"],
        "celulas": {c: sorted(v.values()) for c, v in sorted(acc.items())},
        "sem_coordenada": {
            "locais": len(sem),
            "eleitores": sum(lc.eleitores for lc in sem),
        },
    }
    INDICE.parent.mkdir(parents=True, exist_ok=True)
    INDICE.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    return doc


def ler_indice() -> dict[str, Any]:
    if not INDICE.exists():
        return reindexar()
    return json.loads(INDICE.read_text())


def _celula(resposta: dict[str, Any]) -> dict[str, Any]:
    d = resposta.get("daily", {})
    datas = d.get("time", [])
    serie = []
    for i, dia in enumerate(datas):
        serie.append(
            {
                "data": dia,
                "chuva_mm": d.get("precipitation_sum", [None] * len(datas))[i],
                "prob_pct": d.get("precipitation_probability_max", [None] * len(datas))[
                    i
                ],
                "rajada_kmh": d.get("wind_gusts_10m_max", [None] * len(datas))[i],
                "codigo_wmo": d.get("weather_code", [None] * len(datas))[i],
            }
        )
    alvo = next((s for s in serie if s["data"] == ALVO), None)
    base = alvo or {"chuva_mm": None, "prob_pct": None, "rajada_kmh": None}
    return {
        "chuva_mm": base["chuva_mm"],
        "prob_pct": base["prob_pct"],
        "rajada_kmh": base["rajada_kmh"],
        "codigo_wmo": alvo["codigo_wmo"] if alvo else None,
        "risco": risco(base["chuva_mm"], base["prob_pct"], base["rajada_kmh"]),
        "serie": [
            {k: s[k] for k in ("data", "chuva_mm", "prob_pct", "rajada_kmh")}
            for s in serie
        ],
    }


def resumir(celulas: dict[str, Any], indice: dict[str, Any]) -> dict[str, Any]:
    """Locais e eleitores por nível de risco, por UF e por município."""
    por_uf: dict[str, dict[str, Any]] = {}
    mun: dict[tuple[str, str], dict[str, Any]] = {}
    for c, itens in indice["celulas"].items():
        cel = celulas.get(c)
        nivel = cel["risco"] if cel else "sem_dado"
        for uf, mun_tse, nome, nloc, nel in itens:
            u = por_uf.setdefault(
                uf,
                {
                    "eleitores": dict.fromkeys(NIVEIS, 0),
                    "locais": dict.fromkeys(NIVEIS, 0),
                },
            )
            u["eleitores"][nivel] += nel
            u["locais"][nivel] += nloc
            m = mun.setdefault(
                (uf, mun_tse),
                {
                    "uf": uf,
                    "mun_tse": mun_tse,
                    "municipio": nome,
                    "eleitores": 0,
                    "eleitores_risco_alto": 0,
                    "locais_risco_alto": 0,
                    "chuva_mm_max": None,
                    "rajada_kmh_max": None,
                },
            )
            m["eleitores"] += nel
            if nivel == "alto":
                m["eleitores_risco_alto"] += nel
                m["locais_risco_alto"] += nloc
            if cel:
                for chave_v, campo in (
                    ("chuva_mm", "chuva_mm_max"),
                    ("rajada_kmh", "rajada_kmh_max"),
                ):
                    v = cel[chave_v]
                    if v is not None and (m[campo] is None or v > m[campo]):
                        m[campo] = v
    for u in por_uf.values():
        u["eleitores_total"] = sum(u["eleitores"].values())
        u["locais_total"] = sum(u["locais"].values())
        tot = u["eleitores_total"] or 1
        u["eleitores_risco_alto_pct"] = round(100 * u["eleitores"]["alto"] / tot, 2)
        u["eleitores_risco_medio_ou_alto_pct"] = round(
            100 * (u["eleitores"]["alto"] + u["eleitores"]["medio"]) / tot, 2
        )
    cidades = sorted(
        (m for m in mun.values() if m["eleitores_risco_alto"] > 0),
        key=lambda m: (-m["eleitores_risco_alto"], m["uf"], m["municipio"]),
    )[:30]
    pais = {
        "eleitores": {
            n: sum(u["eleitores"][n] for u in por_uf.values()) for n in NIVEIS
        },
        "locais": {n: sum(u["locais"][n] for u in por_uf.values()) for n in NIVEIS},
        "celulas": {
            n: sum(
                1
                for c in indice["celulas"]
                if (celulas.get(c) or {}).get("risco", "sem_dado") == n
            )
            for n in NIVEIS
        },
    }
    return {
        "pais": pais,
        "por_uf": dict(sorted(por_uf.items())),
        "cidades_risco_alto": cidades,
        "nota_eleitores": "eleitores e locais do cadastro do 1º turno; as seções que mudaram "
        "de prédio para o 2º turno continuam contadas no prédio do 1º turno",
    }


def _sem_carimbo(doc: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in doc.items() if k not in ("gerado_em", "coleta")}


def gerar(
    lote: int = 100, prazo_s: float = 540, aceitar_parcial: bool = False
) -> tuple[dict[str, Any], bool]:
    """Baixa a previsão das células, aplica a regra e grava se mudou.

    Devolve o documento e se o arquivo foi (re)escrito. Previsão incompleta não
    substitui o arquivo anterior, a menos que ``aceitar_parcial``.
    """
    indice = ler_indice()
    centros = {c: grade.centro(c, grade.PASSO_PREVISAO) for c in indice["celulas"]}
    respostas: dict[str, Any] = {}

    def guardar(c: str, item: dict, _url: str, _pos: int) -> None:
        respostas[c] = item

    cliente = coleta.Cliente(registro=REGISTRO, prazo=time.monotonic() + prazo_s)
    estado = coleta.baixar_lotes(
        cliente, coleta.FORECAST, PARAMS, centros, lote, guardar
    )
    celulas = {c: _celula(respostas[c]) for c in sorted(respostas)}
    dias = sorted({s["data"] for cel in celulas.values() for s in cel["serie"]})
    completa = len(celulas) == len(centros)
    exemplo = coleta.params_lote(PARAMS, [next(iter(centros.values()))])
    doc = {
        "gerado_em": coleta.agora(),
        "alvo": ALVO,
        "fonte": "Open-Meteo Forecast API (modelos globais combinados pela API), "
        "célula de 0,5°, consulta diária",
        "rotulo": ROTULO,
        "fonte_detalhe": {
            "url": coleta.FORECAST,
            "parametros": PARAMS,
            "url_exemplo": coleta.FORECAST
            + "?"
            + "&".join(f"{k}={v}" for k, v in exemplo.items()),
            "ponto": "centro da célula de 0,5°",
        },
        "celula_graus": grade.PASSO_PREVISAO,
        "regra_risco": REGRA,
        "dias": dias,
        "coleta": {
            "celulas": len(centros),
            "respondidas": len(celulas),
            "completa": completa,
            "parada": estado["parada"],
        },
        "celulas": celulas,
        "resumo": resumir(celulas, indice),
    }
    if not completa and not aceitar_parcial and SAIDA.exists():
        anterior = json.loads(SAIDA.read_text())
        if anterior.get("coleta", {}).get("completa"):
            return doc, False
    if SAIDA.exists():
        anterior = json.loads(SAIDA.read_text())
        if _sem_carimbo(anterior) == _sem_carimbo(json.loads(json.dumps(doc))):
            return anterior, False
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    return doc, True
