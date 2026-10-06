"""Bloco do capítulo 3 com a origem por UF das seções da parada mais longa e os
links de download. Lê `analysis/apuracao_2026/extratos/janela_1914_2004_por_uf.csv`
(gerado por `scripts/apuracao-2026-extrato-janela.py`); sem o arquivo, não emite nada.
"""

from __future__ import annotations

import csv
from html import escape
from pathlib import Path

from .pagina_comum import inteiro

ROOT = Path(__file__).resolve().parents[2]
REPO = "https://github.com/ArvorCo/PNAD"
EXTRATO = "analysis/apuracao_2026/extratos/janela_1914_2004_por_uf"
BLOB = f"{REPO}/blob/main/"


def linhas_extrato() -> list[dict]:
    caminho = ROOT / f"{EXTRATO}.csv"
    if not caminho.exists():
        return []
    with open(caminho, encoding="utf-8") as f:
        return [
            {k: (int(v) if v.lstrip("-").isdigit() else v) for k, v in r.items()}
            for r in csv.DictReader(f)
        ]


def bloco() -> str:
    L = linhas_extrato()
    if not L:
        return ""
    top = sorted(L, key=lambda r: -r["delta_st_retrato"])[:6]
    retrato = sum(r["st_retrato_nacional_1914"] for r in L)
    uf_1914 = sum(r["st_arquivo_uf_1914"] for r in L)
    uf_2004 = sum(r["st_arquivo_uf_2004"] for r in L)
    mon_1 = sum(r["st_monitoramento_1913"] or 0 for r in L)
    mon_2 = sum(r["st_monitoramento_2005"] or 0 for r in L)
    partes = ", ".join(f"{r['uf']} {inteiro(r['delta_st_retrato'])}" for r in top)
    return (
        "<h3>De onde vieram as seções da parada mais longa</h3>"
        "<p>O arquivo nacional não traz divisão por UF; a divisão vem dos 28 arquivos de UF, gerados em "
        "instantes próprios. A versão nacional de 19:14:08 reproduz a soma das UFs de cerca de 19:08 "
        f"({inteiro(retrato)} seções); no próprio instante 19:14:08 as UFs já somavam {inteiro(uf_1914)}, e às 20:04:39, "
        f"{inteiro(uf_2004)}, quase o mesmo que o nacional. Pelo retrato de 19:08, as seções que entraram de uma vez "
        f"vieram sobretudo de {escape(partes)}. O arquivo de monitoramento, que tem contagem por UF e continuou "
        f"sendo gerado durante a parada, somava {inteiro(mon_1)} seções às 19:13:57 e {inteiro(mon_2)} às 20:05:03: "
        "depois da parada, ficou atrás dos arquivos de UF.</p>"
        f'<p class="io">Tabela por UF, com votos de Lula e Flávio nos dois instantes: '
        f'<a href="{BLOB}{EXTRATO}.md">nota e tabela</a> e <a href="{BLOB}{EXTRATO}.csv">CSV</a>; '
        f'gerados por <a href="{BLOB}scripts/apuracao-2026-extrato-janela.py">apuracao-2026-extrato-janela.py</a> '
        "a partir do banco do coletor.</p>"
    )
