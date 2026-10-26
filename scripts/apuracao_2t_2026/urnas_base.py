"""Leitura somente leitura dos BUs por seção (1º e 2º turnos) para o estudo das urnas.

Os dois bancos (`apuracao/data/secoes_2026.sqlite` e `secoes_2t_2026.sqlite`) são
abertos com `mode=ro` e `PRAGMA query_only`: o coletor do 2º turno pode estar
escrevendo enquanto este módulo lê. Horas do BU são locais da urna, sem fuso.

O 1º turno está encerrado; sua leitura (com a varredura de `voto_secao`) fica em
cache em `data/outputs/apuracao_2t_2026/`, invalidado por tamanho e data do banco.
"""

from __future__ import annotations

import pickle
import sqlite3
from pathlib import Path

import pandas as pd

from .base import APURACAO, CACHE

BANCO_1T = APURACAO / "data/secoes_2026.sqlite"
BANCO_2T = APURACAO / "data/secoes_2t_2026.sqlite"
NUM_LULA = 13
NUM_FLAVIO = 22
CHAVE = ["uf", "mun", "zona", "secao"]
CAMPOS_BU = (
    "b.uf,b.mun,b.zona,b.secao,b.local,b.modelo_urna,b.modelo_fonte,"
    "b.numero_interno_urna,b.tipo_urna,b.tipo_arquivo,b.n_cargas,b.carga_em,"
    "b.codigo_carga,b.abertura,b.encerramento,b.emissao,b.fase,b.pleito,b.aptos,"
    "b.comparecimento,b.log_urnas,b.id_confere,b.sa_junta,b.sa_motivo,"
    "s.bu_sha256,s.hash AS hash_transmissao"
)


def abrir(banco: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{banco}?mode=ro", uri=True, timeout=30)
    con.execute("PRAGMA query_only=1")
    return con


def ler(banco: Path) -> dict:
    """BUs, votos de presidente (Lula e Flávio) e o tamanho do catálogo de seções."""
    con = abrir(banco)
    try:
        bu = pd.read_sql(
            f"SELECT {CAMPOS_BU} FROM bu b JOIN secao s USING(uf,mun,zona,secao)", con
        )
        votos = pd.read_sql(
            "SELECT uf,mun,zona,secao,numero,votos FROM voto_secao "
            f"WHERE cargo=1 AND tipo=1 AND numero IN ({NUM_LULA},{NUM_FLAVIO})",
            con,
        )
        catalogo = con.execute(
            "SELECT COUNT(*), SUM(nsp IS NULL OR nsp=0 OR nsp=secao) FROM secao"
        ).fetchone()
    finally:
        con.close()
    largura = votos.pivot_table(
        index=CHAVE, columns="numero", values="votos", aggfunc="sum", fill_value=0
    ).reset_index()
    largura.columns = [
        {NUM_LULA: "lula", NUM_FLAVIO: "flavio"}.get(c, c) for c in largura.columns
    ]
    for c in ("lula", "flavio"):
        if c not in largura:
            largura[c] = 0
    df = bu.merge(largura[[*CHAVE, "lula", "flavio"]], on=CHAVE, how="left")
    df[["lula", "flavio"]] = df[["lula", "flavio"]].fillna(0).astype(int)
    return {
        "bu": df,
        "secoes_catalogo": int(catalogo[0] or 0),
        "secoes_principais": int(catalogo[1] or 0),
    }


def assinatura(banco: Path) -> str:
    st = banco.stat()
    wal = banco.with_name(banco.name + "-wal")
    extra = wal.stat().st_size if wal.exists() else 0
    return f"{st.st_size}:{st.st_mtime_ns}:{extra}"


def ler_com_cache(banco: Path, nome: str, usar_cache: bool = True) -> dict:
    """Cache só faz sentido para banco encerrado (o 1º turno)."""
    arquivo = CACHE / f"urnas_{nome}.pkl"
    sig = assinatura(banco)
    if usar_cache and arquivo.exists():
        with arquivo.open("rb") as f:
            salvo = pickle.load(f)
        if salvo.get("assinatura") == sig:
            return salvo["dados"]
    dados = ler(banco)
    if usar_cache:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        with arquivo.open("wb") as f:
            pickle.dump({"assinatura": sig, "dados": dados}, f)
    return dados
