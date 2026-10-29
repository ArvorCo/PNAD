"""Movimento: relógios, privacidade e somas antes de taxas/picos."""

import gzip
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest
from politize_se.movimento import histograma

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets/politize_se"


def test_horas_brasilia_e_preservacao():
    r = {
        "status": "ok",
        "relogio_ok": 1,
        "cph_ok": 1,
        "contagem_confere": 1,
        "computados": 20,
        "cph": {"6": 5, "7": 15},
    }
    h, motivo = histograma(r, 2, False, "AC")
    assert h[8:10] == [5, 15] and sum(h) == 20 and motivo == ""
    assert histograma(r, 0, True, "CE") == (None, "pequena")
    assert histograma(r, 0, False, "ZZ") == (None, "exterior")
    assert histograma(None, 0, False, "CE") == (None, "sem_log")
    assert histograma(dict(r, relogio_ok=0), 0, False, "CE") == (None, "relogio")
    assert histograma(dict(r, contagem_confere=0), 0, False, "CE") == (None, "contagem")
    assert histograma(r, None, False, "CE") == (None, "fuso")
    noronha = dict(r, cph={"9": 20})
    assert histograma(noronha, -1, False, "PE")[0][8] == 20
    with pytest.raises(AssertionError):
        histograma(dict(r, computados=19), 0, False, "CE")


def test_publicacao_conserva_totais_e_oculta_pequenas():
    meta = json.loads((ASSETS / "movimento/indice.json").read_text())
    horas = [0] * 24
    total = cobertas = 0
    motivos = Counter()
    for uf, m in meta["ufs"].items():
        raw = (ASSETS / "movimento" / m["arquivo"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == m["sha256"]
        d = json.loads(gzip.decompress(raw))
        for id, rs in d["locais"].items():
            assert id.startswith(uf + "-")
            assert len(rs) == len({r[0] for r in rs})
            for _, hs, motivo in rs:
                total += 1
                if hs is None:
                    motivos[motivo] += 1
                else:
                    assert len(hs) == 24 and all(
                        isinstance(v, int) and v >= 0 for v in hs
                    )
                    assert motivo == ""
                    cobertas += 1
                    horas = [a + b for a, b in zip(horas, hs, strict=True)]
    assert total == meta["secoes"] == 499248
    assert cobertas == meta["cobertas"]
    assert horas == meta["horas"] and sum(horas) == meta["votos"]
    assert motivos == meta["exclusoes"] and motivos["pequena"] > 0
    assert cobertas + sum(motivos.values()) == total


def test_js_agregacao_picos_e_geografia():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node não disponível")
    js = r"""
    global.window={}; require('./docs/assets/politize_se/movimento.js');
    const a=require('node:assert/strict'), M=window.PolitizeMovimento;
    const h1=Array(24).fill(0),h2=Array(24).fill(0);h1[8]=10;h2[9]=100;
    const d={locais:{'CE-00001-1-1000':[[1,h1,''],[2,null,'pequena']], 'CE-00002-1-1001':[[3,h2,'']], 'CE-00001-2-1002':[[4,h1,'']]}};
    const zona=M.resumo(d,{zona:1}); a.equal(zona.secoes,3);a.equal(zona.cobertas,2);a.equal(zona.votos,110);a.equal(M.pico(zona.horas),'9');
    const mun=M.resumo(d,{mun:'00001'});a.equal(mun.secoes,3);a.equal(mun.votos,20);
    const sec=M.resumo(d,{local:'CE-00001-1-1000',secao:2});a.equal(sec.cobertas,0);a.equal(M.pico(sec.horas),null);
    const filtro=M.resumo(d,{local:'CE-00001-1-1000',secoes:[1]});a.equal(filtro.votos,10);a.equal(filtro.secoes,1);
    const empate=Array(24).fill(0);empate[8]=empate[9]=20;a.equal(M.pico(empate),'empate');a.deepEqual(M.picos(empate),[8,9]);
    const COR={},S={meta:{camadas:{}}};require('./docs/assets/politize_se_mapa/movimento.js');
    const MM=window.criarMovimentoMapa({S,COR});MM.instalar();a.equal(MM.picoGrupo([{mov_horas:h1},{mov_horas:h2}]),'9');
    a.equal(S.meta.camadas.pico.nomes['9'],'09h–10h');
    """
    subprocess.run([node, "-e", js], cwd=ROOT, check=True)


def test_totais_zona_somam_contagens_e_nao_taxas():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node não disponível")
    js = r"""
    globalThis.window = {};
    const {criarVisoes} = await import('./docs/assets/politize_se/visoes.js');
    const assert = await import('node:assert/strict');
    const V = criarVisoes({});
    const r = V.totalizar([{n_secoes:1,n_bu2:1,aptos2:100,comp2:60,flavio2:50,lula2:10,fatia_f2:83.3},
                          {n_secoes:2,n_bu2:2,aptos2:400,comp2:300,flavio2:30,lula2:270,fatia_f2:10}]);
    assert.equal(r.n_secoes,3); assert.equal(r.comp2,360);assert.equal(r.flavio2,80);
    assert.equal(r.lula2,280); assert.equal(r.aptos2,500);assert.equal(r.fatia_f2,undefined);
    """
    subprocess.run([node, "--input-type=module", "-e", js], cwd=ROOT, check=True)
