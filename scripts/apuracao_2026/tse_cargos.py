"""Resultados de 2018 e 2022 do TSE para os cargos gerais, lidos em streaming.

Fontes, todas em `data/raw/tse_resultados/` (latin-1, separador `;`):
- `votacao_candidato_munzona_<ano>.zip`, membros `_<UF>.csv`: votos nominais por
  candidatura, município e zona, com a situação de totalização no turno
  (`DS_SIT_TOT_TURNO`);
- `votacao_partido_munzona_2022.zip`, membros `_<UF>.csv`: votos nominais e de
  legenda por partido, município e zona.

Os pacotes são a versão corrente do TSE (2022 gerado em 26/08/2026, 2018 em
13/11/2024): incorporam retotalizações e trazem também eleições suplementares
(`CD_TIPO_ELEICAO` 1), como a de senador em MT em 2020 e a de governador em RR
em 2026. Cada candidatura guarda a eleição de origem para que a análise escolha
de forma explícita o que entra.

O presidente fica de fora: ele está em `tse2022.py`. Os arquivos por UF somam
4 GB por ano; a leitura corta cada linha só até o código do cargo e decodifica
apenas as linhas dos cargos pedidos, sem extrair nada no disco.
"""

from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path

GOVERNADOR = 3
SENADOR = 5
DEPUTADO_FEDERAL = 6
DEPUTADO_ESTADUAL = 7
DEPUTADO_DISTRITAL = 8

TIPO_ORDINARIA = 2
TIPO_SUPLEMENTAR = 1

NULOS = frozenset({"#NULO#", "#NULO", "#NE", ""})
COLUNAS_CANDIDATO = (
    "CD_TIPO_ELEICAO",
    "CD_ELEICAO",
    "DS_ELEICAO",
    "DT_ELEICAO",
    "SG_UF",
    "NR_TURNO",
    "CD_CARGO",
    "SQ_CANDIDATO",
    "NR_CANDIDATO",
    "NM_CANDIDATO",
    "NM_URNA_CANDIDATO",
    "NR_PARTIDO",
    "SG_PARTIDO",
    "SG_FEDERACAO",
    "QT_VOTOS_NOMINAIS",
    "QT_VOTOS_NOMINAIS_VALIDOS",
    "DS_SIT_TOT_TURNO",
)
COLUNAS_PARTIDO = (
    "CD_TIPO_ELEICAO",
    "SG_UF",
    "NR_TURNO",
    "CD_CARGO",
    "NR_PARTIDO",
    "SG_PARTIDO",
    "QT_VOTOS_NOMINAIS_VALIDOS",
    "QT_TOTAL_VOTOS_LEG_VALIDOS",
)
# Posição de CD_CARGO nos layouts de 2018 e 2022. Antes dela só há códigos,
# datas e nomes de eleição e de município, que não contêm o separador.
POSICAO_CARGO = 16


@dataclass
class Candidatura:
    """Uma candidatura num turno de uma eleição, com os votos de todas as zonas."""

    ano: int
    cd_eleicao: int
    ds_eleicao: str
    dt_eleicao: str
    suplementar: bool
    uf: str
    cargo: int
    turno: int
    sq: str
    numero: str
    nome: str
    nome_urna: str
    nr_partido: str
    partido: str
    federacao: str | None
    situacao: str
    votos: int = 0
    votos_nominais: int = 0
    situacoes: set[str] = field(default_factory=set)


def _texto(valor: str) -> str:
    return valor.strip().strip('"').strip()


def _linhas(
    zf: zipfile.ZipFile, membro: str, cargos: set[int], requeridas: tuple[str, ...]
) -> Iterator[tuple[dict[str, int], list[str]]]:
    """Linhas (já separadas) de um CSV do TSE cujo cargo está em `cargos`."""
    alvo = {str(c).encode() for c in cargos}
    with zf.open(membro) as bruto:
        leitor = io.BufferedReader(bruto, buffer_size=1 << 22)
        cabecalho = [_texto(c) for c in leitor.readline().decode("latin-1").split(";")]
        if cabecalho[POSICAO_CARGO] != "CD_CARGO":
            raise ValueError(f"{membro}: CD_CARGO fora da posição {POSICAO_CARGO}")
        indice = {nome: i for i, nome in enumerate(cabecalho)}
        faltam = [c for c in requeridas if c not in indice]
        if faltam:
            raise ValueError(f"{membro}: colunas ausentes {faltam}")
        n = len(cabecalho)
        for linha in leitor:
            cargo = linha.split(b";", POSICAO_CARGO + 1)[POSICAO_CARGO].strip(b'"')
            if cargo not in alvo:
                continue
            texto = linha.decode("latin-1").rstrip("\r\n")
            partes = texto.split(";")
            if len(partes) != n:
                partes = next(csv.reader([texto], delimiter=";"))
                if len(partes) != n:
                    raise ValueError(f"{membro}: linha com {len(partes)} campos")
            yield indice, [_texto(p) for p in partes]


def _membro(zf: zipfile.ZipFile, prefixo: str, uf: str) -> str:
    nome = f"{prefixo}_{uf.upper()}.csv"
    if nome not in zf.namelist():
        raise FileNotFoundError(f"{nome} ausente do pacote")
    return nome


def ler_candidaturas(
    zip_path: Path, ano: int, cargos_por_uf: Mapping[str, set[int]]
) -> dict[tuple[int, str, int], Candidatura]:
    """Candidaturas dos cargos pedidos em cada UF, por (eleição, sequencial, turno).

    Votos são os nominais válidos (`QT_VOTOS_NOMINAIS_VALIDOS`); os nominais
    brutos ficam ao lado. A situação de totalização deve ser a mesma em todas as
    linhas da candidatura no turno; divergência é erro, não escolha.
    """
    saida: dict[tuple[int, str, int], Candidatura] = {}
    prefixo = f"votacao_candidato_munzona_{ano}"
    with zipfile.ZipFile(zip_path) as zf:
        for uf, cargos in sorted(cargos_por_uf.items()):
            membro = _membro(zf, prefixo, uf)
            for ix, p in _linhas(zf, membro, cargos, COLUNAS_CANDIDATO):
                eleicao = int(p[ix["CD_ELEICAO"]])
                sq = p[ix["SQ_CANDIDATO"]]
                turno = int(p[ix["NR_TURNO"]])
                chave = (eleicao, sq, turno)
                cand = saida.get(chave)
                if cand is None:
                    federacao = p[ix["SG_FEDERACAO"]]
                    cand = Candidatura(
                        ano=ano,
                        cd_eleicao=eleicao,
                        ds_eleicao=p[ix["DS_ELEICAO"]],
                        dt_eleicao=p[ix["DT_ELEICAO"]],
                        suplementar=int(p[ix["CD_TIPO_ELEICAO"]]) == TIPO_SUPLEMENTAR,
                        uf=p[ix["SG_UF"]].upper(),
                        cargo=int(p[ix["CD_CARGO"]]),
                        turno=turno,
                        sq=sq,
                        numero=p[ix["NR_CANDIDATO"]],
                        nome=p[ix["NM_CANDIDATO"]],
                        nome_urna=p[ix["NM_URNA_CANDIDATO"]],
                        nr_partido=p[ix["NR_PARTIDO"]],
                        partido=p[ix["SG_PARTIDO"]],
                        federacao=None if federacao in NULOS else federacao,
                        situacao=p[ix["DS_SIT_TOT_TURNO"]],
                    )
                    saida[chave] = cand
                cand.votos += int(p[ix["QT_VOTOS_NOMINAIS_VALIDOS"]])
                cand.votos_nominais += int(p[ix["QT_VOTOS_NOMINAIS"]])
                cand.situacoes.add(p[ix["DS_SIT_TOT_TURNO"]])
    divergentes = [c for c in saida.values() if len(c.situacoes) > 1]
    if divergentes:
        exemplo = divergentes[0]
        raise ValueError(
            f"{len(divergentes)} candidaturas com situação divergente entre zonas, "
            f"por exemplo {exemplo.uf} {exemplo.nome_urna}: {sorted(exemplo.situacoes)}"
        )
    return saida


def ler_votos_partido(
    zip_path: Path, ano: int, cargo: int, ufs: list[str]
) -> dict[str, dict[str, dict[str, int]]]:
    """Votos válidos por partido em cada UF na eleição ordinária, 1º turno.

    `legenda` é `QT_TOTAL_VOTOS_LEG_VALIDOS`, que já inclui os nominais
    convertidos em legenda (candidatura indeferida depois da eleição cujo voto
    fica com o partido). O total é o que entra no quociente partidário. UF sem
    linha do cargo no pacote devolve dicionário vazio, sem preenchimento.
    """
    saida: dict[str, dict[str, dict[str, int]]] = {}
    prefixo = f"votacao_partido_munzona_{ano}"
    with zipfile.ZipFile(zip_path) as zf:
        for uf in sorted(ufs):
            membro = _membro(zf, prefixo, uf)
            por_partido: dict[str, dict[str, int]] = {}
            for ix, p in _linhas(zf, membro, {cargo}, COLUNAS_PARTIDO):
                if int(p[ix["NR_TURNO"]]) != 1:
                    continue
                if int(p[ix["CD_TIPO_ELEICAO"]]) != TIPO_ORDINARIA:
                    continue
                sigla = p[ix["SG_PARTIDO"]]
                alvo = por_partido.setdefault(
                    sigla,
                    {"numero": int(p[ix["NR_PARTIDO"]]), "nominais": 0, "legenda": 0},
                )
                alvo["nominais"] += int(p[ix["QT_VOTOS_NOMINAIS_VALIDOS"]])
                alvo["legenda"] += int(p[ix["QT_TOTAL_VOTOS_LEG_VALIDOS"]])
            for alvo in por_partido.values():
                alvo["total"] = alvo["nominais"] + alvo["legenda"]
            saida[uf.upper()] = por_partido
    return saida
