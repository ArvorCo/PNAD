#!/usr/bin/env python3
"""Análise por seção (boletins de urna), presidente, 1º turno de 2026.

Lê, só para leitura, os boletins de urna coletados seção a seção
(``apuracao/data/secoes_2026.sqlite``), o cadastro de locais de votação
(``data/outputs/locais_votacao_2026.sqlite``), a lista de candidaturas
(``apuracao/data/apuracao.sqlite``), o presidente por seção de 2022 (dados
abertos do TSE) e as zonas mais atípicas de ``anomalias.json``. Grava:

- ``analysis/apuracao_2026/dados/secoes.json`` (contrato em
  ``analysis/apuracao_2026/CONTRATO_SECOES.md``);
- ``analysis/apuracao_2026/secoes.md`` (método, achados e limites).

Sem ``--parcial`` exige a coleta completa (nenhuma seção pendente nem com erro).
Atípico não é irregularidade. Uso:

    python3 scripts/apuracao-2026-secoes.py --parcial
    python3 scripts/apuracao-2026-secoes.py
    python3 scripts/apuracao-2026-secoes.py --so-urna
    python3 scripts/apuracao-2026-secoes.py --so-clusters
    python3 scripts/apuracao-2026-secoes.py --so-textos

``--so-urna`` recarrega o JSON existente e refaz só o bloco ``urna`` (e os
achados e o memorando que dependem dele), sem refazer a mistura gaussiana.
``--so-clusters`` faz o mesmo com o bloco ``clusters`` (a mistura gaussiana das
cinco proporções do eleitorado e os registros das duas tentativas em log-razão),
sem ler os dados de 2022 nem
refazer os extremos e o modelo de urna; os registros das tentativas em
log-razão são reaproveitados do JSON gravado, a menos que se peça
``--refazer-tentativas`` (o ajuste é determinístico e devolve os mesmos números). ``--so-textos`` não lê banco nenhum:
refaz só os rótulos e as frases do bloco ``clusters`` a partir dos números já
gravados (revisão editorial), e os achados e o memorando.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apuracao_2026 import (
    secoes_2022,
    secoes_base,
    secoes_clusters,
    secoes_extremos,
    secoes_texto,
    secoes_urna,
)

ROOT = Path(__file__).resolve().parents[1]
DB_SECOES = ROOT / "apuracao/data/secoes_2026.sqlite"
DB_LOCAIS = ROOT / "data/outputs/locais_votacao_2026.sqlite"
DB_APURACAO = ROOT / "apuracao/data/apuracao.sqlite"
LOG = ROOT / "apuracao/data/logs/secoes-20261005.log"
FINAL = ROOT / "apuracao/data/boletins/final.json"
ANOMALIAS = ROOT / "analysis/apuracao_2026/dados/anomalias.json"
ZIP_VOTOS_2022 = (
    ROOT / "data/raw/tse_resultados/votacao_secao_2022/votacao_secao_2022_BR.zip"
)
ZIP_DETALHE_2022 = ROOT / "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip"
CACHE_2022 = ROOT / "data/outputs/presidente_secao_2022.csv.gz"
SAIDA_JSON = ROOT / "analysis/apuracao_2026/dados/secoes.json"
SAIDA_MD = ROOT / "analysis/apuracao_2026/secoes.md"

AVISO = (
    "Seção atípica é seção que pede explicação, não indício de irregularidade. "
    "O que resolve cada caso é documento: ata da mesa, log da urna e plano de "
    "alocação das urnas do TRE."
)


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def confere_nacional(base: secoes_base.Base, final: Path) -> dict[str, Any] | None:
    """Soma de todos os boletins (válidos e excluídos) contra o arquivo nacional."""
    if not final.exists():
        return None
    pres = json.loads(final.read_text(encoding="utf-8"))["presidente"]
    tse = {
        "comparecimento": int(pres["comparecimento"]),
        "flavio": next(int(c["votos"]) for c in pres["top5"] if "FLAVIO" in c["nome"]),
        "lula": next(int(c["votos"]) for c in pres["top5"] if c["nome"] == "LULA"),
    }
    todos = [base.secoes, base.excluidas]
    bu = {
        "comparecimento": int(sum(int(d["comparecimento"].sum()) for d in todos)),
        "flavio": int(sum(int(d["v22"].sum()) for d in todos)),
        "lula": int(sum(int(d["v13"].sum()) for d in todos)),
    }
    dif = {k: bu[k] - tse[k] for k in tse}
    texto = (
        "soma de todos os boletins menos o arquivo nacional do TSE: "
        + "; ".join(f"{k} {secoes_base.num(v, 0)}" for k, v in dif.items())
        + "."
    )
    return {"tse_final": tse, "boletins": bu, "diferenca": dif, "texto": texto}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--parcial", action="store_true", help="roda com a coleta parcial")
    ap.add_argument("--secoes-db", type=Path, default=DB_SECOES)
    ap.add_argument("--locais-db", type=Path, default=DB_LOCAIS)
    ap.add_argument("--apuracao-db", type=Path, default=DB_APURACAO)
    ap.add_argument("--log", type=Path, default=LOG)
    ap.add_argument("--saida-json", type=Path, default=SAIDA_JSON)
    ap.add_argument("--saida-md", type=Path, default=SAIDA_MD)
    ap.add_argument("--sem-2022", action="store_true", help="não lê os dados de 2022")
    ap.add_argument(
        "--so-urna",
        action="store_true",
        help="refaz só o bloco urna sobre o JSON existente",
    )
    ap.add_argument(
        "--so-clusters",
        action="store_true",
        help="refaz só o bloco clusters sobre o JSON existente",
    )
    ap.add_argument(
        "--refazer-tentativas",
        action="store_true",
        help="com --so-clusters, refaz também as tentativas em log-razão",
    )
    ap.add_argument(
        "--so-textos",
        action="store_true",
        help="refaz só rótulos e frases do bloco clusters, sem ler os bancos",
    )
    a = ap.parse_args(argv)
    if a.so_urna + a.so_clusters + a.so_textos > 1:
        ap.error("use só uma entre --so-urna, --so-clusters e --so-textos")
    if a.so_textos:
        dados = json.loads(a.saida_json.read_text(encoding="utf-8"))
        secoes_clusters.refazer_textos(dados["clusters"], dados["candidatos"])
        dados["limites"] = secoes_texto.LIMITES
        dados["gerado_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return grava(dados, a, dados["cobertura"])

    base = secoes_base.montar(a.secoes_db, a.locais_db, a.apuracao_db, a.log)
    cob = base.cobertura
    completa = cob["secoes_pendentes"] == 0 and cob["secoes_com_erro"] == 0
    if not completa and not a.parcial:
        print(
            f"coleta incompleta: {cob['secoes_pendentes']} seções pendentes, "
            f"{cob['secoes_com_erro']} com erro; use --parcial",
            file=sys.stderr,
        )
        return 2
    cob["parcial"] = not completa
    if completa:
        cob["confere_nacional"] = confere_nacional(base, FINAL)

    if a.so_clusters:
        dados = json.loads(a.saida_json.read_text(encoding="utf-8"))
        anterior = None if a.refazer_tentativas else dados.get("clusters")
        dados["clusters"] = secoes_clusters.clusters(base, anterior)
        dados["limites"] = secoes_texto.LIMITES
        dados["gerado_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return grava(dados, a, cob)
    s22 = None
    if not a.sem_2022:
        s22 = secoes_2022.presidente_2022(ZIP_VOTOS_2022, ZIP_DETALHE_2022, CACHE_2022)
    if a.so_urna:
        dados = json.loads(a.saida_json.read_text(encoding="utf-8"))
        dados["urna"] = secoes_urna.urna(base, s22)
        dados["gerado_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return grava(dados, a, cob)
    anomalias = json.loads(ANOMALIAS.read_text(encoding="utf-8"))

    dados: dict[str, Any] = {
        "titulo": "Análise por seção (boletins de urna), presidente, 1º turno de 2026",
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "versao_contrato": "1.0",
        "aviso": AVISO,
        "fontes": [
            {
                "chave": "boletins",
                "caminho": rel(a.secoes_db),
                "descricao": (
                    "boletins de urna (bu.dat) e logs por seção do 1º turno de 2026, "
                    "coletados em resultados.tse.jus.br/oficial/ele2026/arquivo-urna"
                    "/3220 e decodificados do ASN.1 do TSE"
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
                "descricao": "votos por candidato e seção, presidente, 2022 (TSE)",
            },
            {
                "chave": "detalhe_2022",
                "caminho": rel(ZIP_DETALHE_2022),
                "descricao": "totais e modelo da urna por seção, 2022 (TSE)",
            },
            {
                "chave": "anomalias",
                "caminho": rel(ANOMALIAS),
                "descricao": "triagem por zona já publicada (50 zonas mais atípicas)",
            },
        ],
        "cobertura": cob,
        "candidatos": [
            {"numero": c.numero, "chave": c.chave, "nome": c.nome, "cor": c.cor}
            for c in base.candidatos
        ],
        "extremos": secoes_extremos.extremos(base, anomalias["topo"], s22),
        "clusters": secoes_clusters.clusters(base),
        "urna": secoes_urna.urna(base, s22),
        "outras": secoes_extremos.outras(base),
        "limites": secoes_texto.LIMITES,
    }
    return grava(dados, a, cob)


def grava(dados: dict[str, Any], a: argparse.Namespace, cob: dict[str, Any]) -> int:
    dados["achados"] = secoes_texto.achados(dados)
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    if secoes_texto.PROIBIDO in texto:
        raise ValueError("travessão no JSON")
    a.saida_json.parent.mkdir(parents=True, exist_ok=True)
    a.saida_json.write_text(texto, encoding="utf-8")
    a.saida_md.write_text(secoes_texto.memorando(dados), encoding="utf-8")
    print(
        f"{rel(a.saida_json)}: {len(texto) / 1e6:.2f} MB; "
        f"{cob['secoes_validas']} seções válidas; parcial={cob['parcial']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
