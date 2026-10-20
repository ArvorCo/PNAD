"""Grade de células e leitura dos locais de votação com coordenada.

A célula de uma coordenada é ``(floor(lat / passo), floor(lon / passo))``; o ponto
consultado na Open-Meteo é o centro dela. A chave textual é o canto sudoeste com
duas casas (0,25°, ex.: ``-23.75,-46.75``) ou uma casa (0,5°, ex.: ``-24.0,-47.0``),
o mesmo texto que o app do mapa calcula a partir de lat/lon.
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAIS_DB = ROOT / "data/outputs/locais_votacao_2026.sqlite"

# Caixa do território (Brasil, com ilhas oceânicas), a mesma do mapa de fiscais.
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -34.0, 5.5, -74.5, -28.5
PASSO_ARCHIVE = 0.25
PASSO_PREVISAO = 0.5


def no_territorio(lat: float | None, lon: float | None) -> bool:
    """Coordenada numérica dentro da caixa do território."""
    if lat is None or lon is None:
        return False
    if not (math.isfinite(lat) and math.isfinite(lon)):
        return False
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


def _fator(passo: float) -> int:
    k = round(1 / passo)
    if not math.isclose(k * passo, 1.0):
        raise ValueError(f"passo sem divisor inteiro de 1 grau: {passo}")
    return k


def indice(lat: float, lon: float, passo: float) -> tuple[int, int]:
    """Índices inteiros da célula (multiplicação por potência de 2 é exata)."""
    k = _fator(passo)
    return math.floor(lat * k), math.floor(lon * k)


def casas_da_chave(passo: float) -> int:
    return 1 if passo >= 0.5 else 2


def chave(lat: float, lon: float, passo: float) -> str:
    """Chave da célula: canto sudoeste com casas fixas."""
    k = _fator(passo)
    i, j = indice(lat, lon, passo)
    c = casas_da_chave(passo)
    return f"{i / k:.{c}f},{j / k:.{c}f}"


def centro(chave_cel: str, passo: float) -> tuple[float, float]:
    """Centro da célula a partir da chave."""
    a, b = (float(x) for x in chave_cel.split(","))
    return round(a + passo / 2, 4), round(b + passo / 2, 4)


def arquivo_da_chave(chave_cel: str) -> str:
    """Nome de arquivo estável para a resposta crua de uma célula."""
    return chave_cel.replace(",", "_") + ".json"


def local_id(uf: str, mun: str, zona: int, local_nr: int) -> str:
    """Identificador do local no mapa de fiscais: ``UF-MUNTSE-ZONA-LOCALNR``."""
    return f"{uf}-{mun}-{int(zona)}-{int(local_nr)}"


@dataclass
class Local:
    local_id: str
    uf: str
    mun: str
    municipio: str
    zona: int
    local_nr: int
    nome: str
    lat: float | None
    lon: float | None
    secoes: int
    eleitores: int

    @property
    def tem_coordenada(self) -> bool:
        return self.lat is not None


def ler_locais(
    caminho: Path = LOCAIS_DB, incluir_exterior: bool = False
) -> list[Local]:
    """Um registro por local de votação (UF, município, zona, número do local).

    Coordenada fora do território vira ``None``: o motor não inventa posição.
    """
    sql = """
        SELECT uf, municipio_cd, municipio, zona, local_nr, MIN(local),
               MIN(lat), MIN(lon), COUNT(*), SUM(COALESCE(eleitores, 0))
        FROM secao
        GROUP BY uf, municipio_cd, zona, local_nr
        ORDER BY uf, municipio_cd, zona, local_nr
    """
    with sqlite3.connect(caminho) as con:
        linhas = con.execute(sql).fetchall()
    saida = []
    for uf, mun, municipio, zona, nr, nome, lat, lon, n, el in linhas:
        if uf == "ZZ" and not incluir_exterior:
            continue
        ok = no_territorio(lat, lon)
        saida.append(
            Local(
                local_id=local_id(uf, mun, zona, nr),
                uf=uf,
                mun=mun,
                municipio=municipio,
                zona=int(zona),
                local_nr=int(nr),
                nome=nome or "",
                lat=float(lat) if ok else None,
                lon=float(lon) if ok else None,
                secoes=int(n),
                eleitores=int(el),
            )
        )
    return saida


def celulas(locais: list[Local], passo: float) -> dict[str, tuple[float, float]]:
    """Chaves das células com ao menos um local, com o centro de cada uma."""
    chaves = sorted(
        {
            chave(lc.lat, lc.lon, passo)
            for lc in locais
            if lc.lat is not None and lc.lon is not None
        }
    )
    return {c: centro(c, passo) for c in chaves}
