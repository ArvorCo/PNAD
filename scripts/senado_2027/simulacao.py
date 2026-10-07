"""Monte Carlo dos votos de PEC e de impeachment (seção 3 do CONTRATO).

Cada senador i tem utilidade latente y_i = mu_i + a·Z_nac + b·Z_bloco(i) + e_i,
com e_i logística padrão, e vota sim quando y_i > 0. Dado o choque, o voto é
Bernoulli(expit(mu_i + a·Z_nac + b·Z_bloco)): o choque entra no logit. mu_i é
calibrado para que a probabilidade marginal de sim seja exatamente C_i, então
os votos esperados continuam sendo a soma dos C. `a` e `b` saem das correlações
latentes do contrato: 0,15 entre dois senadores quaisquer (choque nacional) e
0,35 entre dois do mesmo bloco (nacional mais bloco). Cadeira vazia vota não.

Os mesmos sorteios servem a todo cenário, variante e alvo (números aleatórios
comuns), e o pivô reutiliza os sorteios dos demais senadores: a diferença entre
forçar sim e forçar não é exatamente a chance de o voto dele decidir.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from . import base as B
from .scores import REGUA, r1

ALVOS = {"pec": "C_pec", "imp": "C_imp"}
NOS_QUADRATURA = 80
ITERACOES_BISSECAO = 90


@dataclass(frozen=True)
class Sorteios:
    nacional: np.ndarray
    bloco: np.ndarray
    individual: np.ndarray

    @property
    def n(self) -> int:
        return int(self.nacional.shape[0])


def escalas(corr_intrabloco: float, corr_nacional: float) -> tuple[float, float]:
    """Desvios (a, b) dos choques nacional e de bloco no logit.

    Com erro logístico de variância pi²/3, a correlação latente entre dois
    senadores de blocos diferentes é a²/V e entre dois do mesmo bloco é
    (a² + b²)/V, com V = a² + b² + pi²/3.
    """
    if not 0 <= corr_nacional <= corr_intrabloco < 1:
        raise ValueError("exige 0 <= correlação nacional <= intrabloco < 1")
    variancia = (math.pi**2 / 3) / (1 - corr_intrabloco)
    return (
        math.sqrt(corr_nacional * variancia),
        math.sqrt((corr_intrabloco - corr_nacional) * variancia),
    )


def expit(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


def calibrar_locacao(p: np.ndarray, desvio: float) -> np.ndarray:
    """mu tal que E[expit(mu + desvio·Z)] = p, com Z normal padrão.

    Quadratura de Gauss-Hermite e bisseção vetorizada; a função é crescente
    em mu, então a bisseção converge para a raiz única. A soma ponderada é
    explícita, sem `@`: o BLAS do macOS acusa falso estouro com os pesos
    minúsculos das pontas da quadratura.
    """
    p = np.asarray(p, dtype=float)
    if np.any((p <= 0) | (p >= 1)):
        raise ValueError("probabilidade precisa estar em (0, 1)")
    if desvio == 0:
        return np.log(p / (1 - p))
    nos, pesos = np.polynomial.hermite_e.hermegauss(NOS_QUADRATURA)
    pesos = pesos / pesos.sum()
    baixo = np.full(p.shape, -40.0)
    alto = np.full(p.shape, 40.0)
    for _ in range(ITERACOES_BISSECAO):
        meio = (baixo + alto) / 2
        media = (expit(meio[:, None] + desvio * nos[None, :]) * pesos).sum(axis=1)
        abaixo = media < p
        baixo = np.where(abaixo, meio, baixo)
        alto = np.where(abaixo, alto, meio)
    return (baixo + alto) / 2


def sortear(n: int, cadeiras: int, semente: int) -> Sorteios:
    if n <= 0:
        raise ValueError("número de sorteios precisa ser positivo")
    rng = np.random.default_rng(semente)
    return Sorteios(
        nacional=rng.standard_normal(n),
        bloco=rng.standard_normal((n, len(B.BLOCOS))),
        individual=rng.random((n, cadeiras)),
    )


def votos(
    c_pct: Sequence[float | None],
    blocos: Sequence[str | None],
    sorteios: Sorteios,
    a: float,
    b: float,
) -> np.ndarray:
    """Matriz sorteios × cadeiras, True quando o ocupante vota sim."""
    c = np.array([np.nan if v is None else v / 100 for v in c_pct], dtype=float)
    vazia = np.isnan(c)
    indice = np.array([B.BLOCOS.index(x) if x else 0 for x in blocos], dtype=int)
    mu = np.zeros(c.shape)
    if (~vazia).any():
        mu[~vazia] = calibrar_locacao(c[~vazia], math.hypot(a, b))
    logit = mu[None, :] + a * sorteios.nacional[:, None] + b * sorteios.bloco[:, indice]
    prob = expit(logit)
    prob[:, vazia] = 0.0
    return sorteios.individual < prob


def _quantil(acumulada: np.ndarray, q: float) -> int:
    """Menor total k com P(total <= k) >= q."""
    return int(np.searchsorted(acumulada, q - 1e-12))


def resumir(totais: np.ndarray, cadeiras: int, *, histograma: bool = True) -> dict:
    n = totais.shape[0]
    contagem = np.bincount(totais, minlength=cadeiras + 1)
    acumulada = np.cumsum(contagem) / n
    saida = {
        "media": r1(float(totais.mean())),
        "p5": _quantil(acumulada, 0.05),
        "p50": _quantil(acumulada, 0.50),
        "p95": _quantil(acumulada, 0.95),
    }
    for limiar in sorted(set(REGUA["simulacao"]["limiares"].values())):
        saida[f"P{limiar}"] = r1(100 * float((totais >= limiar).mean()))
    if histograma:
        saida["histograma"] = [int(x) for x in contagem]
    return saida


def pivos(
    matriz: np.ndarray,
    limiar: int,
    c_pct: Sequence[float | None],
    pessoas: Sequence[dict | None],
) -> list[dict]:
    """Quanto P(total >= limiar) sobe com sim certo e cai com não certo.

    Só entram ocupantes com C na faixa de pivô da régua. Ordena pela chance
    de o voto decidir (sim certo menos não certo).
    """
    piso, teto = REGUA["simulacao"]["faixa_pivo"]
    totais = matriz.sum(axis=1)
    atual = float((totais >= limiar).mean())
    saida = []
    for j, (c, pessoa) in enumerate(zip(c_pct, pessoas, strict=True)):
        if pessoa is None or c is None or not piso <= c <= teto:
            continue
        outros = totais - matriz[:, j]
        com_sim = float((outros + 1 >= limiar).mean())
        com_nao = float((outros >= limiar).mean())
        saida.append(
            {
                "slug": pessoa["slug"],
                "nome": pessoa["nome"],
                "uf": pessoa["uf"],
                "bloco": pessoa["bloco"],
                "C": c,
                "sobe_pp": r1(100 * (com_sim - atual)),
                "cai_pp": r1(100 * (atual - com_nao)),
                "decisivo_pp": r1(100 * (com_sim - com_nao)),
                "_ordem": com_sim - com_nao,
            }
        )
    saida.sort(key=lambda x: (-x["_ordem"], -x["C"], x["slug"]))
    for item in saida:
        del item["_ordem"]
    return saida


def rodar(
    dados: B.Dados,
    scores: dict[str, dict[str, dict]],
    *,
    sorteios: int | None = None,
    semente: int | None = None,
) -> dict:
    """Distribuições, chances e pivôs por cenário, variante e alvo.

    `scores` é slug -> cenário -> saída de `scores.pontuar`.
    """
    regra = REGUA["simulacao"]
    n = int(sorteios or regra["sorteios"])
    semente = int(regra["semente"] if semente is None else semente)
    a, b = escalas(regra["correlacao_intrabloco"], regra["correlacao_nacional"])
    cadeiras = len(dados.cadeiras)
    comum = sortear(n, cadeiras, semente)
    independente = Sorteios(
        nacional=np.zeros(n),
        bloco=np.zeros((n, len(B.BLOCOS))),
        individual=comum.individual,
    )
    resultado: dict = {
        "parametros": {
            "sorteios": n,
            "semente": semente,
            "correlacao_intrabloco": regra["correlacao_intrabloco"],
            "correlacao_nacional": regra["correlacao_nacional"],
            "desvio_choque_nacional_logit": round(a, 2),
            "desvio_choque_bloco_logit": round(b, 2),
            "limiares": dict(regra["limiares"]),
            "faixa_pivo": list(regra["faixa_pivo"]),
        },
        "variantes": dict(B.VARIANTES),
        "cenarios": {},
    }
    for cenario in B.CENARIOS:
        por_variante: dict = {}
        for variante in B.VARIANTES:
            pessoas = B.ocupantes(dados, cenario, variante)
            blocos = [p["bloco"] if p else None for p in pessoas]
            bloco_saida: dict = {
                "ocupantes": [p["slug"] if p else None for p in pessoas]
            }
            pivo_saida: dict = {}
            for nome, alvo in ALVOS.items():
                c = [scores[p["slug"]][cenario][alvo] if p else None for p in pessoas]
                matriz = votos(c, blocos, comum, a, b)
                resumo = resumir(matriz.sum(axis=1), cadeiras)
                resumo["votos_esperados"] = r1(sum(x for x in c if x is not None) / 100)
                sem = votos(c, blocos, independente, 0.0, 0.0)
                resumo["sem_correlacao"] = resumir(
                    sem.sum(axis=1), cadeiras, histograma=False
                )
                bloco_saida[nome] = resumo
                if variante == "base":
                    pivo_saida[nome] = pivos(
                        matriz, regra["limiares"][alvo], c, pessoas
                    )
            if variante == "base":
                bloco_saida["pivos"] = pivo_saida
            por_variante[variante] = bloco_saida
        base = por_variante["base"]
        for variante, dados_var in por_variante.items():
            if variante == "base":
                continue
            dados_var["diferenca_para_base"] = {
                nome: {
                    "votos_esperados": r1(
                        dados_var[nome]["votos_esperados"]
                        - base[nome]["votos_esperados"]
                    ),
                    **{
                        chave: r1(dados_var[nome][chave] - base[nome][chave])
                        for chave in dados_var[nome]
                        if chave.startswith("P")
                    },
                }
                for nome in ALVOS
            }
        resultado["cenarios"][cenario] = por_variante
    return resultado
