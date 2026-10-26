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
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
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
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sem-api",
        action="store_true",
        help="não consulta o servidor local; projecao_noite.json fica só com a série ao vivo",
    )
    args = parser.parse_args()
    inicio = time.time()
    SAIDA.mkdir(parents=True, exist_ok=True)
    ctx = carregar()
    r2022 = fontes.municipios_2022_2t()
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
    produtos: dict[str, dict[str, Any]] = {}
    produtos["presidente.json"] = placar.presidente(ctx, municipios)
    ufs_pres = produtos["presidente.json"]["ufs"]
    produtos["linha_do_tempo.json"] = tempo.linha_do_tempo(ctx)
    produtos["cedo_tarde.json"] = tempo.cedo_tarde(ctx, municipios)
    produtos["comparacao_1t.json"] = comparacoes.comparacao_1t(ctx, municipios)
    produtos["comparacao_2022.json"] = comparacoes.comparacao_2022(
        ctx, municipios, r2022
    )
    produtos["abstencao.json"] = comparacoes.abstencao(ctx, municipios, r2022, ufs_pres)
    produtos["exterior.json"] = placar.exterior(ctx, municipios)
    produtos["governadores.json"] = estaduais.governadores(ctx, ufs_pres)
    if args.sem_api:
        produtos["projecao_noite.json"] = noite.projecao_vazia()
    else:
        produtos["projecao_noite.json"] = noite.projecao_noite(ctx)
    produtos["paralela.json"] = noite.paralela(ctx)
    for nome, dados in produtos.items():
        caminho = gravar(nome, dados, meta)
        print(f"{caminho.relative_to(ROOT)}: {caminho.stat().st_size:,} bytes")
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
