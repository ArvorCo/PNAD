"""Linhas por seção da mistura gaussiana dos dois turnos, fora do git.

Mesma convenção de ``secoes_linhas``: o motor
(``scripts/apuracao-2t-2026-anomalia.py``) grava uma linha por seção em
``data/outputs/apuracao_2t_2026/anomalia_secoes.json.gz`` (pasta ignorada pelo
git, gzip com ``mtime=0``) e deixa em ``anomalia_ml.json``, na chave
``secoes_arquivo``, só o ponteiro: arquivo relativo à raiz, SHA-256, bytes,
contagem de linhas e colunas. Colunas: ``uf`` (maiúsculas), ``mun`` (cinco
dígitos), ``zona``, ``secao``, ``grupo`` (0..k−1), ``score`` (log-densidade da
mistura, três casas), ``p`` (parcela do país com densidade menor, quatro casas) e
``anomalo`` (0/1). Sem o arquivo, ``bloco`` devolve ``disponivel: False``;
``exigir`` levanta ``LinhasAusentes`` com o comando que o refaz.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from functools import cache
from pathlib import Path
from typing import Any

from .secoes_linhas import LinhasAusentes

ROOT = Path(__file__).resolve().parents[2]
ARQUIVO = ROOT / "data/outputs/apuracao_2t_2026/anomalia_secoes.json.gz"
JSON = ROOT / "analysis/apuracao_2t_2026/dados/anomalia_ml.json"
COMANDO = "python3 scripts/apuracao-2t-2026-anomalia.py"
COLUNAS = ["uf", "mun", "zona", "secao", "grupo", "score", "p", "anomalo"]
CHAVE = "secoes_arquivo"


def gravar(
    colunas: list[str], linhas: list[list[Any]], destino: Path = ARQUIVO
) -> dict[str, Any]:
    """Grava o gzip (mtime fixo, bytes reprodutíveis) e devolve o ponteiro."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    corpo = json.dumps(
        {"colunas": colunas, "linhas": linhas},
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    tmp = destino.with_name(f".{destino.name}.tmp")
    with tmp.open("wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as gz:
        gz.write(corpo)
    tmp.replace(destino)
    dados = destino.read_bytes()
    try:
        arquivo = str(destino.relative_to(ROOT))
    except ValueError:
        arquivo = str(destino)
    return {
        "arquivo": arquivo,
        "sha256": hashlib.sha256(dados).hexdigest(),
        "bytes": len(dados),
        "n_linhas": len(linhas),
        "colunas": colunas,
        "nota": (
            "linhas por seção fora do git; ler com apuracao_2t_2026.anomalia_linhas.bloco"
        ),
    }


def caminho(A: dict[str, Any]) -> Path:
    """Arquivo das linhas apontado por ``anomalia_ml.json``."""
    a = Path(A[CHAVE]["arquivo"])
    return a if a.is_absolute() else ROOT / a


def disponivel(A: dict[str, Any]) -> bool:
    return caminho(A).exists()


@cache
def _ler(caminho_str: str, sha256: str) -> dict[str, Any]:
    dados = Path(caminho_str).read_bytes()
    if hashlib.sha256(dados).hexdigest() != sha256:
        raise ValueError(
            f"{caminho_str} não confere com o SHA-256 de anomalia_ml.json; rode {COMANDO}"
        )
    return json.loads(gzip.decompress(dados))


def bloco(A: dict[str, Any]) -> dict[str, Any]:
    """``{"disponivel", "colunas", "linhas"}``; vazio quando o arquivo falta."""
    p = A[CHAVE]
    c = caminho(A)
    if not c.exists():
        return {
            "disponivel": False,
            "colunas": p["colunas"],
            "linhas": [],
            "arquivo": str(c),
        }
    b = _ler(str(c), p["sha256"])
    if len(b["linhas"]) != p["n_linhas"] or b["colunas"] != p["colunas"]:
        raise ValueError(
            f"{c} não confere com o ponteiro de anomalia_ml.json; rode {COMANDO}"
        )
    return {"disponivel": True, **b}


def exigir(A: dict[str, Any]) -> dict[str, Any]:
    """Como ``bloco``, mas levanta ``LinhasAusentes`` quando o arquivo falta."""
    b = bloco(A)
    if not b["disponivel"]:
        raise LinhasAusentes(
            f"linhas da mistura ausentes em {b['arquivo']}; anomalia_ml.json aponta "
            f"para elas ({A[CHAVE]['n_linhas']} linhas). Refaça com: {COMANDO}"
        )
    return b


def ler_json(caminho_json: Path = JSON) -> dict[str, Any]:
    return json.loads(caminho_json.read_text(encoding="utf-8"))
