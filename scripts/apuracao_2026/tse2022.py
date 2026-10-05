"""Leitura dos resultados presidenciais de 2022 do TSE, em streaming.

Três fontes, todas em `data/raw/tse_resultados/`:
- `api_2022/{uf}-c0001-e000544-r.json` (1º turno) e `-e000545-r.json` (2º turno):
  resultado por UF, com eleitorado, comparecimento, válidos e votos por candidatura;
- `votacao_candidato_munzona_2022.zip`, membro `_BR.csv` (cargo de presidente nos
  dois turnos, por município e zona, latin-1, separador `;`);
- `detalhe_votacao_secao_2022.zip`, membro `_BRASIL.csv` (aptos e comparecimento por
  seção, 1,1 GB), agregado por município e por zona sem extrair o arquivo.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from .dados import num

TURNOS = {1: "544", 2: "545"}
MEMBRO_MUNZONA = "votacao_candidato_munzona_2022_BR.csv"
MEMBRO_DETALHE = "detalhe_votacao_secao_2022_BRASIL.csv"
NUMERO_BOLSONARO = "22"
NUMERO_LULA = "13"


def ler_api_uf(pasta: Path, uf: str, turno: int) -> dict[str, Any]:
    """Resultado presidencial de 2022 de uma UF (ou `br`, `zz`) num turno."""
    caminho = pasta / f"{uf.lower()}-c0001-e000{TURNOS[turno]}-r.json"
    doc = json.loads(caminho.read_text(encoding="utf-8"))
    votos = {str(c["n"]): num(c["vap"]) for c in doc["cand"]}
    nomes = {str(c["n"]): c["nm"] for c in doc["cand"]}
    return {
        "arquivo": caminho.name,
        "eleitores": num(doc["e"]),
        "comparecimento": num(doc["c"]),
        "abstencao": num(doc["a"]),
        "validos": num(doc["vv"]),
        "brancos": num(doc["vb"]),
        "nulos": num(doc["tvn"]),
        "secoes": num(doc["s"]),
        "votos": votos,
        "nomes": nomes,
    }


def ler_api(pasta: Path, ufs: list[str]) -> dict[str, dict[int, dict[str, Any]]]:
    """Os dois turnos de 2022 para cada UF pedida."""
    return {uf: {t: ler_api_uf(pasta, uf, t) for t in TURNOS} for uf in ufs}


def ler_munzona(
    zip_path: Path,
) -> tuple[dict[int, dict[str, Any]], dict[tuple[int, int], dict]]:
    """Votos presidenciais de 2022 por município (dois turnos) e por zona (1º turno).

    Soma as linhas de todas as zonas do município, inclusive voto em trânsito. Os
    votos ficam por número de candidatura, mais `validos` (soma dos nominais
    válidos de todas as candidaturas).
    """
    municipios: dict[int, dict[str, Any]] = {}
    zonas: dict[tuple[int, int], dict[str, int]] = defaultdict(dict)
    with zipfile.ZipFile(zip_path) as zf, zf.open(MEMBRO_MUNZONA) as bruto:
        leitor = csv.reader(io.TextIOWrapper(bruto, encoding="latin-1"), delimiter=";")
        cab = {nome: i for i, nome in enumerate(next(leitor))}
        i_uf, i_cd, i_nm = cab["SG_UF"], cab["CD_MUNICIPIO"], cab["NM_MUNICIPIO"]
        i_zona, i_cargo, i_turno = cab["NR_ZONA"], cab["CD_CARGO"], cab["NR_TURNO"]
        i_nr, i_votos = cab["NR_CANDIDATO"], cab["QT_VOTOS_NOMINAIS_VALIDOS"]
        for linha in leitor:
            if linha[i_cargo] != "1":
                continue
            turno = int(linha[i_turno])
            cd = int(linha[i_cd])
            votos = int(linha[i_votos])
            numero = linha[i_nr]
            mun = municipios.setdefault(
                cd,
                {"uf": linha[i_uf].lower(), "nome": linha[i_nm], "t1": {}, "t2": {}},
            )
            alvo = mun[f"t{turno}"]
            alvo[numero] = alvo.get(numero, 0) + votos
            alvo["validos"] = alvo.get("validos", 0) + votos
            if turno == 1:
                zona = zonas[(cd, int(linha[i_zona]))]
                if numero in (NUMERO_BOLSONARO, NUMERO_LULA):
                    zona[numero] = zona.get(numero, 0) + votos
                zona["validos"] = zona.get("validos", 0) + votos
    return municipios, dict(zonas)


CAMPOS_DETALHE = (
    "NR_TURNO",
    "CD_MUNICIPIO",
    "NR_ZONA",
    "CD_CARGO",
    "QT_APTOS",
    "QT_COMPARECIMENTO",
    "QT_VOTOS_BRANCOS",
    "QT_VOTOS_NULOS",
)
CONTAS = ("aptos", "comparecimento", "brancos", "nulos")


def _inteiro(campo: bytes) -> int:
    return int(campo.strip().strip(b'"'))


def ler_detalhe(
    zip_path: Path,
) -> tuple[dict[int, dict[int, dict[str, int]]], dict[tuple[int, int], dict[str, int]]]:
    """Aptos, comparecimento, brancos e nulos de presidente em 2022.

    Devolve `{turno: {municipio: contas}}` e as contas do 1º turno por
    (município, zona). Lê o CSV nacional seção a seção, sem descompactar no disco;
    os campos usados ficam antes dos textos livres (nome e endereço do local), o
    que permite cortar a linha sem o parser de CSV.
    """
    por_mun: dict[int, dict[int, dict[str, int]]] = {1: {}, 2: {}}
    por_zona: dict[tuple[int, int], dict[str, int]] = {}
    with zipfile.ZipFile(zip_path) as zf, zf.open(MEMBRO_DETALHE) as bruto:
        leitor = io.BufferedReader(bruto, buffer_size=1 << 20)
        cab = [
            c.strip().strip('"') for c in leitor.readline().decode("latin-1").split(";")
        ]
        idx = [cab.index(c) for c in CAMPOS_DETALHE]
        corte = max(idx) + 1
        i_turno, i_cd, i_zona, i_cargo, i_aptos, i_comp, i_br, i_nu = idx
        for linha in leitor:
            campos = linha.split(b";", corte)
            if campos[i_cargo].strip(b'"') != b"1":
                continue
            turno = _inteiro(campos[i_turno])
            cd = _inteiro(campos[i_cd])
            valores = (
                _inteiro(campos[i_aptos]),
                _inteiro(campos[i_comp]),
                _inteiro(campos[i_br]),
                _inteiro(campos[i_nu]),
            )
            alvo = por_mun[turno].setdefault(cd, dict.fromkeys(CONTAS, 0))
            for conta, valor in zip(CONTAS, valores, strict=True):
                alvo[conta] += valor
            if turno == 1:
                zona = por_zona.setdefault(
                    (cd, _inteiro(campos[i_zona])), dict.fromkeys(CONTAS, 0)
                )
                for conta, valor in zip(CONTAS, valores, strict=True):
                    zona[conta] += valor
    return por_mun, por_zona
