#!/usr/bin/env python3
"""Onde colocar fiscal: prioridade de fiscalização por seção para o 2º turno de 2026.

Lê, só para leitura, os boletins de urna por seção (``apuracao/data/secoes_2026.sqlite``),
o cadastro de locais (``data/outputs/locais_votacao_2026.sqlite``), as versões dos
arquivos de zona do TSE (``apuracao/data/apuracao.sqlite``), o presidente por seção de
2022 e os JSONs dos capítulos 11 e 12 (``secoes.json``, ``anomalias.json``,
``fechamento.json``, ``contexto_seguranca.json``). Aplica os doze critérios declarados
(``scripts/apuracao_2026/fiscais_criterios.py``) e grava:

- ``analysis/apuracao_2026/dados/fiscais.json`` (contrato em
  ``analysis/apuracao_2026/CONTRATO_FISCAIS.md``);
- ``docs/assets/fiscais_2026.csv``, ``docs/assets/fiscais_2026_por_local.csv`` e
  ``docs/assets/fiscais_2026.xlsx``;
- ``analysis/apuracao_2026/fiscais.md`` (método, achados e limites).

A camada de risco do território vem de ``scripts/apuracao-2026-fiscais-risco.py``
(arquivos em ``data/outputs/fiscais_risco_*.csv*``) e do acesso por estrada (OSRM, com
cache em ``data/outputs/fiscais_osrm_cache.json``); sem esses arquivos, os campos
ficam nulos e ``meta.fontes_risco`` diz por quê.

Atipicidade estatística não é irregularidade; a lista é de prioridade de
fiscalização, não de acusação; o que resolve cada item é a ata da mesa, o log da urna
e a presença do fiscal. Uso:

    python3 scripts/apuracao-2026-fiscais.py
    python3 scripts/apuracao-2026-fiscais.py --sem-osrm
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2026 import fiscais_agregados as fa
from apuracao_2026 import fiscais_base as fb
from apuracao_2026 import fiscais_criterios as fc
from apuracao_2026 import fiscais_export as fx
from apuracao_2026 import fiscais_regras as fr
from apuracao_2026 import fiscais_territorio as fter
from apuracao_2026 import fiscais_texto as t
from apuracao_2026 import secoes_2022, secoes_base
from apuracao_2026.dados import regiao

ROOT = Path(__file__).resolve().parents[1]
DB_SECOES = ROOT / "apuracao/data/secoes_2026.sqlite"
DB_LOCAIS = ROOT / "data/outputs/locais_votacao_2026.sqlite"
DB_APURACAO = ROOT / "apuracao/data/apuracao.sqlite"
LOG = ROOT / "apuracao/data/logs/secoes-20261005.log"
DADOS = ROOT / "analysis/apuracao_2026/dados"
SECOES = DADOS / "secoes.json"
ANOMALIAS = DADOS / "anomalias.json"
FECHAMENTO = DADOS / "fechamento.json"
CONTEXTO = DADOS / "contexto_seguranca.json"
ZIP_VOTOS_2022 = (
    ROOT / "data/raw/tse_resultados/votacao_secao_2022/votacao_secao_2022_BR.zip"
)
ZIP_DETALHE_2022 = ROOT / "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip"
CACHE_2022 = ROOT / "data/outputs/presidente_secao_2022.csv.gz"
SAIDA_JSON = DADOS / "fiscais.json"
SAIDA_MD = ROOT / "analysis/apuracao_2026/fiscais.md"
CSV_SECOES = ROOT / "docs/assets/fiscais_2026.csv"
CSV_LOCAIS = ROOT / "docs/assets/fiscais_2026_por_local.csv"
XLSX = ROOT / "docs/assets/fiscais_2026.xlsx"


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def fonte(
    chave: str, caminho: Path, descricao: str, hash_: bool = True
) -> dict[str, Any]:
    st = caminho.stat()
    return {
        "chave": chave,
        "caminho": rel(caminho),
        "descricao": descricao,
        "bytes": st.st_size,
        "modificado_em": datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "sha256": fb.sha256(caminho) if hash_ else None,
        "motivo_sem_hash": (
            None
            if hash_
            else "banco ainda gravado pelo coletor: vale o instante (tamanho e data)"
        ),
    }


def sem_arquivo(base: secoes_base.Base, df: pd.DataFrame) -> pd.DataFrame:
    """As seções sem `aux.json` publicado, com o contexto da zona do universo."""
    s = fb.ler_sem_arquivo(DB_SECOES, DB_LOCAIS)
    if s.empty:
        return s
    ibge = secoes_base.ler_ibge(DB_APURACAO)
    s["ibge"] = s["mun"].map(ibge)
    s["regiao"] = s["uf"].map(regiao)
    s["tipo_inferido"] = [
        secoes_base.tipo_local(*a)
        for a in zip(
            s["uf"],
            s["tipo_local"],
            s["local"],
            s["bairro"],
            s["endereco"],
            strict=True,
        )
    ]
    cep = fb.ler_cep(DB_LOCAIS)
    s = s.merge(cep, on=secoes_base.CHAVES, how="left")
    z = df.drop_duplicates(["uf", "mun", "zona"])[
        [
            "uf",
            "mun",
            "zona",
            "zona_lula_pct",
            "zona_flavio_pct",
            "uf_lula_pct",
            "uf_flavio_pct",
        ]
    ]
    s = s.merge(z, on=["uf", "mun", "zona"], how="left")
    s["local_id"] = [
        fb.local_id(u, m, zz, ln, sec)
        for u, m, zz, ln, sec in zip(
            s["uf"], s["mun"], s["zona"], s["local_nr"], s["secao"], strict=True
        )
    ]
    for c in (
        "comparecimento",
        "validos",
        "brancos",
        "nulos",
        f"v{fb.LULA}",
        f"v{fb.FLAVIO}",
    ):
        s[c] = np.nan
    s["explicacao_codigos"] = fb.codigos_explicacao(s.assign(tipo_urna=1))
    marcas = fc.finalizar(fc.marcas_sem_arquivo(len(s)), s["explicacao_codigos"])
    return pd.concat([s.reset_index(drop=True), marcas], axis=1)


def criterios_json(
    sin: pd.DataFrame, fechamento: dict[str, Any]
) -> list[dict[str, Any]]:
    crits = [dict(c) for c in fr.CRITERIOS]
    fr.completar(crits, fechamento)
    out = []
    for c in crits:
        tem = sin["criterios"].map(lambda cs, i=c["id"]: i in cs)
        g = sin[tem]
        so = g["criterios"].map(lambda cs: len(cs) == 1)
        peso: Any = fc.PESOS.get(c["id"])
        if c["id"] == "h":
            peso = {
                "sem_arquivo": fc.PESOS["h_sem_arquivo"],
                "zona_congelada": fc.PESOS["h_zona_congelada"],
            }
        out.append(
            c
            | {
                "peso": peso,
                "secoes": len(g),
                "secoes_por_nivel": {
                    n: int((g["nivel"] == n).sum()) for n in fc.NIVEIS
                },
                "aptos": int(g["aptos"].fillna(0).sum()),
                "so_este": int(so.sum()),
            }
        )
    return out


def preparar() -> dict[str, Any]:
    """Lê os bancos e os JSONs, aplica os critérios e devolve o contexto da rodada."""
    t0 = time.time()
    base = secoes_base.montar(DB_SECOES, DB_LOCAIS, DB_APURACAO, LOG)
    print(
        f"base: {len(base.secoes)} válidas ({time.time() - t0:.0f} s)", file=sys.stderr
    )
    df = fb.universo(base, fb.ler_cep(DB_LOCAIS))
    n0 = len(df)
    s22 = secoes_2022.presidente_2022(ZIP_VOTOS_2022, ZIP_DETALHE_2022, CACHE_2022)
    df = fb.com_2022(df, s22)
    if len(df) != n0:
        raise ValueError("o casamento com 2022 duplicou seções")
    secoes = fb.carregar_json(SECOES)
    anomalias = fb.carregar_json(ANOMALIAS)
    fechamento = fb.carregar_json(FECHAMENTO)
    contexto = fb.contexto_por_municipio(fb.carregar_json(CONTEXTO))
    mist = fb.mistura(df, secoes["clusters"])
    print(f"mistura: {mist['conferencia']} ({time.time() - t0:.0f} s)", file=sys.stderr)
    df["_loglik"], df["_cluster"] = mist["loglik"], mist["cluster"]
    cong = fb.zonas_congeladas(DB_APURACAO)
    marca_cong = fb.secoes_congeladas(df, cong)
    topo = fb.topo_anomalias(anomalias)
    df["enclave_2022"] = fc.crit_a(df)["enclave_2022"].to_numpy()
    df["explicacao_codigos"] = fb.codigos_explicacao(df)
    marcas = fc.aplicar(df, mist["posicao"], marca_cong, topo)
    full = pd.concat([df.drop(columns=["enclave_2022"]), marcas], axis=1)
    sem = sem_arquivo(base, df)
    sin = pd.concat([full[full["pontuacao"] > 0], sem], ignore_index=True)
    sin = fa.ordenar(sin).reset_index(drop=True)
    print(f"sinalizadas: {len(sin)} ({time.time() - t0:.0f} s)", file=sys.stderr)

    return {
        "t0": t0,
        "df": df,
        "sin": sin,
        "sem": sem,
        "mist": mist,
        "cong": cong,
        "topo": topo,
        "secoes": secoes,
        "fechamento": fechamento,
        "contexto": contexto,
    }


def publicar(ctx: dict[str, Any], usar_osrm: bool, saida_json: Path) -> int:
    """Monta o JSON, os exportáveis e o memorando a partir do contexto da rodada."""
    t0, df, sin, sem = ctx["t0"], ctx["df"], ctx["sin"], ctx["sem"]
    mist, cong, topo = ctx["mist"], ctx["cong"], ctx["topo"]
    secoes, fechamento, contexto = ctx["secoes"], ctx["fechamento"], ctx["contexto"]
    loc_u = fa.locais_universo(df)
    mun_u = fa.municipios_universo(df)
    ctx_crime = {
        i["id"]
        for i in fb.carregar_json(CONTEXTO).get("itens", [])
        if i.get("tema") == "faccao_milicia"
    }
    terr = fter.territorio(sin, loc_u, usar_osrm=usar_osrm, ctx_validos=ctx_crime)
    rotulos = {
        int(c["id"]): f"grupo {int(c['id']) + 1}: {c['rotulo']}"
        for c in secoes["clusters"]["componentes"]
    }
    extra = {
        "contexto": contexto,
        "topo": topo,
        "congeladas": {(z["uf"].lower(), z["mun_tse"], z["zona"]): z for z in cong},
        "rotulos_grupo": rotulos,
    }
    registros = [
        fa.secao_fiscal(r, extra, terr["por_local"].get(r["local_id"]))
        for r in sin.to_dict("records")
    ]
    locais = fa.por_local(sin, loc_u, contexto, terr["por_local"])
    muni_todos = fa.municipios_sinalizados(sin, mun_u, contexto)
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fontes = [
        fonte(
            "boletins",
            DB_SECOES,
            "boletins de urna e aux.json por seção, 1º turno de 2026 (TSE)",
        ),
        fonte(
            "locais", DB_LOCAIS, "cadastro de locais de votação 2026 do TSE, por seção"
        ),
        fonte(
            "apuracao",
            DB_APURACAO,
            "versões dos arquivos de zona do TSE e lista de candidaturas",
            hash_=False,
        ),
        fonte(
            "presidente_2022", ZIP_VOTOS_2022, "votos por candidato e seção, 2022 (TSE)"
        ),
        fonte(
            "detalhe_2022",
            ZIP_DETALHE_2022,
            "totais e local de votação por seção, 2022 (TSE)",
        ),
        fonte("secoes", SECOES, "capítulo 12: mistura gaussiana e seções atípicas"),
        fonte("anomalias", ANOMALIAS, "capítulo 11: as 50 zonas mais atípicas"),
        fonte("fechamento", FECHAMENTO, "encerramento por seção e fontes legais"),
        fonte(
            "contexto",
            CONTEXTO,
            "matérias de imprensa sobre segurança e logística no dia",
        ),
    ]
    dados: dict[str, Any] = {
        "titulo": "Onde colocar fiscal: prioridade de fiscalização por seção, 2º turno de 2026",
        "gerado_em": agora,
        "versao_contrato": "1.1",
        "aviso": fr.AVISO,
        "rotulos": fr.ROTULOS,
        "meta": {
            "data_eleicao": "2026-10-04",
            "segundo_turno": "2026-10-25",
            "fonte_segundo_turno": "analysis/apuracao_2026/BRIEF.md",
            "fontes": fontes,
            "criterios": [
                {
                    "id": c["id"],
                    "regra": c["regra"],
                    "limiar": c["limiar"],
                    "peso": fc.PESOS.get(c["id"]),
                }
                for c in fr.CRITERIOS
            ],
            "pesos": fr.pesos_json(),
            "cortes_nivel": fr.cortes_json(),
            "explicacoes_comuns": fb.EXPLICACOES,
            "base_legal": t.base_legal(fechamento),
            "universo": {
                "secoes_validas_cap12": int(df["cap12"].sum()),
                "secoes_zona_divergente_integras": int((~df["cap12"]).sum()),
                "secoes_sem_arquivo": len(sem),
                "secoes_universo": len(df) + len(sem),
                "secoes_na_mistura": mist["secoes"],
            },
            "mistura": {
                k: mist[k]
                for k in ("secoes", "iteracoes", "loglik_media", "conferencia")
            },
            "fontes_risco": terr["fontes"],
            "referencias_crime": terr["referencias_crime"],
            "risco_regra": terr["regra"],
            "exportaveis": [],
        },
        "criterios": criterios_json(sin, fechamento),
        "secoes": registros,
        "destaques": [r for r in registros if r["nivel"] in ("alta", "media")][
            : fa.N_DESTAQUES
        ],
        "por_uf": fa.por_uf(sin, df),
        "por_municipio": fa.por_municipio(muni_todos),
        "por_zona": fa.por_zona(sin, df, topo, extra["congeladas"]),
        "por_local": locais,
        "prioridade_pl": fa.prioridade_pl(sin, locais, muni_todos, mun_u),
        "sensibilidade": fa.sensibilidade(sin, locais),
        "resumo": fa.resumo(sin, df, loc_u, len(df) + len(sem)),
        "mapa": fa.mapa(locais),
        "sem_arquivo": [r for r in registros if r["sem_boletim"]],
        "zonas_congeladas": cong,
    }
    dados["sensibilidade"]["leitura"] = t.leitura_sensibilidade(dados["sensibilidade"])
    dados["achados"] = t.achados(dados)
    dados["limites"] = t.LIMITES

    exp = []
    info = fx.escrever_csv(CSV_SECOES, registros, fx.COLUNAS_SECAO)
    exp.append(
        {
            "formato": "csv",
            "caminho": rel(CSV_SECOES),
            "conteudo": "uma linha por seção sinalizada",
            **info,
            **fx.assinatura(CSV_SECOES),
        }
    )
    info = fx.escrever_csv(CSV_LOCAIS, locais, fx.COLUNAS_LOCAL)
    exp.append(
        {
            "formato": "csv",
            "caminho": rel(CSV_LOCAIS),
            "conteudo": "uma linha por local de votação com seção sinalizada",
            **info,
            **fx.assinatura(CSV_LOCAIS),
        }
    )
    fx.escrever_excel(XLSX, dados, muni_todos)
    exp.append(
        {
            "formato": "xlsx",
            "caminho": rel(XLSX),
            "conteudo": "abas Leia-me, Seções, Locais, Municípios, UFs, Critérios e Riscos",
            "linhas": len(registros),
            "abas": [
                "Leia-me",
                "Seções",
                "Locais",
                "Municípios",
                "UFs",
                "Critérios",
                "Riscos",
            ],
            **fx.assinatura(XLSX),
        }
    )
    dados["meta"]["exportaveis"] = exp
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    if "—" in texto:
        raise ValueError("travessão no JSON")
    saida_json.parent.mkdir(parents=True, exist_ok=True)
    saida_json.write_text(texto, encoding="utf-8")
    SAIDA_MD.write_text(t.memorando(dados), encoding="utf-8")
    print(
        f"{rel(saida_json)}: {len(texto) / 1e6:.2f} MB; {len(registros)} seções "
        f"sinalizadas; {len(locais)} locais ({time.time() - t0:.0f} s)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--sem-osrm", action="store_true", help="não consulta o OSRM")
    ap.add_argument("--saida-json", type=Path, default=SAIDA_JSON)
    a = ap.parse_args(argv)
    return publicar(preparar(), not a.sem_osrm, a.saida_json)


if __name__ == "__main__":
    raise SystemExit(main())
