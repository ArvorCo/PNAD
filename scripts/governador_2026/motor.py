"""Monte Carlo da eleição de governador, por estado: 1º turno e 2º turno.

Cada sorteio faz, para cada estado:

1. amostragem do 1º turno: por casa, Dirichlet com concentração n / deff sobre
   o vetor fechado em 100; as casas se combinam pelos pesos de recência;
2. indecisos: proporcional ao voto declarado, ou uniforme com probabilidade
   `mistura_uniforme`; branco e nulo nunca viram voto;
3. erro não amostral, logística-normal: choque de campo comum a todos os
   estados, choque de campo do estado e choque por candidatura, mais a deriva
   até 04/10, somados ao log das frações válidas;
4. decisão: a candidatura mais votada passa de 50% dos válidos? eleita no 1º
   turno. Senão as duas mais votadas vão ao 2º turno;
5. 2º turno: se o par foi medido, a fração publicada do primeiro nome entre os
   dois recebe o ruído amostral do par e a mesma diferença de choques do 1º
   turno (erro correlacionado entre turnos). Se não foi medido, o voto de cada
   candidatura eliminada migra por uma prior declarada de proximidade entre
   campos, com ruído extra.
"""

from __future__ import annotations

import math

import numpy as np
from senado_2026 import base as SB
from senado_2026.motor import DEFF, MISTURA_UNIFORME, PISO, Erro

from . import base as B
from .base import CAMPOS
from .tse import GRAFIA

SIMULACOES = 20_000
SEMENTE = 20261004
# Posição de cada campo numa reta esquerda-direita, para a prior de transferência.
POSICAO = {
    "esquerda": 0.0,
    "centro-esquerda": 1.0,
    "centro": 2.0,
    "centro-direita": 3.0,
    "direita": 4.0,
    "indefinido": 2.0,
}
# Prior de transferência para pares sem medição: fração do eleitorado da
# candidatura eliminada que vota num dos dois finalistas (o resto vira branco,
# nulo ou abstenção) e a temperatura da divisão entre eles por distância.
TRANSFERENCIA_VALIDA = 0.7
TRANSFERENCIA_TAU = 1.0
# Desvio extra, no logit, da fração do primeiro nome num par não medido.
SD_TRANSFERENCIA_LOGIT = 0.25
# Correlação entre o erro não amostral do 1º turno e o do 2º turno medido: a
# diferença de choques dos dois finalistas entra no 2º turno com este peso, e o
# resto da variância vem de um choque próprio do 2º turno (hipótese declarada).
RHO_TURNOS = 0.5
# Limiar de decisão no 1º turno: maioria absoluta dos válidos.
MAIORIA = 0.5
# Pares de 2º turno listados por estado.
TOP_PARES = 4


def _dirichlet(rng, alfa: np.ndarray, s: int) -> np.ndarray:
    g = rng.gamma(np.maximum(alfa, 1e-3)[None, :], 1.0, (s, len(alfa)))
    g = np.maximum(g, PISO)
    return g / g.sum(axis=1, keepdims=True)


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def transferencia(campos: list[str], a: int, b: int, outros_campo: str = "indefinido"):
    """Fração do voto de cada candidatura (e de 'outros') que vai a `a` e a `b`.

    Devolve dois vetores de tamanho k + 1 (a última posição é 'outros'). Os
    próprios finalistas mantêm 100% do voto. Para os demais, uma fração
    TRANSFERENCIA_VALIDA vota, dividida por softmax de menos a distância
    entre campos sobre TRANSFERENCIA_TAU: mesmo campo do finalista, quase
    tudo para ele; equidistante, metade para cada.
    """
    pos = [POSICAO[c] for c in campos] + [POSICAO[outros_campo]]
    xa, xb = pos[a], pos[b]
    ta = np.zeros(len(pos))
    tb = np.zeros(len(pos))
    for j, x in enumerate(pos):
        if j == a:
            ta[j] = 1.0
        elif j == b:
            tb[j] = 1.0
        else:
            ea = math.exp(-abs(x - xa) / TRANSFERENCIA_TAU)
            eb = math.exp(-abs(x - xb) / TRANSFERENCIA_TAU)
            ta[j] = TRANSFERENCIA_VALIDA * ea / (ea + eb)
            tb[j] = TRANSFERENCIA_VALIDA * eb / (ea + eb)
    return ta, tb


def simular_estado(
    media: dict,
    campos: list[str],
    erro: Erro,
    z_nacional: np.ndarray,
    rng: np.random.Generator,
    pares: dict[tuple[int, int], dict],
    *,
    mistura_uniforme: float = MISTURA_UNIFORME,
    deff: float = DEFF,
) -> dict:
    """Sorteios de um estado. Devolve frações do 1º turno, decisão, par e
    vencedor de cada sorteio."""
    s = z_nacional.shape[0]
    k = len(media["pessoas"])
    campos_idx = np.array([CAMPOS.index(c) for c in campos])
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
    return _decidir(p, choque, campos, pares, rng, erro, sd_idio**2)


def _decidir(
    p: np.ndarray,
    choque: np.ndarray,
    campos: list[str],
    pares: dict[tuple[int, int], dict],
    rng: np.random.Generator,
    erro: Erro,
    sd_idio_2: float,
) -> dict:
    s, k1 = p.shape
    k = k1 - 1
    ranking = p[:, :k]
    primeiro = ranking.argmax(axis=1)
    decidido = ranking.max(axis=1) > MAIORIA
    if k >= 2:
        dois = np.sort(np.argpartition(-ranking, 1, axis=1)[:, :2], axis=1)
    else:
        dois = np.zeros((s, 2), int)
    vencedor = primeiro.copy()
    fracao_a = np.full(s, np.nan)
    medido = np.zeros(s, bool)
    for a, b in {tuple(x) for x in dois[~decidido].tolist()}:
        mask = (~decidido) & (dois[:, 0] == a) & (dois[:, 1] == b)
        if not mask.any():
            continue
        dif = choque[mask, a] - choque[mask, b]
        # Variância teórica da diferença de choques: campo (quando os campos
        # diferem) e próprio dos dois nomes.
        var_dif = 2 * sd_idio_2 + (
            2 * (erro.var_nacional + erro.var_estadual) if campos[a] != campos[b] else 0
        )
        dif = RHO_TURNOS * dif + math.sqrt(
            (1 - RHO_TURNOS**2) * var_dif
        ) * rng.standard_normal(mask.sum())
        par = pares.get((a, b))
        if par:
            base = _logit(np.full(mask.sum(), par["fracao_a"]))
            n_par = max(par["n_par"] / DEFF, 1.0)
            pa = par["fracao_a"]
            sd_amostral = math.sqrt(1.0 / (n_par * max(pa * (1 - pa), 1e-4)))
            sd_deriva = math.sqrt(
                2 * erro.var_deriva_dia * max(0.0, par["dias_ate_eleicao"])
            )
            ruido = rng.standard_normal(mask.sum()) * math.hypot(sd_amostral, sd_deriva)
            fa = _sigmoid(base + ruido + dif)
            medido[mask] = True
        else:
            ta, tb = transferencia(campos, a, b)
            # Soma explícita em vez de matmul: o BLAS do macOS emite avisos
            # espúrios de divisão por zero com frações muito pequenas.
            pm = p[mask]
            pa_ = (pm * ta).sum(axis=1)
            pb_ = (pm * tb).sum(axis=1)
            base = _logit(pa_ / (pa_ + pb_))
            ruido = rng.standard_normal(mask.sum()) * SD_TRANSFERENCIA_LOGIT
            fa = _sigmoid(base + ruido)
        fracao_a[mask] = fa
        vencedor[mask] = np.where(fa > 0.5, a, b)
    return {
        "validos": p,
        "primeiro": primeiro,
        "decidido": decidido,
        "par": dois,
        "fracao_a": fracao_a,
        "medido": medido,
        "vencedor": vencedor,
    }


def resumir_estado(sorteio: dict, nomes: list[str], *, top_pares: int = TOP_PARES):
    p = sorteio["validos"]
    s = p.shape[0]
    k = len(nomes)
    dec = sorteio["decidido"]
    venc = sorteio["vencedor"]
    par = sorteio["par"]
    p_eleito = np.bincount(venc, minlength=k)[:k] / s
    p_vence_1t = np.bincount(venc[dec], minlength=k)[:k] / s
    p_primeiro = np.bincount(sorteio["primeiro"], minlength=k)[:k] / s
    p_vai_2t = np.bincount(par[~dec].ravel(), minlength=k)[:k] / s
    q = np.quantile(100 * p[:, :k], [0.05, 0.5, 0.95], axis=0)
    codigos = par[~dec, 0] * k + par[~dec, 1]
    unicos, freq = np.unique(codigos, return_counts=True)
    ordem = np.argsort(-freq, kind="stable")[:top_pares]
    pares = []
    for i in ordem:
        a, b = int(unicos[i] // k), int(unicos[i] % k)
        mask = (~dec) & (par[:, 0] == a) & (par[:, 1] == b)
        fa = sorteio["fracao_a"][mask]
        pares.append(
            {
                "indices": [a, b],
                "nomes": [nomes[a], nomes[b]],
                "p_par": float(freq[i] / s),
                "medido": bool(sorteio["medido"][mask].all()),
                "fracao_a_media": float(fa.mean()),
                "fracao_a_ic90": [
                    float(np.quantile(fa, 0.05)),
                    float(np.quantile(fa, 0.95)),
                ],
                "p_a_vence_dado_par": float((fa > 0.5).mean()),
            }
        )
    return {
        "p_eleito": p_eleito.tolist(),
        "p_vence_1t": p_vence_1t.tolist(),
        "p_vence_2t": (p_eleito - p_vence_1t).tolist(),
        "p_vai_2t": p_vai_2t.tolist(),
        "p_primeiro": p_primeiro.tolist(),
        "ic90": [[float(q[0, i]), float(q[2, i])] for i in range(k)],
        "mediana": q[1].tolist(),
        "p_decide_1t": float(dec.mean()),
        "pares": pares,
    }


def preparar_estado(uf: str, ondas: list[dict], tse: B.Tse) -> dict:
    """Seleção de ondas, média central, atributos e pares medidos."""
    usadas, descartadas, cobertura = SB.selecionar(ondas, uf)
    prep = {
        "uf": uf,
        "usadas": usadas,
        "descartadas": descartadas,
        "cobertura": cobertura,
        "media": None,
        "candidatos": [],
        "pares": {},
        "pares_nao_casados": [],
    }
    if not usadas:
        return prep
    media = SB.media_estado(usadas, uf, tse)
    candidatos = []
    for p in media["pessoas"]:
        tse_c = tse.por_sq.get(p["sq_candidato"] or "")
        partido = SB.sigla(tse_c["partido"]) if tse_c else p["partido_pesquisa"]
        candidatos.append(
            {
                "nome": (
                    GRAFIA.get(tse_c["nome_urna"], SB.titulo_urna(tse_c["nome_urna"]))
                    if tse_c
                    else SB.nome_exibicao(p["nome_pesquisa"])
                ),
                "nome_urna": tse_c["nome_urna"] if tse_c else None,
                "nome_pesquisa": p["nome_pesquisa"],
                "aliases": p["aliases"],
                "sq_candidato": p["sq_candidato"],
                "foto": tse.foto(p["sq_candidato"]),
                "partido": partido,
                "campo": SB.campo(partido),
                "valor": p["valor"],
                "validos": p["validos"],
                "validos_uniforme": p["validos_uniforme"],
                "elegivel_uniforme": p["elegivel_uniforme"],
            }
        )
    prep["media"] = media
    prep["candidatos"] = candidatos
    prep["pares"], prep["pares_nao_casados"] = B.pares_medidos(
        ondas, uf, media["pessoas"], tse
    )
    return prep


def rodar(
    preps: list[dict],
    erro: Erro,
    *,
    simulacoes: int,
    semente: int,
    mistura_uniforme: float,
    deff: float,
    usar_pares: bool = True,
) -> dict:
    """Um conjunto completo de sorteios com números aleatórios comuns: o
    choque nacional por campo é o mesmo em todos os estados de um sorteio e
    cada estado tem gerador próprio semeado por (semente, posição da UF)."""
    z_nacional = np.random.default_rng([semente, 0]).standard_normal(
        (simulacoes, len(CAMPOS))
    )
    resumos: dict[str, dict] = {}
    campos_venc: dict[str, np.ndarray] = {}
    decididos: dict[str, np.ndarray] = {}
    for i, prep in enumerate(preps):
        if prep["media"] is None or len(prep["candidatos"]) < 2:
            continue
        rng = np.random.default_rng([semente, 1 + i])
        campos = [c["campo"] for c in prep["candidatos"]]
        sorteio = simular_estado(
            prep["media"],
            campos,
            erro,
            z_nacional,
            rng,
            prep["pares"] if usar_pares else {},
            mistura_uniforme=mistura_uniforme,
            deff=deff,
        )
        nomes = [c["nome"] for c in prep["candidatos"]]
        resumos[prep["uf"]] = resumir_estado(sorteio, nomes)
        campos_idx = np.array([CAMPOS.index(c) for c in campos])
        campos_venc[prep["uf"]] = campos_idx[sorteio["vencedor"]]
        decididos[prep["uf"]] = sorteio["decidido"]
    return {
        "resumos": resumos,
        "campos_vencedor": campos_venc,
        "decididos": decididos,
        "simulacoes": simulacoes,
    }


def nacional(rodada: dict) -> dict:
    """Decididos no 1º turno e governos por campo, por sorteio."""
    s = rodada["simulacoes"]
    ufs = sorted(rodada["decididos"])
    if not ufs:
        return {"decididos_1t": None, "por_campo": {}, "ufs_cobertas": 0}
    dec = np.stack([rodada["decididos"][u] for u in ufs], axis=1)
    n_dec = dec.sum(axis=1)
    campos = np.stack([rodada["campos_vencedor"][u] for u in ufs], axis=1)
    por_campo = {}
    for j, c in enumerate(CAMPOS):
        cont = (campos == j).sum(axis=1)
        por_campo[c] = {
            "esperado": float(cont.mean()),
            "ic90": [int(np.quantile(cont, 0.05)), int(np.quantile(cont, 0.95))],
        }
    grupos = {
        "direita": (CAMPOS.index("direita"), CAMPOS.index("centro-direita")),
        "centro": (CAMPOS.index("centro"),),
        "esquerda": (CAMPOS.index("esquerda"), CAMPOS.index("centro-esquerda")),
    }
    por_grupo = {}
    for g, idx in grupos.items():
        cont = np.isin(campos, idx).sum(axis=1)
        por_grupo[g] = {
            "esperado": float(cont.mean()),
            "ic90": [int(np.quantile(cont, 0.05)), int(np.quantile(cont, 0.95))],
            "p_maioria_14": float((cont >= 14).mean()),
        }
    hist = np.bincount(n_dec, minlength=len(ufs) + 1) / s
    return {
        "ufs_cobertas": len(ufs),
        "decididos_1t": {
            "esperado": float(n_dec.mean()),
            "ic90": [int(np.quantile(n_dec, 0.05)), int(np.quantile(n_dec, 0.95))],
            "distribuicao": hist.tolist(),
        },
        "segundo_turno": {
            "esperado": float((len(ufs) - n_dec).mean()),
            "ic90": [
                int(len(ufs) - np.quantile(n_dec, 0.95)),
                int(len(ufs) - np.quantile(n_dec, 0.05)),
            ],
        },
        "por_campo": por_campo,
        "por_grupo": por_grupo,
    }
