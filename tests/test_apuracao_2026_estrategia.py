"""Aritmética do capítulo "O caminho do 2º turno" (scripts/apuracao_2026/estrategia.py).

Os números da regressão central são os do arquivo nacional de presidente do TSE
com 499.248 de 499.248 seções, lido do banco ``apuracao/data/apuracao.sqlite``
(snapshot 513491), e as linhas da Nexus de ``docs/assets/voto_util_092026.json``
(nacional.transferencia). O teste não abre o banco: fixa as entradas.
"""

from __future__ import annotations

import math

import pytest
from apuracao_2026 import estrategia as E
from apuracao_2026 import estrategia_formato as FMT
from apuracao_2026 import estrategia_secoes as S

NEXUS = {
    "Cury": {"Lula": 30, "Flávio": 44, "Branco/nulo": 23, "Indecisos": 2},
    "Caiado": {"Lula": 36, "Flávio": 30, "Branco/nulo": 26, "Indecisos": 7},
    "Renan": {"Lula": 8, "Flávio": 56, "Branco/nulo": 37, "Indecisos": 0},
    "Zema": {"Lula": 13, "Flávio": 59, "Branco/nulo": 29, "Indecisos": 0},
    "Samara": {"Lula": 58, "Flávio": 6, "Branco/nulo": 36, "Indecisos": 0},
}
FLAVIO_1T = 56_104_503
LULA_1T = 53_879_538
TERCEIROS = {
    "Cury": ("Cury", 3_448_569),
    "Renan": ("Renan", 2_675_887),
    "Caiado": ("Caiado", 2_605_148),
    "Zema": ("Zema", 326_488),
    "Samara": ("Samara", 122_911),
    "Hertz": ("Samara", 43_103),
    "Clariana": ("Zema", 40_043),
    "Edmilson": ("Samara", 22_693),
    "Grassi": ("Zema", 16_881),
    "Rui": ("Samara", 15_024),
}


def _linhas_e_origens(matriz: dict) -> tuple[dict, dict]:
    normal = {k: E.normalizar_linha(v) for k, v in matriz.items()}
    linhas = {nome: normal[linha] for nome, (linha, _v) in TERCEIROS.items()}
    origens = {nome: v for nome, (_l, v) in TERCEIROS.items()}
    return linhas, origens


# ---------------------------------------------------------------- transferência


def test_normalizar_linha_soma_um_mesmo_com_arredondamento():
    for linha in NEXUS.values():
        n = E.normalizar_linha(linha)
        assert math.isclose(n["flavio"] + n["lula"] + n["fora"], 1.0)
        assert n["fora"] >= 0
    renan = E.normalizar_linha(NEXUS["Renan"])
    assert math.isclose(renan["flavio"], 56 / 101)
    assert math.isclose(renan["lula"], 8 / 101)


def test_normalizar_linha_sem_massa_falha():
    with pytest.raises(ValueError):
        E.normalizar_linha({"Lula": 0, "Flávio": 0})


def test_destino_tres_hipoteses():
    linha = {"flavio": 0.5, "lula": 0.2, "fora": 0.3}
    assert E.destino(linha, "fica_fora") == (0.5, 0.2)
    f, lu = E.destino(linha, "proporcional")
    assert math.isclose(f, 0.5 + 0.3 * 5 / 7)
    assert math.isclose(lu, 0.2 + 0.3 * 2 / 7)
    assert math.isclose(f + lu, 1.0)
    f, lu = E.destino(linha, "meio_a_meio")
    assert math.isclose(f, 0.65)
    assert math.isclose(lu, 0.35)
    with pytest.raises(ValueError):
        E.destino(linha, "outra")


def test_destino_proporcional_sem_escolha_divide_ao_meio():
    assert E.destino({"flavio": 0.0, "lula": 0.0, "fora": 1.0}, "proporcional") == (
        0.5,
        0.5,
    )


def test_projetar_conta_a_mao():
    linhas = {"A": {"flavio": 0.6, "lula": 0.1, "fora": 0.3}}
    p = E.projetar(100, 90, {"A": 20}, linhas, "fica_fora")
    assert p["flavio"] == 112
    assert p["lula"] == 92
    assert p["margem_votos"] == 20
    assert p["detalhe"][0]["fora"] == 6
    assert p["detalhe"][0]["saldo_flavio"] == 10


def test_meio_a_meio_nao_muda_margem_em_votos():
    linhas, origens = _linhas_e_origens(NEXUS)
    fora = E.projetar(FLAVIO_1T, LULA_1T, origens, linhas, "fica_fora")
    meio = E.projetar(FLAVIO_1T, LULA_1T, origens, linhas, "meio_a_meio")
    assert abs(fora["margem_votos"] - meio["margem_votos"]) <= 1
    assert meio["validos"] > fora["validos"]
    assert meio["margem_pp"] < fora["margem_pp"]


def test_regressao_projecao_central_nexus():
    linhas, origens = _linhas_e_origens(NEXUS)
    p = E.projetar(FLAVIO_1T, LULA_1T, origens, linhas, "fica_fora")
    assert p["flavio"] == 60_146_496
    assert p["lula"] == 56_251_351
    assert p["margem_votos"] == 3_895_146
    assert p["flavio_pct"] == 51.67
    renan = next(d for d in p["detalhe"] if d["origem"] == "Renan")
    assert renan["saldo_flavio"] == round(2_675_887 * 48 / 101)
    proporcional = E.projetar(FLAVIO_1T, LULA_1T, origens, linhas, "proporcional")
    assert proporcional["validos"] == FLAVIO_1T + LULA_1T + sum(origens.values())


def test_equilibrio_zera_a_margem():
    d, reserva = 2_224_965, 9_316_747
    x = E.equilibrio(d, reserva)
    assert x is not None
    assert math.isclose(d - x * reserva + (1 - x) * reserva, 0.0, abs_tol=1e-6)
    assert round(100 * x, 2) == 61.94
    assert E.equilibrio(d, 0) is None
    alto = E.equilibrio(10, 4)
    assert alto is not None
    assert alto > 1  # inalcançável só com a reserva


def _valor(x: float | None) -> float:
    assert x is not None
    return x


def test_eleitores_novos_para_empatar():
    assert math.isclose(_valor(E.eleitores_novos_para_empatar(100, 0.6)), 500)
    assert math.isclose(_valor(E.eleitores_novos_para_empatar(100, 0.75)), 200)
    assert E.eleitores_novos_para_empatar(100, 0.5) is None


def test_analogo_2022_taxas_nacionais():
    b22 = {
        "bolsonaro_1t": 51_072_345,
        "bolsonaro_2t": 58_206_354,
        "lula_1t": 57_259_504,
        "lula_2t": 60_345_999,
        "terceiros_1t": 118_229_719 - 57_259_504 - 51_072_345,
    }
    a = E.analogo_2022(FLAVIO_1T, LULA_1T, 9_316_747, b22)
    assert round(a["taxa_flavio"], 4) == 0.7208
    assert round(a["taxa_lula"], 4) == 0.3118
    assert math.isclose(a["flavio"], FLAVIO_1T + a["taxa_flavio"] * 9_316_747)
    vazio = E.analogo_2022(1, 2, 3, {**b22, "terceiros_1t": 0})
    assert vazio["flavio"] == 1
    assert vazio["lula"] == 2


# ---------------------------------------------------------------- estoque e geografia


def test_estoque_formula():
    # 1000 votos de referência com 50%; hoje 40%: faltam 20% da parcela.
    assert math.isclose(E.estoque(1000, 50.0, 40.0), 200.0)
    assert E.estoque(1000, 50.0, 55.0) == 0.0
    assert E.estoque(1000, 0.0, 10.0) == 0.0


def test_estoque_sao_paulo():
    # Bolsonaro 2022 2º turno em SP: 14.216.587 (55,24%); Flávio 2026: 51,93%.
    est = E.estoque(14_216_587, 55.24, 51.93)
    assert math.isclose(est, 14_216_587 * (1 - 51.93 / 55.24))
    assert 850_000 < est < 852_000


def test_estoque_municipal_maior_ou_igual_que_agregado():
    # Dois municípios: um acima e outro abaixo da referência.
    a = {"ref": 100, "ref_pct": 50.0, "pct": 60.0}
    b = {"ref": 100, "ref_pct": 50.0, "pct": 40.0}
    soma_mun = sum(E.estoque(m["ref"], m["ref_pct"], m["pct"]) for m in (a, b))
    agregado = E.estoque(200, 50.0, 50.0)
    assert soma_mun >= agregado
    assert math.isclose(soma_mun, 20.0)
    assert agregado == 0.0


def test_comparar_uf_campos_coerentes():
    a26 = {
        "flavio": 520,
        "lula": 380,
        "validos": 1000,
        "eleitores": 1300,
        "comparecimento": 1050,
    }
    t1 = {
        "bolsonaro": 480,
        "lula": 410,
        "validos": 1000,
        "eleitores": 1280,
        "comparecimento": 1010,
    }
    t2 = {
        "bolsonaro": 560,
        "lula": 440,
        "validos": 1000,
        "eleitores": 1280,
        "comparecimento": 1020,
    }
    c = E.comparar_uf("SP", a26, t1, t2)
    assert c["regiao"] == "Centro-Sul"
    assert c["flavio_menos_bolsonaro_1t_pp"] == 4.0
    assert c["flavio_menos_bolsonaro_2t_pp"] == -4.0
    assert c["estoque_flavio"] == round(E.estoque(560, 56.0, 52.0))
    assert c["estoque_lula"] == round(E.estoque(440, 44.0, 38.0))
    assert c["ja_supera_bolsonaro_2t"] is False
    assert c["deficit_votos_flavio"] == 40
    assert c["terceiros"] == 100


def test_regiao_de():
    assert E.regiao_de("ba") == "Nordeste"
    assert E.regiao_de("AM") == "Norte"
    assert E.regiao_de("DF") == "Centro-Sul"
    assert E.regiao_de("ZZ") == "Exterior"
    assert len(E.NORDESTE) == 9
    assert len(E.NORTE) == 7


def test_saldo_comparecimento():
    # 1 milhão de aptos, +1 ponto, 95% válidos, Flávio 60 × Lula 30.
    assert math.isclose(E.saldo_comparecimento(1_000_000, 1.0, 0.95, 0.6, 0.3), 2850.0)
    assert E.saldo_comparecimento(1_000_000, 1.0, 0.95, 0.3, 0.6) < 0


def test_variacao_comparecimento_2022():
    t1 = {"comparecimento": 790, "eleitores": 1000, "bolsonaro": 400, "lula": 420}
    t2 = {"comparecimento": 800, "eleitores": 1000, "bolsonaro": 470, "lula": 450}
    v = E.variacao_comparecimento_2022(t1, t2)
    assert v["variacao_votos"] == 10
    assert v["variacao_pp"] == 1.0
    assert v["ganho_bolsonaro"] == 70
    assert v["ganho_lula"] == 30


def test_correlacao():
    assert math.isclose(_valor(E.correlacao([1, 2, 3], [2, 4, 6])), 1.0)
    assert math.isclose(_valor(E.correlacao([1, 2, 3], [3, 2, 1])), -1.0)
    assert E.correlacao([1, 2], [1, 2]) is None
    assert E.correlacao([1, 1, 1], [1, 2, 3]) is None


# ---------------------------------------------------------------- governadores e Congresso


def test_vao_em_pontos_e_votos():
    v = E.vao(600, 1000, 500, 1100)
    assert v["vao_votos"] == 100
    assert v["vao_pp"] == round(60.0 - 100 * 500 / 1100, 2)


def test_consolidacao_entre_turnos_minas():
    # Datafolha pp. 20 e 21: eleitor de Cleitinho, Flávio 60 → 71, Lula 19 → 25.
    taxa = E.consolidacao_entre_turnos(
        {"Flávio": 60, "Lula": 19}, {"Flávio": 71, "Lula": 25}
    )
    assert math.isclose(taxa, 0.05)
    assert round(taxa * 6_321_590) == 316_080


def test_limiares_do_congresso():
    assert E.maioria_absoluta(513) == 257
    assert E.tres_quintos(513) == 308
    assert E.maioria_absoluta(81) == 41
    assert E.tres_quintos(81) == 49


def test_ordenar_movimentos():
    ms = [{"votos_esperados": 5}, {"votos_esperados": 20}, {"votos_esperados": -3}]
    out = E.ordenar_movimentos(ms)
    assert [m["votos_esperados"] for m in out] == [20, 5, -3]
    assert [m["ordem"] for m in out] == [1, 2, 3]


def test_alinhado_e_lado():
    alinhados = {
        "LUCAS RIBEIRO": {"uf": "PB", "nome": "Lucas Ribeiro"},
        "EDUARDO PAES": {"uf": "RJ", "nome": "Eduardo Paes"},
    }
    assert S._alinhado(alinhados, "PB", "LUCAS RIBEIRO")
    assert not S._alinhado(alinhados, "RJ", "DOUGLAS RUAS")
    assert not S._alinhado(alinhados, "MS", "EDUARDO RIEDEL")
    assert S.lado("centro", True) == "lula"
    assert S.lado("centro-esquerda", False) == "lula"
    assert S.lado("centro-direita", False) == "flavio"
    assert S.lado("centro", False) == "centro"


# ---------------------------------------------------------------- texto


def test_formatacao_do_texto():
    assert FMT.qtd(2_224_965) == "2,22 milhões de votos"
    assert FMT.qtd(1_570_998) == "1,57 milhão de votos"
    assert FMT.qtd(992_206) == "992 mil votos"
    assert FMT.qtd(5_807, "eleitores") == "5.807 eleitores"
    assert FMT.sinal(-0.78) == "−0,78"
    assert FMT.sinal(1.14) == "+1,14"
    assert FMT.sinal_votos(-57_634) == "−57.634"
    assert FMT.pontos(1.87) == "1,87 ponto"
    assert FMT.pontos(-2.69) == "2,69 pontos"
    assert FMT.nome("CLEITINHO AZEVEDO") == "Cleitinho Azevedo"
    assert FMT.nome("FEIRA DE SANTANA") == "Feira de Santana"
    assert FMT.nome("JHC") == "JHC"
    assert FMT.lista_e(["a", "b", "c"]) == "a, b e c"
    assert FMT.extenso(6, feminino=True) == "seis"
    assert FMT.extenso(2, feminino=True) == "duas"
    assert FMT.extenso(12) == "12"
    assert FMT.hora_br("2026-10-05T02:59:31.000Z") == "04/10/2026, 23h59"


def test_tabela_alinha_so_colunas_numericas():
    t = FMT.tabela(["UF", "Votos"], [["SP", "1.000"], ["RJ", "−200"]])
    assert t.splitlines()[1] == "| --- | ---: |"
    assert chr(0x2014) not in t
