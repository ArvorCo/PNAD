"""Âncora de tendência: transição exata, recuperação de inclinação, projeção,
paridade com o navegador, validação preditiva e fontes da divisão da migração."""

import json
import re
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest
from predicao_2026 import migracao, preditiva, simulador, tendencia
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parents[1]
START = np.array([0.40, 0.36, 0.16, 0.04, 0.04])
SLOPE = np.array([0.0010, 0.0020, -0.0030, 0.0, 0.0])  # fração por dia
EFFECTS = {
    "A": [0.02, -0.02, 0.0, 0.0, 0.0],
    "B": [-0.02, 0.02, 0.0, 0.0, 0.0],
    "C": [0.0, 0.0, -0.01, 0.01, 0.0],
    "D": [0.0, 0.0, 0.01, -0.01, 0.0],
}
FIRST = date(2026, 8, 20)


def trending(n_polls=48, seed=11, slope=SLOPE):
    rng = np.random.default_rng(seed)
    polls = []
    for i in range(n_polls):
        house = "ABCD"[i % 4]
        begin = FIRST + timedelta(days=i // 2)
        mid = i // 2 + 1
        p = np.maximum(START + slope * mid + EFFECTS[house], 1e-4)
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
                "publicado_vetor": vector.tolist(),
            }
        )
    return polls


@pytest.fixture(scope="module")
def data():
    return json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )


@pytest.mark.parametrize("kappa", [0.0, 1e-5, 2e-3, 0.2, 1.5])
@pytest.mark.parametrize("dt", [0.5, 1.0, 3.0, 9.0])
def test_transition_matches_van_loan(kappa, dt):
    q_level, q_slope = 2e-5, 3e-7
    g, e, m = tendencia.transition(dt, q_level, q_slope, kappa)
    A = np.array([[0.0, 1.0], [0.0, -kappa]])
    Q = np.diag([q_level, q_slope])
    block = np.block([[-A, Q], [np.zeros((2, 2)), A.T]]) * dt
    E = expm(block)
    F = E[2:, 2:].T
    np.testing.assert_allclose(F, [[1, g], [0, e]], rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(m, F @ E[:2, 2:], rtol=1e-6, atol=1e-14)


def test_constant_slope_is_recovered():
    polls = trending()
    today = date(2026, 9, 15)
    fitted = tendencia.fit_variant(polls, today, today, variant="constante")
    a, P, _ = fitted["ultimo"]
    slopes = tendencia._slopes(a, P)
    for k, name in enumerate(("lula", "flavio", "outros")):
        assert slopes["pp_dia"][name] == pytest.approx(100 * SLOPE[k], abs=0.06)
        # A inclinação verdadeira fica dentro de três desvios.
        assert abs(slopes["pp_dia"][name] - 100 * SLOPE[k]) < 3 * (
            slopes["dp_pp_dia"][name]
        )


def test_projection_adds_slope_times_horizon():
    polls = trending()
    state, _ = tendencia.filtered(polls, variant="constante")
    now = tendencia.vector_at(state, state["time"])
    later = tendencia.vector_at(state, state["time"] + 4)
    slope = state["a"][tendencia.FREE : 2 * tendencia.FREE]
    np.testing.assert_allclose((later - now)[: tendencia.FREE], 4 * slope, atol=2e-4)
    # Projeção para trás não existe: o estado fica no último campo.
    np.testing.assert_allclose(tendencia.vector_at(state, state["time"] - 5), now)


def test_damped_projection_converges():
    g_short = tendencia.transition(1.0, 0.0, 0.0, 0.5)[0]
    g_long = tendencia.transition(100.0, 0.0, 0.0, 0.5)[0]
    assert g_short < 1
    assert g_long == pytest.approx(2.0, rel=1e-6)


def test_fe_regression_and_acceleration_on_synthetic():
    polls = trending()
    today = date(2026, 9, 15)
    linear = tendencia.fe_regression(polls, today, 28)
    assert linear["categorias"]["flavio"]["inclinacao_pp_dia"] == pytest.approx(
        0.2, abs=0.05
    )
    assert linear["fracao_flavio_do_ganho"] == pytest.approx(2 / 3, abs=0.1)
    quad = tendencia.fe_regression(polls, today, 28, quadratic=True)
    assert abs(quad["categorias"]["flavio"]["z_aceleracao"]) < 3
    # Com aceleração verdadeira no Flávio, o termo quadrático a detecta.
    accel = trending(seed=3)
    for p in accel:
        t = (
            date.fromisoformat(p["campo"]["inicio"]) - FIRST
        ).days + 1  # mesmo relógio da série
        bump = 0.0004 * t**2
        v = np.array(p["previsao_vetor"])
        v[1] += bump
        v[2] -= bump
        p["previsao_vetor"] = v.tolist()
    q2 = tendencia.fe_regression(accel, today, 28, quadratic=True)
    assert q2["categorias"]["flavio"]["aceleracao_pp_dia2"] == pytest.approx(
        0.08, abs=0.02
    )
    assert q2["categorias"]["flavio"]["p_aceleracao"] < 0.01


def test_shift_valid_preserves_mass():
    v = np.array([0.40, 0.38, 0.14, 0.04, 0.04])
    out = tendencia.shift_valid(v, [0.1, 0.2, -0.3], 5)
    assert out.sum() == pytest.approx(1)
    assert out[3:] == pytest.approx(v[3:])
    assert out[:3].sum() == pytest.approx(v[:3].sum())
    assert 100 * out[1] / out[:3].sum() == pytest.approx(
        100 * v[1] / v[:3].sum() + 1.0, abs=1e-9
    )


def test_acceleration_test_mixture_pvalue():
    assert tendencia.acceleration_test(10.0, 10.0)["p_valor_mistura_chi2"] == 1.0
    r = tendencia.acceleration_test(10.0, 11.92)
    assert r["p_valor_mistura_chi2"] == pytest.approx(0.025, abs=0.002)


def test_published_trend_anchor(data):
    n = data["nacional"]
    t = n["tendencia"]
    assert n["alvos"]["tendencia"] == t["estado_projetado"]["vetor"]
    assert n["alvos"]["tendencia_corte"] == t["estado_corte"]["vetor"]
    assert t["estado_projetado"]["data"] == data["eleicao"]
    assert t["estado_corte"]["data"] == data["referencia"]
    for key in ("tendencia", "tendencia_corte", "central_inclinacao"):
        assert sum(n["alvos"][key]) == pytest.approx(1)
        assert min(n["alvos"][key]) >= 0
    # A projeção não pode encolher a incerteza.
    assert t["estado_projetado"]["dp_margem_pp"] >= t["estado_corte"]["dp_margem_pp"]
    assert set(t["comparacao_modelos"]) >= {
        "constante",
        "integrada",
        "amortecida",
        "nivel_dlm",
    }
    assert t["parametros"]["otimizador_convergiu"]
    for label in (
        "Âncora de tendência projetada a 04/10",
        "Âncora de tendência, nível no corte",
    ):
        assert label in data["sensibilidades"]
    assert data["configuracao"]["defaults"]["base"] == "central_inclinacao"
    split = t["divisao_migracao"]
    assert {r["fonte"] for r in split["resumo"]} == {
        "serie_nacional_28d",
        "estaduais_todos_os_pares",
        "nexus_matriz_quem_pode_mudar",
        "datafolha_matriz_quem_pode_mudar",
    }
    assert 0 < split["sintese"]["fracao_flavio"] < 1
    assert "teto" in t


def test_validation_has_trend_rows(data):
    v = data["validacao_preditiva"]
    om = v["origem_movel"]
    for name in ("tendencia", "tendencia_corte", "central_inclinacao_28d"):
        assert name in om["metricas"]
        m = om["metricas"][name]
        for k in ("lula", "flavio", "outros"):
            assert f"vies_{k}_pp" in m and f"mae_{k}_pp" in m
    assert set(om["por_grupo_horizonte"]) == {"1-2", "1-3", "3-7"}
    for g in om["por_grupo_horizonte"].values():
        assert g["metricas"]["tendencia"]["n_pares"] == g["n_pares"]
    pairs = {(c["a"], c["b"]) for c in om["comparacoes"]}
    assert ("tendencia", "recencia_3d_7d") in pairs
    assert "tendencia" in v["deixa_uma_casa_fora"]["metricas"]
    assert {"tendencia_constante", "tendencia_integrada"} <= set(
        v["aceleracao"]["metricas"]
    )
    assert "dentro_da_amostra" in v["aceleracao"]


def test_trend_rolling_uses_target_field():
    polls = trending(n_polls=40)
    for p in polls:
        p["publicado_vetor"] = p["previsao_vetor"]
    t = date(2026, 9, 5)
    info = preditiva.released(polls, t)
    found, _, states = preditiva.anchors(info, t, {})
    target = polls[-1]
    out = preditiva.projected(found, states, target)
    state = states["tendencia_constante"]
    origin = tendencia.vector_at(state, t.toordinal())
    horizon = preditiva.midpoint(target["campo"]) - t.toordinal()
    slope = state["a"][tendencia.FREE : 2 * tendencia.FREE]
    # A âncora é projetada ao ponto médio do campo alvo, não parada na origem.
    np.testing.assert_allclose(
        (out["tendencia_constante"] - origin)[: tendencia.FREE],
        horizon * slope,
        atol=2e-4,
    )
    assert "central_inclinacao_28d" in out


def test_select_and_browser_parity(data):
    assert "tendencia" in dict(simulador.ANCHORS)
    html = (ROOT / "docs/predicao_2026_1T_presidente.html").read_text()
    assert 'value="tendencia"' in html
    node = shutil.which("node")
    if not node:
        pytest.skip("Node necessário para verificar a simulação no navegador")
    script = """const fs=require('fs'), engine=require(process.argv[1]);
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    (async()=>{const out={};for(const base of ['tendencia','tendencia_corte'])
      out[base]=await engine.simulate(x,{...x.central.parametros,base},()=>{},()=>false,400);
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
        "tendencia": sens["Âncora de tendência projetada a 04/10"],
        "tendencia_corte": sens["Âncora de tendência, nível no corte"],
    }
    for base, result in out.items():
        for i, k in enumerate(("lula", "flavio")):
            center = result["intervalos"][k][1]
            assert center == pytest.approx(
                expected[base]["brasil"]["percentuais"][k], abs=0.3
            ), (base, i)


def _page(pdf, page):
    exe = shutil.which("pdftotext")
    if not exe or not (ROOT / pdf).exists():
        pytest.skip("pdftotext ou PDF ausente")
    return subprocess.run(
        [exe, "-layout", "-f", str(page), "-l", str(page), str(ROOT / pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_declared_numbers_are_on_the_cited_pages():
    d = json.loads(migracao.DECLARED.read_text())
    for src in d["fontes"].values():
        for key in (
            "primeiro_turno",
            "pode_mudar_por_candidato",
            "decididos_por_candidato",
            "segunda_opcao",
            "segunda_opcao_nao_alinhados",
            "matriz_2t",
        ):
            block = src.get(key)
            if not block:
                continue
            text = _page(src["arquivo"], block["pagina"])
            values = block.get("valores") or {
                f"{r}.{c}": v
                for r, row in block["linhas"].items()
                for c, v in row.items()
            }
            for name, value in values.items():
                if value == 0:
                    continue  # barra ausente: conferida na imagem, sem rótulo
                assert re.search(rf"(?<!\d){value}(?!\d)", text), (key, name, value)


def test_state_labels_exist_and_rule_holds():
    rules = json.loads(migracao.LABELS.read_text())
    for uf, labels in rules["rotulos"].items():
        text = (ROOT / f"analysis/voto_util/quaest/{uf}.json").read_text()
        for printed in labels.values():
            assert printed in text
    # Regra: rótulo = fim do campo + 1 dia, conferida onde rótulo e ficha coexistem.
    for uf in ("BA", "CE", "PE"):
        d = json.loads((ROOT / f"analysis/voto_util/quaest/{uf}.json").read_text())
        last = list(d["pres_1t"]["rodadas"])[-1]
        label = d["pres_1t_lista"]["rotulos_barras"][last]
        end = int(d["ficha"]["campo"].split(" a ")[1].split("/")[0])
        assert int(label.split("/")[0]) == end + 1


def test_state_pairs_have_sampling_error():
    pairs = migracao.state_pairs()
    assert len(pairs) >= 20
    for p in pairs:
        assert p["dias"] > 0
        assert sum(p["variacao_pp"].values()) == pytest.approx(0, abs=1e-9)
        assert all(v > 0 for v in p["dp_pp"].values())
