"""Peças comuns do dossiê da apuração do 2º turno de 2026.

Reexporta tudo de ``apuracao_2026.pagina_comum`` (cores, formato, ``Dados``,
``Capitulo``, ``montar``, ``pendente``, ``checar``, ``caminho``) e redefine as
pastas e o endereço do dossiê do 2º turno.

Interface dos capítulos (``analysis/apuracao_2t_2026/CONTRATO_DOSSIE.md``):
``pagina_cap_<ident>.render(d, cap) -> str`` devolve o HTML interno do capítulo,
sem ``<section>``. Se o HTML começar por ``cabeca(...)`` (``<div class="section-head">``),
o esqueleto usa essa cabeça; senão, escreve uma com o título do registro.
"""

from __future__ import annotations

from pathlib import Path

from apuracao_2026.pagina_comum import *  # noqa: F403
from apuracao_2026.pagina_comum import ROOT, Dados

DADOS: Path = ROOT / "analysis/apuracao_2t_2026/dados"
MEMOS: Path = ROOT / "analysis/apuracao_2t_2026"
SLUG = "apuracao_2T_2026"
URL = f"https://brasil.arvor.co/{SLUG}.html"
REPO = "https://github.com/ArvorCo/PNAD"


def dados_2t(pasta: Path = DADOS) -> Dados:
    """Leitor dos JSONs do 2º turno (o ``Dados`` do 1T com a pasta trocada)."""
    return Dados(pasta=pasta)


def cabeca(cap, titulo_html: str, lead: str = "") -> str:
    """Cabeça do capítulo com título próprio; o esqueleto não escreve outra."""
    ld = f'<p class="lead">{lead}</p>' if lead else ""
    return (
        f'<div class="section-head"><p class="kicker">{cap.numero} / {cap.curto.upper()}</p>'
        f"<h2>{titulo_html}</h2>{ld}</div>"
    )


def memo(nome: str) -> str:
    """Texto de um memorando de ``analysis/apuracao_2t_2026`` (ou de ``dados/``)."""
    for base in (MEMOS, DADOS):
        c = base / nome
        if c.exists():
            return c.read_text(encoding="utf-8")
    return ""
