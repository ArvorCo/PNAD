"""Pergunta B: mistura gaussiana (k = 3) sobre a composição do eleitorado da seção.

Atributos por seção: votos de cada uma das 12 candidaturas a presidente, brancos,
nulos e abstenção, todos divididos pelos aptos da eleição federal. As 15 frações
somam 1, então o espaço é composicional: aplica-se a log-razão centrada (CLR),
com zeros trocados por 0,0001 antes do log, como pedido. A CLR de 15 partes vive
num subespaço de 14 dimensões (cada linha soma zero), o que tornaria singular a
covariância completa; por isso a mistura é ajustada nas 14 coordenadas
ortonormais desse subespaço (log-razão isométrica, ILR). A troca é uma rotação:
distâncias de Mahalanobis e a densidade relativa entre seções não mudam.

k = 3 é escolha do autor (05/10/2026, antes 4), pela leitura visual da projeção
em dois componentes principais. O BIC de k = 3, 4 e 5 continua na tabela de
comparação, ao lado da escolha, e o texto diz qual k o BIC prefere.

A verossimilhança tem muitos máximos locais: com quase metade das células em
zero, cada padrão exato de zeros é um subespaço onde um componente pode se
encaixar com variância quase nula. Uma semente só (10 inicializações) pode parar
longe do melhor ajuste; por isso cada k é ajustado com várias sementes, fica o de
maior log-verossimilhança e o JSON guarda a de cada semente.

A especificação pedida é o modelo principal. Como quase metade das células é
zero (candidaturas nanicas sem voto na seção), a mesma mistura é refeita com as
candidaturas de menos de 1% dos válidos somadas numa parte só e com cinco partes
quase sem zeros; as versões saem no JSON com a mesma estrutura.

O numpy ligado ao Accelerate (macOS) emite avisos falsos de divisão por zero em
produtos de matriz; os avisos são silenciados e todo resultado é conferido como
finito.
"""

from __future__ import annotations

import os
import time
import warnings
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from typing import Any, NamedTuple

import numpy as np
import pandas as pd
from scipy.linalg import null_space
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

from .secoes_base import FLAVIO, LULA, ZERO, Base, amostras, clr, pct, r2
from .secoes_clusters_leitura import (
    NOMES_PARTES,
    estabilidade,
    interpretar,
    leitura_projecao,
    menos_votadas,
    padroes_zeros,
    rotulo,
)

SEMENTE = 20261005
N_SEMENTES = 8
SEMENTES = tuple(SEMENTE + i for i in range(N_SEMENTES))
K = 3
K_TABELA = (3, 4, 5)
ESCOLHA_K = {
    "k": K,
    "anterior": 4,
    "data": "05/10/2026",
    "motivo": (
        "escolha do autor pela leitura visual da projeção em dois componentes "
        "principais"
    ),
}
N_INIT = 10
MAX_PONTOS = 8000
TOP_FIGURA = 200
LIMIAR_NANICO = 0.01
EMPATE_LOGLIK = 1e-3
MIN_PARALELO = 50_000  # seções; abaixo disso as sementes rodam em série
MAX_PROCESSOS = 8


class Ajuste(NamedTuple):
    gm: GaussianMixture
    semente: int
    log: list[dict[str, Any]]
    segundo: GaussianMixture | None
    semente_segundo: int | None
    todos: list[tuple[int, GaussianMixture]]


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
    x: np.ndarray, k: int, n_init: int = N_INIT, semente: int = SEMENTE
) -> GaussianMixture:
    gm = GaussianMixture(
        n_components=k,
        covariance_type="full",
        n_init=n_init,
        random_state=semente,
        max_iter=500,
        tol=1e-4,
        reg_covar=1e-6,
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        gm.fit(x)
    return gm


def _ajuste_semente(
    args: tuple[np.ndarray, int, int, int],
) -> tuple[float, int, GaussianMixture]:
    """Um ajuste e a log-verossimilhança média (função de módulo: vai ao processo)."""
    x, k, n_init, s = args
    gm = ajustar(x, k, n_init=n_init, semente=s)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        ll = float(gm.score(x))
    if not np.isfinite(ll):
        raise ValueError(f"log-verossimilhança não finita (k = {k}, semente {s})")
    return ll, s, gm


def ajustar_melhor(
    x: np.ndarray, k: int, sementes: Sequence[int] = SEMENTES, n_init: int = N_INIT
) -> Ajuste:
    """Um ajuste por semente; fica o de maior log-verossimilhança média.

    O segundo melhor (outra semente) serve para medir a estabilidade da partição.
    Com a base inteira, as sementes rodam em processos separados; cada uma tem o
    próprio `random_state`, então o resultado é o mesmo da execução em série.
    """
    tarefas = [(x, k, n_init, s) for s in sementes]
    if len(sementes) > 1 and len(x) >= MIN_PARALELO:
        n = min(len(sementes), os.cpu_count() or 1, MAX_PROCESSOS)
        with ProcessPoolExecutor(max_workers=n) as ex:
            ajustes = list(ex.map(_ajuste_semente, tarefas))
    else:
        ajustes = [_ajuste_semente(t) for t in tarefas]
    ordem = sorted(ajustes, key=lambda a: (-a[0], a[1]))
    log = [
        {
            "semente": s,
            "loglik_media": r2(ll, 4),
            "convergiu": bool(gm.converged_),
            "iteracoes": int(gm.n_iter_),
        }
        for ll, s, gm in ajustes
    ]
    seg = ordem[1] if len(ordem) > 1 else None
    return Ajuste(
        ordem[0][2],
        ordem[0][1],
        log,
        seg[2] if seg else None,
        seg[1] if seg else None,
        [(sm, g) for _, sm, g in ajustes],
    )


def mahalanobis_proprio(
    gm: GaussianMixture, x: np.ndarray, rotulos: np.ndarray
) -> np.ndarray:
    d2 = np.full(len(x), np.nan)
    for c in range(gm.n_components):
        sel = rotulos == c
        if not sel.any():
            continue
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            y = (x[sel] - gm.means_[c]) @ gm.precisions_cholesky_[c]
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


def bloco(
    df: pd.DataFrame,
    fr: np.ndarray,
    chaves: Sequence[str],
    nomes: Mapping[str, str],
    contraste: bool = True,
    max_pontos: int = MAX_PONTOS,
) -> dict[str, Any]:
    """Ajusta k = K e descreve componentes, anômalos, cruzamentos e PCA."""
    z, x = coordenadas(fr)
    t0 = time.time()
    aj = ajustar_melhor(x, K)
    gm = aj.gm
    seg = time.time() - t0
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        bruto = gm.predict(x)
        ll = gm.score_samples(x)
        rot2 = aj.segundo.predict(x) if aj.segundo is not None else None
    if not np.isfinite(ll).all():
        raise ValueError("log-verossimilhança não finita")
    mapa = ordem_estavel(bruto, df["lula_pct"].to_numpy(dtype=float), K)
    rot = mapa[bruto]
    maha = mahalanobis_proprio(gm, x, bruto)
    inv = np.argsort(mapa)
    covs = gm.covariances_[inv]
    pesos = gm.weights_[inv]

    bic = [_linha_bic(K, gm, x, aj.log)]
    if contraste:
        for kc in K_TABELA:
            if kc == K:
                continue
            outro = ajustar_melhor(x, kc)
            bic.append(_linha_bic(kc, outro.gm, x, outro.log))
        bic.sort(key=lambda r: r["k"])

    df = df.assign(_cl=rot, _ll=ll, _maha=maha)
    comps = [_componente(df, fr, chaves, rot, c, covs[c], pesos[c]) for c in range(K)]
    zero = fr <= 0
    ordem_votos = menos_votadas(fr, df["aptos"].to_numpy(dtype=float), chaves)
    padroes = padroes_zeros(zero, rot, K, chaves, ordem_votos)
    for cc, pz in zip(comps, padroes, strict=True):
        cc["padrao_zeros"] = pz
        cc["rotulo"] = rotulo(cc, nomes)
    for linha, (_, g) in zip(aj.log, aj.todos, strict=True):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            rs = g.predict(x)
        linha["cramer_v_regiao"] = r2(cramer(pd.Series(rs), df["regiao"]), 3)
        linha["ari_com_escolhida"] = r2(adjusted_rand_score(bruto, rs), 3)
    anom = escolher_anomalo(
        [cc["loglik_media"] for cc in comps], [cc["dispersao_logdet"] for cc in comps]
    )
    extra = ("_ll", "_maha", "_cl")
    am = df[df["_cl"] == anom].sort_values("_ll").head(20)
    menos = df.sort_values("_ll").head(50)
    lls = [r["loglik_media"] for r in aj.log]
    maximo = max(lls)
    return {
        "features": list(chaves),
        "zeros_substituidos_pct": r2(100 * float((fr <= 0).mean()), 2),
        "degrau_log": degrau_log(df["aptos"].to_numpy(dtype=float)),
        "ajuste": {
            "secoes_ajuste": len(df),
            "secoes_atribuidas": len(df),
            "amostra_estratificada": False,
            "covariancia": "full",
            "n_init": N_INIT,
            "random_state": aj.semente,
            "sementes": aj.log,
            "inicializacoes": N_INIT * len(aj.log),
            "sementes_no_maximo": sum(v >= maximo - EMPATE_LOGLIK for v in lls),
            "max_iter": 500,
            "tol": 1e-4,
            "reg_covar": 1e-6,
            "convergiu": bool(gm.converged_),
            "iteracoes": int(gm.n_iter_),
            "loglik_media": r2(ll.mean(), 4),
            "segundos": r2(seg, 1),
        },
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
        "pca": _pca(df, z, fr, chaves, rot, ll, max_pontos),
        "_rot": rot,
        "_rot2": rot2,
        "_semente2": aj.semente_segundo,
        "_x": x,
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


def degrau_log(aptos: np.ndarray) -> dict[str, Any]:
    """Distância, em unidades de log, entre zero (0,0001) e um voto na seção."""
    d = np.log(1.0 / (aptos * ZERO))
    return {
        "aptos_mediana": r2(np.median(aptos), 0),
        "mediana": r2(np.log(1.0 / (np.median(aptos) * ZERO)), 2),
        "p10": r2(np.percentile(d, 10), 2),
        "p90": r2(np.percentile(d, 90), 2),
    }


def _componente(
    df: pd.DataFrame,
    fr: np.ndarray,
    chaves: Sequence[str],
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
    return {
        "id": c,
        "secoes": n,
        "pct_secoes": pct(n, len(df)),
        "aptos": int(g["aptos"].sum()),
        "aptos_medio": r2(g["aptos"].mean(), 1),
        "votantes_medio": r2(g["votantes"].mean(), 1),
        "centro_pct_eleitorado": {
            k: r2(100 * fr[sel, i].mean(), 3) for i, k in enumerate(chaves)
        },
        "zeros_pct": {
            k: r2(100 * float((fr[sel, i] <= 0).mean()), 1)
            for i, k in enumerate(chaves)
        },
        "centro_pct_validos": {
            "lula": pct(int(g[f"v{LULA}"].sum()), val),
            "flavio": pct(int(g[f"v{FLAVIO}"].sum()), val),
            "outros": pct(
                int((g["validos"] - g[f"v{LULA}"] - g[f"v{FLAVIO}"]).sum()), val
            ),
        },
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
    out = []
    for c in tab.index:
        for r in tab.columns:
            n = int(tab.loc[c, r])
            if n == 0:
                continue
            out.append(
                {
                    "cluster": int(c),
                    nome: str(r).upper() if nome == "uf" else r,
                    "secoes": n,
                    "pct_do_cluster": pct(n, int(tab.loc[c].sum())),
                    f"pct_da_{nome}": pct(n, int(tab[r].sum())),
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


def _pca(
    df: pd.DataFrame,
    z: np.ndarray,
    fr: np.ndarray,
    chaves: Sequence[str],
    rot: np.ndarray,
    ll: np.ndarray,
    max_pontos: int = MAX_PONTOS,
) -> dict[str, Any]:
    pca = PCA(n_components=2, random_state=SEMENTE)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        p = pca.fit_transform(z)
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
        i = int(np.argmax(np.abs(pca.components_[j])))
        s = separacao(p[:, j], fr[:, i] <= 0)
        sep.append(
            {
                "componente": j + 1,
                "feature": chaves[i],
                "carga": r2(pca.components_[j, i], 4),
                "zeros_pct": r2(100 * float((fr[:, i] <= 0).mean()), 1),
                "acerto_balanceado_pct": r2(s[0], 1) if s else None,
                "corte": r2(s[1], 3) if s else None,
            }
        )
    return {
        "base": "componentes principais da CLR (equivale à PCA nas coordenadas ILR)",
        "variancia_explicada": [r2(v, 4) for v in pca.explained_variance_ratio_],
        "cargas": [
            {
                "feature": k,
                "pc1": r2(pca.components_[0, i], 4),
                "pc2": r2(pca.components_[1, i], 4),
            }
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


def _variantes(
    df: pd.DataFrame, fr: np.ndarray, cands: Sequence[Any]
) -> dict[str, tuple[str, np.ndarray, list[str]]]:
    """Duas versões com menos zeros: nanicas somadas e composição densa."""
    total = {c.chave: float(df[f"v{c.numero}"].sum()) for c in cands}
    validos = sum(total.values())
    grandes = [
        i for i, c in enumerate(cands) if total[c.chave] >= LIMIAR_NANICO * validos
    ]
    pequenos = [i for i in range(len(cands)) if i not in grandes]
    nc = len(cands)
    branco, nulo, abst = fr[:, nc], fr[:, nc + 1], fr[:, nc + 2]
    ag = np.column_stack(
        [fr[:, grandes], fr[:, pequenos].sum(axis=1), branco, nulo, abst]
    )
    chaves_ag = [cands[i].chave for i in grandes]
    chaves_ag += ["demais", "brancos", "nulos", "abstencao"]
    i_lula = next(i for i, c in enumerate(cands) if c.numero == LULA)
    i_flavio = next(i for i, c in enumerate(cands) if c.numero == FLAVIO)
    outros = [i for i in range(nc) if i not in (i_lula, i_flavio)]
    densa = np.column_stack(
        [
            fr[:, i_lula],
            fr[:, i_flavio],
            fr[:, outros].sum(axis=1),
            branco + nulo,
            abst,
        ]
    )
    return {
        "nanicos_somados": (
            f"mesma mistura (k = {K}, mesmas sementes) com as {len(pequenos)} "
            "candidaturas de menos de 1% dos válidos somadas na parte `demais`; "
            f"{len(grandes)} candidaturas ficam separadas",
            ag,
            chaves_ag,
        ),
        "densa": (
            f"mesma mistura (k = {K}, mesmas sementes) sobre cinco partes quase sem "
            "zeros: Lula, Flávio, as outras dez candidaturas somadas, brancos e "
            "nulos somados, abstenção",
            densa,
            ["lula", "flavio", "terceiros", "brancos_nulos", "abstencao"],
        ),
    }


def clusters(base: Base) -> dict[str, Any]:
    df = base.secoes
    df = df[df["aptos"] > 0].reset_index(drop=True)
    cands = base.candidatos
    vcols = [f"v{c.numero}" for c in cands]
    chaves = [c.chave for c in cands] + ["brancos", "nulos", "abstencao"]
    nomes = {c.chave: c.nome for c in cands} | NOMES_PARTES
    fr = matriz_fracoes(df, vcols)
    principal = bloco(df, fr, chaves, nomes)
    rot, rot2 = principal.pop("_rot"), principal.pop("_rot2")
    semente2 = principal.pop("_semente2")
    principal.pop("_x")

    variantes: dict[str, Any] = {}
    sens: dict[str, Any] = {}
    for nome, (desc, frv, chv) in _variantes(df, fr, cands).items():
        b = bloco(df, frv, chv, nomes, contraste=False, max_pontos=4000)
        sens[f"ari_principal_vs_{nome}"] = r2(
            adjusted_rand_score(rot, b.pop("_rot")), 3
        )
        for chave in ("_rot2", "_semente2", "_x"):
            b.pop(chave)
        variantes[nome] = {"descricao": desc, **b}

    if rot2 is not None:
        sens["ari_principal_vs_outra_semente"] = r2(adjusted_rand_score(rot, rot2), 3)
        sens["outra_semente"] = semente2
        sens["outra_semente_criterio"] = (
            "a semente de segunda maior log-verossimilhança entre as "
            f"{len(SEMENTES)} ajustadas"
        )
    bic = principal["bic"]
    melhor = min(bic, key=lambda b: b["bic"])["k"] if bic else None
    saida = {
        "k": K,
        "escolha_k": {**ESCOLHA_K, "bic_prefere": melhor},
        "base": "votos de cada componente / aptos da seção (eleição federal)",
        "transformacao": "clr",
        "transformacao_detalhe": (
            "log-razão centrada (CLR) das 15 frações, com zero trocado por 0,0001 "
            "antes do log; a mistura é ajustada nas 14 coordenadas ortonormais do "
            "subespaço de soma zero (ILR), rotação que preserva Mahalanobis e "
            "densidade relativa"
        ),
        "zero": ZERO,
        **principal,
        "variantes": variantes,
        "sensibilidade": sens,
    }
    saida["leitura_projecao"] = leitura_projecao(saida, nomes)
    saida["estabilidade"] = estabilidade(saida)
    saida["interpretacao"] = interpretar(saida, nomes)
    return saida
