"""Réguas de comparação: 1º turno de 2026 e 2º turno de 2022, só fontes locais.

- 1º turno de 2026: `analysis/apuracao_2026/dados/{presidente,exterior,zonas,
  governadores}.json` (gerados por `scripts/apuracao-2026-dados.py` do banco do
  1º turno) e `apuracao/data/referencia_1t.json` (minuto em que cada município
  fechou na noite de 04/10).
- 2º turno de 2022: `data/raw/tse_resultados/votacao_candidato_munzona_2022.zip`
  (votos por município, lido por `apuracao_2026.tse2022.ler_munzona`) e
  `detalhe_votacao_secao_2022.zip`, membro `_BR.csv` (aptos, comparecimento,
  brancos e nulos por seção de presidente), agregado só para o 2º turno e
  guardado em `data/outputs/apuracao_2t_2026/tse2022_2t_municipios.json`.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

from apuracao_2026.tse2022 import ler_munzona

from .base import CACHE, DADOS_1T, REFERENCIA_1T, TSE_RESULTADOS, ler_json

MUNZONA_2022 = TSE_RESULTADOS / "votacao_candidato_munzona_2022.zip"
DETALHE_2022 = TSE_RESULTADOS / "detalhe_votacao_secao_2022.zip"
MEMBRO_DETALHE_BR = "detalhe_votacao_secao_2022_BR.csv"
CACHE_2022 = CACHE / "tse2022_2t_municipios.json"


def _linhas(doc: dict[str, Any]) -> list[dict[str, Any]]:
    cols = doc["colunas"]
    return [dict(zip(cols, linha, strict=True)) for linha in doc["linhas"]]


def municipios_1t() -> dict[str, dict[str, Any]]:
    """Presidente, 1º turno de 2026, por código TSE do município (sem exterior)."""
    doc = ler_json(DADOS_1T / "presidente.json")
    saida: dict[str, dict[str, Any]] = {}
    for r in _linhas(doc["municipios"]):
        r["abstencao"] = r["eleitores"] - r["comparecimento"]
        saida[r["cd_tse"]] = r
    return saida


def ufs_1t() -> dict[str, dict[str, Any]]:
    doc = ler_json(DADOS_1T / "presidente.json")
    return {u["uf"]: u for u in doc["ufs"]}


def nacional_1t() -> dict[str, Any]:
    return ler_json(DADOS_1T / "presidente.json")["nacional"]


def exterior_1t() -> dict[str, dict[str, Any]]:
    doc = ler_json(DADOS_1T / "exterior.json")
    return {c["cd_tse"]: c for c in doc["cidades"]}


def zonas_1t() -> dict[tuple[str, int], dict[str, Any]]:
    doc = ler_json(DADOS_1T / "zonas.json")
    return {(r["cd_tse"], int(r["zona"])): r for r in _linhas(doc["zonas"])}


def governadores_1t() -> dict[str, dict[str, Any]]:
    doc = ler_json(DADOS_1T / "governadores.json")
    return {u["uf"]: u for u in doc["ufs"]}


def referencia_1t() -> dict[str, Any]:
    return ler_json(REFERENCIA_1T)


def fechou_1t(ref: dict[str, Any]) -> dict[str, float | None]:
    """Minuto (após 17:00 de 04/10) em que cada município fechou no 1º turno."""
    saida: dict[str, float | None] = {}
    for _uf, muns in ref["municipios"].items():
        for cd, m in muns.items():
            saida[cd] = m.get("fechou_min")
    return saida


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _inteiro(campo: bytes) -> int:
    return int(campo.strip().strip(b'"'))


def _detalhe_2t() -> dict[str, dict[str, int]]:
    """Aptos, comparecimento, abstenção, brancos e nulos de presidente no 2º turno de 2022."""
    campos = (
        "NR_TURNO",
        "CD_MUNICIPIO",
        "CD_CARGO",
        "QT_APTOS",
        "QT_COMPARECIMENTO",
        "QT_ABSTENCOES",
        "QT_VOTOS_BRANCOS",
        "QT_VOTOS_NULOS",
    )
    contas = ("aptos", "comparecimento", "abstencao", "brancos", "nulos")
    saida: dict[str, dict[str, int]] = {}
    with zipfile.ZipFile(DETALHE_2022) as zf, zf.open(MEMBRO_DETALHE_BR) as bruto:
        leitor = io.BufferedReader(bruto, buffer_size=1 << 20)
        cab = [
            c.strip().strip('"') for c in leitor.readline().decode("latin-1").split(";")
        ]
        idx = [cab.index(c) for c in campos]
        corte = max(idx) + 1
        i_turno, i_cd, i_cargo, *i_contas = idx
        for linha in leitor:
            partes = linha.split(b";", corte)
            if partes[i_cargo].strip(b'"') != b"1" or _inteiro(partes[i_turno]) != 2:
                continue
            cd = str(_inteiro(partes[i_cd])).zfill(5)
            alvo = saida.setdefault(cd, dict.fromkeys(contas, 0))
            for conta, i in zip(contas, i_contas, strict=True):
                alvo[conta] += _inteiro(partes[i])
    return saida


def municipios_2022_2t() -> dict[str, Any]:
    """2º turno presidencial de 2022 por município (código TSE de 5 dígitos), com cache."""
    chave = {
        "munzona": {"arquivo": MUNZONA_2022.name, "bytes": MUNZONA_2022.stat().st_size},
        "detalhe": {
            "arquivo": f"{DETALHE_2022.name}:{MEMBRO_DETALHE_BR}",
            "bytes": DETALHE_2022.stat().st_size,
        },
    }
    if CACHE_2022.exists():
        doc = json.loads(CACHE_2022.read_text(encoding="utf-8"))
        if doc.get("chave") == chave:
            return doc
    votos, _zonas = ler_munzona(MUNZONA_2022)
    detalhe = _detalhe_2t()
    municipios: dict[str, dict[str, Any]] = {}
    for cd_int, m in votos.items():
        cd = str(cd_int).zfill(5)
        t2 = m["t2"]
        if not t2:
            continue
        d = detalhe.get(cd, {})
        municipios[cd] = {
            "uf": m["uf"].upper(),
            "nome": m["nome"],
            "bolsonaro": t2.get("22", 0),
            "lula": t2.get("13", 0),
            "validos": t2.get("validos", 0),
            **d,
        }
    doc = {
        "chave": chave,
        "fontes": {
            "munzona": {**chave["munzona"], "sha256": _sha256(MUNZONA_2022)},
            "detalhe": {**chave["detalhe"], "sha256": _sha256(DETALHE_2022)},
        },
        "municipios": municipios,
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    CACHE_2022.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return doc
