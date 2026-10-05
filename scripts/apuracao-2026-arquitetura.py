#!/usr/bin/env python3
"""Dimensionamento da noite e fontes da arquitetura de totalização do TSE.

Lê só fontes locais, em modo somente leitura: a coleta seção a seção
(`apuracao/data/secoes_2026.sqlite`), o banco da apuração
(`apuracao/data/apuracao.sqlite`), o pacote de 2022 por seção
(`data/raw/tse_resultados/detalhe_votacao_secao_2022.zip`),
`analysis/apuracao_2026/dados/linha_do_tempo.json` e as fontes documentais
curadas em `analysis/apuracao_2026/fontes_arquitetura.json`. Grava
`analysis/apuracao_2026/dados/arquitetura.json`.

Uso:
    python3 scripts/apuracao-2026-arquitetura.py
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone

from apuracao_2026 import arquitetura as A
from apuracao_2026.contexto import BANCO, ROOT, SAIDA, TSE_RESULTADOS
from apuracao_2026.dados import iso_z

SECOES_DB = ROOT / "apuracao/data/secoes_2026.sqlite"
ZIP_2022 = TSE_RESULTADOS / "detalhe_votacao_secao_2022.zip"
FONTES = ROOT / "analysis/apuracao_2026/fontes_arquitetura.json"
LINHA = SAIDA / "linha_do_tempo.json"
JSON_SAIDA = SAIDA / "arquitetura.json"
UFS = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
]


def versoes_nacionais(L: dict) -> list[dict]:
    v = L["nacional"]["versoes"]
    linhas = [dict(zip(v["colunas"], r, strict=False)) for r in v["linhas"]]
    return [x for x in linhas if (x["st"] or 0) > 0]


def main() -> None:
    L = json.loads(LINHA.read_text(encoding="utf-8"))
    fontes = json.loads(FONTES.read_text(encoding="utf-8"))

    s26 = A.ler_secoes_2026(SECOES_DB)
    rec = s26["recebimentos"]
    serie26 = A.por_minuto(rec, A.INICIO, A.FIM)
    lac26 = A.lacunas(rec, A.INICIO.replace(minute=10), A.FIM)
    pico_amostra = max(n for _, n in serie26)

    s22 = A.ler_2022(ZIP_2022)
    serie22 = A.por_minuto(s22["recebimentos"], A.INICIO_2022, A.FIM_2022)
    q22 = A.quantis(s22["atraso_s"], (0.5, 0.9, 0.99))
    pico22 = max(serie22, key=lambda x: x[1])

    pub = A.ler_publicacao(BANCO, "2026-10-04T20:00", "2026-10-05T00:30")
    serie_pub = A.publicacao_brt(pub["minutos"], A.INICIO, A.FIM)
    pico_pub = max(serie_pub, key=lambda x: x[1])
    pico_pub_mb = max(serie_pub, key=lambda x: x[2])

    vs = versoes_nacionais(L)
    taxas = A.taxas_nacionais(vs)
    pico_nac = A.pico_sustentado(taxas)
    paradas = [
        p
        for p in L["travamentos"]["nacional"]
        if (p.get("secoes_no_salto") or 0) > 1000
    ]
    longa = max(paradas, key=lambda p: p["minutos"])
    pausa = L["pausa_geral"]["lacunas"][0]

    bu = A.resumo_bytes(s26["bu_bytes"])
    log = A.resumo_bytes(s26["log_bytes"])
    linhas_sec = s26["linhas_voto"] / s26["secoes_com_voto"]
    n_amostra = len(rec)
    dim = A.dimensionar(
        secoes_amostra=n_amostra,
        bu_bytes_medio=bu["media"],
        log_bytes_medio=log["media"],
        linhas_por_secao=linhas_sec,
        pico_secoes_min=pico_nac["secoes_por_minuto"],
        secoes_paradas=longa["secoes_no_salto"],
    )
    fator = dim["fator_extrapolacao"]

    saida = {
        "meta": {
            "gerado_em": iso_z(datetime.now(timezone.utc)),
            "script": "scripts/apuracao-2026-arquitetura.py",
            "arquivo": "arquitetura.json",
            "regra": (
                "Recebimento pelo carimbo dr_hr do aux de cada seção (hora de Brasília); "
                "extrapolação proporcional da amostra para 499.248 seções; publicação = "
                "versões novas capturadas pelo coletor (piso do que o TSE gerou)."
            ),
        },
        "amostra": {
            "secoes_com_recebimento": n_amostra,
            "ufs_cobertas": s26["ufs_cobertas"],
            "ufs_ausentes": sorted(set(UFS) - set(s26["ufs_cobertas"])),
            "secoes_pais": A.SECOES_PAIS,
            "fracao_do_pais": round(n_amostra / A.SECOES_PAIS, 4),
            "fator_extrapolacao": fator,
            "recebida_ate_19h14": round(
                sum(1 for t in rec if t < datetime(2026, 10, 4, 19, 14)) / n_amostra, 4
            ),
            "nacional_pst_19h14": next(
                (v["pst"] for v in vs if v["gerado_brt"] >= "2026-10-04 19:14"), None
            ),
            "ressalva": (
                "A coleta cobre as UFs listadas e deixa de fora os maiores colégios do "
                "Centro-Sul, que chegaram mais tarde; a forma da curva nacional difere "
                "da amostra. A série extrapolada mostra a ordem de grandeza, não o "
                "minuto exato do país."
            ),
        },
        "recebimento_2026": {
            "colunas": ["minuto", "secoes_amostra", "secoes_extrapoladas"],
            "linhas": [[m, n, round(n * fator)] for m, n in serie26],
            "pico_amostra_por_minuto": pico_amostra,
            "lacunas": lac26,
        },
        "recebimento_2022": {
            "colunas": ["minuto", "secoes"],
            "linhas": serie22,
            "secoes": len(s22["recebimentos"]),
            "pico": {"minuto": pico22[0], "secoes": pico22[1]},
            "atraso_recebimento_totalizacao_s": {
                "p50": q22[0],
                "p90": q22[1],
                "p99": q22[2],
                "n": len(s22["atraso_s"]),
            },
        },
        "publicacao_2026": {
            "colunas": ["minuto", "versoes", "mb"],
            "linhas": serie_pub,
            "pico_versoes": {"minuto": pico_pub[0], "versoes": pico_pub[1]},
            "pico_mb": {"minuto": pico_pub_mb[0], "mb": pico_pub_mb[2]},
            "versoes_total_banco": pub["versoes_total"],
            "mediana_versoes_por_minuto_18h_19h30": statistics.median(
                n for m, n, _ in serie_pub if "18:00" <= m < "19:30"
            ),
            "minutos_sem_versao_19h33_20h01": sum(
                1 for m, n, _ in serie_pub if "19:33" <= m <= "20:01" and n == 0
            ),
        },
        "nacional": {
            "taxas": taxas,
            "pico_sustentado": pico_nac,
            "parada_mais_longa": longa,
            "pausa_geral": {
                "de_brt": pausa["de_brt"],
                "ate_brt": pausa["ate_brt"],
                "minutos": pausa["minutos"],
            },
        },
        "volume": {
            "bu_bytes": bu,
            "log_bytes": log,
            "linhas_por_secao": round(linhas_sec, 1),
            "linhas_por_cargo": s26["linhas_por_cargo"],
            "linhas_voto_amostra": s26["linhas_voto"],
            "secoes_com_voto_amostra": s26["secoes_com_voto"],
            **dim,
            "linhas_por_minuto_nota_tse_2020": 1_000_000,
        },
        "fontes": fontes["fontes"],
        "buscas_sem_achado": fontes["buscas_sem_achado"],
    }
    JSON_SAIDA.write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"{JSON_SAIDA.relative_to(ROOT)}: {JSON_SAIDA.stat().st_size:,} bytes")
    print(
        json.dumps(
            {k: saida[k] for k in ("amostra", "volume")}, ensure_ascii=False, indent=1
        )[:3000]
    )
    print("lacunas 2026:", lac26)
    print("pico nacional:", pico_nac, "pico 2022:", pico22, "atraso 2022:", q22)
    print("publicação:", pico_pub, pico_pub_mb)


if __name__ == "__main__":
    main()
