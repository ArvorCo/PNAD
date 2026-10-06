"""Pergunta B: mistura gaussiana (k = 5) sobre o eleitorado de cada seção.

Modelo principal (06/10/2026, terceira tentativa): cinco variáveis por seção,
Lula, Flávio, brancos, nulos e abstenção, cada uma dividida pelos aptos da
eleição federal. Proporções cruas, sem log e sem troca de zero, como no pedido
original do autor ("voto de cada candidato dividido pelo total do eleitorado da
seção"); o voto nas outras dez candidaturas fica implícito, como o que falta
para 100%, e sai ao lado de cada centro. As cinco proporções são padronizadas
(menos a média entre seções, divididas pelo desvio-padrão entre seções) antes
da mistura, com covariância completa, 16 sementes, duas inicializações do
sklearn, tolerância 1e-6 e até 2.000 iterações.

As duas tentativas anteriores ficam como registro do que não deu certo, só com
agregados (`variantes`):
- `quinze_partes` (05/10/2026): log-razão centrada das 12 candidaturas, brancos,
  nulos e abstenção. Com 42,7% das células em zero trocado por 0,0001, os
  grupos saíram do padrão de zeros das candidaturas nanicas;
- `cinco_partes_clr` (06/10/2026): log-razão das mesmas cinco partes do modelo
  principal. Na escala do log, brancos e nulos, poucos votos por seção,
  dominaram: zero e empate entre eles viraram grupos.

k = 5 é escolha do autor; a tabela do BIC (k = 3, 4 e 5) fica ao lado, e
`ajuste.diagnostico_convergencia` (`secoes_clusters_diag`) mostra se o EM foi
até a convergência e quantas partidas chegam ao mesmo máximo.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from .secoes_base import FLAVIO, LULA, Base, r2
from .secoes_clusters_diag import frase
from .secoes_clusters_leitura import (
    NOMES_PARTES,
    diagnostico_zeros,
    estabilidade,
    leitura_projecao,
)
from .secoes_clusters_motor import (
    INITS,
    K_TABELA,
    N_SEMENTES,
    SEMENTE,
    SEMENTES,
    Composicao,
    K,
    ajustar,
    ajustar_melhor,
    bloco,
    coordenadas,
    cramer,
    degrau_log,
    escolher_anomalo,
    espaco,
    ilr_base,
    ordem_estavel,
    padronizar,
    projecao,
    separacao,
)
from .secoes_clusters_perfil import (
    contagens,
    diagnostico_log,
    empates_por_par,
    padroes_empate,
    referencia,
    resumo_grupos,
    textos,
)

SEMENTES_15 = SEMENTES[:8]  # as oito da versão de 15 partes publicada em 05/10
ESCOLHA_K = {
    "k": K,
    "anterior": 3,
    "data": "06/10/2026",
    "motivo": (
        "escolha do autor, mantida nas três tentativas (15 partes em log-razão, cinco "
        "partes em log-razão e cinco proporções cruas)"
    ),
}
PARTES = ("lula", "flavio", "brancos", "nulos", "abstencao")
TOL_PRINCIPAL = 1e-6  # modelo principal (proporções cruas)
MAX_ITER_PRINCIPAL = 2000
AMOSTRA_BUSCA = 150_000  # seções da busca de sementes, estratificada por UF


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


def composicao_cinco(df: pd.DataFrame, espaco_: str = "padronizada") -> Composicao:
    """Lula, Flávio, brancos, nulos e abstenção; terceiros implícitos (o que falta)."""
    el, fora = matriz_cinco(df)
    apt = df["aptos"].to_numpy(dtype=float)
    return Composicao(fechar(el), list(PARTES), el, fora, apt * el.sum(axis=1), espaco_)


def composicao_quinze(df: pd.DataFrame, cands: Sequence[Any]) -> Composicao:
    fr = matriz_fracoes(df, [f"v{c.numero}" for c in cands])
    chaves = [c.chave for c in cands] + ["brancos", "nulos", "abstencao"]
    return Composicao(fr, chaves, fr, None, df["aptos"].to_numpy(dtype=float))


def _medias_por(codigos: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Média de `y` (n × m) dentro de cada código, devolvida linha a linha."""
    n_cod = int(codigos.max()) + 1
    cont = np.bincount(codigos, minlength=n_cod).astype(float)
    soma = np.stack(
        [
            np.bincount(codigos, weights=y[:, j], minlength=n_cod)
            for j in range(y.shape[1])
        ],
        axis=1,
    )
    return (soma / cont[:, None])[codigos]


def explicacao(
    df: pd.DataFrame, comp: Composicao, rot: np.ndarray
) -> dict[str, dict[str, float | None]]:
    """R² (%) de cada parte entre seções: região, zona, grupo e zona mais grupo.

    `zona_mais_grupo` é a regressão da parte nos indicadores de grupo dentro da
    zona (efeito fixo de zona): o que o grupo acrescenta a quem já sabe a zona,
    que é o que o mapa por zona mostra.
    """
    zona = pd.factorize(
        df["uf"].astype(str)
        + "|"
        + df["mun"].astype(str)
        + "|"
        + df["zona"].astype(str)
    )[0]
    regiao = pd.factorize(df["regiao"].astype(str))[0]
    grupo = np.asarray(rot, dtype=np.int64)
    cols = {k: comp.eleitorado[:, i] for i, k in enumerate(comp.chaves)}
    if comp.fora is not None:
        cols["terceiros"] = comp.fora
    y = np.column_stack(list(cols.values()))
    dummies = (grupo[:, None] == np.arange(1, int(grupo.max()) + 1)[None, :]).astype(
        float
    )
    y_w = y - _medias_por(zona, y)
    d_w = dummies - _medias_por(zona, dummies)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        beta, *_ = np.linalg.lstsq(d_w, y_w, rcond=None)
        sse_zg = ((y_w - d_w @ beta) ** 2).sum(axis=0)
    if not np.isfinite(sse_zg).all():
        raise ValueError("regressão dentro da zona não finita")
    sst = ((y - y.mean(axis=0)) ** 2).sum(axis=0)

    def r2_por(codigos: np.ndarray) -> np.ndarray:
        return 1 - ((y - _medias_por(codigos, y)) ** 2).sum(axis=0) / sst

    tab = {
        "regiao": r2_por(regiao),
        "zona": r2_por(zona),
        "grupo": r2_por(grupo),
        "zona_mais_grupo": 1 - sse_zg / sst,
    }
    return {
        k: {nome: r2(100 * float(v[j]), 2) for nome, v in tab.items()}
        for j, k in enumerate(cols)
    }


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


def registro_cinco_clr(
    b: Mapping[str, Any], nomes: Mapping[str, str]
) -> dict[str, Any]:
    """Os agregados da tentativa de cinco partes em log-razão, de um bloco ajustado
    (o calculado agora ou o principal gravado no JSON de 06/10/2026)."""
    dg = b["ajuste"]["diagnostico_convergencia"]
    top = max(b["pca"]["cargas"], key=lambda x: abs(x["pc1"]))
    r = {
        "descricao": (
            f"a mesma mistura (k = {K}) sobre a log-razão centrada de Lula, Flávio, "
            "brancos, nulos e abstenção, com zero trocado por 0,0001"
        ),
        "abandonada_em": "06/10/2026",
        "motivo": (
            "na escala do log, brancos e nulos, poucos votos por seção, dominaram a "
            "mistura: zero e empate viraram grupos"
        ),
        "k": K,
        "features": list(b["features"]),
        "zeros_substituidos_pct": b["zeros_substituidos_pct"],
        "zeros_por_parte": b["zeros_por_parte"],
        "secoes_com_zero": b["secoes_com_zero"],
        "degrau_log": b["degrau_log"],
        "mediana_votos_por_secao": b["mediana_votos_por_secao"],
        "empates_por_par": [e for e in b["empates_por_par"] if e["pct_secoes"] >= 1],
        "bic": b["bic"],
        "cramer_v_regiao": b["cramer_v_regiao"],
        "cramer_v_uf": b["cramer_v_uf"],
        "convergencia": {
            k: dg[k]
            for k in (
                "total",
                "no_maximo",
                "ari_medio_no_maximo",
                "ari_medio_demais",
                "particao_estavel",
                "frase",
            )
        },
        "grupos": resumo_grupos(b["componentes"]),
        "eixo_1": {
            "variancia_explicada": b["pca"]["variancia_explicada"][0],
            "feature": top["feature"],
            "carga": top["pc1"],
        },
    }
    r["diagnostico"] = diagnostico_log(r)
    return r


def cinco_partes_clr(
    df: pd.DataFrame, comp: Composicao, nomes: Mapping[str, str], cont: np.ndarray
) -> dict[str, Any]:
    """Refaz a segunda tentativa como foi publicada (16 sementes, duas
    inicializações, dez partidas internas, tol 1e-4 e reajuste com tol 1e-6)."""
    b = bloco(df, comp._replace(espaco="clr"), nomes, max_pontos=0)
    for cc, pe in zip(
        b["componentes"], padroes_empate(cont, b["_rot"], K, comp.chaves), strict=True
    ):
        cc["padrao_empates"] = pe
    b |= {
        "k": K,
        "referencia_nacional": referencia(comp),
        "mediana_votos_por_secao": {
            k: r2(float(np.median(cont[:, i])), 1) for i, k in enumerate(comp.chaves)
        },
        "empates_por_par": empates_por_par(cont, comp.chaves),
        "variantes": {},
    }
    textos(b, nomes)
    return registro_cinco_clr(b, nomes)


def tentativas(
    df: pd.DataFrame,
    cands: Sequence[Any],
    comp: Composicao,
    nomes: Mapping[str, str],
    cont: np.ndarray,
    anterior: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Os registros das duas tentativas em log-razão.

    Com `anterior` (o bloco `clusters` já gravado), reaproveita os registros que
    ele tem e, se o principal gravado ainda for o de cinco partes em log-razão,
    converte-o em registro: o ajuste é determinístico, e refazê-lo custaria uns
    quinze minutos para devolver os mesmos números. Sem `anterior`, refaz tudo.
    """
    var = dict((anterior or {}).get("variantes") or {})
    if "quinze_partes" in var and var["quinze_partes"].get("diagnostico"):
        q = var["quinze_partes"]
    else:
        q = quinze_partes(df, composicao_quinze(df, cands), nomes)
        q.pop("_rot")
    if "cinco_partes_clr" in var:
        c5 = var["cinco_partes_clr"]
    elif (
        anterior
        and anterior.get("transformacao") == "clr"
        and list(anterior.get("features") or []) == list(PARTES)
    ):
        c5 = registro_cinco_clr(anterior, nomes)
    else:
        c5 = cinco_partes_clr(df, comp, nomes, cont)
    return {"quinze_partes": q, "cinco_partes_clr": c5}


def clusters(base: Base, anterior: Mapping[str, Any] | None = None) -> dict[str, Any]:
    df = base.secoes
    df = df[df["aptos"] > 0].reset_index(drop=True)
    cands = base.candidatos
    nomes = {c.chave: c.nome for c in cands} | NOMES_PARTES
    comp = composicao_cinco(df)
    cont = contagens(comp)
    principal = bloco(
        df,
        comp,
        nomes,
        tol=TOL_PRINCIPAL,
        max_iter=MAX_ITER_PRINCIPAL,
        modo_diag="continua",
        amostra=AMOSTRA_BUSCA,
    )
    rot = principal.pop("_rot")
    for cc, pe in zip(
        principal["componentes"],
        padroes_empate(cont, rot, K, comp.chaves),
        strict=True,
    ):
        cc["padrao_empates"] = pe
    bic = principal["bic"]
    melhor = min(bic, key=lambda b: b["bic"])["k"] if bic else None
    saida = {
        "k": K,
        "escolha_k": {**ESCOLHA_K, "bic_prefere": melhor},
        "base": (
            "votos de Lula, de Flávio, brancos, nulos e abstenções da seção, cada um "
            "dividido pelos aptos da eleição federal (proporções cruas, sem log; o voto "
            "em terceiros fica implícito, como o que falta para 100%)"
        ),
        "transformacao": "padronizada",
        "transformacao_detalhe": (
            "cada uma das cinco proporções do eleitorado menos a média entre seções, "
            "dividida pelo desvio-padrão entre seções (`padronizacao`); sem log e sem "
            "troca de zero; a mistura é ajustada nessas cinco coordenadas"
        ),
        "zero": None,
        "referencia_nacional": referencia(comp),
        "mediana_votos_por_secao": {
            k: r2(float(np.median(cont[:, i])), 1) for i, k in enumerate(comp.chaves)
        },
        "empates_por_par": empates_por_par(cont, comp.chaves),
        **principal,
        "explicacao_variancia": explicacao(df, comp, rot),
        "variantes": tentativas(df, cands, comp, nomes, cont, anterior),
    }
    textos(saida, nomes)
    return saida


def refazer_textos(cl: dict[str, Any], candidatos: Sequence[Mapping[str, Any]]) -> None:
    """Refaz rótulos e frases do bloco `clusters` a partir dos números gravados.

    Não reajusta nada: serve para revisão editorial do texto gerado sem rodar a
    mistura de novo. A frase de diagnóstico da versão de 15 partes fica como
    está, porque depende de campos que o registro não guarda; a da versão de cinco
    partes em log-razão é refeita dos agregados dela.
    """
    nomes = {c["chave"]: c["nome"] for c in candidatos} | NOMES_PARTES
    dg = (cl.get("ajuste") or {}).get("diagnostico_convergencia")
    if dg:
        dg["frase"] = frase(dg)
    c5 = (cl.get("variantes") or {}).get("cinco_partes_clr")
    if c5:
        c5["diagnostico"] = diagnostico_log(c5)
    textos(cl, nomes)


__all__ = [
    "INITS",
    "K_TABELA",
    "N_SEMENTES",
    "SEMENTE",
    "SEMENTES",
    "Composicao",
    "K",
    "ajustar",
    "ajustar_melhor",
    "coordenadas",
    "cramer",
    "degrau_log",
    "escolher_anomalo",
    "espaco",
    "ilr_base",
    "ordem_estavel",
    "padronizar",
    "projecao",
    "separacao",
]
