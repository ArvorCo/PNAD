"""Horas do boletim de urna em minutos desde a meia-noite de Brasília do dia do turno.

O BU traz a hora local da urna, sem fuso. A conversão soma o fuso da UF e corrige, por
município, a hora mais frequente de abertura: a votação abre às 8h de Brasília no país
inteiro, então um município cuja abertura modal cai uma hora antes da esperada está num
fuso diferente do da UF (oeste do Amazonas). Mesma regra de
``apuracao_2t_2026.secoes_fonte``. O exterior (``ZZ``) fica na hora local da cidade.
"""

from __future__ import annotations

from datetime import datetime
from statistics import multimode

# minutos a somar à hora local para chegar a Brasília
FUSO_PARA_BRASILIA = {"AC": 120, "AM": 60, "RO": 60, "RR": 60, "MT": 60, "MS": 60}
ABERTURA_BRASILIA = 8 * 60


def minutos_locais(texto: str | None, dia: str) -> int | None:
    """``"aaaa-mm-dd hh:mm:ss"`` → minutos desde a meia-noite de ``dia`` (sem fuso)."""
    if not texto:
        return None
    try:
        t = datetime.strptime(texto[:19], "%Y-%m-%d %H:%M:%S")
        d = datetime.strptime(dia, "%Y-%m-%d")
    except ValueError:
        return None
    return int((t - d).total_seconds() // 60)


def para_brasilia(minutos: int | None, uf: str, correcao: int = 0) -> int | None:
    if minutos is None:
        return None
    if uf == "ZZ":
        return minutos
    return minutos + FUSO_PARA_BRASILIA.get(uf, 0) + correcao


def correcoes_municipais(uf: str, aberturas: dict[str, list[int]]) -> dict[str, int]:
    """Por município, minutos a somar depois do fuso da UF (0 quase sempre).

    ``aberturas``: município → aberturas já convertidas pelo fuso da UF.
    """
    if uf == "ZZ":
        return {}
    out: dict[str, int] = {}
    for mun, lista in aberturas.items():
        desvios = [round((a - ABERTURA_BRASILIA) / 60) for a in lista if a is not None]
        if not desvios:
            continue
        moda = min(multimode(desvios), key=abs)
        if moda:
            out[mun] = -60 * moda
    return out


def hhmm(minutos: int | None) -> str | None:
    """Minutos desde a meia-noite → ``"hh:mm"``, com ``" do dia seguinte"`` depois de 24h."""
    if minutos is None:
        return None
    dias, resto = divmod(int(minutos), 1440)
    s = f"{resto // 60:02d}h{resto % 60:02d}"
    return f"{s} do dia seguinte" if dias > 0 else s
