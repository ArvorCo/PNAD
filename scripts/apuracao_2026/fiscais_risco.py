"""Funções puras da camada de risco e contexto do território, por local de votação.

Tudo o que não lê disco nem rede fica aqui, para ser testado com fixtures
pequenas: decodificação do blob GeoPackage, distância em metros por projeção
local, ponto em polígono, quintil nacional, inferência declarada por palavra no
cadastro do TSE e a regra de crime organizado (só mapeamento público citado,
nunca inferido, nunca com nome de grupo).

Regra que atravessa o módulo: onde a base não cobre, o valor é ``None`` e sai
vazio no CSV. Zero e falso só existem quando a base cobre e mede ausência.
"""

from __future__ import annotations

import difflib
import math
import re
import struct
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry

RAIO_TERRA_M = 6_371_008.8
# Graus de longitude por quilômetro no ponto mais austral do Brasil (33,75° S),
# o pior caso; serve de pré-filtro folgado antes da distância exata em metros.
GRAUS_POR_KM_FOLGADO = 1.0 / (111.32 * math.cos(math.radians(34.0)))

SEM_MAPEAMENTO = "sem mapeamento público"
COM_MAPEAMENTO = "mapeamento público"
TEMAS_CRIME = ("faccao_milicia", "coercao", "violencia")

# Palavras do endereço e do bairro que marcam zona rural quando o setor
# censitário não cobre o local. Inferência declarada, nunca medição.
PALAVRAS_RURAIS = (
    "ZONA RURAL",
    "POVOADO",
    "SITIO",
    "FAZENDA",
    "ASSENTAMENTO",
    "COMUNIDADE",
    "RAMAL",
    "GLEBA",
    "LOCALIDADE",
    "AREA RURAL",
)


def normalizar(texto: str | None) -> str:
    """Maiúsculas sem acento, pontuação vira espaço, espaços colapsados."""
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    sem_acento = re.sub(r"[^A-Za-z0-9]+", " ", sem_acento.upper())
    return " ".join(sem_acento.split())


def _padrao(palavras: Sequence[str]) -> re.Pattern[str]:
    """Qualquer das palavras, inteira."""
    corpo = "|".join(re.escape(p) for p in sorted(palavras, key=len, reverse=True))
    return re.compile(rf"\b(?:{corpo})\b")


_RE_RURAL = _padrao(PALAVRAS_RURAIS)
# Palavras da regra (PRESIDIO, PENITENCIARIA, CADEIA, DETENCAO, PRISIONAL,
# CUSTODIA, RESSOCIALIZACAO, POLICIA PENAL, SOCIOEDUCATIV, FUNDACAO CASA,
# INTERNACAO PROVISORIA) viram expressões institucionais: "CUSTÓDIA" e
# "PRESÍDIO" também são nome de gente ("Escola Fernando Presídio", "Escola
# Custódia de Jesus"), e "Fundação Casa da Juventude" não é a Fundação CASA.
_RE_PRISIONAL = re.compile(
    r"^PRESIDIO\b|\b(?:DO|NO) PRESIDIO\b"
    r"|\bPRESIDIO (?:ESTADUAL|REGIONAL|FEDERAL|FEMININO|MASCULINO|DE|DO|DA)\b"
    r"|\bPENITENCIARI|^CADEIA\b|\bCADEIA PUBLICA\b"
    r"|\b(?:CENTRO|CASA) DE DETENCAO\b|\bDETENCAO PROVISORIA\b|\bPRISIONAL\b"
    r"|\bPRISAO PROVISORIA\b|\b(?:CONJUNTO|UNIDADE) PENAL\b"
    r"|\b(?:CENTRO|CASA|UNIDADE) DE CUSTODIA\b|\bCUSTODIA PROVISORIA\b"
    r"|\bRESSOCIALIZACAO\b|\bPOLICIA PENAL\b|\bSOCIO ?EDUCATIV"
    r"|\bFUNDACAO CASA\b(?! D[AEO]\b)|\bINTERNACAO PROVISORIA\b"
    r"|\bUNIDADE DE INTERNACAO\b"
)
_RE_INDIGENA_FORTE = re.compile(r"\bINDIGENA|\bTERRA INDIG")
_RE_ALDEIA = re.compile(r"\bALDEIA")
_RE_QUILOMBOLA = re.compile(r"\bQUILOMBOLA")
_RE_QUILOMBO = re.compile(r"\bQUILOMBO\b")


def palavra_encontrada(padrao: re.Pattern[str], *textos: str | None) -> str | None:
    """Primeira palavra-chave achada nos textos normalizados, ou None."""
    for t in textos:
        m = padrao.search(normalizar(t))
        if m:
            return m.group(0)
    return None


def rural_por_cadastro(endereco: str | None, bairro: str | None) -> str | None:
    """Palavra rural do endereço ou do bairro; None quando nada indica."""
    return palavra_encontrada(_RE_RURAL, endereco, bairro)


def prisional_por_nome(local: str | None) -> str | None:
    """Expressão institucional de unidade prisional ou socioeducativa no nome."""
    return palavra_encontrada(_RE_PRISIONAL, local)


def indigena_por_nome(local: str | None, urbano: bool) -> str | None:
    """INDIGENA ou TERRA INDIG no nome; ALDEIA só fora de setor urbano.

    ALDEIA é também topônimo e nome fantasia urbano ("São Pedro da Aldeia",
    "Aldeias Infantis SOS"); fora da cidade a palavra indica aldeia de fato.
    """
    forte = palavra_encontrada(_RE_INDIGENA_FORTE, local)
    if forte or urbano:
        return forte
    return palavra_encontrada(_RE_ALDEIA, local)


def quilombola_por_nome(local: str | None, urbano: bool) -> str | None:
    """QUILOMBOLA no nome; QUILOMBO só fora de setor urbano (é topônimo)."""
    forte = palavra_encontrada(_RE_QUILOMBOLA, local)
    if forte or urbano:
        return forte
    return palavra_encontrada(_RE_QUILOMBO, local)


# Tamanho do envelope do GeoPackage pelo indicador dos bits 1 a 3 das flags.
_ENVELOPE_BYTES = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def gpkg_para_wkb(blob: bytes) -> tuple[int, bytes]:
    """Separa o cabeçalho GeoPackageBinary e devolve (srs_id, WKB).

    Cabeçalho: ``"GP"``, versão (1 byte), flags (1 byte), srs_id (int32 na
    ordem de bytes do bit 0 das flags), envelope de 0, 32, 48 ou 64 bytes
    conforme os bits 1 a 3. O que sobra é WKB padrão.
    """
    if len(blob) < 8 or blob[:2] != b"GP":
        raise ValueError("blob sem a assinatura GP do GeoPackage")
    flags = blob[3]
    if flags & 0b0010_0000:
        raise ValueError("ExtendedGeoPackageBinary não suportado")
    ordem = "<" if flags & 1 else ">"
    indicador = (flags >> 1) & 0b111
    if indicador not in _ENVELOPE_BYTES:
        raise ValueError(f"indicador de envelope inválido: {indicador}")
    srs_id = struct.unpack(f"{ordem}i", blob[4:8])[0]
    inicio = 8 + _ENVELOPE_BYTES[indicador]
    return srs_id, bytes(blob[inicio:])


def gpkg_para_geom(blob: bytes) -> BaseGeometry:
    return shapely.from_wkb(gpkg_para_wkb(blob)[1])


def projetar_em_metros(geom: BaseGeometry, lat0: float, lon0: float) -> BaseGeometry:
    """Projeção equiretangular centrada no ponto (lat0, lon0), em metros.

    Para raios de até algumas dezenas de quilômetros o erro fica na casa das
    dezenas de metros, que é a precisão pedida pela camada.
    """
    kx = RAIO_TERRA_M * math.cos(math.radians(lat0)) * math.pi / 180.0
    ky = RAIO_TERRA_M * math.pi / 180.0

    def _f(xy: np.ndarray) -> np.ndarray:
        out = np.empty_like(xy)
        out[:, 0] = (xy[:, 0] - lon0) * kx
        out[:, 1] = (xy[:, 1] - lat0) * ky
        return out

    return shapely.transform(geom, _f)


def distancia_km(lat: float, lon: float, geom: BaseGeometry) -> float:
    """Distância do ponto à geometria em km; zero dentro do polígono."""
    if shapely.intersects_xy(geom, lon, lat):
        return 0.0
    proj = projetar_em_metros(geom, lat, lon)
    return float(shapely.distance(shapely.Point(0.0, 0.0), proj)) / 1000.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RAIO_TERRA_M * math.asin(math.sqrt(a)) / 1000.0


def mais_proximo(
    lat: float,
    lon: float,
    candidatos: Iterable[tuple[Any, BaseGeometry]],
    raio_km: float,
) -> tuple[Any, float] | None:
    """O candidato mais próximo dentro do raio, com a distância em km."""
    melhor: tuple[Any, float] | None = None
    for chave, geom in candidatos:
        d = distancia_km(lat, lon, geom)
        if d <= raio_km and (melhor is None or d < melhor[1]):
            melhor = (chave, d)
    return melhor


def pares_no_raio(
    lats: np.ndarray, lons: np.ndarray, geoms: Sequence[BaseGeometry], raio_km: float
) -> dict[int, list[int]]:
    """Índice do ponto -> índices das geometrias a até ``raio_km`` (pré-filtro).

    Usa a árvore STR com distância em graus folgada (pior caso de latitude); a
    distância exata em metros vem depois, em ``mais_proximo``.
    """
    if len(geoms) == 0 or len(lats) == 0:
        return {}
    arvore = shapely.STRtree(list(geoms))
    pontos = shapely.points(lons, lats)
    ip, ig = arvore.query(
        pontos, predicate="dwithin", distance=raio_km * GRAUS_POR_KM_FOLGADO
    )
    saida: dict[int, list[int]] = {}
    for p, g in zip(ip.tolist(), ig.tolist(), strict=True):
        saida.setdefault(p, []).append(g)
    return saida


def quintis(valores: Mapping[Any, float | None]) -> dict[Any, int | None]:
    """Quintil nacional (1 a 5, 5 = maior) sobre as chaves com valor.

    Cortes nos percentis 20, 40, 60 e 80 (interpolação linear do numpy); o
    quintil é 1 mais o número de cortes que o valor supera estritamente. Chave
    sem valor fica ``None``, nunca 1.
    """
    com_valor = [float(v) for v in valores.values() if v is not None]
    if not com_valor:
        return dict.fromkeys(valores)
    cortes = np.quantile(np.array(com_valor), [0.2, 0.4, 0.6, 0.8])
    saida: dict[Any, int | None] = {}
    for k, v in valores.items():
        saida[k] = None if v is None else 1 + int(np.sum(float(v) > cortes))
    return saida


def crime_organizado(itens: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    """Valor e fontes do campo ``crime_organizado`` de um município.

    Só conta item com fonte (id e url). Nunca nomeia grupo: a saída é a
    expressão fixa e a lista de fontes, "id (tema), veículo, data, url".
    """
    validos = [i for i in itens if i.get("id") and i.get("url")]
    if not validos:
        return SEM_MAPEAMENTO, ""
    partes = []
    for i in sorted(validos, key=lambda x: str(x["id"])):
        data = i.get("data") or "sem data"
        partes.append(
            f"{i['id']} ({i.get('tema', '')}), {i.get('veiculo', '')}, {data}, "
            f"{i['url']}"
        )
    return COM_MAPEAMENTO, " | ".join(partes)


# Abreviações usadas em relatórios e ausentes do cadastro do TSE.
ABREVIACOES = (("GOV ", "GOVERNADOR "), ("STA ", "SANTA "), ("STO ", "SANTO "))


def casar_municipio(
    uf: str, nome: str, indice: Mapping[tuple[str, str], str], corte: float = 0.85
) -> tuple[str | None, str]:
    """Código TSE do município pelo nome, dentro da UF.

    Ordem: nome normalizado exato, abreviação expandida, semelhança de
    ``difflib`` acima do corte (registrada como ``aproximado``). Sem casamento,
    ``(None, "sem_casamento")``; nunca escolhe município de outra UF.
    """
    uf = uf.upper()
    alvo = normalizar(nome)
    if (uf, alvo) in indice:
        return indice[(uf, alvo)], "exato"
    expandido = alvo
    for curto, longo in ABREVIACOES:
        if expandido.startswith(curto):
            expandido = longo + expandido[len(curto) :]
    if (uf, expandido) in indice:
        return indice[(uf, expandido)], "abreviacao"
    nomes_uf = [n for (u, n) in indice if u == uf]
    perto = difflib.get_close_matches(expandido, nomes_uf, n=1, cutoff=corte)
    if perto:
        return indice[(uf, perto[0])], f"aproximado: {perto[0]}"
    return None, "sem_casamento"


def local_id(uf: str, mun_tse: str, zona: int, local_nr: int | None, secao=None):
    """``"UF-MUNTSE-ZONA-LOCALNR"``; sem número de local, ``s<secao>``."""
    fim = str(local_nr) if local_nr is not None else f"s{secao}"
    return f"{uf.upper()}-{str(mun_tse).zfill(5)}-{int(zona)}-{fim}"


def decimal(texto: str | None) -> float | None:
    """Número com ponto ou vírgula decimal (os CSV do IBGE misturam os dois)."""
    if texto is None or not str(texto).strip():
        return None
    t = str(texto).strip()
    if "," in t and "." not in t:
        t = t.replace(",", ".")
    return float(t)


def fmt_flag(valor: bool | int | None) -> str:
    """1, 0 ou vazio; ``None`` nunca vira zero."""
    if valor is None:
        return ""
    return "1" if valor else "0"


def fmt_num(valor: float | int | None, casas: int = 3) -> str:
    if valor is None:
        return ""
    if isinstance(valor, int):
        return str(valor)
    return f"{valor:.{casas}f}"


def fmt_txt(valor: Any) -> str:
    return "" if valor is None else str(valor)
