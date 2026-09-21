"""Contratos da cobertura do Grupo Folha sobre o Sudeste, setembro de 2026."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOMINIOS = ("folha.uol.com.br", "uol.com.br")


def load_module(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mod():
    return load_module("datafolha-21092026-cobertura-sudeste")


def test_urls_sao_unicas(mod):
    urls = [item["url"] for item in mod.ITENS]
    assert len(urls) == len(set(urls))


def test_datas_dentro_do_periodo(mod):
    inicio, fim = mod.PERIODO["inicio"], mod.PERIODO["fim"]
    for item in mod.ITENS:
        assert inicio <= item["data"] <= fim, item["titulo"]


def test_temas_na_lista_fechada(mod):
    assert len(set(mod.TEMAS)) == len(mod.TEMAS)
    for item in mod.ITENS:
        assert item["tema"] in mod.TEMAS, item["titulo"]


def test_pesa_na_lista_fechada(mod):
    for item in mod.ITENS:
        assert item["pesa"] in mod.PESA, item["titulo"]


def test_dominio_do_grupo_folha(mod):
    for item in mod.ITENS:
        assert item["url"].startswith("https://"), item["titulo"]
        assert any(d in item["url"] for d in DOMINIOS), item["titulo"]


def test_uf_declarada(mod):
    for item in mod.ITENS:
        assert item["uf"] in mod.UFS, item["titulo"]


def test_consulta_existe(mod):
    ids = {consulta["id"] for consulta in mod.CONSULTAS}
    for item in mod.ITENS:
        assert item["consulta"] in ids, item["titulo"]


def test_consultas_declaram_veiculo_e_url(mod):
    vistos = set()
    for consulta in mod.CONSULTAS:
        assert consulta["id"] not in vistos
        vistos.add(consulta["id"])
        assert consulta["veiculo"] in {"Folha de S.Paulo", "UOL"}
        assert any(d in consulta["url"] for d in DOMINIOS)
        assert consulta["resultados"] is None or consulta["resultados"] >= 0


def test_titulos_sem_travessao(mod):
    for item in mod.ITENS:
        assert "—" not in item["titulo"], item["titulo"]
    for linha in [*mod.LIMITES, mod.LEITURA]:
        assert "—" not in linha


def test_cada_uf_tem_item_e_pauta_material(mod):
    presentes = {item["uf"] for item in mod.ITENS}
    assert presentes == set(mod.UFS)
    for uf in mod.UFS:
        assert mod.PAUTAS_MATERIAIS[uf], uf
        for pauta in mod.PAUTAS_MATERIAIS[uf]:
            assert set(pauta) >= {
                "pauta",
                "valor",
                "devedor",
                "destinatario",
                "url",
            }


def test_json_escrito_bate_com_o_modulo(mod, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ANALYSIS", tmp_path / "analysis")
    monkeypatch.setattr(mod, "ASSETS", tmp_path / "assets")
    mod.main()
    destino = tmp_path / "assets" / "datafolha_21092026_cobertura_sudeste.json"
    payload = json.loads(destino.read_text(encoding="utf-8"))
    assert payload["total_itens"] == len(mod.ITENS)
    assert set(payload["itens_por_uf"]) == set(mod.UFS)
    assert payload["limites"]
    soma = sum(payload["itens_por_uf"].values())
    assert soma == len(mod.ITENS)
    for uf in mod.UFS:
        assert sum(payload["por_uf_tema"][uf].values()) == payload["itens_por_uf"][uf]
        assert sum(payload["por_uf_pesa"][uf].values()) == payload["itens_por_uf"][uf]
