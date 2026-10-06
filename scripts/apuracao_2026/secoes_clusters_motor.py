"""Motor da mistura gaussiana das seções: ajuste, diagnóstico e descrição.

Ajusta a mistura com várias sementes e inicializações (em processos paralelos,
com uma linha de execução de álgebra linear por processo), escolhe a de maior
log-verossimilhança, descreve componentes, o grupo mais atípico, os
cruzamentos com região e UF e a projeção em dois componentes principais. O
espaço da mistura vem da `Composicao`: log-razão (coordenadas ILR da CLR, zero
trocado por 0,0001) ou proporções do eleitorado padronizadas, sem log.

O numpy ligado ao Accelerate (macOS) emite avisos falsos de divisão por zero em
produtos de matriz; os avisos são silenciados e todo resultado é conferido como
finito.
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

from .secoes_base import FLAVIO, LULA, ZERO, amostras, clr, pct, r2
from .secoes_clusters_diag import convergencia, resumir
from .secoes_clusters_leitura import menos_votadas, padroes_zeros, rotulo

SEMENTE = 20261005
N_SEMENTES = 16
SEMENTES = tuple(SEMENTE + i for i in range(N_SEMENTES))
INITS = ("kmeans", "k-means++")
K = 5
K_TABELA = (3, 4, 5)
N_INIT = 10
TOL = 1e-4  # tentativas em log-razão, como publicadas
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
    amostra: int | None = None  # seções da busca; None = base inteira


def amostra_estratificada(
    estratos: Sequence[Any] | np.ndarray, n: int, semente: int = SEMENTE
) -> np.ndarray:
    """Índices de uma amostra sem reposição, proporcional por estrato (a UF).

    A alocação usa o maior resto: cada estrato recebe o piso da cota e as vagas
    que sobram vão aos de maior fração; dentro do estrato, sorteio simples.
    """
    codigos, inv = np.unique(np.asarray(estratos), return_inverse=True)
    total = len(inv)
    if n >= total:
        return np.arange(total)
    cont = np.bincount(inv, minlength=len(codigos))
    alvo = cont * n / total
    cota = np.floor(alvo).astype(int)
    sobra = n - int(cota.sum())
    cota[np.argsort(-(alvo - cota), kind="stable")[:sobra]] += 1
    rng = np.random.default_rng(semente)
    partes = [
        rng.choice(np.flatnonzero(inv == c), size=int(cota[c]), replace=False)
        for c in range(len(codigos))
    ]
    return np.sort(np.concatenate(partes))


def refinar(
    gm: GaussianMixture, x: np.ndarray, tol: float, max_iter: int
) -> GaussianMixture:
    """O ajuste na base inteira, partindo dos parâmetros achados na amostra."""
    novo = GaussianMixture(
        n_components=gm.n_components,
        covariance_type="full",
        n_init=1,
        random_state=gm.random_state,
        max_iter=max_iter,
        tol=tol,
        reg_covar=gm.reg_covar,
        weights_init=gm.weights_,
        means_init=gm.means_,
        precisions_init=gm.precisions_,
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        novo.fit(x)
    return novo


def ilr_base(d: int) -> np.ndarray:
    """Base ortonormal (d × d−1) do subespaço de soma zero."""
    return null_space(np.ones((1, d)))


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
    tol: float = TOL,
    max_iter: int = MAX_ITER,
    idx: np.ndarray | None = None,
) -> Ajuste:
    """Um ajuste por semente e por inicialização; fica o de maior
    log-verossimilhança média (empate: a primeira inicialização, a menor semente).

    Com `idx`, a busca roda só nessas linhas (amostra) e a melhor partida é
    refinada na base inteira (`refinar`); as partidas da busca ficam em `todos`.
    """
    xb = x if idx is None else x[idx]
    tarefas = [(xb, k, n_init, s, i, tol, max_iter) for i in inits for s in sementes]
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
    gm = melhor[3] if idx is None else refinar(melhor[3], x, tol, max_iter)
    return Ajuste(
        gm,
        melhor[1],
        melhor[2],
        log,
        [(s, i, g) for _, s, i, g in ajustes],
        None if idx is None else len(idx),
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

    fr: np.ndarray  # composição fechada (cada linha soma 1): zeros e contagens
    chaves: list[str]
    eleitorado: np.ndarray  # as mesmas partes, divididas pelos aptos
    fora: np.ndarray | None  # fração do eleitorado fora das partes (terceiros)
    unidades: np.ndarray  # votos (e abstenções) somados nas partes
    espaco: str = "clr"  # "clr" (log-razão de `fr`) ou "padronizada" (`eleitorado`)


def padronizar(el: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(p − média) / desvio-padrão, por coluna, entre seções; sem log."""
    media = el.mean(axis=0)
    dp = el.std(axis=0)
    if not (dp > 0).all():
        raise ValueError("parte sem variação entre seções")
    return (el - media) / dp, media, dp


def espaco(comp: Composicao) -> tuple[np.ndarray, np.ndarray | None, dict | None]:
    """Coordenadas da mistura, base para ler as cargas da PCA e a padronização.

    Na log-razão, a mistura roda nas coordenadas ILR e as cargas voltam às partes
    pela base; nas proporções padronizadas, cada coordenada já é uma parte.
    """
    if comp.espaco == "padronizada":
        x, media, dp = padronizar(comp.eleitorado)
        pad = {
            k: {
                "media_pct": r2(100 * float(media[i]), 4),
                "dp_pct": r2(100 * float(dp[i]), 4),
            }
            for i, k in enumerate(comp.chaves)
        }
        return x, None, pad
    _, x = coordenadas(comp.fr)
    return x, ilr_base(x.shape[1] + 1), None


def bloco(
    df: pd.DataFrame,
    comp: Composicao,
    nomes: Mapping[str, str],
    sementes: Sequence[int] = SEMENTES,
    inits: Sequence[str] = INITS,
    contraste: bool = True,
    diagnostico: bool = True,
    max_pontos: int = MAX_PONTOS,
    tol: float = TOL,
    max_iter: int = MAX_ITER,
    modo_diag: str = "refaz",
    amostra: int | None = None,
) -> dict[str, Any]:
    """Ajusta k = K e descreve componentes, anômalos, cruzamentos e PCA.

    Com `amostra`, a busca (sementes × inicializações, uma partida cada) roda numa
    amostra estratificada por UF e a melhor é refinada na base inteira.
    """
    fr, chaves = comp.fr, comp.chaves
    x, base, pad = espaco(comp)
    t0 = time.time()
    idx = amostra_estratificada(df["uf"].to_numpy(), amostra) if amostra else None
    n_init = 1 if amostra else N_INIT
    aj = ajustar_melhor(
        x,
        K,
        sementes=sementes,
        n_init=n_init,
        inits=inits,
        tol=tol,
        max_iter=max_iter,
        idx=idx,
    )
    diag, gm = convergencia(x, aj, modo_diag) if diagnostico else (None, aj.gm)
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
            outro = ajustar_melhor(
                x,
                kc,
                sementes=sementes,
                n_init=n_init,
                inits=inits[:1],
                tol=tol,
                max_iter=max_iter,
                idx=idx,
            )
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
    # com busca na amostra, as partidas se comparam com a melhor delas (mesmos
    # dados de ajuste); a diferença entre ela e o refino na base vai à parte
    ref = particoes[(aj.semente, aj.init)] if aj.amostra else bruto
    for linha in aj.log:
        rs = particoes[(linha["semente"], linha["init"])]
        linha["cramer_v_regiao"] = r2(cramer(pd.Series(rs), df["regiao"]), 3)
        linha["ari_com_escolhida"] = r2(adjusted_rand_score(ref, rs), 3)
    if diag is not None:
        diag["ajustes"] = aj.log
        if aj.amostra:
            diag["ari_amostra_base"] = r2(adjusted_rand_score(ref, bruto), 4)
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
        "busca_em_amostra": (
            {"secoes": len(idx), "estratos": "uf", "semente": SEMENTE}
            if idx is not None
            else None
        ),
        "covariancia": "full",
        "n_init": n_init,
        "inits": list(inits),
        "random_state": aj.semente,
        "init": aj.init,
        "sementes": aj.log,
        "inicializacoes": n_init * len(aj.log),
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
    log_razao = comp.espaco == "clr"
    extra_espaco = (
        {"degrau_log": degrau_log(comp.unidades)}
        if log_razao
        else {"padronizacao": pad}
    )
    return {
        "features": list(chaves),
        ("zeros_substituidos_pct" if log_razao else "zeros_celulas_pct"): r2(
            100 * float(zero.mean()), 2
        ),
        "zeros_por_parte": {
            k: {
                "secoes": int(zero[:, i].sum()),
                "pct_secoes": r2(100 * float(zero[:, i].mean()), 2),
            }
            for i, k in enumerate(chaves)
        },
        "secoes_com_zero": int(zero.any(axis=1).sum()),
        **extra_espaco,
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
        "pca": _pca(df, x, base, fr, chaves, rot, ll, max_pontos),
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


def projecao(
    x: np.ndarray, base: np.ndarray | None = None
) -> tuple[PCA, np.ndarray, np.ndarray]:
    """Dois componentes principais das coordenadas da mistura.

    Devolve o ajuste, os escores e as cargas por parte. Com `base` (a base ILR),
    as cargas são reescritas nas partes (CLR): como a base é ortonormal, a PCA
    nas coordenadas ILR e a PCA na CLR dão os mesmos escores e as mesmas
    variâncias, e a carga de cada parte é `V @ componente`. Sem `base`, cada
    coordenada já é uma parte (proporções padronizadas).
    """
    pca = PCA(n_components=2, random_state=SEMENTE)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        p = pca.fit_transform(x)
    cargas = pca.components_ @ base.T if base is not None else pca.components_
    return pca, p, cargas


def _pca(
    df: pd.DataFrame,
    x: np.ndarray,
    base: np.ndarray | None,
    fr: np.ndarray,
    chaves: Sequence[str],
    rot: np.ndarray,
    ll: np.ndarray,
    max_pontos: int = MAX_PONTOS,
) -> dict[str, Any]:
    pca, p, cargas = projecao(x, base)
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
            if base is not None
            else f"dois componentes principais das {x.shape[1]} proporções do "
            "eleitorado padronizadas (média zero, desvio-padrão um)"
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
