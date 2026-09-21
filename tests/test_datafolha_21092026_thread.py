"""Contrato da thread do Sudeste: cinco cards, a faixa de texto e os numeros.

O gerador nao pode inventar numero. Cada afirmacao dos posts e conferida aqui
contra docs/assets/datafolha_21092026_sudeste.json,
docs/assets/datafolha_21092026_cobertura_sudeste.json e
docs/assets/datafolha_21092026_data.json.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
PAGINA = ROOT / "docs/datafolha_21092026_thread.html"
SUDESTE = ASSETS / "datafolha_21092026_sudeste.json"
COBERTURA = ASSETS / "datafolha_21092026_cobertura_sudeste.json"
NACIONAL = ASSETS / "datafolha_21092026_data.json"

if not (SUDESTE.exists() and COBERTURA.exists() and NACIONAL.exists()):
    pytest.skip(
        "rode scripts/datafolha-21092026-sudeste.py e o de cobertura antes",
        allow_module_level=True,
    )

S = json.loads(SUDESTE.read_text(encoding="utf-8"))
C = json.loads(COBERTURA.read_text(encoding="utf-8"))
N = json.loads(NACIONAL.read_text(encoding="utf-8"))
UFS = ("SP", "MG", "RJ")


def carrega():
    caminho = ROOT / "scripts" / "datafolha-21092026-thread.py"
    spec = importlib.util.spec_from_file_location("datafolha_21092026_thread", caminho)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


MODULO = carrega()
CARDS = MODULO.build_cards()
POSTS = ["\n\n".join(card["copy"]) for card in CARDS]
TEXTO = "\n\n".join(POSTS)


@pytest.fixture(scope="module")
def pagina() -> str:
    if not PAGINA.exists():
        pytest.skip("rode scripts/datafolha-21092026-thread.py antes")
    return PAGINA.read_text(encoding="utf-8")


def test_cinco_cards_com_grafico_proprio():
    assert len(CARDS) == 5
    tags = [card["tag"] for card in CARDS]
    assert tags[0] == "tese"
    assert tags[-1] == "limites"
    for card in CARDS:
        assert card["viz"].startswith("<svg")
        assert card["chips"]


def test_posts_na_faixa_declarada():
    for card, post in zip(CARDS, POSTS, strict=True):
        assert MODULO.MIN_CHARS <= len(post) <= MODULO.MAX_CHARS, (
            card["tag"],
            len(post),
        )


def test_sem_travessao_hashtag_nem_emoji():
    for card, post in zip(CARDS, POSTS, strict=True):
        assert "—" not in post, card["tag"]
        assert "–" not in post, card["tag"]
        assert MODULO.HASHTAG.search(post) is None, card["tag"]
        assert MODULO.EMOJI.search(post) is None, card["tag"]


def test_o_endereco_com_fragmento_nao_conta_como_hashtag():
    # O portao precisa aceitar url com ancora e continuar barrando hashtag.
    assert MODULO.HASHTAG.search("veja em exemplo.html#sudeste") is None
    assert MODULO.HASHTAG.search("olha isso #eleicoes") is not None


def test_placar_nacional_vem_do_json_da_reponderacao():
    publicado = N["reweight"]["turnos"]["2t"]["publicado"]
    ajustado = N["reweight"]["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"][
        "ajustado"
    ]
    assert f"Lula {MODULO.fmt(publicado['lula'])}" in POSTS[0]
    assert f"Flávio {MODULO.fmt(publicado['flavio'])}" in POSTS[0]
    assert MODULO.fmt(ajustado["lula"], 2) in POSTS[0]
    assert MODULO.fmt(ajustado["flavio"], 2) in POSTS[0]


def test_tres_estados_com_governo_e_presidencia_da_mesma_amostra():
    for uf in UFS:
        vao = S["estados"][uf]["vao"]["turno2"]
        nome = MODULO.curto(vao["candidato_governador"])
        assert f"{nome} tem {vao['governador_pct']}" in POSTS[0], uf
        assert f"Flávio tem {vao['presidenciavel_pct']}" in POSTS[0], uf
        assert (
            vao["presidenciavel_pct"]
            == S["estados"][uf]["presidente"]["turno2"]["Flavio Bolsonaro (PL)"]
        )
    assert "teto endereçável, não previsão" in POSTS[0]


def test_duas_reguas_com_base_margem_e_intervalo():
    regional = S["regional_contra_estadual"]
    nac = regional["recorte_nacional"]
    med = regional["media_estadual"]
    contraste = regional["contraste"]
    post = POSTS[1]
    assert MODULO.fmt(nac["base"]) in post
    assert MODULO.fmt(nac["margem_diferenca_pp"], 2) in post
    assert MODULO.fmt(med["lula"], 2) in post
    assert MODULO.fmt(med["flavio"], 2) in post
    assert MODULO.fmt(contraste["ic95"][0], 2) in post
    assert MODULO.fmt(regional["cobertura_do_eleitorado_pct"], 2) in post
    assert contraste["separa_com_95"] is False
    assert "as duas réguas concordam" in post
    # O ES nao pode ser deduzido por subtracao, e a thread precisa dizer isso.
    assert "não se deduz por subtração" in post
    assert regional["es_implicado"]["uso"] == "nao_publicavel_como_estimativa_do_es"


def test_soma_das_amostras_estaduais_confere():
    assert sum(S["estados"][uf]["n"] for uf in UFS) == MODULO.N_ESTADUAL
    assert MODULO.fmt(MODULO.N_ESTADUAL) in POSTS[1]


def test_transferencia_usa_as_linhas_publicadas():
    post = POSTS[2]
    medidas = S["varredura_de_cruzamentos"]["linhas_medidas"]
    assert str(medidas) in post
    rotulo = {
        "Flavio Bolsonaro (PL)": "Flávio",
        "Lula (PT)": "Lula",
        "Escritor Augusto Cury (AVANTE)": "Cury",
    }
    for uf, destino, origem in (
        ("SP", "presidente, 1o turno", "Tarcísio (REPUBLICANOS)"),
        ("MG", "presidente, 2o turno", "Cleitinho Azevedo (REPUBLICANOS)"),
        ("RJ", "presidente, 2o turno", "Eduardo Paes (PSD)"),
    ):
        bloco = next(
            b
            for b in S["cruzamentos_publicados"]
            if b["uf"] == uf and b["destino_pergunta"] == destino
        )
        for destinatario, valor in bloco["linhas"][origem].items():
            assert f"{valor} a {rotulo[destinatario]}" in post or (
                f"{valor} vão a {rotulo[destinatario]}" in post
            ), (uf, destinatario)
    soma = sum(
        next(
            b
            for b in S["cruzamentos_publicados"]
            if b["uf"] == "SP" and b["destino_pergunta"] == "presidente, 1o turno"
        )["linhas"]["Tarcísio (REPUBLICANOS)"].values()
    )
    assert 100 - soma == MODULO.TARCISIO_SEM_LINHA
    cruz_sp = next(
        b
        for b in S["cruzamentos_publicados"]
        if b["uf"] == "SP" and b["destino_pergunta"] == "presidente, 1o turno"
    )["linhas"]["Tarcísio (REPUBLICANOS)"]
    # 41 pontos fora de Flavio e 21 sem linha publicada nao sao o mesmo numero.
    assert 100 - cruz_sp["Flavio Bolsonaro (PL)"] == MODULO.TARCISIO_FORA_FLAVIO
    assert MODULO.TARCISIO_FORA_FLAVIO != MODULO.TARCISIO_SEM_LINHA
    assert (
        f"{MODULO.TARCISIO_FORA_FLAVIO} pontos desse eleitorado fora de Flávio" in post
    )
    assert f"outros {MODULO.TARCISIO_SEM_LINHA} o relatório não abre" in post
    assert "leitura é agregada" in post


def test_senado_da_direita_fica_atras_do_topo():
    achado = next(
        a for a in S["achados"] if a["id"] == "senado_da_direita_atras_do_topo"
    )
    post = POSTS[3]
    for uf in UFS:
        valores = achado["valores"][uf]
        nome = MODULO.curto(valores["candidato"])
        assert f"{nome} com {valores['voto1_pct']}" in post, uf
        assert valores["distancia_pp"] < -20
        assert (
            valores["flavio_turno1_pct"]
            == S["estados"][uf]["presidente"]["turno1"]["Flavio Bolsonaro (PL)"]
        )
    faixa = sorted(abs(achado["valores"][uf]["distancia_pp"]) for uf in UFS)
    assert f"De {faixa[0]} a {faixa[-1]} pontos atrás" in post
    assert "nenhum nome da direita puxa o topo" in post


def test_pauta_cita_a_contagem_da_cobertura():
    post = POSTS[3]
    assert f"publicou {C['total_itens']} itens" in post
    for uf, chaves in MODULO.DESTAQUE_TEMA.items():
        assert MODULO.frase_temas(uf) in post, uf
        for chave in chaves:
            assert chave in C["por_uf_tema"][uf], (uf, chave)
        ficha = C["perguntas_da_pesquisa"][uf.lower()]
        assert ficha["perguntas_sobre_pauta_estadual"] == 0
        assert ficha["tabelas"] == 13
    assert "zero pergunta temática" in post
    # A ressalva do 17/09 nao pode sumir, e o veiculo nao e acusado de esconder.
    assert "17/09" in post
    assert "escondeu nada" in post


def test_juizo_editorial_esta_rotulado():
    assert "juízo editorial" in POSTS[3]
    assert CARDS[3]["tag"] == "juízo editorial"


def test_contraprovas_e_limites_no_ultimo_post():
    post = POSTS[4]
    pl = next(
        linha
        for linha in S["estados"]["MG"]["vao_por_recorte_turno2"]
        if linha["dimensao"] == "partido" and linha["recorte"] == "PL"
    )
    inverso = S["estados"]["MG"]["vao"]["inverso_turno2"]
    assert f"Flávio faz {pl['flavio']}" in post
    assert f"candidato ao governo faz {pl['governador']}" in post
    assert f"{pl['base_governador']} entrevistas" in post
    assert (
        f"{inverso['governador_pct']} contra {inverso['presidenciavel_pct']} de Patrus"
        in post
    )
    assert f"vão de {MODULO.sgn(S['estados']['RJ']['vao']['turno2']['vao_pp'])}" in post
    assert "Fréchet" in post
    assert "Espírito Santo" in post
    assert "brasil.arvor.co/datafolha_21092026.html#sudeste" in post


def test_pagina_tem_cinco_cards_quadrados(pagina: str):
    assert pagina.count('class="card"') == 5
    assert pagina.count("<svg") == 5
    assert "aspect-ratio:1/1" in pagina
    assert "cqw" in pagina
    assert "@media (width <= 720px)" in pagina
    assert "—" not in pagina
    assert "–" not in pagina


def test_pagina_imprime_a_contagem_de_caracteres(pagina: str):
    for post in POSTS:
        assert f"{len(post)} caracteres" in pagina


def test_metatags_completas(pagina: str):
    esperado = [
        '<link rel="canonical" href="https://brasil.arvor.co/datafolha_21092026_thread.html">',
        '<meta property="og:image" content="https://brasil.arvor.co/img/og/datafolha_21092026_thread.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:image" content="https://brasil.arvor.co/img/og/datafolha_21092026_thread.png">',
        '<meta property="og:url" content="https://brasil.arvor.co/datafolha_21092026_thread.html">',
    ]
    for tag in esperado:
        assert tag in pagina, tag
    assert 'href="datafolha_21092026.html#sudeste"' in pagina
    assert 'href="index.html"' in pagina
