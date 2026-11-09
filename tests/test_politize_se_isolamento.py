"""Contratos de pares, agregação e isolamento sem inferência individual."""

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from politize_se.isolamento import (
    COLUNAS,
    CONTAGENS,
    NIVEIS,
    ajustar,
    elegibilidade,
    ler,
    percentis,
    publicar,
    ranks_porte,
    vetor,
)
from politize_se.saida import gravar

ROOT = Path(__file__).resolve().parents[1]
PUBLICO = ROOT / "docs/assets/politize_se/isolamento"


def secao(**kwargs):
    return {
        "secao": 1,
        "mun_tse": "00001",
        "li": 0,
        "pequena": 0,
        "bu2": 1,
        "agreg_igual": 1,
        "agregadas1": [],
        "agregadas2": [],
        "aptos1": 100,
        "comp1": 80,
        "flavio1": 30,
        "lula1": 30,
        "terceira1": 10,
        "brancos1": 5,
        "nulos1": 5,
        "aptos2": 100,
        "comp2": 70,
        "flavio2": 35,
        "lula2": 25,
        "brancos2": 5,
        "nulos2": 5,
        **kwargs,
    }


def test_pares_conservados_sem_imputacao():
    assert elegibilidade(secao()) == ""
    assert elegibilidade(secao(lula2=None)) == "contagem_ausente"
    assert elegibilidade(secao(lula2=0)) == "conservacao"
    assert elegibilidade(secao(lula2=-1)) == "contagem_invalida"
    assert elegibilidade(secao(bu2=0)) == "sem_bu2"
    assert elegibilidade(secao(aptos1=29)) == "pequena"
    assert elegibilidade(secao(aptos2=29)) == "pequena"
    assert elegibilidade(secao(agregadas1=None)) == "agregacao_ausente"
    assert elegibilidade(secao(agregadas2=[7])) == "agregacao_alterada"
    assert elegibilidade(secao(agreg_igual=0)) == "agregacao_alterada"
    assert elegibilidade(secao(aptos2=40)) == "conservacao"
    assert (
        elegibilidade(secao(flavio2=0, lula2=0, brancos2=35, nulos2=35))
        == "sem_voto_nos_dois"
    )


def test_vetor_nao_duplica_complemento_nem_tamanho():
    r = secao()
    v = vetor(r)
    assert len(v) == 7
    assert v == pytest.approx(
        [35 / 60, 10 / 70, 0.3, 35 / 60 - 0.5, 10 / 70 - 10 / 80, 0.1, 10 / 70]
    )
    maior = {**r, **{c: r[c] * 20 for c in CONTAGENS}}
    assert vetor(maior) == pytest.approx(v)


def gravar_zona(origem, rows):
    cols = list(rows[0])
    gravar(
        origem / "AC/1.json.gz",
        {
            "zona": 1,
            "secoes": {"colunas": cols, "linhas": [[r[c] for c in cols] for r in rows]},
            "locais": {
                "colunas": ["local_id"],
                "linhas": [["AC-00001-1-1"], ["AC-00001-1-2"]],
            },
        },
    )


def test_agregacao_soma_so_mesmos_pares_e_mostra_cobertura(tmp_path):
    maior = secao(secao=2)
    maior.update({c: maior[c] * 3 for c in CONTAGENS})
    maior.update(flavio2=125, lula2=55)
    gravar_zona(tmp_path, [secao(), maior, secao(secao=3, agregadas2=[4])])
    d, m = ler(tmp_path)
    g = d["locais"][("AC", "AC-00001-1-1")]
    assert g["secoes_usadas"] == 2 and g["secoes_total"] == 3
    assert g["flavio2"] == 160 and g["aptos2"] == 400
    assert vetor(g)[0] == pytest.approx(160 / 240)
    assert vetor(g)[0] != pytest.approx((vetor(secao())[0] + vetor(maior)[0]) / 2)
    assert m["AC"]["exclusoes"] == {"agregacao_alterada": 1}
    for nivel in NIVEIS:
        assert sum(r["aptos2"] for r in d[nivel].values()) == 400


def test_duplicata_nao_dobra_agrupamentos(tmp_path):
    gravar_zona(tmp_path, [secao(), secao()])
    with pytest.raises(ValueError, match="duplicada"):
        ler(tmp_path)


def test_empates_e_isolamento_reprodutivel():
    assert percentis(np.ones(5)).tolist() == [50] * 5
    rng = np.random.default_rng(5)
    x = np.vstack([rng.normal(0, 0.01, (200, 7)), np.full((1, 7), 20)]).astype(
        np.float32
    )
    a, m = ajustar(x, arvores=32)
    b, n = ajustar(x, arvores=32)
    assert np.array_equal(a, b) and m == n
    assert a[-1, 0] > 99
    assert np.all(a[:, 1] <= a[:, 0]) and np.all(a[:, 0] <= a[:, 2])
    assert len(m["jaccard_top1_pares"]) == 3
    with pytest.raises(ValueError):
        ajustar(np.zeros((1, 7)))


def test_publicar_reprodutivel_com_niveis_insuficientes(tmp_path):
    origem, saida = tmp_path / "fonte", tmp_path / "saida"
    gravar_zona(origem, [secao(), secao(secao=2, li=1, flavio2=30, lula2=30)])
    m = publicar(origem, saida, arvores=8)
    raw = (saida / "AC.json.gz").read_bytes()
    d = json.loads(gzip.decompress(raw))
    assert d["colunas"] == COLUNAS
    assert len(d["secoes"]) == 2 and len(d["locais"]) == 2
    assert d["zonas"] == {} and d["municipios"] == {}
    assert m["niveis"]["zonas"]["motivo"] == "menos_de_duas_unidades"
    publicar(origem, saida, arvores=8)
    assert (saida / "AC.json.gz").read_bytes() == raw


def test_publico_tem_quatro_universos_conservados():
    if not (PUBLICO / "indice.json").exists():
        pytest.skip("build nacional ainda não publicado")
    m = json.loads((PUBLICO / "indice.json").read_text())
    assert len(m["ufs"]) == 27 and "ZZ" not in m["ufs"]
    assert len(m["features"]) == 7
    assert len(m["modelo"]["sementes"]) == 3
    totais = [m["niveis"][nivel]["totais_elegiveis"] for nivel in NIVEIS]
    assert all(t == totais[0] for t in totais)
    contagem = dict.fromkeys(NIVEIS, 0)
    for meta in m["ufs"].values():
        raw = (PUBLICO / meta["arquivo"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == meta["sha256"]
        assert (
            meta["secoes_usadas"] + sum(meta["exclusoes"].values())
            == meta["secoes_total"]
        )
        d = json.loads(gzip.decompress(raw))
        for nivel in NIVEIS:
            contagem[nivel] += len(d[nivel])
            for row in d[nivel].values():
                p, lo, hi, score, usados, total, aptos, porte, faixa = row
                assert (
                    (porte is None and faixa is None)
                    if nivel != "secoes"
                    else (0 <= porte <= 100 and faixa)
                )
                assert 0 <= lo <= p <= hi <= 100
                assert score > 0 and 1 <= usados <= total and aptos >= 30 * usados
    assert contagem == {n: m["niveis"][n]["unidades"] for n in NIVEIS}


def test_rank_dentro_porte_preserva_score_e_compara_pares():
    registros = [{"aptos2": a} for a in (30, 90, 100, 199, 250, 400)]
    scores = np.array([9, 10, 2, 3, 1, 0])
    r = ranks_porte(registros, scores)
    assert r == [
        [25, "30–99"],
        [75, "30–99"],
        [25, "100–199"],
        [75, "100–199"],
        [50, "200–399"],
        [50, "400+"],
    ]
    assert scores.tolist() == [9, 10, 2, 3, 1, 0]
