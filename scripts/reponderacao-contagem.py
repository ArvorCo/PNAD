"""Escala os cenários ao eleitorado oficial; não altera o placar nos válidos."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis/apuracao_2026/dados/presidente.json"


def electorate(source=SOURCE):
    content = source.read_bytes()
    official = json.loads(content)
    rows = official["ufs"]
    total = sum(row["eleitores"] for row in rows)
    if total != official["nacional"]["eleitores"]:
        raise ValueError("Eleitorado das UFs diverge do total nacional do TSE")
    exterior = sum(row["eleitores"] for row in rows if row["uf"] == "ZZ")
    return {
        "total": total - exterior,
        "national_including_exterior": total,
        "excluded_exterior": exterior,
        "scope": "Brasil, sem exterior",
        "source": "analysis/apuracao_2026/dados/presidente.json",
        "source_sha256": hashlib.sha256(content).hexdigest(),
        "source_generated_at": official["meta"]["versao_nacional_gerada_em"],
        "source_snapshot_id": official["meta"]["versao_nacional_snapshot_id"],
        "source_page": "apuracao_1o_turno_2026.html",
        "method": "Eleitorado apto das 27 UFs na apuração presidencial TSE 2026; ZZ excluída para corresponder ao universo das pesquisas. Base fixa, sem estimar mudança de aptidão entre turnos.",
    }


def counts(result, base):
    """Valores contínuos antes do arredondamento em milhões (espelho JS)."""
    total = base["total"]
    if not isinstance(total, (int, float)) or not math.isfinite(total) or total <= 0:
        raise ValueError("Eleitorado precisa ser finito e positivo")
    out = {k: total * v / 100 for k, v in result["por_100_eleitores"].items()}
    out["eleitorado"] = total
    out["validos"] = out["flavio"] + out["lula"]
    out["comparecimento"] = out["validos"] + out["branco_nulo"]
    out["diferenca_flavio_lula"] = out["flavio"] - out["lula"]
    return out
