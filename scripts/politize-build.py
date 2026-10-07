#!/usr/bin/env python3
"""Politize sua vizinhança: build dos JSON do app (contrato em analysis/politize/CONTRATO.md).

Lê, só para leitura, os boletins por seção (``apuracao/data/secoes_2026.sqlite``), o
cadastro de locais (``data/outputs/locais_votacao_2026.sqlite``), o presidente por seção
de 2022, o perfil do eleitorado do TSE (por seção quando o arquivo da UF existe, senão
por zona), a malha de setores do Censo 2022 (R-tree do GeoPackage, ponto a ponto), a
PNADC anual 2025 e as duas pesquisas de 03/10 com voto por renda. Grava em
``docs/assets/politize/dados/``: ``indice.json``, ``mun/<UF>/<mun>.json``,
``zona/<UF>/<zona>.json``, ``cep/<2 dígitos>.json``, ``uf/<UF>.json``,
``geo/<UF>.geojson`` e ``pnad_renda.json``; e o relatório
``analysis/politize/relatorio_build.md``.

Uso::

    python3 scripts/politize-build.py              # build nacional (27 UFs e exterior)
    python3 scripts/politize-build.py --uf AC      # amostra rápida
    python3 scripts/politize-build.py --so-pnad    # só refaz a tabela de renda
    python3 scripts/politize-build.py --sem-setor  # pula o GeoPackage
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from typing import Any

from politize import fontes, fragmentos, montagem, pnad, relatorio
from politize import metricas as mt
from politize.montagem import ResultadoUF


def _ufs(valores: list[str] | None) -> list[str]:
    if not valores:
        return list(fontes.UFS)
    saida = []
    for v in valores:
        for uf in v.split(","):
            uf = uf.strip().upper()
            if uf not in fontes.UFS:
                raise SystemExit(f"UF desconhecida: {uf}")
            if uf not in saida:
                saida.append(uf)
    return saida


def _agora() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _abstencao_referencia(res: ResultadoUF) -> tuple[dict[str, float], float | None]:
    """Abstenção do 2º turno de 2022 por município (seções casadas) e da UF."""
    por_mun: dict[str, list[float]] = {}
    total = [0.0, 0.0]
    for loc in res.locais:
        par = por_mun.setdefault(loc.cad.mun_tse, [0.0, 0.0])
        par[0] += loc.c["aptos22_2t"]
        par[1] += loc.c["comp22_2t"]
        total[0] += loc.c["aptos22_2t"]
        total[1] += loc.c["comp22_2t"]
    mun = {k: mt.pct(a - c, a) for k, (a, c) in por_mun.items() if a}
    return mun, mt.pct(total[1] and total[0] - total[1], total[0])


def _fontes_usadas(resultados: list[ResultadoUF], com_setor: bool) -> list[dict]:
    f = fontes
    lista = [
        (
            "boletins_2026",
            f.DB_SECOES,
            "votos de presidente 1º turno por seção, aptos e comparecimento",
        ),
        (
            "locais_2026",
            f.DB_LOCAIS,
            "local, endereço, bairro, CEP, lat/lon e agregação de seções",
        ),
        (
            "municipios_e_candidaturas_tse",
            f.DB_APURACAO,
            "código IBGE do município e lista oficial de candidaturas a presidente",
        ),
        (
            "presidente_2022",
            f.CSV_2022,
            "Lula e Bolsonaro 1º e 2º turno 2022 por seção, local_nr_2022",
        ),
        (
            "detalhe_2022",
            f.ZIP_DETALHE_2022,
            "aptos e comparecimento do 2º turno de 2022 por seção (abst22_2t_a)",
        ),
        ("pnad_2025", f.CSV_PNAD, "renda domiciliar por UF, escolaridade e situação"),
        ("ipca", f.CSV_IPCA, "correção de preços da renda"),
        ("salario_minimo", f.CSV_SALARIO, "faixas em salários mínimos de 2026"),
        (
            "censo_agregados",
            f.CSV_AGREGADOS,
            "nome oficial do município em caixa normal",
        ),
        ("problemas_uf", f.JSON_PROBLEMAS, "problema mais grave por estado (Quaest)"),
        (
            "transferencia_terceira",
            f.JSON_MIGRACAO,
            "síntese da migração da terceira via (61/39)",
        ),
        (
            "cidades_exterior",
            f.JSON_CIDADES_EXTERIOR,
            "coordenada da cidade para os locais do exterior",
        ),
    ]
    for nome in f.PESQUISAS:
        lista.append(
            (
                f"pesquisa_{nome[:-5]}",
                f.DIR_PESQUISAS / nome,
                "voto por faixa de renda, 1º turno",
            )
        )
    if com_setor:
        lista.append(
            (
                "censo_setores",
                f.GPKG_SETORES,
                "situação e tipo do setor censitário do ponto",
            )
        )
    ufs = [r.uf for r in resultados]
    if any(
        r.meta["locais_perfil_zona"] or r.meta["secoes_perfil_zona"] for r in resultados
    ):
        lista.append(
            ("perfil_zona_2026", f.ZIP_PERFIL_ZONA, "perfil por zona (fallback)")
        )
    for r in resultados:
        if r.meta["perfil_secao"] == "ok":
            lista.append(
                (
                    f"perfil_secao_2026_{r.uf}",
                    f.arquivo_perfil_secao(r.uf),
                    "perfil por seção",
                )
            )
    for uf in ufs:
        origem = f.GEO_MUNDO if uf == "ZZ" else f.DIR_MALHA / f"{uf}.geojson"
        lista.append((f"malha_{uf}", origem, "contorno para o mapa do app"))
    saida = []
    for chave, caminho, uso in lista:
        print(f"  hash {chave}", flush=True)
        saida.append(f.descrever_fonte(chave, caminho, uso))
    return saida


def _mesclar_indice(novo: dict, ufs: list[str]) -> dict:
    """Ao refazer só algumas UFs, mantém no índice as entradas das demais."""
    arq = fontes.SAIDA / "indice.json"
    if not arq.exists():
        return novo
    try:
        antigo = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return novo
    if antigo.get("municipios", {}).get("colunas") != novo["municipios"]["colunas"]:
        return novo
    refeitas = set(ufs)
    novo["ufs"] = sorted(
        [u for u in antigo.get("ufs", []) if u["uf"] not in refeitas] + novo["ufs"],
        key=lambda u: u["uf"],
    )
    novo["municipios"]["linhas"] = sorted(
        [x for x in antigo["municipios"]["linhas"] if x[0] not in refeitas]
        + novo["municipios"]["linhas"],
        key=lambda x: (x[0], x[1]),
    )
    zonas = {k: v for k, v in antigo.get("zonas", {}).items() if k not in refeitas}
    novo["zonas"] = dict(sorted({**zonas, **novo["zonas"]}.items()))
    novo["escopo"] = sorted(u["uf"] for u in novo["ufs"])
    if antigo.get("escopo") == "nacional" or set(novo["escopo"]) == set(fontes.UFS):
        novo["nacional"] = antigo.get("nacional", novo["nacional"])
        novo["nacional_nota"] = (
            "nacional do último build completo; UFs refeitas: " + ", ".join(ufs)
        )
    return novo


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Build dos JSON do Politize sua vizinhança."
    )
    ap.add_argument(
        "--uf", action="append", help="UF a processar (repita ou use vírgula)"
    )
    ap.add_argument("--so-pnad", action="store_true", help="só refaz a tabela de renda")
    ap.add_argument(
        "--sem-setor", action="store_true", help="não consulta o GeoPackage"
    )
    args = ap.parse_args(argv)
    t0 = time.time()
    tabela = pnad.tabela(refazer=args.so_pnad)
    fragmentos.escrever_pnad(tabela)
    print(f"PNAD: {len(tabela.celulas)} células, preços de {tabela.meta['mes_precos']}")
    if args.so_pnad:
        return 0
    ufs = _ufs(args.uf)
    completo = set(ufs) == set(fontes.UFS)
    numeros = fontes.numeros_presidente()
    municipios = fontes.municipios()
    nomes = fontes.nomes_ibge()
    pesquisas = fontes.ler_pesquisas()
    por_casa = [mt.voto_valido_faixas(p["cruzamentos"]["1t"]) for p in pesquisas]
    voto_faixa = mt.media_casas(por_casa)
    problemas = fontes.ler_problemas()
    s22 = fontes.ler_2022(ufs)
    print(f"2022 lido ({time.time() - t0:.0f} s)", flush=True)
    resultados: list[ResultadoUF] = []
    tempos: dict[str, float] = {}
    for uf in ufs:
        t = time.time()
        res = montagem.montar_uf(
            uf, numeros, s22.get(uf, {}), tabela, voto_faixa, not args.sem_setor
        )
        resultados.append(res)
        tempos[uf] = time.time() - t
        print(
            f"{uf}: {len(res.locais)} locais, perfil {res.meta['perfil_secao']}, "
            f"{tempos[uf]:.1f} s",
            flush=True,
        )
    rec = montagem.recentragem_por_uf(resultados)
    for res in resultados:
        reg = rec["por_uf"].get(res.uf)
        desloc = (
            None
            if reg is None
            else (reg["deslocamento_flavio_pp"], reg["deslocamento_lula_pp"])
        )
        abst_mun, abst_uf = _abstencao_referencia(res)
        for loc in res.locais:
            ref = abst_mun.get(loc.cad.mun_tse, abst_uf)
            montagem.finalizar(loc, desloc, ref)
            for sec in loc.secoes:
                montagem.finalizar(sec, desloc, ref)
    montagem.percentis_potencial(resultados)
    todos = [x for r in resultados for x in r.locais]
    potenciais = [x.m["potencial"] for x in todos if x.m["potencial"] is not None]
    p99 = mt.percentis(potenciais, [99])["p99"]
    linhas_mun: list[list[Any]] = []
    resumo_ufs: list[dict[str, Any]] = []
    zonas: dict[str, list[int]] = {}
    for res in resultados:
        saida = fragmentos.escrever_uf(res, municipios, nomes, tabela, problemas)
        linhas_mun.extend(saida["linhas_indice"])
        resumo_ufs.append(saida["uf"])
        zonas[res.uf], _ = fragmentos.escrever_zonas(res, municipios, nomes)
        print(f"{res.uf}: gravado", flush=True)
    ceps = fragmentos.escrever_ceps(todos, set(ufs))
    nacional = montagem.totais(todos, tabela)
    pj = tabela.json()
    parametros = {
        "taxa_conversao": mt.TAXA_CONVERSAO,
        "taxa_conversao_nota": "hipótese declarada: uma em cada três conversas convence",
        "transferencia_terceira": {
            "sem_escolha": mt.SEM_ESCOLHA,
            "flavio_entre_escolhem": mt.FLAVIO_ENTRE_ESCOLHEM,
            "coef_flavio": round(mt.COEF_FLAVIO_2T, 6),
            "coef_lula": round(mt.COEF_LULA_2T, 6),
            "fonte": (
                "parcela sem escolha: Nexus 21/09, p. 79 (40,4 Flávio, 28,4 Lula, 31 sem "
                "escolha); divisão 61/39 entre quem escolhe: síntese de três fontes "
                "(série de 2º turno, matriz Nexus 28/09 e matriz Datafolha 01/10) em "
                "analysis/predicao_2026"
            ),
            "regra": "brancos, nulos e abstenção não viram voto",
        },
        "teto_potencial": mt.TETO_POTENCIAL,
        "teto_componente": mt.TETO_COMPONENTE,
        "teto_componente_nota": (
            "aplicado antes da soma do potencial, nas duas camadas; c_terceira e "
            "c_ausentes sem teto; valor sem teto em c_perfil_bruto e c_reencontro_bruto"
        ),
        "p99_potencial": None if p99 is None else round(p99, 2),
        "peso_ausentes": mt.PESO_AUSENTES,
        "aptos_min_secao": montagem.APTOS_MIN_SECAO,
        "recentragem": rec,
        "voto_faixa": {
            "faixas": ["ate2", "de2a5", "mais5"],
            "base": "% dos válidos (sem branco/nulo e indecisos), 1º turno",
            **{p["_arquivo"]: v for p, v in zip(pesquisas, por_casa, strict=True)},
            "media": voto_faixa,
        },
        "pnad": {
            "mes_base": pj["mes_base"],
            "mes_precos": pj["mes_precos"],
            "fator_ipca": pj["fator_ipca"],
            "salario_minimo_2026": pj["salario_minimo_2026"],
            "celulas_substituidas": sum(1 for x in pj["linhas"] if x["usa"]),
        },
        "unidades": {
            "_v": "% dos válidos (nominais das candidaturas da lista oficial)",
            "_a": "% dos aptos",
            "_pp": "pontos percentuais",
            "cobertura_2022": "fração de 0 a 1 dos aptos em seções casadas com 2022",
            "renda_": "% do eleitorado por faixa; mediana em reais, arredondada a R$ 10",
            "c_": "votos por 100 aptos",
        },
    }
    print("hash das fontes", flush=True)
    indice = {
        "gerado_em": _agora(),
        "versao_contrato": "1.0",
        "escopo": "nacional" if completo else ufs,
        "fontes": _fontes_usadas(resultados, not args.sem_setor),
        "parametros": parametros,
        "nacional": nacional,
        "ufs": sorted(resumo_ufs, key=lambda u: u["uf"]),
        "municipios": {
            "colunas": list(fragmentos.COLUNAS_MUNICIPIO),
            "linhas": sorted(linhas_mun, key=lambda x: (x[0], x[1])),
        },
        "zonas": dict(sorted(zonas.items())),
    }
    if not completo:
        indice = _mesclar_indice(indice, ufs)
    tamanho = fragmentos.gravar_json(fontes.SAIDA / "indice.json", indice)
    st = relatorio.estatisticas(resultados)
    st["ceps"] = ceps
    meta = {
        "gerado_em": indice["gerado_em"],
        "comando": "python3 scripts/politize-build.py "
        + " ".join(sys.argv[1:] if argv is None else argv),
        "segundos": time.time() - t0,
        "tempos": tempos,
        "indice_bytes": tamanho,
    }
    arq = relatorio.escrever(st, resultados, parametros, nacional, meta)
    print(f"indice.json {tamanho / 1024:.0f} KB; relatório em {fontes.rel(arq)}")
    print(f"tempo total {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
