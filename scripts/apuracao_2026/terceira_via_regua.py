"""Régua da urna de 2022: regressão ecológica da conversão da terceira via entre os turnos.

Unidade: município (os 5.570 com resultado de 2022). Para cada um, com ``V`` os
votantes de presidente no 1º turno de 2022:

- ``yB = (Bolsonaro 2º turno − Bolsonaro 1º turno) / V`` e ``yL`` igual para Lula;
- ``x_tv = votos de terceira via no 1º turno / V`` (Simone Tebet, Ciro Gomes e demais);
- ``x_bn = brancos e nulos no 1º turno / V``.

Modelo, ponderado por ``V``, com efeito fixo de UF (transformação interna por UF,
teorema de Frisch-Waugh-Lovell): ``y = a_UF + Σ_g b_g · x_tv · 1[grupo = g] + c · x_bn``.
O coeficiente ``b_g`` lê-se como votos líquidos ganhos por voto de terceira via do
1º turno, no grupo ``g`` (classe de margem de Flávio em 2026, ou região), dentro da
mesma UF. O saldo Bolsonaro menos Lula é ``bB − bL``, exatamente, porque as duas
regressões têm o mesmo desenho.

Intervalos: bootstrap de municípios (reamostragem com reposição, os mesmos sorteios
para Bolsonaro e Lula), percentis 2,5 e 97,5.

Limite fixo: inferência ecológica, de agregado para agregado. Não diz como votou o
eleitor de Tebet ou de Ciro; diz quanto o saldo cresceu a mais onde havia mais
terceira via, na mesma UF. A terceira via de 2022 era outra.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from . import terceira_via as T

SEMENTE = 20261005
N_BOOT = 1000
REGIOES = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")


def _r(x: float | None, casas: int = 4) -> float | None:
    return None if x is None else round(float(x), casas)


def amostra(linhas: Sequence[dict]) -> list[dict]:
    """Municípios com 2022 completo: terceira via, ganhos e brancos e nulos do 1º turno."""
    return [
        m
        for m in linhas
        if m.get("tv22") is not None
        and m.get("comp22_1t")
        and m.get("bn22_1t") is not None
        and m.get("ganho_b22") is not None
    ]


def desenho(
    linhas: Sequence[dict], chave: str | None, rotulos: Sequence[str]
) -> dict[str, np.ndarray]:
    """Matrizes do modelo. ``chave=None`` dá uma inclinação só para a terceira via."""
    V = np.array([m["comp22_1t"] for m in linhas], dtype=float)
    x_tv = np.array([m["tv22"] for m in linhas], dtype=float) / V
    x_bn = np.array([m["bn22_1t"] for m in linhas], dtype=float) / V
    if chave is None:
        colunas = [x_tv]
    else:
        grupo = np.array([rotulos.index(m[chave]) for m in linhas])
        colunas = [x_tv * (grupo == k) for k in range(len(rotulos))]
    ufs = sorted({m["uf"] for m in linhas})
    return {
        "V": V,
        "X": np.column_stack([*colunas, x_bn]),
        "Y": np.column_stack(
            [
                np.array([m["ganho_b22"] for m in linhas], dtype=float) / V,
                np.array([m["ganho_l22"] for m in linhas], dtype=float) / V,
            ]
        ),
        "g": np.array([ufs.index(m["uf"]) for m in linhas]),
    }


def _interno(A: np.ndarray, w: np.ndarray, g: np.ndarray, n_g: int) -> np.ndarray:
    """Cada coluna menos a média ponderada da própria UF."""
    sw = np.bincount(g, weights=w, minlength=n_g)
    sw = np.where(sw > 0, sw, 1.0)
    medias = np.column_stack(
        [
            np.bincount(g, weights=w * A[:, j], minlength=n_g) / sw
            for j in range(A.shape[1])
        ]
    )
    return A - medias[g]


def ajustar(
    X: np.ndarray, Y: np.ndarray, w: np.ndarray, g: np.ndarray, efeito_fixo: bool = True
) -> np.ndarray:
    """Mínimos quadrados ponderados; devolve coeficientes (colunas de X) × (colunas de Y).

    Sem efeito fixo, acrescenta a constante e devolve-a na última linha.
    """
    if efeito_fixo:
        n_g = int(g.max()) + 1
        Xd, Yd = _interno(X, w, g, n_g), _interno(Y, w, g, n_g)
    else:
        Xd = np.column_stack([X, np.ones(len(X))])
        Yd = Y
    # einsum em vez de matmul: o BLAS do macOS emite avisos espúrios de ponto
    # flutuante em matmul; o resultado é conferido como finito logo abaixo.
    xtx = np.einsum("ij,i,ik->jk", Xd, w, Xd)
    xty = np.einsum("ij,i,ik->jk", Xd, w, Yd)
    coef = np.linalg.solve(xtx, xty)
    if not np.all(np.isfinite(coef)):
        raise FloatingPointError("coeficientes não finitos na régua da urna")
    return coef


def bootstrap(
    d: dict[str, np.ndarray], n_boot: int = N_BOOT, semente: int = SEMENTE
) -> np.ndarray:
    """Coeficientes de cada réplica: n_boot × colunas de X × (Bolsonaro, Lula)."""
    rng = np.random.default_rng(semente)
    n = len(d["V"])
    p = np.full(n, 1.0 / n)
    saida = np.empty((n_boot, d["X"].shape[1], 2))
    for b in range(n_boot):
        w = d["V"] * rng.multinomial(n, p)
        saida[b] = ajustar(d["X"], d["Y"], w, d["g"])
    return saida


def _faixa(v: np.ndarray) -> list[float | None]:
    return [_r(np.percentile(v, 2.5)), _r(np.percentile(v, 97.5))]


def modelo(
    linhas: Sequence[dict],
    chave: str | None,
    rotulos: Sequence[str],
    n_boot: int = N_BOOT,
    semente: int = SEMENTE,
) -> dict[str, Any]:
    """Coeficientes por grupo (Bolsonaro, Lula, saldo) com intervalo, e o de brancos e nulos."""
    d = desenho(linhas, chave, rotulos)
    coef = ajustar(d["X"], d["Y"], d["V"], d["g"])
    boot = bootstrap(d, n_boot, semente)
    saldo_boot = boot[:, :, 0] - boot[:, :, 1]
    grupos = list(rotulos) if chave is not None else ["todos"]
    por_grupo = {}
    for k, nome in enumerate(grupos):
        dentro = linhas if chave is None else [m for m in linhas if m[chave] == nome]
        por_grupo[nome] = {
            "municipios": len(dentro),
            "terceira_via_2022": int(sum(m["tv22"] for m in dentro)),
            "bolsonaro": _r(coef[k, 0]),
            "lula": _r(coef[k, 1]),
            "saldo": _r(coef[k, 0] - coef[k, 1]),
            "fora": _r(1 - coef[k, 0] - coef[k, 1]),
            "saldo_ic95": _faixa(saldo_boot[:, k]),
            "bolsonaro_ic95": _faixa(boot[:, k, 0]),
            "lula_ic95": _faixa(boot[:, k, 1]),
        }
    j = len(grupos)
    return {
        "chave": chave,
        "grupos": por_grupo,
        "brancos_nulos": {
            "saldo": _r(coef[j, 0] - coef[j, 1]),
            "saldo_ic95": _faixa(saldo_boot[:, j]),
        },
        "municipios": len(linhas),
        "n_boot": n_boot,
        "semente": semente,
        "_saldo_boot": saldo_boot[:, :j],
        "_coef": coef[:j],
    }


def sem_efeito_fixo(linhas: Sequence[dict]) -> dict[str, float | None]:
    """Inclinação única sem efeito fixo de UF, para mostrar o que o efeito fixo tira."""
    d = desenho(linhas, None, [])
    coef = ajustar(d["X"], d["Y"], d["V"], d["g"], efeito_fixo=False)
    return {
        "saldo_terceira_via": _r(coef[0, 0] - coef[0, 1]),
        "saldo_brancos_nulos": _r(coef[1, 0] - coef[1, 1]),
        "constante": _r(coef[2, 0] - coef[2, 1]),
    }


# ---------------------------------------------------------------- aplicação a 2026


def aplicar(
    brasil: list[dict],
    classe: dict[str, Any],
    regiao: dict[str, Any],
    razao: dict[str, Any],
) -> None:
    """Votos esperados por município pela régua da urna (classe; região e razão simples à parte)."""
    gc, gr = classe["grupos"], regiao["grupos"]
    for m in brasil:
        c = gc[m["classe"]]
        e = m["estoque"]
        m["pv_urna"] = c["saldo"]
        m["saldo_urna"] = e * c["saldo"]
        m["para_flavio_urna"] = e * c["bolsonaro"]
        m["para_lula_urna"] = e * c["lula"]
        m["saldo_urna_regiao"] = e * gr[m["regiao"]]["saldo"]
        m["saldo_razao"] = e * (razao[m["classe"]]["saldo"] or 0.0)


def total_ic(brasil: Sequence[dict], classe: dict[str, Any]) -> list[float | None]:
    """Intervalo do saldo nacional pela régua da urna: as réplicas do bootstrap aplicadas ao estoque."""
    estoques = np.array(
        [sum(m["estoque"] for m in brasil if m["classe"] == c) for c in T.CLASSES],
        dtype=float,
    )
    totais = (classe["_saldo_boot"] * estoques).sum(axis=1)
    return [_r(np.percentile(totais, 2.5), 0), _r(np.percentile(totais, 97.5), 0)]
