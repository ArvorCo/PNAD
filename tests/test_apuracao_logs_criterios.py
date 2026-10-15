"""Regras independentes de voto e tratamento de cobertura insuficiente."""

import pandas as pd
from apuracao_logs.criterios import CRITERIOS, avaliar, campos, referencias
from apuracao_logs.parser import analisar
from apuracao_logs.processamento import reconciliar
from test_apuracao_logs import ciclo, pacote


def registro():
    r = reconciliar(
        analisar(pacote(ciclo())),
        {
            "comparecimento": 1,
            "hab_biometria": 1,
            "hab_ano_nascimento": 0,
            "comp_sem_biometria": 0,
            "fase": 2,
            "pleito": 3220,
        },
    )
    return r


def amostra():
    r = registro()
    r["elegivel_tempo"] = True
    r["motivos_tempo"] = []
    r["modelos"] = ["UE2022"]
    r["bu"]["modelo_urna"] = "UE2022"
    r["tempo_por_cargos"]["1"]["n"] = 100
    row = {"uf": "ZZ", "mun": "29327", "zona": 1, **campos(r)}
    row.update(
        voto_mediana=50.0,
        habilitacao_mediana=20.0,
        den_bio=100,
        comparecimento=100,
        biografica_pct=5.0,
        sem_biometria_pct=5.0,
    )
    return r, row


def test_referencia_precisa_de_trinta_pares():
    _, row = amostra()
    df = pd.DataFrame([row] * 29)
    ref = referencias(
        df, "voto_mediana", ["uf", "modelo", "cargos"], df.elegivel_tempo, 3
    )
    assert ref.ref.isna().all()
    df = pd.DataFrame([row] * 30)
    ref = referencias(
        df, "voto_mediana", ["uf", "modelo", "cargos"], df.elegivel_tempo, 3
    )
    assert (ref.ref == 50).all()


def test_exterior_e_numero_de_cargos_nao_misturam_referencias():
    _, row = amostra()
    df = pd.DataFrame(
        [row] * 30 + [{**row, "uf": "SP", "cargos": "6", "voto_mediana": 90}] * 30
    )
    ref = referencias(
        df, "voto_mediana", ["uf", "modelo", "cargos"], df.elegivel_tempo, 3
    )
    assert list(ref.ref.unique()) == [50, 90]


def test_biometria_ausente_nao_vira_discrepancia():
    r = reconciliar(
        analisar(pacote(ciclo())), {"comparecimento": 1, "fase": 2, "pleito": 3220}
    )
    assert r["biometria_confere"] is None
    row = {"uf": "ZZ", "mun": "29327", "zona": 1, **campos(r)}
    flags, _ = avaliar(pd.DataFrame([row]), [r])
    assert "biometria_divergente" not in flags[0]
    assert not row["elegivel_bio"]
    assert row["biometria_status"] == "ausente_bu"


def test_diagnosticos_nos_dois_sentidos_e_sensibilidade():
    r, row = amostra()
    df = pd.DataFrame(
        [row] * 40 + [{**row, "voto_mediana": 15}, {**row, "voto_mediana": 90}]
    )
    flags, _ = avaliar(df, [r] * len(df))
    assert "tempo_rapido" in flags[-2]
    assert "tempo_lento" in flags[-1]
    assert len(CRITERIOS) == 18
    amplo, _ = avaliar(df, [r] * len(df), 3)
    estrito, _ = avaliar(df, [r] * len(df), 5)
    assert all(set(b) <= set(a) for a, b in zip(amplo, estrito, strict=True))


def test_comparacao_biografica_tem_denominador_e_diferenca_minimos():
    r, row = amostra()
    df = pd.DataFrame(
        [row] * 40
        + [
            {**row, "biografica_pct": 30, "den_bio": 100},
            {**row, "biografica_pct": 30, "den_bio": 10},
            {**row, "biografica_pct": 10, "den_bio": 100},
        ]
    )
    flags, _ = avaliar(df, [r] * len(df))
    assert "biografica_alta" in flags[-3]
    assert "biografica_alta" not in flags[-2]
    assert "biografica_alta" not in flags[-1]


def test_modelos_mistos_nao_entram_em_referencia_de_modelo_unico():
    r, _ = amostra()
    r["modelos"] = ["UE2013", "UE2022"]
    row = campos(r)
    assert not row["modelo_comparavel"] and not row["elegivel_tempo"]
    assert "modelo_indeterminado_misto_ou_divergente" in row["motivos_tempo"]
    # A contagem continua reconciliada; taxas observadas não viram inexistentes.
    assert row["elegivel_bio"]


def test_identidade_excluida_e_diagnostico_sem_alterar_contagem_conciliada():
    r, row = amostra()
    r["contagens"]["urnas_excluidas"] = 1
    row.update(campos(r))
    flags, _ = avaliar(pd.DataFrame([row]), [r])
    assert "identidade_nao_confirmada" in flags[0]
    assert "contagem_divergente" not in flags[0]
    assert row["identificadores_excluidos"] == 1
