"""Evidência da crítica: proveniência e não identificação pelo grupo agregado."""

import hashlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from quaest_141026.integra.data import ROOT
from quaest_141026.integra.references import sources


def test_counterexamples_match_same_observation_but_reverse_absentees_preference():
    example = sources()["exemplo_agregacao"]
    gaps = []
    for scenario in example["cenarios"]:
        groups = scenario["grupos"]
        assert sum(sum(g["pessoas_por_resposta"]) for g in groups) == 100
        totals = [0] * len(example["ordem_respostas"])
        for group in groups:
            values = group["pessoas_por_resposta"]
            assert len(values) == len(totals)
            assert all(isinstance(v, int) and v >= 0 for v in values)
            assert sum(values) == 50
            totals = [a + b for a, b in zip(totals, values, strict=True)]
            if group["grupo"] == "Ausentes":
                gaps.append(values[0] - values[1])
        assert totals == example["total_por_resposta"]
    observed = json.loads(
        (ROOT / "analysis/quaest_141026/integra/temas/transferencia.json").read_text()
    )["linhas"]["Branco/nulo/não foi votar"]
    assert example["total_por_resposta"] == observed
    assert gaps[0] * gaps[1] < 0


def test_reference_pdfs_and_export_preserve_verified_bytes():
    refs = sources()
    public = ROOT / "docs/assets/quaest_14102026_integra/referencias.json"
    assert json.loads(public.read_text()) == refs
    for ref in refs["fontes"]:
        assert ref["natureza"] and ref["localizador"] and ref["limite"]
        if "arquivo" not in ref:
            continue
        paths = (ROOT / ref["arquivo"], ROOT / "docs" / ref["arquivo_publico"])
        for path in paths:
            contents = path.read_bytes()
            assert contents.startswith(b"%PDF")
            assert len(contents) == ref["bytes"]
            assert hashlib.sha256(contents).hexdigest() == ref["sha256"]


@pytest.mark.parametrize("key", ["tse", "idea", "esomar_wapor", "aapor", "pew"])
def test_each_primary_reference_is_linked_in_analysis_and_bibliography(key):
    page = BeautifulSoup(Path("docs/quaest_14102026.html").read_text(), "html.parser")
    ref = next(r for r in sources()["fontes"] if r["id"] == key)
    url = ref["url"]
    assert any(a["href"] == url for a in page.select("#referencias-metodologicas a"))
    analysis = page.select("#agregacao a, #comparecimento a")
    assert any(a["href"] == url for a in analysis)
    assert page.select_one("#agregacao figure.chart")
