"""Base do capítulo 13 (onde colocar fiscal): universo, contexto e insumos.

Reaproveita a leitura dos boletins do capítulo 12 (`secoes_base.montar`) e monta o
universo do capítulo: as seções válidas do capítulo 12, as seções com boletim
íntegro que ficaram fora só porque a zona diverge do arquivo de zona do TSE e as
seções principais ativas sem arquivo publicado. Acrescenta o contexto de zona,
município e UF recalculado sobre esse universo, o casamento com 2022, a mistura
gaussiana do capítulo 12 refeita com a semente gravada, os arquivos de zona que
ficaram parados incompletos e as matérias de contexto por município.

Todos os bancos são abertos só para leitura. Atípico não é irregularidade.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import secoes_base as sb
from .secoes_2022 import casar
from .secoes_base import FLAVIO, LULA

INICIO_APURACAO_UTC = "2026-10-04T20:00:00"  # 17h de Brasília
HORAS_PARADA = 6.0
TEMAS_CONTEXTO = (
    "coercao",
    "faccao_milicia",
    "violencia",
    "logistica_remota",
    "urnas_substituidas",
    "contingencia",
    "totalizacao_tardia",
)


def abrir_ro(caminho: Path) -> sqlite3.Connection:
    return sb.abrir_ro(caminho)


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 22), b""):
            h.update(bloco)
    return h.hexdigest()


def normalizar(s: Any) -> str:
    """Sem acento, maiúsculas, apóstrofos e espaços normalizados."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    n = unicodedata.normalize("NFKD", str(s))
    t = "".join(c for c in n if not unicodedata.combining(c)).upper()
    t = t.replace("’", "'").replace("`", "'")
    return " ".join(t.split())


def local_id(uf: str, mun: str, zona: int, local_nr: Any, secao: int) -> str:
    """Chave do local de votação: UF-MUNTSE-ZONA-LOCALNR (ou s<secao> sem local)."""
    base = f"{str(uf).upper()}-{mun}-{int(zona)}"
    if local_nr is None or (isinstance(local_nr, float) and np.isnan(local_nr)):
        return f"{base}-s{int(secao)}"
    return f"{base}-{int(local_nr)}"


# ---------------------------------------------------------------- leituras extras


def ler_cep(locais_db: Path) -> pd.DataFrame:
    con = abrir_ro(locais_db)
    try:
        return pd.read_sql(
            "SELECT lower(uf) AS uf, municipio_cd AS mun, zona, secao, cep FROM secao",
            con,
        )
    finally:
        con.close()


def ler_sem_arquivo(secoes_db: Path, locais_db: Path) -> pd.DataFrame:
    """Seções principais ativas sem boletim no banco e com `aux.json` 404 (fora o exterior)."""
    con = abrir_ro(secoes_db)
    try:
        s = pd.read_sql(
            "SELECT uf, mun, zona, secao, status_aux FROM secao WHERE nsp IS NULL "
            "AND bu_gz IS NULL AND uf <> 'zz'",
            con,
        )
    finally:
        con.close()
    loc = sb.ler_locais(locais_db)
    m = s.merge(loc, on=sb.CHAVES, how="left")
    m["aptos"] = m["eleitores_federal"].fillna(m["eleitores"])
    return m


def zonas_congeladas(
    apuracao_db: Path, horas: float = HORAS_PARADA, desde_utc: str = INICIO_APURACAO_UTC
) -> list[dict[str, Any]]:
    """Arquivos de zona de presidente cuja última versão incompleta, gerada depois das
    17h de Brasília, ficou publicada `horas` ou mais antes da versão completa."""
    sql = """
    WITH z AS (
      SELECT id, uf, municipio_cd, zona_cd FROM arquivo
      WHERE eleicao_cd = 6257 AND cargo_cd = 1 AND nivel = 'zona'
    ), s AS (
      SELECT z.uf, z.municipio_cd, z.zona_cd, sn.gerado_em, t.ts, t.st
      FROM z JOIN snapshot sn ON sn.arquivo_id = z.id
      JOIN totais t ON t.snapshot_id = sn.id
    ), u AS (
      SELECT uf, municipio_cd, zona_cd,
        max(CASE WHEN st < ts THEN gerado_em END) AS ult_inc,
        min(CASE WHEN st = ts THEN gerado_em END) AS prim_comp
      FROM s GROUP BY uf, municipio_cd, zona_cd
    )
    SELECT u.uf, u.municipio_cd, u.zona_cd, u.ult_inc, u.prim_comp,
      (SELECT s2.ts - s2.st FROM s s2 WHERE s2.uf = u.uf AND
         s2.municipio_cd = u.municipio_cd AND s2.zona_cd = u.zona_cd AND
         s2.gerado_em = u.ult_inc LIMIT 1) AS faltando
    FROM u WHERE u.ult_inc >= ?
    """
    con = abrir_ro(apuracao_db)
    try:
        linhas = con.execute(sql, (desde_utc,)).fetchall()
    finally:
        con.close()
    out = []
    for uf, mun, zona, ult, prim, falt in linhas:
        h = horas_entre(ult, prim)
        if h is None or h < horas:
            continue
        out.append(
            {
                "uf": str(uf).upper(),
                "mun_tse": str(mun),
                "zona": int(zona),
                "ultima_incompleta_utc": ult,
                "primeira_completa_utc": prim,
                "horas_parada": round(h, 2),
                "secoes_faltando": int(falt) if falt is not None else None,
            }
        )
    out.sort(key=lambda r: (r["uf"], r["mun_tse"], r["zona"]))
    return out


def _ts(texto: str | None) -> datetime | None:
    if not texto:
        return None
    t = str(texto).replace("Z", "").split(".")[0]
    try:
        return datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def horas_entre(a: str | None, b: str | None) -> float | None:
    """Horas de `a` até `b` (ISO UTC); sem `b` (nunca completou), `None`."""
    ta, tb = _ts(a), _ts(b)
    if ta is None or tb is None:
        return None
    return (tb - ta).total_seconds() / 3600


def utc_para_brasilia(texto: str) -> str:
    t = _ts(texto)
    if t is None:
        raise ValueError(f"data inválida: {texto}")
    return (t - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")


INTERVALO_LOTE_S = 30.0


def secoes_congeladas(
    df: pd.DataFrame, congeladas: Sequence[dict[str, Any]]
) -> np.ndarray:
    """Marca, em cada zona congelada, as k seções que faltavam no arquivo parado.

    k = ts menos st da última versão incompleta. As que faltavam são as k de
    recebimento (`dr/hr`, Brasília) mais recente até a geração daquela versão: o
    lote que chegou no último minuto e não entrou na totalização. A regra confere
    que existe um intervalo de ao menos 30 segundos entre a k-ésima e a seguinte
    (`conferem`); cada zona ganha `secoes_identificadas`, `conferem`,
    `intervalo_s` e `ultima_incompleta_brasilia`.
    """
    marca = np.zeros(len(df), dtype=bool)
    dr = df["_dr"]
    for z in congeladas:
        corte = pd.Timestamp(utc_para_brasilia(z["ultima_incompleta_utc"]))
        z["ultima_incompleta_brasilia"] = corte.strftime("%Y-%m-%d %H:%M:%S")
        sel = (
            (df["uf"] == z["uf"].lower())
            & (df["mun"] == z["mun_tse"])
            & (df["zona"] == int(z["zona"]))
            & (dr <= corte)
        )
        k = int(z.get("secoes_faltando") or 0)
        ordem = dr[sel].sort_values(ascending=False, kind="stable")
        escolhidas = ordem.index[:k]
        marca[np.asarray(escolhidas, dtype=int)] = True
        intervalo = None
        if 0 < k < len(ordem):
            intervalo = (ordem.iloc[k - 1] - ordem.iloc[k]).total_seconds()
        z["secoes_identificadas"] = len(escolhidas)
        z["intervalo_s"] = intervalo
        z["conferem"] = bool(
            len(escolhidas) == k
            and intervalo is not None
            and intervalo >= INTERVALO_LOTE_S
        )
        z["secoes"] = sorted(int(s) for s in df.loc[escolhidas, "secao"])
    return marca


# ---------------------------------------------------------------- universo


COLS_VOTO_EXTRA = ["brancos", "nulos", "validos", "aptos", "comparecimento"]


def universo(base: sb.Base, cep: pd.DataFrame | None = None) -> pd.DataFrame:
    """Válidas do capítulo 12 mais as íntegras das zonas divergentes, com contexto."""
    v = base.secoes.copy()
    v["cap12"] = True
    ex = base.excluidas
    integra = (
        ex["motivo"].astype(str).str.startswith("zona_divergente")
        & (ex["soma_votos"] == ex["comparecimento"])
        & (ex["aptos"] > 0)
        & ex["tipo_arquivo"].notna()
    )
    e = ex[integra].copy()
    e["cap12"] = False
    sb.derivar(e)
    comuns = [c for c in v.columns if c in e.columns]
    df = pd.concat([v[comuns], e[comuns]], ignore_index=True)
    vcols = base.colunas_voto
    zonas = sb.agregar(df, ["uf", "mun", "zona"], vcols)
    munis = sb.agregar(df, ["uf", "mun"], vcols)
    sb.contexto_zona_municipio(df, zonas, munis)
    ufs = sb.agregar(df, ["uf"], vcols).set_index("uf")
    df["uf_lula_pct"] = df["uf"].map(ufs["lula_pct"])
    df["uf_flavio_pct"] = df["uf"].map(ufs["flavio_pct"])
    df["mun_validos"] = (
        df[["uf", "mun"]]
        .merge(munis[["uf", "mun", "validos"]], on=["uf", "mun"], how="left")["validos"]
        .to_numpy()
    )
    if cep is not None:
        df = df.merge(cep, on=sb.CHAVES, how="left")
    else:
        df["cep"] = None
    df["local_id"] = [
        local_id(u, m, z, ln, s)
        for u, m, z, ln, s in zip(
            df["uf"], df["mun"], df["zona"], df["local_nr"], df["secao"], strict=True
        )
    ]
    fuso = pd.to_timedelta(df["fuso"], unit="h")
    df["_enc"] = pd.to_datetime(df["encerramento"], errors="coerce") + fuso
    df["_dr"] = pd.to_datetime(df["dr_hr"], errors="coerce")
    return df


def com_2022(df: pd.DataFrame, s22: pd.DataFrame | None) -> pd.DataFrame:
    """Casa a seção com 2022 (mesmo número e mesmo local) e calcula os percentuais."""
    if s22 is None:
        out = df.copy()
        out["mesma_secao"] = False
        for c in ("lula22_pct", "bolso22_pct", "lula22_2t_pct", "bolso22_2t_pct"):
            out[c] = np.nan
        out["nominais_1t"] = np.nan
        return out
    m = casar(df, s22)
    with np.errstate(divide="ignore", invalid="ignore"):
        n1 = m["nominais_1t"].to_numpy(dtype=float)
        n2 = m["nominais_2t"].to_numpy(dtype=float)
        m["lula22_pct"] = np.where(n1 > 0, 100 * m["lula_1t"] / n1, np.nan)
        m["bolso22_pct"] = np.where(n1 > 0, 100 * m["bolsonaro_1t"] / n1, np.nan)
        m["lula22_2t_pct"] = np.where(n2 > 0, 100 * m["lula_2t"] / n2, np.nan)
        m["bolso22_2t_pct"] = np.where(n2 > 0, 100 * m["bolsonaro_2t"] / n2, np.nan)
    for c in ("lula22_pct", "bolso22_pct", "lula22_2t_pct", "bolso22_2t_pct"):
        m.loc[~m["mesma_secao"], c] = np.nan
    return m


# ---------------------------------------------------------------- mistura gaussiana


def _ajuste_amostra(args: tuple[np.ndarray, int, str]) -> Any:
    from .secoes_clusters_motor import ajustar

    x, semente, init = args
    return ajustar(x, 5, n_init=1, semente=semente, init=init, tol=1e-6, max_iter=2000)


def mistura(df: pd.DataFrame, clusters: Mapping[str, Any]) -> dict[str, Any]:
    """Refaz o ajuste adotado no capítulo 12 e devolve a log-verossimilhança por seção.

    Mesmo caminho do `secoes_clusters.bloco`: a partida escolhida (semente e
    inicialização gravadas) na amostra estratificada de 150 mil, num processo com uma
    linha de execução de álgebra linear, refinada na base inteira e continuada com
    tolerância 1e-8. Confere as 50 seções de `clusters.menos_provaveis`.
    """
    from .secoes_clusters import composicao_cinco
    from .secoes_clusters_diag import apertar
    from .secoes_clusters_motor import (
        amostra_estratificada,
        espaco,
        ordem_estavel,
        refinar,
        uma_thread,
    )

    sel = df["cap12"].to_numpy(bool) & (df["aptos"].to_numpy(float) > 0)
    d = df[sel].reset_index()
    comp = composicao_cinco(d)
    x, _, _ = espaco(comp)
    aj = clusters["ajuste"]
    busca = aj["busca_em_amostra"]
    idx = amostra_estratificada(
        d["uf"].to_numpy(), int(busca["secoes"]), busca["semente"]
    )
    with uma_thread(), ProcessPoolExecutor(max_workers=1) as ex:
        gm0 = next(ex.map(_ajuste_amostra, [(x[idx], aj["random_state"], aj["init"])]))
    gm = refinar(gm0, x, 1e-6, 2000)
    dg = aj.get("diagnostico_convergencia", {}).get("apertado", {})
    if dg.get("adotado"):
        gm = apertar(gm, x, "continua")
    ll = np.asarray(gm.score_samples(x), dtype=float)
    bruto = gm.predict(x)
    rot = ordem_estavel(bruto, d["lula_pct"].to_numpy(float), gm.n_components)[bruto]
    ll_col = np.full(len(df), np.nan)
    cl_col = np.full(len(df), np.nan)
    ll_col[d["index"].to_numpy()] = ll
    cl_col[d["index"].to_numpy()] = rot
    ordem = np.argsort(ll, kind="stable")
    ref = [
        (r["uf"].lower(), r["mun_tse"], int(r["zona"]), int(r["secao"]), r["loglik"])
        for r in clusters.get("menos_provaveis", [])
    ]
    meu = [
        (
            d.loc[i, "uf"],
            d.loc[i, "mun"],
            int(d.loc[i, "zona"]),
            int(d.loc[i, "secao"]),
            round(float(ll[i]), 3),
        )
        for i in ordem[: len(ref)]
    ]
    iguais = sum(a[:4] == b[:4] for a, b in zip(ref, meu, strict=True))
    dif = max((abs(a[4] - b[4]) for a, b in zip(ref, meu, strict=True)), default=0.0)
    posicao = np.full(len(df), np.nan)
    posicao[d["index"].to_numpy()[ordem]] = np.arange(1, len(ordem) + 1)
    return {
        "loglik": ll_col,
        "cluster": cl_col,
        "posicao": posicao,
        "secoes": int(sel.sum()),
        "iteracoes": [int(gm0.n_iter_), int(gm.n_iter_)],
        "loglik_media": round(float(ll.mean()), 4),
        "conferencia": {
            "referencia": "secoes.json, clusters.menos_provaveis",
            "comparadas": len(ref),
            "iguais": iguais,
            "maior_diferenca_loglik": round(float(dif), 4),
        },
    }


# ---------------------------------------------------------------- contexto


def contexto_por_municipio(ctx: Mapping[str, Any]) -> dict[tuple[str, str], list[dict]]:
    """(UF, nome normalizado) → itens de `contexto_seguranca.json` que citam o município."""
    out: dict[tuple[str, str], list[dict]] = {}
    for item in ctx.get("itens", []):
        if item.get("tema") not in TEMAS_CONTEXTO:
            continue
        for m in item.get("municipios") or []:
            chave = (str(m.get("uf", "")).upper(), normalizar(m.get("nome")))
            out.setdefault(chave, []).append(
                {
                    "id": item["id"],
                    "tema": item.get("tema"),
                    "veiculo": item.get("veiculo"),
                    "data": item.get("data"),
                    "url": item.get("url"),
                    "degrau": item.get("degrau"),
                }
            )
    return out


def topo_anomalias(anomalias: Mapping[str, Any]) -> dict[tuple[str, str, int], dict]:
    return {
        (str(z["uf"]).lower(), str(z["municipio_tse"]), int(z["zona"])): z
        for z in anomalias.get("topo", [])
    }


# ---------------------------------------------------------------- explicações

EXPLICACOES: list[dict[str, str]] = [
    {
        "codigo": "aldeia",
        "rotulo": "aldeia ou terra indígena",
        "regra": "tipo de local inferido 'aldeia ou terra indígena' (ALDEIA, INDIGENA ou "
        "TERRA INDIG no nome, bairro ou endereço do local)",
        "grupo": "comum_documentada",
    },
    {
        "codigo": "presidio",
        "rotulo": "unidade prisional ou socioeducativa",
        "regra": "tipo oficial do TSE 'Preso provisório' ou nome do local com PRESIDIO, "
        "PENITENCIARIA, CADEIA, SOCIOEDUCATIV e afins",
        "grupo": "comum_documentada",
    },
    {
        "codigo": "exterior",
        "rotulo": "seção no exterior",
        "regra": "UF ZZ",
        "grupo": "comum_documentada",
    },
    {
        "codigo": "transito",
        "rotulo": "voto em trânsito",
        "regra": "tipo oficial do TSE 'Voto em trânsito' ou 20% ou mais dos aptos em trânsito",
        "grupo": "comum_documentada",
    },
    {
        "codigo": "minuscula",
        "rotulo": "seção minúscula",
        "regra": "menos de 50 votantes",
        "grupo": "comum_documentada",
    },
    {
        "codigo": "zona_rural",
        "rotulo": "zona rural",
        "regra": "tipo de local inferido 'zona rural' (POVOADO, SITIO, FAZENDA, ZONA RURAL e "
        "afins no bairro ou endereço)",
        "grupo": "provavel",
    },
    {
        "codigo": "quilombo_assentamento",
        "rotulo": "quilombo ou assentamento",
        "regra": "tipo de local inferido 'quilombo' ou 'assentamento'",
        "grupo": "provavel",
    },
    {
        "codigo": "hospital",
        "rotulo": "hospital ou unidade de saúde",
        "regra": "tipo de local inferido 'hospital ou unidade de saúde'",
        "grupo": "provavel",
    },
    {
        "codigo": "pequena",
        "rotulo": "seção pequena",
        "regra": "de 50 a 99 votantes",
        "grupo": "provavel",
    },
    {
        "codigo": "urna_trocada",
        "rotulo": "urna de contingência ou reserva",
        "regra": "tipo de urna diferente de 1 no boletim",
        "grupo": "provavel",
    },
    {
        "codigo": "enclave_2022",
        "rotulo": "já votava assim em 2022",
        "regra": "seção casada com 2022 com o mesmo campo em 90% ou mais (1º ou 2º turno)",
        "grupo": "provavel",
    },
]
COMUNS = {e["codigo"] for e in EXPLICACOES if e["grupo"] == "comum_documentada"}
ROTULO_EXPLICACAO = {e["codigo"]: e["rotulo"] for e in EXPLICACOES}


def codigos_explicacao(df: pd.DataFrame) -> pd.Series:
    """Lista de códigos de explicação por seção (regras de `EXPLICACOES`)."""
    tipo = df["tipo_inferido"].fillna("")
    votantes = df["comparecimento"].to_numpy(float)
    tem_voto = ~np.isnan(votantes)
    votantes = np.nan_to_num(votantes, nan=0.0)
    apt = df["aptos"].fillna(0).to_numpy(float)
    tte = df["aptos_tte"].fillna(0).to_numpy(float) if "aptos_tte" in df else 0 * apt
    with np.errstate(divide="ignore", invalid="ignore"):
        transito = (df["tipo_local"].fillna("") == "Voto em trânsito").to_numpy() | (
            (apt > 0) & (tte / np.where(apt > 0, apt, 1) >= 0.2)
        )
    tu = df["tipo_urna"].fillna(1).to_numpy(float)
    enclave = (
        df["enclave_2022"].fillna(False).to_numpy(bool)
        if "enclave_2022" in df
        else None
    )
    regras = {
        "aldeia": (tipo == "aldeia ou terra indígena").to_numpy(),
        "presidio": (tipo == "unidade prisional ou socioeducativa").to_numpy(),
        "exterior": (df["uf"] == "zz").to_numpy(),
        "transito": transito,
        "minuscula": tem_voto & (votantes < 50),
        "zona_rural": (tipo == "zona rural").to_numpy(),
        "quilombo_assentamento": tipo.isin(["quilombo", "assentamento"]).to_numpy(),
        "hospital": (tipo == "hospital ou unidade de saúde").to_numpy(),
        "pequena": tem_voto & (votantes >= 50) & (votantes < 100),
        "urna_trocada": tu != 1,
    }
    if enclave is not None:
        regras["enclave_2022"] = enclave
    nomes = list(regras)
    mat = np.column_stack([regras[k] for k in nomes])
    return pd.Series(
        [[nomes[j] for j in np.flatnonzero(linha)] for linha in mat], index=df.index
    )


def frase_explicacao(codigos: Sequence[str]) -> str:
    if not codigos:
        return "sem explicação comum acionada: exige explicação documental (ata e log da urna)"
    return (
        "; ".join(ROTULO_EXPLICACAO.get(c, c) for c in codigos) + " (regra declarada)"
    )


def grupo_explicacao(codigos: Sequence[str]) -> str:
    return (
        "comum_documentada"
        if any(c in COMUNS for c in codigos)
        else "exige_explicacao_documental"
    )


def carregar_json(caminho: Path) -> dict[str, Any]:
    return json.loads(caminho.read_text(encoding="utf-8"))


__all__ = ["FLAVIO", "LULA"]
