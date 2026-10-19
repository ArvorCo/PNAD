"""Conservação, fronteiras de inferência e regressões do experimento territorial."""

import json
from datetime import date

import numpy as np
import pandas as pd
import pytest
from projecao_secoes_2t.fontes import PARTS, ROOT, complete_current
from projecao_secoes_2t.motor import DEST, bounds, matrix_fit, predict, share
from projecao_secoes_2t.pesquisas import calibrate, national_poll, update_states


def sample():
    rng = np.random.default_rng(871)
    x = rng.dirichlet([3, 3, 1, 1, 2], 120)
    matrix = np.array(
        [
            [0.94, 0.01, 0.01, 0.04],
            [0.02, 0.94, 0.01, 0.03],
            [0.6, 0.25, 0.05, 0.1],
            [0.1, 0.1, 0.7, 0.1],
            [0.05, 0.05, 0.05, 0.85],
        ]
    )
    y = x @ matrix
    data = pd.DataFrame(
        {
            "uf": ["SP"] * 60 + ["BA"] * 60,
            "mun": ["00001"] * 60 + ["00002"] * 60,
            "zona": 1,
            "secao": range(120),
            "local_1": "ESCOLA",
            "aptos_1": 1000,
            "aptos_2": 1000,
        }
    )
    for i, name in enumerate(PARTS):
        data[f"{name}_1"] = 1000 * x[:, i]
    for i, name in enumerate(DEST):
        data[f"{name}_2"] = 1000 * y[:, i]
    data["outros_2"] = 0
    return data, x, y, matrix


def test_matrix_recovers_identifiable_synthetic_system():
    _, x, y, expected = sample()
    fitted = matrix_fit(x, y, np.ones(len(x)) * 1000, np.ones((5, 4)) / 4, 0)
    assert np.allclose(fitted, expected, atol=1e-4)
    assert np.allclose(fitted.sum(axis=1), 1)
    assert (fitted >= 0).all()


def test_every_model_conserves_electorate_even_without_matching_section():
    data, _, _, _ = sample()
    target = data.copy()
    target["local_1"] = "OUTRA ESCOLA"
    target.loc[:5, "mun"] = "99999"
    outputs, diagnostics = predict(data, target)
    assert diagnostics["casamento"]["secoes_com_chave_e_local"] == 0
    for result in outputs.values():
        assert np.isfinite(result).all()
        assert (result >= 0).all()
        assert np.allclose(result.sum(axis=1), 1)


def test_calibration_hits_national_target_and_preserves_nonvalids():
    _, _, y, _ = sample()
    weights = np.arange(len(y)) + 100
    adjusted, delta = calibrate(y, weights, 0.59)
    counts = (adjusted * weights[:, None]).sum(axis=0)
    assert share(counts[None])[0] == pytest.approx(0.59, abs=1e-12)
    assert np.allclose(adjusted[:, 2:], y[:, 2:])
    assert np.allclose(adjusted.sum(axis=1), 1)
    assert delta > 0


def test_state_update_is_local_before_national_calibration():
    data, _, y, _ = sample()
    row = {
        "uf": "SP",
        "n": 1000,
        "publicado": {"flavio": 65, "lula": 30},
        "recencia": 0.5,
    }
    updated, audit = update_states(data, y, [row], 2)
    assert np.array_equal(updated[data.uf == "BA"], y[data.uf == "BA"])
    assert 0 < audit[0]["peso_pesquisa"] < 0.5
    assert (
        audit[0]["anterior_pct"]
        < audit[0]["atualizado_antes_calibracao_pct"]
        < audit[0]["pesquisa_pct"]
    )


def test_transfer_bounds_do_not_treat_net_gains_as_individual_flows():
    frame = pd.DataFrame(
        {
            "aptos_1": [100, 100],
            "aptos_2": [100, 101],
            "outros_1": [20, 20],
            "direita_2": [90, 80],
        }
    )
    out = bounds(frame)
    assert out["secoes"] == 1
    assert out["minimo_pct"] == 50
    assert out["maximo_pct"] == 100


def test_national_poll_rejects_date_mismatch():
    with pytest.raises(ValueError, match="Corte"):
        national_poll({"reference": "2026-10-20"}, date(2026, 10, 19))


def test_published_report_and_retrospective_are_coherent():
    path = ROOT / "docs/assets/projecao_secoes_2t_2026.json"
    report = json.loads(path.read_text())
    assert report["validacao"]["treino"] == 2018
    assert report["validacao"]["teste"] == 2022
    results = report["validacao"]["resultados"]
    assert report["selecionado"] == min(
        results, key=lambda key: results[key]["rmse_uf_pp"]
    )
    aptos = report["cobertura"]["aptos"]
    assert aptos == 157828968
    for item in report["nacional"].values():
        assert sum(item["votos"].values()) == pytest.approx(aptos, abs=0.01)
    fusion = report["fusao"]
    expected = (1 - fusion["peso_pesquisas"]) * fusion["historico_pct"] + fusion[
        "peso_pesquisas"
    ] * fusion["pesquisas_pct"]
    assert report["nacional"]["combinado"]["flavio_validos"] == pytest.approx(expected)
    assert len({r["uf"] for r in fusion["estaduais"]}) == 6
    states = pd.DataFrame(report["ufs"]["linhas"], columns=report["ufs"]["colunas"])
    for part in DEST:
        assert states[f"combinado_{part}"].sum() == pytest.approx(
            report["nacional"]["combinado"]["votos"][part], abs=0.01
        )


def test_local_coverage_complement_conserves_official_totals():
    path = ROOT / "data/outputs/projecao_secoes_2t/secoes_2026.csv.gz"
    if not path.exists():
        pytest.skip("Extrato local pesado ausente")
    raw = pd.read_csv(path, dtype={"uf": str, "mun": str})
    completed, coverage = complete_current(raw)
    assert coverage["aptos_sem_secao"] == 432714
    assert coverage["municipios_com_residuo"] == 3
    residual = completed[completed.unidade == "residuo_municipal"]
    assert (residual.secao == 0).all()
    assert (residual[[f"{p}_1" for p in PARTS]].sum(axis=1) == residual.aptos_1).all()
