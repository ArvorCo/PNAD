"""Recuos verificáveis, contexto de escrita e ausência diferente de zero."""

import gzip
import hashlib
import json
import subprocess
from collections import Counter

from politize_se.relogios import ROOT, SAIDA, recuos, resumo


def linha(data, msg, app="LOGD", urna="1"):
    return f"{data}\tINFO\t{urna}\t{app}\t{msg}\tHASH\n"


def test_recuo_prep_nao_vira_recuo_durante_voto():
    txt = linha(
        "26/10/2026 16:39:04",
        "Data e hora que foi digitada pelo operador: 25/09/2026 - 16:42:00",
        "SCUE",
    )
    txt += linha("25/10/2026 07:15:31", "Início das operações do logd")
    txt += linha("25/10/2026 08:00:01", "O voto do eleitor foi computado")
    e = recuos([("log", txt)], 0, 28801, 60000)[0]
    assert e["recuo_s"] == 120213
    assert e["antes_computo_na_escrita"] is True
    assert e["data_anterior_informada"] == "25/09/2026"
    assert (
        e["fase"] == "intersecta_votacao"
    )  # só carimbos: não confundir com ordem escrita
    assert "msg" not in e


def test_recuo_separa_urnas_e_arquivos_e_normaliza_fuso():
    txt = linha("25/10/2026 07:00:00", "O voto do eleitor foi computado")
    txt += linha("25/10/2026 06:59:40", "Evento")
    txt += linha("25/10/2026 06:00:00", "Outra urna", urna="2")
    e = recuos(
        [("a", txt), ("b", linha("25/10/2026 06:00:00", "Novo arquivo"))],
        1,
        25200,
        60000,
    )
    assert len(e) == 1 and e[0]["recuo_s"] == 20
    assert not e[0]["antes_computo_na_escrita"] and e[0]["anterior_s"] == 28800


def test_exportacao_recompoe_sinal_existente():
    m = json.loads((SAIDA / "indice.json").read_text())
    assert m["sinalizadas"] == 141 and m["locais_sinalizados"] == 59
    assert m["criterio_existente"] == "relogio"
    assert m["eventos_antes_computo_na_escrita"] == 141
    assert m["eventos_com_data_anterior_informada"] == 113
    assert m["sinalizadas_contagem_confere"] == 140
    total = cobertas = n = 0
    for uf, info in m["ufs"].items():
        blob = (SAIDA / info["arquivo"]).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == info["sha256"]
        d = json.loads(gzip.decompress(blob))
        assert d["uf"] == uf
        for local in d["locais"].values():
            r = resumo(local["secoes"])
            assert r == local["resumo"]
            total += r["secoes"]
            cobertas += r["cobertas"]
            n += r["sinalizadas"]
        for sinal in d["detalhes"].values():
            assert sinal["recuos"] == len(sinal["eventos"])
            assert sinal["max_s"] == max(
                e["anterior_s"] - e["seguinte_s"] for e in sinal["eventos"]
            )
    assert (total, cobertas, n) == (497897, 497871, 141)
    assert Counter(r["uf"] for r in m["sinais"])["SP"] == 122


def test_js_recorte_agrupamento_e_cobertura():
    subprocess.run(
        [
            "node",
            "-e",
            """
const assert=require('node:assert/strict');global.window=globalThis;
require('./docs/assets/politize_se/transmissao.js');require('./docs/assets/politize_se/relogios.js');
const R=PolitizeRelogios,rows=[[1,1,57,0,true,'ok'],[2,0,0,0,true,'ok'],[3,null,null,null,null,'sem_log']];
assert.equal(R.resumo(rows).sinalizadas,1);assert.equal(R.nivel(R.resumo(rows)),1);
assert.equal(R.nivel(R.resumo(rows.slice(1))),null);assert.equal(R.nivel(R.resumo(rows.slice(1,2))),0);
assert.equal(R.nivel({cobertas:1,secoes:1,sinalizadas:1,max_s:300}),2);
assert.equal(R.nivel({cobertas:1,secoes:1,sinalizadas:1,max_s:301}),3);
const l={id:'BA-1-1-1',uf:'BA'},d={locais:{[l.id]:{secoes:rows}}};R.peek=()=>d;
require('./docs/assets/politize_se_mapa/relogios.js');const S={camada:'relogio',meta:{camadas:{}}},COR={};const M=criarRelogiosMapa({S,COR,h:(...x)=>x});M.instalar();
const ls=M.aplicar([l,{...l,horario:true,secoes:[2]},{...l,horario:true,secoes:[3]}]);
assert.equal(ls[0].relogio_sinais,1);assert.equal(ls[1].relogio_faixa,'0');assert.equal(ls[2].relogio_faixa,null);
assert.equal(M.grupo(ls),'1');assert.equal(M.grupo(ls.slice(1)),null);
assert.equal(M.csv(ls[0]).length,M.colunasCsv.length);assert.equal(M.csv(ls[1])[0],0);
""",
        ],
        cwd=ROOT,
        check=True,
    )
