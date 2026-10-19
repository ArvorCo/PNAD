"""Bootstrap estratificado de seções e estimadores de razão de somas.

Cada urna (seção principal) é uma unidade. A reamostragem é feita com reposição dentro
de cada estrato, preservando o tamanho do estrato: para comparar com as demais seções do
mesmo município, o estrato é município × célula; para comparar com o país, só a
célula. Uma célula é a combinação das marcas da urna (categoria, local temporário,
casamento com 2022, faixa de distância), de modo que uma passada serve a todos os
grupos, que são uniões de células.

As somas por estrato saem de uma multiplicação esparsa: a matriz ``A`` (estrato × coluna
por urna) vezes as contagens de cada urna em cada réplica. O IC é o percentil 2,5 e
97,5 das réplicas.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import sparse

Metrica = tuple[str, ...]


@dataclass
class Reamostragem:
    """Somas por estrato, no ponto e em ``reps`` réplicas estratificadas."""

    estrato: np.ndarray
    valores: np.ndarray
    reps: int
    seed: int
    bloco: int = 25

    def __post_init__(self) -> None:
        ordem = np.argsort(self.estrato, kind="stable")
        est = np.asarray(self.estrato, dtype=np.int64)[ordem]
        y = np.asarray(self.valores, dtype=float)[ordem]
        self.n, self.k = y.shape
        self.s = int(est.max()) + 1 if len(est) else 0
        tam = np.bincount(est, minlength=self.s)
        ini = np.concatenate([[0], np.cumsum(tam)[:-1]])
        self._ini = ini[est]
        self._tam = tam[est]
        linhas = (est[:, None] * self.k + np.arange(self.k)[None, :]).ravel()
        colunas = np.repeat(np.arange(self.n), self.k)
        self._a = sparse.csr_matrix(
            (y.ravel(), (linhas, colunas)), shape=(self.s * self.k, self.n)
        )

    def pontual(self) -> np.ndarray:
        """Somas observadas, forma (1, estratos, colunas)."""
        return np.asarray(self._a.sum(axis=1)).reshape(1, self.s, self.k)

    def replicas(self) -> Iterator[np.ndarray]:
        """Blocos de réplicas, forma (réplicas do bloco, estratos, colunas)."""
        rng = np.random.default_rng(self.seed)
        feitas = 0
        while feitas < self.reps:
            r = min(self.bloco, self.reps - feitas)
            u = rng.random((r, self.n))
            idx = self._ini[None, :] + (u * self._tam[None, :]).astype(np.int64)
            plano = (np.arange(r, dtype=np.int64)[:, None] * self.n + idx).ravel()
            cont = np.bincount(plano, minlength=r * self.n).reshape(r, self.n)
            somas = (self._a @ cont.T.astype(float)).T.reshape(r, self.s, self.k)
            feitas += r
            yield somas


def agregador(
    grupo_estrato: np.ndarray, mascara: np.ndarray, m: int
) -> sparse.csr_matrix:
    """Matriz (grupos × estratos) que soma os estratos marcados em cada grupo."""
    sel = np.flatnonzero(mascara)
    return sparse.csr_matrix(
        (np.ones(len(sel)), (grupo_estrato[sel], sel)), shape=(m, len(mascara))
    )


def agregar(somas: np.ndarray, matriz: sparse.csr_matrix) -> np.ndarray:
    """(réplicas, estratos, colunas) -> (réplicas, grupos, colunas)."""
    r, s, k = somas.shape
    plano = somas.transpose(1, 0, 2).reshape(s, r * k)
    out = matriz @ plano
    return np.asarray(out).reshape(matriz.shape[0], r, k).transpose(1, 0, 2)


def valor_metrica(agg: np.ndarray, metrica: Metrica, col: dict[str, int]) -> np.ndarray:
    """Avalia a métrica sobre somas agregadas (última dimensão = colunas)."""
    tipo = metrica[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        if tipo == "razao":
            return agg[..., col[metrica[1]]] / agg[..., col[metrica[2]]]
        if tipo == "dif_razao":
            a = agg[..., col[metrica[1]]] / agg[..., col[metrica[2]]]
            b = agg[..., col[metrica[3]]] / agg[..., col[metrica[4]]]
            return a - b
    raise ValueError(f"métrica desconhecida: {metrica}")


def ponderada_mun(
    trat: np.ndarray,
    ctrl: np.ndarray,
    metrica: Metrica,
    peso: str,
    col: dict[str, int],
    usar: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Valor do grupo e dos controles, município a município, ponderado pelo grupo.

    ``trat`` e ``ctrl`` têm forma (réplicas, municípios, colunas); ``usar`` marca os
    municípios avaliáveis no ponto, fixos nas réplicas.
    """
    rt = valor_metrica(trat[:, usar, :], metrica, col)
    rc = valor_metrica(ctrl[:, usar, :], metrica, col)
    w = trat[:, usar, col[peso]]
    bom = np.isfinite(rt) & np.isfinite(rc) & (w > 0)
    w = np.where(bom, w, 0.0)
    soma = w.sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        vt = (np.where(bom, rt, 0.0) * w).sum(axis=-1) / soma
        vc = (np.where(bom, rc, 0.0) * w).sum(axis=-1) / soma
    return vt, vc


def avaliaveis(
    trat: np.ndarray, ctrl: np.ndarray, metrica: Metrica, peso: str, col: dict[str, int]
) -> np.ndarray:
    """Municípios com os dois lados avaliáveis no ponto (forma (1, M, K))."""
    rt = valor_metrica(trat[0], metrica, col)
    rc = valor_metrica(ctrl[0], metrica, col)
    return np.isfinite(rt) & np.isfinite(rc) & (trat[0][:, col[peso]] > 0)


def resumo_ic(
    ponto: float, reps: np.ndarray, escala: float = 100.0, casas: int = 2
) -> dict:
    """Ponto, IC 95% por percentil e erro-padrão das réplicas, na escala pedida."""
    r = np.asarray(reps, dtype=float)
    r = r[np.isfinite(r)]
    if ponto is None or not np.isfinite(ponto) or not len(r):
        return {"valor": None, "ic95": None, "ep": None}
    lo, hi = np.percentile(r, [2.5, 97.5])
    return {
        "valor": round(float(ponto) * escala, casas),
        "ic95": [round(float(lo) * escala, casas), round(float(hi) * escala, casas)],
        "ep": round(float(r.std(ddof=1)) * escala, casas + 1),
    }


def bootstrap_estatistica(
    grupos: Sequence[np.ndarray],
    funcao: Callable[..., float],
    reps: int,
    seed: int,
) -> tuple[float, np.ndarray]:
    """Bootstrap simples, independente por grupo, de uma estatística de amostras."""
    rng = np.random.default_rng(seed)
    ponto = funcao(*grupos)
    saida = np.empty(reps)
    for i in range(reps):
        amostras = [g[rng.integers(0, len(g), len(g))] if len(g) else g for g in grupos]
        saida[i] = funcao(*amostras)
    return float(ponto), saida
