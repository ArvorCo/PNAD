"""Carga única do banco e dos arquivos de 2022 para todos os conjuntos de dados.

Junta, uma vez só, os arquivos de presidente do 1º turno (nacional, 28 UFs,
5.757 municípios e 6.292 zonas), todas as versões capturadas de cada um, as
versões genuínas (pela hora de geração) e a versão vigente com totais e votos.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import tse2022
from .banco import Banco
from .dados import classificador, num, versoes_genuinas

ROOT = Path(__file__).resolve().parents[2]
APURACAO = ROOT / "apuracao"
BANCO = APURACAO / "data/apuracao.sqlite"
FINAL_JSON = APURACAO / "data/boletins/final.json"
CAMPOS_JSON = APURACAO / "public/campos.json"
EXTERIOR_JSON = APURACAO / "public/exterior_cidades.json"
SENADORES_2022 = APURACAO / "public/senadores_2022.json"
TSE_RESULTADOS = ROOT / "data/raw/tse_resultados"
API_2022 = TSE_RESULTADOS / "api_2022"
MUNZONA_2022 = TSE_RESULTADOS / "votacao_candidato_munzona_2022.zip"
DETALHE_2022 = TSE_RESULTADOS / "detalhe_votacao_secao_2022.zip"
SAIDA = ROOT / "analysis/apuracao_2026/dados"

ELE_FED = 6257
ELE_EST = 6259
CHAVE_NACIONAL = "u:6257:1:br:::"

# Candidaturas presidenciais de 2026 com chave própria nas tabelas, pelo número.
CHAVES_2026 = {22: "flavio", 13: "lula", 70: "cury", 14: "renan", 55: "caiado"}
ORDEM_2026 = ("flavio", "lula", "cury", "renan", "caiado", "outros")
# Candidaturas de 2022 com chave própria, pelo número.
CHAVES_2022 = {"22": "bolsonaro", "13": "lula", "12": "ciro", "15": "tebet"}

UFS = [
    "ac",
    "al",
    "am",
    "ap",
    "ba",
    "ce",
    "df",
    "es",
    "go",
    "ma",
    "mg",
    "ms",
    "mt",
    "pa",
    "pb",
    "pe",
    "pi",
    "pr",
    "rj",
    "rn",
    "ro",
    "rr",
    "rs",
    "sc",
    "se",
    "sp",
    "to",
]
NOME_UF = {
    "ac": "Acre",
    "al": "Alagoas",
    "am": "Amazonas",
    "ap": "Amapá",
    "ba": "Bahia",
    "ce": "Ceará",
    "df": "Distrito Federal",
    "es": "Espírito Santo",
    "go": "Goiás",
    "ma": "Maranhão",
    "mg": "Minas Gerais",
    "ms": "Mato Grosso do Sul",
    "mt": "Mato Grosso",
    "pa": "Pará",
    "pb": "Paraíba",
    "pe": "Pernambuco",
    "pi": "Piauí",
    "pr": "Paraná",
    "rj": "Rio de Janeiro",
    "rn": "Rio Grande do Norte",
    "ro": "Rondônia",
    "rr": "Roraima",
    "rs": "Rio Grande do Sul",
    "sc": "Santa Catarina",
    "se": "Sergipe",
    "sp": "São Paulo",
    "to": "Tocantins",
    "zz": "Exterior",
}


@dataclass
class Arquivo:
    """Um arquivo de resultado do TSE com as versões capturadas."""

    id: int
    chave: str
    nivel: str
    uf: str | None
    municipio_cd: str | None
    zona_cd: str | None
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    versoes: list[dict[str, Any]] = field(default_factory=list)

    @property
    def vigente(self) -> dict[str, Any]:
        return self.versoes[-1]


@dataclass
class Contexto:
    banco: Banco
    candidatos: dict[str, dict[str, Any]]
    chave_de: dict[str, str]
    nacional: Arquivo
    ufs: dict[str, Arquivo]
    municipios: dict[str, Arquivo]
    zonas: dict[tuple[str, str], Arquivo]
    cadastro: dict[str, dict[str, Any]]
    votos_vigentes: dict[int, dict[str, int]]
    api2022: dict[str, dict[int, dict[str, Any]]]
    mun2022: dict[int, dict[str, Any]]
    zona2022: dict[tuple[int, int], dict[str, int]]
    det2022: dict[int, dict[int, dict[str, int]]]
    detzona2022: dict[tuple[int, int], dict[str, int]]
    campos: dict[str, dict[str, str]]

    def agrupar(self, votos: dict[str, int]) -> dict[str, int]:
        """Votos por chave curta (flavio, lula, cury, renan, caiado, outros)."""
        saida = dict.fromkeys(ORDEM_2026, 0)
        for sq, vap in votos.items():
            saida[self.chave_de.get(sq, "outros")] += vap or 0
        return saida


def _arquivos(banco: Banco) -> list[Arquivo]:
    linhas = banco.arquivos(
        "tipo = 'u' AND eleicao_cd = ? AND cargo_cd = 1 ORDER BY id", (ELE_FED,)
    )
    arquivos = [
        Arquivo(
            id=r["id"],
            chave=r["chave"],
            nivel=r["nivel"],
            uf=r["uf"],
            municipio_cd=r["municipio_cd"],
            zona_cd=r["zona_cd"],
        )
        for r in linhas
    ]
    snaps = banco.snapshots([a.id for a in arquivos])
    for arq in arquivos:
        arq.snapshots = snaps.get(arq.id, [])
        arq.versoes = versoes_genuinas(arq.snapshots)
        if not arq.versoes:
            raise RuntimeError(f"arquivo sem versão: {arq.chave}")
    return arquivos


def carregar(com_2022: bool = True) -> Contexto:
    """Abre o banco, lê as versões de presidente e os dados de 2022."""
    banco = Banco(BANCO)
    cands = banco.candidatos(ELE_FED, 1)
    candidatos = {str(c["sqcand"]): c for c in cands}
    chave_de = {
        str(c["sqcand"]): CHAVES_2026.get(int(c["numero"]), "outros") for c in cands
    }
    arquivos = _arquivos(banco)
    nacional = next(a for a in arquivos if a.chave == CHAVE_NACIONAL)
    ufs = {a.uf: a for a in arquivos if a.nivel == "uf" and a.uf}
    municipios = {
        a.municipio_cd: a for a in arquivos if a.nivel == "mu" and a.municipio_cd
    }
    zonas = {
        (a.municipio_cd, a.zona_cd): a
        for a in arquivos
        if a.nivel == "zona" and a.municipio_cd and a.zona_cd
    }
    vigentes = [a.vigente for a in arquivos]
    for snap in vigentes:
        banco.completar_totais(snap)
    votos_vigentes = banco.votos(vigentes)
    banco.esquecer_documentos()
    cadastro = {m["cd"]: m for m in banco.municipios()}
    campos = classificador(json.loads(CAMPOS_JSON.read_text(encoding="utf-8")))
    api2022: dict[str, dict[int, dict[str, Any]]] = {}
    mun2022: dict[int, dict[str, Any]] = {}
    zona2022: dict[tuple[int, int], dict[str, int]] = {}
    det2022: dict[int, dict[int, dict[str, int]]] = {1: {}, 2: {}}
    detzona2022: dict[tuple[int, int], dict[str, int]] = {}
    if com_2022:
        api2022 = tse2022.ler_api(API_2022, [*UFS, "zz", "br"])
        mun2022, zona2022 = tse2022.ler_munzona(MUNZONA_2022)
        det2022, detzona2022 = tse2022.ler_detalhe(DETALHE_2022)
    return Contexto(
        banco=banco,
        candidatos=candidatos,
        chave_de=chave_de,
        nacional=nacional,
        ufs=ufs,
        municipios=municipios,
        zonas=zonas,
        cadastro=cadastro,
        votos_vigentes=votos_vigentes,
        api2022=api2022,
        mun2022=mun2022,
        zona2022=zona2022,
        det2022=det2022,
        detzona2022=detzona2022,
        campos=campos,
    )


def numero_do_municipio(cd: str) -> int:
    """Código TSE do município em inteiro (o banco guarda com zeros à esquerda)."""
    valor = num(cd)
    if not isinstance(valor, int):
        raise ValueError(f"código de município inválido: {cd}")
    return valor
