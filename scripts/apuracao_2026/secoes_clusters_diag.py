"""Diagnóstico de convergência da mistura gaussiana (pedido de 06/10/2026).

Três perguntas, com a resposta gravada em `clusters.ajuste.diagnostico_convergencia`:

1. O EM foi até a convergência? Cada partida já traz `converged_` e `n_iter_`
   (o sklearn para quando a log-verossimilhança média muda menos que `tol`).
   Dois modos de conferir a melhor partida:
   - `refaz` (tentativas de log-razão, tol 1e-4): refaz a partida com `tol`
     1e-6 e até 2.000 iterações, do mesmo `random_state` e da mesma
     inicialização;
   - `continua` (modelo principal, já ajustado com tol 1e-6): continua o EM a
     partir dos parâmetros escolhidos (`warm_start`), com `tol` 1e-8 e até
     5.000 iterações a mais.
   Se a log-verossimilhança média subir mais que 1e-3 por seção ou a partição
   mudar (índice de Rand ajustado abaixo de 0,99), o critério estava parando
   cedo e o ajuste apertado é o adotado.
2. O máximo escolhido é o melhor que a busca encontra? 16 sementes e duas
   inicializações (`kmeans` e `k-means++`), dez partidas internas cada: quantas
   chegam ao mesmo máximo, a 1e-3 por seção.
3. A partição é estável? Índice de Rand ajustado contra a partição escolhida,
   em média, entre as partidas que chegam ao máximo e entre as demais.
"""

from __future__ import annotations

import copy
import warnings
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

from .secoes_base import num, r2

TOL_APERTADO = 1e-6
MAX_ITER_APERTADO = 2000
TOL_CONTINUA = 1e-8
MAX_ITER_CONTINUA = 5000
LIMIAR_LOGLIK = 1e-3  # por seção
LIMIAR_ARI = 0.99  # reajuste apertado: partição "igual"
ESTAVEL = 0.95  # ARI médio entre as partidas no máximo
ESSENCIAL = 0.80
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


def apertar(gm: GaussianMixture, x: np.ndarray, modo: str = "refaz") -> GaussianMixture:
    """`refaz`: a mesma partida com tol 1e-6; `continua`: o EM segue do ajuste."""
    if modo == "continua":
        novo = copy.deepcopy(gm)
        novo.set_params(
            tol=TOL_CONTINUA, max_iter=MAX_ITER_CONTINUA, warm_start=True, n_init=1
        )
    else:
        params = gm.get_params() | {
            "tol": TOL_APERTADO,
            "max_iter": MAX_ITER_APERTADO,
        }
        novo = GaussianMixture(**params)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        novo.fit(x)
    return novo


def convergencia(
    x: np.ndarray, aj: Any, modo: str = "refaz"
) -> tuple[dict[str, Any], GaussianMixture]:
    """Confere a melhor partida com critério mais apertado; devolve o diagnóstico
    e o ajuste adotado.

    `aj` é o `Ajuste` de `secoes_clusters.ajustar_melhor` (gm, semente, init).
    """
    gm = aj.gm
    ap = apertar(gm, x, modo)
    ll_p, ll_a = _score(gm, x), _score(ap, x)
    ari = float(adjusted_rand_score(_prever(gm, x), _prever(ap, x)))
    adota = (ll_a - ll_p) > LIMIAR_LOGLIK or ari < LIMIAR_ARI
    continua = modo == "continua"
    diag = {
        "criterio_padrao": {"tol": float(gm.tol), "max_iter": int(gm.max_iter)},
        "sementes": len({s for s, _, _ in aj.todos}),
        "inits": sorted({i for _, i, _ in aj.todos}, key=["kmeans", "k-means++"].index),
        "partidas_internas": int(gm.n_init) if aj.amostra is None else 1,
        "amostra": aj.amostra,
        "escolhida": {"semente": aj.semente, "init": aj.init},
        "apertado": {
            "modo": modo,
            "tol": TOL_CONTINUA if continua else TOL_APERTADO,
            "max_iter": MAX_ITER_CONTINUA if continua else MAX_ITER_APERTADO,
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


def dec(v: float) -> str:
    """Decimal pequeno sem zeros à direita, com vírgula: 1e-6 → '0,000001'."""
    return f"{v:.12f}".rstrip("0").rstrip(".").replace(".", ",")


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
    ari_max = [a["ari_com_escolhida"] for a in no_max]
    diag["ari_no_maximo_faixa"] = [min(ari_max), max(ari_max)] if ari_max else None
    media = diag["ari_medio_no_maximo"] or 0
    diag["particao_estavel"] = media >= ESTAVEL
    diag["estabilidade"] = (
        "estável"
        if media >= ESTAVEL
        else "estável no essencial" if media >= ESSENCIAL else "instável"
    )
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
    internas = (
        "uma partida cada"
        if d["partidas_internas"] == 1
        else f"{d['partidas_internas']} partidas internas cada"
    )
    onde = (
        f", na amostra estratificada por UF de {num(d['amostra'], 0)} seções"
        if d.get("amostra")
        else ""
    )
    texto = (
        f"{conv} ({d['sementes']} sementes, inicializações {' e '.join(d['inits'])}, "
        f"{internas}{onde}; critério do sklearn: variação da log-verossimilhança "
        f"média abaixo de {dec(cp['tol'])}, de {d['iteracoes'][0]} a "
        f"{d['iteracoes'][1]} iterações). "
    )
    if d.get("amostra"):
        ari_ab = d.get("ari_amostra_base")
        texto += (
            "A melhor partida foi refinada na base inteira, a partir dos parâmetros "
            "da amostra"
            + (
                f" (índice de Rand ajustado de {num(ari_ab, 2)} entre as duas partições)"
                if ari_ab is not None
                else ""
            )
            + ". "
        )
    if ap.get("modo") == "continua":
        texto += (
            f"Continuado a partir do ajuste escolhido, com tolerância "
            f"{dec(ap['tol'])} e até {num(ap['max_iter'], 0)} iterações a mais, o "
            f"EM rodou {ap['iteracoes']} iterações e a log-verossimilhança média subiu "
            f"{num(ap['diferenca_loglik'], 6)} por seção"
        )
    else:
        texto += (
            f"Refeita com tolerância {dec(ap['tol'])} e até "
            f"{num(ap['max_iter'], 0)} iterações, a melhor partida foi de "
            f"{ap['iteracoes_padrao']} para {ap['iteracoes']} iterações e a "
            f"log-verossimilhança média subiu {num(ap['diferenca_loglik'], 6)} por seção"
        )
    ari = ap["ari_padrao_apertado"]
    if ap["adotado"]:
        texto += (
            f", mas a partição mudou (índice de Rand ajustado de {num(ari, 2)} entre as "
            "duas): pelo critério declarado, o ajuste anterior parava cedo, e o publicado "
            "é o apertado."
            if (ap["diferenca_loglik"] or 0) <= LIMIAR_LOGLIK
            else f" (índice de Rand ajustado de {num(ari, 2)} entre as duas partições): "
            "o ajuste anterior parava cedo, e o publicado é o apertado."
        )
    else:
        texto += (
            f" e a partição quase não mudou (índice de Rand ajustado de {num(ari, 2)}): "
            "o critério não parava cedo."
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
    estavel = d.get("estabilidade") or (
        "estável" if d["particao_estavel"] else "instável"
    )
    contra = "a melhor delas" if d.get("amostra") else "a escolhida"
    faixa = d.get("ari_no_maximo_faixa")
    de_a = (
        f", de {num(faixa[0], 2)} a {num(faixa[1], 2)}"
        if faixa and faixa[0] != faixa[1]
        else ""
    )
    texto += (
        f". A partição é {estavel}: índice de Rand ajustado médio, contra {contra}, de "
        f"{num(ari_m or 0, 2)} entre as partidas que chegam ao máximo{de_a}"
    )
    texto += (
        f"; de {num(ari_d, 2)} entre as demais."
        if ari_d is not None
        else ", e não há outras."
    )
    return texto
