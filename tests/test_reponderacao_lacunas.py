"""Interpolação é desenho separado: nunca dados de entrada ou extrapolação."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gaps", ROOT / "scripts/reponderacao_vista/gaps.py"
)
GAPS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GAPS)


def test_bridges_only_internal_gaps_and_leave_values_untouched():
    values = [None, 30, None, None, 35, 34, None, 36, None]
    original = deepcopy(values)
    assert list(GAPS.bridges(values)) == [(1, 4), (5, 7)]
    assert values == original
    assert list(GAPS.bridges([None, None])) == []
    assert list(GAPS.bridges([None, 30, None])) == []
    assert list(GAPS.bridges([30, 31, 32])) == []


def test_each_dotted_connector_matches_a_missing_interval_in_data():
    data = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
    html = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    dates = data["agregador"]["serie"]["datas"]
    for turn, slug in [("1t", "primeiro"), ("2t", "segundo")]:
        chart = html.find(id=f"{slug}-turno-chart")
        count = 0
        for kind in ["publicado", "ajustado"]:
            for key, values in data["agregador"]["serie"][turn][kind].items():
                expected = [
                    (dates[left + 1], dates[right - 1])
                    for left, right in GAPS.bridges(values)
                ]
                links = chart.select(
                    f'g[data-serie="{key}"] g.gap-bridge[data-kind="{kind}"]'
                )
                actual = [(g["data-gap-start"], g["data-gap-end"]) for g in links]
                assert actual == expected
                count += len(links)
                for link in links:
                    assert link.line["stroke-dasharray"] == "1 5"
                    assert link.line["stroke-linecap"] == "round"
                    assert "não representa pesquisa" in link["aria-label"]
                    assert (
                        "não entra" not in link["aria-label"]
                        or "média" in link["aria-label"]
                    )
        assert count > 0
        assert "fora do cálculo" in chart.get_text()
    # O intervalo longo do segundo turno continua ausente na série numérica.
    idx = dates.index("2026-06-05")
    assert data["agregador"]["serie"]["2t"]["ajustado"]["lula"][idx] is None
