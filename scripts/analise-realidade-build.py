#!/usr/bin/env python3
"""Gera o relatório geográfico a partir das bases conciliadas e auditadas."""

import csv
import json

from analise_realidade_eleicao.dados import OUTPUT, ROOT, ler
from analise_realidade_eleicao.faixas import faixas
from analise_realidade_eleicao.pagina import corpo
from ga_tag import injetar


def csv_gravar(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    d, a = ler(OUTPUT / "dados.json"), ler(OUTPUT / "auditoria.json")
    t = ler(OUTPUT / "territorio.json")
    d["faixas_flavio"] = faixas(d["municipios"])
    faixa_por_id = {
        ibge: f["rotulo"] for f in d["faixas_flavio"] for ibge in f["municipios"]
    }
    assets = ROOT / "docs/assets/analise_realidade_eleicao"
    assets.mkdir(parents=True, exist_ok=True)
    for name, obj in [("dados", d), ("auditoria", a), ("territorio", t)]:
        (assets / f"{name}.json").write_text(
            json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            + "\n"
        )
    rows = []
    for m in d["municipios"]:
        rows.append(
            {
                **m,
                "faixa_flavio": faixa_por_id.get(m["ibge"], "Sem classificação"),
                **{
                    f"flavio_menor_{v}": m["ibge"] in ids
                    for v, ids in d["cortes"].items()
                },
            }
        )
    csv_gravar(assets / "municipios.csv", rows)
    csv_gravar(assets / "zonas.csv", d["zonas"])
    csv_gravar(assets / "triagem.csv", a["triagem"]["linhas"])
    csv_gravar(assets / "territorio_locais.csv", t["locais"])
    csv_gravar(assets / "territorio_recortes.csv", t["recortes"])
    # Funciona também via file://: os dados de interação ficam no próprio HTML.
    payload = json.dumps(
        d, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).replace("</", "<\\/")
    head = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A geografia do voto e a auditoria da eleição de 2026 | Arvor</title><meta name="description" content="Renda, progresso social, violência e voto no segundo turno de 2026. Mapas municipais, zonas nas capitais e testes de auditoria com os dois candidatos.">
<link rel="canonical" href="https://brasil.arvor.co/analise_realidade_eleicao.html"><meta property="og:title" content="A geografia do voto. E o que pede explicação."><meta property="og:description" content="5.571 municípios, 298 zonas nas capitais e uma trilha de auditoria da eleição de 2026."><meta property="og:type" content="article"><meta property="og:url" content="https://brasil.arvor.co/analise_realidade_eleicao.html"><meta property="og:image" content="https://brasil.arvor.co/img/og/analise_realidade_eleicao.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="assets/analise_realidade_eleicao/style.css?v=20261028-faixas"></head><body><nav><a href="index.html">Arvor · Brasil</a><a href="apuracao_2T_2026.html">Dossiê da apuração ↗</a></nav><main class="wrap">"""
    html = (
        head
        + corpo(d, a, t)
        + f"""<noscript><p>Mapas, achados e tabelas de auditoria funcionam sem JavaScript. Para filtrar municípios e zonas, ative JavaScript ou baixe os CSVs.</p></noscript></main><footer><div class="wrap">Arvor Intelligence · Análise reproduzível da eleição de 2026 · <a href="#fontes">Fontes, cobertura e limites</a></div></footer><script id="dados" type="application/json">{payload}</script><script src="assets/analise_realidade_eleicao/app.js?v=20261028-faixas" defer></script></body></html>"""
    )
    saida = ROOT / "docs/analise_realidade_eleicao.html"
    saida.write_text(injetar(html), encoding="utf-8")
    print(saida, saida.stat().st_size)


if __name__ == "__main__":
    main()
