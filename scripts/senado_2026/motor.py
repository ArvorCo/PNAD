"""Monte Carlo da eleição de senador, por estado, duas vagas.

Cada sorteio faz, para cada estado:

1. amostragem: por casa, Dirichlet com concentração n / deff sobre o vetor
   fechado em 100 (candidaturas, outros, indecisos, branco/nulo); as casas se
   combinam pelos pesos de recência;
2. indecisos: com probabilidade `mistura_uniforme` o sorteio usa o cenário
   uniforme (indecisos repartidos igualmente entre os nomes com ao menos 1
   ponto), senão o proporcional;
3. erro não amostral, logística-normal: soma ao log das frações válidas um
   choque de campo comum a todos os estados, um choque de campo do estado e um
   choque por candidatura, mais a deriva de passeio aleatório até 04/10, e
   renormaliza;
4. os dois maiores são os eleitos.

As variâncias vêm da calibração de 2022 (`calibracao.py`) ou, sem cobertura
suficiente, da hipótese declarada em `calibracao.HIPOTESE`.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace

import numpy as np

from . import base as B
from . import calibracao as C
from .base import CAMPOS

DEFF = 1.5
SIMULACOES = 20_000
SEMENTE = 20261004
MISTURA_UNIFORME = 0.3
PISO = 1e-12
# Fração da variância estática fora do efeito nacional atribuída ao campo
# dentro do estado. A calibração de 2022 não identifica essa divisão.
FRACAO_ESTADUAL = 0.5
# Hipótese usada só sem calibração: partes iguais entre nacional, estadual e
# candidatura; deriva por dia em log de 0,0015 (ordem da medida em 2022).
DERIVA_HIPOTESE = 0.0015
CORRIDA_REFERENCIA = (30.0, 25.0, 20.0, 10.0, 8.0, 7.0)


@dataclass(frozen=True)
class Erro:
    """Variâncias no log das frações válidas."""

    var_nacional: float
    var_estadual: float
    var_idio: float
    var_deriva_dia: float
    fonte: str

    @property
    def var_estatica(self) -> float:
        return self.var_nacional + self.var_estadual + self.var_idio

    def escalado(self, fator: float) -> Erro:
        """Desvios multiplicados por `fator` (variâncias por fator ao quadrado)."""
        f2 = fator * fator
        return replace(
            self,
            var_nacional=self.var_nacional * f2,
            var_estadual=self.var_estadual * f2,
            var_idio=self.var_idio * f2,
            var_deriva_dia=self.var_deriva_dia * f2,
        )


def sd_pp(
    erro: Erro, *, dias: float = 0.0, corrida=CORRIDA_REFERENCIA, sorteios=200_000
) -> float:
    """Desvio-padrão, em pontos dos válidos, da candidatura em 30% na corrida
    de referência, cada nome num campo diferente (choques independentes)."""
    rng = np.random.default_rng(7)
    p = np.asarray(corrida, float) / sum(corrida)
    var = erro.var_estatica + erro.var_deriva_dia * dias
    eta = np.log(p)[None, :] + math.sqrt(var) * rng.standard_normal((sorteios, len(p)))
    eta -= eta.max(axis=1, keepdims=True)
    q = np.exp(eta)
    q /= q.sum(axis=1, keepdims=True)
    return float(100 * q[:, 0].std())


def erro_de_hipotese() -> Erro:
    """Variância total que reproduz HIPOTESE['sd_pp_30'] na corrida de referência."""
    alvo = C.HIPOTESE["sd_pp_30"]
    lo, hi = 1e-4, 2.0
    for _ in range(30):
        mid = (lo + hi) / 2
        e = Erro(mid / 3, mid / 3, mid / 3, DERIVA_HIPOTESE, "hipotese")
        if sd_pp(e, sorteios=20_000) < alvo:
            lo = mid
        else:
            hi = mid
    v = (lo + hi) / 2
    return Erro(v / 3, v / 3, v / 3, DERIVA_HIPOTESE, "hipotese")


def erro_calibrado(cal: dict | None) -> tuple[Erro, dict]:
    """Erro a partir de calibracao_2022.json, ou a hipótese declarada."""
    detalhe: dict = {}
    if cal:
        cob = cal.get("cobertura", {})
        v = cal.get("variancia_log", {}).get("casas_principais_competitivas") or {}
        tau2 = (cal.get("deriva") or {}).get("var_por_dia_log")
        dias = cal.get("dias_ate_eleicao_medio") or 0.0
        if (
            cob.get("n_estados_casas_principais", 0) >= C.MIN_ESTADOS
            and v.get("var_nao_amostral_log") is not None
            and tau2 is not None
        ):
            estatica = max(0.0, v["var_nao_amostral_log"] - tau2 * dias)
            nacional = min(v.get("var_campo_nacional_log") or 0.0, estatica)
            resto = estatica - nacional
            erro = Erro(
                var_nacional=nacional,
                var_estadual=resto * FRACAO_ESTADUAL,
                var_idio=resto * (1 - FRACAO_ESTADUAL),
                var_deriva_dia=tau2,
                fonte="wikipedia_2022",
            )
            detalhe = {
                "var_nao_amostral_2022_log": v["var_nao_amostral_log"],
                "deriva_descontada_log": tau2 * dias,
                "dias_ate_eleicao_2022": dias,
                "limiar_validos_pesquisa": v.get("limiar_validos_pesquisa"),
                "graus_de_liberdade": v.get("graus_de_liberdade"),
                "var_campo_estadual_medida_log": v.get("var_campo_estadual_log"),
                "pares_mesmo_campo": v.get("pares_mesmo_campo"),
            }
            return erro, detalhe
    return erro_de_hipotese(), detalhe


# --------------------------------------------------------------- sorteio


def _dirichlet(rng, alfa: np.ndarray, s: int) -> np.ndarray:
    g = rng.gamma(np.maximum(alfa, 1e-3)[None, :], 1.0, (s, len(alfa)))
    g = np.maximum(g, PISO)
    return g / g.sum(axis=1, keepdims=True)


def simular_estado(
    media: dict,
    campos_idx: np.ndarray,
    erro: Erro,
    z_nacional: np.ndarray,
    rng: np.random.Generator,
    *,
    mistura_uniforme: float = MISTURA_UNIFORME,
    deff: float = DEFF,
) -> dict:
    """Sorteios de um estado. Devolve frações válidas finais e os dois eleitos.

    `media` vem de `base.media_estado`. `campos_idx` tem o índice do campo de
    cada candidatura em CAMPOS. A última coluna das frações é 'outros', que
    entra nos válidos e nunca é eleita.
    """
    s = z_nacional.shape[0]
    k = len(media["pessoas"])
    v = np.zeros((s, k + 1))
    und = np.zeros(s)
    inv = np.zeros(s)
    peso_ne = 0.0
    for casa in media["casas"]:
        n_ef = casa["onda"]["n_usado"] / deff
        base = [*casa["candidatos"], casa["outros"]]
        tem_ne = casa["indecisos"] is not None
        if tem_ne:
            base += [casa["indecisos"], casa["branco_nulo"]]
        x = _dirichlet(rng, np.asarray(base) * n_ef, s)
        validos = x[:, : k + 1]
        v += casa["peso"] * validos / validos.sum(axis=1, keepdims=True)
        if tem_ne:
            und += casa["peso"] * x[:, k + 1]
            inv += casa["peso"] * x[:, k + 2]
            peso_ne += casa["peso"]
    if peso_ne > 0:
        und /= peso_ne
        inv /= peso_ne
    elegivel = np.array([p["elegivel_uniforme"] for p in media["pessoas"]] + [False])
    m = elegivel.sum()
    usa_uniforme = rng.random(s) < mistura_uniforme
    if m and peso_ne > 0:
        decididos = np.clip(1 - und - inv, 1e-9, 1)[:, None]
        uniforme = v * decididos + und[:, None] * elegivel[None, :] / m
        uniforme /= uniforme.sum(axis=1, keepdims=True)
        v = np.where(usa_uniforme[:, None], uniforme, v)
    dias = max(0.0, media["dias_ate_eleicao"])
    choque = np.zeros((s, k + 1))
    cand = slice(0, k)
    z_estado = rng.standard_normal((s, len(CAMPOS)))
    choque[:, cand] += math.sqrt(erro.var_nacional) * z_nacional[:, campos_idx]
    choque[:, cand] += math.sqrt(erro.var_estadual) * z_estado[:, campos_idx]
    sd_idio = math.sqrt(erro.var_idio + erro.var_deriva_dia * dias)
    choque += sd_idio * rng.standard_normal((s, k + 1))
    eta = np.log(np.maximum(v, PISO)) + choque
    eta -= eta.max(axis=1, keepdims=True)
    p = np.exp(eta)
    p /= p.sum(axis=1, keepdims=True)
    ranking = p[:, :k]
    if k >= 2:
        dois = np.argpartition(-ranking, 1, axis=1)[:, :2]
    else:
        dois = np.zeros((s, 2), int)
    primeiro = ranking.argmax(axis=1)
    return {"validos": p, "eleitos": np.sort(dois, axis=1), "primeiro": primeiro}


def resumir_estado(sorteio: dict, nomes: list[str], *, top_duplas: int = 5) -> dict:
    """p_eleito, p_primeiro, IC90 dos válidos e as duplas mais prováveis."""
    p = sorteio["validos"]
    eleitos = sorteio["eleitos"]
    k = len(nomes)
    s = p.shape[0]
    cont = np.bincount(eleitos.ravel(), minlength=k)[:k]
    primeiro = np.bincount(sorteio["primeiro"], minlength=k)[:k]
    q = np.quantile(100 * p[:, :k], [0.05, 0.5, 0.95], axis=0)
    codigos = eleitos[:, 0] * k + eleitos[:, 1]
    unicos, freq = np.unique(codigos, return_counts=True)
    ordem = np.argsort(-freq, kind="stable")[:top_duplas]
    duplas = [
        {
            "indices": [int(unicos[i] // k), int(unicos[i] % k)],
            "nomes": [nomes[int(unicos[i] // k)], nomes[int(unicos[i] % k)]],
            "p": float(freq[i] / s),
        }
        for i in ordem
    ]
    return {
        "p_eleito": (cont / s).tolist(),
        "p_primeiro": (primeiro / s).tolist(),
        "ic90": [[float(q[0, i]), float(q[2, i])] for i in range(k)],
        "mediana": q[1].tolist(),
        "duplas": duplas,
    }


def descrever_erro(erro: Erro) -> dict:
    d = asdict(erro)
    d["var_estatica"] = erro.var_estatica
    d["sd_log_estatico"] = math.sqrt(erro.var_estatica)
    return d


# ------------------------------------------------------------- orquestração


def preparar_estado(uf: str, ondas: list[dict], tse) -> dict:
    """Seleção de ondas, média central e atributos de cada candidatura."""
    usadas, descartadas, cobertura = B.selecionar(ondas, uf)
    prep = {
        "uf": uf,
        "usadas": usadas,
        "descartadas": descartadas,
        "cobertura": cobertura,
        "media": None,
        "candidatos": [],
    }
    if not usadas:
        return prep
    media = B.media_estado(usadas, uf, tse)
    candidatos = []
    for p in media["pessoas"]:
        tse_c = tse.por_sq.get(p["sq_candidato"] or "")
        partido = B.sigla(tse_c["partido"]) if tse_c else p["partido_pesquisa"]
        excecao = B.CAMPO_EXCECAO_2026.get((uf, p["sq_candidato"] or ""))
        candidatos.append(
            {
                "nome": (
                    B.titulo_urna(tse_c["nome_urna"])
                    if tse_c
                    else B.nome_exibicao(p["nome_pesquisa"])
                ),
                "nome_urna": tse_c["nome_urna"] if tse_c else None,
                "nome_pesquisa": p["nome_pesquisa"],
                "aliases": p["aliases"],
                "sq_candidato": p["sq_candidato"],
                "foto": tse.foto(p["sq_candidato"]),
                "partido": partido,
                "campo": excecao[0] if excecao else B.campo(partido),
                "nota_campo": excecao[1] if excecao else None,
                "valor": p["valor"],
                "validos": p["validos"],
                "validos_uniforme": p["validos_uniforme"],
                "elegivel_uniforme": p["elegivel_uniforme"],
            }
        )
    prep["media"] = media
    prep["candidatos"] = candidatos
    return prep


def rodar(
    preps: list[dict],
    erro: Erro,
    *,
    simulacoes: int,
    semente: int,
    mistura_uniforme: float,
    deff: float,
) -> dict:
    """Um conjunto completo de sorteios, com números aleatórios comuns.

    O choque nacional por campo é o mesmo em todos os estados de um sorteio.
    Cada estado tem gerador próprio, semeado por (semente, posição da UF), para
    que a sensibilidade compare os mesmos sorteios.
    """
    z_nacional = np.random.default_rng([semente, 0]).standard_normal(
        (simulacoes, len(CAMPOS))
    )
    partidos: list[str] = []
    resumos: dict[str, dict] = {}
    assentos: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for i, prep in enumerate(preps):
        if prep["media"] is None or len(prep["candidatos"]) < 2:
            continue
        rng = np.random.default_rng([semente, 1 + i])
        campos_idx = np.array([CAMPOS.index(c["campo"]) for c in prep["candidatos"]])
        sorteio = simular_estado(
            prep["media"],
            campos_idx,
            erro,
            z_nacional,
            rng,
            mistura_uniforme=mistura_uniforme,
            deff=deff,
        )
        nomes = [c["nome"] for c in prep["candidatos"]]
        resumos[prep["uf"]] = resumir_estado(sorteio, nomes)
        for c in prep["candidatos"]:
            rotulo = c["partido"] or "sem partido informado"
            if rotulo not in partidos:
                partidos.append(rotulo)
        p_idx = np.array(
            [
                partidos.index(c["partido"] or "sem partido informado")
                for c in prep["candidatos"]
            ]
        )
        assentos[prep["uf"]] = (
            campos_idx[sorteio["eleitos"]],
            p_idx[sorteio["eleitos"]],
        )
    # Estados sem pesquisa: duas vagas sorteadas da distribuição de campos das
    # vagas sorteadas nos estados com pesquisa recente (hipótese neutra).
    recentes = [p["uf"] for p in preps if p["cobertura"] == "recente"]
    base_campos = np.concatenate(
        [assentos[u][0].ravel() for u in recentes if u in assentos]
        or [np.arange(len(CAMPOS))]
    )
    dist = np.bincount(base_campos, minlength=len(CAMPOS)) / base_campos.size
    rotulo_sem = "estado sem pesquisa"
    for i, prep in enumerate(preps):
        if prep["uf"] in assentos:
            continue
        if rotulo_sem not in partidos:
            partidos.append(rotulo_sem)
        rng = np.random.default_rng([semente, 1 + i])
        c_idx = rng.choice(len(CAMPOS), size=(simulacoes, 2), p=dist)
        assentos[prep["uf"]] = (
            c_idx,
            np.full((simulacoes, 2), partidos.index(rotulo_sem)),
        )
    ordem = [p["uf"] for p in preps]
    campos_novos = np.concatenate([assentos[u][0] for u in ordem], axis=1)
    partidos_novos = np.concatenate([assentos[u][1] for u in ordem], axis=1)
    return {
        "resumos": resumos,
        "campos_novos": campos_novos,
        "partidos_novos": partidos_novos,
        "partidos": partidos,
        "distribuicao_sem_pesquisa": dict(zip(CAMPOS, dist.tolist(), strict=True)),
    }
