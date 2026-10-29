#!/usr/bin/env python3
"""Cruza os recuos de carimbo com modelo e geografia, sem inferir causalidade."""

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    fonte = ROOT / "docs/assets/politize_se/relogios/indice.json"
    indice = json.loads(fonte.read_text())
    sinais = {(r["uf"], r["mun"], r["zona"], r["secao"]): r for r in indice["sinais"]}
    base, cobertas, casos = Counter(), Counter(), Counter()
    municipios = Counter()
    banco = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
    metricas = ROOT / "data/outputs/logs_urnas_2t_2026.sqlite"
    with sqlite3.connect(f"file:{banco}?mode=ro", uri=True) as con:
        con.execute("ATTACH DATABASE ? AS logs", (f"file:{metricas}?mode=ro",))
        query = """SELECT s.uf,s.mun,s.zona,s.secao,b.modelo_urna,
            m.status='ok' AND s.log_sha256=m.sha256 AND s.log_sha256 IS NOT NULL
            FROM secao s LEFT JOIN bu b USING(uf,mun,zona,secao)
            LEFT JOIN logs.metricas m USING(uf,mun,zona,secao)
            WHERE upper(s.uf)!='ZZ' AND (s.nsp IS NULL OR s.nsp=0 OR s.nsp=s.secao)
            ORDER BY s.uf,s.mun,s.zona,s.secao"""
        for uf, mun, zona, secao, modelo, ok in con.execute(query):
            key = (uf.upper(), mun, zona, secao)
            sinal = sinais.get(key)
            recortes = [
                "Brasil",
                "Jaú" if key[:2] == ("SP", "66079") else "Brasil sem Jaú",
            ]
            for recorte in recortes:
                grupo = (recorte, modelo or "Não identificado")
                base[grupo] += 1
                cobertas[grupo] += bool(ok)
                casos[grupo] += bool(sinal)
            if sinal:
                assert ok, key
                municipios[(uf, mun, sinal["municipio"], modelo)] += 1
    assert sum(v for (r, _), v in casos.items() if r == "Brasil") == 141
    assert sum(v for (r, _), v in cobertas.items() if r == "Brasil") == 497871
    resultado = {
        "fonte": str(fonte.relative_to(ROOT)),
        "fonte_sha256": hashlib.sha256(fonte.read_bytes()).hexdigest(),
        "metodo": "Seções principais domésticas; modelo do BU. Taxa usa logs com vínculo de hash verificado. Recorte sem Jaú é diagnóstico geográfico exploratório, não ajuste causal.",
        "grupos": [
            {
                "recorte": r,
                "modelo": m,
                "secoes": base[r, m],
                "logs_verificados": cobertas[r, m],
                "sinalizadas": casos[r, m],
                "taxa_pct": (
                    100 * casos[r, m] / cobertas[r, m] if cobertas[r, m] else None
                ),
            }
            for r, m in sorted(base)
        ],
        "municipios_modelos": [
            {"uf": u, "mun": m, "municipio": n, "modelo": v, "casos": c}
            for (u, m, n, v), c in municipios.most_common()
        ],
    }
    destino = ROOT / "analysis/politize_se/relogios-modelos.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(resultado["grupos"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
