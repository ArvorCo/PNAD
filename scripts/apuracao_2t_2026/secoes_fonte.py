"""Leitura dos boletins de urna do 2º turno, amostra ou coleta completa.

Duas fontes, sempre em modo somente leitura (``?mode=ro``):

- ``amostra``: tabela ``secao_2t`` de ``apuracao/data/apuracao-2t.sqlite``
  (seções sorteadas por UF mais as da totalização paralela), com as horas já em
  UTC pelo fuso da UF e os votos em ``votos_json``;
- ``completo``: ``apuracao/data/secoes_2t_2026.sqlite`` (mesmo esquema do 1º
  turno, ``apuracao/scripts/secoes/banco.ts``), com as horas do BU na hora local
  da urna e os votos em ``voto_secao``.

As duas viram a mesma tabela, com horas em minutos depois das 17:00 de Brasília
de 25/10/2026. A conversão da hora local usa o fuso da UF e depois corrige, por
município, a hora mais frequente de abertura: a votação abre às 08:00 de
Brasília no país inteiro, então um município cuja abertura modal cai uma hora
antes está num fuso diferente do da UF (os municípios do oeste do Amazonas).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ELEICAO_FEDERAL = "6258"
FLAVIO = 22
LULA = 13
# 17:00 de Brasília (UTC-3) de 25/10/2026
T0_2T = pd.Timestamp("2026-10-25 20:00:00", tz="UTC")
# abertura esperada: 08:00 de Brasília, 540 minutos antes das 17:00
ABERTURA_MIN = -540.0
FUSO_MIN = {"AC": -120, "AM": -60, "RO": -60, "RR": -60, "MT": -60, "MS": -60}
# completo só é escolhido automaticamente com ao menos esta parcela do 1º turno
COBERTURA_AUTO = 0.9

COLUNAS = [
    "uf",
    "mun",
    "zona",
    "secao",
    "origem",
    "aptos",
    "comp",
    "fl",
    "lu",
    "brancos",
    "nulos",
    "hab_bio",
    "ano_nasc",
    "sem_bio",
    "tipo_arquivo",
    "tipo_urna",
    "n_cargas",
    "abert_min",
    "enc_min",
    "emis_min",
    "rec_min",
]


def conectar(caminho: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def contar_completo(caminho: Path) -> int:
    """Quantos BUs a coleta completa já tem (0 se o banco ou a tabela faltar)."""
    if not caminho.exists():
        return 0
    with conectar(caminho) as con:
        tem = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='bu'"
        ).fetchone()
        if not tem:
            return 0
        return int(con.execute("SELECT COUNT(*) FROM bu").fetchone()[0])


def escolher_fonte(pedido: str, n_completo: int, n_universo: int) -> str:
    """``auto`` escolhe o banco completo quando ele cobre 90% do universo do 1T."""
    if pedido in ("amostra", "completo"):
        return pedido
    if n_universo > 0 and n_completo >= COBERTURA_AUTO * n_universo:
        return "completo"
    return "amostra"


def minutos_utc(serie: pd.Series) -> pd.Series:
    """ISO UTC → minutos depois das 17:00 de Brasília de 25/10 (1 decimal)."""
    t = pd.to_datetime(serie, utc=True, errors="coerce")
    return ((t - T0_2T).dt.total_seconds() / 60).round(1)


def minutos_local(serie: pd.Series, uf: pd.Series) -> pd.Series:
    """Hora local da urna (sem fuso) → minutos depois das 17:00 de Brasília."""
    t = pd.to_datetime(serie, errors="coerce")
    base = pd.Timestamp("2026-10-25 17:00:00")
    fuso = uf.str.upper().map(FUSO_MIN).fillna(0)
    return ((t - base).dt.total_seconds() / 60 - fuso).round(1)


def _votos_json(texto: str | None) -> tuple[Any, Any, Any, Any]:
    if not texto:
        return (None, None, None, None)
    try:
        b = json.loads(texto)
        c = b["eleicoes"][ELEICAO_FEDERAL]["cargos"]["1"]
    except (KeyError, TypeError, ValueError):
        return (None, None, None, None)
    nom = c.get("nominais", {})
    return (
        int(nom.get(str(FLAVIO), 0)),
        int(nom.get(str(LULA), 0)),
        c.get("branco"),
        c.get("nulo"),
    )


def ler_amostra(caminho: Path) -> pd.DataFrame:
    with conectar(caminho) as con:
        df = pd.read_sql_query(
            "SELECT uf, mun, zona, secao, origem, aptos, comparecimento AS comp, "
            "votos_json, hab_biometria AS hab_bio, hab_ano_nascimento AS ano_nasc, "
            "comp_sem_biometria AS sem_bio, tipo_arquivo, tipo_urna, n_cargas, "
            "abertura_iso, encerramento_iso, emissao_iso, recebido_iso "
            "FROM secao_2t WHERE bu_sha256 IS NOT NULL",
            con,
        )
    votos = [_votos_json(t) for t in df["votos_json"]]
    df[["fl", "lu", "brancos", "nulos"]] = pd.DataFrame(votos, index=df.index)
    df["uf"] = df["uf"].str.upper()
    df["abert_min"] = minutos_utc(df["abertura_iso"])
    df["enc_min"] = minutos_utc(df["encerramento_iso"])
    df["emis_min"] = minutos_utc(df["emissao_iso"])
    df["rec_min"] = minutos_utc(df["recebido_iso"])
    return df[COLUNAS].copy()


def ler_completo(caminho: Path) -> pd.DataFrame:
    with conectar(caminho) as con:
        bu = pd.read_sql_query(
            "SELECT b.uf, b.mun, b.zona, b.secao, b.aptos, b.comparecimento AS comp, "
            "b.hab_biometria AS hab_bio, b.hab_ano_nascimento AS ano_nasc, "
            "b.comp_sem_biometria AS sem_bio, b.tipo_arquivo, b.tipo_urna, "
            "b.n_cargas, b.abertura, b.encerramento, b.emissao, s.dr_hr "
            "FROM bu b LEFT JOIN secao s USING (uf, mun, zona, secao)",
            con,
        )
        votos = pd.read_sql_query(
            "SELECT uf, mun, zona, secao, tipo, numero, votos FROM voto_secao "
            "WHERE cargo = 1 AND (tipo IN (2, 3) OR (tipo = 1 AND numero IN (?, ?)))",
            con,
            params=(FLAVIO, LULA),
        )
    chave = ["uf", "mun", "zona", "secao"]
    votos["col"] = np.select(
        [
            (votos["tipo"] == 1) & (votos["numero"] == FLAVIO),
            (votos["tipo"] == 1) & (votos["numero"] == LULA),
            votos["tipo"] == 2,
        ],
        ["fl", "lu", "brancos"],
        default="nulos",
    )
    piv = votos.pivot_table(index=chave, columns="col", values="votos", aggfunc="sum")
    piv = piv.reindex(columns=["fl", "lu", "brancos", "nulos"]).reset_index()
    df = bu.merge(piv, on=chave, how="left")
    for c in ("fl", "lu", "brancos", "nulos"):
        df[c] = df[c].fillna(0)
    df["origem"] = "completo"
    uf = df["uf"]
    df["abert_min"] = minutos_local(df["abertura"], uf)
    df["enc_min"] = minutos_local(df["encerramento"], uf)
    df["emis_min"] = minutos_local(df["emissao"], uf)
    # dr_hr do aux.json vem em Brasília
    df["rec_min"] = minutos_local(df["dr_hr"], pd.Series("BR", index=df.index))
    df["uf"] = df["uf"].str.upper()
    return df[COLUNAS].copy()


def correcao_fuso_municipal(df: pd.DataFrame) -> pd.Series:
    """Minutos a somar às horas locais convertidas, por seção (0 quase sempre).

    Desvio da abertura em horas inteiras contra as 08:00 de Brasília, pela moda do
    município. Exterior (ZZ) fica de fora: vota na hora da cidade do consulado.
    """
    desvio = ((df["abert_min"] - ABERTURA_MIN) / 60).round()
    tmp = pd.DataFrame({"k": df["uf"] + ":" + df["mun"], "d": desvio})
    tmp = tmp[(df["uf"] != "ZZ") & tmp["d"].notna()]
    if tmp.empty:
        return pd.Series(0.0, index=df.index)
    moda = tmp.groupby("k")["d"].agg(lambda s: s.mode().iloc[0])
    corr = -60.0 * (df["uf"] + ":" + df["mun"]).map(moda).fillna(0)
    return corr.where(df["uf"] != "ZZ", 0.0)


def carregar(fonte: str, db_amostra: Path, db_completo: Path) -> pd.DataFrame:
    df = ler_completo(db_completo) if fonte == "completo" else ler_amostra(db_amostra)
    corr = correcao_fuso_municipal(df)
    df["corr_fuso_min"] = corr
    for c in ("abert_min", "enc_min", "emis_min"):
        df[c] = df[c] + corr
        df.loc[df["uf"] == "ZZ", c] = np.nan
    for c in ("zona", "secao"):
        df[c] = df[c].astype(int)
    df["mun"] = df["mun"].astype(str).str.zfill(5)
    return df.reset_index(drop=True)
