#!/usr/bin/env python3
"""Recria os dados e associações do relatório geográfico, sem acesso à rede."""

import json

from analise_realidade_eleicao.dados import OUTPUT, construir
from analise_realidade_eleicao.estatistica import analisar


def main():
    dados = construir()
    dados["estatisticas"] = analisar(dados)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "dados.json").write_text(
        json.dumps(dados, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        + "\n"
    )
    print(
        f"Municípios: {len(dados['municipios'])}; zonas nas capitais: {len(dados['zonas'])}"
    )
    print("Cortes:", {k: len(v) for k, v in dados["cortes"].items()})
    print(
        "Capitais com diferença BUs/oficial:",
        [
            c
            for c in dados["cobertura_capitais"]
            if c["oficial_validos"] != c["bus_validos"]
        ],
    )
    for k, s in dados["estatisticas"]["municipios"].items():
        print(
            k,
            s["n"],
            "Pearson",
            round(s["pearson"], 3),
            "dentro da UF",
            round(s["dentro_grupo"], 3),
        )


if __name__ == "__main__":
    main()
