"""Matriz de hipótese 1º → 2º turno por ajuste proporcional iterativo (IPF/RAS).

Por UF (e exterior), a prior (linhas publicadas pelos institutos, regressão para
quem faltou no 1º turno, hipóteses declaradas para o resto) é ajustada por
mínima entropia cruzada até bater exatamente as margens das duas urnas: as
origens do 1º turno, reescaladas para o eleitorado apurado do 2º, e os destinos
do 2º turno. A matriz nacional é a soma das UFs, então bate também as margens
nacionais. O ajuste preserva os zeros da prior; não há zero estrutural (piso de
0,2% da linha).

Rotatividade: a urna só mostra a variação líquida do comparecimento. A prior usa o
menor fluxo bruto compatível com a amostra de seções (piso por seção) e com a
variação líquida real de cada UF; a sensibilidade dobra a saída.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from . import transferencia_priors as P

ORIG = P.ORIGENS
DEST = P.DESTINOS
IA = ORIG.index("abstencao")
JA = DEST.index("abstencao")
CELULAS_CRUZA = tuple((ORIG.index(a), DEST.index(b)) for a, b in P.CRUZA)


def ras(
    prior: np.ndarray,
    linhas: np.ndarray,
    colunas: np.ndarray,
    tol: float = 1e-10,
    max_iter: int = 20000,
) -> tuple[np.ndarray, int, float]:
    """Escala linhas e colunas alternadamente até as duas margens baterem.

    Devolve (matriz, iterações, maior desvio relativo de linha). Exige totais iguais.
    """
    if abs(linhas.sum() - colunas.sum()) > 1e-6 * colunas.sum():
        raise ValueError("margens com totais diferentes")
    M = prior.astype(float).copy()
    desvio = float("inf")
    iteracoes = 0
    while iteracoes < max_iter and desvio >= tol:
        iteracoes += 1
        s = M.sum(1)
        M *= np.divide(linhas, s, out=np.zeros_like(s), where=s > 0)[:, None]
        c = M.sum(0)
        M *= np.divide(colunas, c, out=np.zeros_like(c), where=c > 0)[None, :]
        r = M.sum(1)
        desvio = float(np.max(np.abs(r - linhas) / np.maximum(linhas, 1.0)))
    return M, iteracoes, desvio


def ras_fixas(
    prior: np.ndarray,
    linhas: np.ndarray,
    colunas: np.ndarray,
    fixa: np.ndarray,
    livre: np.ndarray,
) -> tuple[np.ndarray, int, float]:
    """RAS com células fixas: as fixas entram como dadas e as livres batem o que sobra.

    Célula fixa vira zero estrutural no ajuste e é somada de volta no fim; linha sem
    nenhuma célula livre precisa fechar sozinha. Falha se o fixo exceder uma margem.
    """
    lin = linhas - fixa.sum(1)
    col = colunas - fixa.sum(0)
    ativas = livre.any(1)
    tol = 1e-6 * float(colunas.sum())
    if np.any(col <= 0) or np.any(lin[ativas] <= 0):
        raise ValueError("células fixas excedem uma margem")
    if np.any(np.abs(lin[~ativas]) > tol):
        raise ValueError("linha toda fixa não fecha a própria margem")
    pr = np.where(livre, prior, 0.0)[ativas]
    Mr, it, desvio = ras(pr, lin[ativas], col)
    M = fixa.copy()
    M[ativas] += Mr
    return M, it, desvio


def churn_uf(
    margens: Mapping[str, Mapping[str, Any]],
    piso: Mapping[str, Any],
    multiplicador: float = 1.0,
) -> dict[str, dict[str, float]]:
    """Entrada e saída por UF: o mínimo compatível com o piso das seções e o líquido real.

    saída = max(piso de saída, piso de entrada − líquido) × multiplicador;
    entrada = saída + líquido. Taxas: entrada sobre ausentes e saída sobre votantes
    do 1º turno.
    """
    nac = piso["nacional"]
    out = {}
    for uf, m in margens.items():
        o = m["origens"]
        a1 = o["abstencao"]
        c1 = sum(v for k, v in o.items() if k != "abstencao")
        c2 = sum(v for k, v in m["destinos"].items() if k != "abstencao")
        liquido = c2 - c1
        p = piso["ufs"].get(uf, nac)
        saida = max(
            p["saida_min_sobre_votantes"] * c1,
            p["entrada_min_sobre_ausentes"] * a1 - liquido,
            0.0,
        )
        saida *= multiplicador
        entrada = saida + liquido
        if entrada <= 0:
            entrada = p["entrada_min_sobre_ausentes"] * a1
            saida = entrada - liquido
        out[uf] = {
            "r": entrada / a1,
            "q": saida / c1,
            "entrada": entrada,
            "saida": saida,
            "liquido": liquido,
        }
    return out


def alpha_bruto(
    b: Mapping[str, float],
    churn: Mapping[str, Mapping[str, float]],
    margens: Mapping[str, Mapping[str, Any]],
) -> dict[str, float]:
    """Divisão de quem voltou, coerente com a composição líquida medida (b).

    A regressão mede a composição da variação líquida: b·líquido = α·entrada − o·saída,
    com o = como teria votado quem faltou no 2º turno (aproximado pela composição do
    comparecimento do 2º turno). Logo α = (b·líquido + o·saída)/entrada.
    """
    ent = sum(c["entrada"] for c in churn.values())
    sai = sum(c["saida"] for c in churn.values())
    liq = ent - sai
    d = {k: sum(m["destinos"][k] for m in margens.values()) for k in DEST}
    comp = d["lula"] + d["flavio"] + d["brancos"] + d["nulos"]
    o = {
        "L": d["lula"] / comp,
        "F": d["flavio"] / comp,
        "BN": (d["brancos"] + d["nulos"]) / comp,
    }
    a = {k: max((b[k] * liq + o[k] * sai) / ent, P.PISO) for k in ("L", "F", "BN")}
    s = sum(a.values())
    return {k: v / s for k, v in a.items()}


def matriz_uf(
    m: Mapping[str, Any],
    churn: Mapping[str, float],
    alpha: Mapping[str, float],
    *,
    fidelidade: float | None,
    terceira: Mapping[str, list],
    bn_hipotese: bool,
    uniforme: bool = False,
    abstencao_fixa: bool = True,
    cruzamento: tuple[float, float] | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """IPF de uma UF.

    `abstencao_fixa`: a linha de quem faltou no 1º turno vem da regressão e da
    rotatividade e fica fixa (é a medição da casa sobre as urnas); só as outras
    linhas são ajustadas, contra o que sobra das margens do 2º turno. Falso deixa
    o IPF mexer nela também (diagnóstico). `uniforme`: prior sem informação.
    `cruzamento`: (Lula → Flávio, Flávio → Lula) como fração da base do 1º turno
    de quem cruza; as duas células ficam fixas (zero estrutural quando 0) e o
    ajuste distribui o resto. None deixa o IPF escolher a partir da prior.
    """
    o = np.array([m["origens"][k] for k in ORIG], dtype=float)
    d = np.array([m["destinos"][k] for k in DEST], dtype=float)
    escala = d.sum() / o.sum()
    o_esc = o * escala
    fb = m["destinos"]["brancos"] / max(
        m["destinos"]["brancos"] + m["destinos"]["nulos"], 1
    )
    if uniforme:
        prior = np.outer(o_esc, d / d.sum())
    else:
        linhas = []
        for k in ORIG:
            lin = P.prior_linha(
                k,
                q=churn["q"],
                r=churn["r"],
                alpha=dict(alpha),
                fidelidade=fidelidade,
                terceira=dict(terceira),
                bn_hipotese=bn_hipotese,
                fracao_brancos=fb,
            )
            linhas.append([lin[j] for j in DEST])
        prior = o_esc[:, None] * np.array(linhas)
    if uniforme:
        M, it, desvio = ras(prior, o_esc, d)
        return M, {"iteracoes": it, "desvio": desvio, "escala_origens": escala}
    fixa = np.zeros_like(prior)
    livre = np.ones(prior.shape, dtype=bool)
    if abstencao_fixa:
        fixa[IA] = prior[IA]
        livre[IA] = False
    if cruzamento is not None:
        for (i, j), k in zip(CELULAS_CRUZA, cruzamento, strict=True):
            fixa[i, j] = k * o_esc[i]
            livre[i, j] = False
    M, it, desvio = ras_fixas(prior, o_esc, d, fixa, livre)
    return M, {"iteracoes": it, "desvio": desvio, "escala_origens": escala}


def cenario(
    margens: Mapping[str, Mapping[str, Any]],
    piso: Mapping[str, Any],
    b: Mapping[str, float],
    *,
    nome: str,
    descricao: str,
    multiplicador: float = 1.0,
    fidelidade: float | None = None,
    terceira: Mapping[str, list] | None = None,
    bn_hipotese: bool = True,
    uniforme: bool = False,
    abstencao_fixa: bool = True,
    cruzamento: tuple[float, float] | None = None,
) -> dict[str, Any]:
    churn = churn_uf(margens, piso, multiplicador)
    alpha = alpha_bruto(b, churn, margens)
    terc = terceira or P.CENTRAL
    total = np.zeros((len(ORIG), len(DEST)))
    por_uf = {}
    diag = {"iteracoes_max": 0, "desvio_max": 0.0, "escala_min": 1.0, "escala_max": 1.0}
    for uf, m in margens.items():
        M, info = matriz_uf(
            m,
            churn[uf],
            alpha,
            fidelidade=fidelidade,
            terceira=terc,
            bn_hipotese=bn_hipotese,
            uniforme=uniforme,
            abstencao_fixa=abstencao_fixa,
            cruzamento=cruzamento,
        )
        total += M
        por_uf[uf] = M
        diag["iteracoes_max"] = max(diag["iteracoes_max"], info["iteracoes"])
        diag["desvio_max"] = max(diag["desvio_max"], info["desvio"])
        diag["escala_min"] = min(diag["escala_min"], info["escala_origens"])
        diag["escala_max"] = max(diag["escala_max"], info["escala_origens"])
    return {
        "nome": nome,
        "descricao": descricao,
        "matriz": total,
        "por_uf": por_uf,
        "alpha": alpha,
        "churn_nacional": {
            "entrada": sum(c["entrada"] for c in churn.values()),
            "saida": sum(c["saida"] for c in churn.values()),
            "liquido": sum(c["liquido"] for c in churn.values()),
        },
        "diagnostico": diag,
    }


def metricas(M: np.ndarray, margens_nac: Mapping[str, Any]) -> dict[str, Any]:
    """Números que a página usa, todos lidos da matriz nacional."""
    d = margens_nac["destinos"]
    ix = {k: i for i, k in enumerate(ORIG)}
    jx = {k: j for j, k in enumerate(DEST)}
    # Origens já reescaladas UF a UF para o eleitorado apurado do 2º turno.
    o = {k: float(M[i].sum()) for i, k in enumerate(ORIG)}
    escala = 1.0

    def cel(a: str, b: str) -> float:
        return float(M[ix[a], jx[b]])

    voltaram = sum(cel("abstencao", k) for k in ("lula", "flavio", "brancos", "nulos"))
    faltaram = sum(cel(k, "abstencao") for k in ORIG if k != "abstencao")
    terc_estoque = sum(o[k] for k in P.TERCEIRA) * escala
    terc_f = sum(cel(k, "flavio") for k in P.TERCEIRA)
    terc_l = sum(cel(k, "lula") for k in P.TERCEIRA)
    terc_bn = sum(cel(k, "brancos") + cel(k, "nulos") for k in P.TERCEIRA)
    terc_a = sum(cel(k, "abstencao") for k in P.TERCEIRA)
    por_cand = {}
    for k in P.TERCEIRA:
        est = o[k] * escala
        por_cand[k] = {
            "estoque": est,
            "flavio_pct": 100 * cel(k, "flavio") / est,
            "lula_pct": 100 * cel(k, "lula") / est,
            "bn_pct": 100 * (cel(k, "brancos") + cel(k, "nulos")) / est,
            "abstencao_pct": 100 * cel(k, "abstencao") / est,
            "flavio_entre_finalistas": 100
            * cel(k, "flavio")
            / max(cel(k, "flavio") + cel(k, "lula"), 1e-9),
        }
    fid_l = cel("lula", "lula") / (o["lula"] * escala)
    fid_f = cel("flavio", "flavio") / (o["flavio"] * escala)
    fora_l = d["lula"] - cel("lula", "lula")
    fora_f = d["flavio"] - cel("flavio", "flavio")
    h2h1 = 100 * o["flavio"] / (o["flavio"] + o["lula"])
    h2h2 = 100 * d["flavio"] / (d["flavio"] + d["lula"])
    sem_volta = (
        100
        * (d["flavio"] - cel("abstencao", "flavio"))
        / (
            d["flavio"]
            - cel("abstencao", "flavio")
            + d["lula"]
            - cel("abstencao", "lula")
        )
    )
    decomposicao = {}
    for k in ORIG:
        dm = cel(k, "flavio") - cel(k, "lula")
        if k == "flavio":
            dm -= o["flavio"] * escala
        if k == "lula":
            dm += o["lula"] * escala
        decomposicao[k] = dm
    return {
        "voltaram": voltaram,
        "voltaram_lula": cel("abstencao", "lula"),
        "voltaram_flavio": cel("abstencao", "flavio"),
        "voltaram_bn": cel("abstencao", "brancos") + cel("abstencao", "nulos"),
        "voltaram_lula_pct": 100 * cel("abstencao", "lula") / voltaram,
        "voltaram_flavio_pct": 100 * cel("abstencao", "flavio") / voltaram,
        "voltaram_bn_pct": 100
        * (cel("abstencao", "brancos") + cel("abstencao", "nulos"))
        / voltaram,
        "voltaram_lula_entre_validos": 100
        * cel("abstencao", "lula")
        / (cel("abstencao", "lula") + cel("abstencao", "flavio")),
        "faltaram_no_2t": faltaram,
        "ausentes_nos_dois": cel("abstencao", "abstencao"),
        "terceira": {
            "estoque": terc_estoque,
            "flavio": terc_f,
            "lula": terc_l,
            "bn": terc_bn,
            "abstencao": terc_a,
            "flavio_pct": 100 * terc_f / terc_estoque,
            "lula_pct": 100 * terc_l / terc_estoque,
            "bn_pct": 100 * terc_bn / terc_estoque,
            "abstencao_pct": 100 * terc_a / terc_estoque,
            "flavio_entre_finalistas": 100 * terc_f / (terc_f + terc_l),
            "por_candidatura": por_cand,
        },
        "fidelidade_lula": 100 * fid_l,
        "fidelidade_flavio": 100 * fid_f,
        "lula_para_flavio": cel("lula", "flavio"),
        "flavio_para_lula": cel("flavio", "lula"),
        "ganho_fora_base_lula": fora_l,
        "ganho_fora_base_flavio": fora_f,
        "razao_consolidacao_flavio_lula": fora_f / fora_l,
        "bn1_continua_bn_pct": 100
        * sum(cel(k, b) for k in ("brancos", "nulos") for b in ("brancos", "nulos"))
        / ((o["brancos"] + o["nulos"]) * escala),
        "h2h_flavio_1t": h2h1,
        "h2h_flavio_2t": h2h2,
        "swing_h2h_pp": h2h2 - h2h1,
        "h2h_sem_os_que_voltaram": sem_volta,
        "explica_pp": sem_volta - h2h2,
        "decomposicao_margem_flavio_menos_lula": decomposicao,
        "margem_1t": o["flavio"] * escala - o["lula"] * escala,
        "margem_2t": d["flavio"] - d["lula"],
        "lula_para_flavio_pct": 100 * cel("lula", "flavio") / o["lula"],
        "flavio_para_lula_pct": 100 * cel("flavio", "lula") / o["flavio"],
        "cruzamento_liquido_para_lula": cel("flavio", "lula") - cel("lula", "flavio"),
        "lula_de_terceira_bn_e_cruzamento": terc_l
        + sum(cel(k, "lula") for k in ("brancos", "nulos"))
        + cel("flavio", "lula")
        - cel("lula", "flavio"),
        "flavio_de_terceira_bn_e_cruzamento": terc_f
        + sum(cel(k, "flavio") for k in ("brancos", "nulos"))
        - cel("flavio", "lula")
        + cel("lula", "flavio"),
    }


def confere_margens(
    cen: Mapping[str, Any], margens: Mapping[str, Mapping[str, Any]]
) -> dict[str, float]:
    """Maior desvio absoluto (votos) das somas de cada matriz de UF contra as margens."""
    lin_max = col_max = 0.0
    for uf, M in cen["por_uf"].items():
        m = margens[uf]
        o = np.array([m["origens"][k] for k in ORIG], dtype=float)
        dd = np.array([m["destinos"][k] for k in DEST], dtype=float)
        o *= dd.sum() / o.sum()
        lin_max = max(lin_max, float(np.max(np.abs(M.sum(1) - o))))
        col_max = max(col_max, float(np.max(np.abs(M.sum(0) - dd))))
    return {"linhas_max_desvio_votos": lin_max, "colunas_max_desvio_votos": col_max}


def como_dict(M: np.ndarray, casas: int = 0) -> dict[str, dict[str, float]]:
    return {
        a: {b: round(float(M[i, j]), casas) for j, b in enumerate(DEST)}
        for i, a in enumerate(ORIG)
    }
