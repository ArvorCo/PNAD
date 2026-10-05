"""Estimadores do capítulo de fechamento: dentro da zona, com intervalo por bootstrap.

Dois estimadores, os dois com reamostragem de zonas (2.000 reamostras, semente
20261005, a mesma da análise por seção):

- `dentro_zona`: o estimador do modelo de urna (`secoes_urna.diferenca_dentro`),
  reaproveitado com o grupo "tarde" no lugar do modelo mais novo e "demais" no do
  mais velho. Em cada zona com os dois grupos, a diferença entre o percentual
  agregado de cada grupo; média ponderada pelos votantes comparados.
- `fe_wls`: regressão por mínimos quadrados ponderados com efeito fixo de zona
  (absorvido pelo desvio da média ponderada da zona). O bootstrap reamostra
  zonas inteiras; como o efeito fixo é por zona, cada zona contribui com a sua
  própria matriz X'WX e o vetor X'Wy, e cada reamostra é uma soma ponderada
  dessas contribuições.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from . import secoes_urna
from .secoes_base import FLAVIO, LULA, r2

BOOT = secoes_urna.BOOT
SEMENTE = secoes_urna.SEMENTE


def dentro_zona(
    df: pd.DataFrame,
    tarde: pd.Series,
    metricas: Mapping[str, tuple[str, ...]],
    unidade: Sequence[str] = ("uf", "mun", "zona"),
    minimo: int = 1,
) -> dict[str, Any] | None:
    """Diferença tarde menos demais dentro da unidade, pelo estimador do modelo de urna.

    O estimador lê o grupo da coluna `modelo_urna`; aqui ela recebe "tarde" ou
    "demais". Colunas auxiliares para métricas que não são percentual:
    `cem` (100 por seção: dá votantes por seção) e `horas_x100` (horas abertas
    vezes 100: dá votantes por hora).
    """
    d = df.copy()
    marca = tarde.reindex(d.index, fill_value=False).to_numpy(dtype=bool)
    d["modelo_urna"] = np.where(marca, "tarde", "demais")
    d["cem"] = 100.0
    if "horas" in d:
        d["horas_x100"] = 100.0 * d["horas"]
    cols = {c for m in metricas.values() for c in m}
    d = d.dropna(subset=[c for c in cols if c in d])
    return secoes_urna.diferenca_dentro(
        d, list(unidade), "demais", "tarde", minimo, metricas
    )


def fe_wls(
    y: Sequence[float] | np.ndarray,
    x: np.ndarray,
    grupos: Sequence[Any] | np.ndarray,
    w: Sequence[float] | np.ndarray,
    nomes: Sequence[str],
    absorver: bool = True,
    boot: int = BOOT,
    semente: int = SEMENTE,
) -> dict[str, Any] | None:
    """Mínimos quadrados ponderados com efeito fixo de grupo e bootstrap de grupos.

    Devolve, para cada coluna de `x` (na ordem de `nomes`), a estimativa, o erro
    padrão (desvio das reamostras) e o intervalo de 95% (percentis 2,5 e 97,5);
    mais o R² dentro do grupo, o número de observações e de grupos. Com
    `absorver=False` não há efeito fixo: entra um intercepto e o bootstrap
    continua reamostrando grupos (erro agrupado pela zona).
    """
    yv = np.asarray(y, dtype=float)
    xv = np.asarray(x, dtype=float)
    if xv.ndim == 1:
        xv = xv[:, None]
    wv = np.asarray(w, dtype=float)
    ok = np.isfinite(yv) & np.isfinite(xv).all(axis=1) & np.isfinite(wv) & (wv > 0)
    yv, xv, wv = yv[ok], xv[ok], wv[ok]
    if len(yv) < 3:
        return None
    codigos, _uniq = pd.factorize(pd.Series(np.asarray(grupos, dtype=object)[ok]))
    g = int(codigos.max()) + 1
    if absorver:
        sw = np.bincount(codigos, weights=wv, minlength=g)
        my = np.bincount(codigos, weights=wv * yv, minlength=g) / sw
        yd = yv - my[codigos]
        xd = np.empty_like(xv)
        for j in range(xv.shape[1]):
            mx = np.bincount(codigos, weights=wv * xv[:, j], minlength=g) / sw
            xd[:, j] = xv[:, j] - mx[codigos]
        desloc = 0
    else:
        yd = yv
        xd = np.column_stack([np.ones(len(yv)), xv])
        desloc = 1
    k = xd.shape[1]
    a = np.zeros((g, k, k))
    b = np.zeros((g, k))
    for i in range(k):
        b[:, i] = np.bincount(codigos, weights=wv * xd[:, i] * yd, minlength=g)
        for j in range(i, k):
            v = np.bincount(codigos, weights=wv * xd[:, i] * xd[:, j], minlength=g)
            a[:, i, j] = v
            a[:, j, i] = v
    rng = np.random.default_rng(semente)
    cont = rng.multinomial(g, np.full(g, 1.0 / g), size=boot).astype(float)
    # O NumPy 2 com o Accelerate do macOS acusa divisão por zero falsa em produto de
    # matrizes finitas; o resultado é conferido logo abaixo, então o aviso é calado.
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        beta = np.linalg.pinv(a.sum(axis=0)) @ b.sum(axis=0)
        ab = (cont @ a.reshape(g, k * k)).reshape(boot, k, k)
        bb = cont @ b
        betas = (np.linalg.pinv(ab) @ bb[:, :, None])[:, :, 0]
        resid = yd - xd @ beta
    if not (np.isfinite(beta).all() and np.isfinite(resid).all()):
        raise ValueError("regressão com coeficiente não finito")
    centro = yd - (np.average(yd, weights=wv) if not absorver else 0.0)
    sst = float((wv * centro**2).sum())
    r2_ = 1 - float((wv * resid**2).sum()) / sst if sst > 0 else None
    coef = {}
    for j, nome in enumerate(nomes):
        col = betas[:, j + desloc]
        col = col[np.isfinite(col)]
        coef[nome] = {
            "estimativa": r2(beta[j + desloc], 3),
            "ep": r2(col.std(ddof=1), 3) if len(col) > 1 else None,
            "ic95": [r2(np.percentile(col, 2.5), 3), r2(np.percentile(col, 97.5), 3)],
        }
    return {
        "coeficientes": coef,
        "r2_dentro" if absorver else "r2": r2(r2_, 4),
        "observacoes": len(yv),
        "zonas": g,
        "bootstrap": boot,
        "semente": semente,
    }


def dummies(
    serie: pd.Series, referencia: str, ordem: Sequence[str] | None = None
) -> tuple[np.ndarray, list[str]]:
    """Colunas 0/1 para cada categoria exceto a de referência (ordem declarada)."""
    cats = list(ordem) if ordem else sorted(serie.dropna().unique())
    cats = [c for c in cats if c != referencia and (serie == c).any()]
    if not cats:
        return np.zeros((len(serie), 0)), []
    m = np.column_stack([(serie == c).to_numpy(dtype=float) for c in cats])
    return m, cats


def dif_zona_w6(g: pd.DataFrame, chave: str) -> float | None:
    """O cálculo da análise por seção (`secoes_extremos._dif_zona`), refeito aqui.

    Média, ponderada pelos válidos de cada seção do grupo, da diferença entre o
    percentual da seção e o do resto da própria zona (a zona sem aquela seção,
    incluídas as outras seções do mesmo grupo).
    """
    d = g[f"{chave}_pct"] - g[f"zona_resto_{chave}_pct"]
    wv = g["validos"].where(d.notna(), 0)
    if wv.sum() == 0:
        return None
    return r2((d.fillna(0) * wv).sum() / wv.sum())


def dif_secao_contra_demais(
    g: pd.DataFrame, tarde: pd.Series, chave: str
) -> float | None:
    """Cada seção tardia contra o agregado das seções não tardias da mesma zona.

    Mesmo peso da análise por seção (válidos da seção tardia); a zona sem seção
    não tardia fica fora. Separa o efeito de tirar as outras tardias do grupo de
    comparação do efeito de trocar o peso.
    """
    num = {"lula": f"v{LULA}", "flavio": f"v{FLAVIO}"}[chave]
    zona = ["uf", "mun", "zona"]
    marca = tarde.reindex(g.index, fill_value=False).to_numpy(dtype=bool)
    demais = g[~marca].groupby(zona)[[num, "validos"]].sum()
    demais = demais[demais["validos"] > 0]
    t = g[marca].merge(
        demais.rename(columns={num: "_n", "validos": "_v"}),
        left_on=zona,
        right_index=True,
        how="inner",
    )
    if t.empty:
        return None
    d = t[f"{chave}_pct"] - 100 * t["_n"] / t["_v"]
    return r2((d * t["validos"]).sum() / t["validos"].sum())
