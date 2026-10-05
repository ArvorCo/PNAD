"""Leitura, só leitura, das séries de presidente por UF e do arquivo nacional.

Abre `apuracao/data/apuracao.sqlite` com `mode=ro` (o coletor continua
escrevendo) e devolve, para cada arquivo `u:6257:1:uf:<uf>::` e para o nacional
`u:6257:1:br:::`, as versões novas pela hora de geração do TSE (regra de
`dados.versoes_genuinas`), com seções, válidos e os votos de Flávio e de Lula.
Versão sem linhas normalizadas é lida do corpo guardado em `blob`.
"""

from __future__ import annotations

from typing import Any

from .banco import Banco
from .contexto import CHAVES_2026, ELE_FED
from .dados import versoes_genuinas


def _chaves(banco: Banco) -> dict[str, str]:
    return {
        str(c["sqcand"]): CHAVES_2026.get(int(c["numero"]), "outros")
        for c in banco.candidatos(ELE_FED, 1)
    }


def series_presidente(
    banco: Banco,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """(série por UF, série nacional) com `gerado`, `capturado`, `st`, `ts`, `vv`,
    `flavio` e `lula` de cada versão nova."""
    chave = _chaves(banco)
    arqs = banco.arquivos(
        "tipo = 'u' AND eleicao_cd = ? AND cargo_cd = 1 AND nivel IN ('uf', 'br')",
        (ELE_FED,),
    )
    snaps = banco.snapshots([a["id"] for a in arqs])
    ufs: dict[str, list[dict[str, Any]]] = {}
    nacional: list[dict[str, Any]] = []
    for arq in arqs:
        versoes = [dict(v) for v in versoes_genuinas(snaps.get(arq["id"], []))]
        for v in versoes:
            banco.completar_totais(v)
        votos = banco.votos(versoes)
        banco.esquecer_documentos()
        linhas = []
        for v in versoes:
            soma = {"flavio": 0, "lula": 0}
            for sq, vap in votos[v["id"]].items():
                k = chave.get(sq, "outros")
                if k in soma:
                    soma[k] += vap or 0
            linhas.append(
                {
                    "gerado": v["gerado_em"],
                    "capturado": v["capturado_em"],
                    "st": v["st"] or 0,
                    "ts": v["ts"] or 0,
                    "vv": v["vv"] or 0,
                    **soma,
                }
            )
        if arq["nivel"] == "br":
            nacional = linhas
        else:
            ufs[arq["uf"]] = linhas
    if len(ufs) != 28 or not nacional:
        raise RuntimeError(
            f"esperava 28 arquivos de UF e o nacional; vieram {len(ufs)}"
        )
    return ufs, nacional
