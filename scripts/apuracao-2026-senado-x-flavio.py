#!/usr/bin/env python3
"""Senado contra Flávio: grava analysis/apuracao_2026/dados/senado_x_flavio.json.

Lê o banco da apuração em modo somente leitura (versão vigente = última gerada
pelo TSE), `presidente.json` (voto de Flávio por UF e por município), a tabela de
campos da casa (`apuracao/public/campos.json`), as coligações do TSE
(`data/raw/tse_candidatos_2026/consulta_cand_2026.zip`) e a exceção de campo da
casa (`docs/assets/voto_util_092026.json`). Método em
`scripts/apuracao_2026/senado_x_flavio.py`.

Uso:
    python3 scripts/apuracao-2026-senado-x-flavio.py
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from apuracao_2026 import coligacoes as COL
from apuracao_2026 import senado_x_flavio as SXF
from apuracao_2026.banco import Banco
from apuracao_2026.contexto import BANCO, CAMPOS_JSON, ELE_EST, ROOT, SAIDA
from apuracao_2026.dados import classificador, iso_z

VOTO_UTIL = ROOT / "docs/assets/voto_util_092026.json"
TRAVESSAO = chr(0x2014)


def main() -> None:
    inicio = time.time()
    banco = Banco(BANCO)
    senado = SXF.ler_senado(banco, ELE_EST)
    banco.fechar()
    presidente = json.loads((SAIDA / "presidente.json").read_text(encoding="utf-8"))
    campos = classificador(json.loads(CAMPOS_JSON.read_text(encoding="utf-8")))
    coligacoes = COL.ler(5)
    if not coligacoes:
        print(f"aviso: {COL.FONTE} ausente; ALINHADOS_LULA conferida só pela casa")
    excecao = json.loads(VOTO_UTIL.read_text(encoding="utf-8"))["campo_excecao"]
    dados = SXF.montar(senado, presidente, campos, coligacoes, excecao)
    corpo = {
        "meta": {
            "gerado_em": iso_z(datetime.now(timezone.utc)),
            "arquivo": "senado_x_flavio.json",
            "script": "scripts/apuracao-2026-senado-x-flavio.py",
            "banco": str(BANCO.relative_to(ROOT)),
            "presidente_json_gerado_em": presidente["meta"]["gerado_em"],
            "fontes": [
                "apuracao/data/apuracao.sqlite (Senado, cargo 5, arquivos de UF e de município)",
                "analysis/apuracao_2026/dados/presidente.json (Flávio por UF e por município)",
                "apuracao/public/campos.json (campo por partido e exceções)",
                COL.FONTE,
                "docs/assets/voto_util_092026.json (campo_excecao)",
            ],
            "regra_de_versao": (
                "versão vigente de cada arquivo = última gerada pelo TSE (gerado_em)"
            ),
        },
        **dados,
    }
    texto = json.dumps(corpo, ensure_ascii=False, separators=(",", ":"))
    if TRAVESSAO in texto:
        raise RuntimeError("senado_x_flavio.json: travessão no texto gerado")
    saida = SAIDA / "senado_x_flavio.json"
    saida.write_text(texto + "\n", encoding="utf-8")
    n = dados["nacional"]
    print(
        f"{saida.relative_to(ROOT)}: {saida.stat().st_size:,} bytes; "
        f"PL {n['pl']['pct']}% × Flávio {n['flavio']['pct']}% ({n['pl']['div_pp']:+.2f} pp); "
        f"aliados {n['aliados']['pct']}% ({n['aliados']['div_pp']:+.2f} pp); "
        f"{time.time() - inicio:.1f} s"
    )


if __name__ == "__main__":
    main()
