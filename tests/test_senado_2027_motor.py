"""Motor do Senado 2027 diante do STF, com a fixture fictícia de nove cadeiras."""

import copy
import csv
import importlib.util
import json
import math
import shutil
from pathlib import Path

import numpy as np
import pytest
from senado_2027 import base as B
from senado_2027 import saida
from senado_2027 import scores as S
from senado_2027 import simulacao as M

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/senado_2027"
AGORA = "2026-10-07T12:00:00+00:00"
SORTEIOS = 4000


@pytest.fixture(scope="module")
def dados():
    lido = B.carregar(FIXTURE)
    assert lido.erros == []
    return lido


@pytest.fixture(scope="module")
def resultado(dados):
    return saida.montar(dados, sorteios=SORTEIOS, semente=11, gerado_em=AGORA)


def _pessoa(dados, slug):
    return next(p for p in dados.pessoas() if p["slug"] == slug)


def _caso(**kw):
    base = {
        "id": "x",
        "tipo": "opiniao",
        "estagio": "reu",
        "foro": "STF",
        "relator": None,
        "data_ultima_decisao": None,
    }
    return {**base, **kw}


def _senador(bloco="D", casos=(), sinais=(), alinhado=False, mandato="eleito_2026"):
    return {
        "slug": "s",
        "nome": "S",
        "bloco": bloco,
        "mandato": mandato,
        "alinhado_governo_lula": alinhado,
        "casos": list(casos),
        "sinais_contrapeso": [{"tipo": t} for t in sinais],
    }


def _copia(tmp_path):
    destino = tmp_path / "senado"
    shutil.copytree(FIXTURE, destino)
    return destino


def _editar(pasta, slug, funcao):
    caminho = pasta / "senadores" / f"{slug}.json"
    dado = json.loads(caminho.read_text(encoding="utf-8"))
    funcao(dado)
    caminho.write_text(json.dumps(dado, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ régua K


def test_reu_no_stf_relatado_por_dino_em_2026_vale_70():
    caso = _caso(relator="Flávio Dino", data_ultima_decisao="2026-04-28")
    pontos = S.pontos_caso(caso)
    assert pontos["componentes"] == {
        "estagio": 45,
        "foro": 10,
        "relator": 5,
        "recencia": 10,
    }
    assert pontos["pontos"] == 70
    assert S.exposicao([caso])["K"] == 70.0


def test_dois_casos_somam_maior_mais_03_do_outro():
    maior = _caso(
        id="a",
        tipo="patrimonial",
        estagio="investigado",
        relator="Alexandre de Moraes",
        data_ultima_decisao="2025-06-10",
    )
    menor = _caso(
        id="b",
        tipo="eleitoral",
        estagio="eleitoral_pendente",
        foro="TSE",
        data_ultima_decisao="2024-11-01",
    )
    assert S.pontos_caso(maior)["pontos"] == 25 + 10 + 5 + 10
    assert S.pontos_caso(menor)["pontos"] == 20 + 5
    assert S.exposicao([maior, menor])["K"] == 50 + 0.3 * 25


def test_teto_de_100_e_empate_dividem_a_parcela(dados):
    k = S.exposicao(_pessoa(dados, "iara-ministra")["casos"])
    assert k["K_bruto"] == 70 + 0.3 * (70 + 60)
    assert k["K"] == 100.0
    papeis = [c["papel"] for c in k["K_por_caso"]]
    assert papeis == ["empate_no_maior", "empate_no_maior", "demais"]
    esperado = (70 * (1 + 0.3) / 2 + 0.3 * 60) * 100 / 109
    assert k["K_patrimonial_ativo"] == S.r1(esperado) == 58.3


def test_nada_localizado_e_k_zero():
    assert S.exposicao([])["K"] == 0.0


def test_estagios_e_foros_da_regua():
    for estagio, pontos in S.REGUA["K"]["estagio"].items():
        caso = _caso(estagio=estagio, foro="outro")
        assert S.pontos_caso(caso)["pontos"] == pontos
    assert set(S.REGUA["K"]["estagio"]) == set(B.ESTAGIOS)
    assert S.pontos_caso(_caso(foro="STJ"))["componentes"]["foro"] == 5
    assert S.pontos_caso(_caso(foro="TRF"))["componentes"]["foro"] == 0


@pytest.mark.parametrize(
    ("relator", "esperado"),
    [
        ("Alexandre de Moraes", "Alexandre de Moraes"),
        ("Alexandre de Moraes (até a remessa)", "Alexandre de Moraes"),
        ("Ministro Moraes", "Alexandre de Moraes"),
        ("Min. Dino", "Flávio Dino"),
        ("Dias Toffoli (HC no STF)", "Dias Toffoli"),
        ("Gilmar Mendes", "Gilmar Mendes"),
        ("Juiz Luiz Alberto de Morais Júnior", None),
        ("Fulano de Moraes (TRF-1)", None),
        ("Rosa Weber", None),
        (None, None),
    ],
)
def test_relator_alvo(relator, esperado):
    assert S.relator_alvo(relator) == esperado


def test_recencia_aceita_data_parcial():
    assert S.pontos_caso(_caso(data_ultima_decisao="2025-06"))["componentes"][
        "recencia"
    ] == (10)
    assert S.pontos_caso(_caso(data_ultima_decisao="2024"))["componentes"][
        "recencia"
    ] == (0)


# ------------------------------------------------------------------ régua C


def test_redutor_patrimonial_so_sobre_k_patrimonial_ativo():
    patrimonial = _caso(
        tipo="patrimonial", estagio="investigado", data_ultima_decisao="2025-01-01"
    )
    opiniao = _caso(id="o", relator="Flávio Dino", data_ultima_decisao="2026-01-01")
    citado = _caso(id="c", tipo="patrimonial", estagio="citado")
    so_patrimonial = S.pontuar(_senador(casos=[patrimonial], sinais=["defesa_do_stf"]))
    assert so_patrimonial["K_patrimonial_ativo"] == 45.0
    # Cada linha da ficha é arredondada a uma casa antes da soma: 0,25 × 45 = 11,3.
    assert so_patrimonial["C_imp"] == S.r1(75 - S.r1(0.25 * 45)) == 63.7
    assert so_patrimonial["C_pec"] == S.r1(88 - S.r1(0.10 * 45)) == 83.5

    misto = S.pontuar(_senador(casos=[opiniao, patrimonial], sinais=["defesa_do_stf"]))
    assert misto["K"] == 70 + 0.3 * 45
    assert misto["K_patrimonial_ativo"] == 13.5
    assert misto["C_imp"] == S.r1(75 - S.r1(0.25 * 13.5)) == 71.6

    for casos in ([opiniao], [citado], [_caso(tipo="8_de_janeiro")]):
        sem = S.pontuar(_senador(casos=casos, sinais=["defesa_do_stf"]))
        assert sem["K"] > 0
        assert sem["K_patrimonial_ativo"] == 0.0
        assert sem["C_imp"] == 75.0
        assert all(a["chave"] != "redutor_patrimonial" for a in sem["ajustes"])


def test_c_fica_entre_2_e_97(dados):
    for pessoa in dados.pessoas():
        for pontos in S.pontuar_cenarios(pessoa).values():
            assert 2 <= pontos["C_imp"] <= 97
            assert 2 <= pontos["C_pec"] <= 97
    ana = S.pontuar(_pessoa(dados, "ana-teste"))
    assert (ana["C_imp"], ana["C_pec"]) == (97.0, 97.0)
    assert ana["ajustes"][-1] == {
        "chave": "limite",
        "rotulo": "Limite de 2 a 97",
        "C_imp": -17.0,
        "C_pec": -18.0,
    }
    assert S.pontuar(_pessoa(dados, "elisa-amostra"))["C_imp"] == 2.0


def test_linhas_de_ajuste_somam_o_c(dados):
    for pessoa in dados.pessoas():
        for pontos in S.pontuar_cenarios(pessoa).values():
            for alvo in ("C_imp", "C_pec"):
                soma = sum(a[alvo] for a in pontos["ajustes"])
                assert math.isclose(soma, pontos[alvo], abs_tol=1e-9)


def test_cada_tipo_de_sinal_conta_uma_vez(dados):
    ana = S.pontuar(_pessoa(dados, "ana-teste"))
    chaves = [a["chave"] for a in ana["ajustes"]]
    assert chaves.count("declaracao_pro_impeachment") == 1
    assert chaves.count("assinatura_pedido_impeachment") == 1
    assert chaves.count("cpi_contra_ministros") == 1
    assert sum(a["C_imp"] for a in ana["ajustes"][:-1]) == 85 + 10 + 8 + 8 + 3


def test_valores_conferidos_a_mao(dados):
    esperado = {
        "bruno-exemplo": {"flavio": (60.5, 67.0), "lula": (55.5, 64.0)},
        "carla-modelo": {"flavio": (27.0, 65.0), "lula": (12.0, 57.0)},
        "daniel-ficticio": {"flavio": (67.5, 86.0), "lula": (62.5, 83.0)},
        "elisa-amostra": {"flavio": (2.0, 18.8), "lula": (2.0, 18.8)},
        "fabio-suplente": {"flavio": (49.0, 77.0), "lula": (34.0, 69.0)},
        "henrique-dado": {"flavio": (35.0, 65.0), "lula": (20.0, 57.0)},
        "gabriela-caso": {"flavio": (2.0, 2.0), "lula": (2.0, 2.0)},
    }
    for slug, por_cenario in esperado.items():
        pontos = S.pontuar_cenarios(_pessoa(dados, slug))
        for cenario, (imp, pec) in por_cenario.items():
            assert (pontos[cenario]["C_imp"], pontos[cenario]["C_pec"]) == (imp, pec)


def test_cenario_lula_reduz_o_que_deve():
    reducao = {
        "DB": (0, 0),
        "D": (5, 3),
        "CD": (15, 8),
        "C": (15, 8),
        "CE": (0, 0),
        "E": (0, 0),
    }
    for bloco, (imp, pec) in reducao.items():
        senador = _senador(bloco=bloco, sinais=["declaracao_pro_impeachment"])
        pontos = S.pontuar_cenarios(senador)
        assert pontos["flavio"]["C_imp"] - pontos["lula"]["C_imp"] == imp
        assert pontos["flavio"]["C_pec"] - pontos["lula"]["C_pec"] == pec


def test_sem_sinal_vale_sem_posicao_e_confianca_baixa(dados):
    fabio = S.pontuar(_pessoa(dados, "fabio-suplente"))
    assert fabio["ajustes"][1]["chave"] == "sem_posicao_localizada"
    assert (fabio["C_imp"], fabio["C_pec"]) == (55 - 6, 80 - 3)
    assert (fabio["confianca"], fabio["incerteza_pp"]) == ("baixa", 14)


def test_confianca(dados):
    nivel = {p["slug"]: S.confianca(p) for p in dados.pessoas()}
    assert nivel["ana-teste"] == "alta"
    assert nivel["bruno-exemplo"] == "alta"
    assert nivel["carla-modelo"] == "media"
    assert nivel["daniel-ficticio"] == "media"
    assert nivel["iara-ministra"] == "baixa"
    assert nivel["joao-exercicio"] == "baixa"
    assert (
        S.confianca(_senador(sinais=["voto_pec8_sim"], mandato="ate_2031")) == "media"
    )
    assert S.confianca(_senador(sinais=["voto_pec8_ausente"])) == "baixa"


def test_regua_publicavel_e_json_puro():
    regua = S.regua_publicavel()
    assert json.loads(json.dumps(regua)) == regua
    assert regua["C"]["limites"] == [2, 97]


# ------------------------------------------------------------- simulação


def test_calibracao_reproduz_a_probabilidade_marginal():
    p = np.array([0.02, 0.2, 0.5, 0.83, 0.97])
    desvio = math.hypot(*M.escalas(0.35, 0.15))
    mu = M.calibrar_locacao(p, desvio)
    nos, pesos = np.polynomial.hermite_e.hermegauss(200)
    media = (M.expit(mu[:, None] + desvio * nos[None, :]) * pesos).sum(1) / pesos.sum()
    assert np.allclose(media, p, atol=1e-9)


def test_escalas_reproduzem_as_correlacoes_latentes():
    a, b = M.escalas(0.35, 0.15)
    variancia = a**2 + b**2 + math.pi**2 / 3
    assert math.isclose((a**2 + b**2) / variancia, 0.35)
    assert math.isclose(a**2 / variancia, 0.15)


def test_simulacao_com_semente_fixa_e_deterministica(dados, resultado):
    outra = saida.montar(dados, sorteios=SORTEIOS, semente=11, gerado_em=AGORA)
    assert outra == resultado
    diferente = saida.montar(dados, sorteios=SORTEIOS, semente=12, gerado_em=AGORA)
    assert diferente["simulacao"] != resultado["simulacao"]


def test_media_simulada_bate_com_votos_esperados(dados):
    sim = saida.montar(dados, sorteios=20000, semente=3, gerado_em=AGORA)["simulacao"]
    for cenario in B.CENARIOS:
        for variante in B.VARIANTES:
            for alvo in M.ALVOS:
                bloco = sim["cenarios"][cenario][variante][alvo]
                assert abs(bloco["media"] - bloco["votos_esperados"]) <= 0.1
                assert sum(bloco["histograma"]) == 20000


def test_p54_nunca_passa_de_p49(resultado):
    for por_variante in resultado["simulacao"]["cenarios"].values():
        for variante in por_variante.values():
            for alvo in M.ALVOS:
                bloco = variante[alvo]
                assert bloco["P54"] <= bloco["P49"]
                assert bloco["p5"] <= bloco["p50"] <= bloco["p95"]
                assert bloco["sem_correlacao"]["P54"] <= bloco["sem_correlacao"]["P49"]


def test_pivo_que_vota_sim_nunca_reduz_a_chance():
    rng = np.random.default_rng(5)
    matriz = rng.random((5000, 9)) < np.linspace(0.2, 0.8, 9)
    pessoas = [
        {"slug": f"s{i}", "nome": f"S{i}", "uf": "GO", "bloco": "C"} for i in range(9)
    ]
    c = [float(x) for x in np.linspace(20, 80, 9)]
    limiar = 5
    lista = M.pivos(matriz, limiar, c, pessoas)
    assert len(lista) == 9
    totais = matriz.sum(axis=1)
    for item in lista:
        assert item["sobe_pp"] >= 0
        assert item["cai_pp"] >= 0
        j = int(item["slug"][1:])
        decisivo = 100 * ((totais - matriz[:, j]) == limiar - 1).mean()
        assert item["decisivo_pp"] == S.r1(decisivo)
    assert [x["decisivo_pp"] for x in lista] == sorted(
        (x["decisivo_pp"] for x in lista), reverse=True
    )


def test_pivos_respeitam_a_faixa_de_c(resultado):
    for por_variante in resultado["simulacao"]["cenarios"].values():
        for lista in por_variante["base"]["pivos"].values():
            for item in lista:
                assert 20 <= item["C"] <= 85
                assert item["sobe_pp"] >= 0


def test_variantes_e_cenarios_trocam_os_ocupantes(dados, resultado):
    cenarios = resultado["simulacao"]["cenarios"]
    assert cenarios["flavio"]["base"]["ocupantes"][8] == "iara-ministra"
    assert cenarios["lula"]["base"]["ocupantes"][8] == "joao-exercicio"
    assert (
        cenarios["flavio"]["suplentes_segundo_turno"]["ocupantes"][2]
        == "diego-suplente"
    )
    assert cenarios["flavio"]["cadeira_sub_judice_vaga"]["ocupantes"][3] is None
    assert dados.origem["diego-suplente"] == "partido"
    assert dados.substitutos["GO-3"]["bloco"] == "E"
    base = cenarios["flavio"]["base"]["imp"]["votos_esperados"]
    vaga = cenarios["flavio"]["cadeira_sub_judice_vaga"]["imp"]["votos_esperados"]
    assert S.r1(base - vaga) == S.r1(67.5 / 100)
    soma = 97 + 60.5 + 27 + 67.5 + 2 + 49 + 2 + 29 + 2
    assert base == S.r1(soma / 100)


# ------------------------------------------------------------------ saída


def _numeros(obj, caminho=""):
    if isinstance(obj, bool):
        return
    if isinstance(obj, float):
        yield caminho, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _numeros(v, f"{caminho}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _numeros(v, f"{caminho}[{i}]")


def test_saida_tem_no_maximo_uma_casa_decimal(resultado):
    publicado = {k: v for k, v in resultado.items() if k != "regua"}
    publicado["simulacao"] = {
        k: v for k, v in resultado["simulacao"].items() if k != "parametros"
    }
    for caminho, valor in _numeros(publicado):
        assert round(valor, 1) == valor, caminho


def test_saida_sem_travessao_e_com_hashes(resultado):
    assert B.travessoes(resultado) == []
    hashes = resultado["hashes_sha256"]
    assert len(hashes) == 11
    assert all(len(h) == 64 for h in hashes.values())


def test_teste_pec8(resultado):
    pec8 = resultado["teste_pec8"]
    votos = {x["slug"]: x["voto"] for x in pec8["senadores"]}
    assert votos == {
        "ana-teste": "sim",
        "bruno-exemplo": "nao",
        "elisa-amostra": "ausente",
        "gabriela-caso": "nao",
        "joao-exercicio": "ausente",
    }
    assert pec8["tabela_K"]["nao"] == {"K_positivo": 2, "K_zero": 0}
    assert pec8["tabela_K"]["ausente"] == {"K_positivo": 1, "K_zero": 1}


def test_fisher_bilateral():
    assert math.isclose(saida.fisher_bilateral(3, 1, 1, 3), 0.4857142857, rel_tol=1e-6)
    assert saida.fisher_bilateral(0, 0, 0, 0) == 1.0


def test_csv_tem_uma_linha_por_cadeira(resultado, tmp_path):
    caminho_json, caminho_csv = saida.gravar(resultado, tmp_path / "senado_2027.json")
    assert json.loads(caminho_json.read_text(encoding="utf-8"))["gerado_em"] == AGORA
    with caminho_csv.open(encoding="utf-8") as arq:
        linhas = list(csv.DictReader(arq))
    assert len(linhas) == 9
    assert tuple(linhas[0]) == saida.COLUNAS_CSV
    ministra = next(x for x in linhas if x["cadeira"] == "CE-3")
    assert ministra["ocupante_lula"] == "joao-exercicio"
    assert ministra["K"] == "100.0"


# --------------------------------------------------------------- validador


def test_validador_rejeita_travessao(tmp_path):
    pasta = _copia(tmp_path)

    def com_travessao(d):
        d["casos"][0]["resumo"] = "Texto com travessão — proibido."

    _editar(pasta, "ana-teste", com_travessao)
    erros = B.carregar(pasta).erros
    assert any("travessão em casos[0].resumo" in e for e in erros)
    with pytest.raises(B.ErroEsquema):
        saida.montar(B.carregar(pasta), sorteios=100)


def test_validador_rejeita_enum_invalido(tmp_path):
    pasta = _copia(tmp_path)

    def enum_ruim(d):
        d["casos"][0]["estagio"] = "suspeito"
        d["sinais_contrapeso"][0]["tipo"] = "apoio_difuso"
        d["bloco"] = "X"

    _editar(pasta, "ana-teste", enum_ruim)
    erros = B.carregar(pasta).erros
    assert any("casos[0].estagio = 'suspeito'" in e for e in erros)
    assert any("sinais_contrapeso[0].tipo = 'apoio_difuso'" in e for e in erros)
    assert any("senador.bloco = 'X'" in e for e in erros)


@pytest.mark.parametrize("data", ["2026-02-30", "2026-13", "07/10/2026", "2026-1-5"])
def test_validador_rejeita_data_invalida(tmp_path, data):
    pasta = _copia(tmp_path)

    def data_ruim(d):
        d["casos"][0]["data_ultima_decisao"] = data

    _editar(pasta, "ana-teste", data_ruim)
    erros = B.carregar(pasta).erros
    assert any("data_ultima_decisao" in e and "não é data ISO" in e for e in erros)


def test_data_parcial_iso_e_aviso_nao_erro():
    assert B.precisao_data("2026-10-07") == "dia"
    assert B.precisao_data("2022-06") == "mes"
    assert B.precisao_data("2017") == "ano"
    assert B.precisao_data("2022-00") is None
    assert B.ano_de("2022-06") == 2022
    erros, avisos = B.validar_senador(
        json.loads((FIXTURE / "senadores/bruno-exemplo.json").read_text()),
        "bruno-exemplo",
    )
    assert erros == []
    assert any("precisão reduzida (mes)" in a for a in avisos)


def test_validador_exige_campos_e_defesa(tmp_path):
    pasta = _copia(tmp_path)

    def sem_campos(d):
        del d["casos"][0]["defesa"]
        d["casos"][0]["fontes"] = []
        d["verificado_em"] = "2026-10"

    _editar(pasta, "ana-teste", sem_campos)
    erros = B.carregar(pasta).erros
    assert any("sem campo obrigatório ['defesa']" in e for e in erros)
    assert any("fontes vazia" in e for e in erros)
    assert any("verificado_em = '2026-10'" in e for e in erros)


def test_casamento_acusa_cadeira_sem_json_e_json_sem_cadeira(tmp_path):
    pasta = _copia(tmp_path)
    (pasta / "senadores/henrique-dado.json").unlink()
    extra = json.loads((pasta / "senadores/ana-teste.json").read_text())
    extra["slug"] = "zeca-avulso"
    (pasta / "senadores/zeca-avulso.json").write_text(json.dumps(extra))
    erros = B.carregar(pasta).erros
    assert any("cadeira CE-2 (henrique-dado): sem JSON" in e for e in erros)
    assert any("zeca-avulso.json: JSON sem cadeira" in e for e in erros)


def test_casamento_acusa_bloco_divergente(tmp_path):
    pasta = _copia(tmp_path)
    _editar(pasta, "bruno-exemplo", lambda d: d.update(bloco="DB"))
    erros = B.carregar(pasta).erros
    assert any("bloco no JSON = 'DB', no elenco = 'D'" in e for e in erros)


def test_elenco_rejeita_contingencia_sem_substituto(dados):
    elenco = copy.deepcopy(dados.elenco)
    elenco["cadeiras"][8]["contingencia"]["substituto"] = None
    elenco["cadeiras"][0]["contingencia"] = {"tipo": "exilio", "substituto": None}
    erros, _ = B.validar_elenco(elenco)
    assert any("ministerio exige substituto" in e for e in erros)
    assert any("'exilio' fora do enum" in e for e in erros)


# ------------------------------------------------------------------- CLI


def _cli():
    spec = importlib.util.spec_from_file_location(
        "senado_2027_motor", ROOT / "scripts/senado-2027-motor.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cli_valida_e_grava(tmp_path, capsys):
    cli = _cli()
    assert cli.main(["--pasta", str(FIXTURE), "--somente-validar"]) == 0
    assert "Esquema válido." in capsys.readouterr().out
    destino = tmp_path / "saida.json"
    argumentos = ["--pasta", str(FIXTURE), "--sorteios", "500", "--saida", str(destino)]
    assert cli.main(argumentos) == 0
    assert destino.exists() and destino.with_suffix(".csv").exists()


def test_cli_falha_com_erro_de_esquema(tmp_path, capsys):
    pasta = _copia(tmp_path)
    _editar(pasta, "ana-teste", lambda d: d.update(uf="XX"))
    assert _cli().main(["--pasta", str(pasta), "--somente-validar"]) == 1
    saida_cli = capsys.readouterr()
    assert "ERROS de esquema" in saida_cli.out
    assert "senador.uf = 'XX'" in saida_cli.out
