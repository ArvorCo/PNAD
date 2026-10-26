"""Leitura dos BUs dos dois turnos e o espaço da mistura (seções do Brasil).

Lê ``apuracao/data/secoes_2026.sqlite`` (1T) e ``secoes_2t_2026.sqlite`` (2T) em
modo somente leitura, com uma consulta agregada por banco (presidente, cargo 1:
tipo 1 nominal com ``numero``, 2 branco, 3 nulo). Universo: seções com BU nos dois
turnos, fora do exterior e com aptos ≥ 30 em ambos. As nove features são frações
do eleitorado do próprio turno, em pontos percentuais (``COLUNAS``); o
comparecimento fica implícito como soma das partes e é conferido contra o BU.

A leitura agregada de cada banco fica em cache em ``data/outputs/apuracao_2t_2026/``
(``anomalia_<turno>.pkl``), invalidado pela assinatura do banco (tamanho e data).
"""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2026.dados import regiao
from apuracao_2026.secoes_clusters_motor import amostra_estratificada

from .base import CACHE
from .urnas_base import CHAVE, abrir, assinatura

NUM_LULA = 13
NUM_FLAVIO = 22
APTOS_MIN = 30
COLUNAS = (
    "lula1",
    "flavio1",
    "outros1",
    "brancos1",
    "nulos1",
    "lula2",
    "flavio2",
    "brancos2",
    "nulos2",
)
PARTES_1T = ("lula", "flavio", "outros", "brancos", "nulos")
PARTES_2T = ("lula", "flavio", "brancos", "nulos")
# colunas do enquadramento por diferença: cinco do 1T e quatro deltas do 2T
COLUNAS_DELTA = (
    "lula1",
    "flavio1",
    "outros1",
    "brancos1",
    "nulos1",
    "d_lula",
    "d_flavio",
    "d_brancos",
    "d_nulos",
)

SQL_BU = (
    "SELECT uf, mun, zona, secao, aptos, comparecimento, modelo_urna, tipo_arquivo, "
    "tipo_urna, n_cargas FROM bu"
)
SQL_VOTOS = f"""
SELECT uf, mun, zona, secao,
  SUM(CASE WHEN tipo=1 AND numero={NUM_LULA} THEN votos ELSE 0 END) AS lula,
  SUM(CASE WHEN tipo=1 AND numero={NUM_FLAVIO} THEN votos ELSE 0 END) AS flavio,
  SUM(CASE WHEN tipo=1 AND numero NOT IN ({NUM_LULA},{NUM_FLAVIO}) THEN votos ELSE 0 END)
    AS outros,
  SUM(CASE WHEN tipo=2 THEN votos ELSE 0 END) AS brancos,
  SUM(CASE WHEN tipo=3 THEN votos ELSE 0 END) AS nulos,
  SUM(CASE WHEN tipo NOT IN (1,2,3) THEN votos ELSE 0 END) AS outros_tipos
FROM voto_secao WHERE cargo=1 GROUP BY uf, mun, zona, secao
"""
VOTOS = ("lula", "flavio", "outros", "brancos", "nulos", "outros_tipos")


def ler_turno(banco: Path) -> pd.DataFrame:
    """BU e votos de presidente por seção, uma linha por BU (UF em maiúsculas)."""
    con = abrir(banco)
    try:
        bu = pd.read_sql(SQL_BU, con)
        votos = pd.read_sql(SQL_VOTOS, con)
    finally:
        con.close()
    df = bu.merge(votos, on=CHAVE, how="left")
    df[list(VOTOS)] = df[list(VOTOS)].fillna(0).astype(np.int64)
    df["uf"] = df["uf"].str.upper()
    return df


def ler_com_cache(banco: Path, nome: str, usar_cache: bool = True) -> pd.DataFrame:
    arquivo = CACHE / f"anomalia_{nome}.pkl"
    sig = assinatura(banco)
    if usar_cache and arquivo.exists():
        with arquivo.open("rb") as f:
            salvo = pickle.load(f)
        if salvo.get("assinatura") == sig:
            return salvo["dados"]
    df = ler_turno(banco)
    if usar_cache:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        with arquivo.open("wb") as f:
            pickle.dump({"assinatura": sig, "dados": df}, f)
    return df


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 22), b""):
            h.update(bloco)
    return h.hexdigest()


def unir(t1: pd.DataFrame, t2: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Universo pareado e as exclusões contadas por motivo (na ordem declarada).

    Motivos, cada seção contada uma vez, no primeiro que a exclui: ``exterior``
    (UF ``ZZ`` em qualquer turno), ``sem_par`` (BU em um turno só), ``aptos_menor_30``
    (aptos abaixo de 30 em algum turno) e ``outros`` (aptos ausentes).
    """
    a = t1.add_suffix("_1").rename(columns={f"{c}_1": c for c in CHAVE})
    b = t2.add_suffix("_2").rename(columns={f"{c}_2": c for c in CHAVE})
    m = a.merge(b, on=CHAVE, how="outer", indicator=True)
    exterior = m["uf"] == "ZZ"
    sem_par = ~exterior & (m["_merge"] != "both")
    par = ~exterior & ~sem_par
    aptos_ok = m["aptos_1"].notna() & m["aptos_2"].notna()
    menor = par & aptos_ok & ((m["aptos_1"] < APTOS_MIN) | (m["aptos_2"] < APTOS_MIN))
    outros = par & ~aptos_ok
    fica = par & aptos_ok & ~menor
    excl = {
        "exterior": int(exterior.sum()),
        "sem_par": int(sem_par.sum()),
        "sem_par_so_1t": int((sem_par & (m["_merge"] == "left_only")).sum()),
        "sem_par_so_2t": int((sem_par & (m["_merge"] == "right_only")).sum()),
        "aptos_menor_30": int(menor.sum()),
        "outros": int(outros.sum()),
    }
    df = m[fica].drop(columns="_merge").reset_index(drop=True)
    for c in ("aptos_1", "aptos_2", "comparecimento_1", "comparecimento_2"):
        df[c] = df[c].astype(np.int64)
    for t in ("1", "2"):
        for v in VOTOS:
            df[f"{v}_{t}"] = df[f"{v}_{t}"].astype(np.int64)
    df["regiao"] = [regiao(u) for u in df["uf"]]
    excl["total_bus"] = len(m)
    return df, excl


def conferir_comparecimento(df: pd.DataFrame) -> dict[str, Any]:
    """Soma dos votos de presidente contra ``bu.comparecimento`` em cada turno.

    A diferença, se houver, é registrada e não muda as features.
    """
    out: dict[str, Any] = {
        "regra": (
            "comparecimento implícito = Lula + Flávio + outros + brancos + nulos (1T) e "
            "Lula + Flávio + brancos + nulos (2T), contra o comparecimento do BU"
        )
    }
    total = np.zeros(len(df), dtype=bool)
    for t in ("1", "2"):
        soma = sum(df[f"{v}_{t}"] for v in VOTOS)
        dif = soma - df[f"comparecimento_{t}"]
        div = dif != 0
        total |= div.to_numpy()
        out[f"turno{t}"] = {
            "secoes": int(div.sum()),
            "soma_diferencas": int(dif.sum()),
            "soma_abs_diferencas": int(dif.abs().sum()),
            "exemplos": [
                {
                    "uf": r.uf,
                    "mun": r.mun,
                    "zona": int(r.zona),
                    "secao": int(r.secao),
                    "votos": int(s),
                    "comparecimento_bu": int(c),
                }
                for r, s, c in zip(
                    df[div].head(5).itertuples(index=False),
                    soma[div].head(5),
                    df.loc[div, f"comparecimento_{t}"].head(5),
                    strict=True,
                )
            ],
        }
    out["secoes"] = int(total.sum())
    out["outros_candidatos_2t_votos"] = int(df["outros_2"].sum())
    out["outros_tipos_votos"] = int(
        df["outros_tipos_1"].sum() + df["outros_tipos_2"].sum()
    )
    return out


def fracoes(df: pd.DataFrame) -> pd.DataFrame:
    """As nove frações do eleitorado (pp) e as derivadas: comparecimento e deltas."""
    a1 = df["aptos_1"].to_numpy(dtype=float)
    a2 = df["aptos_2"].to_numpy(dtype=float)
    f = pd.DataFrame(index=df.index)
    for p in PARTES_1T:
        f[f"{p}1"] = 100.0 * df[f"{p}_1"].to_numpy(dtype=float) / a1
    for p in PARTES_2T:
        f[f"{p}2"] = 100.0 * df[f"{p}_2"].to_numpy(dtype=float) / a2
    f["comp1"] = f[[f"{p}1" for p in PARTES_1T]].sum(axis=1)
    f["comp2"] = f[[f"{p}2" for p in PARTES_2T]].sum(axis=1)
    for p in PARTES_2T:
        f[f"d_{p}"] = f[f"{p}2"] - f[f"{p}1"]
    f["d_comp"] = f["comp2"] - f["comp1"]
    return f


def padronizar(m: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(x − média) / desvio-padrão por coluna, entre seções (desvio populacional)."""
    media = m.mean(axis=0)
    dp = m.std(axis=0)
    if not (dp > 0).all():
        raise ValueError("coluna sem variação entre seções")
    return (m - media) / dp, media, dp


def matriz(f: pd.DataFrame, colunas: tuple[str, ...]) -> np.ndarray:
    x = f[list(colunas)].to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("fração não finita")
    return x


def logdet_transformacao(f: pd.DataFrame) -> float:
    """log|det A| da passagem dos níveis padronizados aos deltas padronizados.

    Z_d = D_d⁻¹ B D_n Z_n + c, com B unitriangular (Δ = 2T − 1T): det A = ∏dp_n / ∏dp_d.
    A log-verossimilhança média nos deltas é a dos níveis menos esse valor.
    """
    dp_n = matriz(f, COLUNAS).std(axis=0)
    dp_d = matriz(f, COLUNAS_DELTA).std(axis=0)
    return float(np.log(dp_n).sum() - np.log(dp_d).sum())


def amostra_universo(df: pd.DataFrame, n: int, semente: int) -> pd.DataFrame:
    """Rascunho: amostra estratificada por UF do universo (``--amostra``)."""
    idx = amostra_estratificada(df["uf"].to_numpy(), n, semente)
    return df.iloc[idx].reset_index(drop=True)


def faixa_aptos(aptos: pd.Series) -> pd.Series:
    """Tamanho da seção no 2T, em faixas fixas de aptos."""
    cortes = [0, 100, 200, 300, 400, np.inf]
    rot = ["30 a 99", "100 a 199", "200 a 299", "300 a 399", "400 ou mais"]
    return pd.cut(aptos, cortes, right=False, labels=rot).astype(str)
