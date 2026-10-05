#!/usr/bin/env python3
"""Conjuntos de dados do dossiê da apuração do 1º turno de 2026.

Lê o banco de auditoria `apuracao/data/apuracao.sqlite` em modo somente leitura
(o coletor pode continuar rodando), os resultados de 2022 do TSE em
`data/raw/tse_resultados/` e o boletim `apuracao/data/boletins/final.json`, e
grava em `analysis/apuracao_2026/dados/`:

- presidente.json, linha_do_tempo.json, exterior.json, zonas.json;
- camara.json, senado.json, assembleias.json, governadores.json;
- resumo.md (achados com número e origem).

Uso:
    (cd apuracao && bun run scripts/final-2026.ts)   # regera final.json antes
    python3 scripts/apuracao-2026-dados.py
    python3 scripts/apuracao-2026-dados.py --regerar-final
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apuracao_2026 import casas, exterior, linha, presidente, resumo, zonas
from apuracao_2026.contexto import APURACAO, BANCO, FINAL_JSON, SAIDA, carregar
from apuracao_2026.dados import iso_z

TRAVESSAO = chr(0x2014)
COMPACTOS = {"presidente.json", "zonas.json", "linha_do_tempo.json", "exterior.json"}


def gravar(nome: str, dados: dict[str, Any], meta: dict[str, Any]) -> Path:
    caminho = SAIDA / nome
    corpo = {"meta": {**meta, "arquivo": nome}, **dados}
    if nome in COMPACTOS:
        texto = json.dumps(corpo, ensure_ascii=False, separators=(",", ":"))
    else:
        texto = json.dumps(corpo, ensure_ascii=False, indent=2)
    if TRAVESSAO in texto:
        raise RuntimeError(f"{nome}: travessão no texto gerado")
    caminho.write_text(texto + "\n", encoding="utf-8")
    return caminho


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--regerar-final",
        action="store_true",
        help="roda `bun run scripts/final-2026.ts` em apuracao/ antes de ler final.json",
    )
    args = parser.parse_args()
    inicio = time.time()
    if args.regerar_final:
        subprocess.run(
            ["bun", "run", "scripts/final-2026.ts"],
            cwd=APURACAO,
            check=True,
            stdout=subprocess.DEVNULL,
        )
    SAIDA.mkdir(parents=True, exist_ok=True)
    ctx = carregar()
    final = casas.ler_final()
    meta = {
        "gerado_em": iso_z(datetime.now(timezone.utc)),
        "banco": str(BANCO.relative_to(BANCO.parents[2])),
        "versao_nacional_snapshot_id": ctx.nacional.vigente["id"],
        "versao_nacional_gerada_em": ctx.nacional.vigente["gerado_em"],
        "final_json_gerado_em": final["gerado_em"],
        "script": "scripts/apuracao-2026-dados.py",
        "regra_de_versao": (
            "versão vigente de cada arquivo = última gerada pelo TSE (gerado_em), "
            "não a última sem a marca regressivo do coletor"
        ),
    }
    produtos: dict[str, dict[str, Any]] = {}
    produtos["presidente.json"] = presidente.montar(ctx)
    produtos["linha_do_tempo.json"] = linha.montar(ctx)
    produtos["exterior.json"] = exterior.montar(ctx)
    produtos["zonas.json"] = zonas.montar(ctx)
    conferencia = casas.conferencia_versoes(ctx.banco)
    produtos["camara.json"] = {
        **casas.camara(ctx.banco, final, ctx.campos),
        "conferencia_versoes": conferencia,
    }
    produtos["senado.json"] = {
        **casas.senado(final),
        "conferencia_versoes": conferencia,
    }
    produtos["assembleias.json"] = {
        **casas.assembleias(final),
        "conferencia_versoes": conferencia,
    }
    produtos["governadores.json"] = {
        **casas.governadores(final),
        "conferencia_versoes": conferencia,
    }
    produtos["presidente.json"]["meta_contagens"] = ctx.banco.contagens_gerais()
    for nome, dados in produtos.items():
        caminho = gravar(nome, dados, meta)
        print(
            f"{caminho.relative_to(SAIDA.parents[2])}: {caminho.stat().st_size:,} bytes"
        )
    texto = resumo.escrever(produtos, meta)
    if TRAVESSAO in texto:
        raise RuntimeError("resumo.md: travessão no texto gerado")
    (SAIDA / "resumo.md").write_text(texto, encoding="utf-8")
    print(f"analysis/apuracao_2026/dados/resumo.md: {len(texto):,} caracteres")
    ctx.banco.fechar()
    print(
        f"final.json de {final['gerado_em']} ({FINAL_JSON.name}); {time.time() - inicio:.1f} s"
    )


if __name__ == "__main__":
    main()
