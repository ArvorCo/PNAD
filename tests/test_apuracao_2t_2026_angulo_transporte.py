"""Ângulo do transporte e da ordem de chegada: motor sintético e textos."""

import json

import numpy as np
import pandas as pd
import pytest
from apuracao_2t_2026 import angulo_transporte as at
from apuracao_2t_2026 import pagina_texto_angulo_transporte as pt

CHAVE = at.CHAVE


def _sintetico(efeito_marcadas: float = 0.0, seed: int = 1):
    rng = np.random.default_rng(seed)
    linhas, fim2, fim1 = [], [], []
    muns = [("BA", at.SALVADOR), ("BA", "30000"), ("SP", "71072"), ("RS", "88013")]
    for k, (uf, mun) in enumerate(muns):
        base_f = 0.25 + 0.15 * k  # municípios mais de Flávio chegam antes
        for s in range(1, 41):
            aptos = 300
            v1 = 220
            fl1 = round(v1 * base_f + rng.integers(-5, 6))
            marcada = s <= 5
            taxa1 = 78.0
            taxa2 = taxa1 + (8.0 if marcada else 1.0)
            v2 = round(aptos * taxa2 / 100 * 0.95)
            f2 = base_f - 0.03 + (efeito_marcadas / 100 if marcada else 0.0)
            fl = round(v2 * f2)
            linhas.append(
                {
                    "uf": uf,
                    "mun": mun,
                    "zona": 1,
                    "secao": s,
                    "aptos": aptos,
                    "taxa1": taxa1,
                    "taxa2": taxa2,
                    "fl": fl,
                    "lu": v2 - fl,
                    "fl1": fl1,
                    "lu1": v1 - fl1,
                    "rec_min": 150 + 40 * k + s / 10,
                    "enc_min": 1 + k + s / 100,
                    "delta_rel_pp": 7.0 if marcada else 0.0,
                }
            )
            cph = {str(h): 20 for h in range(8, 17)}
            fim2.append(
                {
                    "uf": uf,
                    "mun": mun,
                    "zona": 1,
                    "secao": s,
                    "cph": json.dumps(cph),
                    "cph_ok": True,
                    "primeiro_s": 8 * 3600 + 60,
                }
            )
            if s % 5 == 0:
                fim1.append(
                    {
                        "uf": uf,
                        "mun": mun,
                        "zona": 1,
                        "secao": s,
                        "cph": json.dumps(cph),
                        "cph_ok": True,
                        "primeiro_s": 8 * 3600 + 60,
                    }
                )
    sec = pd.DataFrame(linhas)
    m22 = {
        m: {"uf": u, "aptos": 12000, "abstencao": 2400, "bolsonaro": 3000, "lula": 6000}
        for u, m in muns
    }
    t2 = pd.DataFrame(fim2)
    t1 = pd.DataFrame(fim1)
    off = at.deslocamentos(t2)
    return sec, m22, at.com_fim_do_dia(t2, off), at.com_fim_do_dia(t1, off)


def test_auxiliares():
    assert at.hhmm(0) == "17:00"
    assert at.hhmm(-0.4) == "17:00"
    assert at.hhmm(150.6) == "19:31"
    assert at.hhmm(None) is None
    tot, fim, ult = at.parcela_fim({"13": 10, "14": 5, "15": 1}, 1)
    assert (tot, fim, ult) == (16, 6, 1)
    q = at.quintis(np.arange(10.0), np.ones(10))
    assert list(q) == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]


def test_motor_sem_efeito():
    sec, m22, f2, f1 = _sintetico()
    d = at.analisar(sec, m22, f2, f1, reps=50)
    assert d["rotulo"] == at.ROTULO
    T = d["transporte"]
    assert [q["quintil"] for q in T["quintis"]] == [1, 2, 3, 4, 5]
    # fim do dia: 15h e 16h de 9 horas iguais
    assert T["brasil"]["fim_dia_2t_pct"] == pytest.approx(200 / 9, abs=0.01)
    assert T["brasil"]["did"]["salto"]["did_pp"] == pytest.approx(0, abs=0.6)
    sal = d["bahia"]["Salvador"]
    assert sal["bolsonaro_2022_h2h"] == pytest.approx(33.33, abs=0.01)
    assert sal["did_salto"]["reamostragem"].startswith("seções")
    R = d["ordem"]["recebimento"]
    assert R["vintis"][0]["fatia_f_2t"] < R["vintis"][-1]["fatia_f_2t"]
    assert R["resumo"]["dif_amplitude_pp"] < R["resumo"]["fatia_2t_amplitude_pp"]
    assert sum(v["votos_2t"] for v in R["vintis"]) == int((sec["fl"] + sec["lu"]).sum())


def test_motor_detecta_efeito_plantado():
    sec, m22, f2, f1 = _sintetico(efeito_marcadas=-6.0)
    d = at.analisar(sec, m22, f2, f1, reps=50)
    did = d["transporte"]["brasil"]["did"]["salto"]
    assert did["did_pp"] < -4
    assert did["ic95"][1] < 0


def test_markdown_e_textos():
    sec, m22, f2, f1 = _sintetico()
    d = at.analisar(sec, m22, f2, f1, reps=20)
    md = at.markdown(d)
    assert "Ordem de chegada" in md and "—" not in md
    h = pt.bloco_hipotese(d)
    o = pt.bloco_ordem(d)
    for html in (h, o):
        assert html and "—" not in html and "fraude" not in html.lower()
        assert "não prova irregularidade" in html
    assert "<svg" in o and "fig-angulo_ordem_recebimento" in o
    assert "<table" in h


def test_sem_json_devolve_vazio():
    assert pt.bloco_hipotese(None) == ""
    assert pt.bloco_ordem({}) == ""


def test_json_publicado_coerente():
    arq = at.DADOS / "angulo_transporte.json"
    if not arq.exists():
        pytest.skip("angulo_transporte.json ainda não gerado")
    d = json.loads(arq.read_text("utf-8"))
    V = d["ordem"]["recebimento"]["vintis"]
    assert len(V) == 20
    assert all(v["dif_pp"] < 0 for v in V)
    assert len(d["transporte"]["quintis"]) == 5
    assert pt.bloco_hipotese(d) and pt.bloco_ordem(d)
