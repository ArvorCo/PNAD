"""Bateria e abstenção do 2º turno contra a chuva de 25/10 por célula de 0,25°.

A chuva vem de ``analysis/clima_2t_2026/clima.json`` (``clima_2t.observado``): estações do
CEMADEN a até 50 km quando há, modelo ECMWF IFS provisório onde não há. Cada seção herda a
célula do seu local de votação no cadastro do 1º turno (seção que mudou de prédio fica com
a célula do prédio antigo; as 1.362 seções realocadas são 0,3% do total).

Duas exposições, sempre com a fonte separada:
- ``chuva_dia_medida``: dia 25/10 inteiro, só células com estação (o par do 1º turno é a
  faixa da chuva diária ERA5);
- ``chuva_votacao``: 07h às 18h de Brasília, por fonte (estação ou modelo); o par do 1º
  turno é a razão 2,29 da faixa forte contra a seca nas horas de votação.

IC95 por bootstrap de células (as seções de uma célula compartilham a chuva). Descreve
associação; não identifica causa.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from clima_1t import grade
from clima_1t.variaveis import FAIXAS_CHUVA, ROTULO_CHUVA, faixa_chuva, ler_secao_local

from .logs_base import CHAVE, ROOT

CLIMA_2T = ROOT / "analysis/clima_2t_2026/clima.json"
CLIMA_1T = ROOT / "analysis/clima_1t_2026/clima.json"
ESTACAO = ("cemaden", "inmet", "ambos")
REPS = 1000
MIN_CELULAS_IC = 20


def _celulas() -> pd.DataFrame:
    d = json.loads(CLIMA_2T.read_text(encoding="utf-8"))
    df = pd.DataFrame.from_dict(d["celulas"], orient="index")
    df.index.name = "cel"
    return df.reset_index()


def secao_celula() -> pd.DataFrame:
    sl = ler_secao_local()
    cel = {
        (lc.uf, lc.mun, lc.zona, lc.local_nr): grade.chave(
            lc.lat, lc.lon, grade.PASSO_ARCHIVE
        )
        for lc in grade.ler_locais()
        if lc.lat is not None and lc.lon is not None
    }
    sl["cel"] = [
        cel.get((u, m, int(z), int(n)))
        for u, m, z, n in zip(
            sl["uf"], sl["mun"], sl["zona"], sl["local_nr"], strict=True
        )
    ]
    return sl[[*CHAVE, "cel"]]


def _boot(por_cel: pd.DataFrame, num: str, den: str, rng: np.random.Generator):
    """Razão num/den somada nas células, com IC95 por reamostragem de células."""
    n = len(por_cel)
    val = 100 * por_cel[num].sum() / por_cel[den].sum() if por_cel[den].sum() else None
    if n < MIN_CELULAS_IC or val is None:
        return {
            "valor": None if val is None else round(float(val), 2),
            "ic95": None,
        }, None
    a, b = por_cel[num].to_numpy(float), por_cel[den].to_numpy(float)
    idx = rng.integers(0, n, size=(REPS, n))
    reps = 100 * a[idx].sum(1) / b[idx].sum(1)
    lo, hi = np.percentile(reps, [2.5, 97.5])
    return {
        "valor": round(float(val), 2),
        "ic95": [round(float(lo), 2), round(float(hi), 2)],
    }, reps


def _faixas_bateria(x: pd.DataFrame, col: str, rng) -> list[dict]:
    x = x.assign(faixa=x[col].map(faixa_chuva))
    out, ref = [], None
    grupos = [(f, x[x["faixa"] == f]) for f in FAIXAS_CHUVA]
    grupos.append(("20_ou_mais", x[x[col] >= 20]))
    for nome, g in grupos:
        pc = g.groupby("cel")[["bat", "n", "local", "isolada"]].sum()
        parc, reps = _boot(pc, "bat", "n", rng)
        item = {
            "faixa": nome,
            "rotulo": ROTULO_CHUVA.get(nome, "20 mm ou mais"),
            "celulas": len(pc),
            "secoes": int(pc["n"].sum()),
            "com_bateria": int(pc["bat"].sum()),
            "parcela_pct": parc,
            "pct_local": (
                round(100 * pc["local"].sum() / pc["n"].sum(), 2) if len(pc) else None
            ),
            "pct_isolada": (
                round(100 * pc["isolada"].sum() / pc["n"].sum(), 2) if len(pc) else None
            ),
        }
        if nome == "seca":
            ref = (parc["valor"], reps)
        elif ref and ref[0] and parc["valor"] is not None:
            r = {"valor": round(parc["valor"] / ref[0], 3), "ic95": None}
            if reps is not None and ref[1] is not None:
                q = reps / ref[1]
                lo, hi = np.percentile(q, [2.5, 97.5])
                r["ic95"] = [round(float(lo), 3), round(float(hi), 3)]
            item["razao_vs_seca"] = r
        out.append(item)
    return out


def _faixas_abstencao(x: pd.DataFrame, col: str, rng) -> list[dict]:
    """Abstenção menos a média da UF (ponderada por aptos), e a variação contra o 1º turno
    também descontada da UF, por faixa de chuva."""
    x = x.assign(faixa=x[col].map(faixa_chuva))
    out = []
    grupos = [(f, x[x["faixa"] == f]) for f in FAIXAS_CHUVA]
    grupos.append(("20_ou_mais", x[x[col] >= 20]))
    for nome, g in grupos:
        pc = g.groupby("cel")[["w_dev", "w_ddev", "aptos", "aptos_d", "w_abst"]].sum()
        item = {
            "faixa": nome,
            "rotulo": ROTULO_CHUVA.get(nome, "20 mm ou mais"),
            "celulas": len(pc),
            "secoes": len(g),
            "aptos": int(pc["aptos"].sum()),
        }
        for chave, num, den in (
            ("abst_pct", "w_abst", "aptos"),
            ("dentro_uf_pp", "w_dev", "aptos"),
            ("variacao_vs_1t_dentro_uf_pp", "w_ddev", "aptos_d"),
        ):
            v, _ = _boot(pc, num, den, rng)
            if v["valor"] is not None:
                v = {
                    "valor": round(v["valor"] / 100, 2),
                    "ic95": (
                        None
                        if v["ic95"] is None
                        else [round(a / 100, 2) for a in v["ic95"]]
                    ),
                }
            item[chave] = v
        out.append(item)
    return out


def referencia_1t() -> dict | None:
    if not CLIMA_1T.exists():
        return None
    d = json.loads(CLIMA_1T.read_text(encoding="utf-8"))["bateria_x_chuva"][
        "por_exposicao"
    ]
    saida = {}
    for exp in ("chuva_votacao", "chuva_diaria"):
        fx = {f["faixa"]: f for f in d[exp]["faixas"]["bateria_votacao"]}
        saida[exp] = {
            k: {
                "parcela_pct": fx[k]["parcela_pct"]["valor"],
                "razao_vs_seca": (fx[k].get("razao_vs_ref") or {}).get("valor"),
                "ic95": (fx[k].get("razao_vs_ref") or {}).get("ic95"),
            }
            for k in fx
        }
    saida["fonte"] = "analysis/clima_1t_2026/clima.json (bateria_x_chuva, ERA5)"
    return saida


def analisar(t2: pd.DataFrame, s2: pd.DataFrame, bu: pd.DataFrame) -> dict:
    if not CLIMA_2T.exists():
        return {
            "disponivel": False,
            "nota": "analysis/clima_2t_2026/clima.json ausente",
        }
    meta = json.loads(CLIMA_2T.read_text(encoding="utf-8"))
    rng = np.random.default_rng(20261025)
    cel = _celulas()
    sc = secao_celula()
    x = t2[t2["uf"] != "ZZ"][[*CHAVE, "bateria_votacao"]].merge(
        sc, on=CHAVE, how="left"
    )
    x = x.merge(s2[[*CHAVE, "sinais"]], on=CHAVE, how="left").merge(
        cel, on="cel", how="left"
    )
    x["n"] = 1
    x["bat"] = (x["bateria_votacao"] > 0).astype(int)
    sin = x["sinais"].fillna("")
    x["local"] = sin.str.contains("bateria_votacao_local").astype(int)
    x["isolada"] = sin.str.contains("bateria_votacao_isolada").astype(int)
    medida = x["fonte_dia"].isin(ESTACAO)
    vot_med = x["fonte_votacao"].isin(ESTACAO)
    bat = {
        "chuva_dia_medida": _faixas_bateria(x[medida], "chuva_dia_mm", rng),
        "chuva_votacao_medida": (
            _faixas_bateria(x[vot_med], "chuva_votacao_mm", rng)
            if vot_med.any()
            else []
        ),
        "chuva_votacao_modelo": _faixas_bateria(
            x[x["chuva_votacao_modelo_mm"].notna()], "chuva_votacao_modelo_mm", rng
        ),
    }
    a = bu[bu["uf"] != "ZZ"][[*CHAVE, "aptos", "taxa2", "delta_pp"]].merge(
        sc, on=CHAVE, how="left"
    )
    a = a.merge(cel, on="cel", how="left")
    a = a[(a["aptos"] > 0) & a["taxa2"].notna()].copy()
    a["abst"] = 100 - a["taxa2"]
    a["dabst"] = -a["delta_pp"]
    for c, m in (("abst", "dev"), ("dabst", "ddev")):
        w = a["aptos"].astype(float).where(a[c].notna(), 0.0)
        media_uf = (a[c] * w).groupby(a["uf"]).transform("sum") / w.groupby(
            a["uf"]
        ).transform("sum")
        a[m] = a[c] - media_uf
    a["w_dev"] = a["dev"] * a["aptos"]
    a["w_ddev"] = a["ddev"].fillna(0) * a["aptos"]
    a["aptos_d"] = np.where(a["ddev"].notna(), a["aptos"], 0)
    a["w_abst"] = a["abst"] * a["aptos"]
    am = a["fonte_dia"].isin(ESTACAO)
    abst = {
        "chuva_dia_medida": _faixas_abstencao(a[am], "chuva_dia_mm", rng),
        "chuva_votacao_medida": (
            _faixas_abstencao(
                a[a["fonte_votacao"].isin(ESTACAO)], "chuva_votacao_mm", rng
            )
            if a["fonte_votacao"].isin(ESTACAO).any()
            else []
        ),
        "chuva_votacao_modelo": _faixas_abstencao(
            a[a["chuva_votacao_modelo_mm"].notna()], "chuva_votacao_modelo_mm", rng
        ),
    }
    return {
        "disponivel": True,
        "gerado_clima_em": meta["gerado_em"],
        "cobertura_celulas": meta["cobertura"],
        "estacoes": {k: v for k, v in meta["estacoes"].items() if k != "fotos"},
        "secoes_brasil": len(x),
        "secoes_com_celula": int(x["cel"].notna().sum()),
        "secoes_chuva_dia_medida": int(medida.sum()),
        "secoes_chuva_votacao_medida": int(vot_med.sum()),
        "bateria": bat,
        "abstencao": abst,
        "referencia_1t": referencia_1t(),
        "fonte": "analysis/clima_2t_2026/clima.json: estações CEMADEN a até 50 km (1/d²); "
        "sem estação, " + meta["modelo"],
        "nota": "Abstenção dentro da UF = abstenção da seção menos a média da UF ponderada "
        "por aptos; variação contra o 1º turno = (abstenção 2T − abstenção 1T) menos a "
        "mesma média da UF. IC95 por bootstrap de células (1.000 réplicas).",
    }
