"""Variáveis de clima por célula, por urna e por local de votação.

Relógio: a Open-Meteo devolve as horas de 04/10 no relógio de Brasília
(``timezone=America/Sao_Paulo``, UTC-3 sem horário de verão). A votação de 2026 foi das
8h às 17h de Brasília no país inteiro: no Acre e no oeste do Amazonas, das 6h às 15h
locais; no resto do Amazonas, MT, MS, RO e RR, das 7h às 16h locais. A janela de
votação com uma hora de folga de cada lado (7h às 18h de Brasília) é, portanto, a mesma
fatia da série horária para todo o país; o fuso só entra para escrever a hora local
(``hora_pico_chuva``) e para converter a hora do primeiro voto do boletim.

Convenção da série horária: o valor da hora H soma a chuva (ou dá a rajada máxima)
da hora anterior, de H-1 a H. A janela 7h às 18h usa as horas 8 a 18.
"""

from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2026.secoes_base import FUSO_UF
from clima_1t import grade

ROOT = Path(__file__).resolve().parents[2]
CONSOLIDADO = ROOT / "analysis/clima_1t_2026/celulas_archive.json"
CHAVE = ["uf", "mun", "zona", "secao"]

JANELA_BRASILIA = (7, 18)  # início e fim, horas cheias de Brasília
JANELA_ESTRITA = (8, 17)  # horário oficial de votação, sem folga

FAIXAS_CHUVA = ("seca", "fraca", "moderada", "forte", "muito_forte")
FAIXAS_RAJADA = ("ate_40", "40_60", "60_80", "acima_80")
ROTULO_CHUVA = {
    "seca": "seca (0 mm)",
    "fraca": "fraca (até 5 mm)",
    "moderada": "moderada (5 a 20 mm)",
    "forte": "forte (20 a 50 mm)",
    "muito_forte": "muito forte (acima de 50 mm)",
}
ROTULO_RAJADA = {
    "ate_40": "até 40 km/h",
    "40_60": "40 a 60 km/h",
    "60_80": "60 a 80 km/h",
    "acima_80": "acima de 80 km/h",
}


def faixa_chuva(mm: float | None) -> str | None:
    """Faixa da chuva: seca é zero na precisão publicada (0,1 mm)."""
    if mm is None or (isinstance(mm, float) and math.isnan(mm)):
        return None
    if mm < 0.05:
        return "seca"
    if mm <= 5:
        return "fraca"
    if mm <= 20:
        return "moderada"
    if mm <= 50:
        return "forte"
    return "muito_forte"


def faixa_rajada(kmh: float | None) -> str | None:
    if kmh is None or (isinstance(kmh, float) and math.isnan(kmh)):
        return None
    if kmh <= 40:
        return "ate_40"
    if kmh <= 60:
        return "40_60"
    if kmh <= 80:
        return "60_80"
    return "acima_80"


def horas_da_janela(ini: int, fim: int) -> list[int]:
    """Horas cheias da série (fim do intervalo) que cobrem ``ini`` a ``fim``."""
    return list(range(ini + 1, fim + 1))


def janela_local(
    fuso_h: float, ini: int = JANELA_BRASILIA[0], fim: int = JANELA_BRASILIA[1]
):
    """Janela de Brasília escrita na hora local (fuso = horas a somar ao local)."""
    return ini - fuso_h, fim - fuso_h


def soma_janela(
    serie_brasilia: Sequence[float | None], ini: int, fim: int
) -> float | None:
    """Soma das horas ``ini`` a ``fim`` de Brasília; ``None`` se faltar alguma hora."""
    vals = [serie_brasilia[h] for h in horas_da_janela(ini, fim)]
    numeros = [float(v) for v in vals if v is not None]
    if len(numeros) < len(vals):
        return None
    return round(sum(numeros), 2)


def maximo_janela(
    serie_brasilia: Sequence[float | None], ini: int, fim: int
) -> float | None:
    vals = [serie_brasilia[h] for h in horas_da_janela(ini, fim)]
    numeros = [float(v) for v in vals if v is not None]
    if len(numeros) < len(vals):
        return None
    return max(numeros)


def pico_brasilia(
    serie_brasilia: Sequence[float | None], ini: int, fim: int
) -> int | None:
    """Hora de início (Brasília) do intervalo com mais chuva na janela; ``None`` se seca."""
    melhor, hora = 0.0, None
    for h in horas_da_janela(ini, fim):
        v = serie_brasilia[h]
        if v is not None and v > melhor:
            melhor, hora = v, h - 1
    return hora


def hora_local(hora_brasilia: int | None, fuso_h: float | None) -> int | None:
    """Hora local a partir da de Brasília (fuso = horas a somar ao local)."""
    if (
        hora_brasilia is None
        or fuso_h is None
        or (isinstance(fuso_h, float) and math.isnan(fuso_h))
    ):
        return None
    return int((hora_brasilia - fuso_h) % 24)


def ler_consolidado(caminho: Path = CONSOLIDADO) -> dict[str, Any]:
    return json.loads(caminho.read_text())


def clima_por_celula(doc: dict[str, Any]) -> pd.DataFrame:
    """Uma linha por célula de 0,25° com as variáveis do contrato."""
    dias = doc["dias"]
    horas = [int(h) for h in doc["horas_04_10"]]
    if horas != list(range(24)):
        raise RuntimeError("série horária de 04/10 sem as 24 horas")
    diarias = doc["formato"]["diarias"]
    horarias = doc["formato"]["horarias"]
    i4, i3 = dias.index("2026-10-04"), dias.index("2026-10-03")
    jc = diarias.index("precipitation_sum")
    jr = diarias.index("wind_gusts_10m_max")
    jh = diarias.index("precipitation_hours")
    hc, hr = horarias.index("precipitation"), horarias.index("wind_gusts_10m")
    linhas = []
    for cel, (g, d, h) in doc["celulas"].items():
        chuva = d[jc]
        ini, fim = JANELA_BRASILIA
        e_ini, e_fim = JANELA_ESTRITA
        validos = [x for x in chuva if x is not None]
        linhas.append(
            {
                "cel": cel,
                "lat_grade": g[0],
                "lon_grade": g[1],
                "elevacao_m": g[2],
                "chuva_04_10_mm": chuva[i4],
                "chuva_03_10_mm": chuva[i3],
                "chuva_02a05_max_mm": max(validos) if validos else None,
                "horas_chuva_04_10": d[jh][i4],
                "rajada_04_10_kmh": d[jr][i4],
                "chuva_votacao_mm": soma_janela(h[hc], ini, fim),
                "chuva_votacao_estrita_mm": soma_janela(h[hc], e_ini, e_fim),
                "rajada_votacao_kmh": maximo_janela(h[hr], ini, fim),
                "pico_brasilia": pico_brasilia(h[hc], ini, fim),
            }
        )
    df = pd.DataFrame(linhas).set_index("cel")
    df["faixa_chuva"] = df["chuva_04_10_mm"].map(faixa_chuva)
    df["faixa_chuva_votacao"] = df["chuva_votacao_mm"].map(faixa_chuva)
    df["faixa_rajada"] = df["rajada_04_10_kmh"].map(faixa_rajada)
    df["faixa_rajada_votacao"] = df["rajada_votacao_kmh"].map(faixa_rajada)
    return df


def ler_secao_local(caminho: Path = grade.LOCAIS_DB) -> pd.DataFrame:
    """Seção do cadastro -> número do local (a seção agregada aponta o mesmo prédio)."""
    with sqlite3.connect(f"file:{caminho}?mode=ro", uri=True) as con:
        df = pd.read_sql(
            "SELECT uf, municipio_cd AS mun, zona, secao, local_nr FROM secao", con
        )
    df["zona"] = df["zona"].astype("int64")
    df["secao"] = df["secao"].astype("int64")
    return df


def montar_urnas(
    clima: pd.DataFrame, locais: list[grade.Local], fontes: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Uma linha por urna (boletim do 1º turno no Brasil) com clima, logs e 2022.

    ``fontes`` traz ``urnas``, ``logs``, ``atencao`` e ``t2022`` já lidos.
    """
    u = fontes["urnas"]
    u = u.loc[u["uf"] != "ZZ"].copy()
    sl = ler_secao_local()
    u = u.merge(sl, on=CHAVE, how="left")
    u["local_id"] = [
        None if pd.isna(nr) else grade.local_id(uf, mun, z, nr)
        for uf, mun, z, nr in zip(
            u["uf"], u["mun"], u["zona"], u["local_nr"], strict=True
        )
    ]
    cel_do_local = {
        lc.local_id: grade.chave(lc.lat, lc.lon, grade.PASSO_ARCHIVE)
        for lc in locais
        if lc.lat is not None and lc.lon is not None
    }
    u["cel"] = [cel_do_local.get(i) for i in u["local_id"]]
    u = u.merge(fontes["logs"], on=CHAVE, how="left")
    for c in ("log_ok", "relogio_ok", "bateria", "bateria_votacao", "reinicio"):
        u[c] = u[c].eq(True)
    at = fontes["atencao"]
    u = u.merge(at[[*CHAVE, "codigos"]], on=CHAVE, how="left")
    cod = u["codigos"].apply(lambda x: x if isinstance(x, list) else [])
    u["bat_vot_local"] = cod.apply(lambda x: "bateria_votacao_local" in x)
    u["bat_vot_isolada"] = cod.apply(lambda x: "bateria_votacao_isolada" in x)
    u = u.drop(columns="codigos")
    t22 = fontes["t2022"][[*CHAVE, "aptos_2022_2t", "comp_2022_2t"]]
    u = u.merge(t22, on=CHAVE, how="left")
    ok22 = (u["aptos_2022_2t"] > 0) & u["comp_2022_2t"].notna() & (u["aptos"] > 0)
    u["casada_2022"] = ok22
    u["aptos22"] = np.where(ok22, u["aptos_2022_2t"], 0.0)
    u["comp22"] = np.where(ok22, u["comp_2022_2t"], 0.0)
    u["aptos_c"] = np.where(ok22, u["aptos"], 0.0)
    u["comp_c"] = np.where(ok22, u["comparecimento"], 0.0)
    u["aptos"] = u["aptos"].fillna(0).astype(float)
    u["comparecimento"] = u["comparecimento"].fillna(0).astype(float)
    u["abst"] = u["aptos"] - u["comparecimento"]
    with np.errstate(divide="ignore", invalid="ignore"):
        u["abst_pct"] = np.where(u["aptos"] > 0, 100 * u["abst"] / u["aptos"], np.nan)
        a22 = 100 * (u["aptos22"] - u["comp22"]) / u["aptos22"]
        a26 = 100 * (u["aptos_c"] - u["comp_c"]) / u["aptos_c"]
    u["abst22_pct"] = np.where(ok22, a22, np.nan)
    u["dif_abst_pp"] = np.where(ok22, a26 - a22, np.nan)
    u = u.join(clima, on="cel")
    u["tem_clima"] = u["chuva_04_10_mm"].notna()
    return u


def por_local(
    urnas: pd.DataFrame, locais: list[grade.Local], clima: pd.DataFrame
) -> pd.DataFrame:
    """Uma linha por local de votação do Brasil (com ou sem coordenada e boletim)."""
    u = urnas.loc[urnas["local_id"].notna()].copy()
    u["n"] = 1
    u["n_log"] = u["log_ok"].astype(int)
    u["n_relogio"] = u["relogio_ok"].astype(int)
    for c in (
        "bateria",
        "bateria_votacao",
        "reinicio",
        "bat_vot_local",
        "bat_vot_isolada",
    ):
        u[c] = u[c].astype(int)
    u["atrasada"] = u["abertura_atrasada"].eq(True).astype(int)
    soma = u.groupby("local_id").agg(
        urnas=("n", "sum"),
        urnas_log=("n_log", "sum"),
        urnas_relogio=("n_relogio", "sum"),
        urnas_bateria=("bateria", "sum"),
        urnas_bateria_votacao=("bateria_votacao", "sum"),
        urnas_bateria_simultanea=("bat_vot_local", "sum"),
        urnas_bateria_isolada=("bat_vot_isolada", "sum"),
        urnas_reinicio=("reinicio", "sum"),
        urnas_abertura_atrasada=("atrasada", "sum"),
        aptos=("aptos", "sum"),
        comparecimento=("comparecimento", "sum"),
        aptos_c=("aptos_c", "sum"),
        comp_c=("comp_c", "sum"),
        aptos22=("aptos22", "sum"),
        comp22=("comp22", "sum"),
        flavio_v=("flavio", "sum"),
        lula_v=("lula", "sum"),
        fuso=("fuso", "first"),
    )
    base = pd.DataFrame(
        [
            {
                "local_id": lc.local_id,
                "uf": lc.uf,
                "mun": lc.mun,
                "municipio": lc.municipio,
                "zona": lc.zona,
                "local_nr": lc.local_nr,
                "nome": lc.nome,
                "lat": lc.lat,
                "lon": lc.lon,
                "cel": (
                    grade.chave(lc.lat, lc.lon, grade.PASSO_ARCHIVE)
                    if lc.lat is not None and lc.lon is not None
                    else None
                ),
            }
            for lc in locais
        ]
    ).set_index("local_id")
    df = base.join(soma, how="left")
    for c in soma.columns:
        if c != "fuso":
            df[c] = df[c].fillna(0).astype("int64")
    with np.errstate(divide="ignore", invalid="ignore"):
        df["abst_pct"] = np.where(
            df["aptos"] > 0,
            100 * (df["aptos"] - df["comparecimento"]) / df["aptos"],
            np.nan,
        )
        df["abst22_pct"] = np.where(
            df["aptos22"] > 0,
            100 * (df["aptos22"] - df["comp22"]) / df["aptos22"],
            np.nan,
        )
        a26c = np.where(
            df["aptos_c"] > 0,
            100 * (df["aptos_c"] - df["comp_c"]) / df["aptos_c"],
            np.nan,
        )
    df["dif_abst_pp"] = a26c - df["abst22_pct"]
    padrao = df["uf"].str.lower().map(FUSO_UF).fillna(0.0)
    df["fuso"] = pd.to_numeric(df["fuso"], errors="coerce").fillna(padrao)
    df = df.join(clima, on="cel")
    df["hora_pico_chuva"] = [
        hora_local(None if pd.isna(p) else int(p), f)
        for p, f in zip(df["pico_brasilia"], df["fuso"], strict=True)
    ]
    return df.reset_index()
