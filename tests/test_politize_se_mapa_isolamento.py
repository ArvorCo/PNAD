"""A interface conserva o nível do modelo e não inventa escores de grupos."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_isolamento_mapa_niveis_proprios_ausencias_e_exportacao():
    subprocess.run(
        [
            "node",
            "-e",
            r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');global.window=globalThis;
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se_mapa/isolamento.js','utf8'));
const S={camada:'isolamento_local',meta:{camadas:{}}},COR={},H={ativo:()=>false};
const h=(...args)=>args,nf0=new Intl.NumberFormat('pt-BR');
const colunas=['percentil','percentil_min','percentil_max','score','secoes_usadas','secoes_total','aptos2','percentil_porte','faixa_porte'];
const row=p=>[p,p-2,p+1,.44,2,4,600];
const d={formato:1,uf:'AC',colunas,secoes:{'00001-1-1':[...row(91),40,'400+']},
 locais:{'AC-00001-1-100':row(99),'AC-00001-1-200':row(10)},
 zonas:{'1':row(50),'2':row(30)},municipios:{'00001':row(70),'00002':row(40)}};
let falha=false;
const buscar=async url=>{if(falha)throw Error('rede');return url.includes('indice.json')?{ufs:{AC:{arquivo:'AC.json.gz'}}}:d;};
(async()=>{
 const X=criarIsolamentoMapa({S,COR,H,h,nf0,buscar});await X.instalar();await X.carregar(['AC']);
 const ls=[{id:'AC-00001-1-100',uf:'AC',mun:'00001',zona:1},
 {id:'AC-00001-1-200',uf:'AC',mun:'00001',zona:1},
 {id:'AC-00002-2-300',uf:'AC',mun:'00002',zona:2}];
 X.aplicar(ls);assert.equal(ls[0].isolamento_local,99);assert.equal(ls[0].isolamento_zona,50);
 assert.equal(ls[0].isolamento_municipio,70);assert.equal(ls[2].isolamento_local,null);
 assert.equal(X.grupo(ls.slice(0,2)),null);assert.equal(X.grupo([ls[0]]),99);
 S.camada='isolamento_zona';assert.equal(X.grupo(ls.slice(0,2)),50);assert.equal(X.grupo(ls),null);
 assert.equal(X.grupo([ls[0],{...ls[2],zona:1}]),50); // zona cruza municípios
 S.camada='isolamento_municipio';assert.equal(X.grupo(ls.slice(0,2)),70);assert.equal(X.grupo(ls),null);
 assert.equal(X.grupo([ls[0],{...ls[2],mun:'00001'}]),70); // município cruza zonas
 assert(JSON.stringify(X.celulaSecao(ls[0],1)).includes('P91'));
 assert(JSON.stringify(X.celulaSecao(ls[0],1)).includes('Dentro do porte 400+: P40'));
 assert(!JSON.stringify(X.celulaSecao(ls[0],1)).includes('P99'));
 assert(JSON.stringify(X.celulaSecao(ls[0],2)).includes('Sem escore'));
 assert.equal(X.csv(ls[0]).length,X.colunasCsv.length);
 assert.equal(X.csv(ls[0])[0],'99');assert.equal(X.csv(ls[0])[7],'50');assert.equal(X.csv(ls[0])[14],'70');
 const recorte={...ls[0],horario:true};X.aplicar([recorte]);
 assert.equal(recorte.isolamento_local,null);assert.equal(recorte.isolamento_zona,null);
 assert.equal(X.grupo([recorte]),null);assert(X.csv(recorte).every(v=>v===null));
 assert(X.texto(recorte).includes('recorte de horário'));
 assert(!JSON.stringify(X.celulaSecao(recorte,1)).includes('P91'));
 assert.equal(X.grupo([]),null);
 falha=true;await X.carregar(['CE']);const ausente={...ls[0],uf:'CE'};X.aplicar([ausente]);
 assert.equal(ausente.isolamento_municipio,null);
})().catch(e=>{console.error(e);process.exit(1)});
""",
        ],
        cwd=ROOT,
        check=True,
    )
