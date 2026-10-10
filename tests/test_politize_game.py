"""Politize: o jogo da conversa. Roteiro, build e página (contrato em analysis/politize_game/CONTRATO.md)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from ga_tag import GA_ID
from politize_game import roteiro

ROOT = Path(__file__).resolve().parents[1]
PAGINA = ROOT / "docs/politize_game.html"
PASTA = ROOT / "docs/politize_game"
TRAVESSAO = "—"


@pytest.fixture(scope="module")
def payload() -> dict:
    return roteiro.montar()


def test_roteiro_valida_no_contrato(payload: dict):
    assert [p["id"] for p in payload["personagens"]] == roteiro.PERSONAGENS
    assert sorted(c["id"] for c in payload["cenarios"]) == sorted(roteiro.CENARIOS)
    assert [n["id"] for n in payload["npcs"]] == roteiro.NPCS_A + roteiro.NPCS_B


def test_todo_npc_aparece_em_algum_cenario_sugerido(payload: dict):
    sugeridos: set[str] = set()
    for c in payload["cenarios"]:
        sugeridos.update(c.get("npcs_sugeridos", []))
    faltam = {n["id"] for n in payload["npcs"]} - sugeridos
    assert not faltam, f"NPCs sem cenário sugerido: {sorted(faltam)}"


def test_cenarios_dos_npcs_existem(payload: dict):
    ids = {c["id"] for c in payload["cenarios"]}
    for n in payload["npcs"]:
        assert set(n["cenarios"]) <= ids, n["id"]


def test_condutas_ilegais_so_como_opcao_grave_com_lei(payload: dict):
    """Carona, favor, boca de urna e ameaça nunca são premiadas e sempre citam a lei."""
    achou = 0
    for n in payload["npcs"]:
        conjuntos = [n["escuta"], n["fecho"], *[o["opcoes"] for o in n["objecoes"]]]
        for ops in conjuntos:
            for op in ops:
                if set(op["tags"]) & roteiro.TAGS_ILEGAIS:
                    achou += 1
                    assert op["tipo"] == "grave", (n["id"], op["texto"])
                    assert op["fonte"].startswith("lei."), (n["id"], op["texto"])
                    assert op["fonte_texto"] == roteiro.LEIS[op["fonte"]]
    assert achou >= 8


def test_ideologicos_nao_viram_voto_para_flavio(payload: dict):
    ideologicos = [n for n in payload["npcs"] if n["campo"] == "esquerda_ideologica"]
    assert len(ideologicos) >= 1
    for n in ideologicos:
        assert n["desfechos"]["alto"] == "nulo", n["id"]
        assert "flavio" not in n["desfechos"].values(), n["id"]


def test_propostas_citadas_resolvem_para_o_plano(payload: dict):
    citadas = 0
    for n in payload["npcs"]:
        for o in n["objecoes"]:
            for op in o["opcoes"]:
                if "programa" in op["tags"]:
                    citadas += 1
                    assert "plano de governo, p." in op["fonte_texto"], (
                        n["id"],
                        op["fonte"],
                    )
    assert citadas >= 12, "o roteiro precisa citar o plano em ao menos 12 opções"


def test_resolver_fonte_cobre_as_quatro_familias():
    textos, propostas = roteiro.carregar_apoio()
    assert roteiro.resolver_fonte("lei.art299", textos, propostas).startswith(
        "Oferecer"
    )
    cuidado = roteiro.resolver_fonte(
        "textos.conversas_por_origem.cury.cuidado", textos, propostas
    )
    assert cuidado == textos["conversas_por_origem"]["cury"]["cuidado"]
    item = roteiro.resolver_fonte(
        "textos.arquetipos.reencontro.o_que_nao_fazer[1]", textos, propostas
    )
    assert item == textos["arquetipos"]["reencontro"]["o_que_nao_fazer"][1]
    assert "p. 13" in roteiro.resolver_fonte(
        "propostas.seguranca.13", textos, propostas
    )
    with pytest.raises(KeyError):
        roteiro.resolver_fonte("propostas.seguranca.999", textos, propostas)
    with pytest.raises(KeyError):
        roteiro.resolver_fonte("textos.temas", textos, propostas)


def test_dados_js_publicado_esta_em_dia(payload: dict):
    """O dados.js publicado é exatamente o build do roteiro atual."""
    publicado = (PASTA / "dados.js").read_text(encoding="utf-8")
    assert publicado == roteiro.para_js(payload)
    corpo = publicado.split("window.POLITIZE_GAME=", 1)[1].rstrip().rstrip(";")
    assert json.loads(corpo.replace("<\\/", "</"))["versao"] == payload["versao"]


@pytest.mark.parametrize(
    "arquivo",
    ["politize_game.html", "politize_game/app.js", "politize_game/app.css",
     "politize_game/avatares.js", "politize_game/cenas.js", "politize_game/dados.js",
     "politize_game/manifest.webmanifest"],
)  # fmt: skip
def test_arquivos_publicados_sem_travessao_nem_modulos(arquivo: str):
    texto = (ROOT / "docs" / arquivo).read_text(encoding="utf-8")
    assert TRAVESSAO not in texto, arquivo
    if arquivo.endswith(".html"):
        assert 'type="module"' not in texto, "scripts clássicos, para abrir de file://"
        for script in ("dados.js", "avatares.js", "cenas.js", "app.js"):
            assert f"politize_game/{script}" in texto
    if arquivo.endswith(".js"):
        assert "fetch(" not in texto and "import " not in texto.split("\n", 1)[0]


def test_pagina_tem_cabecalho_da_casa():
    html = PAGINA.read_text(encoding="utf-8")
    assert html.count(GA_ID) == 2
    assert 'rel="canonical" href="https://brasil.arvor.co/politize_game.html"' in html
    assert "img/og/politize_game.png" in html
    assert 'rel="manifest"' in html
    assert "politizesuavizinhanca.html" in html, "o jogo volta para o Politize"
    assert "<noscript>" in html


def test_politize_linka_o_jogo():
    html = (ROOT / "docs/politizesuavizinhanca.html").read_text(encoding="utf-8")
    assert "politize_game.html" in html


def test_motor_implementa_mistura_e_fraqueza():
    """Pontos do contrato que o JS precisa carregar: mistura fixa, fraqueza dobrada, semente."""
    js = (PASTA / "app.js").read_text(encoding="utf-8")
    for termo in (
        "esquerda_ideologica",
        "lulista_pragmatico",
        "publico",
        "limiares",
        "fraqueza",
        "localStorage",
        "mulberry32",
    ):
        assert termo in js, termo
    assert "aria-live" in PAGINA.read_text(encoding="utf-8")
    assert re.search(r"rede_x", js), "rede_x no máximo uma vez por rodada"


def test_card_social_do_jogo():
    import importlib

    card = importlib.import_module("social-card-politize-game").card(ROOT)
    assert card["slug"] == "politize_game"
    assert TRAVESSAO not in json.dumps(card, ensure_ascii=False)
    assert (ROOT / "docs/img/og/politize_game.png").exists()
