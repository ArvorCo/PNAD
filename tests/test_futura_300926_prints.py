"""Source integrity and guardrails for the partial Futura screenshot archive."""
import hashlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'data/originals/futura_092026_30/transcricao.json').read_text())


def test_eight_original_screenshots_and_complete_crossbreaks():
    images = DATA['fonte']['imagens']
    assert [p['pagina'] for p in images] == [7,20,22,23,24,25,29,30]
    for item in images:
        payload = (ROOT/item['arquivo']).read_bytes()
        assert payload.startswith(b'\x89PNG')
        assert len(payload) == item['bytes']
        assert hashlib.sha256(payload).hexdigest() == item['sha256']
    tables = DATA['cruzamentos_demograficos']
    assert sum(len(row) for ballot in tables.values() for dim in ballot.values() for row in dim.values()) == 306
    assert DATA['publicado']['1t']['lula'] == 39.4
    assert DATA['espontanea']['percentuais']['lula'] == 39.6
    assert 'marcal' not in DATA['publicado']['1t']
    assert 'clariana' not in DATA['publicado']['1t']


def test_nonresponse_and_unresolved_recomposition_remain_explicit():
    income = DATA['perfil']['percentuais']['renda']
    assert income['ns_nr'] == 10
    assert sum(income.values()) == pytest.approx(99.9)
    checks = {(c['turno'],c['dimensao']):c for c in DATA['controles']}
    assert len(checks) == 6
    assert checks['2t','idade']['residuos_pp']['lula'] == pytest.approx(-.910379)
    assert checks['1t','genero']['recomposto']['lula'] == pytest.approx(39.54)
    assert checks['2t','genero']['recomposto']['flavio'] == pytest.approx(48.835)
    assert any('não se explicam só por arredondamento' in s for s in DATA['limites'])


def test_new_wave_is_documented_without_imputed_income_votes():
    p = json.loads((ROOT/'analysis/reponderacao/pesquisas/futura_2026-09-29.json').read_text())
    assert p['ignorar'] and p['cruzamentos'] == {}
    assert p['n'] == 2000
    assert p['fonte']['tipo'] == 'relatorio' and p['fonte']['total_paginas'] == 46
    assert p['fonte']['conferido_em'] == '2026-10-02'
    assert p['divulgacao'] == '2026-09-30'
    assert p['renda']['amostra_pct'] == [27.7,23.6,23.6,9.9,5.1]
    html = BeautifulSoup((ROOT/'docs/reponderacao_pnad.html').read_text(),'html.parser')
    section = html.find(id='atualizacao')
    rows = [r for r in section.find_all('tr') if 'Futura' in r.get_text()]
    assert len(rows) == 1
    assert '39,4 × 42,2' in rows[0].get_text()
    assert '43,5 × 49,0' in rows[0].get_text()
