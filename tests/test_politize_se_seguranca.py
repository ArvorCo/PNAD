"""Cobertura documental e classes espaciais nunca viram ausência de crime."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/assets/politize_se/seguranca"


def dados():
    return json.loads((BASE / "dados.json").read_text())


def test_presenca_documental_exige_fonte_e_nao_confunde_sede_de_gabinete():
    d = dados()
    assert d["contagens"]["municipios_fbsp"] == 343
    assert len(d["municipios"]) == 367
    assert "CE-14478" not in d["municipios"]  # Juazeiro: sede de gabinete.
    assert "CE-15598" not in d["municipios"]  # Sobral: sede de gabinete.
    assert d["municipios"]["CE-13579"]["fontes"] == ["ctx-034"]
    for m in d["municipios"].values():
        assert m["fontes"]
        assert all(f in d["referencias"] for f in m["fontes"])
    assert "Amanã" in d["revisao"]


def test_imagem_original_e_intersecoes_reproduzem_analise_auditada():
    d = dados()
    for camada in d["cartografia"].values():
        raw = (BASE / camada["arquivo"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == camada["sha256"]
    anterior = ROOT / "docs/assets/analise_realidade_eleicao/territorio.json"
    if anterior.exists():
        for r in json.loads(anterior.read_text())["locais"]:
            atual = d["locais_rj"][r["local_id"]]
            for k in ("controle", "influencia"):
                assert atual[k] == r[k]
    for r in d["locais_rj"].values():
        if not r["coordenada_cadastral"]:
            assert r["controle"] is None and r["influencia"] is None
    assert any(r["controle"] == "Sem marcação" for r in d["locais_rj"].values())


def test_browser_nao_transforma_sem_cobertura_em_zero_nem_grupo_misto_em_dominio():
    js = r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const d = JSON.parse(fs.readFileSync('docs/assets/politize_se/seguranca/dados.json'));
global.window = {};
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se/seguranca.js','utf8'));
window.PolitizeSeguranca.dados = async () => d;
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se_mapa/seguranca.js','utf8'));
(async () => {
 const S = {meta:{camadas:{}}, camada:'controle'}, COR = {};
 const q = window.criarSegurancaMapa({S,COR,h:()=>{}});
 await q.instalar();
 const id = Object.keys(d.locais_rj).find(id=>d.locais_rj[id].controle==='CV');
 const marcado = q.aplicar({id});
 const ausente = q.aplicar({id:'CE-15598-121-1139'});
 assert.equal(marcado.seg_controle,'CV');
 assert.equal(ausente.seg_controle,null);
 assert.equal(ausente.seg_crime,null);
 assert.equal(q.grupo([marcado]),'CV');
 assert.equal(q.grupo([marcado,ausente]),'misto');
 assert.equal(q.grupo([ausente]),null);
 assert.equal(q.csv(ausente).length,q.colunasCsv.length);
 assert.equal(q.csv(ausente)[2],'Sem cobertura territorial');
 S.camada='crime';
 assert.equal(q.texto(ausente),'Sem documentação nesta base');
})().catch(e=>{console.error(e);process.exit(1)});
"""
    subprocess.run(["node", "-e", js], cwd=ROOT, check=True)
