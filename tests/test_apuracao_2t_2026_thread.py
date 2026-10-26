"""Testes da thread do dossiê da apuração do 2º turno de 2026."""

import re
from pathlib import Path

import pytest
from apuracao_2t_2026.thread_base import (
    URL_DOSSIE,
    dado,
    digitos_soltos,
    problemas_de_texto,
)
from apuracao_2t_2026.thread_build import (
    CAMPOS_TEXTO,
    MAX_CHARS,
    MAX_POSTS,
    MIN_CHARS,
    MIN_POSTS,
    VETADAS_TESE,
    caminhos_png,
    montar,
    valores,
    verificar,
)
from apuracao_2t_2026.thread_pagina import pagina
from apuracao_2026.thread_base import num, pct

ROOT = Path(__file__).resolve().parents[1]
PAGINA = ROOT / "docs/apuracao_2T_2026_thread.html"


@pytest.fixture(scope="module")
def posts():
    return montar()


@pytest.fixture(scope="module")
def html(posts):
    return pagina(posts, caminhos_png(len(posts)), valores())


def test_quantidade_de_cards(posts):
    assert MIN_POSTS <= len(posts) <= MAX_POSTS
    assert 16 <= len(posts) <= 22


def test_tamanho_dos_posts(posts):
    for i, p in enumerate(posts, 1):
        assert MIN_CHARS <= len(p["corpo"]) <= MAX_CHARS, (i, len(p["corpo"]))


def test_verificacao_completa_sem_erros(posts):
    assert verificar(posts) == []


def test_sem_travessao_hashtag_emoji_ou_palavra_vetada(posts, html):
    for p in posts:
        assert problemas_de_texto(p["corpo"]) == []
    assert "—" not in html
    assert "–" not in html
    assert "fraude" not in html.lower()


def test_nenhum_algarismo_digitado(posts):
    for p in posts:
        for modelo in [p[c] for c in CAMPOS_TEXTO] + list(p["texto"]):
            assert digitos_soltos(modelo) == [], modelo


def test_detector_de_algarismo_pega_numero_solto():
    assert digitos_soltos("Lula teve 51,78% dos válidos") == ["51,78%"]
    assert digitos_soltos("Lula teve {l_pct} no 2º turno de 2026") == []


def test_link_do_dossie_no_primeiro_e_no_ultimo(posts):
    assert URL_DOSSIE in posts[0]["corpo"]
    assert URL_DOSSIE in posts[-1]["corpo"]


def test_card_sabado_domingo_e_tese(posts):
    card = [p for p in posts if "sábado" in p["tag_f"].lower()]
    assert len(card) == 1
    assert "juízo editorial" in card[0]["corpo"].lower()
    assert "juízo editorial declarado do autor" in posts[0]["corpo"].lower()


def test_sem_frases_vetadas_pela_tese(posts, html):
    for frase in VETADAS_TESE:
        assert frase not in html.lower(), frase


def test_hipotese_do_autor_rotulada(posts):
    hip = next(p for p in posts if "hipótese do autor" in p["tag_f"].lower())
    assert "juízo editorial" in hip["corpo"].lower()
    assert "se foi isso mesmo, não saberemos" in hip["corpo"]


def test_numeros_chave_batem_com_os_dados(posts):
    n = dado("presidente")["nacional"]
    corpo = posts[1]["corpo"]
    assert pct(n["pct_lula"]) in corpo
    assert pct(n["pct_flavio"]) in corpo
    assert num(n["margem_lula_votos"]) in corpo
    sil = dado("linha_do_tempo")["pausas"]["silencio_geral"]
    assert num(sil["minutos"], 1) in posts[2]["titulo_f"]
    pv = dado("pesquisas_vs_urna")["resumo"]
    assert (
        f"+{num(pv['publicado_validos_do_total']['media'], 2)}"
        in next(p for p in posts if p["tag_f"] == "Pesquisas × urna")["metrica_f"]
    )


def test_cada_card_tem_svg(posts):
    for p in posts:
        assert p["svg"].startswith("<svg") and "</svg>" in p["svg"]


def test_pagina_publicada_igual_a_gerada(html):
    assert PAGINA.read_text(encoding="utf-8") == html


def test_pngs_existem(posts):
    for rel in caminhos_png(len(posts)):
        assert (ROOT / "docs" / rel).exists(), rel


def test_pagina_tem_ga_e_og(html):
    assert html.count("G-ZPYEE8P9YC") >= 1
    assert re.search(
        r'og:image" content="https://brasil\.arvor\.co/img/og/apuracao_2T_2026_thread\.png',
        html,
    )


def test_card_transferencia_rotulado(posts):
    i = next(k for k, p in enumerate(posts) if "Transferência" in p["tag_f"])
    assert "1º × 2º turno" in posts[i - 1]["tag_f"]
    corpo = posts[i]["corpo"]
    assert corpo.startswith("Estimativa, não medição.")
    assert "hachurada" in corpo
    assert "url(#tr-" in posts[i]["svg"]


def test_card_logs(posts):
    i = next(k for k, p in enumerate(posts) if p["tag_f"] == "Os logs das urnas")
    assert posts[i - 1]["tag_f"] == "Seções: biometria"
    corpo = posts[i]["corpo"]
    assert "pede explicação" in corpo
    assert "deslocamento de voto" not in corpo
