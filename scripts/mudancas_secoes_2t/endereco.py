"""Normalização de nome e endereço de local de votação, e distância na esfera.

A comparação separa edição de cadastro (acento, abreviação, número acrescentado,
complemento) de troca de prédio. Regra declarada no contrato: maiúsculas, sem
acento, sem pontuação, abreviações expandidas (``R.`` vira ``RUA``, ``AV.`` vira
``AVENIDA``), marcador de número (``N.``, ``Nº``) removido, complemento depois de
`` - `` separado do logradouro. Como há cadastros que põem a localidade antes do
logradouro (``JATOBA - PRACA DO COMERCIO - ZONA RURAL``), cada parte separada por
`` - `` é candidata a logradouro, e duas grafias são o mesmo logradouro quando as
palavras significativas da menor estão todas na maior.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

import numpy as np

RAIO_TERRA_M = 6_371_008.8

ABREVIACOES = {
    "R": "RUA",
    "RUA": "RUA",
    "AV": "AVENIDA",
    "AVN": "AVENIDA",
    "AVEN": "AVENIDA",
    "PC": "PRACA",
    "PCA": "PRACA",
    "PRC": "PRACA",
    "PRACA": "PRACA",
    "TV": "TRAVESSA",
    "TRAV": "TRAVESSA",
    "TR": "TRAVESSA",
    "EST": "ESTRADA",
    "ESTR": "ESTRADA",
    "ROD": "RODOVIA",
    "AL": "ALAMEDA",
    "POV": "POVOADO",
    "LOC": "LOCALIDADE",
    "DR": "DOUTOR",
    "PROF": "PROFESSOR",
    "PROFA": "PROFESSORA",
    "STA": "SANTA",
    "STO": "SANTO",
    "SAO": "SAO",
    "QD": "QUADRA",
    "LT": "LOTE",
}
# Palavras que não identificam o logradouro (tipo, conectivo, marcador).
GENERICAS = frozenset(
    {
        "RUA",
        "AVENIDA",
        "PRACA",
        "TRAVESSA",
        "ESTRADA",
        "RODOVIA",
        "ALAMEDA",
        "SERVIDAO",
        "VIA",
        "LARGO",
        "BECO",
        "POVOADO",
        "LOCALIDADE",
        "COMUNIDADE",
        "DISTRITO",
        "BAIRRO",
        "ZONA",
        "RURAL",
        "URBANA",
        "RUAL",
        "SITIO",
        "FAZENDA",
        "CENTRO",
        "DE",
        "DA",
        "DO",
        "DAS",
        "DOS",
        "E",
        "A",
        "O",
        "AS",
        "OS",
        "EM",
        "COM",
        "SN",
        "S",
        "N",
        "NO",
        "NUM",
        "NUMERO",
        "KM",
        "CEP",
        "ESQUINA",
        "ANTIGO",
        "ANTIGA",
        "PROXIMO",
        "AO",
        "QUADRA",
        "LOTE",
    }
)
_PONTUACAO = re.compile(r"[^A-Z0-9 ]+")
_ESPACOS = re.compile(r"\s+")
_PARENTESES = re.compile(r"\([^)]*\)?")
_CEP = re.compile(r"\bCEP\b[\s.:]*[0-9][0-9.\- ]*")
_SN = re.compile(r"\bS\s*/\s*N[º°O.]*|\bS\s*N\b\.?|\bSN\b")
_MARCADOR_N = re.compile(r"\bN(?:[º°O]|UM(?:ERO)?)?\b\.?\s*(?=[0-9])|\bN[º°]")


def sem_acento(texto: object) -> str:
    if not isinstance(texto, str):
        return ""
    n = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in n if not unicodedata.combining(c)).upper()


def palavras(texto: str) -> list[str]:
    """Texto em maiúsculas, sem acento e sem pontuação, com abreviações expandidas."""
    t = sem_acento(texto).replace("¿", " ")
    t = _PONTUACAO.sub(" ", t)
    return [ABREVIACOES.get(p, p) for p in _ESPACOS.sub(" ", t).strip().split(" ") if p]


def normalizar_nome(nome: str) -> str:
    return " ".join(palavras(nome))


@dataclass(frozen=True)
class Endereco:
    """Endereço normalizado: partes separadas por `` - ``, logradouro e número."""

    partes: tuple[tuple[str, ...], ...]
    logradouro: tuple[str, ...]
    numero: str | None

    @property
    def significativas(self) -> frozenset[str]:
        return frozenset(_significativas(self.logradouro))

    @property
    def todas(self) -> frozenset[str]:
        return frozenset(p for parte in self.partes for p in _significativas(parte))


def _significativas(tokens: tuple[str, ...]) -> list[str]:
    return [t for t in tokens if t not in GENERICAS and not t.isdigit()]


def _logradouro_e_numero(tokens: list[str]) -> tuple[tuple[str, ...], str | None]:
    """Logradouro = palavras antes do primeiro número; número sem zeros à esquerda."""
    for i, t in enumerate(tokens):
        if t.isdigit():
            # rodovia e quadra levam número no nome (BR 116, QD 310)
            if i > 0 and tokens[i - 1] in {"BR", "RODOVIA", "KM", "QUADRA"}:
                continue
            return tuple(tokens[:i]), t.lstrip("0") or "0"
    return tuple(tokens), None


def normalizar_endereco(endereco: str) -> Endereco:
    t = sem_acento(endereco).replace("¿", " ")
    t = _PARENTESES.sub(" ", t)
    t = _CEP.sub(" ", t)
    t = _SN.sub(" ", t)
    t = _MARCADOR_N.sub(" ", t)
    brutas = [p for p in re.split(r"\s+-\s+|\s+-(?=\S)|(?<=\S)-\s+", t) if p.strip()]
    partes: list[tuple[str, ...]] = []
    for bruta in brutas:
        # o logradouro termina na primeira vírgula; o resto é número ou bairro
        tokens = palavras(bruta)
        if tokens:
            partes.append(tuple(tokens))
    if not partes:
        return Endereco((), (), None)
    primeira = palavras(brutas[0].split(",")[0]) if brutas else []
    logradouro, numero = _logradouro_e_numero(list(partes[0]))
    if primeira and len(primeira) < len(logradouro):
        logradouro = tuple(primeira)
    return Endereco(tuple(partes), logradouro, numero)


def _contido(a: frozenset[str], b: frozenset[str]) -> bool:
    if not a or not b:
        return False
    menor, maior = (a, b) if len(a) <= len(b) else (b, a)
    return menor <= maior


def mesmo_logradouro(e1: str, e2: str) -> bool:
    """Mesmo logradouro, tolerando abreviação, complemento e localidade acrescentada."""
    a, b = normalizar_endereco(e1), normalizar_endereco(e2)
    if a.logradouro and a.logradouro == b.logradouro:
        return True
    sa, sb = a.significativas, b.significativas
    if _contido(sa, sb):
        return True
    # localidade antes do logradouro: o logradouro de um é uma das partes do outro
    partes_a = {frozenset(_significativas(p)) for p in a.partes} - {frozenset()}
    partes_b = {frozenset(_significativas(p)) for p in b.partes} - {frozenset()}
    if sa and any(_contido(sa, p) for p in partes_b):
        return True
    if sb and any(_contido(sb, p) for p in partes_a):
        return True
    return _contido(a.todas, b.todas)


def mesmo_endereco(e1: str, e2: str) -> bool:
    """Mesmo logradouro e, quando os dois têm número, o mesmo número."""
    if not mesmo_logradouro(e1, e2):
        return False
    n1 = normalizar_endereco(e1).numero
    n2 = normalizar_endereco(e2).numero
    return n1 is None or n2 is None or n1 == n2


def semelhanca_nomes(n1: str, n2: str) -> float:
    """Jaccard das palavras significativas dos dois nomes (0 a 1)."""
    a = {p for p in palavras(n1) if p not in GENERICAS and len(p) > 1}
    b = {p for p in palavras(n2) if p not in GENERICAS and len(p) > 1}
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def haversine_m(
    lat1: float | None, lon1: float | None, lat2: float | None, lon2: float | None
) -> float | None:
    """Distância em metros na esfera de raio médio; ``None`` sem coordenada."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    if any(math.isnan(float(x)) for x in (lat1, lon1, lat2, lon2)):
        return None
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RAIO_TERRA_M * math.asin(min(1.0, math.sqrt(a)))


def haversine_vetor(
    lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray
) -> np.ndarray:
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * RAIO_TERRA_M * np.arcsin(np.minimum(1.0, np.sqrt(a)))
