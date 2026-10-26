"""Leitura somente leitura das três fontes de metadados das urnas por seção.

1. BU (`apuracao/data/secoes_2026.sqlite` e `secoes_2t_2026.sqlite`): número interno
   da urna, carga (código, data, mídia FC, gerador da mídia), flash de votação (FV),
   versão do software de votação, tipo de urna e de arquivo, horários e votos.
2. `.vsc` (`apuracao/data/vsc_2t_2026.sqlite`, coleta de `apuracao/scripts/vsc-coletar.ts`):
   certificado de hardware da urna, cadeia até a AC, assinaturas e lista de arquivos.
3. Logs processados do 2º turno (`data/outputs/logs_urnas_2t_2026.sqlite`, tabela
   `metricas`, coluna `resumo` em JSON do `scripts/apuracao_logs/parser.py`): urnas do
   log, códigos de carga, mídias de carga e `metadados_urna` (versão da aplicação,
   série da MR, computador e data da mídia). Ausente ou parcial: as colunas ficam nulas
   e o relatório diz quanto foi coberto.

Todos os bancos abrem com `mode=ro`: as coletas podem estar escrevendo.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from .base import APURACAO, ROOT
from .urnas_base import BANCO_1T, BANCO_2T, CHAVE, abrir, ler, ler_com_cache

BANCO_VSC = APURACAO / "data/vsc_2t_2026.sqlite"
BANCO_LOGS_2T = ROOT / "data/outputs/logs_urnas_2t_2026.sqlite"

EXTRA_BU = (
    "b.uf,b.mun,b.zona,b.secao,b.numero_serie_fc,b.numero_serie_fv,b.gerador_midia,"
    "b.versao_votacao,b.gerado_em,s.nsp,s.nsa"
)
COLUNAS_VSC = (
    "uf",
    "mun",
    "zona",
    "secao",
    "status",
    "hash",
    "mesmo_hash_bu",
    "origem",
    "sha256",
    "sw_serial",
    "sw_chave_data",
    "sw_resumo_ok",
    "hw_criado_em",
    "hw_usuario",
    "hw_serial",
    "hw_algoritmo",
    "hw_resumo_ok",
    "modelo_codigo",
    "algoritmo_hw_codigo",
    "listas_ok",
    "n_arquivos",
    "cert_formato",
    "cert_sha256",
    "cert_serial",
    "cert_emissor_cn",
    "cert_titular_cn",
    "cert_validade_inicio",
    "cert_validade_fim",
    "cert_chave_sha256",
    "cadeia_valida",
    "ac",
    "cadeia_motivo",
    "erro_certificado",
    "cn_confere_usuario",
    "hw_assinatura_ok",
    "hw_bu_assinatura_ok",
    "bu_confere_vsc",
)
COLUNAS_LOG = (
    "log_status",
    "log_ids",
    "log_cargas",
    "log_midias",
    "log_versao",
    "log_serie_mr",
    "log_serie_mr_dia",
    "log_midia_votacao_computador",
    "log_carga_por_urna",
    "log_reinicios_votacao",
    "log_partidas_vota",
    "log_urna_bu_no_log",
    "log_carga_bu_no_log",
    "log_outras_urnas",
    "log_midia_computador",
    "log_midia_gerada_em",
    "log_carga_registrada_em",
)


def ler_bu(banco: Path, turno: str, usar_cache: bool = True) -> pd.DataFrame:
    """BU com votos (de `urnas_base`) e os campos de mídia e versão."""
    dados = ler_com_cache(banco, turno, usar_cache) if turno == "1t" else ler(banco)
    con = abrir(banco)
    try:
        extra = pd.read_sql(
            f"SELECT {EXTRA_BU} FROM bu b JOIN secao s USING(uf,mun,zona,secao)", con
        )
    finally:
        con.close()
    df = dados["bu"].merge(extra, on=CHAVE, how="left")
    df.attrs["secoes_principais"] = dados["secoes_principais"]
    df.attrs["secoes_catalogo"] = dados["secoes_catalogo"]
    return df


def _vazio(colunas) -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in colunas})


def ler_vsc(banco: Path, turno: int) -> tuple[pd.DataFrame, dict]:
    """Linhas do `.vsc` de um turno e a contagem por status. Banco ausente: vazio."""
    if not banco.exists():
        return _vazio(COLUNAS_VSC), {"banco": "ausente"}
    con = sqlite3.connect(f"file:{banco}?mode=ro", uri=True, timeout=30)
    try:
        con.execute("PRAGMA query_only=1")
        df = pd.read_sql(
            f"SELECT {','.join(COLUNAS_VSC)} FROM vsc WHERE turno = ?",
            con,
            params=(turno,),
        )
        arq = con.execute(
            "SELECT COUNT(*), SUM(nome_confere = 0) FROM vsc_arquivo WHERE turno = ?",
            (turno,),
        ).fetchone()
    finally:
        con.close()
    status = {str(k): int(v) for k, v in df.status.value_counts().items()}
    return df, {
        "status": status,
        "arquivos_listados": int(arq[0] or 0),
        "arquivos_com_nome_de_outra_secao": int(arq[1] or 0),
    }


def _conjunto(valor) -> list[str]:
    if valor is None:
        return []
    obj = json.loads(valor) if isinstance(valor, str) else valor
    if isinstance(obj, dict):
        return sorted({str(x) for v in obj.values() for x in (v or [])})
    if isinstance(obj, list):
        return sorted({str(x) for x in obj})
    return [str(obj)]


def _meta(valor, campo: str) -> list[str]:
    if valor is None:
        return []
    obj = json.loads(valor)
    saida = set()
    for meta in (obj or {}).values():
        v = (meta or {}).get(campo)
        if v is None:
            continue
        saida.update(str(x) for x in (v if isinstance(v, list) else [v]))
    return sorted(saida)


def _carga_por_urna(valor) -> dict[int, str]:
    """{número interno da urna: data e hora da carga registrada no log (dd/mm/aaaa hh:mm:ss)}."""
    if valor is None:
        return {}
    saida = {}
    for urna, meta in (json.loads(valor) or {}).items():
        v = (meta or {}).get("carga_registrada_em")
        if isinstance(v, list):
            v = min(v) if v else None
        if v and str(urna).isdigit():
            saida[int(urna)] = str(v)
    return saida


def ler_logs(banco: Path) -> tuple[pd.DataFrame, dict]:
    """Metadados do log processado do 2º turno; tolerante à ausência do banco e das chaves."""
    if not banco.exists():
        return _vazio((*CHAVE, *COLUNAS_LOG)), {"banco": "ausente", "secoes": 0}
    con = sqlite3.connect(f"file:{banco}?mode=ro", uri=True, timeout=30)
    try:
        con.execute("PRAGMA query_only=1")
        tabelas = {r[0] for r in con.execute("SELECT name FROM sqlite_master")}
        if "metricas" not in tabelas:
            return _vazio((*CHAVE, *COLUNAS_LOG)), {"banco": "sem tabela metricas"}
        bruto = pd.read_sql(
            "SELECT uf,mun,zona,secao,status AS log_status,"
            "json_extract(resumo,'$.urnas_log') AS u,"
            "json_extract(resumo,'$.cargas_log') AS c,"
            "json_extract(resumo,'$.midias_log') AS m,"
            "json_extract(resumo,'$.metadados_urna') AS meta,"
            "json_extract(resumo,'$.contagens.reinicios_durante_votacao') AS reinicios,"
            "json_extract(resumo,'$.contagens.partidas_vota') AS partidas,"
            "json_extract(resumo,'$.identidade_log.urna_bu_no_log') AS urna_bu,"
            "json_extract(resumo,'$.identidade_log.carga_bu_no_log') AS carga_bu,"
            "json_array_length(resumo,'$.identidade_log.outras_urnas_no_log') AS outras "
            "FROM metricas",
            con,
        )
    finally:
        con.close()
    df = bruto[[*CHAVE, "log_status"]].copy()
    # `log_ids`, e não `log_urnas`: o banco dos BUs já tem a coluna `log_urnas`
    df["log_ids"] = bruto.u.map(_conjunto)
    df["log_cargas"] = bruto.c.map(_conjunto)
    df["log_midias"] = bruto.m.map(lambda v: [x.upper() for x in _conjunto(v)])
    for campo, coluna in (
        ("versao_aplicacao", "log_versao"),
        ("serie_mr", "log_serie_mr"),
        ("serie_mr_dia", "log_serie_mr_dia"),
        ("midia_votacao_computador_dia", "log_midia_votacao_computador"),
        ("midia_carga_computador", "log_midia_computador"),
        ("midia_carga_gerada_em", "log_midia_gerada_em"),
        ("carga_registrada_em", "log_carga_registrada_em"),
    ):
        df[coluna] = bruto.meta.map(lambda v, c=campo: _meta(v, c))
    df["log_carga_por_urna"] = bruto.meta.map(_carga_por_urna)
    df["log_reinicios_votacao"] = bruto.reinicios
    df["log_partidas_vota"] = bruto.partidas
    df["log_urna_bu_no_log"] = bruto.urna_bu
    df["log_carga_bu_no_log"] = bruto.carga_bu
    df["log_outras_urnas"] = bruto.outras
    com_meta = int(bruto.meta.notna().sum())
    return df, {
        "banco": (
            str(banco.relative_to(ROOT)) if banco.is_relative_to(ROOT) else str(banco)
        ),
        "secoes": len(df),
        "com_metadados_urna": com_meta,
        "com_cargas_log": int(bruto.c.notna().sum()),
    }


__all__ = [
    "BANCO_1T",
    "BANCO_2T",
    "BANCO_LOGS_2T",
    "BANCO_VSC",
    "ler_bu",
    "ler_logs",
    "ler_vsc",
]
