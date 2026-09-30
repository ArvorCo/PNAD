"""Comparação descritiva do perfil, sem estimar voto nem imputar renda ausente."""

import csv
import importlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
m = importlib.import_module("reponderacao-pnad")
p = json.loads(
    (ROOT / "analysis/reponderacao/pesquisas/futura_2026-09-29.json").read_text()
)
profile = json.loads(
    (ROOT / "data/originals/futura_092026_30/transcricao.json").read_text()
)["perfil"]["percentuais"]
b = m.Benchmark()
ipca = m.load_ipca()
cuts = m.band_cuts_brl(p, ipca)
raw = p["renda"]["amostra_pct"]
norm = [100 * x / sum(raw) for x in raw]
result = {
    "fonte_pnad": b.meta,
    "ultimo_ipca_disponivel": max(ipca),
    "cortes_reais_abril2026": cuts,
    "futura_renda_total_amostra": raw,
    "futura_renda_entre_declarantes": norm,
    "futura_sem_renda": 10,
    "pnad_renda": {k: b.shares(k, cuts) for k in m.SCENARIOS},
}
counts = {k: defaultdict(float) for k in ["genero", "idade", "regiao"]}
with (ROOT / b.meta["source"]).open() as f:
    reader = csv.reader(f)
    h = next(reader)
    ai = h.index("V2009__idade_na_data_de_referencia")
    wi = h.index("V1032__peso_com_calibracao")
    si = h.index("V2007__sexo")
    ui = h.index("UF__unidade_da_federacao")
    for row in reader:
        age = int(row[ai])
        w = float(row[wi])
        if age < 16 or w <= 0:
            continue
        sex = {"1": "masculino", "2": "feminino"}[row[si]]
        region = {
            "1": "norte",
            "2": "nordeste",
            "3": "sudeste",
            "4": "sul",
            "5": "centro_oeste",
        }[row[ui][0]]
        age_group = next(
            label
            for cutoff, label in [
                (25, "16_24"),
                (35, "25_34"),
                (45, "35_44"),
                (60, "45_59"),
                (999, "60_mais"),
            ]
            if age < cutoff
        )
        for dim, label in [("genero", sex), ("regiao", region), ("idade", age_group)]:
            counts[dim][label] += w
result["outros_perfis_pnad16mais"] = {
    k: {group: 100 * w / sum(v.values()) for group, w in v.items()}
    for k, v in counts.items()
}
result["diferencas_demograficas_pp"] = {
    k: {group: profile[k][group] - v for group, v in values.items()}
    for k, values in result["outros_perfis_pnad16mais"].items()
}
result["limites"] = [
    "Comparação de composição, não teste estatístico nem estimativa de viés eleitoral.",
    "A amostra Futura não é identificada como bruta ou ponderada nos prints.",
    "Para calibração eleitoral de idade, gênero e região, a referência adequada é o TSE; PNAD 16+ não é cadastro eleitoral.",
    "Escolaridade não comparada sem compatibilizar completas/incompletas e sem instrução; religião não está na base PNADC usada.",
]
out = Path(__file__).with_name("comparacao-perfil-futura.json")
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
(ROOT / "docs/assets/futura_20260930_perfil_pnad.json").write_text(out.read_text())
print(json.dumps(result, ensure_ascii=False, indent=2))
