"""Revisão geral de 05/10: rótulo único, limites no fim, dez teses e as quatro figuras novas."""

from __future__ import annotations

import re

import pytest
from apuracao_2026 import pagina_comum as C
from apuracao_2026.pagina_figuras import FIGURAS
from apuracao_2026.pagina_texto import dados_figuras, teses
from apuracao_2026.pagina_view import pagina

NOVAS = (
    "noite_pesos_regioes",
    "marcos_falha",
    "urna_reguas",
    "terceira_via_reguas_totais",
)


@pytest.fixture(scope="module")
def dados():
    return C.Dados()


@pytest.fixture(scope="module")
def html(dados):
    return pagina(dados)[0]


def test_rotulo_unico_cobre_o_achado_contrario():
    assert (
        C.rotulo("contrario")
        == '<span class="selo selo-contrario">Achado contrário</span>'
    )
    h = C.nota("hipotese", "texto", "Do autor.")
    assert h.startswith(
        '<aside class="hyp"><p><span class="selo selo-hipotese">Hipótese</span>'
    )
    lista = C.nota("juizo", "<ul><li>a</li></ul>")
    assert "</p><ul>" in lista


def test_limites_no_fim_do_capitulo():
    h = C.limites(["a", "", "b"], "remete")
    assert h.count("<li>") == 2 and "Limites do capítulo" in h and "<p>remete</p>" in h


@pytest.mark.parametrize("nome", NOVAS)
def test_figuras_novas_desenham_com_os_dados(dados, nome):
    h = FIGURAS[nome](dados_figuras(dados))
    assert 'class="pendente"' not in h[:200]
    assert 'class="fig-larga"' in h and 'class="fig-estreita"' in h
    assert h.count("<title>") == 2 and "<figcaption>" in h
    assert "—" not in h
    tamanhos = [float(x) for x in re.findall(r'font-size="([\d.]+)"', h)]
    assert min(tamanhos) >= 13


def test_figura_nova_ausente_vira_pendente():
    assert 'class="pendente"' in FIGURAS["urna_reguas"]({})


def test_dez_teses_com_capitulo(dados):
    h = teses(dados)
    itens = re.findall(r"<li>(.*?)</li>", h)
    assert len(itens) == 10
    assert all('class="selo selo-' in x and 'href="#' in x for x in itens)


def test_pagina_sem_travessao_e_com_as_figuras_novas(html):
    assert "—" not in html
    for nome in NOVAS:
        assert f'id="fig-{nome}"' in html
    assert html.count('class="limites"') >= 8
    assert '<aside class="juizo"><b>' not in html
