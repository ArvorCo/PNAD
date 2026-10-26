"""Contas da habilitação do eleitor: país, UF, município, seção, urna e voto.

Regras declaradas em ``REGRAS``. Parcela = categoria / comparecimento x 100, só no
universo com categoria (Brasil, BU da urna: ``tipo_arquivo`` 1 ou 2). Ano de
nascimento não é voto sem identificação: é eleitor com biometria cadastrada que o
leitor não reconheceu, identificado pelo documento e liberado pela data de
nascimento. Sem cadastro é eleitor que nunca coletou biometria.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import secoes_voto
from .biometria_dados import CHAVE

ROTULO = (
    "Ano de nascimento não é voto sem identificação: é eleitor com biometria "
    "cadastrada que o leitor não reconheceu, identificado pelo documento. Sem "
    "cadastro é eleitor que nunca coletou biometria. Parcela alta pede explicação, "
    "não prova irregularidade."
)

REGRAS: dict[str, Any] = {
    "universo": "Brasil (sem ZZ), BU da urna (tipo_arquivo 1 ou 2), comparecimento > 0",
    "municipio_aptos_min": 20000,
    "ranking_n": 30,
    "alta_min_pct": 10,
    "alta_fator_mediana_municipal": 2,
    "salto_pp_min": 5,
    "histograma": "caixas de 1 pp de 0 a 30, última aberta (30 ou mais)",
    "modelos_antigos": ["UE2013", "UE2015"],
    "modelos_novos": ["UE2020", "UE2022"],
    "n_min": secoes_voto.N_MIN,
}
CATS = [("bio", "biometria"), ("ano", "ano_nascimento"), ("sem", "sem_cadastro")]


def r2(v: float | None) -> float | None:
    return None if v is None or not np.isfinite(v) else round(float(v), 2)


def universo(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["uf"] != "ZZ") & (df["tipo_arquivo"] <= 2) & (df["comp"] > 0)].copy()


def totais(df: pd.DataFrame) -> dict[str, Any]:
    br = df[df["uf"] != "ZZ"]
    zz = df[df["uf"] == "ZZ"]
    u = universo(df)
    comp = int(u["comp"].sum())
    out: dict[str, Any] = {
        "secoes": len(u),
        "comparecimento_com_categoria": comp,
        **{nome: int(u[c].sum()) for c, nome in CATS},
        **{f"{nome}_pct": r2(100 * u[c].sum() / comp) for c, nome in CATS},
        "identidade_fecha": bool((u["bio"] + u["ano"] + u["sem"] == u["comp"]).all()),
        "secoes_identidade_falha": int(
            (u["bio"] + u["ano"] + u["sem"] != u["comp"]).sum()
        ),
        "exterior_secoes": int((zz["tipo_arquivo"] <= 2).sum()),
        "exterior_modelos": {
            str(k): int(v)
            for k, v in zz.loc[zz["tipo_arquivo"] <= 2, "modelo_urna"]
            .value_counts()
            .sort_index()
            .items()
        },
        "exterior_comparecimento_sem_categoria": int(zz["comp"].fillna(0).sum()),
        "sistema_apuracao_secoes_brasil": int((br["tipo_arquivo"] > 2).sum()),
        "sistema_apuracao_secoes_exterior": int((zz["tipo_arquivo"] > 2).sum()),
        "sistema_apuracao_comparecimento_brasil": int(
            br.loc[br["tipo_arquivo"] > 2, "comp"].fillna(0).sum()
        ),
    }
    out["comparecimento_total"] = (
        comp
        + out["exterior_comparecimento_sem_categoria"]
        + out["sistema_apuracao_comparecimento_brasil"]
    )
    return out


def _parcelas(g: pd.DataFrame, suf: str) -> dict[str, Any]:
    comp = float(g["comp"].sum())
    o: dict[str, Any] = {f"comp{suf}": int(comp)}
    for c, nome in CATS:
        o[f"{nome}{suf}"] = int(g[c].sum())
        o[f"{nome}_pct{suf}"] = r2(100 * g[c].sum() / comp) if comp > 0 else None
    return o


def por_grupo(u1: pd.DataFrame, u2: pd.DataFrame, chave: list[str]) -> pd.DataFrame:
    a = u2.groupby(chave).apply(
        lambda g: pd.Series(_parcelas(g, "_2t")), include_groups=False
    )
    b = u1.groupby(chave).apply(
        lambda g: pd.Series(_parcelas(g, "_1t")), include_groups=False
    )
    t = a.join(b, how="outer").reset_index()
    for _, nome in CATS:
        t[f"{nome}_delta_pp"] = (t[f"{nome}_pct_2t"] - t[f"{nome}_pct_1t"]).round(2)
    return t


def registros(t: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for rec in t.to_dict(orient="records"):
        out.append(
            {
                k: (
                    None
                    if isinstance(v, float) and not np.isfinite(v)
                    else (int(v) if isinstance(v, (np.integer,)) else v)
                )
                for k, v in rec.items()
            }
        )
    return out


def municipios(
    u1: pd.DataFrame,
    u2: pd.DataFrame,
    aptos2: pd.DataFrame,
    nomes: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    t = por_grupo(u1, u2, ["uf", "mun"])
    ap = aptos2.groupby(["uf", "mun"])["aptos"].sum().rename("aptos_2t").reset_index()
    t = t.merge(ap, on=["uf", "mun"], how="left")
    t = t[t["aptos_2t"] >= REGRAS["municipio_aptos_min"]].copy()
    t["nome"] = [
        nomes.get((u, m), {}).get("nome")
        for u, m in zip(t["uf"], t["mun"], strict=True)
    ]
    t["lat"] = [
        nomes.get((u, m), {}).get("lat") for u, m in zip(t["uf"], t["mun"], strict=True)
    ]
    t["lon"] = [
        nomes.get((u, m), {}).get("lon") for u, m in zip(t["uf"], t["mun"], strict=True)
    ]
    n = REGRAS["ranking_n"]
    cols = [
        "uf", "mun", "nome", "lat", "lon", "aptos_2t", "comp_2t",
        "ano_nascimento_pct_2t", "ano_nascimento_pct_1t", "ano_nascimento_delta_pp",
        "sem_cadastro_pct_2t", "sem_cadastro_pct_1t", "sem_cadastro_delta_pp",
        "biometria_pct_2t", "biometria_pct_1t",
    ]  # fmt: skip
    return {
        "n_municipios": len(t),
        "maior_ano_nascimento": registros(
            t.sort_values("ano_nascimento_pct_2t", ascending=False).head(n)[cols]
        ),
        "menor_ano_nascimento": registros(
            t.sort_values("ano_nascimento_pct_2t").head(10)[cols]
        ),
        "maior_sem_cadastro": registros(
            t.sort_values("sem_cadastro_pct_2t", ascending=False).head(n)[cols]
        ),
        "maior_alta_ano_nascimento": registros(
            t.sort_values("ano_nascimento_delta_pp", ascending=False).head(10)[cols]
        ),
        "mediana_ano_nascimento_pct_2t": r2(t["ano_nascimento_pct_2t"].median()),
        "mediana_sem_cadastro_pct_2t": r2(t["sem_cadastro_pct_2t"].median()),
    }


def histograma(u1: pd.DataFrame, u2: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"caixas_pp": list(range(31)), "turnos": {}}
    for nome, u in (("1t", u1), ("2t", u2)):
        p = 100 * u["ano"] / u["comp"]
        k = np.minimum(np.floor(p), 30).astype(int)
        cont = np.bincount(k, minlength=31)
        out["turnos"][nome] = {
            "n": len(u),
            "contagem": [int(c) for c in cont],
            "p50": r2(p.median()),
            "p90": r2(p.quantile(0.9)),
            "p99": r2(p.quantile(0.99)),
            "secoes_10_mais": int((p >= 10).sum()),
            "secoes_30_mais": int((p >= 30).sum()),
            "secoes_50_mais": int((p >= 50).sum()),
        }
    return out


def modelos(u1: pd.DataFrame, u2: pd.DataFrame) -> dict[str, Any]:
    """Parcela por modelo de urna nos dois turnos e o teste dentro do município."""
    lin = []
    for nome, u in (("1t", u1), ("2t", u2)):
        for mod, g in u.groupby(u["modelo_urna"].fillna("sem_log")):
            p = 100 * g["ano"] / g["comp"]
            lin.append(
                {
                    "turno": nome,
                    "modelo": mod,
                    "secoes": len(g),
                    "comp": int(g["comp"].sum()),
                    "ano_nascimento_pct": r2(100 * g["ano"].sum() / g["comp"].sum()),
                    "sem_cadastro_pct": r2(100 * g["sem"].sum() / g["comp"].sum()),
                    "ano_nascimento_p50_secao": r2(p.median()),
                }
            )
    antigos, novos = REGRAS["modelos_antigos"], REGRAS["modelos_novos"]
    dentro = {}
    for nome, u in (("1t", u1), ("2t", u2)):
        x = u[u["modelo_urna"].isin(antigos + novos)].assign(
            antigo=lambda d: d["modelo_urna"].isin(antigos)
        )
        difs, pesos = [], []
        n_a = n_n = 0
        for _, g in x.groupby(["uf", "mun"]):
            a, b = g[g["antigo"]], g[~g["antigo"]]
            if a.empty or b.empty:
                continue
            difs.append(
                100
                * (a["ano"].sum() / a["comp"].sum() - b["ano"].sum() / b["comp"].sum())
            )
            pesos.append(a["comp"].sum())
            n_a += len(a)
            n_n += len(b)
        d = np.array(difs)
        w = np.array(pesos, dtype=float)
        m = float(np.sum(w * d) / np.sum(w)) if len(d) else None
        ep = (
            float(np.sqrt(np.sum(w**2 * (d - m) ** 2)) / np.sum(w))
            if len(d) > 1
            else None
        )
        dentro[nome] = {
            "municipios": len(d),
            "secoes_antigas": n_a,
            "secoes_novas": n_n,
            "dif_ano_nascimento_antiga_menos_nova_pp": r2(m),
            "ep_pp": r2(ep),
        }
    # mesma seção, urna trocada entre os turnos
    j = u2[[*CHAVE, "modelo_urna", "ano", "comp"]].merge(
        u1[[*CHAVE, "modelo_urna", "ano", "comp"]], on=CHAVE, suffixes=("_2t", "_1t")
    )
    j = j[j["modelo_urna_2t"].notna() & j["modelo_urna_1t"].notna()]
    j["d"] = 100 * j["ano_2t"] / j["comp_2t"] - 100 * j["ano_1t"] / j["comp_1t"]
    ant = j["modelo_urna_1t"].isin(antigos), j["modelo_urna_2t"].isin(antigos)
    trocas = []
    for rot, m_ in (
        ("mesmo modelo", j["modelo_urna_1t"] == j["modelo_urna_2t"]),
        ("antiga no 1T, nova no 2T", ant[0] & ~ant[1]),
        ("nova no 1T, antiga no 2T", ~ant[0] & ant[1]),
        (
            "trocou entre novas ou entre antigas",
            (j["modelo_urna_1t"] != j["modelo_urna_2t"]) & (ant[0] == ant[1]),
        ),
    ):
        g = j[m_]
        trocas.append(
            {
                "grupo": rot,
                "secoes": len(g),
                "variacao_ano_nascimento_media_pp": (
                    r2(g["d"].mean()) if len(g) >= REGRAS["n_min"] else None
                ),
                "variacao_ano_nascimento_p50_pp": (
                    r2(g["d"].median()) if len(g) >= REGRAS["n_min"] else None
                ),
            }
        )
    return {
        "por_modelo": lin,
        "dentro_do_municipio": dentro,
        "mesma_secao_troca": trocas,
    }


def voto(u1: pd.DataFrame, u2: pd.DataFrame) -> list[dict[str, Any]]:
    """Fatia de Flávio nas seções com parcela alta contra as vizinhas do município."""
    j = u2.merge(
        u1[[*CHAVE, "ano", "sem", "comp", "fl", "lu"]],
        on=CHAVE,
        how="left",
        suffixes=("", "1"),
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        j["ano_pct"] = 100 * j["ano"] / j["comp"]
        j["sem_pct"] = 100 * j["sem"] / j["comp"]
        j["ano_pct1"] = 100 * j["ano1"] / j["comp1"]
        f2 = 100 * j["fl"] / (j["fl"] + j["lu"])
        f1 = 100 * j["fl1"] / (j["fl1"] + j["lu1"])
    j["delta_fatia_pp"] = (f2 - f1).where(np.isfinite(f2 - f1))
    med_ano = j.groupby(["uf", "mun"])["ano_pct"].transform("median")
    med_sem = j.groupby(["uf", "mun"])["sem_pct"].transform("median")
    rg = REGRAS
    grupos = {
        "ano_nascimento_alto": (
            "ano de nascimento ≥ 10% e ≥ 2x a mediana do município",
            (j["ano_pct"] >= rg["alta_min_pct"]) & (j["ano_pct"] >= 2 * med_ano),
        ),
        "sem_cadastro_alto": (
            "sem cadastro ≥ 10% e ≥ 2x a mediana do município",
            (j["sem_pct"] >= rg["alta_min_pct"]) & (j["sem_pct"] >= 2 * med_sem),
        ),
        "ano_nascimento_salto": (
            "ano de nascimento 5 pp ou mais acima da própria seção no 1T",
            (j["ano_pct"] - j["ano_pct1"]) >= rg["salto_pp_min"],
        ),
    }
    out = []
    for k, (desc, m) in grupos.items():
        out.append({"grupo": k, "descricao": desc, **secoes_voto.comparar(j, m)})
    return out
