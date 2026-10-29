"""Corte exato, qualidade dos logs e recomposição dos prédios filtrados."""

import gzip
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest
from politize_se.horarios import COLUNAS, grupo, linha, segundos_brt, ultimo_util

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets/politize_se_mapa"


@pytest.mark.parametrize(
    ("s", "esperado"), [(None, "sem"), (0, "ate"), (62100, "ate"), (62101, "apos")]
)
def test_corte_exato(s, esperado):
    assert grupo(s) == esperado


def test_fusos_e_data():
    assert segundos_brt("2026-10-25 15:15:00", 2) == 62100
    assert segundos_brt("2026-10-25 18:15:01", -1) == 62101
    assert segundos_brt("2026-10-24 17:00:00", 0) is None
    assert segundos_brt("2026-10-25 23:00:00", 2) is None
    assert segundos_brt("inválido", 0) is None
    assert segundos_brt(None, 0) is None


def test_qualidade_log():
    r = {
        "uf": "AC",
        "status": "ok",
        "relogio_ok": 1,
        "ultimo_s": 54901,
        "primeiro_s": 21600,
        "off": 2,
        "contagem_confere": 1,
        "computados": 300,
        "comparecimento": 300,
        "urna_confere": 1,
        "carga_confere": 1,
        "id_confere": 1,
    }
    assert ultimo_util(r) == (62101, "")
    for k, v, motivo in [
        ("uf", "ZZ", "exterior"),
        ("status", None, "sem_log"),
        ("relogio_ok", 0, "relogio"),
        ("ultimo_s", None, "sem_horario"),
        ("computados", 299, "contagem"),
        ("urna_confere", 0, "identidade"),
    ]:
        assert ultimo_util(dict(r, **{k: v})) == (None, motivo)


def test_privacidade_e_sinais():
    s = {
        "secao": 1,
        "pequena": True,
        "comp2": 21,
        "flavio2": 10,
        "lula2": 11,
        "bu2": True,
        "urna_situacao": "nova",
        "mudanca": {"real": False},
    }
    r = dict(zip(COLUNAS, linha(s, (62100, 62000, "")), strict=True))
    assert r["comp2"] is None and r["flavio2"] is None and r["lula2"] is None
    assert r["enc"] == 62100 and r["trocada"] == 1 and r["mudou"] == 0
    s.update(urna_situacao="mesma_recarga", mudanca={"real": True})
    r = dict(zip(COLUNAS, linha(s, (None, None, "sem_log")), strict=True))
    assert r["trocada"] == 0 and r["mudou"] == 1


def test_dados_publicados():
    indice = json.loads((ASSETS / "horarios/indice.json").read_text())
    counts = {k: Counter() for k in ["enc", "ultimo"]}
    for uf, meta in indice["ufs"].items():
        p = ASSETS / "horarios" / meta["arquivo"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == meta["sha256"]
        d = json.loads(gzip.decompress(p.read_bytes()))
        assert d["colunas"] == COLUNAS
        predios = json.loads((ASSETS / "uf" / f"{uf}.json").read_text())["locais"]
        ids = predios["colunas"].index("id")
        secs = predios["colunas"].index("secoes")
        mapa = {r[ids]: set(r[secs]) for r in predios["linhas"]}
        assert set(mapa) == set(d["locais"])
        for ident, rows in d["locais"].items():
            assert mapa[ident] == {r[0] for r in rows}
            for r in rows:
                assert len(r) == len(COLUNAS)
                for k in counts:
                    counts[k][grupo(r[COLUNAS.index(k)])] += 1
    assert counts == indice["contagens"]
    # Reproduz a auditoria independente dos bancos de boletins/logs de 28/10.
    assert counts["ultimo"] == {"ate": 494959, "apos": 2790, "sem": 1499}
    assert counts["enc"] == {"ate": 488813, "apos": 9084, "sem": 1351}
    assert indice["secoes_bu_fora_do_mapa"] == 0


def test_motor_js():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node indisponível")
    js = r"""
    global.window = {}; require('./docs/assets/politize_se_mapa/horarios.js');
    const assert = require('node:assert/strict'), H = window.HorariosPolitize;
    assert.equal(H.grupo(null), 'sem'); assert.equal(H.grupo(0), 'ate');
    assert.equal(H.grupo(62100), 'ate'); assert.equal(H.grupo(62101), 'apos');
    assert.equal(H.hora(62101), '17:15:01');
    const a = {secao:1, enc:62101, ultimo:62099, bu2:1, agreg_igual:1,
      aptos1:100,comp1:70,flavio1:30,lula1:40,aptos2:100,comp2:90,flavio2:60,lula2:30,bn2:0};
    const b = {...a,secao:2,ultimo:62101,flavio2:10,lula2:80};
    const base = {id:'X',n_secoes:2,fatia_f2:38.9};
    const ss = [a,b].filter(s=>H.passa(s,{enc:'apos',ultimo:'ate'}));
    assert.deepEqual(ss,[a]);
    const r = H.agregar(base,ss);
    assert.deepEqual(r.secoes,[1]); assert.equal(r.n_secoes,1); assert.equal(r.total_secoes,2);
    assert.equal(r.fatia_f2,100*60/90); assert.equal(r.comp_pct2,90);
    assert.equal(r.d_fatia_pp,100*60/90-100*30/70);
    assert.equal(r.log_subiu,null); assert.equal(base.fatia_f2,38.9);
    assert.equal(H.agregar(base,[]),null);
    assert.equal(H.agregar(base,[{...a,pequena:true}]).fatia_f2,null);
    assert.equal(H.agregar(base,[{...a,flavio2:null}]).fatia_f2,null);
    assert.equal(H.agregar(base,[{...a,flavio2:0,lula2:90}]).fatia_f2,0);
    """
    subprocess.run([node, "-e", js], cwd=ROOT, check=True)
