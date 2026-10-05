"""Carga das fontes da comparação 2022 × 2026, todas locais.

2026: `apuracao/data/boletins/final.json` (bancadas, senadores e governadores,
com campo já atribuído), `analysis/apuracao_2026/dados/presidente.json` (gerado
por `scripts/apuracao-2026-dados.py`; na falta dele, o nível de UF sai direto do
banco) e o banco `apuracao/data/apuracao.sqlite` em modo somente leitura (votos
por partido na Câmara, nomes completos das candidaturas, números dos partidos).

2022 e 2018: os pacotes do TSE em `data/raw/tse_resultados/` (ver `tse2022.py`
e `tse_cargos.py`).
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import casas, tse2022, tse_cargos
from .banco import Banco
from .comparacao import normalizar_texto
from .contexto import (
    API_2022,
    BANCO,
    CAMPOS_JSON,
    CHAVES_2026,
    ELE_EST,
    ELE_FED,
    FINAL_JSON,
    ROOT,
    SAIDA,
    SENADORES_2022,
    TSE_RESULTADOS,
    UFS,
)
from .dados import classificador, versoes_genuinas

CAND_2022 = TSE_RESULTADOS / "votacao_candidato_munzona_2022.zip"
CAND_2018 = TSE_RESULTADOS / "votacao_candidato_munzona_2018.zip"
PARTIDO_2022 = TSE_RESULTADOS / "votacao_partido_munzona_2022.zip"
PRESIDENTE_JSON = SAIDA / "presidente.json"
CAMARA_JSON = SAIDA / "camara.json"

# Assembleias comparadas (as 11 casas do boletim final); DF é Câmara Legislativa.
ASSEMBLEIAS = ("SP", "MG", "RJ", "BA", "RS", "PR", "PE", "CE", "GO", "SC", "DF")


@dataclass
class Fontes:
    final: dict[str, Any]
    campos: dict[str, dict[str, str]]
    pres26: dict[str, dict[str, int]]
    pres26_origem: str
    api2022: dict[str, dict[int, dict[str, Any]]]
    cand22: dict[tuple[int, str, int], tse_cargos.Candidatura]
    cand18: dict[tuple[int, str, int], tse_cargos.Candidatura]
    partido22: dict[str, dict[str, dict[str, int]]]
    camara26_votos: dict[str, dict[str, int]]
    camara26_origem: str
    nomes26: dict[tuple[int, str, str], list[tuple[str, str]]]
    partidos26: dict[int, str]
    senadores_2022_ref: list[dict[str, Any]]
    arquivos: list[dict[str, Any]]


def relativo(caminho: Path) -> str:
    return str(caminho.resolve().relative_to(ROOT))


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arq:
        for bloco in iter(lambda: arq.read(1 << 22), b""):
            h.update(bloco)
    return h.hexdigest()


def geracao_tse(zip_path: Path, membro: str) -> str | None:
    """`DT_GERACAO HH_GERACAO` da primeira linha de dados de um CSV do TSE."""
    with zipfile.ZipFile(zip_path) as zf, zf.open(membro) as bruto:
        texto = io.TextIOWrapper(bruto, encoding="latin-1")
        cab = [c.strip().strip('"') for c in texto.readline().split(";")]
        linha = [c.strip().strip('"') for c in texto.readline().split(";")]
    campos = dict(zip(cab, linha, strict=False))
    if "DT_GERACAO" not in campos:
        return None
    return f"{campos['DT_GERACAO']} {campos.get('HH_GERACAO', '')}".strip()


def _pres26_do_json(doc: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    saida = {}
    for u in doc["ufs"]:
        v = u["votos"]
        saida[u["uf"].upper()] = {
            "e26": u["eleitores"],
            "c26": u["comparecimento"],
            "a26": u["abstencao"],
            "vv26": u["validos"],
            "vb26": u["brancos"],
            "vn26": u["nulos"],
            "flavio": v["flavio"],
            "lula26": v["lula"],
            "cury": v["cury"],
            "renan": v["renan"],
            "caiado": v["caiado"],
            "outros26": v["outros"],
        }
    return saida


def _pres26_do_banco(banco: Banco) -> dict[str, dict[str, int]]:
    """Nível de UF do presidente direto do banco (versão vigente de cada arquivo)."""
    arqs = banco.arquivos(
        "tipo = 'u' AND eleicao_cd = ? AND cargo_cd = 1 AND nivel = 'uf'", (ELE_FED,)
    )
    snaps = banco.snapshots([a["id"] for a in arqs])
    chave = {
        str(c["sqcand"]): CHAVES_2026.get(int(c["numero"]), "outros")
        for c in banco.candidatos(ELE_FED, 1)
    }
    vigentes = []
    for a in arqs:
        versoes = versoes_genuinas(snaps.get(a["id"], []))
        if not versoes:
            raise RuntimeError(f"presidente {a['uf']}: arquivo sem versão")
        vigentes.append((a["uf"].upper(), banco.completar_totais(dict(versoes[-1]))))
    votos = banco.votos([s for _, s in vigentes])
    saida = {}
    for uf, s in vigentes:
        agrupado = dict.fromkeys(
            ("flavio", "lula", "cury", "renan", "caiado", "outros"), 0
        )
        for sq, vap in votos[s["id"]].items():
            agrupado[chave.get(sq, "outros")] += vap or 0
        saida[uf] = {
            "e26": s["te"],
            "c26": s["comparecimento"],
            "a26": s["abstencao"],
            "vv26": s["vv"],
            "vb26": s["vb"],
            "vn26": s["tvn"],
            "flavio": agrupado["flavio"],
            "lula26": agrupado["lula"],
            "cury": agrupado["cury"],
            "renan": agrupado["renan"],
            "caiado": agrupado["caiado"],
            "outros26": agrupado["outros"],
        }
    banco.esquecer_documentos()
    return saida


def _camara26_votos(
    banco: Banco, final: dict[str, Any], campos: dict[str, dict[str, str]]
) -> tuple[dict[str, dict[str, int]], str]:
    """Votos por partido na Câmara em cada UF (nominais mais legenda).

    Reaproveita `camara.json` quando ele foi gerado do mesmo `final.json`; senão
    recalcula pelo mesmo código (`casas.camara`).
    """
    if CAMARA_JSON.exists():
        doc = json.loads(CAMARA_JSON.read_text(encoding="utf-8"))
        if doc.get("meta", {}).get("final_json_gerado_em") == final["gerado_em"]:
            return (
                {
                    u["uf"]: {p["partido"]: p["votos"] for p in u["votos_por_partido"]}
                    for u in doc["ufs"]
                },
                f"{relativo(CAMARA_JSON)} (votos_por_partido, mesmo final.json)",
            )
    doc = casas.camara(banco, final, campos)
    return (
        {
            u["uf"]: {p["partido"]: p["votos"] for p in u["votos_por_partido"]}
            for u in doc["ufs"]
        },
        "apuracao.sqlite, voto_partido (tvtn + tvtl), via casas.camara",
    )


def _nomes26(banco: Banco) -> dict[tuple[int, str, str], list[tuple[str, str]]]:
    """(cargo, UF, nome de urna normalizado) -> [(nome completo normalizado, partido)]."""
    linhas = banco.linhas(
        "SELECT c.uf, c.cargo_cd, c.nome_urna, c.nome, p.sigla AS partido "
        "FROM candidato c LEFT JOIN partido p ON p.n = c.partido_n "
        "WHERE c.eleicao_cd = ?",
        (ELE_EST,),
    )
    saida: dict[tuple[int, str, str], list[tuple[str, str]]] = {}
    for r in linhas:
        chave = (
            int(r["cargo_cd"]),
            str(r["uf"]).upper(),
            normalizar_texto(r["nome_urna"]),
        )
        saida.setdefault(chave, []).append(
            (normalizar_texto(r["nome"]), r["partido"] or "")
        )
    return saida


def carregar() -> Fontes:
    final = json.loads(FINAL_JSON.read_text(encoding="utf-8"))
    campos = classificador(json.loads(CAMPOS_JSON.read_text(encoding="utf-8")))
    banco = Banco(BANCO)
    if PRESIDENTE_JSON.exists():
        pres_doc = json.loads(PRESIDENTE_JSON.read_text(encoding="utf-8"))
        pres26 = _pres26_do_json(pres_doc)
        pres_origem = f"{relativo(PRESIDENTE_JSON)} (ufs, gerado em {pres_doc['meta']['gerado_em']})"
    else:
        pres26 = _pres26_do_banco(banco)
        pres_origem = "apuracao.sqlite (arquivos de UF do presidente, versão vigente)"
    camara_votos, camara_origem = _camara26_votos(banco, final, campos)
    nomes26 = _nomes26(banco)
    partidos26 = {
        int(r["n"]): r["sigla"]
        for r in banco.linhas(
            "SELECT n, sigla FROM partido WHERE sigla IS NOT NULL AND sigla != ''"
        )
    }
    banco.fechar()
    api2022 = tse2022.ler_api(API_2022, [*UFS, "zz", "br"])
    cargos22: dict[str, set[int]] = {}
    for uf in UFS:
        cargos = {
            tse_cargos.GOVERNADOR,
            tse_cargos.SENADOR,
            tse_cargos.DEPUTADO_FEDERAL,
        }
        if uf.upper() == "DF":
            cargos.add(tse_cargos.DEPUTADO_DISTRITAL)
        elif uf.upper() in ASSEMBLEIAS:
            cargos.add(tse_cargos.DEPUTADO_ESTADUAL)
        cargos22[uf] = cargos
    cand22 = tse_cargos.ler_candidaturas(CAND_2022, 2022, cargos22)
    cand18 = tse_cargos.ler_candidaturas(
        CAND_2018, 2018, {uf: {tse_cargos.SENADOR} for uf in UFS}
    )
    partido22 = tse_cargos.ler_votos_partido(
        PARTIDO_2022, 2022, tse_cargos.DEPUTADO_FEDERAL, list(UFS)
    )
    arquivos = []
    for caminho, membro in (
        (CAND_2022, "votacao_candidato_munzona_2022_AC.csv"),
        (CAND_2018, "votacao_candidato_munzona_2018_AC.csv"),
        (PARTIDO_2022, "votacao_partido_munzona_2022_AC.csv"),
    ):
        arquivos.append(
            {
                "arquivo": relativo(caminho),
                "bytes": caminho.stat().st_size,
                "sha256": sha256(caminho),
                "geracao_tse": geracao_tse(caminho, membro),
            }
        )
    for caminho in (FINAL_JSON, CAMPOS_JSON, SENADORES_2022):
        arquivos.append(
            {
                "arquivo": relativo(caminho),
                "bytes": caminho.stat().st_size,
                "sha256": sha256(caminho),
            }
        )
    return Fontes(
        final=final,
        campos=campos,
        pres26=pres26,
        pres26_origem=pres_origem,
        api2022=api2022,
        cand22=cand22,
        cand18=cand18,
        partido22=partido22,
        camara26_votos=camara_votos,
        camara26_origem=camara_origem,
        nomes26=nomes26,
        partidos26=partidos26,
        senadores_2022_ref=json.loads(SENADORES_2022.read_text(encoding="utf-8")),
        arquivos=arquivos,
    )
