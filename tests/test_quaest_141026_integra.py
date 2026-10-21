"""Íntegra: integridade, cobertura, denominadores e cenários sem imputação."""

import hashlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from quaest_141026.integra.archive import EXPECTED_SHA
from quaest_141026.integra.data import DATA, ROOT, build, topics


@pytest.fixture(scope="module")
def data():
    return build()


def test_original_and_public_copy_are_identical_and_catalog_covers_every_page(data):
    source = data["documento"]
    for path in (ROOT / source["arquivo"], ROOT / "docs" / source["arquivo_publico"]):
        assert path.stat().st_size == source["bytes"] == 55270493
        assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_SHA
    assert [p["pagina"] for p in data["catalogo"]] == list(range(1, 153))
    keys = {t["id"] for t in data["temas"]}
    assert len(keys) == 23
    covered = {p for t in data["temas"] for p in t["paginas"]}
    for row in data["catalogo"]:
        assert row["tema"] in keys | {"metodo", "separador"}
        assert row["pagina"] in covered or row["tema"] in {"metodo", "separador"}
        image = ROOT / "docs" / row["imagem"]
        assert hashlib.sha256(image.read_bytes()).hexdigest() == row["sha256"]
    assert all(t["formulacao_publicada"] and t["limite"] for t in topics())


def test_transfer_is_mixed_group_with_incomplete_matrix_and_rounded_products(data):
    tr = data["transferencia"]
    assert tr["ausentes_separados"] is tr["matriz_completa"] is False
    assert tr["grupo_pct"] == 22
    assert tr["contribuicoes_total_pp"]["lula"] == pytest.approx(9.46)
    assert tr["contribuicoes_total_pp"]["flavio"] == pytest.approx(8.36)
    assert tr["vantagem_lula_total_pp"] == pytest.approx(1.1)
    stress = tr["cenario_conversao"]
    assert stress[-1]["flavio_total"] == 46
    assert stress[-1]["lula_total"] == 44
    assert stress[0]["flavio_total"] == pytest.approx(37.64)
    assert stress[0]["lula_total"] == pytest.approx(34.54)
    assert all(
        r["flavio_validos"] + r["lula_validos"] == pytest.approx(100) for r in stress
    )
    t = next(t for t in data["temas"] if t["id"] == "transferencia")
    assert t["pesos_lembrados_pct"]["Outros"] is None


def test_official_reference_uses_electorate_and_accounts_for_every_voter(data):
    counts = data["urna"]["contagens"]
    assert counts["eleitores"] == 157828968
    assert counts["comparecimento"] == 124934069
    assert counts["comparecimento"] + counts["abstencao"] == counts["eleitores"]
    assert (
        counts["validos"] + counts["brancos"] + counts["nulos"]
        == counts["comparecimento"]
    )
    pct = data["urna"]["pct_eleitorado"]
    assert pct["flavio"] == pytest.approx(35.456484)
    assert pct["sem_voto_valido"] == pytest.approx(24.620995)
    assert pct["sem_voto_valido"] + pct["validos"] == pytest.approx(100)


def test_interest_sensitivity_does_not_pretend_to_be_likely_voter(data):
    lv = data["eleitor_provavel"]
    assert not lv["regra_publicada"]
    rows = lv["sensibilidades_por_interesse"]
    assert len(rows) == 4
    assert rows[1]["flavio_validos"] == pytest.approx(100 * 50 / 97)
    assert all(
        r["flavio_validos"] == pytest.approx(100 * r["flavio"] / r["soma"])
        for r in rows
    )


def test_profile_and_proposals_preserve_partitions_and_source_values(data):
    by_id = {t["id"]: t for t in data["temas"]}
    assert len(by_id["perfil"]["grupos"]) == 8
    assert all(sum(g.values()) == 100 for g in by_id["perfil"]["grupos"].values())
    assert list(by_id["perfil"]["grupos"]["Renda familiar (p. 147)"].values()) == [
        31,
        42,
        27,
    ]
    assert all(sum(row) == 100 for row in by_id["propostas"]["linhas"].values())
    assert sum(by_id["preocupacao"]["valores"].values()) == 94
    for topic in topics():
        assert (
            json.loads(
                (
                    ROOT
                    / "docs/assets/quaest_14102026_integra"
                    / (topic["id"] + ".json")
                ).read_text()
            )
            == topic
        )
    assert (DATA / "CONTRATO.md").exists()


def test_no_js_fallback_has_every_topic_and_page_with_reviewable_sources():
    page = BeautifulSoup(Path("docs/quaest_14102026.html").read_text(), "html.parser")
    assert len(page.select("#q-temas-completos > details")) == 23
    assert len(page.select("#q-catalogo-completo tbody tr")) == 152
    assert len(page.select("figure.chart")) >= 24
    assert page.select_one("#q-document-controls").has_attr("hidden")
    assert page.select_one("#q-document-image")["src"].endswith("p019.webp")
    assert "9% não é uma previsão de abstenção" in page.get_text()
    assert "sem promessa de transcrição célula a célula" in page.get_text()
    central = BeautifulSoup(
        Path("docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    # A nota da cobertura atual muda quando chega outra onda; a de 14/10
    # continua acessível no histórico, sem impor sua presença na central atual.
    assert central.select_one('[data-history-id="quaest_2026-10-13"]')
