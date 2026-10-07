"""Toda página navegável de docs/ carrega a tag do Google Analytics, uma vez só."""

from pathlib import Path

import pytest
from ga_tag import DOCS, GA_ID, GA_TAG, injetar, paginas

PAGINAS = paginas(DOCS)


def test_ha_paginas():
    assert len(PAGINAS) > 50


@pytest.mark.parametrize("pagina", PAGINAS, ids=[p.name for p in PAGINAS])
def test_pagina_tem_a_tag_uma_vez_no_head(pagina: Path):
    texto = pagina.read_text(encoding="utf-8")
    assert texto.count(GA_ID) == 2, f"{pagina.name}: id esperado 2x (src e config)"
    assert texto.count("gtag/js?id=") == 1, f"{pagina.name}: tag duplicada ou ausente"
    cabeca = texto[: texto.lower().find("</head>")]
    assert GA_ID in cabeca, f"{pagina.name}: a tag precisa ficar dentro de <head>"


def test_injetar_depois_do_charset():
    html = '<!doctype html><html><head><meta charset="utf-8">\n<title>x</title></head>'
    saida = injetar(html)
    assert saida.startswith(
        '<!doctype html><html><head><meta charset="utf-8">\n' + GA_TAG
    )
    assert "<title>x</title>" in saida


def test_injetar_sem_charset_usa_o_head():
    saida = injetar('<html lang="pt-BR"><head><title>x</title></head>')
    assert saida.startswith('<html lang="pt-BR"><head>' + GA_TAG)


def test_injetar_e_idempotente():
    uma = injetar("<head></head>")
    assert injetar(uma) == uma


def test_injetar_sem_head_falha():
    with pytest.raises(ValueError):
        injetar("<p>sem cabeçalho</p>")


def test_tag_sem_travessao_e_com_id():
    assert "—" not in GA_TAG
    assert GA_TAG.count(GA_ID) == 2
