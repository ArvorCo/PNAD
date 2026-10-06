"""Diagnóstico de convergência da mistura gaussiana (pedido de 06/10/2026).

Três perguntas, com a resposta gravada em `clusters.ajuste.diagnostico_convergencia`:

1. O EM foi até a convergência? Cada partida já traz `converged_` e `n_iter_`
   (o sklearn para quando a log-verossimilhança média muda menos que `tol`,
   1e-4). A melhor partida é refeita com `tol` 1e-6 e até 2.000 iterações, do
   mesmo `random_state` e da mesma inicialização. Se a log-verossimilhança média
   subir mais que 1e-3 por seção ou a partição mudar (índice de Rand ajustado
   abaixo de 0,99), o critério padrão estava parando cedo e o ajuste apertado é
   o adotado.
2. O máximo escolhido é o melhor que a busca encontra? 16 sementes e duas
   inicializações (`kmeans` e `k-means++`), dez partidas internas cada: quantas
   chegam ao mesmo máximo, a 1e-3 por seção.
3. A partição é estável? Índice de Rand ajustado contra a partição escolhida,
   em média, entre as partidas que chegam ao máximo e entre as demais.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

from .secoes_base import num, r2

TOL_APERTADO = 1e-6
MAX_ITER_APERTADO = 2000
LIMIAR_LOGLIK = 1e-3  # por seção
LIMIAR_ARI = 0.99
EMPATE = 1e-3


def _score(gm: GaussianMixture, x: np.ndarray) -> float:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        ll = float(gm.score(x))
    if not np.isfinite(ll):
        raise ValueError("log-verossimilhança não finita")
    return ll


def _prever(gm: GaussianMixture, x: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return gm.predict(x)


def apertar(gm: GaussianMixture, x: np.ndarray) -> GaussianMixture:
    """A mesma partida (semente, inicialização, partidas internas), tol 1e-6."""
    params = gm.get_params() | {"tol": TOL_APERTADO, "max_iter": MAX_ITER_APERTADO}
    novo = GaussianMixture(**params)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        novo.fit(x)
    return novo


def convergencia(x: np.ndarray, aj: Any) -> tuple[dict[str, Any], GaussianMixture]:
    """Reajuste apertado da melhor partida; devolve o diagnóstico e o ajuste adotado.

    `aj` é o `Ajuste` de `secoes_clusters.ajustar_melhor` (gm, semente, init).
    """
    gm = aj.gm
    ap = apertar(gm, x)
    ll_p, ll_a = _score(gm, x), _score(ap, x)
    ari = float(adjusted_rand_score(_prever(gm, x), _prever(ap, x)))
    adota = (ll_a - ll_p) > LIMIAR_LOGLIK or ari < LIMIAR_ARI
    diag = {
        "criterio_padrao": {"tol": float(gm.tol), "max_iter": int(gm.max_iter)},
        "sementes": len({s for s, _, _ in aj.todos}),
        "inits": sorted({i for _, i, _ in aj.todos}, key=["kmeans", "k-means++"].index),
        "partidas_internas": int(gm.n_init),
        "escolhida": {"semente": aj.semente, "init": aj.init},
        "apertado": {
            "tol": TOL_APERTADO,
            "max_iter": MAX_ITER_APERTADO,
            "convergiu": bool(ap.converged_),
            "iteracoes": int(ap.n_iter_),
            "iteracoes_padrao": int(gm.n_iter_),
            "loglik_media_padrao": r2(ll_p, 6),
            "loglik_media_apertado": r2(ll_a, 6),
            "diferenca_loglik": r2(ll_a - ll_p, 6),
            "ari_padrao_apertado": r2(ari, 4),
            "adotado": bool(adota),
            "regra": (
                "adota o apertado se a log-verossimilhança média subir mais que "
                f"{num(LIMIAR_LOGLIK, 3)} por seção ou o índice de Rand ajustado "
                f"ficar abaixo de {num(LIMIAR_ARI, 2)}"
            ),
        },
        "tolerancia_maximo": EMPATE,
    }
    return diag, (ap if adota else gm)


def _media(v: Sequence[float]) -> float | None:
    return r2(float(np.mean(v)), 3) if v else None


def resumir(diag: dict[str, Any]) -> None:
    """Completa o diagnóstico com a tabela das partidas (`diag['ajustes']`)."""
    aj = diag["ajustes"]
    lls = [a["loglik_media"] for a in aj]
    m = max(lls)
    no_max = [a for a in aj if a["loglik_media"] >= m - EMPATE]
    demais = [a for a in aj if a["loglik_media"] < m - EMPATE]
    diag["total"] = len(aj)
    diag["no_maximo"] = len(no_max)
    diag["por_init"] = {
        i: {
            "total": sum(a["init"] == i for a in aj),
            "no_maximo": sum(a["init"] == i for a in no_max),
        }
        for i in diag["inits"]
    }
    diag["todas_convergiram"] = all(a["convergiu"] for a in aj)
    its = [a["iteracoes"] for a in aj]
    diag["iteracoes"] = [min(its), max(its)]
    diag["loglik_media"] = [min(lls), max(lls)]
    diag["ari_medio_no_maximo"] = _media([a["ari_com_escolhida"] for a in no_max])
    diag["ari_medio_demais"] = _media([a["ari_com_escolhida"] for a in demais])
    diag["particao_estavel"] = (diag["ari_medio_no_maximo"] or 0) >= LIMIAR_ARI
    diag["frase"] = frase(diag)


def frase(d: Mapping[str, Any]) -> str:
    """'O EM convergiu nas N partidas ...; N de M chegaram ao mesmo máximo; ...'."""
    ap = d["apertado"]
    cp = d["criterio_padrao"]
    falhas = sum(1 for a in d["ajustes"] if not a["convergiu"])
    conv = (
        f"O EM convergiu nas {d['total']} partidas"
        if not falhas
        else f"O EM não convergiu em {falhas} das {d['total']} partidas"
    )
    texto = (
        f"{conv} ({d['sementes']} sementes, inicializações {' e '.join(d['inits'])}, "
        f"{d['partidas_internas']} partidas internas cada; critério do sklearn: "
        f"variação da log-verossimilhança média abaixo de {num(cp['tol'], 4)}, de "
        f"{d['iteracoes'][0]} a {d['iteracoes'][1]} iterações). Refeita com tolerância "
        f"{num(ap['tol'], 6)} e até {num(ap['max_iter'], 0)} iterações, a melhor "
        f"partida foi de {ap['iteracoes_padrao']} para {ap['iteracoes']} iterações e "
        f"a log-verossimilhança média subiu {num(ap['diferenca_loglik'], 6)} por seção"
    )
    ari = ap["ari_padrao_apertado"]
    if ap["adotado"]:
        texto += (
            f", mas a partição mudou (índice de Rand ajustado de {num(ari, 2)} entre as "
            "duas): pelo critério declarado, o padrão parava cedo, e o ajuste publicado "
            "é o apertado."
            if (ap["diferenca_loglik"] or 0) <= LIMIAR_LOGLIK
            else f" (índice de Rand ajustado de {num(ari, 2)} entre as duas partições): "
            "o padrão parava cedo, e o ajuste publicado é o apertado."
        )
    else:
        texto += (
            f" e a partição quase não mudou (índice de Rand ajustado de {num(ari, 2)}): "
            "o padrão não parava cedo."
        )
    texto += (
        f" {d['no_maximo']} de {d['total']} partidas chegaram ao mesmo máximo, a "
        f"{num(d['tolerancia_maximo'], 3)} por seção"
    )
    pi = d.get("por_init") or {}
    if len(pi) > 1:
        texto += (
            " ("
            + "; ".join(f"{i}: {v['no_maximo']} de {v['total']}" for i, v in pi.items())
            + ")"
        )
    ari_m, ari_d = d.get("ari_medio_no_maximo"), d.get("ari_medio_demais")
    estavel = "estável" if d["particao_estavel"] else "instável"
    texto += (
        f". A partição escolhida é {estavel}: índice de Rand ajustado médio de "
        f"{num(ari_m or 0, 2)} contra as partidas que chegam ao máximo"
    )
    texto += (
        f" e de {num(ari_d, 2)} contra as demais."
        if ari_d is not None
        else ", e não há outras."
    )
    return texto
