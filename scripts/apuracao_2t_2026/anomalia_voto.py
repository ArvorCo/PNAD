"""Voto do grupo atípico contra as vizinhas, amostras e explicação provável.

- ``voto``: a comparação de ``secoes_voto.comparar`` (fatia de Flávio entre os dois
  no 2T contra as demais seções do mesmo município, e diferença em diferenças
  contra o 1T), com IC de 95% por bootstrap de municípios (2.000 reamostragens).
  A estimativa pontual é refeita aqui, município a município, e conferida contra
  a de ``comparar``; diferença acima do arredondamento levanta.
- ``amostras``: as seções de menor densidade, com o link do Politize-se e a
  explicação provável pela régua de ``secoes_ranking.explicar``.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2026.secoes_base import r2

from . import secoes_ranking, secoes_ref, secoes_voto

REPS = 2000
SEMENTE = 20261026
LINK = "politizese.html#uf={uf}&zona={zona}&secao={secao}"


def quadro_voto(d: pd.DataFrame) -> pd.DataFrame:
    """As colunas que ``secoes_voto.comparar`` lê, a partir dos BUs dos dois turnos."""
    fl, lu = d["flavio_2"].astype(float), d["lula_2"].astype(float)
    fl1, lu1 = d["flavio_1"].astype(float), d["lula_1"].astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        fat2 = np.where(fl + lu > 0, 100 * fl / (fl + lu), np.nan)
        fat1 = np.where(fl1 + lu1 > 0, 100 * fl1 / (fl1 + lu1), np.nan)
    return pd.DataFrame(
        {
            "uf": d["uf"],
            "mun": d["mun"],
            "fl": fl,
            "lu": lu,
            "comp": d["comparecimento_2"].astype(float),
            "fl1": fl1,
            "lu1": lu1,
            "delta_fatia_pp": fat2 - fat1,
        },
        index=d.index,
    )


def por_municipio(x: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    """Uma linha por município com seções dos dois lados (como em ``comparar``)."""
    v = x[(x["fl"] + x["lu"]) > 0].assign(s=mask.reindex(x.index).fillna(False))
    v = v.assign(
        w=v["fl"] + v["lu"],
        ok=v["delta_fatia_pp"].notna(),
    )
    v = v.assign(
        wd=np.where(v["ok"], v["w"] * v["delta_fatia_pp"].fillna(0), 0.0),
        wok=np.where(v["ok"], v["w"], 0.0),
        n_ok=v["ok"].astype(int),
    )
    g = v.groupby(["uf", "mun", "s"], sort=False)[
        ["fl", "lu", "w", "wd", "wok", "n_ok"]
    ].sum()
    g["n"] = v.groupby(["uf", "mun", "s"], sort=False).size()
    t = g.unstack("s")
    t = t[t[("n", True)].notna() & t[("n", False)].notna()]
    s = {c: t[(c, True)].to_numpy(dtype=float) for c in g.columns}
    c = {k: t[(k, False)].to_numpy(dtype=float) for k in g.columns}
    with np.errstate(divide="ignore", invalid="ignore"):
        d_fatia = 100 * (s["fl"] / s["w"] - c["fl"] / c["w"])
        did = np.where(
            (s["wok"] > 0) & (c["wok"] > 0),
            s["wd"] / s["wok"] - c["wd"] / c["wok"],
            np.nan,
        )
    return pd.DataFrame(
        {
            "n_s": s["n"],
            "n_c": c["n"],
            "w": s["w"],
            "d_fatia": d_fatia,
            "did": did,
            "n_did": np.where(np.isfinite(did), s["n_ok"], 0),
        }
    )


def _media(d: np.ndarray, w: np.ndarray) -> float:
    ok = np.isfinite(d) & (w > 0)
    return float(np.sum(w[ok] * d[ok]) / np.sum(w[ok]))


def _ic(d: np.ndarray, w: np.ndarray, reps: int, semente: int) -> list[float | None]:
    """IC de 95% (percentis) da média ponderada, reamostrando municípios."""
    ok = np.isfinite(d) & (w > 0)
    d, w = d[ok], w[ok]
    m = len(d)
    if m < 2:
        return [None, None]
    rng = np.random.default_rng(semente)
    cont = rng.multinomial(m, np.full(m, 1.0 / m), size=reps).astype(float)
    # Accelerate (macOS) avisa divisão por zero falsa em produto de matriz
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        est = (cont @ (w * d)) / (cont @ w)
    if not np.isfinite(est).all():
        raise ValueError("bootstrap não finito")
    lo, hi = np.percentile(est, [2.5, 97.5])
    return [r2(lo, 2), r2(hi, 2)]


def voto(
    d: pd.DataFrame, mask: pd.Series, reps: int = REPS, semente: int = SEMENTE
) -> dict[str, Any]:
    """Grupo atípico contra as vizinhas do mesmo município e contra o 1T."""
    x = quadro_voto(d)
    ref = secoes_voto.comparar(x, mask)
    t = por_municipio(x, mask)
    w = t["w"].to_numpy()
    out: dict[str, Any] = {
        "n": int(t["n_s"].sum()),
        "n_vizinhas": int(t["n_c"].sum()),
        "n_municipios": len(t),
        "n_grupo_total": ref["n_sinal_total"],
        "n_did": int(t["n_did"].sum()),
        "reamostragens": reps,
        "metodo": (
            "diferença por município (grupo menos demais seções do mesmo município), "
            "média ponderada pelos votos de Flávio e Lula no grupo; IC de 95% por "
            "percentis de 2.000 reamostragens de municípios com reposição"
        ),
        "nota": (
            "o grupo foi definido pelas próprias frações de voto: a comparação "
            "descreve o tamanho da diferença, não é teste independente"
        ),
    }
    if out["n"] < secoes_voto.N_MIN:
        out["insuficiente"] = True
        return out
    fat = _media(t["d_fatia"].to_numpy(), w)
    did = _media(t["did"].to_numpy(), w) if out["n_did"] >= secoes_voto.N_MIN else None
    for nome, mio, deles in (
        ("fatia", fat, ref.get("dif_fatia_flavio_vs_vizinhas_pp")),
        ("did", did, ref.get("did_fatia_flavio_pp")),
    ):
        if mio is not None and deles is not None and abs(mio - deles) > 0.006:
            raise AssertionError(f"{nome}: {mio} diverge de comparar ({deles})")
    out |= {
        "fatia_f2_vs_vizinhas_pp": r2(fat, 2),
        "ic95": _ic(t["d_fatia"].to_numpy(), w, reps, semente),
        "ep_aprox": ref.get("ep_fatia_flavio_vs_vizinhas_pp"),
        "did_vs_1t_pp": r2(did, 2) if did is not None else None,
        "ic95_did": (
            _ic(t["did"].to_numpy(), w, reps, semente + 1)
            if did is not None
            else [None, None]
        ),
        "ep_did_aprox": ref.get("ep_did_fatia_flavio_pp"),
        "flavio_no_comp_vs_vizinhas_pp": ref.get("dif_flavio_no_comp_vs_vizinhas_pp"),
        "lula_no_comp_vs_vizinhas_pp": ref.get("dif_lula_no_comp_vs_vizinhas_pp"),
    }
    return out


# ---------------------------------------------------------------- explicação


def contexto_explicacao(
    sig: pd.DataFrame, regua: pd.DataFrame
) -> tuple[pd.DataFrame, pd.Series]:
    """Colunas que ``secoes_ranking.explicar`` lê, por seção, e os saltos por local.

    ``sig``: linhas por seção de ``secoes.json`` (sinais do 2T); ``regua``: a régua
    do 1T (``secoes_ref.ler_regua``). As contas repetem ``secoes_sinais.montar``.
    """
    med_mun, med_zona = secoes_ref.medianas_1t(regua)
    chave = ["uf", "mun", "zona", "secao"]
    x = sig.merge(
        regua[[*chave, "aptos1", "comp1", "sem_bio1", "ano_nasc1", "local"]],
        on=chave,
        how="left",
    )
    x = x.merge(med_mun[["uf", "mun", "mun_p50_taxa1"]], on=["uf", "mun"], how="left")
    x = x.merge(med_zona, on=["uf", "zona"], how="left")
    x["nao_bio_pct1"] = secoes_ref.pct(x["sem_bio1"] + x["ano_nasc1"], x["comp1"])
    x["aptos_var_pct"] = secoes_ref.pct(x["aptos"] - x["aptos1"], x["aptos1"])
    x["tardia"] = x["sinal_tardia"]
    x["papel"] = x["sinal_papel"]
    x["delta"] = x["sinal_delta"]
    saltos = x[x["sinal_salto_bio"].astype(bool) & x["local"].notna()]
    por_local = saltos.groupby("local").size()
    return x.set_index(chave).sort_index(), por_local


def explicar(
    linha: pd.Series, por_local: pd.Series, agregadas: Sequence[Any]
) -> list[str]:
    li = linha.get("local")
    sl = (
        int(por_local.get(li, 0)) - int(bool(linha["sinal_salto_bio"]))
        if pd.notna(li)
        else 0
    )
    return secoes_ranking.explicar(linha, list(agregadas), sl)


def amostras(
    d: pd.DataFrame,
    idx: np.ndarray,
    nomes: Mapping[tuple[str, str], str],
    ctx: tuple[pd.DataFrame, pd.Series] | None,
    politize: Mapping[tuple[str, str, int, int], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Linhas publicáveis das seções ``idx`` (na ordem dada)."""
    out = []
    for i in idx:
        r = d.iloc[int(i)]
        k = (r["uf"], r["mun"], int(r["zona"]), int(r["secao"]))
        exp: list[str] | None = None
        if ctx is not None and k in ctx[0].index:
            linha = ctx[0].loc[k]
            exp = explicar(linha, ctx[1], (politize.get(k) or {}).get("agregadas", []))
        esc = r["escore"]
        out.append(
            {
                "uf": r["uf"],
                "mun": r["mun"],
                "municipio": nomes.get((r["uf"], r["mun"])),
                "zona": int(r["zona"]),
                "secao": int(r["secao"]),
                "grupo": int(r["grupo"]),
                "aptos_1t": int(r["aptos_1"]),
                "aptos_2t": int(r["aptos_2"]),
                "comparecimento_1t": int(r["comparecimento_1"]),
                "comparecimento_2t": int(r["comparecimento_2"]),
                "lula_1t": int(r["lula_1"]),
                "flavio_1t": int(r["flavio_1"]),
                "outros_1t": int(r["outros_1"]),
                "brancos_1t": int(r["brancos_1"]),
                "nulos_1t": int(r["nulos_1"]),
                "lula_2t": int(r["lula_2"]),
                "flavio_2t": int(r["flavio_2"]),
                "brancos_2t": int(r["brancos_2"]),
                "nulos_2t": int(r["nulos_2"]),
                "comp1_pct": r2(r["comp1"], 2),
                "comp2_pct": r2(r["comp2"], 2),
                "modelo": r["modelo"],
                "escore": int(esc) if pd.notna(esc) else None,
                "score": r2(r["score"], 3),
                "p": r2(r["p"], 6),
                "explicacao_provavel": "; ".join(exp) if exp else None,
                "sem_explicacao": (
                    exp == [secoes_ranking.SEM_EXPLICACAO] if exp else None
                ),
                "link": LINK.format(
                    uf=r["uf"], zona=int(r["zona"]), secao=int(r["secao"])
                ),
            }
        )
    return out
