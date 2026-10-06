"""Testes do bloco de cenários de risco e casos documentados do capítulo 13."""

import copy
import json
from pathlib import Path

import pytest
from apuracao_2026 import fiscais_cenarios as FC
from apuracao_2026 import pagina_texto_fiscais_b as TFB
from apuracao_2026.pagina_comum import figura_catalogo

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/apuracao_2026/fiscais_fixture.json"
DADOS = ROOT / "analysis/apuracao_2026/dados/fiscais.json"


@pytest.fixture(scope="module")
def J():
    dado = FC.carregar()
    if dado is None:
        pytest.skip("fontes_fiscais.json ainda não existe")
    return dado


@pytest.fixture(scope="module")
def F():
    origem = FIXTURE if FIXTURE.exists() else DADOS
    return json.loads(origem.read_text(encoding="utf-8"))


def test_json_integro(J, F):
    assert FC.validar(J, {c["id"] for c in F["criterios"]}) == []


def test_cenarios_pedidos_estao_todos(J):
    ids = {c["id"] for c in J["cenarios"]}
    pedidos = {
        "pianista",
        "mesario",
        "compra",
        "cabresto",
        "transporte",
        "medo",
        "boca_urna",
        "contingencia",
        "zeresima",
        "filas",
        "abstencao",
        "cadastro",
    }
    assert pedidos <= ids


def test_transporte_e_impedimento_sao_linhas_separadas(J):
    transporte = FC.cenario(J, "transporte")
    abstencao = FC.cenario(J, "abstencao")
    assert set(transporte["base_legal"]).isdisjoint(abstencao["base_legal"])
    leis = " ".join(FC.lei(J, b)["norma"] for b in transporte["base_legal"])
    assert "6.091" in leis


def test_boca_de_urna_completa_e_sem_sinal(J):
    b = FC.cenario(J, "boca_urna")
    assert b["sinal"] == "nenhum" and b["criterios"] == []
    assert any("39" in FC.lei(J, x)["dispositivo"] for x in b["base_legal"])
    assert "filma" in b["confere"] and "juiz eleitoral" in b["confere"]


def test_casos_com_fonte_data_e_nunca_de_2026(J):
    fontes = FC.por_id(J["fontes"])
    for c in J["casos"]:
        assert c["fontes"], c["id"]
        assert int(c["ano"]) < 2026, c["id"]
        for f in c["fontes"]:
            assert fontes[f]["url"].startswith("http")
            assert fontes[f]["data"][:4].isdigit()


def test_arquivos_brutos_conferem_quando_presentes(J):
    import hashlib

    for f in J["fontes"]:
        if not f.get("arquivo") or not f.get("sha256"):
            continue
        caminho = ROOT / f["arquivo"]
        if not caminho.exists():
            continue
        assert hashlib.sha256(caminho.read_bytes()).hexdigest() == f["sha256"], f["id"]


def test_validar_acusa_referencia_quebrada(J):
    ruim = copy.deepcopy(J)
    ruim["casos"][0]["fontes"] = ["nao_existe"]
    ruim["cenarios"][0]["base_legal"] = ["nem_esta"]
    erros = FC.validar(ruim)
    assert any("nao_existe" in e for e in erros)
    assert any("nem_esta" in e for e in erros)


def test_validar_recusa_caso_de_2026(J):
    ruim = copy.deepcopy(J)
    ruim["casos"][0]["ano"] = 2026
    ruim["casos"][0]["data"] = "2026-10-04"
    assert any("2026" in e for e in FC.validar(ruim))


def test_figuras_renderizam(J, F):
    d = {"fiscais": F}
    cen = figura_catalogo("fiscais_cenarios", d)
    assert 'id="fig-fiscais_cenarios"' in cen and "pendente" not in cen
    for c in J["cenarios"]:
        assert c["nome"].split()[0] in cen
    casos = figura_catalogo("fiscais_casos", d)
    assert 'id="fig-fiscais_casos"' in casos
    assert casos.count('<tr><td class="num">') == len(J["casos"])
    assert "—" not in cen + casos


def test_bloco_de_texto(J, F):
    avisos = []
    h = TFB.bloco(F, lambda nome: figura_catalogo(nome, {"fiscais": F}), avisos.append)
    for h3 in TFB.H3:
        assert f"<h3>{h3}</h3>" in h
    assert "selo-hipotese" in h and "selo-verificado" in h
    assert "Nenhum cenário desta seção é atribuído à eleição de 2026" in h
    assert h.rstrip().endswith("</aside>")
    assert "—" not in h
    assert avisos == []
