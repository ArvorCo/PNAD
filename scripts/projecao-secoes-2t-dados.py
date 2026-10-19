#!/usr/bin/env python3
"""Apuração + histórico + pesquisas; exporta projeções e auditoria reproduzível."""

import argparse
import json
from datetime import date

from projecao_secoes_2t.fontes import (
    OUT,
    PARTS,
    ROOT,
    complete_current,
    current,
    historical,
    save_json,
    sha,
)
from projecao_secoes_2t.motor import DEST, LABELS, predict, share
from projecao_secoes_2t.pesquisas import combine


def aggregate(frame, predictions, group):
    columns = ["aptos_1", *[f"{p}_1" for p in PARTS]]
    result = frame.groupby(group)[columns].sum()
    for name, values in predictions.items():
        counts = values * frame.aptos_1.to_numpy()[:, None]
        aux = frame[group].copy()
        aux[[f"{name}_{p}" for p in DEST]] = counts
        result = result.join(aux.groupby(group).sum())
    return result.reset_index()


def pack(frame):
    return {
        "colunas": list(frame.columns),
        "linhas": frame.where(frame.notna(), None).values.tolist(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hoje", default="2026-10-19")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    today = date.fromisoformat(args.hoje)
    if not date(2026, 10, 5) <= today <= date(2026, 10, 25):
        raise ValueError("Corte fora do segundo turno pré-eleitoral")
    train, meta22 = historical(2022)
    raw, meta26 = current(args.refresh)
    target, coverage = complete_current(raw)
    train = train[train.uf != "ZZ"].reset_index(drop=True)
    validation = json.loads(
        (ROOT / "analysis/projecao_secoes_2t/validacao.json").read_text()
    )
    predictions, fit = predict(train, target)
    selected = validation["selecionado"]
    snapshot_path = ROOT / "docs/assets/reponderacao_simulador.json"
    snapshot = json.loads(snapshot_path.read_text())
    combined, fusion = combine(
        target, predictions[selected], validation, snapshot, today
    )
    predictions["combinado"] = combined
    state_table = aggregate(target, predictions, ["uf"])
    city_table = aggregate(
        target,
        {"historico": predictions[selected], "combinado": combined},
        ["uf", "mun"],
    )
    official = json.loads(
        (ROOT / "analysis/apuracao_2026/dados/presidente.json").read_text()
    )
    cities = {r[0]: r[3] for r in official["municipios"]["linhas"]}
    city_table.insert(2, "municipio", city_table.mun.map(cities))
    national = {}
    for name, values in predictions.items():
        counts = (values * target.aptos_1.to_numpy()[:, None]).sum(axis=0)
        national[name] = {
            "rotulo": LABELS.get(name, "Urna + pesquisas"),
            "flavio_validos": float(100 * share(counts[None, :])[0]),
            "votos": dict(zip(DEST, counts.tolist(), strict=True)),
            "comparecimento_pct": float(100 * (1 - counts[-1] / target.aptos_1.sum())),
        }
    historical_states = (
        train.groupby("uf")[[f"{p}_{t}" for t in (1, 2) for p in ["aptos", *PARTS]]]
        .sum()
        .reset_index()
    )
    # A distribuição de ganhos líquidos inclui comparecimento, BN e mudanças de finalista.
    historical_states["ganho_direita"] = (
        historical_states.direita_2 - historical_states.direita_1
    )
    historical_states["ganho_esquerda"] = (
        historical_states.esquerda_2 - historical_states.esquerda_1
    )
    export = target.copy()
    for name in [*LABELS, "combinado"]:
        export[f"{name}_flavio_validos_pct"] = 100 * share(predictions[name])
    for i, name in enumerate(DEST):
        export[f"combinado_{name}_votos"] = combined[:, i] * target.aptos_1
    out_csv = OUT / "projecao_secoes_2026.csv.gz"
    export.to_csv(
        out_csv,
        index=False,
        float_format="%.8f",
        compression={"method": "gzip", "mtime": 0},
    )
    state_csv = ROOT / "docs/assets/projecao_secoes_2t_ufs.csv"
    state_table.to_csv(state_csv, index=False, float_format="%.8f")
    # Fonte numérica pública compacta; extrato completo fica disponível como gzip.
    public_csv = ROOT / "docs/fontes/projecao_secoes_2t_2026.csv.gz"
    public_csv.write_bytes(out_csv.read_bytes())
    data = {
        "schema": 1,
        "referencia": args.hoje,
        "eleicao": "2026-10-25",
        "universo": "Brasil sem exterior",
        "selecionado": selected,
        "cobertura": coverage,
        "nacional": national,
        "fusao": fusion,
        "validacao": validation,
        "ufs": pack(state_table),
        "municipios": pack(city_table),
        "historico_2022_ufs": pack(historical_states),
        "ajuste_2022": fit,
        "fontes": {
            "2022": meta22,
            "2026": meta26,
            "pesquisas_snapshot": snapshot["version"],
            "pesquisas_sha256": sha(snapshot_path),
            "extrato_completo": {
                "arquivo": str(public_csv.relative_to(ROOT)),
                "sha256": sha(public_csv),
                "bytes": public_csv.stat().st_size,
            },
        },
        "codigo": {
            str(p.relative_to(ROOT)): sha(p)
            for p in sorted((ROOT / "scripts/projecao_secoes_2t").glob("*.py"))
        },
        "notas": [
            "Experimento com seleção em uma retrospectiva; não substitui as centrais anteriores nem fornece probabilidade de vitória validada.",
            "O método selecionado mantém a razão local entre finalistas; 2022 informa a comparação e os cenários, mas sua transferência estimada não venceu o teste 2018→2022.",
            "Resultados fracionários por seção são expectativas do modelo; não são votos individuais observados.",
            "Resíduos municipais são linhas de zona/seção zero, rotuladas residuo_municipal, e não contam como seções.",
            "Seções principal/agregadas: a unidade é o boletim principal, sem dupla contagem.",
        ],
    }
    save_json(ROOT / "docs/assets/projecao_secoes_2t_2026.json", data)
    save_json(
        ROOT / "analysis/projecao_secoes_2t/resultado.json",
        {
            k: v
            for k, v in data.items()
            if k not in ("municipios", "validacao", "ajuste_2022")
        },
    )
    city_table.to_csv(OUT / "municipios.csv", index=False)
    print(
        json.dumps(
            {
                "selecionado": selected,
                "cobertura": coverage,
                "nacional": national,
                "peso_pesquisas": fusion["peso_pesquisas"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
