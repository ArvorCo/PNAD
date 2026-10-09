"""Acervo pós-1º turno por UF; diagnóstico, separado da âncora nacional.

Não soma estaduais como casas nacionais nem transporta as preferências antigas
do motor territorial. Campos, fontes e cobertura eleitoral ficam auditáveis.
"""

import hashlib
import json
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "analysis/reponderacao/estaduais"


def build(today):
    official = ROOT / "analysis/apuracao_2026/dados/presidente.json"
    ufs = json.loads(official.read_text())["ufs"]
    electorate = {row["uf"]: row["eleitores"] for row in ufs if row["uf"] != "ZZ"}
    total = sum(electorate.values())
    selected = {}
    start = (today - timedelta(days=6)).isoformat()
    for path in sorted(INPUT.glob("*.json")):
        row = json.loads(path.read_text())
        field, release = row["campo"], row["divulgacao"]
        if field["inicio"] <= "2026-10-04" or field["fim"] > today.isoformat():
            continue
        if not start <= release <= today.isoformat():
            continue
        source = ROOT / row["source"]["arquivo"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != row["source"]["sha256"]:
            raise ValueError("Fonte estadual mudou: " + row["id"])
        if row["n"] <= 0 or abs(sum(row["publicado"].values()) - 100) > 2:
            raise ValueError("Partição ou amostra estadual inválida: " + row["id"])
        key = (row["uf"], row["instituto"])
        previous = selected.get(key)
        if previous is None or (field["fim"], release, row["id"]) > (
            previous["campo"]["fim"],
            previous["divulgacao"],
            previous["id"],
        ):
            valid = row["publicado"]["flavio"] + row["publicado"]["lula"]
            selected[key] = {
                **row,
                "source_record": str(path.relative_to(ROOT)),
                "source_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "electorate": electorate[row["uf"]],
                "validos_normalizados": {
                    k: 100 * row["publicado"][k] / valid for k in ("flavio", "lula")
                },
            }
    covered = {key[0] for key in selected}
    return {
        "reference": today.isoformat(),
        "selected": list(selected.values()),
        "covered_ufs": sorted(covered),
        "covered_electorate": sum(electorate[uf] for uf in covered),
        "electorate": total,
        "coverage_pct": 100 * sum(electorate[uf] for uf in covered) / total,
        "use": "Diagnóstico por UF; não altera a central nacional nesta versão.",
        "reason": "A âncora atual adapta os componentes nacionais do motor. A camada territorial precisa de cobertura atual e calibração por eleitorado, comparecimento e efeitos de casa. Somar uma estadual à média nacional ou transportar o voto do 1º turno sem modelo de transferência daria precisão artificial.",
        "source_electorate": str(official.relative_to(ROOT)),
        "source_electorate_sha256": hashlib.sha256(official.read_bytes()).hexdigest(),
        "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
