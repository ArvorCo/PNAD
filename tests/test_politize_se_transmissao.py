"""Carimbos, pares da mesma seção, cobertura e recorte no navegador."""

import gzip
import hashlib
import json
import subprocess
from collections import Counter

import pytest
from politize_se.transmissao import ROOT, SAIDA, classificar, nivel, resumo, segundos


def registro(**campos):
    return dict(
        {
            "uf": "AC",
            "mun": "01392",
            "secao": 1,
            "id_confere": 1,
            "pleito": 3221,
            "encerramento": "2026-10-25 15:00:00",
            "emissao": "2026-10-25 15:02:00",
            "dr_hr": "2026-10-25 20:00:00",
            "n_hashes": 1,
            "tipo_arquivo": 1,
        },
        **campos,
    )


def test_carimbos_fusos_e_dias():
    r = classificar(registro())
    assert r[1:6] == [61200, 61320, 72000, 10800, "ok"]
    r = classificar(registro(dr_hr="2026-10-26 01:00:00"))
    assert r[3] == 90000 and r[4] == 28800
    assert segundos("2026-10-25 18:00:00", -1) == 61200
    assert segundos("inválido") is None
    assert segundos("2026-10-25T17:00:00-03:00") is None


def test_inconsistencias_nao_viram_atraso_zero():
    r = classificar(registro(dr_hr="2026-10-25 16:59:59"))
    assert r[4] == -1 and r[5] == "recebimento_antes_encerramento"
    assert resumo([r])["max_s"] is None
    assert classificar(registro(dr_hr="2026-10-25 17:01:00"))[5] == "ordem_emissao"
    assert classificar(registro(n_hashes=2))[5] == "multiplos_pacotes"
    assert classificar(registro(id_confere=0))[5] == "identidade"
    assert classificar(registro(uf="ZZ"))[5] == "exterior"


def test_maximo_e_contraste_sao_de_secoes_identificadas():
    rows = [
        [1, 61200, 61320, 64800, 3600, "ok", 1, 1],
        [2, 68400, 68520, 75600, 7200, "ok", 1, 1],
        [3, 61200, 61320, 64800, 3600, "ok", 1, 1],
    ]
    d = resumo(rows)
    assert d["max_s"] == 7200  # não 75600 - 61200 = 14400
    assert d["secao_max"] == 2 and d["mediana_outras_s"] == 3600
    assert d["excesso_outras_s"] == 3600
    assert resumo(rows[:1])["mediana_outras_s"] is None


@pytest.mark.parametrize(
    ("s", "esperado"),
    [
        (None, None),
        (-1, None),
        (0, 0),
        (3600, 0),
        (3601, 1),
        (14400, 3),
        (14401, 4),
        (18000, 4),
        (18001, 5),
    ],
)
def test_faixas(s, esperado):
    assert nivel(s) == esperado


def test_bases_publicadas_recompoem_e_conferem_hashes():
    m = json.loads((SAIDA / "indice.json").read_text())
    counts = Counter()
    ns = nl = nc = 0
    for uf, meta in m["ufs"].items():
        raw = (SAIDA / meta["arquivo"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == meta["sha256"]
        d = json.loads(gzip.decompress(raw))
        assert d["uf"] == uf
        for local in d["locais"].values():
            r = resumo(local["secoes"])
            assert r == local["resumo"]
            ns += r["secoes"]
            nc += r["cobertas"]
            nl += 1
            counts.update(row[5] for row in local["secoes"])
    assert (
        (ns, nc, nl)
        == (m["secoes"], m["cobertas"], m["locais"])
        == (497897, 497881, 94094)
    )
    assert counts == {
        "ok": 497881,
        "recebimento_antes_encerramento": 3,
        "ordem_emissao": 13,
    }
    assert sum(f["secoes"] for f in m["faixas"]) == nc
    assert sum(f["locais"] for f in m["faixas"]) == m["locais_cobertos"]
    assert m["quantis_s"]["p50"] == 12210 and m["quantis_s"]["max"] == 22580


def test_js_recortes_grupos_sem_dados_e_contraste():
    subprocess.run(
        [
            "node",
            "-e",
            r"""
const assert=require('node:assert/strict');global.window=globalThis;
require('./docs/assets/politize_se/transmissao.js');const T=PolitizeTransmissao;
const rows=[[1,61200,61320,64800,3600,'ok',1,1],[2,68400,68520,75600,7200,'ok',1,1],[3,61200,61320,64800,3600,'ok',1,1],[4,61200,61320,61199,-1,'recebimento_antes_encerramento',1,1]];
const l={id:'SP-71072-1-100',uf:'SP',n_secoes:4},data={formato:1,uf:'SP',locais:{[l.id]:{secoes:rows,resumo:T.resumo(rows)}}};
assert.equal(T.nivel(null),null);assert.equal(T.nivel(-1),null);assert.equal(T.nivel(18000),4);assert.equal(T.nivel(18001),5);
assert.equal(T.hora(90000),'01:00:00 · 26/10');assert.equal(T.duracao(22580),'6h 16min 20s');
assert.equal(T.resumo(rows).max_s,7200);assert.equal(T.resumo(rows).mediana_outras_s,3600);
assert.equal(T.resumo(rows).cobertas,3);assert.equal(T.resumo([rows[3]]).max_s,null);
assert.equal(T.selecionar(data,{local:l.id,secoes:[1,4]}).length,2);
assert.equal(T.leitura(data,{local:l.id,secoes:[1,4]}).max_s,3600);
assert.equal(T.leitura(data,{local:l.id,secao:3}).max_s,3600);
assert.equal(T.leitura(data,{local:'inexistente'}),null);
T.peek=uf=>uf==='SP'?data:undefined;T.dados=async()=>data;
require('./docs/assets/politize_se_mapa/transmissao.js');
const S={camada:'transmissao',meta:{camadas:{}}},COR={},H={};const D=criarTransmissaoMapa({S,COR,H,h:(...x)=>x});D.instalar();
const ls=D.aplicar([l,{...l,horario:true,secoes:[1,4]},{...l,uf:'ZZ'}]);
assert.equal(ls[0].transmissao_max_s,7200);assert.equal(ls[1].transmissao_max_s,3600);assert.equal(ls[2].transmissao_max_s,null);
assert.equal(D.grupo(ls),'1');assert.equal(D.grupo([ls[2]]),null);assert.equal(D.grupo([]),null);
assert.equal(D.csv(ls[0]).length,D.colunasCsv.length);assert.equal(D.csv(ls[1])[0],3600);assert.equal(D.csv(ls[1])[2],1);
assert(D.csv(ls[2]).every(v=>v===null));assert.equal(D.badge(ls[0]),null);
assert(JSON.stringify(D.badge({...l,transmissao_max_s:18001})).includes('Muita atenção'));
""",
        ],
        cwd=ROOT,
        check=True,
    )
