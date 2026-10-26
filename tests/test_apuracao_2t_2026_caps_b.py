"""Capítulos cedo/tarde, turnos e abstenção do dossiê do 2º turno, com os JSONs reais.

Renderiza cada capítulo, confere a ausência de travessão, a presença dos números
centrais lidos do próprio JSON, figuras com viewBox de área positiva e o
noscript das listas longas bem formado. Pula se os dados ainda não existem.
"""

import importlib
import json
import re

import pytest
from apuracao_2t_2026.pagina_comum import DADOS, Dados
from apuracao_2026.pagina_comum import Capitulo, num

pytestmark = pytest.mark.skipif(
    not (DADOS / "cedo_tarde.json").exists(), reason="dados do 2º turno ausentes"
)

CAPS = {
    "cedo_tarde": ("05", ["ct_decis", "ct_transicao"]),
    "turnos": (
        "06",
        ["tu_barras_uf", "tu_dispersao", "tu_hist_2022", "tu_mapas_swing"],
    ),
    "abstencao": (
        "07",
        ["ab_ranking", "ab_mapa_delta", "ab_histograma", "ab_recortes", "ab_quintis"],
    ),
}


@pytest.fixture(scope="module")
def html():
    d = Dados(pasta=DADOS)
    out = {}
    for ident, (numero, _) in CAPS.items():
        mod = importlib.import_module(f"apuracao_2t_2026.pagina_cap_{ident}")
        cap = Capitulo(ident, numero, ident, ident, (), lambda _d: "")
        out[ident] = mod.render(d, cap)
    assert not d.avisos, d.avisos
    return out


def _json(nome):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


@pytest.mark.parametrize("ident", CAPS)
def test_sem_travessao_e_sem_pendencia(html, ident):
    h = html[ident]
    assert "—" not in h
    assert "fraude" not in h.lower()
    assert "em preparação" not in h
    assert "<section" not in h
    assert 'class="section-head"' in h


@pytest.mark.parametrize("ident", CAPS)
def test_figuras_presentes_e_com_area(html, ident):
    h = html[ident]
    for fig in CAPS[ident][1]:
        assert f'id="fig-{fig}"' in h, fig
    for w, hh in re.findall(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', h):
        assert float(w) > 0 and float(hh) > 0
    for x in re.findall(r'<rect [^>]*width="(-[\d.]+)"', h):
        pytest.fail(f"retângulo com largura negativa {x}")


@pytest.mark.parametrize("ident", CAPS)
def test_noscript_bem_formado(html, ident):
    h = html[ident]
    assert h.count('<noscript class="fig-src">') == h.count("</noscript>")


def test_cedo_tarde_numeros(html):
    C = _json("cedo_tarde.json")
    h = html["cedo_tarde"]
    sw = [x["swing_h2h_flavio_pp"] for x in C["decis_2t"]]
    assert num(abs(max(sw)), 2) in h and num(abs(min(sw)), 2) in h
    assert num(C["decis_2t"][0]["h2h_flavio"], 2) in h
    assert "Ponte Alta do Norte" in h
    assert h.count("<tr>") >= len(C["ultimos_50"])


def test_turnos_numeros(html):
    C1 = _json("comparacao_1t.json")
    h = html["turnos"]
    b = C1["brasil"]
    assert num(b["t1_h2h_flavio"], 2) in h and num(b["t2_h2h_flavio"], 2) in h
    assert sum(u["swing_h2h_flavio_pp"] < 0 for u in C1["ufs"]) == len(C1["ufs"])
    assert f"Caiu em {len(C1['ufs'])} das {len(C1['ufs'])} UFs" in h
    assert "Macapá (AP)" in h
    assert num(C1["dispersao_municipal"]["n_swing_h2h_pro_flavio"], 0) in h
    # listas completas: uma linha por município em que Flávio ganhou votos
    n = C1["flavio_ganhou_votos"]["n"]
    i = h.index('id="tu-lista-flavio-ganhou-votos"')
    trecho = h[i : h.index("</details>", i)]
    assert trecho.count("<tr>") == n + 1


def test_abstencao_numeros(html):
    A = _json("abstencao.json")
    P = _json("presidente.json")
    h = html["abstencao"]
    assert num(P["nacional"]["pct_abstencao"], 2) in h
    assert num(A["brasil"]["pa_1t_mesmos"], 2) in h
    for uf in ("AP", "RR", "AC"):
        assert uf in h
    assert (
        "82,7" in h
        or num(A["concentracao_abaixo_15"][1]["pct_aptos_abaixo_15_no_pais"], 1) in h
    )
    assert "Hipótese" in h and "Achado contrário" in h
