"""Leitura dos boletins de urna por seção (1º turno de 2026, presidente).

Lê, só para leitura, o banco da coleta seção a seção
(``apuracao/data/secoes_2026.sqlite``), o cadastro de locais de votação
(``data/outputs/locais_votacao_2026.sqlite``) e a lista de candidaturas do
banco da apuração. Todas as leituras do banco de seções acontecem dentro de uma
única transação de leitura, para que o coletor, que continua gravando, não
produza um retrato misturado.

Unidades: uma linha por boletim de urna (seção principal). Seções agregadas não
têm boletim próprio: o voto delas está no boletim da principal.

As funções puras (transformação log-razão, fuso, palavras-chave de local) ficam
no fim do arquivo e são testadas sem banco.
"""

from __future__ import annotations

import json
import math
import sqlite3
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .dados import regiao

LULA = 13
FLAVIO = 22
ELEICAO_FEDERAL = 6257
CARGO_PRESIDENTE = 1
ZERO = 1e-4

TIPO_ARQUIVO = {
    1: "votação na urna (normal)",
    2: "votação recuperada (RED)",
    3: "sistema de apuração (3)",
    4: "sistema de apuração (4)",
    5: "sistema de apuração (5)",
    6: "sistema de apuração (6)",
}
TIPO_URNA = {
    1: "urna de seção",
    3: "urna de contingência",
    4: "urna de reserva (seção)",
    6: "urna de reserva (encerrando seção)",
}

# Nomes de exibição; os demais vêm do nome de urna do TSE em caixa de título.
NOMES = {
    13: "Lula",
    22: "Flávio Bolsonaro",
    70: "Augusto Cury",
    55: "Ronaldo Caiado",
    14: "Renan Santos",
    30: "Romeu Zema",
}
CORES = {13: "#b02f21", 22: "#1457aa", 70: "#0f7f5f"}

# Fuso padrão por UF (horas a somar à hora local para chegar à de Brasília).
FUSO_UF = {
    "ac": 2,
    "am": 1,
    "mt": 1,
    "ms": 1,
    "ro": 1,
    "rr": 1,
}


def chave_candidato(numero: int) -> str:
    """Chave estável no JSON: `lula`, `flavio` ou `n<numero>`."""
    if numero == LULA:
        return "lula"
    if numero == FLAVIO:
        return "flavio"
    return f"n{numero}"


def nome_candidato(numero: int, nome_urna: str | None) -> str:
    if numero in NOMES:
        return NOMES[numero]
    return (nome_urna or str(numero)).title()


def abrir_ro(caminho: Path) -> sqlite3.Connection:
    """Conexão somente leitura (`mode=ro` e `query_only`)."""
    con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    con.execute("PRAGMA query_only = 1")
    return con


# ---------------------------------------------------------------- estrutura


@dataclass
class Candidato:
    numero: int
    chave: str
    nome: str
    cor: str | None


@dataclass
class Base:
    """Tudo o que as análises usam, já filtrado e alinhado por seção."""

    secoes: pd.DataFrame  # uma linha por boletim válido
    candidatos: list[Candidato]
    cobertura: dict[str, Any]
    zonas: pd.DataFrame  # agregados por (uf, mun, zona) das seções válidas
    municipios: pd.DataFrame  # agregados por (uf, mun)
    excluidas: pd.DataFrame  # boletins fora da análise, com o motivo
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def colunas_voto(self) -> list[str]:
        return [f"v{c.numero}" for c in self.candidatos]


CHAVES = ["uf", "mun", "zona", "secao"]


# ---------------------------------------------------------------- leitura


def ler_candidatos(apuracao: Path) -> list[tuple[int, str]]:
    con = abrir_ro(apuracao)
    try:
        linhas = con.execute(
            "SELECT numero, nome_urna FROM candidato WHERE eleicao_cd = ? "
            "AND cargo_cd = ? ORDER BY numero",
            (ELEICAO_FEDERAL, CARGO_PRESIDENTE),
        ).fetchall()
    finally:
        con.close()
    return [(int(n), str(u)) for n, u in linhas]


def ler_ibge(apuracao: Path) -> dict[str, str]:
    con = abrir_ro(apuracao)
    try:
        linhas = con.execute("SELECT cd, ibge FROM municipio").fetchall()
    finally:
        con.close()
    return {str(cd): str(ibge) for cd, ibge in linhas if ibge}


def ler_banco_secoes(caminho: Path, numeros: Sequence[int]) -> dict[str, pd.DataFrame]:
    """Lê as tabelas necessárias numa só transação de leitura."""
    con = abrir_ro(caminho)
    lista = ",".join(str(int(n)) for n in numeros)
    soma = ", ".join(
        f"SUM(CASE WHEN tipo = 1 AND numero = {int(n)} THEN votos ELSE 0 END) AS v{int(n)}"
        for n in numeros
    )
    try:
        con.execute("BEGIN")
        saida = {
            "cs": pd.read_sql("SELECT uf, secoes, baixado_em FROM cs", con),
            "secao": pd.read_sql(
                "SELECT uf, mun, zona, secao, nsp IS NOT NULL AS agregada, "
                "status_aux, erro IS NOT NULL AS com_erro, bu_gz IS NOT NULL AS tem_bu, "
                "dr_hr FROM secao",
                con,
            ),
            "bu": pd.read_sql(
                "SELECT uf, mun, zona, secao, local AS local_bu, modelo_urna, modelo_fonte, "
                "tipo_urna, tipo_arquivo, aptos AS aptos_bu, aptos_secao, aptos_tte, "
                "comparecimento AS comparecimento_bu, abertura, encerramento, "
                "n_cargas, id_confere FROM bu",
                con,
            ),
            "cargo": pd.read_sql(
                "SELECT uf, mun, zona, secao, aptos, comparecimento FROM bu_cargo "
                "WHERE cargo = 1",
                con,
            ),
            "votos": pd.read_sql(
                f"SELECT uf, mun, zona, secao, {soma}, "
                "SUM(CASE WHEN tipo = 2 THEN votos ELSE 0 END) AS brancos, "
                "SUM(CASE WHEN tipo = 3 THEN votos ELSE 0 END) AS nulos_urna, "
                f"SUM(CASE WHEN tipo = 1 AND numero NOT IN ({lista}) THEN votos "
                "ELSE 0 END) AS fora_lista, "
                "SUM(CASE WHEN tipo NOT IN (1, 2, 3) THEN votos ELSE 0 END) AS outros_tipos "
                "FROM voto_secao WHERE cargo = 1 GROUP BY uf, mun, zona, secao",
                con,
            ),
            "conferencia": pd.read_sql(
                "SELECT uf, mun, zona, secoes_cs, secoes_bu, ts_zona, st_zona, ok, "
                "divergencias FROM conferencia_zona WHERE cargo = 1",
                con,
            ),
        }
        con.execute("COMMIT")
    finally:
        con.close()
    return saida


def ler_locais(caminho: Path) -> pd.DataFrame:
    con = abrir_ro(caminho)
    try:
        df = pd.read_sql(
            "SELECT lower(uf) AS uf, municipio_cd AS mun, municipio, zona, secao, "
            "agregada_cd, secao_principal, local_nr, local, tipo_local, endereco, "
            "bairro, lat, lon, eleitores, eleitores_federal FROM secao",
            con,
        )
    finally:
        con.close()
    return df


def ultimo_progresso(log: Path) -> dict[str, Any] | None:
    """Último registro `progresso` (ou `fim`) do log JSON por linha do coletor."""
    if not log.exists():
        return None
    ultimo: dict[str, Any] | None = None
    with log.open(encoding="utf-8") as f:
        for linha in f:
            if '"progresso"' not in linha and '"fim"' not in linha:
                continue
            try:
                ultimo = json.loads(linha)
            except json.JSONDecodeError:
                continue
    return ultimo


# ---------------------------------------------------------------- montagem


def _agregar_locais(locais: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por seção principal, com o eleitorado das agregadas somado."""
    principal = locais[locais["agregada_cd"] != 2].copy()
    agreg = locais[locais["agregada_cd"] == 2]
    soma = (
        agreg.groupby(["uf", "mun", "zona", "secao_principal"])["eleitores"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "eleitores_agregadas", "count": "n_agregadas"})
        .reset_index()
        .rename(columns={"secao_principal": "secao"})
    )
    principal = principal.merge(soma, on=CHAVES, how="left")
    principal["eleitores_agregadas"] = principal["eleitores_agregadas"].fillna(0)
    principal["n_agregadas"] = principal["n_agregadas"].fillna(0).astype(int)
    return principal.drop(columns=["agregada_cd", "secao_principal"])


def montar(
    secoes_db: Path,
    locais_db: Path,
    apuracao_db: Path,
    log: Path | None = None,
) -> Base:
    cand = ler_candidatos(apuracao_db)
    numeros = [n for n, _ in cand]
    t = ler_banco_secoes(secoes_db, numeros)
    locais = _agregar_locais(ler_locais(locais_db))
    ibge = ler_ibge(apuracao_db)

    bu = t["bu"].merge(t["cargo"], on=CHAVES, how="left")
    bu = bu.merge(t["votos"], on=CHAVES, how="left")
    sec = t["secao"][[*CHAVES, "dr_hr"]]
    bu = bu.merge(sec, on=CHAVES, how="left")
    vcols = [f"v{n}" for n in numeros]
    for c in [*vcols, "brancos", "nulos_urna", "fora_lista", "outros_tipos"]:
        bu[c] = bu[c].fillna(0).astype(np.int64)
    bu["validos"] = bu[vcols].sum(axis=1)
    bu["nulos"] = bu["nulos_urna"] + bu["fora_lista"] + bu["outros_tipos"]
    bu["soma_votos"] = bu["validos"] + bu["brancos"] + bu["nulos"]
    bu["aptos"] = bu["aptos"].fillna(bu["aptos_bu"])
    bu["comparecimento"] = bu["comparecimento"].fillna(bu["comparecimento_bu"])

    conf = t["conferencia"].copy()
    conf["congelada"] = conf["st_zona"] < conf["ts_zona"]
    bu = bu.merge(
        conf[["uf", "mun", "zona", "ok", "congelada"]],
        on=["uf", "mun", "zona"],
        how="left",
    )

    motivo = pd.Series("", index=bu.index, dtype=object)
    congelada = bu["congelada"].eq(True)
    motivo[bu["ok"].isna()] = "zona_sem_conferencia"
    motivo[(bu["ok"] == 0) & congelada] = "zona_divergente_arquivo_incompleto"
    motivo[(bu["ok"] == 0) & ~congelada] = "zona_divergente"
    motivo[(motivo == "") & bu["tipo_arquivo"].isna()] = "tipo_arquivo_ausente"
    motivo[(motivo == "") & ~(bu["aptos"] > 0)] = "sem_aptos"
    motivo[(motivo == "") & (bu["soma_votos"] != bu["comparecimento"])] = (
        "votos_diferentes_do_comparecimento"
    )
    bu["motivo"] = motivo

    bu = bu.merge(
        locais.drop(columns=["municipio"]).rename(
            columns={"eleitores": "eleitores_cad"}
        ),
        on=CHAVES,
        how="left",
    )
    nomes = locais.drop_duplicates(["uf", "mun"]).set_index(["uf", "mun"])["municipio"]
    bu["municipio"] = [
        nomes.get((u, m), None) for u, m in zip(bu["uf"], bu["mun"], strict=True)
    ]
    bu["ibge"] = bu["mun"].map(ibge)
    bu["regiao"] = bu["uf"].map(regiao)
    bu["fuso"] = fusos_por_municipio(bu)
    bu["tipo_inferido"] = [
        tipo_local(*a)
        for a in zip(
            bu["uf"],
            bu["tipo_local"],
            bu["local"],
            bu["bairro"],
            bu["endereco"],
            strict=True,
        )
    ]

    validas = bu[bu["motivo"] == ""].copy().reset_index(drop=True)
    excluidas = bu[bu["motivo"] != ""].copy().reset_index(drop=True)
    derivar(validas)
    zonas = agregar(validas, ["uf", "mun", "zona"], vcols)
    municipios = agregar(validas, ["uf", "mun"], vcols)
    contexto_zona_municipio(validas, zonas, municipios)

    candidatos = [
        Candidato(n, chave_candidato(n), nome_candidato(n, u), CORES.get(n))
        for n, u in cand
    ]
    total_votos = {
        f"v{c.numero}": int(validas[f"v{c.numero}"].sum()) for c in candidatos
    }
    candidatos.sort(key=lambda c: -total_votos[f"v{c.numero}"])

    cobertura = montar_cobertura(t, bu, validas, excluidas, log)
    return Base(validas, candidatos, cobertura, zonas, municipios, excluidas)


def derivar(df: pd.DataFrame) -> None:
    """Percentuais por seção (válidos, eleitorado, comparecimento)."""
    val = df["validos"].to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        df["lula_pct"] = np.where(val > 0, 100 * df[f"v{LULA}"] / val, np.nan)
        df["flavio_pct"] = np.where(val > 0, 100 * df[f"v{FLAVIO}"] / val, np.nan)
        df["outros"] = df["validos"] - df[f"v{LULA}"] - df[f"v{FLAVIO}"]
        df["abstencao"] = df["aptos"] - df["comparecimento"]
        apt = df["aptos"].to_numpy(dtype=float)
        comp = df["comparecimento"].to_numpy(dtype=float)
        df["abstencao_pct"] = np.where(apt > 0, 100 * df["abstencao"] / apt, np.nan)
        df["brancos_pct"] = np.where(comp > 0, 100 * df["brancos"] / comp, np.nan)
        df["nulos_pct"] = np.where(comp > 0, 100 * df["nulos"] / comp, np.nan)
    df["votantes"] = df["comparecimento"]


def agregar(df: pd.DataFrame, por: list[str], vcols: Sequence[str]) -> pd.DataFrame:
    cols = [*vcols, "validos", "brancos", "nulos", "aptos", "comparecimento"]
    g = df.groupby(por, sort=False)[cols].sum()
    g["secoes"] = df.groupby(por, sort=False).size()
    g = g.reset_index()
    with np.errstate(divide="ignore", invalid="ignore"):
        g["lula_pct"] = 100 * g[f"v{LULA}"] / g["validos"]
        g["flavio_pct"] = 100 * g[f"v{FLAVIO}"] / g["validos"]
    return g


def contexto_zona_municipio(
    df: pd.DataFrame, zonas: pd.DataFrame, municipios: pd.DataFrame
) -> None:
    """% da zona e do município (com e sem a própria seção) em cada seção."""
    for nome, agg, por in (
        ("zona", zonas, ["uf", "mun", "zona"]),
        ("mun", municipios, ["uf", "mun"]),
    ):
        m = df[por].merge(
            agg[[*por, f"v{LULA}", f"v{FLAVIO}", "validos", "secoes"]],
            on=por,
            how="left",
        )
        lz = m[f"v{LULA}"].to_numpy(dtype=float)
        fz = m[f"v{FLAVIO}"].to_numpy(dtype=float)
        vz = m["validos"].to_numpy(dtype=float)
        lv = df[f"v{LULA}"].to_numpy(dtype=float)
        fv = df[f"v{FLAVIO}"].to_numpy(dtype=float)
        vv = df["validos"].to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            df[f"{nome}_lula_pct"] = np.where(vz > 0, 100 * lz / vz, np.nan)
            df[f"{nome}_flavio_pct"] = np.where(vz > 0, 100 * fz / vz, np.nan)
            resto = vz - vv
            df[f"{nome}_resto_lula_pct"] = np.where(
                resto > 0, 100 * (lz - lv) / resto, np.nan
            )
            df[f"{nome}_resto_flavio_pct"] = np.where(
                resto > 0, 100 * (fz - fv) / resto, np.nan
            )
        df[f"{nome}_secoes"] = m["secoes"].to_numpy()


def montar_cobertura(
    t: Mapping[str, pd.DataFrame],
    bu: pd.DataFrame,
    validas: pd.DataFrame,
    excluidas: pd.DataFrame,
    log: Path | None,
) -> dict[str, Any]:
    sec = t["secao"]
    conf = t["conferencia"]
    cs = t["cs"]
    pend = sec["status_aux"].isna() | (sec["status_aux"] == "")
    por_uf = []
    completas = []
    incompletas = []
    for uf in sorted(cs["uf"]):
        s = sec[sec["uf"] == uf]
        c = conf[conf["uf"] == uf]
        principais = int((s["agregada"] == 0).sum())
        com_bu = int((bu["uf"] == uf).sum())
        pendentes = int(pend[sec["uf"] == uf].sum())
        erros = int(s["com_erro"].sum())
        zonas = int(s[["mun", "zona"]].drop_duplicates().shape[0])
        linha = {
            "uf": uf.upper(),
            "secoes_cs": len(s),
            "agregadas": int((s["agregada"] == 1).sum()),
            "principais": principais,
            "pendentes": pendentes,
            "com_erro": erros,
            "com_bu": com_bu,
            "validas": int((validas["uf"] == uf).sum()),
            "zonas": zonas,
            "zonas_ok": int((c["ok"] == 1).sum()),
            "zonas_divergentes": int((c["ok"] == 0).sum()),
            "zonas_sem_conferencia": zonas - int(c["ok"].notna().sum()),
        }
        por_uf.append(linha)
        if pendentes == 0 and erros == 0 and linha["zonas_sem_conferencia"] == 0:
            completas.append(uf.upper())
        else:
            incompletas.append(
                {
                    "uf": uf.upper(),
                    "coletadas": len(s) - pendentes,
                    "total": len(s),
                }
            )
    motivos = {
        "sem_bu": "seção principal sem boletim de urna no banco (ainda não coletada ou sem arquivo)",
        "zona_sem_conferencia": "zona ainda não conferida contra o arquivo de zona do TSE",
        "zona_divergente_arquivo_incompleto": (
            "soma das seções diferente do arquivo de zona do TSE, que congelou "
            "com menos seções totalizadas do que as existentes (st < ts)"
        ),
        "zona_divergente": "soma das seções diferente do arquivo de zona do TSE",
        "tipo_arquivo_ausente": "boletim sem tipo de arquivo declarado",
        "sem_aptos": "boletim sem eleitorado apto",
        "votos_diferentes_do_comparecimento": (
            "soma dos votos de presidente diferente do comparecimento do boletim"
        ),
    }
    excl = []
    sem_bu = int(
        ((sec["agregada"] == 0) & (sec["tem_bu"] == 0)).sum()
    )  # inclui pendentes
    excl.append(
        {
            "codigo": "sem_bu",
            "motivo": motivos["sem_bu"],
            "secoes": sem_bu,
            "aptos": None,
        }
    )
    for cod, g in excluidas.groupby("motivo"):
        excl.append(
            {
                "codigo": str(cod),
                "motivo": motivos.get(str(cod), str(cod)),
                "secoes": len(g),
                "aptos": int(g["aptos"].fillna(0).sum()),
            }
        )
    prog = ultimo_progresso(log) if log is not None else None
    vl = validas
    totais = {
        "aptos": int(vl["aptos"].sum()),
        "comparecimento": int(vl["comparecimento"].sum()),
        "validos": int(vl["validos"].sum()),
        "lula": int(vl[f"v{LULA}"].sum()),
        "flavio": int(vl[f"v{FLAVIO}"].sum()),
        "brancos": int(vl["brancos"].sum()),
        "nulos": int(vl["nulos"].sum()),
    }
    totais["lula_pct"] = pct(totais["lula"], totais["validos"])
    totais["flavio_pct"] = pct(totais["flavio"], totais["validos"])
    return {
        "parcial": None,
        "carimbo_log": prog.get("em") if prog else None,
        "restantes_log": prog.get("restantes") if prog else None,
        "secoes_cs": len(sec),
        "secoes_principais_cs": int((sec["agregada"] == 0).sum()),
        "secoes_agregadas_cs": int((sec["agregada"] == 1).sum()),
        "secoes_pendentes": int(pend.sum()),
        "secoes_com_erro": int(sec["com_erro"].sum()),
        "secoes_com_bu": len(bu),
        "secoes_validas": len(validas),
        "excluidas": excl,
        "ufs_completas": completas,
        "ufs_incompletas": incompletas,
        "por_uf": por_uf,
        "totais_validos": totais,
        "votos_diferentes_do_comparecimento": int(
            (bu["soma_votos"] != bu["comparecimento"]).sum()
        ),
    }


# ---------------------------------------------------------------- funções puras


def pct(a: float, b: float, casas: int = 2) -> float | None:
    if not b:
        return None
    return round(100.0 * a / b, casas)


def num(x: float, casas: int = 1) -> str:
    """Número em pt-BR: vírgula decimal e ponto de milhar."""
    texto = f"{x:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def r2(x: Any, casas: int = 2) -> float | None:
    """Arredonda para o JSON; NaN e infinito viram `null`."""
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return round(v, casas)


def clr(fracoes: np.ndarray, zero: float = ZERO) -> np.ndarray:
    """Log-razão centrada por linha, com zeros trocados por `zero` antes do log.

    `fracoes` tem uma linha por seção e uma coluna por componente (somando 1).
    Valores menores ou iguais a zero viram `zero`; nada mais é alterado, como
    pedido. Cada linha do resultado soma zero.
    """
    x = np.asarray(fracoes, dtype=float).copy()
    x[~(x > 0)] = zero
    lx = np.log(x)
    return lx - lx.mean(axis=1, keepdims=True)


def logit(fracoes: np.ndarray, zero: float = ZERO) -> np.ndarray:
    """Logit por componente, com zeros trocados por `zero` e uns por 1 - `zero`."""
    x = np.asarray(fracoes, dtype=float).copy()
    x[~(x > 0)] = zero
    x[x >= 1] = 1 - zero
    return np.log(x / (1 - x))


def fusos_por_municipio(df: pd.DataFrame) -> pd.Series:
    """Horas a somar à hora local do boletim para chegar à hora de Brasília.

    A votação de 2026 abriu às 8h de Brasília no país inteiro: a hora local mais
    frequente de abertura no município diz o fuso (6h no Acre, 7h na maior parte
    do Amazonas, 9h em Fernando de Noronha). Sem moda plausível, usa o fuso da UF.
    Exterior: `NaN` (hora local da cidade, sem conversão).
    """
    hora = pd.to_datetime(df["abertura"], errors="coerce").dt.hour
    base = pd.DataFrame({"uf": df["uf"], "mun": df["mun"], "h": hora})
    moda = (
        base.dropna(subset=["h"])
        .groupby(["uf", "mun"])["h"]
        .agg(lambda s: s.value_counts().idxmax())
        .to_dict()
    )
    saida = []
    for uf, mun in zip(df["uf"], df["mun"], strict=True):
        if uf == "zz":
            saida.append(np.nan)
            continue
        h = moda.get((uf, mun))
        if h is not None and 5 <= h <= 9:
            saida.append(float(8 - h))
        else:
            saida.append(float(FUSO_UF.get(uf, 0)))
    return pd.Series(saida, index=df.index, dtype=float)


def _sem_acento(s: str) -> str:
    n = unicodedata.normalize("NFKD", s)
    return "".join(c for c in n if not unicodedata.combining(c)).upper()


# Regras declaradas de tipo de local (inferência por palavra-chave, na ordem).
REGRAS_LOCAL: list[tuple[str, str, list[str]]] = [
    ("exterior", "uf", ["ZZ"]),
    ("unidade prisional ou socioeducativa", "tipo_local", ["PRESO PROVISORIO"]),
    (
        "unidade prisional ou socioeducativa",
        "local",
        [
            "PRESIDIO",
            "PENITENCIARIA",
            "CADEIA",
            "DETENCAO",
            "PRISIONAL",
            "CUSTODIA",
            "RESSOCIALIZACAO",
            "POLICIA PENAL",
            "SOCIOEDUCATIV",
            "FUNDACAO CASA",
            "INTERNACAO PROVISORIA",
        ],
    ),
    ("voto em trânsito", "tipo_local", ["VOTO EM TRANSITO"]),
    (
        "hospital ou unidade de saúde",
        "local",
        ["HOSPITAL", "PRONTO SOCORRO", "SANATORIO", "MATERNIDADE"],
    ),
    (
        "aldeia ou terra indígena",
        "local+bairro+endereco",
        ["ALDEIA", "INDIGENA", "TERRA INDIG"],
    ),
    ("quilombo", "local+bairro+endereco", ["QUILOMB"]),
    ("assentamento", "local+bairro+endereco", ["ASSENTAMENTO"]),
    (
        "zona rural",
        "bairro+endereco",
        [
            "ZONA RURAL",
            "POVOADO",
            "SITIO",
            "FAZENDA",
            "RAMAL",
            "GLEBA",
            "COMUNIDADE",
            "RIO ",
            "IGARAPE",
            "LOCALIDADE",
            "AREA RURAL",
        ],
    ),
    (
        "escola ou universidade",
        "local",
        [
            "ESCOLA",
            "COLEGIO",
            "EMEF",
            "EMEI",
            "EMEIF",
            "CEMEI",
            "CMEI",
            "UNIDADE ESCOLAR",
            "U.E.",
            "U. E.",
            "E.E.",
            "E. E.",
            "EE ",
            "EEEF",
            "EEEM",
            "CRECHE",
            "UNIVERSIDADE",
            "FACULDADE",
            "INSTITUTO FEDERAL",
            "CENTRO EDUCACIONAL",
            "CENTRO DE ENSINO",
            "CENTRO DE EDUCACAO",
            "EDUCACIONAL",
            "GRUPO ESCOLAR",
            "CAMPUS",
            "LICEU",
            "ENSINO",
        ],
    ),
]


def tipo_local(
    uf: str,
    tipo_tse: str | None,
    local: str | None,
    bairro: str | None,
    endereco: str | None,
) -> str:
    """Tipo de local inferido pelas regras `REGRAS_LOCAL` (primeira que casar)."""
    campos = {
        "uf": _sem_acento(uf or ""),
        "tipo_local": _sem_acento(tipo_tse or ""),
        "local": _sem_acento(local or ""),
        "bairro": _sem_acento(bairro or ""),
        "endereco": _sem_acento(endereco or ""),
    }
    for tipo, campo, palavras in REGRAS_LOCAL:
        texto = " | ".join(campos[p] for p in campo.split("+"))
        if campo == "uf":
            if campos["uf"] in palavras:
                return tipo
            continue
        if any(p in texto for p in palavras):
            return tipo
    return "outro" if local else "sem cadastro"


def regras_local_json() -> list[dict[str, Any]]:
    return [{"tipo": t, "campo": c, "palavras": p} for t, c, p in REGRAS_LOCAL]


def hora_brasilia(texto: Any, fuso: float) -> str | None:
    """Converte a hora local do boletim para Brasília (`fuso` em horas)."""
    if texto is None or (isinstance(texto, float) and math.isnan(texto)):
        return None
    if fuso is None or (isinstance(fuso, float) and math.isnan(fuso)):
        return None
    ts = pd.to_datetime(texto, errors="coerce")
    if ts is pd.NaT or pd.isna(ts):
        return None
    return str((ts + pd.Timedelta(hours=float(fuso))).strftime("%Y-%m-%d %H:%M:%S"))


def secao_ref(linha: Mapping[str, Any], extra: Mapping[str, Any] | None = None) -> dict:
    """Registro `SecaoRef` do contrato a partir de uma linha da base."""
    g = linha.get

    def inteiro(k: str) -> int | None:
        v = g(k)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return int(v)

    lat = r2(g("lat"), 4)
    lon = r2(g("lon"), 4)
    fuso = g("fuso")
    ref = {
        "uf": str(g("uf")).upper(),
        "regiao": g("regiao"),
        "municipio": g("municipio"),
        "mun_tse": g("mun"),
        "ibge": g("ibge") if isinstance(g("ibge"), str) else None,
        "zona": inteiro("zona"),
        "secao": inteiro("secao"),
        "local": _texto(g("local")),
        "bairro": _texto(g("bairro")),
        "tipo_local_tse": _texto(g("tipo_local")),
        "tipo_local_inferido": g("tipo_inferido"),
        "lat": lat,
        "lon": lon,
        "modelo_urna": _texto(g("modelo_urna")),
        "tipo_urna": inteiro("tipo_urna"),
        "tipo_arquivo": inteiro("tipo_arquivo"),
        "aptos": inteiro("aptos"),
        "comparecimento": inteiro("comparecimento"),
        "validos": inteiro("validos"),
        "lula": inteiro(f"v{LULA}"),
        "flavio": inteiro(f"v{FLAVIO}"),
        "outros": inteiro("outros"),
        "brancos": inteiro("brancos"),
        "nulos": inteiro("nulos"),
        "lula_pct": r2(g("lula_pct")),
        "flavio_pct": r2(g("flavio_pct")),
        "zona_lula_pct": r2(g("zona_lula_pct")),
        "zona_flavio_pct": r2(g("zona_flavio_pct")),
        "mun_lula_pct": r2(g("mun_lula_pct")),
        "mun_flavio_pct": r2(g("mun_flavio_pct")),
        "abertura_brasilia": hora_brasilia(g("abertura"), fuso),
        "encerramento_brasilia": hora_brasilia(g("encerramento"), fuso),
        "recebido_tse": _texto(g("dr_hr")),
        "explicacao": explicar(linha),
    }
    if extra:
        ref.update(extra)
    return ref


def _texto(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    s = str(v).strip()
    return s or None


def explicar(linha: Mapping[str, Any]) -> str:
    """Frase curta do que provavelmente explica a seção (regra declarada)."""
    g = linha.get
    partes: list[str] = []
    tipo = g("tipo_inferido")
    if tipo and tipo not in {"outro", "escola ou universidade", "sem cadastro"}:
        partes.append(f"{tipo} (inferido pelo cadastro do local)")
    votantes = g("comparecimento") or 0
    if votantes < 50:
        partes.append(f"seção minúscula ({int(votantes)} votantes)")
    elif votantes < 100:
        partes.append(f"seção pequena ({int(votantes)} votantes)")
    apt = g("aptos") or 0
    tte = g("aptos_tte") or 0
    if apt and tte / apt >= 0.2:
        partes.append(f"{int(tte)} de {int(apt)} aptos em trânsito")
    tu = g("tipo_urna")
    if tu is not None and not (isinstance(tu, float) and math.isnan(tu)) and tu != 1:
        partes.append(TIPO_URNA.get(int(tu), f"tipo de urna {int(tu)}"))
    ta = g("tipo_arquivo")
    if ta is not None and not (isinstance(ta, float) and math.isnan(ta)) and ta != 1:
        partes.append(TIPO_ARQUIVO.get(int(ta), f"tipo de arquivo {int(ta)}"))
    partes.extend(_frase_zona(linha))
    if not partes:
        partes.append("sem regra estrutural acionada: comparar com ata e log da seção")
    return "; ".join(partes)


def _frase_zona(linha: Mapping[str, Any]) -> list[str]:
    """Diz quando a zona inteira vota como a seção (diferença menor que 5 pp)."""
    g = linha.get
    lula, flavio = g("lula_pct"), g("flavio_pct")
    if lula is None or flavio is None or math.isnan(lula) or math.isnan(flavio):
        return []
    chave, nome = ("lula", "Lula") if lula >= flavio else ("flavio", "Flávio")
    sec = lula if chave == "lula" else flavio
    zona = g(f"zona_{chave}_pct")
    if zona is None or math.isnan(zona) or abs(sec - zona) >= 5:
        return []
    return [f"a zona inteira vota assim ({nome} {zona:.1f}% na zona)".replace(".", ",")]


def amostras(df: pd.DataFrame, n: int, extra: Iterable[str] = ()) -> list[dict]:
    out = []
    for _, linha in df.head(n).iterrows():
        d = linha.to_dict()
        out.append(secao_ref(d, {k: r2(d.get(k), 3) for k in extra}))
    return out
