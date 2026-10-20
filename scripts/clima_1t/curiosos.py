"""Listas de locais curiosos (análise 5 do contrato) e cruzamento com as mudanças do 2º turno.

Cada lista tem regra declarada e no máximo 30 itens; cada item traz o link do local no
mapa de fiscais. Lista é pista para conferir, não conclusão: chuva de reanálise a 0,25°
não é a chuva no telhado do prédio.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from clima_1t.variaveis import faixa_chuva

ROOT = Path(__file__).resolve().parents[2]
MUDANCAS = ROOT / "analysis/mudancas_secoes_2t/mudancas.json"
PONTOS_MUDANCAS = ROOT / "analysis/mudancas_secoes_2t/clima/open_meteo.json"
LIMITE = 30
APTOS_MIN = 200

CAMPOS = [
    "chuva_04_10_mm",
    "chuva_votacao_mm",
    "hora_pico_chuva",
    "rajada_04_10_kmh",
    "rajada_votacao_kmh",
    "faixa_chuva",
    "urnas",
    "urnas_bateria",
    "urnas_bateria_votacao",
    "urnas_bateria_simultanea",
    "urnas_bateria_isolada",
    "urnas_reinicio",
    "aptos",
    "abst_pct",
    "abst22_pct",
    "dif_abst_pp",
]


def _valor(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return None if not np.isfinite(v) else round(float(v), 2)
    return v


def item(linha: pd.Series, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    d = {
        "local_id": linha["local_id"],
        "nome": linha["nome"],
        "municipio": linha["municipio"],
        "uf": linha["uf"],
        "zona": int(linha["zona"]),
    }
    d.update({c: _valor(linha[c]) for c in CAMPOS})
    if extra:
        d.update({k: _valor(v) for k, v in extra.items()})
    d["mapa"] = f"fiscais_mapa.html#uf={linha['uf']}&l={linha['local_id']}"
    return d


def _por_municipio(df: pd.DataFrame, maximo: int) -> pd.DataFrame:
    return df.groupby(["uf", "mun"], sort=False).head(maximo)


def listas(locais: pd.DataFrame) -> dict[str, Any]:
    todos = locais.loc[locais["urnas"] > 0].copy()
    # referências do município com todos os locais com boletim, com ou sem clima
    med = todos.groupby(["uf", "mun"])["dif_abst_pp"].transform("median")
    todos["dif_excesso_mun_pp"] = todos["dif_abst_pp"] - med
    bat_mun = todos.groupby(["uf", "mun"])["urnas_bateria_votacao"].transform("sum")
    todos["bat_vot_outros_locais_mun"] = bat_mun - todos["urnas_bateria_votacao"]
    df = todos.loc[todos["chuva_04_10_mm"].notna()].copy()
    df["forte"] = df["faixa_chuva"].isin(["forte", "muito_forte"])
    est = df["aptos_c"] >= APTOS_MIN
    saida: dict[str, Any] = {}

    a = df.loc[
        df["forte"]
        & (df["urnas_bateria_votacao"] >= 1)
        & est
        & (df["dif_excesso_mun_pp"] > 0)
    ]
    a = a.sort_values("dif_excesso_mun_pp", ascending=False).head(LIMITE)
    saida["a_chuva_forte_bateria_abstencao_alta"] = {
        "regra": "mais de 20 mm no dia 04/10, ao menos uma urna com bateria durante a votação "
        f"e salto de abstenção contra 2022 acima da mediana dos locais do município; ao menos "
        f"{APTOS_MIN} aptos nas seções casadas com 2022; ordem: excesso sobre a mediana",
        "total_que_atende": int(
            (
                df["forte"]
                & (df["urnas_bateria_votacao"] >= 1)
                & est
                & (df["dif_excesso_mun_pp"] > 0)
            ).sum()
        ),
        "itens": [
            item(r, {"dif_excesso_mun_pp": r["dif_excesso_mun_pp"]})
            for _, r in a.iterrows()
        ],
    }

    mb = (
        (df["urnas_bateria_votacao"] >= 5)
        & (df["chuva_04_10_mm"] < 0.05)
        & (df["bat_vot_outros_locais_mun"] == 0)
    )
    b = df.loc[mb].sort_values(
        ["urnas_bateria_votacao", "urnas"], ascending=[False, True]
    )
    saida["b_bateria_em_predio_seco_e_sozinho"] = {
        "regra": "5 ou mais urnas com bateria durante a votação no mesmo prédio, chuva zero no "
        "dia 04/10 e nenhuma outra urna do município com bateria durante a votação "
        "(pista de rede elétrica do prédio ou do entorno, não de tempo)",
        "total_que_atende": int(mb.sum()),
        "itens": [item(r) for _, r in b.head(LIMITE).iterrows()],
    }

    mc = (
        (df["faixa_chuva"] == "muito_forte")
        & (df["urnas_bateria"] == 0)
        & (df["urnas_log"] > 0)
    )
    c = df.loc[mc].sort_values(["chuva_04_10_mm", "urnas"], ascending=[False, False])
    c = _por_municipio(c, 2)
    saida["c_chuva_muito_forte_sem_bateria"] = {
        "regra": "mais de 50 mm no dia 04/10 e nenhuma urna do prédio com registro de bateria "
        "em qualquer momento; ordem: chuva, depois número de urnas; no máximo 2 por município",
        "total_que_atende": int(mc.sum()),
        "itens": [item(r) for _, r in c.head(LIMITE).iterrows()],
    }

    md = df["forte"] & est & df["dif_abst_pp"].notna()
    d = df.loc[md].sort_values("dif_abst_pp", ascending=False)
    saida["d_maior_salto_de_abstencao_com_chuva_forte"] = {
        "regra": "mais de 20 mm no dia 04/10, ao menos "
        f"{APTOS_MIN} aptos nas seções casadas com 2022; ordem: diferença contra o 2º turno "
        "de 2022, maior primeiro",
        "total_que_atende": int(md.sum()),
        "itens": [item(r) for _, r in d.head(LIMITE).iterrows()],
    }

    me = md & (df["dif_abst_pp"] < 0)
    e = df.loc[me].sort_values("dif_abst_pp", ascending=True)
    saida["e_chuva_forte_e_abstencao_caiu"] = {
        "regra": "mais de 20 mm no dia 04/10, ao menos "
        f"{APTOS_MIN} aptos casados, abstenção de 2026 menor que a do 2º turno de 2022; "
        "ordem: maior queda primeiro",
        "total_que_atende": int(me.sum()),
        "total_com_chuva_forte": int(md.sum()),
        "itens": [item(r) for _, r in e.head(LIMITE).iterrows()],
    }
    return saida


def _resumo_grupo(d: pd.DataFrame) -> dict[str, Any]:
    w = d["aptos"]
    casada = d["aptos_c"] > 0
    return {
        "locais": len(d),
        "urnas": int(d["urnas"].sum()),
        "aptos": int(w.sum()),
        "chuva_04_10_media_mm": (
            round(float((d["chuva_04_10_mm"] * w).sum() / w.sum()), 2)
            if w.sum()
            else None
        ),
        "locais_chuva_forte_pct": (
            round(
                100 * float(d["faixa_chuva"].isin(["forte", "muito_forte"]).mean()), 2
            )
            if len(d)
            else None
        ),
        "urnas_bateria_votacao_pct": round(
            100
            * float(
                d["urnas_bateria_votacao"].sum() / max(d["urnas_relogio"].sum(), 1)
            ),
            2,
        ),
        "abst_pct": (
            round(100 * float((d["aptos"] - d["comparecimento"]).sum() / w.sum()), 2)
            if w.sum()
            else None
        ),
        "dif_abst_pp": (
            round(
                100
                * float(
                    (d.loc[casada, "aptos_c"] - d.loc[casada, "comp_c"]).sum()
                    / d.loc[casada, "aptos_c"].sum()
                    - (d.loc[casada, "aptos22"] - d.loc[casada, "comp22"]).sum()
                    / d.loc[casada, "aptos22"].sum()
                ),
                2,
            )
            if casada.any()
            else None
        ),
    }


def mudancas(locais: pd.DataFrame) -> dict[str, Any]:
    """Confresa (MT) e as origens dos 334 pares com mudança real para o 2º turno."""
    doc = json.loads(MUDANCAS.read_text())
    pares = [x for x in doc["locais"] if x["mudanca_real"]]
    origens = {
        f"{x['uf']}-{x['mun_tse']}-{int(x['zona'])}-{int(x['local_1t'])}" for x in pares
    }
    df = locais.loc[locais["urnas"] > 0].copy()
    com = df.loc[df["chuva_04_10_mm"].notna()]
    eh = com["local_id"].isin(origens)
    conf = df.loc[(df["uf"] == "MT") & (df["municipio"].str.upper() == "CONFRESA")]
    conf = conf.sort_values("aptos", ascending=False)
    lista = com.loc[eh].sort_values("chuva_04_10_mm", ascending=False)
    return {
        "fonte": str(MUDANCAS.relative_to(ROOT)),
        "pares_mudanca_real": len(pares),
        "origens_distintas": len(origens),
        "origens_com_clima": int(eh.sum()),
        "origens": _resumo_grupo(com.loc[eh]),
        "demais_locais": _resumo_grupo(com.loc[~eh]),
        "origens_por_chuva": [item(r) for _, r in lista.head(LIMITE).iterrows()],
        "confresa_mt": {
            "municipio": _resumo_grupo(conf) if len(conf) else None,
            "locais": [item(r) for _, r in conf.head(LIMITE).iterrows()],
            "origem_de_mudanca": sorted(set(conf["local_id"]) & origens),
        },
    }


def conferencia_pontos(locais: pd.DataFrame) -> dict[str, Any]:
    """Compara a chuva da célula com a do ponto exato baixado pelo motor das mudanças."""
    if not PONTOS_MUDANCAS.exists():
        return {"situacao": "arquivo ausente"}
    doc = json.loads(PONTOS_MUDANCAS.read_text())
    chuva_cel: dict[str, float] = {
        str(k): float(v)
        for k, v in zip(locais["local_id"], locais["chuva_04_10_mm"], strict=True)
        if pd.notna(v)
    }
    pares = []
    for pid, p in doc["pontos"].items():
        dia = next((d for d in p["dias"] if d["data"] == "2026-10-04"), None)
        if pid not in chuva_cel or dia is None or dia.get("precipitation_sum") is None:
            continue
        pares.append((float(dia["precipitation_sum"]), chuva_cel[pid]))
    if not pares:
        return {"situacao": "sem pares"}
    a = np.array(pares)
    mesma = np.mean([faixa_chuva(x) == faixa_chuva(y) for x, y in a])
    return {
        "fonte": str(PONTOS_MUDANCAS.relative_to(ROOT)),
        "regra": "chuva diária de 04/10 no ponto exato do local (motor das mudanças, ERA5 "
        "pela Open-Meteo) contra a do centro da célula de 0,25° deste motor",
        "pares": len(a),
        "correlacao": round(float(np.corrcoef(a[:, 0], a[:, 1])[0, 1]), 4),
        "diferenca_media_absoluta_mm": round(
            float(np.mean(np.abs(a[:, 0] - a[:, 1]))), 3
        ),
        "diferenca_mediana_absoluta_mm": round(
            float(np.median(np.abs(a[:, 0] - a[:, 1]))), 3
        ),
        "mesma_faixa_pct": round(100 * float(mesma), 2),
        "media_ponto_mm": round(float(a[:, 0].mean()), 3),
        "media_celula_mm": round(float(a[:, 1].mean()), 3),
    }
