"""Cadência horária dos cômputos pelo relógio da urna, convertida para Brasília.

O log guarda a hora local da urna. A votação abre às 08:00 de Brasília no país
inteiro, então o deslocamento de cada município é ``8 − hora modal do primeiro
cômputo`` das suas seções (0 em quase todo o país, 1 nas UFs a UTC−4, 2 no Acre e
no oeste do Amazonas). Exterior fica fora: vota na hora da cidade do consulado.

O 1º turno vem de uma amostra relida com o leitor atual (``logs_amostra_1t``):
as métricas publicadas do 1º turno não guardavam a cadência.
"""

from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pandas as pd

from .logs_base import CHAVE, REGIAO

HORAS = list(range(8, 20))


def deslocamentos(t2: pd.DataFrame) -> pd.DataFrame:
    x = t2[(t2["uf"] != "ZZ") & t2["primeiro_s"].notna()].copy()
    x["h0"] = (x["primeiro_s"] // 3600).astype(int)
    moda = x.groupby(["uf", "mun"])["h0"].agg(lambda s: s.mode().iloc[0])
    return (8 - moda).rename("off").reset_index()


def _horas(cph: pd.Series, off: pd.Series) -> Counter:
    c: Counter = Counter()
    for txt, o in zip(cph, off, strict=True):
        for h, n in json.loads(txt).items():
            c[int(h) + int(o)] += n
    return c


def perfil(cph: pd.Series, off: pd.Series) -> dict:
    """Parcela dos cômputos por hora de Brasília (8 = 08:00–08:59)."""
    c = _horas(cph, off)
    tot = sum(c.values())
    if not tot:
        return {"computados": 0, "pct": {}}
    pct = {str(h): round(100 * c.get(h, 0) / tot, 3) for h in HORAS}
    tarde = sum(n for h, n in c.items() if h >= 19)
    pct["19"] = round(100 * tarde / tot, 4)
    return {
        "computados": int(tot),
        "pct": pct,
        "pct_ultima_hora": round(100 * c.get(16, 0) / tot, 3),
        "pct_17_19": round(100 * (c.get(17, 0) + c.get(18, 0)) / tot, 4),
        "pct_depois_19": round(100 * tarde / tot, 5),
        "computados_17_19": int(c.get(17, 0) + c.get(18, 0)),
        "computados_depois_19": int(tarde),
        "pct_primeira_hora": round(100 * c.get(8, 0) / tot, 3),
    }


def _ultimo(df: pd.DataFrame) -> pd.Series:
    return df["ultimo_s"] / 3600 + df["off"]


def analisar(t2: pd.DataFrame, a1: pd.DataFrame, bu: pd.DataFrame, s2) -> dict:
    off = deslocamentos(t2)
    x = t2[t2["uf"] != "ZZ"].merge(off, on=["uf", "mun"], how="inner")
    ok = x[x["cph_ok"]]
    out: dict = {
        "regra_fuso": "hora local do log + (8 − hora modal do primeiro cômputo no município); exterior fora",
        "municipios_por_deslocamento": {
            str(k): int(v) for k, v in off["off"].value_counts().sort_index().items()
        },
        "secoes_2t": len(ok),
        "brasil_2t": perfil(ok["cph"], ok["off"]),
    }
    a = a1[(a1["uf"] != "ZZ")].copy()
    a = a[a["cph_ok"].astype(bool)].merge(off, on=["uf", "mun"], how="inner")
    mesmas = ok.merge(a[CHAVE], on=CHAVE)
    out["amostra_1t"] = {
        "secoes": len(a),
        "regra": "uma seção em cada cinco, sorteio determinístico pelo SHA-256 da chave UF-município-zona-seção",
        "brasil_1t": perfil(a["cph"], a["off"]),
        "brasil_2t_mesmas": perfil(mesmas["cph"], mesmas["off"]),
    }
    regioes = {}
    for reg in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]:
        r2 = ok[ok["uf"].map(REGIAO) == reg]
        r1 = a[a["uf"].map(REGIAO) == reg]
        regioes[reg] = {
            "secoes_2t": len(r2),
            "secoes_1t_amostra": len(r1),
            "2t": perfil(r2["cph"], r2["off"]),
            "1t": perfil(r1["cph"], r1["off"]),
        }
    out["regioes"] = regioes
    # último voto pelo relógio do log
    x["ult_brt"] = _ultimo(x)
    a["ult_brt"] = _ultimo(a)
    rel = x[x["relogio_ok"]]
    out["ultimo_voto"] = {
        "secoes": len(rel),
        "depois_17": int((rel["ult_brt"] >= 17).sum()),
        "depois_1715": int((rel["ult_brt"] >= 17.25).sum()),
        "depois_1730": int((rel["ult_brt"] >= 17.5).sum()),
        "depois_18": int((rel["ult_brt"] >= 18).sum()),
        "depois_19": int((rel["ult_brt"] >= 19).sum()),
        "pct_depois_17": round(100 * (rel["ult_brt"] >= 17).mean(), 3),
        "pct_depois_1730": round(100 * (rel["ult_brt"] >= 17.5).mean(), 3),
        "pct_depois_19": round(100 * (rel["ult_brt"] >= 19).mean(), 4),
        "amostra_1t": {
            "pct_depois_17": round(100 * (a["ult_brt"] >= 17).mean(), 2),
            "pct_depois_1730": round(100 * (a["ult_brt"] >= 17.5).mean(), 2),
            "pct_depois_18": round(100 * (a["ult_brt"] >= 18).mean(), 2),
            "pct_depois_19": round(100 * (a["ult_brt"] >= 19).mean(), 2),
        },
    }
    depois19 = rel[rel["ult_brt"] >= 19].merge(bu, on=CHAVE, how="left")
    out["lista_depois_19"] = [
        {
            "uf": r.uf,
            "mun": r.mun,
            "zona": int(r.zona),
            "secao": int(r.secao),
            "ultimo_voto_brt": _hhmm(r.ult_brt),
            "computados": int(r.computados or 0),
            "votos_depois_19": int(
                sum(
                    n for h, n in json.loads(r.cph).items() if int(h) + int(r.off) >= 19
                )
            ),
            "fatia_f": _f(r.fatia_f),
            "fatia_f1": _f(r.fatia_f1),
        }
        for r in depois19.sort_values("ult_brt").itertuples()
    ]
    # BUs encerrados depois das 19h (secoes.json) contra o último voto no log
    j = x.merge(bu[[*CHAVE, "apos_19h", "enc_min", "fatia_f", "fatia_f1"]], on=CHAVE)
    j = j[j["relogio_ok"]]
    t19 = j[j["apos_19h"].astype(bool)]
    out["bu_apos_19h"] = {
        "secoes": len(t19),
        "ultimo_voto_ate_1715": int((t19["ult_brt"] < 17.25).sum()),
        "ultimo_voto_1715_1900": int(
            ((t19["ult_brt"] >= 17.25) & (t19["ult_brt"] < 19)).sum()
        ),
        "ultimo_voto_depois_19": int((t19["ult_brt"] >= 19).sum()),
        "mediana_ultimo_voto": (
            _hhmm(float(t19["ult_brt"].median())) if len(t19) else None
        ),
        "nota": "encerramento do BU depois das 19:00 de Brasília contra a hora do último cômputo no log da mesma seção",
    }
    out["por_sinal"] = por_sinal(ok, bu, s2)
    return out


def por_sinal(ok: pd.DataFrame, bu: pd.DataFrame, s2: pd.DataFrame) -> list[dict]:
    """A forma do dia muda nas seções com sinal? Parcela da 1ª hora, da última e depois das 17h."""
    j = ok.merge(
        bu[[*CHAVE, "sinal_sem_bio", "sinal_ano_nasc", "escore"]], on=CHAVE, how="left"
    ).merge(s2[[*CHAVE, "sinais", "atencao"]], on=CHAVE, how="left")
    sinais = j["sinais"].fillna("")
    grupos = {
        "todas": np.ones(len(j), bool),
        "sem nenhum diagnóstico no log": sinais.eq("").to_numpy(),
        "sistema religado durante a votação": (j["reinicios_sist"] > 0).to_numpy(),
        "bateria durante a votação": (j["bateria_votacao"] > 0).to_numpy(),
        "liberação sem biometria alta (BU)": j["sinal_sem_bio"]
        .fillna(False)
        .astype(bool)
        .to_numpy(),
        "habilitação por ano de nascimento alta (BU)": j["sinal_ano_nasc"]
        .fillna(False)
        .astype(bool)
        .to_numpy(),
        "atenção 2 ou 3 nos logs": (j["atencao"].fillna(0) >= 2).to_numpy(),
        "escore do BU 2 ou mais": (j["escore"].fillna(0) >= 2).to_numpy(),
    }
    out = []
    for nome, m in grupos.items():
        g = j[m]
        p = perfil(g["cph"], g["off"])
        out.append(
            {
                "grupo": nome,
                "secoes": len(g),
                "pct_primeira_hora": p.get("pct_primeira_hora"),
                "pct_ultima_hora": p.get("pct_ultima_hora"),
                "pct_17_19": p.get("pct_17_19"),
                "pct": p.get("pct"),
            }
        )
    return out


def _f(v) -> float | None:
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)


def _hhmm(h: float) -> str:
    m = round(h * 60)
    return f"{m // 60:02d}:{m % 60:02d}"
