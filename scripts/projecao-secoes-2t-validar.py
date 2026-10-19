#!/usr/bin/env python3
"""Uma retrospectiva temporal: treina 2018, avalia 2022; exporta todos os métodos."""

from projecao_secoes_2t.fontes import ROOT, historical, save_json
from projecao_secoes_2t.motor import bounds, predict, score


def main():
    train, meta18 = historical(2018)
    target, meta22 = historical(2022)
    train = train[train.uf != "ZZ"].reset_index(drop=True)
    target = target[target.uf != "ZZ"].reset_index(drop=True)
    predictions, fit = predict(train, target)
    results = score(target, predictions)
    selected = min(results, key=lambda name: results[name]["rmse_uf_pp"])
    report = {
        "treino": 2018,
        "teste": 2022,
        "universo": "Brasil sem exterior, seções com partições íntegras e mesmo local nos dois turnos",
        "criterio": "Menor RMSE por UF, ponderado pelos válidos observados; seleção exploratória em uma eleição",
        "selecionado": selected,
        "resultados": results,
        "limites_transferencia_2022": bounds(target),
        "fontes": [meta18, meta22],
        "ajuste_2018": fit,
    }
    save_json(ROOT / "analysis/projecao_secoes_2t/validacao.json", report)
    for key, row in results.items():
        print(key, {k: v for k, v in row.items() if k not in ("ufs", "rotulo")})
    print("Selecionado", selected)


if __name__ == "__main__":
    main()
