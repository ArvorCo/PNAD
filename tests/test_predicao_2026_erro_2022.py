"""Erro das pesquisas de 2022: fontes íntegras, TSE conferido e aritmética fechada."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAIS = ROOT / "data/originals/pesquisas_2022"
BASE = ROOT / "analysis/predicao_2026/erro_2022"
LFS = b"version https://git-lfs.github.com/spec/v1"
GRUPOS = ("lula", "bolsonaro", "tebet", "ciro", "demais")


def carregar():
    # tests/conftest.py já põe scripts/ no caminho de importação.
    return importlib.import_module("predicao-2026-erro-2022")


@pytest.fixture(scope="module")
def mod():
    return carregar()


@pytest.fixture(scope="module")
def saida(mod):
    return mod.construir()


def fontes():
    return sorted(ORIGINAIS.glob("*/fonte.json"))


@pytest.mark.parametrize("fonte", fontes(), ids=lambda p: p.parent.name)
def test_documentos_batem_com_sha256(fonte):
    meta = json.loads(fonte.read_text())
    assert meta["documentos"]
    for doc in meta["documentos"]:
        path = fonte.parent / doc["arquivo"]
        assert path.exists(), path
        data = path.read_bytes()
        if data.startswith(LFS):
            pytest.skip(f"{path.name} é ponteiro do Git LFS sem conteúdo baixado")
        assert len(data) == doc["bytes"]
        assert hashlib.sha256(data).hexdigest() == doc["sha256"]


def test_toda_pesquisa_tem_pasta_e_fonte():
    transc = json.loads((BASE / "pesquisas_2022.json").read_text())
    for p in transc["pesquisas"]:
        assert (ORIGINAIS / p["id"] / "fonte.json").exists(), p["id"]
        assert p["validos_publicados"] or p["totais"], p["id"]


def test_oficial_bate_com_tse_rastreado(saida):
    tse = json.loads((ROOT / "analysis/voto_util/tse_2022_uf.json").read_text())
    br = tse["brasil_2022"]["t1"]
    votos = saida["resultado_oficial"]["votos"]
    for k in ("lula", "bolsonaro", "tebet", "ciro", "outros", "validos"):
        assert votos[k] == br[k]
    assert (
        votos["lula"]
        + votos["bolsonaro"]
        + votos["tebet"]
        + votos["ciro"]
        + (votos["outros"])
        == votos["validos"]
    )
    assert votos["validos"] + votos["brancos"] + votos["nulos"] == (
        votos["comparecimento"]
    )
    parc = saida["resultado_oficial"]["parcelas_validos_pp"]
    assert sum(parc.values()) == pytest.approx(100)
    assert parc["lula"] == pytest.approx(100 * 57259504 / 118229719)


def test_oficial_bate_com_api_bruta_quando_presente(saida):
    conf = saida["resultado_oficial"]["conferencia_api_bruta"]
    if conf is None:
        pytest.skip("JSON bruto da API do TSE fora do repositório (data/raw)")
    assert conf["igual_ao_json_rastreado"]
    assert conf.get("ufs_mais_exterior_fecham_brasil", True)


def test_erros_fecham_com_a_aritmetica(saida):
    oficial = saida["resultado_oficial"]["parcelas_validos_pp"]
    for r in saida["por_casa"]:
        v = r["validos_pp"]
        assert sum(v.values()) == pytest.approx(100)
        for k in GRUPOS:
            assert r["erro_pp"][k] == pytest.approx(v[k] - oficial[k])
        assert sum(r["erro_pp"].values()) == pytest.approx(0, abs=1e-9)
        d = r["diferenca_lula_menos_bolsonaro"]
        assert d["erro"] == pytest.approx(
            r["erro_pp"]["lula"] - r["erro_pp"]["bolsonaro"]
        )
        assert r["erro_absoluto_medio_pp"] == pytest.approx(
            sum(abs(r["erro_pp"][k]) for k in GRUPOS) / 5
        )


def test_media_e_erro_comum(saida):
    m = saida["media_das_casas"]
    rows = {r["id"]: r for r in saida["por_casa"]}
    dentro = [rows[i] for i in m["casas"]]
    assert all(r["incluir"] for r in dentro)
    assert "gerp" not in m["casas"] and "brasmarket" not in m["casas"]
    media_dif = sum(r["diferenca_lula_menos_bolsonaro"]["erro"] for r in dentro)
    media_dif /= len(dentro)
    assert m["erro_comum_diferenca_lula_menos_bolsonaro"] == pytest.approx(media_dif)
    proprio = m["componente_proprio_diferenca_pp"]
    assert sum(proprio.values()) == pytest.approx(0, abs=1e-9)
    ap = saida["aplicacao_2026"]["deslocamentos_pp_em_flavio_menos_lula"]
    assert ap["repeticao_de_2022"] == pytest.approx(media_dif)
    assert ap["direcao_oposta"] == pytest.approx(-media_dif)


def test_validos_calculados_das_contagens(saida):
    verita = next(r for r in saida["por_casa"] if r["id"] == "verita")
    assert verita["base_validos"] == "calculado_das_contagens"
    soma = 22821 + 21286 + 2149 + 2098 + 716 + 461 + 205 + 154 + 51
    assert verita["validos_pp"]["lula"] == pytest.approx(100 * 21286 / soma)


def test_saida_gravada_esta_em_dia(saida):
    gravada = json.loads((BASE / "erro_2022.json").read_text())
    assert gravada["media_das_casas"] == json.loads(
        json.dumps(saida["media_das_casas"])
    )


def test_sem_travessao():
    for path in [BASE / "memorando.md", BASE / "pesquisas_2022.json"]:
        assert chr(0x2014) not in path.read_text(), path


PAYLOAD = ROOT / "docs/assets/predicao_2026_1T_presidente.json"
PAGE = ROOT / "docs/predicao_2026_1T_presidente.html"


@pytest.fixture(scope="module")
def payload():
    return json.loads(PAYLOAD.read_text())


def test_payload_tem_erro_2022_com_fonte_e_hash(payload):
    e = payload["erro_2022"]
    fonte = ROOT / e["fonte"]["arquivo"]
    assert hashlib.sha256(fonte.read_bytes()).hexdigest() == e["fonte"]["sha256"]
    gravada = json.loads(fonte.read_text())
    assert e["media_das_casas"] == gravada["media_das_casas"]
    assert all(doc["sha256"] for h in e["por_casa"] for doc in h["documentos"])
    ligacoes = {r["casa_2026"]: r["ligacao"] for r in e["comparacao_2026"]["linhas"]}
    assert ligacoes["Nexus"].startswith("Grupo")
    assert ligacoes["Meio/Ideia"].startswith("Marca")
    assert ligacoes["Datafolha"] == "Mesmo instituto"


def test_sensibilidades_do_erro_2022_deslocam_a_diferenca(payload):
    e = payload["erro_2022"]
    rotulos = e["aplicacao_2026"]["sensibilidades"]
    desloc = e["aplicacao_2026"]["deslocamentos_pp_em_flavio_menos_lula"]
    comum = e["media_das_casas"]["erro_comum_diferenca_lula_menos_bolsonaro"]
    assert desloc["repeticao_de_2022"] == pytest.approx(comum)
    central = payload["central"]["brasil"]["margem_flavio_lula"]
    sens = payload["sensibilidades"]
    for chave, alvo in (("repeticao", comum), ("invertido", -comum)):
        cenario = sens[rotulos[chave]]
        assert cenario["parametros"]["vies_pp"] == pytest.approx(alvo)
        margem = cenario["brasil"]["margem_flavio_lula"]
        assert margem - central == pytest.approx(alvo, abs=0.05)
    # A central não absorve o erro de 2022.
    assert payload["configuracao"]["central"]["vies_pp"] == 0


def test_pagina_publica_o_bloco_de_2022(payload):
    html = PAGE.read_text()
    assert "O erro de 2022, casa por casa" in html
    assert "2022 contra 2026" in html
    assert "{{" not in html and chr(0x2014) not in html
    bloco = html[html.index('id="erro-2022"') :]
    bloco = bloco[: bloco.index("Quanto cada escolha de modelo")]
    assert "Datafolha, Ipec e Ipespe/Abrapel" in bloco
    assert "Paraná Pesquisas" in bloco
    assert "+3,92" in bloco and "+4,96" in bloco
    for rotulo in payload["erro_2022"]["aplicacao_2026"]["sensibilidades"].values():
        assert rotulo in html
