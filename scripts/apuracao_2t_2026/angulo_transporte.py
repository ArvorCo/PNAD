"""Ângulo do transporte em massa e da ordem de chegada dos lotes (2º turno de 2026).

Duas perguntas, refeitas por seção:

1. **Marca de transporte.** Se houve mobilização de última hora onde Lula é forte,
   a abstenção cai mais nos quintis fortes de Lula, a última parte do dia pesa mais
   lá e a fatia de Flávio nas seções com salto de comparecimento cai contra as
   vizinhas do mesmo município (diferença em diferenças).
2. **Ordem de chegada.** Seções ordenadas pelo recebimento do BU (``rec_min``) e
   pelo encerramento (``enc_min``), em 20 vintis de mesmo número de votos nos dois
   finalistas: fatia de Flávio no 2T, no 1T nas mesmas seções e a diferença.

Fontes, todas locais e somente leitura: linhas por seção de ``secoes.json``
(``secoes_linhas.bloco``), métricas do log do 2T e amostra do 1T (cache do
capítulo de logs, ``data/outputs/logs_2t_capitulo/``) e o 2º turno de 2022 por
município (``data/outputs/apuracao_2t_2026/tse2022_2t_municipios.json``). Exterior
fora. Rótulo: pede explicação, não prova irregularidade.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DADOS = ROOT / "analysis/apuracao_2t_2026/dados"
CACHE_LOGS = ROOT / "data/outputs/logs_2t_capitulo"
TSE2022 = ROOT / "data/outputs/apuracao_2t_2026/tse2022_2t_municipios.json"
ROTULO = "pede explicação, não prova irregularidade"
SALVADOR = "38490"
CHAVE = ["uf", "mun", "zona", "secao"]
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
REGIAO = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "Norte"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Nordeste"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "Centro-Oeste"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Sudeste"),
    **dict.fromkeys(["PR", "RS", "SC"], "Sul"),
}
SALTO_PP = 5.0  # salto de comparecimento contra a mediana do município (sinal_delta)
FIM_DIA_PP = 10.0  # parcela 15h–17h acima da mediana do município
MIN_SECOES_MUN = 10
N_VINTIS = 20
REPS = 400


# ------------------------------------------------------------------ leitura


def hhmm(rec_min: float | None) -> str | None:
    """Minutos depois das 17:00 de Brasília viram 'HH:MM'."""
    if rec_min is None or not np.isfinite(rec_min):
        return None
    m = round(17 * 60 + float(rec_min))
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def parcela_fim(cph: str | dict, off: int) -> tuple[float, float, float]:
    """(total, cômputos 15h–16h59, cômputos 16h–16h59) em hora de Brasília."""
    d = json.loads(cph) if isinstance(cph, str) else (cph or {})
    tot = fim = ult = 0.0
    for h, n in d.items():
        hb = int(h) + int(off)
        tot += n
        if hb in (15, 16):
            fim += n
        if hb == 16:
            ult += n
    return tot, fim, ult


def deslocamentos(logs: pd.DataFrame) -> pd.DataFrame:
    """8 − hora modal do primeiro cômputo do município (regra de ``logs_cadencia``)."""
    x = logs[logs["primeiro_s"].notna()].copy()
    x["h0"] = (x["primeiro_s"] // 3600).astype(int)
    moda = x.groupby(["uf", "mun"])["h0"].agg(lambda s: s.mode().iloc[0])
    return (8 - moda).rename("off").reset_index()


def com_fim_do_dia(logs: pd.DataFrame, off: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por seção com cômputos totais, 15h–17h e 16h–17h (Brasília)."""
    x = logs[logs["cph_ok"].astype(bool)].merge(off, on=["uf", "mun"], how="inner")
    v = [parcela_fim(c, o) for c, o in zip(x["cph"], x["off"], strict=True)]
    arr = np.array(v, dtype=float).reshape(-1, 3)
    out = x[CHAVE].copy()
    out["cmp"], out["cmp_fim"], out["cmp_ult"] = arr[:, 0], arr[:, 1], arr[:, 2]
    return out[out["cmp"] > 0]


def carregar(S: dict) -> dict:
    """Tabelas da análise a partir dos arquivos locais (levanta se faltarem)."""
    from . import secoes_linhas

    b = secoes_linhas.exigir(S)
    sec = pd.DataFrame(b["linhas"], columns=b["colunas"])
    t2 = pd.read_parquet(
        CACHE_LOGS / "metricas_2t.parquet",
        columns=[*CHAVE, "cph", "cph_ok", "primeiro_s"],
    )
    t2["uf"] = t2["uf"].str.upper()
    a1 = pd.DataFrame(
        json.loads(x)
        for x in (CACHE_LOGS / "amostra_1t.jsonl").read_text("utf-8").splitlines()
    )[[*CHAVE, "cph", "cph_ok", "primeiro_s"]]
    a1["uf"] = a1["uf"].str.upper()
    off = deslocamentos(t2[t2["uf"] != "ZZ"])
    m22 = json.loads(TSE2022.read_text("utf-8"))["municipios"]
    return {
        "sec": sec,
        "fim2": com_fim_do_dia(t2[t2["uf"] != "ZZ"], off),
        "fim1": com_fim_do_dia(a1[a1["uf"] != "ZZ"], off),
        "m22": m22,
    }


# ------------------------------------------------------------------ preparo


def preparar(sec: pd.DataFrame, m22: dict, fim2: pd.DataFrame, fim1: pd.DataFrame):
    """Seções do Brasil com 1T pareado, quintil de Lula e fim do dia nos dois turnos."""
    x = sec[(sec["uf"] != "ZZ")].copy()
    x = x[x["taxa1"].notna() & x["fl1"].notna() & ((x["fl1"] + x["lu1"]) > 0)]
    x = x[(x["fl"] + x["lu"]) > 0].copy()
    x["regiao"] = x["uf"].map(REGIAO)
    x["v2"] = x["fl"] + x["lu"]
    x["v1"] = x["fl1"] + x["lu1"]
    x["lula1"] = 100 * x["lu1"] / x["v1"]
    x["abst2"] = 100 - x["taxa2"]
    x["abst1"] = 100 - x["taxa1"]
    pa22 = {
        k: 100 * v["abstencao"] / v["aptos"] for k, v in m22.items() if v.get("aptos")
    }
    x["abst22"] = x["mun"].map(pa22)
    x["quintil"] = quintis(x["lula1"].to_numpy(), x["aptos"].to_numpy())
    x = x.merge(fim2, on=CHAVE, how="left").merge(
        fim1.rename(
            columns={"cmp": "cmp1", "cmp_fim": "cmp_fim1", "cmp_ult": "cmp_ult1"}
        ),
        on=CHAVE,
        how="left",
    )
    x["fim_pct"] = 100 * x["cmp_fim"] / x["cmp"]
    return x.reset_index(drop=True)


def quintis(valor: np.ndarray, peso: np.ndarray, n: int = 5) -> np.ndarray:
    """Grupo 1..n por valor crescente, cada um com a mesma soma de pesos."""
    ordem = np.argsort(valor, kind="stable")
    acum = np.cumsum(peso[ordem]) / peso.sum()
    g = np.minimum((acum * n - 1e-12).astype(int), n - 1) + 1
    out = np.empty_like(g)
    out[ordem] = g
    return out


def media(v: pd.Series, w: pd.Series) -> float | None:
    ok = v.notna() & w.notna()
    if not ok.any() or w[ok].sum() == 0:
        return None
    return float(np.average(v[ok], weights=w[ok]))


def r2(x: float | None, casas: int = 2) -> float | None:
    return None if x is None or not np.isfinite(x) else round(float(x), casas)


# ------------------------------------------------------------------ marca de transporte


def did_vizinhas(x: pd.DataFrame, marca: pd.Series, reps: int = REPS, seed: int = 7):
    """Fatia de Flávio 2T−1T nas seções marcadas menos nas vizinhas do município.

    Cada município com ao menos uma marcada e uma vizinha entra com a diferença
    entre as variações ponderadas por votos; a média pondera pelos votos das
    marcadas. IC de 95% por reamostragem de municípios.
    """
    y = x.assign(m=marca.to_numpy())
    n_mun = y.groupby(["uf", "mun"])["m"].transform("size")
    y = y[n_mun >= MIN_SECOES_MUN]
    g = y.groupby(["uf", "mun", "m"]).agg(
        f2=("fl", "sum"), v2=("v2", "sum"), f1=("fl1", "sum"), v1=("v1", "sum")
    )
    g["sw"] = 100 * (g["f2"] / g["v2"] - g["f1"] / g["v1"])
    t = g["sw"].unstack("m")
    w = g["v2"].unstack("m")
    if True not in t.columns or False not in t.columns:
        return {"n_secoes_marcadas": 0}
    ok = t[True].notna() & t[False].notna()
    d = (t[True] - t[False])[ok].to_numpy()
    p = w[True][ok].to_numpy()
    if not len(d):
        return {"n_secoes_marcadas": 0}
    est = float(np.average(d, weights=p))
    rng = np.random.default_rng(seed)
    if len(d) >= 5:
        bs = []
        for _ in range(reps):
            i = rng.integers(0, len(d), len(d))
            bs.append(np.average(d[i], weights=p[i]))
        reamostra = "municípios"
    else:
        bs = _bs_secoes(y, rng, reps)
        reamostra = "seções, dentro de marcadas e vizinhas"
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {
        "reamostragem": reamostra,
        "n_secoes_marcadas": int(y["m"].sum()),
        "n_municipios": len(d),
        "did_pp": r2(est),
        "ic95": [r2(lo), r2(hi)],
        "swing_marcadas_pp": r2(float(np.average(t[True][ok], weights=p))),
        "swing_vizinhas_pp": r2(float(np.average(t[False][ok], weights=p))),
    }


def _bs_secoes(y: pd.DataFrame, rng, reps: int) -> list[float]:
    """IC de um ou poucos municípios: reamostra seções em cada grupo."""
    grupos = {
        k: g[["fl", "v2", "fl1", "v1"]].to_numpy(float) for k, g in y.groupby("m")
    }
    out = []
    for _ in range(reps):
        sw = {}
        for k, a in grupos.items():
            b = a[rng.integers(0, len(a), len(a))]
            sw[k] = 100 * (
                b[:, 0].sum() / b[:, 1].sum() - b[:, 2].sum() / b[:, 3].sum()
            )
        out.append(sw[True] - sw[False])
    return out


def marcas(x: pd.DataFrame) -> dict[str, pd.Series]:
    med_fim = x.groupby(["uf", "mun"])["fim_pct"].transform("median")
    salto = x["delta_rel_pp"] >= SALTO_PP
    fim = (x["fim_pct"] - med_fim) >= FIM_DIA_PP
    return {"salto": salto, "fim": fim.fillna(False), "salto_e_fim": salto & fim}


def resumo_grupo(g: pd.DataFrame) -> dict:
    v1 = g["v1"].sum()
    v2 = g["v2"].sum()
    f2 = 100 * g["fl"].sum() / v2
    f1 = 100 * g["fl1"].sum() / v1
    ab2 = media(g["abst2"], g["aptos"])
    ab1 = media(g["abst1"], g["aptos"])
    ab22 = media(g["abst22"], g["aptos"])
    c2 = g[g["cmp"].notna()]
    c1 = g[g["cmp1"].notna() & g["cmp"].notna()]
    fim2 = 100 * c2["cmp_fim"].sum() / c2["cmp"].sum() if len(c2) else None
    ult2 = 100 * c2["cmp_ult"].sum() / c2["cmp"].sum() if len(c2) else None
    fim1 = 100 * c1["cmp_fim1"].sum() / c1["cmp1"].sum() if len(c1) else None
    fim2m = 100 * c1["cmp_fim"].sum() / c1["cmp"].sum() if len(c1) else None
    return {
        "secoes": len(g),
        "aptos": int(g["aptos"].sum()),
        "lula1_min": r2(float(g["lula1"].min())),
        "lula1_max": r2(float(g["lula1"].max())),
        "abst_1t": r2(ab1),
        "abst_2t": r2(ab2),
        "abst_2022_mun": r2(ab22),
        "delta_abst_1t_pp": r2(None if ab1 is None else ab2 - ab1),
        "delta_abst_2022_pp": r2(None if ab22 is None else ab2 - ab22),
        "fatia_f_1t": r2(f1),
        "fatia_f_2t": r2(f2),
        "swing_f_pp": r2(f2 - f1),
        "fim_dia_2t_pct": r2(fim2),
        "ultima_hora_2t_pct": r2(ult2),
        "secoes_amostra_1t": len(c1),
        "fim_dia_1t_pct": r2(fim1),
        "fim_dia_2t_mesmas_pct": r2(fim2m),
        "delta_fim_dia_pp": r2(None if fim1 is None or fim2m is None else fim2m - fim1),
    }


def transporte(x: pd.DataFrame, reps: int = REPS) -> dict:
    mk = marcas(x)
    por_q = []
    for q in range(1, 6):
        sel = x["quintil"] == q
        g = x[sel]
        item = {"quintil": q, **resumo_grupo(g)}
        item["did"] = {
            k: did_vizinhas(g, v[sel], reps=reps, seed=q) for k, v in mk.items()
        }
        por_q.append(item)
    por_r = []
    for reg in REGIOES:
        sel = x["regiao"] == reg
        g = x[sel]
        if not len(g):
            continue
        item = {"regiao": reg, **resumo_grupo(g)}
        item["did"] = {
            k: did_vizinhas(g, v[sel], reps=reps, seed=11) for k, v in mk.items()
        }
        por_r.append(item)
    q1, q5 = por_q[0], por_q[-1]

    def dif(c):
        a, b = q5.get(c), q1.get(c)
        return None if a is None or b is None else r2(a - b)

    brasil = {**resumo_grupo(x)}
    brasil["did"] = {k: did_vizinhas(x, v, reps=reps, seed=3) for k, v in mk.items()}
    return {
        "brasil": brasil,
        "quintis": por_q,
        "regioes": por_r,
        "q5_menos_q1": {
            c: dif(c)
            for c in (
                "delta_abst_1t_pp",
                "delta_abst_2022_pp",
                "fim_dia_2t_pct",
                "delta_fim_dia_pp",
                "swing_f_pp",
            )
        },
        "correlacao_secao": correlacoes(x),
    }


def correlacoes(x: pd.DataFrame) -> dict:
    """Dentro do município: variação do comparecimento contra variação da fatia."""
    y = x.copy()
    y["dc"] = y["taxa2"] - y["taxa1"]
    y["sw"] = 100 * (y["fl"] / y["v2"] - y["fl1"] / y["v1"])
    for c in ("dc", "sw"):
        y[c + "_d"] = y[c] - y.groupby(["uf", "mun"])[c].transform("mean")
    c = np.corrcoef(y["dc_d"], y["sw_d"])[0, 1]
    beta = float(np.polyfit(y["dc_d"], y["sw_d"], 1)[0])
    return {
        "secoes": len(y),
        "corr_dentro_municipio": r2(float(c), 3),
        "inclinacao_pp_por_pp": r2(beta, 3),
        "nota": "variação da fatia de Flávio (pp) por ponto de comparecimento a mais, ambas centradas no município",
    }


def bahia(x: pd.DataFrame, m22: dict) -> dict:
    out = {}
    for nome, sel in (
        ("Salvador", x["mun"] == SALVADOR),
        ("Bahia sem Salvador", (x["uf"] == "BA") & (x["mun"] != SALVADOR)),
        ("Bahia", x["uf"] == "BA"),
        ("Brasil", pd.Series(True, index=x.index)),
    ):
        g = x[sel]
        item = resumo_grupo(g)
        item["did_salto"] = did_vizinhas(g, marcas(x)["salto"][sel], seed=5)
        out[nome] = item
    s22 = m22.get(SALVADOR, {})
    ba = [v for v in m22.values() if v.get("uf") == "BA"]
    out["Salvador"]["bolsonaro_2022_h2h"] = r2(
        100 * s22["bolsonaro"] / (s22["bolsonaro"] + s22["lula"])
    )
    out["Bahia"]["bolsonaro_2022_h2h"] = r2(
        100
        * sum(v["bolsonaro"] for v in ba)
        / sum(v["bolsonaro"] + v["lula"] for v in ba)
    )
    return out


# ------------------------------------------------------------------ ordem de chegada


def vintis(x: pd.DataFrame, coluna: str, n: int = N_VINTIS) -> list[dict]:
    """Grupos de mesmo número de votos nos dois finalistas, pela ordem de ``coluna``."""
    y = x[x[coluna].notna()].sort_values([coluna, *CHAVE], kind="stable")
    acum = y["v2"].cumsum().to_numpy() / y["v2"].sum()
    y = y.assign(g=np.minimum((acum * n - 1e-12).astype(int), n - 1) + 1)
    out = []
    for g, b in y.groupby("g"):
        f2 = 100 * b["fl"].sum() / b["v2"].sum()
        f1 = 100 * b["fl1"].sum() / b["v1"].sum()
        ufs = b.groupby("uf")["v2"].sum().sort_values(ascending=False)
        out.append(
            {
                "vintil": int(g),
                "secoes": len(b),
                "votos_2t": int(b["v2"].sum()),
                "de": hhmm(float(b[coluna].min())),
                "ate": hhmm(float(b[coluna].max())),
                "fatia_f_2t": r2(f2),
                "fatia_f_1t": r2(f1),
                "dif_pp": r2(f2 - f1),
                "ufs_principais": [str(u) for u in ufs.index[:3]],
                "pct_votos_nordeste": r2(
                    100 * b.loc[b["regiao"] == "Nordeste", "v2"].sum() / b["v2"].sum()
                ),
            }
        )
    return out


def acumulado(x: pd.DataFrame, coluna: str) -> dict:
    """Soma na ordem de ``coluna``: janela em que Flávio fica à frente."""
    y = x[x[coluna].notna()].sort_values([coluna, *CHAVE], kind="stable")
    f = y["fl"].cumsum().to_numpy()
    v = y["v2"].cumsum().to_numpy()
    s = 100 * f / v
    t = y[coluna].to_numpy()
    validos = v >= 100_000  # sem o ruído das primeiras seções
    frente = validos & (s > 50)
    i_max = int(np.argmax(np.where(validos, s, -1)))
    j = np.flatnonzero(frente)
    return {
        "minimo_votos": 100_000,
        "frente_de": hhmm(float(t[j[0]])) if len(j) else None,
        "frente_ate": hhmm(float(t[j[-1]])) if len(j) else None,
        "maximo_pct": r2(float(s[i_max])),
        "maximo_em": hhmm(float(t[i_max])),
        "final_pct": r2(float(s[-1])),
    }


def resumo_vintis(v: list[dict]) -> dict:
    f2 = np.array([a["fatia_f_2t"] for a in v])
    d = np.array([a["dif_pp"] for a in v])
    k = np.arange(1, len(v) + 1)
    return {
        "fatia_2t_amplitude_pp": r2(float(f2.max() - f2.min())),
        "dif_amplitude_pp": r2(float(d.max() - d.min())),
        "fatia_2t_desvio_pp": r2(float(f2.std())),
        "dif_desvio_pp": r2(float(d.std())),
        "corr_ordem_fatia_2t": r2(float(np.corrcoef(k, f2)[0, 1]), 3),
        "corr_ordem_dif": r2(float(np.corrcoef(k, d)[0, 1]), 3),
        "primeiro": v[0],
        "ultimo": v[-1],
    }


def ordem(x: pd.DataFrame) -> dict:
    rec = vintis(x, "rec_min")
    enc = vintis(x, "enc_min")
    return {
        "recebimento": {
            "vintis": rec,
            "resumo": resumo_vintis(rec),
            "acumulado": acumulado(x, "rec_min"),
            "antes_17h": int((x["rec_min"] < 0).sum()),
        },
        "encerramento": {
            "vintis": enc,
            "resumo": resumo_vintis(enc),
            "acumulado": acumulado(x, "enc_min"),
        },
    }


# ------------------------------------------------------------------ montagem


def analisar(
    sec: pd.DataFrame,
    m22: dict,
    fim2: pd.DataFrame,
    fim1: pd.DataFrame,
    reps: int = REPS,
) -> dict:
    x = preparar(sec, m22, fim2, fim1)
    return {
        "rotulo": ROTULO,
        "definicoes": {
            "quintil": "seções do Brasil (sem exterior) por fatia de Lula entre os dois finalistas no 1º turno, cinco grupos de mesmo eleitorado (aptos do 2T)",
            "abstencao": "100 − comparecimento/aptos da seção; 2022 é o 2º turno do município da seção (seções de 2022 não são pareadas), pesada pelos aptos de 2026",
            "fim_do_dia": "parcela dos cômputos do log entre 15h e 16h59 de Brasília (as duas últimas horas da votação regular); 1T só na amostra de uma seção em cinco",
            "fatia_f": "Flávio / (Flávio + Lula), soma dos votos do grupo",
            "salto": f"comparecimento 2T−1T da seção ao menos {SALTO_PP:g} pp acima da mediana do município",
            "fim": f"parcela 15h–17h da seção ao menos {FIM_DIA_PP:g} pp acima da mediana do município",
            "did": f"(fatia de Flávio 2T−1T nas marcadas) − (o mesmo nas vizinhas do município), municípios com {MIN_SECOES_MUN}+ seções; IC95 por reamostragem de municípios",
            "vintis": "20 grupos de mesmo número de votos nos dois finalistas, pela ordem de rec_min (recebimento do BU pelo TSE) ou enc_min (encerramento do BU), horário de Brasília",
        },
        "base": {"secoes": len(x), "aptos": int(x["aptos"].sum())},
        "transporte": transporte(x, reps=reps),
        "bahia": bahia(x, m22),
        "ordem": ordem(x),
    }


def fmt(v, casas: int = 2, sinal: bool = False) -> str:
    if v is None:
        return "s/d"
    s = f"{v:+.{casas}f}" if sinal else f"{v:.{casas}f}"
    return s.replace("-", "−").replace(".", ",")


def _linhas(itens: Iterable[str]) -> str:
    return "\n".join(itens) + "\n"


def markdown(d: dict) -> str:
    T = d["transporte"]
    L = [
        "# Transporte em massa e ordem de chegada (2º turno de 2026)",
        "",
        f"Rótulo: {d['rotulo']}. Base: {d['base']['secoes']:_} seções pareadas com o 1º turno, sem exterior.".replace(
            "_", "."
        ),
        "",
        "## Quintis de Lula no 1º turno",
        "",
        "| Quintil | Lula 1T | Abst. 1T | Abst. 2T | 2T−1T | 2T−2022 (mun.) | 15h–17h 2T | 15h–17h 1T (amostra) | 2T−1T fim do dia | Flávio 2T−1T | DiD salto | DiD fim do dia |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for q in T["quintis"]:
        ds, df_ = q["did"]["salto"], q["did"]["fim"]
        L.append(
            f"| Q{q['quintil']} | {fmt(q['lula1_min'], 1)}–{fmt(q['lula1_max'], 1)} | {fmt(q['abst_1t'])} | {fmt(q['abst_2t'])} | "
            f"{fmt(q['delta_abst_1t_pp'], sinal=True)} | {fmt(q['delta_abst_2022_pp'], sinal=True)} | {fmt(q['fim_dia_2t_pct'])} | "
            f"{fmt(q['fim_dia_1t_pct'])} | {fmt(q['delta_fim_dia_pp'], sinal=True)} | {fmt(q['swing_f_pp'], sinal=True)} | "
            f"{fmt(ds.get('did_pp'), sinal=True)} ({fmt((ds.get('ic95') or [None])[0], sinal=True)} a {fmt((ds.get('ic95') or [None, None])[1], sinal=True)}) | "
            f"{fmt(df_.get('did_pp'), sinal=True)} |"
        )
    L += ["", "Q5 menos Q1: " + json.dumps(T["q5_menos_q1"], ensure_ascii=False), ""]
    L += [
        "## Regiões",
        "",
        "| Região | Abst. 2T−1T | 2T−2022 | 15h–17h 2T | 15h–17h 1T | Flávio 2T−1T | DiD salto |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in T["regioes"]:
        L.append(
            f"| {r['regiao']} | {fmt(r['delta_abst_1t_pp'], sinal=True)} | {fmt(r['delta_abst_2022_pp'], sinal=True)} | "
            f"{fmt(r['fim_dia_2t_pct'])} | {fmt(r['fim_dia_1t_pct'])} | {fmt(r['swing_f_pp'], sinal=True)} | "
            f"{fmt(r['did']['salto'].get('did_pp'), sinal=True)} |"
        )
    L += ["", "## Bahia e Salvador", ""]
    for nome, b in d["bahia"].items():
        L.append(
            f"- {nome}: abstenção 1T {fmt(b['abst_1t'])}, 2T {fmt(b['abst_2t'])}, 2022 {fmt(b['abst_2022_mun'])}; "
            f"Flávio 1T {fmt(b['fatia_f_1t'])}, 2T {fmt(b['fatia_f_2t'])} ({fmt(b['swing_f_pp'], sinal=True)}); "
            f"15h–17h 2T {fmt(b['fim_dia_2t_pct'])}, 1T {fmt(b['fim_dia_1t_pct'])}; DiD salto {fmt(b['did_salto'].get('did_pp'), sinal=True)}"
            + (
                f"; Bolsonaro 2022 {fmt(b['bolsonaro_2022_h2h'])}"
                if "bolsonaro_2022_h2h" in b
                else ""
            )
        )
    for nome, chave in (
        ("recebimento do BU", "recebimento"),
        ("encerramento do BU", "encerramento"),
    ):
        od = d["ordem"][chave]
        L += [
            "",
            f"## Ordem de chegada por {nome}",
            "",
            "| Vintil | De | Até | Flávio 2T | Flávio 1T | Diferença | UFs |",
            "|---|---|---|---|---|---|---|",
        ]
        for v in od["vintis"]:
            L.append(
                f"| {v['vintil']} | {v['de']} | {v['ate']} | {fmt(v['fatia_f_2t'])} | {fmt(v['fatia_f_1t'])} | "
                f"{fmt(v['dif_pp'], sinal=True)} | {', '.join(v['ufs_principais'])} |"
            )
        L += [
            "",
            "Resumo: "
            + json.dumps(
                {
                    k: v
                    for k, v in od["resumo"].items()
                    if k not in ("primeiro", "ultimo")
                },
                ensure_ascii=False,
            ),
        ]
        L += ["Acumulado: " + json.dumps(od["acumulado"], ensure_ascii=False)]
    return _linhas(L)
