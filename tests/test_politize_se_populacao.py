"""População municipal: universos, contagens, cobertura e direção dos círculos."""

import csv
import subprocess

import pytest
from politize_se.populacao import DADOS, OUT, ROOT, censo, numero, proporcao
from politize_se.populacao_fontes import UFS, hash_arquivo, ler


@pytest.fixture(scope="module")
def dados():
    return ler(OUT / "municipios.json")["municipios"], ler(OUT / "indice.json")


def test_ausencia_nao_e_zero():
    assert numero("-") == 0
    assert numero("...") is None
    assert numero("..") is None
    assert proporcao(None, 5) is None
    assert proporcao(0, 5) == 0
    assert proporcao(10, 0) is None


def test_cobertura_correspondencia_e_censo(dados):
    rows, meta = dados
    assert len(rows) == 5571
    assert len({r["ibge"] for r in rows}) == len(rows)
    assert sum(r["censo_total"] or 0 for r in rows) == 203080756
    ausentes = [r for r in rows if r["estimativa16"] is None]
    assert [(r["uf"], r["nome"]) for r in ausentes] == [
        ("MT", "Boa Esperança do Norte")
    ]
    for uf in UFS.values():
        oficial = censo(uf)
        for r in (m for m in rows if m["uf"] == uf and m["censo16"] is not None):
            assert r["censo16"] == oficial[r["ibge"]]["p16"]
            assert r["censo16"] == sum(map(sum, r["censo_idade_sexo"]))
    assert meta["cobertura"]["com_estimativa16"] == 5570


def test_estimativa_nao_imputa_cadastro_nem_usa_aptos_como_populacao(dados):
    for r in dados[0]:
        e = r["estimativa16"]
        if e is None:
            assert all(
                r[k + "_por100"] is None
                for k in ["eleitorado", "comparecimento1", "comparecimento2"]
            )
            continue
        assert e == pytest.approx(
            r["pop_total_recente"] * r["censo16"] / r["censo_total"], abs=0.00051
        )
        assert 0 < e < r["pop_total_recente"]
        for k in ["eleitorado", "comparecimento1", "comparecimento2"]:
            assert r[k + "_por100"] == pytest.approx(100 * r[k] / e, abs=0.00000051)
            assert r[k + "_saldo"] == pytest.approx(r[k] - e, abs=0.00051)


def test_comparecimento_e_eleitorado_sao_bases_distintas(dados):
    for r in dados[0]:
        t = ler(DADOS / f"mun/{r['uf']}/{r['mun']}.json")["totais"]
        assert r["eleitorado"] == sum(r["tse_idade_sexo"])
        for turno in [1, 2]:
            assert r["comparecimento" + str(turno)] == t["comp" + str(turno)]
            assert r["eleitorado_bu" + str(turno)] == t["aptos" + str(turno)]
            assert r["comparecimento" + str(turno)] <= r["eleitorado_bu" + str(turno)]
        assert r["bu2"] <= r["secoes"]
    cobertura = ler(DADOS / "indice.json")["cobertura"]["ufs"]
    assert sum(r["bu2"] for r in dados[0]) == sum(
        v["com_bu_2t"] for uf, v in cobertura.items() if uf != "ZZ"
    )


def test_perfis_com_mesmo_denominador_16_e_nao_informados(dados):
    for r in dados[0]:
        v = r["tse_idade_sexo"]
        c = r["censo_idade_sexo"]
        assert r["mulheres_tse_pct"] == proporcao(sum(v[1::3]), sum(v))
        assert r["jovens_tse_pct"] == proporcao(sum(v[:6]), sum(v))
        assert r["idosos_tse_pct"] == proporcao(sum(v[18:30]), sum(v))
        if c:
            assert r["mulheres_censo_pct"] == proporcao(
                sum(x[1] for x in c), r["censo16"]
            )
            for k in ["mulheres", "jovens", "idosos"]:
                assert r[k + "_dif_pp"] == pytest.approx(
                    r[k + "_tse_pct"] - r[k + "_censo_pct"], abs=0.00000051
                )


def test_fontes_reproduziveis_e_pnad_estadual(dados):
    meta = dados[1]
    for f in meta["fontes"]:
        assert hash_arquivo(ROOT / f["arquivo"]) == f["sha256"]
    assert set(meta["pnad"]["ufs"]) == set(UFS.values())
    assert meta["pnad"]["ano"] == 2026
    assert meta["pnad"]["peso"] == "V1028"
    for p in meta["pnad"]["ufs"].values():
        assert 0 < p["p16"] < p["total"]
    assert meta["ano_estimativa"] == 2026


def test_csv_preserva_nulos_e_numeros(dados):
    with (OUT / "municipios.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(dados[0])
    assert next(r for r in rows if r["ibge"] == "5101837")["estimativa16"] == ""


def test_raio_tem_direcao_e_area_proporcional():
    subprocess.run(
        [
            "node",
            "-e",
            r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');global.window=globalThis;
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se/populacao.js','utf8'));
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se_mapa/populacao.js','utf8'));
const p=criarPopulacaoMapa({S:{}});
assert(p.raio(50)<p.raio(100));assert(p.raio(150)>p.raio(100));
assert(Math.abs(p.raio(150)**2 / p.raio(50)**2 - 3)<1e-9);
assert.equal(p.raio(null),4);assert.notEqual(p.raio(0),p.raio(null));
""",
        ],
        cwd=ROOT,
        check=True,
    )
