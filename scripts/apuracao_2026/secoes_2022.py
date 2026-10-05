"""Presidente por seção em 2022 (1º e 2º turnos), para comparar com 2026.

Fontes do TSE (dados abertos, latin-1, `;`):

- ``votacao_secao_2022_BR.zip``: votos por candidato e seção na eleição federal
  (presidente), os dois turnos;
- ``detalhe_votacao_secao_2022.zip`` (arquivo ``_BR.csv``): aptos, comparecimento,
  brancos, nulos, local de votação e modelo da urna por seção.

O resultado compacto (uma linha por seção) fica em cache em
``data/outputs/presidente_secao_2022.csv.gz``; o cache guarda o SHA-256 dos dois
ZIPs de origem e é refeito quando eles mudam.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

USE_VOTOS = ["NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
USE_VOTOS += ["CD_CARGO", "NR_VOTAVEL", "QT_VOTOS", "NM_LOCAL_VOTACAO"]
USE_DETALHE = ["NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "CD_CARGO"]
USE_DETALHE += ["QT_APTOS", "QT_COMPARECIMENTO", "QT_VOTOS_NOMINAIS"]
USE_DETALHE += ["QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS", "NR_LOCAL_VOTACAO"]
USE_DETALHE += ["NM_LOCAL_VOTACAO", "CD_MODELO_URNA", "DT_RECEBIMENTO_BU_HOR_TSE"]
CHAVES = ["uf", "mun", "zona", "secao"]


def _sha(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _membro(z: zipfile.ZipFile, sufixo: str) -> str:
    for nome in z.namelist():
        if nome.endswith(sufixo):
            return nome
    raise FileNotFoundError(sufixo)


def _chaves(df: pd.DataFrame) -> pd.DataFrame:
    df["uf"] = df["SG_UF"].str.lower()
    df["mun"] = df["CD_MUNICIPIO"].astype(int).map(lambda v: f"{v:05d}")
    df["zona"] = df["NR_ZONA"].astype(int)
    df["secao"] = df["NR_SECAO"].astype(int)
    return df


def ler_votos(zip_votos: Path) -> pd.DataFrame:
    partes = []
    with (
        zipfile.ZipFile(zip_votos) as z,
        z.open(_membro(z, "votacao_secao_2022_BR.csv")) as f,
    ):
        for bloco in pd.read_csv(
            f,
            sep=";",
            encoding="latin-1",
            usecols=USE_VOTOS,
            dtype=str,
            chunksize=2_000_000,
        ):
            bloco = bloco[bloco["CD_CARGO"] == "1"]
            bloco = _chaves(bloco)
            bloco["n"] = bloco["NR_VOTAVEL"].astype(int)
            bloco["v"] = bloco["QT_VOTOS"].astype(int)
            bloco["t"] = bloco["NR_TURNO"].astype(int)
            partes.append(bloco[[*CHAVES, "t", "n", "v", "NM_LOCAL_VOTACAO"]])
    df = pd.concat(partes, ignore_index=True)
    linhas = []
    for t in (1, 2):
        d = df[df["t"] == t]
        nominal = d[(d["n"] != 95) & (d["n"] != 96)]
        g = pd.DataFrame(
            {
                f"lula_{t}t": d[d["n"] == 13].groupby(CHAVES)["v"].sum(),
                f"bolsonaro_{t}t": d[d["n"] == 22].groupby(CHAVES)["v"].sum(),
                f"nominais_{t}t": nominal.groupby(CHAVES)["v"].sum(),
            }
        )
        linhas.append(g)
    saida = pd.concat(linhas, axis=1).fillna(0).astype(np.int64).reset_index()
    nomes = (
        df[df["t"] == 1]
        .drop_duplicates(CHAVES)
        .set_index(CHAVES)["NM_LOCAL_VOTACAO"]
        .rename("local_2022")
    )
    return saida.merge(nomes.reset_index(), on=CHAVES, how="left")


def ler_detalhe(zip_detalhe: Path) -> pd.DataFrame:
    with (
        zipfile.ZipFile(zip_detalhe) as z,
        z.open(_membro(z, "detalhe_votacao_secao_2022_BR.csv")) as f,
    ):
        df = pd.read_csv(f, sep=";", encoding="latin-1", usecols=USE_DETALHE, dtype=str)
    df = df[(df["CD_CARGO"] == "1") & (df["NR_TURNO"] == "1")].copy()
    df = _chaves(df)
    saida = df[CHAVES].copy()
    for origem, destino in (
        ("QT_APTOS", "aptos_2022"),
        ("QT_COMPARECIMENTO", "comparecimento_2022"),
        ("QT_VOTOS_BRANCOS", "brancos_2022"),
        ("QT_VOTOS_NULOS", "nulos_2022"),
        ("NR_LOCAL_VOTACAO", "local_nr_2022"),
    ):
        saida[destino] = pd.to_numeric(df[origem], errors="coerce")
    modelo = pd.to_numeric(df["CD_MODELO_URNA"], errors="coerce")
    saida["modelo_2022"] = [
        f"UE{int(m)}" if pd.notna(m) and m > 0 else None for m in modelo
    ]
    saida["recebido_2022"] = df["DT_RECEBIMENTO_BU_HOR_TSE"].to_numpy()
    return saida


def presidente_2022(
    zip_votos: Path, zip_detalhe: Path, cache: Path
) -> pd.DataFrame | None:
    """Uma linha por seção de 2022 com votos de presidente e modelo da urna."""
    if not zip_votos.exists() or not zip_detalhe.exists():
        return None
    meta = cache.with_suffix(".json")
    assinatura = {"votos": _sha(zip_votos), "detalhe": _sha(zip_detalhe)}
    if cache.exists() and meta.exists():
        try:
            if json.loads(meta.read_text(encoding="utf-8")) == assinatura:
                return pd.read_csv(cache, dtype={"mun": str, "uf": str})
        except (OSError, json.JSONDecodeError):
            pass
    votos = ler_votos(zip_votos)
    detalhe = ler_detalhe(zip_detalhe)
    df = votos.merge(detalhe, on=CHAVES, how="outer")
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False, compression="gzip")
    meta.write_text(json.dumps(assinatura), encoding="utf-8")
    return df


def normalizar_local(s: str) -> str:
    """Nome de local sem acento, em maiúsculas, sem pontos nem espaços repetidos."""
    n = unicodedata.normalize("NFKD", s)
    t = "".join(c for c in n if not unicodedata.combining(c)).upper()
    return " ".join(t.replace(".", " ").split())


def casar(df: pd.DataFrame, s22: pd.DataFrame) -> pd.DataFrame:
    """Junta 2022 às seções de 2026 e marca `mesma_secao`.

    Mesma seção: mesma UF, município, zona e número, mesmo nome de local de
    votação nos dois cadastros (normalizado) e voto nominal de presidente em 2022.
    """
    cols = [
        *CHAVES,
        "lula_1t",
        "bolsonaro_1t",
        "nominais_1t",
        "lula_2t",
        "bolsonaro_2t",
        "nominais_2t",
        "local_2022",
        "modelo_2022",
        "aptos_2022",
    ]
    m = df.merge(s22[cols], on=CHAVES, how="left")
    l26 = m["local"].fillna("").map(normalizar_local)
    l22 = m["local_2022"].fillna("").map(normalizar_local)
    m["mesma_secao"] = (l26 != "") & (l26 == l22) & (m["nominais_1t"].fillna(0) > 0)
    return m
