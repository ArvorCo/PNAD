#!/usr/bin/env python3
"""Comparação 2022 × 2026 de todos os cargos gerais para o dossiê da apuração.

Lê só fontes locais: os pacotes do TSE de 2018 e 2022 em
`data/raw/tse_resultados/`, o boletim final `apuracao/data/boletins/final.json`,
`analysis/apuracao_2026/dados/presidente.json` (quando existe) e o banco da
apuração em modo somente leitura. Grava:

- `analysis/apuracao_2026/dados/comparacao_2022.json`;
- `analysis/apuracao_2026/comparacao_2022.md` (os doze achados, com número e
  origem, e a tabela de partidos assumida).

Uso:
    python3 scripts/apuracao-2026-comparacao.py
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from apuracao_2026 import comparacao_casas, comparacao_secoes, comparacao_texto
from apuracao_2026.comparacao import SUCESSORES
from apuracao_2026.comparacao_fontes import carregar
from apuracao_2026.contexto import ROOT, SAIDA
from apuracao_2026.dados import iso_z

JSON_SAIDA = SAIDA / "comparacao_2022.json"
TRAVESSAO = "\u2014"
MD_SAIDA = ROOT / "analysis/apuracao_2026/comparacao_2022.md"


def pressupostos() -> list[str]:
    return [
        "Eleito é o que o TSE grava em DS_SIT_TOT_TURNO (ELEITO, ELEITO POR QP, "
        "ELEITO POR MÉDIA) no pacote corrente, que incorpora retotalizações "
        "posteriores à eleição; a bancada pode diferir da diplomada em dezembro de 2022.",
        "Eleitos da urna, não titulares atuais: suplência, licença, morte e troca de "
        "partido depois da eleição ficam fora, salvo a exceção já declarada pela casa "
        "para Cleitinho (MG, Senado 2022).",
        "Campo de 2018 e 2022 pela tabela da casa (apuracao/public/campos.json); "
        "sigla extinta herda o campo do sucessor de 2026 (tabela `partidos`).",
        "Em 2018 o PSL vai ao União Brasil (centro-direita) pela regra de sucessão; "
        "a contagem com o PSL de 2018 como direita sai em `sensibilidade_psl_2018_direita`.",
        "Teto da direita de 2018 e 2022 (sensibilidade, não regra): toda sigla extinta que "
        "a sucessão leva à centro-direita conta como direita; dá o piso do crescimento da "
        "direita e não muda o bloco de direita e centro-direita.",
        "Câmara de 2026: UFs marcadas em `ufs_provisorias_2026` usam a alocação "
        "pelo quociente do telão, que reproduziu nome a nome o TSE nas UFs fechadas.",
        "Votos de partido na Câmara: nominais válidos mais legenda; no MA de 2022 só "
        "nominais, porque o pacote de partidos do TSE não traz o cargo.",
        "Governador de RR: a comparação usa a eleição ordinária de 2022; a suplementar "
        "de 21/06/2026 que o pacote traz fica registrada à parte.",
    ]


def main() -> None:
    inicio = time.time()
    f = carregar()
    pres = comparacao_secoes.presidente(f)
    cam = comparacao_secoes.camara(f)
    sen = comparacao_casas.senado(f)
    gov = comparacao_casas.governadores(f)
    ass = comparacao_casas.assembleias(f)
    partidos = comparacao_casas.tabela_partidos(f)
    corpo = {
        "meta": {
            "gerado_em": iso_z(datetime.now(timezone.utc)),
            "script": "scripts/apuracao-2026-comparacao.py",
            "arquivo": "comparacao_2022.json",
            "final_json_gerado_em": f.final["gerado_em"],
            "fontes": f.arquivos,
        },
        "pressupostos": pressupostos(),
        "partidos": {
            "sucessores_declarados": {
                k: {
                    "sigla_2026": v.sigla_2026,
                    "tipo": v.tipo,
                    "descricao": v.descricao,
                }
                for k, v in SUCESSORES.items()
            },
            "siglas_2018_2022": partidos,
        },
        "presidente": pres,
        "camara": cam,
        "senado": sen,
        "governadores": gov,
        "assembleias": ass,
    }
    texto = json.dumps(corpo, ensure_ascii=False, indent=1)
    if TRAVESSAO in texto:
        raise RuntimeError("comparacao_2022.json: travessão no texto gerado")
    JSON_SAIDA.write_text(texto + "\n", encoding="utf-8")
    md = comparacao_texto.escrever(corpo)
    if TRAVESSAO in md:
        raise RuntimeError("comparacao_2022.md: travessão no texto gerado")
    MD_SAIDA.write_text(md, encoding="utf-8")
    for caminho in (JSON_SAIDA, MD_SAIDA):
        print(f"{caminho.relative_to(ROOT)}: {caminho.stat().st_size:,} bytes")
    print(f"{time.time() - inicio:.1f} s")


if __name__ == "__main__":
    main()
