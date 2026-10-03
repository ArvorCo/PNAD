"""Âncora dinâmica (DLM) e validação preditiva por origem móvel."""

import json
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predicao_2026 import dinamico, motor, preditiva  # noqa: E402

TRUE = np.array([0.40, 0.38, 0.14, 0.04, 0.04])
EFFECTS = {
    "A": [0.02, -0.02, 0.0, 0.0, 0.0],
    "B": [-0.02, 0.02, 0.0, 0.0, 0.0],
    "C": [0.0, 0.0, -0.01, 0.01, 0.0],
    "D": [0.0, 0.0, 0.01, -0.01, 0.0],
}


def synthetic(n_polls=48, seed=7):
    rng = np.random.default_rng(seed)
    start = date(2026, 8, 20)
    polls = []
    for i in range(n_polls):
        house = "ABCD"[i % 4]
        begin = start + timedelta(days=i // 2)
        p = np.maximum(TRUE + EFFECTS[house], 1e-4)
        p /= p.sum()
        vector = rng.multinomial(2000, p) / 2000
        polls.append(
            {
                "id": f"{house}-{i}",
                "instituto": house,
                "campo": {
                    "inicio": begin.isoformat(),
                    "fim": (begin + timedelta(days=2)).isoformat(),
                },
                "divulgacao": (begin + timedelta(days=3)).isoformat(),
                "n": 2000,
                "previsao_vetor": vector.tolist(),
            }
        )
    return polls


@pytest.fixture(scope="module")
def data():
    return json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )


def test_dlm_recovers_level_and_house_effects():
    polls = synthetic()
    fitted = dinamico.fit(polls, date(2026, 10, 15))
    final = np.array(fitted["estado_final"]["vetor"])
    assert final.sum() == pytest.approx(1)
    assert (final >= 0).all()
    np.testing.assert_allclose(final, TRUE, atol=0.012)
    effects = fitted["efeitos_casa"]
    assert effects["A"]["efeito_pp"]["lula"] > 1
    assert effects["B"]["efeito_pp"]["flavio"] > 1
    # Soma zero entre casas, categoria a categoria.
    for k in dinamico.CATEGORIES:
        assert sum(h["efeito_pp"][k] for h in effects.values()) == pytest.approx(
            0, abs=1e-6
        )
    # Efeito de casa soma zero entre categorias: as partes continuam somando 1.
    for h in effects.values():
        assert sum(h["efeito_pp"].values()) == pytest.approx(0, abs=1e-6)
    assert fitted["parametros"]["otimizador_convergiu"]


def test_dlm_is_deterministic_and_uses_no_future_wave():
    polls = synthetic()
    a = dinamico.level(polls, date(2026, 9, 20))[0]
    assert np.array_equal(a, dinamico.level(polls, date(2026, 9, 20))[0])
    cutoff = date(2026, 9, 10)
    info = preditiva.released(polls, cutoff)
    assert info and all(p["divulgacao"] <= cutoff.isoformat() for p in info)
    assert all(p["campo"]["fim"] <= cutoff.isoformat() for p in info)


def test_dlm_rejects_too_short_or_invalid_series():
    with pytest.raises(ValueError):
        dinamico.fit(synthetic()[:2], date(2026, 10, 1))
    bad = synthetic()[:5]
    bad[0]["previsao_vetor"] = [0.5, -0.1, 0.3, 0.2, 0.1]
    with pytest.raises(ValueError):
        dinamico.fit(bad, date(2026, 10, 1))


def test_dlm_convention_matches_engine():
    assert dinamico.DEFF == motor.DEFF
    assert dinamico.CATEGORIES == motor.GROUPS


def test_published_dynamic_anchor_is_consistent(data):
    n = data["nacional"]
    d = n["dinamico"]
    assert n["alvos"]["dinamico"] == d["estado_final"]["vetor"]
    assert sum(n["alvos"]["dinamico"]) == pytest.approx(1)
    assert min(n["alvos"]["dinamico"]) >= 0
    assert d["n_ondas"] == len(n["pesquisas"])
    assert d["vetor_tipo"] == "previsao_vetor"
    assert d["janela_inicio"] == "2026-08-15"
    assert d["parametros"]["otimizador_convergiu"]
    assert d["log_verossimilhanca"] >= d["parametros"]["log_verossimilhanca_phi_1"]
    for k in dinamico.CATEGORIES:
        assert sum(h["efeito_pp"][k] for h in d["efeitos_casa"].values()) == (
            pytest.approx(0, abs=1e-6)
        )
    assert d["trajetoria"][-1]["data"] == data["referencia"]
    assert "Âncora dinâmica (DLM com efeitos de casa)" in data["sensibilidades"]
    # A central não muda por causa da âncora nova.
    assert data["configuracao"]["defaults"]["base"] == "inclusivo"


def test_predictive_validation_is_labelled_and_paired(data):
    v = data["validacao_preditiva"]
    assert "não da urna" in v["natureza"]
    disk = json.loads(
        (ROOT / "docs/assets/predicao_2026_validacao_preditiva.json").read_text()
    )
    assert disk["hash_modelo"] == data["hash_modelo"]
    assert {k: x for k, x in disk.items() if k != "hash_modelo"} == v
    for section in ("origem_movel", "deixa_uma_casa_fora", "com_casa_do_alvo"):
        sizes = {m["n_pares"] for m in v[section]["metricas"].values()}
        assert sizes == {v[section]["n_pares"]}
    assert "recencia_3d_7d" in v["origem_movel"]["metricas"]
    assert "dinamico" in v["origem_movel"]["metricas"]


def test_rolling_targets_start_after_origin():
    polls = synthetic()
    pairs = preditiva.rolling(polls)
    assert pairs
    by_id = {p["id"]: p for p in polls}
    for pair in pairs:
        start = by_id[pair["alvo"]]["campo"]["inicio"]
        assert 1 <= pair["horizonte_dias"] <= preditiva.HORIZON
        assert start > pair["origem"]


def test_page_has_dynamic_tables():
    html = (ROOT / "docs/predicao_2026_1T_presidente.html").read_text()
    assert "Efeitos de casa do modelo dinâmico" in html
    assert "Origem móvel, todas as casas" in html
    assert 'value="dinamico"' in html


def test_browser_dynamic_anchor_is_recentred(data):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node necessário para verificar a simulação no navegador")
    script = """const fs=require('fs'), engine=require(process.argv[1]);
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    (async()=>{const out={};for(const base of ['inclusivo','dinamico'])
      out[base]=await engine.simulate(x,{base},()=>{},()=>false,400);
    process.stdout.write(JSON.stringify(out));})();"""
    run = subprocess.run(
        [node, "-e", script, str(ROOT / "docs/assets/predicao_2026.js")],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(run.stdout)
    sens = data["sensibilidades"]
    expected = {
        "inclusivo": sens["Central inclusiva com recência, sem voto útil adicional"],
        "dinamico": sens["Âncora dinâmica (DLM com efeitos de casa)"],
    }
    for base, result in out.items():
        center = result["intervalos"]["lula"][1]
        assert center == pytest.approx(
            expected[base]["brasil"]["percentuais"]["lula"], abs=0.3
        )
