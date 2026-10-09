"""Acrescenta ondas e revisões ao diário sem reescrever datas anteriores."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "analysis/reponderacao/log.json"
POLLS = ROOT / "analysis/reponderacao/pesquisas"


def update(data, path=MANIFEST, folder=POLLS):
    history = json.loads(path.read_text())
    known = {p["id"] for p in history["waves"]}
    previous = history.get("wave_hashes", {})
    hashes, added, revised = {}, [], []
    date = data["gerado_em"][:10]
    for source in sorted(folder.glob("*.json")):
        content = source.read_bytes()
        poll = json.loads(content)
        key = poll["id"]
        digest = hashlib.sha256(content).hexdigest()
        hashes[key] = digest
        if key not in known:
            history["waves"].append({"id": key, "added": date, "commit": None})
            added.append(key)
        elif key in previous and previous[key] != digest:
            revised.append(key)
    if added or revised:
        history["changes"].append(
            {
                "date": date,
                "title": "Atualização do acervo",
                "description": "; ".join(
                    label + ": " + ", ".join(keys)
                    for label, keys in (
                        ("Ondas incorporadas", added),
                        ("Ondas revistas", revised),
                    )
                    if keys
                )
                + ". Os documentos e os cálculos por turno ficam nas fichas; as versões dos arquivos permanecem no histórico Git.",
                "where": [
                    "reponderacao_pnad.html#pesquisas",
                    "reponderacao_pnad_1o_turno_2026.html#pesquisas",
                ],
                "hashes_before": {key: previous[key] for key in revised},
                "hashes_after": {key: hashes[key] for key in added + revised},
            }
        )
    history["wave_hashes"] = hashes
    # Um registro por linha mantém o acervo extenso legível e abaixo de 1.000 linhas.
    lines = []
    for key, value in history.items():
        encoded = json.dumps(value, ensure_ascii=False)
        if isinstance(value, list):
            encoded = (
                "[\n"
                + ",\n".join(
                    "    " + json.dumps(row, ensure_ascii=False) for row in value
                )
                + "\n  ]"
            )
        lines.append("  " + json.dumps(key) + ": " + encoded)
    output = "{\n" + ",\n".join(lines) + "\n}\n"
    if path.read_text() != output:
        path.write_text(output)
    return history
