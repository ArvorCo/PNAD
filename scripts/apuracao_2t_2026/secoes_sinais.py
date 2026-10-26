"""Sinais por seção do 2º turno contra a própria seção no 1º turno.

Regras declaradas em ``REGRAS`` (as quatro primeiras repetem
``apuracao/src/secoes2t/comparecimento-tipos.ts``; ``ano_nasc`` é acréscimo
desta análise e fica fora do escore da API):

- ``delta``: comparecimento/aptos no 2T menos o da mesma seção no 1T ≥ +5 pp;
- ``sem_bio``: sem biometria cadastrada ≥ 10% do comparecimento e ≥ 2× a
  mediana do município no 1T;
- ``ano_nasc``: habilitados por ano de nascimento (biometria cadastrada que não
  foi reconhecida) ≥ 10% do comparecimento e ≥ 2× a mediana do município no 1T;
- ``tardia``: encerramento (último voto) depois das 19:00 de Brasília, ou 30 min
  ou mais depois do encerramento da própria seção no 1T;
- ``papel``: BU do sistema de apuração (``tipo_arquivo`` ≥ 3);
- ``salto_bio``: parcela sem biometria reconhecida (sem biometria cadastrada mais
  ano de nascimento) ≥ 10% e ao menos 5 pp acima da mesma seção no 1T. É o sinal
  mais próximo da hipótese do mesário que libera eleitor ausente, porque compara
  a seção com ela mesma e não com o município.

``escore_api`` (0 a 4) repete a rota; ``escore`` (0 a 6) soma os seis sinais.

Contingência (``tipo_urna`` 3, 4 ou 6, ou mais de uma carga) e "depois das
17:00" são descrição. Sinal pede explicação, não prova irregularidade.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .secoes_ref import pct

ROTULO = (
    "Sinal pede explicação, não prova irregularidade; a extensão até 19h eleva o "
    "comparecimento legitimamente."
)

REGRAS: dict[str, Any] = {
    "delta_pp_min": 5,
    "delta_forte_pp_min": 10,
    "sem_bio_min_pct": 10,
    "sem_bio_fator": 2,
    "ano_nasc_min_pct": 10,
    "ano_nasc_fator": 2,
    "apos_hhmm": "19:00",
    "tardia_min_vs_1t": 30,
    "papel_tipo_min": 3,
    "salto_bio_min_pct": 10,
    "salto_bio_pp_min": 5,
    "contingencia_tipos_urna": [3, 4, 6],
    "secao_pequena_aptos": 100,
    "aptos_mudaram_pct": 10,
    "n_min_delta": 20,
    "delta_relativo": (
        "delta_pp menos a mediana do município (n ≥ 20) ou da UF ≥ 5 pp; descrição, "
        "fora do escore"
    ),
    "magnitude": (
        "max(0, delta_pp)/5 + max(0, sem_bio_pct - 2 x mediana municipal)/10 + "
        "max(0, ano_nasc_pct - 2 x mediana municipal)/10 + atraso do encerramento "
        "contra o 1T (ou depois das 19:00) em minutos/30 + 1 se BU do sistema de "
        "apuração + max(0, salto da parcela sem biometria reconhecida)/5"
    ),
}

SINAIS = ["delta", "sem_bio", "ano_nasc", "salto_bio", "tardia", "papel"]
SINAIS_API = ["delta", "sem_bio", "tardia", "papel"]


def r2(x: Any) -> Any:
    return np.round(np.asarray(x, dtype=float), 2)


def hhmm(minutos: float | None) -> str | None:
    """Minutos depois das 17:00 de Brasília → "hh:mm" (passa da meia-noite com +1)."""
    if minutos is None or not np.isfinite(minutos):
        return None
    total = int(17 * 60 + np.floor(minutos))
    dias, resto = divmod(total, 1440)
    s = f"{resto // 60:02d}:{resto % 60:02d}"
    return f"{s} (+{dias})" if dias > 0 else s


def montar(
    df: pd.DataFrame,
    ref: pd.DataFrame,
    mun_ref: dict[str, Any],
    med_mun: pd.DataFrame,
    med_zona: pd.DataFrame,
) -> pd.DataFrame:
    """Cruza o 2T com o 1T da mesma seção e calcula taxas e diferenças."""
    chave = ["uf", "mun", "zona", "secao"]
    x = df.merge(ref, on=chave, how="left")
    x = x.merge(med_mun, on=["uf", "mun"], how="left")
    x = x.merge(med_zona, on=["uf", "zona"], how="left")
    x["mun_p50_sem_bio_api"] = [
        (mun_ref.get(u.lower(), {}).get(m) or {}).get("sem_bio_p50")
        for u, m in zip(x["uf"], x["mun"], strict=True)
    ]
    x["mun_p50_sem_bio_api"] = x["mun_p50_sem_bio_api"].astype(float)
    x["tem_ref"] = x["aptos1"].notna()
    x["taxa2"] = r2(pct(x["comp"], x["aptos"]))
    x["taxa1"] = r2(pct(x["comp1"], x["aptos1"]))
    x["delta_pp"] = r2(x["taxa2"] - x["taxa1"])
    x["sem_bio_pct"] = r2(pct(x["sem_bio"], x["comp"]))
    x["sem_bio_pct1"] = r2(pct(x["sem_bio1"], x["comp1"]))
    x["ano_nasc_pct"] = r2(pct(x["ano_nasc"], x["comp"]))
    x["ano_nasc_pct1"] = r2(pct(x["ano_nasc1"], x["comp1"]))
    x["nao_bio_pct"] = r2(pct(x["sem_bio"] + x["ano_nasc"], x["comp"]))
    x["nao_bio_pct1"] = r2(pct(x["sem_bio1"] + x["ano_nasc1"], x["comp1"]))
    # régua do 1T convertida pelo fuso da UF: recebe a mesma correção municipal
    x["enc1_min"] = x["enc1_min"] + x["corr_fuso_min"]
    x["atraso_vs_1t_min"] = (x["enc_min"] - x["enc1_min"]).round(1)
    x["fatia_f"] = r2(pct(x["fl"], x["fl"] + x["lu"]))
    x["fatia_f1"] = r2(pct(x["fl1"], x["fl1"] + x["lu1"]))
    x["delta_fatia_pp"] = r2(x["fatia_f"] - x["fatia_f1"])
    x["aptos_var_pct"] = r2(pct(x["aptos"] - x["aptos1"], x["aptos1"]))
    return x


def sinais(x: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta os sinais, o escore e a magnitude (regras em ``REGRAS``)."""
    rg = REGRAS
    enc_hm = np.floor(x["enc_min"])
    x["apos_17h"] = enc_hm >= 1
    x["apos_19h"] = enc_hm >= 121
    x["delta"] = x["delta_pp"] >= rg["delta_pp_min"]
    x["delta_forte"] = x["delta_pp"] >= rg["delta_forte_pp_min"]
    # referência local da alta: mediana do município com n ≥ 20, senão da UF
    med_uf = x.groupby("uf")["delta_pp"].transform("median")
    gm = x.groupby(["uf", "mun"])["delta_pp"]
    med_mun = gm.transform("median").where(gm.transform("count") >= rg["n_min_delta"])
    x["delta_ref_local_pp"] = r2(med_mun.fillna(med_uf))
    x["delta_rel_pp"] = r2(x["delta_pp"] - x["delta_ref_local_pp"])
    x["delta_relativo"] = x["delta_rel_pp"] >= rg["delta_pp_min"]
    x["sem_bio_s"] = (x["sem_bio_pct"] >= rg["sem_bio_min_pct"]) & (
        x["sem_bio_pct"] >= rg["sem_bio_fator"] * x["mun_p50_sem_bio_api"]
    )
    x["ano_nasc_s"] = (x["ano_nasc_pct"] >= rg["ano_nasc_min_pct"]) & (
        x["ano_nasc_pct"] >= rg["ano_nasc_fator"] * x["mun_p50_ano_nasc_pct1"]
    )
    x["tardia"] = x["apos_19h"] | (x["atraso_vs_1t_min"] >= rg["tardia_min_vs_1t"])
    x["papel"] = x["tipo_arquivo"].fillna(0) >= rg["papel_tipo_min"]
    x["contingencia"] = x["tipo_urna"].isin(rg["contingencia_tipos_urna"]) | (
        x["n_cargas"].fillna(0) > 1
    )
    x["biometria_baixa"] = x["sem_bio_s"] | x["ano_nasc_s"]
    x["salto_bio_pp"] = r2(x["nao_bio_pct"] - x["nao_bio_pct1"])
    x["sinal_salto_bio"] = (x["nao_bio_pct"] >= rg["salto_bio_min_pct"]) & (
        x["salto_bio_pp"] >= rg["salto_bio_pp_min"]
    )
    x["pianista"] = x["delta"] & x["sinal_salto_bio"]
    x = x.rename(columns={"sem_bio_s": "sinal_sem_bio", "ano_nasc_s": "sinal_ano_nasc"})
    x["sinal_delta"] = x["delta"]
    x["sinal_tardia"] = x["tardia"]
    x["sinal_papel"] = x["papel"]
    x["escore_api"] = sum(x[f"sinal_{s}"].astype(int) for s in SINAIS_API)
    x["escore"] = sum(x[f"sinal_{s}"].astype(int) for s in SINAIS)
    atraso = np.fmax(
        x["atraso_vs_1t_min"].fillna(0), np.where(x["apos_19h"], x["enc_min"] - 120, 0)
    )
    x["magnitude"] = r2(
        np.fmax(x["delta_pp"].fillna(0), 0) / 5
        + np.fmax(x["sem_bio_pct"] - 2 * x["mun_p50_sem_bio_api"], 0).fillna(0) / 10
        + np.fmax(x["ano_nasc_pct"] - 2 * x["mun_p50_ano_nasc_pct1"], 0).fillna(0) / 10
        + np.fmax(atraso, 0) / 30
        + x["papel"].astype(int)
        + np.fmax(x["salto_bio_pp"].fillna(0), 0) / 5
    )
    return x


def conferencia_api(x: pd.DataFrame) -> dict[str, int]:
    """Contagens com o fuso só da UF, como a rota /api/2t/comparecimento."""
    enc = x["enc_min"] - x["corr_fuso_min"]
    enc1 = x["enc1_min"] - x["corr_fuso_min"]
    apos19 = np.floor(enc) >= 121
    tardia = apos19 | ((enc - enc1) >= REGRAS["tardia_min_vs_1t"])
    esc = (
        x["sinal_delta"].astype(int)
        + x["sinal_sem_bio"].astype(int)
        + tardia.astype(int)
        + x["sinal_papel"].astype(int)
    )
    return {
        "delta": int(x["sinal_delta"].sum()),
        "sem_bio": int(x["sinal_sem_bio"].sum()),
        "tarde": int((np.floor(enc) >= 1).sum()),
        "tardia": int(tardia.sum()),
        "apos_19h": int(apos19.sum()),
        "papel": int(x["sinal_papel"].sum()),
        "contingencia": int(x["contingencia"].sum()),
        "escore_2_mais": int((esc >= 2).sum()),
    }


def _q(v: pd.Series, q: float) -> float | None:
    v = v.dropna()
    return None if v.empty else float(np.round(v.quantile(q), 2))


def _media(v: pd.Series) -> float | None:
    v = v.dropna()
    return None if v.empty else float(np.round(v.mean(), 2))


def _parcela(mask: pd.Series, base: pd.Series | None = None) -> float | None:
    b = mask.notna() if base is None else base
    n = int(b.sum())
    return None if n == 0 else float(np.round(100 * mask[b].sum() / n, 2))


def _soma_pct(num: pd.Series, den: pd.Series) -> float | None:
    ok = num.notna() & den.notna()
    d = float(den[ok].sum())
    return None if d <= 0 else float(np.round(100 * num[ok].sum() / d, 2))


def persistencia(r: pd.DataFrame) -> dict[str, Any]:
    """Quantas seções com sinal de biometria já tinham o mesmo sinal no 1T."""
    sb1 = (r["sem_bio_pct1"] >= REGRAS["sem_bio_min_pct"]) & (
        r["sem_bio_pct1"] >= REGRAS["sem_bio_fator"] * r["mun_p50_sem_bio_api"]
    )
    an1 = (r["ano_nasc_pct1"] >= REGRAS["ano_nasc_min_pct"]) & (
        r["ano_nasc_pct1"] >= REGRAS["ano_nasc_fator"] * r["mun_p50_ano_nasc_pct1"]
    )
    s, a = r["sinal_sem_bio"], r["sinal_ano_nasc"]
    return {
        "sem_bio_n": int(s.sum()),
        "sem_bio_ja_no_1t": int((s & sb1).sum()),
        "sem_bio_dif_p50_pp": _q((r["sem_bio_pct"] - r["sem_bio_pct1"])[s], 0.5),
        "ano_nasc_n": int(a.sum()),
        "ano_nasc_ja_no_1t": int((a & an1).sum()),
        "ano_nasc_dif_p50_pp": _q((r["ano_nasc_pct"] - r["ano_nasc_pct1"])[a], 0.5),
    }


def resumo_grupo(g: pd.DataFrame) -> dict[str, Any]:
    """Distribuições e contagens de um grupo de seções (UF, município ou país)."""
    r = g[g["tem_ref"]]
    hora = g["enc_min"].notna()
    hora1 = r["enc_min"].notna() & r["enc1_min"].notna()
    out: dict[str, Any] = {
        "n": len(g),
        "n_ref_1t": len(r),
        "delta_comp": {
            "n": int(r["delta_pp"].notna().sum()),
            "p10": _q(r["delta_pp"], 0.1),
            "p50": _q(r["delta_pp"], 0.5),
            "p90": _q(r["delta_pp"], 0.9),
            "media": _media(r["delta_pp"]),
            "pct_5_mais": _parcela(r["delta_pp"] >= 5, r["delta_pp"].notna()),
            "pct_10_mais": _parcela(r["delta_pp"] >= 10, r["delta_pp"].notna()),
            "pct_menos_5": _parcela(r["delta_pp"] <= -5, r["delta_pp"].notna()),
            "n_relativo_5_mais": int(r["delta_relativo"].sum()),
            "comp_2t_pct": _soma_pct(r["comp"], r["aptos"]),
            "comp_1t_pct": _soma_pct(r["comp1"], r["aptos1"]),
        },
        "sem_biometria": {
            "pct_2t": _soma_pct(r["sem_bio"], r["comp"]),
            "pct_1t_mesmas": _soma_pct(r["sem_bio1"], r["comp1"]),
            "p50_secao_2t": _q(r["sem_bio_pct"], 0.5),
            "p50_secao_1t": _q(r["sem_bio_pct1"], 0.5),
            "p50_municipios_1t": _q(r["mun_p50_sem_bio_api"], 0.5),
            "n_sinal": int(r["sinal_sem_bio"].sum()),
        },
        "ano_nascimento": {
            "pct_2t": _soma_pct(r["ano_nasc"], r["comp"]),
            "pct_1t_mesmas": _soma_pct(r["ano_nasc1"], r["comp1"]),
            "p50_secao_2t": _q(r["ano_nasc_pct"], 0.5),
            "p50_secao_1t": _q(r["ano_nasc_pct1"], 0.5),
            "p50_municipios_1t": _q(r["mun_p50_ano_nasc_pct1"], 0.5),
            "n_sinal": int(r["sinal_ano_nasc"].sum()),
        },
        "encerramento": {
            "n": int(hora.sum()),
            "p50_2t": hhmm(_q(g.loc[hora, "enc_min"], 0.5)),
            "p90_2t": hhmm(_q(g.loc[hora, "enc_min"], 0.9)),
            "p99_2t": hhmm(_q(g.loc[hora, "enc_min"], 0.99)),
            "n_mesmas_1t": int(hora1.sum()),
            "p50_1t_mesmas": hhmm(_q(r.loc[hora1, "enc1_min"], 0.5)),
            "p90_1t_mesmas": hhmm(_q(r.loc[hora1, "enc1_min"], 0.9)),
            "pct_apos_1700_2t": _parcela(np.floor(g.loc[hora, "enc_min"]) >= 1),
            "pct_apos_1800_2t": _parcela(np.floor(g.loc[hora, "enc_min"]) >= 61),
            "pct_apos_1900_2t": _parcela(np.floor(g.loc[hora, "enc_min"]) >= 121),
            "pct_apos_1700_1t_mesmas": _parcela(
                np.floor(r.loc[hora1, "enc1_min"]) >= 1
            ),
            "pct_apos_1800_1t_mesmas": _parcela(
                np.floor(r.loc[hora1, "enc1_min"]) >= 61
            ),
            "pct_apos_1900_1t_mesmas": _parcela(
                np.floor(r.loc[hora1, "enc1_min"]) >= 121
            ),
            "n_tardias": int(g["tardia"].sum()),
            "n_apos_19h": int(g["apos_19h"].sum()),
        },
        "urna": {
            "contingencia": int(g["contingencia"].sum()),
            "tipo_urna": {
                str(int(k)): int(v)
                for k, v in g["tipo_urna"].dropna().value_counts().sort_index().items()
            },
            "mais_de_uma_carga": int((g["n_cargas"].fillna(0) > 1).sum()),
            "sistema_apuracao": int(g["papel"].sum()),
        },
        "salto_biometria": {
            "n_sinal": int(r["sinal_salto_bio"].sum()),
            "p50_salto_pp": _q(r["salto_bio_pp"], 0.5),
            "p90_salto_pp": _q(r["salto_bio_pp"], 0.9),
            "n_comparecimento_e_salto": int(r["pianista"].sum()),
        },
        "persistencia": persistencia(r),
        "sinais": {s: int(g[f"sinal_{s}"].sum()) for s in SINAIS},
        "escore": {
            str(k): int(v) for k, v in g["escore"].value_counts().sort_index().items()
        },
        "escore_2_mais": int((g["escore"] >= 2).sum()),
    }
    return out


def agregados(x: pd.DataFrame, nomes: dict[tuple[str, str], str]) -> dict[str, Any]:
    por_uf = [{"uf": uf, **resumo_grupo(g)} for uf, g in x.groupby("uf", sort=True)]
    por_mun = []
    for (uf, mun), g in x.groupby(["uf", "mun"], sort=True):
        r = resumo_grupo(g)
        por_mun.append(
            {
                "uf": uf,
                "mun": mun,
                "nome": nomes.get((uf, mun)),
                "n": r["n"],
                "n_ref_1t": r["n_ref_1t"],
                "delta_comp_p50": r["delta_comp"]["p50"],
                "delta_comp_media": r["delta_comp"]["media"],
                "pct_delta_5_mais": r["delta_comp"]["pct_5_mais"],
                "sem_bio_pct_2t": r["sem_biometria"]["pct_2t"],
                "sem_bio_pct_1t_mesmas": r["sem_biometria"]["pct_1t_mesmas"],
                "sem_bio_mun_p50_1t": _q(g["mun_p50_sem_bio_api"], 0.5),
                "ano_nasc_pct_2t": r["ano_nascimento"]["pct_2t"],
                "ano_nasc_pct_1t_mesmas": r["ano_nascimento"]["pct_1t_mesmas"],
                "ano_nasc_mun_p50_1t": _q(g["mun_p50_ano_nasc_pct1"], 0.5),
                "enc_p50_2t": r["encerramento"]["p50_2t"],
                "enc_p50_1t_mesmas": r["encerramento"]["p50_1t_mesmas"],
                "contingencia": r["urna"]["contingencia"],
                "sistema_apuracao": r["urna"]["sistema_apuracao"],
                "sinais": r["sinais"],
                "escore_2_mais": r["escore_2_mais"],
            }
        )
    # colunar: com o banco completo são 5.570 municípios
    for m in por_mun:
        for s, v in m.pop("sinais").items():
            m[f"sinal_{s}"] = v
    cols = list(por_mun[0]) if por_mun else []
    return {
        "brasil": resumo_grupo(x),
        "por_uf": por_uf,
        "por_municipio": {
            "colunas": cols,
            "linhas": [[m[c] for c in cols] for m in por_mun],
        },
    }


def prorrogacao(x: pd.DataFrame) -> dict[str, Any]:
    """As seções ficaram abertas até 19h? Encerramento, emissão e recebimento."""

    def bloco(g: pd.DataFrame) -> dict[str, Any]:
        h = g[g["enc_min"].notna()]
        enc = np.floor(h["enc_min"])
        rec = h["rec_min"]
        lag_er = h["rec_min"] - h["enc_min"]
        lag_ee = h["emis_min"] - h["enc_min"]
        lag_mr = h["rec_min"] - h["emis_min"]
        r1 = h[h["enc1_min"].notna()]
        return {
            "n": len(h),
            "abertura_p50": hhmm(_q(h["abert_min"], 0.5)),
            "encerramento_p50": hhmm(_q(h["enc_min"], 0.5)),
            "encerramento_p90": hhmm(_q(h["enc_min"], 0.9)),
            "encerramento_p99": hhmm(_q(h["enc_min"], 0.99)),
            "encerramento_max": hhmm(float(h["enc_min"].max()) if len(h) else None),
            "pct_ate_1715": _parcela(enc <= 15),
            "pct_apos_1730": _parcela(enc >= 31),
            "pct_apos_1800": _parcela(enc >= 61),
            "pct_apos_1900": _parcela(enc >= 121),
            "n_apos_1900": int((enc >= 121).sum()),
            "pct_apos_1800_1t_mesmas": _parcela(np.floor(r1["enc1_min"]) >= 61),
            "pct_apos_1900_1t_mesmas": _parcela(np.floor(r1["enc1_min"]) >= 121),
            "emissao_menos_encerramento_p50_min": _q(lag_ee, 0.5),
            "emissao_menos_encerramento_p90_min": _q(lag_ee, 0.9),
            "emissao_p50": hhmm(_q(h["emis_min"], 0.5)),
            "emissao_p90": hhmm(_q(h["emis_min"], 0.9)),
            "pct_bu_emitido_ate_1730": _parcela(np.floor(h["emis_min"]) <= 30),
            "pct_bu_emitido_apos_1900": _parcela(np.floor(h["emis_min"]) >= 121),
            "recebimento_primeiro": hhmm(
                float(rec.min()) if rec.notna().any() else None
            ),
            "recebimento_p10": hhmm(_q(rec, 0.1)),
            "recebimento_p50": hhmm(_q(rec, 0.5)),
            "pct_recebido_antes_1900": _parcela(rec < 120, rec.notna()),
            "lag_encerramento_recebimento_p50_min": _q(lag_er, 0.5),
            "lag_encerramento_recebimento_p90_min": _q(lag_er, 0.9),
            "lag_emissao_recebimento_p50_min": _q(lag_mr, 0.5),
        }

    return {
        "brasil": bloco(x),
        "por_uf": [{"uf": uf, **bloco(g)} for uf, g in x.groupby("uf", sort=True)],
    }


INDICADORES_NACIONAIS: dict[str, str] = {
    "apos_1800": "último voto depois das 18:00 de Brasília",
    "apos_19h": "último voto depois das 19:00 de Brasília",
    "recebido_antes_1900": "BU recebido antes das 19:00 de Brasília",
    "delta": "comparecimento ≥ +5 pp contra a própria seção no 1T",
    "delta_relativo": "comparecimento ≥ 5 pp acima da alta mediana do município ou UF",
    "queda5": "comparecimento ≤ -5 pp contra a própria seção no 1T",
    "sinal_sem_bio": "sinal de sem biometria",
    "sinal_ano_nasc": "sinal de ano de nascimento",
    "sinal_salto_bio": "salto da parcela sem biometria reconhecida",
    "pianista": "comparecimento +5 pp e salto de biometria",
    "tardia": "tardia",
    "contingencia": "contingência ou mais de uma carga",
    "escore2": "escore 2 ou mais",
}


def estimativa_nacional(x: pd.DataFrame, secoes_uf: dict[str, int]) -> dict[str, Any]:
    """Proporções do país pela amostra estratificada por UF (pesos = seções do 1T).

    Só as seções de origem ``amostra`` (sorteio prévio, autoponderado dentro da
    UF); a paralela fica fora. IC de 95% pela variância estratificada sob sorteio
    simples dentro da UF, sem correção de população finita.
    """
    a = x[x["origem"] == "amostra"].assign(
        apos_1800=np.floor(x["enc_min"]) >= 61,
        recebido_antes_1900=x["rec_min"] < 120,
        queda5=x["delta_pp"] <= -5,
        escore2=x["escore"] >= 2,
    )
    if a.empty:
        return {"disponivel": False}
    total = sum(secoes_uf.get(u, 0) for u in a["uf"].unique())
    out: dict[str, Any] = {
        "disponivel": True,
        "n": len(a),
        "ufs": int(a["uf"].nunique()),
        "secoes_universo": total,
        "metodo": "média das UFs ponderada pelas seções do 1T; IC 95% estratificado",
        "indicadores": [],
    }
    for col, desc in INDICADORES_NACIONAIS.items():
        est = var = 0.0
        for uf, g in a.groupby("uf"):
            w = secoes_uf.get(uf, 0) / total
            v = g[col].astype(bool)
            p = float(v.mean())
            est += w * p
            var += w**2 * p * (1 - p) / max(len(g), 1)
        ep = float(np.sqrt(var))
        out["indicadores"].append(
            {
                "indicador": col,
                "descricao": desc,
                "pct": round(100 * est, 2),
                "ic95": [
                    round(100 * max(0.0, est - 1.96 * ep), 2),
                    round(100 * (est + 1.96 * ep), 2),
                ],
                "secoes_estimadas": round(est * total),
            }
        )
    for col, desc in (
        ("delta_pp", "variação média do comparecimento por seção, pp"),
        ("salto_bio_pp", "variação média da parcela sem biometria reconhecida, pp"),
    ):
        est = var = 0.0
        for uf, g in a.groupby("uf"):
            w = secoes_uf.get(uf, 0) / total
            v = g[col].dropna()
            est += w * float(v.mean())
            if len(v) > 1:
                var += w**2 * float(v.var(ddof=1)) / len(v)
        ep = float(np.sqrt(var))
        out["indicadores"].append(
            {
                "indicador": f"media_{col}",
                "descricao": desc,
                "valor": round(est, 2),
                "ic95": [round(est - 1.96 * ep, 2), round(est + 1.96 * ep, 2)],
            }
        )
    return out
