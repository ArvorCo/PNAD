"""Leitura dos dois cadastros de locais de votação do TSE, direto do ZIP.

Os CSVs (latin-1, ``;``, decimais com vírgula) têm 517.179 linhas por turno; o
arquivo de 18/10 traz o 1º e o 2º turnos juntos. Nada é extraído para o disco: o
arquivo nacional é lido em blocos e só as colunas usadas ficam em memória.
"""

from __future__ import annotations

import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ZIP_1T = ROOT / "data/raw/tse_eleitorado/eleitorado_local_votacao_2026.zip"
ZIP_2T = (
    ROOT
    / "data/raw/tse_eleitorado/locais_2t/eleitorado_local_votacao_2026_20261018.zip"
)
SHA_1T = "045df0a517be35490bcdfdbaf91ed2224122efec9b0d2ab199836e15f8b0805c"
SHA_2T = "a948d3e587d7116ffe003fb07a083b2d1d64ce9a236f703f92d36e168f1b5adb"
ARQUIVO_NACIONAL = "eleitorado_local_votacao_2026_BRASIL.csv"

# Coluna do TSE -> nome curto usado no motor.
COLUNAS = {
    "DT_GERACAO": "dt_geracao",
    "HH_GERACAO": "hh_geracao",
    "NR_TURNO": "turno",
    "SG_UF": "uf",
    "CD_MUNICIPIO": "mun",
    "NM_MUNICIPIO": "municipio",
    "NR_ZONA": "zona",
    "NR_SECAO": "secao",
    "CD_TIPO_SECAO_AGREGADA": "tipo_secao",
    "NR_SECAO_PRINCIPAL": "principal",
    "NR_LOCAL_VOTACAO": "local",
    "NM_LOCAL_VOTACAO": "nome",
    "DS_TIPO_LOCAL": "tipo_local",
    "DS_ENDERECO": "endereco",
    "NM_BAIRRO": "bairro",
    "NR_CEP": "cep",
    "NR_LATITUDE": "lat",
    "NR_LONGITUDE": "lon",
    "DS_SITU_LOCAL_VOTACAO": "situ_local",
    "DS_SITU_SECAO": "situ_secao",
    "QT_ELEITOR_SECAO": "eleitores",
    "QT_ELEITOR_ELEICAO_FEDERAL": "eleitores_federal",
    "NR_LOCAL_VOTACAO_ORIGINAL": "original",
    "NM_LOCAL_VOTACAO_ORIGINAL": "nome_original",
    "DS_ENDERECO_LOCVT_ORIGINAL": "endereco_original",
}
INTEIRAS = (
    "turno",
    "zona",
    "secao",
    "tipo_secao",
    "principal",
    "local",
    "eleitores",
    "eleitores_federal",
    "original",
)
CHAVE = ["uf", "mun", "zona", "secao"]


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _coordenada(serie: pd.Series) -> pd.Series:
    """Texto com vírgula decimal -> float; vazio, zero ou ``-1`` viram ``NaN``."""
    x = pd.to_numeric(serie.str.replace(",", ".", regex=False), errors="coerce")
    return x.where((x != 0) & (x != -1))


def ler_turno(caminho: Path, turno: int, bloco: int = 200_000) -> pd.DataFrame:
    """Linhas de um turno do arquivo nacional, só com as colunas de ``COLUNAS``."""
    partes = []
    with zipfile.ZipFile(caminho) as z, z.open(ARQUIVO_NACIONAL) as bruto:
        leitor = pd.read_csv(
            bruto,
            sep=";",
            encoding="latin-1",
            dtype=str,
            usecols=list(COLUNAS),
            keep_default_na=False,
            chunksize=bloco,
        )
        for parte in leitor:
            parte = parte[parte["NR_TURNO"] == str(turno)]
            if len(parte):
                partes.append(parte.rename(columns=COLUNAS))
    df = pd.concat(partes, ignore_index=True)
    for c in INTEIRAS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("int64")
    df["mun"] = df["mun"].str.zfill(5)
    for c in ("lat", "lon"):
        df[c] = _coordenada(df[c])
    for c in ("nome", "endereco", "bairro", "nome_original", "endereco_original"):
        df[c] = df[c].str.strip()
    return df


def metadados(caminho: Path, df: pd.DataFrame, esperado: str) -> dict[str, Any]:
    st = caminho.stat()
    sha = sha256(caminho)
    geracao = sorted(set(zip(df["dt_geracao"], df["hh_geracao"], strict=True)))
    return {
        "caminho": str(caminho.relative_to(ROOT)),
        "bytes": st.st_size,
        "sha256": sha,
        "sha256_confere": sha == esperado,
        "gerado_tse": [f"{d} {h}" for d, h in geracao],
        "linhas": len(df),
        "modificado_em": datetime.fromtimestamp(st.st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }


def ler_cadastros() -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    """Cadastro do 1º turno (arquivo de 02/10) e do 2º turno (arquivo de 18/10)."""
    t1 = ler_turno(ZIP_1T, 1)
    t2 = ler_turno(ZIP_2T, 2)
    fontes = [
        {
            "chave": "cadastro_1t",
            "descricao": "Eleitorado por local de votação, 1º turno (TSE, arquivo de 02/10/2026)",
            **metadados(ZIP_1T, t1, SHA_1T),
        },
        {
            "chave": "cadastro_2t",
            "descricao": "Eleitorado por local de votação, linhas do 2º turno "
            "(TSE, arquivo de 18/10/2026)",
            **metadados(ZIP_2T, t2, SHA_2T),
        },
    ]
    return t1, t2, fontes
