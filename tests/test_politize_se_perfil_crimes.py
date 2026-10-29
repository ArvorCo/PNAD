"""Perfil agregado por unidade correta e índice explícito sem imputar ausentes."""

import gzip
import json
import subprocess
from pathlib import Path

from politize_se.crimes import COMPONENTES, indice, percentil
from politize_se.perfil import estatisticas
from politize_se.perfil import indice as posicao

ROOT = Path(__file__).resolve().parents[1]


def test_faixas_incluem_extremos_e_desconhecidos():
    v = [0] * 33
    for idade, sexo, n in [
        (1600, 2, 3),
        (2124, 4, 4),
        (6064, 4, 5),
        (9999, 2, 6),
        (-3, 0, 7),
    ]:
        v[posicao(idade, sexo)] += n
    assert estatisticas(v) == [25, 9, 7, 11, 7, 7]


def test_indice_empates_e_componentes_faltantes():
    assert percentil(2, [1, 2, 2, 3]) == 50
    assert percentil(0, [0, 0, 0]) == 50
    dados = {
        u: {"indicadores": {k: {"taxa": n} for k in COMPONENTES}}
        for u, n in [("AA", 1), ("BB", 2), ("CC", 3)]
    }
    dados["CC"]["indicadores"]["estupro"]["taxa"] = None
    meta = indice(dados)
    assert dados["AA"]["indice"] == 0
    assert dados["BB"]["indice"] == 100
    assert dados["CC"]["indice"] is None
    assert meta["ufs_completas"] == 2
    assert sum(meta["pesos"].values()) == 1


def test_publicacao_perfil_conserva_contagens_e_ausencias():
    pasta = ROOT / "docs/assets/politize_se/perfil"
    meta = json.loads((pasta / "indice.json").read_text())
    assert len(meta["ufs"]) == 28
    for uf in meta["ufs"]:
        d = json.loads(gzip.decompress((pasta / f"{uf['uf']}.json.gz").read_bytes()))
        r = json.loads(
            gzip.decompress((pasta / f"resumos/{uf['uf']}.json.gz").read_bytes())
        )
        assert len(d["secoes"]) == uf["secoes"]
        assert sum(sum(v) for _, v in d["secoes"].values()) == uf["eleitores"]
        assert sum(v[0] for v in r["locais"].values()) == uf["eleitores"]
        assert all(
            len(v) == 33 and all(isinstance(n, int) and n >= 0 for n in v)
            for _, v in d["secoes"].values()
        )
        for v in r["locais"].values():
            assert v[1] + v[5] <= v[0]
            assert v[2] + v[3] + v[4] <= v[0]


def test_taxas_criminais_e_geografia_publicadas():
    d = json.loads((ROOT / "docs/assets/politize_se/crimes/dados.json").read_text())
    assert d["geografia"] == "UF" and d["ano"] == 2025
    for u in d["ufs"].values():
        for r in u["indicadores"].values():
            if r["taxa"] is not None:
                assert r["completo"] and r["meses"] == 12 and r["linhas_sem_valor"] == 0
                assert abs(r["taxa"] - r["n"] * 100000 / u["populacao"]) < 0.000051
        if u["indice"] is not None:
            assert abs(u["indice"] - sum(u["componentes_indice"].values()) / 5) < 0.006
    for k in ["trafico", "estupro", "roubo_veiculo", "furto_veiculo"]:
        assert all(
            u["indicadores"][k]["linhas_municipais"] == 0 for u in d["ufs"].values()
        )


def test_js_recortes_zona_municipio_secao_e_filtro():
    subprocess.run(
        [
            "node",
            "-e",
            r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');global.window=globalThis;
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se/perfil.js','utf8'));
const P=PolitizePerfil,v=n=>[n,...Array(32).fill(0)],d={uf:'CE',secoes:{'00001-1-1':[100,v(10)],'00001-2-2':[200,v(20)],'00002-1-3':[100,v(30)]}};
assert.equal(P.estatisticas(P.somar(P.selecionar(d,{zona:1})))[0],40);
assert.equal(P.estatisticas(P.somar(P.selecionar(d,{mun:1})))[0],30);
assert.equal(P.estatisticas(P.somar(P.selecionar(d,{local:'CE-00001-1-100',secoes:[1]})))[0],10);
assert.equal(P.selecionar(d,{local:'CE-00001-1-100',secoes:[999]}).length,0);
assert.equal(P.estatisticas(P.somar(P.selecionar(d,{mun:1,zona:2,secao:2})))[0],20);
""",
        ],
        cwd=ROOT,
        check=True,
    )
