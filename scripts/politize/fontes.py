"""Leitura das fontes do Politize sua vizinhança.

Toda leitura é somente leitura e em fluxo. Os bancos SQLite abrem com
``file:...?mode=ro``; os CSV grandes (perfil do eleitorado, 2022) são lidos linha a
linha de dentro do ZIP, sem extrair para o disco. Os resultados caros ficam em cache
em ``analysis/politize/cache/`` (ignorado pelo git), com a assinatura (bytes e data)
do arquivo de origem para invalidar quando ele muda.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import sqlite3
import unicodedata
import zipfile
import zlib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import shapely

ROOT = Path(__file__).resolve().parents[2]
DB_SECOES = ROOT / "apuracao/data/secoes_2026.sqlite"
DB_LOCAIS = ROOT / "data/outputs/locais_votacao_2026.sqlite"
DB_APURACAO = ROOT / "apuracao/data/apuracao.sqlite"
CSV_2022 = ROOT / "data/outputs/presidente_secao_2022.csv.gz"
ZIP_DETALHE_2022 = ROOT / "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip"
DIR_PERFIL_SECAO = ROOT / "data/raw/tse_eleitorado/perfil_eleitor_secao"
ZIP_PERFIL_ZONA = ROOT / "data/raw/tse_eleitorado/perfil_eleitorado_2026.zip"
GPKG_SETORES = ROOT / "data/raw/ibge_setores_2022/BR_setores_CD2022.gpkg"
CSV_AGREGADOS = (
    ROOT
    / "data/originals/censo_2022_setores_censitarios/Agregados_por_setores_basico_BR.csv"
)
CSV_PNAD = ROOT / "data/outputs/base_anual_visita1_labeled_npv.csv"
CSV_IPCA = ROOT / "data/outputs/ipca.csv"
CSV_SALARIO = ROOT / "data/originals/salario_minimo.csv"
DIR_PESQUISAS = ROOT / "analysis/reponderacao/pesquisas"
PESQUISAS = ("datafolha_2026-10-03.json", "quaest_2026-10-03.json")
JSON_PROBLEMAS = ROOT / "analysis/voto_util/problemas_quaest_092026.json"
JSON_MIGRACAO = ROOT / "analysis/predicao_2026/tendencia/migracao_declarada.json"
DIR_MALHA = ROOT / "apuracao/public/geo/mun"
JSON_CIDADES_EXTERIOR = ROOT / "apuracao/public/geo/exterior_cidades.json"
GEO_MUNDO = ROOT / "apuracao/public/geo/mundo.geojson"
CACHE = ROOT / "analysis/politize/cache"
SAIDA = ROOT / "docs/assets/politize/dados"

ELEICAO_FEDERAL = 6257
NUM_FLAVIO = 22
NUM_LULA = 13
TABELA_SETORES = "BR_setores_CD2022"

# sigla: (nome, região, código IBGE da UF)
UFS: dict[str, tuple[str, str, str | None]] = {
    "AC": ("Acre", "Norte", "12"),
    "AL": ("Alagoas", "Nordeste", "27"),
    "AM": ("Amazonas", "Norte", "13"),
    "AP": ("Amapá", "Norte", "16"),
    "BA": ("Bahia", "Nordeste", "29"),
    "CE": ("Ceará", "Nordeste", "23"),
    "DF": ("Distrito Federal", "Centro-Oeste", "53"),
    "ES": ("Espírito Santo", "Sudeste", "32"),
    "GO": ("Goiás", "Centro-Oeste", "52"),
    "MA": ("Maranhão", "Nordeste", "21"),
    "MG": ("Minas Gerais", "Sudeste", "31"),
    "MS": ("Mato Grosso do Sul", "Centro-Oeste", "50"),
    "MT": ("Mato Grosso", "Centro-Oeste", "51"),
    "PA": ("Pará", "Norte", "15"),
    "PB": ("Paraíba", "Nordeste", "25"),
    "PE": ("Pernambuco", "Nordeste", "26"),
    "PI": ("Piauí", "Nordeste", "22"),
    "PR": ("Paraná", "Sul", "41"),
    "RJ": ("Rio de Janeiro", "Sudeste", "33"),
    "RN": ("Rio Grande do Norte", "Nordeste", "24"),
    "RO": ("Rondônia", "Norte", "11"),
    "RR": ("Roraima", "Norte", "14"),
    "RS": ("Rio Grande do Sul", "Sul", "43"),
    "SC": ("Santa Catarina", "Sul", "42"),
    "SE": ("Sergipe", "Nordeste", "28"),
    "SP": ("São Paulo", "Sudeste", "35"),
    "TO": ("Tocantins", "Norte", "17"),
    "ZZ": ("Exterior", "Exterior", None),
}
UF_POR_CODIGO = {cod: sigla for sigla, (_, _, cod) in UFS.items() if cod}

SecaoKey = tuple[str, int, int]  # (mun_tse, zona, secao)
LocalKey = tuple[str, int, int]  # (mun_tse, zona, local_nr)

# --------------------------------------------------------------- utilidades


def abrir_ro(caminho: Path) -> sqlite3.Connection:
    if not caminho.exists():
        raise FileNotFoundError(caminho)
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def rel(caminho: Path) -> str:
    try:
        return str(caminho.resolve().relative_to(ROOT))
    except ValueError:
        return str(caminho)


def assinatura(caminho: Path) -> list[int]:
    st = caminho.stat()
    return [st.st_size, st.st_mtime_ns]


def ler_cache(nome: str, sig: Any) -> Any | None:
    arq = CACHE / nome
    if not arq.exists():
        return None
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if dados.get("sig") != sig:
        return None
    return dados.get("dados")


def gravar_cache(nome: str, sig: Any, dados: Any) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / nome).write_text(
        json.dumps({"sig": sig, "dados": dados}, ensure_ascii=False),
        encoding="utf-8",
    )


def sha256(caminho: Path) -> str:
    """SHA-256 do arquivo, com cache por (bytes, data de modificação)."""
    sig = assinatura(caminho)
    chave = f"sha256_{hashlib.sha1(rel(caminho).encode()).hexdigest()[:16]}.json"
    guardado = ler_cache(chave, sig)
    if guardado:
        return str(guardado)
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 22), b""):
            h.update(bloco)
    valor = h.hexdigest()
    gravar_cache(chave, sig, valor)
    return valor


def descrever_fonte(chave: str, caminho: Path, uso: str) -> dict[str, Any]:
    st = caminho.stat()
    return {
        "chave": chave,
        "caminho": rel(caminho),
        "bytes": st.st_size,
        "sha256": sha256(caminho),
        "modificado_em": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "uso": uso,
    }


def sem_acento(texto: str) -> str:
    n = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in n if not unicodedata.combining(c))


_MINUSCULAS = {"de", "da", "do", "das", "dos", "e", "del", "di", "du", "la", "le"}


def caixa_normal(nome: str) -> str:
    """Nome em caixa normal: ``"SÃO JOÃO DEL REI"`` vira ``"São João del Rei"``."""
    partes = []
    for i, palavra in enumerate(nome.strip().lower().split()):
        if i > 0 and palavra in _MINUSCULAS:
            partes.append(palavra)
            continue
        sub = palavra.split("-")
        partes.append("-".join(s[:1].upper() + s[1:] for s in sub))
    return " ".join(partes)


# ------------------------------------------------------------- municípios


@dataclass(frozen=True)
class Municipio:
    uf: str
    mun_tse: str
    ibge: str | None
    nome_tse: str
    capital: bool


def municipios() -> dict[str, Municipio]:
    """Município TSE (5 dígitos) com UF, código IBGE e nome do cadastro do TSE."""
    con = abrir_ro(DB_APURACAO)
    try:
        rows = con.execute(
            "SELECT cd, uf, ibge, nome, capital FROM municipio"
        ).fetchall()
    finally:
        con.close()
    saida = {}
    for cd, uf, ibge, nome, capital in rows:
        mun = str(cd).zfill(5)
        saida[mun] = Municipio(
            uf=str(uf).upper(),
            mun_tse=mun,
            ibge=str(ibge) if ibge else None,
            nome_tse=str(nome or ""),
            capital=bool(capital),
        )
    return saida


def nomes_ibge() -> dict[str, list[str]]:
    """Por código IBGE: ``[nome do município, nome do distrito-sede]`` do Censo 2022.

    O distrito-sede (``CD_DIST`` = município + ``05``) serve de conferência: o arquivo
    de agregados (e a malha) trazem ``Unas`` para o município 2932507, cujo distrito
    sede e o cadastro do TSE dizem ``Una``.
    """
    sig = [*assinatura(CSV_AGREGADOS), "v2"]
    guardado = ler_cache("nomes_ibge.json", sig)
    if guardado is not None:
        return dict(guardado)
    nomes: dict[str, list[str]] = {}
    with CSV_AGREGADOS.open(encoding="latin-1", newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        cab = next(leitor)
        i_cd, i_nm = cab.index("CD_MUN"), cab.index("NM_MUN")
        i_dist, i_nd = cab.index("CD_DIST"), cab.index("NM_DIST")
        for linha in leitor:
            cd = linha[i_cd]
            reg = nomes.setdefault(cd, [linha[i_nm].strip(), ""])
            if not reg[1] and linha[i_dist] == cd + "05":
                reg[1] = linha[i_nd].strip()
    gravar_cache("nomes_ibge.json", sig, nomes)
    return nomes


def normalizar_nome(texto: str) -> str:
    """Comparação de nomes sem acento, caixa, apóstrofo nem hífen."""
    t = sem_acento(texto).upper().replace("'", "").replace("-", " ")
    return " ".join(t.split())


def numeros_presidente() -> set[int]:
    """Números da lista oficial de candidaturas a presidente (eleição 6257)."""
    con = abrir_ro(DB_APURACAO)
    try:
        rows = con.execute(
            "SELECT numero FROM candidato WHERE eleicao_cd = ? AND cargo_cd = 1",
            (ELEICAO_FEDERAL,),
        ).fetchall()
    finally:
        con.close()
    numeros = {int(r[0]) for r in rows if r[0] is not None}
    if NUM_FLAVIO not in numeros or NUM_LULA not in numeros:
        raise ValueError("lista de candidaturas a presidente sem 22 ou 13")
    return numeros


# --------------------------------------------------------------- votos 2026

# Índices do vetor de votos por seção.
(
    V_APTOS,
    V_COMP,
    V_FLAVIO,
    V_LULA,
    V_TERCEIRA,
    V_BRANCOS,
    V_NULOS,
    V_FORA,
    V_CURY,
    V_RENAN,
    V_CAIADO,
    V_ZEMA,
) = range(12)
# Terceira via separada por candidatura (número na urna); o resto vai a outros_nominais.
TERCEIRA_NOMEADA = {70: V_CURY, 14: V_RENAN, 55: V_CAIADO, 30: V_ZEMA}


def votos_uf(uf: str, numeros: set[int]) -> tuple[dict[SecaoKey, list[int]], dict]:
    """Presidente, 1º turno, por seção principal com boletim de urna.

    Seção agregada já vem somada na principal. Voto nominal em número fora da lista
    oficial de candidaturas conta como nulo, como na totalização do TSE.
    """
    con = abrir_ro(DB_SECOES)
    saida: dict[SecaoKey, list[int]] = {}
    tipos: dict[str, int] = {}
    try:
        for mun, zona, secao, aptos, comp, tu, ta in con.execute(
            "SELECT c.mun, c.zona, c.secao, c.aptos, c.comparecimento, "
            "b.tipo_urna, b.tipo_arquivo FROM bu_cargo c "
            "JOIN secao s ON s.uf = c.uf AND s.mun = c.mun AND s.zona = c.zona "
            "AND s.secao = c.secao "
            "JOIN bu b ON b.uf = c.uf AND b.mun = c.mun AND b.zona = c.zona "
            "AND b.secao = c.secao "
            "WHERE c.uf = ? AND c.cargo = 1 AND s.nsp IS NULL",
            (uf.lower(),),
        ):
            vetor = [0] * 12
            vetor[V_APTOS], vetor[V_COMP] = int(aptos or 0), int(comp or 0)
            saida[(str(mun).zfill(5), int(zona), int(secao))] = vetor
            rotulo = f"urna{tu}_arquivo{ta}"
            tipos[rotulo] = tipos.get(rotulo, 0) + 1
        sem_bu = 0
        banco = {"flavio": 0, "lula": 0}
        for mun, zona, secao, tipo, numero, votos in con.execute(
            "SELECT mun, zona, secao, tipo, numero, votos FROM voto_secao "
            "WHERE uf = ? AND cargo = 1",
            (uf.lower(),),
        ):
            if tipo == 1 and numero == NUM_FLAVIO:
                banco["flavio"] += int(votos)
            elif tipo == 1 and numero == NUM_LULA:
                banco["lula"] += int(votos)
            reg = saida.get((str(mun).zfill(5), int(zona), int(secao)))
            if reg is None:
                sem_bu += int(votos)
                continue
            _somar_voto(reg, int(tipo), int(numero), int(votos), numeros)
        secoes_sem_bu = con.execute(
            "SELECT COUNT(*) FROM secao s LEFT JOIN bu b ON b.uf = s.uf "
            "AND b.mun = s.mun AND b.zona = s.zona AND b.secao = s.secao "
            "WHERE s.uf = ? AND s.nsp IS NULL AND b.uf IS NULL",
            (uf.lower(),),
        ).fetchone()[0]
    finally:
        con.close()
    divergentes = sum(1 for r in saida.values() if sum(r[V_FLAVIO:V_FORA]) != r[V_COMP])
    meta = {
        "secoes": len(saida),
        "secoes_principais_sem_bu": int(secoes_sem_bu),
        "votos_fora_do_universo": sem_bu,
        "banco_flavio": banco["flavio"],
        "banco_lula": banco["lula"],
        "votos_fora_lista": sum(r[V_FORA] for r in saida.values()),
        "secoes_soma_diferente_do_comparecimento": divergentes,
        "tipos": tipos,
    }
    return saida, meta


def _somar_voto(reg: list[int], tipo: int, numero: int, votos: int, numeros: set[int]):
    if tipo == 1:
        if numero == NUM_FLAVIO:
            reg[V_FLAVIO] += votos
        elif numero == NUM_LULA:
            reg[V_LULA] += votos
        elif numero in numeros:
            reg[V_TERCEIRA] += votos
            if numero in TERCEIRA_NOMEADA:
                reg[TERCEIRA_NOMEADA[numero]] += votos
        else:
            reg[V_NULOS] += votos
            reg[V_FORA] += votos
    elif tipo == 2:
        reg[V_BRANCOS] += votos
    elif tipo == 3:
        reg[V_NULOS] += votos
    else:
        raise ValueError(f"tipo de voto inesperado para presidente: {tipo}")


# ---------------------------------------------------------------- cadastro


@dataclass
class LocalCadastro:
    uf: str
    mun_tse: str
    municipio: str
    zona: int
    local_nr: int
    nome: str
    endereco: str
    bairro: str
    cep: str | None
    lat: float | None
    lon: float | None
    tipo_local: str
    coord_fonte: str | None = None

    @property
    def id(self) -> str:
        return local_id(self.uf, self.mun_tse, self.zona, self.local_nr)


def local_id(uf: str, mun_tse: str, zona: int, local_nr: int) -> str:
    return f"{uf.upper()}-{str(mun_tse).zfill(5)}-{int(zona)}-{int(local_nr)}"


def _cep(valor: Any) -> str | None:
    texto = "".join(c for c in str(valor or "") if c.isdigit())
    if len(texto) != 8 or texto == "00000000":
        return None
    return texto


def cadastro_uf(
    uf: str,
) -> tuple[
    dict[SecaoKey, LocalKey], dict[LocalKey, LocalCadastro], dict[SecaoKey, SecaoKey]
]:
    """Seção -> local onde ela vota, atributos de cada local e seção -> principal.

    Seção agregada vota na urna da principal, então vai para o local da principal.
    A principal aponta para si mesma em ``principal_de``.
    """
    con = abrir_ro(DB_LOCAIS)
    try:
        rows = con.execute(
            "SELECT municipio_cd, municipio, zona, secao, secao_principal, local_nr, "
            "local, tipo_local, endereco, bairro, cep, lat, lon FROM secao "
            "WHERE uf = ? ORDER BY municipio_cd, zona, secao",
            (uf.upper(),),
        ).fetchall()
    finally:
        con.close()
    exterior = cidades_exterior() if uf.upper() == "ZZ" else {}
    proprio: dict[SecaoKey, LocalKey] = {}
    principal_de: dict[SecaoKey, SecaoKey] = {}
    locais: dict[LocalKey, LocalCadastro] = {}
    for (
        mun,
        nome_mun,
        zona,
        secao,
        sp,
        nr,
        local,
        tipo,
        end,
        bairro,
        cep,
        lat,
        lon,
    ) in rows:
        mun5 = str(mun).zfill(5)
        chave_s = (mun5, int(zona), int(secao))
        chave_l = (mun5, int(zona), int(nr))
        proprio[chave_s] = chave_l
        principal_de[chave_s] = chave_s if sp is None else (mun5, int(zona), int(sp))
        if sp is not None or chave_l in locais:
            continue
        ponto = lat is not None and lon is not None and uf.upper() != "ZZ"
        coord_fonte = "cadastro" if ponto else None
        if uf.upper() == "ZZ" and mun5 in exterior:
            lat, lon = exterior[mun5]["lat"], exterior[mun5]["lon"]
            ponto, coord_fonte = True, "cidade"
        locais[chave_l] = LocalCadastro(
            uf=uf.upper(),
            mun_tse=mun5,
            municipio=str(nome_mun or ""),
            zona=int(zona),
            local_nr=int(nr),
            nome=str(local or "").strip(),
            endereco=str(end or "").strip(),
            bairro=str(bairro or "").strip(),
            cep=_cep(cep) if uf.upper() != "ZZ" else None,
            lat=float(lat) if ponto else None,
            lon=float(lon) if ponto else None,
            tipo_local=str(tipo or "").strip(),
            coord_fonte=coord_fonte,
        )
    secao_local = {s: proprio[principal_de[s]] for s in proprio}
    return secao_local, locais, principal_de


def cidades_exterior() -> dict[str, dict[str, Any]]:
    """Cidade do exterior (código TSE) -> nome, lat, lon e país (ISO 3166 alfa-2)."""
    dados = json.loads(JSON_CIDADES_EXTERIOR.read_text(encoding="utf-8"))
    return {str(c["cd"]).zfill(5): c for c in dados}


# -------------------------------------------------------------------- 2022

# Vetor de 2022 por seção: local_nr, lula_1t, bolsonaro_1t, nominais_1t, lula_2t,
# bolsonaro_2t, nominais_2t, aptos_1t, comparecimento_1t, aptos_2t, comparecimento_2t.
S22_COLS = (
    "local_nr_2022",
    "lula_1t",
    "bolsonaro_1t",
    "nominais_1t",
    "lula_2t",
    "bolsonaro_2t",
    "nominais_2t",
    "aptos_2022",
    "comparecimento_2022",
)


def _int(valor: str) -> int | None:
    valor = (valor or "").strip()
    if not valor:
        return None
    return round(float(valor))


def ler_2022(ufs: Iterable[str]) -> dict[str, dict[SecaoKey, list[int | None]]]:
    """Presidente por seção em 2022 (1º e 2º turnos), separado por UF."""
    alvo = {u.lower() for u in ufs}
    saida: dict[str, dict[SecaoKey, list[int | None]]] = {u.upper(): {} for u in alvo}
    with gzip.open(CSV_2022, "rt", encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            uf = linha["uf"]
            if uf not in alvo:
                continue
            chave = (linha["mun"].zfill(5), int(linha["zona"]), int(linha["secao"]))
            saida[uf.upper()][chave] = [_int(linha[c]) for c in S22_COLS] + [None, None]
    turno2 = ler_2022_2t()
    for uf, secoes in saida.items():
        extra = turno2.get(uf, {})
        for chave, vetor in secoes.items():
            par = extra.get("|".join(map(str, chave)))
            if par is not None:
                vetor[9], vetor[10] = par
    return saida


def ler_2022_2t() -> dict[str, dict[str, list[int]]]:
    """Aptos e comparecimento do 2º turno de 2022 (presidente), por seção.

    O CSV compacto de 2022 só guarda aptos e comparecimento do 1º turno; o 2º vem do
    detalhe de votação do TSE (``detalhe_votacao_secao_2022_BR.csv``), lido em fluxo.
    """
    sig = assinatura(ZIP_DETALHE_2022)
    guardado = ler_cache("presidente_2t_2022.json", sig)
    if guardado is not None:
        return guardado
    saida: dict[str, dict[str, list[int]]] = {}
    with zipfile.ZipFile(ZIP_DETALHE_2022) as z:
        nome = next(n for n in z.namelist() if n.endswith("_BR.csv"))
        with z.open(nome) as bruto:
            leitor = csv.reader(
                io.TextIOWrapper(bruto, encoding="latin-1"), delimiter=";"
            )
            cab = next(leitor)
            ix = {c: cab.index(c) for c in cab}
            for linha in leitor:
                if linha[ix["NR_TURNO"]] != "2" or linha[ix["CD_CARGO"]] != "1":
                    continue
                uf = linha[ix["SG_UF"]].upper()
                chave = "|".join(
                    (
                        linha[ix["CD_MUNICIPIO"]].zfill(5),
                        str(int(linha[ix["NR_ZONA"]])),
                        str(int(linha[ix["NR_SECAO"]])),
                    )
                )
                saida.setdefault(uf, {})[chave] = [
                    int(linha[ix["QT_APTOS"]]),
                    int(linha[ix["QT_COMPARECIMENTO"]]),
                ]
    gravar_cache("presidente_2t_2022.json", sig, saida)
    return saida


# ------------------------------------------------------------------ perfil

PERFIL_COLS = (
    "fem",
    "masc",
    "a16_24",
    "a25_34",
    "a35_44",
    "a45_59",
    "a60",
    "fund_inc",
    "fund_med",
    "med_sup_inc",
    "superior",
    "total",
)
P_IDX = {c: i for i, c in enumerate(PERFIL_COLS)}
ESC_TSE = {
    "ANALFABETO": "fund_inc",
    "LE E ESCREVE": "fund_inc",
    "ENSINO FUNDAMENTAL INCOMPLETO": "fund_inc",
    "ENSINO FUNDAMENTAL COMPLETO": "fund_med",
    "ENSINO MEDIO INCOMPLETO": "fund_med",
    "ENSINO MEDIO COMPLETO": "med_sup_inc",
    "SUPERIOR INCOMPLETO": "med_sup_inc",
    "SUPERIOR COMPLETO": "superior",
    "NAO INFORMADO": None,
}
GENERO_TSE = {"FEMININO": "fem", "MASCULINO": "masc", "NAO INFORMADO": None}


def faixa_idade(rotulo: str) -> str | None:
    """``"21 a 24 anos"`` -> ``a16_24``; idade inválida -> ``None``.

    Quem tem 15 anos no cadastro de julho completa 16 até a eleição e entra em a16_24.
    """
    digitos = ""
    for c in rotulo.strip():
        if c.isdigit():
            digitos += c
        elif digitos:
            break
    if not digitos:
        return None
    idade = int(digitos)
    if idade < 25:
        return "a16_24"
    if idade < 35:
        return "a25_34"
    if idade < 45:
        return "a35_44"
    if idade < 60:
        return "a45_59"
    return "a60"


def _rotulo(texto: str) -> str:
    return sem_acento(texto.strip().upper())


def _acumular_perfil(
    leitor: Iterable[list[str]], cab: list[str], chave_de
) -> dict[Any, list[int]]:
    ig, ii, ie = (
        cab.index("DS_GENERO"),
        cab.index("DS_FAIXA_ETARIA"),
        cab.index("DS_GRAU_ESCOLARIDADE"),
    )
    iq = cab.index("QT_ELEITORES")
    cache_idade: dict[str, str | None] = {}
    saida: dict[Any, list[int]] = {}
    for linha in leitor:
        qt = int(linha[iq])
        if qt == 0:
            continue
        chave = chave_de(linha)
        vetor = saida.get(chave)
        if vetor is None:
            vetor = saida[chave] = [0] * len(PERFIL_COLS)
        vetor[P_IDX["total"]] += qt
        genero = GENERO_TSE[_rotulo(linha[ig])]
        if genero:
            vetor[P_IDX[genero]] += qt
        rot_idade = linha[ii]
        if rot_idade not in cache_idade:
            cache_idade[rot_idade] = faixa_idade(rot_idade)
        idade = cache_idade[rot_idade]
        if idade:
            vetor[P_IDX[idade]] += qt
        esc = ESC_TSE[_rotulo(linha[ie])]
        if esc:
            vetor[P_IDX[esc]] += qt
    return saida


def arquivo_perfil_secao(uf: str) -> Path:
    return DIR_PERFIL_SECAO / f"perfil_eleitor_secao_2026_{uf.upper()}.zip"


def perfil_secao_uf(uf: str) -> tuple[dict[str, list[int]] | None, str]:
    """Perfil por seção (chave ``mun|zona|secao|local``) ou ``None`` e o motivo."""
    arq = arquivo_perfil_secao(uf)
    if not arq.exists():
        return None, "arquivo por seção ausente"
    sig = assinatura(arq)
    guardado = ler_cache(f"perfil_secao_{uf.upper()}.json", sig)
    if guardado is not None:
        return guardado, "ok"
    try:
        with zipfile.ZipFile(arq) as z:
            nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            with z.open(nome) as bruto:
                leitor = csv.reader(
                    io.TextIOWrapper(bruto, encoding="latin-1", newline=""),
                    delimiter=";",
                )
                cab = next(leitor)
                im, iz = cab.index("CD_MUNICIPIO"), cab.index("NR_ZONA")
                isec, iloc = cab.index("NR_SECAO"), cab.index("NR_LOCAL_VOTACAO")
                por_secao = _acumular_perfil(
                    leitor,
                    cab,
                    lambda r: (
                        f"{r[im].zfill(5)}|{int(r[iz])}|{int(r[isec])}|{int(r[iloc])}"
                    ),
                )
    except (zipfile.BadZipFile, zlib.error, EOFError, StopIteration, OSError) as exc:
        return None, f"arquivo por seção ilegível: {type(exc).__name__}"
    if not por_secao:
        return None, "arquivo por seção vazio"
    gravar_cache(f"perfil_secao_{uf.upper()}.json", sig, por_secao)
    return por_secao, "ok"


def perfil_zona_uf(uf: str) -> dict[str, list[int]]:
    """Perfil por zona eleitoral (chave ``mun|zona``), fallback do perfil por seção."""
    sig = [*assinatura(ZIP_PERFIL_ZONA), uf.upper()]
    guardado = ler_cache(f"perfil_zona_{uf.upper()}.json", sig)
    if guardado is not None:
        return guardado
    with zipfile.ZipFile(ZIP_PERFIL_ZONA) as z:
        nome = f"perfil_eleitorado_2026_{uf.upper()}.csv"
        with z.open(nome) as bruto:
            leitor = csv.reader(
                io.TextIOWrapper(bruto, encoding="latin-1", newline=""), delimiter=";"
            )
            cab = next(leitor)
            im, iz = cab.index("CD_MUNICIPIO"), cab.index("NR_ZONA")
            por_zona = _acumular_perfil(
                leitor, cab, lambda r: f"{r[im].zfill(5)}|{int(r[iz])}"
            )
    gravar_cache(f"perfil_zona_{uf.upper()}.json", sig, por_zona)
    return por_zona


# ----------------------------------------------------------------- setores

SITUACAO_SETOR = {
    "1": "urbana",
    "2": "urbana",
    "3": "urbana",
    "5": "rural",
    "6": "rural",
    "7": "rural",
    "8": "rural",
}
TIPO_SETOR = {
    "0": "comum",
    "1": "favela",
    "2": "militar",
    "5": "aldeia",
    "6": "prisao",
    "9": "quilombo",
}


def tipo_setor(cd_tipo: str | None) -> str | None:
    if cd_tipo is None or cd_tipo == "":
        return None
    return TIPO_SETOR.get(cd_tipo, "outro")


def situacao_setor(cd_sit: str | None) -> str | None:
    if cd_sit is None:
        return None
    return SITUACAO_SETOR.get(cd_sit)


def _gpkg_para_geom(blob: bytes):
    """Geometria de um blob GeoPackage (cabeçalho GP + WKB)."""
    if len(blob) < 8 or blob[:2] != b"GP":
        raise ValueError("blob sem a assinatura GP do GeoPackage")
    flags = blob[3]
    envelope = (flags >> 1) & 0b111
    tamanho = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope]
    return shapely.from_wkb(bytes(blob[8 + tamanho :]))


def setores_uf(uf: str, pontos: dict[str, tuple[float, float]]) -> dict[str, list]:
    """Setor censitário que cobre o ponto de cada local: ``[cd_setor, cd_sit, cd_tipo]``.

    Consulta o índice R-tree do próprio GeoPackage, ponto a ponto, sem carregar a malha.
    Ponto na divisa de dois setores fica com o de menor geocódigo. Cache por UF com a
    coordenada usada, para refazer só os locais que mudaram de ponto.
    """
    nome_cache = f"setor_{uf.upper()}.json"
    sig = assinatura(GPKG_SETORES)
    anterior = ler_cache(nome_cache, sig) or {}
    saida: dict[str, list] = {}
    faltam = {}
    for lid, (lat, lon) in pontos.items():
        reg = anterior.get(lid)
        if reg is not None and reg[0] == lat and reg[1] == lon:
            saida[lid] = reg[2:]
        else:
            faltam[lid] = (lat, lon)
    if faltam:
        con = abrir_ro(GPKG_SETORES)
        rtree = f"rtree_{TABELA_SETORES}_geom"
        q_ids = (
            f"SELECT id FROM {rtree} WHERE minx <= ? AND maxx >= ? "
            "AND miny <= ? AND maxy >= ?"
        )
        geoms: dict[int, tuple[Any, str, str, str]] = {}
        try:
            for lid, (lat, lon) in faltam.items():
                achados = []
                for (fid,) in con.execute(q_ids, (lon, lon, lat, lat)).fetchall():
                    if fid not in geoms:
                        blob, cd, sit, tipo = con.execute(
                            f"SELECT geom, CD_SETOR, CD_SIT, CD_TIPO FROM {TABELA_SETORES}"
                            " WHERE id = ?",
                            (fid,),
                        ).fetchone()
                        geoms[fid] = (_gpkg_para_geom(blob), cd, sit, tipo)
                    g, cd, sit, tipo = geoms[fid]
                    if shapely.intersects_xy(g, lon, lat):
                        achados.append([cd, sit, tipo])
                saida[lid] = min(achados) if achados else [None, None, None]
                if len(geoms) > 100_000:
                    geoms.clear()
        finally:
            con.close()
    gravar_cache(
        nome_cache,
        sig,
        {lid: [*pontos[lid], *saida[lid]] for lid in pontos},
    )
    return saida


# ------------------------------------------------- pesquisas e problemas


def ler_pesquisas() -> list[dict[str, Any]]:
    saida = []
    for nome in PESQUISAS:
        dados = json.loads((DIR_PESQUISAS / nome).read_text(encoding="utf-8"))
        dados["_arquivo"] = rel(DIR_PESQUISAS / nome)
        saida.append(dados)
    return saida


def ler_problemas() -> dict[str, Any]:
    return json.loads(JSON_PROBLEMAS.read_text(encoding="utf-8"))
