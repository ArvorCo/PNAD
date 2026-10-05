"""Pergunta 2 do fechamento: onde a eleição termina tarde nos dois anos.

Régua única dos dois anos: a hora de recebimento do boletim no TSE. Como 2022
chegou, no conjunto, mais tarde que 2026, a persistência usa a posição relativa
dentro do próprio ano (percentil da mediana municipal), não um corte de hora
fixo. Persistente = no décimo mais tardio do país nos dois anos. O corte de hora
fixo pedido (p90 do município depois das 19h) também é publicado.

Município só entra com cobertura de 2026 de ao menos 95% das seções principais
e com 3 seções ou mais nos dois anos. Local de votação: casado entre os anos pelo
nome normalizado dentro do mesmo município.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import secoes_base
from .fechamento_base import (
    COBERTURA_MUNICIPIO,
    MIN_SECOES_MUNICIPIO,
    RURAIS,
    pearson,
    spearman,
)
from .fechamento_modelo import BOOT, SEMENTE
from .secoes_2022 import normalizar_local
from .secoes_base import FLAVIO, LULA, r2

DECIL = 0.9
CORTE_HORA = 120  # 19h
N_LISTA = 30
N_LOCAIS = 40
TIPOS_RURAIS = RURAIS | {"aldeia ou terra indígena"}


def _q90(x: pd.Series) -> float:
    return float(x.quantile(0.9))


def municipios_2026(d26: pd.DataFrame, principais: pd.DataFrame) -> pd.DataFrame:
    ok = d26.dropna(subset=["rec_min"])
    g = ok.groupby(["uf", "mun"])
    m = pd.DataFrame(
        {
            "secoes_2026": g.size(),
            "med26": g["rec_min"].median(),
            "p9026": g["rec_min"].agg(_q90),
            "enc_med26": g["enc_min"].median(),
            "enc18_26": g["enc_min"].agg(lambda s: 100 * float((s >= 60).mean())),
            "trans_med26": (ok["rec_min"] - ok["enc_min"])
            .groupby([ok["uf"], ok["mun"]])
            .median(),
            "eleitorado_2026": g["aptos"].sum(),
            "rural_pct": g["tipo_inferido"].agg(
                lambda s: 100 * float(s.isin(TIPOS_RURAIS).mean())
            ),
            "lat": g["lat"].mean(),
            "lon": g["lon"].mean(),
            "municipio": g["municipio"].first(),
            "ibge": g["ibge"].first(),
            "regiao": g["regiao"].first(),
        }
    )
    val = ok[ok["valida"]]
    gv = val.groupby(["uf", "mun"])
    soma = gv[[f"v{LULA}", f"v{FLAVIO}", "validos"]].sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        m["lula26"] = 100 * soma[f"v{LULA}"] / soma["validos"]
        m["flavio26"] = 100 * soma[f"v{FLAVIO}"] / soma["validos"]
    cob = principais.set_index(["uf", "mun"])
    m = m.join(cob[["principais"]], how="left")
    m["cobertura"] = m["secoes_2026"] / m["principais"]
    return m


def municipios_2022(d22: pd.DataFrame) -> pd.DataFrame:
    ok = d22.dropna(subset=["rec_min"])
    g = ok.groupby(["uf", "mun"])
    soma = g[["lula_1t", "bolsonaro_1t", "nominais_1t"]].sum()
    out = pd.DataFrame(
        {
            "secoes_2022": g.size(),
            "med22": g["rec_min"].median(),
            "p9022": g["rec_min"].agg(_q90),
        }
    )
    out["lula22"] = 100 * soma["lula_1t"] / soma["nominais_1t"]
    out["bolsonaro22"] = 100 * soma["bolsonaro_1t"] / soma["nominais_1t"]
    return out


def comparar(m26: pd.DataFrame, m22: pd.DataFrame) -> pd.DataFrame:
    m = m26.join(m22, how="inner")
    m = m[
        (m["cobertura"] >= COBERTURA_MUNICIPIO)
        & (m["secoes_2026"] >= MIN_SECOES_MUNICIPIO)
        & (m["secoes_2022"] >= MIN_SECOES_MUNICIPIO)
    ].copy()
    m["pct22"] = m["med22"].rank(pct=True)
    m["pct26"] = m["med26"].rank(pct=True)
    m["persistente"] = (m["pct22"] >= DECIL) & (m["pct26"] >= DECIL)
    return m


def correlacoes(m: pd.DataFrame) -> dict[str, Any]:
    x, y = m["med22"].to_numpy(), m["med26"].to_numpy()
    rng = np.random.default_rng(SEMENTE)
    n = len(m)
    reps = []
    for _ in range(BOOT):
        i = rng.integers(0, n, n)
        reps.append(spearman(x[i], y[i]))
    reps_a = np.asarray(reps, dtype=float)
    reps_a = reps_a[np.isfinite(reps_a)]
    uf = m.index.get_level_values("uf")
    dx = m["med22"] - m.groupby(uf)["med22"].transform("mean")
    dy = m["med26"] - m.groupby(uf)["med26"].transform("mean")
    return {
        "municipios": n,
        "pearson": r2(pearson(x, y), 3),
        "spearman": r2(spearman(x, y), 3),
        "spearman_ic95": (
            [
                r2(np.percentile(reps_a, 2.5), 3),
                r2(np.percentile(reps_a, 97.5), 3),
            ]
            if len(reps_a)
            else [None, None]
        ),
        "pearson_dentro_uf": r2(pearson(dx, dy), 3),
        "spearman_dentro_uf": r2(spearman(dx, dy), 3),
        "bootstrap": BOOT,
        "semente": SEMENTE,
        "leitura": (
            "correlação entre a mediana de recebimento do município em 2022 e em 2026; "
            "dentro da UF, depois de tirar a média da UF em cada ano"
        ),
    }


def _amostra(d26: pd.DataFrame, filtro: pd.Series) -> dict[str, Any] | None:
    g = d26[filtro].sort_values("rec_min", ascending=False)
    if g.empty:
        return None
    return secoes_base.secao_ref(g.iloc[0].to_dict())


def _item_municipio(uf: str, mun: str, x: pd.Series, d26: pd.DataFrame) -> dict:
    return {
        "uf": uf.upper(),
        "regiao": x["regiao"],
        "municipio": x["municipio"],
        "mun_tse": mun,
        "ibge": x["ibge"] if isinstance(x["ibge"], str) else None,
        "eleitorado_2026": int(x["eleitorado_2026"]),
        "secoes_2026": int(x["secoes_2026"]),
        "secoes_2022": int(x["secoes_2022"]),
        "mediana_2022": r2(x["med22"], 1),
        "mediana_2026": r2(x["med26"], 1),
        "p90_2022": r2(x["p9022"], 1),
        "p90_2026": r2(x["p9026"], 1),
        "percentil_2022": r2(100 * x["pct22"], 1),
        "percentil_2026": r2(100 * x["pct26"], 1),
        "encerramento_mediana_2026": r2(x["enc_med26"], 1),
        "encerramento_depois_1800_pct": r2(x["enc18_26"], 1),
        "transmissao_mediana_2026": r2(x["trans_med26"], 1),
        "rural_pct": r2(x["rural_pct"], 1),
        "lula_pct_2026": r2(x["lula26"]),
        "flavio_pct_2026": r2(x["flavio26"]),
        "lula_pct_2022": r2(x["lula22"]),
        "bolsonaro_pct_2022": r2(x["bolsonaro22"]),
        "amostra": _amostra(d26, (d26["uf"] == uf) & (d26["mun"] == mun)),
    }


def locais(d26: pd.DataFrame, d22: pd.DataFrame, mun_ok: pd.Index) -> dict[str, Any]:
    a = d26.dropna(subset=["rec_min"]).copy()
    b = d22.dropna(subset=["rec_min"]).copy()
    a["ln"] = a["local"].fillna("").map(normalizar_local)
    b["ln"] = b["local_2022"].fillna("").map(normalizar_local)
    a = a[(a["ln"] != "") & a.set_index(["uf", "mun"]).index.isin(mun_ok)]
    b = b[b["ln"] != ""]
    k = ["uf", "mun", "ln"]
    l26 = a.groupby(k).agg(
        secoes_2026=("rec_min", "size"),
        med26=("rec_min", "median"),
        enc26=("enc_min", "median"),
        aptos=("aptos", "sum"),
        tipo=("grupo_tipo", lambda s: s.mode().iloc[0]),
        municipio=("municipio", "first"),
        local=("local", "first"),
    )
    l22 = b.groupby(k).agg(secoes_2022=("rec_min", "size"), med22=("rec_min", "median"))
    m = l26.join(l22, how="inner")
    if m.empty:
        return {"casados": 0}
    m["pct22"] = m["med22"].rank(pct=True)
    m["pct26"] = m["med26"].rank(pct=True)
    m["persistente"] = (m["pct22"] >= DECIL) & (m["pct26"] >= DECIL)
    p = m[m["persistente"]]
    por_tipo = []
    for tipo, g in m.groupby("tipo"):
        n_p = int(g["persistente"].sum())
        por_tipo.append(
            {
                "tipo": tipo,
                "locais": len(g),
                "persistentes": n_p,
                "pct_dos_locais": r2(100 * len(g) / len(m)),
                "pct_dos_persistentes": r2(100 * n_p / len(p)) if len(p) else None,
            }
        )
    por_tipo.sort(key=lambda r: -r["persistentes"])
    lista = []
    ordem = p.assign(_m=(p["pct22"] + p["pct26"]) / 2).sort_values(
        ["_m", "med26"], ascending=False
    )
    for (uf, mun, ln), x in ordem.head(N_LOCAIS).iterrows():
        filtro = (a["uf"] == uf) & (a["mun"] == mun) & (a["ln"] == ln)
        lista.append(
            {
                "uf": uf.upper(),
                "municipio": x["municipio"],
                "mun_tse": mun,
                "local": x["local"],
                "tipo": x["tipo"],
                "secoes_2026": int(x["secoes_2026"]),
                "secoes_2022": int(x["secoes_2022"]),
                "mediana_2022": r2(x["med22"], 1),
                "mediana_2026": r2(x["med26"], 1),
                "encerramento_mediana_2026": r2(x["enc26"], 1),
                "amostra": _amostra(a, filtro),
            }
        )
    esperado = len(m) * (1 - DECIL) ** 2
    return {
        "criterio": (
            "mesmo nome de local (sem acento, maiúsculas, sem pontuação) no mesmo "
            "município nos dois anos; persistente = mediana de recebimento no décimo "
            "mais tardio dos locais casados nos dois anos"
        ),
        "casados": len(m),
        "spearman": r2(spearman(m["med22"], m["med26"]), 3),
        "persistentes": len(p),
        "esperado_independencia": r2(esperado, 1),
        "razao": r2(len(p) / esperado, 2) if esperado else None,
        "secoes_2026_nos_persistentes": int(p["secoes_2026"].sum()),
        "eleitorado_2026_nos_persistentes": int(p["aptos"].sum()),
        "por_tipo": por_tipo,
        "lista": lista,
    }


def persistencia(
    d26: pd.DataFrame, d22: pd.DataFrame, principais: pd.DataFrame
) -> dict[str, Any]:
    m26 = municipios_2026(d26, principais)
    m22 = municipios_2022(d22)
    m = comparar(m26, m22)
    if m.empty:
        return {"municipios": 0}
    esperado = len(m) * (1 - DECIL) ** 2
    pers = m[m["persistente"]]
    ordem = pers.assign(_m=(pers["pct22"] + pers["pct26"]) / 2).sort_values(
        ["_m", "med26"], ascending=False
    )
    lista = [
        _item_municipio(uf, mun, x, d26)
        for (uf, mun), x in ordem.head(N_LISTA).iterrows()
    ]
    p26 = m["p9026"] >= CORTE_HORA
    p22 = m["p9022"] >= CORTE_HORA
    pontos = []
    for (uf, mun), x in m.iterrows():
        pontos.append(
            [
                uf.upper(),
                mun,
                x["municipio"],
                r2(x["lat"], 3),
                r2(x["lon"], 3),
                int(x["eleitorado_2026"]),
                r2(x["med22"], 1),
                r2(x["med26"], 1),
                r2(x["p9022"], 1),
                r2(x["p9026"], 1),
                int(bool(x["persistente"])),
                r2(x["rural_pct"], 0),
            ]
        )
    pers_rural = float((pers["rural_pct"] >= 50).mean()) if len(pers) else None
    todos_rural = float((m["rural_pct"] >= 50).mean())
    return {
        "regua": "hora de recebimento do boletim no TSE, em minutos depois das 17h de Brasília",
        "criterio_municipio": (
            f"cobertura de 2026 de ao menos {int(100 * COBERTURA_MUNICIPIO)}% das seções "
            f"principais e {MIN_SECOES_MUNICIPIO} seções ou mais nos dois anos"
        ),
        "municipios_2026": len(m26),
        "municipios": len(m),
        "mediana_das_medianas": {
            "2022": r2(m["med22"].median(), 1),
            "2026": r2(m["med26"].median(), 1),
        },
        "correlacao": correlacoes(m),
        "decil": {
            "corte_2022_min": r2(m["med22"].quantile(DECIL), 1),
            "corte_2026_min": r2(m["med26"].quantile(DECIL), 1),
            "persistentes": len(pers),
            "esperado_independencia": r2(esperado, 1),
            "razao": r2(len(pers) / esperado, 2) if esperado else None,
            "rural_maioria_pct_persistentes": (
                r2(100 * pers_rural) if pers_rural is not None else None
            ),
            "rural_maioria_pct_todos": r2(100 * todos_rural),
            "eleitorado_2026_persistentes": int(pers["eleitorado_2026"].sum()),
            "encerramento_mediana_persistentes": r2(pers["enc_med26"].median(), 1),
            "encerramento_mediana_todos": r2(m["enc_med26"].median(), 1),
            "transmissao_mediana_persistentes": r2(pers["trans_med26"].median(), 1),
            "transmissao_mediana_todos": r2(m["trans_med26"].median(), 1),
        },
        "p90_depois_19h": {
            "definicao": "p90 da hora de recebimento das seções do município às 19h de Brasília ou depois",
            "municipios_2026": int(p26.sum()),
            "municipios_2022": int(p22.sum()),
            "ambos": int((p26 & p22).sum()),
            "so_2026": int((p26 & ~p22).sum()),
            "so_2022": int((~p26 & p22).sum()),
            "nenhum": int((~p26 & ~p22).sum()),
        },
        "lista": lista,
        "pontos": {
            "colunas": [
                "uf",
                "mun_tse",
                "municipio",
                "lat",
                "lon",
                "eleitorado",
                "med22",
                "med26",
                "p9022",
                "p9026",
                "persistente",
                "rural_pct",
            ],
            "linhas": pontos,
        },
        "locais": locais(d26, d22, m.index),
    }
