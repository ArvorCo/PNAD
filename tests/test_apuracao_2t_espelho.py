"""Simetria numérica e presença dos dois candidatos nas figuras do dossiê."""

import json
from html.parser import HTMLParser
from pathlib import Path

import pytest
from apuracao_2t_2026 import pagina_fig_cedo_tarde as cedo
from apuracao_2t_2026 import pagina_fig_noite as noite
from apuracao_2t_2026 import pagina_fig_turnos as turnos
from apuracao_2t_2026.pagina_fig_espelho import efeitos, espelhar
from apuracao_2t_2026.pagina_fig_zeros_duplo import fig_zeros

ROOT = Path(__file__).resolve().parents[1]


class Elementos(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def dados(nome):
    return json.loads(
        (ROOT / f"analysis/apuracao_2t_2026/dados/{nome}.json").read_text()
    )


def test_intervalo_assimetrico_espelha_os_extremos_na_ordem_correta():
    assert espelhar(-2, (-4, -1)) == (2, (1, 4))
    assert espelhar(*espelhar(-2, (-4, -1))) == (-2, (-4, -1))
    assert espelhar(0.3) == (-0.3, None)


def test_efeitos_desenha_os_dois_valores_em_posicoes_simetrica_e_cores_distintas():
    html = efeitos(
        "teste",
        [{"nome": "Sinal", "valor": -2, "intervalo": (-4, -1)}],
        "Teste",
        "Fonte",
    )
    pontos = [
        a
        for t, a in Elementos(html).tags
        if t == "circle" and a.get("class") == "effect-point"
    ]
    assert {p["data-candidato"]: float(p["data-valor"]) for p in pontos} == {
        "Flávio": -2,
        "Lula": 2,
    }
    assert float(pontos[0]["cx"]) + float(pontos[1]["cx"]) == pytest.approx(
        440 + 935, abs=0.02
    )
    assert pontos[0]["fill"] != pontos[1]["fill"]


@pytest.mark.parametrize(
    "render,nome,por_candidato",
    [(noite.fig_fatia, "linha_do_tempo", 1), (cedo.fig_decis, "cedo_tarde", 4)],
)
def test_curvas_tem_series_visiveis_de_ambos_os_candidatos(render, nome, por_candidato):
    tags = Elementos(render(dados(nome))).tags
    curvas = [a for t, a in tags if t == "polyline" and "data-candidato" in a]
    assert sum(a["data-candidato"] == "Flávio" for a in curvas) == por_candidato
    assert sum(a["data-candidato"] == "Lula" for a in curvas) == por_candidato
    assert all(a["points"] for a in curvas)


def test_dispersao_mostra_os_dois_denominadores_normalizados():
    html = turnos.fig_dispersao(dados("comparacao_1t"))
    assert 'id="fig-tu_dispersao_lula"' in html
    assert 'id="fig-tu_dispersao"' in html
    assert "Lula no 1º turno, % entre Flávio e Lula" in html
    assert "Flávio no 1º turno, % entre Flávio e Lula" in html


def test_zeros_inclui_uf_que_so_tem_zero_para_lula():
    z = dados("zeros")
    z["por_uf"] = [
        {
            "uf": "XX",
            "secoes_2022_2t": 100,
            "secoes_2026_2t": 100,
            "zero_direita_2022_2t": 0,
            "zero_direita_2026_2t": 0,
            "zero_lula_2022_2t": 1,
            "zero_lula_2026_2t": 2,
        }
    ]
    html = fig_zeros(z)
    assert "XX" in html and "Lula 2022" in html and "Lula 2026" in html
    assert "2 de 100 seções" in html
