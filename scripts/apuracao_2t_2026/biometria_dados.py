"""Leitura das categorias de habilitação do BU, 1º e 2º turno (somente leitura).

O BU traz, para cada seção, quantos eleitores foram habilitados por biometria
(``hab_biometria``), por ano de nascimento (``hab_ano_nascimento``: biometria
cadastrada que o leitor não reconheceu, liberada pela data de nascimento) e sem
biometria cadastrada (``comp_sem_biometria``: eleitor que nunca coletou
biometria). As três somam o comparecimento. O BU do exterior e o do sistema de
apuração não publicam as categorias.

Bancos: ``apuracao/data/secoes_2026.sqlite`` (1º turno) e
``apuracao/data/secoes_2t_2026.sqlite`` (2º turno), tabelas ``bu`` e
``voto_secao`` (``apuracao/scripts/secoes/banco.ts``).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

FLAVIO, LULA = 22, 13
CHAVE = ["uf", "mun", "zona", "secao"]


def conectar(caminho: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def ler_turno(caminho: Path) -> pd.DataFrame:
    """Uma linha por BU: categorias, modelo da urna, tipo de arquivo e votos F/L."""
    with conectar(caminho) as con:
        bu = pd.read_sql_query(
            "SELECT uf, mun, zona, secao, modelo_urna, tipo_arquivo, tipo_urna, aptos, "
            "comparecimento AS comp, hab_biometria AS bio, hab_ano_nascimento AS ano, "
            "comp_sem_biometria AS sem FROM bu",
            con,
        )
        v = pd.read_sql_query(
            "SELECT uf, mun, zona, secao, numero, votos FROM voto_secao "
            "WHERE cargo = 1 AND tipo = 1 AND numero IN (?, ?)",
            con,
            params=(FLAVIO, LULA),
        )
    piv = v.pivot_table(index=CHAVE, columns="numero", values="votos", aggfunc="sum")
    piv = piv.reindex(columns=[FLAVIO, LULA]).fillna(0)
    piv.columns = ["fl", "lu"]
    df = bu.merge(piv.reset_index(), on=CHAVE, how="left")
    df[["fl", "lu"]] = df[["fl", "lu"]].fillna(0)
    df["uf"] = df["uf"].str.upper()
    df["mun"] = df["mun"].astype(str).str.zfill(5)
    return df


def exterior_log(caminho: Path) -> dict[str, int] | None:
    """Habilitações do exterior pelo log das urnas (o BU do exterior não as publica)."""
    if not caminho.exists():
        return None
    q = (
        "SELECT COUNT(*), "
        + ", ".join(
            f"COALESCE(SUM(json_extract(resumo, '$.tipos_habilitacao_computados.{k}')), 0)"
            for k in ("biometrica", "biografica", "sem_biometria")
        )
        + " FROM metricas WHERE uf IN ('zz', 'ZZ')"
    )
    with conectar(caminho) as con:
        n, bio, ano, sem = con.execute(q).fetchone()
    return {
        "urnas_com_log": int(n),
        "biometrica": int(bio),
        "biografica": int(ano),
        "sem_biometria": int(sem),
    }
