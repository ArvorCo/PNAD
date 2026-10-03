"""Testes do parser do painel do G1 para Senado, sem rede."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "senado_g1", ROOT / "scripts/senado-2026-g1.py"
)
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)

PAINEL = """
<div class="methodology">
  <p class="methodology__description">
    O Datafolha foi encomendado pela Globo e pela Folha de S.Paulo e ouviu
    2.520 eleitores de 16 anos ou mais, entre os dias 2 e 3 de outubro.
    A margem de erro é de dois pontos percentuais, para mais ou para menos.
    A pesquisa foi registrada na Justiça Eleitoral sob o número SP-09337/2026.
  </p>
</div>
<button class="segment" data-url="https://x/sp/sao-paulo/eleicoes/2026/pesquisas-eleitorais/senador/1-turno/Quaest"></button>
<button class="segment" data-url="https://x/sp/sao-paulo/eleicoes/2026/pesquisas-eleitorais/senador/1-turno/Datafolha"></button>
<a data-url="https://x/ac/acre/eleicoes/2026/pesquisas-eleitorais/senador/1-turno"></a>
<p id="ESTIMULADA-SEN-005"></p><a id="ESPONTANEA-SEN-005"></a>
<script>
  window.g1PesquisasEleitorais = {
    paginaId: "126",
    turno: "1",
    instituto: "Datafolha",
    tipoPergunta: "ESTIMULADA-SEN-005",
    uf: ""
  }
</script>
<span>ESTIMULADA-SEN-005 VTSVALIDOS-SEN-006</span>
"""

RESULTADO = {
    "cenarios": [
        {
            "bandeira_slug": "total",
            "opcoes_resposta": [
                {"nome": "Ana", "partido": {"sigla": "pl"}, "foto": "http://f/a.jpg"},
                {"nome": "Beto", "partido": None, "foto": None},
            ],
            "data": [
                {
                    "option": "Ana",
                    "values": [
                        {"date": "2026-09-24T00:00:00Z", "value": 0.12},
                        {"date": "2026-10-03T00:00:00Z", "value": 0.16},
                    ],
                },
                {
                    "option": "Beto",
                    "values": [{"date": "2026-10-03T00:00:00Z", "value": 0.5}],
                },
                {
                    "option": "Indecisos",
                    "values": [{"date": "2026-10-03T00:00:00Z", "value": 0.13}],
                },
                {
                    "option": "Em Branco/Nulo/Nenhum",
                    "values": [{"date": "2026-10-03T00:00:00Z", "value": 0.21}],
                },
            ],
        }
    ]
}


def test_config_e_codigos():
    config = MOD.parse_config(PAINEL)
    assert config["paginaId"] == "126"
    assert config["instituto"] == "Datafolha"
    assert config["tipoPergunta"] == "ESTIMULADA-SEN-005"
    assert MOD.parse_codigos(PAINEL) == [
        "ESTIMULADA-SEN-005",
        "ESPONTANEA-SEN-005",
        "VTSVALIDOS-SEN-006",
    ]
    assert MOD.tipo_do_codigo("VTSVALIDOS-SEN-006") == "validos"


def test_institutos_so_do_seletor_de_instituto():
    assert MOD.parse_institutos(PAINEL) == ["Quaest", "Datafolha"]


def test_metodologia_completa():
    texto = MOD.parse_metodologia_texto(PAINEL)
    dados = MOD.parse_metodologia(texto, "SP")
    assert dados["campo"] == {"inicio": "2026-10-02", "fim": "2026-10-03"}
    assert dados["n"] == 2520
    assert dados["margem_pp"] == 2.0
    assert dados["registro_tse"] == "SP-09337/2026"
    assert dados["contratante"] == "Globo e Folha de S.Paulo"


def test_campo_formas_de_escrita():
    assert MOD.parse_campo("entre os dias 28 de setembro e 1º de outubro") == {
        "inicio": "2026-09-28",
        "fim": "2026-10-01",
    }
    assert MOD.parse_campo("entre os dias 20 a 23 de setembro de 2026") == {
        "inicio": "2026-09-20",
        "fim": "2026-09-23",
    }
    assert MOD.parse_campo("no dia 02 de outubro") == {
        "inicio": "2026-10-02",
        "fim": "2026-10-02",
    }
    assert MOD.parse_campo("sem datas aqui") is None


def test_registros_da_uf_primeiro():
    texto = "números BA-01850/2026 e BR-03961/2026"
    assert MOD.parse_registros(texto, "BA") == ["BA-01850/2026", "BR-03961/2026"]
    assert MOD.parse_registros("BR-1234/2026 e AC-08968/2026", "AC")[0] == (
        "AC-08968/2026"
    )


def test_metodo_e_margem_decimal():
    assert MOD.parse_metodo("entrevistas pessoais domiciliares") == "presencial"
    assert MOD.parse_metodo("nada") == "nao informado"
    assert MOD.parse_margem("A margem de erro é de 2,5 pontos percentuais") == 2.5


def test_serie_em_pontos_percentuais():
    cenario = MOD.escolher_cenario(RESULTADO)
    serie = MOD.serie_por_data(cenario)
    assert sorted(serie) == ["2026-09-24", "2026-10-03"]
    assert serie["2026-10-03"]["Ana"] == 16.0
    assert serie["2026-09-24"] == {"Ana": 12.0}


def test_serie_formato_de_ponto_solto():
    cenario = {"data": [{"date": "2026-09-26T00:00:00Z", "value": 0.25, "option": "X"}]}
    assert MOD.serie_por_data(cenario) == {"2026-09-26": {"X": 25.0}}


def test_bloco_separa_indecisos_e_branco_nulo():
    cenario = MOD.escolher_cenario(RESULTADO)
    serie = MOD.serie_por_data(cenario)
    bloco = MOD.bloco_resposta(serie["2026-10-03"], MOD.opcoes_por_nome(cenario))
    assert [c["nome"] for c in bloco["candidatos"]] == ["Beto", "Ana"]
    assert bloco["candidatos"][1]["partido"] == "PL"
    assert bloco["candidatos"][0]["partido"] is None
    assert bloco["indecisos"] == 13.0
    assert bloco["branco_nulo"] == 21.0
    assert MOD.soma_bloco(bloco) == 100.0


def test_onda_da_metodologia_ignora_texto_defasado():
    metodologia = {"campo": {"inicio": "2026-09-20", "fim": "2026-09-23"}}
    datas = ["2026-08-24", "2026-09-24", "2026-10-03"]
    assert MOD.onda_da_metodologia(datas, metodologia) == "2026-09-24"
    assert MOD.onda_da_metodologia(["2026-10-03"], metodologia) is None


def test_slug_instituto():
    assert MOD.slug_instituto("Paraná Pesquisas") == "parana"
    assert MOD.slug_instituto("AtlasIntel") == "atlas"
    assert MOD.slug_instituto("Datafolha") == "datafolha"
