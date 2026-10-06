"""Pergunta B: mistura gaussiana (k = 5) sobre a composição do eleitorado da seção.

Modelo principal (06/10/2026): cinco partes por seção, Lula, Flávio, brancos,
nulos e abstenção, todas divididas pelos aptos da eleição federal. O voto nas
outras dez candidaturas fica fora das partes, a pedido do autor: a composição é
fechada sobre as cinco (renormalizadas para somar 1), e o que falta para o
eleitorado inteiro é exatamente o voto em terceiros, publicado ao lado de cada
centro. Transformação: log-razão centrada (CLR) das cinco partes fechadas, com
zero trocado por 0,0001 antes do log; a mistura é ajustada nas quatro
coordenadas ortonormais do subespaço de soma zero (log-razão isométrica, ILR),
rotação que preserva distâncias de Mahalanobis e densidade relativa.

A primeira versão (05/10/2026) usava 15 partes: as 12 candidaturas, brancos,
nulos e abstenção. Com 42,7% das células em zero, o degrau entre 0,0001 e um
voto definiu os grupos pelo padrão de zeros das candidaturas nanicas, não pela
geografia nem pelo perfil político. Ela continua ajustada, com as mesmas oito
sementes de antes, mas o JSON guarda só os agregados (`variantes.quinze_partes`),
para o texto explicar por que foi abandonada.

k = 5 é escolha do autor; a tabela do BIC (k = 3, 4 e 5) fica ao lado. O ajuste
principal usa 16 sementes e duas inicializações do sklearn (`kmeans` e
`k-means++`), dez partidas internas cada; fica o de maior log-verossimilhança, e
`ajuste.diagnostico_convergencia` mostra se o EM foi até a convergência
(reajuste da melhor partida com tolerância 1e-6) e quantas partidas chegam ao
mesmo máximo (`secoes_clusters_diag`).

O numpy ligado ao Accelerate (macOS) emite avisos falsos de divisão por zero em
produtos de matriz; os avisos são silenciados e todo resultado é conferido como
finito. Nos processos paralelos, a biblioteca de álgebra linear roda com uma
linha de execução por processo, para não disputar os núcleos.
"""

from __future__ import annotations

import os
import time
import warnings
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from typing import Any, NamedTuple

import numpy as np
import pandas as pd
from scipy.linalg import null_space
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

from .secoes_base import FLAVIO, LULA, ZERO, Base, amostras, clr, pct, r2
from .secoes_clusters_diag import convergencia, frase, resumir
from .secoes_clusters_leitura import (
    NOMES_PARTES,
    diagnostico_zeros,
    estabilidade,
    leitura_projecao,
    menos_votadas,
    padroes_zeros,
    rotulo,
)
from .secoes_clusters_perfil import (
    artefato,
    contagens,
    empates_por_par,
    padroes_empate,
    referencia,
    resumo_grupos,
    rotulo_perfil,
    textos,
)

SEMENTE = 20261005
N_SEMENTES = 16
SEMENTES = tuple(SEMENTE + i for i in range(N_SEMENTES))
SEMENTES_15 = SEMENTES[:8]  # as oito da versão de 15 partes publicada em 05/10
INITS = ("kmeans", "k-means++")
K = 5
K_TABELA = (3, 4, 5)
ESCOLHA_K = {
    "k": K,
    "anterior": 3,
    "data": "06/10/2026",
    "motivo": (
        "escolha do autor, mantida quando a mistura passou de 15 para cinco partes"
    ),
}
PARTES = ("lula", "flavio", "brancos", "nulos", "abstencao")
N_INIT = 10
TOL = 1e-4
MAX_ITER = 500
MAX_PONTOS = 8000
TOP_FIGURA = 200
EMPATE_LOGLIK = 1e-3
MIN_PARALELO = 50_000  # seções; abaixo disso as partidas rodam em série
MAX_PROCESSOS = 16
VARS_THREADS = (
    "VECLIB_MAXIMUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
)


class Ajuste(NamedTuple):
    gm: GaussianMixture
    semente: int
    init: str
    log: list[dict[str, Any]]
    todos: list[tuple[int, str, GaussianMixture]]


def ilr_base(d: int) -> np.ndarray:
    """Base ortonormal (d × d−1) do subespaço de soma zero."""
    return null_space(np.ones((1, d)))


def matriz_fracoes(df: pd.DataFrame, vcols: Sequence[str]) -> np.ndarray:
    """Frações do eleitorado: candidatos, brancos, nulos e abstenção (≥ 0)."""
    apt = df["aptos"].to_numpy(dtype=float)
    abst = np.clip(
        df["aptos"].to_numpy(float) - df["comparecimento"].to_numpy(float), 0, None
    )
    partes = [df[c].to_numpy(dtype=float) for c in vcols]
    partes += [df["brancos"].to_numpy(float), df["nulos"].to_numpy(float), abst]
    return np.column_stack(partes) / apt[:, None]


def matriz_cinco(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Lula, Flávio, brancos, nulos e abstenção / aptos, e o que falta (terceiros).

    O que falta para 1 é o voto nas outras dez candidaturas dividido pelos aptos,
    porque comparecimento = válidos + brancos + nulos.
    """
    fr = matriz_fracoes(df, [f"v{LULA}", f"v{FLAVIO}"])
    return fr, np.clip(1.0 - fr.sum(axis=1), 0.0, None)


def fechar(fr: np.ndarray) -> np.ndarray:
    """Renormaliza cada linha para somar 1 (fechamento da composição)."""
    soma = fr.sum(axis=1, keepdims=True)
    if not (soma > 0).all():
        raise ValueError("seção sem nenhuma das partes da composição")
    return fr / soma


def coordenadas(fr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """CLR (com zero → 0,0001) e as coordenadas ILR correspondentes."""
    z = clr(fr, ZERO)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        x = z @ ilr_base(z.shape[1])
    if not np.isfinite(x).all():
        raise ValueError("coordenadas ILR não finitas")
    return z, x


def ajustar(
    x: np.ndarray,
    k: int,
    n_init: int = N_INIT,
    semente: int = SEMENTE,
    init: str = "kmeans",
    tol: float = TOL,
    max_iter: int = MAX_ITER,
) -> GaussianMixture:
    gm = GaussianMixture(
        n_components=k,
        covariance_type="full",
        n_init=n_init,
        init_params=init,
        random_state=semente,
        max_iter=max_iter,
        tol=tol,
        reg_covar=1e-6,
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        gm.fit(x)
    return gm


def loglik(gm: GaussianMixture, x: np.ndarray) -> float:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        ll = float(gm.score(x))
    if not np.isfinite(ll):
        raise ValueError("log-verossimilhança não finita")
    return ll


def prever(gm: GaussianMixture, x: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return gm.predict(x)


def _ajuste_partida(
    args: tuple[np.ndarray, int, int, int, str, float, int],
) -> tuple[float, int, str, GaussianMixture]:
    """Um ajuste e a log-verossimilhança média (função de módulo: vai ao processo)."""
    x, k, n_init, s, init, tol, max_iter = args
    gm = ajustar(x, k, n_init=n_init, semente=s, init=init, tol=tol, max_iter=max_iter)
    return loglik(gm, x), s, init, gm


@contextmanager
def uma_thread() -> Iterator[None]:
    """Processos filhos com uma linha de execução de álgebra linear cada."""
    antes = {v: os.environ.get(v) for v in VARS_THREADS}
    os.environ.update(dict.fromkeys(VARS_THREADS, "1"))
    try:
        yield
    finally:
        for v, val in antes.items():
            if val is None:
                os.environ.pop(v, None)
            else:
                os.environ[v] = val


def rodar(
    tarefas: Sequence[tuple[np.ndarray, int, int, int, str, float, int]],
) -> list[tuple[float, int, str, GaussianMixture]]:
    """Roda as partidas; com a base inteira, em processos separados.

    Cada partida tem o próprio `random_state`, então o resultado não depende da
    ordem nem do paralelismo.
    """
    if len(tarefas) > 1 and len(tarefas[0][0]) >= MIN_PARALELO:
        n = min(len(tarefas), os.cpu_count() or 1, MAX_PROCESSOS)
        with uma_thread(), ProcessPoolExecutor(max_workers=n) as ex:
            return list(ex.map(_ajuste_partida, tarefas))
    return [_ajuste_partida(t) for t in tarefas]


def ajustar_melhor(
    x: np.ndarray,
    k: int,
    sementes: Sequence[int] = SEMENTES,
    n_init: int = N_INIT,
    inits: Sequence[str] = ("kmeans",),
) -> Ajuste:
    """Um ajuste por semente e por inicialização; fica o de maior
    log-verossimilhança média (empate: a primeira inicialização, a menor semente)."""
    tarefas = [(x, k, n_init, s, i, TOL, MAX_ITER) for i in inits for s in sementes]
    ajustes = rodar(tarefas)
    ordem = sorted(
        ajustes, key=lambda a: (-round(a[0], 9), list(inits).index(a[2]), a[1])
    )
    log = [
        {
            "semente": s,
            "init": i,
            "loglik_media": r2(ll, 4),
            "convergiu": bool(gm.converged_),
            "iteracoes": int(gm.n_iter_),
        }
        for ll, s, i, gm in ajustes
    ]
    melhor = ordem[0]
    return Ajuste(
        melhor[3], melhor[1], melhor[2], log, [(s, i, g) for _, s, i, g in ajustes]
    )


def mahalanobis_proprio(
    gm: GaussianMixture, x: np.ndarray, rotulos: np.ndarray
) -> np.ndarray:
    d2 = np.full(len(x), np.nan)
    medias = np.asarray(gm.means_)
    prec = np.asarray(gm.precisions_cholesky_)
    for c in range(gm.n_components):
        sel = rotulos == c
        if not sel.any():
            continue
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            y = (x[sel] - medias[c]) @ prec[c]
        d2[sel] = (y**2).sum(axis=1)
    return np.sqrt(d2)


def escolher_anomalo(loglik_media: Sequence[float], dispersao: Sequence[float]) -> int:
    """Componente de menor densidade média e maior dispersão.

    Soma dos postos: posto 0 para a menor log-verossimilhança média e posto 0
    para a maior dispersão (log-determinante da covariância). Empate: a menor
    log-verossimilhança média decide.
    """
    ll = np.asarray(loglik_media, dtype=float)
    dp = np.asarray(dispersao, dtype=float)
    r_ll = np.argsort(np.argsort(ll, kind="stable"), kind="stable")
    r_dp = np.argsort(np.argsort(-dp, kind="stable"), kind="stable")
    soma = r_ll + r_dp
    candidatos = np.flatnonzero(soma == soma.min())
    return int(candidatos[np.argmin(ll[candidatos])])


def ordem_estavel(rot: np.ndarray, lula_val: np.ndarray, k: int) -> np.ndarray:
    """Mapa componente → id, do mais lulista ao menos (% de Lula nos válidos)."""
    medias = [
        float(np.nanmean(lula_val[rot == c])) if (rot == c).any() else -1.0
        for c in range(k)
    ]
    ordem = np.argsort(-np.asarray(medias), kind="stable")
    novo = np.empty_like(ordem)
    novo[ordem] = np.arange(len(ordem))
    return novo


def separacao(score: np.ndarray, zero: np.ndarray) -> tuple[float, float] | None:
    """Melhor corte num eixo para separar seções com e sem zero numa parte.

    Devolve o acerto balanceado (média da taxa de acerto nos dois lados, em %)
    e o valor do corte. Sem seções dos dois tipos, None.
    """
    pos = np.asarray(zero, dtype=bool)
    npos, nneg = int(pos.sum()), int((~pos).sum())
    if npos == 0 or nneg == 0:
        return None
    ordem = np.argsort(score, kind="stable")
    s = np.asarray(score)[ordem]
    zp = pos[ordem]
    tpr = np.cumsum(zp) / npos
    tnr = (nneg - np.cumsum(~zp)) / nneg
    bal = (tpr + tnr) / 2
    bal = np.maximum(bal, 1 - bal)
    i = int(np.argmax(bal))
    return float(100 * bal[i]), float(s[i])


# ---------------------------------------------------------------- bloco


class Composicao(NamedTuple):
    """O que entra na mistura e o que descreve os centros."""

    fr: np.ndarray  # composição modelada (cada linha soma 1)
    chaves: list[str]
    eleitorado: np.ndarray  # as mesmas partes, divididas pelos aptos
    fora: np.ndarray | None  # fração do eleitorado fora das partes (terceiros)
    unidades: np.ndarray  # votos (e abstenções) somados nas partes


def bloco(
    df: pd.DataFrame,
    comp: Composicao,
    nomes: Mapping[str, str],
    sementes: Sequence[int] = SEMENTES,
    inits: Sequence[str] = INITS,
    contraste: bool = True,
    diagnostico: bool = True,
    max_pontos: int = MAX_PONTOS,
) -> dict[str, Any]:
    """Ajusta k = K e descreve componentes, anômalos, cruzamentos e PCA."""
    fr, chaves = comp.fr, comp.chaves
    _, x = coordenadas(fr)
    t0 = time.time()
    aj = ajustar_melhor(x, K, sementes=sementes, inits=inits)
    diag, gm = convergencia(x, aj) if diagnostico else (None, aj.gm)
    seg = time.time() - t0
    bruto = prever(gm, x)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        ll = np.asarray(gm.score_samples(x), dtype=float)
    if not np.isfinite(ll).all():
        raise ValueError("log-verossimilhança não finita")
    mapa = ordem_estavel(bruto, df["lula_pct"].to_numpy(dtype=float), K)
    rot = mapa[bruto]
    maha = mahalanobis_proprio(gm, x, bruto)
    inv = np.argsort(mapa)
    covs = np.asarray(gm.covariances_)[inv]
    pesos = np.asarray(gm.weights_)[inv]

    bic = [_linha_bic(K, gm, x, aj.log)]
    if contraste:
        for kc in K_TABELA:
            if kc == K:
                continue
            outro = ajustar_melhor(x, kc, sementes=sementes, inits=inits[:1])
            bic.append(_linha_bic(kc, outro.gm, x, outro.log))
        bic.sort(key=lambda r: r["k"])

    df = df.assign(_cl=rot, _ll=ll, _maha=maha)
    comps = [_componente(df, comp, rot, c, covs[c], pesos[c]) for c in range(K)]
    zero = fr <= 0
    ordem_votos = menos_votadas(fr, comp.unidades, chaves)
    padroes = padroes_zeros(zero, rot, K, chaves, ordem_votos)
    for cc, pz in zip(comps, padroes, strict=True):
        cc["padrao_zeros"] = pz
        cc["rotulo"] = rotulo(cc, nomes)
    particoes = {(s, i): prever(g, x) for s, i, g in aj.todos}
    for linha in aj.log:
        rs = particoes[(linha["semente"], linha["init"])]
        linha["cramer_v_regiao"] = r2(cramer(pd.Series(rs), df["regiao"]), 3)
        linha["ari_com_escolhida"] = r2(adjusted_rand_score(bruto, rs), 3)
    if diag is not None:
        diag["ajustes"] = aj.log
        resumir(diag)
    anom = escolher_anomalo(
        [cc["loglik_media"] for cc in comps], [cc["dispersao_logdet"] for cc in comps]
    )
    extra = ("_ll", "_maha", "_cl")
    am = df[df["_cl"] == anom].sort_values("_ll").head(20)
    menos = df.sort_values("_ll").head(50)
    lls = [r["loglik_media"] for r in aj.log]
    maximo = max(lls)
    ajuste = {
        "secoes_ajuste": len(df),
        "secoes_atribuidas": len(df),
        "amostra_estratificada": False,
        "covariancia": "full",
        "n_init": N_INIT,
        "inits": list(inits),
        "random_state": aj.semente,
        "init": aj.init,
        "sementes": aj.log,
        "inicializacoes": N_INIT * len(aj.log),
        "sementes_no_maximo": sum(v >= maximo - EMPATE_LOGLIK for v in lls),
        "max_iter": int(gm.max_iter),
        "tol": float(gm.tol),
        "reg_covar": 1e-6,
        "convergiu": bool(gm.converged_),
        "iteracoes": int(gm.n_iter_),
        "loglik_media": r2(ll.mean(), 4),
        "segundos": r2(seg, 1),
    }
    if diag is not None:
        ajuste["diagnostico_convergencia"] = diag
    return {
        "features": list(chaves),
        "zeros_substituidos_pct": r2(100 * float(zero.mean()), 2),
        "zeros_por_parte": {
            k: {
                "secoes": int(zero[:, i].sum()),
                "pct_secoes": r2(100 * float(zero[:, i].mean()), 2),
            }
            for i, k in enumerate(chaves)
        },
        "secoes_com_zero": int(zero.any(axis=1).sum()),
        "degrau_log": degrau_log(comp.unidades),
        "ajuste": ajuste,
        "bic": bic,
        "componentes": comps,
        "menos_votadas": [chaves[i] for i in ordem_votos],
        "mais_anomalo": {
            "id": anom,
            "criterio": (
                "soma dos postos de menor log-verossimilhança média e de maior "
                "dispersão (log-determinante da covariância); empate decidido pela "
                "menor log-verossimilhança média. Amostras: as 20 seções de menor "
                "log-verossimilhança dentro do componente."
            ),
            "amostras": _refs(am, extra),
        },
        "menos_provaveis": _refs(menos, extra),
        "cluster_regiao": _cruzar(df, "regiao", "regiao"),
        "cluster_uf": _cruzar(df, "uf", "uf"),
        "cramer_v_regiao": r2(cramer(df["_cl"], df["regiao"]), 3),
        "cramer_v_uf": r2(cramer(df["_cl"], df["uf"]), 3),
        "pca": _pca(df, x, fr, chaves, rot, ll, max_pontos),
        "_rot": rot,
    }


def _linha_bic(
    k: int, gm: GaussianMixture, x: np.ndarray, log: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return {
            "k": k,
            "bic": r2(gm.bic(x), 1),
            "loglik_media": r2(gm.score(x), 4),
            "loglik_sementes": [r["loglik_media"] for r in log],
        }


def degrau_log(unidades: np.ndarray) -> dict[str, Any]:
    """Distância, em unidades de log, entre zero (0,0001) e um voto na seção.

    `unidades` é o total da composição em votos (e abstenções): os aptos na
    versão de 15 partes, os aptos menos o voto em terceiros na de cinco.
    """
    u = np.clip(np.asarray(unidades, dtype=float), 1.0, None)
    d = np.log(1.0 / (u * ZERO))
    return {
        "aptos_mediana": r2(np.median(u), 0),
        "mediana": r2(np.log(1.0 / (np.median(u) * ZERO)), 2),
        "p10": r2(np.percentile(d, 10), 2),
        "p90": r2(np.percentile(d, 90), 2),
    }


def _componente(
    df: pd.DataFrame,
    comp: Composicao,
    rot: np.ndarray,
    c: int,
    cov: np.ndarray,
    peso: float,
) -> dict[str, Any]:
    sel = rot == c
    g = df[sel]
    n = int(sel.sum())
    val = int(g["validos"].sum())
    sinal, logdet = np.linalg.slogdet(cov)
    saida = {
        "id": c,
        "secoes": n,
        "pct_secoes": pct(n, len(df)),
        "aptos": int(g["aptos"].sum()),
        "aptos_medio": r2(g["aptos"].mean(), 1),
        "votantes_medio": r2(g["votantes"].mean(), 1),
        "centro_pct_eleitorado": {
            k: r2(100 * comp.eleitorado[sel, i].mean(), 3)
            for i, k in enumerate(comp.chaves)
        },
        "zeros_pct": {
            k: r2(100 * float((comp.fr[sel, i] <= 0).mean()), 1)
            for i, k in enumerate(comp.chaves)
        },
        "centro_pct_validos": {
            "lula": pct(int(g[f"v{LULA}"].sum()), val),
            "flavio": pct(int(g[f"v{FLAVIO}"].sum()), val),
            "outros": pct(
                int((g["validos"] - g[f"v{LULA}"] - g[f"v{FLAVIO}"]).sum()), val
            ),
        },
    }
    if comp.fora is not None:
        saida["terceiros_pct_eleitorado"] = r2(100 * comp.fora[sel].mean(), 3)
    return saida | {
        "peso": r2(peso, 4),
        "dispersao_logdet": r2(logdet if sinal > 0 else float("nan"), 3),
        "dispersao_traco": r2(np.trace(cov), 3),
        "loglik_media": r2(g["_ll"].mean(), 3),
        "loglik_p05": r2(np.percentile(g["_ll"], 5), 3),
        "mahalanobis_mediana": r2(g["_maha"].median(), 3),
        "ufs_top": [
            {"uf": str(u).upper(), "secoes": int(m), "pct_do_cluster": pct(int(m), n)}
            for u, m in g["uf"].value_counts().head(6).items()
        ],
        "regioes": [
            {"regiao": r, "secoes": int(m), "pct_do_cluster": pct(int(m), n)}
            for r, m in g["regiao"].value_counts().items()
        ],
        "modelo_urna": [
            {"modelo": md, "pct_do_cluster": pct(int(m), n)}
            for md, m in g["modelo_urna"].fillna("sem modelo").value_counts().items()
        ],
    }


def _refs(df: pd.DataFrame, extra: Sequence[str]) -> list[dict[str, Any]]:
    out = amostras(df, len(df), extra)
    for r in out:
        r["loglik"] = r.pop("_ll", None)
        r["mahalanobis"] = r.pop("_maha", None)
        cl = r.pop("_cl", None)
        r["cluster"] = int(cl) if cl is not None else None
    return out


def _cruzar(df: pd.DataFrame, col: str, nome: str) -> list[dict[str, Any]]:
    tab = pd.crosstab(df["_cl"], df[col])
    vals = tab.to_numpy(dtype=np.int64)
    out = []
    for ci, c in enumerate(tab.index):
        for ri, r in enumerate(tab.columns):
            n = int(vals[ci, ri])
            if n == 0:
                continue
            out.append(
                {
                    "cluster": int(c),
                    nome: str(r).upper() if nome == "uf" else r,
                    "secoes": n,
                    "pct_do_cluster": pct(n, int(vals[ci].sum())),
                    f"pct_da_{nome}": pct(n, int(vals[:, ri].sum())),
                }
            )
    return out


def cramer(a: pd.Series, b: pd.Series) -> float:
    tab = pd.crosstab(a, b).to_numpy(dtype=float)
    r, k = tab.shape
    if min(r, k) < 2:
        return 0.0
    n = tab.sum()
    esp = tab.sum(1, keepdims=True) * tab.sum(0, keepdims=True) / n
    chi2 = ((tab - esp) ** 2 / esp).sum()
    return float(np.sqrt(chi2 / (n * (min(r, k) - 1))))


def projecao(x: np.ndarray) -> tuple[PCA, np.ndarray, np.ndarray]:
    """Dois componentes principais das coordenadas ILR.

    Devolve o ajuste, os escores e as cargas reescritas nas partes (CLR): como a
    base ILR é ortonormal, a PCA nas coordenadas ILR e a PCA na CLR dão os mesmos
    escores e as mesmas variâncias, e a carga de cada parte é `V @ componente`.
    """
    pca = PCA(n_components=2, random_state=SEMENTE)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        p = pca.fit_transform(x)
    cargas = pca.components_ @ ilr_base(x.shape[1] + 1).T
    return pca, p, cargas


def _pca(
    df: pd.DataFrame,
    x: np.ndarray,
    fr: np.ndarray,
    chaves: Sequence[str],
    rot: np.ndarray,
    ll: np.ndarray,
    max_pontos: int = MAX_PONTOS,
) -> dict[str, Any]:
    pca, p, cargas = projecao(x)
    rng = np.random.default_rng(SEMENTE)
    n = len(df)
    top = np.argsort(ll)[:TOP_FIGURA]
    escolhidos: set[int] = {int(i) for i in top}
    for c in np.unique(rot):
        idx = np.flatnonzero(rot == c)
        alvo = min(len(idx), max(min(len(idx), 400), round(max_pontos * len(idx) / n)))
        escolhidos.update(int(i) for i in rng.choice(idx, size=alvo, replace=False))
    topset = {int(i) for i in top}
    ufs = df["uf"].str.upper().to_numpy()
    pontos = [
        [r2(p[i, 0], 3), r2(p[i, 1], 3), int(rot[i]), int(i in topset), str(ufs[i])]
        for i in sorted(escolhidos)
    ]
    sep = []
    for j in range(2):
        i = int(np.argmax(np.abs(cargas[j])))
        s = separacao(p[:, j], fr[:, i] <= 0)
        sep.append(
            {
                "componente": j + 1,
                "feature": chaves[i],
                "carga": r2(cargas[j, i], 4),
                "zeros_pct": r2(100 * float((fr[:, i] <= 0).mean()), 1),
                "acerto_balanceado_pct": r2(s[0], 1) if s else None,
                "corte": r2(s[1], 3) if s else None,
            }
        )
    return {
        "base": (
            f"dois componentes principais das {x.shape[1]} coordenadas ILR; as cargas "
            f"são lidas nas {len(chaves)} partes (CLR), com os mesmos escores"
        ),
        "variancia_explicada": [r2(v, 4) for v in pca.explained_variance_ratio_],
        "cargas": [
            {"feature": k, "pc1": r2(cargas[0, i], 4), "pc2": r2(cargas[1, i], 4)}
            for i, k in enumerate(chaves)
        ],
        "separacao": sep,
        "centros": [
            {
                "cluster": int(c),
                "x": r2(p[rot == c, 0].mean(), 3),
                "y": r2(p[rot == c, 1].mean(), 3),
            }
            for c in np.unique(rot)
        ],
        "elipses": [_elipse_plano(p[rot == c], int(c)) for c in np.unique(rot)],
        "colunas": ["x", "y", "cluster", "top200", "uf"],
        "pontos": pontos,
        "n_pontos": len(pontos),
    }


def _elipse_plano(q: np.ndarray, c: int) -> dict[str, Any]:
    """Centro e covariância, no plano dos dois componentes, de todas as seções do grupo."""
    cov = np.cov(q, rowvar=False, bias=True) if len(q) > 1 else np.zeros((2, 2))
    return {
        "cluster": c,
        "x": r2(q[:, 0].mean(), 4),
        "y": r2(q[:, 1].mean(), 4),
        "cov": [
            [r2(cov[0, 0], 5), r2(cov[0, 1], 5)],
            [r2(cov[1, 0], 5), r2(cov[1, 1], 5)],
        ],
    }


# ---------------------------------------------------------------- principal


def composicao_cinco(df: pd.DataFrame) -> Composicao:
    el, fora = matriz_cinco(df)
    apt = df["aptos"].to_numpy(dtype=float)
    return Composicao(fechar(el), list(PARTES), el, fora, apt * el.sum(axis=1))


def composicao_quinze(df: pd.DataFrame, cands: Sequence[Any]) -> Composicao:
    fr = matriz_fracoes(df, [f"v{c.numero}" for c in cands])
    chaves = [c.chave for c in cands] + ["brancos", "nulos", "abstencao"]
    return Composicao(fr, chaves, fr, None, df["aptos"].to_numpy(dtype=float))


def _faixa(v: Sequence[float]) -> list[float | None]:
    return [r2(min(v), 3), r2(max(v), 3)] if v else [None, None]


def quinze_partes(
    df: pd.DataFrame, comp: Composicao, nomes: Mapping[str, str]
) -> dict[str, Any]:
    """A versão de 15 partes (05/10/2026), só com os agregados.

    Mesmas oito sementes e mesma inicialização da versão publicada; sem
    amostras e sem os pontos da projeção, que não servem mais a figura nenhuma.
    """
    b = bloco(
        df,
        comp,
        nomes,
        sementes=SEMENTES_15,
        inits=INITS[:1],
        diagnostico=False,
        max_pontos=0,
    )
    aj = b["ajuste"]
    sm = aj["sementes"]
    outras = [s for s in sm if s["semente"] != aj["random_state"]]
    return {
        "descricao": (
            f"a mesma mistura (k = {K}) sobre {len(comp.chaves)} partes: as 12 "
            "candidaturas, brancos, nulos e abstenção, divididos pelos aptos"
        ),
        "abandonada_em": "06/10/2026",
        "motivo": (
            "os grupos saíram do padrão de zeros das candidaturas nanicas, não da "
            "geografia nem do perfil de voto"
        ),
        "k": K,
        "features": b["features"],
        "zeros_substituidos_pct": b["zeros_substituidos_pct"],
        "secoes_com_zero": b["secoes_com_zero"],
        "degrau_log": b["degrau_log"],
        "bic": b["bic"],
        "cramer_v_regiao": b["cramer_v_regiao"],
        "cramer_v_uf": b["cramer_v_uf"],
        "ajuste": {
            "sementes": len(sm),
            "n_init": aj["n_init"],
            "random_state": aj["random_state"],
            "sementes_no_maximo": aj["sementes_no_maximo"],
            "loglik_sementes": _faixa([s["loglik_media"] for s in sm]),
            "ari_outras_sementes": _faixa([s["ari_com_escolhida"] for s in outras]),
            "cramer_v_sementes": _faixa([s["cramer_v_regiao"] for s in sm]),
        },
        "grupos": resumo_grupos(b["componentes"]),
        "nuvens": {
            "variancia_explicada": b["pca"]["variancia_explicada"],
            "separacao": b["pca"]["separacao"],
        },
        "diagnostico": diagnostico_zeros(b, nomes),
        "leitura_projecao": leitura_projecao({**b, "k": K}, nomes),
        "estabilidade": estabilidade(b),
        "_rot": b["_rot"],
    }


def meio_voto(
    df: pd.DataFrame,
    comp: Composicao,
    nomes: Mapping[str, str],
    ref: Mapping[str, Any],
    cont: np.ndarray,
) -> dict[str, Any]:
    """Sensibilidade: zero trocado por meio voto antes do fechamento.

    Meio voto é a metade do menor valor observável (um voto), a regra de
    substituição multiplicativa usual em dados composicionais. O degrau entre
    zero e um voto cai de cerca de 3,5 para 0,7 unidade de log.
    """
    cont = comp.eleitorado * df["aptos"].to_numpy(dtype=float)[:, None]
    cont = np.where(cont > 0, cont, 0.5)
    mv = Composicao(
        fechar(cont), comp.chaves, comp.eleitorado, comp.fora, comp.unidades
    )
    b = bloco(
        df,
        mv,
        nomes,
        sementes=SEMENTES_15,
        inits=INITS[:1],
        contraste=False,
        diagnostico=False,
        max_pontos=0,
    )
    empates = padroes_empate(cont, b["_rot"], K, comp.chaves)
    for cc, pe in zip(b["componentes"], empates, strict=True):
        cc["padrao_empates"] = pe
        cc["artefato"] = artefato(cc, nomes) or None
        cc["rotulo"] = rotulo_perfil(cc, ref, nomes)
    aj = b["ajuste"]
    return {
        "descricao": (
            f"a mesma mistura (k = {K}, {len(SEMENTES_15)} sementes) com zero trocado "
            "por meio voto, e não por 0,0001, antes de fechar a composição"
        ),
        "k": K,
        "cramer_v_regiao": b["cramer_v_regiao"],
        "cramer_v_uf": b["cramer_v_uf"],
        "ajuste": {
            "sementes": len(aj["sementes"]),
            "sementes_no_maximo": aj["sementes_no_maximo"],
            "loglik_sementes": _faixa([s["loglik_media"] for s in aj["sementes"]]),
        },
        "grupos": resumo_grupos(b["componentes"]),
        "_rot": b["_rot"],
    }


def clusters(base: Base) -> dict[str, Any]:
    df = base.secoes
    df = df[df["aptos"] > 0].reset_index(drop=True)
    cands = base.candidatos
    nomes = {c.chave: c.nome for c in cands} | NOMES_PARTES
    comp = composicao_cinco(df)
    cont = contagens(comp)
    principal = bloco(df, comp, nomes)
    rot = principal.pop("_rot")
    for cc, pe in zip(
        principal["componentes"],
        padroes_empate(cont, rot, K, comp.chaves),
        strict=True,
    ):
        cc["padrao_empates"] = pe
    ref = referencia(comp)

    q = quinze_partes(df, composicao_quinze(df, cands), nomes)
    rot15 = q.pop("_rot")
    mv = meio_voto(df, comp, nomes, ref, cont)
    rot_mv = mv.pop("_rot")
    sens = {
        "ari_principal_vs_quinze_partes": r2(adjusted_rand_score(rot, rot15), 3),
        "ari_principal_vs_meio_voto": r2(adjusted_rand_score(rot, rot_mv), 3),
    }
    bic = principal["bic"]
    melhor = min(bic, key=lambda b: b["bic"])["k"] if bic else None
    saida = {
        "k": K,
        "escolha_k": {**ESCOLHA_K, "bic_prefere": melhor},
        "base": (
            "votos de Lula, de Flávio, brancos, nulos e abstenções da seção, divididos "
            "pelos aptos da eleição federal e renormalizados para somar 1 (composição "
            "fechada sobre as cinco partes; o voto em terceiros fica fora)"
        ),
        "transformacao": "clr",
        "transformacao_detalhe": (
            "log-razão centrada (CLR) das cinco partes fechadas, com zero trocado por "
            "0,0001 antes do log; a mistura é ajustada nas quatro coordenadas "
            "ortonormais do subespaço de soma zero (ILR), rotação que preserva "
            "Mahalanobis e densidade relativa"
        ),
        "zero": ZERO,
        "referencia_nacional": ref,
        "mediana_votos_por_secao": {
            k: r2(float(np.median(cont[:, i])), 1) for i, k in enumerate(comp.chaves)
        },
        "empates_por_par": empates_por_par(cont, comp.chaves),
        **principal,
        "variantes": {"quinze_partes": q, "meio_voto": mv},
        "sensibilidade": sens,
    }
    textos(saida, nomes)
    return saida


def refazer_textos(cl: dict[str, Any], candidatos: Sequence[Mapping[str, Any]]) -> None:
    """Refaz rótulos e frases do bloco `clusters` a partir dos números gravados.

    Não reajusta nada: serve para revisão editorial do texto gerado sem rodar a
    mistura de novo. A frase de diagnóstico da versão de 15 partes fica como
    está, porque depende de campos que o registro não guarda.
    """
    nomes = {c["chave"]: c["nome"] for c in candidatos} | NOMES_PARTES
    dg = (cl.get("ajuste") or {}).get("diagnostico_convergencia")
    if dg:
        dg["frase"] = frase(dg)
    textos(cl, nomes)
