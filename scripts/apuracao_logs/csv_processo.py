"""Tabela longa de processos por tipo; referências e métricas com chave da seção."""

import csv
import gzip
import io

from .processo import TIPOS


def exportar(linhas, destino):
    colunas = [
        "uf",
        "mun",
        "zona",
        "secao",
        "modelo",
        "cargos",
        "tipo",
        "n",
        "media_s",
        "p10_s",
        "mediana_s",
        "p90_s",
        "max_s",
        "referencia_mediana_s",
        "escala_s",
        "pares",
        "elegivel",
        "sinal_rapido",
    ]
    with (
        destino.open("wb") as arquivo,
        gzip.GzipFile(filename="", mode="wb", fileobj=arquivo, mtime=0) as gz,
        io.TextIOWrapper(gz, encoding="utf-8", newline="") as txt,
    ):
        w = csv.DictWriter(txt, fieldnames=colunas)
        w.writeheader()
        for row in linhas:
            for tipo in TIPOS:
                d = row["processo_tipos"].get(tipo, {})
                ref = row["referencias_processo"].get(tipo, {})
                med, esc = ref.get("mediana"), ref.get("escala")
                ok = bool(
                    row["processo_elegivel"]
                    and row["elegivel_bio"]
                    and d.get("n", 0) >= 30
                    and med is not None
                )
                w.writerow(
                    {
                        **{
                            k: row[k]
                            for k in ("uf", "mun", "zona", "secao", "modelo", "cargos")
                        },
                        "tipo": tipo,
                        "n": d.get("n", 0),
                        **{
                            col: d.get(chave)
                            for col, chave in (
                                ("media_s", "media"),
                                ("p10_s", "p10"),
                                ("mediana_s", "p50"),
                                ("p90_s", "p90"),
                                ("max_s", "max"),
                            )
                        },
                        "referencia_mediana_s": med,
                        "escala_s": esc if med is not None else None,
                        "pares": ref.get("pares", 0),
                        "elegivel": ok,
                        "sinal_rapido": bool(
                            ok and d["p50"] < med - 4 * esc and d["p50"] < 0.5 * med
                        ),
                    }
                )
