#!/usr/bin/env python3
"""Fechamento das seções: onde a votação termina tarde, em 2022 e 2026.

Lê, só para leitura, os boletins de urna coletados seção a seção
(``apuracao/data/secoes_2026.sqlite``), o cadastro de locais de votação de 2026,
a lista de candidaturas do banco da apuração, os dados abertos do TSE de 2022
por seção (recebimento do boletim, votos de presidente, local) e a análise por
seção já publicada (``secoes.json``, para conferir o número dela). Grava:

- ``analysis/apuracao_2026/dados/fechamento.json`` (agregados, listas e amostras
  com o registro ``SecaoRef`` do contrato de seções);
- ``analysis/apuracao_2026/fechamento.md`` (método, achados e limites).

Roda com a coleta parcial e marca ``cobertura.parcial``. Para a rodada final,
depois que a coleta terminar: rodar de novo este script e
``python3 scripts/apuracao-2026-build.py``. Uso:

    python3 scripts/apuracao-2026-fechamento.py
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apuracao_2026 import (
    fechamento_base,
    fechamento_dist,
    fechamento_modelo,
    fechamento_persist,
    fechamento_texto,
    fechamento_voto,
    secoes_2022,
)

ROOT = Path(__file__).resolve().parents[1]
DB_SECOES = ROOT / "apuracao/data/secoes_2026.sqlite"
DB_LOCAIS = ROOT / "data/outputs/locais_votacao_2026.sqlite"
DB_APURACAO = ROOT / "apuracao/data/apuracao.sqlite"
ZIP_VOTOS_2022 = (
    ROOT / "data/raw/tse_resultados/votacao_secao_2022/votacao_secao_2022_BR.zip"
)
ZIP_DETALHE_2022 = ROOT / "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip"
CACHE_2022 = ROOT / "data/outputs/presidente_secao_2022.csv.gz"
CACHE_TIPO_2022 = ROOT / "data/outputs/fechamento_tipo_local_2022.csv.gz"
SECOES_JSON = ROOT / "analysis/apuracao_2026/dados/secoes.json"
SAIDA_JSON = ROOT / "analysis/apuracao_2026/dados/fechamento.json"
SAIDA_MD = ROOT / "analysis/apuracao_2026/fechamento.md"
LIMITE_BYTES = 2_000_000


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def fontes(a: argparse.Namespace) -> list[dict[str, str]]:
    return [
        {
            "chave": "boletins",
            "caminho": rel(a.secoes_db),
            "descricao": (
                "boletins de urna de 2026 por seção: abertura e encerramento (primeiro e "
                "último voto, hora local da urna), habilitação por biometria e por ano de "
                "nascimento; recebimento no TSE (dr/hr do aux.json, hora de Brasília)"
            ),
        },
        {
            "chave": "locais",
            "caminho": rel(a.locais_db),
            "descricao": "cadastro de locais de votação 2026 do TSE, por seção",
        },
        {
            "chave": "candidatos",
            "caminho": rel(a.apuracao_db),
            "descricao": "lista de candidaturas a presidente (eleição 6257)",
        },
        {
            "chave": "presidente_2022",
            "caminho": rel(ZIP_VOTOS_2022),
            "descricao": "votos por candidato e seção, presidente, 1º turno de 2022 (TSE)",
        },
        {
            "chave": "detalhe_2022",
            "caminho": rel(ZIP_DETALHE_2022),
            "descricao": (
                "recebimento do boletim no TSE (DT_RECEBIMENTO_BU_HOR_TSE, hora TSE), "
                "aptos, comparecimento, nome e endereço do local por seção, 2022"
            ),
        },
        {
            "chave": "secoes",
            "caminho": rel(SECOES_JSON),
            "descricao": "análise por seção já publicada (número a conferir)",
        },
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--secoes-db", type=Path, default=DB_SECOES)
    ap.add_argument("--locais-db", type=Path, default=DB_LOCAIS)
    ap.add_argument("--apuracao-db", type=Path, default=DB_APURACAO)
    ap.add_argument("--saida-json", type=Path, default=SAIDA_JSON)
    ap.add_argument("--saida-md", type=Path, default=SAIDA_MD)
    a = ap.parse_args(argv)

    d26 = fechamento_base.montar_2026(a.secoes_db, a.locais_db, a.apuracao_db)
    principais = fechamento_base.ler_principais(a.secoes_db)
    principais = principais[principais["uf"] != "zz"]
    s22 = secoes_2022.presidente_2022(ZIP_VOTOS_2022, ZIP_DETALHE_2022, CACHE_2022)
    if s22 is None:
        raise SystemExit("dados de 2022 ausentes em data/raw/tse_resultados/")
    tipos = fechamento_base.tipos_2022(ZIP_DETALHE_2022, CACHE_TIPO_2022)
    d22 = fechamento_base.montar_2022(s22, tipos)
    cob = fechamento_base.cobertura(d26, principais, d22)
    completas = cob["ufs_completas"]
    secoes_json = (
        json.loads(SECOES_JSON.read_text(encoding="utf-8"))
        if SECOES_JSON.exists()
        else None
    )

    v = fechamento_voto.base_voto(d26, completas)
    ests = fechamento_voto.estimadores(v, d22, completas)
    todas = fechamento_voto.base_voto(
        d26, sorted({u.upper() for u in d26["uf"].unique()})
    )
    dados: dict[str, Any] = {
        "titulo": "Onde a votação termina tarde: encerramento e recebimento por seção, 2022 e 2026",
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "versao_contrato": "1.0",
        "aviso": fechamento_texto.AVISO,
        "fontes": fontes(a),
        "fontes_legais": fechamento_texto.FONTES_LEGAIS,
        "definicoes": fechamento_texto.DEFINICOES,
        "cobertura": cob,
        "distribuicao": fechamento_dist.distribuicao(d26, d22, completas),
        "tamanho": fechamento_dist.por_tamanho(d26, d22, completas),
        "tipo_local": fechamento_dist.por_tipo(d26, d22, completas),
        "persistencia": fechamento_persist.persistencia(d26, d22, principais),
        "voto": {
            "bootstrap": fechamento_modelo.BOOT,
            "semente": fechamento_modelo.SEMENTE,
            "metricas": fechamento_voto.ROTULO_METRICA,
            "estimadores": ests,
        },
        "lula_hora": fechamento_voto.correlacao_lula(v),
        "conferencia_secoes": fechamento_voto.conferencia_w6(todas, secoes_json),
        "explicacoes": fechamento_voto.explicacoes(v, principais, ests),
        "amostras": fechamento_voto.amostras(v),
        "limites": fechamento_texto.LIMITES,
    }
    dados["achados"] = fechamento_texto.achados(dados)
    texto = json.dumps(
        dados, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    if fechamento_texto.PROIBIDO in texto:
        raise ValueError("travessão no JSON")
    if "fraude" in texto.lower():
        raise ValueError("palavra proibida no JSON")
    if len(texto.encode()) > LIMITE_BYTES:
        raise ValueError(
            f"fechamento.json com {len(texto.encode())} bytes, acima de 2 MB"
        )
    a.saida_json.parent.mkdir(parents=True, exist_ok=True)
    a.saida_json.write_text(texto, encoding="utf-8")
    a.saida_md.write_text(fechamento_texto.memorando(dados), encoding="utf-8")
    print(
        f"{rel(a.saida_json)}: {len(texto) / 1e6:.2f} MB; {cob['secoes_2026']} seções de 2026, "
        f"{len(completas)} UFs completas; parcial={cob['parcial']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
