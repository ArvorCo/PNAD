"""Relação de cada sinal com o voto, sempre dentro do mesmo município.

Duas comparações por sinal:

- **contra as vizinhas**: fatia de Flávio entre os dois (F/(F+L)) e parcelas de
  Flávio e de Lula no comparecimento, nas seções com o sinal contra as demais do
  MESMO município, média dos municípios ponderada pelos votos das seções com
  sinal (nunca contra o país);
- **contra o 1T**: variação da fatia de Flávio entre os dois na própria seção
  (2T menos 1T) nas seções com sinal, menos a mesma variação nas vizinhas do
  município (diferença em diferenças).

Diferenças só com n ≥ 20 seções com sinal; o n vai sempre ao lado. O erro-padrão
é aproximado, entre municípios, e não incorpora o desenho da amostra.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

N_MIN = 20

GRUPOS: dict[str, str] = {
    "delta": "comparecimento ≥ +5 pp contra a própria seção no 1T",
    "delta_relativo": "comparecimento ≥ 5 pp acima da alta mediana do município ou UF",
    "delta_forte": "comparecimento ≥ +10 pp contra a própria seção no 1T",
    "sinal_sem_bio": "sem biometria cadastrada ≥ 10% e ≥ 2x a mediana municipal do 1T",
    "sinal_ano_nasc": "habilitados por ano de nascimento ≥ 10% e ≥ 2x a mediana municipal",
    "biometria_baixa": "sem biometria ou ano de nascimento acima da regra",
    "sinal_salto_bio": "sem biometria reconhecida ≥ 10% e +5 pp contra a própria seção",
    "pianista": "comparecimento ≥ +5 pp e salto da parcela sem biometria reconhecida",
    "tardia": "encerrou depois das 19:00 ou 30 min depois do 1T (prorrogação)",
    "apos_19h": "encerrou depois das 19:00 de Brasília",
    "contingencia": "urna de contingência ou com mais de uma carga",
    "papel": "BU do sistema de apuração",
    "escore2": "escore 2 ou mais",
}


def _r(v: float | None) -> float | None:
    return None if v is None or not np.isfinite(v) else float(np.round(v, 2))


def _media_pond(d: np.ndarray, w: np.ndarray) -> tuple[float | None, float | None]:
    ok = np.isfinite(d) & (w > 0)
    if not ok.any():
        return None, None
    d, w = d[ok], w[ok]
    m = float(np.sum(w * d) / np.sum(w))
    ep = float(np.sqrt(np.sum(w**2 * (d - m) ** 2)) / np.sum(w)) if len(d) > 1 else None
    return m, ep


def comparar(x: pd.DataFrame, mask: pd.Series) -> dict[str, Any]:
    """Seções com sinal contra as demais do mesmo município, e contra o 1T."""
    v = x[(x["fl"] + x["lu"]) > 0].copy()
    v["s"] = mask.reindex(v.index).fillna(False).astype(bool)
    n_sinal_total = int(v["s"].sum())
    linhas = []
    for _, g in v.groupby(["uf", "mun"], sort=False):
        s, c = g[g["s"]], g[~g["s"]]
        if s.empty or c.empty:
            continue
        vs, vc = s["fl"].sum() + s["lu"].sum(), c["fl"].sum() + c["lu"].sum()
        d_fatia = 100 * (s["fl"].sum() / vs - c["fl"].sum() / vc)
        d_f = 100 * (s["fl"].sum() / s["comp"].sum() - c["fl"].sum() / c["comp"].sum())
        d_l = 100 * (s["lu"].sum() / s["comp"].sum() - c["lu"].sum() / c["comp"].sum())
        s1 = s[s["delta_fatia_pp"].notna()]
        c1 = c[c["delta_fatia_pp"].notna()]
        did = np.nan
        n1 = 0
        if not s1.empty and not c1.empty:
            ws, wc = s1["fl"] + s1["lu"], c1["fl"] + c1["lu"]
            did = np.average(s1["delta_fatia_pp"], weights=ws) - np.average(
                c1["delta_fatia_pp"], weights=wc
            )
            n1 = len(s1)
        linhas.append((len(s), len(c), vs, d_fatia, d_f, d_l, did, n1))
    t = np.array(linhas, dtype=float).reshape(-1, 8)
    n_s = int(t[:, 0].sum())
    n_c = int(t[:, 1].sum())
    w = t[:, 2]
    out: dict[str, Any] = {
        "n_sinal_total": n_sinal_total,
        "n_sinal_comparavel": n_s,
        "n_vizinhas": n_c,
        "n_municipios": len(t),
    }
    s_all = v[v["s"] & v["delta_fatia_pp"].notna()]
    out["n_vs_1t"] = len(s_all)
    if n_s >= N_MIN:
        for i, nome in (
            (3, "fatia_flavio"),
            (4, "flavio_no_comp"),
            (5, "lula_no_comp"),
        ):
            m, ep = _media_pond(t[:, i], w)
            out[f"dif_{nome}_vs_vizinhas_pp"] = _r(m)
            out[f"ep_{nome}_vs_vizinhas_pp"] = _r(ep)
    n_did = int(t[:, 7].sum())
    out["n_did"] = n_did
    if n_did >= N_MIN:
        m, ep = _media_pond(t[:, 6], w)
        out["did_fatia_flavio_pp"] = _r(m)
        out["ep_did_fatia_flavio_pp"] = _r(ep)
    if len(s_all) >= N_MIN:
        out["delta_fatia_flavio_vs_1t_pp"] = _r(
            np.average(s_all["delta_fatia_pp"], weights=s_all["fl"] + s_all["lu"])
        )
        out["votos_flavio_2t"] = int(s_all["fl"].sum())
        out["votos_lula_2t"] = int(s_all["lu"].sum())
        out["votos_flavio_1t"] = int(s_all["fl1"].sum())
        out["votos_lula_1t"] = int(s_all["lu1"].sum())
    return out


def tabela_2x2x2(x: pd.DataFrame) -> list[dict[str, Any]]:
    """Comparecimento alto × biometria baixa × fatia de Flávio subiu contra o 1T."""
    v = x[x["delta_fatia_pp"].notna() & x["delta_pp"].notna()]
    out = []
    for alto in (True, False):
        for baixa in (True, False):
            g = v[(v["delta"] == alto) & (v["biometria_baixa"] == baixa)]
            sobe = g["delta_fatia_pp"] > 0
            cel: dict[str, Any] = {
                "comparecimento_alto": alto,
                "biometria_baixa": baixa,
                "n": len(g),
                "n_flavio_sobe": int(sobe.sum()),
                "n_flavio_nao_sobe": int((~sobe).sum()),
            }
            if len(g) >= N_MIN:
                w = g["fl"] + g["lu"]
                cel["pct_flavio_sobe"] = _r(100 * sobe.mean())
                cel["delta_fatia_flavio_pp"] = _r(
                    np.average(g["delta_fatia_pp"], weights=w)
                )
                cel["fatia_flavio_2t"] = _r(100 * g["fl"].sum() / w.sum())
            out.append(cel)
    return out


def votos_absolutos(x: pd.DataFrame) -> dict[str, Any]:
    """Quem ganhou votos absolutos contra o 1T na mesma seção."""
    v = x[x["fl1"].notna() & x["lu1"].notna()]
    df, dl = v["fl"] - v["fl1"], v["lu"] - v["lu1"]
    n = len(v)

    def p(m: pd.Series) -> dict[str, Any]:
        return {"n": int(m.sum()), "pct": _r(100 * m.mean()) if n else None}

    forte = v[v["delta_forte"]]
    dff, dlf = forte["fl"] - forte["fl1"], forte["lu"] - forte["lu1"]
    out: dict[str, Any] = {
        "n": n,
        "flavio_ganhou": p(df > 0),
        "lula_ganhou": p(dl > 0),
        "flavio_ganhou_lula_perdeu": p((df > 0) & (dl < 0)),
        "lula_ganhou_flavio_perdeu": p((dl > 0) & (df < 0)),
        "ganho_flavio_maior": p(df > dl),
        "ganho_medio_flavio": _r(float(df.mean())) if n else None,
        "ganho_medio_lula": _r(float(dl.mean())) if n else None,
        "comparecimento_10pp": {
            "n": len(forte),
            "lula_ganhou_mais": int((dlf > dff).sum()),
            "flavio_ganhou_mais": int((dff > dlf).sum()),
            "empate": int((dff == dlf).sum()),
        },
    }
    if len(forte) >= N_MIN:
        out["comparecimento_10pp"]["pct_lula_ganhou_mais"] = _r(
            100 * float((dlf > dff).mean())
        )
        out["comparecimento_10pp"]["pct_lula_ganhou_mais_demais"] = _r(
            100
            * float(
                ((dl > df) & ~v["delta_forte"]).sum()
                / max(1, (~v["delta_forte"]).sum())
            )
        )
        out["comparecimento_10pp"]["ganho_medio_flavio"] = _r(float(dff.mean()))
        out["comparecimento_10pp"]["ganho_medio_lula"] = _r(float(dlf.mean()))
    return out


def relacao(x: pd.DataFrame) -> dict[str, Any]:
    x = x.assign(escore2=x["escore"] >= 2)
    sinais = []
    for col, desc in GRUPOS.items():
        sinais.append({"sinal": col, "descricao": desc, **comparar(x, x[col])})
    por_uf_tardia = []
    for uf, g in x.groupby("uf", sort=True):
        c = comparar(g, g["tardia"])
        if c["n_sinal_total"] > 0:
            por_uf_tardia.append({"uf": uf, **c})
    return {
        "sinais": sinais,
        "prorrogacao_por_uf": por_uf_tardia,
        "tabela_2x2x2": tabela_2x2x2(x),
        "votos_absolutos": votos_absolutos(x),
    }
