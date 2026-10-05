"""Testes da camada de anomalias por zona (apuração de 2026), com dados sintéticos."""

from collections import Counter

import numpy as np
import pytest
from apuracao_2026 import anomalias as an
from apuracao_2026 import anomalias_dados as dados


def _painel(semente=7, n_grupos=4, por_grupo=100, n_atributos=6):
    """Zonas sintéticas: cada grupo (UF) com centro e escala próprios."""
    rng = np.random.default_rng(semente)
    grupos = np.repeat([f"G{i}" for i in range(n_grupos)], por_grupo)
    centros = rng.normal(0.0, 5.0, size=(n_grupos, n_atributos))
    escalas = rng.uniform(0.5, 2.0, size=(n_grupos, n_atributos))
    idx = np.repeat(np.arange(n_grupos), por_grupo)
    x = centros[idx] + escalas[idx] * rng.normal(size=(idx.size, n_atributos))
    return x, grupos, escalas, idx


def _plantar(x, escalas, idx, linha=123, colunas=(1, 4), tamanho=7.0):
    x = x.copy()
    for c in colunas:
        x[linha, c] += tamanho * escalas[idx[linha], c]
    return x


def _z(x, grupos):
    return np.column_stack(
        [an.z_robusto_grupo(x[:, j], grupos)[0] for j in range(x.shape[1])]
    )


def test_escala_robusta_mad_e_casos_degenerados():
    assert an.escala_robusta(np.array([1.0, 2.0, 3.0, 4.0, 100.0])) == pytest.approx(
        an.MAD_K * 1.0
    )
    assert an.escala_robusta(np.array([5.0, 5.0, 5.0])) == 0.0
    # MAD zero com cauda: cai no desvio médio absoluto, positivo e finito.
    s = an.escala_robusta(np.array([0.0, 0.0, 0.0, 0.0, 1.0]))
    assert s == pytest.approx(an.MEDIA_AD_K * 0.2)
    assert an.escala_robusta(np.array([np.nan, np.nan])) == 0.0


def test_z_robusto_centra_em_cada_grupo_e_tolera_constante():
    valores = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 0.0, 1.0, 2.0, 3.0, 4.0])
    grupos = np.array(["A"] * 5 + ["B"] * 5)
    z, centros, _ = an.z_robusto_grupo(valores, grupos)
    assert centros == {"A": 12.0, "B": 2.0}
    assert z[2] == 0.0 and z[7] == 0.0
    assert z[4] == pytest.approx(-z[0]) and z[4] > 0
    constante, _, escalas = an.z_robusto_grupo(np.full(10, 3.0), grupos)
    assert np.all(constante == 0.0)
    assert escalas == {"A": 0.0, "B": 0.0}
    com_ausente, _, _ = an.z_robusto_grupo(np.array([1.0, np.nan, 3.0]), ["A"] * 3)
    assert np.isnan(com_ausente[1]) and np.isfinite(com_ausente[[0, 2]]).all()


@pytest.mark.parametrize("usar_sklearn", [True, False])
def test_outlier_plantado_fica_em_primeiro(usar_sklearn):
    if usar_sklearn and not an.sklearn_disponivel():
        pytest.skip("scikit-learn ausente")
    x, grupos, escalas, idx = _painel()
    x = _plantar(x, escalas, idx)
    escores, meta = an.escores_modelos(_z(x, grupos), usar_sklearn=usar_sklearn)
    final = an.escore_combinado(escores)
    assert int(np.argmax(final)) == 123
    assert final.max() <= 100.0 and final.min() > 0.0
    esperado = {"z_rms", "mahalanobis"} | (
        {"isolation_forest", "lof"} if usar_sklearn else set()
    )
    assert set(escores) == esperado
    assert meta["sklearn"] is usar_sklearn


def test_robusto_a_atributo_constante():
    x, grupos, escalas, idx = _painel()
    x = _plantar(x, escalas, idx)
    com_constante = np.column_stack([x, np.full(x.shape[0], 42.0)])
    z = _z(com_constante, grupos)
    assert np.all(z[:, -1] == 0.0)
    escores, meta = an.escores_modelos(z)
    assert meta["colunas_constantes"] == 1
    for valores in escores.values():
        assert np.isfinite(valores).all()
    assert int(np.argmax(an.escore_combinado(escores))) == 123


def test_outlier_plantado_sobrevive_a_ausentes():
    x, grupos, escalas, idx = _painel()
    x = _plantar(x, escalas, idx)
    x[::17, 0] = np.nan  # ausente vira mediana da UF (z = 0)
    escores, _ = an.escores_modelos(_z(x, grupos), usar_sklearn=False)
    assert int(np.argmax(an.escore_combinado(escores))) == 123


def test_residuo_hierarquico_isola_a_zona_que_destoa_do_municipio():
    # UF com 20 zonas de swing zero, e um município de 4 zonas com efeito
    # comum de +10 pontos, uma delas com +30.
    swing = np.array([0.0] * 20 + [0.10, 0.10, 0.10, 0.30])
    uf = ["X"] * 24
    municipio = [f"m{i}" for i in range(20)] + ["M"] * 4
    peso = np.ones(24)
    r = an.residuo_hierarquico(swing, uf, municipio, peso)
    assert int(np.argmax(np.abs(r["residuo"]))) == 23
    assert list(r["fonte"][20:]) == ["municipio"] * 4
    # o efeito local das três zonas comuns inclui a destoante, mas encolhido
    assert np.all(np.abs(r["residuo"][20:23]) < np.abs(r["residuo"][23]) / 3)
    assert r["swing_uf"][0] == pytest.approx(0.6 / 24)


def test_residuo_hierarquico_usa_vizinhos_quando_municipio_tem_uma_zona():
    swing = np.array([0.0, 0.0, 0.2, 0.2, 0.2])
    vizinhos = [np.array([1]), np.array([0]), np.array([3, 4]), np.array([2, 4]), []]
    vizinhos = [np.asarray(v, dtype=int) for v in vizinhos]
    r = an.residuo_hierarquico(
        swing, ["X"] * 5, list("abcde"), np.ones(5), vizinhos=vizinhos
    )
    assert list(r["fonte"]) == ["vizinhanca"] * 4 + ["uf"]
    assert r["efeito_local"][2] > 0 and r["efeito_local"][0] < 0


def test_vizinhos_proximos_respeita_uf_e_municipio():
    lat = np.array([0.0, 0.0, 0.0, 10.0])
    lon = np.array([0.0, 0.1, 0.2, 0.0])
    viz = an.vizinhos_proximos(lat, lon, ["A", "A", "A", "B"], ["m", "m", "n", "p"], 5)
    assert list(viz[0]) == [2]  # a zona 1 é do mesmo município
    assert list(viz[3]) == []  # sozinha na UF


def test_fator_tamanho_recupera_variancia_maior_em_zona_pequena():
    rng = np.random.default_rng(3)
    # faixa estreita o bastante para o fator não bater nos limites [0,5; 3]
    tamanho = np.exp(rng.uniform(np.log(6_000), np.log(60_000), 4_000))
    z = rng.normal(size=tamanho.size) * (tamanho / np.median(tamanho)) ** -0.5
    fator, inclinacao = an.fator_tamanho(z, np.log(tamanho))
    assert inclinacao == pytest.approx(-0.5, abs=0.08)
    pequenas = tamanho < np.quantile(tamanho, 0.1)
    grandes = tamanho > np.quantile(tamanho, 0.9)
    assert fator[pequenas].mean() > 1.4 > 0.8 > fator[grandes].mean()
    ajustado = z / fator
    razao = np.std(ajustado[pequenas]) / np.std(ajustado[grandes])
    assert razao == pytest.approx(1.0, abs=0.25)


def test_percentis_dividem_empates():
    assert list(an.percentis(np.array([1.0, 2.0, 2.0, 3.0]))) == [
        0.25,
        0.625,
        0.625,
        1.0,
    ]


def test_motivos_ordenam_e_caem_para_combinacao():
    nomes = ["a", "b", "c", "d"]
    assert an.motivos([0.5, -4.0, 3.0, np.nan], nomes) == [("b", -4.0), ("c", 3.0)]
    assert an.motivos([0.5, -1.0, 0.2, 0.1], nomes) == [("b", -1.0), ("a", 0.5)]


def test_explicacoes_por_regra_e_hipotese_padrao():
    pequena = an.explicacoes(
        {"secoes": 9, "eleitorado": 2_500, "referencia_2022": "municipio"}
    )
    assert pequena == ["zona pequena (9 seções), variância alta"]
    padrao = an.explicacoes(
        {"secoes": 300, "eleitorado": 90_000, "referencia_2022": "zona"}
    )
    assert padrao[0].startswith("efeito político local não medido")
    tardia = an.explicacoes(
        {
            "secoes": 300,
            "eleitorado": 90_000,
            "z_atraso": 4.0,
            "z_atraso_2022": 2.0,
            "pct_indigena": 0.4,
            "terceiro_lider": ("Caiado", 0.25),
            "z_terceiros": 3.0,
        }
    )
    assert any("aldeias" in t and "40%" in t for t in tardia)
    assert any("já se repetia em 2022" in t for t in tardia)
    assert any("Caiado 25,0%" in t for t in tardia)
    for frase in pequena + padrao + tardia:
        assert chr(0x2014) not in frase


def test_classificar_local_distingue_aldeia_urbana():
    assert dados.classificar_local("ESCOLA ESTADUAL INDÍGENA X", "", "") == (
        True,
        False,
    )
    assert dados.classificar_local("POSTO - ALDEIA SUMARÉ", "", "ÁREA RURAL") == (
        True,
        False,
    )
    assert dados.classificar_local("COLÉGIO ALDEIA DA SERRA", "ALAMEDA", "ALDEIA") == (
        False,
        False,
    )
    assert dados.classificar_local("ESCOLA QUILOMBOLA", "", "") == (False, True)


def test_ponte_por_locais_reparte_e_compoe():
    mun = ("sp", "71072")
    locais22 = {
        (mun, "0001", "10"): {
            "nome": "ESCOLA A",
            "endereco": "RUA 1",
            "aptos": 100,
            "comparecimento": 80,
            "brancos": 2,
            "nulos": 3,
            "nominais": 75,
            "nominais_2t": 76,
        },
        (mun, "0002", "20"): {
            "nome": "ESCOLA B",
            "endereco": "RUA 2",
            "aptos": 200,
            "comparecimento": 150,
            "brancos": 5,
            "nulos": 5,
            "nominais": 140,
            "nominais_2t": 141,
        },
        (mun, "0002", "21"): {
            "nome": "ESCOLA B",
            "endereco": "RUA 9",
            "aptos": 50,
            "comparecimento": 40,
            "brancos": 1,
            "nulos": 1,
            "nominais": 38,
            "nominais_2t": 38,
        },
    }
    locais26 = {
        (mun, "0400", "1"): {"nome": "ESCOLA A", "endereco": "RUA 1", "eleitores": 60},
        (mun, "0401", "2"): {"nome": "ESCOLA A", "endereco": "RUA 1", "eleitores": 40},
        (mun, "0401", "3"): {"nome": "ESCOLA B", "endereco": "RUA 2", "eleitores": 210},
        (mun, "0401", "4"): {"nome": "OUTRA", "endereco": "RUA 7", "eleitores": 30},
    }
    ponte = dados.cruzar_locais(locais22, locais26)
    assert ponte == {
        (mun, "0400", "1"): (mun, "0001", "10"),
        (mun, "0401", "2"): (mun, "0001", "10"),
        (mun, "0401", "3"): (mun, "0002", "20"),  # desempate pelo endereço
    }
    votos22 = {
        (("sp", "71072", "0001"), 1): Counter({22: 30, 13: 70}),
        (("sp", "71072", "0001"), 2): Counter({22: 40, 13: 60}),
        (("sp", "71072", "0002"), 1): Counter({22: 60, 13: 40}),
        (("sp", "71072", "0002"), 2): Counter({22: 70, 13: 30}),
    }
    ref = dados.referencia_por_locais(locais22, locais26, ponte, votos22)
    nova = ref[("sp", "71072", "0400")]
    assert nova["cobertura"] == 1.0
    assert nova["aptos"] == pytest.approx(60.0)  # 60% do local de 2022
    assert nova["votos_1t"][13] == pytest.approx(0.6 * 75 * 0.7)
    outra = ref[("sp", "71072", "0401")]
    assert outra["cobertura"] == pytest.approx(250 / 280)
    assert outra["aptos"] == pytest.approx(40.0 + 200.0)
    total_1t = sum(outra["votos_1t"].values())
    assert total_1t == pytest.approx(0.4 * 75 + 140)
