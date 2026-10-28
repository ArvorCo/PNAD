#!/usr/bin/env python3
"""Conjuntos de dados do dossiê da apuração do 2º turno de 2026 (25/10/2026).

Lê em modo somente leitura o banco `apuracao/data/apuracao-2t.sqlite` (o coletor
pode continuar escrevendo), as réguas do 1º turno (`analysis/apuracao_2026/dados/`
e `apuracao/data/referencia_1t.json`), os pacotes do TSE de 2022 em
`data/raw/tse_resultados/` e, para a projeção da casa ao longo da noite, o
servidor local `http://127.0.0.1:4180` (rotas `/api/2t/*` com `at=`). Grava em
`analysis/apuracao_2t_2026/dados/`:

presidente.json, linha_do_tempo.json, cedo_tarde.json, comparacao_1t.json,
comparacao_2022.json, abstencao.json, exterior.json, governadores.json,
projecao_noite.json, paralela.json e resumo.md.

Reexecutável: cada rodada lê a versão vigente de cada arquivo (a mais nova pelo
`gerado_em`), então a rodada final só precisa ser repetida quando o exterior
fechar.

Uso:
    python3 scripts/apuracao-2t-2026-dados.py
    python3 scripts/apuracao-2t-2026-dados.py --sem-api   # sem o servidor local
    python3 scripts/apuracao-2t-2026-dados.py --so comparacao_1t.json

`--so` regrava só os arquivos pedidos; os demais e o `resumo.md` ficam como estão
(útil com o servidor local desligado, que deixaria `projecao_noite.json` vazio).
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from typing import Any

from apuracao_2t_2026 import (
    comparacoes,
    estaduais,
    fontes,
    noite,
    placar,
    resumo,
    tempo,
)
from apuracao_2t_2026.base import BANCO_2T, ROOT, ROTULO, SAIDA, brt
from apuracao_2t_2026.carga import carregar
from apuracao_2026.dados import iso_z

TRAVESSAO = chr(0x2014)
PRODUTOS = (
    "presidente.json",
    "linha_do_tempo.json",
    "cedo_tarde.json",
    "comparacao_1t.json",
    "comparacao_2022.json",
    "abstencao.json",
    "exterior.json",
    "governadores.json",
    "projecao_noite.json",
    "paralela.json",
)
COMPACTOS = {
    "presidente.json",
    "linha_do_tempo.json",
    "comparacao_1t.json",
    "comparacao_2022.json",
    "abstencao.json",
}


def gravar(nome: str, dados: dict[str, Any], meta: dict[str, Any]) -> Path:
    caminho = SAIDA / nome
    corpo = {"meta": {**meta, "arquivo": nome, "rotulo": ROTULO}, **dados}
    if nome in COMPACTOS:
        texto = json.dumps(corpo, ensure_ascii=False, separators=(",", ":"))
    else:
        texto = json.dumps(corpo, ensure_ascii=False, indent=1)
    if TRAVESSAO in texto:
        raise RuntimeError(f"{nome}: travessão no texto gerado")
    caminho.write_text(texto + "\n", encoding="utf-8")
    return caminho


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--sem-api",
        action="store_true",
        help="não consulta o servidor local; projecao_noite.json fica só com a série ao vivo",
    )
    parser.add_argument(
        "--so",
        nargs="+",
        choices=PRODUTOS,
        metavar="ARQUIVO",
        help="regrava só estes arquivos; os demais e o resumo.md ficam como estão",
    )
    args = parser.parse_args()
    so = set(args.so or PRODUTOS)
    inicio = time.time()
    SAIDA.mkdir(parents=True, exist_ok=True)
    ctx = carregar()
    meta = {
        "gerado_em": iso_z(datetime.now(timezone.utc)),
        "script": "scripts/apuracao-2t-2026-dados.py",
        "banco": str(BANCO_2T.relative_to(ROOT)),
        "versao_nacional_snapshot_id": ctx.br["snapshot_id"],
        "versao_nacional_gerada_em": ctx.br["gerado_em"],
        "versao_nacional_gerada_brt": brt(ctx.br["gerado_em"]),
        "pst_nacional": round(ctx.br["pst"], 2),
        "regra_de_versao": (
            "versão vigente de cada arquivo = a mais nova pelo relógio de geração do "
            "TSE (gerado_em), desempate pelo id de captura"
        ),
    }
    municipios = placar.linhas_municipais(ctx)
    pres = cache(lambda: placar.presidente(ctx, municipios))
    r2022 = cache(fontes.municipios_2022_2t)
    fabricas: dict[str, Callable[[], dict[str, Any]]] = {
        "presidente.json": pres,
        "linha_do_tempo.json": lambda: tempo.linha_do_tempo(ctx),
        "cedo_tarde.json": lambda: tempo.cedo_tarde(ctx, municipios),
        "comparacao_1t.json": lambda: comparacoes.comparacao_1t(ctx, municipios),
        "comparacao_2022.json": lambda: comparacoes.comparacao_2022(
            ctx, municipios, r2022()
        ),
        "abstencao.json": lambda: comparacoes.abstencao(
            ctx, municipios, r2022(), pres()["ufs"]
        ),
        "exterior.json": lambda: placar.exterior(ctx, municipios),
        "governadores.json": lambda: estaduais.governadores(ctx, pres()["ufs"]),
        "projecao_noite.json": (
            noite.projecao_vazia if args.sem_api else lambda: noite.projecao_noite(ctx)
        ),
        "paralela.json": lambda: noite.paralela(ctx),
    }
    produtos = {nome: fabricas[nome]() for nome in PRODUTOS if nome in so}
    for nome, dados in produtos.items():
        caminho = gravar(nome, dados, meta)
        print(f"{caminho.relative_to(ROOT)}: {caminho.stat().st_size:,} bytes")
    if len(produtos) == len(PRODUTOS):
        texto = resumo.escrever(produtos, meta)
        if TRAVESSAO in texto:
            raise RuntimeError("resumo.md: travessão no texto gerado")
        (SAIDA / "resumo.md").write_text(texto, encoding="utf-8")
        print(f"{(SAIDA / 'resumo.md').relative_to(ROOT)}: {len(texto):,} caracteres")
    ctx.banco.fechar()
    print(
        f"versão nacional de {meta['versao_nacional_gerada_brt']}; {time.time() - inicio:.1f} s"
    )


if __name__ == "__main__":
    main()
