"""Os estados lentos, em dois anos: marcos da totalização por UF em 2022 e 2026.

Partes puras, sem banco nem disco. Tempo em minutos desde as 17h de Brasília do
dia da eleição (02/10/2022 e 04/10/2026), quando as urnas fecharam em todas as
UFs; depois da meia-noite os minutos passam de 420.

Duas réguas por ano:
- 2022, por seção (dados abertos do TSE): `DT_RECEBIMENTO_BU_HOR_TSE` (o boletim
  chegou ao TSE) e `DT_PRIM_TOT_PARCIAL_HOR_TSE` (o boletim entrou pela primeira
  vez numa totalização parcial), as duas na hora do TSE;
- 2026: a versão do arquivo de UF em que as seções totalizadas passaram de cada
  fração (hora de geração do TSE) e, onde a coleta seção a seção já tem o
  carimbo de recebimento publicado no `aux` de cada seção, a mesma conta do 2022.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence
from itertools import pairwise
from typing import Any

FRACOES = (0.5, 0.9, 0.99, 1.0)
CHAVES = ("50", "90", "99", "100")
# Fuso das UFs fora de Brasília (UTC-3). Parte do Amazonas fica em UTC-5 (o
# encerramento mais cedo nos boletins da UF marca 15h); a UF entra como UTC-4,
# o fuso da capital.
FUSO_UF = {"ac": -5, "am": -4, "mt": -4, "ms": -4, "ro": -4, "rr": -4}


def fuso(uf: str) -> int:
    return FUSO_UF.get(uf.lower(), -3)


def marco_tempos(tempos: Sequence[float], total: int | None = None) -> dict[str, float]:
    """Minuto em que a contagem acumulada de seções passou de cada fração.

    `tempos` são os minutos de cada seção (qualquer ordem); `total` é o universo
    (padrão: o próprio número de tempos). A fração q é alcançada quando pelo menos
    ceil(q × total) seções já têm tempo; 100% é o tempo da última.
    """
    xs = sorted(tempos)
    n = total if total is not None else len(xs)
    if not xs or n <= 0:
        return {}
    saida = {}
    for f, k in zip(FRACOES, CHAVES, strict=True):
        alvo = max(1, math.ceil(f * n))
        if alvo <= len(xs):
            saida[k] = round(xs[alvo - 1], 2)
    return saida


def marco_serie(pontos: Sequence[tuple[float, int]], total: int) -> dict[str, float]:
    """Mesma conta sobre uma série acumulada (minuto, seções totalizadas)."""
    saida = {}
    for f, k in zip(FRACOES, CHAVES, strict=True):
        alvo = max(1, math.ceil(f * total))
        hit = next((m for m, st in pontos if st >= alvo), None)
        if hit is not None:
            saida[k] = round(hit, 2)
    return saida


def curva_tempos(tempos: Sequence[float], total: int, grade: Sequence[float]) -> list:
    """Porcentagem acumulada de seções em cada minuto da grade."""
    xs = sorted(tempos)
    saida, i = [], 0
    for m in grade:
        while i < len(xs) and xs[i] <= m:
            i += 1
        saida.append(round(100 * i / total, 2) if total else None)
    return saida


def curva_serie(pontos: Sequence[tuple[float, int]], total: int, grade) -> list:
    saida, i, atual = [], 0, 0
    for m in grade:
        while i < len(pontos) and pontos[i][0] <= m:
            atual = pontos[i][1]
            i += 1
        saida.append(round(100 * atual / total, 2) if total else None)
    return saida


def postos(valores: Sequence[float]) -> list[float]:
    """Postos médios (empates recebem a média das posições), começando em 1."""
    ordem = sorted(range(len(valores)), key=lambda i: valores[i])
    saida = [0.0] * len(valores)
    i = 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and valores[ordem[j + 1]] == valores[ordem[i]]:
            j += 1
        medio = (i + j) / 2 + 1
        for k in range(i, j + 1):
            saida[ordem[k]] = medio
        i = j + 1
    return saida


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Correlação de postos de Spearman (Pearson sobre postos médios)."""
    if len(x) != len(y) or len(x) < 3:
        return None
    rx, ry = postos(x), postos(y)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx == 0 or syy == 0:
        return None
    return round(sxy / math.sqrt(sxx * syy), 4)


def ultimos(
    municipios: Mapping[Any, Mapping[str, Any]], n: int = 3
) -> list[dict[str, Any]]:
    """Os `n` municípios cuja última seção entrou por último (mais tardio primeiro)."""
    lista = sorted(municipios.items(), key=lambda kv: -kv[1]["min"])
    return [{"cd": str(cd), **v} for cd, v in lista[:n]]


def lentas(valores: Mapping[str, float | None]) -> set[str]:
    """UFs com marco acima da mediana das UFs naquele ano."""
    ok = {u: v for u, v in valores.items() if v is not None}
    if not ok:
        return set()
    med = statistics.median(ok.values())
    return {u for u, v in ok.items() if v > med}


def classificar(
    m2022: Mapping[str, float | None], m2026: Mapping[str, float | None]
) -> dict[str, list[str]]:
    """Lenta nos dois anos (estrutural), só em um, ou em nenhum."""
    a, b = lentas(m2022), lentas(m2026)
    todas = set(m2022) | set(m2026)
    return {
        "lentas_nos_dois": sorted(a & b),
        "so_2022": sorted(a - b),
        "so_2026": sorted(b - a),
        "rapidas_nos_dois": sorted(todas - a - b),
    }


def mediana_grupo(
    valores: Mapping[str, float | None], ufs: Sequence[str]
) -> float | None:
    xs = [valores[u] for u in ufs if valores.get(u) is not None]
    return round(statistics.median(xs), 2) if xs else None


def teste_fuso(
    m2022: Mapping[str, float | None], m2026: Mapping[str, float | None]
) -> dict[str, Any]:
    """Mediana do marco nas UFs fora de UTC-3 contra as demais, nos dois anos."""
    com = sorted(u for u in m2026 if fuso(u) != -3)
    sem = sorted(u for u in m2026 if fuso(u) == -3)
    return {
        "ufs_fora_de_brasilia": com,
        "mediana_2026_fora": mediana_grupo(m2026, com),
        "mediana_2026_brasilia": mediana_grupo(m2026, sem),
        "mediana_2022_fora": mediana_grupo(m2022, com),
        "mediana_2022_brasilia": mediana_grupo(m2022, sem),
        "fora_entre_as_lentas_2026": sorted(set(com) & lentas(m2026)),
        "fora_entre_as_lentas_2022": sorted(set(com) & lentas(m2022)),
    }


def maior_lacuna(tempos: Sequence[float], de: float, ate: float) -> dict[str, Any]:
    """Maior intervalo sem nenhum tempo dentro de [de, ate], em minutos."""
    xs = sorted(t for t in tempos if de <= t <= ate)
    if len(xs) < 2:
        return {"de": None, "ate": None, "minutos": None, "n": len(xs)}
    a, b = max(pairwise(xs), key=lambda p: p[1] - p[0])
    return {
        "de": round(a, 3),
        "ate": round(b, 3),
        "minutos": round(b - a, 3),
        "n": len(xs),
    }


def por_minuto(tempos: Sequence[float], de: int, ate: int) -> list[int]:
    """Contagem de tempos em cada minuto inteiro de `de` a `ate` (exclusivo)."""
    cont = [0] * (ate - de)
    for t in tempos:
        k = math.floor(t) - de
        if 0 <= k < len(cont):
            cont[k] += 1
    return cont


def hora(m: float | None) -> str | None:
    """Minutos desde as 17h para `HH:MM`, com `(+1)` depois da meia-noite."""
    if m is None:
        return None
    total = 17 * 60 + math.floor(m + 1e-9)
    dia, resto = divmod(total, 1440)
    h = f"{resto // 60:02d}:{resto % 60:02d}"
    return h + (f" (+{dia})" if dia else "")


def dentro(m: float | None, janela: tuple[float, float]) -> bool:
    return m is not None and janela[0] <= m <= janela[1]
