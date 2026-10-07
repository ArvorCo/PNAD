"""Métricas do Politize sua vizinhança: funções puras, sem leitura de arquivo.

Convenções do contrato: ``_v`` = % dos válidos (nominais das candidaturas da lista),
``_a`` = % dos aptos, ``_pp`` = pontos percentuais. Ausência = ``None``, nunca zero.
Tudo é calculado sem arredondar; o arredondamento (1 casa) acontece só na saída, e as
regras de arquétipo leem os valores já arredondados, os mesmos que o app mostra.
"""

from __future__ import annotations

import bisect
import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

# Conta do 2º turno: a terceira via fica 30% sem escolha (Nexus 21/09, p. 79) e o
# resto divide-se 61% Flávio / 39% Lula (síntese de três fontes em
# analysis/predicao_2026). Brancos, nulos e abstenção não viram voto.
SEM_ESCOLHA = 0.30
FLAVIO_ENTRE_ESCOLHEM = 0.61
COEF_FLAVIO_2T = (1 - SEM_ESCOLHA) * FLAVIO_ENTRE_ESCOLHEM
COEF_LULA_2T = (1 - SEM_ESCOLHA) * (1 - FLAVIO_ENTRE_ESCOLHEM)
TAXA_CONVERSAO = 0.35
PESO_AUSENTES = 0.5
TETO_POTENCIAL = 40.0

CONTADORES = (
    "aptos",
    "secoes",
    "comparecimento",
    "flavio",
    "lula",
    "terceira",
    "brancos",
    "nulos",
    "cury",
    "renan",
    "caiado",
    "zema",
    "outros_nominais",
)
CONTADORES_2022 = (
    "aptos_casado",
    "flavio_casado",
    "aptos22",
    "b22_1t",
    "l22_1t",
    "nom22_1t",
    "b22_2t",
    "l22_2t",
    "nom22_2t",
    "aptos22_2t",
    "comp22_2t",
)


def pct(num: float | None, den: float | None) -> float | None:
    """Percentual (0 a 100); ``None`` quando o denominador é zero ou ausente."""
    if num is None or not den:
        return None
    return 100.0 * num / den


def r1(x: float | None) -> float | None:
    """Uma casa decimal, arredondamento comercial (0,05 sobe), sem ``-0.0``."""
    if x is None:
        return None
    v = math.floor(abs(x) * 10 + 0.5 + 1e-9) / 10
    return 0.0 if v == 0 else math.copysign(v, x)


# ------------------------------------------------------------ votos e 2022


def metricas_votos(c: Mapping[str, float]) -> dict[str, float | None]:
    """Taxas de 2026 a partir das contagens do local (ou de uma soma de locais)."""
    aptos, comp = c["aptos"], c["comparecimento"]
    validos = c["flavio"] + c["lula"] + c["terceira"]
    flavio_v = pct(c["flavio"], validos)
    lula_v = pct(c["lula"], validos)
    return {
        "validos": validos,
        "abstencao": aptos - comp,
        "flavio_v": flavio_v,
        "lula_v": lula_v,
        "terceira_v": pct(c["terceira"], validos),
        "bn_v": pct(c["brancos"] + c["nulos"], validos),
        "flavio_a": pct(c["flavio"], aptos),
        "lula_a": pct(c["lula"], aptos),
        "terceira_a": pct(c["terceira"], aptos),
        "bn_a": pct(c["brancos"] + c["nulos"], aptos),
        "abst_a": pct(aptos - comp, aptos),
        "margem_v": None if flavio_v is None else flavio_v - (lula_v or 0.0),
    }


def metricas_2022(c: Mapping[str, float]) -> dict[str, float | None]:
    """Taxas de 2022 sobre as seções casadas (mesmo número e mesmo local).

    ``reencontro_a`` compara Bolsonaro 2022 e Flávio 2026 nas mesmas seções casadas,
    cada um sobre os próprios aptos: é saldo agregado, nunca trajetória de pessoa.
    """
    aptos = c["aptos"]
    if not c.get("aptos_casado") or not c.get("aptos22"):
        return {
            "cobertura_2022": 0.0 if aptos else None,
            "bolsonaro22_1t_v": None,
            "lula22_1t_v": None,
            "bolsonaro22_2t_v": None,
            "lula22_2t_v": None,
            "abst22_2t_a": None,
            "bolsonaro22_1t_a": None,
            "reencontro_a": None,
        }
    b22_a = pct(c["b22_1t"], c["aptos22"])
    flavio_casado_a = pct(c["flavio_casado"], c["aptos_casado"])
    return {
        "cobertura_2022": pct(c["aptos_casado"], aptos),
        "bolsonaro22_1t_v": pct(c["b22_1t"], c["nom22_1t"]),
        "lula22_1t_v": pct(c["l22_1t"], c["nom22_1t"]),
        "bolsonaro22_2t_v": pct(c["b22_2t"], c["nom22_2t"]),
        "lula22_2t_v": pct(c["l22_2t"], c["nom22_2t"]),
        "abst22_2t_a": pct(c["aptos22_2t"] - c["comp22_2t"], c["aptos22_2t"]),
        "bolsonaro22_1t_a": b22_a,
        "reencontro_a": reencontro(b22_a, flavio_casado_a),
    }


def reencontro(bolsonaro22_1t_a: float | None, flavio_a: float | None) -> float | None:
    """max(0, Bolsonaro 2022 1º turno − Flávio 2026), em % dos aptos."""
    if bolsonaro22_1t_a is None or flavio_a is None:
        return None
    return max(0.0, bolsonaro22_1t_a - flavio_a)


# ------------------------------------------------------- perfil e renda


def parcelas_perfil(vetor: Sequence[float], cols: Sequence[str]) -> dict[str, float]:
    """Shares (0 a 100) de sexo, idade e escolaridade; desconhecidos fora do denominador."""
    v = dict(zip(cols, vetor, strict=True))
    saida: dict[str, float] = {}
    grupos = (
        ("fem", "masc"),
        ("a16_24", "a25_34", "a35_44", "a45_59", "a60"),
        ("fund_inc", "fund_med", "med_sup_inc", "superior"),
    )
    for grupo in grupos:
        total = sum(v[g] for g in grupo)
        for g in grupo:
            saida[g] = 100.0 * v[g] / total if total else None
    return saida


def voto_valido_faixas(cruzamento: Mapping[str, Any]) -> list[dict[str, float]]:
    """Flávio e Lula em % dos válidos por faixa de renda (sem branco/nulo e indecisos)."""
    opcoes = list(cruzamento["opcoes"])
    fora = {"branco_nulo", "indecisos"}
    saida = []
    for linha in cruzamento["linhas"]:
        valores = dict(zip(opcoes, linha, strict=True))
        validos = sum(v for k, v in valores.items() if k not in fora)
        saida.append(
            {
                "flavio": 100.0 * valores["flavio"] / validos,
                "lula": 100.0 * valores["lula"] / validos,
            }
        )
    return saida


def media_casas(por_casa: Sequence[Sequence[Mapping[str, float]]]):
    """Média simples, faixa a faixa, das casas (mesmas faixas em todas)."""
    n = len(por_casa)
    faixas = len(por_casa[0])
    return [
        {k: sum(casa[i][k] for casa in por_casa) / n for k in ("flavio", "lula")}
        for i in range(faixas)
    ]


def esperado_bruto(
    renda: Mapping[str, float] | None, voto: Sequence[Mapping[str, float]]
) -> tuple[float, float] | None:
    """Voto esperado pelo perfil de renda: soma de parcela da faixa × voto da faixa."""
    if renda is None:
        return None
    pesos = [renda["ate2"], renda["de2a5"], renda["mais5"]]
    total = sum(pesos)
    if total <= 0:
        return None
    f = sum(p * v["flavio"] for p, v in zip(pesos, voto, strict=True)) / total
    l_ = sum(p * v["lula"] for p, v in zip(pesos, voto, strict=True)) / total
    return f, l_


def deslocamento(
    pares: Iterable[tuple[float, float]], alvo: float
) -> tuple[float, float]:
    """(média ponderada, alvo − média) para pares (valor, peso)."""
    soma = peso = 0.0
    for valor, w in pares:
        soma += valor * w
        peso += w
    media = soma / peso
    return media, alvo - media


# ------------------------------------------------------ índice de conversa


def componentes(
    m: Mapping[str, float | None], vao_perfil_pp: float | None
) -> dict[str, float | None]:
    """Componentes do potencial, em votos por 100 aptos.

    Componente sem dado (2022 sem casamento, local sem perfil de renda) entra como
    zero no potencial e fica ``None`` no campo.
    """
    if m.get("terceira_a") is None:
        return {
            "c_terceira": None,
            "c_ausentes": None,
            "c_reencontro": None,
            "c_perfil": None,
            "potencial": None,
        }
    c_terceira = m["terceira_a"] + m["bn_a"]
    c_ausentes = PESO_AUSENTES * m["abst_a"]
    c_reencontro = m.get("reencontro_a")
    if vao_perfil_pp is None or not m.get("aptos"):
        c_perfil = None
    else:
        c_perfil = max(0.0, vao_perfil_pp) * m["validos"] / m["aptos"]
    potencial = c_terceira + c_ausentes + (c_reencontro or 0.0) + (c_perfil or 0.0)
    return {
        "c_terceira": c_terceira,
        "c_ausentes": c_ausentes,
        "c_reencontro": c_reencontro,
        "c_perfil": c_perfil,
        "potencial": potencial,
    }


def indice(potencial: float | None, teto: float = TETO_POTENCIAL) -> int | None:
    """0 a 100: potencial sobre o teto prático, saturado em 100."""
    if potencial is None:
        return None
    return math.floor(100.0 * min(1.0, potencial / teto) + 0.5)


# ------------------------------------------------------------ conta 2º turno


def conta_2t(
    flavio: float,
    lula: float,
    terceira: float,
    abst22_2t_a: float | None,
    taxa: float = TAXA_CONVERSAO,
) -> dict[str, float | int | None]:
    """Projeção do 2º turno no local e conversas para virar ou para segurar.

    ``faltam`` é o menor número inteiro de votos a mais que põe Flávio à frente
    (0 se já está à frente). ``conversas_para_virar`` = faltam / taxa, para cima.
    Quando já está à frente, ``conversas_para_segurar`` = abstenção esperada do próprio
    lado, ``flavio_2t × abst22_2t_a / 100``.
    """
    f2 = flavio + COEF_FLAVIO_2T * terceira
    l2 = lula + COEF_LULA_2T * terceira
    dif = l2 - f2
    faltam = 0 if dif < 0 else math.floor(dif + 1e-9) + 1
    if faltam > 0:
        virar = math.ceil(faltam / taxa - 1e-9)
        segurar = None
    else:
        virar = None
        segurar = None if abst22_2t_a is None else round(f2 * abst22_2t_a / 100.0)
    return {
        "flavio_2t": f2,
        "lula_2t": l2,
        "faltam": faltam,
        "conversas_para_virar": virar,
        "conversas_para_segurar": segurar,
    }


# ------------------------------------------------------------- votos em aberto


def em_aberto(c: Mapping[str, float]) -> float:
    """Votos que não foram para Flávio nem para Lula: terceira + brancos + nulos +
    abstenção (aptos menos comparecimento)."""
    return (
        c["terceira"] + c["brancos"] + c["nulos"] + (c["aptos"] - c["comparecimento"])
    )


def bna(c: Mapping[str, float]) -> float:
    """Brancos + nulos + abstenção, em votos (os em aberto sem a terceira via)."""
    return c["brancos"] + c["nulos"] + (c["aptos"] - c["comparecimento"])


def viravel(flavio: float, lula: float, bna_votos: float) -> str | None:
    """Quem viraria o local só com brancos, nulos e abstenção (``None`` se ninguém).

    ``"flavio"``: Lula na frente e bna >= Lula − Flávio. ``"lula"``: Flávio na frente
    e bna >= Flávio − Lula. Empate exato não é virada de ninguém.
    """
    if lula > flavio and bna_votos >= lula - flavio:
        return "flavio"
    if flavio > lula and bna_votos >= flavio - lula:
        return "lula"
    return None


# ----------------------------------------------------------------- agregação


def somar(registros: Iterable[Mapping[str, Any]], chaves: Iterable[str]) -> dict:
    chaves = tuple(chaves)
    total = dict.fromkeys(chaves, 0.0)
    for r in registros:
        for k in chaves:
            total[k] += r.get(k) or 0
    return total


def media_ponderada(
    pares: Iterable[tuple[float | None, float]],
) -> float | None:
    soma = peso = 0.0
    for valor, w in pares:
        if valor is None or not w:
            continue
        soma += valor * w
        peso += w
    return soma / peso if peso else None


def posicao_percentil(valor: float | None, ordenados: Sequence[float]) -> int | None:
    """Posição de 0 a 100: parcela dos outros elementos com valor estritamente menor.

    ``ordenados`` é a referência em ordem crescente (inclui o próprio valor). O maior
    valor recebe 100 e o menor 0; empates recebem a mesma posição. Arredonda para
    baixo, para "mais que X% dos locais" nunca exagerar.
    """
    if valor is None or len(ordenados) < 2:
        return None
    menores = bisect.bisect_left(ordenados, valor)
    return math.floor(100.0 * menores / (len(ordenados) - 1) + 1e-9)


def percentis(valores: Sequence[float], qs: Sequence[float]) -> dict[str, float]:
    """Percentis por interpolação linear (mesma regra do numpy ``linear``)."""
    xs = sorted(valores)
    n = len(xs)
    saida = {}
    for q in qs:
        if n == 0:
            saida[f"p{q:g}"] = None
            continue
        pos = (n - 1) * q / 100.0
        i = math.floor(pos)
        j = min(i + 1, n - 1)
        saida[f"p{q:g}"] = xs[i] + (xs[j] - xs[i]) * (pos - i)
    return saida
