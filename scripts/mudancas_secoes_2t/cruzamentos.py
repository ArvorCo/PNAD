"""Cruzamentos de leitura: urna do 1º turno, logs, mapa de fiscais, Politize e 2022.

Tudo é somente leitura. Unidade: a urna (seção principal); seção agregada vota na
urna da principal e não tem boletim próprio.
"""

from __future__ import annotations

import gzip
import json
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2026.secoes_base import fusos_por_municipio

ROOT = Path(__file__).resolve().parents[2]
BU = ROOT / "apuracao/data/secoes_2026.sqlite"
LOGS = ROOT / "data/outputs/logs_urnas_2026.sqlite"
FISCAIS = ROOT / "docs/assets/fiscais_mapa"
POLITIZE_ZONA = ROOT / "docs/assets/politize/dados/zona"
CSV_2022 = ROOT / "data/outputs/presidente_secao_2022.csv.gz"
CHAVE = ["uf", "mun", "zona", "secao"]
FLAVIO, LULA = 22, 13
ABERTURA_ATRASADA_MIN = 8 * 60 + 30
FILA_MIN = 18 * 60


def _ro(caminho: Path) -> sqlite3.Connection:
    if not caminho.exists():
        raise FileNotFoundError(caminho)
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def _minutos_brasilia(texto: pd.Series, fuso: pd.Series) -> pd.Series:
    """Hora local do boletim convertida para minutos do dia em Brasília."""
    local = pd.to_datetime(texto, errors="coerce")
    t = local + pd.to_timedelta(fuso, unit="h")
    m = (t.dt.hour * 60 + t.dt.minute + t.dt.second / 60).astype(float)
    # votação de um dia só: hora que passa da meia-noite não entra
    return m.where(t.dt.day == local.dt.day)


def ler_urnas() -> tuple[pd.DataFrame, dict[str, int]]:
    """Uma linha por boletim: aptos, comparecimento, votos de presidente e horários.

    Devolve também os totais nacionais de presidente somados direto de ``voto_secao``
    (todas as seções, Brasil e exterior), referência dos cenários.
    """
    con = _ro(BU)
    try:
        votos = pd.read_sql(
            "SELECT uf, mun, zona, secao,"
            f" SUM(CASE WHEN tipo=1 AND numero={FLAVIO} THEN votos ELSE 0 END) flavio,"
            f" SUM(CASE WHEN tipo=1 AND numero={LULA} THEN votos ELSE 0 END) lula,"
            f" SUM(CASE WHEN tipo=1 AND numero NOT IN ({FLAVIO},{LULA}) THEN votos ELSE 0 END)"
            " terceira,"
            " SUM(CASE WHEN tipo=2 THEN votos ELSE 0 END) brancos,"
            " SUM(CASE WHEN tipo=3 THEN votos ELSE 0 END) nulos,"
            " SUM(CASE WHEN tipo NOT IN (1,2,3) THEN votos ELSE 0 END) outros_tipos"
            " FROM voto_secao WHERE cargo=1 GROUP BY uf, mun, zona, secao",
            con,
        )
        cargo = pd.read_sql(
            "SELECT uf, mun, zona, secao, aptos, comparecimento FROM bu_cargo WHERE cargo=1",
            con,
        )
        bu = pd.read_sql(
            "SELECT uf, mun, zona, secao, modelo_urna, tipo_urna, abertura, encerramento"
            " FROM bu",
            con,
        )
    finally:
        con.close()
    totais = {
        "validos": int(
            votos["flavio"].sum() + votos["lula"].sum() + votos["terceira"].sum()
        ),
        "flavio": int(votos["flavio"].sum()),
        "lula": int(votos["lula"].sum()),
        "brancos": int(votos["brancos"].sum()),
        "nulos": int(votos["nulos"].sum()),
        "secoes_com_voto": len(votos),
    }
    bu["fuso"] = fusos_por_municipio(bu)
    bu["abertura_min"] = _minutos_brasilia(bu["abertura"], bu["fuso"])
    bu["encerramento_min"] = _minutos_brasilia(bu["encerramento"], bu["fuso"])
    df = bu.drop(columns=["abertura", "encerramento"]).merge(
        cargo, on=CHAVE, how="left"
    )
    df = df.merge(votos, on=CHAVE, how="left")
    df["uf"] = df["uf"].str.upper()
    for c in ("flavio", "lula", "terceira", "brancos", "nulos", "outros_tipos"):
        df[c] = df[c].fillna(0).astype("int64")
    df["validos"] = df["flavio"] + df["lula"] + df["terceira"]
    hora = df["abertura_min"].notna()
    df["hora_ok"] = hora
    df["abertura_atrasada"] = hora & (df["abertura_min"] >= ABERTURA_ATRASADA_MIN)
    fim = df["encerramento_min"].notna()
    df["fim_ok"] = fim
    df["fila_fechamento"] = fim & (df["encerramento_min"] > FILA_MIN)
    return df, totais


def ler_logs() -> pd.DataFrame:
    """Bateria, bateria durante a votação e reinício, do resumo de cada log."""
    con = _ro(LOGS)
    try:
        df = pd.read_sql(
            "SELECT uf, mun, zona, secao, status,"
            " COALESCE(json_extract(resumo, '$.contagens.eventos_bateria'), 0) bat,"
            " COALESCE(json_extract(resumo, '$.bateria_fases.votacao'), 0) bat_vot,"
            " COALESCE(json_extract(resumo, '$.contagens.reinicios_durante_votacao'), 0) rein,"
            " json_extract(resumo, '$.tempos_validos') tempos_validos"
            " FROM metricas",
            con,
        )
    finally:
        con.close()
    df["uf"] = df["uf"].str.upper()
    df["log_ok"] = df["status"] == "ok"
    df["bateria"] = df["log_ok"] & (df["bat"] > 0)
    df["bateria_votacao"] = df["log_ok"] & (df["bat_vot"] > 0)
    df["reinicio"] = df["log_ok"] & (df["rein"] > 0)
    df["relogio_ok"] = df["log_ok"] & (df["tempos_validos"] == 1)
    return df[
        [*CHAVE, "log_ok", "relogio_ok", "bateria", "bateria_votacao", "reinicio"]
    ]


def ler_atencao() -> pd.DataFrame:
    """Nível de atenção (0 a 3) e códigos de log do mapa de fiscais, por seção."""
    indice = json.loads((FISCAIS / "indice.json").read_text(encoding="utf-8"))
    cols_l = indice["colunas_locais"]
    cols_s = indice["colunas_secoes"]
    il_mun, il_zona = cols_l.index("mun"), cols_l.index("zona")
    is_li, is_sec = cols_s.index("li"), cols_s.index("secao")
    is_at, is_logs = cols_s.index("atencao"), cols_s.index("logs")
    linhas: list[tuple[Any, ...]] = []
    for uf, parte in indice["partes"].items():
        d = json.loads((FISCAIS / parte["arquivo"]).read_text(encoding="utf-8"))
        locais = d["locais"]
        for s in d["secoes"]:
            loc = locais[s[is_li]]
            linhas.append(
                (
                    uf,
                    str(loc[il_mun]).zfill(5),
                    int(loc[il_zona]),
                    int(s[is_sec]),
                    0 if s[is_at] is None else int(s[is_at]),
                    list(s[is_logs] or []),
                )
            )
    df = pd.DataFrame(linhas, columns=[*CHAVE, "atencao", "codigos"])
    return df.drop_duplicates(CHAVE)


def ler_2022() -> pd.DataFrame:
    """Seção de 2022: local, nome do local, aptos e comparecimento nos dois turnos.

    O 2º turno vem da mesma fonte que o Politize lê (``politize.fontes.ler_2022_2t``,
    detalhe de votação por seção do TSE), com o cache do Politize.
    """
    from politize.fontes import ler_2022_2t

    with gzip.open(CSV_2022, "rt", encoding="utf-8") as f:
        d = pd.read_csv(
            f,
            usecols=[
                "uf",
                "mun",
                "zona",
                "secao",
                "local_2022",
                "local_nr_2022",
                "aptos_2022",
                "comparecimento_2022",
            ],
            dtype={"mun": str, "uf": str},
        )
    d["uf"] = d["uf"].str.upper()
    d["mun"] = d["mun"].str.zfill(5)
    segundo = ler_2022_2t()
    linhas = [
        (uf, *k.split("|"), v[0], v[1])
        for uf, secs in segundo.items()
        for k, v in secs.items()
    ]
    t2 = pd.DataFrame(linhas, columns=[*CHAVE, "aptos_2022_2t", "comp_2022_2t"])
    t2["zona"] = t2["zona"].astype("int64")
    t2["secao"] = t2["secao"].astype("int64")
    d = d.merge(t2, on=CHAVE, how="outer")
    d = d.rename(
        columns={"aptos_2022": "aptos_2022_1t", "comparecimento_2022": "comp_2022_1t"}
    )
    return d


def conferir_politize(
    urnas: pd.DataFrame, zonas: set[tuple[str, int]]
) -> dict[str, Any]:
    """Confere aptos e votos das urnas com mudança contra os fragmentos do Politize."""
    alvo = {
        (str(r["uf"]), str(r["mun"]), int(r["zona"]), int(r["secao"])): r
        for r in urnas[[*CHAVE, "aptos", "flavio", "lula"]].to_dict("records")
    }
    lidas = iguais = diferentes = ausentes = ocultos = 0
    exemplos: list[dict[str, Any]] = []
    for uf, zona in sorted(zonas):
        arq = POLITIZE_ZONA / uf / f"{zona}.json"
        if not arq.exists():
            continue
        tab = json.loads(arq.read_text(encoding="utf-8"))["secoes"]
        cols = tab["colunas"]
        ix = {c: cols.index(c) for c in ("secao", "mun_tse", "aptos", "flavio", "lula")}
        for linha in tab["linhas"]:
            chave = (
                uf,
                str(linha[ix["mun_tse"]]).zfill(5),
                int(zona),
                int(linha[ix["secao"]]),
            )
            r = alvo.get(chave)
            if r is None:
                ausentes += 1
                continue
            lidas += 1
            par = [(linha[ix[c]], r[c]) for c in ("aptos", "flavio", "lula")]
            if any(a is None for a, _ in par):
                ocultos += 1
            if all(
                int(a) == int(b) for a, b in par if a is not None and not pd.isna(b)
            ):
                iguais += 1
            else:
                diferentes += 1
                if len(exemplos) < 10:
                    exemplos.append(
                        {
                            "chave": list(map(str, chave)),
                            "politize": [a for a, _ in par],
                            "motor": [None if pd.isna(b) else int(b) for _, b in par],
                        }
                    )
    return {
        "zonas_lidas": len(zonas),
        "secoes_conferidas": lidas,
        "iguais": iguais,
        "diferentes": diferentes,
        "fora_do_motor": ausentes,
        "voto_oculto_no_politize": ocultos,
        "nota": "o Politize não mostra voto de seção com menos de 30 aptos; nessas, só os "
        "aptos são conferidos",
        "exemplos_diferentes": exemplos,
    }


def montar_urnas(cls: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Urna (seção principal) com classificação, votos, logs, atenção e 2022."""
    princ = cls.loc[~cls["agregada"]].copy()
    soma = cls.groupby(["uf", "mun", "zona", "urna"])["eleitores_2t"].sum()
    eleitores = soma.reset_index().rename(
        columns={"urna": "secao", "eleitores_2t": "eleitores_urna"}
    )
    princ = princ.merge(eleitores, on=CHAVE, how="left")
    urnas, totais = ler_urnas()
    df = princ.merge(urnas, on=CHAVE, how="left", indicator="_bu")
    df["tem_bu"] = (df["_bu"] == "both") & df["aptos"].notna() & (df["aptos"] > 0)
    df = df.drop(columns="_bu")
    df = df.merge(ler_logs(), on=CHAVE, how="left")
    for c in ("log_ok", "relogio_ok", "bateria", "bateria_votacao", "reinicio"):
        df[c] = df[c].eq(True)
    at = ler_atencao()
    df = df.merge(at, on=CHAVE, how="left")
    df["atencao"] = np.where(df["log_ok"], df["atencao"].fillna(0), np.nan)
    df["codigos"] = df["codigos"].apply(lambda x: x if isinstance(x, list) else [])
    df["atencao_23"] = df["atencao"] >= 2
    df = df.merge(ler_2022(), on=CHAVE, how="left")
    totais["validos_nas_urnas_do_cadastro"] = int(df["validos"].fillna(0).sum())
    return df, totais
