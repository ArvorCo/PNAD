"""Pergunta B: mistura gaussiana (k = 4) sobre a composição do eleitorado da seção.

Atributos por seção: votos de cada uma das 12 candidaturas a presidente, brancos,
nulos e abstenção, todos divididos pelos aptos da eleição federal. As 15 frações
somam 1, então o espaço é composicional: aplica-se a log-razão centrada (CLR),
com zeros trocados por 0,0001 antes do log, como pedido. A CLR de 15 partes vive
num subespaço de 14 dimensões (cada linha soma zero), o que tornaria singular a
covariância completa; por isso a mistura é ajustada nas 14 coordenadas
ortonormais desse subespaço (log-razão isométrica, ILR). A troca é uma rotação:
distâncias de Mahalanobis e a densidade relativa entre seções não mudam.

A especificação pedida é o modelo principal. Como quase metade das células é
zero (candidaturas nanicas sem voto na seção), a mesma mistura é refeita com as
candidaturas de menos de 1% dos válidos somadas numa parte só; as duas versões
saem no JSON com a mesma estrutura.

O numpy ligado ao Accelerate (macOS) emite avisos falsos de divisão por zero em
produtos de matriz; os avisos são silenciados e todo resultado é conferido como
finito.
"""

from __future__ import annotations

import time
import warnings
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.linalg import null_space
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

from .secoes_base import FLAVIO, LULA, ZERO, Base, amostras, clr, num, pct, r2

SEMENTE = 20261005
K = 4
K_CONTRASTE = (3, 5)
N_INIT = 10
MAX_PONTOS = 8000
TOP_FIGURA = 200
LIMIAR_NANICO = 0.01


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


# ---------------------------------------------------------------- bloco


def bloco(
    df: pd.DataFrame,
    fr: np.ndarray,
    chaves: Sequence[str],
    contraste: bool = True,
    max_pontos: int = MAX_PONTOS,
) -> dict[str, Any]:
    """Ajusta k = 4 e descreve componentes, anômalos, cruzamentos e PCA."""
    z, x = coordenadas(fr)
    t0 = time.time()
    gm = ajustar(x, K)
    seg = time.time() - t0
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        bruto = gm.predict(x)
        ll = gm.score_samples(x)
    if not np.isfinite(ll).all():
        raise ValueError("log-verossimilhança não finita")
    mapa = ordem_estavel(bruto, df["lula_pct"].to_numpy(dtype=float), K)
    rot = mapa[bruto]
    maha = mahalanobis_proprio(gm, x, bruto)
    inv = np.argsort(mapa)
    covs = gm.covariances_[inv]
    pesos = gm.weights_[inv]

    bic = [{"k": K, "bic": r2(gm.bic(x), 1), "loglik_media": r2(ll.mean(), 4)}]
    if contraste:
        for kc in K_CONTRASTE:
            g2 = ajustar(x, kc)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                bic.append(
                    {
                        "k": kc,
                        "bic": r2(g2.bic(x), 1),
                        "loglik_media": r2(g2.score(x), 4),
                    }
                )
        bic.sort(key=lambda r: r["k"])

    df = df.assign(_cl=rot, _ll=ll, _maha=maha)
    comps = [_componente(df, fr, chaves, rot, c, covs[c], pesos[c]) for c in range(K)]
    anom = escolher_anomalo(
        [cc["loglik_media"] for cc in comps], [cc["dispersao_logdet"] for cc in comps]
    )
    extra = ("_ll", "_maha", "_cl")
    am = df[df["_cl"] == anom].sort_values("_ll").head(20)
    menos = df.sort_values("_ll").head(50)
    return {
        "features": list(chaves),
        "zeros_substituidos_pct": r2(100 * float((fr <= 0).mean()), 2),
        "ajuste": {
            "secoes_ajuste": len(df),
            "secoes_atribuidas": len(df),
            "amostra_estratificada": False,
            "covariancia": "full",
            "n_init": N_INIT,
            "random_state": SEMENTE,
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
        "pca": _pca(df, z, chaves, rot, ll, max_pontos),
        "_rot": rot,
        "_x": x,
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
    out = {
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
    out["rotulo"] = _rotulo(out)
    return out


def _refs(df: pd.DataFrame, extra: Sequence[str]) -> list[dict[str, Any]]:
    out = amostras(df, len(df), extra)
    for r in out:
        r["loglik"] = r.pop("_ll", None)
        r["mahalanobis"] = r.pop("_maha", None)
        cl = r.pop("_cl", None)
        r["cluster"] = int(cl) if cl is not None else None
    return out


def _rotulo(c: dict[str, Any]) -> str:
    v = c["centro_pct_validos"]
    reg = c["regioes"][0] if c["regioes"] else {"regiao": "?", "pct_do_cluster": 0}
    lider = "Lula" if (v["lula"] or 0) >= (v["flavio"] or 0) else "Flávio"
    pl = v["lula"] if lider == "Lula" else v["flavio"]
    ab = c["centro_pct_eleitorado"].get("abstencao") or 0
    return (
        f"{lider} {num(pl or 0, 0)}% dos válidos, abstenção {num(ab, 0)}%, "
        f"{reg['regiao']} {num(reg['pct_do_cluster'] or 0, 0)}% das seções"
    )


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
        "centros": [
            {
                "cluster": int(c),
                "x": r2(p[rot == c, 0].mean(), 3),
                "y": r2(p[rot == c, 1].mean(), 3),
            }
            for c in np.unique(rot)
        ],
        "colunas": ["x", "y", "cluster", "top200", "uf"],
        "pontos": pontos,
        "n_pontos": len(pontos),
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
            f"mesma mistura (k = 4, mesma semente) com as {len(pequenos)} "
            "candidaturas de menos de 1% dos válidos somadas na parte `demais`; "
            f"{len(grandes)} candidaturas ficam separadas",
            ag,
            chaves_ag,
        ),
        "densa": (
            "mesma mistura (k = 4, mesma semente) sobre cinco partes quase sem "
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
    fr = matriz_fracoes(df, vcols)
    principal = bloco(df, fr, chaves)
    rot, x = principal.pop("_rot"), principal.pop("_x")

    variantes: dict[str, Any] = {}
    sens: dict[str, Any] = {}
    for nome, (desc, frv, chv) in _variantes(df, fr, cands).items():
        b = bloco(df, frv, chv, contraste=False, max_pontos=4000)
        sens[f"ari_principal_vs_{nome}"] = r2(
            adjusted_rand_score(rot, b.pop("_rot")), 3
        )
        b.pop("_x")
        variantes[nome] = {"descricao": desc, **b}

    gs = ajustar(x, K, semente=SEMENTE + 1)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        rs = gs.predict(x)
    sens["ari_principal_vs_outra_semente"] = r2(adjusted_rand_score(rot, rs), 3)
    sens["outra_semente"] = SEMENTE + 1
    saida = {
        "k": K,
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
    saida["interpretacao"] = interpretar(saida)
    return saida


def _amplitude_zeros(
    comps: Sequence[dict[str, Any]], features: Sequence[str]
) -> tuple[str, float]:
    amp = {}
    for f in features:
        vals = [cc["zeros_pct"].get(f) or 0.0 for cc in comps]
        amp[f] = max(vals) - min(vals)
    f_max = max(amp, key=lambda k: amp[k])
    return f_max, amp[f_max]


def interpretar(c: dict[str, Any]) -> list[str]:
    """Frases geradas dos números; a primeira diz se os grupos são geografia."""
    comps = c["componentes"]
    v = c["cramer_v_regiao"] or 0.0
    frases = []
    f_max, amp = _amplitude_zeros(comps, c["features"])
    if v < 0.3 and amp >= 50:
        frases.append(
            "Na especificação pedida, os quatro grupos não são geografia (V de "
            f"Cramér entre grupo e região {num(v, 2)}): separam as seções pelo "
            "padrão de zeros. "
            f"{num(c['zeros_substituidos_pct'], 1)}% das células são zero e viram "
            "0,0001; no log, uma candidatura sem voto fica a 3 ou 4 unidades de "
            "uma com um voto, e a mistura usa esse degrau para separar grupos "
            f"(a parte que mais distingue os grupos é `{f_max}`, com "
            f"{num(amp, 0)} pontos de diferença na proporção de zeros entre eles)."
        )
    elif v >= 0.3:
        frases.append(
            "Os quatro grupos seguem sobretudo a geografia e o lado do voto (V de "
            f"Cramér entre grupo e região {num(v, 2)})."
        )
    else:
        frases.append(
            "Os grupos não se reduzem à região (V de Cramér entre grupo e região "
            f"{num(v, 2)}); o que os separa precisa ser lido nos centros."
        )
    for nome, rot in (
        ("nanicos_somados", "nanicas somadas"),
        ("densa", "cinco partes"),
    ):
        var = c["variantes"][nome]
        vv = var["cramer_v_regiao"] or 0.0
        fm, am = _amplitude_zeros(var["componentes"], var["features"])
        motivo = (
            f"; o padrão de zeros ainda separa os grupos (`{fm}`, {num(am, 0)} pontos)"
            if am >= 50
            else ""
        )
        frases.append(
            f"Na versão com {rot}, o V de Cramér entre grupo e região é "
            f"{num(vv, 2)}{motivo}."
        )
    for cc in comps:
        frases.append(
            f"Grupo {cc['id']}: {cc['rotulo']}; {num(cc['secoes'], 0)} seções."
        )
    a = comps[c["mais_anomalo"]["id"]]
    frases.append(
        f"O grupo de menor densidade e maior dispersão é o {a['id']} "
        f"({a['rotulo']}); as 20 seções menos prováveis dele vêm com o que "
        "provavelmente as explica."
    )
    return frases
