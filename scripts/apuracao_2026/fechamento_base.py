"""Hora de encerramento e de recebimento por seção, 1º turno de 2026 e de 2022.

Duas réguas de hora, ambas em minutos depois das 17h de Brasília do dia da
eleição (a votação termina às 17h de Brasília no país inteiro; quem está na
fila recebe senha e vota depois):

- **encerramento** (só 2026): campo `dataHoraEncerramento` do boletim de urna,
  "término da aquisição do voto (último voto)" na especificação do TSE, gravado
  na hora local da urna e convertido para Brasília pelo fuso do município
  (`secoes_base.fusos_por_municipio`: hora local de abertura mais frequente);
- **recebimento** (2022 e 2026): hora em que o boletim chegou ao TSE, já em
  hora de Brasília nos dois anos (`dr/hr` do `aux.json` em 2026;
  `DT_RECEBIMENTO_BU_HOR_TSE`, "Hora TSE", nos dados abertos de 2022). É a
  única régua que existe nos dois anos e mede fila mais transporte da mídia.

Exterior fica fora: vota e transmite na hora local da cidade.

Leitura do banco da coleta: somente leitura, pela mesma montagem da análise por
seção (`secoes_base.montar`), mais as três contagens de habilitação do boletim
(biometria, ano de nascimento, sem biometria cadastrada). As funções puras
ficam no fim e são testadas sem banco.
"""

from __future__ import annotations

import hashlib
import json
import math
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import secoes_2022, secoes_base
from .dados import regiao

DIA_2026 = pd.Timestamp("2026-10-04 17:00:00")
DIA_2022 = pd.Timestamp("2022-10-02 17:00:00")
ABERTURA_2026 = pd.Timestamp("2026-10-04 08:00:00")
CORTES = (30, 60, 120)  # 17:30, 18:00 e 19:00 de Brasília
GRADE = tuple(range(0, 421, 10))  # 17:00 a 24:00, de dez em dez minutos
TOLERANCIA_RELOGIO = (
    5  # minutos: recebido antes do encerramento além disso é fuso errado
)
COBERTURA_UF = 0.99
COBERTURA_MUNICIPIO = 0.95
MIN_SECOES_MUNICIPIO = 3

# Faixas de eleitorado apto da seção (o tamanho que o TRE define antes da eleição).
FAIXAS_APTOS: list[tuple[str, int, int | None]] = [
    ("até 199", 0, 199),
    ("200 a 249", 200, 249),
    ("250 a 299", 250, 299),
    ("300 a 349", 300, 349),
    ("350 a 399", 350, 399),
    ("400 ou mais", 400, None),
]
# Faixas de hora de encerramento (minutos depois das 17h); a primeira fica vazia
# se nenhuma urna encerrar antes das 17h, como manda a regra.
FAIXAS_HORA: list[tuple[str, float, float]] = [
    ("até 17:00", -math.inf, 0),
    ("17:00 a 17:30", 0, 30),
    ("17:30 a 18:00", 30, 60),
    ("18:00 a 19:00", 60, 120),
    ("depois de 19:00", 120, math.inf),
]
RURAIS = {"zona rural", "assentamento", "quilombo"}
GRUPO_TIPO = {
    "aldeia ou terra indígena": "aldeia ou terra indígena",
    "zona rural": "zona rural, assentamento ou quilombo",
    "assentamento": "zona rural, assentamento ou quilombo",
    "quilombo": "zona rural, assentamento ou quilombo",
    "unidade prisional ou socioeducativa": "unidade prisional ou socioeducativa",
    "escola ou universidade": "escola fora de zona rural",
    "hospital ou unidade de saúde": "outro local",
    "voto em trânsito": "outro local",
    "outro": "outro local",
    "sem cadastro": "outro local",
}
ORDEM_TIPO = [
    "aldeia ou terra indígena",
    "zona rural, assentamento ou quilombo",
    "unidade prisional ou socioeducativa",
    "escola fora de zona rural",
    "outro local",
]

CHAVES = ["uf", "mun", "zona", "secao"]


# ---------------------------------------------------------------- 2026


def ler_habilitacao(secoes_db: Path) -> pd.DataFrame:
    """Contagens de habilitação do boletim (biometria, ano de nascimento, sem biometria)."""
    con = secoes_base.abrir_ro(secoes_db)
    try:
        return pd.read_sql(
            "SELECT uf, mun, zona, secao, comp_sem_biometria, hab_biometria, "
            "hab_ano_nascimento FROM bu",
            con,
        )
    finally:
        con.close()


def ler_principais(secoes_db: Path) -> pd.DataFrame:
    """Seções principais do cadastro (cs) e quantas já têm hora de recebimento."""
    con = secoes_base.abrir_ro(secoes_db)
    try:
        return pd.read_sql(
            "SELECT uf, mun, COUNT(*) AS principais, "
            "SUM(dr_hr IS NOT NULL) AS com_hora, "
            "SUM(log_sha256 IS NOT NULL) AS com_hash_log FROM secao "
            "WHERE nsp IS NULL GROUP BY uf, mun",
            con,
        )
    finally:
        con.close()


def montar_2026(secoes_db: Path, locais_db: Path, apuracao_db: Path) -> pd.DataFrame:
    """Uma linha por boletim de seção do Brasil (sem exterior), com as horas em minutos.

    `valida` marca as seções que entram nas contas de voto (as mesmas da análise
    por seção: zona conferida contra o arquivo do TSE). Horários usam todas as
    seções com boletim, porque a hora não depende da conferência de votos.
    """
    base = secoes_base.montar(secoes_db, locais_db, apuracao_db)
    validas = base.secoes.assign(valida=True)
    excl = base.excluidas.assign(valida=False)
    df = pd.concat([validas, excl], ignore_index=True)
    df = df[df["uf"] != "zz"].copy()
    hab = ler_habilitacao(secoes_db)
    df = df.merge(hab, on=CHAVES, how="left")
    return derivar(df)


def derivar(df: pd.DataFrame) -> pd.DataFrame:
    """Minutos depois das 17h (encerramento e recebimento), horas abertas e taxas."""
    fuso = pd.to_timedelta(df["fuso"].astype(float).fillna(0), unit="h")
    enc = pd.to_datetime(df["encerramento"], errors="coerce") + fuso
    abe = pd.to_datetime(df["abertura"], errors="coerce") + fuso
    rec = pd.to_datetime(df["dr_hr"], errors="coerce")
    df["enc_min"] = (enc - DIA_2026).dt.total_seconds() / 60
    df["abe_min"] = (abe - ABERTURA_2026).dt.total_seconds() / 60
    df["rec_min"] = (rec - DIA_2026).dt.total_seconds() / 60
    df["fuso_inconsistente"] = df["rec_min"] < df["enc_min"] - TOLERANCIA_RELOGIO
    df.loc[df["fuso_inconsistente"], ["enc_min", "abe_min"]] = np.nan
    horas = (df["enc_min"] + 540 - df["abe_min"]) / 60
    df["horas"] = horas.where(horas > 0)
    comp = df["comparecimento"].astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        df["votantes_hora"] = comp / df["horas"]
        df["ano_nascimento_pct"] = np.where(
            comp > 0, 100 * df["hab_ano_nascimento"] / comp, np.nan
        )
        df["sem_biometria_pct"] = np.where(
            comp > 0, 100 * df["comp_sem_biometria"] / comp, np.nan
        )
    df["regiao"] = df["uf"].map(regiao)
    df["faixa_aptos"] = faixa_aptos(df["aptos"])
    df["grupo_tipo"] = df["tipo_inferido"].map(GRUPO_TIPO).fillna("outro local")
    df["faixa_hora"] = faixa_hora(df["enc_min"])
    return df


# ---------------------------------------------------------------- 2022


def _sha(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def tipos_2022(zip_detalhe: Path, cache: Path) -> pd.DataFrame:
    """Tipo de local inferido de cada seção de 2022, lendo o detalhe em blocos.

    Mesmas regras de `secoes_base.REGRAS_LOCAL`, com o nome do local e o endereço
    de 2022 (o arquivo de 2022 não tem bairro). Cache com o SHA-256 do ZIP e das
    regras; refeito quando um dos dois muda.
    """
    regras = json.dumps(secoes_base.regras_local_json(), ensure_ascii=False)
    assinatura = {
        "zip": _sha(zip_detalhe),
        "regras": hashlib.sha256(regras.encode()).hexdigest(),
    }
    meta = cache.with_suffix(".json")
    if cache.exists() and meta.exists():
        try:
            if json.loads(meta.read_text(encoding="utf-8")) == assinatura:
                return pd.read_csv(cache, dtype={"uf": str, "mun": str})
        except (OSError, json.JSONDecodeError):
            pass
    usar = ["NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "CD_CARGO"]
    usar += ["NM_LOCAL_VOTACAO", "DS_LOCAL_VOTACAO_ENDERECO"]
    partes = []
    with (
        zipfile.ZipFile(zip_detalhe) as z,
        z.open(secoes_2022._membro(z, "detalhe_votacao_secao_2022_BR.csv")) as f,
    ):
        for bloco in pd.read_csv(
            f, sep=";", encoding="latin-1", usecols=usar, dtype=str, chunksize=200_000
        ):
            bloco = bloco[(bloco["CD_CARGO"] == "1") & (bloco["NR_TURNO"] == "1")]
            if bloco.empty:
                continue
            bloco = secoes_2022._chaves(bloco.copy())
            bloco["tipo_2022"] = [
                secoes_base.tipo_local(u.upper(), None, loc, None, end)
                for u, loc, end in zip(
                    bloco["uf"],
                    bloco["NM_LOCAL_VOTACAO"],
                    bloco["DS_LOCAL_VOTACAO_ENDERECO"],
                    strict=True,
                )
            ]
            partes.append(bloco[[*CHAVES, "tipo_2022"]])
    df = pd.concat(partes, ignore_index=True).drop_duplicates(CHAVES)
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False, compression="gzip")
    meta.write_text(json.dumps(assinatura), encoding="utf-8")
    return df


def montar_2022(s22: pd.DataFrame, tipos: pd.DataFrame | None) -> pd.DataFrame:
    """Seções de 2022 do Brasil com recebimento em minutos e tipo de local."""
    df = s22[(s22["uf"] != "zz") & (s22["nominais_1t"].fillna(0) > 0)].copy()
    rec = pd.to_datetime(
        df["recebido_2022"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
    )
    df["rec_min"] = (rec - DIA_2022).dt.total_seconds() / 60
    df["regiao"] = df["uf"].map(regiao)
    df["aptos"] = df["aptos_2022"]
    df["comparecimento"] = df["comparecimento_2022"]
    df["faixa_aptos"] = faixa_aptos(df["aptos"])
    if tipos is not None:
        df = df.merge(tipos, on=CHAVES, how="left")
    else:
        df["tipo_2022"] = None
    df["grupo_tipo"] = df["tipo_2022"].map(GRUPO_TIPO).fillna("outro local")
    return df


# ---------------------------------------------------------------- cobertura


def cobertura(
    d26: pd.DataFrame, principais: pd.DataFrame, d22: pd.DataFrame
) -> dict[str, Any]:
    """UFs completas em 2026 (hora de recebimento em 99% das seções principais)."""
    p = principais[principais["uf"] != "zz"]
    por_uf = p.groupby("uf")[["principais", "com_hora"]].sum()
    linhas = []
    completas, em_coleta, sem = [], [], []
    for uf, x in por_uf.iterrows():
        frac = x["com_hora"] / x["principais"] if x["principais"] else 0.0
        linhas.append(
            {
                "uf": str(uf).upper(),
                "principais": int(x["principais"]),
                "com_hora": int(x["com_hora"]),
                "pct": secoes_base.r2(100 * frac),
            }
        )
        if frac >= COBERTURA_UF:
            completas.append(str(uf).upper())
        elif x["com_hora"] > 0:
            em_coleta.append(str(uf).upper())
        else:
            sem.append(str(uf).upper())
    return {
        "parcial": bool(em_coleta or sem),
        "criterio_uf": (
            f"UF completa quando ao menos {int(100 * COBERTURA_UF)}% das seções "
            "principais do cadastro têm hora de recebimento na coleta"
        ),
        "ufs_completas": completas,
        "ufs_em_coleta": em_coleta,
        "ufs_sem_2026": sem,
        "por_uf": linhas,
        "secoes_2026": len(d26),
        "secoes_2026_validas_voto": int(d26["valida"].sum()),
        "secoes_2026_completas": int(d26["uf"].str.upper().isin(completas).sum()),
        "secoes_2022": len(d22),
        "secoes_2022_mesmas_ufs": int(d22["uf"].str.upper().isin(completas).sum()),
        "fuso_inconsistente": int(d26["fuso_inconsistente"].sum()),
        "sem_encerramento": int(d26["enc_min"].isna().sum()),
        "sem_recebimento_2026": int(d26["rec_min"].isna().sum()),
        "sem_recebimento_2022": int(d22["rec_min"].isna().sum()),
        "exterior": (
            "fora: o exterior vota na hora local da cidade e transmite por outro "
            "caminho"
        ),
    }


# ---------------------------------------------------------------- funções puras


def faixa_aptos(aptos: Iterable[Any]) -> list[str | None]:
    out: list[str | None] = []
    for a in aptos:
        if a is None or (isinstance(a, float) and math.isnan(a)):
            out.append(None)
            continue
        rot = None
        for nome, lo, hi in FAIXAS_APTOS:
            if a >= lo and (hi is None or a <= hi):
                rot = nome
                break
        out.append(rot)
    return out


def faixa_hora(minutos: Iterable[Any]) -> list[str | None]:
    out: list[str | None] = []
    for m in minutos:
        if m is None or (isinstance(m, float) and math.isnan(m)):
            out.append(None)
            continue
        out.append(next(n for n, lo, hi in FAIXAS_HORA if lo <= m < hi))
    return out


def resumo_tempo(minutos: Sequence[float] | np.ndarray | pd.Series) -> dict | None:
    """Mediana, p90, p99 e parcelas depois de 17:30, 18:00 e 19:00 (minutos)."""
    x = pd.Series(minutos, dtype=float).dropna().to_numpy()
    if len(x) == 0:
        return None
    q = np.percentile(x, [50, 90, 99])
    out: dict[str, Any] = {
        "secoes": len(x),
        "mediana": secoes_base.r2(q[0], 1),
        "p90": secoes_base.r2(q[1], 1),
        "p99": secoes_base.r2(q[2], 1),
    }
    for c, nome in zip(CORTES, ("1730", "1800", "1900"), strict=True):
        out[f"depois_{nome}_pct"] = secoes_base.r2(100 * float((x >= c).mean()))
    return out


def acumulada(minutos: Sequence[float] | np.ndarray | pd.Series) -> list[float] | None:
    """Parcela (%) das seções com hora até cada ponto de `GRADE`."""
    x = np.sort(pd.Series(minutos, dtype=float).dropna().to_numpy())
    if len(x) == 0:
        return None
    pos = np.searchsorted(x, np.asarray(GRADE, dtype=float), side="right")
    return [round(100 * float(v) / len(x), 2) for v in pos]


def rotulo_hora(minutos: float | None) -> str:
    """Minutos depois das 17h viram 'HH:MM' (com '(dia seguinte)' depois da meia-noite)."""
    if minutos is None or (isinstance(minutos, float) and math.isnan(minutos)):
        return "n/d"
    total = 17 * 60 + round(minutos)
    dia, resto = divmod(total, 1440)
    h, m = divmod(resto, 60)
    sufixo = " (dia seguinte)" if dia >= 1 else ""
    return f"{h:02d}:{m:02d}{sufixo}"


def rotulo_duracao(minutos: float | None) -> str:
    """Minutos viram '6 min' ou '1h19'."""
    if minutos is None or (isinstance(minutos, float) and math.isnan(minutos)):
        return "n/d"
    m = round(minutos)
    if abs(m) < 60:
        return f"{m} min"
    h, r = divmod(m, 60)
    return f"{h}h{r:02d}"


def spearman(x: Sequence[float] | np.ndarray, y: Sequence[float] | np.ndarray) -> float:
    """Correlação de postos (postos médios nos empates), sem SciPy."""
    a = pd.Series(np.asarray(x, dtype=float)).rank().to_numpy()
    b = pd.Series(np.asarray(y, dtype=float)).rank().to_numpy()
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def pearson(x: Sequence[float] | np.ndarray, y: Sequence[float] | np.ndarray) -> float:
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def lacuna(
    minutos: Sequence[float] | np.ndarray | pd.Series, ate: float = 420
) -> dict | None:
    """Maior intervalo sem nenhum recebimento entre 17h e `ate` (minutos depois das 17h).

    Devolve o último recebimento antes do buraco, o primeiro depois, a duração e
    quantas seções chegaram nos 5 minutos seguintes ao fim do buraco.
    """
    x = np.sort(pd.Series(minutos, dtype=float).dropna().to_numpy())
    x = x[(x >= 0) & (x <= ate)]
    if len(x) < 2:
        return None
    gaps = np.diff(x)
    i = int(np.argmax(gaps))
    ini, fim = float(x[i]), float(x[i + 1])
    return {
        "ultimo_antes_min": secoes_base.r2(ini, 2),
        "primeiro_depois_min": secoes_base.r2(fim, 2),
        "minutos": secoes_base.r2(fim - ini, 1),
        "secoes_5min_depois": int(((x >= fim) & (x < fim + 5)).sum()),
        "secoes_5min_antes": int(((x > ini - 5) & (x <= ini)).sum()),
    }
