"""Tamanho e anel usam a diferença percentual e a soma dos votos publicáveis."""

import gzip
import json
import subprocess
from pathlib import Path

from politize_se.placar_mapa import par

ROOT = Path(__file__).resolve().parents[1]


def test_contagens_respeitam_cobertura_e_secao_pequena():
    r = {"n_bu2": 1, "aptos2": 100, "fatia_f2": 60, "flavio2": 42, "lula2": 28}
    assert par(r) == [42, 28]
    for update in ({"n_bu2": 0}, {"aptos2": 29}, {"fatia_f2": None}, {"lula2": None}):
        assert par({**r, **update}) == [None, None]
    assert par({**r, "flavio2": 0}) == [0, 28]


def test_exportacao_exata_em_todas_as_ufs():
    origem = ROOT / "docs/assets/politize_se/dados/mun"
    destino = ROOT / "docs/assets/politize_se_mapa/placares"
    for p in sorted(destino.glob("*.json.gz")):
        d = json.loads(gzip.decompress(p.read_bytes()))
        n = 0
        for path in (origem / d["uf"]).glob("*.json"):
            t = json.loads(path.read_text())["locais"]
            for row in t["linhas"]:
                r = dict(zip(t["colunas"], row, strict=True))
                assert d["locais"][r["local_id"]] == par(r)
                n += 1
        assert n == len(d["locais"])


def test_anel_ponderado_tamanho_simetrico_e_filtro_sem_vazar_votos():
    js = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
global.window=globalThis;
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se_mapa/placar.js','utf8'));
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se_mapa/horarios.js','utf8'));
const P=PlacarMapa, r=(f,l)=>P.resumo([{flavio2:f,lula2:l}]);
assert.equal(P.raio(r(50,50)),18);
assert.equal(P.raio(r(100,0)),32);
assert.equal(P.raio(r(60,40)),P.raio(r(40,60)));
assert.equal(P.raio(r(600,400)),P.raio(r(60,40)));
assert(P.raio(r(80,20))>P.raio(r(60,40)));
const g=P.resumo([{flavio2:90,lula2:10},{flavio2:100,lula2:900}]);
assert(Math.abs(g.pf-100*190/1100)<1e-10);assert.notEqual(g.pf,50);
assert.equal(P.resumo([{flavio2:null,lula2:10}]).pf,null);
assert(P.resumo([{flavio2:null,lula2:10},{flavio2:0,lula2:10}]).parcial);
const s={secao:1,bu2:true,agreg_igual:true,aptos1:100,aptos2:100,flavio2:20,lula2:60};
const filtrado=HorariosPolitize.agregar({flavio2:900,lula2:100},[s]);
assert.equal(filtrado.flavio2,20);assert.equal(filtrado.lula2,60);
assert.equal(P.resumo([filtrado]).pl,75);
assert.equal(HorariosPolitize.agregar({},[{...s,pequena:true}]).flavio2,null);
assert.equal(HorariosPolitize.agregar({},[{...s,pequena:true}]).lula2,null);
"""
    subprocess.run(["node", "-e", js], cwd=ROOT, check=True)
