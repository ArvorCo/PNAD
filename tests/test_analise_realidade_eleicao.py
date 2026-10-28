"""Contratos substantivos do relatório: cortes, agregações, controles e auditoria."""

import hashlib
import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pytest
from analise_realidade_eleicao import auditoria, figuras
from analise_realidade_eleicao.dados import cortes, ponderar
from analise_realidade_eleicao.estatistica import correlacao, dentro_grupos, resumo

ROOT = Path(__file__).resolve().parents[1]


def test_cortes_estritos_sem_arredondamento():
    rows = [
        {"ibge": "na_borda", "completo": True, "validos": 100, "flavio": 5},
        {"ibge": "abaixo", "completo": True, "validos": 100001, "flavio": 5000},
        {"ibge": "incompleto", "completo": False, "validos": 100, "flavio": 1},
        {"ibge": "vazio", "completo": True, "validos": 0, "flavio": 0},
    ]
    assert cortes(rows)["5"] == ["abaixo"]
    assert cortes(rows)["10"] == ["na_borda", "abaixo"]


def test_ponderacao_preserva_ausencia_e_zero():
    assert ponderar([{"x": None, "aptos": 50}], "x") is None
    assert (
        ponderar(
            [
                {"x": 0, "aptos": 10},
                {"x": 100, "aptos": 30},
                {"x": None, "aptos": 1000},
            ],
            "x",
        )
        == 75
    )


def test_controle_regional_remove_associacao_entre_grupos():
    x = np.array([1, 2, 3, 101, 102, 103])
    y = np.array([3, 2, 1, 103, 102, 101])
    g = ["A"] * 3 + ["B"] * 3
    assert correlacao(x, y) > 0.99
    assert correlacao(dentro_grupos(x, g), dentro_grupos(y, g)) == pytest.approx(-1)
    assert correlacao(x, 100 - y) == pytest.approx(-correlacao(x, y))


def test_faixas_nao_imputam_taxa_ausente():
    rows = [
        {
            "uf": "A",
            "validos": 100,
            "flavio": 100 - i * 10,
            "lula": i * 10,
            "pct_lula": i * 10,
            "x": i if i != 1 else None,
        }
        for i in range(6)
    ]
    s = resumo(rows, "x")
    assert s["n"] == 5
    assert s["validos"] == 500
    assert sum(b["n"] for b in s["faixas"]) == 5


def test_previsao_nao_usa_o_proprio_resultado():
    x = np.ones((25, 1))
    y = np.linspace(25, 75, 25)
    folds = np.arange(25) % 5
    before = auditoria.prever_fora_amostra(x, y, folds)
    y[0] = 100
    after = auditoria.prever_fora_amostra(x, y, folds)
    assert before[0] == after[0]


def test_triagem_usa_contagens_e_nao_imputa_perfil_ausente(monkeypatch):
    c = {
        "uf": "SP",
        "cd_tse": "1",
        "completo": True,
        "t1_flavio": 2,
        "t1_lula": 1,
        "t1_h2h_flavio": 66.67,
        "delta_comparecimento_pp": 0,
        "t1_aptos": 10,
        "delta_votos_flavio": 1,
        "delta_votos_lula": 1,
    }
    monkeypatch.setattr(auditoria, "ler", lambda _: {"municipios": None})
    monkeypatch.setattr(auditoria, "linhas", lambda _: [c])
    monkeypatch.setattr(auditoria, "prever_fora_amostra", lambda x, y, folds: y.copy())
    m = {
        "uf": "SP",
        "cd_tse": "1",
        "ibge": "1",
        "nome": "Teste",
        "renda_ate2": 50,
        "superior": 10,
        "rural_pct": 0,
        "validos": 5,
        "pct_lula": 40,
        "aptos": 10,
        "sede_lat": 0,
        "sede_lon": 0,
    }
    result = auditoria.triagem([m, {**m, "rural_pct": None}])
    assert result["n"] == 1
    assert result["exclusoes"] == {"perfil_incompleto": 1}
    assert result["linhas"][0]["lula_1t_entre_dois"] == pytest.approx(100 / 3)
    assert result["linhas"][0]["swing_lula"] == pytest.approx(40 - 100 / 3)


def test_bus_vazios_nao_viram_divergencia_mas_voto_positivo_sem_linha_sim(
    tmp_path, monkeypatch
):
    path = tmp_path / "apuracao/data/secoes_2t_2026.sqlite"
    path.parent.mkdir(parents=True)
    with sqlite3.connect(path) as c:
        c.executescript(
            """CREATE TABLE bu_cargo(uf,mun,zona,secao,cargo,aptos,comparecimento,votos);
        CREATE TABLE voto_secao(uf,mun,zona,secao,cargo,tipo,numero,votos);
        INSERT INTO bu_cargo VALUES('sp','1',1,1,1,100,0,0),('sp','1',1,2,1,100,10,10),('sp','1',1,3,1,100,20,20);
        INSERT INTO voto_secao VALUES('sp','1',1,3,1,1,13,12),('sp','1',1,3,1,1,22,8);"""
        )
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(auditoria, "ROOT", tmp_path)
    result = auditoria.integridade_bus(
        [
            {
                "uf": "SP",
                "cd_tse": "1",
                "ibge": "x",
                "nome": "cidade",
                "secoes_total": 3,
                "flavio": 8,
                "lula": 12,
            }
        ]
    )
    t = result["testes"]
    assert [r["secao"] for r in t["bus_sem_linhas_com_total_zero"]] == [1]
    assert [r["secao"] for r in t["soma_votos_diferente_cargo"]] == [2]
    assert result["diferencas"] == []
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_area_do_circulo_proporcional_a_diferenca(monkeypatch):
    monkeypatch.setattr(figuras, "contornos", lambda: "")
    rows = [
        {
            "ibge": str(i),
            "uf": "SP",
            "nome": "Teste",
            "completo": True,
            "flavio": 1,
            "lula": 99,
            "validos": 100,
            "pct_flavio": 1,
            "pct_lula": 99,
            "diferenca": v,
            "sede_lon": -45,
            "sede_lat": -20,
        }
        for i, v in enumerate((1000, 4000))
    ]
    svg = figuras.mapa(rows, 5, 4000)
    radii = [float(v) for v in re.findall(r'<circle[^>]+ r="([\d.]+)"', svg)]
    assert max(radii) / min(radii) == pytest.approx(2)


def test_contrato_dados_reais_e_capitais():
    p = ROOT / "analysis/analise_realidade_eleicao/dados.json"
    if not p.exists():
        pytest.skip("base geográfica local ausente")
    d = json.loads(p.read_text())
    ms = d["municipios"]
    assert len(ms) == 5571
    assert len({m["ibge"] for m in ms}) == len(ms)
    assert {k: len(v) for k, v in cortes(ms).items()} == {
        "5": 0,
        "10": 11,
        "25": 1011,
        "30": 1487,
    }
    assert all(m["flavio"] + m["lula"] == m["validos"] for m in ms)
    assert len(d["cobertura_capitais"]) == 27
    assert len(d["zonas"]) == 298
    for cap in d["cobertura_capitais"]:
        for campo in ("flavio", "lula", "validos"):
            assert cap[f"bus_{campo}"] == cap[f"oficial_{campo}"]
    assert sum(m["ips"] is not None for m in ms) == 5570
    assert sum(m["homicidios_taxa_100mil"] is not None for m in ms) == 3853
