"""Bootstrap por célula de clima e regressões com efeito fixo.

Unidade de reamostragem: a célula de 0,25°. Todas as urnas de uma célula têm o mesmo
clima, então a célula é o conglomerado natural; reamostrar urnas trataria como
independentes urnas que dividem a mesma chuva e estreitaria o intervalo à toa. Cada
réplica sorteia as células com reposição (pesos multinomiais) e refaz as somas.

Regressões: statsmodels, com erro-padrão robusto por conglomerado de célula. Efeito
fixo de UF por variáveis indicadoras; efeito fixo de município por subtração das médias
ponderadas (Frisch-Waugh-Lovell), que dá o mesmo coeficiente sem 5 mil colunas.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import sparse

Z95 = 1.959963984540054


@dataclass
class BootCelulas:
    """Pesos de réplica por célula: contagens multinomiais que somam o nº de células."""

    n_celulas: int
    reps: int
    seed: int = 20261004
    bloco: int = 100

    def blocos(self) -> Iterator[np.ndarray]:
        rng = np.random.default_rng(self.seed)
        p = np.full(self.n_celulas, 1.0 / self.n_celulas)
        feitas = 0
        while feitas < self.reps:
            r = min(self.bloco, self.reps - feitas)
            yield rng.multinomial(self.n_celulas, p, size=r).astype(float)
            feitas += r


def matriz_somas(
    cel: np.ndarray, grupo: np.ndarray, valores: np.ndarray, n_cel: int, n_grupos: int
):
    """Matriz esparsa (células × grupos·colunas) com as somas de cada célula."""
    ok = grupo >= 0
    k = valores.shape[1]
    linhas = np.repeat(cel[ok], k)
    colunas = (grupo[ok][:, None] * k + np.arange(k)[None, :]).ravel()
    vals = valores[ok].ravel()
    return sparse.csr_matrix((vals, (linhas, colunas)), shape=(n_cel, n_grupos * k))


def aplicar(
    boot: BootCelulas,
    cel: np.ndarray,
    grupo: np.ndarray,
    valores: np.ndarray,
    n_grupos: int,
    funcao: Callable[[np.ndarray], np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Avalia ``funcao`` nas somas (réplicas × grupos × colunas): ponto e réplicas."""
    k = valores.shape[1]
    s = matriz_somas(cel, grupo, valores, boot.n_celulas, n_grupos)
    st = s.T.tocsr()
    ponto = np.asarray(s.sum(axis=0)).reshape(1, n_grupos, k)
    p = funcao(ponto)[0]
    reps = []
    for w in boot.blocos():
        somas = np.asarray(st @ w.T).T.reshape(w.shape[0], n_grupos, k)
        reps.append(funcao(somas))
    return p, np.concatenate(reps, axis=0)


def ic(
    ponto: float, reps: np.ndarray, escala: float = 1.0, casas: int = 2
) -> dict[str, Any]:
    """Ponto, IC 95% por percentil e erro-padrão das réplicas."""
    r = np.asarray(reps, dtype=float)
    r = r[np.isfinite(r)]
    if ponto is None or not np.isfinite(ponto) or len(r) < 10:
        return {"valor": None, "ic95": None, "ep": None}
    lo, hi = np.percentile(r, [2.5, 97.5])
    return {
        "valor": _arr(float(ponto) * escala, casas),
        "ic95": [_arr(float(lo) * escala, casas), _arr(float(hi) * escala, casas)],
        "ep": _arr(float(r.std(ddof=1)) * escala, casas + 1),
    }


def _arr(x: float, casas: int) -> float:
    """Arredonda sem devolver ``-0.0``."""
    return round(x, casas) + 0.0


def sem_ic(valor: dict[str, Any], motivo: str) -> dict[str, Any]:
    """Mantém o ponto e retira o intervalo quando há poucos conglomerados."""
    return {"valor": valor.get("valor"), "ic95": None, "ep": None, "nota": motivo}


def razao(somas: np.ndarray, num: int, den: int) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return somas[..., num] / somas[..., den]


def dif_dentro(
    taxa: np.ndarray, peso: np.ndarray, ref: int, mascara: np.ndarray | None = None
) -> np.ndarray:
    """Diferença média dentro do estrato, de cada grupo contra o grupo ``ref``.

    ``taxa`` e ``peso`` têm forma (réplicas, estratos, grupos). Para cada grupo ``g``,
    a média de ``taxa(g) - taxa(ref)`` nos estratos que têm os dois, ponderada pelo
    peso do grupo ``g`` (aptos, em geral). ``mascara`` (estratos × grupos) fixa os
    estratos avaliáveis no ponto; nas réplicas, estrato sem um dos lados sai da média.
    """
    d = taxa - taxa[:, :, [ref]]
    bom = np.isfinite(d) & (peso > 0)
    if mascara is not None:
        bom &= mascara[None, :, :]
    w = np.where(bom, peso, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (np.where(bom, d, 0.0) * w).sum(axis=1) / w.sum(axis=1)


# --- Regressões -----------------------------------------------------------------------


def _desenho(
    df: pd.DataFrame, x: list[str], fe: str | None, cat: list[str], num: list[str]
) -> pd.DataFrame:
    partes = [df[x + num].astype(float)]
    for c in cat + ([fe] if fe else []):
        partes.append(
            pd.get_dummies(df[c].astype(str), prefix=c, drop_first=True, dtype=float)
        )
    X = pd.concat(partes, axis=1)
    return cast(pd.DataFrame, sm.add_constant(X, has_constant="add"))


def _linha(res, nome: str, escala_exp: bool) -> dict[str, Any]:
    b = float(res.params[nome])
    se = float(res.bse[nome])
    if not np.isfinite(se):
        raise RuntimeError(f"erro-padrão indefinido para {nome}")
    lo, hi = b - Z95 * se, b + Z95 * se
    if escala_exp:
        return {
            "odds_ratio": _arr(float(np.exp(b)), 4),
            "ic95": [_arr(float(np.exp(lo)), 4), _arr(float(np.exp(hi)), 4)],
            "coef": _arr(b, 5),
            "ep": _arr(se, 5),
            "p": float(f"{float(res.pvalues[nome]):.4g}"),
        }
    return {
        "coef": _arr(b, 4),
        "ic95": [_arr(lo, 4), _arr(hi, 4)],
        "ep": _arr(se, 5),
        "p": float(f"{float(res.pvalues[nome]):.4g}"),
    }


def logit(
    df: pd.DataFrame,
    y: str,
    x: list[str],
    cluster: str,
    fe: str | None = "uf",
    cat: list[str] | None = None,
    num: list[str] | None = None,
) -> dict[str, Any]:
    """Logística com efeito fixo de UF e EP por conglomerado; odds ratio por unidade de x."""
    cat, num = cat or [], num or []
    d = df.dropna(subset=[y, *x, *num, cluster, *cat] + ([fe] if fe else []))
    X = _desenho(d, x, fe, cat, num)
    yy = d[y].astype(float)
    grupos = pd.factorize(d[cluster])[0]
    res = sm.GLM(yy, X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": grupos}, maxiter=100
    )
    return {
        "n": len(d),
        "eventos": int(yy.sum()),
        "conglomerados": int(grupos.max() + 1),
        "termos": {v: _linha(res, v, True) for v in x},
        "convergiu": bool(res.converged),
    }


def mqp(
    df: pd.DataFrame,
    y: str,
    x: list[str],
    peso: str,
    cluster: str,
    fe: str | None = "uf",
    cat: list[str] | None = None,
    num: list[str] | None = None,
) -> dict[str, Any]:
    """Mínimos quadrados ponderados com efeito fixo de UF (indicadoras) e EP por célula."""
    cat, num = cat or [], num or []
    d = df.dropna(subset=[y, *x, *num, peso, cluster, *cat] + ([fe] if fe else []))
    d = d.loc[d[peso] > 0]
    X = _desenho(d, x, fe, cat, num)
    grupos = pd.factorize(d[cluster])[0]
    pesos: Any = d[peso].to_numpy(float)
    res = sm.WLS(d[y].astype(float), X, weights=pesos).fit(
        cov_type="cluster", cov_kwds={"groups": grupos}
    )
    return {
        "n": len(d),
        "peso": peso,
        "conglomerados": int(grupos.max() + 1),
        "termos": {v: _linha(res, v, False) for v in x},
    }


def mqp_fe_municipio(
    df: pd.DataFrame, y: str, x: list[str], peso: str, cluster: str, fe: str = "mun_id"
) -> dict[str, Any]:
    """MQP com efeito fixo de município pela subtração das médias ponderadas."""
    d = df.dropna(subset=[y, *x, peso, cluster, fe])
    d = d.loc[d[peso] > 0].copy()
    w = d[peso].astype(float)
    cols = [y, *x]
    sw = w.groupby(d[fe]).transform("sum")
    for c in cols:
        media = (d[c].astype(float) * w).groupby(d[fe]).transform("sum") / sw
        d[c + "__w"] = d[c].astype(float) - media
    # municípios com uma só unidade ou sem variação em x não informam o coeficiente
    var = d[[c + "__w" for c in x]].abs().groupby(d[fe]).transform("max").max(axis=1)
    d = d.loc[var > 1e-12]
    grupos = pd.factorize(d[cluster])[0]
    res = sm.WLS(
        d[y + "__w"],
        d[[c + "__w" for c in x]],
        weights=cast(Any, d[peso].to_numpy(float)),
    ).fit(cov_type="cluster", cov_kwds={"groups": grupos})
    termos = {}
    for c in x:
        lin = _linha(res, c + "__w", False)
        termos[c] = lin
    return {
        "n": len(d),
        "municipios_informativos": int(d[fe].nunique()),
        "peso": peso,
        "conglomerados": int(grupos.max() + 1),
        "termos": termos,
    }
