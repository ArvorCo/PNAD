"""Evidence and exclusion safeguards for the 30 September documentary update."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = json.loads((ROOT / "docs/assets/reponderacao_20260930.json").read_text())
DATA = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


def test_new_report_integrity_and_rounded_topline():
    poll = AUDIT["fontes"][0]
    src = poll["fonte"]
    content = (ROOT / src["pdf"]).read_bytes()
    assert content.startswith(b"%PDF-")
    assert hashlib.sha256(content).hexdigest() == src["sha256"]
    assert len(content) == src["bytes"]
    assert sum(poll["publicado"]["1t"].values()) == pytest.approx(100.5)
    assert sum(poll["publicado"]["2t"].values()) == pytest.approx(100.1)
    assert src["paginas"]["2t_renda"] == 37
    check = AUDIT["controle_auxiliar_meio"]
    assert check["recomposto"][:2] == pytest.approx([48.443, 47.95])
    assert check["residuo_max_pp"] < 0.06


def test_missing_income_weights_never_become_a_calibrated_poll():
    poll_id = "meio_ideia_2026-09-28"
    raw = json.loads(
        (ROOT / f"analysis/reponderacao/pesquisas/{poll_id}.json").read_text()
    )
    assert raw["ignorar"]
    assert not {"bases", "amostra_pct"} & raw["renda"].keys()
    assert raw["campo"] == {"inicio": "2026-09-25", "fim": "2026-09-28"}
    assert raw["divulgacao"] == "2026-09-30"
    assert poll_id in {p["id"] for p in DATA["nao_reponderaveis"]}
    assert poll_id not in {p["id"] for p in DATA["pesquisas"]}
    forecast = json.loads((ROOT / "docs/assets/reponderacao_validos.json").read_text())
    for ballot in forecast["ballots"].values():
        for scenario in ballot["scenarios"].values():
            assert not {"Meio/Ideia", "Futura"} & {
                p["instituto"] for p in scenario["polls"]
            }


def test_futura_recheck_is_not_a_new_field_wave():
    poll = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/futura_2026-09-23.json").read_text()
    )
    assert poll["fonte"]["conferido_em"] == "2026-09-30"
    assert poll["divulgacao"] == "2026-09-24"
    assert poll["campo"]["fim"] == "2026-09-23"
    assert poll["ignorar"] and not poll["cruzamentos"]
    assert sum(poll["renda"]["amostra_pct"]) == pytest.approx(90.8)
