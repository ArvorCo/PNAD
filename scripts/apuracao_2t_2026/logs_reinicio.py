"""Reinícios e bateria durante a votação: instante, votos antes e depois, voto da seção.

A comparação de voto usa a fatia de Flávio entre os dois finalistas no BU
(``secoes.json``: ``fatia_f`` no 2º turno, ``fatia_f1`` no 1º, na mesma seção):

- contra as vizinhas: fatia da seção menos a média das seções do mesmo município
  sem o sinal, no 2º turno;
- diferença em diferenças: (fatia 2T − fatia 1T) da seção menos a média da mesma
  variação nas vizinhas sem o sinal. Tira o que é próprio do lugar.

Municípios com menos de cinco vizinhas sem o sinal ficam fora. IC95 normal sobre
a média das seções (erro-padrão = desvio / √n). Descreve; não identifica causa.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .logs_base import CHAVE, ROOT

CONTINGENCIA = (3, 4, 6)
CLIMA = ROOT / "docs/assets/fiscais_mapa/clima/previsao.json"
INDICE_CELULAS = ROOT / "analysis/clima_1t_2026/indice_celulas_05.json"
CLIMA_1T = ROOT / "analysis/clima_1t_2026/clima.json"
FAIXAS_CHUVA = [
    (0, 1, "até 1 mm"),
    (1, 5, "1 a 5 mm"),
    (5, 20, "5 a 20 mm"),
    (20, 1e9, "20 mm ou mais"),
]


def _ic(v: pd.Series, w: pd.Series | None = None) -> dict:
    """Média e IC95 normal; com ``w``, média ponderada e erro-padrão de razão
    (sqrt(Σ w² (x − m)²) / Σ w), sem ``w``, desvio / √n."""
    ok = v.notna() if w is None else v.notna() & w.notna() & (w > 0)
    v = v[ok]
    n = len(v)
    if n < 2:
        return {"n": n, "media_pp": None, "ep_pp": None, "ic95_pp": None}
    if w is None:
        m, ep = float(v.mean()), float(v.std(ddof=1) / np.sqrt(n))
    else:
        ww = w[ok].astype(float)
        m = float(np.average(v, weights=ww))
        ep = float(np.sqrt(np.sum(ww**2 * (v - m) ** 2)) / ww.sum())
    return {
        "n": n,
        "media_pp": round(m, 3),
        "ep_pp": round(ep, 3),
        "ic95_pp": [round(m - 1.96 * ep, 3), round(m + 1.96 * ep, 3)],
    }


def comparar_voto(base: pd.DataFrame, marca: pd.Series, min_vizinhas: int = 5) -> dict:
    """``base`` tem CHAVE, fatia_f, fatia_f1 e, para o peso, fl e lu (votos dos dois
    finalistas no 2º turno); ``marca`` é booleano alinhado.

    Regra da casa: vizinhas do mesmo município, média ponderada pelos votos dos dois
    finalistas na seção com sinal. A média simples por seção vai em ``sem_peso``.
    O exterior deve chegar separado (a vizinhança lá é a cidade do consulado).
    """
    b = base.assign(g=marca.to_numpy()).dropna(subset=["fatia_f", "fatia_f1"]).copy()
    b["var"] = b["fatia_f"] - b["fatia_f1"]
    viz = (
        b[~b["g"]]
        .groupby(["uf", "mun"])
        .agg(n_viz=("var", "size"), viz_f=("fatia_f", "mean"), viz_var=("var", "mean"))
    )
    g = b[b["g"]].join(viz, on=["uf", "mun"])
    g = g[g["n_viz"] >= min_vizinhas]
    w = (g["fl"] + g["lu"]) if {"fl", "lu"} <= set(g.columns) else None
    return {
        "contra_vizinhas_2t": _ic(g["fatia_f"] - g["viz_f"], w),
        "dif_em_dif_contra_1t": _ic(g["var"] - g["viz_var"], w),
        "secoes_com_sinal": int(b["g"].sum()),
        "ponderado": w is not None,
        "sem_peso": {
            "contra_vizinhas_2t": _ic(g["fatia_f"] - g["viz_f"]),
            "dif_em_dif_contra_1t": _ic(g["var"] - g["viz_var"]),
        },
    }


def _hora_brt(seg: pd.Series, off: pd.Series) -> pd.Series:
    return seg / 3600 + off


def reinicios(t2, s1, s2, bu, off) -> dict:
    x = t2.merge(off, on=["uf", "mun"], how="left").merge(
        s1[[*CHAVE, "sinais"]].rename(columns={"sinais": "sinais1"}),
        on=CHAVE,
        how="left",
    )
    tem = x["reinicios_sist"] > 0
    troca = (x["outras_urnas"] > 0) | x["tipo_urna"].isin(CONTINGENCIA)
    no1t = x["sinais1"].fillna("").str.contains("reinicio_sistema")
    r = x[tem].copy()
    r["hora_brt"] = _hora_brt(r["reinicio_s"], r["off"].fillna(0))
    r["pct_antes"] = (
        100 * r["reinicio_antes"] / r["computados"].where(r["computados"] > 0)
    )
    horas = (
        r[r["uf"] != "ZZ"]["hora_brt"].dropna().astype(int).value_counts().sort_index()
    )
    base = x[CHAVE].merge(
        bu[[*CHAVE, "fatia_f", "fatia_f1", "fl", "lu"]], on=CHAVE, how="left"
    )
    grupos = {
        "todas com reinício": tem,
        "reinício na mesma urna": tem & ~troca,
        "reinício com troca de urna ou urna de contingência": tem & troca,
        "reinício só no 2º turno": tem & ~no1t,
        "reinício nos dois turnos": tem & no1t,
        "troca de urna ou contingência sem reinício": ~tem & troca,
    }
    voto = []
    for nome, m in grupos.items():
        voto.append({"grupo": nome, **comparar_voto(base, m.reset_index(drop=True))})
    return {
        "secoes": int(tem.sum()),
        "partidas_sistema": int(x.loc[tem, "reinicios_sist"].sum()),
        "mesma_urna": int((tem & ~troca).sum()),
        "troca_ou_contingencia": int((tem & troca).sum()),
        "so_2t": int((tem & ~no1t).sum()),
        "nos_dois": int((tem & no1t).sum()),
        "mais_de_um": int((x["reinicios_sist"] > 1).sum()),
        "hora_brt": {str(int(h)): int(n) for h, n in horas.items()},
        "votos_antes_mediana": _r(r["reinicio_antes"].median()),
        "votos_depois_mediana": _r(r["reinicio_depois"].median()),
        "pct_votos_antes_mediana": _r(r["pct_antes"].median()),
        "pct_antes_quartis": [
            _r(r["pct_antes"].quantile(q)) for q in (0.25, 0.5, 0.75)
        ],
        "sem_voto_depois": int((r["reinicio_depois"] == 0).sum()),
        "contagem_confere": int(r["contagem_confere"].sum()),
        "voto": voto,
    }


def _r(v, casas: int = 1):
    return None if v is None or pd.isna(v) else round(float(v), casas)


def chuva_municipal() -> pd.DataFrame:
    """Chuva prevista (08h–17h de Brasília) por município, média das células pelo eleitorado."""
    if not CLIMA.exists() or not INDICE_CELULAS.exists():
        return pd.DataFrame(columns=["uf", "mun", "chuva_mm"])
    prev = json.loads(CLIMA.read_text(encoding="utf-8"))["celulas"]
    idx = json.loads(INDICE_CELULAS.read_text(encoding="utf-8"))["celulas"]
    linhas = []
    for cel, muns in idx.items():
        mm = (prev.get(cel) or {}).get("chuva_mm")
        if mm is None:
            continue
        for uf, mun, _nome, _locais, eleitores in muns:
            linhas.append((uf, mun, float(mm), float(eleitores)))
    df = pd.DataFrame(linhas, columns=["uf", "mun", "mm", "w"])
    df["mw"] = df["mm"] * df["w"]
    g = df.groupby(["uf", "mun"])[["mw", "w"]].sum()
    return (g["mw"] / g["w"]).rename("chuva_mm").reset_index()


def bateria(t2, s1, s2, bu) -> dict:
    j = s2[[*CHAVE, "sinais", "bateria_simultaneas"]].merge(
        s1[[*CHAVE, "sinais"]].rename(columns={"sinais": "sinais1"}),
        on=CHAVE,
        how="outer",
    )
    s2s, s1s = j["sinais"].fillna(""), j["sinais1"].fillna("")
    out = {}
    for crit in ("bateria_votacao_local", "bateria_votacao_isolada"):
        out[crit] = {
            "2t": int(s2s.str.contains(crit).sum()),
            "1t": int(s1s.str.contains(crit).sum()),
            "nos_dois": int((s2s.str.contains(crit) & s1s.str.contains(crit)).sum()),
        }
    x = t2[t2["uf"] != "ZZ"].merge(chuva_municipal(), on=["uf", "mun"], how="left")
    x = x.merge(s2[[*CHAVE, "sinais"]], on=CHAVE, how="left")
    x["bat"] = x["bateria_votacao"] > 0
    x["local"] = x["sinais"].fillna("").str.contains("bateria_votacao_local")
    x["isolada"] = x["sinais"].fillna("").str.contains("bateria_votacao_isolada")
    faixas = []
    for lo, hi, nome in FAIXAS_CHUVA:
        g = x[(x["chuva_mm"] >= lo) & (x["chuva_mm"] < hi)]
        faixas.append(
            {
                "faixa": nome,
                "secoes": len(g),
                "pct_bateria_votacao": _r(100 * g["bat"].mean(), 2) if len(g) else None,
                "pct_local": _r(100 * g["local"].mean(), 2) if len(g) else None,
                "pct_isolada": _r(100 * g["isolada"].mean(), 2) if len(g) else None,
            }
        )
    out["por_chuva_prevista"] = faixas
    out["votos_medios_local"] = _r(x.loc[x["local"], "computados"].mean(), 1)
    out["sem_chuva_prevista"] = int(x["chuva_mm"].isna().sum())
    out["secoes_bateria_votacao"] = int(x["bat"].sum())
    out["pct_bateria_votacao"] = _r(100 * x["bat"].mean(), 2)
    base = t2[CHAVE].merge(
        bu[[*CHAVE, "fatia_f", "fatia_f1", "fl", "lu"]], on=CHAVE, how="left"
    )
    sinais_t2 = (
        t2[CHAVE]
        .merge(s2[[*CHAVE, "sinais"]], on=CHAVE, how="left")["sinais"]
        .fillna("")
    )
    out["voto"] = [
        {
            "grupo": "bateria durante a votação junto com o município",
            **comparar_voto(base, sinais_t2.str.contains("bateria_votacao_local")),
        },
        {
            "grupo": "bateria durante a votação só nesta urna",
            **comparar_voto(base, sinais_t2.str.contains("bateria_votacao_isolada")),
        },
    ]
    out["referencia_1t"] = referencia_1t()
    out["fonte_chuva"] = (
        "previsão Open-Meteo de 24/10 22h21 UTC para 08h–17h de 25/10, célula de 0,5°, "
        "média das células do município pelo eleitorado; não é chuva observada"
    )
    return out


def referencia_1t() -> dict | None:
    """O achado do 1º turno com chuva observada (ERA5), lido de ``clima.json``."""
    if not CLIMA_1T.exists():
        return None
    d = json.loads(CLIMA_1T.read_text(encoding="utf-8"))
    fx = d["bateria_x_chuva"]["por_exposicao"]["chuva_votacao"]["faixas"][
        "bateria_votacao"
    ]
    por = {x["faixa"]: x for x in fx}
    if "seca" not in por or "forte" not in por:
        return None
    return {
        "seca_pct": por["seca"]["parcela_pct"]["valor"],
        "forte_pct": por["forte"]["parcela_pct"]["valor"],
        "razao_forte": por["forte"].get("razao_vs_ref", {}).get("valor"),
        "fonte": "analysis/clima_1t_2026/clima.json (bateria_x_chuva, chuva nas horas de votação, ERA5)",
    }
