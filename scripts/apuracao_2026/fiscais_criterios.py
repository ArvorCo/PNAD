"""Critérios de prioridade de fiscalização por seção (capítulo 13).

Cada critério é uma regra com limiar declarado, aplicada de forma vetorial à base
do universo (`fiscais_base.universo`). A pontuação soma pesos declarados; o nível
(alta, média, baixa) sai de cortes declarados, e a explicação comum documentada
(aldeia, presídio, exterior, trânsito, seção minúscula) tira a seção do nível alta.

Atipicidade estatística não é irregularidade; a lista é de prioridade de
fiscalização, não de acusação; o que resolve cada item é a ata da mesa, o log da
urna e a presença do fiscal.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pandas as pd

from .fiscais_base import COMUNS
from .secoes_base import FLAVIO, LULA

IDS = ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l")
DE_SECAO = ("a", "b", "c", "d", "e", "f", "j", "k")  # contam para o critério l
PESOS: dict[str, int] = {
    "a": 3,
    "b": 3,
    "c": 3,
    "d": 2,
    "e": 2,
    "f": 2,
    "g": 1,
    "h_sem_arquivo": 3,
    "h_zona_congelada": 1,
    "i": 1,
    "j": 2,
    "k": 1,
    "l": 2,
}
CORTE_ALTA = 5
CORTE_MEDIA = 3
CORTE_ALTA_IGUAIS = 3
CORTE_MEDIA_IGUAIS = 2
NIVEIS = ("alta", "media", "baixa")

# limiares
A_PCT, A_VOTANTES, A_EXCESSO = 90.0, 100, 20.0
B_VOTANTES = 150
C_APTOS = 50
D_HORA, D_EXCESSO = "2026-10-04 19:00:00", 10.0
E_TOP = 200
F_DIF = 10.0
G_HORA = "2026-10-05 00:00:00"
I_EXCESSO_UF = 10.0
J_MIN_VOTOS, J_DESVIOS = 50, 3.0
K_DESVIOS, K_PP, K_VOTANTES, K_OUTRAS = 3.0, 3.0, 50, 8
L_MIN = 3


def _f(df: pd.DataFrame, col: str) -> np.ndarray:
    return df[col].to_numpy(dtype=float)


def crit_a(df: pd.DataFrame) -> pd.DataFrame:
    lp, fp = _f(df, "lula_pct"), _f(df, "flavio_pct")
    lula_maior = np.nan_to_num(lp, nan=-1) >= np.nan_to_num(fp, nan=-1)
    pct = np.where(lula_maior, lp, fp)
    resto = np.where(
        lula_maior, _f(df, "zona_resto_lula_pct"), _f(df, "zona_resto_flavio_pct")
    )
    exc = pct - resto
    with np.errstate(invalid="ignore"):
        dispara = (
            (pct >= A_PCT)
            & (_f(df, "comparecimento") >= A_VOTANTES)
            & (np.nan_to_num(exc, nan=-999) >= A_EXCESSO)
        )
    l22 = np.fmax(_f(df, "lula22_pct"), _f(df, "lula22_2t_pct"))
    b22 = np.fmax(_f(df, "bolso22_pct"), _f(df, "bolso22_2t_pct"))
    campo22 = np.where(lula_maior, l22, b22)
    enclave = dispara & (np.nan_to_num(campo22, nan=-1) >= A_PCT)
    return pd.DataFrame(
        {
            "a": dispara,
            "a_cand": np.where(lula_maior, "lula", "flavio"),
            "a_pct": pct,
            "a_exc": exc,
            "a_pct_2022": campo22,
            "enclave_2022": enclave,
        },
        index=df.index,
    )


def crit_b(df: pd.DataFrame) -> pd.DataFrame:
    zl = df[f"v{LULA}"].to_numpy() == 0
    zf = df[f"v{FLAVIO}"].to_numpy() == 0
    dispara = (zl | zf) & (_f(df, "comparecimento") >= B_VOTANTES)
    quem = np.where(zl & zf, "lula e flavio", np.where(zl, "lula", "flavio"))
    return pd.DataFrame({"b": dispara, "b_quem": quem}, index=df.index)


def crit_c(df: pd.DataFrame) -> pd.DataFrame:
    apt, comp = _f(df, "aptos"), _f(df, "comparecimento")
    dispara = (apt >= C_APTOS) & (comp >= apt)
    return pd.DataFrame({"c": dispara}, index=df.index)


def crit_d(df: pd.DataFrame) -> pd.DataFrame:
    enc = df["_enc"]
    exc = _f(df, "lula_pct") - _f(df, "zona_resto_lula_pct")
    tarde = (enc >= pd.Timestamp(D_HORA)).to_numpy() & (df["uf"] != "zz").to_numpy()
    dispara = tarde & (np.nan_to_num(exc, nan=-999) >= D_EXCESSO)
    return pd.DataFrame({"d": dispara, "d_exc": exc}, index=df.index)


def crit_e(df: pd.DataFrame, posicao: np.ndarray) -> pd.DataFrame:
    pos = np.asarray(posicao, dtype=float)
    dispara = np.nan_to_num(pos, nan=np.inf) <= E_TOP
    return pd.DataFrame({"e": dispara, "e_pos": pos}, index=df.index)


def crit_f(df: pd.DataFrame) -> pd.DataFrame:
    fora = (
        (df["tipo_arquivo"].fillna(1).to_numpy(float) != 1)
        | (df["tipo_urna"].fillna(1).to_numpy(float) != 1)
        | (df["n_cargas"].fillna(1).to_numpy(float) > 1)
    )
    dl = _f(df, "lula_pct") - _f(df, "zona_resto_lula_pct")
    dfv = _f(df, "flavio_pct") - _f(df, "zona_resto_flavio_pct")
    maior = np.fmax(np.abs(dl), np.abs(dfv))
    dispara = fora & (np.nan_to_num(maior, nan=-1) >= F_DIF)
    return pd.DataFrame(
        {"f": dispara, "f_dif_lula": dl, "f_dif_flavio": dfv}, index=df.index
    )


def crit_g(df: pd.DataFrame) -> pd.DataFrame:
    dispara = (df["_dr"] >= pd.Timestamp(G_HORA)).to_numpy() & (
        df["uf"] != "zz"
    ).to_numpy()
    return pd.DataFrame({"g": dispara}, index=df.index)


def crit_h(df: pd.DataFrame, congelada: np.ndarray) -> pd.DataFrame:
    """h(2): seção que faltava num arquivo de zona congelado (`secoes_congeladas`).

    h(1) (sem arquivo) não está nesta base: as seções sem boletim entram à parte.
    """
    marca = np.asarray(congelada, dtype=bool)
    return pd.DataFrame(
        {"h": marca, "h_tipo": np.where(marca, "zona_congelada", "")}, index=df.index
    )


def crit_i(df: pd.DataFrame, topo: Mapping[tuple[str, str, int], Any]) -> pd.DataFrame:
    chaves = set(topo)
    no_topo = np.array(
        [
            (u, m, int(z)) in chaves
            for u, m, z in zip(df["uf"], df["mun"], df["zona"], strict=True)
        ]
    )
    el = _f(df, "lula_pct") - _f(df, "uf_lula_pct")
    ef = _f(df, "flavio_pct") - _f(df, "uf_flavio_pct")
    maior = np.fmax(el, ef)
    dispara = no_topo & (np.nan_to_num(maior, nan=-999) >= I_EXCESSO_UF)
    return pd.DataFrame(
        {"i": dispara, "i_exc_lula": el, "i_exc_flavio": ef, "i_topo": no_topo},
        index=df.index,
    )


def crit_j(df: pd.DataFrame) -> pd.DataFrame:
    """Variação da margem 2022-2026 da mesma seção fora de média ± 3 dp da UF."""
    marg26 = _f(df, "flavio_pct") - _f(df, "lula_pct")
    marg22 = _f(df, "bolso22_pct") - _f(df, "lula22_pct")
    swing = marg26 - marg22
    ok = (
        df["mesma_secao"].fillna(False).to_numpy(bool)
        & (np.nan_to_num(_f(df, "nominais_1t"), nan=0) >= J_MIN_VOTOS)
        & (_f(df, "validos") >= J_MIN_VOTOS)
        & np.isfinite(swing)
    )
    tab = pd.DataFrame({"uf": df["uf"].to_numpy(), "s": np.where(ok, swing, np.nan)})
    g = tab.groupby("uf")["s"]
    media = g.transform("mean").to_numpy()
    dp = g.transform("std").to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (swing - media) / dp
    dispara = ok & (np.abs(np.nan_to_num(z, nan=0)) > J_DESVIOS)
    return pd.DataFrame(
        {
            "j": dispara,
            "j_swing": np.where(ok, swing, np.nan),
            "j_media": media,
            "j_dp": dp,
            "j_z": np.where(ok, z, np.nan),
        },
        index=df.index,
    )


def _loo(chave: pd.Series, p: np.ndarray, valido: np.ndarray) -> tuple[np.ndarray, ...]:
    """Média e desvio-padrão (amostral) das OUTRAS seções da mesma zona."""
    x = np.where(valido, p, 0.0)
    w = valido.astype(float)
    t = pd.DataFrame({"k": chave.to_numpy(), "x": x, "x2": x * x, "w": w})
    s = t.groupby("k")[["x", "x2", "w"]].transform("sum")
    n = s["w"].to_numpy() - w
    sx = s["x"].to_numpy() - x
    sx2 = s["x2"].to_numpy() - x * x
    with np.errstate(divide="ignore", invalid="ignore"):
        media = sx / n
        var = (sx2 - n * media * media) / (n - 1)
    dp = np.sqrt(np.clip(var, 0, None))
    return media, dp, n


def crit_k(df: pd.DataFrame) -> pd.DataFrame:
    chave = (
        df["uf"].astype(str)
        + "|"
        + df["mun"].astype(str)
        + "|"
        + df["zona"].astype(str)
    )
    comp = _f(df, "comparecimento")
    tem = comp > 0
    saida: dict[str, Any] = {}
    dispara = np.zeros(len(df), dtype=bool)
    for parte in ("brancos", "nulos"):
        p = np.where(tem, 100 * _f(df, parte) / np.where(tem, comp, 1), np.nan)
        media, dp, n = _loo(chave, np.nan_to_num(p), tem)
        with np.errstate(divide="ignore", invalid="ignore"):
            z = (p - media) / dp
        d = (
            (comp >= K_VOTANTES)
            & (n >= K_OUTRAS)
            & (dp > 0)
            & (np.nan_to_num(z, nan=0) >= K_DESVIOS)
            & (np.nan_to_num(p - media, nan=0) >= K_PP)
        )
        dispara |= d
        saida[f"k_{parte}"] = d
        saida[f"k_{parte}_pct"] = p
        saida[f"k_{parte}_media"] = media
        saida[f"k_{parte}_z"] = z
    saida["k"] = dispara
    return pd.DataFrame(saida, index=df.index)


def crit_l(df: pd.DataFrame, marcas: pd.DataFrame) -> pd.DataFrame:
    de_secao = marcas[list(DE_SECAO)].any(axis=1)
    n = de_secao.groupby(df["local_id"]).transform("sum").to_numpy()
    dispara = de_secao.to_numpy() & (n >= L_MIN)
    return pd.DataFrame({"l": dispara, "l_n": n}, index=df.index)


# ---------------------------------------------------------------- pontuação e nível


def pontuar(marcas: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Pontuação com pesos declarados e com pesos iguais (número de critérios)."""
    pont = np.zeros(len(marcas))
    iguais = np.zeros(len(marcas))
    for c in IDS:
        if c == "h":
            sem = marcas["h_tipo"].to_numpy() == "sem_arquivo"
            peso = np.where(sem, PESOS["h_sem_arquivo"], PESOS["h_zona_congelada"])
        else:
            peso = PESOS[c]
        m = marcas[c].to_numpy(bool)
        pont += np.where(m, peso, 0)
        iguais += m
    return pont.astype(int), iguais.astype(int)


def nivel(
    pontuacao: int, comum: bool, enclave: bool, alta: int, media: int
) -> str | None:
    """Alta só sem explicação comum; com ela, um degrau abaixo; enclave, baixa."""
    if pontuacao <= 0:
        return None
    if enclave:
        return "baixa"
    if pontuacao >= alta:
        return "media" if comum else "alta"
    if pontuacao >= media:
        return "baixa" if comum else "media"
    return "baixa"


def niveis(
    pont: Iterable[int],
    comum: Iterable[bool],
    enclave: Iterable[bool],
    alta: int,
    media: int,
) -> list[str | None]:
    return [
        nivel(int(p), bool(c), bool(e), alta, media)
        for p, c, e in zip(pont, comum, enclave, strict=True)
    ]


def aplicar(
    df: pd.DataFrame,
    posicao_mistura: np.ndarray,
    congelada: np.ndarray,
    topo: Mapping[tuple[str, str, int], Any],
) -> pd.DataFrame:
    """Todas as marcas e detalhes, a pontuação e os dois níveis."""
    partes = [
        crit_a(df),
        crit_b(df),
        crit_c(df),
        crit_d(df),
        crit_e(df, posicao_mistura),
        crit_f(df),
        crit_g(df),
        crit_h(df, congelada),
        crit_i(df, topo),
        crit_j(df),
        crit_k(df),
    ]
    marcas = pd.concat(partes, axis=1)
    marcas = pd.concat([marcas, crit_l(df, marcas)], axis=1)
    return finalizar(marcas, df["explicacao_codigos"])


def finalizar(marcas: pd.DataFrame, codigos: pd.Series) -> pd.DataFrame:
    pont, iguais = pontuar(marcas)
    comum = np.array([any(c in COMUNS for c in cs) for cs in codigos])
    enclave = marcas["enclave_2022"].to_numpy(bool)
    marcas["pontuacao"] = pont
    marcas["pontuacao_iguais"] = iguais
    marcas["comum"] = comum
    marcas["nivel"] = niveis(pont, comum, enclave, CORTE_ALTA, CORTE_MEDIA)
    marcas["nivel_iguais"] = niveis(
        iguais, comum, enclave, CORTE_ALTA_IGUAIS, CORTE_MEDIA_IGUAIS
    )
    marcas["criterios"] = [
        [c for c in IDS if linha[c]] for linha in marcas[list(IDS)].to_dict("records")
    ]
    return marcas


def marcas_sem_arquivo(n: int) -> pd.DataFrame:
    """Marcas das seções sem arquivo publicado: só o critério h(1)."""
    base = {c: np.zeros(n, dtype=bool) for c in IDS}
    base["h"] = np.ones(n, dtype=bool)
    base["h_tipo"] = np.full(n, "sem_arquivo")
    base["enclave_2022"] = np.zeros(n, dtype=bool)
    return pd.DataFrame(base)


ORDEM_NIVEL = {"alta": 0, "media": 1, "baixa": 2}
