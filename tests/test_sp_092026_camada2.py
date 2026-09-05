"""Contratos da camada 2 do atlas paulista: reponderação, IPF, vão, índice e corredores."""

import json
from itertools import pairwise
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def asset(name):
    return json.loads((ROOT / "docs/assets" / name).read_text())


@pytest.fixture(scope="module")
def k():
    return asset("sp_092026_camada2.json")


def test_reweight_recomposes_published_toplines(k):
    """Cada cruzamento de renda recompõe o placar publicado; o único resíduo acima de 1 pp está declarado."""
    failures = []
    for inst in ("datafolha", "quaest", "atlas"):
        for q, block in k["reponderacao"][inst].items():
            if not isinstance(block, dict) or "candidatos" not in block:
                continue
            for name, c in block["candidatos"].items():
                if abs(c["residuo_pp"]) >= 1:
                    failures.append((inst, q, name, c["residuo_pp"]))
                assert c["sensibilidade"] == pytest.approx(
                    c["publicado"] + c["reponderado"] - c["recomposto"], abs=0.02
                )
    assert failures == [("quaest", "pres1", "Flávio", pytest.approx(2.32, abs=0.01))]
    assert "nota" in k["reponderacao"]["quaest"]["pres1"]


def test_reweight_uses_pnad_partition(k):
    r = k["reponderacao"]
    assert sum(r["pnad_sm3"].values()) == pytest.approx(100, abs=0.05)
    assert sum(r["pnad_brl5"].values()) == pytest.approx(100, abs=0.05)
    # O achado contrário à tese fica registrado: a Atlas perde a liderança de Flávio com a régua da PNAD.
    atlas2 = r["atlas"]["pres2"]
    assert atlas2["diferenca_publicada"] == pytest.approx(3.5)
    assert 0 < atlas2["diferenca_sensibilidade"] < 1
    df2 = r["datafolha"]["gov2"]
    assert df2["diferenca_sensibilidade"] > df2["diferenca_publicada"]


def test_ipf_closes_published_margins(k):
    for f in k["fluxos"]:
        m = f["matriz"]
        dst_sum = sum(f["destino"].values())
        src_sum = sum(f["origem"].values())
        for s, row in m.items():
            assert sum(row.values()) == pytest.approx(
                f["origem"][s] * dst_sum / src_sum, abs=0.05
            )
        for d in f["destino"]:
            assert sum(m[s][d] for s in m) == pytest.approx(f["destino"][d], abs=0.05)
        # zeros estruturais da prior são preservados
        for s, row in f["prior"].items():
            for d, p in row.items():
                if p == 0:
                    assert m[s][d] == 0
        assert f["robusto"]["diferenca_tarcisio_menos_direita_pp"] == pytest.approx(
            f["origem"]["Tarcísio"] - f["destino"]["Flávio"], abs=0.01
        )


def test_flows_cover_three_institutes_and_leak_is_similar(k):
    names = [f["nome"].split(":")[0] for f in k["fluxos"]]
    assert names == ["Datafolha", "Atlas", "Real Time", "Quaest"]
    leaks = [100 - f["estimado"]["tarcisio_para_direita_pct"] for f in k["fluxos"][:3]]
    assert all(12 < leak < 21 for leak in leaks)


def test_stock_is_consistent_between_rounds(k):
    m = k["micro"]
    e = m["estado"]
    co = m["coeficientes"]
    assert co == {
        "Tarcísio": 0.047,
        "Haddad": 0.018,
        "Rodrigo Garcia": 0.115,
        "Tarcísio 2T": 0.063,
        "Haddad 2T": 0.026,
    }
    assert (
        abs(e["estoque_votos_total"] - e["estoque2t_votos_total"])
        / e["estoque_votos_total"]
        < 0.05
    )
    assert e["tar2"] == pytest.approx(55.27) and e["bol2"] == pytest.approx(55.24)
    assert e["votos_tarcisio_sem_bolsonaro_acima"] < 100000
    top = m["trabalho"]
    assert top[0]["nome"] == "São Paulo"
    assert all(a["estoque_votos"] >= b["estoque_votos"] for a, b in pairwise(top))
    assert all(r["eleitorado"] >= 40000 for r in m["densidade"])


def test_series_reweighted_effect_is_stable(k):
    q = k["reponderacao"]["serie"]["quaest_gov2"]["ondas"]
    assert [o["onda"] for o in q] == ["abr/26", "jul/26", "ago/26"]
    efeitos = [o["diferenca_sensibilidade"] - o["diferenca_publicada"] for o in q]
    assert all(-1.5 < e < -0.5 for e in efeitos)
    for o in q:
        for c in o["candidatos"].values():
            assert abs(c["residuo_pp"]) < 0.7
    df = k["reponderacao"]["serie"]["datafolha_gov2"]["ondas"]
    assert [o["diferenca_publicada"] for o in df] == [15, 16, 19]
    assert df[-1]["diferenca_sensibilidade"] > 19
    rt = k["reponderacao"]["realtime"]
    assert rt["gov1"]["diferenca_sensibilidade"] > rt["gov1"]["diferenca_publicada"]


def test_gap_by_segment_is_consistent(k):
    v = k["vao"]
    assert v["total"]["vao"] == pytest.approx(6.4)
    for s in v["segmentos"]:
        assert s["vao_tarcisio_flavio"] == pytest.approx(
            s["tarcisio"] - s["flavio"], abs=0.06
        )
        assert s["tarcisio"] + s["haddad"] + s["nao_escolha_gov"] == pytest.approx(
            100, abs=0.6
        )
        assert s["lula"] + s["flavio"] + s["nao_escolha_pres"] == pytest.approx(
            100, abs=0.6
        )
    biggest = max(v["segmentos"], key=lambda s: s["vao_tarcisio_flavio"])
    assert (biggest["grupo"], biggest["segmento"]) == (
        "Voto para presidente em 2022, 2º turno",
        "Branco ou nulo",
    )
    ideologia = [s for s in v["segmentos"] if s["grupo"] == "Ideologia declarada"]
    assert max(ideologia, key=lambda s: s["vao_tarcisio_flavio"])["segmento"] == (
        "Antipetistas e antibolsonaristas"
    )


def test_carrier_index_definition(k):
    est = k["carregadores"]["estado"]
    assert est["bolsonaro_1t"] == pytest.approx(47.71, abs=0.01)
    assert est["tarcisio"] == pytest.approx(42.32, abs=0.01)
    assert est["pontes"] > est["bolsonaro_1t"]
    for r in k["carregadores"]["regioes"]:
        base = r["bol1"] / est["bolsonaro_1t"]
        assert r["i_tarcisio"] == pytest.approx(
            100 * (r["tarcisio"] / est["tarcisio"]) / base, abs=0.6
        )
    assert (
        sum(r["eleitores"] for r in k["carregadores"]["regioes"])
        == k["eleitorado_sp"]
        == 34105333
    )


def test_corridors_are_disjoint_and_sourced(k):
    seen = set()
    for c in k["corredores"]:
        ids = set(c["ids"])
        assert not ids & seen
        seen |= ids
        assert c["resumo"]["eleitores"] == sum(x["eleitorado"] for x in c["cidades"])
        pauta = c["pauta"]
        assert len(pauta["fatos"]) >= 3
        for texto, veiculo, data, url in pauta["fatos"]:
            assert url.startswith("https://") and veiculo and data and texto
        assert pauta["alerta"] and pauta["juizo"] and pauta["frase"]
        for a in c["ancoras"]:
            assert a["concentracao_pct"] >= 40
    assert len(k["corredores"]) == 9
    html = (ROOT / "docs/sp_092026.html").read_text()
    assert "—" not in html and "–" not in html
    assert html.count('class="corridor"') == 9
    assert html.count("<svg") >= 13


def test_three_level_flows_close_margins_and_answer_hypothesis(k):
    f3 = k["fluxos3"]
    assert [f["nome"].split(":")[0] for f in f3["fluxos"]] == [
        "Datafolha",
        "Atlas",
        "Real Time",
    ] or [f["nome"].split(":")[0] for f in f3["fluxos"]] == [
        "Atlas",
        "Datafolha",
        "Real Time",
    ]
    for f in f3["fluxos"]:
        gov1, pres1, pres2 = (
            f["niveis"]["gov1"],
            f["niveis"]["pres1"],
            f["niveis"]["pres2"],
        )
        s1, s2 = sum(gov1.values()), sum(pres1.values())
        for o, row in f["estagio1"].items():
            assert sum(row.values()) == pytest.approx(gov1[o] * s2 / s1, abs=0.06)
        for c in pres1:
            assert sum(f["estagio1"][o][c] for o in gov1) == pytest.approx(
                pres1[c], abs=0.06
            )
        for d in pres2:
            assert sum(f["estagio2"][c][d] for c in pres1) == pytest.approx(
                pres2[d], abs=0.08
            )
        r = f["resumo"]
        assert 70 < r["retencao_flavio_pct"] < 90
        # a terceira via devolve mais a Flávio do que manda a Lula
        assert r["terceira_via_para_flavio"] > r["terceira_via_para_lula"]
        assert r["tarcisio_para_lula_direto_1t"] > r["terceira_via_para_lula"]
