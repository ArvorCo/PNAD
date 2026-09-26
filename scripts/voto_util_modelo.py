"""Motor de cenarios do mapa do voto util (1o turno de 2026).

Funcoes puras, sem leitura de arquivo, para que o teste exercite a aritmetica
isolada. A pagina chama isso de "modelo de cenario", nunca de previsao: ele diz
quanto Flavio teria dos votos validos SE uma fracao do caminho entre o 1o e o
2o turno fosse antecipada, com o eleitorado ponderado por quem de fato vota.

Notacao, em pontos percentuais dos entrevistados de uma UF:
    F1, L1  voto em Flavio e em Lula no 1o turno
    T1      demais candidaturas (votos validos que nao sao de F nem de L)
    I1, B1  indecisos e branco/nulo/nao vai votar
    F2, L2  os mesmos dois no 2o turno, na mesma amostra
Reserva de Flavio = F2 - F1: gente que ja escolhe Flavio contra Lula e ainda
nao o escolhe no 1o turno. E o voto util medido, nao suposto.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class Estado:
    uf: str
    peso: float  # eleitores esperados (eleitorado 2026 x comparecimento de 2022)
    F1: float
    L1: float
    T1: float
    I1: float
    B1: float
    F2: float
    L2: float
    n: int = 1000
    # Fracao da reserva de cada lado que sai da terceira via (o resto sai de
    # indecisos e branco/nulo, que nao contam como voto valido).
    fT_flavio: float = 0.5
    fT_lula: float = 0.5
    medido_2t: bool = True
    extra: dict = field(default_factory=dict)

    @property
    def reserva_flavio(self) -> float:
        return max(0.0, self.F2 - self.F1)

    @property
    def reserva_lula(self) -> float:
        return max(0.0, self.L2 - self.L1)


def cenario(e: Estado, lam: float, theta: float) -> dict[str, float]:
    """Antecipa `lam` da reserva de Flavio e `theta` da de Lula para o 1o turno.

    A parte da reserva que sai da terceira via reduz T1; a parte que sai de
    indecisos e branco/nulo entra no denominador dos validos. T1 nunca fica
    negativo: se a reserva pedir mais terceira via do que existe, o excesso e
    tratado como vindo de indecisos e branco/nulo.
    """
    rf, rl = lam * e.reserva_flavio, theta * e.reserva_lula
    tira_t = min(e.T1, rf * e.fT_flavio + rl * e.fT_lula)
    F, L, T = e.F1 + rf, e.L1 + rl, e.T1 - tira_t
    validos = F + L + T
    return {"F": F, "L": L, "T": T, "validos": validos}


def agrega(estados: list[Estado], lam: float, theta: float) -> dict[str, float]:
    """Soma nacional em eleitores esperados; devolve percentuais dos validos."""
    tf = tl = tt = 0.0
    for e in estados:
        c = cenario(e, lam, theta)
        tf += e.peso * c["F"]
        tl += e.peso * c["L"]
        tt += e.peso * c["T"]
    val = tf + tl + tt
    return {
        "flavio_validos": 100 * tf / val,
        "lula_validos": 100 * tl / val,
        "outros_validos": 100 * tt / val,
        "margem": 100 * (tf - tl) / val,
    }


def limiar(
    estados: list[Estado], alvo: str, nivel: float = 50.0, *, dois_lados: bool = False
) -> float | None:
    """Menor lambda em [0, 1] que leva `alvo` a `nivel` (bissecao).

    `alvo` e "flavio_validos" ou "margem". Com `dois_lados`, Lula antecipa a
    mesma fracao da propria reserva. Devolve None se nem lambda=1 alcanca.
    """

    def val(lam: float) -> float:
        return agrega(estados, lam, lam if dois_lados else 0.0)[alvo]

    if val(0.0) >= nivel:
        return 0.0
    if val(1.0) < nivel:
        return None
    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if val(mid) >= nivel:
            hi = mid
        else:
            lo = mid
    return hi


def eleitor_provavel(
    sempre: dict[str, float],
    outros: dict[str, float],
    p_sempre: float,
    p_outros: float,
    r: float,
) -> dict[str, float]:
    """Mistura as duas colunas do cruzamento por comparecimento.

    `p_sempre` e `p_outros` sao as parcelas da amostra em cada grupo; `r` e a
    propensao relativa de o grupo "ja deixou de votar ou nao vai votar"
    comparecer, contra 1 do grupo "sempre vota".
    """
    w1, w2 = p_sempre, p_outros * r
    chaves = set(sempre) | set(outros)
    return {
        k: (w1 * sempre.get(k, 0.0) + w2 * outros.get(k, 0.0)) / (w1 + w2)
        for k in chaves
    }


def simula(
    estados: list[Estado],
    lam: float,
    theta: float,
    *,
    n_sim: int = 4000,
    deff: float = 1.5,
    erro_nacional: float = 1.5,
    erro_reserva: float = 0.35,
    seed: int = 2026,
) -> dict[str, float]:
    """Monte Carlo do cenario: erro amostral por UF, erro comum nacional e
    incerteza da reserva onde o 2o turno nao foi medido.

    `erro_nacional` e o desvio padrao, em pontos, de um deslocamento comum a
    todas as UFs (vies de pesquisa), aplicado com sinal oposto a F e L.
    `erro_reserva` e o desvio relativo da reserva estimada (so onde nao ha
    2o turno medido).
    """
    rng = random.Random(seed)
    fl, mg, lu = [], [], []
    for _ in range(n_sim):
        comum = rng.gauss(0.0, erro_nacional)
        sims = []
        for e in estados:
            se = math.sqrt(deff / max(e.n, 100))

            def pert(p: float, se: float = se) -> float:
                return max(
                    0.0,
                    p
                    + 100
                    * rng.gauss(
                        0.0,
                        se * math.sqrt(max(p, 0.5) / 100 * (1 - min(p, 99.5) / 100)),
                    ),
                )

            k = 1.0 if e.medido_2t else max(0.0, rng.gauss(1.0, erro_reserva))
            F1, L1 = pert(e.F1) + comum / 2, pert(e.L1) - comum / 2
            F2 = F1 + e.reserva_flavio * k
            L2 = L1 + e.reserva_lula * k
            sims.append(
                Estado(
                    e.uf,
                    e.peso,
                    max(F1, 0.0),
                    max(L1, 0.0),
                    pert(e.T1),
                    e.I1,
                    e.B1,
                    F2,
                    L2,
                    e.n,
                    e.fT_flavio,
                    e.fT_lula,
                    e.medido_2t,
                )
            )
        a = agrega(sims, lam, theta)
        fl.append(a["flavio_validos"])
        mg.append(a["margem"])
        lu.append(a["lula_validos"])
    fl.sort()
    mg.sort()
    lu.sort()

    def q(xs: list[float], p: float) -> float:
        return xs[min(len(xs) - 1, max(0, int(p * len(xs))))]

    return {
        "flavio_p10": q(fl, 0.10),
        "flavio_p50": q(fl, 0.50),
        "flavio_p90": q(fl, 0.90),
        "margem_p10": q(mg, 0.10),
        "margem_p50": q(mg, 0.50),
        "margem_p90": q(mg, 0.90),
        "lula_p10": q(lu, 0.10),
        "lula_p50": q(lu, 0.50),
        "lula_p90": q(lu, 0.90),
        "p_flavio_primeiro": sum(1 for m in mg if m > 0) / len(mg),
        "p_flavio_50": sum(1 for f in fl if f > 50) / len(fl),
        "p_lula_50": sum(1 for x in lu if x > 50) / len(lu),
    }
