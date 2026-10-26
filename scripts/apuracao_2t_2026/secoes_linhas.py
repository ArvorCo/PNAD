"""Linhas por seção da análise do 2º turno, fora do git.

Com o banco completo, uma linha por seção passa de 100 MB. O script
``scripts/apuracao-2t-2026-secoes.py`` grava as linhas em
``data/outputs/apuracao_2t_2026/secoes_linhas.json.gz`` (pasta ignorada pelo
git) e deixa em ``secoes.json``, na chave ``secoes``, só o ponteiro: arquivo
relativo à raiz, SHA-256, bytes, contagem de linhas e colunas. Quem precisa das
linhas chama ``bloco(S)``; um ``secoes.json`` antigo, com as linhas embutidas,
continua valendo. Sem o arquivo (no CI, por desenho), ``bloco`` devolve um bloco
vazio com ``disponivel: False``; cada leitor decide. Quem não pode seguir sem as
linhas chama ``exigir(S)``, que levanta ``LinhasAusentes`` com o comando que as
refaz. A thread lê só os agregados de ``secoes.json`` (``reduzidos_thread``).
"""

from __future__ import annotations

import gzip
import hashlib
import json
from functools import cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARQUIVO = ROOT / "data/outputs/apuracao_2t_2026/secoes_linhas.json.gz"
COMANDO = "python3 scripts/apuracao-2t-2026-secoes.py --fonte completo"


class LinhasAusentes(FileNotFoundError):
    """O arquivo pesado das linhas por seção não está nesta máquina."""


def gravar(
    colunas: list[str], linhas: list[list[Any]], destino: Path = ARQUIVO
) -> dict:
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
        "nota": "linhas por seção fora do git; ler com apuracao_2t_2026.secoes_linhas.bloco",
    }


def caminho(S: dict) -> Path | None:
    """Arquivo das linhas apontado por ``secoes.json`` (None se embutidas)."""
    p = S["secoes"]
    if "linhas" in p:
        return None
    a = Path(p["arquivo"])
    return a if a.is_absolute() else ROOT / a


def disponivel(S: dict) -> bool:
    c = caminho(S)
    return c is None or c.exists()


@cache
def _ler(caminho_str: str, sha256: str) -> dict:
    dados = Path(caminho_str).read_bytes()
    if hashlib.sha256(dados).hexdigest() != sha256:
        raise ValueError(
            f"{caminho_str} não confere com o SHA-256 de secoes.json; rode {COMANDO}"
        )
    return json.loads(gzip.decompress(dados))


def bloco(S: dict) -> dict:
    """``{"disponivel", "colunas", "linhas"}``; vazio quando o arquivo falta."""
    p = S["secoes"]
    if "linhas" in p:
        return {"disponivel": True, **p}
    c = caminho(S)
    assert c is not None
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
            f"{c} não confere com o ponteiro de secoes.json; rode {COMANDO}"
        )
    return {"disponivel": True, **b}


def exigir(S: dict) -> dict:
    """Como ``bloco``, mas levanta ``LinhasAusentes`` quando o arquivo falta."""
    b = bloco(S)
    if not b["disponivel"]:
        raise LinhasAusentes(
            f"linhas por seção ausentes em {b['arquivo']}; secoes.json aponta para "
            f"elas ({S['secoes']['n_linhas']} linhas). Refaça com: {COMANDO}"
        )
    return b
