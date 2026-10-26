"""Motor da mistura gaussiana dos dois turnos: número de grupos, ajuste e contraste.

- ``tabela_bic``: para k = 2..10, oito sementes × duas inicializações (uma partida
  cada) numa amostra estratificada por UF; fica a partida convergida de maior
  log-verossimilhança, com BIC, ICL (BIC + 2 × entropia das responsabilidades, na
  escala de −2 log L), iterações e convergência.
- ``escolher_k``: regra declarada do joelho do BIC a 5% da queda total, ICL como
  alternativa, 3 ≤ k* ≤ 10.
- ``ajustar_base``: as mesmas 16 partidas na base inteira; nunca escolhe partida
  não convergida (cada uma repete com ``max_iter`` dobrado antes de desistir).
- Partida degenerada: algum componente com menor autovalor da covariância abaixo
  de ``LIMIAR_DEGENERADA`` (1e-4 nas coordenadas padronizadas, espalhamento abaixo
  de 1% do desvio entre seções, muito menor que o efeito de um voto). Acontece
  quando um componente se cola num valor exato de uma fração discreta (por
  exemplo, todas as seções com zero branco no 2T): a verossimilhança cresce sem
  limite, só segurada por ``reg_covar``. É o maximizador espúrio da literatura
  (McLachlan e Peel, 2000, seção 3.10); a partida fica fora da escolha e é contada.
- ``kmeans_contraste``: k-means nos dois enquadramentos (níveis; níveis e deltas),
  com inércia, silhueta numa amostra fixa de 20.000 seções e convergência.

As partidas rodam em processos separados, com uma linha de execução de álgebra
linear cada (``uma_thread`` do 1º turno): o numpy do macOS com Accelerate emite
avisos falsos de divisão por zero em produtos de matriz; os avisos são
silenciados e todo resultado é conferido como finito.
"""

from __future__ import annotations

import os
import time
import warnings
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np
from apuracao_2026.secoes_base import r2
from apuracao_2026.secoes_clusters_motor import Ajuste, escolher_anomalo, uma_thread
from sklearn.cluster import KMeans
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture

SEMENTE = 20261026
N_SEMENTES = 8
SEMENTES = tuple(SEMENTE + i for i in range(N_SEMENTES))
INITS = ("kmeans", "k-means++")
TOL = 1e-6
MAX_ITER = 2000
REG_COVAR = 1e-6
MAX_DOBRAS = 2  # max_iter 2.000 → 4.000 → 8.000 antes de desistir
LIMIAR_DEGENERADA = 1e-4  # menor autovalor de covariância, coordenadas padronizadas
K_FAIXA = tuple(range(2, 11))
K_PISO, K_TETO = 3, 10
LIMIAR_JOELHO = 0.05
AMOSTRA_BIC = 120_000
EMPATE_LOGLIK = 1e-3
KM_N_INIT = 10
KM_MAX_ITER = 1000
KM_TOL = 1e-6
SILHUETA_N = 20_000
MAX_PROCESSOS = 16

_DADOS: dict[str, Any] = {}


def _iniciar(dados: Mapping[str, Any]) -> None:
    _DADOS.clear()
    _DADOS.update(dados)


def gmm(
    k: int,
    semente: int,
    init: str,
    tol: float = TOL,
    max_iter: int = MAX_ITER,
    **extra: Any,
) -> GaussianMixture:
    return GaussianMixture(
        n_components=k,
        covariance_type="full",
        n_init=1,
        init_params=init,
        random_state=semente,
        max_iter=max_iter,
        tol=tol,
        reg_covar=REG_COVAR,
        **extra,
    )


def min_autovalor(gm: GaussianMixture) -> float:
    """Menor autovalor entre as covariâncias dos componentes."""
    return float(min(np.linalg.eigvalsh(c).min() for c in gm.covariances_))


def degenerada(gm: GaussianMixture) -> bool:
    return min_autovalor(gm) < LIMIAR_DEGENERADA


def entropia(gm: GaussianMixture, x: np.ndarray) -> float:
    """−Σ τ log τ das responsabilidades (zero onde τ = 0)."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        tau = gm.predict_proba(x)
        termo = np.where(tau > 0, tau * np.log(np.where(tau > 0, tau, 1.0)), 0.0)
    return float(-termo.sum())


def partida(
    x: np.ndarray,
    k: int,
    semente: int,
    init: str,
    tol: float = TOL,
    max_iter: int = MAX_ITER,
    icl: bool = False,
) -> dict[str, Any]:
    """Uma partida (n_init = 1); sem convergir, refaz com ``max_iter`` dobrado."""
    mi = max_iter
    t0 = time.time()
    for dobra in range(MAX_DOBRAS + 1):
        gm = gmm(k, semente, init, tol, mi)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            gm.fit(x)
            ll = float(gm.score(x))
        if gm.converged_ or dobra == MAX_DOBRAS:
            break
        mi *= 2
    if not np.isfinite(ll):
        raise ValueError("log-verossimilhança não finita")
    mev = min_autovalor(gm)
    out = {
        "k": k,
        "semente": semente,
        "init": init,
        "loglik_media": ll,
        "convergiu": bool(gm.converged_),
        "min_autovalor": mev,
        "degenerada": mev < LIMIAR_DEGENERADA,
        "iteracoes": int(gm.n_iter_),
        "max_iter_usado": mi,
        "dobras": dobra,
        "segundos": time.time() - t0,
        "gm": gm,
    }
    if icl:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            bic = float(gm.bic(x))
        en = entropia(gm, x)
        out |= {"bic": bic, "entropia": en, "icl": bic + 2 * en}
    return out


def _tarefa(args: tuple[Any, ...]) -> dict[str, Any]:
    tipo = args[0]
    if tipo == "gmm":
        _, nome, k, s, init, tol, max_iter, icl = args
        return partida(_DADOS[nome], k, s, init, tol, max_iter, icl)
    _, nome, k = args
    return _kmeans(_DADOS[nome], k, _DADOS.get("idx_silhueta"))


def rodar(
    dados: Mapping[str, Any],
    tarefas: Sequence[tuple[Any, ...]],
    paralelo: bool = True,
) -> list[dict[str, Any]]:
    """Roda as tarefas; em processos separados quando ``paralelo``.

    Cada tarefa tem o próprio ``random_state``: o resultado não depende da ordem
    nem do paralelismo.
    """
    if paralelo and len(tarefas) > 1:
        n = min(len(tarefas), os.cpu_count() or 1, MAX_PROCESSOS)
        with (
            uma_thread(),
            ProcessPoolExecutor(
                max_workers=n, initializer=_iniciar, initargs=(dict(dados),)
            ) as ex,
        ):
            return list(ex.map(_tarefa, tarefas))
    _iniciar(dados)
    try:
        return [_tarefa(t) for t in tarefas]
    finally:
        _DADOS.clear()


def _publica(p: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "semente": p["semente"],
        "init": p["init"],
        "loglik_media": r2(p["loglik_media"], 6),
        "convergiu": p["convergiu"],
        "degenerada": p["degenerada"],
        "min_autovalor": float(f"{p['min_autovalor']:.3e}"),
        "iteracoes": p["iteracoes"],
        "max_iter_usado": p["max_iter_usado"],
    }


def valida(p: Mapping[str, Any]) -> bool:
    """Partida elegível: convergiu e não degenerou."""
    return bool(p["convergiu"]) and not p.get("degenerada", False)


def melhor(partidas: Sequence[Mapping[str, Any]], inits: Sequence[str]) -> Any:
    """A partida válida de maior log-verossimilhança (empate: a primeira
    inicialização, a menor semente). Sem nenhuma válida, levanta: nada é publicado."""
    ok = [p for p in partidas if valida(p)]
    if not ok:
        conv = sum(bool(p["convergiu"]) for p in partidas)
        raise RuntimeError(
            f"nenhuma partida válida: {conv} de {len(partidas)} convergiram (max_iter "
            f"dobrado até {MAX_DOBRAS} vezes) e todas as convergidas degeneraram; "
            "nada é publicado"
        )
    return min(
        ok,
        key=lambda p: (
            -round(p["loglik_media"], 9),
            list(inits).index(p["init"]),
            p["semente"],
        ),
    )


def tabela_bic(
    xs: np.ndarray,
    ks: Sequence[int] = K_FAIXA,
    sementes: Sequence[int] = SEMENTES,
    inits: Sequence[str] = INITS,
    tol: float = TOL,
    max_iter: int = MAX_ITER,
    paralelo: bool = True,
) -> tuple[list[dict[str, Any]], dict[int, GaussianMixture]]:
    """Uma linha por k com a melhor partida convergida na amostra."""
    tarefas = [
        ("gmm", "xs", k, s, i, tol, max_iter, True)
        for k in ks
        for i in inits
        for s in sementes
    ]
    res = rodar({"xs": xs}, tarefas, paralelo)
    linhas, modelos = [], {}
    for k in ks:
        pk = [p for p in res if p["k"] == k]
        b = melhor(pk, inits)
        lls = [p["loglik_media"] for p in pk if valida(p)]
        linhas.append(
            {
                "k": k,
                "bic": r2(b["bic"], 1),
                "icl": r2(b["icl"], 1),
                "entropia": r2(b["entropia"], 1),
                "loglik_media": r2(b["loglik_media"], 6),
                "iteracoes": b["iteracoes"],
                "convergiu": b["convergiu"],
                "semente": b["semente"],
                "init": b["init"],
                "partidas": len(pk),
                "partidas_convergiram": sum(p["convergiu"] for p in pk),
                "partidas_degeneradas": sum(p["degenerada"] for p in pk),
                "partidas_no_maximo": sum(
                    v >= b["loglik_media"] - EMPATE_LOGLIK for v in lls
                ),
                "max_iter_usado": max(p["max_iter_usado"] for p in pk),
            }
        )
        modelos[k] = b["gm"]
    return linhas, modelos


def escolher_k(
    linhas: Sequence[Mapping[str, Any]],
    limiar: float = LIMIAR_JOELHO,
    piso: int = K_PISO,
    teto: int = K_TETO,
) -> dict[str, Any]:
    """k* pela regra declarada.

    Joelho: o menor k cuja queda do BIC até k + 1 fica abaixo de ``limiar`` da
    queda total entre o menor e o maior k da tabela. Sem joelho (nenhuma queda
    abaixo do limiar, ou queda total não positiva), k* = argmin do ICL. O
    resultado fica entre ``piso`` e ``teto``.
    """
    t = sorted(linhas, key=lambda r: r["k"])
    ks = [int(r["k"]) for r in t]
    bic = np.array([float(r["bic"]) for r in t])
    icl = np.array([float(r["icl"]) for r in t])
    total = float(bic[0] - bic[-1])
    quedas = [
        {
            "de": ks[i],
            "para": ks[i + 1],
            "queda": r2(bic[i] - bic[i + 1], 1),
            "pct_da_total": (
                r2(100 * (bic[i] - bic[i + 1]) / total, 2) if total else None
            ),
        }
        for i in range(len(ks) - 1)
    ]
    joelho = None
    if total > 0:
        for i in range(len(ks) - 1):
            if bic[i] - bic[i + 1] < limiar * total:
                joelho = ks[i]
                break
    k_icl = ks[int(np.argmin(icl))]
    if joelho is not None:
        bruto, origem = joelho, "joelho_bic"
        texto = (
            f"joelho do BIC: k = {joelho} é o menor k em que a queda do BIC até "
            f"k + 1 fica abaixo de {round(100 * limiar)}% da queda total de "
            f"k = {ks[0]} a k = {ks[-1]}"
        )
    else:
        bruto, origem = k_icl, "min_icl"
        texto = (
            f"sem joelho (nenhuma queda do BIC abaixo de {round(100 * limiar)}% da "
            f"queda total de k = {ks[0]} a k = {ks[-1]}): k = {k_icl}, o menor ICL"
        )
    k = min(max(bruto, piso), teto)
    if k != bruto:
        texto += f"; levado a {k} pelo limite declarado ({piso} ≤ k ≤ {teto})"
    return {
        "k_escolhido": k,
        "k_joelho_bic": joelho,
        "k_min_icl": k_icl,
        "k_min_bic": ks[int(np.argmin(bic))],
        "origem": origem,
        "regra": texto,
        "regra_declarada": (
            f"k* é o menor k em que a queda do BIC do passo seguinte fica abaixo de "
            f"{round(100 * limiar)}% da queda total de k = {ks[0]} até k = {ks[-1]} "
            f"(o joelho); sem joelho, k* = argmin do ICL; {piso} ≤ k* ≤ {teto}"
        ),
        "quedas": quedas,
        "queda_total": r2(total, 1),
    }


def ajustar_base(
    x: np.ndarray,
    k: int,
    sementes: Sequence[int] = SEMENTES,
    inits: Sequence[str] = INITS,
    tol: float = TOL,
    max_iter: int = MAX_ITER,
    paralelo: bool = True,
) -> Ajuste:
    """As partidas sementes × inicializações na base; fica a melhor convergida.

    Devolve o ``Ajuste`` do 1º turno (gm, semente, init, log, todos, amostra),
    que ``secoes_clusters_diag.convergencia`` sabe ler.
    """
    tarefas = [
        ("gmm", "x", k, s, i, tol, max_iter, False) for i in inits for s in sementes
    ]
    res = rodar({"x": x}, tarefas, paralelo)
    b = melhor(res, inits)
    return Ajuste(
        b["gm"],
        b["semente"],
        b["init"],
        [_publica(p) for p in res],
        [(p["semente"], p["init"], p["gm"]) for p in res],
        None,
    )


def ordem_por_lula2(rot: np.ndarray, lula2: np.ndarray, k: int) -> np.ndarray:
    """Mapa componente → id, por Lula no 2T (% do eleitorado) médio crescente."""
    medias = [
        float(np.mean(lula2[rot == c])) if (rot == c).any() else np.inf
        for c in range(k)
    ]
    ordem = np.argsort(np.asarray(medias), kind="stable")
    novo = np.empty_like(ordem)
    novo[ordem] = np.arange(len(ordem))
    return novo


def postos_anomalo(
    loglik_media: Sequence[float], dispersao: Sequence[float]
) -> list[dict[str, Any]]:
    """Todos os grupos pelo critério do 1º turno, do mais atípico ao menos.

    Soma dos postos de menor log-verossimilhança média e de maior dispersão;
    empate pela menor log-verossimilhança média. O primeiro coincide com
    ``escolher_anomalo``.
    """
    ll = np.asarray(loglik_media, dtype=float)
    dp = np.asarray(dispersao, dtype=float)
    r_ll = np.argsort(np.argsort(ll, kind="stable"), kind="stable")
    r_dp = np.argsort(np.argsort(-dp, kind="stable"), kind="stable")
    soma = r_ll + r_dp
    ordem = sorted(range(len(ll)), key=lambda c: (int(soma[c]), float(ll[c])))
    if ordem[0] != escolher_anomalo(ll, dp):
        raise AssertionError("ordem dos postos diverge de escolher_anomalo")
    return [
        {
            "id": int(c),
            "posto_loglik": int(r_ll[c]),
            "posto_dispersao": int(r_dp[c]),
            "soma_postos": int(soma[c]),
        }
        for c in ordem
    ]


def pontuar(gm: GaussianMixture, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Log-densidade da mistura por seção e a parcela do país abaixo dela."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        s = np.asarray(gm.score_samples(x), dtype=float)
    if not np.isfinite(s).all():
        raise ValueError("log-densidade não finita")
    ordenado = np.sort(s)
    p = np.searchsorted(ordenado, s, side="left") / len(s)
    return s, p


def prever(gm: GaussianMixture, x: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return np.asarray(gm.predict(x))


# ---------------------------------------------------------------- k-means


def _kmeans(x: np.ndarray, k: int, idx: np.ndarray | None) -> dict[str, Any]:
    km = KMeans(
        n_clusters=k,
        n_init=KM_N_INIT,
        max_iter=KM_MAX_ITER,
        tol=KM_TOL,
        random_state=SEMENTE,
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        rot = km.fit_predict(x)
        sil = (
            float(silhouette_score(x[idx], rot[idx]))
            if idx is not None and len(np.unique(rot[idx])) > 1
            else None
        )
    return {
        "k": k,
        "inercia": float(km.inertia_),
        "silhueta": sil,
        "iteracoes": int(km.n_iter_),
        "convergiu": int(km.n_iter_) < KM_MAX_ITER,
        "rot": rot.astype(np.int16),
    }


def kmeans_contraste(
    frames: Mapping[str, np.ndarray],
    ks: Sequence[int] = K_FAIXA,
    n_silhueta: int = SILHUETA_N,
    paralelo: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """k-means em cada enquadramento, k = 2..10, com silhueta em amostra fixa."""
    n = len(next(iter(frames.values())))
    rng = np.random.default_rng(SEMENTE)
    idx = np.sort(rng.choice(n, size=min(n, n_silhueta), replace=False))
    tarefas = [("kmeans", nome, k) for nome in frames for k in ks]
    res = rodar({**frames, "idx_silhueta": idx}, tarefas, paralelo)
    out: dict[str, list[dict[str, Any]]] = {}
    for (_, nome, _k), r in zip(tarefas, res, strict=True):
        out.setdefault(nome, []).append(r)
    return out
